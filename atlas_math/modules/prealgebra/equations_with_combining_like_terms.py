from __future__ import annotations

import itertools
import random
from fractions import Fraction
from typing import Iterable

from atlas_math.modules.shared.common import make_sample

MODULE_INFO = {
    "module_id": "prealgebra.equations_with_combining_like_terms",
    "name": "Equations with Combining Like Terms",
    "topic": "prealgebra",
    "subtopic": "core_prealgebra",
    "difficulty_levels": ["level_1", "level_2", "level_3", "level_4", "level_5"],
    "enabled": True,
}

INSTRUCTIONS = [
    "Solve the equation after combining like terms: {problem}",
    "Simplify each side and solve: {problem}",
    "Combine like terms, then isolate the variable: {problem}",
    "Work carefully through the algebra: {problem}",
]

LEVEL_SPEC_CAPS = {"level_1": 1000, "level_2": 1400, "level_3": 1800, "level_4": 2200, "level_5": 2600}
FAMILY_CAPS = {
    "level_1": {"same_side_positive": 1000},
    "level_2": {"same_side_signed": 700, "both_sides_positive": 700},
    "level_3": {"both_sides_signed": 900, "coeff_on_rhs": 900},
    "level_4": {"negative_result": 1100, "fraction_solution": 1100},
    "level_5": {"decimals_exact": 1300, "larger_coeff_mix": 1300},
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


def _solve(spec: dict):
    return spec["answer"]


def _problem_text(spec: dict) -> str:
    return spec["problem"]


def _sample_from_spec(spec: dict, difficulty: str, instruction_idx: int = 0) -> dict:
    problem = _problem_text(spec)
    answer = _fmt_number(_solve(spec))
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
    instruction = INSTRUCTIONS[instruction_idx % len(INSTRUCTIONS)].format(problem=problem)
    return make_sample(
        module_id=MODULE_INFO["module_id"],
        topic=MODULE_INFO["topic"],
        subtopic=MODULE_INFO["subtopic"],
        difficulty=difficulty,
        instruction=instruction,
        input_text=problem,
        answer=answer,
        metadata=metadata,
    )


def _spec(family: str, values: tuple, problem: str, answer):
    key = ":".join([family] + [str(v) for v in values])
    return {"family": family, "values": values, "problem": problem, "answer": answer, "canonical_key": key, "case_id": key, "family_id": family}


def iter_level1_specs() -> Iterable[dict]:
    limit = FAMILY_CAPS["level_1"]["same_side_positive"]
    emitted = 0
    for a in range(1, 13):
        for b in range(1, 13):
            for solution in range(-20, 21):
                rhs = (a + b) * solution
                yield _spec("same_side_positive", (a, b, solution), f"{a}x + {b}x = {rhs}", Fraction(solution))
                emitted += 1
                if emitted >= limit:
                    return


def iter_level2_specs() -> Iterable[dict]:
    budgets = FAMILY_CAPS["level_2"]
    emitted = 0
    for a in range(2, 13):
        for b in range(-12, 13):
            if b == 0:
                continue
            for solution in range(-15, 16):
                rhs = (a + b) * solution
                if a + b == 0:
                    continue
                sign = '+' if b > 0 else '-'
                yield _spec("same_side_signed", (a, b, solution), f"{a}x {sign} {abs(b)}x = {rhs}", Fraction(solution))
                emitted += 1
                if emitted >= budgets["same_side_signed"]:
                    break
            if emitted >= budgets["same_side_signed"]:
                break
        if emitted >= budgets["same_side_signed"]:
            break

    emitted = 0
    for a in range(2, 13):
        for b in range(1, 11):
            for c in range(1, 11):
                if a == c:
                    continue
                for solution in range(-12, 13):
                    d = (a - c) * solution + b
                    yield _spec("both_sides_positive", (a, b, c, d, solution), f"{a}x + {b} = {c}x + {d}", Fraction(solution))
                    emitted += 1
                    if emitted >= budgets["both_sides_positive"]:
                        return


def iter_level3_specs() -> Iterable[dict]:
    budgets = FAMILY_CAPS["level_3"]
    emitted = 0
    for a in range(-10, 11):
        if a == 0:
            continue
        for b in range(-10, 11):
            if b == 0 or a + b == 0:
                continue
            for solution in range(-12, 13):
                rhs = (a + b) * solution
                pa = f"{a}x" if a != 1 else "x"
                pb = f"+ {b}x" if b > 0 else f"- {abs(b)}x"
                yield _spec("both_sides_signed", (a, b, solution), f"{pa} {pb} = {rhs}", Fraction(solution))
                emitted += 1
                if emitted >= budgets["both_sides_signed"]:
                    break
            if emitted >= budgets["both_sides_signed"]:
                break
        if emitted >= budgets["both_sides_signed"]:
            break

    emitted = 0
    for a in range(2, 13):
        for b in range(-12, 13):
            for c in range(-9, 10):
                if c == 0 or a == c:
                    continue
                for solution in range(-10, 11):
                    d = (a - c) * solution + b
                    yield _spec("coeff_on_rhs", (a, b, c, d, solution), f"{a}x + {b} = {c}x + {d}", Fraction(solution))
                    emitted += 1
                    if emitted >= budgets["coeff_on_rhs"]:
                        return


def iter_level4_specs() -> Iterable[dict]:
    budgets = FAMILY_CAPS["level_4"]
    emitted = 0
    for a in range(2, 14):
        for c in range(-13, 14):
            if c == a:
                continue
            for solution in range(-20, 0):
                for b in range(-10, 11):
                    d = (a - c) * solution + b
                    yield _spec("negative_result", (a, b, c, d, solution), f"{a}x + {b} = {c}x + {d}", Fraction(solution))
                    emitted += 1
                    if emitted >= budgets["negative_result"]:
                        break
                if emitted >= budgets["negative_result"]:
                    break
            if emitted >= budgets["negative_result"]:
                break
        if emitted >= budgets["negative_result"]:
            break

    emitted = 0
    for a in range(2, 13):
        for c in range(-10, 11):
            if c == a:
                continue
            diff = a - c
            for num in range(-25, 26):
                if num == 0:
                    continue
                sol = Fraction(num, diff)
                if sol.denominator == 1:
                    continue
                yield _spec("fraction_solution", (a, c, num), f"{a}x = {c}x + {num}", sol)
                emitted += 1
                if emitted >= budgets["fraction_solution"]:
                    return


def iter_level5_specs() -> Iterable[dict]:
    budgets = FAMILY_CAPS["level_5"]
    emitted = 0
    decimals = [5, 10, 15, 20, 25, 30]
    for a10 in decimals:
        for c10 in decimals:
            if a10 == c10:
                continue
            for solution in range(-10, 11):
                for b in range(-10, 11):
                    rhs = (Fraction(a10 - c10, 10) * solution) + b
                    if rhs.denominator != 1:
                        continue
                    yield _spec("decimals_exact", (a10, b, c10, int(rhs), solution), f"{a10/10:.1f}x + {b} = {c10/10:.1f}x + {int(rhs)}", Fraction(solution))
                    emitted += 1
                    if emitted >= budgets["decimals_exact"]:
                        break
                if emitted >= budgets["decimals_exact"]:
                    break
            if emitted >= budgets["decimals_exact"]:
                break
        if emitted >= budgets["decimals_exact"]:
            break

    emitted = 0
    for a in range(-15, 16):
        for b in range(-15, 16):
            for c in range(-15, 16):
                if a == 0 or c == 0 or a == c:
                    continue
                for solution in range(-12, 13):
                    d = (a - c) * solution + b
                    yield _spec("larger_coeff_mix", (a, b, c, d, solution), f"{a}x + {b} = {c}x + {d}", Fraction(solution))
                    emitted += 1
                    if emitted >= budgets["larger_coeff_mix"]:
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
    return {
        "level_1": ["combines positive like terms on one side before solving"],
        "level_2": ["adds signed same-side combinations and basic both-side equations"],
        "level_3": ["adds signed coefficients on both sides"],
        "level_4": ["adds negative and fractional solutions"],
        "level_5": ["adds exact decimal coefficients and wider coefficient ranges"],
    }


