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
APP_VERSION = "0.2.0"

POSTGRES_DSN = os.getenv("POSTGRES_DSN", "postgresql://foodlab:change-me@postgres:5432/foodlab")
REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379/0")
DATA_DIR = os.getenv("DATA_DIR", "/srv/foodlab/data")

API_KEY = os.getenv("API_KEY", "")
API_AUTH_ENABLED = os.getenv("API_AUTH_ENABLED", "1") == "1"

JOB_QUEUE_NAME = os.getenv("JOB_QUEUE_NAME", "foodlab:jobs")
DEFAULT_SCHEMA_NAME = os.getenv("DEFAULT_SCHEMA_NAME", "tasks/document_analysis")
DEFAULT_SCHEMA_VERSION = os.getenv("DEFAULT_SCHEMA_VERSION", "1.0.0")
DEFAULT_RULE_SET = os.getenv("DEFAULT_RULE_SET", "document_analysis_v1")
DEFAULT_ENTRY_CHANNEL = os.getenv("DEFAULT_ENTRY_CHANNEL", "api")

os.makedirs(DATA_DIR, exist_ok=True)

app = FastAPI(title=APP_NAME, version=APP_VERSION)


class ErrorItem(BaseModel):
    code: str
    message: str
    details: dict[str, Any] | None = None


class TraceMeta(BaseModel):
    request_id: str | None = None
    correlation_id: str | None = None
    trace_id: str | None = None
    source_system: str | None = None
    entry_channel: str | None = None


class RuntimeMeta(BaseModel):
    provider: str = APP_NAME
    model: str | None = None
    processing_ms: int = 0
    queued_at: str | None = None
    started_at: str | None = None
    completed_at: str | None = None
    worker_id: str | None = None
    api_version: str = APP_VERSION


class MetaModel(BaseModel):
    trace: TraceMeta = Field(default_factory=TraceMeta)
    runtime: RuntimeMeta = Field(default_factory=RuntimeMeta)


class Envelope(BaseModel):
    success: bool
    schema_version: str | None = None
    job_id: str | None = None
    status: str
    data: dict[str, Any] = Field(default_factory=dict)
    meta: MetaModel = Field(default_factory=MetaModel)
    errors: list[ErrorItem] = Field(default_factory=list)


class SubmitMeta(BaseModel):
    correlation_id: str | None = None
    trace_id: str | None = None
    source_system: str | None = None
    business_context: dict[str, Any] = Field(default_factory=dict)


class TextSubmitRequest(BaseModel):
    text: str
    schema_name: str | None = DEFAULT_SCHEMA_NAME
    schema_version: str | None = DEFAULT_SCHEMA_VERSION
    rule_set: str | None = DEFAULT_RULE_SET
    entry_channel: str | None = DEFAULT_ENTRY_CHANNEL
    metadata: dict[str, Any] = Field(default_factory=dict)
    meta: SubmitMeta = Field(default_factory=SubmitMeta)


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def utc_now_iso() -> str:
    return utc_now().isoformat()


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
                trace_json JSONB NOT NULL DEFAULT '{}'::jsonb,
                runtime_json JSONB NOT NULL DEFAULT '{}'::jsonb,
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
        # Backward-compatible migrations for existing tables.
        cur.execute("ALTER TABLE foodlab_jobs ADD COLUMN IF NOT EXISTS trace_json JSONB NOT NULL DEFAULT '{}'::jsonb;")
        cur.execute("ALTER TABLE foodlab_jobs ADD COLUMN IF NOT EXISTS runtime_json JSONB NOT NULL DEFAULT '{}'::jsonb;")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_foodlab_jobs_status ON foodlab_jobs (status);")
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


def extract_trace(
    request: Request,
    *,
    entry_channel: str | None,
    source_system: str | None = None,
    correlation_id: str | None = None,
    trace_id: str | None = None,
) -> TraceMeta:
    request_id = request.headers.get("x-request-id") or str(uuid.uuid4())
    return TraceMeta(
        request_id=request_id,
        correlation_id=correlation_id or request.headers.get("x-correlation-id"),
        trace_id=trace_id or request.headers.get("x-trace-id"),
        source_system=source_system or request.headers.get("x-source-system"),
        entry_channel=entry_channel,
    )


def empty_runtime(*, queued_at: str | None = None) -> RuntimeMeta:
    return RuntimeMeta(queued_at=queued_at)


def envelope_ok(
    *,
    status: str,
    job_id: str | None = None,
    data: dict[str, Any] | None = None,
    schema_version: str | None = None,
    trace: TraceMeta | None = None,
    runtime: RuntimeMeta | None = None,
) -> dict[str, Any]:
    return Envelope(
        success=True,
        schema_version=schema_version,
        status=status,
        job_id=job_id,
        data=data or {},
        meta=MetaModel(
            trace=trace or TraceMeta(),
            runtime=runtime or RuntimeMeta(),
        ),
        errors=[],
    ).model_dump()


def envelope_error(
    *,
    status: str,
    code: str,
    message: str,
    job_id: str | None = None,
    schema_version: str | None = None,
    details: dict[str, Any] | None = None,
    trace: TraceMeta | None = None,
    runtime: RuntimeMeta | None = None,
) -> dict[str, Any]:
    return Envelope(
        success=False,
        schema_version=schema_version,
        status=status,
        job_id=job_id,
        data={},
        meta=MetaModel(
            trace=trace or TraceMeta(),
            runtime=runtime or RuntimeMeta(),
        ),
        errors=[ErrorItem(code=code, message=message, details=details)],
    ).model_dump()


def insert_job(
    *,
    job_id: str,
    input_type: str,
    source_path: str | None,
    input_text: str | None,
    metadata_json: dict[str, Any],
    trace_json: dict[str, Any],
    runtime_json: dict[str, Any],
    schema_name: str | None,
    schema_version: str | None,
    rule_set: str | None,
) -> None:
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO foodlab_jobs (
                job_id,
                input_type,
                source_path,
                input_text,
                metadata_json,
                trace_json,
                runtime_json,
                schema_name,
                schema_version,
                rule_set,
                status
            )
            VALUES (%s, %s, %s, %s, %s::jsonb, %s::jsonb, %s::jsonb, %s, %s, %s, 'queued')
            """,
            (
                job_id,
                input_type,
                source_path,
                input_text,
                json.dumps(metadata_json),
                json.dumps(trace_json),
                json.dumps(runtime_json),
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
                job_id,
                status,
                schema_name,
                schema_version,
                rule_set,
                COALESCE(result_json, '{}'::jsonb)::text,
                CASE WHEN validation_json IS NULL THEN NULL ELSE validation_json::text END,
                CASE WHEN rules_json IS NULL THEN NULL ELSE rules_json::text END,
                COALESCE(trace_json, '{}'::jsonb)::text,
                COALESCE(runtime_json, '{}'::jsonb)::text,
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
        "trace": json.loads(row[8] or "{}"),
        "runtime": json.loads(row[9] or "{}"),
        "error_message": row[10],
        "created_at": row[11],
        "updated_at": row[12],
    }


def queue_job(job_id: str, trace: TraceMeta) -> None:
    payload = {
        "job_id": job_id,
        "queued_at": utc_now_iso(),
        "trace": trace.model_dump(),
    }
    get_redis().rpush(JOB_QUEUE_NAME, json.dumps(payload))


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": APP_NAME, "version": APP_VERSION}


@app.post("/api/v1/jobs/text", dependencies=[Depends(require_api_key)])
def submit_text(req: TextSubmitRequest, request: Request) -> JSONResponse:
    job_id = str(uuid.uuid4())
    queued_at = utc_now_iso()
    trace = extract_trace(
        request,
        entry_channel=req.entry_channel,
        source_system=req.meta.source_system,
        correlation_id=req.meta.correlation_id,
        trace_id=req.meta.trace_id,
    )
    runtime = empty_runtime(queued_at=queued_at)

    insert_job(
        job_id=job_id,
        input_type="text",
        source_path=None,
        input_text=req.text,
        metadata_json=req.metadata,
        trace_json=trace.model_dump(),
        runtime_json=runtime.model_dump(),
        schema_name=req.schema_name,
        schema_version=req.schema_version,
        rule_set=req.rule_set,
    )
    queue_job(job_id, trace)

    return JSONResponse(
        envelope_ok(
            status="queued",
            job_id=job_id,
            schema_version=req.schema_version,
            data={"message": "job queued"},
            trace=trace,
            runtime=runtime,
        ),
        status_code=202,
    )


@app.post("/api/v1/jobs/submit", dependencies=[Depends(require_api_key)])
async def submit_file(
    request: Request,
    file: UploadFile = File(...),
    schema_name: str | None = DEFAULT_SCHEMA_NAME,
    schema_version: str | None = DEFAULT_SCHEMA_VERSION,
    rule_set: str | None = DEFAULT_RULE_SET,
    entry_channel: str | None = DEFAULT_ENTRY_CHANNEL,
    correlation_id: str | None = None,
    trace_id: str | None = None,
    source_system: str | None = None,
) -> JSONResponse:
    job_id = str(uuid.uuid4())
    queued_at = utc_now_iso()

    trace = extract_trace(
        request,
        entry_channel=entry_channel,
        source_system=source_system,
        correlation_id=correlation_id,
        trace_id=trace_id,
    )
    runtime = empty_runtime(queued_at=queued_at)

    job_dir = os.path.join(DATA_DIR, job_id)
    os.makedirs(job_dir, exist_ok=True)
    target_path = os.path.join(job_dir, file.filename)
    with open(target_path, "wb") as handle:
        handle.write(await file.read())

    metadata = {
        "filename": file.filename,
        "content_type": file.content_type,
        "content_length": request.headers.get("content-length"),
    }

    insert_job(
        job_id=job_id,
        input_type="file",
        source_path=target_path,
        input_text=None,
        metadata_json=metadata,
        trace_json=trace.model_dump(),
        runtime_json=runtime.model_dump(),
        schema_name=schema_name,
        schema_version=schema_version,
        rule_set=rule_set,
    )
    queue_job(job_id, trace)

    return JSONResponse(
        envelope_ok(
            status="queued",
            job_id=job_id,
            schema_version=schema_version,
            data={"message": "job queued"},
            trace=trace,
            runtime=runtime,
        ),
        status_code=202,
    )


@app.get("/api/v1/jobs/{job_id}", dependencies=[Depends(require_api_key)])
def get_job(job_id: str) -> dict[str, Any]:
    job = fetch_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="job not found")

    return envelope_ok(
        status=job["status"],
        job_id=job_id,
        schema_version=job["schema_version"],
        data={
            "result": job["data"],
            "validation": job["validation"],
            "rules": job["rules"],
        },
        trace=TraceMeta(**job["trace"]),
        runtime=RuntimeMeta(**job["runtime"]),
    )


@app.get("/api/v1/jobs/{job_id}/result", dependencies=[Depends(require_api_key)])
def get_job_result(job_id: str) -> dict[str, Any]:
    job = fetch_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="job not found")

    trace = TraceMeta(**job["trace"])
    runtime = RuntimeMeta(**job["runtime"])

    if job["status"] in {"queued", "processing"}:
        return envelope_ok(
            status=job["status"],
            job_id=job_id,
            schema_version=job["schema_version"],
            data={},
            trace=trace,
            runtime=runtime,
        )

    if job["status"] == "failed":
        return envelope_error(
            status=job["status"],
            code="job_failed",
            message=job["error_message"] or "job failed",
            job_id=job_id,
            schema_version=job["schema_version"],
            trace=trace,
            runtime=runtime,
        )

    return envelope_ok(
        status=job["status"],
        job_id=job_id,
        schema_version=job["schema_version"],
        data={
            "result": job["data"],
            "validation": job["validation"],
            "rules": job["rules"],
        },
        trace=trace,
        runtime=runtime,
    )
