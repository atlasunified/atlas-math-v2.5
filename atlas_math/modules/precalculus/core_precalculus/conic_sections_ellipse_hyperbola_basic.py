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
    "module_id": "precalculus.conic_sections_ellipse_hyperbola_basic",
    "name": "Conic Sections Ellipse Hyperbola Basic",
    "topic": "precalculus",
    "subtopic": "core_precalculus",
    "difficulty_levels": ["level_1", "level_2", "level_3", "level_4", "level_5"],
    "enabled": True,
}
INSTRUCTIONS = [
    "Analyze the conic section: {problem}",
    "Find the requested conic features: {problem}",
    "Determine the ellipse or hyperbola information: {problem}",
]

def _emit(level, rows):
    for idx, row in enumerate(rows):
        if idx >= LEVEL_SPEC_CAPS[level]:
            return
        yield _spec(*row)

def iter_level1_specs():
    return _emit("level_1", [
        ("classify", ("x2_over_plus_y2_over",), "Classify the conic: x^2/25 + y^2/9 = 1.", "ellipse"),
        ("classify", ("x2_over_minus_y2_over",), "Classify the conic: x^2/16 - y^2/4 = 1.", "hyperbola"),
        ("center", ((0,0),), "Find the center of x^2/36 + y^2/4 = 1.", "(0, 0)"),
    ])

def iter_level2_specs():
    return _emit("level_2", [
        ("ellipse_axes", (25,9), "For x^2/25 + y^2/9 = 1, find the lengths of the major and minor axes.", "major axis 10, minor axis 6"),
        ("hyperbola_vertices", (16,9), "Find the vertices of x^2/16 - y^2/9 = 1.", "(-4, 0) and (4, 0)"),
        ("ellipse_vertices", (36,4), "Find the vertices of x^2/36 + y^2/4 = 1.", "(-6, 0) and (6, 0)"),
    ])

def iter_level3_specs():
    return _emit("level_3", [
        ("translated_center", ((2,-1),), "Find the center of (x - 2)^2/16 + (y + 1)^2/25 = 1.", "(2, -1)"),
        ("major_axis_direction", (16,25), "Does (x - 2)^2/16 + (y + 1)^2/25 = 1 have a horizontal or vertical major axis?", "vertical"),
        ("hyperbola_orientation", (9,4), "Is the transverse axis horizontal or vertical for y^2/9 - x^2/4 = 1?", "vertical"),
    ])

def iter_level4_specs():
    return _emit("level_4", [
        ("ellipse_foci", (25,9), "Find the foci of x^2/25 + y^2/9 = 1.", "(-4, 0) and (4, 0)"),
        ("hyperbola_foci", (16,9), "Find the foci of x^2/16 - y^2/9 = 1.", "(-5, 0) and (5, 0)"),
        ("hyperbola_asymptotes", (4,3), "Find the asymptotes of x^2/16 - y^2/9 = 1.", "y = (3/4)x and y = -(3/4)x"),
    ])

def iter_level5_specs():
    return _emit("level_5", [
        ("write_ellipse", ((1,-2),5,3), "Write the standard form of the ellipse centered at (1, -2) with horizontal semi-major axis 5 and semi-minor axis 3.", "(x - 1)^2/25 + (y + 2)^2/9 = 1"),
        ("write_hyperbola", ((-3,4),4,2), "Write the standard form of the hyperbola centered at (-3, 4) with horizontal transverse semi-axis 4 and conjugate semi-axis 2.", "(x + 3)^2/16 - (y - 4)^2/4 = 1"),
        ("eccentricity", (25,9), "Find the eccentricity of x^2/25 + y^2/9 = 1.", "4/5"),
    ])


