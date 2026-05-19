from __future__ import annotations

import itertools
import random
from typing import Iterable

from atlas_math.modules.shared.common import make_sample

MODULE_INFO = {
    "module_id": "arithmetic.rounding_and_place_value",
    "name": "Rounding and Place Value",
    "topic": "arithmetic",
    "subtopic": "core_arithmetic",
    "difficulty_levels": ["level_1", "level_2", "level_3", "level_4", "level_5"],
    "enabled": True,
}

INSTRUCTIONS = [
    "Solve the rounding problem: {problem}",
    "Use place value to answer: {problem}",
    "Round or identify the requested digit: {problem}",
    "Work carefully with the place values in this problem: {problem}",
]

LEVEL_SPEC_CAPS = {
    "level_1": 1200,
    "level_2": 1500,
    "level_3": 1800,
    "level_4": 2200,
    "level_5": 2600,
}

FAMILY_CAPS = {
    "level_1": {"nearest_10": 1200},
    "level_2": {"nearest_100": 750, "digit_value_whole": 750},
    "level_3": {"nearest_tenth": 900, "digit_value_decimal": 900},
    "level_4": {"nearest_1000": 1100, "nearest_hundredth": 1100},
    "level_5": {"multi_rounding": 1300, "which_rounds_to": 1300},
}

CAPACITY_HINTS = {level: {"value": cap, "quality": "capped"} for level, cap in LEVEL_SPEC_CAPS.items()}
MAX_SPEC_PREFIX = 5000
MAX_GENERATE_MULTIPLIER = 8
MAX_ITER_SAMPLES = 4096

PLACE_NAMES = {
    1: "ones",
    10: "tens",
    100: "hundreds",
    1000: "thousands",
    0.1: "tenths",
    0.01: "hundredths",
}


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


def _fmt_number(value):
    if isinstance(value, float):
        text = f"{value:.4f}".rstrip("0").rstrip(".")
        return text
    return str(value)


def _round_half_up(value: float, unit: float):
    scaled = value / unit
    if scaled >= 0:
        return int(scaled + 0.5) * unit
    return int(scaled - 0.5) * unit


def _digit_at_place(value, place):
    if place >= 1:
        return (int(abs(value)) // int(place)) % 10
    scale = int(round(1 / place))
    scaled = int(round(abs(value) * scale))
    return scaled % 10


def _evaluate(spec: dict):
    family = spec["family"]
    vals = spec["values"]
    if family in {"nearest_10", "nearest_100", "nearest_1000", "nearest_tenth", "nearest_hundredth"}:
        value, unit = vals
        result = _round_half_up(float(value), float(unit))
        if unit >= 1:
            return int(round(result))
        return round(result + 0.0, 2)
    if family in {"digit_value_whole", "digit_value_decimal"}:
        value, place = vals
        digit = _digit_at_place(value, place)
        return digit * place
    if family == "multi_rounding":
        value, unit1, unit2 = vals
        first = _round_half_up(float(value), float(unit1))
        second = _round_half_up(float(first), float(unit2))
        if unit2 >= 1:
            return int(round(second))
        return round(second + 0.0, 2)
    if family == "which_rounds_to":
        target, unit, delta = vals
        return int(target + delta)
    raise ValueError(f"Unknown family: {family}")


def _problem_text(spec: dict) -> str:
    family = spec["family"]
    vals = spec["values"]
    if family in {"nearest_10", "nearest_100", "nearest_1000", "nearest_tenth", "nearest_hundredth"}:
        return f"Round {_fmt_number(vals[0])} to the nearest {PLACE_NAMES[vals[1]]}."
    if family in {"digit_value_whole", "digit_value_decimal"}:
        return f"What is the value of the digit in the {PLACE_NAMES[vals[1]]} place in {_fmt_number(vals[0])}?"
    if family == "multi_rounding":
        return f"Round {_fmt_number(vals[0])} to the nearest {PLACE_NAMES[vals[1]]}, then round that result to the nearest {PLACE_NAMES[vals[2]]}."
    if family == "which_rounds_to":
        return f"Which integer rounds to {vals[0]} when rounded to the nearest {PLACE_NAMES[vals[1]]}: {int(vals[0] + vals[2])}?"
    raise ValueError(f"Unknown family: {family}")


def _answer_text(spec: dict) -> str:
    result = _evaluate(spec)
    return _fmt_number(result)


def _sample_from_spec(spec: dict, difficulty: str, instruction_idx: int = 0) -> dict:
    problem = _problem_text(spec)
    answer = _answer_text(spec)
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
    family = "nearest_10"
    limit = FAMILY_CAPS["level_1"][family]
    emitted = 0
    for value in range(12, 998):
        yield {
            "family": family,
            "values": (value, 10),
            "canonical_key": f"{family}:{value}",
            "case_id": f"{family}:{value}",
            "family_id": family,
        }
        emitted += 1
        if emitted >= limit:
            return


def iter_level2_specs() -> Iterable[dict]:
    budgets = FAMILY_CAPS["level_2"]
    emitted = 0
    for value in range(105, 5005, 5):
        yield {
            "family": "nearest_100",
            "values": (value, 100),
            "canonical_key": f"nearest_100:{value}",
            "case_id": f"nearest_100:{value}",
            "family_id": "nearest_100",
        }
        emitted += 1
        if emitted >= budgets["nearest_100"]:
            break

    emitted = 0
    for value in range(123, 9999, 7):
        for place in (10, 100, 1000):
            yield {
                "family": "digit_value_whole",
                "values": (value, place),
                "canonical_key": f"digit_value_whole:{value}:{place}",
                "case_id": f"digit_value_whole:{value}:{place}",
                "family_id": "digit_value_whole",
            }
            emitted += 1
            if emitted >= budgets["digit_value_whole"]:
                return


def iter_level3_specs() -> Iterable[dict]:
    budgets = FAMILY_CAPS["level_3"]
    emitted = 0
    for whole in range(2, 120):
        for tenths in range(0, 10):
            for hundredths in (0, 2, 4, 5, 6, 8):
                value = whole + tenths / 10 + hundredths / 100
                yield {
                    "family": "nearest_tenth",
                    "values": (value, 0.1),
                    "canonical_key": f"nearest_tenth:{value}",
                    "case_id": f"nearest_tenth:{value}",
                    "family_id": "nearest_tenth",
                }
                emitted += 1
                if emitted >= budgets["nearest_tenth"]:
                    break
            if emitted >= budgets["nearest_tenth"]:
                break
        if emitted >= budgets["nearest_tenth"]:
            break

    emitted = 0
    for whole in range(1, 90):
        for tenths in range(0, 10):
            for hundredths in range(0, 10):
                value = whole + tenths / 10 + hundredths / 100
                for place in (0.1, 0.01):
                    yield {
                        "family": "digit_value_decimal",
                        "values": (value, place),
                        "canonical_key": f"digit_value_decimal:{value}:{place}",
                        "case_id": f"digit_value_decimal:{value}:{place}",
                        "family_id": "digit_value_decimal",
                    }
                    emitted += 1
                    if emitted >= budgets["digit_value_decimal"]:
                        return


def iter_level4_specs() -> Iterable[dict]:
    budgets = FAMILY_CAPS["level_4"]
    emitted = 0
    for value in range(1500, 250000, 125):
        yield {
            "family": "nearest_1000",
            "values": (value, 1000),
            "canonical_key": f"nearest_1000:{value}",
            "case_id": f"nearest_1000:{value}",
            "family_id": "nearest_1000",
        }
        emitted += 1
        if emitted >= budgets["nearest_1000"]:
            break

    emitted = 0
    for whole in range(1, 80):
        for tenths in range(0, 10):
            for hundredths in range(0, 10):
                for thousandths in (0, 2, 4, 5, 6, 8):
                    value = whole + tenths / 10 + hundredths / 100 + thousandths / 1000
                    yield {
                        "family": "nearest_hundredth",
                        "values": (value, 0.01),
                        "canonical_key": f"nearest_hundredth:{value}",
                        "case_id": f"nearest_hundredth:{value}",
                        "family_id": "nearest_hundredth",
                    }
                    emitted += 1
                    if emitted >= budgets["nearest_hundredth"]:
                        return


def iter_level5_specs() -> Iterable[dict]:
    budgets = FAMILY_CAPS["level_5"]
    emitted = 0
    for value in range(1355, 125000, 37):
        for unit1, unit2 in ((10, 100), (10, 1000), (100, 1000), (0.01, 0.1)):
            yield {
                "family": "multi_rounding",
                "values": (value / 100 if unit1 < 1 else value, unit1, unit2),
                "canonical_key": f"multi_rounding:{value}:{unit1}:{unit2}",
                "case_id": f"multi_rounding:{value}:{unit1}:{unit2}",
                "family_id": "multi_rounding",
            }
            emitted += 1
            if emitted >= budgets["multi_rounding"]:
                break
        if emitted >= budgets["multi_rounding"]:
            break

    emitted = 0
    for target in range(20, 500, 10):
        for delta in (-4, -3, -2, -1, 0, 1, 2, 3, 4):
            yield {
                "family": "which_rounds_to",
                "values": (target, 10, delta),
                "canonical_key": f"which_rounds_to:{target}:{delta}",
                "case_id": f"which_rounds_to:{target}:{delta}",
                "family_id": "which_rounds_to",
            }
            emitted += 1
            if emitted >= budgets["which_rounds_to"]:
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
        "level_1": ["rounds whole numbers to the nearest ten"],
        "level_2": ["adds nearest hundred rounding and whole-number digit-value questions"],
        "level_3": ["extends to decimal rounding and decimal place-value identification"],
        "level_4": ["adds nearest thousand and nearest hundredth cases"],
        "level_5": ["adds chained rounding and inverse-style which-number-rounds-to prompts"],
    }


