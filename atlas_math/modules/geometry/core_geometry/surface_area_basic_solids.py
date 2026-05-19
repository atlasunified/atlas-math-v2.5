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

TASK_INSTRUCTION = "Find the surface area"

MODULE_INFO = {
    'module_id': 'geometry.surface_area_basic_solids',
    'name': 'Surface Area Basic Solids',
    'topic': 'geometry',
    'subtopic': 'core_geometry',
    'difficulty_levels': ['level_1', 'level_2', 'level_3', 'level_4', 'level_5'],
    'enabled': True,
}
LEVEL_SPEC_CAPS = {'level_1': 420, 'level_2': 500, 'level_3': 560, 'level_4': 700, 'level_5': 840}
FAMILY_CAPS = {
    'level_1': {'cube_sa': 420},
    'level_2': {'rect_prism_sa': 500},
    'level_3': {'triangular_prism_text': 560},
    'level_4': {'cylinder_exact_pi': 700},
    'level_5': {'composite_textual': 840},
}
CAPACITY_HINTS = {k: {'value': v, 'quality': 'capped'} for k, v in LEVEL_SPEC_CAPS.items()}
CURRICULUM = {
    'level_1': ['surface area of cubes'],
    'level_2': ['surface area of rectangular prisms'],
    'level_3': ['surface area from textual net descriptions'],
    'level_4': ['surface area of cylinders in terms of pi'],
    'level_5': ['surface area of composite solids'],
}

def iter_level1_specs():
    emitted = 0
    limit = FAMILY_CAPS['level_1']['cube_sa']
    for s in range(1, 71):
        yield _spec('cube_sa', (s,), f"A cube has side length {s}. Find its surface area.", str(6 * s * s))
        emitted += 1
        if emitted >= limit:
            return


def iter_level2_specs():
    emitted = 0
    limit = FAMILY_CAPS['level_2']['rect_prism_sa']
    for l in range(2, 22):
        for w in range(2, 18):
            for h in range(2, 14):
                sa = 2 * (l * w + l * h + w * h)
                yield _spec('rect_prism_sa', (l, w, h), f"A rectangular prism has length {l}, width {w}, and height {h}. Find its surface area.", str(sa))
                emitted += 1
                if emitted >= limit:
                    return


def iter_level3_specs():
    emitted = 0
    limit = FAMILY_CAPS['level_3']['triangular_prism_text']
    triples = [(3, 4, 5), (5, 12, 13), (6, 8, 10)]
    for a, b, c in triples:
        for length in range(2, 26):
            base_area = a * b // 2
            sa = 2 * base_area + length * (a + b + c)
            problem = f"A triangular prism has right-triangle bases with side lengths {a}, {b}, and {c}, and prism length {length}. Find its surface area."
            yield _spec('triangular_prism_text', (a, b, c, length), problem, str(sa))
            emitted += 1
            if emitted >= limit:
                return


def iter_level4_specs():
    emitted = 0
    limit = FAMILY_CAPS['level_4']['cylinder_exact_pi']
    for r in range(1, 21):
        for h in range(1, 21):
            coeff = 2 * r * r + 2 * r * h
            answer = f"{coeff}pi"
            yield _spec('cylinder_exact_pi', (r, h), f"A cylinder has radius {r} and height {h}. Find its total surface area in terms of pi.", answer)
            emitted += 1
            if emitted >= limit:
                return


def iter_level5_specs():
    emitted = 0
    limit = FAMILY_CAPS['level_5']['composite_textual']
    for a in range(2, 14):
        for b in range(2, 14):
            for c in range(2, 10):
                for d in range(1, 8):
                    if d >= c:
                        continue
                    sa = 2*(a*b + a*c + b*c) + 2*(a*b + a*d + b*d) - 2*a*b
                    problem = f"A solid is made by stacking a {a} by {b} by {d} rectangular prism directly on top of a {a} by {b} by {c} rectangular prism. Find the exposed surface area."
                    yield _spec('composite_textual', (a, b, c, d), problem, str(sa))
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


