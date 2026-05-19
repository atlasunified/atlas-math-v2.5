from __future__ import annotations

import itertools
import math
import random
from fractions import Fraction
from typing import Dict, Iterable, List, Tuple

try:
    from atlas_math.modules.shared.common import make_sample as _shared_make_sample
except Exception:
    _shared_make_sample = None


def _compat_make_sample(*, prompt, answer, metadata=None, level=None):
    metadata = dict(metadata or {})
    difficulty = f"level_{level}" if level is not None else str(metadata.get("family_id", "level_1")).split("::", 1)[0]
    module_id = MODULE_INFO.get("module_id") or f"trigonometry.core_trigonometry.{MODULE_INFO.get('name', 'unknown')}"
    if _shared_make_sample is None:
        return {"instruction": "Solve the trigonometry problem.", "input": prompt, "answer": str(answer), "difficulty": difficulty, "metadata": metadata}
    return _shared_make_sample(
        module_id=module_id,
        topic=MODULE_INFO.get("topic", "trigonometry"),
        subtopic=MODULE_INFO.get("subtopic", "core_trigonometry"),
        difficulty=difficulty,
        instruction="Solve the trigonometry problem.",
        input_text=prompt,
        answer=answer,
        metadata=metadata,
    )


def make_sample(**kwargs):
    if "prompt" in kwargs:
        return _compat_make_sample(**kwargs)
    if _shared_make_sample is None:
        return kwargs
    return _shared_make_sample(**kwargs)

MODULE_INFO = {
    "topic": "trigonometry",
    "subtopic": "core_trigonometry",
    "name": "unit_circle_coordinates",
    "difficulty_levels": ["level_1", "level_2", "level_3"],
}

LEVELS = {
    1: [0, 30, 45, 60, 90],
    2: [120, 135, 150, 180, 210, 225, 240],
    3: [270, 300, 315, 330, 360],
}
ANGLE_TO_COORDS = {
    0: ("1", "0"), 30: ("sqrt(3)/2", "1/2"), 45: ("sqrt(2)/2", "sqrt(2)/2"),
    60: ("1/2", "sqrt(3)/2"), 90: ("0", "1"), 120: ("-1/2", "sqrt(3)/2"),
    135: ("-sqrt(2)/2", "sqrt(2)/2"), 150: ("-sqrt(3)/2", "1/2"), 180: ("-1", "0"),
    210: ("-sqrt(3)/2", "-1/2"), 225: ("-sqrt(2)/2", "-sqrt(2)/2"), 240: ("-1/2", "-sqrt(3)/2"),
    270: ("0", "-1"), 300: ("1/2", "-sqrt(3)/2"), 315: ("sqrt(2)/2", "-sqrt(2)/2"),
    330: ("sqrt(3)/2", "-1/2"), 360: ("1", "0"),
}

def curriculum():
    return {"levels": sorted(LEVELS)}

def iter_specs(level=None):
    levels = [level] if level else sorted(LEVELS)
    for lvl in levels:
        for ang in LEVELS[lvl]:
            yield {"level": lvl, "angle": ang}

def build_sample(spec, idx=0):
    a=spec['angle']
    x,y=ANGLE_TO_COORDS[a]
    return make_sample(
        prompt=f"What are the unit circle coordinates for {a}°?",
        answer=f"({x}, {y})",
        metadata={"canonical_key": f"unit_circle::{a}", "case_id": idx, "family_id": f"level_{spec['level']}"},
        level=spec["level"],
    )

def iter_samples(level=None):
    for i,s in enumerate(iter_specs(level)):
        yield build_sample(s, i)

def estimate_capacity(level=None):
    return sum(1 for _ in iter_specs(level))

def generate(level=1, seed=None, limit=50):
    pool=list(itertools.islice(iter_samples(level), limit))
    rng=random.Random(seed); rng.shuffle(pool)
    for item in pool: yield item

def generate_unique(level=1, seed=None, limit=50):
    yield from generate(level, seed, limit)


