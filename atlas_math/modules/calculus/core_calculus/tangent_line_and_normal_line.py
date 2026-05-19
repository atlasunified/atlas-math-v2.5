from __future__ import annotations

import random
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
    "module_id": "calculus.tangent_line_and_normal_line",
    "name": "Tangent Line And Normal Line",
    "topic": "calculus",
    "subtopic": "core_calculus",
    "difficulty_levels": ["level_1", "level_2", "level_3", "level_4", "level_5"],
    "enabled": True,
}
INSTRUCTIONS = [
    "Find the tangent or normal line: {problem}",
    "Compute the requested line equation: {problem}",
    "Use derivatives to determine the line: {problem}",
]

def _emit(level: str, items):
    cap = LEVEL_SPEC_CAPS[level]
    for idx, item in enumerate(items):
        if idx >= cap:
            return
        prompt, ans, family, values = item
        yield _spec(family, values, prompt, ans)

def iter_level1_specs():
    items=[]
    for a in [1,2,3]:
        for b in [-2,0,3]:
            x0=1
            y0=a*x0*x0+b
            m=2*a*x0
            prompt=f"For y = {a}x^2 {'+' if b>=0 else '-'} {abs(b)}, find the tangent line at x = {x0}."
            ans=f"y - {y0} = {m}(x - {x0})"
            items.append((prompt,ans,'tangent_quadratic_fixed',(a,b,x0)))
    return _emit('level_1', items)

def iter_level2_specs():
    items=[]
    for a in [1,2,3]:
        for x0 in [1,2,3]:
            y0=a*(x0**3)
            m=3*a*(x0**2)
            prompt=f"For y = {a}x^3, find the tangent line at x = {x0}."
            ans=f"y - {y0} = {m}(x - {x0})"
            items.append((prompt,ans,'tangent_cubic',(a,x0)))
    return _emit('level_2', items)

def iter_level3_specs():
    items=[]
    for a in [1,2,4]:
        for c in [1,3,5]:
            x0=0
            y0=c
            m=a
            prompt=f"For y = e^({a}x) + {c-1}, find the tangent line at x = 0."
            ans=f"y - {y0} = {m}(x - 0)"
            items.append((prompt,ans,'tangent_exponential',(a,c)))
    return _emit('level_3', items)

def iter_level4_specs():
    items=[]
    for a in [1,2,3]:
        for x0 in [1,2,4]:
            y0=x0**2 + a
            mt=2*x0
            mn=f"-1/{mt}" if mt != 0 else 'undefined'
            prompt=f"For y = x^2 + {a}, find the normal line at x = {x0}."
            ans=f"y - {y0} = {mn}(x - {x0})"
            items.append((prompt,ans,'normal_quadratic',(a,x0)))
    return _emit('level_4', items)

def iter_level5_specs():
    items=[]
    for a in [1,2,3]:
        for b in [1,2,5]:
            x0=1
            y0=a+b
            mt=(2*a*1+b)
            prompt=f"For y = {a}x^2 + {b}x, find both the tangent and normal lines at x = 1."
            ans=f"tangent: y - {y0} = {mt}(x - 1); normal: y - {y0} = -1/{mt}(x - 1)"
            items.append((prompt,ans,'tangent_and_normal',(a,b)))
    return _emit('level_5', items)


