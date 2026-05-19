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

TASK_INSTRUCTION = "Use triangle side relationships"

MODULE_INFO = {
    'module_id': 'geometry.triangle_side_relationships',
    'name': 'Triangle Side Relationships',
    'topic': 'geometry',
    'subtopic': 'core_geometry',
    'difficulty_levels': ['level_1', 'level_2', 'level_3', 'level_4', 'level_5'],
    'enabled': True,
}
LEVEL_SPEC_CAPS = {'level_1': 400, 'level_2': 500, 'level_3': 700, 'level_4': 850, 'level_5': 950}
FAMILY_CAPS = {
    'level_1': {'classify_triangle_inequality': 400},
    'level_2': {'possible_third_side_range': 500},
    'level_3': {'longest_side_from_angles': 700},
    'level_4': {'solve_triangle_inequality': 850},
    'level_5': {'sort_sides_by_angles': 950},
}
CAPACITY_HINTS = {k: {'value': v, 'quality': 'capped'} for k, v in LEVEL_SPEC_CAPS.items()}
CURRICULUM = {
    'level_1': ['decide whether three lengths can form a triangle'],
    'level_2': ['find integer possibilities for a third side'],
    'level_3': ['match largest angle to longest side'],
    'level_4': ['solve basic triangle inequality for a variable'],
    'level_5': ['order sides using angle sizes'],
}


def iter_level1_specs():
    emitted = 0
    limit = FAMILY_CAPS['level_1']['classify_triangle_inequality']
    for a in range(2, 21):
        for b in range(2, 21):
            for c in range(2, 21):
                answer = 'yes' if a + b > c and a + c > b and b + c > a else 'no'
                problem = f"Can side lengths {a}, {b}, and {c} form a triangle? Answer yes or no."
                yield _spec('classify_triangle_inequality', (a, b, c), problem, answer)
                emitted += 1
                if emitted >= limit:
                    return


def iter_level2_specs():
    emitted = 0
    limit = FAMILY_CAPS['level_2']['possible_third_side_range']
    for a in range(3, 21):
        for b in range(3, 21):
            lo = abs(a - b) + 1
            hi = a + b - 1
            if lo > hi:
                continue
            problem = f"A triangle has side lengths {a}, {b}, and x where x is an integer. What is the smallest and largest possible value of x? Give your answer as smallest to largest."
            yield _spec('possible_third_side_range', (a, b), problem, f"{lo} to {hi}")
            emitted += 1
            if emitted >= limit:
                return


def iter_level3_specs():
    emitted = 0
    limit = FAMILY_CAPS['level_3']['longest_side_from_angles']
    for A in range(20, 121):
        for B in range(20, 121):
            C = 180 - A - B
            if C <= 0:
                continue
            angles = {'a': A, 'b': B, 'c': C}
            longest = max(angles, key=lambda k: (angles[k], k))
            problem = f"In triangle ABC, angle A = {A}°, angle B = {B}°, and angle C = {C}°. Which side is longest: a, b, or c?"
            yield _spec('longest_side_from_angles', (A, B), problem, longest)
            emitted += 1
            if emitted >= limit:
                return


def iter_level4_specs():
    emitted = 0
    limit = FAMILY_CAPS['level_4']['solve_triangle_inequality']
    for x in range(2, 31):
        for b in range(1, 10):
            first = x + b
            for second in range(3, 21):
                for third in range(3, 21):
                    if first + second > third and first + third > second and second + third > first:
                        problem = f"The side lengths of a triangle are x + {b}, {second}, and {third}. If x is a positive integer and the triangle is valid, find one possible value of x: use x = {x}."
                        yield _spec('solve_triangle_inequality', (x, b, second, third), problem, str(x))
                        emitted += 1
                        if emitted >= limit:
                            return


def iter_level5_specs():
    emitted = 0
    limit = FAMILY_CAPS['level_5']['sort_sides_by_angles']
    for A in range(30, 101, 5):
        for B in range(30, 101, 5):
            C = 180 - A - B
            if C <= 0:
                continue
            ordered = sorted([('a', A), ('b', B), ('c', C)], key=lambda t: (t[1], t[0]))
            answer = ' < '.join([name for name, _ in ordered])
            problem = f"In triangle ABC, angle A = {A}°, angle B = {B}°, and angle C = {C}°. Order the sides from shortest to longest using a, b, and c."
            yield _spec('sort_sides_by_angles', (A, B), problem, answer)
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


