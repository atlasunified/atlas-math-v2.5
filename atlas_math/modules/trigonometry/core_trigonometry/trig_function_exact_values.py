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
    "name": "trig_function_exact_values",
    "difficulty_levels": ["level_1", "level_2", "level_3"],
}

FUNCS = ["sin", "cos", "tan"]
ANGLES = {
    1: [0, 30, 45, 60, 90],
    2: [120, 135, 150, 180, 210, 225, 240],
    3: [300, 315, 330, 360],
}
VALUES = {
    ("sin",0):"0", ("sin",30):"1/2", ("sin",45):"sqrt(2)/2", ("sin",60):"sqrt(3)/2", ("sin",90):"1",
    ("sin",120):"sqrt(3)/2", ("sin",135):"sqrt(2)/2", ("sin",150):"1/2", ("sin",180):"0",
    ("sin",210):"-1/2", ("sin",225):"-sqrt(2)/2", ("sin",240):"-sqrt(3)/2", ("sin",300):"-sqrt(3)/2",
    ("sin",315):"-sqrt(2)/2", ("sin",330):"-1/2", ("sin",360):"0",
    ("cos",0):"1", ("cos",30):"sqrt(3)/2", ("cos",45):"sqrt(2)/2", ("cos",60):"1/2", ("cos",90):"0",
    ("cos",120):"-1/2", ("cos",135):"-sqrt(2)/2", ("cos",150):"-sqrt(3)/2", ("cos",180):"-1",
    ("cos",210):"-sqrt(3)/2", ("cos",225):"-sqrt(2)/2", ("cos",240):"-1/2", ("cos",300):"1/2",
    ("cos",315):"sqrt(2)/2", ("cos",330):"sqrt(3)/2", ("cos",360):"1",
    ("tan",0):"0", ("tan",30):"sqrt(3)/3", ("tan",45):"1", ("tan",60):"sqrt(3)", ("tan",90):"undefined",
    ("tan",120):"-sqrt(3)", ("tan",135):"-1", ("tan",150):"-sqrt(3)/3", ("tan",180):"0",
    ("tan",210):"sqrt(3)/3", ("tan",225):"1", ("tan",240):"sqrt(3)", ("tan",300):"-sqrt(3)",
    ("tan",315):"-1", ("tan",330):"-sqrt(3)/3", ("tan",360):"0",
}

def curriculum(): return {"levels": sorted(ANGLES)}

def iter_specs(level=None):
    levels=[level] if level else sorted(ANGLES)
    for lvl in levels:
        for ang in ANGLES[lvl]:
            for fn in FUNCS:
                yield {"level":lvl,"angle":ang,"func":fn}

def build_sample(spec, idx=0):
    fn,a=spec['func'],spec['angle']
    return make_sample(prompt=f"Find the exact value of {fn}({a}°).",answer=VALUES[(fn,a)],metadata={"canonical_key":f"exact::{fn}::{a}","case_id":idx,"family_id":f"level_{spec['level']}::{fn}"}, level=spec["level"])

def iter_samples(level=None):
    for i,s in enumerate(iter_specs(level)): yield build_sample(s,i)

def estimate_capacity(level=None): return sum(1 for _ in iter_specs(level))

def generate(level=1, seed=None, limit=72):
    pool=list(itertools.islice(iter_samples(level), limit)); rng=random.Random(seed); rng.shuffle(pool); yield from pool

def generate_unique(level=1, seed=None, limit=72): yield from generate(level, seed, limit)


