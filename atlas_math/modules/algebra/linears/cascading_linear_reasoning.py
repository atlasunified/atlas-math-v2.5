from __future__ import annotations

import itertools
import random
from functools import lru_cache

from atlas_math.modules.shared.common import make_sample

from .linear_common import INSTRUCTIONS, metadata_for_spec, specs_for_difficulty


MODULE_INFO = {
    "module_id": "algebra.linears.cascading_linear_reasoning",
    "name": "Cascading Linear Reasoning",
    "topic": "algebra",
    "subtopic": "linears",
    "difficulty_levels": ["level_1", "level_2", "level_3", "level_4", "level_5"],
    "enabled": True,
}

_LEVELS = MODULE_INFO["difficulty_levels"]


def _build_from_spec(spec, difficulty: str, instruction_idx: int = 0):
    instruction = INSTRUCTIONS[instruction_idx % len(INSTRUCTIONS)].format(problem=spec.prompt)
    return make_sample(
        module_id=MODULE_INFO["module_id"],
        topic=MODULE_INFO["topic"],
        subtopic=MODULE_INFO["subtopic"],
        difficulty=difficulty,
        instruction=instruction,
        input_text=spec.prompt,
        answer=spec.answer,
        metadata=metadata_for_spec(spec),
    )


def generate_unique(count: int = 10, difficulty: str = "level_1", offset: int = 0, stride: int = 1, seed=None):
    specs = specs_for_difficulty(difficulty)
    iterator = itertools.islice(specs, max(0, offset), None, max(1, stride))
    out = []
    for local_idx, spec in zip(range(count), iterator):
        out.append(_build_from_spec(spec, difficulty, instruction_idx=offset + local_idx * max(1, stride)))
    return out


def generate(count: int = 10, difficulty: str = "level_1", seed=None):
    rng = random.Random(seed)
    capacity = estimate_capacity(difficulty)
    if capacity:
        max_offset = max(0, capacity - count)
        offset = rng.randint(0, max_offset) if max_offset > 0 else 0
        return generate_unique(count=count, difficulty=difficulty, offset=offset, stride=1)
    return generate_unique(count=count, difficulty=difficulty)


def iter_samples(difficulty: str = "level_1", seed=None):
    for idx, spec in enumerate(specs_for_difficulty(difficulty)):
        yield _build_from_spec(spec, difficulty, instruction_idx=idx)


@lru_cache(maxsize=None)
def estimate_capacity(difficulty: str | None = None):
    if difficulty is None:
        return sum(estimate_capacity(level) for level in _LEVELS)
    return len(specs_for_difficulty(difficulty))






