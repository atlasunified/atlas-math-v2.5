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

TASK_INSTRUCTION = "Use triangle similarity to find the missing value"

MODULE_INFO = {
    'module_id': 'geometry.similar_triangles_numeric',
    'name': 'Similar Triangles Numeric',
    'topic': 'geometry',
    'subtopic': 'core_geometry',
    'difficulty_levels': ['level_1', 'level_2', 'level_3', 'level_4', 'level_5'],
    'enabled': True,
}
LEVEL_SPEC_CAPS = {'level_1': 420, 'level_2': 520, 'level_3': 620, 'level_4': 700, 'level_5': 840}
FAMILY_CAPS = {
    'level_1': {'single_scale_up': 420},
    'level_2': {'single_scale_down': 520},
    'level_3': {'perimeter_similarity': 620},
    'level_4': {'area_similarity': 700},
    'level_5': {'multi_step_similarity': 840},
}
CAPACITY_HINTS = {k: {'value': v, 'quality': 'capped'} for k, v in LEVEL_SPEC_CAPS.items()}
CURRICULUM = {
    'level_1': ['find a corresponding side using scale up'],
    'level_2': ['find a corresponding side using scale down'],
    'level_3': ['perimeter relationships in similar triangles'],
    'level_4': ['area relationships in similar triangles'],
    'level_5': ['multi-step similarity problems'],
}

def iter_level1_specs():
    emitted = 0
    limit = FAMILY_CAPS['level_1']['single_scale_up']
    for a in range(2, 21):
        for b in range(3, 25):
            for k in range(2, 11):
                yield _spec('single_scale_up', (a, b, k), f"Two triangles are similar. In the smaller triangle, a side is {a}. The corresponding side in the larger triangle is {a*k}. Another side in the smaller triangle is {b}. Find the corresponding side in the larger triangle.", str(b * k))
                emitted += 1
                if emitted >= limit:
                    return


def iter_level2_specs():
    emitted = 0
    limit = FAMILY_CAPS['level_2']['single_scale_down']
    for a in range(2, 21):
        for b in range(3, 25):
            for k in range(2, 11):
                yield _spec('single_scale_down', (a, b, k), f"Two triangles are similar. In the larger triangle, a side is {a*k}. The corresponding side in the smaller triangle is {a}. Another side in the larger triangle is {b*k}. Find the corresponding side in the smaller triangle.", str(b))
                emitted += 1
                if emitted >= limit:
                    return


def iter_level3_specs():
    emitted = 0
    limit = FAMILY_CAPS['level_3']['perimeter_similarity']
    for p in range(12, 81):
        for k in range(2, 11):
            yield _spec('perimeter_similarity', (p, k), f"Two triangles are similar. The perimeter of the smaller triangle is {p}. If the scale factor from the smaller triangle to the larger triangle is {k}, find the perimeter of the larger triangle.", str(p * k))
            emitted += 1
            if emitted >= limit:
                return


def iter_level4_specs():
    emitted = 0
    limit = FAMILY_CAPS['level_4']['area_similarity']
    for area in range(3, 88):
        for k in range(2, 11):
            yield _spec('area_similarity', (area, k), f"Two triangles are similar. The area of the smaller triangle is {area}. If the scale factor from the smaller triangle to the larger triangle is {k}, find the area of the larger triangle.", str(area * k * k))
            emitted += 1
            if emitted >= limit:
                return


def iter_level5_specs():
    emitted = 0
    limit = FAMILY_CAPS['level_5']['multi_step_similarity']
    for a in range(2, 21):
        for b in range(3, 25):
            for c in range(4, 29):
                for k in range(2, 8):
                    large_a = a * k
                    large_b = b * k
                    problem = f"Triangles ABC and DEF are similar. In triangle ABC, the sides are {a}, {b}, and {c}. In triangle DEF, the sides corresponding to {a} and {b} are {large_a} and {large_b}. Find the side corresponding to {c}."
                    yield _spec('multi_step_similarity', (a, b, c, k), problem, str(c * k))
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


