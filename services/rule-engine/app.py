from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

RULE_BASE_DIR = Path(os.getenv("RULE_BASE_DIR", "/app/rules"))

app = FastAPI(title="rule-engine", version="0.2.0")


class EvaluateRequest(BaseModel):
    rule_set: str = Field(..., examples=["document_analysis_v2"])
    payload: dict[str, Any]


def rules_path(rule_set: str) -> Path:
    return RULE_BASE_DIR / f"{rule_set}.json"


def load_rules(rule_set: str) -> dict[str, Any]:
    path = rules_path(rule_set)
    if not path.exists():
        raise HTTPException(status_code=404, detail=f"rule set not found: {rule_set}")
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def _extract_values(payload: Any, field_path: str) -> list[Any]:
    current = [payload]
    for token in field_path.split("."):
        expand_list = token.endswith("[]")
        token = token[:-2] if expand_list else token
        next_items: list[Any] = []
        for item in current:
            if isinstance(item, dict) and token in item:
                value = item[token]
                if expand_list and isinstance(value, list):
                    next_items.extend(value)
                else:
                    next_items.append(value)
        current = next_items
    return current


def _match_where(rule: dict[str, Any], obj: Any) -> bool:
    where = rule.get("where")
    if not where:
        return True
    if not isinstance(obj, dict):
        return False

    parameter_equals = where.get("parameter_equals")
    if parameter_equals is not None:
        if str(obj.get("parameter", "")).strip().lower() != str(parameter_equals).strip().lower():
            return False

    unit_equals = where.get("unit_equals")
    if unit_equals is not None:
        if str(obj.get("unit", "")).strip().lower() != str(unit_equals).strip().lower():
            return False

    return True


def _numeric(value: Any) -> float | None:
    try:
        return float(value)
    except Exception:
        return None


def _matches_scalar(rule: dict[str, Any], value: Any) -> bool:
    if "equals" in rule and value == rule["equals"]:
        return True
    if "contains" in rule and isinstance(value, str) and str(rule["contains"]).lower() in value.lower():
        return True
    if "max" in rule:
        v = _numeric(value)
        if v is not None and v > float(rule["max"]):
            return True
    if "min" in rule:
        v = _numeric(value)
        if v is not None and v < float(rule["min"]):
            return True
    return False


def _evaluate_object_rule(rule: dict[str, Any], values: list[Any]) -> list[dict[str, Any]]:
    matches: list[dict[str, Any]] = []
    compare_field = rule.get("compare_field", "value")

    for obj in values:
        if not isinstance(obj, dict):
            continue
        if not _match_where(rule, obj):
            continue

        candidate = obj.get(compare_field)
        triggered = False

        if "max" in rule:
            v = _numeric(candidate)
            if v is not None and v > float(rule["max"]):
                triggered = True

        if "min" in rule:
            v = _numeric(candidate)
            if v is not None and v < float(rule["min"]):
                triggered = True

        if "equals" in rule and candidate == rule["equals"]:
            triggered = True

        if triggered:
            matches.append(
                {
                    "rule_id": rule.get("rule_id"),
                    "severity": rule.get("severity", "warning"),
                    "message": rule.get("message", "rule matched"),
                    "field": rule["field"],
                    "value": candidate,
                    "object": obj,
                }
            )
    return matches


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/rules")
def list_rules() -> dict[str, list[str]]:
    if not RULE_BASE_DIR.exists():
        return {"rule_sets": []}
    return {"rule_sets": sorted(p.stem for p in RULE_BASE_DIR.glob("*.json"))}


@app.post("/evaluate")
def evaluate(req: EvaluateRequest) -> dict[str, Any]:
    rule_set = load_rules(req.rule_set)
    matches: list[dict[str, Any]] = []

    for rule in rule_set.get("rules", []):
        values = _extract_values(req.payload, rule["field"])

        if rule["field"].endswith("[]") and ("where" in rule or rule.get("compare_field")):
            matches.extend(_evaluate_object_rule(rule, values))
            continue

        for value in values:
            if _matches_scalar(rule, value):
                matches.append(
                    {
                        "rule_id": rule.get("rule_id"),
                        "severity": rule.get("severity", "warning"),
                        "message": rule.get("message", "rule matched"),
                        "field": rule["field"],
                        "value": value,
                    }
                )

    return {
        "rule_set": req.rule_set,
        "ok": not any(m["severity"] == "error" for m in matches),
        "matches": matches,
    }
