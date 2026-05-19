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

TASK_INSTRUCTION = "Apply the Pythagorean theorem"

MODULE_INFO = {
    'module_id': 'geometry.pythagorean_theorem',
    'name': 'Pythagorean Theorem',
    'topic': 'geometry',
    'subtopic': 'core_geometry',
    'difficulty_levels': ['level_1', 'level_2', 'level_3', 'level_4', 'level_5'],
    'enabled': True,
}
LEVEL_SPEC_CAPS = {'level_1': 450, 'level_2': 550, 'level_3': 700, 'level_4': 850, 'level_5': 1000}
FAMILY_CAPS = {
    'level_1': {'find_hypotenuse_integer': 450},
    'level_2': {'find_leg_integer': 550},
    'level_3': {'word_problem_distance': 700},
    'level_4': {'simplify_radical_hypotenuse': 850},
    'level_5': {'coordinate_distance': 1000},
}
CAPACITY_HINTS = {k: {'value': v, 'quality': 'capped'} for k, v in LEVEL_SPEC_CAPS.items()}
CURRICULUM = {
    'level_1': ['find a hypotenuse from integer legs'],
    'level_2': ['find a leg from a leg and hypotenuse'],
    'level_3': ['distance-style word problems'],
    'level_4': ['simplify square-root answers'],
    'level_5': ['distance on the coordinate plane'],
}
TRIPLES = [(3,4,5),(5,12,13),(6,8,10),(8,15,17),(7,24,25),(9,12,15)]


def _sqrt_simplified(n: int) -> str:
    outside = 1
    inside = n
    factor = 2
    while factor * factor <= inside:
        while inside % (factor * factor) == 0:
            outside *= factor
            inside //= factor * factor
        factor += 1
    if inside == 1:
        return str(outside)
    if outside == 1:
        return f"sqrt({inside})"
    return f"{outside}sqrt({inside})"


def iter_level1_specs():
    emitted = 0
    limit = FAMILY_CAPS['level_1']['find_hypotenuse_integer']
    for a, b, c in TRIPLES:
        for scale in range(1, 21):
            aa, bb, cc = a * scale, b * scale, c * scale
            yield _spec('find_hypotenuse_integer', (aa, bb), f"A right triangle has legs {aa} and {bb}. Find the hypotenuse.", str(cc))
            emitted += 1
            if emitted >= limit:
                return


def iter_level2_specs():
    emitted = 0
    limit = FAMILY_CAPS['level_2']['find_leg_integer']
    for a, b, c in TRIPLES:
        for scale in range(1, 21):
            aa, bb, cc = a * scale, b * scale, c * scale
            yield _spec('find_leg_integer', (aa, cc), f"A right triangle has one leg {aa} and hypotenuse {cc}. Find the other leg.", str(bb))
            emitted += 1
            if emitted >= limit:
                return
            yield _spec('find_leg_integer', (bb, cc), f"A right triangle has one leg {bb} and hypotenuse {cc}. Find the other leg.", str(aa))
            emitted += 1
            if emitted >= limit:
                return


def iter_level3_specs():
    emitted = 0
    limit = FAMILY_CAPS['level_3']['word_problem_distance']
    for a, b, c in TRIPLES:
        for scale in range(1, 16):
            aa, bb, cc = a * scale, b * scale, c * scale
            problem = f"A ladder is placed {aa} feet from a wall and reaches a point {bb} feet up the wall. How long is the ladder?"
            yield _spec('word_problem_distance', (aa, bb), problem, str(cc))
            emitted += 1
            if emitted >= limit:
                return


def iter_level4_specs():
    emitted = 0
    limit = FAMILY_CAPS['level_4']['simplify_radical_hypotenuse']
    for a in range(2, 26):
        for b in range(2, 26):
            s = a * a + b * b
            if int(math.isqrt(s)) ** 2 == s:
                continue
            problem = f"A right triangle has legs {a} and {b}. Find the hypotenuse in simplest radical form."
            yield _spec('simplify_radical_hypotenuse', (a, b), problem, _sqrt_simplified(s))
            emitted += 1
            if emitted >= limit:
                return


def iter_level5_specs():
    emitted = 0
    limit = FAMILY_CAPS['level_5']['coordinate_distance']
    for x1 in range(-6, 7):
        for y1 in range(-6, 7):
            for dx, dy, _ in TRIPLES:
                x2, y2 = x1 + dx, y1 + dy
                problem = f"Find the distance between ({x1}, {y1}) and ({x2}, {y2})."
                yield _spec('coordinate_distance', (x1, y1, x2, y2), problem, str(int(math.hypot(dx, dy))))
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


