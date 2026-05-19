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

TASK_INSTRUCTION = "Find the requested polygon angle measure"

MODULE_INFO = {
    'module_id': 'geometry.polygon_interior_exterior_angles',
    'name': 'Polygon Interior Exterior Angles',
    'topic': 'geometry',
    'subtopic': 'core_geometry',
    'difficulty_levels': ['level_1', 'level_2', 'level_3', 'level_4', 'level_5'],
    'enabled': True,
}
LEVEL_SPEC_CAPS = {'level_1': 420, 'level_2': 520, 'level_3': 620, 'level_4': 700, 'level_5': 840}
FAMILY_CAPS = {
    'level_1': {'sum_interior': 420},
    'level_2': {'single_regular_interior': 520},
    'level_3': {'single_regular_exterior': 620},
    'level_4': {'find_sides_from_exterior': 700},
    'level_5': {'missing_interior_from_sum': 840},
}
CAPACITY_HINTS = {k: {'value': v, 'quality': 'capped'} for k, v in LEVEL_SPEC_CAPS.items()}
CURRICULUM = {
    'level_1': ['sum of interior angles'],
    'level_2': ['one interior angle of a regular polygon'],
    'level_3': ['one exterior angle of a regular polygon'],
    'level_4': ['number of sides from an exterior angle'],
    'level_5': ['missing angle from interior-angle sum'],
}

def iter_level1_specs():
    emitted = 0
    limit = FAMILY_CAPS['level_1']['sum_interior']
    for n in range(3, 123):
        yield _spec('sum_interior', (n,), f"Find the sum of the interior angles of a {n}-gon.", str((n - 2) * 180))
        emitted += 1
        if emitted >= limit:
            return


def iter_level2_specs():
    emitted = 0
    limit = FAMILY_CAPS['level_2']['single_regular_interior']
    for n in range(3, 123):
        num = (n - 2) * 180
        if num % n != 0:
            continue
        yield _spec('single_regular_interior', (n,), f"A polygon is regular with {n} sides. Find the measure of one interior angle.", str(num // n))
        emitted += 1
        if emitted >= limit:
            return


def iter_level3_specs():
    emitted = 0
    limit = FAMILY_CAPS['level_3']['single_regular_exterior']
    for n in range(3, 121):
        if 360 % n != 0:
            continue
        yield _spec('single_regular_exterior', (n,), f"A polygon is regular with {n} sides. Find the measure of one exterior angle.", str(360 // n))
        emitted += 1
        if emitted >= limit:
            return


def iter_level4_specs():
    emitted = 0
    limit = FAMILY_CAPS['level_4']['find_sides_from_exterior']
    for ext in [1,2,3,4,5,6,8,9,10,12,15,18,20,24,30,36,40,45,60,72,90,120]:
        n = 360 // ext
        problem = f"A regular polygon has one exterior angle measuring {ext} degrees. How many sides does the polygon have?"
        yield _spec('find_sides_from_exterior', (ext,), problem, str(n))
        emitted += 1
        if emitted >= limit:
            return


def iter_level5_specs():
    emitted = 0
    limit = FAMILY_CAPS['level_5']['missing_interior_from_sum']
    for n in range(4, 21):
        total = (n - 2) * 180
        vals = list(range(100, 100 + 5 * (n - 1), 5))
        known = vals[: n - 1]
        missing = total - sum(known)
        if missing <= 0:
            continue
        joined = ', '.join(str(v) for v in known)
        problem = f"The interior angles of an {n}-gon are {joined}, and x degrees. Find x."
        yield _spec('missing_interior_from_sum', tuple(known) + (n,), problem, str(missing))
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
    rng = random.Random(seed if seed is not None else _stable_seed(MODULE_INFO['module_id'], difficulty, count))
    rng.shuffle(pool)
    return [_sample_from_spec(spec, difficulty, idx) for idx, spec in enumerate(pool[:count])]


def generate_unique(count=10, difficulty='level_1', seed=None):
    count = max(0, int(count))
    pool = list(itertools.islice(_iter_specs(difficulty), 0, MAX_SPEC_PREFIX))
    if not pool or count == 0:
        return []
    rng = random.Random(seed if seed is not None else _stable_seed('unique', MODULE_INFO['module_id'], difficulty, count))
    rng.shuffle(pool)
    out = []
    seen = set()
    for spec in pool:
        key = spec['canonical_key']
        if key in seen:
            continue
        seen.add(key)
        out.append(_sample_from_spec(spec, difficulty, len(out)))
        if len(out) >= count:
            break
    return out


def iter_samples(difficulty='level_1'):
    for idx, spec in enumerate(_take(_iter_specs(difficulty), MAX_ITER_SAMPLES)):
        yield _sample_from_spec(spec, difficulty, idx)


