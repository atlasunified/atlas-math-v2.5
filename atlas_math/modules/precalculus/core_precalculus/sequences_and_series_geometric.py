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
    "module_id": "precalculus.sequences_and_series_geometric",
    "name": "Sequences and Series Geometric",
    "topic": "precalculus",
    "subtopic": "core_precalculus",
    "difficulty_levels": ["level_1", "level_2", "level_3", "level_4", "level_5"],
    "enabled": True,
}
INSTRUCTIONS = [
    "Work with the geometric sequence or series: {problem}",
    "Find the requested geometric-sequence value: {problem}",
    "Compute the geometric-series result: {problem}",
]

def _emit(level, rows):
    for idx, row in enumerate(rows):
        if idx >= LEVEL_SPEC_CAPS[level]:
            return
        yield _spec(*row)

def iter_level1_specs():
    return _emit("level_1", [
        ("next_term", (3,2), "Find the next term: 3, 6, 12, 24, ...", "48"),
        ("ratio", (5,-2), "Find the common ratio of the geometric sequence 5, -10, 20, -40, ...", "-2"),
    ])

def iter_level2_specs():
    return _emit("level_2", [
        ("nth_term", (2,3,5), "A geometric sequence has a_1 = 2 and r = 3. Find a_5.", "162"),
        ("explicit", (7,2), "Write an explicit formula for the geometric sequence with a_1 = 7 and r = 2.", "a_n = 7(2)^(n-1)"),
        ("nth_term_frac", (81,1/3,4), "A geometric sequence has a_1 = 81 and r = 1/3. Find a_4.", "3"),
    ])

def iter_level3_specs():
    return _emit("level_3", [
        ("find_n", (3,2,48), "For the geometric sequence with a_1 = 3 and r = 2, find n if a_n = 48.", "n = 5"),
        ("sum_n", (2,3,4), "Find the sum of the first 4 terms of the geometric sequence with a_1 = 2 and r = 3.", "80"),
    ])

def iter_level4_specs():
    return _emit("level_4", [
        ("sum_n_frac", (64,1/2,5), "Find the sum of the first 5 terms of the geometric sequence with a_1 = 64 and r = 1/2.", "124"),
        ("from_terms", (12,96,2,5), "A geometric sequence has a_2 = 12 and a_5 = 96. Find the common ratio.", "2"),
    ])

def iter_level5_specs():
    return _emit("level_5", [
        ("infinite_sum", (5,1/2), "Find the sum to infinity of the geometric series 5 + 2.5 + 1.25 + ...", "10"),
        ("system_terms", (6,486,2,6), "A geometric sequence satisfies a_2 = 6 and a_6 = 486. Find the common ratio.", "3"),
    ])


