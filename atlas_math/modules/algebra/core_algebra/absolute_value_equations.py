from __future__ import annotations

import itertools
import random
from fractions import Fraction
from typing import Iterable

from atlas_math.modules.shared.common import make_sample

MODULE_INFO = {
    "module_id": "algebra.absolute_value_equations",
    "name": "Absolute Value Equations",
    "topic": "algebra",
    "subtopic": "core_algebra",
    "difficulty_levels": ["level_1", "level_2", "level_3", "level_4", "level_5"],
    "enabled": True,
}

INSTRUCTIONS = [
    "Solve the absolute value equation: {problem}",
    "Find all real solutions: {problem}",
    "Work through the absolute value cases: {problem}",
    "Solve for x: {problem}",
]

LEVEL_SPEC_CAPS = {"level_1": 900, "level_2": 1200, "level_3": 1500, "level_4": 1800, "level_5": 2200}
FAMILY_CAPS = {
    "level_1": {"x_minus_h_eq_k": 900},
    "level_2": {"a_x_minus_h_eq_k": 700, "x_plus_h_plus_d_eq_k": 500},
    "level_3": {"two_solution_integer": 900, "no_solution_basic": 600},
    "level_4": {"fraction_shift": 900, "signed_inner_linear": 900},
    "level_5": {"two_sided_linear": 1100, "fractional_rhs": 1100},
}
CAPACITY_HINTS = {level: {"value": cap, "quality": "capped"} for level, cap in LEVEL_SPEC_CAPS.items()}
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


def _fmt_solution_set(solutions: tuple[Fraction, ...]) -> str:
    if not solutions:
        return "no solution"
    ordered = sorted(solutions)
    return ", ".join(_fmt_number(v) for v in ordered)


def _spec(family: str, values: tuple, problem: str, solutions: tuple[Fraction, ...]):
    canonical = ":".join([family] + [str(v) for v in values])
    return {
        "family": family,
        "values": values,
        "problem": problem,
        "solutions": tuple(sorted(set(solutions))),
        "canonical_key": canonical,
        "case_id": canonical,
        "family_id": family,
    }


def _sample_from_spec(spec: dict, difficulty: str, instruction_idx: int = 0) -> dict:
    answer = _fmt_solution_set(spec["solutions"])
    metadata = {
        "family": spec["family"],
        "level_number": _level_num(difficulty),
        "structured": True,
        "canonical_key": spec["canonical_key"],
        "case_id": spec["case_id"],
        "family_id": spec["family_id"],
        "template_id": spec["family"],
        "final_answer": answer,
        "values": list(spec.get("values", [])),
    }
    instruction = INSTRUCTIONS[instruction_idx % len(INSTRUCTIONS)].format(problem=spec["problem"])
    return make_sample(
        module_id=MODULE_INFO["module_id"],
        topic=MODULE_INFO["topic"],
        subtopic=MODULE_INFO["subtopic"],
        difficulty=difficulty,
        instruction=instruction,
        input_text=spec["problem"],
        answer=answer,
        metadata=metadata,
    )


def iter_level1_specs() -> Iterable[dict]:
    limit = FAMILY_CAPS["level_1"]["x_minus_h_eq_k"]
    emitted = 0
    for h in range(-20, 21):
        for k in range(0, 16):
            problem = f"|x - ({h})| = {k}"
            solutions = (Fraction(h - k), Fraction(h + k)) if k > 0 else (Fraction(h),)
            yield _spec("x_minus_h_eq_k", (h, k), problem, solutions)
            emitted += 1
            if emitted >= limit:
                return


def iter_level2_specs() -> Iterable[dict]:
    budgets = FAMILY_CAPS["level_2"]
    emitted = 0
    for a in [2, 3, 4, 5, -2, -3, -4, -5]:
        for h in range(-12, 13):
            for k in range(0, 13):
                inner = f"{a}x - ({a * h})"
                if k == 0:
                    sols = (Fraction(h),)
                else:
                    sols = (Fraction(a * h - k, a), Fraction(a * h + k, a))
                yield _spec("a_x_minus_h_eq_k", (a, h, k), f"|{inner}| = {k}", sols)
                emitted += 1
                if emitted >= budgets["a_x_minus_h_eq_k"]:
                    break
            if emitted >= budgets["a_x_minus_h_eq_k"]:
                break
        if emitted >= budgets["a_x_minus_h_eq_k"]:
            break

    emitted = 0
    for h in range(-15, 16):
        for d in range(-8, 9):
            for total in range(max(0, d), 18):
                rhs = total - d
                problem = f"|x + {h}| + {d} = {total}"
                sols = (Fraction(-h - rhs), Fraction(-h + rhs)) if rhs > 0 else (Fraction(-h),)
                yield _spec("x_plus_h_plus_d_eq_k", (h, d, total), problem, sols)
                emitted += 1
                if emitted >= budgets["x_plus_h_plus_d_eq_k"]:
                    return


def iter_level3_specs() -> Iterable[dict]:
    budgets = FAMILY_CAPS["level_3"]
    emitted = 0
    for a in [2, 3, 4, 5, 6, -2, -3, -4]:
        for b in range(-18, 19, 2):
            for c in range(1, 15):
                if (-b - c) % a != 0 or (-b + c) % a != 0:
                    continue
                s1 = Fraction(-b - c, a)
                s2 = Fraction(-b + c, a)
                yield _spec("two_solution_integer", (a, b, c), f"|{a}x + {b}| = {c}", (s1, s2))
                emitted += 1
                if emitted >= budgets["two_solution_integer"]:
                    break
            if emitted >= budgets["two_solution_integer"]:
                break
        if emitted >= budgets["two_solution_integer"]:
            break

    emitted = 0
    for a in [1, 2, 3, 4, 5, -1, -2, -3, -4]:
        for b in range(-12, 13):
            for c in range(-10, 0):
                yield _spec("no_solution_basic", (a, b, c), f"|{a}x + {b}| = {c}", ())
                emitted += 1
                if emitted >= budgets["no_solution_basic"]:
                    return


def iter_level4_specs() -> Iterable[dict]:
    budgets = FAMILY_CAPS["level_4"]
    emitted = 0
    for p in range(1, 9):
        for q in range(2, 9):
            h = Fraction(p, q)
            for c in range(0, 13):
                problem = f"|x - {p}/{q}| = {c}"
                sols = (h - c, h + c) if c > 0 else (h,)
                yield _spec("fraction_shift", (p, q, c), problem, sols)
                emitted += 1
                if emitted >= budgets["fraction_shift"]:
                    break
            if emitted >= budgets["fraction_shift"]:
                break
        if emitted >= budgets["fraction_shift"]:
            break

    emitted = 0
    for a in [-6, -5, -4, -3, -2, 2, 3, 4, 5, 6]:
        for b in range(-15, 16):
            for c in range(0, 13):
                if (-b - c) % a != 0 or (-b + c) % a != 0:
                    continue
                problem = f"|{a}x + {b}| = {c}"
                sols = (Fraction(-b - c, a), Fraction(-b + c, a)) if c > 0 else (Fraction(-b, a),)
                yield _spec("signed_inner_linear", (a, b, c), problem, sols)
                emitted += 1
                if emitted >= budgets["signed_inner_linear"]:
                    return


def iter_level5_specs() -> Iterable[dict]:
    budgets = FAMILY_CAPS["level_5"]
    emitted = 0
    for a in [2, 3, 4, 5, -2, -3, -4]:
        for b in range(-10, 11):
            for d in range(-8, 9):
                for c in range(0, 13):
                    left_const = a * d + b
                    if (-left_const - c) % a != 0 or (-left_const + c) % a != 0:
                        continue
                    problem = f"|{a}(x + {d}) + {b}| = {c}"
                    sols = (Fraction(-left_const - c, a), Fraction(-left_const + c, a)) if c > 0 else (Fraction(-left_const, a),)
                    yield _spec("two_sided_linear", (a, b, d, c), problem, sols)
                    emitted += 1
                    if emitted >= budgets["two_sided_linear"]:
                        break
                if emitted >= budgets["two_sided_linear"]:
                    break
            if emitted >= budgets["two_sided_linear"]:
                break
        if emitted >= budgets["two_sided_linear"]:
            break

    emitted = 0
    for a in [2, 3, 4, -2, -3, -4]:
        for b in range(-12, 13):
            for c_num in range(1, 10):
                for c_den in range(2, 8):
                    c = Fraction(c_num, c_den)
                    if (-b - c) / a != Fraction(-b * c.denominator - c.numerator, a * c.denominator):
                        pass
                    sols = (Fraction(-b - c, a), Fraction(-b + c, a))
                    problem = f"|{a}x + {b}| = {c_num}/{c_den}"
                    yield _spec("fractional_rhs", (a, b, c_num, c_den), problem, sols)
                    emitted += 1
                    if emitted >= budgets["fractional_rhs"]:
                        return


def _iter_specs(difficulty: str = "level_1") -> Iterable[dict]:
    level = _level_num(difficulty)
    if level == 1:
        return _take(iter_level1_specs(), LEVEL_SPEC_CAPS["level_1"])
    if level == 2:
        return _take(iter_level2_specs(), LEVEL_SPEC_CAPS["level_2"])
    if level == 3:
        return _take(iter_level3_specs(), LEVEL_SPEC_CAPS["level_3"])
    if level == 4:
        return _take(iter_level4_specs(), LEVEL_SPEC_CAPS["level_4"])
    return _take(iter_level5_specs(), LEVEL_SPEC_CAPS["level_5"])


def curriculum() -> dict:
    return {
        "level_1": ["solve |x-h|=k with integer centers and nonnegative right sides"],
        "level_2": ["adds coefficients and simple outer constants"],
        "level_3": ["adds no-solution cases and broader integer linear interiors"],
        "level_4": ["adds fractional shifts and signed coefficients"],
        "level_5": ["adds nested linear interiors and fractional right-hand sides"],
    }


def estimate_capacity(difficulty: str = "level_1"):
    return dict(CAPACITY_HINTS.get(difficulty, {"value": None, "quality": "unknown"}))


def generate(count: int = 10, difficulty: str = "level_1", seed=None) -> list[dict]:
    count = max(0, int(count))
    prefix = min(max(count * MAX_GENERATE_MULTIPLIER, 256), MAX_SPEC_PREFIX)
    pool = list(itertools.islice(_iter_specs(difficulty), 0, prefix))
    if not pool or count == 0:
        return []
    rng = random.Random(_stable_seed(MODULE_INFO["module_id"], difficulty, seed, "generate"))
    rng.shuffle(pool)
    return [_sample_from_spec(spec, difficulty, instruction_idx=i) for i, spec in enumerate(pool[:count])]


def generate_unique(count: int = 10, difficulty: str = "level_1", offset: int = 0, stride: int = 1, seed=None) -> list[dict]:
    count = max(0, int(count))
    offset = max(0, int(offset))
    stride = max(1, int(stride))
    pool = list(itertools.islice(_iter_specs(difficulty), 0, MAX_SPEC_PREFIX))
    rng = random.Random(_stable_seed(MODULE_INFO["module_id"], difficulty, seed, offset, stride, "unique"))
    rng.shuffle(pool)
    seen = set()
    ordered = []
    for spec in pool:
        key = spec["canonical_key"]
        if key in seen:
            continue
        seen.add(key)
        ordered.append(spec)
    selected = ordered[offset::stride][:count]
    return [_sample_from_spec(spec, difficulty, instruction_idx=i) for i, spec in enumerate(selected)]


def iter_samples(difficulty: str = "level_1", seed=None):
    max_items = min(LEVEL_SPEC_CAPS.get(difficulty, 1000), MAX_ITER_SAMPLES)
    pool = list(itertools.islice(_iter_specs(difficulty), 0, max_items))
    rng = random.Random(_stable_seed(MODULE_INFO["module_id"], difficulty, seed, "iter"))
    rng.shuffle(pool)
    seen = set()
    for idx, spec in enumerate(pool):
        key = spec["canonical_key"]
        if key in seen:
            continue
        seen.add(key)
        yield _sample_from_spec(spec, difficulty, instruction_idx=idx)


