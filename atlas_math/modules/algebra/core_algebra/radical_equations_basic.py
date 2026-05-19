from __future__ import annotations

import itertools
import math
import random
from fractions import Fraction
from typing import Iterable

from atlas_math.modules.shared.common import make_sample

INSTRUCTIONS = ["{instruction}: {problem}", "Solve and report the result: {problem}", "Work the problem and give the final answer: {problem}", "Compute the requested result: {problem}"]
MAX_SPEC_PREFIX = 5000
MAX_GENERATE_MULTIPLIER = 8
MAX_ITER_SAMPLES = 4096


def _level_num(difficulty: str) -> int:
    try: value = int(str(difficulty).rsplit('_', 1)[-1])
    except Exception: value = 1
    return max(1, min(5, value))


def _stable_seed(*parts) -> str:
    return '|'.join(str(p) for p in parts)


def _take(iterable: Iterable[dict], n: int) -> Iterable[dict]:
    for idx, item in enumerate(iterable):
        if idx >= max(0, int(n)):
            break
        yield item


MODULE_INFO = {"module_id": "algebra.radical_equations_basic", "name": "Radical Equations Basic", "topic": "algebra", "subtopic": "core_algebra", "difficulty_levels": ["level_1", "level_2", "level_3", "level_4", "level_5"], "enabled": True}
LEVEL_SPEC_CAPS = {"level_1": 700, "level_2": 850, "level_3": 1000, "level_4": 1150, "level_5": 1300}
FAMILY_CAPS = {"level_1": {"single_root": 700}, "level_2": {"translated_root": 850}, "level_3": {"root_equals_linear": 1000}, "level_4": {"extraneous_check": 1150}, "level_5": {"two_radical_sides": 1300}}
CAPACITY_HINTS = {k: {"value": v, "quality": "capped"} for k, v in LEVEL_SPEC_CAPS.items()}
CURRICULUM = {
    "level_1": ["solve basic equations with one square root"],
    "level_2": ["solve translated radical equations"],
    "level_3": ["solve radical equations with linear expressions"],
    "level_4": ["check for extraneous solutions after squaring"],
    "level_5": ["solve equations with radicals on both sides in easy cases"],
}


def _spec(family, values, problem, answer):
    canonical = ':'.join([family] + [str(v) for v in values])
    return {"family": family, "values": values, "problem": problem, "answer": answer, "canonical_key": canonical, "case_id": canonical, "family_id": family}


def _sample_from_spec(spec, difficulty, instruction_idx=0):
    answer = spec['answer']
    metadata = {"family": spec['family'], "level_number": _level_num(difficulty), "structured": True, "canonical_key": spec['canonical_key'], "case_id": spec['case_id'], "family_id": spec['family_id'], "template_id": spec['family'], "final_answer": answer, "values": list(spec.get('values', []))}
    instruction = INSTRUCTIONS[instruction_idx % len(INSTRUCTIONS)].format(instruction="Solve the radical equation", problem=spec['problem'])
    return make_sample(module_id=MODULE_INFO['module_id'], topic=MODULE_INFO['topic'], subtopic=MODULE_INFO['subtopic'], difficulty=difficulty, instruction=instruction, input_text=spec['problem'], answer=answer, metadata=metadata)


def iter_level1_specs():
    emitted = 0
    for r in range(0, 31):
        for a in range(0, 16):
            n = (r + a) ** 2
            yield _spec('single_root', (r, a), f"Solve √x = {r + a}.", f"x = {n}")
            emitted += 1
            if emitted >= FAMILY_CAPS['level_1']['single_root']:
                return


def iter_level2_specs():
    emitted = 0
    for r in range(-9, 21):
        for a in range(1, 12):
            n = (r + a) ** 2
            yield _spec('translated_root', (r, a), f"Solve √(x + {a}) = {r + a}.", f"x = {n - a}")
            emitted += 1
            if emitted >= FAMILY_CAPS['level_2']['translated_root']:
                return


def iter_level3_specs():
    emitted = 0
    for r in range(-8, 17):
        for a in range(1, 10):
            rhs = r + a
            yield _spec('root_equals_linear', (r, a), f"Solve √(x + {a}) = {rhs}.", f"x = {rhs*rhs - a}")
            emitted += 1
            if emitted >= FAMILY_CAPS['level_3']['root_equals_linear']:
                return


def iter_level4_specs():
    emitted = 0
    for r in range(1, 15):
        for t in range(2, 20):
            a = t * t - t - r
            if a <= 0:
                continue
            x = r + t
            problem = f"Solve √(x + {a}) = x - {r}."
            yield _spec('extraneous_check', (r, a, x), problem, f"x = {x}")
            emitted += 1
            if emitted >= FAMILY_CAPS['level_4']['extraneous_check']:
                return


def iter_level5_specs():
    emitted = 0
    for r in range(0, 15):
        for a in range(1, 10):
            left = r + a
            problem = f"Solve √(x + {a}) = √{left*left}."
            yield _spec('two_radical_sides', (r, a), problem, f"x = {left*left - a}")
            emitted += 1
            if emitted >= FAMILY_CAPS['level_5']['two_radical_sides']:
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
    seen, ordered = set(), []
    for spec in pool:
        key = spec['canonical_key']
        if key in seen:
            continue
        seen.add(key)
        ordered.append(spec)
    return [_sample_from_spec(spec, difficulty, i) for i, spec in enumerate(ordered[offset::stride][:count])]


def iter_samples(difficulty='level_1', seed=None):
    max_items = min(LEVEL_SPEC_CAPS.get(difficulty, 1000), MAX_ITER_SAMPLES)
    pool = list(itertools.islice(_iter_specs(difficulty), 0, max_items))
    rng = random.Random(_stable_seed(MODULE_INFO['module_id'], difficulty, seed, 'iter'))
    rng.shuffle(pool)
    seen = set()
    for idx, spec in enumerate(pool):
        key = spec['canonical_key']
        if key in seen:
            continue
        seen.add(key)
        yield _sample_from_spec(spec, difficulty, idx)


