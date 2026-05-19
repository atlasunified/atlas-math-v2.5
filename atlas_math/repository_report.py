from __future__ import annotations

import csv
import json
from collections import defaultdict
from pathlib import Path
from typing import Any

from atlas_math.cli_common import fmt_int, fmt_pct
from atlas_math.cli_config import DEFAULT_LEVELS
from atlas_math.cli_dashboard import ANSI, LEVEL_COLORS, bar, retro_footer, retro_header, term_width


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _iter_manifest_paths(root: Path):
    for path in root.rglob("manifest.json"):
        yield path


def _level_row(manifest: dict[str, Any], difficulty: str, level: dict[str, Any]) -> dict[str, Any]:
    estimated = level.get("estimated_combinations")
    unique_case_count = level.get("unique_case_count", level.get("cases_count", 0))
    coverage_ratio = level.get("coverage_ratio")
    if coverage_ratio is None and isinstance(estimated, int) and estimated > 0:
        coverage_ratio = unique_case_count / estimated
    missing_count = level.get("missing_count")
    if missing_count is None and isinstance(estimated, int):
        missing_count = max(0, estimated - unique_case_count)

    return {
        "module_id": manifest.get("module_id"),
        "name": manifest.get("name"),
        "topic": manifest.get("topic"),
        "subtopic": manifest.get("subtopic"),
        "generator": manifest.get("generator"),
        "difficulty": difficulty,
        "structured": manifest.get("structured"),
        "repository_mode": level.get("repository_mode", manifest.get("repository_mode", "sampled")),
        "supports_zero": level.get("supports_zero", manifest.get("supports_zero")),
        "supports_negative": level.get("supports_negative", manifest.get("supports_negative")),
        "supports_positive": level.get("supports_positive", manifest.get("supports_positive")),
        "estimated_combinations": estimated,
        "raw_sample_count": level.get("raw_sample_count", level.get("sample_count", 0)),
        "sample_count": level.get("sample_count", 0),
        "duplicate_sample_count": level.get("duplicate_sample_count", 0),
        "raw_cases_count": level.get("raw_cases_count", level.get("cases_count", 0)),
        "cases_count": level.get("cases_count", 0),
        "unique_case_count": unique_case_count,
        "duplicate_case_count": level.get("duplicate_case_count", 0),
        "coverage_ratio": coverage_ratio,
        "missing_count": missing_count,
        "full_coverage": bool(level.get("full_coverage", False)),
        "sample_file": level.get("sample_file"),
        "cases_file": level.get("cases_file"),
        "manifest_file": manifest.get("manifest_file"),
    }


def analyze_repository(output_dir: str = "repository") -> dict[str, Any]:
    root = Path(output_dir)
    rows: list[dict[str, Any]] = []
    for path in sorted(_iter_manifest_paths(root)):
        manifest = _read_json(path)
        manifest["manifest_file"] = path.as_posix()
        for difficulty, level in (manifest.get("levels") or {}).items():
            rows.append(_level_row(manifest, difficulty, level))

    def bucket_factory():
        return {
            "levels": 0,
            "exact_levels": 0,
            "sampled_only_levels": 0,
            "raw_sample_count": 0,
            "sample_count": 0,
            "duplicate_sample_count": 0,
            "raw_cases_count": 0,
            "cases_count": 0,
            "unique_case_count": 0,
            "duplicate_case_count": 0,
            "estimated_combinations": 0,
            "known_coverage_levels": 0,
            "full_coverage_levels": 0,
        }

    by_difficulty: dict[str, dict[str, Any]] = defaultdict(bucket_factory)
    by_topic: dict[str, dict[str, Any]] = defaultdict(bucket_factory)

    totals = bucket_factory()
    totals.update({
        "modules": len({row["module_id"] for row in rows}),
        "levels": len(rows),
    })

    for row in rows:
        exact = row.get("repository_mode") != "sampled" and isinstance(row.get("estimated_combinations"), int)
        difficulty_bucket = by_difficulty[row["difficulty"]]
        topic_bucket = by_topic[row["topic"]]
        for bucket in (difficulty_bucket, topic_bucket, totals):
            bucket["levels"] += 1
            bucket["raw_sample_count"] += int(row.get("raw_sample_count") or 0)
            bucket["sample_count"] += int(row.get("sample_count") or 0)
            bucket["duplicate_sample_count"] += int(row.get("duplicate_sample_count") or 0)
            bucket["raw_cases_count"] += int(row.get("raw_cases_count") or 0)
            bucket["cases_count"] += int(row.get("cases_count") or 0)
            bucket["unique_case_count"] += int(row.get("unique_case_count") or 0)
            bucket["duplicate_case_count"] += int(row.get("duplicate_case_count") or 0)
            if exact:
                bucket["exact_levels"] += 1
                bucket["estimated_combinations"] += int(row.get("estimated_combinations") or 0)
                bucket["known_coverage_levels"] += 1
                if row.get("full_coverage"):
                    bucket["full_coverage_levels"] += 1
            else:
                bucket["sampled_only_levels"] += 1

    for bucket in [*by_difficulty.values(), *by_topic.values(), totals]:
        estimated = bucket["estimated_combinations"]
        bucket["coverage_ratio"] = None if estimated <= 0 else bucket["unique_case_count"] / estimated
        bucket["missing_count"] = None if estimated <= 0 else max(0, estimated - bucket["unique_case_count"])

    quality = {
        "sample_duplicate_rate": 0.0 if totals["raw_sample_count"] <= 0 else totals["duplicate_sample_count"] / max(1, totals["raw_sample_count"]),
        "case_duplicate_rate": 0.0 if totals["raw_cases_count"] <= 0 else totals["duplicate_case_count"] / max(1, totals["raw_cases_count"]),
        "coverage_ratio": totals.get("coverage_ratio"),
        "full_coverage_level_ratio": 0.0 if totals["exact_levels"] <= 0 else totals["full_coverage_levels"] / max(1, totals["exact_levels"]),
    }

    return {
        "repository_dir": root.as_posix(),
        "summary": totals,
        "quality": quality,
        "by_difficulty": dict(by_difficulty),
        "by_topic": dict(by_topic),
        "rows": rows,
    }


def _write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")


def _write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
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


def write_repository_reports(output_dir: str = "repository") -> dict[str, str]:
    root = Path(output_dir)
    report = analyze_repository(output_dir)
    report_json = root / "coverage_report.json"
    report_csv = root / "coverage_report.csv"
    _write_json(report_json, report)
    _write_csv(report_csv, report["rows"])
    return {
        "report_json": report_json.as_posix(),
        "report_csv": report_csv.as_posix(),
    }


def render_repository_dashboard(report: dict[str, Any]) -> str:
    width = max(100, min(term_width(), 160))
    summary = report["summary"]
    quality = report.get("quality", {})
    inner_width = width - 4
    lines = [retro_header("ATLAS MATH // REPOSITORY COVERAGE", width)]

    coverage_ratio = summary.get("coverage_ratio")
    if coverage_ratio is None:
        coverage_text = "exact-only" if summary.get("exact_levels", 0) > 0 else "n/a (sampled repository)"
    else:
        coverage_text = fmt_pct(coverage_ratio)
    lines.append(
        f"{ANSI['bright_magenta']}║{ANSI['reset']} "
        f"{ANSI['bright_cyan']}MODULES{ANSI['reset']} {fmt_int(summary['modules']):>8}   "
        f"{ANSI['bright_white']}LEVELS{ANSI['reset']} {fmt_int(summary['levels']):>8}   "
        f"{ANSI['bright_green']}EXACT{ANSI['reset']} {fmt_int(summary['exact_levels']):>8}   "
        f"{ANSI['bright_yellow']}SAMPLED{ANSI['reset']} {fmt_int(summary['sampled_only_levels']):>8}   "
        f"{ANSI['bright_red']}FULL_COV{ANSI['reset']} {fmt_int(summary['full_coverage_levels']):>8}"
    )
    lines.append(
        f"{ANSI['bright_magenta']}║{ANSI['reset']} "
        f"{ANSI['bright_white']}KNOWN_EXACT_CASES{ANSI['reset']} {fmt_int(summary['estimated_combinations']):>10}   "
        f"{ANSI['bright_white']}EXPORTED{ANSI['reset']} {fmt_int(summary['unique_case_count']):>10}   "
        f"{ANSI['bright_white']}MISSING{ANSI['reset']} {fmt_int(summary['missing_count'] or 0):>10}   "
        f"{ANSI['bright_white']}COVERAGE{ANSI['reset']} {coverage_text:>8}"
    )
    lines.append(
        f"{ANSI['bright_magenta']}║{ANSI['reset']} "
        f"{ANSI['bright_white']}SAMPLES{ANSI['reset']} {fmt_int(summary['sample_count']):>11}   "
        f"{ANSI['bright_white']}DUPE_S{ANSI['reset']} {fmt_int(summary['duplicate_sample_count']):>10}   "
        f"{ANSI['bright_white']}CASES{ANSI['reset']} {fmt_int(summary['cases_count']):>13}   "
        f"{ANSI['bright_white']}DUPE_C{ANSI['reset']} {fmt_int(summary['duplicate_case_count']):>10}"
    )
    lines.append(
        f"{ANSI['bright_magenta']}║{ANSI['reset']} "
        f"{ANSI['bright_white']}PROGRESS{ANSI['reset']} "
        f"{bar(0.0 if coverage_ratio is None else coverage_ratio, max(20, inner_width - 52), ANSI['bright_green'], ANSI['bright_black'])} "
        f"{coverage_text} {ANSI['bright_magenta']}║{ANSI['reset']}"
    )
    lines.append(
        f"{ANSI['bright_magenta']}║{ANSI['reset']} "
        f"{ANSI['bright_white']}QUALITY{ANSI['reset']} dupS={fmt_pct(quality.get('sample_duplicate_rate', 0.0)):>8} "
        f"dupC={fmt_pct(quality.get('case_duplicate_rate', 0.0)):>8} "
        f"full_cov={fmt_pct(quality.get('full_coverage_level_ratio', 0.0)):>8}"
    )
    lines.append(
        f"{ANSI['bright_magenta']}║{ANSI['reset']} "
        f"{ANSI['bright_yellow']}Difficulty coverage and export counts{ANSI['reset']}"
    )

    for difficulty in DEFAULT_LEVELS:
        if difficulty not in report["by_difficulty"]:
            continue
        bucket = report["by_difficulty"][difficulty]
        ratio = bucket.get("coverage_ratio")
        color = LEVEL_COLORS.get(difficulty, ANSI["bright_white"])
        bar_ratio = 0.0 if ratio is None else ratio
        ratio_text = fmt_pct(ratio) if ratio is not None else ("exact-only" if bucket.get("exact_levels", 0) > 0 else "n/a")
        stats = (
            f"exact_levels={bucket['exact_levels']:<3} sampled_only={bucket['sampled_only_levels']:<3}  "
            f"exact={fmt_int(bucket['unique_case_count']):>7}/{fmt_int(bucket['estimated_combinations']):<7}  "
            f"samples={fmt_int(bucket['sample_count']):>7}  dupS={fmt_int(bucket['duplicate_sample_count']):>6}  "
            f"dupC={fmt_int(bucket['duplicate_case_count']):>6}  full={bucket['full_coverage_levels']}/{bucket['exact_levels']}"
        )
        lines.append(
            f"{ANSI['bright_magenta']}║{ANSI['reset']} "
            f"{color}{difficulty:<10}{ANSI['reset']} "
            f"C:{bar(bar_ratio, max(12, min(24, inner_width // 5)), color, ANSI['bright_black'])} "
            f"{ratio_text:>22}  "
            f"{ANSI['dim']}{stats}{ANSI['reset']} "
            f"{ANSI['bright_magenta']}║{ANSI['reset']}"
        )

    lines.append(retro_footer(width))
    return "\n".join(lines)

