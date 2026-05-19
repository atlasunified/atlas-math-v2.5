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
    "module_id": "precalculus.rational_function_asymptotes_basic",
    "name": "Rational Function Asymptotes Basic",
    "topic": "precalculus",
    "subtopic": "core_precalculus",
    "difficulty_levels": ["level_1", "level_2", "level_3", "level_4", "level_5"],
    "enabled": True,
}
INSTRUCTIONS = [
    "Find the asymptote(s): {problem}",
    "Determine the vertical or horizontal asymptote(s): {problem}",
    "Identify the asymptotes of the rational function: {problem}",
]

def _emit(level, rows):
    cap = LEVEL_SPEC_CAPS[level]
    for idx, (expr, answer, values) in enumerate(rows):
        if idx >= cap:
            return
        yield _spec("rational_asymptotes", values, f"Find the asymptote(s) of f(x) = {expr}.", answer)

def iter_level1_specs():
    return _emit("level_1", [
        ("1/x", "vertical: x = 0; horizontal: y = 0", ("1/x",)),
        ("3/(x-2)", "vertical: x = 2; horizontal: y = 0", ("3/(x-2)",)),
    ])

def iter_level2_specs():
    return _emit("level_2", [
        ("(x+1)/(x-4)", "vertical: x = 4; horizontal: y = 1", ("lin_over_lin", 4, 1)),
        ("(2x-3)/(x+5)", "vertical: x = -5; horizontal: y = 2", ("lin_over_lin", -5, 2)),
    ])

def iter_level3_specs():
    return _emit("level_3", [
        ("(x^2+1)/(x-3)", "vertical: x = 3; horizontal: none", ("deg_num_gt_den", 3)),
        ("(x+2)/(x^2+1)", "vertical: none; horizontal: y = 0", ("no_real_va", 0)),
        ("5/(x^2-9)", "vertical: x = -3 and x = 3; horizontal: y = 0", ("two_va", -3, 3)),
    ])

def iter_level4_specs():
    return _emit("level_4", [
        ("(3x^2+1)/(x^2-4)", "vertical: x = -2 and x = 2; horizontal: y = 3", ("quad_over_quad", -2, 2, 3)),
        ("(x^2-1)/(x^2+4x+4)", "vertical: x = -2; horizontal: y = 1", ("quad_over_quad", -2, 1)),
    ])

def iter_level5_specs():
    return _emit("level_5", [
        ("(2x^3-1)/(x^2-1)", "vertical: x = -1 and x = 1; horizontal: none", ("cubic_over_quad", -1, 1)),
        ("(x^2+3x)/(x^2-9)", "vertical: x = -3 and x = 3; horizontal: y = 1", ("quad_over_quad", -3, 3, 1)),
        ("(4x-7)/(x^2-16)", "vertical: x = -4 and x = 4; horizontal: y = 0", ("lin_over_quad", -4, 4, 0)),
    ])


