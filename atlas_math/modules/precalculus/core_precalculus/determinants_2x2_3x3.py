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
    "module_id": "precalculus.determinants_2x2_3x3",
    "name": "Determinants 2x2 3x3",
    "topic": "precalculus",
    "subtopic": "core_precalculus",
    "difficulty_levels": ["level_1", "level_2", "level_3", "level_4", "level_5"],
    "enabled": True,
}
INSTRUCTIONS = ['Find the determinant: {problem}', 'Compute the determinant value: {problem}', 'Evaluate the determinant exactly: {problem}']

def _emit(level, rows):
    for idx, row in enumerate(rows):
        if idx >= LEVEL_SPEC_CAPS[level]:
            return
        yield _spec(*row)

def iter_level1_specs():
    return _emit("level_1", [('det_2x2', (((1, 2), (3, 4)),), 'Find det([[1, 2], [3, 4]]).', '-2'), ('det_2x2', (((5, 1), (2, 7)),), 'Find det([[5, 1], [2, 7]]).', '33'), ('det_2x2', (((0, 3), (-2, 6)),), 'Find det([[0, 3], [-2, 6]]).', '6')])
def iter_level2_specs():
    return _emit("level_2", [('det_2x2', (((-1, 4), (2, 5)),), 'Find det([[-1, 4], [2, 5]]).', '-13'), ('det_2x2', (((3, 0), (0, 9)),), 'Find det([[3, 0], [0, 9]]).', '27'), ('det_scale', (2, ((1, 2), (3, 4))), 'Find det(2[[1, 2], [3, 4]]).', '-8')])
def iter_level3_specs():
    return _emit("level_3", [('det_3x3_tri', (((1, 2, 0), (0, 3, 4), (0, 0, 5)),), 'Find det([[1, 2, 0], [0, 3, 4], [0, 0, 5]]).', '15'), ('det_3x3_diag', (((2, 0, 0), (0, -1, 0), (0, 0, 4)),), 'Find det([[2, 0, 0], [0, -1, 0], [0, 0, 4]]).', '-8'), ('det_3x3_zero_row', (((1, 2, 3), (0, 0, 0), (4, 5, 6)),), 'Find det([[1, 2, 3], [0, 0, 0], [4, 5, 6]]).', '0')])
def iter_level4_specs():
    return _emit("level_4", [('det_3x3_expand', (((1, 0, 2), (-1, 3, 1), (3, 2, 0)),), 'Find det([[1, 0, 2], [-1, 3, 1], [3, 2, 0]]).', '-24'), ('det_3x3_expand', (((2, 1, 0), (4, -1, 3), (1, 2, 5)),), 'Find det([[2, 1, 0], [4, -1, 3], [1, 2, 5]]).', '-31'), ('row_swap', (((1, 2), (3, 4)),), 'If matrix B is formed by swapping the two rows of [[1, 2], [3, 4]], what is det(B)?', '2')])
def iter_level5_specs():
    return _emit("level_5", [('det_3x3_expand', (((3, 1, 2), (0, -1, 4), (5, 2, 0)),), 'Find det([[3, 1, 2], [0, -1, 4], [5, 2, 0]]).', '59'), ('det_singular', (((2, 4, 6), (1, 2, 3), (0, 1, 1)),), 'Find det([[2, 4, 6], [1, 2, 3], [0, 1, 1]]).', '0'), ('det_product_rule', (-2, ((1, 2), (3, 4))), 'For A = [[1, 2], [3, 4]], find det((-2)A).', '8')])


