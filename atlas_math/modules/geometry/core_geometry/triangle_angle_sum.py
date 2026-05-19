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
    return {
        'family': family,
        'values': values,
        'problem': problem,
        'answer': answer,
        'canonical_key': canonical,
        'case_id': canonical,
        'family_id': family,
    }


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
        instruction=TASK_INSTRUCTION, problem=spec['problem']
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

TASK_INSTRUCTION = "Use triangle angle facts"

MODULE_INFO = {
    'module_id': 'geometry.triangle_angle_sum',
    'name': 'Triangle Angle Sum',
    'topic': 'geometry',
    'subtopic': 'core_geometry',
    'difficulty_levels': ['level_1', 'level_2', 'level_3', 'level_4', 'level_5'],
    'enabled': True,
}
LEVEL_SPEC_CAPS = {'level_1': 550, 'level_2': 700, 'level_3': 850, 'level_4': 950, 'level_5': 1000}
FAMILY_CAPS = {
    'level_1': {'missing_angle': 550},
    'level_2': {'right_triangle': 700},
    'level_3': {'exterior_angle': 850},
    'level_4': {'expression_angle': 950},
    'level_5': {'isosceles_expression': 1000},
}
CAPACITY_HINTS = {k: {'value': v, 'quality': 'capped'} for k, v in LEVEL_SPEC_CAPS.items()}
CURRICULUM = {
    'level_1': ['find a missing angle in a triangle'],
    'level_2': ['find acute angles in right triangles'],
    'level_3': ['use exterior-angle theorem'],
    'level_4': ['solve for a variable using angle sum'],
    'level_5': ['use isosceles structure with expressions'],
}


def iter_level1_specs():
    emitted = 0
    limit = FAMILY_CAPS['level_1']['missing_angle']
    for a in range(20, 121):
        for b in range(20, 121):
            c = 180 - a - b
            if c <= 0:
                continue
            yield _spec('missing_angle', (a, b), f"A triangle has angles measuring {a}°, {b}°, and x°. Find x.", str(c))
            emitted += 1
            if emitted >= limit:
                return


def iter_level2_specs():
    emitted = 0
    limit = FAMILY_CAPS['level_2']['right_triangle']
    for a in range(10, 81):
        b = 90 - a
        yield _spec('right_triangle', (a,), f"A right triangle has one acute angle measuring {a}°. What is the measure of the other acute angle?", str(b))
        emitted += 1
        if emitted >= limit:
            return


def iter_level3_specs():
    emitted = 0
    limit = FAMILY_CAPS['level_3']['exterior_angle']
    for a in range(20, 91):
        for b in range(20, 91):
            ext = a + b
            if ext >= 180:
                continue
            yield _spec('exterior_angle', (a, b), f"In a triangle, two remote interior angles measure {a}° and {b}°. Find the exterior angle formed at the third vertex.", str(ext))
            emitted += 1
            if emitted >= limit:
                return


def iter_level4_specs():
    emitted = 0
    limit = FAMILY_CAPS['level_4']['expression_angle']
    for x in range(2, 26):
        for a in range(1, 5):
            for b in range(0, 16):
                first = a * x + b
                for second in range(20, 101):
                    third = 180 - first - second
                    if min(first, second, third) <= 0:
                        continue
                    problem = f"A triangle has angles measuring {a}x + {b} degrees, {second} degrees, and {third} degrees. Find x."
                    yield _spec('expression_angle', (x, a, b, second, third), problem, str(x))
                    emitted += 1
                    if emitted >= limit:
                        return


def iter_level5_specs():
    emitted = 0
    limit = FAMILY_CAPS['level_5']['isosceles_expression']
    for x in range(2, 26):
        for a in range(1, 5):
            for b in range(0, 16):
                equal = a * x + b
                vertex = 180 - 2 * equal
                if min(equal, vertex) <= 0:
                    continue
                problem = f"An isosceles triangle has two equal angles each measuring {a}x + {b} degrees. The third angle measures {vertex} degrees. Find x."
                yield _spec('isosceles_expression', (x, a, b, vertex), problem, str(x))
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
    count = max(0, int(count))
    offset = max(0, int(offset))
    stride = max(1, int(stride))
    pool = list(itertools.islice(_iter_specs(difficulty), 0, MAX_SPEC_PREFIX))
    rng = random.Random(_stable_seed(MODULE_INFO['module_id'], difficulty, seed, offset, stride, 'unique'))
    rng.shuffle(pool)
    seen = set()
    ordered = []
    for spec in pool:
        if spec['canonical_key'] in seen:
            continue
        seen.add(spec['canonical_key'])
        ordered.append(spec)
    return [_sample_from_spec(spec, difficulty, i) for i, spec in enumerate(ordered[offset::stride][:count])]


def iter_samples(difficulty='level_1', seed=None):
    max_items = min(LEVEL_SPEC_CAPS.get(difficulty, 1000), MAX_ITER_SAMPLES)
    pool = list(itertools.islice(_iter_specs(difficulty), 0, max_items))
    rng = random.Random(_stable_seed(MODULE_INFO['module_id'], difficulty, seed, 'iter'))
    rng.shuffle(pool)
    seen = set()
    for idx, spec in enumerate(pool):
        if spec['canonical_key'] in seen:
            continue
        seen.add(spec['canonical_key'])
        yield _sample_from_spec(spec, difficulty, idx)


