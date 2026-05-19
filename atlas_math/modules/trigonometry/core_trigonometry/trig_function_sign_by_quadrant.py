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
    "name": "trig_function_sign_by_quadrant",
    "difficulty_levels": ["level_1", "level_2", "level_3"],
}

FUNCS=["sin","cos","tan"]
QUADS=[1,2,3,4]
SIGNS={
    ("sin",1):"positive", ("sin",2):"positive", ("sin",3):"negative", ("sin",4):"negative",
    ("cos",1):"positive", ("cos",2):"negative", ("cos",3):"negative", ("cos",4):"positive",
    ("tan",1):"positive", ("tan",2):"negative", ("tan",3):"positive", ("tan",4):"negative",
}
LEVELS={1:["sin","cos"],2:["tan"],3:["sin","cos","tan"]}

def curriculum(): return {"levels": sorted(LEVELS)}

def iter_specs(level=None):
    levels=[level] if level else sorted(LEVELS)
    for lvl in levels:
        for fn in LEVELS[lvl]:
            for q in QUADS:
                yield {"level":lvl,"func":fn,"quadrant":q}

def build_sample(spec, idx=0):
    fn,q=spec['func'],spec['quadrant']
    return make_sample(prompt=f"In Quadrant {q}, is {fn}(θ) positive or negative?",answer=SIGNS[(fn,q)],metadata={"canonical_key":f"sign::{fn}::Q{q}","case_id":idx,"family_id":f"level_{spec['level']}::{fn}"}, level=spec["level"])

def iter_samples(level=None):
    for i,s in enumerate(iter_specs(level)): yield build_sample(s,i)

def estimate_capacity(level=None): return sum(1 for _ in iter_specs(level))

def generate(level=1, seed=None, limit=50):
    pool=list(itertools.islice(iter_samples(level), limit)); rng=random.Random(seed); rng.shuffle(pool); yield from pool

def generate_unique(level=1, seed=None, limit=50): yield from generate(level, seed, limit)


