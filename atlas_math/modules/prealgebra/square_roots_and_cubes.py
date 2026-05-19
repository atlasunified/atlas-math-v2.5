from __future__ import annotations

import random
from typing import Iterable

from atlas_math.modules.shared.common import make_sample

MODULE_INFO = {
    "module_id": "prealgebra.square_roots_and_cubes",
    "name": "Square Roots and Cubes",
    "topic": "prealgebra",
    "subtopic": "core_prealgebra",
    "difficulty_levels": ["level_1", "level_2", "level_3", "level_4", "level_5"],
    "enabled": True,
}

INSTRUCTIONS = [
    "Evaluate: {problem}",
    "Find the value: {problem}",
    "Work out the root or power: {problem}",
    "Simplify: {problem}",
]

LEVEL_SPEC_CAPS = {"level_1": 600, "level_2": 800, "level_3": 1000, "level_4": 1200, "level_5": 1400}
FAMILY_CAPS = {
    "level_1": {"perfect_squares": 600},
    "level_2": {"perfect_cubes": 800},
    "level_3": {"square_and_cube_mix": 1000},
    "level_4": {"signed_cubes": 1200},
    "level_5": {"nested_small": 1400},
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


def _solve(spec: dict):
    family = spec["family"]
    v = spec["values"]
    if family == "perfect_squares":
        return v[0]
    if family == "perfect_cubes":
        return v[0]
    if family == "square_and_cube_mix":
        return v[2] if v[1] == "sqrt" else v[2] ** 3
    if family == "signed_cubes":
        return v[0]
    if family == "nested_small":
        return v[0]
    raise ValueError(f"Unknown family: {family}")


def _problem_text(spec: dict) -> str:
    family = spec["family"]
    v = spec["values"]
    if family == "perfect_squares":
        return f"√{v[0] ** 2}"
    if family == "perfect_cubes":
        return f"∛{v[0] ** 3}"
    if family == "square_and_cube_mix":
        return f"√{v[2] ** 2}" if v[1] == "sqrt" else f"{v[2]}^3"
    if family == "signed_cubes":
        return f"∛({v[0] ** 3})"
    if family == "nested_small":
        return f"√{(v[0] ** 2) * (v[1] ** 2)} / {v[1]}"
    raise ValueError(f"Unknown family: {family}")


def _sample_from_spec(spec: dict, difficulty: str, instruction_idx: int = 0) -> dict:
    problem = _problem_text(spec)
    answer = str(_solve(spec))
    metadata = {"family": spec["family"], "level_number": _level_num(difficulty), "structured": True, "canonical_key": spec["canonical_key"], "case_id": spec["case_id"], "family_id": spec["family_id"], "template_id": spec["family"], "final_answer": answer, "values": list(spec["values"])}
    instruction = INSTRUCTIONS[instruction_idx % len(INSTRUCTIONS)].format(problem=problem)
    return make_sample(module_id=MODULE_INFO["module_id"], topic=MODULE_INFO["topic"], subtopic=MODULE_INFO["subtopic"], difficulty=difficulty, instruction=instruction, input_text=problem, answer=answer, metadata=metadata)


def iter_level1_specs() -> Iterable[dict]:
    for n in range(1, FAMILY_CAPS["level_1"]["perfect_squares"] + 1):
        yield {"family": "perfect_squares", "values": (n,), "canonical_key": f"perfect_squares:{n}", "case_id": f"perfect_squares:{n}", "family_id": "perfect_squares"}


def iter_level2_specs() -> Iterable[dict]:
    for n in range(1, FAMILY_CAPS["level_2"]["perfect_cubes"] + 1):
        yield {"family": "perfect_cubes", "values": (n,), "canonical_key": f"perfect_cubes:{n}", "case_id": f"perfect_cubes:{n}", "family_id": "perfect_cubes"}


def iter_level3_specs() -> Iterable[dict]:
    emitted = 0
    for op in ("sqrt", "cube"):
        for n in range(1, 101):
            yield {"family": "square_and_cube_mix", "values": (0, op, n), "canonical_key": f"square_and_cube_mix:{op}:{n}", "case_id": f"square_and_cube_mix:{op}:{n}", "family_id": "square_and_cube_mix"}
            emitted += 1
            if emitted >= FAMILY_CAPS["level_3"]["square_and_cube_mix"]:
                return


def iter_level4_specs() -> Iterable[dict]:
    emitted = 0
    for n in range(-50, 51):
        yield {"family": "signed_cubes", "values": (n,), "canonical_key": f"signed_cubes:{n}", "case_id": f"signed_cubes:{n}", "family_id": "signed_cubes"}
        emitted += 1
        if emitted >= FAMILY_CAPS["level_4"]["signed_cubes"]:
            return


def iter_level5_specs() -> Iterable[dict]:
    emitted = 0
    for a in range(1, 101):
        for b in range(1, 21):
            yield {"family": "nested_small", "values": (a, b), "canonical_key": f"nested_small:{a}:{b}", "case_id": f"nested_small:{a}:{b}", "family_id": "nested_small"}
            emitted += 1
            if emitted >= FAMILY_CAPS["level_5"]["nested_small"]:
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


