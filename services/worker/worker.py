import json
import os
import time
from pathlib import Path
from typing import Any, Dict, Optional

import psycopg2
import requests
from psycopg2.extras import RealDictCursor

POSTGRES_DSN = os.getenv("POSTGRES_DSN", "postgresql://foodlab:change-me@postgres:5432/foodlab")
PARSER_URL = os.getenv("PARSER_URL", "http://parser-service:8092")
RAG_URL = os.getenv("RAG_URL", "http://rag-service:8082")
POLL_SECONDS = int(os.getenv("WORKER_POLL_SECONDS", "2"))

def conn():
    return psycopg2.connect(POSTGRES_DSN, cursor_factory=RealDictCursor)

def claim_job() -> Optional[Dict[str, Any]]:
    db = conn()
    try:
        with db:
            with db.cursor() as cur:
                cur.execute("""
                with next_job as (
                    select id from jobs where status='queued' order by created_at asc for update skip locked limit 1
                )
                update jobs j
                set status='running', updated_at=now()
                from next_job
                where j.id = next_job.id
                returning j.*;
                """)
                job = cur.fetchone()
                if not job:
                    return None
                cur.execute("select * from job_files where job_id=%s order by created_at asc", (job["id"],))
                job["files"] = cur.fetchall()
                return job
    finally:
        db.close()

def finish_job(job_id: str, status: str, result: Any = None, error: str | None = None) -> None:
    db = conn()
    try:
        with db:
            with db.cursor() as cur:
                cur.execute(
                    "update jobs set status=%s, result_json=%s, error_message=%s, updated_at=now() where id=%s",
                    (status, json.dumps(result) if result is not None else None, error, job_id),
                )
    finally:
        db.close()

def process_text(job: Dict[str, Any]) -> Dict[str, Any]:
    file_path = Path(job["files"][0]["source_path"])
    text = file_path.read_text(encoding="utf-8", errors="ignore")
    req = job.get("request_json") or {}
    mode = req.get("mode", "query")
    if mode == "index":
        resp = requests.post(
            f"{RAG_URL.rstrip('/')}/ingest/document",
            json={"document_name": job["files"][0]["source_name"], "text": text, "metadata": req.get("metadata") or {}},
            timeout=300,
        )
    else:
        resp = requests.post(f"{RAG_URL.rstrip('/')}/query", json={"query": text, "generate_answer": True}, timeout=300)
    resp.raise_for_status()
    return resp.json()

def process_files(job: Dict[str, Any]) -> Dict[str, Any]:
    req = job.get("request_json") or {}
    results = []
    for file_info in job["files"]:
        parsed = requests.post(
            f"{PARSER_URL.rstrip('/')}/parse",
            json={"file_path": file_info["source_path"], "force_ocr": False},
            timeout=600,
        )
        parsed.raise_for_status()
        parsed_json = parsed.json()
        ingest = requests.post(
            f"{RAG_URL.rstrip('/')}/ingest/document",
            json={
                "document_name": parsed_json["source_name"],
                "text": parsed_json.get("text", ""),
                "metadata": {
                    "source_type": parsed_json.get("source_type"),
                    **(req.get("metadata") or {}),
                },
            },
            timeout=600,
        )
        ingest.raise_for_status()
        results.append({"file": file_info["source_name"], "parse": parsed_json, "ingest": ingest.json()})
    return {"items": results}

def main():
    while True:
        job = None
        try:
            job = claim_job()
            if not job:
                time.sleep(POLL_SECONDS)
                continue
            if job["job_type"] == "text":
                result = process_text(job)
            else:
                result = process_files(job)
            finish_job(job["id"], "done", result=result)
        except Exception as exc:
            if job:
                finish_job(job["id"], "error", error=str(exc))
            time.sleep(POLL_SECONDS)

if __name__ == "__main__":
    main()
