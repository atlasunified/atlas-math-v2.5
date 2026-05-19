from __future__ import annotations

import itertools
import random
from fractions import Fraction
from typing import Iterable

from atlas_math.modules.shared.common import make_sample

MODULE_INFO = {
    "module_id": "prealgebra.inequalities_two_step",
    "name": "Two-Step Inequalities",
    "topic": "prealgebra",
    "subtopic": "core_prealgebra",
    "difficulty_levels": ["level_1", "level_2", "level_3", "level_4", "level_5"],
    "enabled": True,
}
INSTRUCTIONS = [
    "Solve the two-step inequality: {problem}",
    "Isolate the variable and keep track of the inequality direction: {problem}",
    "Work through the inequality carefully: {problem}",
    "Find all values of the variable that satisfy: {problem}",
]
LEVEL_SPEC_CAPS = {"level_1": 1000, "level_2": 1400, "level_3": 1800, "level_4": 2200, "level_5": 2600}
FAMILY_CAPS = {
    "level_1": {"ax_plus_b": 1000},
    "level_2": {"ax_minus_b": 700, "positive_both_sides": 700},
    "level_3": {"negative_coeff_flip": 900, "division_then_shift": 900},
    "level_4": {"fraction_coeff": 1100, "negative_solution": 1100},
    "level_5": {"decimal_coeff": 1300, "signed_coeff_mix": 1300},
}
CAPACITY_HINTS = {level: {"value": cap, "quality": "capped"} for level, cap in LEVEL_SPEC_CAPS.items()}
MAX_SPEC_PREFIX = 5000
MAX_GENERATE_MULTIPLIER = 8
MAX_ITER_SAMPLES = 4096
OPS = ['<', '<=', '>', '>=']

def _level_num(difficulty: str) -> int:
    try:
        value = int(str(difficulty).rsplit("_", 1)[-1])
    except Exception:
        value = 1
    return max(1, min(5, value))

def _difficulty_name(level: int) -> str:
    return f"level_{max(1, min(5, int(level)))}"

def _stable_seed(*parts) -> str:
    return "|".join(str(part) for part in parts)

def _take(iterable: Iterable[dict], n: int) -> Iterable[dict]:
    for idx, item in enumerate(iterable):
        if idx >= max(0, int(n)):
            break
        yield item

def _flip(op: str) -> str:
    return {'<': '>', '<=': '>=', '>': '<', '>=': '<='}[op]

def _fmt_number(value) -> str:
    if isinstance(value, Fraction):
        return str(value.numerator) if value.denominator == 1 else f"{value.numerator}/{value.denominator}"
    return str(value)

def _sample_from_spec(spec: dict, difficulty: str, instruction_idx: int = 0) -> dict:
    answer = f"x {spec['solved_op']} {_fmt_number(spec['boundary'])}"
    metadata = {"family": spec["family"], "level_number": _level_num(difficulty), "structured": True, "canonical_key": spec["canonical_key"], "case_id": spec["case_id"], "family_id": spec["family_id"], "template_id": spec["family"], "final_answer": answer, "values": list(spec.get("values", []))}
    instruction = INSTRUCTIONS[instruction_idx % len(INSTRUCTIONS)].format(problem=spec["problem"])
    return make_sample(module_id=MODULE_INFO["module_id"], topic=MODULE_INFO["topic"], subtopic=MODULE_INFO["subtopic"], difficulty=difficulty, instruction=instruction, input_text=spec["problem"], answer=answer, metadata=metadata)

def _spec(family, values, problem, boundary, op, flipped=False):
    key = ":".join([family] + [str(v) for v in values] + [op])
    return {"family": family, "values": values, "problem": problem, "boundary": boundary, "solved_op": _flip(op) if flipped else op, "canonical_key": key, "case_id": key, "family_id": family}

def iter_level1_specs() -> Iterable[dict]:
    limit = FAMILY_CAPS["level_1"]["ax_plus_b"]
    emitted = 0
    for a in range(2, 13):
        for b in range(-15, 16):
            for bound in range(-15, 16):
                for op in OPS:
                    rhs = a * bound + b
                    yield _spec("ax_plus_b", (a,b,rhs), f"{a}x + {b} {op} {rhs}", Fraction(bound), op)
                    emitted += 1
                    if emitted >= limit:
                        return

def iter_level2_specs() -> Iterable[dict]:
    budgets = FAMILY_CAPS["level_2"]
    emitted = 0
    for a in range(2, 13):
        for b in range(1, 16):
            for bound in range(-15, 16):
                for op in OPS:
                    rhs = a * bound - b
                    yield _spec("ax_minus_b", (a,b,rhs), f"{a}x - {b} {op} {rhs}", Fraction(bound), op)
                    emitted += 1
                    if emitted >= budgets["ax_minus_b"]:
                        break
                if emitted >= budgets["ax_minus_b"]:
                    break
            if emitted >= budgets["ax_minus_b"]:
                break
        if emitted >= budgets["ax_minus_b"]:
            break

    emitted = 0
    for a in range(2, 13):
        for c in range(1, 11):
            if a == c:
                continue
            for d in range(-15, 16):
                for bound in range(-10, 11):
                    for op in OPS:
                        rhs = (a - c) * bound + d
                        yield _spec("positive_both_sides", (a,c,d,rhs), f"{a}x + {d} {op} {c}x + {rhs}", Fraction(bound), op)
                        emitted += 1
                        if emitted >= budgets["positive_both_sides"]:
                            return

def iter_level3_specs() -> Iterable[dict]:
    budgets = FAMILY_CAPS["level_3"]
    emitted = 0
    for a in range(-12, -1):
        for b in range(-15, 16):
            for bound in range(-12, 13):
                for op in OPS:
                    rhs = a * bound + b
                    yield _spec("negative_coeff_flip", (a,b,rhs), f"{a}x + {b} {op} {rhs}", Fraction(bound), op, flipped=True)
                    emitted += 1
                    if emitted >= budgets["negative_coeff_flip"]:
                        break
                if emitted >= budgets["negative_coeff_flip"]:
                    break
            if emitted >= budgets["negative_coeff_flip"]:
                break
        if emitted >= budgets["negative_coeff_flip"]:
            break

    emitted = 0
    for a in range(2, 13):
        for b in range(-12, 13):
            for bound in range(-12, 13):
                for op in OPS:
                    rhs = Fraction(bound + b, a)
                    if rhs.denominator != 1:
                        continue
                    yield _spec("division_then_shift", (a,b,int(rhs)), f"x/{a} - {b} {op} {int(rhs)}", Fraction(bound), op)
                    emitted += 1
                    if emitted >= budgets["division_then_shift"]:
                        return

def iter_level4_specs() -> Iterable[dict]:
    budgets = FAMILY_CAPS["level_4"]
    emitted = 0
    for num in range(1, 10):
        for den in range(2, 10):
            coeff = Fraction(num, den)
            for b in range(-10, 11):
                for bound in range(-10, 11):
                    for op in OPS:
                        rhs = coeff * bound + b
                        yield _spec("fraction_coeff", (num,den,b,rhs.numerator,rhs.denominator), f"({num}/{den})x + {b} {op} {rhs.numerator}/{rhs.denominator}", Fraction(bound), op)
                        emitted += 1
                        if emitted >= budgets["fraction_coeff"]:
                            break
                    if emitted >= budgets["fraction_coeff"]:
                        break
                if emitted >= budgets["fraction_coeff"]:
                    break
            if emitted >= budgets["fraction_coeff"]:
                break
        if emitted >= budgets["fraction_coeff"]:
            break

    emitted = 0
    for a in range(2, 13):
        for b in range(-15, 16):
            for bound in range(-20, 0):
                for op in OPS:
                    rhs = a * bound + b
                    yield _spec("negative_solution", (a,b,rhs), f"{a}x + {b} {op} {rhs}", Fraction(bound), op)
                    emitted += 1
                    if emitted >= budgets["negative_solution"]:
                        return

def iter_level5_specs() -> Iterable[dict]:
    budgets = FAMILY_CAPS["level_5"]
    emitted = 0
    for tenths in [5,10,15,20,25,30]:
        if tenths == 10:
            continue
        for b in range(-10, 11):
            for bound in range(-10, 11):
                for op in OPS:
                    rhs = Fraction(tenths,10) * bound + b
                    if rhs.denominator != 1:
                        continue
                    yield _spec("decimal_coeff", (tenths,b,int(rhs)), f"{tenths/10:.1f}x + {b} {op} {int(rhs)}", Fraction(bound), op)
                    emitted += 1
                    if emitted >= budgets["decimal_coeff"]:
                        break
                if emitted >= budgets["decimal_coeff"]:
                    break
            if emitted >= budgets["decimal_coeff"]:
                break
        if emitted >= budgets["decimal_coeff"]:
            break

    emitted = 0
    for a in list(range(-12,-1)) + list(range(2,13)):
        for b in range(-12, 13):
            for bound in range(-12, 13):
                for op in OPS:
                    rhs = a * bound + b
                    yield _spec("signed_coeff_mix", (a,b,rhs), f"{a}x + {b} {op} {rhs}", Fraction(bound), op, flipped=(a < 0))
                    emitted += 1
                    if emitted >= budgets["signed_coeff_mix"]:
                        return

def _iter_specs(difficulty: str) -> Iterable[dict]:
    level = _level_num(difficulty)
    cap = LEVEL_SPEC_CAPS[_difficulty_name(level)]
    if level == 1:
        return _take(iter_level1_specs(), cap)
    if level == 2:
        return _take(itertools.chain(iter_level1_specs(), iter_level2_specs()), cap)
    if level == 3:
        return _take(itertools.chain(iter_level1_specs(), iter_level2_specs(), iter_level3_specs()), cap)
    if level == 4:
        return _take(itertools.chain(iter_level1_specs(), iter_level2_specs(), iter_level3_specs(), iter_level4_specs()), cap)
    return _take(itertools.chain(iter_level1_specs(), iter_level2_specs(), iter_level3_specs(), iter_level4_specs(), iter_level5_specs()), cap)

def generate(count: int = 10, difficulty: str = "level_1", seed=None):
    pool_size = min(MAX_SPEC_PREFIX, max(int(count) * MAX_GENERATE_MULTIPLIER, int(count), 64))
    pool = list(itertools.islice(_iter_specs(difficulty), 0, pool_size))
    rng = random.Random(_stable_seed(seed, difficulty, "generate"))
    rng.shuffle(pool)
    out = []
    seen = set()
    for idx, spec in enumerate(pool):
        sample = _sample_from_spec(spec, difficulty, instruction_idx=idx)
        key = sample.get("input", "")
        if key in seen:
            continue
        seen.add(key)
        out.append(sample)
        if len(out) >= count:
            break
    return out

def generate_unique(count: int = 10, difficulty: str = "level_1", offset: int = 0, stride: int = 1, seed=None):
    level = _difficulty_name(_level_num(difficulty))
    pool = list(itertools.islice(_iter_specs(difficulty), 0, min(LEVEL_SPEC_CAPS[level], MAX_ITER_SAMPLES)))
    rng = random.Random(_stable_seed(seed, difficulty, offset, stride, "generate_unique"))
    rng.shuffle(pool)
    out = []
    seen = set()
    for idx in range(max(0, int(offset)), len(pool), max(1, int(stride))):
        sample = _sample_from_spec(pool[idx], difficulty, instruction_idx=idx)
        key = sample.get("input", "")
        if key in seen:
            continue
        seen.add(key)
        out.append(sample)
        if len(out) >= count:
            break
    return out

def iter_samples(difficulty: str = "level_1", seed=None):
    level = _difficulty_name(_level_num(difficulty))
    pool = list(itertools.islice(_iter_specs(difficulty), 0, min(LEVEL_SPEC_CAPS[level], MAX_ITER_SAMPLES)))
    rng = random.Random(_stable_seed(seed, difficulty, "iter_samples"))
    rng.shuffle(pool)
    seen = set()
    for idx, spec in enumerate(pool):
        sample = _sample_from_spec(spec, difficulty, instruction_idx=idx)
        key = sample.get("input", "")
        if key in seen:
            continue
        seen.add(key)
        yield sample

def estimate_capacity(difficulty: str = "level_1"):
    return CAPACITY_HINTS.get(_difficulty_name(_level_num(difficulty)), {"value": None, "quality": "unknown"})

def curriculum() -> dict:
    return {"level_1": ["solves ax + b inequalities"], "level_2": ["adds subtraction and both-side forms"], "level_3": ["adds negative coefficient sign flips and division-shift forms"], "level_4": ["adds fractional coefficients and negative solutions"], "level_5": ["adds exact decimal and signed coefficient variants"]}


