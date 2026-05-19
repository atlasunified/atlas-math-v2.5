from __future__ import annotations

import random
from fractions import Fraction
from typing import Iterable

from atlas_math.modules.shared.common import make_sample

MODULE_INFO = {
    "module_id": "algebra.linear_equations_multi_step",
    "name": "Linear Equations Multi-Step",
    "topic": "algebra",
    "subtopic": "core_algebra",
    "difficulty_levels": ["level_1", "level_2", "level_3", "level_4", "level_5"],
    "enabled": True,
}

INSTRUCTIONS = [
    "Solve the multi-step equation: {problem}",
    "Simplify both sides and solve: {problem}",
    "Work carefully through the linear equation: {problem}",
    "Use algebraic steps to solve for x: {problem}",
]

LEVEL_SPEC_CAPS = {"level_1": 1000, "level_2": 1400, "level_3": 1800, "level_4": 2200, "level_5": 2600}
FAMILY_CAPS = {
    "level_1": {"distribution_then_solve": 1000},
    "level_2": {"combine_both_sides": 700, "parentheses_both_sides": 700},
    "level_3": {"signed_distribution": 900, "fraction_rhs": 900},
    "level_4": {"fraction_coefficients": 1100, "nested_grouping": 1100},
    "level_5": {"decimal_fraction_mix": 1300, "multiple_groupings_both_sides": 1300},
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
    return "|".join(str(part) for part in parts)


def _take(iterable: Iterable[dict], n: int) -> Iterable[dict]:
    for idx, item in enumerate(iterable):
        if idx >= max(0, int(n)):
            break
        yield item


def _fmt_number(value) -> str:
    if isinstance(value, Fraction):
        return str(value.numerator) if value.denominator == 1 else f"{value.numerator}/{value.denominator}"
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
    return make_sample(module_id=MODULE_INFO["module_id"], topic=MODULE_INFO["topic"], subtopic=MODULE_INFO["subtopic"], difficulty=difficulty, instruction=instruction, input_text=spec["problem"], answer=answer, metadata=metadata)


def _spec(family: str, values: tuple, problem: str, answer):
    canonical = ":".join([family] + [str(v) for v in values])
    return {"family": family, "values": values, "problem": problem, "answer": answer, "canonical_key": canonical, "case_id": canonical, "family_id": family}


def iter_level1_specs() -> Iterable[dict]:
    limit = FAMILY_CAPS["level_1"]["distribution_then_solve"]
    emitted = 0
    for a in range(2, 13):
        for b in range(-8, 9):
            for c in range(-12, 13):
                for solution in range(-12, 13):
                    rhs = a * (solution + b) + c
                    yield _spec("distribution_then_solve", (a, b, c, rhs), f"{a}(x + {b}) + {c} = {rhs}", Fraction(solution))
                    emitted += 1
                    if emitted >= limit:
                        return


def iter_level2_specs() -> Iterable[dict]:
    budgets = FAMILY_CAPS["level_2"]
    emitted = 0
    for a in range(2, 10):
        for c in range(1, 10):
            if a == c:
                continue
            for b in range(-8, 9):
                for d in range(-10, 11):
                    for solution in range(-10, 11):
                        rhs = (a - c) * solution + a * b + d
                        yield _spec("combine_both_sides", (a, b, c, d, rhs), f"{a}(x + {b}) = {c}x + {rhs - d} - {d}", Fraction(solution))
                        emitted += 1
                        if emitted >= budgets["combine_both_sides"]:
                            break
                    if emitted >= budgets["combine_both_sides"]:
                        break
                if emitted >= budgets["combine_both_sides"]:
                    break
            if emitted >= budgets["combine_both_sides"]:
                break
        if emitted >= budgets["combine_both_sides"]:
            break

    emitted = 0
    for a in range(2, 10):
        for b in range(-6, 7):
            for c in range(2, 10):
                for d in range(-6, 7):
                    if a == c:
                        continue
                    for solution in range(-10, 11):
                        e = a * (solution + b) - c * (solution + d)
                        yield _spec("parentheses_both_sides", (a, b, c, d, e), f"{a}(x + {b}) = {c}(x + {d}) + {e}", Fraction(solution))
                        emitted += 1
                        if emitted >= budgets["parentheses_both_sides"]:
                            return


def iter_level3_specs() -> Iterable[dict]:
    budgets = FAMILY_CAPS["level_3"]
    emitted = 0
    for a in list(range(-9, -1)) + list(range(2, 10)):
        for b in range(-8, 9):
            for c in range(-10, 11):
                for solution in range(-10, 11):
                    rhs = a * (solution + b) + c
                    yield _spec("signed_distribution", (a, b, c, rhs), f"{a}(x + {b}) + {c} = {rhs}", Fraction(solution))
                    emitted += 1
                    if emitted >= budgets["signed_distribution"]:
                        break
                if emitted >= budgets["signed_distribution"]:
                    break
            if emitted >= budgets["signed_distribution"]:
                break
        if emitted >= budgets["signed_distribution"]:
            break

    emitted = 0
    for a in range(2, 10):
        for b in range(-6, 7):
            for c in range(-8, 9):
                for solution in range(-10, 11):
                    rhs = Fraction(a * (solution + b) + c, 2)
                    yield _spec("fraction_rhs", (a, b, c, rhs.numerator, rhs.denominator), f"{a}(x + {b}) + {c} = {rhs.numerator}/{rhs.denominator}", Fraction(solution))
                    emitted += 1
                    if emitted >= budgets["fraction_rhs"]:
                        return


def iter_level4_specs() -> Iterable[dict]:
    budgets = FAMILY_CAPS["level_4"]
    emitted = 0
    for n1 in range(1, 8):
        for d1 in range(2, 8):
            a = Fraction(n1, d1)
            if a == 1:
                continue
            for n2 in range(1, 8):
                for d2 in range(2, 8):
                    b = Fraction(n2, d2)
                    for c in range(-6, 7):
                        for solution in range(-8, 9):
                            rhs = a * solution + b + c
                            yield _spec("fraction_coefficients", (n1, d1, n2, d2, c, rhs.numerator, rhs.denominator), f"({n1}/{d1})x + {n2}/{d2} + {c} = {rhs.numerator}/{rhs.denominator}", Fraction(solution))
                            emitted += 1
                            if emitted >= budgets["fraction_coefficients"]:
                                break
                        if emitted >= budgets["fraction_coefficients"]:
                            break
                    if emitted >= budgets["fraction_coefficients"]:
                        break
                if emitted >= budgets["fraction_coefficients"]:
                    break
            if emitted >= budgets["fraction_coefficients"]:
                break
        if emitted >= budgets["fraction_coefficients"]:
            break

    emitted = 0
    for a in range(2, 7):
        for b in range(-5, 6):
            for c in range(2, 7):
                for d in range(-5, 6):
                    for e in range(-6, 7):
                        if 2 * a + c == 0:
                            continue
                        for solution in range(-8, 9):
                            rhs = a * (2 * solution + b) + c * (solution + d) + e
                            yield _spec("nested_grouping", (a, b, c, d, e, rhs), f"{a}(2x + {b}) + {c}(x + {d}) + {e} = {rhs}", Fraction(solution))
                            emitted += 1
                            if emitted >= budgets["nested_grouping"]:
                                return


def iter_level5_specs() -> Iterable[dict]:
    budgets = FAMILY_CAPS["level_5"]
    emitted = 0
    for tenths in [5, 15, 20, 25, 30]:
        a = Fraction(tenths, 10)
        for n in range(1, 7):
            for d in range(2, 7):
                b = Fraction(n, d)
                for c in range(-6, 7):
                    for solution in range(-8, 9):
                        rhs = a * (solution + c) - b
                        yield _spec("decimal_fraction_mix", (tenths, n, d, c, rhs.numerator, rhs.denominator), f"{tenths/10:.1f}(x + {c}) - {n}/{d} = {rhs.numerator}/{rhs.denominator}", Fraction(solution))
                        emitted += 1
                        if emitted >= budgets["decimal_fraction_mix"]:
                            break
                    if emitted >= budgets["decimal_fraction_mix"]:
                        break
                if emitted >= budgets["decimal_fraction_mix"]:
                    break
            if emitted >= budgets["decimal_fraction_mix"]:
                break
        if emitted >= budgets["decimal_fraction_mix"]:
            break

    emitted = 0
    for a in range(2, 6):
        for b in range(-4, 5):
            for c in range(2, 6):
                for d in range(-4, 5):
                    for e in range(2, 6):
                        for f in range(-4, 5):
                            if a + c == e:
                                continue
                            for solution in range(-6, 7):
                                g = a * (solution + b) + c * (solution + d) - e * (solution + f)
                                yield _spec("multiple_groupings_both_sides", (a, b, c, d, e, f, g), f"{a}(x + {b}) + {c}(x + {d}) = {e}(x + {f}) + {g}", Fraction(solution))
                                emitted += 1
                                if emitted >= budgets["multiple_groupings_both_sides"]:
                                    return


def _iter_specs_for_difficulty(difficulty: str) -> Iterable[dict]:
    level_num = _level_num(difficulty)
    fn = globals().get(f"iter_level{level_num}_specs") or globals().get(f"iter_level_{level_num}_specs")
    if fn is None:
        return ()
    return fn()


def curriculum() -> dict:
    return {level: {"difficulty": level, "spec_cap": LEVEL_SPEC_CAPS[level], "families": dict(FAMILY_CAPS[level]), "capacity_hint": dict(CAPACITY_HINTS[level])} for level in LEVEL_SPEC_CAPS}


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


