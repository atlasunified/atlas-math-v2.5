from __future__ import annotations

import itertools
import math
import random
from typing import Iterable

from atlas_math.modules.shared.common import make_sample

INSTRUCTIONS = [
    "{instruction}: {problem}",
    "Solve and report the result: {problem}",
    "Work the problem and give the final answer: {problem}",
    "Compute the requested result: {problem}",
]
MAX_SPEC_PREFIX = 5000
MAX_GENERATE_MULTIPLIER = 8
MAX_ITER_SAMPLES = 4096


def _level_num(difficulty: str) -> int:
    try:
        value = int(str(difficulty).rsplit('_', 1)[-1])
    except Exception:
        value = 1
    return max(1, min(5, value))


def _stable_seed(*parts) -> str:
    return '|'.join(str(p) for p in parts)


def _take(iterable: Iterable[dict], n: int) -> Iterable[dict]:
    for idx, item in enumerate(iterable):
        if idx >= max(0, int(n)):
            break
        yield item


def _spec(family, values, problem, answer):
    canonical = ':'.join([family] + [str(v) for v in values])
    return {
        'family': family,
        'values': values,
        'problem': problem,
        'answer': answer,
        'canonical_key': canonical,
        'case_id': canonical,
        'family_id': family,
    }


def _num(v):
    if isinstance(v, float):
        if abs(v - round(v)) < 1e-9:
            return str(int(round(v)))
        return f"{v:.2f}".rstrip('0').rstrip('.')
    return str(v)


def _sample_from_spec(spec, difficulty, instruction_idx=0):
    answer = spec['answer']
    metadata = {
        'family': spec['family'],
        'level_number': _level_num(difficulty),
        'structured': True,
        'canonical_key': spec['canonical_key'],
        'case_id': spec['case_id'],
        'family_id': spec['family_id'],
        'template_id': spec['family'],
        'final_answer': answer,
        'values': list(spec.get('values', [])),
    }
    instruction = INSTRUCTIONS[instruction_idx % len(INSTRUCTIONS)].format(
        instruction=TASK_INSTRUCTION,
        problem=spec['problem'],
    )
    return make_sample(
        module_id=MODULE_INFO['module_id'],
        topic=MODULE_INFO['topic'],
        subtopic=MODULE_INFO['subtopic'],
        difficulty=difficulty,
        instruction=instruction,
        input_text=spec['problem'],
        answer=answer,
        metadata=metadata,
    )

TASK_INSTRUCTION = 'Apply the described transformation on the coordinate plane'
MODULE_INFO = {'module_id': 'geometry.transformations_translation_reflection_rotation', 'name': 'Transformations Translation Reflection Rotation', 'topic': 'geometry', 'subtopic': 'core_geometry', 'difficulty_levels': ['level_1', 'level_2', 'level_3', 'level_4', 'level_5'], 'enabled': True}
LEVEL_SPEC_CAPS = {'level_1': 300, 'level_2': 300, 'level_3': 300, 'level_4': 300, 'level_5': 300}
FAMILY_CAPS = {
    'level_1': {'translation': 300},
    'level_2': {'reflect_x': 300},
    'level_3': {'reflect_y': 300},
    'level_4': {'rotate_90': 300},
    'level_5': {'rotate_180_or_270': 300},
}
CAPACITY_HINTS = {k: {'value': v, 'quality': 'capped'} for k, v in LEVEL_SPEC_CAPS.items()}
CURRICULUM = {
    'level_1': ['translations'],
    'level_2': ['reflection across x-axis'],
    'level_3': ['reflection across y-axis'],
    'level_4': ['90 degree rotation about origin'],
    'level_5': ['180 and 270 degree rotations about origin'],
}

def iter_level1_specs():
    emitted = 0; limit = FAMILY_CAPS['level_1']['translation']
    for x in range(-12, 13):
        for y in range(-12, 13):
            for dx in range(-5, 6):
                for dy in range(-5, 6):
                    if dx == 0 and dy == 0:
                        continue
                    ans = f"({x + dx}, {y + dy})"
                    yield _spec('translation', (x, y, dx, dy), f"Translate the point ({x}, {y}) by the vector <{dx}, {dy}>. What are the new coordinates?", ans)
                    emitted += 1
                    if emitted >= limit:
                        return

def iter_level2_specs():
    emitted = 0; limit = FAMILY_CAPS['level_2']['reflect_x']
    for x in range(-20, 21):
        for y in range(-20, 21):
            yield _spec('reflect_x', (x, y), f"Reflect the point ({x}, {y}) across the x-axis. What are the new coordinates?", f"({x}, {-y})")
            emitted += 1
            if emitted >= limit:
                return

def iter_level3_specs():
    emitted = 0; limit = FAMILY_CAPS['level_3']['reflect_y']
    for x in range(-20, 21):
        for y in range(-20, 21):
            yield _spec('reflect_y', (x, y), f"Reflect the point ({x}, {y}) across the y-axis. What are the new coordinates?", f"({-x}, {y})")
            emitted += 1
            if emitted >= limit:
                return

def iter_level4_specs():
    emitted = 0; limit = FAMILY_CAPS['level_4']['rotate_90']
    for x in range(-15, 16):
        for y in range(-15, 16):
            yield _spec('rotate_90', (x, y), f"Rotate the point ({x}, {y}) 90 degrees counterclockwise about the origin. What are the new coordinates?", f"({-y}, {x})")
            emitted += 1
            if emitted >= limit:
                return

def iter_level5_specs():
    emitted = 0; limit = FAMILY_CAPS['level_5']['rotate_180_or_270']
    for x in range(-15, 16):
        for y in range(-15, 16):
            yield _spec('rotate_180_or_270', (x, y, 180), f"Rotate the point ({x}, {y}) 180 degrees about the origin. What are the new coordinates?", f"({-x}, {-y})")
            emitted += 1
            if emitted >= limit:
                return
            yield _spec('rotate_180_or_270', (x, y, 270), f"Rotate the point ({x}, {y}) 270 degrees counterclockwise about the origin. What are the new coordinates?", f"({y}, {-x})")
            emitted += 1
            if emitted >= limit:
                return

def _iter_specs(difficulty='level_1'):
    level = _level_num(difficulty)
    if level == 1:
        return _take(iter_level1_specs(), LEVEL_SPEC_CAPS['level_1'])
    if level == 2:
        return _take(iter_level2_specs(), LEVEL_SPEC_CAPS['level_2'])
    if level == 3:
        return _take(iter_level3_specs(), LEVEL_SPEC_CAPS['level_3'])
    if level == 4:
        return _take(iter_level4_specs(), LEVEL_SPEC_CAPS['level_4'])
    return _take(iter_level5_specs(), LEVEL_SPEC_CAPS['level_5'])

def curriculum():
    return CURRICULUM

def estimate_capacity(difficulty='level_1'):
    return dict(CAPACITY_HINTS.get(difficulty, {'value': None, 'quality': 'unknown'}))

def generate(count=10, difficulty='level_1', seed=None):
    count = max(0, int(count))
    prefix = min(max(count * MAX_GENERATE_MULTIPLIER, 256), MAX_SPEC_PREFIX)
    pool = list(itertools.islice(_iter_specs(difficulty), 0, prefix))
    if not pool or count == 0:
        return []
    rng = random.Random(_stable_seed(MODULE_INFO['module_id'], difficulty, seed, 'generate'))
    rng.shuffle(pool)
    return [_sample_from_spec(spec, difficulty, i) for i, spec in enumerate(pool[:count])]

def generate_unique(count=10, difficulty='level_1', offset=0, stride=1, seed=None):
    count = max(0, int(count)); offset = max(0, int(offset)); stride = max(1, int(stride))
    pool = list(itertools.islice(_iter_specs(difficulty), 0, MAX_SPEC_PREFIX))
    rng = random.Random(_stable_seed(MODULE_INFO['module_id'], difficulty, seed, offset, stride, 'unique'))
    rng.shuffle(pool)
    chosen, seen, idx = [], set(), offset
    while idx < len(pool) and len(chosen) < count:
        spec = pool[idx]
        if spec['canonical_key'] not in seen:
            seen.add(spec['canonical_key'])
            chosen.append(spec)
        idx += stride
    return [_sample_from_spec(spec, difficulty, i) for i, spec in enumerate(chosen)]

def iter_samples(difficulty='level_1', limit=MAX_ITER_SAMPLES):
    limit = min(max(0, int(limit)), MAX_ITER_SAMPLES)
    for i, spec in enumerate(_take(_iter_specs(difficulty), limit)):
        yield _sample_from_spec(spec, difficulty, i)


