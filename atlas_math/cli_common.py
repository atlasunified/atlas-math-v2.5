from __future__ import annotations

import hashlib
import json
import math
import os
from dataclasses import asdict, is_dataclass
from pathlib import Path
from typing import Any

from atlas_math.cli_config import DEFAULT_DIFFICULTY_MIXES, DEFAULT_LEVELS, SIZE_PRESETS


def info_get(info: Any, key: str, default=None):
    if isinstance(info, dict):
        return info.get(key, default)
    return getattr(info, key, default)


def clamp(value: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, value))


def fmt_int(n: int) -> str:
    return f"{n:,}"


def fmt_pct(x: float) -> str:
    return f"{x * 100:5.1f}%"


def safe_int(raw: str, default: int | None = None) -> int | None:
    try:
        return int(raw)
    except (TypeError, ValueError):
        return default


def safe_float(raw: str, default: float | None = None) -> float | None:
    try:
        return float(raw)
    except (TypeError, ValueError):
        return default


def dedupe_keep_order(items):
    seen = set()
    out = []
    for item in items:
        if item not in seen:
            seen.add(item)
            out.append(item)
    return out


def sample_to_dict(sample):
    if sample is None:
        raise TypeError("Sample is None")

    if isinstance(sample, dict):
        return sample

    if is_dataclass(sample):
        return asdict(sample)

    if hasattr(sample, "__dict__"):
        data = dict(sample.__dict__)
        if data:
            return data

    required = ("instruction", "input", "answer")
    if all(hasattr(sample, key) for key in required):
        data = {}
        for key in (
            "module_id",
            "topic",
            "subtopic",
            "difficulty",
            "difficulty_level",
            "instruction",
            "input",
            "output",
            "output_words",
            "answer",
            "answer_words",
            "metadata",
            "sample_id",
            "case_id",
            "canonical_key",
            "family_id",
            "template_id",
            "source_mode",
            "generator_version",
            "split_group_key",
        ):
            if hasattr(sample, key):
                data[key] = getattr(sample, key)
        return data

    raise TypeError(f"Unsupported sample type: {type(sample).__name__}")


def serialize_sample(sample, fmt: str = "clean"):
    data = attach_identity_fields(sample_to_dict(sample))

    if fmt == "clean":
        return {
            "instruction": data.get("instruction", ""),
            "input": data.get("input", ""),
            "answer": str(data.get("answer", "")),
            "answer_words": data.get("answer_words", ""),
            "difficulty": data.get("difficulty", ""),
        }

    if fmt == "extended":
        return {
            "instruction": data.get("instruction", ""),
            "input": data.get("input", ""),
            "answer": str(data.get("answer", "")),
            "answer_words": data.get("answer_words", ""),
            "difficulty": data.get("difficulty", ""),
            "topic": data.get("topic", ""),
            "subtopic": data.get("subtopic", ""),
        }

    if fmt == "rich":
        return data

    raise ValueError(f"Unknown format: {fmt}")


def write_jsonl(records, output: str):
    out_path = Path(output)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8") as handle:
        for record in records:
            handle.write(json.dumps(record, ensure_ascii=False) + "\n")


def normalize_text(value: Any) -> str:
    if value is None:
        return ""
    return " ".join(str(value).strip().split())


def attach_identity_fields(record: dict[str, Any]) -> dict[str, Any]:
    normalized = dict(record)
    metadata = normalized.get("metadata") or {}
    if not isinstance(metadata, dict):
        metadata = {"raw_metadata": metadata}
        normalized["metadata"] = metadata

    canonical_key = str(
        normalized.get("canonical_key")
        or metadata.get("canonical_key")
        or metadata.get("case_id")
        or ""
    )
    family_id = str(
        normalized.get("family_id")
        or metadata.get("family_id")
        or metadata.get("family")
        or metadata.get("template_family")
        or ""
    )
    template_id = str(
        normalized.get("template_id")
        or metadata.get("template_id")
        or family_id
        or ""
    )
    case_id = str(
        normalized.get("case_id")
        or metadata.get("case_id")
        or canonical_key
        or ""
    )

    normalized["canonical_key"] = canonical_key
    normalized["family_id"] = family_id
    normalized["template_id"] = template_id
    normalized["case_id"] = case_id

    if not normalized.get("sample_id"):
        normalized["sample_id"] = hashlib.sha256(
            json.dumps(normalized, sort_keys=True, ensure_ascii=False).encode("utf-8")
        ).hexdigest()

    if not normalized.get("split_group_key"):
        normalized["split_group_key"] = canonical_key or case_id or family_id or normalized["sample_id"]

    return normalized


SUPPORTED_DEDUPE_MODES = {"input_answer", "input_only", "full", "canonical", "case_id", "family"}


def dedupe_key_from_record(record: dict, dedupe_mode: str = "input_answer") -> str:
    if dedupe_mode not in SUPPORTED_DEDUPE_MODES:
        raise ValueError(f"Unknown dedupe mode: {dedupe_mode}")

    record = attach_identity_fields(record)
    if dedupe_mode == "input_only":
        raw = normalize_text(record.get("input", ""))
    elif dedupe_mode == "full":
        raw = json.dumps(record, sort_keys=True, ensure_ascii=False)
    elif dedupe_mode == "canonical":
        raw = normalize_text(record.get("canonical_key", ""))
    elif dedupe_mode == "case_id":
        raw = normalize_text(record.get("case_id", ""))
    elif dedupe_mode == "family":
        raw = normalize_text(record.get("family_id", ""))
    else:
        raw = "||".join(
            [
                normalize_text(record.get("input", "")),
                normalize_text(record.get("answer", "")),
            ]
        )
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def dedupe_records_posthoc(records: list[dict], dedupe_mode: str) -> tuple[list[dict], int]:
    unique_records = []
    seen_keys = set()
    duplicates = 0

    for record in records:
        key = dedupe_key_from_record(record, dedupe_mode=dedupe_mode)
        if key in seen_keys:
            duplicates += 1
            continue
        seen_keys.add(key)
        unique_records.append(record)

    return unique_records, duplicates


def choose_worker_count(raw_workers: int | None) -> int:
    cpu_count = os.cpu_count() or 1
    if raw_workers is None or raw_workers <= 0:
        return cpu_count
    return max(1, raw_workers)


def module_levels(registry, module_id: str) -> list[str]:
    module = registry.get(module_id)
    if module is None:
        return []
    info = getattr(module, "MODULE_INFO", {})
    return list(info_get(info, "difficulty_levels", None) or DEFAULT_LEVELS)


def resolve_target_records(size: str | None = None, target_records: int | None = None) -> int:
    if target_records is not None:
        if target_records <= 0:
            raise ValueError("target_records must be greater than 0")
        return target_records

    size = size or "small"
    target = SIZE_PRESETS.get(size)
    if target is None:
        raise ValueError(f"Unknown size preset: {size}")
    return target


def normalize_mix(mix: dict[str, float], available_levels: list[str]) -> dict[str, float]:
    filtered = {level: max(0.0, float(mix.get(level, 0.0))) for level in available_levels}
    total = sum(filtered.values())
    if total <= 0:
        equal = 1.0 / max(len(available_levels), 1)
        return {level: equal for level in available_levels}
    return {level: value / total for level, value in filtered.items()}


def resolve_difficulty_mix(mix_name: str, available_levels: list[str]) -> dict[str, float]:
    if mix_name not in DEFAULT_DIFFICULTY_MIXES:
        raise ValueError(f"Unknown difficulty mix: {mix_name}")
    return normalize_mix(DEFAULT_DIFFICULTY_MIXES[mix_name], available_levels)


def allocate_integer_counts(total: int, weights_by_key: dict[str, float]) -> dict[str, int]:
    if total <= 0 or not weights_by_key:
        return {}

    normalized_total = sum(max(0.0, w) for w in weights_by_key.values())
    if normalized_total <= 0:
        keys = list(weights_by_key.keys())
        base = total // len(keys)
        rem = total % len(keys)
        return {key: base + (1 if i < rem else 0) for i, key in enumerate(keys)}

    normalized = {k: max(0.0, v) / normalized_total for k, v in weights_by_key.items()}
    raw = {k: total * normalized[k] for k in normalized}
    floored = {k: int(raw[k]) for k in raw}
    assigned = sum(floored.values())
    remainder = total - assigned

    order = sorted(raw.keys(), key=lambda k: (raw[k] - floored[k]), reverse=True)
    for i in range(remainder):
        floored[order[i % len(order)]] += 1
    return floored


def should_retry_after_round(unique_count: int, target_total: int, tolerance: float) -> bool:
    lower_bound = math.floor(target_total * (1.0 - tolerance))
    return unique_count < lower_bound

