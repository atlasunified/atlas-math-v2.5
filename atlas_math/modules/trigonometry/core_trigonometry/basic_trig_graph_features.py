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
    "name": "basic_trig_graph_features",
    "difficulty_levels": ["level_1", "level_2", "level_3"],
}

SPECS={
    1:[("y=sin(x)","period","2π"),("y=cos(x)","period","2π"),("y=tan(x)","period","π")],
    2:[("y=sin(x)","range","[-1, 1]"),("y=cos(x)","range","[-1, 1]"),("y=tan(x)","range","all real numbers")],
    3:[("y=sin(x)","amplitude","1"),("y=cos(x)","amplitude","1")],
}

def curriculum(): return {"levels": sorted(SPECS)}

def iter_specs(level=None):
    levels=[level] if level else sorted(SPECS)
    for lvl in levels:
        for expr,feat,ans in SPECS[lvl]:
            yield {"level":lvl,"expr":expr,"feature":feat,"answer":ans}

def build_sample(spec, idx=0):
    feat=spec['feature']
    return make_sample(prompt=f"What is the {feat} of {spec['expr']}?",answer=spec['answer'],metadata={"canonical_key":f"graph::{spec['expr']}::{feat}","case_id":idx,"family_id":f"level_{spec['level']}"}, level=spec["level"])

def iter_samples(level=None):
    for i,s in enumerate(iter_specs(level)): yield build_sample(s,i)

def estimate_capacity(level=None): return sum(1 for _ in iter_specs(level))

def generate(level=1, seed=None, limit=30):
    pool=list(itertools.islice(iter_samples(level), limit)); rng=random.Random(seed); rng.shuffle(pool); yield from pool

def generate_unique(level=1, seed=None, limit=30): yield from generate(level, seed, limit)


