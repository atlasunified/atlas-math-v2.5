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


MODULE_INFO = {"module_id": "algebra.piecewise_function_evaluation", "name": "Piecewise Function Evaluation", "topic": "algebra", "subtopic": "core_algebra", "difficulty_levels": ["level_1", "level_2", "level_3", "level_4", "level_5"], "enabled": True}
LEVEL_SPEC_CAPS = {"level_1": 700, "level_2": 850, "level_3": 1000, "level_4": 1150, "level_5": 1300}
FAMILY_CAPS = {"level_1": {"two_piece_linear": 700}, "level_2": {"boundary_values": 850}, "level_3": {"three_piece_mixed": 1000}, "level_4": {"absolute_piece_style": 1150}, "level_5": {"nested_piece_conditions": 1300}}
CAPACITY_HINTS = {k: {"value": v, "quality": "capped"} for k, v in LEVEL_SPEC_CAPS.items()}
CURRICULUM = {
    "level_1": ["evaluate two-piece linear functions"],
    "level_2": ["evaluate correctly at piece boundaries"],
    "level_3": ["evaluate three-piece piecewise definitions"],
    "level_4": ["evaluate piecewise functions that resemble absolute value definitions"],
    "level_5": ["evaluate more detailed piecewise conditions"],
}


def _spec(family, values, problem, answer):
    canonical = ':'.join([family] + [str(v) for v in values])
    return {"family": family, "values": values, "problem": problem, "answer": answer, "canonical_key": canonical, "case_id": canonical, "family_id": family}


def _sample_from_spec(spec, difficulty, instruction_idx=0):
    answer = spec['answer']
    metadata = {"family": spec['family'], "level_number": _level_num(difficulty), "structured": True, "canonical_key": spec['canonical_key'], "case_id": spec['case_id'], "family_id": spec['family_id'], "template_id": spec['family'], "final_answer": answer, "values": list(spec.get('values', []))}
    instruction = INSTRUCTIONS[instruction_idx % len(INSTRUCTIONS)].format(instruction="Evaluate the piecewise function", problem=spec['problem'])
    return make_sample(module_id=MODULE_INFO['module_id'], topic=MODULE_INFO['topic'], subtopic=MODULE_INFO['subtopic'], difficulty=difficulty, instruction=instruction, input_text=spec['problem'], answer=answer, metadata=metadata)


def iter_level1_specs():
    emitted = 0
    for a in range(1, 11):
        for b in range(-10, 11):
            for x in range(-10, 11):
                val = x + a if x < 0 else x + b
                problem = f"For f(x) = {{x + {a}, if x < 0; x + {b}, if x ≥ 0}}, find f({x})."
                yield _spec('two_piece_linear', (a, b, x), problem, str(val))
                emitted += 1
                if emitted >= FAMILY_CAPS['level_1']['two_piece_linear']:
                    return


def iter_level2_specs():
    emitted = 0
    for a in range(1, 11):
        for b in range(1, 11):
            x = a
            val = 2 * x + b
            problem = f"For g(x) = {{x - {a}, if x < {a}; 2x + {b}, if x ≥ {a}}}, find g({x})."
            yield _spec('boundary_values', (a, b), problem, str(val))
            emitted += 1
            if emitted >= FAMILY_CAPS['level_2']['boundary_values']:
                return


def iter_level3_specs():
    emitted = 0
    for a in range(1, 8):
        for b in range(1, 8):
            for x in range(-2, 6):
                if x < 0:
                    val = x - a
                elif x <= b:
                    val = x * x
                else:
                    val = x + a
                problem = f"For h(x) = {{x - {a}, if x < 0; x^2, if 0 ≤ x ≤ {b}; x + {a}, if x > {b}}}, find h({x})."
                yield _spec('three_piece_mixed', (a, b, x), problem, str(val))
                emitted += 1
                if emitted >= FAMILY_CAPS['level_3']['three_piece_mixed']:
                    return


def iter_level4_specs():
    emitted = 0
    for a in range(1, 12):
        for x in range(-12, 13):
            val = -x + a if x < 0 else x + a
            problem = f"For p(x) = {{-x + {a}, if x < 0; x + {a}, if x ≥ 0}}, find p({x})."
            yield _spec('absolute_piece_style', (a, x), problem, str(val))
            emitted += 1
            if emitted >= FAMILY_CAPS['level_4']['absolute_piece_style']:
                return


def iter_level5_specs():
    emitted = 0
    for a in range(1, 8):
        for b in range(1, 8):
            for x in range(-4, 9):
                if x < -a:
                    val = x + b
                elif x <= a:
                    val = x * x - b
                else:
                    val = 2 * x + a
                problem = f"For q(x) = {{x + {b}, if x < -{a}; x^2 - {b}, if -{a} ≤ x ≤ {a}; 2x + {a}, if x > {a}}}, find q({x})."
                yield _spec('nested_piece_conditions', (a, b, x), problem, str(val))
                emitted += 1
                if emitted >= FAMILY_CAPS['level_5']['nested_piece_conditions']:
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


