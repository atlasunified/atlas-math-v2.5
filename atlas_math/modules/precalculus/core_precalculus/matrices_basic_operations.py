from __future__ import annotations

import random
from typing import Iterable

from atlas_math.modules.shared.common import make_sample

LEVEL_SPEC_CAPS = {"level_1": 400, "level_2": 500, "level_3": 600, "level_4": 700, "level_5": 800}
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

def _spec(family: str, values: tuple, prompt: str, answer: str, metadata_extra: dict | None = None):
    canonical = ":".join([family] + [str(v) for v in values])
    meta = metadata_extra.copy() if metadata_extra else {}
    return {
        "family": family,
        "values": values,
        "prompt": prompt,
        "answer": answer,
        "canonical_key": canonical,
        "case_id": canonical,
        "family_id": family,
        "meta": meta,
    }

def _sample_from_spec(spec: dict, difficulty: str, instruction_idx: int = 0) -> dict:
    metadata = {
        "family": spec["family"],
        "level_number": _level_num(difficulty),
        "structured": True,
        "canonical_key": spec["canonical_key"],
        "case_id": spec["case_id"],
        "family_id": spec["family_id"],
        "template_id": spec["family"],
        "final_answer": spec["answer"],
        "values": list(spec.get("values", [])),
    }
    metadata.update(spec.get("meta", {}))
    instruction = INSTRUCTIONS[instruction_idx % len(INSTRUCTIONS)].format(problem=spec["prompt"])
    return make_sample(
        module_id=MODULE_INFO["module_id"],
        topic=MODULE_INFO["topic"],
        subtopic=MODULE_INFO["subtopic"],
        difficulty=difficulty,
        instruction=instruction,
        input_text=spec["prompt"],
        answer=spec["answer"],
        metadata=metadata,
    )

def _iter_specs_for_difficulty(difficulty: str) -> Iterable[dict]:
    level_num = _level_num(difficulty)
    fn = globals().get(f"iter_level{level_num}_specs") or globals().get(f"iter_level_{level_num}_specs")
    if fn is None:
        return ()
    return fn()

def curriculum() -> dict:
    return {level: {"capacity": LEVEL_SPEC_CAPS[level]} for level in LEVEL_SPEC_CAPS}

def estimate_capacity(difficulty: str | None = None) -> dict:
    if difficulty is None:
        return {k: v.copy() for k, v in CAPACITY_HINTS.items()}
    level = f"level_{_level_num(difficulty)}"
    return CAPACITY_HINTS[level].copy()

def iter_samples(difficulty: str) -> Iterable[dict]:
    for idx, spec in enumerate(_take(_iter_specs_for_difficulty(difficulty), MAX_ITER_SAMPLES)):
        yield _sample_from_spec(spec, difficulty, idx)

def generate(difficulty: str, seed: int | str | None = None) -> dict:
    level = f"level_{_level_num(difficulty)}"
    limit = min(MAX_SPEC_PREFIX, LEVEL_SPEC_CAPS[level] * MAX_GENERATE_MULTIPLIER)
    pool = list(_take(_iter_specs_for_difficulty(difficulty), limit))
    if not pool:
        raise ValueError(f"No specs available for {difficulty}")
    rng = random.Random(_stable_seed(MODULE_INFO["module_id"], difficulty, seed if seed is not None else "default"))
    spec = pool[rng.randrange(len(pool))]
    return _sample_from_spec(spec, difficulty, rng.randrange(len(INSTRUCTIONS)))

def generate_unique(difficulty: str, limit: int | None = None, seed: int | str | None = None) -> list[dict]:
    level = f"level_{_level_num(difficulty)}"
    max_items = LEVEL_SPEC_CAPS[level] if limit is None else min(int(limit), LEVEL_SPEC_CAPS[level])
    pool = list(_take(_iter_specs_for_difficulty(difficulty), min(MAX_SPEC_PREFIX, LEVEL_SPEC_CAPS[level] * MAX_GENERATE_MULTIPLIER)))
    rng = random.Random(_stable_seed(MODULE_INFO["module_id"], difficulty, seed if seed is not None else "unique"))
    rng.shuffle(pool)
    return [_sample_from_spec(spec, difficulty, idx) for idx, spec in enumerate(pool[:max_items])]

MODULE_INFO = {
    "module_id": "precalculus.matrices_basic_operations",
    "name": "Matrices Basic Operations",
    "topic": "precalculus",
    "subtopic": "core_precalculus",
    "difficulty_levels": ["level_1", "level_2", "level_3", "level_4", "level_5"],
    "enabled": True,
}
INSTRUCTIONS = ['Compute the matrix operation: {problem}', 'Work with the matrices and simplify: {problem}', 'Find the resulting matrix or entry: {problem}']

def _emit(level, rows):
    for idx, row in enumerate(rows):
        if idx >= LEVEL_SPEC_CAPS[level]:
            return
        yield _spec(*row)

def iter_level1_specs():
    return _emit("level_1", [('add_2x2', (((1, 2), (3, 4)), ((5, 6), (7, 8))), 'Add [[1, 2], [3, 4]] + [[5, 6], [7, 8]].', '[[6, 8], [10, 12]]'), ('scalar_2x2', (2, ((1, -1), (0, 3))), 'Compute 2[[1, -1], [0, 3]].', '[[2, -2], [0, 6]]'), ('subtract_2x2', (((4, 5), (6, 7)), ((1, 2), (3, 4))), 'Compute [[4, 5], [6, 7]] - [[1, 2], [3, 4]].', '[[3, 3], [3, 3]]')])
def iter_level2_specs():
    return _emit("level_2", [('entry_lookup', (((2, 5), (7, 1)), 2, 1), 'For A = [[2, 5], [7, 1]], find a_(2,1).', '7'), ('multiply_scalar', (-3, ((2, 0), (-1, 4))), 'Compute -3[[2, 0], [-1, 4]].', '[[-6, 0], [3, -12]]'), ('add_2x2', (((-1, 3), (2, 0)), ((4, -2), (5, 1))), 'Add [[-1, 3], [2, 0]] + [[4, -2], [5, 1]].', '[[3, 1], [7, 1]]')])
def iter_level3_specs():
    return _emit("level_3", [('mul_2x2', (((1, 2), (3, 4)), ((2, 0), (1, 5))), 'Multiply [[1, 2], [3, 4]] by [[2, 0], [1, 5]].', '[[4, 10], [10, 20]]'), ('mul_2x1', (((2, -1), (0, 3)), (4, 5)), 'Multiply [[2, -1], [0, 3]] by [[4], [5]].', '[[3], [15]]'), ('identity_mul', (((3, 1), (2, 4)),), 'Compute I[[3, 1], [2, 4]] for the 2x2 identity matrix I.', '[[3, 1], [2, 4]]')])
def iter_level4_specs():
    return _emit("level_4", [('mul_2x2', (((0, 1), (2, 3)), ((4, -1), (5, 2))), 'Multiply [[0, 1], [2, 3]] by [[4, -1], [5, 2]].', '[[5, 2], [23, 4]]'), ('transpose', (((1, 4, 7), (2, 5, 8)),), 'Find the transpose of [[1, 4, 7], [2, 5, 8]].', '[[1, 2], [4, 5], [7, 8]]'), ('difference', (((8, 3), (-2, 6)), ((5, 1), (4, -1))), 'Compute [[8, 3], [-2, 6]] - [[5, 1], [4, -1]].', '[[3, 2], [-6, 7]]')])
def iter_level5_specs():
    return _emit("level_5", [('mul_2x2', (((2, 1), (-1, 3)), ((4, 0), (5, 2))), 'Multiply [[2, 1], [-1, 3]] by [[4, 0], [5, 2]].', '[[13, 2], [11, 6]]'), ('distribute_scalar', (3, ((1, 2), (3, 4)), ((0, 1), (1, 0))), 'Compute 3([[1, 2], [3, 4]] + [[0, 1], [1, 0]]).', '[[3, 9], [12, 12]]'), ('square_matrix', (((1, 1), (1, 0)),), 'Compute [[1, 1], [1, 0]]^2.', '[[2, 1], [1, 1]]')])


