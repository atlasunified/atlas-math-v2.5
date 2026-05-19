from __future__ import annotations

import inspect
import itertools
import math
import time
from collections import defaultdict
from concurrent.futures import ProcessPoolExecutor, as_completed

from atlas_math.cli_common import (
    allocate_integer_counts,
    choose_worker_count,
    dedupe_keep_order,
    dedupe_key_from_record,
    dedupe_records_posthoc,
    fmt_int,
    fmt_pct,
    info_get,
    module_levels,
    resolve_difficulty_mix,
    resolve_target_records,
    serialize_sample,
    should_retry_after_round,
    write_jsonl,
)
from atlas_math.cli_config import (
    DEFAULT_EXHAUSTION_PATIENCE,
    DEFAULT_GENERATION_MODE,
    DEFAULT_MAX_BATCH_SIZE,
    DEFAULT_MAX_ROUNDS,
    DEFAULT_MIN_UNIQUE_RATE,
    DEFAULT_MIN_YIELD_RATIO,
    DEFAULT_RETRY_OVERSHOOT,
    DEFAULT_TARGET_TOLERANCE,
)
from atlas_math.cli_dashboard import ansi_enabled as dashboard_ansi_enabled, draw_dashboard, finish_dashboard, render_estimation_dashboard
from atlas_math.registry import get_registry



def _difficulty_to_level_arg(difficulty):
    """Convert canonical difficulty labels like level_3 to numeric levels for legacy generators."""
    text = str(difficulty or "level_1")
    if text.startswith("level_"):
        try:
            return int(text.rsplit("_", 1)[-1])
        except ValueError:
            return text
    return difficulty


def call_generate_random(module, count: int, difficulty: str | None):
    generate = getattr(module, "generate")
    sig = inspect.signature(generate)
    params = sig.parameters
    kwargs = {}

    if "count" in params:
        kwargs["count"] = count
    if "difficulty" in params:
        kwargs["difficulty"] = difficulty if difficulty is not None else "level_1"
    if "seed" in params:
        kwargs["seed"] = None

    sig.bind_partial(**kwargs)
    result = generate(**kwargs)
    if result is None:
        return []
    return result if isinstance(result, list) else list(result)


def call_iter_function(fn, difficulty: str, offset: int, stride: int, count: int):
    sig = inspect.signature(fn)
    params = sig.parameters
    kwargs = {}

    if "difficulty" in params:
        kwargs["difficulty"] = difficulty
    elif "level" in params:
        kwargs["level"] = _difficulty_to_level_arg(difficulty)

    iterator = fn(**kwargs)
    if iterator is None:
        return []
    if offset > 0:
        iterator = itertools.islice(iterator, offset, None)
    if stride > 1:
        iterator = itertools.islice(iterator, 0, None, stride)
    return list(itertools.islice(iterator, count))


def call_generate_unique_function(fn, difficulty: str, count: int, offset: int, stride: int):
    sig = inspect.signature(fn)
    params = sig.parameters
    kwargs = {}

    if "count" in params:
        kwargs["count"] = count
    if "difficulty" in params:
        kwargs["difficulty"] = difficulty
    elif "level" in params:
        kwargs["level"] = _difficulty_to_level_arg(difficulty)
    if "offset" in params:
        kwargs["offset"] = offset
    elif "start" in params:
        kwargs["start"] = offset
    if "stride" in params:
        kwargs["stride"] = stride
    elif "step" in params:
        kwargs["step"] = stride
    if "seed" in params:
        kwargs["seed"] = None

    sig.bind_partial(**kwargs)
    result = fn(**kwargs)
    if result is None:
        return []
    return result if isinstance(result, list) else list(result)


def module_supports_structured(module) -> bool:
    return any(hasattr(module, name) for name in ("generate_unique", "iter_samples", "iter_unique", "iter_repository_cases"))


def module_has_exact_capacity(module, difficulty: str | None) -> bool:
    capacity = module_estimate_capacity(module, difficulty)
    return capacity.get("quality") == "exact" and capacity.get("value") is not None


def call_generate_structured(module, count: int, difficulty: str, worker_offset: int, worker_stride: int):
    if hasattr(module, "generate_unique"):
        return call_generate_unique_function(
            getattr(module, "generate_unique"),
            difficulty=difficulty,
            count=count,
            offset=worker_offset,
            stride=worker_stride,
        )

    iter_name = "iter_unique" if hasattr(module, "iter_unique") else None
    if iter_name is None and hasattr(module, "iter_samples"):
        iter_name = "iter_samples"
    if iter_name is None:
        return []

    return call_iter_function(
        getattr(module, iter_name),
        difficulty=difficulty,
        offset=worker_offset,
        stride=worker_stride,
        count=count,
    )


def call_generate(
    module,
    count: int,
    difficulty: str | None,
    generation_mode: str = DEFAULT_GENERATION_MODE,
    worker_offset: int = 0,
    worker_stride: int = 1,
):
    if generation_mode not in {"auto", "structured", "random"}:
        raise ValueError(f"Unknown generation mode: {generation_mode}")

    if generation_mode in {"auto", "structured"} and module_supports_structured(module):
        structured_samples = call_generate_structured(
            module,
            count=count,
            difficulty=difficulty or "level_1",
            worker_offset=worker_offset,
            worker_stride=max(1, worker_stride),
        )
        if structured_samples:
            return structured_samples
        if generation_mode == "structured":
            return []

    return call_generate_random(module, count=count, difficulty=difficulty)


def _capacity_descriptor(value=None, quality: str | None = None) -> dict[str, object]:
    allowed = {"exact", "estimated", "lower_bound", "unknown"}
    quality = (quality or "unknown").lower()
    if quality not in allowed:
        quality = "unknown"

    if value is None:
        return {"value": None, "quality": "unknown" if quality == "unknown" else quality}

    try:
        normalized = max(0, int(value))
    except Exception:
        return {"value": None, "quality": "unknown"}

    return {"value": normalized, "quality": quality if normalized is not None else "unknown"}


def module_estimate_capacity(module, difficulty: str | None) -> dict[str, object]:
    for name in ("estimate_capacity", "capacity"):
        if not hasattr(module, name):
            continue
        fn = getattr(module, name)
        try:
            sig = inspect.signature(fn)
            params = sig.parameters
            kwargs = {}
            if "difficulty" in params:
                kwargs["difficulty"] = difficulty
            elif "level" in params:
                kwargs["level"] = difficulty
            value = fn(**kwargs)
            if isinstance(value, dict):
                return _capacity_descriptor(value.get("value"), value.get("quality", "estimated"))
            if value is None:
                return _capacity_descriptor(None, "unknown")
            inferred_quality = "exact" if module_supports_structured(module) else "estimated"
            return _capacity_descriptor(value, inferred_quality)
        except Exception:
            return _capacity_descriptor(None, "unknown")
    return _capacity_descriptor(None, "unknown")


def build_bucket_inventory(registry, module_ids):
    inventory = []
    for module_id in dedupe_keep_order(module_ids):
        module = registry.get(module_id)
        if module is None:
            continue
        for difficulty in module_levels(registry, module_id):
            capacity = module_estimate_capacity(module, difficulty)
            inventory.append(
                {
                    "module_id": module_id,
                    "difficulty": difficulty,
                    "bucket_id": f"{module_id}::{difficulty}",
                    "capacity": capacity,
                    "capacity_value": capacity.get("value"),
                    "capacity_quality": capacity.get("quality", "unknown"),
                    "structured": module_supports_structured(module),
                }
            )
    return inventory


def plan_generation(
    registry,
    module_ids,
    size: str | None = None,
    target_records: int | None = None,
    difficulty_mix_name: str = "balanced",
    run_to_completion: bool = False,
):
    target = None if run_to_completion else resolve_target_records(size=size, target_records=target_records)
    inventory = build_bucket_inventory(registry, module_ids)

    if not inventory:
        return {
            "target_records": target or 0,
            "module_count": 0,
            "bucket_count": 0,
            "difficulty_mix_name": difficulty_mix_name,
            "difficulty_targets": {},
            "bucket_targets": {},
            "buckets": [],
            "structured_bucket_count": 0,
            "known_capacity_total": None,
        }

    if run_to_completion:
        planned_buckets = []
        exact_capacity_total = 0
        known_capacity_bucket_count = 0
        unknown_capacity_bucket_count = 0
        exact_capacity_bucket_count = 0
        estimated_capacity_bucket_count = 0
        lower_bound_capacity_bucket_count = 0
        skipped_non_exact_bucket_count = 0
        for item in inventory:
            capacity_value = item.get("capacity_value")
            capacity_quality = item.get("capacity_quality", "unknown")
            if capacity_value is None:
                unknown_capacity_bucket_count += 1
                skipped_non_exact_bucket_count += 1
                continue
            known_capacity_bucket_count += 1
            if capacity_quality == "exact":
                exact_capacity_bucket_count += 1
            elif capacity_quality == "estimated":
                estimated_capacity_bucket_count += 1
                skipped_non_exact_bucket_count += 1
                continue
            elif capacity_quality == "lower_bound":
                lower_bound_capacity_bucket_count += 1
                skipped_non_exact_bucket_count += 1
                continue
            else:
                skipped_non_exact_bucket_count += 1
                continue
            if capacity_value <= 0:
                continue
            exact_capacity_total += capacity_value
            planned_buckets.append(
                {
                    "module_id": item["module_id"],
                    "difficulty": item["difficulty"],
                    "bucket_id": item["bucket_id"],
                    "target": capacity_value,
                    "capacity": item["capacity"],
                    "capacity_value": capacity_value,
                    "capacity_quality": capacity_quality,
                    "structured": item["structured"],
                }
            )
        return {
            "target_records": exact_capacity_total,
            "module_count": len({item["module_id"] for item in inventory}),
            "bucket_count": len(inventory),
            "difficulty_mix_name": "run_to_completion",
            "difficulty_targets": {},
            "bucket_targets": {item["bucket_id"]: item["target"] for item in planned_buckets},
            "buckets": planned_buckets,
            "structured_bucket_count": sum(1 for item in inventory if item["structured"]),
            "known_capacity_total": exact_capacity_total,
            "known_capacity_bucket_count": known_capacity_bucket_count,
            "unknown_capacity_bucket_count": unknown_capacity_bucket_count,
            "exact_capacity_bucket_count": exact_capacity_bucket_count,
            "estimated_capacity_bucket_count": estimated_capacity_bucket_count,
            "lower_bound_capacity_bucket_count": lower_bound_capacity_bucket_count,
            "skipped_non_exact_bucket_count": skipped_non_exact_bucket_count,
        }

    available_levels = sorted({item["difficulty"] for item in inventory})
    difficulty_mix = resolve_difficulty_mix(difficulty_mix_name, available_levels)
    difficulty_targets = allocate_integer_counts(target, difficulty_mix)

    by_difficulty = defaultdict(list)
    for item in inventory:
        by_difficulty[item["difficulty"]].append(item)

    bucket_targets = {}
    for difficulty, bucket_items in by_difficulty.items():
        weights = {}
        for item in bucket_items:
            capacity_value = item.get("capacity_value")
            weights[item["bucket_id"]] = (
                float(capacity_value) if capacity_value is not None and capacity_value > 0 else 1.0
            )
        bucket_targets.update(
            allocate_integer_counts(difficulty_targets.get(difficulty, 0), weights)
        )

    planned_buckets = []
    known_capacity_total = 0
    has_unknown_capacity = False
    known_capacity_bucket_count = 0
    unknown_capacity_bucket_count = 0
    exact_capacity_bucket_count = 0
    estimated_capacity_bucket_count = 0
    lower_bound_capacity_bucket_count = 0

    for item in inventory:
        count = bucket_targets.get(item["bucket_id"], 0)
        capacity_value = item.get("capacity_value")

        if capacity_value is None:
            has_unknown_capacity = True
            unknown_capacity_bucket_count += 1
        else:
            known_capacity_total += capacity_value
            known_capacity_bucket_count += 1
            if item.get("capacity_quality") == "exact":
                exact_capacity_bucket_count += 1
            elif item.get("capacity_quality") == "estimated":
                estimated_capacity_bucket_count += 1
            elif item.get("capacity_quality") == "lower_bound":
                lower_bound_capacity_bucket_count += 1
            count = min(count, capacity_value)

        if count > 0:
            planned_buckets.append(
                {
                    "module_id": item["module_id"],
                    "difficulty": item["difficulty"],
                    "bucket_id": item["bucket_id"],
                    "target": count,
                    "capacity": item["capacity"],
                    "capacity_value": item.get("capacity_value"),
                    "capacity_quality": item.get("capacity_quality"),
                    "structured": item["structured"],
                }
            )

    return {
        "target_records": target,
        "module_count": len({item["module_id"] for item in inventory}),
        "bucket_count": len(inventory),
        "difficulty_mix_name": difficulty_mix_name,
        "difficulty_targets": difficulty_targets,
        "bucket_targets": bucket_targets,
        "buckets": planned_buckets,
        "structured_bucket_count": sum(1 for item in inventory if item["structured"]),
        "known_capacity_total": None if has_unknown_capacity else known_capacity_total,
        "known_capacity_bucket_count": known_capacity_bucket_count,
        "unknown_capacity_bucket_count": unknown_capacity_bucket_count,
        "exact_capacity_bucket_count": exact_capacity_bucket_count,
        "estimated_capacity_bucket_count": estimated_capacity_bucket_count,
        "lower_bound_capacity_bucket_count": lower_bound_capacity_bucket_count,
    }


def estimate_record_count(
    registry,
    module_ids,
    size: str | None = None,
    target_records: int | None = None,
    difficulty_mix_name: str = "balanced",
    run_to_completion: bool = False,
) -> dict:
    plan = plan_generation(
        registry=registry,
        module_ids=module_ids,
        size=size,
        target_records=target_records,
        difficulty_mix_name=difficulty_mix_name,
        run_to_completion=run_to_completion,
    )
    bucket_counts = [bucket["target"] for bucket in plan["buckets"]]
    return {
        "target_records": plan["target_records"],
        "module_count": plan["module_count"],
        "unit_count": plan["bucket_count"],
        "planned_batches": len(plan["buckets"]),
        "estimated_records": sum(bucket_counts),
        "min_per_unit": min(bucket_counts, default=0),
        "max_per_unit": max(bucket_counts, default=0),
        "difficulty_targets": plan["difficulty_targets"],
        "difficulty_mix_name": plan["difficulty_mix_name"],
        "structured_bucket_count": plan["structured_bucket_count"],
        "known_capacity_total": plan["known_capacity_total"],
        "known_capacity_bucket_count": plan["known_capacity_bucket_count"],
        "unknown_capacity_bucket_count": plan["unknown_capacity_bucket_count"],
        "exact_capacity_bucket_count": plan["exact_capacity_bucket_count"],
        "estimated_capacity_bucket_count": plan["estimated_capacity_bucket_count"],
        "lower_bound_capacity_bucket_count": plan["lower_bound_capacity_bucket_count"],
        "skipped_non_exact_bucket_count": plan.get("skipped_non_exact_bucket_count", 0),
    }


def worker_generate_chunk(module_id: str, difficulty: str, count: int, fmt: str, generation_mode: str, worker_offset: int, worker_stride: int):
    registry = get_registry()
    module = registry.get(module_id)
    if module is None:
        return {"module_id": module_id, "difficulty": difficulty, "records": [], "error": f"missing module: {module_id}"}

    try:
        samples = call_generate(
            module,
            count=count,
            difficulty=difficulty,
            generation_mode=generation_mode,
            worker_offset=worker_offset,
            worker_stride=worker_stride,
        )
        return {
            "module_id": module_id,
            "difficulty": difficulty,
            "records": [serialize_sample(sample, fmt=fmt) for sample in samples],
            "error": None,
        }
    except Exception as exc:
        return {"module_id": module_id, "difficulty": difficulty, "records": [], "error": f"{type(exc).__name__}: {exc}"}


def estimate_additional_raw_needed(
    target_total: int,
    unique_count: int,
    raw_generated: int,
    min_unique_rate: float = DEFAULT_MIN_UNIQUE_RATE,
    overshoot: float = DEFAULT_RETRY_OVERSHOOT,
) -> int:
    remaining_unique = max(0, target_total - unique_count)
    if remaining_unique <= 0:
        return 0
    observed_unique_rate = unique_count / max(raw_generated, 1)
    effective_rate = max(min_unique_rate, observed_unique_rate)
    return max(1, math.ceil((remaining_unique / effective_rate) * overshoot))


def _adaptive_chunk_cap(state: dict, *, remaining_global: int, open_bucket_count: int, worker_count: int, max_batch_size: int) -> int:
    effective_max = max(1, int(max_batch_size or 1))
    remaining_need = max(0, int(state.get("target_raw", 0)) - int(state.get("accepted_raw", 0)))
    if remaining_need <= 0 or remaining_global <= 0:
        return 0

    fair_share = max(1, math.ceil(remaining_global / max(1, open_bucket_count)))
    worker_share = max(1, math.ceil(remaining_global / max(1, worker_count)))
    base = min(effective_max, remaining_need, max(1, min(fair_share, worker_share)))

    if state.get("structured"):
        base = max(base, min(effective_max, remaining_need, max(2, math.ceil(fair_share * 1.25))))

    if int(state.get("low_yield_rounds", 0)) > 0:
        base = max(1, math.ceil(base / 2))
    if int(state.get("worker_errors", 0)) > 0:
        base = max(1, math.ceil(base / 2))
    if int(state.get("random_fallback_count", 0)) > 0 and not state.get("structured"):
        base = max(1, math.ceil(base * 0.75))

    capacity_value = state.get("capacity_value")
    if state.get("capacity_quality") == "exact" and capacity_value is not None:
        remaining_capacity = max(0, int(capacity_value) - int(state.get("generated", 0)))
        base = min(base, remaining_capacity)

    return max(1, min(effective_max, remaining_need, remaining_global, base))


def _plan_chunk_jobs(bucket_state: dict[str, dict], *, raw_records_count: int, raw_target_records: int, worker_count: int, max_batch_size: int) -> list[tuple[str, str, str, int, int, int]]:
    open_bucket_ids = [
        bucket_id
        for bucket_id, state in bucket_state.items()
        if not state.get("exhausted") and int(state.get("accepted_raw", 0)) < int(state.get("target_raw", 0))
    ]
    if not open_bucket_ids:
        return []

    remaining_global = max(0, raw_target_records - raw_records_count)
    if remaining_global <= 0:
        return []

    capped_needs: dict[str, int] = {}
    weights: dict[str, float] = {}
    for bucket_id in open_bucket_ids:
        state = bucket_state[bucket_id]
        cap = _adaptive_chunk_cap(
            state,
            remaining_global=remaining_global,
            open_bucket_count=len(open_bucket_ids),
            worker_count=worker_count,
            max_batch_size=max_batch_size,
        )
        if cap <= 0:
            continue
        capped_needs[bucket_id] = cap
        weight = float(cap)
        if state.get("structured"):
            weight *= 1.15
        if int(state.get("low_yield_rounds", 0)) > 0:
            weight *= 0.5
        if int(state.get("worker_errors", 0)) > 0:
            weight *= 0.5
        weights[bucket_id] = max(0.1, weight)

    if not capped_needs:
        return []

    global_budget = min(remaining_global, sum(capped_needs.values()))
    allocated = allocate_integer_counts(global_budget, weights)
    jobs = []
    worker_slot = 0
    for bucket_id in open_bucket_ids:
        count = min(capped_needs.get(bucket_id, 0), allocated.get(bucket_id, 0))
        if count <= 0:
            continue
        state = bucket_state[bucket_id]
        if state.get("structured"):
            worker_offset = int(state.get("next_offset", 0))
            worker_stride = 1
        else:
            worker_offset = worker_slot % max(1, worker_count)
            worker_stride = max(1, worker_count)
        jobs.append((bucket_id, state["module_id"], state["difficulty"], count, worker_offset, worker_stride))
        worker_slot += 1
    return jobs


def _seed_seen_keys(current_unique_records: list[dict] | None, dedupe_mode: str) -> set[str]:
    if not current_unique_records:
        return set()
    return {dedupe_key_from_record(record, dedupe_mode=dedupe_mode) for record in current_unique_records}




def _render_plain_progress_line(*, round_index: int, max_rounds: int, unique_so_far: int, target_unique_records: int, raw_generated: int, duplicates_so_far: int, worker_count: int, open_buckets: int, total_buckets: int) -> str:
    progress_ratio = unique_so_far / max(target_unique_records, 1)
    return (
        f"[progress] round={round_index}/{max_rounds} "
        f"unique={fmt_int(unique_so_far)}/{fmt_int(target_unique_records)} ({fmt_pct(progress_ratio)}) "
        f"raw={fmt_int(raw_generated)} dupes={fmt_int(duplicates_so_far)} "
        f"workers={worker_count} buckets_open={open_buckets}/{total_buckets}"
    )

def generate_round_raw_records(
    module_ids,
    raw_target_records: int,
    target_unique_records: int,
    fmt: str = "clean",
    progress: bool = False,
    workers: int | None = None,
    max_batch_size: int = DEFAULT_MAX_BATCH_SIZE,
    difficulty_mix_name: str = "balanced",
    min_yield_ratio: float = DEFAULT_MIN_YIELD_RATIO,
    exhaustion_patience: int = DEFAULT_EXHAUSTION_PATIENCE,
    round_index: int = 1,
    max_rounds: int = DEFAULT_MAX_ROUNDS,
    current_unique_records: list[dict] | None = None,
    current_duplicates: int = 0,
    current_raw_generated: int = 0,
    yield_history: list[float] | None = None,
    dedupe_mode: str = "input_answer",
    generation_mode: str = DEFAULT_GENERATION_MODE,
    run_to_completion: bool = False,
):
    registry = get_registry()
    module_ids = dedupe_keep_order(module_ids)
    plan = plan_generation(
        registry=registry,
        module_ids=module_ids,
        target_records=raw_target_records,
        difficulty_mix_name=difficulty_mix_name,
        run_to_completion=run_to_completion,
    )
    buckets = plan["buckets"]
    if not buckets:
        return {"raw_records": [], "bucket_state": {}, "yield_history": yield_history or []}

    worker_count = choose_worker_count(workers)
    seen_global_keys = _seed_seen_keys(current_unique_records, dedupe_mode)

    bucket_state = {
        bucket["bucket_id"]: {
            "module_id": bucket["module_id"],
            "difficulty": bucket["difficulty"],
            "target_raw": bucket["target"],
            "accepted_raw": 0,
            "unique_global": 0,
            "generated": 0,
            "duplicates_local": 0,
            "duplicates_global": 0,
            "low_yield_rounds": 0,
            "exhausted": False,
            "capacity": bucket.get("capacity"),
            "capacity_value": bucket.get("capacity_value"),
            "capacity_quality": bucket.get("capacity_quality", "unknown"),
            "structured": bucket.get("structured", False),
            "next_offset": 0,
        }
        for bucket in buckets
    }

    raw_records: list[dict] = []
    yield_history = list(yield_history or [])
    start_time = time.time()
    last_draw = 0.0
    plain_progress_interval = 2.0

    def maybe_draw(force: bool = False):
        nonlocal last_draw
        if not progress:
            return
        now = time.time()
        interval = 0.20 if dashboard_ansi_enabled() else plain_progress_interval
        if not force and (now - last_draw) < interval:
            return
        if current_unique_records is None:
            unique_so_far = sum(state["unique_global"] for state in bucket_state.values())
            duplicates_so_far = sum(state["duplicates_global"] for state in bucket_state.values())
        else:
            unique_so_far = len(seen_global_keys)
            duplicates_so_far = current_duplicates + sum(state["duplicates_global"] for state in bucket_state.values())
        raw_generated_so_far = current_raw_generated + len(raw_records)
        if dashboard_ansi_enabled():
            dashboard = render_estimation_dashboard(
                target_total=target_unique_records,
                raw_target_total=raw_target_records,
                unique_so_far=unique_so_far,
                raw_generated=raw_generated_so_far,
                duplicates_so_far=duplicates_so_far,
                worker_count=worker_count,
                difficulty_targets=plan["difficulty_targets"],
                bucket_state=bucket_state,
                yield_history=yield_history,
                start_time=start_time,
                round_index=round_index,
                max_rounds=max_rounds,
            )
            draw_dashboard(dashboard)
        else:
            open_buckets = sum(1 for state in bucket_state.values() if not state["exhausted"])
            print(_render_plain_progress_line(
                round_index=round_index,
                max_rounds=max_rounds,
                unique_so_far=unique_so_far,
                target_unique_records=target_unique_records,
                raw_generated=raw_generated_so_far,
                duplicates_so_far=duplicates_so_far,
                worker_count=worker_count,
                open_buckets=open_buckets,
                total_buckets=len(bucket_state),
            ))
        last_draw = now

    def healthy_open_buckets():
        return [bucket_id for bucket_id, state in bucket_state.items() if not state["exhausted"] and state["accepted_raw"] < state["target_raw"]]

    def needed_for_bucket(bucket_id: str) -> int:
        state = bucket_state[bucket_id]
        return max(0, state["target_raw"] - state["accepted_raw"])

    def next_jobs():
        return _plan_chunk_jobs(
            bucket_state,
            raw_records_count=len(raw_records),
            raw_target_records=raw_target_records,
            worker_count=worker_count,
            max_batch_size=max_batch_size,
        )

    if progress:
        if dashboard_ansi_enabled():
            maybe_draw(force=True)
        else:
            print(
                f"[start] launching generation round {round_index}/{max_rounds} with {worker_count} worker(s) across {len(bucket_state)} bucket(s); raw target={fmt_int(raw_target_records)}, unique target={fmt_int(target_unique_records)}"
            )
            maybe_draw(force=True)

    try:
        with ProcessPoolExecutor(max_workers=worker_count) as executor:
            while len(raw_records) < raw_target_records:
                jobs = next_jobs()
                if not jobs:
                    break

                future_to_job = {}
                for bucket_id, module_id, difficulty, count, worker_offset, worker_stride in jobs:
                    future = executor.submit(
                        worker_generate_chunk,
                        module_id,
                        difficulty,
                        count,
                        fmt,
                        generation_mode,
                        worker_offset,
                        worker_stride,
                    )
                    future_to_job[future] = (bucket_id, module_id, difficulty, worker_offset, worker_stride)

                for future in as_completed(future_to_job):
                    bucket_id, module_id, difficulty, worker_offset, worker_stride = future_to_job[future]
                    state = bucket_state[bucket_id]
                    try:
                        result = future.result()
                    except Exception as exc:
                        state["low_yield_rounds"] += 1
                        state["exhausted"] = state["low_yield_rounds"] >= exhaustion_patience
                        if not progress:
                            print(f"[skip] {module_id} {difficulty}: worker failure: {type(exc).__name__}: {exc}")
                        maybe_draw()
                        continue

                    if result.get("error"):
                        state["low_yield_rounds"] += 1
                        state["exhausted"] = state["low_yield_rounds"] >= exhaustion_patience
                        if not progress:
                            print(f"[skip] {module_id} {difficulty}: {result['error']}")
                        maybe_draw()
                        continue

                    chunk_records = result.get("records", [])
                    remaining_global = raw_target_records - len(raw_records)
                    admitted_records = chunk_records[: max(0, remaining_global)]
                    generated_now = len(chunk_records)
                    accepted_now = len(admitted_records)
                    raw_records.extend(admitted_records)

                    state["generated"] += generated_now
                    state["accepted_raw"] += accepted_now
                    if state.get("structured"):
                        state["next_offset"] = max(int(state.get("next_offset", 0)), int(worker_offset) + int(generated_now) * max(1, int(worker_stride)))

                    local_seen = set()
                    unique_local = 0
                    local_dupes = 0
                    unique_global = 0
                    global_dupes = 0
                    for record in admitted_records:
                        key = dedupe_key_from_record(record, dedupe_mode=dedupe_mode)
                        if key in local_seen:
                            local_dupes += 1
                        else:
                            local_seen.add(key)
                            unique_local += 1
                        if key in seen_global_keys:
                            global_dupes += 1
                        else:
                            seen_global_keys.add(key)
                            unique_global += 1

                    state["unique_global"] += unique_global
                    state["duplicates_local"] += local_dupes
                    state["duplicates_global"] += global_dupes

                    yield_ratio = unique_global / max(accepted_now, 1)
                    yield_history.append(yield_ratio)
                    if len(yield_history) > 120:
                        yield_history = yield_history[-120:]

                    if accepted_now == 0 or yield_ratio < min_yield_ratio:
                        state["low_yield_rounds"] += 1
                    else:
                        state["low_yield_rounds"] = 0

                    if state["low_yield_rounds"] >= exhaustion_patience:
                        state["exhausted"] = True
                    if state["accepted_raw"] >= state["target_raw"]:
                        state["exhausted"] = True
                    if state.get("capacity_quality") == "exact" and state.get("capacity_value") is not None and state["generated"] >= state["capacity_value"]:
                        state["exhausted"] = True

                    maybe_draw()

                if len(raw_records) >= raw_target_records:
                    break
                remaining_global = raw_target_records - len(raw_records)
                if remaining_global <= 0:
                    break
                open_buckets = healthy_open_buckets()
                if not open_buckets:
                    break

                unmet = {}
                for bucket_id in open_buckets:
                    state = bucket_state[bucket_id]
                    remaining_need = max(0, state["target_raw"] - state["accepted_raw"])
                    if state.get("capacity_quality") == "exact" and state.get("capacity_value") is not None:
                        remaining_capacity = max(0, state["capacity_value"] - state["generated"])
                        remaining_need = min(remaining_need, remaining_capacity)
                    unmet[bucket_id] = remaining_need

                if sum(unmet.values()) <= 0:
                    break

                redistributed = allocate_integer_counts(remaining_global, {key: float(value) for key, value in unmet.items() if value > 0})
                for bucket_id in open_buckets:
                    state = bucket_state[bucket_id]
                    new_target = state["accepted_raw"] + redistributed.get(bucket_id, 0)
                    if state["capacity_quality"] == "exact" and state["capacity"] is not None:
                        new_target = min(new_target, state["generated"] + max(0, int(state.get("capacity_value") or 0) - state["generated"]))
                    state["target_raw"] = max(state["accepted_raw"], new_target)

                maybe_draw()
    finally:
        if progress:
            maybe_draw(force=True)
            finish_dashboard()

    return {"raw_records": raw_records[:raw_target_records], "bucket_state": bucket_state, "yield_history": yield_history}


def generate_from_modules(
    module_ids,
    size: str = "small",
    target_records: int | None = None,
    fmt: str = "clean",
    output: str = "outputs/output.jsonl",
    progress: bool = False,
    dedupe: bool = True,
    dedupe_mode: str = "input_answer",
    workers: int | None = None,
    max_batch_size: int = DEFAULT_MAX_BATCH_SIZE,
    difficulty_mix_name: str = "balanced",
    min_yield_ratio: float = DEFAULT_MIN_YIELD_RATIO,
    exhaustion_patience: int = DEFAULT_EXHAUSTION_PATIENCE,
    target_tolerance: float = DEFAULT_TARGET_TOLERANCE,
    max_rounds: int = DEFAULT_MAX_ROUNDS,
    generation_mode: str = DEFAULT_GENERATION_MODE,
    run_to_completion: bool = False,
):
    module_ids = dedupe_keep_order(module_ids)
    if run_to_completion:
        registry = get_registry()
        inventory = build_bucket_inventory(registry, module_ids)
        exact_total = sum(
            int(item.get("capacity_value") or 0)
            for item in inventory
            if item.get("capacity_quality") == "exact" and item.get("capacity_value") is not None
        )
        resolved_target = exact_total
        if exact_total <= 0:
            write_jsonl([], output)
            print("[warn] run-to-completion requested, but no exact-capacity structured generators were available.")
            return 0
    else:
        resolved_target = resolve_target_records(size=size, target_records=target_records)
    worker_count = choose_worker_count(workers)

    if not module_ids:
        write_jsonl([], output)
        return 0

    all_raw_records: list[dict] = []
    unique_records: list[dict] = []
    duplicates = 0
    raw_generated = 0
    yield_history: list[float] = []
    raw_target_this_round = resolved_target
    rounds_completed = 0
    previous_unique_count = -1

    while rounds_completed < max_rounds:
        rounds_completed += 1
        round_result = generate_round_raw_records(
            module_ids=module_ids,
            raw_target_records=raw_target_this_round,
            target_unique_records=resolved_target,
            fmt=fmt,
            progress=progress,
            workers=worker_count,
            max_batch_size=max_batch_size,
            difficulty_mix_name=difficulty_mix_name,
            min_yield_ratio=min_yield_ratio,
            exhaustion_patience=exhaustion_patience,
            round_index=rounds_completed,
            max_rounds=max_rounds,
            current_unique_records=unique_records,
            current_duplicates=duplicates,
            current_raw_generated=raw_generated,
            yield_history=yield_history,
            dedupe_mode=dedupe_mode,
            generation_mode=generation_mode,
            run_to_completion=run_to_completion,
        )

        all_raw_records.extend(round_result["raw_records"])
        raw_generated = len(all_raw_records)
        if dedupe:
            unique_records, duplicates = dedupe_records_posthoc(all_raw_records, dedupe_mode)
        else:
            unique_records = list(all_raw_records)
            duplicates = 0

        unique_count = len(unique_records)
        unique_rate = unique_count / max(raw_generated, 1)
        lower_bound = math.floor(resolved_target * (1.0 - target_tolerance))
        upper_bound = math.ceil(resolved_target * (1.0 + target_tolerance))

        print(
            f"Round {rounds_completed}: raw={fmt_int(raw_generated)}, unique={fmt_int(unique_count)}, "
            f"dupes={fmt_int(duplicates)}, unique_rate={unique_rate:.2%}, "
            f"target_window=[{fmt_int(lower_bound)}, {fmt_int(upper_bound)}]"
        )

        if lower_bound <= unique_count <= upper_bound:
            break
        if unique_count > upper_bound:
            unique_records = unique_records[:resolved_target]
            break
        if not should_retry_after_round(unique_count, resolved_target, target_tolerance):
            break
        if previous_unique_count == unique_count:
            print("[warn] no unique growth detected after post-hoc dedupe; stopping early.")
            break

        previous_unique_count = unique_count
        raw_target_this_round = estimate_additional_raw_needed(
            target_total=resolved_target,
            unique_count=unique_count,
            raw_generated=raw_generated,
        )
        if raw_target_this_round <= 0:
            break
        print(
            f"Retrying with estimated raw generation count {fmt_int(raw_target_this_round)} "
            f"based on observed unique rate {unique_rate:.2%}."
        )

    final_unique_records = unique_records[:resolved_target]
    final_unique_count = len(final_unique_records)
    lower_bound = math.floor(resolved_target * (1.0 - target_tolerance))
    if final_unique_count < lower_bound:
        print(
            f"[warn] finished with {fmt_int(final_unique_count)} unique record(s); "
            f"target was {fmt_int(resolved_target)} with tolerance ±{target_tolerance:.0%}."
        )

    write_jsonl(final_unique_records, output)
    observed_unique_rate = final_unique_count / max(raw_generated, 1)
    print(
        f"Done. Raw={fmt_int(raw_generated)}, unique={fmt_int(final_unique_count)}, "
        f"duplicates={fmt_int(max(0, raw_generated - final_unique_count))}, "
        f"observed_unique_rate={observed_unique_rate:.2%}, rounds={rounds_completed}."
    )
    return final_unique_count

