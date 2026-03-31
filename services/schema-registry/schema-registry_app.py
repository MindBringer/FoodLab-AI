from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from jsonschema import Draft202012Validator

SCHEMA_BASE_DIR = Path(os.getenv("SCHEMA_BASE_DIR", "/app/schemas"))

app = FastAPI(title="schema-registry", version="0.1.0")


class ValidateRequest(BaseModel):
    schema_name: str
    schema_version: str
    payload: dict[str, Any]


def schema_path(schema_name: str, schema_version: str) -> Path:
    return SCHEMA_BASE_DIR / schema_name / f"{schema_version}.json"


def load_schema(schema_name: str, schema_version: str) -> dict[str, Any]:
    path = schema_path(schema_name, schema_version)
    if not path.exists():
        raise HTTPException(status_code=404, detail=f"schema not found: {schema_name}/{schema_version}")
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/schemas")
def list_schemas() -> dict[str, Any]:
    items: dict[str, list[str]] = {}
    if not SCHEMA_BASE_DIR.exists():
        return {"schemas": items}
    for folder in sorted(p for p in SCHEMA_BASE_DIR.iterdir() if p.is_dir()):
        versions = sorted(p.stem for p in folder.glob("*.json"))
        items[folder.name] = versions
    return {"schemas": items}


@app.get("/schemas/{schema_name}")
def get_schema_versions(schema_name: str) -> dict[str, Any]:
    folder = SCHEMA_BASE_DIR / schema_name
    if not folder.exists():
        raise HTTPException(status_code=404, detail="schema group not found")
    versions = sorted(p.stem for p in folder.glob("*.json"))
    return {"schema_name": schema_name, "versions": versions}


@app.get("/schemas/{schema_name}/{schema_version}")
def get_schema(schema_name: str, schema_version: str) -> dict[str, Any]:
    return load_schema(schema_name, schema_version)


@app.post("/validate")
def validate(req: ValidateRequest) -> dict[str, Any]:
    schema = load_schema(req.schema_name, req.schema_version)
    validator = Draft202012Validator(schema)
    errors = sorted(validator.iter_errors(req.payload), key=lambda e: list(e.path))
    return {
        "valid": len(errors) == 0,
        "schema_name": req.schema_name,
        "schema_version": req.schema_version,
        "errors": [
            {
                "message": e.message,
                "path": list(e.path),
                "validator": e.validator,
            }
            for e in errors
        ],
    }

