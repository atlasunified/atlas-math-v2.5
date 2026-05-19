from __future__ import annotations

import random
from fractions import Fraction
from typing import Iterable

from atlas_math.modules.shared.common import make_sample

MODULE_INFO = {
    "module_id": "prealgebra.slope_from_points",
    "name": "Slope from Points",
    "topic": "prealgebra",
    "subtopic": "core_prealgebra",
    "difficulty_levels": ["level_1", "level_2", "level_3", "level_4", "level_5"],
    "enabled": True,
}

INSTRUCTIONS = [
    "Find the slope: {problem}",
    "Determine the slope from the two points: {problem}",
    "Compute the slope carefully: {problem}",
    "Use the slope formula: {problem}",
]

LEVEL_SPEC_CAPS = {"level_1": 900, "level_2": 1100, "level_3": 1300, "level_4": 1500, "level_5": 1700}
FAMILY_CAPS = {
    "level_1": {"positive_integer": 900},
    "level_2": {"negative_integer": 1100},
    "level_3": {"fractional": 1300},
    "level_4": {"horizontal": 1500},
    "level_5": {"mixed_signed_fraction": 1700},
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


def _stable_seed(*parts) -> str:
    return "|".join(str(p) for p in parts)


def _take(iterable: Iterable[dict], n: int) -> Iterable[dict]:
    for idx, item in enumerate(iterable):
        if idx >= max(0, int(n)):
            break
        yield item


def _fmt(value) -> str:
    if isinstance(value, Fraction):
        return str(value.numerator) if value.denominator == 1 else f"{value.numerator}/{value.denominator}"
    return str(value)


def _solve(spec: dict):
    x1, y1, x2, y2 = spec["values"]
    return Fraction(y2 - y1, x2 - x1)


def _problem_text(spec: dict) -> str:
    x1, y1, x2, y2 = spec["values"]
    return f"Find the slope of the line through ({x1}, {y1}) and ({x2}, {y2})."


def _sample_from_spec(spec: dict, difficulty: str, instruction_idx: int = 0) -> dict:
    problem = _problem_text(spec)
    answer = _fmt(_solve(spec))
    metadata = {"family": spec["family"], "level_number": _level_num(difficulty), "structured": True, "canonical_key": spec["canonical_key"], "case_id": spec["case_id"], "family_id": spec["family_id"], "template_id": spec["family"], "final_answer": answer, "values": list(spec["values"])}
    instruction = INSTRUCTIONS[instruction_idx % len(INSTRUCTIONS)].format(problem=problem)
    return make_sample(module_id=MODULE_INFO["module_id"], topic=MODULE_INFO["topic"], subtopic=MODULE_INFO["subtopic"], difficulty=difficulty, instruction=instruction, input_text=problem, answer=answer, metadata=metadata)


def iter_level1_specs() -> Iterable[dict]:
    emitted = 0
    for dx in range(1, 13):
        for m in range(1, 11):
            dy = m * dx
            for x1 in range(-10, 11):
                for y1 in range(-10, 11):
                    yield {"family": "positive_integer", "values": (x1, y1, x1 + dx, y1 + dy), "canonical_key": f"positive_integer:{x1}:{y1}:{x1+dx}:{y1+dy}", "case_id": f"positive_integer:{x1}:{y1}:{x1+dx}:{y1+dy}", "family_id": "positive_integer"}
                    emitted += 1
                    if emitted >= FAMILY_CAPS["level_1"]["positive_integer"]:
                        return


def iter_level2_specs() -> Iterable[dict]:
    emitted = 0
    for dx in range(1, 13):
        for m in range(1, 11):
            dy = -m * dx
            for x1 in range(-10, 11):
                for y1 in range(-10, 11):
                    yield {"family": "negative_integer", "values": (x1, y1, x1 + dx, y1 + dy), "canonical_key": f"negative_integer:{x1}:{y1}:{x1+dx}:{y1+dy}", "case_id": f"negative_integer:{x1}:{y1}:{x1+dx}:{y1+dy}", "family_id": "negative_integer"}
                    emitted += 1
                    if emitted >= FAMILY_CAPS["level_2"]["negative_integer"]:
                        return


def iter_level3_specs() -> Iterable[dict]:
    emitted = 0
    for dx in range(2, 13):
        for dy in range(1, dx):
            if Fraction(dy, dx).denominator == 1:
                continue
            for x1 in range(-10, 11):
                for y1 in range(-10, 11):
                    yield {"family": "fractional", "values": (x1, y1, x1 + dx, y1 + dy), "canonical_key": f"fractional:{x1}:{y1}:{x1+dx}:{y1+dy}", "case_id": f"fractional:{x1}:{y1}:{x1+dx}:{y1+dy}", "family_id": "fractional"}
                    emitted += 1
                    if emitted >= FAMILY_CAPS["level_3"]["fractional"]:
                        return


def iter_level4_specs() -> Iterable[dict]:
    emitted = 0
    for x1 in range(-30, 31):
        for y in range(-20, 21):
            for dx in range(1, 21):
                yield {"family": "horizontal", "values": (x1, y, x1 + dx, y), "canonical_key": f"horizontal:{x1}:{y}:{x1+dx}:{y}", "case_id": f"horizontal:{x1}:{y}:{x1+dx}:{y}", "family_id": "horizontal"}
                emitted += 1
                if emitted >= FAMILY_CAPS["level_4"]["horizontal"]:
                    return


def iter_level5_specs() -> Iterable[dict]:
    emitted = 0
    for dx in range(-12, 13):
        if dx == 0:
            continue
        for dy in range(-12, 13):
            if dy == 0:
                continue
            slope = Fraction(dy, dx)
            if slope.denominator == 1:
                continue
            for x1 in range(-8, 9):
                for y1 in range(-8, 9):
                    yield {"family": "mixed_signed_fraction", "values": (x1, y1, x1 + dx, y1 + dy), "canonical_key": f"mixed_signed_fraction:{x1}:{y1}:{x1+dx}:{y1+dy}", "case_id": f"mixed_signed_fraction:{x1}:{y1}:{x1+dx}:{y1+dy}", "family_id": "mixed_signed_fraction"}
                    emitted += 1
                    if emitted >= FAMILY_CAPS["level_5"]["mixed_signed_fraction"]:
                        return


def iter_specs(difficulty: str) -> Iterable[dict]:
    level = _level_num(difficulty)
    if level == 1:
        yield from iter_level1_specs()
    elif level == 2:
        yield from iter_level2_specs()
    elif level == 3:
        yield from iter_level3_specs()
    elif level == 4:
        yield from iter_level4_specs()
    else:
        yield from iter_level5_specs()


def generate(difficulty: str = "level_1", seed: int | None = None) -> dict:
    pool = list(_take(iter_specs(difficulty), min(LEVEL_SPEC_CAPS.get(difficulty, 1000), MAX_GENERATE_MULTIPLIER * 256)))
    rng = random.Random(seed if seed is not None else _stable_seed(MODULE_INFO["module_id"], difficulty))
    spec = rng.choice(pool)
    return _sample_from_spec(spec, difficulty, instruction_idx=rng.randrange(len(INSTRUCTIONS)))


def generate_unique(difficulty: str = "level_1", limit: int | None = None, seed: int | None = None) -> Iterable[dict]:
    max_items = min(LEVEL_SPEC_CAPS.get(difficulty, 1000), limit if limit is not None else LEVEL_SPEC_CAPS.get(difficulty, 1000), MAX_SPEC_PREFIX)
    pool = list(_take(iter_specs(difficulty), max_items))
    rng = random.Random(seed if seed is not None else _stable_seed(MODULE_INFO["module_id"], difficulty, "unique"))
    rng.shuffle(pool)
    for idx, spec in enumerate(pool):
        yield _sample_from_spec(spec, difficulty, instruction_idx=idx)


def iter_samples(difficulty: str = "level_1", limit: int | None = None) -> Iterable[dict]:
    max_items = min(limit if limit is not None else LEVEL_SPEC_CAPS.get(difficulty, 1000), LEVEL_SPEC_CAPS.get(difficulty, 1000), MAX_ITER_SAMPLES)
    for idx, spec in enumerate(_take(iter_specs(difficulty), max_items)):
        yield _sample_from_spec(spec, difficulty, instruction_idx=idx)


def estimate_capacity(difficulty: str | None = None) -> dict:
    if difficulty is None:
        return {level: CAPACITY_HINTS[level] for level in MODULE_INFO["difficulty_levels"]}
    return CAPACITY_HINTS.get(difficulty, {"value": 0, "quality": "none"})


def curriculum() -> dict:
    return {"module_id": MODULE_INFO["module_id"], "topic": MODULE_INFO["topic"], "subtopic": MODULE_INFO["subtopic"], "difficulty_levels": MODULE_INFO["difficulty_levels"], "capacity": estimate_capacity()}


