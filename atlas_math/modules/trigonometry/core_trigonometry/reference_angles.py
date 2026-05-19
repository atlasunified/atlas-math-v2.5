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
    "name": "reference_angles",
    "difficulty_levels": ["level_1", "level_2", "level_3"],
}

ANGLES={1:[30,45,60,120,135,150],2:[210,225,240,300,315,330],3:[390,405,420,480,495,510]}
REF={30:30,45:45,60:60,120:60,135:45,150:30,210:30,225:45,240:60,300:60,315:45,330:30,390:30,405:45,420:60,480:60,495:45,510:30}

def curriculum(): return {"levels": sorted(ANGLES)}

def iter_specs(level=None):
    levels=[level] if level else sorted(ANGLES)
    for lvl in levels:
        for ang in ANGLES[lvl]:
            yield {"level":lvl,"angle":ang}

def build_sample(spec, idx=0):
    a=spec['angle']
    return make_sample(prompt=f"What is the reference angle for {a}°?",answer=f"{REF[a]}°",metadata={"canonical_key":f"ref::{a}","case_id":idx,"family_id":f"level_{spec['level']}"}, level=spec["level"])

def iter_samples(level=None):
    for i,s in enumerate(iter_specs(level)): yield build_sample(s,i)

def estimate_capacity(level=None): return sum(1 for _ in iter_specs(level))

def generate(level=1, seed=None, limit=40):
    pool=list(itertools.islice(iter_samples(level), limit)); rng=random.Random(seed); rng.shuffle(pool); yield from pool

def generate_unique(level=1, seed=None, limit=40): yield from generate(level, seed, limit)


