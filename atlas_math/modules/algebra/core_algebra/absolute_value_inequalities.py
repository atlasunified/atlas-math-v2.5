from __future__ import annotations

import itertools
import random
from fractions import Fraction
from typing import Iterable

from atlas_math.modules.shared.common import make_sample

MODULE_INFO = {
    "module_id": "algebra.absolute_value_inequalities",
    "name": "Absolute Value Inequalities",
    "topic": "algebra",
    "subtopic": "core_algebra",
    "difficulty_levels": ["level_1", "level_2", "level_3", "level_4", "level_5"],
    "enabled": True,
}

INSTRUCTIONS = [
    "Solve the absolute value inequality: {problem}",
    "Write the solution set: {problem}",
    "Find all real numbers that satisfy: {problem}",
    "Express the answer in interval notation: {problem}",
]

LEVEL_SPEC_CAPS = {"level_1": 900, "level_2": 1200, "level_3": 1500, "level_4": 1800, "level_5": 2200}
FAMILY_CAPS = {
    "level_1": {"distance_less_greater": 900},
    "level_2": {"scaled_inner": 700, "outer_shift": 500},
    "level_3": {"signed_coeff": 800, "impossible_or_all": 700},
    "level_4": {"fraction_center": 900, "fraction_bound": 900},
    "level_5": {"nested_linear": 1100, "decimal_bound": 1100},
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
    if isinstance(value, float):
        return f"{value:.2f}".rstrip("0").rstrip(".")
    return str(value)


def _interval_answer(kind: str, center: Fraction, radius) -> str:
    if isinstance(radius, float):
        left = float(center) - radius
        right = float(center) + radius
        left_s = _fmt_number(left)
        right_s = _fmt_number(right)
    else:
        left = center - radius
        right = center + radius
        left_s = _fmt_number(left)
        right_s = _fmt_number(right)
    if kind == "lt":
        return f"({left_s}, {right_s})"
    if kind == "le":
        return f"[{left_s}, {right_s}]"
    if kind == "gt":
        return f"(-inf, {left_s}) U ({right_s}, inf)"
    if kind == "ge":
        return f"(-inf, {left_s}] U [{right_s}, inf)"
    if kind == "all":
        return "all real numbers"
    return "no solution"


def _spec(family: str, values: tuple, problem: str, answer: str):
    canonical = ":".join([family] + [str(v) for v in values])
    return {
        "family": family,
        "values": values,
        "problem": problem,
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


def iter_level1_specs() -> Iterable[dict]:
    limit = FAMILY_CAPS["level_1"]["distance_less_greater"]
    emitted = 0
    for h in range(-18, 19):
        for k in range(0, 13):
            for symbol, kind in [("<", "lt"), ("<=", "le"), (">", "gt"), (">=", "ge")]:
                problem = f"|x - ({h})| {symbol} {k}"
                answer = _interval_answer(kind, Fraction(h), Fraction(k))
                yield _spec("distance_less_greater", (h, k, kind), problem, answer)
                emitted += 1
                if emitted >= limit:
                    return


def iter_level2_specs() -> Iterable[dict]:
    budgets = FAMILY_CAPS["level_2"]
    emitted = 0
    for a in [2, 3, 4, 5, -2, -3, -4, -5]:
        for h in range(-12, 13):
            for k in range(0, 11):
                center = Fraction(a * h, a)
                for symbol, kind in [("<", "lt"), ("<=", "le"), (">", "gt"), (">=", "ge")]:
                    problem = f"|{a}x - ({a * h})| {symbol} {k}"
                    answer = _interval_answer(kind, Fraction(h), Fraction(k, abs(a)))
                    yield _spec("scaled_inner", (a, h, k, kind), problem, answer)
                    emitted += 1
                    if emitted >= budgets["scaled_inner"]:
                        break
                if emitted >= budgets["scaled_inner"]:
                    break
            if emitted >= budgets["scaled_inner"]:
                break
        if emitted >= budgets["scaled_inner"]:
            break

    emitted = 0
    for h in range(-15, 16):
        for d in range(-8, 9):
            for total in range(-3, 17):
                rhs = total - d
                for symbol, kind in [("<", "lt"), ("<=", "le"), (">", "gt"), (">=", "ge")]:
                    problem = f"|x + {h}| + {d} {symbol} {total}"
                    if rhs < 0:
                        answer = "no solution" if kind in {"lt", "le"} else "all real numbers"
                    else:
                        answer = _interval_answer(kind, Fraction(-h), Fraction(rhs))
                    yield _spec("outer_shift", (h, d, total, kind), problem, answer)
                    emitted += 1
                    if emitted >= budgets["outer_shift"]:
                        return


def iter_level3_specs() -> Iterable[dict]:
    budgets = FAMILY_CAPS["level_3"]
    emitted = 0
    for a in [-6, -5, -4, -3, -2, 2, 3, 4, 5, 6]:
        for b in range(-18, 19):
            for k in range(0, 13):
                center = Fraction(-b, a)
                radius = Fraction(k, abs(a))
                for symbol, kind in [("<", "lt"), ("<=", "le"), (">", "gt"), (">=", "ge")]:
                    problem = f"|{a}x + {b}| {symbol} {k}"
                    answer = _interval_answer(kind, center, radius)
                    yield _spec("signed_coeff", (a, b, k, kind), problem, answer)
                    emitted += 1
                    if emitted >= budgets["signed_coeff"]:
                        break
                if emitted >= budgets["signed_coeff"]:
                    break
            if emitted >= budgets["signed_coeff"]:
                break
        if emitted >= budgets["signed_coeff"]:
            break

    emitted = 0
    for h in range(-12, 13):
        for neg_k in range(1, 8):
            for symbol, answer in [
                ("<", "no solution"),
                ("<=", "no solution"),
                (">", "all real numbers"),
                (">=", "all real numbers"),
            ]:
                problem = f"|x - ({h})| {symbol} -{neg_k}"
                kind = f"special_{symbol}_{neg_k}"
                yield _spec("impossible_or_all", (h, symbol, neg_k), problem, answer)
                emitted += 1
                if emitted >= budgets["impossible_or_all"]:
                    return


def iter_level4_specs() -> Iterable[dict]:
    budgets = FAMILY_CAPS["level_4"]
    emitted = 0
    for p in range(1, 8):
        for q in range(2, 8):
            center = Fraction(p, q)
            for k in range(0, 12):
                for symbol, kind in [("<", "lt"), ("<=", "le"), (">", "gt"), (">=", "ge")]:
                    problem = f"|x - {p}/{q}| {symbol} {k}"
                    answer = _interval_answer(kind, center, Fraction(k))
                    yield _spec("fraction_center", (p, q, k, kind), problem, answer)
                    emitted += 1
                    if emitted >= budgets["fraction_center"]:
                        break
                if emitted >= budgets["fraction_center"]:
                    break
            if emitted >= budgets["fraction_center"]:
                break
        if emitted >= budgets["fraction_center"]:
            break

    emitted = 0
    for h in range(-12, 13):
        for num in range(1, 10):
            for den in range(2, 8):
                bound = Fraction(num, den)
                for symbol, kind in [("<", "lt"), ("<=", "le"), (">", "gt"), (">=", "ge")]:
                    problem = f"|x - ({h})| {symbol} {num}/{den}"
                    answer = _interval_answer(kind, Fraction(h), bound)
                    yield _spec("fraction_bound", (h, num, den, kind), problem, answer)
                    emitted += 1
                    if emitted >= budgets["fraction_bound"]:
                        return


def iter_level5_specs() -> Iterable[dict]:
    budgets = FAMILY_CAPS["level_5"]
    emitted = 0
    for a in [2, 3, 4, 5, -2, -3, -4]:
        for d in range(-8, 9):
            for b in range(-10, 11):
                center = Fraction(-(a * d + b), a)
                for k in range(0, 11):
                    for symbol, kind in [("<", "lt"), ("<=", "le"), (">", "gt"), (">=", "ge")]:
                        problem = f"|{a}(x + {d}) + {b}| {symbol} {k}"
                        answer = _interval_answer(kind, center, Fraction(k, abs(a)))
                        yield _spec("nested_linear", (a, d, b, k, kind), problem, answer)
                        emitted += 1
                        if emitted >= budgets["nested_linear"]:
                            break
                    if emitted >= budgets["nested_linear"]:
                        break
                if emitted >= budgets["nested_linear"]:
                    break
            if emitted >= budgets["nested_linear"]:
                break
        if emitted >= budgets["nested_linear"]:
            break

    emitted = 0
    for h in range(-10, 11):
        for tenths in [5, 10, 15, 20, 25, 30, 35, 40]:
            bound = tenths / 10.0
            for symbol, kind in [("<", "lt"), ("<=", "le"), (">", "gt"), (">=", "ge")]:
                problem = f"|x - ({h})| {symbol} {bound:.1f}"
                answer = _interval_answer(kind, Fraction(h), bound)
                yield _spec("decimal_bound", (h, tenths, kind), problem, answer)
                emitted += 1
                if emitted >= budgets["decimal_bound"]:
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
        "level_1": ["solve |x-h| compared to nonnegative integer bounds"],
        "level_2": ["adds scaling inside absolute value and outer constants"],
        "level_3": ["adds signed coefficients and negative-bound edge cases"],
        "level_4": ["adds fractional centers and fractional bounds"],
        "level_5": ["adds nested linear interiors and decimal bounds"],
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


