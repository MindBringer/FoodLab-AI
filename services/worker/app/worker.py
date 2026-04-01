from __future__ import annotations

import json
import os
import re
import time
from typing import Any

import psycopg
import redis
import requests

POSTGRES_DSN = os.getenv("POSTGRES_DSN", "postgresql://foodlab:change-me@postgres:5432/foodlab")
REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379/0")
PARSER_URL = os.getenv("PARSER_URL", "http://parser-service:8092")
SCHEMA_REGISTRY_URL = os.getenv("SCHEMA_REGISTRY_URL", "http://schema-registry:8095")
RULE_ENGINE_URL = os.getenv("RULE_ENGINE_URL", "http://rule-engine:8096")
LLM_ROUTER_URL = os.getenv("LLM_ROUTER_URL", "http://llm-router:8091")
JOB_QUEUE_NAME = os.getenv("JOB_QUEUE_NAME", "foodlab:jobs")
JOB_DLQ_NAME = os.getenv("JOB_DLQ_NAME", "foodlab:jobs:dlq")
JOB_RETRY_LIMIT = int(os.getenv("JOB_RETRY_LIMIT", "3"))
POLL_SECONDS = float(os.getenv("WORKER_POLL_SECONDS", "2"))

WORKER_ENABLE_LLM = os.getenv("WORKER_ENABLE_LLM", "1") == "1"
WORKER_LLM_TIMEOUT = int(os.getenv("WORKER_LLM_TIMEOUT", "90"))
WORKER_LLM_MAX_CHARS = int(os.getenv("WORKER_LLM_MAX_CHARS", "12000"))
WORKER_LLM_FALLBACK_HEURISTIC = os.getenv("WORKER_LLM_FALLBACK_HEURISTIC", "1") == "1"

session = requests.Session()


def get_conn():
    return psycopg.connect(POSTGRES_DSN)


def get_redis() -> redis.Redis:
    return redis.Redis.from_url(REDIS_URL, decode_responses=True)


def update_status(job_id: str, status: str, *, result=None, validation=None, rules=None, error_message=None) -> None:
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute(
            """
            UPDATE foodlab_jobs
            SET status = %s,
                result_json = COALESCE(%s::jsonb, result_json),
                validation_json = %s::jsonb,
                rules_json = %s::jsonb,
                error_message = %s,
                updated_at = NOW()
            WHERE job_id = %s
            """,
            (
                status,
                json.dumps(result) if result is not None else None,
                json.dumps(validation) if validation is not None else None,
                json.dumps(rules) if rules is not None else None,
                error_message,
                job_id,
            ),
        )
        conn.commit()


def fetch_job(job_id: str) -> dict[str, Any] | None:
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute(
            """
            SELECT
              job_id, input_type, source_path, input_text,
              metadata_json::text, schema_name, schema_version, rule_set
            FROM foodlab_jobs
            WHERE job_id = %s
            """,
            (job_id,),
        )
        row = cur.fetchone()
        if not row:
            return None
        return {
            "job_id": row[0],
            "input_type": row[1],
            "source_path": row[2],
            "input_text": row[3],
            "metadata": json.loads(row[4] or "{}"),
            "schema_name": row[5],
            "schema_version": row[6],
            "rule_set": row[7],
        }


def parse_input(job: dict[str, Any]) -> dict[str, Any]:
    if job["input_type"] == "text":
        return {"text": job["input_text"], "metadata": job["metadata"]}

    source_path = job["source_path"]
    try:
        with open(source_path, "rb") as f:
            files = {"file": (os.path.basename(source_path), f)}
            resp = session.post(f"{PARSER_URL}/parse", files=files, timeout=120)
            if resp.ok:
                data = resp.json()
                if isinstance(data, dict):
                    return data
    except Exception:
        pass

    try:
        with open(source_path, "r", encoding="utf-8") as f:
            return {"text": f.read(), "metadata": job["metadata"]}
    except Exception:
        return {"text": "", "metadata": job["metadata"]}


def detect_document_type_hint(text: str) -> str | None:
    t = (text or "").lower()
    if any(m in t for m in ["vertrag", "contract", "kündigungsfrist", "vertragsparteien", "vereinbarung"]):
        return "contract"
    if any(m in t for m in ["rechnung", "invoice", "rechnungsnummer", "mwst", "ust", "netto", "brutto"]):
        return "invoice"
    if any(m in t for m in ["labor", "analyse", "lab report", "probe", "mg/kg", "µg", "ph-wert", "ph wert"]):
        return "lab_report"
    if "bericht" in t or "report" in t:
        return "report"
    return None


def heuristic_result(parsed: dict[str, Any]) -> dict[str, Any]:
    text = parsed.get("text") or parsed.get("content") or ""
    return {
        "document_type": detect_document_type_hint(text) or "document",
        "sample_type": None,
        "product_name": None,
        "matrix": None,
        "assessment": None,
        "findings": [],
        "warnings": [],
    }


def trim_text(text: str, max_chars: int) -> str:
    text = (text or "").strip()
    return text[:max_chars] if len(text) > max_chars else text


def build_prompt(text: str, metadata: dict[str, Any], document_type_hint: str | None) -> str:
    filename = metadata.get("filename")
    content_type = metadata.get("content_type")
    entry_channel = metadata.get("entry_channel")
    hint_block = f'Dokumentklassen-Hinweis: "{document_type_hint}"' if document_type_hint else "Dokumentklassen-Hinweis: none"

    return f"""
Du bist ein Extraktionsmodul für FoodLab.
Antworte AUSSCHLIESSLICH mit gültigem JSON.
Keine Einleitung. Keine Erklärungen. Keine Markdown-Codeblöcke.

Gib exakt dieses JSON-Schema zurück:
{{
  "document_type": "contract|invoice|report|lab_report|document",
  "sample_type": null,
  "product_name": null,
  "matrix": null,
  "assessment": null,
  "findings": [
    {{
      "parameter": "string",
      "value": null,
      "unit": null,
      "limit_value": null,
      "limit_unit": null,
      "status": "ok|above_limit|below_limit|unknown|null"
    }}
  ],
  "warnings": [
    "string"
  ]
}}

Regeln:
1. Nur diese Felder verwenden.
2. Wenn ein starker Dokumentklassen-Hinweis vorhanden ist, übernimm ihn, sofern der Text nicht klar dagegen spricht.
3. Bei Vertragstexten: document_type="contract", findings=[].
4. Bei Rechnungstexten: document_type="invoice", findings=[].
5. Bei Labor-/Analyseberichten: document_type="lab_report".
6. findings nur mit echten messbaren Parametern füllen.
7. Produktnamen, Probennamen und Eigennamen niemals übersetzen. Originalsprache beibehalten.
8. Wenn eine Probe explizit benannt ist, setze sample_type auf diese Bezeichnung.
9. Setze matrix auf allgemeine Produktklasse, z. B. Getränk, Gewürz, Öl, Pulver, Milchprodukt, unbekannt.
10. Setze assessment, wenn im Text Begriffe wie "unauffällig", "auffällig", "Grenzwert überschritten", "nicht konform" oder ähnliche Bewertungen vorkommen.
11. status pro finding:
    - above_limit wenn explizit Grenzwertüberschreitung genannt ist
    - ok wenn explizit unauffällig / innerhalb Grenzwert genannt ist
    - sonst unknown
12. limit_value und limit_unit nur setzen, wenn im Text explizit genannt.
13. warnings sparsam verwenden.
14. Keine generischen Aussagen wie:
   - "Keine relevante Analysefunde ..."
   - "Keine Informationen gefunden"
   - "Keine Analyse möglich"
   - "Mehrere mögliche Produktnamen erkannt"
   - "Text enthält keine messbaren Parameter"
15. Wenn keine sinnvollen warnings vorliegen: warnings=[].
16. value und limit_value nur als Zahl, nicht als String.

Metadaten:
- filename: {filename}
- content_type: {content_type}
- entry_channel: {entry_channel}
- {hint_block}

Dokumentinhalt:
{text}
""".strip()


def extract_json_object(text: str) -> dict[str, Any]:
    raw = (text or "").strip()
    try:
        data = json.loads(raw)
        if isinstance(data, dict):
            return data
    except Exception:
        pass

    fenced = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", raw, flags=re.DOTALL | re.IGNORECASE)
    if fenced:
        data = json.loads(fenced.group(1))
        if isinstance(data, dict):
            return data

    start = raw.find("{")
    end = raw.rfind("}")
    if start != -1 and end != -1 and end > start:
        data = json.loads(raw[start:end + 1])
        if isinstance(data, dict):
            return data

    raise ValueError("LLM response did not contain valid JSON object")


def normalize_findings(value: Any) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        return []
    findings = []
    for item in value:
        if not isinstance(item, dict):
            continue
        parameter = str(item.get("parameter") or "").strip()
        if not parameter:
            continue

        parsed_value = None
        raw_value = item.get("value")
        if raw_value not in (None, ""):
            try:
                parsed_value = float(raw_value)
                if parsed_value.is_integer():
                    parsed_value = int(parsed_value)
            except Exception:
                parsed_value = None

        parsed_limit_value = None
        raw_limit_value = item.get("limit_value")
        if raw_limit_value not in (None, ""):
            try:
                parsed_limit_value = float(raw_limit_value)
                if parsed_limit_value.is_integer():
                    parsed_limit_value = int(parsed_limit_value)
            except Exception:
                parsed_limit_value = None

        status = item.get("status")
        allowed_status = {"ok", "above_limit", "below_limit", "unknown"}
        if status not in allowed_status:
            status = "unknown"

        unit = item.get("unit")
        limit_unit = item.get("limit_unit")

        findings.append({
            "parameter": parameter,
            "value": parsed_value,
            "unit": str(unit).strip() if unit not in (None, "") else None,
            "limit_value": parsed_limit_value,
            "limit_unit": str(limit_unit).strip() if limit_unit not in (None, "") else None,
            "status": status,
        })
    return findings


def sanitize_warnings(warnings: Any, document_type: str) -> list[str]:
    if not isinstance(warnings, list):
        warnings = [str(warnings)] if warnings not in (None, "") else []

    blocked_patterns = [
        r"keine relevante analyse",
        r"keine analyse",
        r"keine information",
        r"nichts gefunden",
        r"keine relevante analysefunde",
        r"no relevant analysis",
        r"no findings",
        r"mehrere mögliche produktnamen",
        r"keine messbaren parameter",
        r"text enthält keine messbaren parameter",
    ]

    cleaned = []
    for w in warnings:
        text = str(w).strip()
        if not text:
            continue
        lower = text.lower()
        if any(re.search(pattern, lower) for pattern in blocked_patterns):
            continue
        if document_type in {"contract", "invoice"} and ("analyse" in lower or "produkt" in lower or "parameter" in lower):
            continue
        cleaned.append(text)

    deduped = []
    seen = set()
    for item in cleaned:
        if item not in seen:
            deduped.append(item)
            seen.add(item)
    return deduped


def detect_matrix(sample_type: str | None, product_name: str | None) -> str | None:
    source = " ".join([sample_type or "", product_name or ""]).lower()
    if not source.strip():
        return None
    if any(x in source for x in ["saft", "getränk", "wasser", "limonade"]):
        return "Getränk"
    if any(x in source for x in ["gewürz", "curry", "mischung", "pulver"]):
        return "Gewürz"
    if any(x in source for x in ["öl", "olive", "raps"]):
        return "Öl"
    if any(x in source for x in ["milch", "joghurt", "käse"]):
        return "Milchprodukt"
    return None


def normalize_assessment(value: Any) -> str | None:
    if value in (None, ""):
        return None
    text = str(value).strip().lower()
    if "unauffällig" in text:
        return "unauffällig"
    if "auffällig" in text:
        return "auffällig"
    if "grenzwert" in text and "überschritten" in text:
        return "grenzwertüberschreitung"
    if "nicht konform" in text:
        return "nicht konform"
    return str(value).strip()


def normalize_result(data: dict[str, Any], document_type_hint: str | None) -> dict[str, Any]:
    document_type = str(data.get("document_type") or "document").strip().lower()
    allowed = {"contract", "invoice", "report", "lab_report", "document"}
    if document_type not in allowed:
        document_type = "document"

    if document_type_hint in {"contract", "invoice", "lab_report", "report"}:
        if document_type == "document":
            document_type = document_type_hint
        elif document_type_hint == "contract" and document_type != "contract":
            document_type = "contract"
        elif document_type_hint == "invoice" and document_type != "invoice":
            document_type = "invoice"
        elif document_type_hint == "lab_report" and document_type not in {"lab_report", "report"}:
            document_type = "lab_report"

    sample_type = data.get("sample_type")
    product_name = data.get("product_name")
    findings = normalize_findings(data.get("findings", []))
    matrix = data.get("matrix")
    assessment = normalize_assessment(data.get("assessment"))

    if document_type in {"contract", "invoice"}:
        findings = []
        matrix = None
        assessment = None

    if matrix in (None, ""):
        matrix = detect_matrix(
            str(sample_type).strip() if sample_type not in (None, "") else None,
            str(product_name).strip() if product_name not in (None, "") else None,
        )

    return {
        "document_type": document_type,
        "sample_type": str(sample_type).strip() if sample_type not in (None, "") else None,
        "product_name": str(product_name).strip() if product_name not in (None, "") else None,
        "matrix": str(matrix).strip() if matrix not in (None, "") else None,
        "assessment": assessment,
        "findings": findings,
        "warnings": sanitize_warnings(data.get("warnings", []), document_type),
    }


def call_llm_router(prompt: str) -> dict[str, Any]:
    resp = session.post(f"{LLM_ROUTER_URL}/chat", json={"prompt": prompt}, timeout=WORKER_LLM_TIMEOUT)
    resp.raise_for_status()
    body = resp.json()
    if not isinstance(body, dict):
        raise ValueError("Unexpected llm-router response")
    return body


def derive_structured_result(parsed: dict[str, Any]) -> dict[str, Any]:
    text = parsed.get("text") or parsed.get("content") or ""
    metadata = parsed.get("metadata") or {}
    document_type_hint = detect_document_type_hint(text)

    if not WORKER_ENABLE_LLM:
        return heuristic_result(parsed)

    text = trim_text(text, WORKER_LLM_MAX_CHARS)
    prompt = build_prompt(text, metadata, document_type_hint)

    try:
        llm_response = call_llm_router(prompt)
        data = extract_json_object(llm_response.get("text", ""))
        result = normalize_result(data, document_type_hint)
        result["warnings"] = result.get("warnings", []) + [
            f"llm_provider={llm_response.get('provider')}",
            f"llm_model={llm_response.get('model')}",
        ]
        return result
    except Exception as exc:
        if WORKER_LLM_FALLBACK_HEURISTIC:
            fallback = heuristic_result(parsed)
            fallback["warnings"] = fallback.get("warnings", []) + [f"llm_fallback={type(exc).__name__}"]
            return fallback
        raise


def validate_result(job: dict[str, Any], result: dict[str, Any]) -> dict[str, Any] | None:
    if not job["schema_name"] or not job["schema_version"]:
        return None
    resp = session.post(
        f"{SCHEMA_REGISTRY_URL}/validate",
        json={"schema_name": job["schema_name"], "schema_version": job["schema_version"], "payload": result},
        timeout=30,
    )
    resp.raise_for_status()
    return resp.json()


def evaluate_rules(job: dict[str, Any], result: dict[str, Any]) -> dict[str, Any] | None:
    if not job["rule_set"]:
        return None
    resp = session.post(f"{RULE_ENGINE_URL}/evaluate", json={"rule_set": job["rule_set"], "payload": result}, timeout=30)
    resp.raise_for_status()
    return resp.json()


def process_job(job_id: str) -> None:
    job = fetch_job(job_id)
    if not job:
        return

    update_status(job_id, "processing")
    try:
        parsed = parse_input(job)
        result = derive_structured_result(parsed)
        validation = validate_result(job, result)
        rules = evaluate_rules(job, result)

        final_status = "done"
        if validation and not validation.get("valid", True):
            final_status = "failed"
        elif rules and not rules.get("ok", True):
            final_status = "done_with_warnings"

        update_status(job_id, final_status, result=result, validation=validation, rules=rules, error_message=None)
    except Exception as exc:
        update_status(job_id, "failed", error_message=str(exc))
        raise


def send_to_dlq(message: str, reason: str) -> None:
    payload = {"message": message, "reason": reason, "moved_at": time.time()}
    get_redis().rpush(JOB_DLQ_NAME, json.dumps(payload))


def loop_forever() -> None:
    r = get_redis()
    while True:
        item = r.blpop(JOB_QUEUE_NAME, timeout=int(POLL_SECONDS))
        if not item:
            continue
        _, raw = item
        retries = 0
        try:
            message = json.loads(raw)
            retries = int(message.get("retries", 0))
            process_job(message["job_id"])
        except Exception:
            retries += 1
            try:
                msg = json.loads(raw)
            except Exception:
                send_to_dlq(raw, "invalid_json")
                continue

            if retries > JOB_RETRY_LIMIT:
                send_to_dlq(raw, "retry_limit_exceeded")
                continue

            msg["retries"] = retries
            r.rpush(JOB_QUEUE_NAME, json.dumps(msg))
            time.sleep(1)


if __name__ == "__main__":
    loop_forever()
