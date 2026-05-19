from __future__ import annotations

import random
from fractions import Fraction
from typing import Iterable

from atlas_math.modules.shared.common import make_sample

MODULE_INFO = {
    "module_id": "prealgebra.sequence_next_term_arithmetic",
    "name": "Sequence Next Term Arithmetic",
    "topic": "prealgebra",
    "subtopic": "core_prealgebra",
    "difficulty_levels": ["level_1", "level_2", "level_3", "level_4", "level_5"],
    "enabled": True,
}
INSTRUCTIONS = [
    "Find the next term: {problem}",
    "Complete the arithmetic sequence: {problem}",
    "Use the common difference to continue the sequence: {problem}",
    "Determine the next number: {problem}",
]
LEVEL_SPEC_CAPS = {"level_1": 900, "level_2": 1100, "level_3": 1300, "level_4": 1500, "level_5": 1700}
FAMILY_CAPS = {"level_1": {"positive_difference": 900}, "level_2": {"negative_difference": 1100}, "level_3": {"signed_start": 1300}, "level_4": {"large_step": 1500}, "level_5": {"mixed_signed_large": 1700}}
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

def _problem_text(spec: dict) -> str:
    start, diff = spec["values"]
    terms = [start + i * diff for i in range(4)]
    return f"What is the next term in the arithmetic sequence {terms[0]}, {terms[1]}, {terms[2]}, {terms[3]}?"

def _sample_from_spec(spec: dict, difficulty: str, instruction_idx: int = 0) -> dict:
    problem = _problem_text(spec)
    start, diff = spec["values"]
    answer = str(start + 4 * diff)
    metadata = {"family": spec["family"], "level_number": _level_num(difficulty), "structured": True, "canonical_key": spec["canonical_key"], "case_id": spec["case_id"], "family_id": spec["family_id"], "template_id": spec["family"], "final_answer": answer, "values": list(spec["values"])}
    instruction = INSTRUCTIONS[instruction_idx % len(INSTRUCTIONS)].format(problem=problem)
    return make_sample(module_id=MODULE_INFO["module_id"], topic=MODULE_INFO["topic"], subtopic=MODULE_INFO["subtopic"], difficulty=difficulty, instruction=instruction, input_text=problem, answer=answer, metadata=metadata)

def _emit(family: str, starts, diffs, limit: int):
    emitted = 0
    for start in starts:
        for diff in diffs:
            yield {"family": family, "values": (start, diff), "canonical_key": f"{family}:{start}:{diff}", "case_id": f"{family}:{start}:{diff}", "family_id": family}
            emitted += 1
            if emitted >= limit:
                return

def iter_level1_specs() -> Iterable[dict]:
    yield from _emit("positive_difference", range(1, 51), range(1, 13), FAMILY_CAPS["level_1"]["positive_difference"])

def iter_level2_specs() -> Iterable[dict]:
    yield from _emit("negative_difference", range(10, 101), range(-12, 0), FAMILY_CAPS["level_2"]["negative_difference"])

def iter_level3_specs() -> Iterable[dict]:
    yield from _emit("signed_start", range(-50, 51), list(range(-10, 0)) + list(range(1, 11)), FAMILY_CAPS["level_3"]["signed_start"])

def iter_level4_specs() -> Iterable[dict]:
    yield from _emit("large_step", range(-100, 101), list(range(-25, -9)) + list(range(10, 26)), FAMILY_CAPS["level_4"]["large_step"])

def iter_level5_specs() -> Iterable[dict]:
    yield from _emit("mixed_signed_large", range(-200, 201), list(range(-40, -9)) + list(range(10, 41)), FAMILY_CAPS["level_5"]["mixed_signed_large"])

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


