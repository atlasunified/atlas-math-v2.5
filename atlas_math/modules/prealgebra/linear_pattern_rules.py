from __future__ import annotations

import random
from fractions import Fraction
from typing import Iterable

from atlas_math.modules.shared.common import make_sample

MODULE_INFO = {
    "module_id": "prealgebra.linear_pattern_rules",
    "name": "Linear Pattern Rules",
    "topic": "prealgebra",
    "subtopic": "core_prealgebra",
    "difficulty_levels": ["level_1", "level_2", "level_3", "level_4", "level_5"],
    "enabled": True,
}
INSTRUCTIONS = [
    "Find the rule: {problem}",
    "Write the linear pattern rule: {problem}",
    "Determine the expression for the pattern: {problem}",
    "Use the pattern information to write a rule: {problem}",
]
LEVEL_SPEC_CAPS = {"level_1": 900, "level_2": 1100, "level_3": 1300, "level_4": 1500, "level_5": 1700}
FAMILY_CAPS = {"level_1": {"positive_slope": 900}, "level_2": {"negative_slope": 1100}, "level_3": {"table_to_rule": 1300}, "level_4": {"nth_term_large_intercept": 1500}, "level_5": {"signed_coeff_signed_intercept": 1700}}
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

def _rule(m: int, b: int) -> str:
    if b == 0:
        return f"{m}n"
    if b > 0:
        return f"{m}n + {b}"
    return f"{m}n - {abs(b)}"

def _problem_text(spec: dict) -> str:
    m, b = spec["values"]
    terms = [m * n + b for n in range(1, 5)]
    return f"The pattern has terms {terms[0]}, {terms[1]}, {terms[2]}, {terms[3]} for n = 1, 2, 3, 4. Write a rule for the nth term."

def _sample_from_spec(spec: dict, difficulty: str, instruction_idx: int = 0) -> dict:
    problem = _problem_text(spec)
    m, b = spec["values"]
    answer = _rule(m, b)
    metadata = {"family": spec["family"], "level_number": _level_num(difficulty), "structured": True, "canonical_key": spec["canonical_key"], "case_id": spec["case_id"], "family_id": spec["family_id"], "template_id": spec["family"], "final_answer": answer, "values": list(spec["values"])}
    instruction = INSTRUCTIONS[instruction_idx % len(INSTRUCTIONS)].format(problem=problem)
    return make_sample(module_id=MODULE_INFO["module_id"], topic=MODULE_INFO["topic"], subtopic=MODULE_INFO["subtopic"], difficulty=difficulty, instruction=instruction, input_text=problem, answer=answer, metadata=metadata)

def _emit(family: str, m_values, b_values, limit: int):
    emitted = 0
    for m in m_values:
        for b in b_values:
            yield {"family": family, "values": (m, b), "canonical_key": f"{family}:{m}:{b}", "case_id": f"{family}:{m}:{b}", "family_id": family}
            emitted += 1
            if emitted >= limit:
                return

def iter_level1_specs() -> Iterable[dict]:
    yield from _emit("positive_slope", range(1, 13), range(0, 16), FAMILY_CAPS["level_1"]["positive_slope"])

def iter_level2_specs() -> Iterable[dict]:
    yield from _emit("negative_slope", range(-12, 0), range(-10, 11), FAMILY_CAPS["level_2"]["negative_slope"])

def iter_level3_specs() -> Iterable[dict]:
    yield from _emit("table_to_rule", list(range(2, 16)) + list(range(-15, -1)), range(-15, 16), FAMILY_CAPS["level_3"]["table_to_rule"])

def iter_level4_specs() -> Iterable[dict]:
    yield from _emit("nth_term_large_intercept", range(1, 16), range(-40, 41), FAMILY_CAPS["level_4"]["nth_term_large_intercept"])

def iter_level5_specs() -> Iterable[dict]:
    yield from _emit("signed_coeff_signed_intercept", list(range(-20, 0)) + list(range(1, 21)), range(-30, 31), FAMILY_CAPS["level_5"]["signed_coeff_signed_intercept"])

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


