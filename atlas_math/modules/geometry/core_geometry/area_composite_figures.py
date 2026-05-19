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

TASK_INSTRUCTION = 'Find the area of the composite figure described textually'
MODULE_INFO = {'module_id': 'geometry.area_composite_figures', 'name': 'Area Composite Figures', 'topic': 'geometry', 'subtopic': 'core_geometry', 'difficulty_levels': ['level_1', 'level_2', 'level_3', 'level_4', 'level_5'], 'enabled': True}
LEVEL_SPEC_CAPS = {'level_1': 240, 'level_2': 240, 'level_3': 240, 'level_4': 240, 'level_5': 240}
FAMILY_CAPS = {
    'level_1': {'two_rectangles_add': 240},
    'level_2': {'large_minus_small_rectangle': 240},
    'level_3': {'rectangle_plus_triangle': 240},
    'level_4': {'rectangle_plus_semicircle': 240},
    'level_5': {'l_shape_gridlike': 240},
}
CAPACITY_HINTS = {k: {'value': v, 'quality': 'capped'} for k, v in LEVEL_SPEC_CAPS.items()}
CURRICULUM = {
    'level_1': ['sum areas of two rectangles'],
    'level_2': ['subtract a missing rectangle'],
    'level_3': ['combine rectangle and triangle'],
    'level_4': ['combine rectangle and semicircle using π = 3.14'],
    'level_5': ['l-shaped region from outer and cutout rectangles'],
}

def iter_level1_specs():
    emitted = 0; limit = FAMILY_CAPS['level_1']['two_rectangles_add']
    for a in range(2, 21):
        for b in range(2, 21):
            for c in range(2, 16):
                for d in range(2, 16):
                    ans = a * b + c * d
                    yield _spec('two_rectangles_add', (a, b, c, d), f"A composite figure is made from two non-overlapping rectangles. One rectangle measures {a} by {b}. The other measures {c} by {d}. What is the total area?", str(ans))
                    emitted += 1
                    if emitted >= limit:
                        return

def iter_level2_specs():
    emitted = 0; limit = FAMILY_CAPS['level_2']['large_minus_small_rectangle']
    for W in range(6, 31):
        for H in range(6, 31):
            for w in range(1, W):
                for h in range(1, H):
                    ans = W * H - w * h
                    yield _spec('large_minus_small_rectangle', (W, H, w, h), f"A large rectangle measures {W} by {H}. A smaller rectangular section measuring {w} by {h} is removed from it. What is the remaining area?", str(ans))
                    emitted += 1
                    if emitted >= limit:
                        return

def iter_level3_specs():
    emitted = 0; limit = FAMILY_CAPS['level_3']['rectangle_plus_triangle']
    for w in range(2, 25):
        for h in range(2, 25):
            for b in range(2, 21):
                for th in range(2, 21):
                    ans = w * h + 0.5 * b * th
                    yield _spec('rectangle_plus_triangle', (w, h, b, th), f"A figure is made from a rectangle of dimensions {w} by {h} and a triangle with base {b} and height {th}. They do not overlap. What is the total area?", _num(ans))
                    emitted += 1
                    if emitted >= limit:
                        return

def iter_level4_specs():
    emitted = 0; limit = FAMILY_CAPS['level_4']['rectangle_plus_semicircle']
    for w in range(2, 21):
        for h in range(2, 21):
            for r in range(1, 11):
                ans = w * h + 0.5 * 3.14 * r * r
                yield _spec('rectangle_plus_semicircle', (w, h, r), f"A figure is made from a rectangle measuring {w} by {h} and a semicircle of radius {r}. Using π = 3.14, what is the total area?", _num(ans))
                emitted += 1
                if emitted >= limit:
                    return

def iter_level5_specs():
    emitted = 0; limit = FAMILY_CAPS['level_5']['l_shape_gridlike']
    for W in range(5, 31):
        for H in range(5, 31):
            for cut_w in range(1, W-1):
                for cut_h in range(1, H-1):
                    ans = W * H - cut_w * cut_h
                    yield _spec('l_shape_gridlike', (W, H, cut_w, cut_h), f"An L-shaped figure can be viewed as a {W} by {H} rectangle with a {cut_w} by {cut_h} corner removed. What is the area of the L-shaped figure?", str(ans))
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


