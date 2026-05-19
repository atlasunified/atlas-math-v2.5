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

TASK_INSTRUCTION = "Use angle relationships"

MODULE_INFO = {
    'module_id': 'geometry.angle_relationships_basic',
    'name': 'Angle Relationships Basic',
    'topic': 'geometry',
    'subtopic': 'core_geometry',
    'difficulty_levels': ['level_1', 'level_2', 'level_3', 'level_4', 'level_5'],
    'enabled': True,
}
LEVEL_SPEC_CAPS = {'level_1': 500, 'level_2': 700, 'level_3': 800, 'level_4': 900, 'level_5': 1000}
FAMILY_CAPS = {
    'level_1': {'complementary': 500},
    'level_2': {'supplementary': 700},
    'level_3': {'vertical_angles': 800},
    'level_4': {'find_from_expression': 900},
    'level_5': {'multi_step_angle_chain': 1000},
}
CAPACITY_HINTS = {k: {'value': v, 'quality': 'capped'} for k, v in LEVEL_SPEC_CAPS.items()}
CURRICULUM = {
    'level_1': ['complementary angles'],
    'level_2': ['supplementary angles'],
    'level_3': ['vertical angles'],
    'level_4': ['solve linear expressions for angle measures'],
    'level_5': ['multi-step angle relationships'],
}


def iter_level1_specs():
    emitted = 0
    limit = FAMILY_CAPS['level_1']['complementary']
    for a in range(5, 86):
        b = 90 - a
        yield _spec('complementary', (a,), f"Two angles are complementary. One angle measures {a}°. What is the other angle?", str(b))
        emitted += 1
        if emitted >= limit:
            return


def iter_level2_specs():
    emitted = 0
    limit = FAMILY_CAPS['level_2']['supplementary']
    for a in range(10, 171):
        b = 180 - a
        yield _spec('supplementary', (a,), f"Two angles are supplementary. One angle measures {a}°. What is the other angle?", str(b))
        emitted += 1
        if emitted >= limit:
            return


def iter_level3_specs():
    emitted = 0
    limit = FAMILY_CAPS['level_3']['vertical_angles']
    for a in range(15, 166):
        yield _spec('vertical_angles', (a,), f"Two vertical angles are formed by intersecting lines. One of the angles measures {a}°. What is the measure of its vertical angle?", str(a))
        emitted += 1
        if emitted >= limit:
            return


def iter_level4_specs():
    emitted = 0
    limit = FAMILY_CAPS['level_4']['find_from_expression']
    for x in range(2, 31):
        for a in range(1, 6):
            for b in range(0, 21):
                angle1 = a * x + b
                if not (5 <= angle1 <= 175):
                    continue
                angle2 = 180 - angle1
                if not (5 <= angle2 <= 175):
                    continue
                problem = f"Two angles are supplementary. One angle is {a}x + {b} degrees and the other is {angle2} degrees. Find x."
                yield _spec('find_from_expression', (x, a, b, angle2), problem, str(x))
                emitted += 1
                if emitted >= limit:
                    return


def iter_level5_specs():
    emitted = 0
    limit = FAMILY_CAPS['level_5']['multi_step_angle_chain']
    for x in range(2, 26):
        for a in range(1, 5):
            for b in range(0, 16):
                first = a * x + b
                if not (10 <= first <= 160):
                    continue
                second = 180 - first
                third = second
                problem = (
                    f"Angle A and angle B are supplementary. Angle B and angle C are vertical angles. "
                    f"If angle A = {a}x + {b} degrees, and angle C = {third} degrees, find x."
                )
                yield _spec('multi_step_angle_chain', (x, a, b, third), problem, str(x))
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


