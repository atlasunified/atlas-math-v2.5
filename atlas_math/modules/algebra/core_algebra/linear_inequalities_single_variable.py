from __future__ import annotations

import random
from fractions import Fraction
from typing import Iterable

from atlas_math.modules.shared.common import make_sample

MODULE_INFO = {
    "module_id": "algebra.linear_inequalities_single_variable",
    "name": "Linear Inequalities in One Variable",
    "topic": "algebra",
    "subtopic": "core_algebra",
    "difficulty_levels": ["level_1", "level_2", "level_3", "level_4", "level_5"],
    "enabled": True,
}

INSTRUCTIONS = [
    "Solve the inequality: {problem}",
    "Find all x-values that satisfy: {problem}",
    "Work through the inequality carefully: {problem}",
    "Solve for x and watch the inequality direction: {problem}",
]

LEVEL_SPEC_CAPS = {"level_1": 1000, "level_2": 1400, "level_3": 1800, "level_4": 2200, "level_5": 2600}
FAMILY_CAPS = {
    "level_1": {"ax_plus_b": 1000},
    "level_2": {"variables_both_sides": 700, "grouped_positive": 700},
    "level_3": {"negative_coeff_flip": 900, "division_form": 900},
    "level_4": {"fraction_coeff": 1100, "decimal_coeff": 1100},
    "level_5": {"signed_both_sides": 1300, "nested_grouping_flip": 1300},
}
CAPACITY_HINTS = {level: {"value": cap, "quality": "capped"} for level, cap in LEVEL_SPEC_CAPS.items()}
MAX_SPEC_PREFIX = 5000
MAX_GENERATE_MULTIPLIER = 8
MAX_ITER_SAMPLES = 4096
OPS = ["<", "<=", ">", ">="]


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


def _flip(op: str) -> str:
    return {"<": ">", "<=": ">=", ">": "<", ">=": "<="}[op]


def _fmt_number(value) -> str:
    if isinstance(value, Fraction):
        return str(value.numerator) if value.denominator == 1 else f"{value.numerator}/{value.denominator}"
    return str(value)


def _spec(family, values, problem, boundary, op, flipped=False):
    key = ":".join([family] + [str(v) for v in values] + [op])
    return {"family": family, "values": values, "problem": problem, "boundary": boundary, "solved_op": _flip(op) if flipped else op, "canonical_key": key, "case_id": key, "family_id": family}


def _sample_from_spec(spec: dict, difficulty: str, instruction_idx: int = 0) -> dict:
    answer = f"x {spec['solved_op']} {_fmt_number(spec['boundary'])}"
    metadata = {"family": spec["family"], "level_number": _level_num(difficulty), "structured": True, "canonical_key": spec["canonical_key"], "case_id": spec["case_id"], "family_id": spec["family_id"], "template_id": spec["family"], "final_answer": answer, "values": list(spec.get("values", []))}
    instruction = INSTRUCTIONS[instruction_idx % len(INSTRUCTIONS)].format(problem=spec["problem"])
    return make_sample(module_id=MODULE_INFO["module_id"], topic=MODULE_INFO["topic"], subtopic=MODULE_INFO["subtopic"], difficulty=difficulty, instruction=instruction, input_text=spec["problem"], answer=answer, metadata=metadata)


def iter_level1_specs() -> Iterable[dict]:
    limit = FAMILY_CAPS["level_1"]["ax_plus_b"]
    emitted = 0
    for a in range(2, 13):
        for b in range(-12, 13):
            for bound in range(-15, 16):
                for op in OPS:
                    rhs = a * bound + b
                    yield _spec("ax_plus_b", (a, b, rhs), f"{a}x + {b} {op} {rhs}", Fraction(bound), op)
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
            for b in range(-10, 11):
                for e in range(-10, 11):
                    for bound in range(-10, 11):
                        for op in OPS:
                            c = (a - d) * bound + e - b
                            yield _spec("variables_both_sides", (a, b, d, c, e), f"{a}x + {b} {op} {d}x + {c} + {e}", Fraction(bound), op)
                            emitted += 1
                            if emitted >= budgets["variables_both_sides"]:
                                break
                        if emitted >= budgets["variables_both_sides"]:
                            break
                    if emitted >= budgets["variables_both_sides"]:
                        break
                if emitted >= budgets["variables_both_sides"]:
                    break
            if emitted >= budgets["variables_both_sides"]:
                break
        if emitted >= budgets["variables_both_sides"]:
            break

    emitted = 0
    for a in range(2, 10):
        for b in range(-8, 9):
            for c in range(-10, 11):
                for bound in range(-10, 11):
                    for op in OPS:
                        rhs = a * (bound + b) + c
                        yield _spec("grouped_positive", (a, b, c, rhs), f"{a}(x + {b}) + {c} {op} {rhs}", Fraction(bound), op)
                        emitted += 1
                        if emitted >= budgets["grouped_positive"]:
                            return


def iter_level3_specs() -> Iterable[dict]:
    budgets = FAMILY_CAPS["level_3"]
    emitted = 0
    for a in range(-12, -1):
        for b in range(-12, 13):
            for bound in range(-12, 13):
                for op in OPS:
                    rhs = a * bound + b
                    yield _spec("negative_coeff_flip", (a, b, rhs), f"{a}x + {b} {op} {rhs}", Fraction(bound), op, flipped=True)
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
    for a in range(2, 16):
        for b in range(-10, 11):
            for bound in range(-12, 13):
                for op in OPS:
                    rhs = Fraction(bound, a) + b
                    if rhs.denominator != 1:
                        continue
                    yield _spec("division_form", (a, b, int(rhs)), f"x/{a} + {b} {op} {int(rhs)}", Fraction(bound), op)
                    emitted += 1
                    if emitted >= budgets["division_form"]:
                        return


def iter_level4_specs() -> Iterable[dict]:
    budgets = FAMILY_CAPS["level_4"]
    emitted = 0
    for num in range(1, 9):
        for den in range(2, 9):
            coeff = Fraction(num, den)
            if coeff == 1:
                continue
            for b in range(-8, 9):
                for bound in range(-10, 11):
                    for op in OPS:
                        rhs = coeff * bound + b
                        yield _spec("fraction_coeff", (num, den, b, rhs.numerator, rhs.denominator), f"({num}/{den})x + {b} {op} {rhs.numerator}/{rhs.denominator}", Fraction(bound), op)
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
    for tenths in [5, 15, 20, 25, 30, 35]:
        coeff = Fraction(tenths, 10)
        for b in range(-8, 9):
            for bound in range(-10, 11):
                for op in OPS:
                    rhs = coeff * bound + b
                    if rhs.denominator != 1:
                        continue
                    yield _spec("decimal_coeff", (tenths, b, int(rhs)), f"{tenths/10:.1f}x + {b} {op} {int(rhs)}", Fraction(bound), op)
                    emitted += 1
                    if emitted >= budgets["decimal_coeff"]:
                        break
                if emitted >= budgets["decimal_coeff"]:
                    break
            if emitted >= budgets["decimal_coeff"]:
                break
        if emitted >= budgets["decimal_coeff"]:
            break


def iter_level5_specs() -> Iterable[dict]:
    budgets = FAMILY_CAPS["level_5"]
    emitted = 0
    for a in list(range(-10, -1)) + list(range(2, 11)):
        for d in range(-10, 11):
            if a == d:
                continue
            for b in range(-8, 9):
                for e in range(-8, 9):
                    for bound in range(-8, 9):
                        for op in OPS:
                            c = (a - d) * bound + e - b
                            yield _spec("signed_both_sides", (a, b, d, c, e), f"{a}x + {b} {op} {d}x + {c} + {e}", Fraction(bound), op, flipped=(a - d < 0))
                            emitted += 1
                            if emitted >= budgets["signed_both_sides"]:
                                break
                        if emitted >= budgets["signed_both_sides"]:
                            break
                    if emitted >= budgets["signed_both_sides"]:
                        break
                if emitted >= budgets["signed_both_sides"]:
                    break
            if emitted >= budgets["signed_both_sides"]:
                break
        if emitted >= budgets["signed_both_sides"]:
            break

    emitted = 0
    for a in range(-8, -1):
        for b in range(-5, 6):
            for c in range(2, 7):
                for d in range(-5, 6):
                    for bound in range(-8, 9):
                        for op in OPS:
                            rhs = a * (2 * bound + b) + c * (bound + d)
                            yield _spec("nested_grouping_flip", (a, b, c, d, rhs), f"{a}(2x + {b}) + {c}(x + {d}) {op} {rhs}", Fraction(bound), op, flipped=(2 * a + c < 0))
                            emitted += 1
                            if emitted >= budgets["nested_grouping_flip"]:
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


