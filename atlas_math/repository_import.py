from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Iterable, TextIO

from atlas_math.cli_common import dedupe_keep_order
from atlas_math.repository import split_repository_parts, to_posix, write_json


def _iter_jsonl(path: Path):
    with path.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            raw = line.strip()
            if not raw:
                continue
            try:
                yield json.loads(raw)
            except json.JSONDecodeError as exc:
                raise ValueError(f"Invalid JSONL at {path}:{line_number}: {exc}") from exc


def _matches(value: str, selected: set[str] | None) -> bool:
    return True if not selected else value in selected


def _normalize_difficulty(row: dict[str, Any]) -> str:
    raw = str(row.get("difficulty") or row.get("difficulty_level") or "level_1").strip()
    if not raw:
        return "level_1"
    if raw.startswith("level_"):
        return raw
    if raw.isdigit():
        return f"level_{raw}"
    return raw


def _normalize_module_id(row: dict[str, Any]) -> str:
    module_id = str(row.get("module_id") or "").strip()
    if module_id:
        return module_id

    topic = str(row.get("topic") or "unknown").strip() or "unknown"
    subtopic = str(row.get("subtopic") or "general").strip().strip("/") or "general"
    generator = str(row.get("generator") or row.get("name") or "imported").strip() or "imported"

    dotted_subtopic = ".".join(part for part in subtopic.split("/") if part and part != "general")
    return ".".join(part for part in [topic, dotted_subtopic, generator] if part)


def _normalize_row(row: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(row, dict):
        raise TypeError(f"Expected dict rows in dataset import, got {type(row).__name__}")

    normalized = dict(row)
    module_id = _normalize_module_id(normalized)
    normalized["module_id"] = module_id

    info = {
        "topic": normalized.get("topic", "unknown"),
        "subtopic": normalized.get("subtopic", "general"),
    }
    topic, subtopic, generator = split_repository_parts(module_id, info)

    normalized["topic"] = topic
    normalized["subtopic"] = subtopic
    normalized["generator"] = generator
    normalized["difficulty"] = _normalize_difficulty(normalized)
    return normalized


def _open_bucket_writer(path: Path) -> TextIO:
    path.parent.mkdir(parents=True, exist_ok=True)
    return path.open("a", encoding="utf-8")


def _load_json(path: Path, default):
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def _load_existing_state(root: Path) -> tuple[dict[tuple[str, str, str], dict[str, Any]], list[dict[str, Any]]]:
    manifest_map: dict[tuple[str, str, str], dict[str, Any]] = {}
    index_rows = _load_json(root / "index.json", [])
    for manifest_path in root.rglob("manifest.json"):
        manifest = _load_json(manifest_path, {})
        key = (
            str(manifest.get("topic") or ""),
            str(manifest.get("subtopic") or ""),
            str(manifest.get("generator") or manifest.get("name") or ""),
        )
        if any(not part for part in key):
            continue
        manifest_map[key] = manifest
    return manifest_map, index_rows


def _ensure_index_row(index_rows: list[dict[str, Any]], key: tuple[str, str, str], module_dir: Path, manifest: dict[str, Any]) -> None:
    for row in index_rows:
        if (
            str(row.get("topic") or ""),
            str(row.get("subtopic") or ""),
            str(row.get("generator") or ""),
        ) == key:
            row["path"] = to_posix(module_dir)
            row["manifest_file"] = to_posix(module_dir / "manifest.json")
            row["levels"] = sorted((manifest.get("levels") or {}).keys())
            row["module_id"] = manifest.get("module_id")
            return

    index_rows.append(
        {
            "module_id": manifest.get("module_id"),
            "topic": key[0],
            "subtopic": key[1],
            "generator": key[2],
            "path": to_posix(module_dir),
            "levels": sorted((manifest.get("levels") or {}).keys()),
            "structured": False,
            "manifest_file": to_posix(module_dir / "manifest.json"),
        }
    )


def _write_state(root: Path, manifest_map: dict[tuple[str, str, str], dict[str, Any]], index_rows: list[dict[str, Any]]) -> None:
    for key, manifest in manifest_map.items():
        module_dir = root / key[0] / key[1] / key[2]
        manifest["difficulty_levels"] = sorted(dedupe_keep_order(manifest.get("difficulty_levels") or []))
        write_json(module_dir / "manifest.json", manifest)
    write_json(root / "index.json", index_rows)


def _is_dataset_jsonl(path: Path) -> bool:
    if not path.is_file():
        return False
    if path.suffix.lower() != ".jsonl":
        return False
    lowered = path.name.lower()
    if lowered.startswith("."):
        return False
    if lowered.endswith(".tmp.jsonl"):
        return False
    return True


def _resolve_dataset_files(dataset_path: Path) -> list[Path]:
    if dataset_path.is_file():
        return [dataset_path]

    if not dataset_path.is_dir():
        raise FileNotFoundError(f"Dataset not found: {dataset_path}")

    dataset_dict = dataset_path / "dataset_dict.json"
    if dataset_dict.exists():
        try:
            payload = json.loads(dataset_dict.read_text(encoding="utf-8"))
        except Exception:
            payload = {}
        splits = payload.get("splits") or {}
        resolved: list[Path] = []
        for raw_path in splits.values():
            path = Path(str(raw_path))
            if not path.is_absolute():
                path = dataset_path / path.name if not path.exists() else path
            if path.exists() and _is_dataset_jsonl(path):
                resolved.append(path)
        if resolved:
            return dedupe_keep_order(resolved)

    candidates = [
        path for path in sorted(dataset_path.rglob("*.jsonl"))
        if _is_dataset_jsonl(path)
    ]
    if candidates:
        return candidates

    raise FileNotFoundError(
        f"No dataset JSONL files found under {dataset_path}. "
        f"Point to a .jsonl file, or to a directory containing JSONL dataset files."
    )


def _auto_chunk_size(paths: list[Path]) -> int:
    total_bytes = 0
    for path in paths:
        try:
            total_bytes += path.stat().st_size
        except OSError:
            continue
    if total_bytes <= 25 * 1024 * 1024:
        return 50000
    if total_bytes <= 250 * 1024 * 1024:
        return 100000
    return 250000


def import_repository_from_dataset(
    dataset: str,
    output_dir: str = "repository",
    topic: str | None = None,
    topics: list[str] | None = None,
    modules: list[str] | None = None,
    difficulties: list[str] | None = None,
    chunk_size: int | None = 250000,
    progress: bool = False,
    write_report: bool = True,
) -> dict[str, Any]:
    dataset_path = Path(dataset)
    if not dataset_path.exists():
        raise FileNotFoundError(f"Dataset not found: {dataset}")

    dataset_files = _resolve_dataset_files(dataset_path)
    resolved_chunk_size = max(1, chunk_size) if chunk_size and chunk_size > 0 else _auto_chunk_size(dataset_files)

    root = Path(output_dir)
    root.mkdir(parents=True, exist_ok=True)

    selected_topics = set(dedupe_keep_order(list(topics or []) + ([topic] if topic else []))) or None
    selected_modules = set(modules or []) or None
    selected_difficulties = set(difficulties or []) or None

    manifest_map, index_rows = _load_existing_state(root)
    rows_read = 0
    rows_written = 0
    chunks_processed = 0

    bucket_handles: dict[tuple[str, str, str, str], TextIO] = {}
    rows_in_chunk = 0

    try:
        for input_path in dataset_files:
            if progress:
                print(f"[repository-import] reading {input_path}")
            for raw_row in _iter_jsonl(input_path):
                rows_read += 1
                normalized = _normalize_row(raw_row)

                topic_name = str(normalized["topic"])
                subtopic_name = str(normalized["subtopic"])
                generator_name = str(normalized["generator"])
                module_id = str(normalized["module_id"])
                difficulty_name = str(normalized["difficulty"])

                if not _matches(topic_name, selected_topics):
                    continue
                if not _matches(module_id, selected_modules):
                    continue
                if not _matches(difficulty_name, selected_difficulties):
                    continue

                module_dir = root / topic_name / subtopic_name / generator_name
                manifest_key = (topic_name, subtopic_name, generator_name)
                manifest = manifest_map.get(manifest_key)
                if manifest is None:
                    manifest = {
                        "module_id": module_id,
                        "name": generator_name,
                        "topic": topic_name,
                        "subtopic": subtopic_name,
                        "generator": generator_name,
                        "difficulty_levels": [],
                        "structured": False,
                        "supports_zero": None,
                        "supports_negative": None,
                        "supports_positive": None,
                        "estimated_combinations": None,
                        "repository_mode": "imported",
                        "levels": {},
                    }
                    manifest_map[manifest_key] = manifest

                _ensure_index_row(index_rows, manifest_key, module_dir, manifest)

                if difficulty_name not in manifest["difficulty_levels"]:
                    manifest["difficulty_levels"].append(difficulty_name)

                level = manifest["levels"].get(difficulty_name)
                if level is None:
                    sample_path = module_dir / f"{difficulty_name}.jsonl"
                    level = {
                        "repository_mode": "imported",
                        "estimated_combinations": None,
                        "supports_zero": None,
                        "supports_negative": None,
                        "supports_positive": None,
                        "sample_count": 0,
                        "raw_sample_count": 0,
                        "duplicate_sample_count": 0,
                        "cases_count": 0,
                        "unique_case_count": 0,
                        "coverage_ratio": None,
                        "missing_count": None,
                        "full_coverage": False,
                        "sample_file": to_posix(sample_path),
                    }
                    manifest["levels"][difficulty_name] = level

                bucket_key = (topic_name, subtopic_name, generator_name, difficulty_name)
                handle = bucket_handles.get(bucket_key)
                if handle is None:
                    handle = _open_bucket_writer(Path(level["sample_file"]))
                    bucket_handles[bucket_key] = handle

                handle.write(json.dumps(normalized, ensure_ascii=False) + "\n")
                level["sample_count"] += 1
                level["raw_sample_count"] += 1
                level["cases_count"] = level.get("cases_count", 0) + 1
                level["unique_case_count"] = level.get("unique_case_count", 0) + 1
                rows_written += 1
                rows_in_chunk += 1

                if progress and rows_read % 100000 == 0:
                    print(
                        f"[repository-import] rows_read={rows_read} rows_written={rows_written} "
                        f"generators={len(manifest_map)} chunks={chunks_processed}"
                    )

                if rows_in_chunk >= resolved_chunk_size:
                    for open_handle in bucket_handles.values():
                        open_handle.close()
                    bucket_handles.clear()
                    _write_state(root, manifest_map, index_rows)
                    chunks_processed += 1
                    rows_in_chunk = 0

        if rows_in_chunk > 0:
            chunks_processed += 1
    finally:
        for open_handle in bucket_handles.values():
            open_handle.close()

    _write_state(root, manifest_map, index_rows)

    result = {
        "dataset": dataset_path.as_posix(),
        "dataset_files": [path.as_posix() for path in dataset_files],
        "output_dir": root.as_posix(),
        "index_file": (root / "index.json").as_posix(),
        "module_count": len(index_rows),
        "level_count": sum(len(manifest.get("levels", {})) for manifest in manifest_map.values()),
        "rows_read": rows_read,
        "rows_written": rows_written,
        "chunks_processed": chunks_processed,
        "chunk_size": resolved_chunk_size,
        "chunk_size_mode": "auto" if not chunk_size or chunk_size <= 0 else "manual",
        "topic": topic,
        "topics": dedupe_keep_order(list(topics or []) + ([topic] if topic else [])),
        "modules": dedupe_keep_order(modules or []),
        "difficulties": dedupe_keep_order(difficulties or []),
    }

    if write_report:
        from atlas_math.repository_report import write_repository_reports
        result.update(write_repository_reports(root.as_posix()))

    return result

