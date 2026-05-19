from __future__ import annotations

import itertools
import random
from fractions import Fraction
from typing import Iterable

from atlas_math.modules.shared.common import make_sample

MODULE_INFO = {
    "module_id": "prealgebra.absolute_value_equations_basic",
    "name": "Absolute Value Equations Basic",
    "topic": "prealgebra",
    "subtopic": "core_prealgebra",
    "difficulty_levels": ["level_1", "level_2", "level_3", "level_4", "level_5"],
    "enabled": True,
}
INSTRUCTIONS = [
    "Solve the absolute value equation: {problem}",
    "Find all solutions: {problem}",
    "Split the absolute value into cases and solve: {problem}",
    "Work carefully through the absolute value equation: {problem}",
]
LEVEL_SPEC_CAPS = {"level_1": 1000, "level_2": 1400, "level_3": 1800, "level_4": 2200, "level_5": 2600}
FAMILY_CAPS = {"level_1": {"abs_x_equals_a": 1000}, "level_2": {"abs_x_plus_b": 700, "abs_x_minus_b": 700}, "level_3": {"abs_ax_equals_b": 900, "no_solution_negative_rhs": 900}, "level_4": {"abs_ax_plus_b": 1100, "single_solution_zero": 1100}, "level_5": {"fraction_coeff": 1300, "decimal_coeff_exact": 1300}}
CAPACITY_HINTS = {level: {"value": cap, "quality": "capped"} for level, cap in LEVEL_SPEC_CAPS.items()}
MAX_SPEC_PREFIX = 5000
MAX_GENERATE_MULTIPLIER = 8
MAX_ITER_SAMPLES = 4096

def _level_num(difficulty: str) -> int:
    try: return max(1, min(5, int(str(difficulty).rsplit('_',1)[-1])))
    except Exception: return 1

def _difficulty_name(level: int) -> str: return f"level_{max(1, min(5, int(level)))}"
def _stable_seed(*parts) -> str: return '|'.join(str(part) for part in parts)

def _take(iterable: Iterable[dict], n: int) -> Iterable[dict]:
    for idx, item in enumerate(iterable):
        if idx >= max(0, int(n)): break
        yield item

def _fmt_number(value) -> str:
    if isinstance(value, Fraction):
        return str(value.numerator) if value.denominator == 1 else f"{value.numerator}/{value.denominator}"
    return str(value)

def _answer_text(solutions):
    if not solutions: return 'no solution'
    vals = sorted(set(solutions))
    return ', '.join(f"x = {_fmt_number(v)}" for v in vals)

def _sample_from_spec(spec: dict, difficulty: str, instruction_idx: int = 0) -> dict:
    answer = _answer_text(spec['solutions'])
    metadata = {"family": spec["family"], "level_number": _level_num(difficulty), "structured": True, "canonical_key": spec["canonical_key"], "case_id": spec["case_id"], "family_id": spec["family_id"], "template_id": spec["family"], "final_answer": answer, "values": list(spec.get("values", []))}
    instruction = INSTRUCTIONS[instruction_idx % len(INSTRUCTIONS)].format(problem=spec['problem'])
    return make_sample(module_id=MODULE_INFO['module_id'], topic=MODULE_INFO['topic'], subtopic=MODULE_INFO['subtopic'], difficulty=difficulty, instruction=instruction, input_text=spec['problem'], answer=answer, metadata=metadata)

def _spec(family, values, problem, solutions):
    key = ':'.join([family] + [str(v) for v in values])
    return {"family": family, "values": values, "problem": problem, "solutions": tuple(solutions), "canonical_key": key, "case_id": key, "family_id": family}

def iter_level1_specs() -> Iterable[dict]:
    limit = FAMILY_CAPS['level_1']['abs_x_equals_a']
    emitted = 0
    for a in range(0, 41):
        sols = [Fraction(0)] if a == 0 else [Fraction(-a), Fraction(a)]
        yield _spec('abs_x_equals_a', (a,), f'|x| = {a}', sols)
        emitted += 1
        if emitted >= limit: return

def iter_level2_specs() -> Iterable[dict]:
    budgets = FAMILY_CAPS['level_2']
    emitted = 0
    for b in range(-20, 21):
        for a in range(0, 21):
            sols = [Fraction(-a - b), Fraction(a - b)] if a != 0 else [Fraction(-b)]
            yield _spec('abs_x_plus_b', (b,a), f'|x + {b}| = {a}', sols)
            emitted += 1
            if emitted >= budgets['abs_x_plus_b']: break
        if emitted >= budgets['abs_x_plus_b']: break
    emitted = 0
    for b in range(-20, 21):
        for a in range(0, 21):
            sols = [Fraction(b - a), Fraction(b + a)] if a != 0 else [Fraction(b)]
            yield _spec('abs_x_minus_b', (b,a), f'|x - {b}| = {a}', sols)
            emitted += 1
            if emitted >= budgets['abs_x_minus_b']: return

def iter_level3_specs() -> Iterable[dict]:
    budgets = FAMILY_CAPS['level_3']
    emitted = 0
    for a in range(2, 13):
        for b in range(0, 31):
            sols = [Fraction(-b, a), Fraction(b, a)] if b != 0 else [Fraction(0)]
            yield _spec('abs_ax_equals_b', (a,b), f'|{a}x| = {b}', sols)
            emitted += 1
            if emitted >= budgets['abs_ax_equals_b']: break
        if emitted >= budgets['abs_ax_equals_b']: break
    emitted = 0
    for rhs in range(-30, 0):
        yield _spec('no_solution_negative_rhs', (rhs,), f'|x + 3| = {rhs}', [])
        emitted += 1
        if emitted >= budgets['no_solution_negative_rhs']: return

def iter_level4_specs() -> Iterable[dict]:
    budgets = FAMILY_CAPS['level_4']
    emitted = 0
    for a in range(2, 13):
        for b in range(-20, 21):
            for rhs in range(0, 25):
                sols = [Fraction(-rhs - b, a), Fraction(rhs - b, a)] if rhs != 0 else [Fraction(-b, a)]
                yield _spec('abs_ax_plus_b', (a,b,rhs), f'|{a}x + {b}| = {rhs}', sols)
                emitted += 1
                if emitted >= budgets['abs_ax_plus_b']: break
            if emitted >= budgets['abs_ax_plus_b']: break
        if emitted >= budgets['abs_ax_plus_b']: break
    emitted = 0
    for a in range(-20, 21):
        yield _spec('single_solution_zero', (a,), f'|x - {a}| = 0', [Fraction(a)])
        emitted += 1
        if emitted >= budgets['single_solution_zero']: return

def iter_level5_specs() -> Iterable[dict]:
    budgets = FAMILY_CAPS['level_5']
    emitted = 0
    for num in range(1, 10):
        for den in range(2, 10):
            for rhs in range(0, 16):
                coeff = Fraction(num, den)
                sols = [Fraction(-rhs, 1) / coeff, Fraction(rhs, 1) / coeff] if rhs != 0 else [Fraction(0)]
                yield _spec('fraction_coeff', (num,den,rhs), f'|({num}/{den})x| = {rhs}', sols)
                emitted += 1
                if emitted >= budgets['fraction_coeff']: break
            if emitted >= budgets['fraction_coeff']: break
        if emitted >= budgets['fraction_coeff']: break
    emitted = 0
    for tenths in [5,10,15,20,25,30]:
        if tenths == 10: continue
        coeff = Fraction(tenths, 10)
        for rhs in range(0, 16):
            sols = [Fraction(-rhs, 1) / coeff, Fraction(rhs, 1) / coeff] if rhs != 0 else [Fraction(0)]
            if any(v.denominator != 1 for v in sols):
                continue
            yield _spec('decimal_coeff_exact', (tenths,rhs), f'|{tenths/10:.1f}x| = {rhs}', sols)
            emitted += 1
            if emitted >= budgets['decimal_coeff_exact']: return

def _iter_specs(difficulty: str) -> Iterable[dict]:
    level = _level_num(difficulty); cap = LEVEL_SPEC_CAPS[_difficulty_name(level)]
    if level == 1: return _take(iter_level1_specs(), cap)
    if level == 2: return _take(itertools.chain(iter_level1_specs(), iter_level2_specs()), cap)
    if level == 3: return _take(itertools.chain(iter_level1_specs(), iter_level2_specs(), iter_level3_specs()), cap)
    if level == 4: return _take(itertools.chain(iter_level1_specs(), iter_level2_specs(), iter_level3_specs(), iter_level4_specs()), cap)
    return _take(itertools.chain(iter_level1_specs(), iter_level2_specs(), iter_level3_specs(), iter_level4_specs(), iter_level5_specs()), cap)

def generate(count: int = 10, difficulty: str = 'level_1', seed=None):
    pool_size = min(MAX_SPEC_PREFIX, max(int(count) * MAX_GENERATE_MULTIPLIER, int(count), 64)); pool = list(itertools.islice(_iter_specs(difficulty), 0, pool_size)); rng = random.Random(_stable_seed(seed, difficulty, 'generate')); rng.shuffle(pool); out=[]; seen=set()
    for idx, spec in enumerate(pool):
        sample = _sample_from_spec(spec, difficulty, instruction_idx=idx); key = sample.get('input', '')
        if key in seen: continue
        seen.add(key); out.append(sample)
        if len(out) >= count: break
    return out

def generate_unique(count: int = 10, difficulty: str = 'level_1', offset: int = 0, stride: int = 1, seed=None):
    level = _difficulty_name(_level_num(difficulty)); pool = list(itertools.islice(_iter_specs(difficulty), 0, min(LEVEL_SPEC_CAPS[level], MAX_ITER_SAMPLES))); rng = random.Random(_stable_seed(seed, difficulty, offset, stride, 'generate_unique')); rng.shuffle(pool); out=[]; seen=set()
    for idx in range(max(0, int(offset)), len(pool), max(1, int(stride))):
        sample = _sample_from_spec(pool[idx], difficulty, instruction_idx=idx); key = sample.get('input', '')
        if key in seen: continue
        seen.add(key); out.append(sample)
        if len(out) >= count: break
    return out

def iter_samples(difficulty: str = 'level_1', seed=None):
    level = _difficulty_name(_level_num(difficulty)); pool = list(itertools.islice(_iter_specs(difficulty), 0, min(LEVEL_SPEC_CAPS[level], MAX_ITER_SAMPLES))); rng = random.Random(_stable_seed(seed, difficulty, 'iter_samples')); rng.shuffle(pool); seen=set()
    for idx, spec in enumerate(pool):
        sample = _sample_from_spec(spec, difficulty, instruction_idx=idx); key = sample.get('input', '')
        if key in seen: continue
        seen.add(key); yield sample

def estimate_capacity(difficulty: str = 'level_1'): return CAPACITY_HINTS.get(_difficulty_name(_level_num(difficulty)), {'value': None, 'quality': 'unknown'})
def curriculum() -> dict: return {'level_1': ['solves |x| = a'], 'level_2': ['adds horizontal shifts inside the absolute value'], 'level_3': ['adds coefficients and no-solution cases'], 'level_4': ['adds general linear expressions inside the absolute value'], 'level_5': ['adds fractional and exact decimal coefficients']}


