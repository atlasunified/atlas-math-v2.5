from __future__ import annotations

import itertools
import random
from typing import Iterable

from atlas_math.modules.shared.common import make_sample

INSTRUCTIONS = ["{instruction}: {problem}", "Solve and report the result: {problem}", "Work the problem and give the final answer: {problem}", "Compute the requested result: {problem}"]
MAX_SPEC_PREFIX = 5000
MAX_GENERATE_MULTIPLIER = 8
MAX_ITER_SAMPLES = 4096
PI = 3.14


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
    return {'family': family, 'values': values, 'problem': problem, 'answer': answer, 'canonical_key': canonical, 'case_id': canonical, 'family_id': family}


def _num(v):
    return f"{v:.2f}".rstrip('0').rstrip('.') if isinstance(v, float) and not float(v).is_integer() else str(int(v)) if float(v).is_integer() else str(v)


def _sample_from_spec(spec, difficulty, instruction_idx=0):
    answer = spec['answer']
    metadata = {'family': spec['family'], 'level_number': _level_num(difficulty), 'structured': True, 'canonical_key': spec['canonical_key'], 'case_id': spec['case_id'], 'family_id': spec['family_id'], 'template_id': spec['family'], 'final_answer': answer, 'values': list(spec.get('values', []))}
    instruction = INSTRUCTIONS[instruction_idx % len(INSTRUCTIONS)].format(instruction=TASK_INSTRUCTION, problem=spec['problem'])
    return make_sample(module_id=MODULE_INFO['module_id'], topic=MODULE_INFO['topic'], subtopic=MODULE_INFO['subtopic'], difficulty=difficulty, instruction=instruction, input_text=spec['problem'], answer=answer, metadata=metadata)


TASK_INSTRUCTION = 'Use volume formulas with π = 3.14 unless noted'
MODULE_INFO = {'module_id': 'geometry.volume_cylinder_cone_sphere', 'name': 'Volume Cylinder Cone Sphere', 'topic': 'geometry', 'subtopic': 'core_geometry', 'difficulty_levels': ['level_1', 'level_2', 'level_3', 'level_4', 'level_5'], 'enabled': True}
LEVEL_SPEC_CAPS = {'level_1': 500, 'level_2': 700, 'level_3': 800, 'level_4': 900, 'level_5': 1000}
FAMILY_CAPS = {'level_1': {'cylinder_volume': 500}, 'level_2': {'cone_volume': 700}, 'level_3': {'sphere_volume': 800}, 'level_4': {'mixed_solids': 900}, 'level_5': {'compare_solids': 1000}}
CAPACITY_HINTS = {k: {'value': v, 'quality': 'capped'} for k, v in LEVEL_SPEC_CAPS.items()}
CURRICULUM = {'level_1': ['volume of a cylinder'], 'level_2': ['volume of a cone'], 'level_3': ['volume of a sphere'], 'level_4': ['identify and use the right solid formula'], 'level_5': ['compare volumes of solids']}


def iter_level1_specs():
    emitted = 0; limit = FAMILY_CAPS['level_1']['cylinder_volume']
    for r in range(1, 21):
        for h in range(2, 31):
            yield _spec('cylinder_volume', (r, h), f"A cylinder has radius {r} and height {h}. Using π = 3.14, what is its volume?", _num(PI * r * r * h))
            emitted += 1
            if emitted >= limit:
                return


def iter_level2_specs():
    emitted = 0; limit = FAMILY_CAPS['level_2']['cone_volume']
    for r in range(1, 21):
        for h in range(3, 33, 3):
            yield _spec('cone_volume', (r, h), f"A cone has radius {r} and height {h}. Using π = 3.14, what is its volume?", _num(PI * r * r * h / 3))
            emitted += 1
            if emitted >= limit:
                return


def iter_level3_specs():
    emitted = 0; limit = FAMILY_CAPS['level_3']['sphere_volume']
    for r in range(1, 25):
        yield _spec('sphere_volume', (r,), f"A sphere has radius {r}. Using π = 3.14, what is its volume?", _num(4 * PI * r ** 3 / 3))
        emitted += 1
        if emitted >= limit:
            return


def iter_level4_specs():
    emitted = 0; limit = FAMILY_CAPS['level_4']['mixed_solids']
    for r in range(1, 16):
        for h in range(2, 21):
            yield _spec('mixed_solids', ('cyl', r, h), f"A solid is a cylinder with radius {r} and height {h}. Using π = 3.14, find its volume.", _num(PI * r * r * h))
            emitted += 1
            if emitted >= limit:
                return
            yield _spec('mixed_solids', ('cone', r, h), f"A solid is a cone with radius {r} and height {h}. Using π = 3.14, find its volume.", _num(PI * r * r * h / 3))
            emitted += 1
            if emitted >= limit:
                return


def iter_level5_specs():
    emitted = 0; limit = FAMILY_CAPS['level_5']['compare_solids']
    for r in range(1, 16):
        for h in range(2, 21):
            cyl = PI * r * r * h
            cone = cyl / 3
            yield _spec('compare_solids', (r, h), f"A cylinder and a cone have the same radius {r} and height {h}. Using π = 3.14, what is the positive difference between their volumes?", _num(cyl - cone))
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


