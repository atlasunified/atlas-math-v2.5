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


MODULE_INFO = {"module_id": "algebra.rational_expressions_simplify", "name": "Rational Expressions Simplify", "topic": "algebra", "subtopic": "core_algebra", "difficulty_levels": ["level_1", "level_2", "level_3", "level_4", "level_5"], "enabled": True}
LEVEL_SPEC_CAPS = {"level_1": 800, "level_2": 900, "level_3": 1000, "level_4": 1100, "level_5": 1200}
FAMILY_CAPS = {"level_1": {"monomial_cancel": 800}, "level_2": {"factor_cancel": 900}, "level_3": {"signed_cancel": 1000}, "level_4": {"quadratic_cancel": 1100}, "level_5": {"mixed_multi_factor": 1200}}
CAPACITY_HINTS = {k: {"value": v, "quality": "capped"} for k, v in LEVEL_SPEC_CAPS.items()}
CURRICULUM = {
    "level_1": ["cancel common monomial factors"],
    "level_2": ["factor linear binomials before simplifying"],
    "level_3": ["simplify rational expressions with sign handling"],
    "level_4": ["simplify after factoring quadratic differences/products"],
    "level_5": ["simplify rational products with several factor groups"],
}


def _spec(family, values, problem, answer):
    canonical = ':'.join([family] + [str(v) for v in values])
    return {"family": family, "values": values, "problem": problem, "answer": answer, "canonical_key": canonical, "case_id": canonical, "family_id": family}


def _sample_from_spec(spec, difficulty, instruction_idx=0):
    answer = spec['answer']
    metadata = {"family": spec['family'], "level_number": _level_num(difficulty), "structured": True, "canonical_key": spec['canonical_key'], "case_id": spec['case_id'], "family_id": spec['family_id'], "template_id": spec['family'], "final_answer": answer, "values": list(spec.get('values', []))}
    instruction = INSTRUCTIONS[instruction_idx % len(INSTRUCTIONS)].format(instruction="Simplify the rational expression", problem=spec['problem'])
    return make_sample(module_id=MODULE_INFO['module_id'], topic=MODULE_INFO['topic'], subtopic=MODULE_INFO['subtopic'], difficulty=difficulty, instruction=instruction, input_text=spec['problem'], answer=answer, metadata=metadata)


def iter_level1_specs():
    emitted = 0
    for a in range(2, 16):
        for b in range(2, 16):
            for p in range(1, 6):
                num = a * b
                den = b
                answer = f"{a}x^{p}" if p != 1 else f"{a}x"
                problem = f"Simplify ({num}x^{p})/({den})."
                yield _spec('monomial_cancel', (a, b, p), problem, answer)
                emitted += 1
                if emitted >= FAMILY_CAPS['level_1']['monomial_cancel']:
                    return


def iter_level2_specs():
    emitted = 0
    for a in range(1, 13):
        for b in range(1, 13):
            for c in range(1, 13):
                if a == c:
                    continue
                problem = f"Simplify ((x + {a})({c}x + {b}))/({c}x + {b})."
                answer = f"x + {a}"
                yield _spec('factor_cancel', (a, b, c), problem, answer)
                emitted += 1
                if emitted >= FAMILY_CAPS['level_2']['factor_cancel']:
                    return


def iter_level3_specs():
    emitted = 0
    for a in range(2, 15):
        for b in range(1, 11):
            for c in range(1, 11):
                problem = f"Simplify (-{a}(x - {b})) / ({a}(x - {b}))."
                yield _spec('signed_cancel', (a, b, c), problem, '-1')
                emitted += 1
                if emitted >= FAMILY_CAPS['level_3']['signed_cancel']:
                    return


def iter_level4_specs():
    emitted = 0
    for a in range(1, 16):
        for b in range(1, 16):
            problem = f"Simplify (x^2 - {a*a})/(x - {a})."
            answer = f"x + {a}"
            yield _spec('quadratic_cancel', (a, b), problem, answer)
            emitted += 1
            if emitted >= FAMILY_CAPS['level_4']['quadratic_cancel']:
                return


def iter_level5_specs():
    emitted = 0
    for a in range(1, 10):
        for b in range(1, 10):
            for c in range(1, 10):
                problem = f"Simplify ((x + {a})({b}x + {c})) / (({b}x + {c}))."
                answer = f"x + {a}"
                yield _spec('mixed_multi_factor', (a, b, c), problem, answer)
                emitted += 1
                if emitted >= FAMILY_CAPS['level_5']['mixed_multi_factor']:
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


