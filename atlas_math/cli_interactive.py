from __future__ import annotations

import os
import sys
from pathlib import Path

from atlas_math.cli_common import clamp, dedupe_keep_order, safe_float, safe_int
from atlas_math.cli_commands import cmd_list
from atlas_math.cli_config import (
    DEFAULT_DEDUPE_MODE,
    DEFAULT_DIFFICULTY_MIXES,
    DEFAULT_EXHAUSTION_PATIENCE,
    DEFAULT_GENERATION_MODE,
    DEFAULT_MAX_BATCH_SIZE,
    DEFAULT_MAX_ROUNDS,
    DEFAULT_MIN_YIELD_RATIO,
    DEFAULT_TARGET_TOLERANCE,
    SIZE_PRESETS,
)
from atlas_math.cli_generation import estimate_record_count, generate_from_modules
from atlas_math.registry import get_registry
from atlas_math.repository import export_repository
from atlas_math.repository_dataset import build_dataset_from_repository, export_hf_dataset_from_repository
from atlas_math.repository_import import import_repository_from_dataset
from atlas_math.repository_report import analyze_repository, render_repository_dashboard, write_repository_reports
from atlas_math.splitting import SPLIT_MODES


ANSI = {
    "reset": "\033[0m",
    "bold": "\033[1m",
    "dim": "\033[2m",
    "cyan": "\033[36m",
    "green": "\033[32m",
    "yellow": "\033[33m",
    "magenta": "\033[35m",
    "red": "\033[31m",
    "bright_black": "\033[90m",
}


def ansi_enabled() -> bool:
    return sys.stdout.isatty()


def style(text: str, *codes: str) -> str:
    if not ansi_enabled() or not codes:
        return text
    return "".join(codes) + text + ANSI["reset"]


def term_width(default: int = 88) -> int:
    try:
        return os.get_terminal_size().columns
    except OSError:
        return default


def rule(char: str = "─") -> str:
    return char * max(40, min(term_width(), 100))


def header(title: str, subtitle: str | None = None) -> None:
    width = max(40, min(term_width(), 100))
    inner = f" {title} "
    side = max(0, width - len(inner) - 2)
    left = side // 2
    right = side - left
    print()
    print(style(f"╔{'═' * left}{inner}{'═' * right}╗", ANSI["magenta"], ANSI["bold"]))
    if subtitle:
        body = subtitle[: width - 4]
        print(style(f"║ {body.ljust(width - 4)} ║", ANSI["magenta"]))
    print(style(f"╚{'═' * (width - 2)}╝", ANSI["magenta"]))


def section(title: str) -> None:
    print(style(f"\n{title}", ANSI["bold"], ANSI["cyan"]))
    print(style(rule(), ANSI["bright_black"]))


def prompt_text(label: str, default: str | None = None, required: bool = False) -> str:
    while True:
        suffix = f" [{default}]" if default not in (None, "") else ""
        raw = input(f"{label}{suffix}: ").strip()
        if raw:
            return raw
        if default is not None:
            return default
        if not required:
            return ""
        print(style("A value is required.", ANSI["red"]))


def prompt_int(label: str, default: int | None = None, minimum: int | None = None) -> int | None:
    while True:
        suffix = f" [{default}]" if default is not None else ""
        raw = input(f"{label}{suffix}: ").strip()
        if not raw:
            return default
        value = safe_int(raw)
        if value is None:
            print(style("Enter a whole number.", ANSI["red"]))
            continue
        if minimum is not None and value < minimum:
            print(style(f"Enter a value >= {minimum}.", ANSI["red"]))
            continue
        return value


def prompt_float(label: str, default: float | None = None, minimum: float | None = None) -> float | None:
    while True:
        suffix = f" [{default}]" if default is not None else ""
        raw = input(f"{label}{suffix}: ").strip()
        if not raw:
            return default
        value = safe_float(raw)
        if value is None:
            print(style("Enter a numeric value.", ANSI["red"]))
            continue
        if minimum is not None and value < minimum:
            print(style(f"Enter a value >= {minimum}.", ANSI["red"]))
            continue
        return value


def prompt_yes_no(label: str, default: bool = True) -> bool:
    suffix = "[Y/n]" if default else "[y/N]"
    while True:
        raw = input(f"{label} {suffix}: ").strip().lower()
        if not raw:
            return default
        if raw in {"y", "yes"}:
            return True
        if raw in {"n", "no"}:
            return False
        print(style("Please answer y or n.", ANSI["red"]))


def choose_from_list(options: list[str], title: str, default_index: int = 0) -> str:
    while True:
        section(title)
        for idx, option in enumerate(options, start=1):
            marker = "*" if idx - 1 == default_index else " "
            print(f" {marker} {idx:>2}) {option}")
        raw = input(f"Select option [{default_index + 1}]: ").strip()
        if not raw:
            return options[default_index]
        selected = safe_int(raw)
        if selected is None or not (1 <= selected <= len(options)):
            print(style("Invalid selection. Try again.", ANSI["red"]))
            continue
        return options[selected - 1]


def prompt_csv_list(label: str) -> list[str] | None:
    raw = input(f"{label} (comma-separated, blank for all): ").strip()
    if not raw:
        return None
    return dedupe_keep_order([piece.strip() for piece in raw.split(",") if piece.strip()]) or None


def choose_topics(registry) -> list[str] | None:
    topics = sorted(registry.topics())
    if not topics:
        print(style("No topics found in registry.", ANSI["red"]))
        return None

    section("Available topics")
    print("  0) all")
    for i, topic in enumerate(topics, start=1):
        print(f" {i:>2}) {topic}")

    while True:
        raw_topic = input("Select topic numbers [0]: ").strip() or "0"
        if raw_topic == "0":
            return None
        pieces = [piece.strip() for piece in raw_topic.split(",") if piece.strip()]
        selected_topics: list[str] = []
        valid = True
        for piece in pieces:
            idx = safe_int(piece)
            if idx is None or not (1 <= idx <= len(topics)):
                print(style(f"Invalid topic selection: {piece}", ANSI["red"]))
                valid = False
                break
            selected_topics.append(topics[idx - 1])
        if valid and selected_topics:
            return dedupe_keep_order(selected_topics)
        print(style("Please choose one or more valid topic numbers.", ANSI["red"]))


def ask_size_and_target(*, allow_run_to_completion: bool = False) -> tuple[str | None, int | None, bool]:
    section("Dataset target")
    if allow_run_to_completion and prompt_yes_no("Run structured generators to completion when exact finite capacity is known?", default=False):
        return None, None, True
    for name, value in SIZE_PRESETS.items():
        print(f" - {name:<6} {value}")
    raw_target = input("Exact target records (blank to use preset): ").strip()
    if raw_target:
        target = safe_int(raw_target)
        if target is None or target <= 0:
            print(style("Invalid target. Falling back to preset.", ANSI["yellow"]))
        else:
            return None, target, False
    size = choose_from_list(list(SIZE_PRESETS.keys()), "Choose size preset", default_index=0)
    return size, None, False


def ask_output(default_path: str) -> str:
    return prompt_text("Output path", default=default_path)


def confirm_large_run(target_records: int) -> bool:
    if target_records <= 10000:
        return True
    print(style(f"This run targets about {target_records} unique records after deduplication.", ANSI["yellow"]))
    return prompt_yes_no("Continue?", default=False)


def resolve_modules_for_topics(registry, topics: list[str] | None) -> list[str]:
    if not topics:
        return sorted(registry.modules().keys())
    module_ids: list[str] = []
    for topic in topics:
        module_ids.extend(sorted(registry.modules_by_topic(topic).keys()))
    return dedupe_keep_order(module_ids)


def prompt_module_filters(registry, allow_generators: bool = False, allow_difficulties: bool = False) -> dict[str, list[str] | None]:
    topics = choose_topics(registry)
    default_modules = resolve_modules_for_topics(registry, topics)
    if default_modules:
        section("Modules in selected topics")
        for module_id in default_modules:
            print(f" - {module_id}")
    modules = prompt_csv_list("Restrict to module ids")
    generators = prompt_csv_list("Restrict to generator names") if allow_generators else None
    difficulties = prompt_csv_list("Restrict to difficulties") if allow_difficulties else None
    return {
        "topics": topics,
        "modules": modules,
        "generators": generators,
        "difficulties": difficulties,
        "default_modules": default_modules,
    }


def effective_module_ids(filter_state: dict[str, list[str] | None]) -> list[str] | None:
    modules = filter_state.get("modules")
    if modules:
        return modules
    default_modules = filter_state.get("default_modules")
    return default_modules if default_modules else None


class MenuAction:
    def __init__(self, key: str, label: str, handler, section_name: str) -> None:
        self.key = key
        self.label = label
        self.handler = handler
        self.section_name = section_name


def action_list_modules() -> None:
    as_json = prompt_yes_no("Output JSON instead of human-readable text?", default=False)
    cmd_list(as_json=as_json)


def action_build_from_generators() -> None:
    registry = get_registry()
    filters = prompt_module_filters(registry, allow_generators=False, allow_difficulties=False)
    module_ids = effective_module_ids(filters)
    if not module_ids:
        print(style("No modules matched the current filters.", ANSI["red"]))
        return

    size, target_records, run_to_completion = ask_size_and_target(allow_run_to_completion=True)
    difficulty_mix = choose_from_list(list(DEFAULT_DIFFICULTY_MIXES.keys()), "Choose difficulty mix", 0)
    generation_mode = choose_from_list(["auto", "structured", "random"], "Choose generation mode", ["auto", "structured", "random"].index(DEFAULT_GENERATION_MODE if DEFAULT_GENERATION_MODE in {"auto","structured","random"} else "auto"))
    fmt = choose_from_list(["clean", "extended", "rich"], "Choose output format", 2)
    output = ask_output("outputs/output.jsonl")
    progress = prompt_yes_no("Show live progress dashboard?", default=True)
    dedupe_mode = choose_from_list(["input_answer", "input_only", "full", "canonical", "case_id", "family"], "Choose dedupe mode", 0)
    default_workers = min(4, os.cpu_count() or 1)
    workers = prompt_int("Worker count", default=default_workers, minimum=1)
    max_batch_size = prompt_int("Max batch size", default=DEFAULT_MAX_BATCH_SIZE, minimum=1) or DEFAULT_MAX_BATCH_SIZE
    min_yield_ratio = prompt_float("Min yield ratio", default=DEFAULT_MIN_YIELD_RATIO, minimum=0.0)
    exhaustion_patience = prompt_int("Exhaustion patience", default=DEFAULT_EXHAUSTION_PATIENCE, minimum=1) or DEFAULT_EXHAUSTION_PATIENCE
    target_tolerance = prompt_float("Target tolerance", default=DEFAULT_TARGET_TOLERANCE, minimum=0.0)
    max_rounds = prompt_int("Max rounds", default=DEFAULT_MAX_ROUNDS, minimum=1) or DEFAULT_MAX_ROUNDS

    if not run_to_completion:
        requested_target = target_records or SIZE_PRESETS.get(size or "small", 100)
        if not confirm_large_run(requested_target):
            return

    estimate = estimate_record_count(
        registry,
        module_ids,
        size=size,
        target_records=target_records,
        difficulty_mix_name=difficulty_mix,
        run_to_completion=run_to_completion,
    )
    print(style(f"\nEstimated first-round raw records: {estimate['estimated_records']}", ANSI["green"]))
    if run_to_completion and estimate.get("skipped_non_exact_bucket_count", 0):
        print(style(
            f"Run-to-completion will skip {estimate['skipped_non_exact_bucket_count']} bucket(s) without exact finite capacity.",
            ANSI["yellow"],
        ))

    written = generate_from_modules(
        module_ids,
        size=size or "small",
        target_records=target_records,
        fmt=fmt,
        output=output,
        progress=progress,
        dedupe=True,
        dedupe_mode=dedupe_mode,
        workers=workers,
        max_batch_size=max_batch_size,
        difficulty_mix_name=difficulty_mix,
        min_yield_ratio=clamp(min_yield_ratio or DEFAULT_MIN_YIELD_RATIO, 0.0, 1.0),
        exhaustion_patience=exhaustion_patience,
        target_tolerance=clamp((target_tolerance or DEFAULT_TARGET_TOLERANCE), 0.0, 0.5),
        max_rounds=max_rounds,
        generation_mode=generation_mode,
        run_to_completion=run_to_completion,
    )
    print(style(f"\nWrote {written} records to {output}", ANSI["green"]))


def action_export_repository() -> None:
    registry = get_registry()
    filters = prompt_module_filters(registry)
    module_ids = effective_module_ids(filters)
    if not module_ids:
        print(style("No modules matched the current filters.", ANSI["red"]))
        return
    output_dir = prompt_text("Repository output dir", default="repository")
    samples_per_level = prompt_int("Samples per level", default=50, minimum=0) or 0
    export_all_cases = prompt_yes_no("Export full exact case sets when available?", default=True)
    cases_per_level = None if export_all_cases else prompt_int("Cases per level limit", default=0, minimum=0)
    fmt = choose_from_list(["clean", "extended", "rich"], "Choose repository export format", 2)
    generation_mode = choose_from_list(["auto", "structured", "random"], "Choose generation mode", 0)
    progress = prompt_yes_no("Show live progress dashboard?", default=True)
    result = export_repository(
        output_dir=output_dir,
        module_ids=module_ids,
        samples_per_level=samples_per_level,
        fmt=fmt,
        generation_mode=generation_mode,
        cases_per_level=cases_per_level,
        write_report=True,
        progress=progress,
    )
    print(style(f"\nRepository written to {result['output_dir']}", ANSI["green"]))


def action_build_from_repository() -> None:
    registry = get_registry()
    repo_dir = prompt_text("Repository directory", default="repository")
    filters = prompt_module_filters(registry, allow_generators=True, allow_difficulties=True)
    size, target_records, _ = ask_size_and_target(allow_run_to_completion=False)
    difficulty_mix = choose_from_list(list(DEFAULT_DIFFICULTY_MIXES.keys()), "Choose difficulty mix", 0)
    output = ask_output("outputs/repository_build.jsonl")
    source_kind = choose_from_list(["samples", "cases", "auto"], "Choose repository row source", 2)
    dedupe_mode = choose_from_list(["input_answer", "input_only", "full", "canonical", "case_id", "family"], "Choose dedupe mode", 0)
    shuffle = prompt_yes_no("Shuffle selected rows?", default=True)
    seed = prompt_int("Shuffle seed", default=42, minimum=0) or 42
    result = build_dataset_from_repository(
        repository_dir=repo_dir,
        output=output,
        topic=None,
        topics=filters["topics"],
        modules=effective_module_ids(filters),
        generators=filters["generators"],
        difficulties=filters["difficulties"],
        size=size,
        target_records=target_records,
        difficulty_mix_name=difficulty_mix,
        dedupe_mode=dedupe_mode,
        shuffle=shuffle,
        seed=seed,
        source_kind=source_kind,
    )
    print(style(f"\nWrote {result['written_records']} records to {output}", ANSI["green"]))


def action_export_hf_dataset() -> None:
    registry = get_registry()
    repo_dir = prompt_text("Repository directory", default="repository")
    output_dir = prompt_text("HF output dir", default="outputs/hf_dataset")
    filters = prompt_module_filters(registry, allow_generators=True, allow_difficulties=True)
    fmt = choose_from_list(["hf", "chatml", "alpaca"], "Choose HF export format", 0)
    source_kind = choose_from_list(["samples", "cases", "auto"], "Choose repository row source", 2)
    split_mode = choose_from_list(sorted(SPLIT_MODES.keys()), "Choose split mode", sorted(SPLIT_MODES.keys()).index("grouped_canonical") if "grouped_canonical" in SPLIT_MODES else 0)
    train_ratio = prompt_float("Train ratio", default=0.90, minimum=0.0) or 0.90
    validation_ratio = prompt_float("Validation ratio", default=0.05, minimum=0.0) or 0.05
    test_ratio = prompt_float("Test ratio", default=0.05, minimum=0.0) or 0.05
    dedupe_mode = choose_from_list(["input_answer", "input_only", "full", "canonical", "case_id", "family"], "Choose dedupe mode", 0)
    shuffle = prompt_yes_no("Shuffle before split?", default=True)
    seed = prompt_int("Shuffle seed", default=42, minimum=0) or 42
    result = export_hf_dataset_from_repository(
        repository_dir=repo_dir,
        output_dir=output_dir,
        topic=None,
        topics=filters["topics"],
        modules=effective_module_ids(filters),
        generators=filters["generators"],
        difficulties=filters["difficulties"],
        train_ratio=train_ratio,
        validation_ratio=validation_ratio,
        test_ratio=test_ratio,
        dedupe_mode=dedupe_mode,
        shuffle=shuffle,
        seed=seed,
        format_name=fmt,
        source_kind=source_kind,
        split_mode=split_mode,
    )
    print(style(f"\nHF dataset written to {result['output_dir']}", ANSI["green"]))
    print(f"Counts: {result['counts']}")


def action_import_repository() -> None:
    dataset = prompt_text("Dataset JSONL path", required=True)
    output_dir = prompt_text("Repository output dir", default="repository")
    chunk_size = prompt_int("Chunk size", default=250000, minimum=1) or 250000
    result = import_repository_from_dataset(
        dataset=dataset,
        output_dir=output_dir,
        chunk_size=chunk_size,
        progress=True,
        write_report=True,
    )
    print(
        style(
            f"\nImported {result['rows_written']} rows into {output_dir} across {result['chunks_processed']} chunk(s).",
            ANSI["green"],
        )
    )


def action_show_report_dashboard() -> None:
    repo_dir = prompt_text("Repository directory", default="repository")
    report = analyze_repository(repo_dir)
    print()
    print(render_repository_dashboard(report))


def action_write_report_files() -> None:
    repo_dir = prompt_text("Repository directory", default="repository")
    default_json = f"{repo_dir}/coverage_report.json"
    default_csv = f"{repo_dir}/coverage_report.csv"
    json_out = prompt_text("JSON report path", default=default_json)
    csv_out = prompt_text("CSV report path", default=default_csv)

    generated = write_repository_reports(repo_dir)
    generated_json = Path(generated["report_json"])
    generated_csv = Path(generated["report_csv"])
    requested_json = Path(json_out)
    requested_csv = Path(csv_out)

    if requested_json != generated_json:
        requested_json.parent.mkdir(parents=True, exist_ok=True)
        requested_json.write_text(generated_json.read_text(encoding="utf-8"), encoding="utf-8")
    if requested_csv != generated_csv:
        requested_csv.parent.mkdir(parents=True, exist_ok=True)
        requested_csv.write_text(generated_csv.read_text(encoding="utf-8"), encoding="utf-8")

    print(style("\nRepository reports written.", ANSI["green"]))
    print(f"JSON: {requested_json.as_posix()}")
    print(f"CSV:  {requested_csv.as_posix()}")


def action_refresh_registry() -> None:
    registry = get_registry()
    registry.refresh()
    print(style("\nRegistry refreshed.", ANSI["green"]))


ACTIONS = [
    MenuAction("1", "List registered modules", action_list_modules, "CLI-equivalent commands"),
    MenuAction("2", "Build dataset from generators", action_build_from_generators, "CLI-equivalent commands"),
    MenuAction("3", "Export repository from generators", action_export_repository, "CLI-equivalent commands"),
    MenuAction("4", "Build dataset from repository", action_build_from_repository, "CLI-equivalent commands"),
    MenuAction("5", "Show repository coverage dashboard", action_show_report_dashboard, "CLI-equivalent commands"),
    MenuAction("6", "Write repository report files (JSON/CSV)", action_write_report_files, "CLI-equivalent commands"),
    MenuAction("7", "Export HF dataset from repository", action_export_hf_dataset, "Repository tools"),
    MenuAction("8", "Import repository from dataset", action_import_repository, "Repository tools"),
    MenuAction("9", "Refresh registry", action_refresh_registry, "Maintenance"),
    MenuAction("0", "Quit", lambda: None, "Maintenance"),
]


def render_main_menu() -> None:
    header("ATLAS MATH", "Interactive command center")
    current_section = None
    for action in ACTIONS:
        if action.section_name != current_section:
            current_section = action.section_name
            print(style(f"\n{current_section}", ANSI["bold"], ANSI["cyan"]))
        print(f"  {action.key}) {action.label}")


def interactive_menu() -> int:
    action_map = {action.key: action for action in ACTIONS}
    while True:
        render_main_menu()
        choice = input("\nSelect option [0]: ").strip() or "0"
        action = action_map.get(choice)
        if action is None:
            print(style("\nInvalid selection. Try again.", ANSI["red"]))
            continue
        if choice == "0":
            return 0
        print()
        action.handler()

