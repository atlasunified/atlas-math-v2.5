from __future__ import annotations

import itertools
import random
from fractions import Fraction
from typing import Iterable

from atlas_math.modules.shared.common import make_sample

MODULE_INFO = {
    "module_id": "algebra.systems_of_linear_inequalities",
    "name": "Systems of Linear Inequalities",
    "topic": "algebra",
    "subtopic": "core_algebra",
    "difficulty_levels": ["level_1", "level_2", "level_3", "level_4", "level_5"],
    "enabled": True,
}

INSTRUCTIONS = [
    "Solve the system of inequalities: {problem}",
    "Write the solution set in interval notation: {problem}",
    "Find all real numbers that satisfy both inequalities: {problem}",
    "Determine the intersection of the two solution sets: {problem}",
]

LEVEL_SPEC_CAPS = {"level_1": 900, "level_2": 1200, "level_3": 1500, "level_4": 1800, "level_5": 2200}
FAMILY_CAPS = {
    "level_1": {"bounded_interval": 900},
    "level_2": {"halfline_and_bound": 700, "closed_open_mix": 500},
    "level_3": {"disjoint_or_empty": 750, "scaled_bounds": 750},
    "level_4": {"fraction_bounds": 900, "decimal_bounds": 900},
    "level_5": {"nested_linear": 1100, "mixed_fraction_scale": 1100},
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


def _bound_interval(lo, lo_incl: bool, hi, hi_incl: bool) -> str:
    left = "[" if lo_incl else "("
    right = "]" if hi_incl else ")"
    return f"{left}{_fmt_number(lo)}, {_fmt_number(hi)}{right}"


def _halfline(side: str, bound, incl: bool) -> str:
    if side == "left":
        return f"(-inf, {_fmt_number(bound)}{']' if incl else ')'}"
    return f"{'[' if incl else '('}{_fmt_number(bound)}, inf)"


def _spec(family: str, values: tuple, ineq1: str, ineq2: str, answer: str):
    canonical = ":".join([family] + [str(v) for v in values])
    return {
        "family": family,
        "values": values,
        "problem": f"{ineq1}\n{ineq2}",
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
    limit = FAMILY_CAPS["level_1"]["bounded_interval"]
    emitted = 0
    for lo in range(-15, 6):
        for hi in range(lo + 1, 16):
            for lo_incl in [False, True]:
                for hi_incl in [False, True]:
                    ineq1 = f"x {'>=' if lo_incl else '>'} {lo}"
                    ineq2 = f"x {'<=' if hi_incl else '<'} {hi}"
                    ans = _bound_interval(Fraction(lo), lo_incl, Fraction(hi), hi_incl)
                    yield _spec("bounded_interval", (lo, lo_incl, hi, hi_incl), ineq1, ineq2, ans)
                    emitted += 1
                    if emitted >= limit:
                        return


def iter_level2_specs() -> Iterable[dict]:
    budgets = FAMILY_CAPS["level_2"]
    emitted = 0
    for bound in range(-12, 13):
        for hi in range(bound + 1, 15):
            for incl1 in [False, True]:
                for incl2 in [False, True]:
                    ineq1 = f"x {'>=' if incl1 else '>'} {bound}"
                    ineq2 = f"x {'<=' if incl2 else '<'} {hi}"
                    yield _spec("halfline_and_bound", (bound, incl1, hi, incl2), ineq1, ineq2, _bound_interval(Fraction(bound), incl1, Fraction(hi), incl2))
                    emitted += 1
                    if emitted >= budgets["halfline_and_bound"]:
                        break
                if emitted >= budgets["halfline_and_bound"]:
                    break
            if emitted >= budgets["halfline_and_bound"]:
                break
        if emitted >= budgets["halfline_and_bound"]:
            break

    emitted = 0
    for lo in range(-12, 7):
        for hi in range(lo + 2, 17):
            for lo_incl, hi_incl in [(True, False), (False, True)]:
                ineq1 = f"2x {'>=' if lo_incl else '>'} {2 * lo}"
                ineq2 = f"x {'<=' if hi_incl else '<'} {hi}"
                yield _spec("closed_open_mix", (lo, lo_incl, hi, hi_incl), ineq1, ineq2, _bound_interval(Fraction(lo), lo_incl, Fraction(hi), hi_incl))
                emitted += 1
                if emitted >= budgets["closed_open_mix"]:
                    return


def iter_level3_specs() -> Iterable[dict]:
    budgets = FAMILY_CAPS["level_3"]
    emitted = 0
    for a in range(-10, 6):
        for b in range(a + 1, 13):
            ineq1 = f"x < {a}"
            ineq2 = f"x > {b}"
            yield _spec("disjoint_or_empty", (a, b), ineq1, ineq2, "no solution")
            emitted += 1
            if emitted >= budgets["disjoint_or_empty"]:
                return

    emitted = 0
    for lo in range(-10, 6):
        for hi in range(lo + 2, 16):
            for lo_incl in [False, True]:
                for hi_incl in [False, True]:
                    ineq1 = f"3x {'>=' if lo_incl else '>'} {3 * lo}"
                    ineq2 = f"-2x {'>=' if hi_incl else '>'} {-2 * hi}"
                    ans = _bound_interval(Fraction(lo), lo_incl, Fraction(hi), hi_incl)
                    yield _spec("scaled_bounds", (lo, lo_incl, hi, hi_incl), ineq1, ineq2, ans)
                    emitted += 1
                    if emitted >= budgets["scaled_bounds"]:
                        return


def iter_level4_specs() -> Iterable[dict]:
    budgets = FAMILY_CAPS["level_4"]
    emitted = 0
    vals = [Fraction(n, d) for n in range(-10, 11) for d in (2, 3, 4)]
    vals = sorted(set(vals))
    for lo in vals:
        for hi in vals:
            if hi <= lo:
                continue
            for lo_incl in [False, True]:
                for hi_incl in [False, True]:
                    ineq1 = f"x {'>=' if lo_incl else '>'} {_fmt_number(lo)}"
                    ineq2 = f"x {'<=' if hi_incl else '<'} {_fmt_number(hi)}"
                    yield _spec("fraction_bounds", (lo, lo_incl, hi, hi_incl), ineq1, ineq2, _bound_interval(lo, lo_incl, hi, hi_incl))
                    emitted += 1
                    if emitted >= budgets["fraction_bounds"]:
                        break
                if emitted >= budgets["fraction_bounds"]:
                    break
            if emitted >= budgets["fraction_bounds"]:
                break
        if emitted >= budgets["fraction_bounds"]:
            break

    emitted = 0
    vals_d = [n / 10.0 for n in range(-35, 41, 5)]
    for lo in vals_d:
        for hi in vals_d:
            if hi <= lo:
                continue
            ineq1 = f"x >= {_fmt_number(lo)}"
            ineq2 = f"x < {_fmt_number(hi)}"
            yield _spec("decimal_bounds", (lo, hi), ineq1, ineq2, _bound_interval(lo, True, hi, False))
            emitted += 1
            if emitted >= budgets["decimal_bounds"]:
                return


def iter_level5_specs() -> Iterable[dict]:
    budgets = FAMILY_CAPS["level_5"]
    emitted = 0
    for a, d, lo, hi in [(2, -1, -4, 5), (3, 2, -3, 4), (-2, 3, -5, 2), (4, -2, -2, 3)]:
        for lo_incl in [False, True]:
            for hi_incl in [False, True]:
                if a > 0:
                    ineq1 = f"{a}(x + {d}) {'>=' if lo_incl else '>'} {a * lo}"
                    ineq2 = f"{a}(x + {d}) {'<=' if hi_incl else '<'} {a * hi}"
                else:
                    ineq1 = f"{a}(x + {d}) {'<=' if lo_incl else '<'} {a * lo}"
                    ineq2 = f"{a}(x + {d}) {'>=' if hi_incl else '>'} {a * hi}"
                ans = _bound_interval(Fraction(lo - d), lo_incl, Fraction(hi - d), hi_incl)
                yield _spec("nested_linear", (a, d, lo, lo_incl, hi, hi_incl), ineq1, ineq2, ans)
                emitted += 1
                if emitted >= budgets["nested_linear"]:
                    break
            if emitted >= budgets["nested_linear"]:
                break
        if emitted >= budgets["nested_linear"]:
            break

    emitted = 0
    coeffs = [Fraction(1, 2), Fraction(3, 2), Fraction(-1, 2), Fraction(-3, 2)]
    vals = [Fraction(n, 2) for n in range(-10, 11)]
    for a in coeffs:
        for lo in vals:
            for hi in vals:
                if hi <= lo:
                    continue
                for lo_incl in [False, True]:
                    for hi_incl in [False, True]:
                        if a > 0:
                            ineq1 = f"{_fmt_number(a)}x {'>=' if lo_incl else '>'} {_fmt_number(a * lo)}"
                            ineq2 = f"{_fmt_number(a)}x {'<=' if hi_incl else '<'} {_fmt_number(a * hi)}"
                        else:
                            ineq1 = f"{_fmt_number(a)}x {'<=' if lo_incl else '<'} {_fmt_number(a * lo)}"
                            ineq2 = f"{_fmt_number(a)}x {'>=' if hi_incl else '>'} {_fmt_number(a * hi)}"
                        yield _spec("mixed_fraction_scale", (a, lo, lo_incl, hi, hi_incl), ineq1, ineq2, _bound_interval(lo, lo_incl, hi, hi_incl))
                        emitted += 1
                        if emitted >= budgets["mixed_fraction_scale"]:
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
        "level_1": ["intersect one-variable linear inequalities to form bounded intervals"],
        "level_2": ["adds coefficient scaling and mixed open/closed endpoints"],
        "level_3": ["adds empty intersections and sign-flip coefficient cases"],
        "level_4": ["adds rational and decimal interval bounds"],
        "level_5": ["adds parentheses and fractional scaling"],
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


