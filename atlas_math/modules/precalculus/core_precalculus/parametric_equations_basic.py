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
    "module_id": "precalculus.parametric_equations_basic",
    "name": "Parametric Equations Basic",
    "topic": "precalculus",
    "subtopic": "core_precalculus",
    "difficulty_levels": ["level_1", "level_2", "level_3", "level_4", "level_5"],
    "enabled": True,
}
INSTRUCTIONS = [
    "Work with the parametric equations: {problem}",
    "Eliminate the parameter or evaluate the motion: {problem}",
    "Find the requested parametric information: {problem}",
]

def _emit(level, rows):
    for idx, row in enumerate(rows):
        if idx >= LEVEL_SPEC_CAPS[level]:
            return
        yield _spec(*row)

def iter_level1_specs():
    return _emit("level_1", [
        ("evaluate_point", ("x=t+1","y=2t-3",2), "For x = t + 1 and y = 2t - 3, find the point when t = 2.", "(3, 1)"),
        ("evaluate_point", ("x=3-t","y=t+4",-1), "For x = 3 - t and y = t + 4, find the point when t = -1.", "(4, 3)"),
        ("direction", ("x=t","y=2t",), "As t increases, in what general direction does the point move for x = t, y = 2t?", "up and right"),
    ])

def iter_level2_specs():
    return _emit("level_2", [
        ("eliminate_linear", (), "Eliminate the parameter: x = t + 2, y = 3t - 1.", "y = 3x - 7"),
        ("eliminate_linear", (), "Eliminate the parameter: x = 4 - 2t, y = t + 5.", "x = 14 - 2y"),
        ("find_t_from_point", ("x=2t+1","y=t-4",(7,-1)), "Find t for the point (7, -1) on x = 2t + 1, y = t - 4.", "3"),
    ])

def iter_level3_specs():
    return _emit("level_3", [
        ("quadratic_path", (), "Eliminate the parameter: x = t, y = t^2 + 1.", "y = x^2 + 1"),
        ("circle_param", (), "What curve is described by x = 3 cos t, y = 3 sin t?", "circle of radius 3 centered at the origin"),
        ("line_segment_range", (), "For x = 1 + 2t and y = 5 - t with 0 <= t <= 3, find the endpoints of the traced segment.", "(1, 5) and (7, 2)"),
    ])

def iter_level4_specs():
    return _emit("level_4", [
        ("velocity", ("x=t^2","y=3t",2), "For x = t^2 and y = 3t, find dx/dt and dy/dt at t = 2.", "dx/dt = 4, dy/dt = 3"),
        ("slope_dy_dx", ("x=t^2+1","y=t^3",1), "For x = t^2 + 1 and y = t^3, find dy/dx at t = 1.", "3/2"),
        ("same_point", (), "Can x = t^2 and y = t^3 pass through the origin for more than one t-value?", "no"),
    ])

def iter_level5_specs():
    return _emit("level_5", [
        ("second_derivative", (), "For x = t^2 and y = t^3, find d^2y/dx^2 at t = 1.", "3/4"),
        ("eliminate_trig", (), "Eliminate the parameter: x = 2 cos t, y = 5 sin t.", "x^2/4 + y^2/25 = 1"),
        ("intercept_param", (), "For x = 4 - t and y = t^2 - 1, find the y-intercept(s) of the Cartesian curve.", "(0, 15)"),
    ])


