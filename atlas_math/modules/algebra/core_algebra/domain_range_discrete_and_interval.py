from __future__ import annotations

import itertools
import random
from fractions import Fraction
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


def _fmt_number(value) -> str:
    if isinstance(value, Fraction):
        if value.denominator == 1:
            return str(value.numerator)
        return f"{value.numerator}/{value.denominator}"
    return str(value)


def _fmt_interval(a: int, b: int, left_closed: bool = True, right_closed: bool = True) -> str:
    left = "[" if left_closed else "("
    right = "]" if right_closed else ")"
    return f"{left}{a}, {b}{right}"


MODULE_INFO = {
    "module_id": "algebra.domain_range_discrete_and_interval",
    "name": "Domain and Range: Discrete and Interval",
    "topic": "algebra",
    "subtopic": "core_algebra",
    "difficulty_levels": ["level_1", "level_2", "level_3", "level_4", "level_5"],
    "enabled": True,
}
LEVEL_SPEC_CAPS = {"level_1": 700, "level_2": 850, "level_3": 1000, "level_4": 1200, "level_5": 1400}
FAMILY_CAPS = {
    "level_1": {"domain_discrete": 350, "range_discrete": 350},
    "level_2": {"domain_interval": 425, "range_interval": 425},
    "level_3": {"domain_quadratic_interval": 1000},
    "level_4": {"range_linear_interval": 600, "range_abs_interval": 600},
    "level_5": {"domain_range_piecewise_style": 1400},
}
CAPACITY_HINTS = {k: {"value": v, "quality": "capped"} for k, v in LEVEL_SPEC_CAPS.items()}


def _spec(family, values, problem, answer):
    canonical = ':'.join([family] + [str(v) for v in values])
    return {"family": family, "values": values, "problem": problem, "answer": answer, "canonical_key": canonical, "case_id": canonical, "family_id": family}


def _sample_from_spec(spec, difficulty, instruction_idx=0):
    answer = spec['answer']
    metadata = {
        "family": spec['family'],
        "level_number": _level_num(difficulty),
        "structured": True,
        "canonical_key": spec['canonical_key'],
        "case_id": spec['case_id'],
        "family_id": spec['family_id'],
        "template_id": spec['family'],
        "final_answer": answer,
        "values": list(spec.get('values', [])),
    }
    instruction = INSTRUCTIONS[instruction_idx % len(INSTRUCTIONS)].format(
        instruction="Find the requested domain or range", problem=spec['problem']
    )
    return make_sample(module_id=MODULE_INFO['module_id'], topic=MODULE_INFO['topic'], subtopic=MODULE_INFO['subtopic'], difficulty=difficulty, instruction=instruction, input_text=spec['problem'], answer=answer, metadata=metadata)


def iter_level1_specs():
    emit_d = 0
    for start in range(-10, 8):
        for step in range(1, 5):
            for n in range(3, 7):
                xs = tuple(start + step * i for i in range(n))
                ys = tuple(2 * x + 1 for x in xs)
                yield _spec('domain_discrete', (start, step, n), f"Consider the relation with points {list(zip(xs, ys))}. What is the domain?", '{' + ', '.join(str(x) for x in xs) + '}')
                emit_d += 1
                if emit_d >= FAMILY_CAPS['level_1']['domain_discrete']:
                    break
            if emit_d >= FAMILY_CAPS['level_1']['domain_discrete']:
                break
        if emit_d >= FAMILY_CAPS['level_1']['domain_discrete']:
            break
    emit_r = 0
    for start in range(-8, 9):
        for step in range(1, 4):
            for n in range(3, 7):
                xs = tuple(start + i for i in range(n))
                ys = tuple(step * x - 2 for x in xs)
                yield _spec('range_discrete', (start, step, n), f"Consider the relation with points {list(zip(xs, ys))}. What is the range?", '{' + ', '.join(str(y) for y in ys) + '}')
                emit_r += 1
                if emit_r >= FAMILY_CAPS['level_1']['range_discrete']:
                    return


def iter_level2_specs():
    emit_d = 0
    for a in range(-12, 8):
        for length in range(3, 11):
            b = a + length
            yield _spec('domain_interval', (a, b), f"For f(x) = 3x - 4 with x restricted to {_fmt_interval(a, b)}, what is the domain?", _fmt_interval(a, b))
            emit_d += 1
            if emit_d >= FAMILY_CAPS['level_2']['domain_interval']:
                break
        if emit_d >= FAMILY_CAPS['level_2']['domain_interval']:
            break
    emit_r = 0
    for a in range(-10, 7):
        for length in range(2, 11):
            b = a + length
            lo = 2 * a + 1
            hi = 2 * b + 1
            yield _spec('range_interval', (a, b), f"For f(x) = 2x + 1 with domain {_fmt_interval(a, b)}, what is the range?", _fmt_interval(lo, hi))
            emit_r += 1
            if emit_r >= FAMILY_CAPS['level_2']['range_interval']:
                return


def iter_level3_specs():
    emitted = 0
    limit = FAMILY_CAPS['level_3']['domain_quadratic_interval']
    for h in range(-6, 5):
        for k in range(-4, 5):
            for radius in range(2, 8):
                a = h - radius
                b = h + radius
                rng = _fmt_interval(k, k + radius * radius)
                yield _spec('domain_quadratic_interval', (h, k, a, b), f"For f(x) = (x - {h})^2 + {k}, restricted so that the range is {rng}, what is the domain?", _fmt_interval(a, b))
                emitted += 1
                if emitted >= limit:
                    return


def iter_level4_specs():
    emit_lin = 0
    for m in [1, 2, 3, 4]:
        for b in range(-6, 7):
            for left in range(-8, 5):
                right = left + random.Random(f'{m}|{b}|{left}').randint(2, 7)
                ans = _fmt_interval(m * left + b, m * right + b)
                yield _spec('range_linear_interval', (m, b, left, right), f"Find the range of f(x) = {m}x + {b} on {_fmt_interval(left, right)}.", ans)
                emit_lin += 1
                if emit_lin >= FAMILY_CAPS['level_4']['range_linear_interval']:
                    break
            if emit_lin >= FAMILY_CAPS['level_4']['range_linear_interval']:
                break
        if emit_lin >= FAMILY_CAPS['level_4']['range_linear_interval']:
            break
    emit_abs = 0
    for h in range(-6, 7):
        for k in range(-5, 6):
            for radius in range(2, 8):
                a = h - radius
                b = h + radius
                ans = _fmt_interval(k, k + radius)
                yield _spec('range_abs_interval', (h, k, a, b), f"Find the range of f(x) = |x - {h}| + {k} on {_fmt_interval(a, b)}.", ans)
                emit_abs += 1
                if emit_abs >= FAMILY_CAPS['level_4']['range_abs_interval']:
                    return


def iter_level5_specs():
    emitted = 0
    limit = FAMILY_CAPS['level_5']['domain_range_piecewise_style']
    for cut in range(-4, 5):
        for left in range(-10, 0):
            for right in range(1, 11):
                if not (left <= cut <= right):
                    continue
                dom = _fmt_interval(left, right)
                low = min(2 * left + 3, -right + 5)
                high = max(2 * cut + 3, -cut + 5)
                ans = f"domain {dom}; range {_fmt_interval(low, high)}"
                problem = f"Let f(x) = 2x + 3 for x ≤ {cut} and f(x) = -x + 5 for x > {cut}, with x restricted to {dom}. Give both the domain and range."
                yield _spec('domain_range_piecewise_style', (cut, left, right), problem, ans)
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
    return {
        'level_1': ['find domain or range from finite sets of ordered pairs'],
        'level_2': ['work domain and range on basic closed intervals'],
        'level_3': ['reverse quadratic range restrictions into domains'],
        'level_4': ['find ranges on intervals for linear and absolute value functions'],
        'level_5': ['reason about domain and range together for simple piecewise rules'],
    }


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


