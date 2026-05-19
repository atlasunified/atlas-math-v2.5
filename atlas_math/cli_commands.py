from __future__ import annotations

import argparse
import json
from pathlib import Path

from atlas_math.cli_common import clamp, dedupe_keep_order, fmt_int, info_get, resolve_target_records
from atlas_math.cli_config import (
    DEFAULT_DEDUPE_MODE,
    DEFAULT_DIFFICULTY_MIXES,
    DEFAULT_EXHAUSTION_PATIENCE,
    DEFAULT_GENERATION_MODE,
    DEFAULT_MAX_BATCH_SIZE,
    DEFAULT_MAX_ROUNDS,
    DEFAULT_MIN_YIELD_RATIO,
    DEFAULT_TARGET_TOLERANCE,
)
from atlas_math.cli_generation import estimate_record_count, generate_from_modules, module_supports_structured
from atlas_math.registry import get_registry
from atlas_math.repository import export_repository
from atlas_math.repository_dataset import build_dataset_from_repository, export_hf_dataset_from_repository
from atlas_math.repository_report import analyze_repository, render_repository_dashboard, write_repository_reports


def cmd_list(as_json: bool = False):
    registry = get_registry()
    modules = registry.modules()

    if as_json:
        payload = []
        for module_id, module in modules.items():
            info = getattr(module, "MODULE_INFO", {})
            payload.append(
                {
                    "module_id": module_id,
                    "name": info_get(info, "name", module_id),
                    "topic": info_get(info, "topic", "unknown"),
                    "difficulty_levels": info_get(info, "difficulty_levels", []),
                    "structured": module_supports_structured(module),
                }
            )
        print(json.dumps(payload, indent=2))
        return

    print("\nRegistered modules:\n")
    for module_id, module in modules.items():
        info = getattr(module, "MODULE_INFO", {})
        levels = info_get(info, "difficulty_levels", [])
        levels_text = ", ".join(levels) if levels else "n/a"
        structured = "structured" if module_supports_structured(module) else "random-only"
        print(
            f"- {module_id} | {info_get(info, 'name', module_id)} | "
            f"topic={info_get(info, 'topic', 'unknown')} | "
            f"levels={levels_text} | mode={structured}"
        )

    errors = registry.errors()
    if errors:
        print("\n\nSkipped modules with import errors:\n")
        for name, err in errors.items():
            print(f"- {name}: {err}")


def resolve_module_ids(registry, modules=None, topic=None, topics=None):
    if modules:
        return dedupe_keep_order(modules)

    selected_topics = []
    if topic:
        selected_topics = sorted(registry.topics()) if topic == "all" else [topic]
    elif topics:
        selected_topics = sorted(registry.topics()) if "all" in topics else topics
    else:
        selected_topics = sorted(registry.topics())

    module_ids = []
    for selected_topic in selected_topics:
        module_ids.extend(sorted(registry.modules_by_topic(selected_topic).keys()))
    return dedupe_keep_order(module_ids)


def print_build_plan(args, module_ids, estimate, worker_count, tolerance):
    print(
        f"Planned build: target_unique={'run_to_completion' if args.run_to_completion else resolve_target_records(args.size, args.target_records)} "
        f"with est_raw_round1={estimate['estimated_records']} across "
        f"{estimate['module_count']} module(s) and {estimate['unit_count']} module/difficulty bucket(s). "
        f"Structured={estimate['structured_bucket_count']}/{estimate['unit_count']}. "
        f"Difficulty mix={args.difficulty_mix}. Generation mode={args.generation_mode}. "
        f"Workers={worker_count}. Post-hoc dedupe={args.dedupe_mode}. "
        f"Tolerance=±{tolerance:.0%}. Max rounds={max(1, args.max_rounds)}."
    )
    print(
        f"Bucket summary: total={estimate['unit_count']} known_capacity={estimate['known_capacity_bucket_count']} "
        f"unknown_capacity={estimate['unknown_capacity_bucket_count']} structured={estimate['structured_bucket_count']}."
    )
    if args.run_to_completion and estimate.get("skipped_non_exact_bucket_count", 0):
        print(
            f"Run-to-completion will skip {estimate['skipped_non_exact_bucket_count']} bucket(s) without exact finite capacity."
        )
    if not module_ids:
        print("[warn] no modules matched the selected topic/module filters.")


def run_build_from_args(args):
    registry = get_registry()
    module_ids = resolve_module_ids(registry, modules=args.modules, topic=args.topic, topics=args.topics)

    estimate = estimate_record_count(
        registry,
        module_ids,
        size=args.size,
        target_records=args.target_records,
        difficulty_mix_name=args.difficulty_mix,
        run_to_completion=args.run_to_completion,
    )

    worker_count = args.workers
    tolerance = args.target_tolerance
    if tolerance > 1:
        tolerance = tolerance / 100.0
    tolerance = clamp(tolerance, 0.0, 0.50)
    print_build_plan(args, module_ids, estimate, worker_count or 0, tolerance)

    count = generate_from_modules(
        module_ids,
        size=args.size,
        target_records=args.target_records,
        fmt=args.fmt,
        output=args.output,
        progress=args.progress,
        dedupe=True,
        dedupe_mode=args.dedupe_mode,
        workers=args.workers,
        max_batch_size=max(1, args.max_batch_size),
        difficulty_mix_name=args.difficulty_mix,
        min_yield_ratio=max(0.0, min(1.0, args.min_yield_ratio)),
        exhaustion_patience=max(1, args.exhaustion_patience),
        target_tolerance=tolerance,
        max_rounds=max(1, args.max_rounds),
        generation_mode=args.generation_mode,
        run_to_completion=args.run_to_completion,
    )
    print(f"Wrote {count} records to {args.output}")
    return 0




def run_repository_build_from_args(args):
    result = build_dataset_from_repository(
        repository_dir=args.repository_dir,
        output=args.output,
        topic=args.topic,
        topics=args.topics,
        modules=args.modules,
        generators=args.generators,
        difficulties=args.difficulties,
        size=args.size,
        target_records=args.target_records,
        difficulty_mix_name=args.difficulty_mix,
        dedupe_mode=args.dedupe_mode,
        shuffle=args.shuffle,
        seed=args.seed,
        source_kind=args.source_kind,
    )

    requested_target = resolve_target_records(args.size, args.target_records)
    selected_topics = dedupe_keep_order(list(args.topics or []) + ([args.topic] if args.topic else []))
    print(
        f"Planned repository build: target_unique={requested_target} from repository={args.repository_dir} \
with available_records={result['available_records']} across matched_levels={result['matched_levels']} and manifests={result['manifests']}. \
Difficulty mix={args.difficulty_mix}. Source={args.source_kind}. Post-hoc dedupe={args.dedupe_mode}. Shuffle={'yes' if args.shuffle else 'no'}. Seed={args.seed}."
    )
    print(
        f"Repository filters: topics={selected_topics or ['all']} modules={args.modules or ['all']} \
 generators={args.generators or ['all']} difficulties={args.difficulties or ['all']}."
    )
    print(
        f"Selection summary: selected={result.get('selected_records', 0)} written={result['written_records']} \
 duplicates_removed={result['duplicates_removed']}."
    )
    for level in sorted(result.get('selected_by_difficulty', {})):
        print(
            f"  - {level}: target={result['difficulty_targets'].get(level, 0)} \
selected={result['selected_by_difficulty'].get(level, 0)}"
        )
    print(f"Wrote {result['written_records']} records to {args.output}")
    return 0


def run_hf_export_from_args(args):
    result = export_hf_dataset_from_repository(
        repository_dir=args.repository_dir,
        output_dir=args.output_dir,
        topic=args.topic,
        topics=args.topics,
        modules=args.modules,
        generators=args.generators,
        difficulties=args.difficulties,
        train_ratio=args.train_ratio,
        validation_ratio=args.validation_ratio,
        test_ratio=args.test_ratio,
        dedupe_mode=args.dedupe_mode,
        shuffle=args.shuffle,
        seed=args.seed,
        format_name=args.format_name,
        source_kind=args.source_kind,
        split_mode=args.split_mode,
    )
    print(json.dumps(result, indent=2))
    return 0

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="atlas-math")
    subparsers = parser.add_subparsers(dest="command")

    list_parser = subparsers.add_parser("list")
    list_parser.add_argument("--json", action="store_true")

    build_parser = subparsers.add_parser("build")
    build_parser.add_argument("--topic", default=None)
    build_parser.add_argument("--topics", nargs="*", default=None)
    build_parser.add_argument("--modules", nargs="*", default=None)
    build_parser.add_argument("--size", default="small", choices=["small", "medium", "large", "full"], help="Preset total target unique dataset size.")
    build_parser.add_argument("--target-records", type=int, default=None, help="Exact total target unique records after deduplication. Overrides --size.")
    build_parser.add_argument("--difficulty-mix", default="balanced", choices=list(DEFAULT_DIFFICULTY_MIXES.keys()), help="How round targets are distributed across difficulty levels.")
    build_parser.add_argument("--generation-mode", default=DEFAULT_GENERATION_MODE, choices=["auto", "structured", "random"], help="Prefer structured laddered generation when modules support it.")
    build_parser.add_argument("--format", dest="fmt", default="clean", choices=["clean", "extended", "rich"])
    build_parser.add_argument("--run-to-completion", action="store_true", help="For structured generators with exact capacity, enumerate every available case instead of targeting a preset size.")
    build_parser.add_argument("--output", default="outputs/output.jsonl")
    build_parser.add_argument("--progress", action="store_true")
    build_parser.add_argument("--dedupe-mode", choices=["input_answer", "input_only", "full", "canonical", "case_id", "family"], default=DEFAULT_DEDUPE_MODE, help="How post-hoc deduplication determines uniqueness.")
    build_parser.add_argument("--workers", type=int, default=None, help="Number of worker processes. Default: all CPUs.")
    build_parser.add_argument("--max-batch-size", type=int, default=DEFAULT_MAX_BATCH_SIZE, help="Upper bound for adaptive per-job chunk sizing. Actual chunk sizes are auto-detected at runtime.")
    build_parser.add_argument("--min-yield-ratio", type=float, default=DEFAULT_MIN_YIELD_RATIO, help="Mark a bucket unhealthy when its approximate unique/raw rate falls below this threshold.")
    build_parser.add_argument("--exhaustion-patience", type=int, default=DEFAULT_EXHAUSTION_PATIENCE, help="How many low-yield rounds before a bucket is treated as exhausted.")
    build_parser.add_argument("--target-tolerance", type=float, default=DEFAULT_TARGET_TOLERANCE, help="Acceptable miss window around target. 0.05 means ±5%%.")
    build_parser.add_argument("--max-rounds", type=int, default=DEFAULT_MAX_ROUNDS, help="Maximum number of generation rounds including retries.")

    repository_parser = subparsers.add_parser("repository")
    repository_parser.add_argument("--topic", default=None)
    repository_parser.add_argument("--topics", nargs="*", default=None)
    repository_parser.add_argument("--modules", nargs="*", default=None)
    repository_parser.add_argument("--output-dir", default="repository")
    repository_parser.add_argument("--samples-per-level", type=int, default=50)
    repository_parser.add_argument("--cases-per-level", type=int, default=None)
    repository_parser.add_argument("--format", dest="fmt", default="rich", choices=["clean", "extended", "rich"])
    repository_parser.add_argument("--generation-mode", default=DEFAULT_GENERATION_MODE, choices=["auto", "structured", "random"])
    repository_parser.add_argument("--progress", action="store_true")

    repository_build_parser = subparsers.add_parser("repository-build")
    repository_build_parser.add_argument("--repository-dir", default="repository")
    repository_build_parser.add_argument("--topic", default=None)
    repository_build_parser.add_argument("--topics", nargs="*", default=None)
    repository_build_parser.add_argument("--modules", nargs="*", default=None)
    repository_build_parser.add_argument("--generators", nargs="*", default=None)
    repository_build_parser.add_argument("--difficulties", nargs="*", default=None)
    repository_build_parser.add_argument("--size", default="small", choices=["small", "medium", "large", "full"], help="Preset total target unique dataset size.")
    repository_build_parser.add_argument("--target-records", type=int, default=None, help="Exact total target unique records after deduplication. Overrides --size.")
    repository_build_parser.add_argument("--difficulty-mix", default="balanced", choices=list(DEFAULT_DIFFICULTY_MIXES.keys()), help="How selected repository rows are distributed across difficulty levels.")
    repository_build_parser.add_argument("--dedupe-mode", choices=["input_answer", "input_only", "full", "canonical", "case_id", "family"], default=DEFAULT_DEDUPE_MODE, help="How post-hoc deduplication determines uniqueness.")
    repository_build_parser.add_argument("--shuffle", dest="shuffle", action="store_true")
    repository_build_parser.add_argument("--no-shuffle", dest="shuffle", action="store_false")
    repository_build_parser.set_defaults(shuffle=True)
    repository_build_parser.add_argument("--seed", type=int, default=42)
    repository_build_parser.add_argument("--output", default="outputs/repository_build.jsonl")
    repository_build_parser.add_argument("--source-kind", default="samples", choices=["samples", "cases", "auto"], help="Use sampled rows, exported case rows, or prefer cases when available.")
    repository_build_parser.add_argument("--split-mode", default="grouped_canonical", choices=["random", "grouped_canonical", "grouped_case", "grouped_family"], help="Split policy for release dataset exports.")

    hf_export_parser = subparsers.add_parser("hf-export")
    hf_export_parser.add_argument("--repository-dir", default="repository")
    hf_export_parser.add_argument("--output-dir", default="outputs/hf_dataset")
    hf_export_parser.add_argument("--topic", default=None)
    hf_export_parser.add_argument("--topics", nargs="*", default=None)
    hf_export_parser.add_argument("--modules", nargs="*", default=None)
    hf_export_parser.add_argument("--generators", nargs="*", default=None)
    hf_export_parser.add_argument("--difficulties", nargs="*", default=None)
    hf_export_parser.add_argument("--train-ratio", type=float, default=0.90)
    hf_export_parser.add_argument("--validation-ratio", type=float, default=0.05)
    hf_export_parser.add_argument("--test-ratio", type=float, default=0.05)
    hf_export_parser.add_argument("--dedupe-mode", choices=["input_answer", "input_only", "full", "canonical", "case_id", "family"], default=DEFAULT_DEDUPE_MODE)
    hf_export_parser.add_argument("--shuffle", dest="shuffle", action="store_true")
    hf_export_parser.add_argument("--no-shuffle", dest="shuffle", action="store_false")
    hf_export_parser.set_defaults(shuffle=True)
    hf_export_parser.add_argument("--seed", type=int, default=42)
    hf_export_parser.add_argument("--format", dest="format_name", default="hf", choices=["hf", "chatml", "alpaca"])
    hf_export_parser.add_argument("--source-kind", default="auto", choices=["samples", "cases", "auto"])
    hf_export_parser.add_argument("--split-mode", default="grouped_canonical", choices=["random", "grouped_canonical", "grouped_case", "grouped_family"])

    report_parser = subparsers.add_parser("report")
    report_parser.add_argument("--repository-dir", default="repository")
    report_parser.add_argument("--json-out", default=None)
    report_parser.add_argument("--csv-out", default=None)
    report_parser.add_argument("--dashboard", action="store_true")
    return parser


def dispatch_command(args) -> int:
    if args.command == "list":
        cmd_list(as_json=args.json)
        return 0
    if args.command == "build":
        return run_build_from_args(args)
    if args.command == "repository-build":
        return run_repository_build_from_args(args)
    if args.command == "repository":
        registry = get_registry()
        module_ids = resolve_module_ids(registry, modules=args.modules, topic=args.topic, topics=args.topics)
        result = export_repository(
            output_dir=args.output_dir,
            module_ids=module_ids,
            samples_per_level=max(0, args.samples_per_level),
            fmt=args.fmt,
            generation_mode=args.generation_mode,
            cases_per_level=args.cases_per_level,
            write_report=True,
            progress=args.progress,
        )
        print(json.dumps(result, indent=2))
        return 0
    if args.command == "hf-export":
        return run_hf_export_from_args(args)
    if args.command == "report":
        report = analyze_repository(args.repository_dir)
        if args.dashboard:
            print(render_repository_dashboard(report))
        json_out = args.json_out or f"{args.repository_dir}/coverage_report.json"
        csv_out = args.csv_out or f"{args.repository_dir}/coverage_report.csv"
        paths = write_repository_reports(args.repository_dir)
        if json_out != paths["report_json"] or csv_out != paths["report_csv"]:
            report_paths = write_repository_reports(args.repository_dir)
            if json_out != report_paths["report_json"]:
                Path(json_out).write_text(Path(report_paths["report_json"]).read_text(encoding="utf-8"), encoding="utf-8")
            if csv_out != report_paths["report_csv"]:
                Path(csv_out).write_text(Path(report_paths["report_csv"]).read_text(encoding="utf-8"), encoding="utf-8")
        print(json.dumps({"repository_dir": args.repository_dir, "report_json": json_out, "report_csv": csv_out}, indent=2))
        return 0
    return 0

