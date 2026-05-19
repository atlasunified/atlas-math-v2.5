from __future__ import annotations

import itertools
import random
from typing import Iterable

from atlas_math.modules.shared.common import make_sample

INSTRUCTIONS = ["{instruction}: {problem}", "Solve and report the result: {problem}", "Work the problem and give the final answer: {problem}", "Compute the requested result: {problem}"]
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
    return {'family': family, 'values': values, 'problem': problem, 'answer': answer, 'canonical_key': canonical, 'case_id': canonical, 'family_id': family}


def _sample_from_spec(spec, difficulty, instruction_idx=0):
    answer = spec['answer']
    metadata = {'family': spec['family'], 'level_number': _level_num(difficulty), 'structured': True, 'canonical_key': spec['canonical_key'], 'case_id': spec['case_id'], 'family_id': spec['family_id'], 'template_id': spec['family'], 'final_answer': answer, 'values': list(spec.get('values', []))}
    instruction = INSTRUCTIONS[instruction_idx % len(INSTRUCTIONS)].format(instruction=TASK_INSTRUCTION, problem=spec['problem'])
    return make_sample(module_id=MODULE_INFO['module_id'], topic=MODULE_INFO['topic'], subtopic=MODULE_INFO['subtopic'], difficulty=difficulty, instruction=instruction, input_text=spec['problem'], answer=answer, metadata=metadata)


TASK_INSTRUCTION = 'Find the volume of the rectangular prism'
MODULE_INFO = {'module_id': 'geometry.volume_rectangular_prism', 'name': 'Volume Rectangular Prism', 'topic': 'geometry', 'subtopic': 'core_geometry', 'difficulty_levels': ['level_1', 'level_2', 'level_3', 'level_4', 'level_5'], 'enabled': True}
LEVEL_SPEC_CAPS = {'level_1': 500, 'level_2': 700, 'level_3': 800, 'level_4': 900, 'level_5': 1000}
FAMILY_CAPS = {'level_1': {'integer_dims': 500}, 'level_2': {'missing_factor': 700}, 'level_3': {'larger_integers': 800}, 'level_4': {'word_problem': 900}, 'level_5': {'compare_prisms': 1000}}
CAPACITY_HINTS = {k: {'value': v, 'quality': 'capped'} for k, v in LEVEL_SPEC_CAPS.items()}
CURRICULUM = {'level_1': ['volume from three integer dimensions'], 'level_2': ['find a missing dimension from volume'], 'level_3': ['volume with larger integers'], 'level_4': ['volume in a word problem'], 'level_5': ['compare two rectangular prisms']}


def iter_level1_specs():
    emitted = 0; limit = FAMILY_CAPS['level_1']['integer_dims']
    for l in range(2, 21):
        for w in range(2, 16):
            for h in range(2, 11):
                yield _spec('integer_dims', (l, w, h), f"A rectangular prism has length {l}, width {w}, and height {h}. What is its volume?", str(l * w * h))
                emitted += 1
                if emitted >= limit:
                    return


def iter_level2_specs():
    emitted = 0; limit = FAMILY_CAPS['level_2']['missing_factor']
    for l in range(2, 21):
        for w in range(2, 16):
            for h in range(2, 11):
                v = l * w * h
                yield _spec('missing_factor', (l, w, v), f"A rectangular prism has volume {v}. Its length is {l} and its width is {w}. What is its height?", str(h))
                emitted += 1
                if emitted >= limit:
                    return


def iter_level3_specs():
    emitted = 0; limit = FAMILY_CAPS['level_3']['larger_integers']
    for l in range(10, 41):
        for w in range(5, 21):
            for h in range(4, 13):
                yield _spec('larger_integers', (l, w, h), f"Find the volume of a rectangular prism with dimensions {l} by {w} by {h}.", str(l * w * h))
                emitted += 1
                if emitted >= limit:
                    return


def iter_level4_specs():
    emitted = 0; limit = FAMILY_CAPS['level_4']['word_problem']
    for l in range(3, 26):
        for w in range(3, 16):
            for h in range(2, 13):
                yield _spec('word_problem', (l, w, h), f"A storage box is {l} cm long, {w} cm wide, and {h} cm tall. How many cubic centimeters does it hold?", str(l * w * h))
                emitted += 1
                if emitted >= limit:
                    return


def iter_level5_specs():
    emitted = 0; limit = FAMILY_CAPS['level_5']['compare_prisms']
    for l1 in range(2, 16):
        for w1 in range(2, 11):
            for h1 in range(2, 9):
                v1 = l1 * w1 * h1
                l2, w2, h2 = l1 + 1, w1 + 1, h1
                v2 = l2 * w2 * h2
                yield _spec('compare_prisms', (l1, w1, h1, l2, w2, h2), f"Prism A has dimensions {l1} by {w1} by {h1}. Prism B has dimensions {l2} by {w2} by {h2}. What is the positive difference between their volumes?", str(abs(v2 - v1)))
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


