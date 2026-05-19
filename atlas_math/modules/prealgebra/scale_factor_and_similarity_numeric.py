from __future__ import annotations

import random
from fractions import Fraction
from typing import Iterable

from atlas_math.modules.shared.common import make_sample

MODULE_INFO = {
    "module_id": "prealgebra.scale_factor_and_similarity_numeric",
    "name": "Scale Factor and Similarity (Numeric)",
    "topic": "prealgebra",
    "subtopic": "core_prealgebra",
    "difficulty_levels": ["level_1", "level_2", "level_3", "level_4", "level_5"],
    "enabled": True,
}

INSTRUCTIONS = [
    "Solve: {problem}",
    "Find the missing measurement: {problem}",
    "Use the scale factor: {problem}",
    "Work with the similar figures: {problem}",
]

LEVEL_SPEC_CAPS = {"level_1": 900, "level_2": 1000, "level_3": 1200, "level_4": 1400, "level_5": 1600}
FAMILY_CAPS = {
    "level_1": {"simple_scale_up": 900},
    "level_2": {"simple_scale_down": 1000},
    "level_3": {"missing_original": 1200},
    "level_4": {"fraction_scale": 1400},
    "level_5": {"similar_sides_multi": 1600},
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
    family = spec["family"]
    v = spec["values"]
    if family == "simple_scale_up":
        return v[0] * v[1]
    if family == "simple_scale_down":
        return Fraction(v[0], v[1])
    if family == "missing_original":
        return Fraction(v[0], v[1])
    if family == "fraction_scale":
        return Fraction(v[0] * v[1], v[2])
    if family == "similar_sides_multi":
        return Fraction(v[2] * v[3], v[0])
    raise ValueError(f"Unknown family: {family}")


def _problem_text(spec: dict) -> str:
    family = spec["family"]
    v = spec["values"]
    if family == "simple_scale_up":
        return f"A figure is enlarged by a scale factor of {v[1]}. If a side was {v[0]}, what is the new side length?"
    if family == "simple_scale_down":
        return f"A figure is reduced by a scale factor of 1/{v[1]}. If a side was {v[0]}, what is the new side length?"
    if family == "missing_original":
        return f"A similar figure has scale factor {v[1]}. A side in the new figure is {v[0]}. What was the corresponding side in the original figure?"
    if family == "fraction_scale":
        return f"A side of length {v[0]} is scaled by a factor of {v[1]}/{v[2]}. What is the new length?"
    if family == "similar_sides_multi":
        return f"Two similar figures have corresponding sides {v[0]} and {v[2]}. If another side on the smaller figure is {v[1]}, what is the matching side on the larger figure?"
    raise ValueError(f"Unknown family: {family}")


def _sample_from_spec(spec: dict, difficulty: str, instruction_idx: int = 0) -> dict:
    problem = _problem_text(spec)
    answer = _fmt(_solve(spec))
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
    return make_sample(module_id=MODULE_INFO["module_id"], topic=MODULE_INFO["topic"], subtopic=MODULE_INFO["subtopic"], difficulty=difficulty, instruction=instruction, input_text=problem, answer=answer, metadata=metadata)


def iter_level1_specs() -> Iterable[dict]:
    emitted = 0
    for side in range(1, 51):
        for factor in range(2, 13):
            yield {"family": "simple_scale_up", "values": (side, factor), "canonical_key": f"simple_scale_up:{side}:{factor}", "case_id": f"simple_scale_up:{side}:{factor}", "family_id": "simple_scale_up"}
            emitted += 1
            if emitted >= FAMILY_CAPS["level_1"]["simple_scale_up"]:
                return


def iter_level2_specs() -> Iterable[dict]:
    emitted = 0
    for side in range(2, 101):
        for factor in range(2, 13):
            if side % factor != 0:
                continue
            yield {"family": "simple_scale_down", "values": (side, factor), "canonical_key": f"simple_scale_down:{side}:{factor}", "case_id": f"simple_scale_down:{side}:{factor}", "family_id": "simple_scale_down"}
            emitted += 1
            if emitted >= FAMILY_CAPS["level_2"]["simple_scale_down"]:
                return


def iter_level3_specs() -> Iterable[dict]:
    emitted = 0
    for new_side in range(2, 121):
        for factor in range(2, 13):
            if new_side % factor != 0:
                continue
            yield {"family": "missing_original", "values": (new_side, factor), "canonical_key": f"missing_original:{new_side}:{factor}", "case_id": f"missing_original:{new_side}:{factor}", "family_id": "missing_original"}
            emitted += 1
            if emitted >= FAMILY_CAPS["level_3"]["missing_original"]:
                return


def iter_level4_specs() -> Iterable[dict]:
    emitted = 0
    for side in range(1, 41):
        for num in range(2, 13):
            for den in range(2, 13):
                ans = Fraction(side * num, den)
                if ans.denominator > 12:
                    continue
                yield {"family": "fraction_scale", "values": (side, num, den), "canonical_key": f"fraction_scale:{side}:{num}:{den}", "case_id": f"fraction_scale:{side}:{num}:{den}", "family_id": "fraction_scale"}
                emitted += 1
                if emitted >= FAMILY_CAPS["level_4"]["fraction_scale"]:
                    return


def iter_level5_specs() -> Iterable[dict]:
    emitted = 0
    for small_ref in range(2, 26):
        for small_other in range(1, 31):
            for large_ref in range(small_ref + 1, 81):
                ans = Fraction(small_other * large_ref, small_ref)
                if ans.denominator > 12:
                    continue
                yield {"family": "similar_sides_multi", "values": (small_ref, small_other, large_ref, small_other), "canonical_key": f"similar_sides_multi:{small_ref}:{small_other}:{large_ref}", "case_id": f"similar_sides_multi:{small_ref}:{small_other}:{large_ref}", "family_id": "similar_sides_multi"}
                emitted += 1
                if emitted >= FAMILY_CAPS["level_5"]["similar_sides_multi"]:
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


