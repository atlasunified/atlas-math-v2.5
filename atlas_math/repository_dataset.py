from __future__ import annotations

import json
import random
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

from atlas_math.cli_common import (
    allocate_integer_counts,
    attach_identity_fields,
    dedupe_records_posthoc,
    dedupe_keep_order,
    info_get,
    resolve_difficulty_mix,
    resolve_target_records,
    write_jsonl,
)
from atlas_math.splitting import SPLIT_MODES, audit_split_leakage, split_rows
from atlas_math.validation import validate_record


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            rows.append(json.loads(line))
    return rows


def _iter_manifest_paths(root: Path):
    for path in root.rglob("manifest.json"):
        yield path


def _matches(value: str, selected: set[str] | None) -> bool:
    return True if not selected else value in selected


def _sample_path(root: Path, repository_dir: str, sample_file: str) -> Path:
    sample_path = root / Path(sample_file).relative_to(repository_dir) if str(sample_file).startswith(repository_dir + "/") else Path(sample_file)
    if not sample_path.is_absolute():
        sample_path = (Path.cwd() / sample_path) if not sample_path.exists() else sample_path
    return sample_path


def _normalize_repository_row(row: dict[str, Any], *, module_id: str, topic_name: str, subtopic: str, generator: str, difficulty: str) -> dict[str, Any]:
    normalized = dict(row)
    normalized.setdefault("module_id", module_id)
    normalized.setdefault("topic", topic_name)
    normalized.setdefault("subtopic", subtopic)
    normalized.setdefault("generator", generator)
    normalized.setdefault("difficulty", difficulty)
    normalized.setdefault("source_mode", "repository")
    normalized.setdefault("generator_version", normalized.get("generator_version") or "v1")
    return attach_identity_fields(normalized)


def collect_repository_rows(
    repository_dir: str = "repository",
    topic: str | None = None,
    topics: list[str] | None = None,
    modules: list[str] | None = None,
    generators: list[str] | None = None,
    difficulties: list[str] | None = None,
    source_kind: str = "samples",
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    root = Path(repository_dir)
    normalized_topics = list(topics or [])
    if topic:
        normalized_topics.append(topic)
    selected_topics = set(dedupe_keep_order(normalized_topics)) or None
    selected_modules = set(modules or []) or None
    selected_generators = set(generators or []) or None
    selected_difficulties = set(difficulties or []) or None

    rows_by_difficulty: dict[str, list[dict[str, Any]]] = defaultdict(list)
    scanned_levels = 0
    matched_levels = 0
    manifests = 0

    for manifest_path in sorted(_iter_manifest_paths(root)):
        manifest = _read_json(manifest_path)
        manifests += 1
        module_id = str(manifest.get("module_id") or "")
        topic_name = str(manifest.get("topic") or "")
        generator = str(manifest.get("generator") or "")
        subtopic = str(manifest.get("subtopic") or "general")
        if not _matches(topic_name, selected_topics):
            continue
        if not _matches(module_id, selected_modules):
            continue
        if not _matches(generator, selected_generators):
            continue

        levels = manifest.get("levels") or {}
        for difficulty, level in levels.items():
            scanned_levels += 1
            if selected_difficulties and difficulty not in selected_difficulties:
                continue
            source_file = None
            if source_kind == "cases":
                source_file = level.get("cases_file")
            elif source_kind == "auto":
                source_file = level.get("cases_file") or level.get("sample_file")
            else:
                source_file = level.get("sample_file")

            if not source_file:
                continue
            sample_path = _sample_path(root, repository_dir, source_file)
            if not sample_path.exists():
                continue

            matched_levels += 1
            for row in _read_jsonl(sample_path):
                normalized = _normalize_repository_row(
                    row,
                    module_id=module_id,
                    topic_name=topic_name,
                    subtopic=subtopic,
                    generator=generator,
                    difficulty=difficulty,
                )
                rows_by_difficulty[difficulty].append(normalized)

    rows: list[dict[str, Any]] = []
    for difficulty in sorted(rows_by_difficulty.keys()):
        rows.extend(rows_by_difficulty[difficulty])

    meta = {
        "repository_dir": repository_dir,
        "scanned_levels": scanned_levels,
        "matched_levels": matched_levels,
        "manifests": manifests,
        "rows_by_difficulty": {k: len(v) for k, v in rows_by_difficulty.items()},
        "source_kind": source_kind,
    }
    return rows, meta


def _validate_rows(rows: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    validated: list[dict[str, Any]] = []
    invalid_rows: list[dict[str, Any]] = []
    error_counts: Counter[str] = Counter()
    for row in rows:
        normalized = attach_identity_fields(row)
        validation = validate_record(normalized)
        normalized["validation"] = validation
        if validation.get("is_valid"):
            validated.append(normalized)
        else:
            invalid_rows.append(normalized)
            for error in validation.get("errors", []):
                error_counts[str(error)] += 1
    return validated, {
        "rows_validated": len(validated),
        "rows_invalid": len(invalid_rows),
        "validation_error_counts": dict(error_counts),
        "validator_coverage": len(validated) + len(invalid_rows),
    }


def _identity_metrics(rows: list[dict[str, Any]]) -> dict[str, float]:
    total = max(1, len(rows))
    return {
        "canonical_key_coverage": sum(1 for row in rows if row.get("canonical_key")) / total,
        "case_id_coverage": sum(1 for row in rows if row.get("case_id")) / total,
        "family_id_coverage": sum(1 for row in rows if row.get("family_id")) / total,
        "split_group_key_coverage": sum(1 for row in rows if row.get("split_group_key")) / total,
    }


def build_dataset_from_repository(
    repository_dir: str = "repository",
    output: str = "outputs/repository_build.jsonl",
    topic: str | None = None,
    topics: list[str] | None = None,
    modules: list[str] | None = None,
    generators: list[str] | None = None,
    difficulties: list[str] | None = None,
    size: str | None = None,
    target_records: int | None = None,
    difficulty_mix_name: str = "balanced",
    dedupe_mode: str = "input_answer",
    shuffle: bool = True,
    seed: int = 42,
    source_kind: str = "samples",
) -> dict[str, Any]:
    rows, meta = collect_repository_rows(
        repository_dir=repository_dir,
        topic=topic,
        topics=topics,
        modules=modules,
        generators=generators,
        difficulties=difficulties,
        source_kind=source_kind,
    )

    rows_by_difficulty: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        rows_by_difficulty[str(row.get("difficulty") or "level_1")].append(row)

    available_levels = sorted(rows_by_difficulty.keys())
    requested_target = resolve_target_records(size, target_records)
    difficulty_mix = resolve_difficulty_mix(difficulty_mix_name, available_levels or ["level_1"])
    difficulty_targets = allocate_integer_counts(requested_target, difficulty_mix)

    rng = random.Random(seed)
    selected: list[dict[str, Any]] = []
    selected_by_difficulty: dict[str, int] = {}
    for difficulty in available_levels:
        items = list(rows_by_difficulty[difficulty])
        if shuffle:
            rng.shuffle(items)
        take = min(len(items), difficulty_targets.get(difficulty, 0))
        selected.extend(items[:take])
        selected_by_difficulty[difficulty] = take

    if shuffle:
        rng.shuffle(selected)

    deduped, duplicates_removed = dedupe_records_posthoc(selected, dedupe_mode)
    validated_rows, validation_summary = _validate_rows(deduped)
    write_jsonl(validated_rows, output)

    return {
        "available_records": sum(len(v) for v in rows_by_difficulty.values()),
        "selected_records": len(selected),
        "written_records": len(validated_rows),
        "duplicates_removed": duplicates_removed,
        "difficulty_targets": difficulty_targets,
        "selected_by_difficulty": selected_by_difficulty,
        "dedupe_mode": dedupe_mode,
        "shuffle": shuffle,
        "seed": seed,
        "source_kind": source_kind,
        **validation_summary,
        **_identity_metrics(validated_rows),
        **meta,
    }


def _hf_row(row: dict[str, Any], format_name: str) -> dict[str, Any]:
    row = attach_identity_fields(row)
    instruction = row.get("instruction", "")
    input_text = row.get("input", "")
    answer = row.get("answer", row.get("output", ""))

    common = {
        "difficulty": row.get("difficulty", ""),
        "topic": row.get("topic", ""),
        "subtopic": row.get("subtopic", ""),
        "module_id": row.get("module_id", ""),
        "generator": row.get("generator", ""),
        "sample_id": row.get("sample_id", ""),
        "case_id": row.get("case_id", ""),
        "canonical_key": row.get("canonical_key", ""),
        "family_id": row.get("family_id", ""),
        "template_id": row.get("template_id", ""),
        "split_group_key": row.get("split_group_key", ""),
        "validation": row.get("validation"),
    }

    if format_name == "chatml":
        user_content = instruction if not input_text else f"{instruction}\n\n{input_text}"
        return {
            "messages": [
                {"role": "user", "content": user_content},
                {"role": "assistant", "content": str(answer)},
            ],
            **common,
        }

    if format_name == "alpaca":
        return {
            "instruction": instruction,
            "input": input_text,
            "output": str(answer),
            **common,
        }

    return {
        "prompt": instruction if not input_text else f"{instruction}\n\n{input_text}",
        "response": str(answer),
        "instruction": instruction,
        "input": input_text,
        "answer": str(answer),
        **common,
    }


def export_hf_dataset_from_repository(
    repository_dir: str = "repository",
    output_dir: str = "outputs/hf_dataset",
    topic: str | None = None,
    topics: list[str] | None = None,
    modules: list[str] | None = None,
    generators: list[str] | None = None,
    difficulties: list[str] | None = None,
    train_ratio: float = 0.90,
    validation_ratio: float = 0.05,
    test_ratio: float = 0.05,
    dedupe_mode: str = "input_answer",
    shuffle: bool = True,
    seed: int = 42,
    format_name: str = "hf",
    source_kind: str = "samples",
    split_mode: str = "grouped_canonical",
) -> dict[str, Any]:
    total_ratio = train_ratio + validation_ratio + test_ratio
    if total_ratio <= 0:
        raise ValueError("train/validation/test ratios must sum to more than 0")
    if split_mode not in SPLIT_MODES:
        raise ValueError(f"Unknown split mode: {split_mode}")

    train_ratio = train_ratio / total_ratio
    validation_ratio = validation_ratio / total_ratio
    test_ratio = test_ratio / total_ratio

    rows, meta = collect_repository_rows(
        repository_dir=repository_dir,
        topic=topic,
        topics=topics,
        modules=modules,
        generators=generators,
        difficulties=difficulties,
        source_kind=source_kind,
    )
    deduped_rows, duplicates_removed = dedupe_records_posthoc(rows, dedupe_mode)
    validated_rows, validation_summary = _validate_rows(deduped_rows)

    if shuffle:
        random.Random(seed).shuffle(validated_rows)

    ratios = {"train": train_ratio, "validation": validation_ratio, "test": test_ratio}
    splits = split_rows(validated_rows, split_mode=split_mode, split_ratios=ratios, seed=seed)
    leakage = {
        "canonical_key": audit_split_leakage(splits, "canonical_key"),
        "case_id": audit_split_leakage(splits, "case_id"),
        "family_id": audit_split_leakage(splits, "family_id"),
    }

    root = Path(output_dir)
    root.mkdir(parents=True, exist_ok=True)

    paths = {}
    split_counts = {}
    for split_name, rows_for_split in splits.items():
        rendered = [_hf_row(row, format_name=format_name) for row in rows_for_split]
        path = root / f"{split_name}.jsonl"
        write_jsonl(rendered, path.as_posix())
        paths[split_name] = path.as_posix()
        split_counts[split_name] = len(rendered)

    dataset_dict = {
        "format": format_name,
        "splits": paths,
        "counts": split_counts,
        "repository_dir": repository_dir,
        "duplicates_removed": duplicates_removed,
        "dedupe_mode": dedupe_mode,
        "shuffle": shuffle,
        "seed": seed,
        "source_kind": source_kind,
        "split_mode": split_mode,
        "leakage_audit": leakage,
        **validation_summary,
        **_identity_metrics(validated_rows),
        **meta,
    }
    (root / "dataset_dict.json").write_text(json.dumps(dataset_dict, indent=2, ensure_ascii=False), encoding="utf-8")

    return {
        "output_dir": root.as_posix(),
        "dataset_dict": (root / "dataset_dict.json").as_posix(),
        "format": format_name,
        "counts": split_counts,
        "duplicates_removed": duplicates_removed,
        "dedupe_mode": dedupe_mode,
        "shuffle": shuffle,
        "seed": seed,
        "source_kind": source_kind,
        "split_mode": split_mode,
        "leakage_audit": leakage,
        **validation_summary,
        **_identity_metrics(validated_rows),
        **meta,
    }

