from __future__ import annotations

import json
import os
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

session = requests.Session()


def get_conn():
    return psycopg.connect(POSTGRES_DSN)


def get_redis() -> redis.Redis:
    return redis.Redis.from_url(REDIS_URL, decode_responses=True)


def update_status(job_id: str, status: str, *, result: dict[str, Any] | None = None, validation: dict[str, Any] | None = None, rules: dict[str, Any] | None = None, error_message: str | None = None) -> None:
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

    # tolerant wrapper: try generic parser endpoint, fall back to reading plain text files
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


def derive_structured_result(parsed: dict[str, Any]) -> dict[str, Any]:
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

    findings: list[dict[str, Any]] = []
    warnings: list[str] = []

    return {
        "document_type": document_type,
        "sample_type": None,
        "product_name": None,
        "findings": findings,
        "warnings": warnings,
    }


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
