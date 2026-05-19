from __future__ import annotations

import itertools
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


def _spec(family, values, problem, answer):
    canonical = ':'.join([family] + [str(v) for v in values])
    return {'family': family, 'values': values, 'problem': problem, 'answer': answer, 'canonical_key': canonical, 'case_id': canonical, 'family_id': family}


def _sample_from_spec(spec, difficulty, instruction_idx=0):
    answer = spec['answer']
    metadata = {
        'family': spec['family'], 'level_number': _level_num(difficulty), 'structured': True,
        'canonical_key': spec['canonical_key'], 'case_id': spec['case_id'], 'family_id': spec['family_id'],
        'template_id': spec['family'], 'final_answer': answer, 'values': list(spec.get('values', [])),
    }
    instruction = INSTRUCTIONS[instruction_idx % len(INSTRUCTIONS)].format(instruction=TASK_INSTRUCTION, problem=spec['problem'])
    return make_sample(module_id=MODULE_INFO['module_id'], topic=MODULE_INFO['topic'], subtopic=MODULE_INFO['subtopic'], difficulty=difficulty, instruction=instruction, input_text=spec['problem'], answer=answer, metadata=metadata)


TASK_INSTRUCTION = "Find the requested perimeter or area"
MODULE_INFO = {'module_id': 'geometry.perimeter_area_basic_shapes', 'name': 'Perimeter Area Basic Shapes', 'topic': 'geometry', 'subtopic': 'core_geometry', 'difficulty_levels': ['level_1', 'level_2', 'level_3', 'level_4', 'level_5'], 'enabled': True}
LEVEL_SPEC_CAPS = {'level_1': 500, 'level_2': 700, 'level_3': 800, 'level_4': 900, 'level_5': 1000}
FAMILY_CAPS = {'level_1': {'square_perimeter': 500}, 'level_2': {'rectangle_area': 700}, 'level_3': {'triangle_area': 800}, 'level_4': {'mixed_rectangle': 900}, 'level_5': {'compare_shapes': 1000}}
CAPACITY_HINTS = {k: {'value': v, 'quality': 'capped'} for k, v in LEVEL_SPEC_CAPS.items()}
CURRICULUM = {
    'level_1': ['perimeter of a square'],
    'level_2': ['area of a rectangle'],
    'level_3': ['area of a triangle'],
    'level_4': ['choose perimeter or area of a rectangle from text'],
    'level_5': ['compare two shape measurements'],
}


def iter_level1_specs():
    limit = FAMILY_CAPS['level_1']['square_perimeter']
    emitted = 0
    for s in range(2, 127):
        yield _spec('square_perimeter', (s,), f"A square has side length {s} units. What is its perimeter?", str(4 * s))
        emitted += 1
        if emitted >= limit:
            return


def iter_level2_specs():
    limit = FAMILY_CAPS['level_2']['rectangle_area']
    emitted = 0
    for l in range(2, 41):
        for w in range(2, 31):
            yield _spec('rectangle_area', (l, w), f"A rectangle has length {l} units and width {w} units. What is its area?", str(l * w))
            emitted += 1
            if emitted >= limit:
                return


def iter_level3_specs():
    limit = FAMILY_CAPS['level_3']['triangle_area']
    emitted = 0
    for b in range(2, 51):
        for h in range(2, 51, 2):
            area = b * h // 2
            yield _spec('triangle_area', (b, h), f"A triangle has base {b} units and height {h} units. What is its area?", str(area))
            emitted += 1
            if emitted >= limit:
                return


def iter_level4_specs():
    limit = FAMILY_CAPS['level_4']['mixed_rectangle']
    emitted = 0
    for l in range(3, 41):
        for w in range(2, l + 1):
            problem_p = f"A rectangular garden measures {l} meters by {w} meters. What is its perimeter?"
            yield _spec('mixed_rectangle', ('p', l, w), problem_p, str(2 * (l + w)))
            emitted += 1
            if emitted >= limit:
                return
            problem_a = f"A rectangular garden measures {l} meters by {w} meters. What is its area?"
            yield _spec('mixed_rectangle', ('a', l, w), problem_a, str(l * w))
            emitted += 1
            if emitted >= limit:
                return


def iter_level5_specs():
    limit = FAMILY_CAPS['level_5']['compare_shapes']
    emitted = 0
    for s in range(2, 31):
        for l in range(2, 31):
            w = s
            area_square = s * s
            area_rect = l * w
            problem = f"A square has side length {s}. A rectangle has length {l} and width {w}. What is the positive difference between their areas?"
            yield _spec('compare_shapes', (s, l, w), problem, str(abs(area_square - area_rect)))
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


