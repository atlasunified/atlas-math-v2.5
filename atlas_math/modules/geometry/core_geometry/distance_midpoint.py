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
    return {
        'family': family,
        'values': values,
        'problem': problem,
        'answer': answer,
        'canonical_key': canonical,
        'case_id': canonical,
        'family_id': family,
    }


def _fmt_num(n):
    return str(int(n)) if int(n) == n else str(n)


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


TASK_INSTRUCTION = "Solve the coordinate geometry problem"

MODULE_INFO = {
    'module_id': 'geometry.distance_midpoint',
    'name': 'Distance Midpoint',
    'topic': 'geometry',
    'subtopic': 'core_geometry',
    'difficulty_levels': ['level_1', 'level_2', 'level_3', 'level_4', 'level_5'],
    'enabled': True,
}
LEVEL_SPEC_CAPS = {'level_1': 500, 'level_2': 700, 'level_3': 800, 'level_4': 900, 'level_5': 1000}
FAMILY_CAPS = {
    'level_1': {'horizontal_vertical_distance': 500},
    'level_2': {'midpoint_integer': 700},
    'level_3': {'distance_pythagorean': 800},
    'level_4': {'midpoint_with_negatives': 900},
    'level_5': {'choose_distance_or_midpoint': 1000},
}
CAPACITY_HINTS = {k: {'value': v, 'quality': 'capped'} for k, v in LEVEL_SPEC_CAPS.items()}
CURRICULUM = {
    'level_1': ['distance on a horizontal or vertical line'],
    'level_2': ['midpoint of a segment with integer coordinates'],
    'level_3': ['distance between two points using the distance formula'],
    'level_4': ['midpoint with negative coordinates'],
    'level_5': ['mixed coordinate geometry with distance and midpoint'],
}


def iter_level1_specs():
    emitted = 0
    limit = FAMILY_CAPS['level_1']['horizontal_vertical_distance']
    for x1 in range(-12, 13):
        for x2 in range(-12, 13):
            if x1 == x2:
                continue
            y = (x1 + x2) % 9 - 4
            dist = abs(x2 - x1)
            problem = f"What is the distance between ({x1}, {y}) and ({x2}, {y})?"
            yield _spec('horizontal_vertical_distance', (x1, y, x2), problem, str(dist))
            emitted += 1
            if emitted >= limit:
                return


def iter_level2_specs():
    emitted = 0
    limit = FAMILY_CAPS['level_2']['midpoint_integer']
    for x1 in range(-10, 11):
        for y1 in range(-10, 11):
            for dx in range(-4, 5):
                for dy in range(-4, 5):
                    if dx == 0 and dy == 0:
                        continue
                    x2 = x1 + 2 * dx
                    y2 = y1 + 2 * dy
                    if not (-16 <= x2 <= 16 and -16 <= y2 <= 16):
                        continue
                    mx, my = x1 + dx, y1 + dy
                    problem = f"Find the midpoint of the segment with endpoints ({x1}, {y1}) and ({x2}, {y2})."
                    yield _spec('midpoint_integer', (x1, y1, x2, y2), problem, f"({_fmt_num(mx)}, {_fmt_num(my)})")
                    emitted += 1
                    if emitted >= limit:
                        return


def iter_level3_specs():
    emitted = 0
    limit = FAMILY_CAPS['level_3']['distance_pythagorean']
    triples = [(3, 4, 5), (5, 12, 13), (6, 8, 10), (8, 15, 17), (7, 24, 25)]
    for x1 in range(-8, 9):
        for y1 in range(-8, 9):
            for dx, dy, dist in triples:
                for sx in (-1, 1):
                    for sy in (-1, 1):
                        x2 = x1 + sx * dx
                        y2 = y1 + sy * dy
                        if not (-25 <= x2 <= 25 and -25 <= y2 <= 25):
                            continue
                        problem = f"Find the distance between ({x1}, {y1}) and ({x2}, {y2})."
                        yield _spec('distance_pythagorean', (x1, y1, x2, y2), problem, str(dist))
                        emitted += 1
                        if emitted >= limit:
                            return


def iter_level4_specs():
    emitted = 0
    limit = FAMILY_CAPS['level_4']['midpoint_with_negatives']
    for x1 in range(-14, 1):
        for y1 in range(-14, 1):
            for x2 in range(1, 15):
                for y2 in range(1, 15):
                    if (x1 + x2) % 2 or (y1 + y2) % 2:
                        continue
                    mx, my = (x1 + x2) / 2, (y1 + y2) / 2
                    problem = f"Find the midpoint of the segment joining ({x1}, {y1}) and ({x2}, {y2})."
                    yield _spec('midpoint_with_negatives', (x1, y1, x2, y2), problem, f"({_fmt_num(mx)}, {_fmt_num(my)})")
                    emitted += 1
                    if emitted >= limit:
                        return


def iter_level5_specs():
    emitted = 0
    limit = FAMILY_CAPS['level_5']['choose_distance_or_midpoint']
    for x1 in range(-8, 9):
        for y1 in range(-8, 9):
            x2 = x1 + 6
            y2 = y1 + 8
            if not (-20 <= x2 <= 20 and -20 <= y2 <= 20):
                continue
            problem = (
                f"For the points A({x1}, {y1}) and B({x2}, {y2}), find both the distance AB and the midpoint of AB. "
                f"Write the answer as distance, midpoint."
            )
            mx, my = (x1 + x2) / 2, (y1 + y2) / 2
            answer = f"10, ({_fmt_num(mx)}, {_fmt_num(my)})"
            yield _spec('choose_distance_or_midpoint', (x1, y1, x2, y2), problem, answer)
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
    chosen = []
    idx = offset
    while idx < len(pool) and len(chosen) < count:
        spec = pool[idx]
        key = spec['canonical_key']
        if key not in seen:
            seen.add(key)
            chosen.append(spec)
        idx += stride
    return [_sample_from_spec(spec, difficulty, i) for i, spec in enumerate(chosen)]


def iter_samples(difficulty='level_1', limit=MAX_ITER_SAMPLES):
    limit = min(max(0, int(limit)), MAX_ITER_SAMPLES)
    for i, spec in enumerate(_take(_iter_specs(difficulty), limit)):
        yield _sample_from_spec(spec, difficulty, i)


