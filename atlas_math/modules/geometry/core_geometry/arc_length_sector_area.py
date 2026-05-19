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

TASK_INSTRUCTION = 'Use arc length and sector area formulas with π = 3.14'
MODULE_INFO = {'module_id': 'geometry.arc_length_sector_area', 'name': 'Arc Length Sector Area', 'topic': 'geometry', 'subtopic': 'core_geometry', 'difficulty_levels': ['level_1', 'level_2', 'level_3', 'level_4', 'level_5'], 'enabled': True}
LEVEL_SPEC_CAPS = {'level_1': 240, 'level_2': 240, 'level_3': 240, 'level_4': 240, 'level_5': 240}
FAMILY_CAPS = {
    'level_1': {'arc_length_quarter_half': 240},
    'level_2': {'sector_area_quarter_half': 240},
    'level_3': {'arc_length_general_angle': 240},
    'level_4': {'sector_area_general_angle': 240},
    'level_5': {'compare_sector_and_arc': 240},
}
CAPACITY_HINTS = {k: {'value': v, 'quality': 'capped'} for k, v in LEVEL_SPEC_CAPS.items()}
CURRICULUM = {
    'level_1': ['arc length for common fractions of a circle'],
    'level_2': ['sector area for common fractions of a circle'],
    'level_3': ['arc length with general central angle'],
    'level_4': ['sector area with general central angle'],
    'level_5': ['multi-step circle sector comparison'],
}
PI = 3.14

def iter_level1_specs():
    emitted = 0; limit = FAMILY_CAPS['level_1']['arc_length_quarter_half']
    for r in range(1, 31):
        for deg, frac_name in [(90, 'quarter'), (180, 'half')]:
            arc = 2 * PI * r * deg / 360
            yield _spec('arc_length_quarter_half', (r, deg), f"A circle has radius {r}. What is the arc length of a {deg}° arc? Use π = 3.14.", _num(arc))
            emitted += 1
            if emitted >= limit:
                return

def iter_level2_specs():
    emitted = 0; limit = FAMILY_CAPS['level_2']['sector_area_quarter_half']
    for r in range(1, 26):
        for deg in (90, 180):
            area = PI * r * r * deg / 360
            yield _spec('sector_area_quarter_half', (r, deg), f"A circle has radius {r}. What is the area of a {deg}° sector? Use π = 3.14.", _num(area))
            emitted += 1
            if emitted >= limit:
                return

def iter_level3_specs():
    emitted = 0; limit = FAMILY_CAPS['level_3']['arc_length_general_angle']
    for r in range(1, 31):
        for deg in range(30, 331, 15):
            arc = 2 * PI * r * deg / 360
            yield _spec('arc_length_general_angle', (r, deg), f"A circle has radius {r}. What is the arc length of a {deg}° arc? Use π = 3.14.", _num(arc))
            emitted += 1
            if emitted >= limit:
                return

def iter_level4_specs():
    emitted = 0; limit = FAMILY_CAPS['level_4']['sector_area_general_angle']
    for r in range(1, 26):
        for deg in range(30, 331, 15):
            area = PI * r * r * deg / 360
            yield _spec('sector_area_general_angle', (r, deg), f"A circle has radius {r}. What is the area of a {deg}° sector? Use π = 3.14.", _num(area))
            emitted += 1
            if emitted >= limit:
                return

def iter_level5_specs():
    emitted = 0; limit = FAMILY_CAPS['level_5']['compare_sector_and_arc']
    for r in range(2, 26):
        for deg1 in (60, 90, 120, 150):
            for deg2 in (180, 240, 300):
                diff = PI * r * r * (deg2 - deg1) / 360
                yield _spec('compare_sector_and_arc', (r, deg1, deg2), f"In a circle of radius {r}, one sector has central angle {deg1}° and another has central angle {deg2}°. Using π = 3.14, what is the positive difference between the areas of the two sectors?", _num(diff))
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


