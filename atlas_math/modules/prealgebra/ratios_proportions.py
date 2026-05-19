from __future__ import annotations

import random
from fractions import Fraction
from typing import Iterable

from atlas_math.modules.shared.common import make_sample

MODULE_INFO = {
    "module_id": "prealgebra.ratios_proportions",
    "name": "Ratios and Proportions",
    "topic": "prealgebra",
    "subtopic": "core_prealgebra",
    "difficulty_levels": ["level_1", "level_2", "level_3", "level_4", "level_5"],
    "enabled": True,
}

INSTRUCTIONS = [
    "Solve: {problem}",
    "Find the missing value: {problem}",
    "Use proportional reasoning: {problem}",
    "Complete the ratio or proportion: {problem}",
]

LEVEL_SPEC_CAPS = {
    "level_1": 900,
    "level_2": 1200,
    "level_3": 1400,
    "level_4": 1600,
    "level_5": 1800,
}

FAMILY_CAPS = {
    "level_1": {"simplify_ratio": 900},
    "level_2": {"equivalent_ratio": 1200},
    "level_3": {"direct_proportion_integer": 1400},
    "level_4": {"direct_proportion_fraction": 1600},
    "level_5": {"word_proportion": 1800},
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


def _fmt(value) -> str:
    if isinstance(value, Fraction):
        return str(value.numerator) if value.denominator == 1 else f"{value.numerator}/{value.denominator}"
    return str(value)


def _solve(spec: dict):
    family = spec["family"]
    v = spec["values"]
    if family == "simplify_ratio":
        a, b, g = v
        return f"{a // g}:{b // g}"
    if family == "equivalent_ratio":
        a, b, k, missing_side = v
        return b * k if missing_side == "right" else a * k
    if family == "direct_proportion_integer":
        a, b, c = v
        return Fraction(b * c, a)
    if family == "direct_proportion_fraction":
        a, b, c_num, c_den = v
        return Fraction(b, a) * Fraction(c_num, c_den)
    if family == "word_proportion":
        items1, cost1, items2 = v
        return Fraction(cost1 * items2, items1)
    raise ValueError(f"Unknown family: {family}")


def _problem_text(spec: dict) -> str:
    family = spec["family"]
    v = spec["values"]
    if family == "simplify_ratio":
        a, b, _ = v
        return f"Simplify the ratio {a}:{b}."
    if family == "equivalent_ratio":
        a, b, k, missing_side = v
        if missing_side == "right":
            return f"Complete the equivalent ratio: {a}:{b} = {a * k}:x"
        return f"Complete the equivalent ratio: {a}:{b} = x:{b * k}"
    if family == "direct_proportion_integer":
        a, b, c = v
        return f"Solve the proportion {a}/{b} = {c}/x"
    if family == "direct_proportion_fraction":
        a, b, c_num, c_den = v
        return f"Solve the proportion {a}/{b} = {c_num}/{c_den} ÷ x? No. Instead solve {a}/{b} = {c_num}/{c_den} / x is ambiguous. Solve {a}/{b} = ({c_num}/{c_den})/x"
    if family == "word_proportion":
        items1, cost1, items2 = v
        return f"If {items1} notebooks cost ${cost1}, how much do {items2} notebooks cost at the same rate?"
    raise ValueError(f"Unknown family: {family}")


def _display_problem_text(spec: dict) -> str:
    family = spec["family"]
    v = spec["values"]
    if family == "direct_proportion_fraction":
        a, b, c_num, c_den = v
        return f"Solve the proportion {a}/{b} = ({c_num}/{c_den})/x"
    return _problem_text(spec)


def _sample_from_spec(spec: dict, difficulty: str, instruction_idx: int = 0) -> dict:
    problem = _display_problem_text(spec)
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
    limit = FAMILY_CAPS["level_1"]["simplify_ratio"]
    emitted = 0
    for g in range(2, 13):
        for a0 in range(1, 16):
            for b0 in range(1, 16):
                if a0 == b0:
                    continue
                a = a0 * g
                b = b0 * g
                yield {
                    "family": "simplify_ratio",
                    "values": (a, b, g),
                    "canonical_key": f"simplify_ratio:{a}:{b}:{g}",
                    "case_id": f"simplify_ratio:{a}:{b}:{g}",
                    "family_id": "simplify_ratio",
                }
                emitted += 1
                if emitted >= limit:
                    return


def iter_level2_specs() -> Iterable[dict]:
    limit = FAMILY_CAPS["level_2"]["equivalent_ratio"]
    emitted = 0
    for a in range(1, 16):
        for b in range(1, 16):
            for k in range(2, 13):
                for missing_side in ("right", "left"):
                    yield {
                        "family": "equivalent_ratio",
                        "values": (a, b, k, missing_side),
                        "canonical_key": f"equivalent_ratio:{a}:{b}:{k}:{missing_side}",
                        "case_id": f"equivalent_ratio:{a}:{b}:{k}:{missing_side}",
                        "family_id": "equivalent_ratio",
                    }
                    emitted += 1
                    if emitted >= limit:
                        return


def iter_level3_specs() -> Iterable[dict]:
    limit = FAMILY_CAPS["level_3"]["direct_proportion_integer"]
    emitted = 0
    for a in range(2, 16):
        for b in range(2, 21):
            for c in range(2, 21):
                if (b * c) % a != 0:
                    continue
                yield {
                    "family": "direct_proportion_integer",
                    "values": (a, b, c),
                    "canonical_key": f"direct_proportion_integer:{a}:{b}:{c}",
                    "case_id": f"direct_proportion_integer:{a}:{b}:{c}",
                    "family_id": "direct_proportion_integer",
                }
                emitted += 1
                if emitted >= limit:
                    return


def iter_level4_specs() -> Iterable[dict]:
    limit = FAMILY_CAPS["level_4"]["direct_proportion_fraction"]
    emitted = 0
    for a in range(2, 13):
        for b in range(2, 13):
            for c_num in range(1, 21):
                for c_den in range(2, 13):
                    ans = Fraction(b, a) * Fraction(c_num, c_den)
                    if ans.denominator > 12:
                        continue
                    yield {
                        "family": "direct_proportion_fraction",
                        "values": (a, b, c_num, c_den),
                        "canonical_key": f"direct_proportion_fraction:{a}:{b}:{c_num}:{c_den}",
                        "case_id": f"direct_proportion_fraction:{a}:{b}:{c_num}:{c_den}",
                        "family_id": "direct_proportion_fraction",
                    }
                    emitted += 1
                    if emitted >= limit:
                        return


def iter_level5_specs() -> Iterable[dict]:
    limit = FAMILY_CAPS["level_5"]["word_proportion"]
    emitted = 0
    for items1 in range(2, 13):
        for unit_price in range(2, 11):
            cost1 = items1 * unit_price
            for items2 in range(3, 26):
                if items2 == items1:
                    continue
                yield {
                    "family": "word_proportion",
                    "values": (items1, cost1, items2),
                    "canonical_key": f"word_proportion:{items1}:{cost1}:{items2}",
                    "case_id": f"word_proportion:{items1}:{cost1}:{items2}",
                    "family_id": "word_proportion",
                }
                emitted += 1
                if emitted >= limit:
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
    return {
        "module_id": MODULE_INFO["module_id"],
        "topic": MODULE_INFO["topic"],
        "subtopic": MODULE_INFO["subtopic"],
        "difficulty_levels": MODULE_INFO["difficulty_levels"],
        "capacity": estimate_capacity(),
    }


