from __future__ import annotations

import itertools
import random
from typing import Iterable

MAX_SPEC_PREFIX = 5000
MAX_GENERATE_MULTIPLIER = 8
MAX_ITER_SAMPLES = 4096
CAPACITY_HINTS = {
    "level_1": {"value": 2500, "quality": "capped"},
    "level_2": {"value": 4000, "quality": "capped"},
    "level_3": {"value": 4000, "quality": "capped"},
    "level_4": {"value": 5000, "quality": "capped"},
    "level_5": {"value": 4000, "quality": "capped"},
}

from atlas_math.modules.shared.common import make_sample
from atlas_math.modules.algebra.inequalities.inequality_common import (
    iter_level1_specs,
    iter_level2_specs,
    iter_level3_specs,
    iter_level4_specs,
    iter_level5_specs,
    render_spec,
)

MODULE_INFO = {
    "module_id": "algebra.inequalities.cascading_linear_inequalities",
    "name": "Cascading Linear Inequalities",
    "topic": "algebra",
    "subtopic": "inequalities",
    "difficulty_levels": ["level_1", "level_2", "level_3", "level_4", "level_5"],
    "enabled": True,
}

INSTRUCTIONS = [
    "Solve the inequality and explain your reasoning: {problem}",
    "Work through the inequality step by step: {problem}",
    "Find the solution set and show the algebra: {problem}",
    "Solve carefully and justify each key step: {problem}",
]

_LEVELS = MODULE_INFO["difficulty_levels"]


def _level_num(difficulty: str) -> int:
    try:
        n = int(str(difficulty).rsplit("_", 1)[-1])
    except Exception:
        n = 1
    return max(1, min(5, n))


def _take(iterable: Iterable[dict], limit: int) -> Iterable[dict]:
    return itertools.islice(iterable, 0, max(0, int(limit)))


def _iter_specs(difficulty: str) -> Iterable[dict]:
    level = _level_num(difficulty)
    cap = CAPACITY_HINTS.get(f"level_{level}", {"value": MAX_SPEC_PREFIX})["value"] or MAX_SPEC_PREFIX
    if level == 1:
        return _take(iter_level1_specs(), cap)
    if level == 2:
        return _take(iter_level2_specs(), cap)
    if level == 3:
        return _take(iter_level3_specs(), cap)
    if level == 4:
        return _take(iter_level4_specs(), cap)
    return _take(iter_level5_specs(), cap)


def _sample_from_spec(spec: dict, difficulty: str, instruction_idx: int = 0):
    level = _level_num(difficulty)
    problem, answer, metadata = render_spec(spec, level)
    metadata = dict(metadata)
    metadata.update(
        {
            "level_number": level,
            "family": metadata.get("family", spec.get("family")),
            "teaching_style": "option_c",
            "structured": True,
        }
    )
    instruction = INSTRUCTIONS[instruction_idx % len(INSTRUCTIONS)].format(problem=problem)
    return make_sample(
        module_id=MODULE_INFO["module_id"],
        topic=MODULE_INFO["topic"],
        subtopic=MODULE_INFO["subtopic"],
        difficulty=difficulty,
        instruction=instruction,
        input_text=problem,
        answer=answer,
        metadata=metadata,
    )


def generate_unique(count: int = 10, difficulty: str = "level_1", offset: int = 0, stride: int = 1, seed=None):
    if count <= 0:
        return []
    stride = max(1, int(stride or 1))
    offset = max(0, int(offset or 0))
    rng = random.Random("|".join(str(part) for part in (MODULE_INFO["module_id"], seed if seed is not None else "unique", difficulty, offset, stride, count)))
    pool = list(_iter_specs(difficulty))
    if not pool:
        return []
    indexed_pool = list(enumerate(pool))
    rng.shuffle(indexed_pool)
    items = []
    seen: set[str] = set()
    start = offset % len(indexed_pool)
    ordered = indexed_pool[start::stride] + indexed_pool[:start:stride]
    for idx, spec in ordered:
        sample = _sample_from_spec(spec, difficulty, instruction_idx=idx + offset)
        key = str(sample.get("input", ""))
        if key in seen:
            continue
        seen.add(key)
        items.append(sample)
        if len(items) >= count:
            break
    return items


def generate(count: int = 10, difficulty: str = "level_1", seed=None):
    if count <= 0:
        return []
    rng = random.Random(seed)
    prefix = min(max(count * MAX_GENERATE_MULTIPLIER, 256), MAX_SPEC_PREFIX)
    pool = list(itertools.islice(_iter_specs(difficulty), 0, prefix))
    rng.shuffle(pool)
    out = []
    seen: set[str] = set()
    for idx, spec in enumerate(pool):
        sample = _sample_from_spec(spec, difficulty, instruction_idx=idx)
        key = str(sample.get("input", ""))
        if key in seen:
            continue
        seen.add(key)
        out.append(sample)
        if len(out) >= count:
            break
    if len(out) < count:
        out.extend(generate_unique(count=count - len(out), difficulty=difficulty, offset=len(pool), stride=1, seed=seed))
    return out[:count]


def iter_samples(difficulty: str = "level_1", seed=None):
    emitted = 0
    seen: set[str] = set()
    for idx, spec in enumerate(_iter_specs(difficulty)):
        sample = _sample_from_spec(spec, difficulty, instruction_idx=idx)
        key = str(sample.get("input", ""))
        if key in seen:
            continue
        seen.add(key)
        yield sample
        emitted += 1
        if emitted >= MAX_ITER_SAMPLES:
            return


def estimate_capacity(difficulty: str = "level_1"):
    return dict(CAPACITY_HINTS.get(difficulty, {"value": MAX_SPEC_PREFIX, "quality": "capped"}))






