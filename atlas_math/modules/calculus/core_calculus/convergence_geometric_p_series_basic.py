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
    "module_id": "calculus.convergence_geometric_p_series_basic",
    "name": "Convergence Geometric P Series Basic",
    "topic": "calculus",
    "subtopic": "core_calculus",
    "difficulty_levels": ["level_1", "level_2", "level_3", "level_4", "level_5"],
    "enabled": True,
}
INSTRUCTIONS = ['Determine whether the series converges or diverges: {problem}', 'Classify the series: {problem}', 'State whether it converges or diverges: {problem}']


def _emit(level: str, items):
    cap = LEVEL_SPEC_CAPS[level]
    for idx, item in enumerate(items):
        if idx >= cap:
            return
        yield _spec(*item)

def iter_level_1_specs():
    items=[]
    for r in ["1/2","1/3","2/3","-1/2","-3/4"]:
        prompt=f"Σ_{{n=0}}^∞ ({r})^n"
        items.append(("geometric_converges", (r,), prompt, "converges", {"series_type":"geometric"}))
    for r in ["2","-2","3/2","-5/4"]:
        prompt=f"Σ_{{n=0}}^∞ ({r})^n"
        items.append(("geometric_diverges", (r,), prompt, "diverges", {"series_type":"geometric"}))
    return _emit("level_1", items)

def iter_level_2_specs():
    items=[]
    for p in [2,3,4,5,6]:
        prompt=f"Σ_{{n=1}}^∞ 1/n^{p}"
        items.append(("p_series_converges", (p,), prompt, "converges", {"series_type":"p-series"}))
    for p in [1,"1/2","3/4"]:
        prompt=f"Σ_{{n=1}}^∞ 1/n^{p}"
        items.append(("p_series_diverges", (p,), prompt, "diverges", {"series_type":"p-series"}))
    return _emit("level_2", items)

def iter_level_3_specs():
    items=[]
    for a in [1,2,3,4]:
        for r in ["1/2","1/3","-1/2"]:
            prompt=f"Σ_{{n=0}}^∞ {a}({r})^n"
            items.append(("scaled_geometric_converges", (a,r), prompt, "converges", {"series_type":"geometric_scaled"}))
    return _emit("level_3", items)

def iter_level_4_specs():
    items=[]
    for a in [1,2,3,4]:
        for p in [2,3,4,5]:
            prompt=f"Σ_{{n=1}}^∞ {a}/n^{p}"
            items.append(("scaled_p_series_converges", (a,p), prompt, "converges", {"series_type":"p-series_scaled"}))
    return _emit("level_4", items)

def iter_level_5_specs():
    items=[]
    for form in [("2^n","diverges"),("1/n","diverges"),("1/n^2","converges"),("(3/4)^n","converges")]:
        expr, ans = form
        prompt=f"Σ_{{n=1}}^∞ {expr}"
        items.append(("mixed_recognition", (expr,), prompt, ans, {"series_type":"recognition"}))
    return _emit("level_5", items)


