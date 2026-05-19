from __future__ import annotations

import itertools
import random
from fractions import Fraction
from typing import Iterable

from atlas_math.modules.shared.common import make_sample

MODULE_INFO = {
    "module_id": "prealgebra.one_step_equations",
    "name": "One-Step Equations",
    "topic": "prealgebra",
    "subtopic": "core_prealgebra",
    "difficulty_levels": ["level_1", "level_2", "level_3", "level_4", "level_5"],
    "enabled": True,
}

INSTRUCTIONS = [
    "Solve the equation: {problem}",
    "Find the value of the variable: {problem}",
    "Work through the one-step equation carefully: {problem}",
    "Isolate the variable and solve: {problem}",
]

LEVEL_SPEC_CAPS = {
    "level_1": 1000,
    "level_2": 1400,
    "level_3": 1800,
    "level_4": 2200,
    "level_5": 2600,
}

FAMILY_CAPS = {
    "level_1": {"x_plus_a": 1000},
    "level_2": {"x_minus_a": 700, "ax_equals_b": 700},
    "level_3": {"x_over_a": 900, "a_times_x_signed": 900},
    "level_4": {"negative_x_plus_a": 1100, "fractional_solution": 1100},
    "level_5": {"fraction_coeff": 1300, "decimal_coeff_exact": 1300},
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
    family = spec["family"]
    v = spec["values"]
    if family == "x_plus_a":
        return v[1] - v[0]
    if family == "x_minus_a":
        return v[1] + v[0]
    if family == "ax_equals_b":
        return Fraction(v[1], v[0])
    if family == "x_over_a":
        return v[0] * v[1]
    if family == "a_times_x_signed":
        return Fraction(v[1], v[0])
    if family == "negative_x_plus_a":
        return v[0] - v[1]
    if family == "fractional_solution":
        return Fraction(v[1], v[0])
    if family == "fraction_coeff":
        return Fraction(v[2]) / Fraction(v[0], v[1])
    if family == "decimal_coeff_exact":
        return Fraction(v[1], 1) / Fraction(v[0], 10)
    raise ValueError(f"Unknown family: {family}")


def _problem_text(spec: dict) -> str:
    family = spec["family"]
    v = spec["values"]
    if family == "x_plus_a":
        return f"x + {v[0]} = {v[1]}"
    if family == "x_minus_a":
        return f"x - {v[0]} = {v[1]}"
    if family == "ax_equals_b":
        return f"{v[0]}x = {v[1]}"
    if family == "x_over_a":
        return f"x/{v[0]} = {v[1]}"
    if family == "a_times_x_signed":
        return f"{v[0]}x = {v[1]}"
    if family == "negative_x_plus_a":
        return f"-x + {v[0]} = {v[1]}"
    if family == "fractional_solution":
        return f"{v[0]}x = {v[1]}"
    if family == "fraction_coeff":
        return f"({v[0]}/{v[1]})x = {v[2]}"
    if family == "decimal_coeff_exact":
        return f"{v[0]/10:.1f}x = {v[1]}"
    raise ValueError(f"Unknown family: {family}")


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
        "values": list(spec["values"]),
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


def iter_level1_specs() -> Iterable[dict]:
    family = "x_plus_a"
    limit = FAMILY_CAPS["level_1"][family]
    emitted = 0
    for a in range(-20, 21):
        for solution in range(-25, 26):
            b = solution + a
            yield {
                "family": family,
                "values": (a, b),
                "canonical_key": f"{family}:{a}:{b}",
                "case_id": f"{family}:{a}:{b}",
                "family_id": family,
            }
            emitted += 1
            if emitted >= limit:
                return


def iter_level2_specs() -> Iterable[dict]:
    budgets = FAMILY_CAPS["level_2"]
    emitted = 0
    for a in range(-20, 21):
        for solution in range(-25, 26):
            b = solution - a
            yield {
                "family": "x_minus_a",
                "values": (a, b),
                "canonical_key": f"x_minus_a:{a}:{b}",
                "case_id": f"x_minus_a:{a}:{b}",
                "family_id": "x_minus_a",
            }
            emitted += 1
            if emitted >= budgets["x_minus_a"]:
                break
        if emitted >= budgets["x_minus_a"]:
            break

    emitted = 0
    for a in range(2, 16):
        for solution in range(-20, 21):
            b = a * solution
            yield {
                "family": "ax_equals_b",
                "values": (a, b),
                "canonical_key": f"ax_equals_b:{a}:{b}",
                "case_id": f"ax_equals_b:{a}:{b}",
                "family_id": "ax_equals_b",
            }
            emitted += 1
            if emitted >= budgets["ax_equals_b"]:
                return


def iter_level3_specs() -> Iterable[dict]:
    budgets = FAMILY_CAPS["level_3"]
    emitted = 0
    for a in range(2, 16):
        for solution in range(-20, 21):
            rhs = solution
            yield {
                "family": "x_over_a",
                "values": (a, rhs),
                "canonical_key": f"x_over_a:{a}:{rhs}",
                "case_id": f"x_over_a:{a}:{rhs}",
                "family_id": "x_over_a",
            }
            emitted += 1
            if emitted >= budgets["x_over_a"]:
                break
        if emitted >= budgets["x_over_a"]:
            break

    emitted = 0
    for a in range(-15, 16):
        if a in {0, 1, -1}:
            continue
        for solution in range(-15, 16):
            b = a * solution
            yield {
                "family": "a_times_x_signed",
                "values": (a, b),
                "canonical_key": f"a_times_x_signed:{a}:{b}",
                "case_id": f"a_times_x_signed:{a}:{b}",
                "family_id": "a_times_x_signed",
            }
            emitted += 1
            if emitted >= budgets["a_times_x_signed"]:
                return


def iter_level4_specs() -> Iterable[dict]:
    budgets = FAMILY_CAPS["level_4"]
    emitted = 0
    for a in range(-20, 31):
        for solution in range(-20, 21):
            b = a - solution
            yield {
                "family": "negative_x_plus_a",
                "values": (a, b),
                "canonical_key": f"negative_x_plus_a:{a}:{b}",
                "case_id": f"negative_x_plus_a:{a}:{b}",
                "family_id": "negative_x_plus_a",
            }
            emitted += 1
            if emitted >= budgets["negative_x_plus_a"]:
                break
        if emitted >= budgets["negative_x_plus_a"]:
            break

    emitted = 0
    for a in range(2, 16):
        for num in range(-30, 31):
            if num == 0:
                continue
            yield {
                "family": "fractional_solution",
                "values": (a, num),
                "canonical_key": f"fractional_solution:{a}:{num}",
                "case_id": f"fractional_solution:{a}:{num}",
                "family_id": "fractional_solution",
            }
            emitted += 1
            if emitted >= budgets["fractional_solution"]:
                return


def iter_level5_specs() -> Iterable[dict]:
    budgets = FAMILY_CAPS["level_5"]
    emitted = 0
    for num in range(1, 10):
        for den in range(2, 10):
            for rhs in range(-20, 21):
                yield {
                    "family": "fraction_coeff",
                    "values": (num, den, rhs),
                    "canonical_key": f"fraction_coeff:{num}:{den}:{rhs}",
                    "case_id": f"fraction_coeff:{num}:{den}:{rhs}",
                    "family_id": "fraction_coeff",
                }
                emitted += 1
                if emitted >= budgets["fraction_coeff"]:
                    break
            if emitted >= budgets["fraction_coeff"]:
                break
        if emitted >= budgets["fraction_coeff"]:
            break

    emitted = 0
    for tenths in range(2, 31):
        if tenths == 10:
            continue
        for solution in range(-20, 21):
            rhs = Fraction(tenths, 10) * solution
            if rhs.denominator != 1:
                continue
            yield {
                "family": "decimal_coeff_exact",
                "values": (tenths, int(rhs)),
                "canonical_key": f"decimal_coeff_exact:{tenths}:{int(rhs)}",
                "case_id": f"decimal_coeff_exact:{tenths}:{int(rhs)}",
                "family_id": "decimal_coeff_exact",
            }
            emitted += 1
            if emitted >= budgets["decimal_coeff_exact"]:
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
        "level_1": ["solves x + a = b"],
        "level_2": ["adds subtraction and multiplication equations with integer solutions"],
        "level_3": ["adds division forms and signed coefficients"],
        "level_4": ["adds negative-variable equations and fractional answers"],
        "level_5": ["adds fractional and exact decimal coefficients while keeping one-step structure"],
    }


