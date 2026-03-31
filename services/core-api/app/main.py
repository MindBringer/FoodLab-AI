from __future__ import annotations

import json
import os
import uuid
from datetime import datetime, timezone
from typing import Any, Optional

import psycopg
import redis
from fastapi import Depends, FastAPI, File, Header, HTTPException, Request, UploadFile
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

APP_NAME = "foodlab-core-api"
APP_VERSION = "0.1.0"

POSTGRES_DSN = os.getenv("POSTGRES_DSN", "postgresql://foodlab:change-me@postgres:5432/foodlab")
REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379/0")
DATA_DIR = os.getenv("DATA_DIR", "/srv/foodlab/data")
API_KEY = os.getenv("API_KEY", "")
API_AUTH_ENABLED = os.getenv("API_AUTH_ENABLED", "1") == "1"
JOB_QUEUE_NAME = os.getenv("JOB_QUEUE_NAME", "foodlab:jobs")

os.makedirs(DATA_DIR, exist_ok=True)

app = FastAPI(title=APP_NAME, version=APP_VERSION)


class ErrorItem(BaseModel):
    code: str
    message: str
    details: dict[str, Any] | None = None


class MetaModel(BaseModel):
    provider: str = "foodlab-core-api"
    model: str | None = None
    processing_ms: int = 0
    entry_channel: str | None = None


class Envelope(BaseModel):
    success: bool
    schema_version: str = "1.0.0"
    job_id: str | None = None
    status: str
    data: dict[str, Any] = Field(default_factory=dict)
    meta: MetaModel = Field(default_factory=MetaModel)
    errors: list[ErrorItem] = Field(default_factory=list)


class TextSubmitRequest(BaseModel):
    text: str
    schema_name: str | None = "tasks/document_analysis"
    schema_version: str | None = "1.0.0"
    rule_set: str | None = "document_analysis_v1"
    entry_channel: str | None = "api"
    metadata: dict[str, Any] = Field(default_factory=dict)


class JobResultModel(BaseModel):
    job_id: str
    status: str
    schema_name: str | None = None
    schema_version: str | None = None
    rule_set: str | None = None
    data: dict[str, Any] = Field(default_factory=dict)
    validation: dict[str, Any] | None = None
    rules: dict[str, Any] | None = None
    error_message: str | None = None
    created_at: str
    updated_at: str


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def get_redis() -> redis.Redis:
    return redis.Redis.from_url(REDIS_URL, decode_responses=True)


def get_conn():
    return psycopg.connect(POSTGRES_DSN)


def ensure_db() -> None:
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS foodlab_jobs (
                job_id TEXT PRIMARY KEY,
                input_type TEXT NOT NULL,
                source_path TEXT,
                input_text TEXT,
                metadata_json JSONB NOT NULL DEFAULT '{}'::jsonb,
                schema_name TEXT,
                schema_version TEXT,
                rule_set TEXT,
                status TEXT NOT NULL,
                result_json JSONB NOT NULL DEFAULT '{}'::jsonb,
                validation_json JSONB,
                rules_json JSONB,
                error_message TEXT,
                created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
            );
            """
        )
        cur.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_foodlab_jobs_status
            ON foodlab_jobs (status);
            """
        )
        conn.commit()


@app.on_event("startup")
def startup() -> None:
    ensure_db()


def require_api_key(x_api_key: Optional[str] = Header(default=None)) -> None:
    if not API_AUTH_ENABLED:
        return
    if not API_KEY:
        raise HTTPException(status_code=500, detail="API auth enabled but API_KEY not configured")
    if x_api_key != API_KEY:
        raise HTTPException(status_code=401, detail="invalid api key")


def envelope_ok(*, status: str, job_id: str | None = None, data: dict[str, Any] | None = None, entry_channel: str | None = None) -> dict[str, Any]:
    return Envelope(
        success=True,
        status=status,
        job_id=job_id,
        data=data or {},
        meta=MetaModel(entry_channel=entry_channel),
        errors=[],
    ).model_dump()


def envelope_error(*, status: str, code: str, message: str, job_id: str | None = None, details: dict[str, Any] | None = None) -> dict[str, Any]:
    return Envelope(
        success=False,
        status=status,
        job_id=job_id,
        data={},
        errors=[ErrorItem(code=code, message=message, details=details)],
    ).model_dump()


def insert_job(
    *,
    job_id: str,
    input_type: str,
    source_path: str | None,
    input_text: str | None,
    metadata_json: dict[str, Any],
    schema_name: str | None,
    schema_version: str | None,
    rule_set: str | None,
) -> None:
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO foodlab_jobs
            (job_id, input_type, source_path, input_text, metadata_json, schema_name, schema_version, rule_set, status)
            VALUES (%s, %s, %s, %s, %s::jsonb, %s, %s, %s, 'queued')
            """,
            (
                job_id,
                input_type,
                source_path,
                input_text,
                json.dumps(metadata_json),
                schema_name,
                schema_version,
                rule_set,
            ),
        )
        conn.commit()


def fetch_job(job_id: str) -> dict[str, Any] | None:
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute(
            """
            SELECT
              job_id, status, schema_name, schema_version, rule_set,
              COALESCE(result_json, '{}'::jsonb)::text,
              CASE WHEN validation_json IS NULL THEN NULL ELSE validation_json::text END,
              CASE WHEN rules_json IS NULL THEN NULL ELSE rules_json::text END,
              error_message,
              created_at::text,
              updated_at::text
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
            "status": row[1],
            "schema_name": row[2],
            "schema_version": row[3],
            "rule_set": row[4],
            "data": json.loads(row[5] or "{}"),
            "validation": json.loads(row[6]) if row[6] else None,
            "rules": json.loads(row[7]) if row[7] else None,
            "error_message": row[8],
            "created_at": row[9],
            "updated_at": row[10],
        }


def queue_job(job_id: str) -> None:
    payload = {"job_id": job_id, "queued_at": utc_now().isoformat()}
    get_redis().rpush(JOB_QUEUE_NAME, json.dumps(payload))


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": APP_NAME, "version": APP_VERSION}


@app.post("/api/v1/jobs/text", dependencies=[Depends(require_api_key)])
def submit_text(req: TextSubmitRequest) -> JSONResponse:
    job_id = str(uuid.uuid4())
    insert_job(
        job_id=job_id,
        input_type="text",
        source_path=None,
        input_text=req.text,
        metadata_json={**req.metadata, "entry_channel": req.entry_channel},
        schema_name=req.schema_name,
        schema_version=req.schema_version,
        rule_set=req.rule_set,
    )
    queue_job(job_id)
    return JSONResponse(
        envelope_ok(status="queued", job_id=job_id, entry_channel=req.entry_channel, data={"message": "job queued"}),
        status_code=202,
    )


@app.post("/api/v1/jobs/submit", dependencies=[Depends(require_api_key)])
async def submit_file(
    request: Request,
    file: UploadFile = File(...),
    schema_name: str | None = "tasks/document_analysis",
    schema_version: str | None = "1.0.0",
    rule_set: str | None = "document_analysis_v1",
    entry_channel: str | None = "api",
) -> JSONResponse:
    job_id = str(uuid.uuid4())
    job_dir = os.path.join(DATA_DIR, job_id)
    os.makedirs(job_dir, exist_ok=True)
    target_path = os.path.join(job_dir, file.filename)
    with open(target_path, "wb") as f:
        f.write(await file.read())

    metadata = {
        "entry_channel": entry_channel,
        "filename": file.filename,
        "content_type": file.content_type,
        "headers": dict(request.headers),
    }

    insert_job(
        job_id=job_id,
        input_type="file",
        source_path=target_path,
        input_text=None,
        metadata_json=metadata,
        schema_name=schema_name,
        schema_version=schema_version,
        rule_set=rule_set,
    )
    queue_job(job_id)
    return JSONResponse(
        envelope_ok(status="queued", job_id=job_id, entry_channel=entry_channel, data={"message": "job queued"}),
        status_code=202,
    )


@app.get("/api/v1/jobs/{job_id}", dependencies=[Depends(require_api_key)])
def get_job(job_id: str) -> dict[str, Any]:
    job = fetch_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="job not found")
    return envelope_ok(
        status=job["status"],
        job_id=job["job_id"],
        data={
            "schema_name": job["schema_name"],
            "schema_version": job["schema_version"],
            "rule_set": job["rule_set"],
            "created_at": job["created_at"],
            "updated_at": job["updated_at"],
        },
    )


@app.get("/api/v1/jobs/{job_id}/result", dependencies=[Depends(require_api_key)])
def get_job_result(job_id: str) -> dict[str, Any]:
    job = fetch_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="job not found")
    if job["status"] in {"queued", "processing"}:
        return envelope_ok(status=job["status"], job_id=job_id, data={})
    if job["status"] == "failed":
        return envelope_error(
            status=job["status"],
            code="job_failed",
            message=job["error_message"] or "job failed",
            job_id=job_id,
        )
    return envelope_ok(
        status=job["status"],
        job_id=job_id,
        data={
            "result": job["data"],
            "validation": job["validation"],
            "rules": job["rules"],
        },
    )
