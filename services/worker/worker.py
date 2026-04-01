from __future__ import annotations

import json
import os
import re
import time
from typing import Any

import psycopg
import redis
import requests

APP_NAME = "foodlab-worker"

POSTGRES_DSN = os.getenv("POSTGRES_DSN", "postgresql://foodlab:change-me@postgres:5432/foodlab")
REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379/0")
PARSER_URL = os.getenv("PARSER_URL", "http://parser-service:8092")
RAG_URL = os.getenv("RAG_URL", "http://rag-service:8082")
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


def update_status(
    job_id: str,
    status: str,
    *,
    result: dict[str, Any] | None = None,
    validation: dict[str, Any] | None = None,
    rules: dict[str, Any] | None = None,
    error_message: str | None = None,
) -> None:
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


def heuristic_result(parsed: dict[str, Any]) -> dict[str, Any]:
    text = parsed.get("text") or parsed.get("content") or ""
    text_lower = text.lower()

    document_type = "document"
    if "vertrag" in text_lower or "contract" in text_lower:
        document_type = "contract"
    elif "rechnung" in text_lower or "invoice" in text_lower:
        document_type = "invoice"
    elif "bericht" in text_lower or "report" in text_lower:
        document_type = "report"
    elif "analyse" in text_lower or "lab" in text_lower:
        document_type = "lab_report"

    return {
        "document_type": document_type,
        "sample_type": None,
        "product_name": None,
        "findings": [],
        "warnings": [],
    }


def trim_text(text: str, max_chars: int) -> str:
    text = (text or "").strip()
    if len(text) <= max_chars:
        return text
    return text[:max_chars]


def build_prompt(text: str, metadata: dict[str, Any]) -> str:
    filename = metadata.get("filename")
    content_type = metadata.get("content_type")
    entry_channel = metadata.get("entry_channel")

    return f"""
Du analysierst Dokumente für FoodLab.

Aufgabe:
Lies den folgenden Dokumentinhalt und gib AUSSCHLIESSLICH gültiges JSON zurück.
Keine Einleitung. Keine Markdown-Codeblöcke. Kein zusätzlicher Text.

Zielstruktur:
{{
  "document_type": "contract|invoice|report|lab_report|document",
  "sample_type": null,
  "product_name": null,
  "findings": [
    {{
      "parameter": "string",
      "value": null,
      "unit": null
    }}
  ],
  "warnings": [
    "string"
  ]
}}

Regeln:
- Nur gültiges JSON ausgeben.
- document_type muss immer gesetzt sein.
- Wenn nichts Sicheres gefunden wird: document_type = "document".
- findings ist immer ein Array.
- warnings ist immer ein Array.
- Keine zusätzlichen Felder erzeugen.
- value nur als Zahl, wenn im Text klar erkennbar.
- sample_type und product_name nur setzen, wenn im Text erkennbar, sonst null.

Metadaten:
- filename: {filename}
- content_type: {content_type}
- entry_channel: {entry_channel}

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
        candidate = raw[start : end + 1]
        data = json.loads(candidate)
        if isinstance(data, dict):
            return data

    raise ValueError("LLM response did not contain valid JSON object")


def normalize_findings(value: Any) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        return []

    findings: list[dict[str, Any]] = []
    for item in value:
        if not isinstance(item, dict):
            continue
        parameter = str(item.get("parameter") or "").strip()
        if not parameter:
            continue

        raw_value = item.get("value")
        parsed_value = None
        if raw_value is not None and raw_value != "":
            try:
                parsed_value = float(raw_value)
                if parsed_value.is_integer():
                    parsed_value = int(parsed_value)
            except Exception:
                parsed_value = None

        unit = item.get("unit")
        findings.append(
            {
                "parameter": parameter,
                "value": parsed_value,
                "unit": str(unit).strip() if unit not in (None, "") else None,
            }
        )
    return findings


def normalize_result(data: dict[str, Any]) -> dict[str, Any]:
    document_type = str(data.get("document_type") or "document").strip().lower()
    allowed_types = {"contract", "invoice", "report", "lab_report", "document"}
    if document_type not in allowed_types:
        document_type = "document"

    sample_type = data.get("sample_type")
    product_name = data.get("product_name")
    warnings = data.get("warnings", [])

    if not isinstance(warnings, list):
        warnings = [str(warnings)]
    warnings = [str(w).strip() for w in warnings if str(w).strip()]

    return {
        "document_type": document_type,
        "sample_type": str(sample_type).strip() if sample_type not in (None, "") else None,
        "product_name": str(product_name).strip() if product_name not in (None, "") else None,
        "findings": normalize_findings(data.get("findings", [])),
        "warnings": warnings,
    }


def call_llm_router(prompt: str) -> dict[str, Any]:
    resp = session.post(
        f"{LLM_ROUTER_URL}/chat",
        json={"prompt": prompt},
        timeout=WORKER_LLM_TIMEOUT,
    )
    resp.raise_for_status()
    body = resp.json()
    if not isinstance(body, dict):
        raise ValueError("Unexpected llm-router response")
    return body


def derive_structured_result(parsed: dict[str, Any]) -> dict[str, Any]:
    text = parsed.get("text") or parsed.get("content") or ""
    metadata = parsed.get("metadata") or {}

    if not WORKER_ENABLE_LLM:
        return heuristic_result(parsed)

    text = trim_text(text, WORKER_LLM_MAX_CHARS)
    prompt = build_prompt(text, metadata)

    try:
        llm_response = call_llm_router(prompt)
        llm_text = llm_response.get("text", "")
        data = extract_json_object(llm_text)
        result = normalize_result(data)
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
        json={
            "schema_name": job["schema_name"],
            "schema_version": job["schema_version"],
            "payload": result,
        },
        timeout=30,
    )
    resp.raise_for_status()
    return resp.json()


def evaluate_rules(job: dict[str, Any], result: dict[str, Any]) -> dict[str, Any] | None:
    if not job["rule_set"]:
        return None
    resp = session.post(
        f"{RULE_ENGINE_URL}/evaluate",
        json={"rule_set": job["rule_set"], "payload": result},
        timeout=30,
    )
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

        update_status(
            job_id,
            final_status,
            result=result,
            validation=validation,
            rules=rules,
            error_message=None,
        )
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
