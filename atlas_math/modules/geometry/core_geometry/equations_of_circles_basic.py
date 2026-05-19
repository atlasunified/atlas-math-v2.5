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

TASK_INSTRUCTION = 'Write the equation of the circle in standard form or read information from it'
MODULE_INFO = {'module_id': 'geometry.equations_of_circles_basic', 'name': 'Equations Of Circles Basic', 'topic': 'geometry', 'subtopic': 'core_geometry', 'difficulty_levels': ['level_1', 'level_2', 'level_3', 'level_4', 'level_5'], 'enabled': True}
LEVEL_SPEC_CAPS = {'level_1': 250, 'level_2': 300, 'level_3': 300, 'level_4': 300, 'level_5': 300}
FAMILY_CAPS = {
    'level_1': {'center_origin': 250},
    'level_2': {'center_integer': 300},
    'level_3': {'read_radius': 300},
    'level_4': {'read_center': 300},
    'level_5': {'point_on_circle': 300},
}
CAPACITY_HINTS = {k: {'value': v, 'quality': 'capped'} for k, v in LEVEL_SPEC_CAPS.items()}
CURRICULUM = {
    'level_1': ['equation with center at origin'],
    'level_2': ['equation with nonzero center'],
    'level_3': ['read radius from equation'],
    'level_4': ['read center from equation'],
    'level_5': ['check whether a point lies on a circle'],
}

def _eq(h, k, r):
    return f"(x - {h})^2 + (y - {k})^2 = {r*r}" if h >= 0 and k >= 0 else f"(x - {h})^2 + (y - {k})^2 = {r*r}"

def iter_level1_specs():
    emitted = 0; limit = FAMILY_CAPS['level_1']['center_origin']
    for r in range(1, 26):
        yield _spec('center_origin', (r,), f"Write the equation of the circle with center (0, 0) and radius {r}.", f"x^2 + y^2 = {r*r}")
        emitted += 1
        if emitted >= limit:
            return

def iter_level2_specs():
    emitted = 0; limit = FAMILY_CAPS['level_2']['center_integer']
    for h in range(-8, 9):
        for k in range(-8, 9):
            if h == 0 and k == 0:
                continue
            for r in range(1, 7):
                xpart = f"(x - {h})^2" if h >= 0 else f"(x + {abs(h)})^2"
                ypart = f"(y - {k})^2" if k >= 0 else f"(y + {abs(k)})^2"
                yield _spec('center_integer', (h, k, r), f"Write the equation of the circle with center ({h}, {k}) and radius {r}.", f"{xpart} + {ypart} = {r*r}")
                emitted += 1
                if emitted >= limit:
                    return

def iter_level3_specs():
    emitted = 0; limit = FAMILY_CAPS['level_3']['read_radius']
    for h in range(-5, 6):
        for k in range(-5, 6):
            for r in range(1, 11):
                xpart = f"(x - {h})^2" if h >= 0 else f"(x + {abs(h)})^2"
                ypart = f"(y - {k})^2" if k >= 0 else f"(y + {abs(k)})^2"
                yield _spec('read_radius', (h, k, r), f"For the circle {xpart} + {ypart} = {r*r}, what is the radius?", str(r))
                emitted += 1
                if emitted >= limit:
                    return

def iter_level4_specs():
    emitted = 0; limit = FAMILY_CAPS['level_4']['read_center']
    for h in range(-6, 7):
        for k in range(-6, 7):
            for r in range(1, 8):
                xpart = f"(x - {h})^2" if h >= 0 else f"(x + {abs(h)})^2"
                ypart = f"(y - {k})^2" if k >= 0 else f"(y + {abs(k)})^2"
                yield _spec('read_center', (h, k, r), f"For the circle {xpart} + {ypart} = {r*r}, what is the center?", f"({h}, {k})")
                emitted += 1
                if emitted >= limit:
                    return

def iter_level5_specs():
    emitted = 0; limit = FAMILY_CAPS['level_5']['point_on_circle']
    triples = [(3, 4, 5), (5, 12, 13), (8, 15, 17), (7, 24, 25)]
    for h in range(-4, 5):
        for k in range(-4, 5):
            for a, b, r in triples:
                for sx in (-1, 1):
                    for sy in (-1, 1):
                        px, py = h + sx * a, k + sy * b
                        xpart = f"(x - {h})^2" if h >= 0 else f"(x + {abs(h)})^2"
                        ypart = f"(y - {k})^2" if k >= 0 else f"(y + {abs(k)})^2"
                        yield _spec('point_on_circle', (h, k, r, px, py), f"Does the point ({px}, {py}) lie on the circle {xpart} + {ypart} = {r*r}? Answer yes or no.", 'yes')
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


