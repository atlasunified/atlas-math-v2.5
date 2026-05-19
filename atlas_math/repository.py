from __future__ import annotations

import csv
import hashlib
import json
import time
from pathlib import Path
from typing import Any

from atlas_math.cli_common import attach_identity_fields, dedupe_records_posthoc, info_get, module_levels, serialize_sample
from atlas_math.cli_config import DEFAULT_GENERATION_MODE
from atlas_math.cli_generation import call_generate, call_generate_structured, module_estimate_capacity, module_supports_structured
from atlas_math.registry import get_registry
from atlas_math.cli_dashboard import draw_dashboard, finish_dashboard, render_repository_export_dashboard


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames: list[str] = []
    seen: set[str] = set()
    for row in rows:
        for key in row.keys():
            if key not in seen:
                fieldnames.append(key)
                seen.add(key)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def to_posix(path: Path | str) -> str:
    return Path(path).as_posix() if isinstance(path, Path) else str(path).replace("\\", "/")


def stable_case_id(case: Any) -> str:
    payload = json.dumps(case, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def call_repository_spec(module, difficulty: str | None = None) -> dict[str, Any]:
    spec: dict[str, Any] = {}
    if not hasattr(module, "repository_spec"):
        return spec

    try:
        extra = module.repository_spec(difficulty=difficulty)
    except TypeError:
        extra = module.repository_spec()
    except Exception as exc:
        return {"repository_spec_error": f"{type(exc).__name__}: {exc}"}

    if not isinstance(extra, dict):
        return {"repository_spec_error": "repository_spec must return a dict"}
    return dict(extra)


def get_repository_iterator(module, difficulty: str):
    if hasattr(module, "iter_repository_cases"):
        try:
            iterator = module.iter_repository_cases(difficulty=difficulty)
        except TypeError:
            iterator = module.iter_repository_cases(difficulty)
        except Exception as exc:
            return None, f"{type(exc).__name__}: {exc}"

        if iterator is None:
            return None, None
        return iterator, None

    if module_supports_structured(module):
        capacity = module_estimate_capacity(module, difficulty)
        if capacity.get("quality") == "exact" and capacity.get("value") is not None:
            total = max(0, int(capacity["value"]))

            def _iter_fallback_cases():
                offset = 0
                batch_size = 256
                while offset < total:
                    chunk = call_generate_structured(
                        module,
                        count=min(batch_size, total - offset),
                        difficulty=difficulty,
                        worker_offset=offset,
                        worker_stride=1,
                    )
                    if not chunk:
                        break
                    for sample in chunk:
                        yield serialize_sample(sample, fmt="rich")
                    offset += len(chunk)

            return _iter_fallback_cases(), None

    return None, None


def split_repository_parts(module_id: str, info: dict[str, Any]) -> tuple[str, str, str]:
    topic = str(info_get(info, "topic", "unknown") or "unknown")
    raw_subtopic = str(info_get(info, "subtopic", "") or "").strip()
    tail = module_id[len(topic) + 1 :] if module_id.startswith(f"{topic}.") else module_id
    tail_parts = [part for part in tail.split(".") if part]

    generator = tail_parts[-1] if tail_parts else module_id.rsplit(".", 1)[-1]
    subtopic = ""

    if raw_subtopic:
        if "." in raw_subtopic:
            sub_parts = [part for part in raw_subtopic.split(".") if part]
            if sub_parts and sub_parts[-1] == generator:
                sub_parts = sub_parts[:-1]
            subtopic = "/".join(sub_parts)
        else:
            subtopic = raw_subtopic
    elif len(tail_parts) > 1:
        subtopic = "/".join(tail_parts[:-1])

    subtopic = subtopic.strip("/") or "general"
    return topic, subtopic, generator


def build_module_manifest(module, difficulty: str | None = None) -> dict[str, Any]:
    info = getattr(module, "MODULE_INFO", {})
    module_id = info_get(info, "module_id", "")
    topic, subtopic, generator = split_repository_parts(module_id, info)
    manifest = {
        "module_id": module_id,
        "name": info_get(info, "name", module_id),
        "topic": topic,
        "subtopic": subtopic,
        "generator": generator,
        "description": info_get(info, "description", ""),
        "difficulty_levels": list(info_get(info, "difficulty_levels", []) or []),
        "structured": module_supports_structured(module),
        "supports_zero": None,
        "supports_negative": None,
        "supports_positive": None,
        "estimated_combinations": None,
        "repository_mode": "sampled",
    }

    extra = call_repository_spec(module, difficulty=difficulty)
    if "enumeration_mode" in extra and "repository_mode" not in extra:
        extra["repository_mode"] = extra.pop("enumeration_mode")
    manifest.update(extra)
    return manifest


def _normalize_case_row(case: Any, difficulty: str) -> dict[str, Any]:
    row = dict(case) if isinstance(case, dict) else {"value": case}
    row.setdefault("difficulty", difficulty)
    row.setdefault("case_id", stable_case_id(row))
    if isinstance(row.get("metadata"), dict):
        meta = row["metadata"]
        row.setdefault("canonical_key", meta.get("canonical_key", ""))
        row.setdefault("family_id", meta.get("family") or meta.get("family_id") or "")
    return attach_identity_fields(row)




def _repository_progress_state(output_dir: str, module_total: int, level_total: int) -> dict[str, Any]:
    return {
        "output_dir": output_dir,
        "module_total": max(0, module_total),
        "module_index": 0,
        "level_total": max(0, level_total),
        "level_index": 0,
        "current_module": "",
        "current_level": "",
        "exact_level_count": 0,
        "sampled_level_count": 0,
        "sample_count_total": 0,
        "case_count_total": 0,
        "manifest_count": 0,
        "report_written": False,
        "start_time": time.time(),
        "last_draw": 0.0,
    }


def _maybe_draw_repository_progress(state: dict[str, Any], force: bool = False) -> None:
    now = time.time()
    if not force and (now - state.get("last_draw", 0.0)) < 0.1:
        return
    draw_dashboard(
        render_repository_export_dashboard(
            output_dir=state["output_dir"],
            module_total=state["module_total"],
            module_index=state["module_index"],
            level_total=state["level_total"],
            level_index=state["level_index"],
            current_module=state["current_module"],
            current_level=state["current_level"],
            exact_level_count=state["exact_level_count"],
            sampled_level_count=state["sampled_level_count"],
            sample_count_total=state["sample_count_total"],
            case_count_total=state["case_count_total"],
            manifest_count=state["manifest_count"],
            report_written=state["report_written"],
            start_time=state["start_time"],
        )
    )
    state["last_draw"] = now


def export_repository(
    output_dir: str = "repository",
    module_ids: list[str] | None = None,
    samples_per_level: int = 50,
    fmt: str = "rich",
    generation_mode: str = DEFAULT_GENERATION_MODE,
    cases_per_level: int | None = None,
    write_report: bool = True,
    progress: bool = False,
    sample_dedupe_mode: str = "input_answer",
    case_dedupe_mode: str = "full",
) -> dict[str, Any]:
    registry = get_registry()
    modules = registry.modules()
    selected_ids = sorted(modules.keys()) if not module_ids else list(module_ids)

    root = Path(output_dir)
    index_rows: list[dict[str, Any]] = []
    level_total = sum(len(module_levels(registry, module_id)) for module_id in selected_ids)
    progress_state = _repository_progress_state(str(root), len(selected_ids), level_total)

    if progress:
        _maybe_draw_repository_progress(progress_state, force=True)

    try:
        for module_pos, module_id in enumerate(selected_ids, start=1):
            module = registry.get(module_id)
            if module is None:
                continue

            progress_state["module_index"] = module_pos
            progress_state["current_module"] = module_id

            info = getattr(module, "MODULE_INFO", {})
            topic, subtopic, generator = split_repository_parts(module_id, info)
            module_dir = root / topic / subtopic / generator
            levels = module_levels(registry, module_id)

            module_manifest = build_module_manifest(module)
            module_manifest["levels"] = {}

            for difficulty in levels:
                progress_state["current_level"] = difficulty
                level_meta = build_module_manifest(module, difficulty=difficulty)
                level_manifest = {
                    "repository_mode": level_meta.get("repository_mode", "sampled"),
                    "estimated_combinations": level_meta.get("estimated_combinations"),
                    "supports_zero": level_meta.get("supports_zero"),
                    "supports_negative": level_meta.get("supports_negative"),
                    "supports_positive": level_meta.get("supports_positive"),
                    "sample_count": 0,
                    "cases_count": 0,
                    "unique_case_count": 0,
                    "coverage_ratio": None,
                }
                if "dimensions" in level_meta:
                    level_manifest["dimensions"] = level_meta["dimensions"]
                if "repository_spec_error" in level_meta:
                    level_manifest["repository_spec_error"] = level_meta["repository_spec_error"]

                raw_sample_rows: list[dict[str, Any]] = []
                sample_rows: list[dict[str, Any]] = []
                try:
                    samples = call_generate(
                        module,
                        count=max(0, samples_per_level),
                        difficulty=difficulty,
                        generation_mode=generation_mode,
                    )
                    raw_sample_rows = [attach_identity_fields(serialize_sample(sample, fmt=fmt)) for sample in samples]
                    sample_rows, duplicate_sample_count = dedupe_records_posthoc(raw_sample_rows, sample_dedupe_mode)
                except Exception as exc:
                    level_manifest["sample_export_error"] = f"{type(exc).__name__}: {exc}"
                    duplicate_sample_count = 0

                sample_path = module_dir / f"{difficulty}.jsonl"
                write_jsonl(sample_path, sample_rows)
                level_manifest["raw_sample_count"] = len(raw_sample_rows)
                level_manifest["sample_count"] = len(sample_rows)
                level_manifest["duplicate_sample_count"] = duplicate_sample_count
                level_manifest["sample_file"] = to_posix(sample_path)
                progress_state["sample_count_total"] += len(sample_rows)

                iterator, iterator_error = get_repository_iterator(module, difficulty)
                if iterator_error:
                    level_manifest["cases_export_error"] = iterator_error
                elif iterator is not None:
                    case_limit = None if cases_per_level is None else max(0, cases_per_level)
                    raw_case_rows: list[dict[str, Any]] = []
                    case_rows: list[dict[str, Any]] = []
                    try:
                        for idx, case in enumerate(iterator):
                            if case_limit is not None and idx >= case_limit:
                                break
                            raw_case_rows.append(_normalize_case_row(case, difficulty))
                        case_rows, duplicate_case_count = dedupe_records_posthoc(raw_case_rows, case_dedupe_mode)
                    except Exception as exc:
                        level_manifest["cases_export_error"] = f"{type(exc).__name__}: {exc}"
                        raw_case_rows = []
                        case_rows = []
                        duplicate_case_count = 0

                    unique_case_ids = {row["case_id"] for row in case_rows}
                    level_manifest["raw_cases_count"] = len(raw_case_rows)
                    level_manifest["cases_count"] = len(case_rows)
                    level_manifest["unique_case_count"] = len(unique_case_ids)
                    level_manifest["duplicate_case_count"] = duplicate_case_count
                    progress_state["case_count_total"] += len(unique_case_ids)
                    if case_rows:
                        cases_path = module_dir / f"cases_{difficulty}.jsonl"
                        write_jsonl(cases_path, case_rows)
                        level_manifest["cases_file"] = to_posix(cases_path)

                estimated = level_manifest.get("estimated_combinations")
                unique_case_count = level_manifest.get("unique_case_count", 0)
                if isinstance(estimated, int) and estimated > 0:
                    level_manifest["coverage_ratio"] = unique_case_count / estimated
                    level_manifest["missing_count"] = max(0, estimated - unique_case_count)
                    level_manifest["full_coverage"] = unique_case_count >= estimated
                else:
                    level_manifest["missing_count"] = None
                    level_manifest["full_coverage"] = False

                module_manifest["levels"][difficulty] = level_manifest
                progress_state["level_index"] += 1
                if level_manifest.get("repository_mode") == "sampled":
                    progress_state["sampled_level_count"] += 1
                else:
                    progress_state["exact_level_count"] += 1
                if progress:
                    _maybe_draw_repository_progress(progress_state)

            manifest_path = module_dir / "manifest.json"
            write_json(manifest_path, module_manifest)
            progress_state["manifest_count"] += 1

            index_rows.append(
                {
                    "module_id": module_id,
                    "topic": topic,
                    "subtopic": subtopic,
                    "generator": generator,
                    "path": to_posix(module_dir),
                    "levels": levels,
                    "structured": module_supports_structured(module),
                    "manifest_file": to_posix(manifest_path),
                }
            )

        index_path = root / "index.json"
        write_json(index_path, index_rows)
        result = {
            "output_dir": root.as_posix(),
            "module_count": len(index_rows),
            "index_file": index_path.as_posix(),
        }
        if write_report:
            from atlas_math.repository_report import write_repository_reports

            report_paths = write_repository_reports(output_dir)
            result.update(report_paths)
            progress_state["report_written"] = True

        if progress:
            _maybe_draw_repository_progress(progress_state, force=True)
        return result
    finally:
        if progress:
            _maybe_draw_repository_progress(progress_state, force=True)
            finish_dashboard()

