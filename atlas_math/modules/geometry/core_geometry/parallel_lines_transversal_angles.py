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

TASK_INSTRUCTION = "Use parallel-line angle relationships"

MODULE_INFO = {
    'module_id': 'geometry.parallel_lines_transversal_angles',
    'name': 'Parallel Lines and Transversal Angles',
    'topic': 'geometry',
    'subtopic': 'core_geometry',
    'difficulty_levels': ['level_1', 'level_2', 'level_3', 'level_4', 'level_5'],
    'enabled': True,
}
LEVEL_SPEC_CAPS = {'level_1': 500, 'level_2': 650, 'level_3': 800, 'level_4': 900, 'level_5': 1000}
FAMILY_CAPS = {
    'level_1': {'corresponding': 500},
    'level_2': {'alternate_interior': 650},
    'level_3': {'same_side_interior': 800},
    'level_4': {'expression_corresponding': 900},
    'level_5': {'expression_same_side': 1000},
}
CAPACITY_HINTS = {k: {'value': v, 'quality': 'capped'} for k, v in LEVEL_SPEC_CAPS.items()}
CURRICULUM = {
    'level_1': ['corresponding angles'],
    'level_2': ['alternate interior angles'],
    'level_3': ['same-side interior angles'],
    'level_4': ['solve variable in corresponding-angle setting'],
    'level_5': ['solve variable in same-side-interior setting'],
}


def iter_level1_specs():
    emitted = 0
    limit = FAMILY_CAPS['level_1']['corresponding']
    for a in range(15, 166):
        yield _spec('corresponding', (a,), f"Two parallel lines are cut by a transversal. If one corresponding angle is {a}°, what is the measure of the other corresponding angle?", str(a))
        emitted += 1
        if emitted >= limit:
            return


def iter_level2_specs():
    emitted = 0
    limit = FAMILY_CAPS['level_2']['alternate_interior']
    for a in range(15, 166):
        yield _spec('alternate_interior', (a,), f"Two parallel lines are cut by a transversal. If one alternate interior angle is {a}°, what is the measure of the other alternate interior angle?", str(a))
        emitted += 1
        if emitted >= limit:
            return


def iter_level3_specs():
    emitted = 0
    limit = FAMILY_CAPS['level_3']['same_side_interior']
    for a in range(15, 166):
        b = 180 - a
        yield _spec('same_side_interior', (a,), f"Two parallel lines are cut by a transversal. If one same-side interior angle is {a}°, what is the measure of the other same-side interior angle?", str(b))
        emitted += 1
        if emitted >= limit:
            return


def iter_level4_specs():
    emitted = 0
    limit = FAMILY_CAPS['level_4']['expression_corresponding']
    for x in range(2, 31):
        for a in range(1, 6):
            for b in range(0, 16):
                val = a * x + b
                if not (10 <= val <= 170):
                    continue
                problem = f"Two parallel lines are cut by a transversal. One corresponding angle is {a}x + {b} degrees and the matching corresponding angle is {val} degrees. Find x."
                yield _spec('expression_corresponding', (x, a, b), problem, str(x))
                emitted += 1
                if emitted >= limit:
                    return


def iter_level5_specs():
    emitted = 0
    limit = FAMILY_CAPS['level_5']['expression_same_side']
    for x in range(2, 31):
        for a in range(1, 5):
            for b in range(0, 21):
                first = a * x + b
                if not (10 <= first <= 170):
                    continue
                second = 180 - first
                problem = f"Two parallel lines are cut by a transversal. One same-side interior angle is {a}x + {b} degrees and the other same-side interior angle is {second} degrees. Find x."
                yield _spec('expression_same_side', (x, a, b, second), problem, str(x))
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


