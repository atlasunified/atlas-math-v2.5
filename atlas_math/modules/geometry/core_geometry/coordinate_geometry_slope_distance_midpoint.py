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

TASK_INSTRUCTION = "Find the requested coordinate-geometry quantity"

MODULE_INFO = {
    'module_id': 'geometry.coordinate_geometry_slope_distance_midpoint',
    'name': 'Coordinate Geometry Slope Distance Midpoint',
    'topic': 'geometry',
    'subtopic': 'core_geometry',
    'difficulty_levels': ['level_1', 'level_2', 'level_3', 'level_4', 'level_5'],
    'enabled': True,
}
LEVEL_SPEC_CAPS = {'level_1': 420, 'level_2': 520, 'level_3': 620, 'level_4': 700, 'level_5': 840}
FAMILY_CAPS = {
    'level_1': {'integer_slope': 420},
    'level_2': {'integer_distance': 520},
    'level_3': {'integer_midpoint': 620},
    'level_4': {'classify_segment': 700},
    'level_5': {'multi_quantity': 840},
}
CAPACITY_HINTS = {k: {'value': v, 'quality': 'capped'} for k, v in LEVEL_SPEC_CAPS.items()}
CURRICULUM = {
    'level_1': ['slope from two points'],
    'level_2': ['distance from two points'],
    'level_3': ['midpoint from two points'],
    'level_4': ['classify by slope and distance'],
    'level_5': ['compute multiple coordinate quantities'],
}
TRIPLES = [(3,4,5),(5,12,13),(6,8,10),(8,15,17)]

def _reduce_fraction(a: int, b: int) -> str:
    if b == 0:
        return 'undefined'
    g = math.gcd(a, b)
    a //= g
    b //= g
    if b < 0:
        a, b = -a, -b
    if b == 1:
        return str(a)
    return f"{a}/{b}"


def iter_level1_specs():
    emitted = 0
    limit = FAMILY_CAPS['level_1']['integer_slope']
    for x1 in range(-10, 11):
        for y1 in range(-10, 11):
            for dx in range(-6, 7):
                for dy in range(-6, 7):
                    if dx == 0 and dy == 0:
                        continue
                    x2, y2 = x1 + dx, y1 + dy
                    ans = _reduce_fraction(dy, dx)
                    yield _spec('integer_slope', (x1, y1, x2, y2), f"Find the slope of the line through ({x1}, {y1}) and ({x2}, {y2}).", ans)
                    emitted += 1
                    if emitted >= limit:
                        return


def iter_level2_specs():
    emitted = 0
    limit = FAMILY_CAPS['level_2']['integer_distance']
    for x1 in range(-8, 9):
        for y1 in range(-8, 9):
            for dx, dy, d in TRIPLES:
                x2, y2 = x1 + dx, y1 + dy
                yield _spec('integer_distance', (x1, y1, x2, y2), f"Find the distance between ({x1}, {y1}) and ({x2}, {y2}).", str(d))
                emitted += 1
                if emitted >= limit:
                    return


def iter_level3_specs():
    emitted = 0
    limit = FAMILY_CAPS['level_3']['integer_midpoint']
    for x1 in range(-10, 11):
        for y1 in range(-10, 11):
            for x2 in range(-10, 11):
                for y2 in range(-10, 11):
                    if (x1 + x2) % 2 or (y1 + y2) % 2:
                        continue
                    ans = f"({(x1 + x2)//2}, {(y1 + y2)//2})"
                    yield _spec('integer_midpoint', (x1, y1, x2, y2), f"Find the midpoint of the segment with endpoints ({x1}, {y1}) and ({x2}, {y2}).", ans)
                    emitted += 1
                    if emitted >= limit:
                        return


def iter_level4_specs():
    emitted = 0
    limit = FAMILY_CAPS['level_4']['classify_segment']
    for x1 in range(-6, 7):
        for y1 in range(-6, 7):
            for dx, dy, d in TRIPLES:
                x2, y2 = x1 + dx, y1 + dy
                slope = _reduce_fraction(dy, dx)
                problem = f"A segment has endpoints ({x1}, {y1}) and ({x2}, {y2}). Give its slope and distance as an ordered pair (slope, distance)."
                yield _spec('classify_segment', (x1, y1, x2, y2), problem, f"({slope}, {d})")
                emitted += 1
                if emitted >= limit:
                    return


def iter_level5_specs():
    emitted = 0
    limit = FAMILY_CAPS['level_5']['multi_quantity']
    for x1 in range(-6, 7):
        for y1 in range(-6, 7):
            for dx, dy, d in TRIPLES:
                x2, y2 = x1 + dx, y1 + dy
                if (x1 + x2) % 2 or (y1 + y2) % 2:
                    continue
                slope = _reduce_fraction(dy, dx)
                midpoint = f"({(x1 + x2)//2}, {(y1 + y2)//2})"
                problem = f"For the points ({x1}, {y1}) and ({x2}, {y2}), find the slope, distance, and midpoint."
                yield _spec('multi_quantity', (x1, y1, x2, y2), problem, f"({slope}, {d}, {midpoint})")
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


