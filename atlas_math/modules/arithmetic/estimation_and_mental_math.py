from __future__ import annotations

import itertools
import random
from typing import Iterable

from atlas_math.modules.shared.common import make_sample

MODULE_INFO = {
    "module_id": "arithmetic.estimation_and_mental_math",
    "name": "Estimation and Mental Math",
    "topic": "arithmetic",
    "subtopic": "core_arithmetic",
    "difficulty_levels": ["level_1", "level_2", "level_3", "level_4", "level_5"],
    "enabled": True,
}

INSTRUCTIONS = [
    "Estimate or compute mentally: {problem}",
    "Use mental math strategies to solve: {problem}",
    "Give the estimated or mental-math answer: {problem}",
    "Work this out efficiently without long calculation: {problem}",
]

LEVEL_SPEC_CAPS = {
    "level_1": 1200,
    "level_2": 1500,
    "level_3": 1800,
    "level_4": 2200,
    "level_5": 2600,
}

FAMILY_CAPS = {
    "level_1": {"compatible_sum": 1200},
    "level_2": {"nearest_ten_estimate": 750, "compatible_product": 750},
    "level_3": {"difference_estimate": 900, "front_end_sum": 900},
    "level_4": {"percent_benchmark": 1100, "distributive_mental": 1100},
    "level_5": {"multi_step_estimate": 1300, "best_reasonable_estimate": 1300},
}

CAPACITY_HINTS = {level: {"value": cap, "quality": "capped"} for level, cap in LEVEL_SPEC_CAPS.items()}
MAX_SPEC_PREFIX = 5000
MAX_GENERATE_MULTIPLIER = 8
MAX_ITER_SAMPLES = 4096


def _level_num(difficulty: str) -> int:
    try:
        value = int(str(difficulty).rsplit("_", 1)[-1])
    except Exception:
        value = 1
    return max(1, min(5, value))


def _difficulty_name(level: int) -> str:
    return f"level_{max(1, min(5, int(level)))}"


def _stable_seed(*parts) -> str:
    return "|".join(str(part) for part in parts)


def _take(iterable: Iterable[dict], n: int) -> Iterable[dict]:
    for idx, item in enumerate(iterable):
        if idx >= max(0, int(n)):
            break
        yield item


def _round_to_nearest(value: int, unit: int) -> int:
    return int(unit * round(value / unit))


def _evaluate(spec: dict):
    family = spec["family"]
    v = spec["values"]
    if family == "compatible_sum":
        return v[0] + v[1]
    if family == "nearest_ten_estimate":
        return _round_to_nearest(v[0], 10) + _round_to_nearest(v[1], 10)
    if family == "compatible_product":
        return v[0] * v[1]
    if family == "difference_estimate":
        return _round_to_nearest(v[0], 10) - _round_to_nearest(v[1], 10)
    if family == "front_end_sum":
        return (v[0] // 100) * 100 + (v[1] // 100) * 100 + (v[2] // 100) * 100
    if family == "percent_benchmark":
        return (v[0] * v[1]) // 100
    if family == "distributive_mental":
        return v[0] * v[1] + v[0] * v[2]
    if family == "multi_step_estimate":
        return (_round_to_nearest(v[0], 10) + _round_to_nearest(v[1], 10)) * v[2]
    if family == "best_reasonable_estimate":
        return round((v[0] * v[1]) / v[2])
    raise ValueError(f"Unknown family: {family}")


def _problem_text(spec: dict) -> str:
    family = spec["family"]
    v = spec["values"]
    if family == "compatible_sum":
        return f"Add mentally: {v[0]} + {v[1]}."
    if family == "nearest_ten_estimate":
        return f"Estimate {v[0]} + {v[1]} by rounding to the nearest ten."
    if family == "compatible_product":
        return f"Multiply mentally: {v[0]} × {v[1]}."
    if family == "difference_estimate":
        return f"Estimate {v[0]} - {v[1]} by rounding to the nearest ten."
    if family == "front_end_sum":
        return f"Use front-end estimation to estimate {v[0]} + {v[1]} + {v[2]}."
    if family == "percent_benchmark":
        return f"Find {v[0]}% of {v[1]} mentally."
    if family == "distributive_mental":
        return f"Use the distributive property to compute {v[0]} × ({v[1]} + {v[2]})."
    if family == "multi_step_estimate":
        return f"Round {v[0]} and {v[1]} to the nearest ten, add, then multiply by {v[2]}."
    if family == "best_reasonable_estimate":
        return f"Choose the best whole-number estimate for ({v[0]} × {v[1]}) ÷ {v[2]}."
    raise ValueError(f"Unknown family: {family}")


def _sample_from_spec(spec: dict, difficulty: str, instruction_idx: int = 0) -> dict:
    problem = _problem_text(spec)
    answer = str(_evaluate(spec))
    metadata = {
        "family": spec["family"],
        "level_number": _level_num(difficulty),
        "structured": True,
        "canonical_key": spec["canonical_key"],
        "case_id": spec["case_id"],
        "family_id": spec["family_id"],
        "template_id": spec["family"],
        "final_answer": answer,
        "values": list(spec["values"]),
    }
    instruction = INSTRUCTIONS[instruction_idx % len(INSTRUCTIONS)].format(problem=problem)
    return make_sample(
        module_id=MODULE_INFO["module_id"],
        topic=MODULE_INFO["topic"],
        subtopic=MODULE_INFO["subtopic"],
        difficulty=difficulty,
        instruction=instruction,
        input_text=problem,
        answer=answer,
        metadata=metadata,
    )


def iter_level1_specs() -> Iterable[dict]:
    family = "compatible_sum"
    limit = FAMILY_CAPS["level_1"][family]
    emitted = 0
    for a in range(10, 101, 5):
        for b in range(10, 101, 5):
            yield {
                "family": family,
                "values": (a, b),
                "canonical_key": f"{family}:{a}:{b}",
                "case_id": f"{family}:{a}:{b}",
                "family_id": family,
            }
            emitted += 1
            if emitted >= limit:
                return


def iter_level2_specs() -> Iterable[dict]:
    budgets = FAMILY_CAPS["level_2"]
    emitted = 0
    for a in range(23, 496, 7):
        for b in range(24, 497, 9):
            yield {
                "family": "nearest_ten_estimate",
                "values": (a, b),
                "canonical_key": f"nearest_ten_estimate:{a}:{b}",
                "case_id": f"nearest_ten_estimate:{a}:{b}",
                "family_id": "nearest_ten_estimate",
            }
            emitted += 1
            if emitted >= budgets["nearest_ten_estimate"]:
                break
        if emitted >= budgets["nearest_ten_estimate"]:
            break

    emitted = 0
    for a in range(12, 101, 2):
        for b in (5, 10, 20, 25, 50):
            yield {
                "family": "compatible_product",
                "values": (a, b),
                "canonical_key": f"compatible_product:{a}:{b}",
                "case_id": f"compatible_product:{a}:{b}",
                "family_id": "compatible_product",
            }
            emitted += 1
            if emitted >= budgets["compatible_product"]:
                return


def iter_level3_specs() -> Iterable[dict]:
    budgets = FAMILY_CAPS["level_3"]
    emitted = 0
    for a in range(123, 996, 11):
        for b in range(57, 890, 13):
            if a <= b:
                continue
            yield {
                "family": "difference_estimate",
                "values": (a, b),
                "canonical_key": f"difference_estimate:{a}:{b}",
                "case_id": f"difference_estimate:{a}:{b}",
                "family_id": "difference_estimate",
            }
            emitted += 1
            if emitted >= budgets["difference_estimate"]:
                break
        if emitted >= budgets["difference_estimate"]:
            break

    emitted = 0
    for a in range(123, 995, 17):
        for b in range(215, 998, 19):
            for c in range(301, 999, 23):
                yield {
                    "family": "front_end_sum",
                    "values": (a, b, c),
                    "canonical_key": f"front_end_sum:{a}:{b}:{c}",
                    "case_id": f"front_end_sum:{a}:{b}:{c}",
                    "family_id": "front_end_sum",
                }
                emitted += 1
                if emitted >= budgets["front_end_sum"]:
                    return


def iter_level4_specs() -> Iterable[dict]:
    budgets = FAMILY_CAPS["level_4"]
    emitted = 0
    for pct in (1, 5, 10, 20, 25, 50):
        for value in range(40, 1001, 5):
            if value * pct % 100 != 0:
                continue
            yield {
                "family": "percent_benchmark",
                "values": (pct, value),
                "canonical_key": f"percent_benchmark:{pct}:{value}",
                "case_id": f"percent_benchmark:{pct}:{value}",
                "family_id": "percent_benchmark",
            }
            emitted += 1
            if emitted >= budgets["percent_benchmark"]:
                break
        if emitted >= budgets["percent_benchmark"]:
            break

    emitted = 0
    for a in range(6, 41):
        for b in range(11, 60, 4):
            for c in range(1, 11):
                yield {
                    "family": "distributive_mental",
                    "values": (a, b, c),
                    "canonical_key": f"distributive_mental:{a}:{b}:{c}",
                    "case_id": f"distributive_mental:{a}:{b}:{c}",
                    "family_id": "distributive_mental",
                }
                emitted += 1
                if emitted >= budgets["distributive_mental"]:
                    return


def iter_level5_specs() -> Iterable[dict]:
    budgets = FAMILY_CAPS["level_5"]
    emitted = 0
    for a in range(23, 496, 7):
        for b in range(24, 497, 9):
            for multiplier in (2, 3, 4, 5):
                yield {
                    "family": "multi_step_estimate",
                    "values": (a, b, multiplier),
                    "canonical_key": f"multi_step_estimate:{a}:{b}:{multiplier}",
                    "case_id": f"multi_step_estimate:{a}:{b}:{multiplier}",
                    "family_id": "multi_step_estimate",
                }
                emitted += 1
                if emitted >= budgets["multi_step_estimate"]:
                    break
            if emitted >= budgets["multi_step_estimate"]:
                break
        if emitted >= budgets["multi_step_estimate"]:
            break

    emitted = 0
    for a in range(45, 496, 9):
        for b in range(12, 91, 3):
            for c in range(2, 26):
                yield {
                    "family": "best_reasonable_estimate",
                    "values": (a, b, c),
                    "canonical_key": f"best_reasonable_estimate:{a}:{b}:{c}",
                    "case_id": f"best_reasonable_estimate:{a}:{b}:{c}",
                    "family_id": "best_reasonable_estimate",
                }
                emitted += 1
                if emitted >= budgets["best_reasonable_estimate"]:
                    return


def _iter_specs(difficulty: str) -> Iterable[dict]:
    level = _difficulty_name(_level_num(difficulty))
    if level == "level_1":
        return _take(iter_level1_specs(), LEVEL_SPEC_CAPS[level])
    if level == "level_2":
        return _take(iter_level2_specs(), LEVEL_SPEC_CAPS[level])
    if level == "level_3":
        return _take(iter_level3_specs(), LEVEL_SPEC_CAPS[level])
    if level == "level_4":
        return _take(iter_level4_specs(), LEVEL_SPEC_CAPS[level])
    return _take(iter_level5_specs(), LEVEL_SPEC_CAPS[level])


def generate(count: int = 10, difficulty: str = "level_1", seed=None) -> list[dict]:
    if count <= 0:
        return []
    prefix = min(max(int(count) * MAX_GENERATE_MULTIPLIER, 256), MAX_SPEC_PREFIX)
    pool = list(itertools.islice(_iter_specs(difficulty), 0, prefix))
    rng = random.Random(_stable_seed(seed, difficulty, count, "generate"))
    rng.shuffle(pool)
    out, seen = [], set()
    for idx, spec in enumerate(pool):
        sample = _sample_from_spec(spec, difficulty, instruction_idx=idx)
        key = sample.get("input", "")
        if key in seen:
            continue
        seen.add(key)
        out.append(sample)
        if len(out) >= count:
            break
    return out


def generate_unique(count: int = 10, difficulty: str = "level_1", offset: int = 0, stride: int = 1, seed=None) -> list[dict]:
    if count <= 0:
        return []
    stride = max(1, int(stride or 1))
    offset = max(0, int(offset or 0))
    level = _difficulty_name(_level_num(difficulty))
    prefix = min(max(count * 16, 512), LEVEL_SPEC_CAPS[level], MAX_SPEC_PREFIX)
    pool = list(itertools.islice(_iter_specs(difficulty), 0, prefix))
    indexed_pool = list(enumerate(pool))
    rng = random.Random(_stable_seed(seed, difficulty, offset, stride, count, "generate_unique"))
    rng.shuffle(indexed_pool)
    if not indexed_pool:
        return []
    start = offset % len(indexed_pool)
    ordered = indexed_pool[start::stride] + indexed_pool[:start:stride]
    out, seen = [], set()
    for idx, spec in ordered:
        sample = _sample_from_spec(spec, difficulty, instruction_idx=idx + offset)
        key = sample.get("input", "")
        if key in seen:
            continue
        seen.add(key)
        out.append(sample)
        if len(out) >= count:
            break
    return out


def iter_samples(difficulty: str = "level_1", seed=None):
    level = _difficulty_name(_level_num(difficulty))
    max_items = min(LEVEL_SPEC_CAPS[level], MAX_ITER_SAMPLES)
    pool = list(itertools.islice(_iter_specs(difficulty), 0, max_items))
    rng = random.Random(_stable_seed(seed, difficulty, "iter_samples"))
    rng.shuffle(pool)
    seen = set()
    for idx, spec in enumerate(pool):
        sample = _sample_from_spec(spec, difficulty, instruction_idx=idx)
        key = sample.get("input", "")
        if key in seen:
            continue
        seen.add(key)
        yield sample


def estimate_capacity(difficulty: str = "level_1"):
    return CAPACITY_HINTS.get(_difficulty_name(_level_num(difficulty)), {"value": None, "quality": "unknown"})


def curriculum() -> dict:
    return {
        "level_1": ["uses exact compatible sums for quick mental calculation"],
        "level_2": ["adds nearest-ten estimates and compatible products"],
        "level_3": ["adds difference estimates and front-end estimation with three addends"],
        "level_4": ["adds benchmark percents and distributive-property mental computation"],
        "level_5": ["adds multi-step estimates and best whole-number estimate prompts"],
    }


