from __future__ import annotations

import itertools
import random
from fractions import Fraction
from typing import Iterable

from atlas_math.modules.shared.common import make_sample

MODULE_INFO = {
    "module_id": "prealgebra.absolute_value_inequalities_basic",
    "name": "Absolute Value Inequalities Basic",
    "topic": "prealgebra",
    "subtopic": "core_prealgebra",
    "difficulty_levels": ["level_1", "level_2", "level_3", "level_4", "level_5"],
    "enabled": True,
}
INSTRUCTIONS = [
    "Solve the absolute value inequality: {problem}",
    "Write the solution set for: {problem}",
    "Split into cases and solve the inequality: {problem}",
    "Work carefully through the absolute value inequality: {problem}",
]
LEVEL_SPEC_CAPS = {"level_1": 1000, "level_2": 1400, "level_3": 1800, "level_4": 2200, "level_5": 2600}
FAMILY_CAPS = {"level_1": {"abs_x_lt_a": 1000}, "level_2": {"abs_x_gt_a": 700, "shifted_lt": 700}, "level_3": {"shifted_gt": 900, "no_solution_lt_negative": 900}, "level_4": {"all_reals_gt_negative": 1100, "scaled_abs": 1100}, "level_5": {"fraction_coeff": 1300, "decimal_coeff_exact": 1300}}
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

def _sample_from_spec(spec: dict, difficulty: str, instruction_idx: int = 0) -> dict:
    metadata = {"family": spec["family"], "level_number": _level_num(difficulty), "structured": True, "canonical_key": spec["canonical_key"], "case_id": spec["case_id"], "family_id": spec["family_id"], "template_id": spec["family"], "final_answer": spec['answer'], "values": list(spec.get("values", []))}
    instruction = INSTRUCTIONS[instruction_idx % len(INSTRUCTIONS)].format(problem=spec['problem'])
    return make_sample(module_id=MODULE_INFO['module_id'], topic=MODULE_INFO['topic'], subtopic=MODULE_INFO['subtopic'], difficulty=difficulty, instruction=instruction, input_text=spec['problem'], answer=spec['answer'], metadata=metadata)

def _spec(family, values, problem, answer):
    key = ':'.join([family] + [str(v) for v in values])
    return {"family": family, "values": values, "problem": problem, "answer": answer, "canonical_key": key, "case_id": key, "family_id": family}

def iter_level1_specs() -> Iterable[dict]:
    limit = FAMILY_CAPS['level_1']['abs_x_lt_a']; emitted = 0
    for a in range(1, 41):
        yield _spec('abs_x_lt_a', (a,), f'|x| < {a}', f'-{a} < x < {a}')
        emitted += 1
        if emitted >= limit: return

def iter_level2_specs() -> Iterable[dict]:
    budgets = FAMILY_CAPS['level_2']; emitted = 0
    for a in range(0, 41):
        yield _spec('abs_x_gt_a', (a,), f'|x| > {a}', f'x < -{a} or x > {a}')
        emitted += 1
        if emitted >= budgets['abs_x_gt_a']: break
    emitted = 0
    for b in range(-20, 21):
        for a in range(1, 21):
            left = -a - b; right = a - b
            yield _spec('shifted_lt', (b,a), f'|x + {b}| < {a}', f'{left} < x < {right}')
            emitted += 1
            if emitted >= budgets['shifted_lt']: return

def iter_level3_specs() -> Iterable[dict]:
    budgets = FAMILY_CAPS['level_3']; emitted = 0
    for b in range(-20, 21):
        for a in range(0, 21):
            left = -a - b; right = a - b
            yield _spec('shifted_gt', (b,a), f'|x + {b}| > {a}', f'x < {left} or x > {right}')
            emitted += 1
            if emitted >= budgets['shifted_gt']: break
        if emitted >= budgets['shifted_gt']: break
    emitted = 0
    for rhs in range(-20, 0):
        yield _spec('no_solution_lt_negative', (rhs,), f'|x - 4| < {rhs}', 'no solution')
        emitted += 1
        if emitted >= budgets['no_solution_lt_negative']: return

def iter_level4_specs() -> Iterable[dict]:
    budgets = FAMILY_CAPS['level_4']; emitted = 0
    for rhs in range(-20, 0):
        yield _spec('all_reals_gt_negative', (rhs,), f'|x + 2| > {rhs}', 'all real numbers')
        emitted += 1
        if emitted >= budgets['all_reals_gt_negative']: break
    emitted = 0
    for a in range(2, 13):
        for rhs in range(1, 21):
            bound = Fraction(rhs, a)
            yield _spec('scaled_abs', (a,rhs), f'|{a}x| <= {rhs}', f'-{bound} <= x <= {bound}')
            emitted += 1
            if emitted >= budgets['scaled_abs']: return

def iter_level5_specs() -> Iterable[dict]:
    budgets = FAMILY_CAPS['level_5']; emitted = 0
    for num in range(1, 10):
        for den in range(2, 10):
            for rhs in range(1, 16):
                bound = Fraction(rhs * den, num)
                yield _spec('fraction_coeff', (num,den,rhs), f'|({num}/{den})x| < {rhs}', f'-{bound} < x < {bound}')
                emitted += 1
                if emitted >= budgets['fraction_coeff']: break
            if emitted >= budgets['fraction_coeff']: break
        if emitted >= budgets['fraction_coeff']: break
    emitted = 0
    for tenths in [5,10,15,20,25,30]:
        if tenths == 10: continue
        coeff = Fraction(tenths, 10)
        for rhs in range(1, 16):
            bound = Fraction(rhs, 1) / coeff
            if bound.denominator != 1: continue
            yield _spec('decimal_coeff_exact', (tenths,rhs), f'|{tenths/10:.1f}x| >= {rhs}', f'x <= -{bound} or x >= {bound}')
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
def curriculum() -> dict: return {'level_1': ['solves |x| < a'], 'level_2': ['adds |x| > a and shifted open-interval forms'], 'level_3': ['adds shifted outside-interval forms and impossible less-than cases'], 'level_4': ['adds always-true greater-than cases and scaled absolute values'], 'level_5': ['adds fractional and exact decimal absolute value inequalities']}


