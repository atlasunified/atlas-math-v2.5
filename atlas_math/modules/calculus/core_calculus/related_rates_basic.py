from __future__ import annotations

import random
from typing import Iterable

from atlas_math.modules.shared.common import make_sample

LEVEL_SPEC_CAPS = {"level_1": 240, "level_2": 300, "level_3": 360, "level_4": 420, "level_5": 480}
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
    "module_id": "calculus.related_rates_basic",
    "name": "Related Rates Basic",
    "topic": "calculus",
    "subtopic": "core_calculus",
    "difficulty_levels": ["level_1", "level_2", "level_3", "level_4", "level_5"],
    "enabled": True,
}
INSTRUCTIONS = [
    "Solve the related-rates problem: {problem}",
    "Find the requested rate: {problem}",
    "Use implicit differentiation and the given values: {problem}",
]

def _emit(level: str, items):
    cap = LEVEL_SPEC_CAPS[level]
    for idx, item in enumerate(items):
        if idx >= cap:
            return
        yield _spec(*item)

def iter_level1_specs():
    items=[]
    for r in [2,3,4,5,6,8]:
        for dr in [1,2,3,4]:
            prompt=f"A circle has radius r={r} cm increasing at dr/dt={dr} cm/s. Find dA/dt when A=πr^2."
            ans=f"{2*r*dr}π"
            items.append(("circle_area", (r,dr), prompt, ans, {"shape":"circle"}))
    return _emit('level_1', items)

def iter_level2_specs():
    items=[]
    for r in [2,3,4,5,6]:
        for dr in [1,2,3]:
            prompt=f"A sphere has radius r={r} cm increasing at dr/dt={dr} cm/s. Find dV/dt when V=(4/3)πr^3."
            ans=f"{4*r*r*dr}π"
            items.append(("sphere_volume", (r,dr), prompt, ans, {"shape":"sphere"}))
    return _emit('level_2', items)

def iter_level3_specs():
    items=[]
    for x in [3,4,5,6,8]:
        for dx in [1,2,3]:
            for y in [4,5,7,9]:
                prompt=f"A ladder satisfies x^2 + y^2 = 25^2. If x={x} ft and dx/dt={dx} ft/s, with y={y} ft at that instant, find dy/dt."
                ans=f"-{x*dx}/{y}"
                items.append(("ladder_related", (x,dx,y), prompt, ans, {"equation":"x^2+y^2=25^2"}))
    return _emit('level_3', items)

def iter_level4_specs():
    items=[]
    for l in [2,3,4,5,6]:
        for dl in [1,2,3]:
            for w in [3,4,5,6]:
                for dw in [1,2]:
                    prompt=f"A rectangle has length l={l} increasing at dl/dt={dl} cm/s and width w={w} increasing at dw/dt={dw} cm/s. Find dA/dt for A=lw."
                    ans=str(w*dl + l*dw)
                    items.append(("rectangle_area", (l,dl,w,dw), prompt, ans, {"shape":"rectangle"}))
    return _emit('level_4', items)

def iter_level5_specs():
    items=[]
    for x in [3,4,5,6]:
        for dx in [1,2,3]:
            for y in [4,5,7,8]:
                for dy in [1,2]:
                    prompt=f"A particle satisfies x^2 + y^2 = r^2. At an instant x={x}, dx/dt={dx}, y={y}, and dy/dt={dy}. Find dr/dt."
                    r2=x*x+y*y
                    ans=f"({x*dx}+{y*dy})/√{r2}"
                    items.append(("radius_related", (x,dx,y,dy), prompt, ans, {"equation":"x^2+y^2=r^2"}))
    return _emit('level_5', items)


