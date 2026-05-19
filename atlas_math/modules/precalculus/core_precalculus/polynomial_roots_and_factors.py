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
    "module_id": "precalculus.polynomial_roots_and_factors",
    "name": "Polynomial Roots and Factors",
    "topic": "precalculus",
    "subtopic": "core_precalculus",
    "difficulty_levels": ["level_1", "level_2", "level_3", "level_4", "level_5"],
    "enabled": True,
}
INSTRUCTIONS = [
    "Find the requested roots or factors: {problem}",
    "Determine the polynomial roots or factors: {problem}",
    "Identify the zeros or factorization: {problem}",
]

def _emit(level, rows):
    cap = LEVEL_SPEC_CAPS[level]
    for idx, row in enumerate(rows):
        if idx >= cap:
            return
        family, values, prompt, answer = row
        yield _spec(family, values, prompt, answer)

def iter_level1_specs():
    return _emit("level_1", [
        ("roots_linear", ("x-4",), "Find the root of p(x) = x - 4.", "x = 4"),
        ("roots_linear", ("x+7",), "Find the root of p(x) = x + 7.", "x = -7"),
    ])

def iter_level2_specs():
    return _emit("level_2", [
        ("factor_from_root", (3,), "A polynomial has root x = 3. Give one corresponding linear factor.", "x - 3"),
        ("factor_from_root", (-5,), "A polynomial has root x = -5. Give one corresponding linear factor.", "x + 5"),
        ("roots_factored", ("(x-2)(x+1)",), "Find the roots of p(x) = (x - 2)(x + 1).", "x = 2, -1"),
    ])

def iter_level3_specs():
    return _emit("level_3", [
        ("roots_quadratic", ("x^2-5x+6",), "Find the roots of p(x) = x^2 - 5x + 6.", "x = 2, 3"),
        ("roots_quadratic", ("x^2+x-6",), "Find the roots of p(x) = x^2 + x - 6.", "x = -3, 2"),
        ("factored_form", (2, -3), "Write a monic quadratic with roots 2 and -3 in factored form.", "(x - 2)(x + 3)"),
    ])

def iter_level4_specs():
    return _emit("level_4", [
        ("roots_cubic", ("(x-1)(x+2)(x-4)",), "Find the roots of p(x) = (x - 1)(x + 2)(x - 4).", "x = 1, -2, 4"),
        ("factors_from_roots", (-1, 2, 5), "Give the factored form of a monic cubic with roots -1, 2, and 5.", "(x + 1)(x - 2)(x - 5)"),
    ])

def iter_level5_specs():
    return _emit("level_5", [
        ("multiplicity", (2, 3, -1, 1), "Write a polynomial in factored form with roots 2 (double root) and -1.", "(x - 2)^2(x + 1)"),
        ("multiplicity", (-3, 2, 4, 1), "Write a polynomial in factored form with roots -3 (double root) and 4.", "(x + 3)^2(x - 4)"),
        ("roots_multiplicity", ("(x+1)^2(x-5)",), "Find the roots of p(x) = (x + 1)^2(x - 5), including multiplicity.", "x = -1 (mult. 2), 5"),
    ])


