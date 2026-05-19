from __future__ import annotations

import random
from fractions import Fraction
from typing import Iterable

from atlas_math.modules.shared.common import make_sample

MODULE_INFO = {
    "module_id": "algebra.compound_inequalities",
    "name": "Compound Inequalities",
    "topic": "algebra",
    "subtopic": "core_algebra",
    "difficulty_levels": ["level_1", "level_2", "level_3", "level_4", "level_5"],
    "enabled": True,
}

INSTRUCTIONS = [
    "Solve the compound inequality: {problem}",
    "Find the solution set for: {problem}",
    "Work carefully through the compound inequality: {problem}",
    "Express the compound inequality solution clearly: {problem}",
]

LEVEL_SPEC_CAPS = {"level_1": 1000, "level_2": 1400, "level_3": 1800, "level_4": 2200, "level_5": 2600}
FAMILY_CAPS = {
    "level_1": {"double_inequality_integer": 1000},
    "level_2": {"and_pair": 700, "or_pair": 700},
    "level_3": {"negative_coeff_between": 900, "negative_coeff_or": 900},
    "level_4": {"fraction_between": 1100, "decimal_or": 1100},
    "level_5": {"variables_both_sides_and": 1300, "nested_between": 1300},
}
CAPACITY_HINTS = {level: {"value": cap, "quality": "capped"} for level, cap in LEVEL_SPEC_CAPS.items()}
MAX_SPEC_PREFIX = 5000
MAX_GENERATE_MULTIPLIER = 8
MAX_ITER_SAMPLES = 4096
BOUND_OPS = [("<", "<"), ("<=", "<"), ("<", "<="), ("<=", "<=")]


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


def _interval_answer(left_op: str, left: Fraction, right_op: str, right: Fraction) -> str:
    return f"{_fmt_number(left)} {left_op} x {right_op} {_fmt_number(right)}"


def _pair_answer(left_op: str, left: Fraction, joiner: str, right_op: str, right: Fraction) -> str:
    return f"x {left_op} {_fmt_number(left)} {joiner} x {right_op} {_fmt_number(right)}"


def _spec(family, values, problem, answer):
    key = ":".join([family] + [str(v) for v in values])
    return {"family": family, "values": values, "problem": problem, "answer": answer, "canonical_key": key, "case_id": key, "family_id": family}


def _sample_from_spec(spec: dict, difficulty: str, instruction_idx: int = 0) -> dict:
    answer = spec["answer"]
    metadata = {"family": spec["family"], "level_number": _level_num(difficulty), "structured": True, "canonical_key": spec["canonical_key"], "case_id": spec["case_id"], "family_id": spec["family_id"], "template_id": spec["family"], "final_answer": answer, "values": list(spec.get("values", []))}
    instruction = INSTRUCTIONS[instruction_idx % len(INSTRUCTIONS)].format(problem=spec["problem"])
    return make_sample(module_id=MODULE_INFO["module_id"], topic=MODULE_INFO["topic"], subtopic=MODULE_INFO["subtopic"], difficulty=difficulty, instruction=instruction, input_text=spec["problem"], answer=answer, metadata=metadata)


def iter_level1_specs() -> Iterable[dict]:
    limit = FAMILY_CAPS["level_1"]["double_inequality_integer"]
    emitted = 0
    for a in range(-15, 10):
        for b in range(a + 1, a + 26):
            for left_op, right_op in BOUND_OPS:
                problem = f"{a} {left_op} x {right_op} {b}"
                answer = _interval_answer(left_op, Fraction(a), right_op, Fraction(b))
                yield _spec("double_inequality_integer", (a, b, left_op, right_op), problem, answer)
                emitted += 1
                if emitted >= limit:
                    return


def iter_level2_specs() -> Iterable[dict]:
    budgets = FAMILY_CAPS["level_2"]
    emitted = 0
    for a in range(-20, 5):
        for b in range(a + 2, a + 28):
            for left_op, right_op in BOUND_OPS:
                problem = f"x {_flip(left_op)} {a} and x {right_op} {b}"
                answer = _interval_answer(left_op, Fraction(a), right_op, Fraction(b))
                yield _spec("and_pair", (a, b, left_op, right_op), problem, answer)
                emitted += 1
                if emitted >= budgets["and_pair"]:
                    break
            if emitted >= budgets["and_pair"]:
                break
        if emitted >= budgets["and_pair"]:
            break

    emitted = 0
    for a in range(-15, 16):
        for b in range(a + 2, a + 20):
            for lo, ro in [("<", ">"), ("<=", ">"), ("<", ">="), ("<=", ">=")]:
                problem = f"x {lo} {a} or x {ro} {b}"
                answer = _pair_answer(lo, Fraction(a), "or", ro, Fraction(b))
                yield _spec("or_pair", (a, b, lo, ro), problem, answer)
                emitted += 1
                if emitted >= budgets["or_pair"]:
                    return


def iter_level3_specs() -> Iterable[dict]:
    budgets = FAMILY_CAPS["level_3"]
    emitted = 0
    for a in range(-9, -1):
        for low in range(-10, 1):
            for high in range(low + 1, low + 16):
                for left_op, right_op in BOUND_OPS:
                    left = a * low
                    right = a * high
                    problem = f"{left} {_flip(left_op)} {a}x {_flip(right_op)} {right}"
                    answer = _interval_answer(left_op, Fraction(low), right_op, Fraction(high))
                    yield _spec("negative_coeff_between", (a, low, high, left_op, right_op), problem, answer)
                    emitted += 1
                    if emitted >= budgets["negative_coeff_between"]:
                        break
                if emitted >= budgets["negative_coeff_between"]:
                    break
            if emitted >= budgets["negative_coeff_between"]:
                break
        if emitted >= budgets["negative_coeff_between"]:
            break

    emitted = 0
    for a in range(-9, -1):
        for left_bound in range(-12, 5):
            for right_bound in range(left_bound + 2, left_bound + 18):
                for lo, ro in [(">", "<"), (">=", "<"), (">", "<="), (">=", "<=")]:
                    left_rhs = a * left_bound
                    right_rhs = a * right_bound
                    problem = f"{a}x {_flip(lo)} {left_rhs} or {a}x {_flip(ro)} {right_rhs}"
                    answer = _pair_answer(lo, Fraction(left_bound), "or", ro, Fraction(right_bound))
                    yield _spec("negative_coeff_or", (a, left_bound, right_bound, lo, ro), problem, answer)
                    emitted += 1
                    if emitted >= budgets["negative_coeff_or"]:
                        return


def iter_level4_specs() -> Iterable[dict]:
    budgets = FAMILY_CAPS["level_4"]
    emitted = 0
    for num in range(1, 8):
        for den in range(2, 8):
            coeff = Fraction(num, den)
            if coeff == 1:
                continue
            for low in range(-8, 1):
                for high in range(low + 1, low + 12):
                    for left_op, right_op in BOUND_OPS:
                        left = coeff * low
                        right = coeff * high
                        problem = f"{left.numerator}/{left.denominator} {left_op} ({num}/{den})x {right_op} {right.numerator}/{right.denominator}"
                        answer = _interval_answer(left_op, Fraction(low), right_op, Fraction(high))
                        yield _spec("fraction_between", (num, den, low, high, left_op, right_op), problem, answer)
                        emitted += 1
                        if emitted >= budgets["fraction_between"]:
                            break
                    if emitted >= budgets["fraction_between"]:
                        break
                if emitted >= budgets["fraction_between"]:
                    break
            if emitted >= budgets["fraction_between"]:
                break
        if emitted >= budgets["fraction_between"]:
            break

    emitted = 0
    for tenths in [5, 15, 20, 25, 30]:
        coeff = Fraction(tenths, 10)
        for a in range(-10, 6):
            for b in range(a + 2, a + 16):
                for lo, ro in [("<", ">"), ("<=", ">"), ("<", ">="), ("<=", ">=")]:
                    left = coeff * a
                    right = coeff * b
                    if left.denominator != 1 or right.denominator != 1:
                        continue
                    problem = f"{tenths/10:.1f}x {lo} {left.numerator} or {tenths/10:.1f}x {ro} {right.numerator}"
                    answer = _pair_answer(lo, Fraction(a), "or", ro, Fraction(b))
                    yield _spec("decimal_or", (tenths, a, b, lo, ro), problem, answer)
                    emitted += 1
                    if emitted >= budgets["decimal_or"]:
                        return


def iter_level5_specs() -> Iterable[dict]:
    budgets = FAMILY_CAPS["level_5"]
    emitted = 0
    for a in range(2, 9):
        for d in range(1, 8):
            if a == d:
                continue
            for b in range(-6, 7):
                for e in range(-6, 7):
                    coeff = a - d
                    if coeff <= 0:
                        continue
                    for low in range(-8, 1):
                        for high in range(low + 1, low + 12):
                            for left_op, right_op in BOUND_OPS:
                                c1 = coeff * low + e - b
                                c2 = coeff * high + e - b
                                problem = f"{a}x + {b} {_flip(left_op)} {d}x + {c1} + {e} and {a}x + {b} {right_op} {d}x + {c2} + {e}"
                                answer = _interval_answer(left_op, Fraction(low), right_op, Fraction(high))
                                yield _spec("variables_both_sides_and", (a, b, d, e, low, high, left_op, right_op), problem, answer)
                                emitted += 1
                                if emitted >= budgets["variables_both_sides_and"]:
                                    break
                            if emitted >= budgets["variables_both_sides_and"]:
                                break
                        if emitted >= budgets["variables_both_sides_and"]:
                            break
                    if emitted >= budgets["variables_both_sides_and"]:
                        break
                if emitted >= budgets["variables_both_sides_and"]:
                    break
            if emitted >= budgets["variables_both_sides_and"]:
                break
        if emitted >= budgets["variables_both_sides_and"]:
            break

    emitted = 0
    for a in range(2, 7):
        for b in range(-5, 6):
            for c in range(-5, 6):
                for low in range(-6, 1):
                    for high in range(low + 1, low + 10):
                        for left_op, right_op in BOUND_OPS:
                            left = a * (2 * low + b) + c
                            right = a * (2 * high + b) + c
                            problem = f"{left} {left_op} {a}(2x + {b}) + {c} {right_op} {right}"
                            answer = _interval_answer(left_op, Fraction(low), right_op, Fraction(high))
                            yield _spec("nested_between", (a, b, c, low, high, left_op, right_op), problem, answer)
                            emitted += 1
                            if emitted >= budgets["nested_between"]:
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


