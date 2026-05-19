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

TASK_INSTRUCTION = 'Use scale factor and dilation relationships'
MODULE_INFO = {'module_id': 'geometry.dilations_and_scale_factor', 'name': 'Dilations And Scale Factor', 'topic': 'geometry', 'subtopic': 'core_geometry', 'difficulty_levels': ['level_1', 'level_2', 'level_3', 'level_4', 'level_5'], 'enabled': True}
LEVEL_SPEC_CAPS = {'level_1': 250, 'level_2': 250, 'level_3': 250, 'level_4': 250, 'level_5': 250}
FAMILY_CAPS = {
    'level_1': {'find_image_length': 250},
    'level_2': {'find_scale_factor': 250},
    'level_3': {'dilate_point_origin': 250},
    'level_4': {'similar_perimeter': 250},
    'level_5': {'similar_area': 250},
}
CAPACITY_HINTS = {k: {'value': v, 'quality': 'capped'} for k, v in LEVEL_SPEC_CAPS.items()}
CURRICULUM = {
    'level_1': ['find image measure from preimage and scale factor'],
    'level_2': ['find scale factor from measures'],
    'level_3': ['dilate coordinate point about origin'],
    'level_4': ['use perimeter scale relationship'],
    'level_5': ['use area scale relationship'],
}

def iter_level1_specs():
    emitted = 0; limit = FAMILY_CAPS['level_1']['find_image_length']
    scales = [0.5, 1.5, 2, 2.5, 3, 4]
    for length in range(2, 51):
        for k in scales:
            yield _spec('find_image_length', (length, k), f"A segment of length {length} is dilated by a scale factor of {_num(k)}. What is the image length?", _num(length * k))
            emitted += 1
            if emitted >= limit:
                return

def iter_level2_specs():
    emitted = 0; limit = FAMILY_CAPS['level_2']['find_scale_factor']
    for pre in range(2, 31):
        for mult_num, mult_den in [(1,2), (3,2), (2,1), (5,2), (3,1), (4,1)]:
            img = pre * mult_num / mult_den
            yield _spec('find_scale_factor', (pre, img), f"A segment of length {pre} is dilated to length {_num(img)}. What is the scale factor?", _num(img / pre))
            emitted += 1
            if emitted >= limit:
                return

def iter_level3_specs():
    emitted = 0; limit = FAMILY_CAPS['level_3']['dilate_point_origin']
    scales = [0.5, 2, 3, -1, -2]
    for x in range(-8, 9):
        for y in range(-8, 9):
            for k in scales:
                yield _spec('dilate_point_origin', (x, y, k), f"Dilate the point ({x}, {y}) about the origin by scale factor {_num(k)}. What are the image coordinates?", f"({_num(x * k)}, {_num(y * k)})")
                emitted += 1
                if emitted >= limit:
                    return

def iter_level4_specs():
    emitted = 0; limit = FAMILY_CAPS['level_4']['similar_perimeter']
    for p in range(6, 61):
        for k in [0.5, 1.5, 2, 2.5, 3]:
            yield _spec('similar_perimeter', (p, k), f"A polygon has perimeter {p}. A similar polygon is formed by a dilation with scale factor {_num(k)}. What is the new perimeter?", _num(p * k))
            emitted += 1
            if emitted >= limit:
                return

def iter_level5_specs():
    emitted = 0; limit = FAMILY_CAPS['level_5']['similar_area']
    for area in range(4, 81):
        for k in [0.5, 1.5, 2, 3, 4]:
            yield _spec('similar_area', (area, k), f"A figure has area {area}. A similar figure is formed by a dilation with scale factor {_num(k)}. What is the new area?", _num(area * k * k))
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


