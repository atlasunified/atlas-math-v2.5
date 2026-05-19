from __future__ import annotations

import itertools
import random
from fractions import Fraction
from typing import Iterable

from atlas_math.modules.shared.common import make_sample

MODULE_INFO = {
    "module_id": "algebra.systems_of_linear_equations",
    "name": "Systems of Linear Equations",
    "topic": "algebra",
    "subtopic": "core_algebra",
    "difficulty_levels": ["level_1", "level_2", "level_3", "level_4", "level_5"],
    "enabled": True,
}

INSTRUCTIONS = [
    "Solve the system: {problem}",
    "Find the ordered pair that satisfies the system: {problem}",
    "Use elimination or substitution to solve: {problem}",
    "Solve for (x, y): {problem}",
]

LEVEL_SPEC_CAPS = {"level_1": 900, "level_2": 1200, "level_3": 1500, "level_4": 1800, "level_5": 2200}
FAMILY_CAPS = {
    "level_1": {"unique_integer_solution": 900},
    "level_2": {"scaled_equation": 700, "negative_coefficients": 500},
    "level_3": {"dependent_or_inconsistent": 750, "larger_integer_solution": 750},
    "level_4": {"fraction_solution": 900, "mixed_signs": 900},
    "level_5": {"nested_parentheses": 1100, "fraction_coefficients": 1100},
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


def _fmt_equation(a, b, c) -> str:
    return f"{_fmt_number(a)}x + {_fmt_number(b)}y = {_fmt_number(c)}"


def _fmt_solution(solution: tuple[Fraction, Fraction] | None, kind: str = "unique") -> str:
    if kind == "infinite":
        return "infinitely many solutions"
    if kind == "none":
        return "no solution"
    assert solution is not None
    x, y = solution
    return f"({_fmt_number(x)}, {_fmt_number(y)})"


def _spec(family: str, values: tuple, eq1: str, eq2: str, answer: str):
    canonical = ":".join([family] + [str(v) for v in values])
    return {
        "family": family,
        "values": values,
        "problem": f"{eq1}\n{eq2}",
        "answer": answer,
        "canonical_key": canonical,
        "case_id": canonical,
        "family_id": family,
    }


def _sample_from_spec(spec: dict, difficulty: str, instruction_idx: int = 0) -> dict:
    answer = spec["answer"]
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


def _unique_system(a1, b1, a2, b2, x, y, family, values):
    c1 = a1 * x + b1 * y
    c2 = a2 * x + b2 * y
    if a1 * b2 == a2 * b1:
        return None
    return _spec(family, values, _fmt_equation(a1, b1, c1), _fmt_equation(a2, b2, c2), _fmt_solution((Fraction(x), Fraction(y))))


def iter_level1_specs() -> Iterable[dict]:
    limit = FAMILY_CAPS["level_1"]["unique_integer_solution"]
    emitted = 0
    for x in range(-6, 7):
        for y in range(-6, 7):
            for a1, b1, a2, b2 in [(1, 1, 1, -1), (1, 2, 2, -1), (2, 1, 1, -2), (3, 1, 1, 1)]:
                spec = _unique_system(a1, b1, a2, b2, x, y, "unique_integer_solution", (a1, b1, a2, b2, x, y))
                if spec is None:
                    continue
                yield spec
                emitted += 1
                if emitted >= limit:
                    return


def iter_level2_specs() -> Iterable[dict]:
    budgets = FAMILY_CAPS["level_2"]
    emitted = 0
    for x in range(-8, 9):
        for y in range(-8, 9):
            for a1, b1, a2, b2 in [(2, 3, 1, -2), (3, 2, 2, -1), (4, 1, 1, -3), (2, 5, 3, -2)]:
                spec = _unique_system(a1, b1, a2, b2, x, y, "scaled_equation", (a1, b1, a2, b2, x, y))
                if spec is None:
                    continue
                yield spec
                emitted += 1
                if emitted >= budgets["scaled_equation"]:
                    break
            if emitted >= budgets["scaled_equation"]:
                break
        if emitted >= budgets["scaled_equation"]:
            break

    emitted = 0
    for x in range(-8, 9):
        for y in range(-8, 9):
            for a1, b1, a2, b2 in [(-1, 2, 3, 1), (2, -3, 1, 2), (-2, 1, 1, -1), (3, -2, -1, 4)]:
                spec = _unique_system(a1, b1, a2, b2, x, y, "negative_coefficients", (a1, b1, a2, b2, x, y))
                if spec is None:
                    continue
                yield spec
                emitted += 1
                if emitted >= budgets["negative_coefficients"]:
                    return


def iter_level3_specs() -> Iterable[dict]:
    budgets = FAMILY_CAPS["level_3"]
    emitted = 0
    for a, b, c in [(1, 2, 8), (2, -1, 3), (3, 1, -6), (-1, 2, 5)]:
        eq1 = _fmt_equation(a, b, c)
        eq2 = _fmt_equation(2 * a, 2 * b, 2 * c)
        yield _spec("dependent_or_inconsistent", (a, b, c, "dependent"), eq1, eq2, _fmt_solution(None, "infinite"))
        emitted += 1
        if emitted >= budgets["dependent_or_inconsistent"]:
            return
        eq3 = _fmt_equation(2 * a, 2 * b, 2 * c + 1)
        yield _spec("dependent_or_inconsistent", (a, b, c, "inconsistent"), eq1, eq3, _fmt_solution(None, "none"))
        emitted += 1
        if emitted >= budgets["dependent_or_inconsistent"]:
            return

    emitted = 0
    for x in range(-12, 13):
        for y in range(-12, 13):
            for a1, b1, a2, b2 in [(3, 4, 5, -2), (4, -3, 2, 5), (5, 2, 3, -4), (6, 1, -2, 3)]:
                spec = _unique_system(a1, b1, a2, b2, x, y, "larger_integer_solution", (a1, b1, a2, b2, x, y))
                if spec is None:
                    continue
                yield spec
                emitted += 1
                if emitted >= budgets["larger_integer_solution"]:
                    return


def iter_level4_specs() -> Iterable[dict]:
    budgets = FAMILY_CAPS["level_4"]
    emitted = 0
    for x in [Fraction(n, d) for n in range(-6, 7) for d in (2, 3)]:
        for y in [Fraction(n, d) for n in range(-6, 7) for d in (2, 3)]:
            for a1, b1, a2, b2 in [(2, 1, 1, -1), (3, 2, 2, -3), (4, -1, 1, 2)]:
                c1 = a1 * x + b1 * y
                c2 = a2 * x + b2 * y
                if a1 * b2 == a2 * b1:
                    continue
                yield _spec(
                    "fraction_solution",
                    (a1, b1, a2, b2, x, y),
                    _fmt_equation(a1, b1, c1),
                    _fmt_equation(a2, b2, c2),
                    _fmt_solution((x, y)),
                )
                emitted += 1
                if emitted >= budgets["fraction_solution"]:
                    break
            if emitted >= budgets["fraction_solution"]:
                break
        if emitted >= budgets["fraction_solution"]:
            break

    emitted = 0
    for x in range(-10, 11):
        for y in range(-10, 11):
            for a1, b1, a2, b2 in [(-3, 5, 2, -4), (4, -5, -2, 3), (-4, -1, 3, 2), (5, -2, -3, 4)]:
                spec = _unique_system(a1, b1, a2, b2, x, y, "mixed_signs", (a1, b1, a2, b2, x, y))
                if spec is None:
                    continue
                yield spec
                emitted += 1
                if emitted >= budgets["mixed_signs"]:
                    return


def iter_level5_specs() -> Iterable[dict]:
    budgets = FAMILY_CAPS["level_5"]
    emitted = 0
    for x in range(-8, 9):
        for y in range(-8, 9):
            for a1, b1, d1, a2, b2, d2 in [(2, 3, -1, 1, -2, 2), (3, -1, 2, 2, 1, -3), (-2, 4, 1, 3, -2, -1)]:
                c1 = a1 * (x + d1) + b1 * y
                c2 = a2 * x + b2 * (y + d2)
                if a1 * b2 == a2 * b1:
                    continue
                eq1 = f"{a1}(x + {d1}) + {b1}y = {_fmt_number(c1)}"
                eq2 = f"{a2}x + {b2}(y + {d2}) = {_fmt_number(c2)}"
                yield _spec("nested_parentheses", (a1, b1, d1, a2, b2, d2, x, y), eq1, eq2, _fmt_solution((Fraction(x), Fraction(y))))
                emitted += 1
                if emitted >= budgets["nested_parentheses"]:
                    break
            if emitted >= budgets["nested_parentheses"]:
                break
        if emitted >= budgets["nested_parentheses"]:
            break

    emitted = 0
    coeffs = [(Fraction(1, 2), 1, 2, Fraction(-3, 2)), (Fraction(3, 2), -1, 1, Fraction(1, 2)), (Fraction(1, 3), 2, Fraction(5, 2), -1)]
    vals = [Fraction(n, d) for n in range(-6, 7) for d in (2, 3)]
    for x in vals:
        for y in vals:
            for a1, b1, a2, b2 in coeffs:
                c1 = a1 * x + b1 * y
                c2 = a2 * x + b2 * y
                if a1 * b2 == a2 * b1:
                    continue
                yield _spec(
                    "fraction_coefficients",
                    (a1, b1, a2, b2, x, y),
                    _fmt_equation(a1, b1, c1),
                    _fmt_equation(a2, b2, c2),
                    _fmt_solution((x, y)),
                )
                emitted += 1
                if emitted >= budgets["fraction_coefficients"]:
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
        "level_1": ["solve 2x2 systems with small integer coefficients and unique integer solutions"],
        "level_2": ["adds scaled equations and negative coefficients"],
        "level_3": ["adds dependent and inconsistent systems plus larger integer solutions"],
        "level_4": ["adds rational solutions and more mixed signs"],
        "level_5": ["adds parentheses and fractional coefficients"],
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


