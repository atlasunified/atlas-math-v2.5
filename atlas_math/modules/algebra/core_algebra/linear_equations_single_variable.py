from __future__ import annotations

import itertools
import random
from fractions import Fraction
from typing import Iterable

from atlas_math.modules.shared.common import make_sample

MODULE_INFO = {
    "module_id": "algebra.linear_equations_single_variable",
    "name": "Linear Equations in One Variable",
    "topic": "algebra",
    "subtopic": "core_algebra",
    "difficulty_levels": ["level_1", "level_2", "level_3", "level_4", "level_5"],
    "enabled": True,
}

INSTRUCTIONS = [
    "Solve the equation: {problem}",
    "Find the value of x: {problem}",
    "Work through the algebra carefully: {problem}",
    "Solve for the variable: {problem}",
]

LEVEL_SPEC_CAPS = {"level_1": 1000, "level_2": 1400, "level_3": 1800, "level_4": 2200, "level_5": 2600}
FAMILY_CAPS = {
    "level_1": {"ax_plus_b_eq_c": 1000},
    "level_2": {"ax_plus_b_eq_dx": 700, "x_over_a_plus_b_eq_c": 700},
    "level_3": {"signed_coeff_eq": 900, "grouped_linear": 900},
    "level_4": {"fraction_coeff": 1100, "variables_both_sides_constants_both_sides": 1100},
    "level_5": {"decimal_and_fraction_mix": 1300, "nested_parentheses_linear": 1300},
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


def _difficulty_name(level: int) -> str:
    return f"level_{max(1, min(5, int(level)))}"


def _stable_seed(*parts) -> str:
    return "|".join(str(part) for part in parts)


def _take(iterable: Iterable[dict], n: int) -> Iterable[dict]:
    for idx, item in enumerate(iterable):
        if idx >= max(0, int(n)):
            break
        yield item


def _fmt_number(value) -> str:
    if isinstance(value, Fraction):
        return str(value.numerator) if value.denominator == 1 else f"{value.numerator}/{value.denominator}"
    if isinstance(value, float):
        return f"{value:.2f}".rstrip("0").rstrip(".")
    return str(value)


def _sample_from_spec(spec: dict, difficulty: str, instruction_idx: int = 0) -> dict:
    answer = _fmt_number(spec["answer"])
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


def _spec(family: str, values: tuple, problem: str, answer):
    canonical = ":".join([family] + [str(v) for v in values])
    return {"family": family, "values": values, "problem": problem, "answer": answer, "canonical_key": canonical, "case_id": canonical, "family_id": family}


def iter_level1_specs() -> Iterable[dict]:
    limit = FAMILY_CAPS["level_1"]["ax_plus_b_eq_c"]
    emitted = 0
    for a in range(2, 13):
        for b in range(-15, 16):
            for solution in range(-20, 21):
                c = a * solution + b
                yield _spec("ax_plus_b_eq_c", (a, b, c), f"{a}x + {b} = {c}", Fraction(solution))
                emitted += 1
                if emitted >= limit:
                    return


def iter_level2_specs() -> Iterable[dict]:
    budgets = FAMILY_CAPS["level_2"]
    emitted = 0
    for a in range(2, 13):
        for d in range(1, 11):
            if a == d:
                continue
            for b in range(-12, 13):
                for solution in range(-15, 16):
                    c = (a - d) * solution + b
                    yield _spec("ax_plus_b_eq_dx", (a, b, d, c), f"{a}x + {b} = {d}x + {c}", Fraction(solution))
                    emitted += 1
                    if emitted >= budgets["ax_plus_b_eq_dx"]:
                        break
                if emitted >= budgets["ax_plus_b_eq_dx"]:
                    break
            if emitted >= budgets["ax_plus_b_eq_dx"]:
                break
        if emitted >= budgets["ax_plus_b_eq_dx"]:
            break

    emitted = 0
    for a in range(2, 16):
        for b in range(-12, 13):
            for solution in range(-15, 16):
                c = Fraction(solution, a) + b
                if c.denominator != 1:
                    continue
                yield _spec("x_over_a_plus_b_eq_c", (a, b, int(c)), f"x/{a} + {b} = {int(c)}", Fraction(solution))
                emitted += 1
                if emitted >= budgets["x_over_a_plus_b_eq_c"]:
                    return


def iter_level3_specs() -> Iterable[dict]:
    budgets = FAMILY_CAPS["level_3"]
    emitted = 0
    for a in list(range(-12, -1)) + list(range(2, 13)):
        for b in range(-12, 13):
            for solution in range(-15, 16):
                c = a * solution + b
                yield _spec("signed_coeff_eq", (a, b, c), f"{a}x + {b} = {c}", Fraction(solution))
                emitted += 1
                if emitted >= budgets["signed_coeff_eq"]:
                    break
            if emitted >= budgets["signed_coeff_eq"]:
                break
        if emitted >= budgets["signed_coeff_eq"]:
            break

    emitted = 0
    for a in list(range(-9, -1)) + list(range(2, 10)):
        for h in range(-8, 9):
            for k in range(-12, 13):
                for solution in range(-12, 13):
                    rhs = a * (solution + h) + k
                    yield _spec("grouped_linear", (a, h, k, rhs), f"{a}(x + {h}) + {k} = {rhs}", Fraction(solution))
                    emitted += 1
                    if emitted >= budgets["grouped_linear"]:
                        return


def iter_level4_specs() -> Iterable[dict]:
    budgets = FAMILY_CAPS["level_4"]
    emitted = 0
    for num in range(1, 10):
        for den in range(2, 10):
            coeff = Fraction(num, den)
            if coeff == 1:
                continue
            for b in range(-10, 11):
                for solution in range(-12, 13):
                    rhs = coeff * solution + b
                    yield _spec("fraction_coeff", (num, den, b, rhs.numerator, rhs.denominator), f"({num}/{den})x + {b} = {rhs.numerator}/{rhs.denominator}", Fraction(solution))
                    emitted += 1
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
        for d in range(-10, 11):
            if a == d:
                continue
            for b in range(-12, 13):
                for e in range(-12, 13):
                    for solution in range(-12, 13):
                        c = (a - d) * solution + e - b
                        yield _spec("variables_both_sides_constants_both_sides", (a, b, d, c, e), f"{a}x + {b} = {d}x + {c} + {e}", Fraction(solution))
                        emitted += 1
                        if emitted >= budgets["variables_both_sides_constants_both_sides"]:
                            return


def iter_level5_specs() -> Iterable[dict]:
    budgets = FAMILY_CAPS["level_5"]
    emitted = 0
    for tenths in [5, 15, 20, 25, 30, 35]:
        coeff = Fraction(tenths, 10)
        for num in range(1, 8):
            for den in range(2, 8):
                const = Fraction(num, den)
                for solution in range(-10, 11):
                    rhs = coeff * solution + const
                    yield _spec("decimal_and_fraction_mix", (tenths, num, den, rhs.numerator, rhs.denominator), f"{tenths/10:.1f}x + {num}/{den} = {rhs.numerator}/{rhs.denominator}", Fraction(solution))
                    emitted += 1
                    if emitted >= budgets["decimal_and_fraction_mix"]:
                        break
                if emitted >= budgets["decimal_and_fraction_mix"]:
                    break
            if emitted >= budgets["decimal_and_fraction_mix"]:
                break
        if emitted >= budgets["decimal_and_fraction_mix"]:
            break

    emitted = 0
    for a in range(2, 8):
        for b in range(-6, 7):
            for c in range(-6, 7):
                for d in range(-8, 9):
                    for solution in range(-10, 11):
                        rhs = a * (2 * solution + b) + c * (solution + d)
                        yield _spec("nested_parentheses_linear", (a, b, c, d, rhs), f"{a}(2x + {b}) + {c}(x + {d}) = {rhs}", Fraction(solution))
                        emitted += 1
                        if emitted >= budgets["nested_parentheses_linear"]:
                            return


def _iter_specs_for_difficulty(difficulty: str) -> Iterable[dict]:
    level_num = _level_num(difficulty)
    fn = globals().get(f"iter_level{level_num}_specs") or globals().get(f"iter_level_{level_num}_specs")
    if fn is None:
        return ()
    return fn()


def curriculum() -> dict:
    return {
        level: {
            "difficulty": level,
            "spec_cap": LEVEL_SPEC_CAPS[level],
            "families": dict(FAMILY_CAPS[level]),
            "capacity_hint": dict(CAPACITY_HINTS[level]),
        }
        for level in LEVEL_SPEC_CAPS
    }


def estimate_capacity(difficulty: str | None = None):
    if difficulty is None:
        return {level: dict(CAPACITY_HINTS[level]) for level in LEVEL_SPEC_CAPS}
    return dict(CAPACITY_HINTS.get(difficulty, {"value": 0, "quality": "unknown"}))


def iter_samples(difficulty: str | None = None, limit: int | None = None):
    difficulties = [difficulty] if difficulty else list(MODULE_INFO["difficulty_levels"])
    remaining = MAX_ITER_SAMPLES if limit is None else max(0, min(int(limit), MAX_ITER_SAMPLES))
    for diff in difficulties:
        if remaining <= 0:
            break
        for idx, spec in enumerate(_iter_specs_for_difficulty(diff)):
            if remaining <= 0:
                break
            yield _sample_from_spec(spec, diff, instruction_idx=idx)
            remaining -= 1


def generate(difficulty: str = "level_1", count: int = 10, seed: int | None = None):
    count = max(0, min(int(count), MAX_SPEC_PREFIX))
    rng = random.Random(seed)
    specs = list(_take(_iter_specs_for_difficulty(difficulty), min(MAX_SPEC_PREFIX, max(count * MAX_GENERATE_MULTIPLIER, count))))
    if not specs:
        return []
    rng.shuffle(specs)
    return [_sample_from_spec(spec, difficulty, instruction_idx=i) for i, spec in enumerate(specs[:count])]


def generate_unique(difficulty: str = "level_1", count: int = 10, seed: int | None = None):
    count = max(0, min(int(count), MAX_SPEC_PREFIX))
    specs = list(_take(_iter_specs_for_difficulty(difficulty), MAX_SPEC_PREFIX))
    rng = random.Random(_stable_seed(MODULE_INFO["module_id"], difficulty, seed, count))
    rng.shuffle(specs)
    return [_sample_from_spec(spec, difficulty, instruction_idx=i) for i, spec in enumerate(specs[:count])]


