from __future__ import annotations

import itertools
import math
import random
from fractions import Fraction
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
    "module_id": "precalculus.vectors_dot_product",
    "name": "Vectors Dot Product",
    "topic": "precalculus",
    "subtopic": "core_precalculus",
    "difficulty_levels": ["level_1", "level_2", "level_3", "level_4", "level_5"],
    "enabled": True,
}
INSTRUCTIONS = [
    "Evaluate the dot product or related quantity: {problem}",
    "Find the requested vector-angle information: {problem}",
    "Use the dot product: {problem}",
]

def _emit(level, rows):
    for idx, row in enumerate(rows):
        if idx >= LEVEL_SPEC_CAPS[level]:
            return
        yield _spec(*row)

def iter_level1_specs():
    return _emit("level_1", [
        ("dot", ((2,3),(4,-1)), "Find <2, 3> · <4, -1>.", "5"),
        ("dot", ((-1,5),(6,2)), "Find <-1, 5> · <6, 2>.", "4"),
        ("dot", ((3,0),(0,7)), "Find <3, 0> · <0, 7>.", "0"),
    ])

def iter_level2_specs():
    return _emit("level_2", [
        ("orthogonal", ((3,4),(4,-3)), "Are <3, 4> and <4, -3> orthogonal?", "yes"),
        ("orthogonal", ((1,2),(2,1)), "Are <1, 2> and <2, 1> orthogonal?", "no"),
        ("magnitude_square", ((-6,8),), "Use the dot product to find |<-6, 8>|^2.", "100"),
    ])

def iter_level3_specs():
    return _emit("level_3", [
        ("angle", ((1,0),(0,1)), "Find the angle between <1, 0> and <0, 1>.", "90°"),
        ("angle", ((1,0),(1,1)), "Find the angle between <1, 0> and <1, 1>.", "45°"),
        ("proj_scalar", ((3,4),(5,0)), "Find the scalar projection of <3, 4> onto <5, 0>.", "3"),
    ])

def iter_level4_specs():
    return _emit("level_4", [
        ("solve_k_orth", ((2,1),(1,'k')), "Find k so that <2, 1> and <1, k> are orthogonal.", "-2"),
        ("cos_angle", ((2,2),(3,0)), "Find cos θ between <2, 2> and <3, 0>.", "sqrt(2)/2"),
        ("vector_projection", ((3,4),(5,0)), "Find the vector projection of <3, 4> onto <5, 0>.", "<3, 0>"),
    ])

def iter_level5_specs():
    return _emit("level_5", [
        ("work", (10,60), "A force of magnitude 10 acts at an angle of 60° to the displacement of length 4. Find the work.", "20"),
        ("solve_component", ((1,2),(3,'k'),11), "Find k if <1, 2> · <3, k> = 11.", "4"),
        ("compare_angles", ((2,1),(1,2),((2,1),(-1,2))), "Which pair makes the larger angle: <2, 1> with <1, 2> or <2, 1> with <-1, 2>?", "<2, 1> with <-1, 2>"),
    ])


