from __future__ import annotations

import shutil
import sys
import time
from collections import defaultdict

from atlas_math.cli_common import clamp, fmt_int, fmt_pct
from atlas_math.cli_config import DEFAULT_LEVELS

ANSI = {
    "reset": "\033[0m",
    "bold": "\033[1m",
    "dim": "\033[2m",
    "black": "\033[30m",
    "red": "\033[31m",
    "green": "\033[32m",
    "yellow": "\033[33m",
    "blue": "\033[34m",
    "magenta": "\033[35m",
    "cyan": "\033[36m",
    "white": "\033[37m",
    "bright_black": "\033[90m",
    "bright_red": "\033[91m",
    "bright_green": "\033[92m",
    "bright_yellow": "\033[93m",
    "bright_blue": "\033[94m",
    "bright_magenta": "\033[95m",
    "bright_cyan": "\033[96m",
    "bright_white": "\033[97m",
    "bg_black": "\033[40m",
    "bg_red": "\033[41m",
    "bg_green": "\033[42m",
    "bg_yellow": "\033[43m",
    "bg_blue": "\033[44m",
    "bg_magenta": "\033[45m",
    "bg_cyan": "\033[46m",
    "bg_white": "\033[47m",
    "home": "\033[H",
    "clear": "\033[2J",
    "hide_cursor": "\033[?25l",
    "show_cursor": "\033[?25h",
}

LEVEL_COLORS = {
    "level_1": ANSI["bright_green"],
    "level_2": ANSI["bright_cyan"],
    "level_3": ANSI["bright_yellow"],
    "level_4": ANSI["bright_magenta"],
    "level_5": ANSI["bright_red"],
}


def ansi_enabled() -> bool:
    return sys.stdout.isatty()


def term_width(default: int = 100) -> int:
    try:
        return shutil.get_terminal_size((default, 30)).columns
    except Exception:
        return default


def bar(
    ratio: float,
    width: int,
    color: str = "",
    empty_color: str = "",
    full_char: str = "█",
    empty_char: str = "·",
) -> str:
    ratio = clamp(ratio, 0.0, 1.0)
    filled = int(round(width * ratio))
    empty = max(0, width - filled)
    return (
        f"{color}{full_char * filled}{ANSI['reset']}"
        f"{empty_color}{empty_char * empty}{ANSI['reset']}"
    )


def sparkline(values: list[float], width: int) -> str:
    ticks = "▁▂▃▄▅▆▇█"
    if not values:
        return " " * width
    vals = values[-width:]
    out = []
    for value in vals:
        idx = int(clamp(value, 0.0, 0.999999) * len(ticks))
        idx = min(idx, len(ticks) - 1)
        out.append(ticks[idx])
    return "".join(out).rjust(width)


def retro_header(title: str, width: int) -> str:
    inner = f" {title} "
    pad = max(0, width - len(inner) - 2)
    left = pad // 2
    right = pad - left
    return f"{ANSI['bright_magenta']}╔{'═' * left}{inner}{'═' * right}╗{ANSI['reset']}\n"


def retro_footer(width: int) -> str:
    return f"{ANSI['bright_magenta']}╚{'═' * (width - 2)}╝{ANSI['reset']}"


def difficulty_rollup(bucket_state: dict) -> dict[str, dict[str, int]]:
    out = defaultdict(
        lambda: {
            "target_raw": 0,
            "accepted_raw": 0,
            "unique_global": 0,
            "generated": 0,
            "duplicates_local": 0,
            "duplicates_global": 0,
            "exhausted": 0,
            "target_met": 0,
            "low_yield_exhausted": 0,
            "capacity_exhausted": 0,
            "error_exhausted": 0,
            "open_buckets": 0,
            "buckets": 0,
            "known_capacity": 0,
            "exact_capacity_buckets": 0,
            "estimated_capacity_buckets": 0,
            "lower_bound_capacity_buckets": 0,
            "unknown_capacity_buckets": 0,
        }
    )
    for state in bucket_state.values():
        level = state["difficulty"]
        out[level]["target_raw"] += state["target_raw"]
        out[level]["accepted_raw"] += state["accepted_raw"]
        out[level]["unique_global"] += state["unique_global"]
        out[level]["generated"] += state["generated"]
        out[level]["duplicates_local"] += state["duplicates_local"]
        out[level]["duplicates_global"] += state["duplicates_global"]
        out[level]["buckets"] += 1
        status = state.get("status", "open")
        if status != "open":
            out[level]["exhausted"] += 1
        if status == "target_met":
            out[level]["target_met"] += 1
        elif status == "low_yield":
            out[level]["low_yield_exhausted"] += 1
        elif status == "capacity_hit":
            out[level]["capacity_exhausted"] += 1
        elif status == "error":
            out[level]["error_exhausted"] += 1
        else:
            out[level]["open_buckets"] += 1
        capacity = state.get("capacity_value", state.get("capacity"))
        capacity_quality = state.get("capacity_quality", "unknown")
        if capacity is None or capacity_quality == "unknown":
            out[level]["unknown_capacity_buckets"] += 1
        else:
            out[level]["known_capacity"] += capacity
            if capacity_quality == "exact":
                out[level]["exact_capacity_buckets"] += 1
            elif capacity_quality == "estimated":
                out[level]["estimated_capacity_buckets"] += 1
            elif capacity_quality == "lower_bound":
                out[level]["lower_bound_capacity_buckets"] += 1
    return dict(out)


def _capacity_text(unique_global: int, known_capacity: int, unknown_capacity_buckets: int, exact_capacity_buckets: int, estimated_capacity_buckets: int, lower_bound_capacity_buckets: int) -> str:
    if known_capacity <= 0:
        return "cap=n/a"
    ratio = unique_global / max(known_capacity, 1)
    if ratio > 1.0:
        value = ">100%"
    else:
        value = fmt_pct(ratio)
    if unknown_capacity_buckets > 0 or estimated_capacity_buckets > 0 or lower_bound_capacity_buckets > 0:
        return f"cap≈{value}"
    if exact_capacity_buckets <= 0:
        return "cap=n/a"
    return f"cap={value}"


def render_estimation_dashboard(
    *,
    target_total: int,
    raw_target_total: int,
    unique_so_far: int,
    raw_generated: int,
    duplicates_so_far: int,
    worker_count: int,
    difficulty_targets: dict[str, int],
    bucket_state: dict,
    yield_history: list[float],
    start_time: float,
    round_index: int,
    max_rounds: int,
) -> str:
    width = max(100, min(term_width(), 160))
    inner_width = width - 4

    overall_ratio = unique_so_far / max(target_total, 1)
    overall_yield = unique_so_far / max(raw_generated, 1)
    elapsed = max(0.001, time.time() - start_time)
    unique_rate = unique_so_far / elapsed
    raw_rate = raw_generated / elapsed
    exhausted_count = sum(1 for state in bucket_state.values() if state["exhausted"])
    total_buckets = len(bucket_state)

    lines = []
    lines.append(retro_header("ATLAS MATH // SYNTHESIS ESTIMATOR", width))
    lines.append(
        f"{ANSI['bright_magenta']}║{ANSI['reset']} "
        f"{ANSI['bright_cyan']}TARGET{ANSI['reset']} {fmt_int(target_total):>10}   "
        f"{ANSI['bright_green']}UNIQUE{ANSI['reset']} {fmt_int(unique_so_far):>10}   "
        f"{ANSI['bright_yellow']}RAW{ANSI['reset']} {fmt_int(raw_generated):>10}   "
        f"{ANSI['bright_red']}DUPES{ANSI['reset']} {fmt_int(duplicates_so_far):>10}   "
        f"{ANSI['bright_white']}RAW_GOAL{ANSI['reset']} {fmt_int(raw_target_total):>10}   "
        f"{ANSI['bright_white']}RND{ANSI['reset']} {round_index}/{max_rounds}"
    )
    lines.append(
        f"{ANSI['bright_magenta']}║{ANSI['reset']} "
        f"{ANSI['bright_white']}PROGRESS{ANSI['reset']} "
        f"{bar(overall_ratio, max(20, inner_width - 50), ANSI['bright_green'], ANSI['bright_black'])} "
        f"{fmt_pct(overall_ratio)} {ANSI['bright_magenta']}║{ANSI['reset']}"
    )
    lines.append(
        f"{ANSI['bright_magenta']}║{ANSI['reset']} "
        f"{ANSI['bright_white']}YIELD{ANSI['reset']} {fmt_pct(overall_yield)}   "
        f"{ANSI['bright_white']}UNIQ/s{ANSI['reset']} {fmt_int(int(unique_rate)):>8}   "
        f"{ANSI['bright_white']}RAW/s{ANSI['reset']} {fmt_int(int(raw_rate)):>8}   "
        f"{ANSI['bright_white']}WORKERS{ANSI['reset']} {worker_count:>3}   "
        f"{ANSI['bright_white']}BUCKETS{ANSI['reset']} {exhausted_count:>3}/{total_buckets:<3} exhausted   "
        f"{ANSI['bright_white']}TREND{ANSI['reset']} {ANSI['bright_cyan']}{sparkline(yield_history, 20)}{ANSI['reset']}"
    )
    lines.append(
        f"{ANSI['bright_magenta']}║{ANSI['reset']} "
        f"{ANSI['bright_yellow']}Difficulty progress and bucket health{ANSI['reset']}"
    )

    rollup = difficulty_rollup(bucket_state)
    ordered_levels = [level for level in DEFAULT_LEVELS if level in difficulty_targets or level in rollup]

    for level in ordered_levels:
        stats = rollup.get(level, {})
        planned_unique = difficulty_targets.get(level, 0)
        unique_global = stats.get("unique_global", 0)
        generated = stats.get("generated", 0)
        dupes_global = stats.get("duplicates_global", 0)
        exhausted = stats.get("exhausted", 0)
        buckets = max(1, stats.get("buckets", 0))
        known_capacity = stats.get("known_capacity", 0)
        exact_capacity_buckets = stats.get("exact_capacity_buckets", 0)
        estimated_capacity_buckets = stats.get("estimated_capacity_buckets", 0)
        lower_bound_capacity_buckets = stats.get("lower_bound_capacity_buckets", 0)
        unknown_capacity_buckets = stats.get("unknown_capacity_buckets", 0)

        target_ratio = unique_global / max(planned_unique, 1)
        yield_ratio = unique_global / max(generated, 1)
        fill_ratio = None if known_capacity <= 0 else min(unique_global / max(known_capacity, 1), 1.0)
        fill_render_ratio = 0.0 if fill_ratio is None else fill_ratio
        color = LEVEL_COLORS.get(level, ANSI["bright_white"])
        label = f"{level:<10}"
        fill_text = _capacity_text(
            unique_global,
            known_capacity,
            unknown_capacity_buckets,
            exact_capacity_buckets,
            estimated_capacity_buckets,
            lower_bound_capacity_buckets,
        )
        stats_text = (
            f"uniq={fmt_int(unique_global):>7}/{fmt_int(planned_unique):<7}  "
            f"yld={fmt_pct(yield_ratio)}  {fill_text}  dup={fmt_int(dupes_global):>7}  "
            f"done={stats.get('target_met', 0)}/{buckets} low={stats.get('low_yield_exhausted', 0)} "
            f"cap={stats.get('capacity_exhausted', 0)} err={stats.get('error_exhausted', 0)} open={stats.get('open_buckets', 0)}"
        )
        prog_width = max(10, min(22, inner_width // 5))
        fill_width = max(10, min(18, inner_width // 6))

        lines.append(
            f"{ANSI['bright_magenta']}║{ANSI['reset']} "
            f"{color}{label}{ANSI['reset']} "
            f"P:{bar(target_ratio, prog_width, color, ANSI['bright_black'])} "
            f"F:{bar(fill_render_ratio, fill_width, ANSI['bright_blue'], ANSI['bright_black'])} "
            f"{ANSI['dim']}{stats_text}{ANSI['reset']} "
            f"{ANSI['bright_magenta']}║{ANSI['reset']}"
        )

    lines.append(retro_footer(width))
    return "\n".join(lines)




def render_repository_export_dashboard(
    *,
    output_dir: str,
    module_total: int,
    module_index: int,
    level_total: int,
    level_index: int,
    current_module: str,
    current_level: str,
    exact_level_count: int,
    sampled_level_count: int,
    sample_count_total: int,
    case_count_total: int,
    manifest_count: int,
    report_written: bool,
    start_time: float,
) -> str:
    width = max(100, min(term_width(), 160))
    inner_width = width - 4
    elapsed = max(0.001, time.time() - start_time)
    levels_per_sec = level_index / elapsed
    progress_ratio = level_index / max(level_total, 1)
    module_ratio = module_index / max(module_total, 1)

    lines = []
    lines.append(retro_header("ATLAS MATH // REPOSITORY EXPORT", width))
    lines.append(
        f"{ANSI['bright_magenta']}║{ANSI['reset']} "
        f"{ANSI['bright_cyan']}MODULES{ANSI['reset']} {module_index:>5}/{module_total:<5}   "
        f"{ANSI['bright_white']}LEVELS{ANSI['reset']} {level_index:>6}/{level_total:<6}   "
        f"{ANSI['bright_green']}EXACT{ANSI['reset']} {fmt_int(exact_level_count):>8}   "
        f"{ANSI['bright_yellow']}SAMPLED{ANSI['reset']} {fmt_int(sampled_level_count):>8}"
    )
    lines.append(
        f"{ANSI['bright_magenta']}║{ANSI['reset']} "
        f"{ANSI['bright_white']}SAMPLES{ANSI['reset']} {fmt_int(sample_count_total):>10}   "
        f"{ANSI['bright_white']}CASES{ANSI['reset']} {fmt_int(case_count_total):>12}   "
        f"{ANSI['bright_white']}MANIFESTS{ANSI['reset']} {fmt_int(manifest_count):>8}   "
        f"{ANSI['bright_white']}RATE{ANSI['reset']} {levels_per_sec:>6.2f} lvl/s"
    )
    lines.append(
        f"{ANSI['bright_magenta']}║{ANSI['reset']} "
        f"{ANSI['bright_white']}LEVEL PROGRESS{ANSI['reset']} "
        f"{bar(progress_ratio, max(20, inner_width - 58), ANSI['bright_green'], ANSI['bright_black'])} "
        f"{fmt_pct(progress_ratio)} {ANSI['bright_magenta']}║{ANSI['reset']}"
    )
    lines.append(
        f"{ANSI['bright_magenta']}║{ANSI['reset']} "
        f"{ANSI['bright_white']}MODULE PROGRESS{ANSI['reset']} "
        f"{bar(module_ratio, max(20, inner_width - 59), ANSI['bright_cyan'], ANSI['bright_black'])} "
        f"{fmt_pct(module_ratio)} {ANSI['bright_magenta']}║{ANSI['reset']}"
    )
    lines.append(
        f"{ANSI['bright_magenta']}║{ANSI['reset']} "
        f"{ANSI['bright_yellow']}Current module{ANSI['reset']}: {current_module or '-'}"
    )
    lines.append(
        f"{ANSI['bright_magenta']}║{ANSI['reset']} "
        f"{ANSI['bright_yellow']}Current level{ANSI['reset']}: {current_level or '-'}   "
        f"{ANSI['bright_white']}OUTPUT{ANSI['reset']} {output_dir}   "
        f"{ANSI['bright_white']}REPORT{ANSI['reset']} {'yes' if report_written else 'pending'}"
    )
    lines.append(retro_footer(width))
    return "\n".join(lines)

def draw_dashboard(text: str):
    if not ansi_enabled():
        return
    sys.stdout.write(ANSI["hide_cursor"])
    sys.stdout.write(ANSI["home"])
    sys.stdout.write(ANSI["clear"])
    sys.stdout.write(text)
    sys.stdout.flush()


def finish_dashboard():
    if ansi_enabled():
        sys.stdout.write(ANSI["show_cursor"])
        sys.stdout.flush()

