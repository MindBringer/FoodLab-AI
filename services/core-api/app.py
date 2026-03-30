import json
import os
import time
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional

import psycopg2
from fastapi import Body, Depends, FastAPI, File, Form, Header, HTTPException, Query, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from psycopg2.extras import RealDictCursor

app = FastAPI(title="FoodLab Core API", version="3.0.0")

API_KEY = os.getenv("API_KEY", "")
API_AUTH_ENABLED = os.getenv("API_AUTH_ENABLED", "1") == "1"
POSTGRES_DSN = os.getenv("POSTGRES_DSN", "postgresql://foodlab:change-me@postgres:5432/foodlab")
DATA_DIR = Path(os.getenv("DATA_DIR", "/srv/foodlab/data"))
RAW_DIR = DATA_DIR / "raw"
INBOX_DIR = DATA_DIR / "inbox"
RESULTS_DIR = DATA_DIR / "results"

for p in [RAW_DIR, INBOX_DIR, RESULTS_DIR]:
    p.mkdir(parents=True, exist_ok=True)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

def get_conn():
    return psycopg2.connect(POSTGRES_DSN, cursor_factory=RealDictCursor)

def init_db() -> None:
    conn = get_conn()
    try:
        with conn:
            with conn.cursor() as cur:
                cur.execute("""
                create table if not exists jobs (
                    id text primary key,
                    job_type text not null,
                    status text not null,
                    prompt text null,
                    correlation_id text null,
                    request_json jsonb null,
                    result_json jsonb null,
                    error_message text null,
                    created_at timestamptz not null default now(),
                    updated_at timestamptz not null default now()
                );
                """)
                cur.execute("""
                create table if not exists job_files (
                    id text primary key,
                    job_id text not null references jobs(id) on delete cascade,
                    source_name text not null,
                    source_path text not null,
                    source_type text null,
                    size_bytes bigint not null default 0,
                    created_at timestamptz not null default now()
                );
                """)
                cur.execute("create index if not exists idx_jobs_status_created on jobs(status, created_at);")
    finally:
        conn.close()

@app.on_event("startup")
def on_startup() -> None:
    init_db()

def require_api_key(
    x_api_key: Optional[str] = Header(None, alias="X-API-Key"),
    api_key: Optional[str] = Query(None),
):
    if not API_AUTH_ENABLED:
        return
    candidate = (x_api_key or api_key or "").strip()
    if not candidate or candidate != API_KEY:
        raise HTTPException(status_code=401, detail="unauthorized")

@app.get("/health")
def health():
    return {"status": "ok", "service": "core-api", "db": "postgres"}

@app.post("/api/v1/jobs/text")
def submit_text_job(
    body: Dict[str, Any] = Body(...),
    _: None = Depends(require_api_key),
):
    text = str(body.get("text") or "").strip()
    if not text:
        raise HTTPException(status_code=422, detail="text is required")
    mode = str(body.get("mode") or "query").strip().lower()
    prompt = str(body.get("prompt") or "").strip()
    correlation_id = body.get("correlation_id")
    source_name = str(body.get("source_name") or "inline.txt")

    job_id = str(uuid.uuid4())
    file_id = str(uuid.uuid4())
    file_path = INBOX_DIR / f"{job_id}_{source_name}"
    file_path.write_text(text, encoding="utf-8")

    request_json = {
        "mode": mode,
        "source_name": source_name,
        "metadata": body.get("metadata") or {},
    }

    conn = get_conn()
    try:
        with conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    insert into jobs (id, job_type, status, prompt, correlation_id, request_json)
                    values (%s, %s, 'queued', %s, %s, %s)
                    """,
                    (job_id, "text", prompt, correlation_id, json.dumps(request_json)),
                )
                cur.execute(
                    """
                    insert into job_files (id, job_id, source_name, source_path, source_type, size_bytes)
                    values (%s, %s, %s, %s, %s, %s)
                    """,
                    (file_id, job_id, source_name, str(file_path), "text/plain", len(text.encode("utf-8"))),
                )
    finally:
        conn.close()

    return {
        "job_id": job_id,
        "status": "queued",
        "job_type": "text",
        "correlation_id": correlation_id,
        "request": request_json,
    }

@app.post("/api/v1/jobs/submit")
async def submit_file_job(
    files: List[UploadFile] = File(...),
    mode: str = Form("index"),
    prompt: str = Form(""),
    correlation_id: Optional[str] = Form(None),
    metadata_json: str = Form("{}"),
    _: None = Depends(require_api_key),
):
    if not files:
        raise HTTPException(status_code=422, detail="files are required")

    job_id = str(uuid.uuid4())
    request_json = {
        "mode": mode,
        "metadata": json.loads(metadata_json or "{}"),
    }

    conn = get_conn()
    try:
        with conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    insert into jobs (id, job_type, status, prompt, correlation_id, request_json)
                    values (%s, %s, 'queued', %s, %s, %s)
                    """,
                    (job_id, "file", prompt, correlation_id, json.dumps(request_json)),
                )
                accepted = []
                for upload in files:
                    content = await upload.read()
                    safe_name = os.path.basename(upload.filename or "upload.bin")
                    file_id = str(uuid.uuid4())
                    file_path = RAW_DIR / f"{job_id}_{file_id}_{safe_name}"
                    file_path.write_bytes(content)
                    cur.execute(
                        """
                        insert into job_files (id, job_id, source_name, source_path, source_type, size_bytes)
                        values (%s, %s, %s, %s, %s, %s)
                        """,
                        (
                            file_id,
                            job_id,
                            safe_name,
                            str(file_path),
                            upload.content_type or "application/octet-stream",
                            len(content),
                        ),
                    )
                    accepted.append(
                        {
                            "file_id": file_id,
                            "name": safe_name,
                            "content_type": upload.content_type or "application/octet-stream",
                            "size_bytes": len(content),
                        }
                    )
    finally:
        conn.close()

    return {
        "job_id": job_id,
        "status": "queued",
        "job_type": "file",
        "correlation_id": correlation_id,
        "request": request_json,
        "submitted_files": accepted,
    }

@app.get("/api/v1/jobs/{job_id}")
def get_job(job_id: str, _: None = Depends(require_api_key)):
    conn = get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute("select * from jobs where id=%s", (job_id,))
            job = cur.fetchone()
            if not job:
                raise HTTPException(status_code=404, detail="job not found")
            cur.execute(
                "select id, source_name, source_path, source_type, size_bytes, created_at from job_files where job_id=%s order by created_at asc",
                (job_id,),
            )
            job["submitted_files"] = cur.fetchall()
            return job
    finally:
        conn.close()

@app.get("/api/v1/jobs/{job_id}/result")
def get_job_result(job_id: str, _: None = Depends(require_api_key)):
    conn = get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute("select id, status, result_json, error_message, updated_at from jobs where id=%s", (job_id,))
            job = cur.fetchone()
            if not job:
                raise HTTPException(status_code=404, detail="job not found")
            return {
                "job_id": job["id"],
                "status": job["status"],
                "result": job["result_json"],
                "error": job["error_message"],
                "updated_at": job["updated_at"],
            }
    finally:
        conn.close()
