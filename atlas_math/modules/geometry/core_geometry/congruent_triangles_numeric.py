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

TASK_INSTRUCTION = "Use triangle congruence to find the missing measure"

MODULE_INFO = {
    'module_id': 'geometry.congruent_triangles_numeric',
    'name': 'Congruent Triangles Numeric',
    'topic': 'geometry',
    'subtopic': 'core_geometry',
    'difficulty_levels': ['level_1', 'level_2', 'level_3', 'level_4', 'level_5'],
    'enabled': True,
}
LEVEL_SPEC_CAPS = {'level_1': 420, 'level_2': 520, 'level_3': 620, 'level_4': 700, 'level_5': 840}
FAMILY_CAPS = {
    'level_1': {'corresponding_sides': 420},
    'level_2': {'corresponding_angles': 520},
    'level_3': {'perimeter_from_parts': 620},
    'level_4': {'algebraic_side_values': 700},
    'level_5': {'mixed_correspondence': 840},
}
CAPACITY_HINTS = {k: {'value': v, 'quality': 'capped'} for k, v in LEVEL_SPEC_CAPS.items()}
CURRICULUM = {
    'level_1': ['corresponding sides in congruent triangles'],
    'level_2': ['corresponding angles in congruent triangles'],
    'level_3': ['perimeter reasoning with congruent triangles'],
    'level_4': ['solve simple algebra from congruent sides'],
    'level_5': ['mixed correspondence problems'],
}

def iter_level1_specs():
    emitted = 0
    limit = FAMILY_CAPS['level_1']['corresponding_sides']
    for s in range(2, 120):
        yield _spec('corresponding_sides', (s,), f"Triangle ABC is congruent to triangle DEF. If side AB = {s}, find the length of the corresponding side DE.", str(s))
        emitted += 1
        if emitted >= limit:
            return


def iter_level2_specs():
    emitted = 0
    limit = FAMILY_CAPS['level_2']['corresponding_angles']
    for ang in range(20, 161):
        yield _spec('corresponding_angles', (ang,), f"Triangle PQR is congruent to triangle XYZ. If angle P = {ang} degrees, find the measure of the corresponding angle X.", str(ang))
        emitted += 1
        if emitted >= limit:
            return


def iter_level3_specs():
    emitted = 0
    limit = FAMILY_CAPS['level_3']['perimeter_from_parts']
    for a in range(3, 31):
        for b in range(4, 32):
            for c in range(5, 33):
                p = a + b + c
                problem = f"Triangle ABC is congruent to triangle DEF. The side lengths of triangle ABC are {a}, {b}, and {c}. Find the perimeter of triangle DEF."
                yield _spec('perimeter_from_parts', (a, b, c), problem, str(p))
                emitted += 1
                if emitted >= limit:
                    return


def iter_level4_specs():
    emitted = 0
    limit = FAMILY_CAPS['level_4']['algebraic_side_values']
    for x in range(1, 41):
        for c in range(1, 21):
            left = 2 * x + c
            right = left
            problem = f"Two congruent triangles have corresponding sides with lengths 2x + {c} and {right}. Find x."
            yield _spec('algebraic_side_values', (x, c), problem, str(x))
            emitted += 1
            if emitted >= limit:
                return


def iter_level5_specs():
    emitted = 0
    limit = FAMILY_CAPS['level_5']['mixed_correspondence']
    for s in range(3, 41):
        for ang in range(30, 151, 5):
            problem = f"Triangles ABC and DEF are congruent. A side corresponding to AB measures {s}, and an angle corresponding to angle C measures {ang} degrees. Find the values of DE and angle F."
            yield _spec('mixed_correspondence', (s, ang), problem, f"{s}, {ang}")
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


