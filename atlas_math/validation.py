from __future__ import annotations

from typing import Any, Callable

Validator = Callable[[dict[str, Any]], dict[str, Any]]
MODULE_VALIDATORS: dict[str, Validator] = {}


def register_validator(module_id: str, validator: Validator) -> None:
    MODULE_VALIDATORS[module_id] = validator


def default_validator(record: dict[str, Any]) -> dict[str, Any]:
    errors: list[str] = []
    if not str(record.get("instruction", "")).strip():
        errors.append("missing_instruction")
    if not str(record.get("input", "")).strip():
        errors.append("missing_input")
    if not str(record.get("answer", record.get("output", ""))).strip():
        errors.append("missing_answer")

    metadata = record.get("metadata") or {}
    if not isinstance(metadata, dict):
        errors.append("invalid_metadata")

    return {
        "is_valid": not errors,
        "checks_run": ["nonempty_fields", "metadata_shape"],
        "errors": errors,
        "normalized_answer": str(record.get("answer", record.get("output", ""))).strip() or None,
        "verifier_name": "default",
    }


def validate_record(record: dict[str, Any]) -> dict[str, Any]:
    module_id = str(record.get("module_id") or "")
    validator = MODULE_VALIDATORS.get(module_id, default_validator)
    result = validator(record)
    if not isinstance(result, dict):
        raise TypeError("validator must return a dict")
    return result




