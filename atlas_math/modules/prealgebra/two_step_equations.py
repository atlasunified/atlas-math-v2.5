from __future__ import annotations

import itertools
import random
from fractions import Fraction
from typing import Iterable

from atlas_math.modules.shared.common import make_sample

MODULE_INFO = {
    "module_id": "prealgebra.two_step_equations",
    "name": "Two-Step Equations",
    "topic": "prealgebra",
    "subtopic": "core_prealgebra",
    "difficulty_levels": ["level_1", "level_2", "level_3", "level_4", "level_5"],
    "enabled": True,
}

INSTRUCTIONS = [
    "Solve the equation: {problem}",
    "Find the value of the variable: {problem}",
    "Use inverse operations to solve: {problem}",
    "Work through the two-step equation carefully: {problem}",
]

LEVEL_SPEC_CAPS = {
    "level_1": 1000,
    "level_2": 1400,
    "level_3": 1800,
    "level_4": 2200,
    "level_5": 2600,
}

FAMILY_CAPS = {
    "level_1": {"ax_plus_b": 1000},
    "level_2": {"ax_minus_b": 700, "x_over_a_plus_b": 700},
    "level_3": {"signed_coeff": 900, "negative_constant": 900},
    "level_4": {"fraction_rhs_integer_solution": 1100, "decimal_rhs_exact": 1100},
    "level_5": {"fraction_coeff": 1300, "grouped_linear": 1300},
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
    if family == "ax_plus_b":
        return Fraction(v[2] - v[1], v[0])
    if family == "ax_minus_b":
        return Fraction(v[2] + v[1], v[0])
    if family == "x_over_a_plus_b":
        return (v[2] - v[1]) * v[0]
    if family == "signed_coeff":
        return Fraction(v[2] - v[1], v[0])
    if family == "negative_constant":
        return Fraction(v[2] - v[1], v[0])
    if family == "fraction_rhs_integer_solution":
        return Fraction(v[2] - v[1], v[0])
    if family == "decimal_rhs_exact":
        return Fraction(v[2] - v[1], v[0])
    if family == "fraction_coeff":
        return Fraction(v[3] - v[2], 1) / Fraction(v[0], v[1])
    if family == "grouped_linear":
        return Fraction(v[3] - v[2], v[0]) - v[1]
    raise ValueError(f"Unknown family: {family}")


def _problem_text(spec: dict) -> str:
    family = spec["family"]
    v = spec["values"]
    if family == "ax_plus_b":
        return f"{v[0]}x + {v[1]} = {v[2]}"
    if family == "ax_minus_b":
        return f"{v[0]}x - {v[1]} = {v[2]}"
    if family == "x_over_a_plus_b":
        return f"x/{v[0]} + {v[1]} = {v[2]}"
    if family == "signed_coeff":
        return f"{v[0]}x + {v[1]} = {v[2]}"
    if family == "negative_constant":
        return f"{v[0]}x + ({v[1]}) = {v[2]}"
    if family == "fraction_rhs_integer_solution":
        return f"{v[0]}x + {v[1]} = {v[2]}/{v[3]}"
    if family == "decimal_rhs_exact":
        return f"{v[0]}x + {v[1]} = {v[2]/10:.1f}"
    if family == "fraction_coeff":
        return f"({v[0]}/{v[1]})x + {v[2]} = {v[3]}"
    if family == "grouped_linear":
        return f"{v[0]}(x + {v[1]}) + {v[2]} = {v[3]}"
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
    family = "ax_plus_b"
    limit = FAMILY_CAPS["level_1"][family]
    emitted = 0
    for a in range(2, 13):
        for solution in range(-20, 21):
            for b in range(-12, 13):
                c = a * solution + b
                yield {
                    "family": family,
                    "values": (a, b, c),
                    "canonical_key": f"{family}:{a}:{b}:{c}",
                    "case_id": f"{family}:{a}:{b}:{c}",
                    "family_id": family,
                }
                emitted += 1
                if emitted >= limit:
                    return


def iter_level2_specs() -> Iterable[dict]:
    budgets = FAMILY_CAPS["level_2"]
    emitted = 0
    for a in range(2, 13):
        for solution in range(-20, 21):
            for b in range(1, 16):
                c = a * solution - b
                yield {
                    "family": "ax_minus_b",
                    "values": (a, b, c),
                    "canonical_key": f"ax_minus_b:{a}:{b}:{c}",
                    "case_id": f"ax_minus_b:{a}:{b}:{c}",
                    "family_id": "ax_minus_b",
                }
                emitted += 1
                if emitted >= budgets["ax_minus_b"]:
                    break
            if emitted >= budgets["ax_minus_b"]:
                break
        if emitted >= budgets["ax_minus_b"]:
            break

    emitted = 0
    for a in range(2, 16):
        for solution in range(-20, 21):
            for b in range(-12, 13):
                c = solution // a + b if solution % a == 0 else None
                if c is None:
                    continue
                yield {
                    "family": "x_over_a_plus_b",
                    "values": (a, b, c),
                    "canonical_key": f"x_over_a_plus_b:{a}:{b}:{c}",
                    "case_id": f"x_over_a_plus_b:{a}:{b}:{c}",
                    "family_id": "x_over_a_plus_b",
                }
                emitted += 1
                if emitted >= budgets["x_over_a_plus_b"]:
                    return


def iter_level3_specs() -> Iterable[dict]:
    budgets = FAMILY_CAPS["level_3"]
    emitted = 0
    for a in range(-12, 13):
        if a in {0, 1, -1}:
            continue
        for solution in range(-15, 16):
            for b in range(-10, 11):
                c = a * solution + b
                yield {
                    "family": "signed_coeff",
                    "values": (a, b, c),
                    "canonical_key": f"signed_coeff:{a}:{b}:{c}",
                    "case_id": f"signed_coeff:{a}:{b}:{c}",
                    "family_id": "signed_coeff",
                }
                emitted += 1
                if emitted >= budgets["signed_coeff"]:
                    break
            if emitted >= budgets["signed_coeff"]:
                break
        if emitted >= budgets["signed_coeff"]:
            break

    emitted = 0
    for a in range(2, 13):
        for solution in range(-20, 21):
            for b in range(-20, 0):
                c = a * solution + b
                yield {
                    "family": "negative_constant",
                    "values": (a, b, c),
                    "canonical_key": f"negative_constant:{a}:{b}:{c}",
                    "case_id": f"negative_constant:{a}:{b}:{c}",
                    "family_id": "negative_constant",
                }
                emitted += 1
                if emitted >= budgets["negative_constant"]:
                    return


def iter_level4_specs() -> Iterable[dict]:
    budgets = FAMILY_CAPS["level_4"]
    emitted = 0
    for a in range(2, 13):
        for b in range(-10, 11):
            for numerator in range(-40, 41):
                rhs = Fraction(a * numerator + a * b, a)
                if rhs.denominator != 1:
                    continue
                yield {
                    "family": "fraction_rhs_integer_solution",
                    "values": (a, b, rhs.numerator, rhs.denominator),
                    "canonical_key": f"fraction_rhs_integer_solution:{a}:{b}:{rhs.numerator}:{rhs.denominator}",
                    "case_id": f"fraction_rhs_integer_solution:{a}:{b}:{rhs.numerator}:{rhs.denominator}",
                    "family_id": "fraction_rhs_integer_solution",
                }
                emitted += 1
                if emitted >= budgets["fraction_rhs_integer_solution"]:
                    break
            if emitted >= budgets["fraction_rhs_integer_solution"]:
                break
        if emitted >= budgets["fraction_rhs_integer_solution"]:
            break

    emitted = 0
    for a in range(2, 11):
        for solution in range(-15, 16):
            for b in range(-9, 10):
                rhs = a * solution + b
                if rhs * 10 != int(rhs * 10):
                    continue
                yield {
                    "family": "decimal_rhs_exact",
                    "values": (a, b, int(rhs * 10)),
                    "canonical_key": f"decimal_rhs_exact:{a}:{b}:{int(rhs * 10)}",
                    "case_id": f"decimal_rhs_exact:{a}:{b}:{int(rhs * 10)}",
                    "family_id": "decimal_rhs_exact",
                }
                emitted += 1
                if emitted >= budgets["decimal_rhs_exact"]:
                    return


def iter_level5_specs() -> Iterable[dict]:
    budgets = FAMILY_CAPS["level_5"]
    emitted = 0
    for num in range(1, 10):
        for den in range(2, 10):
            for solution in range(-12, 13):
                for const in range(-9, 10):
                    rhs = Fraction(num, den) * solution + const
                    if rhs.denominator != 1:
                        continue
                    yield {
                        "family": "fraction_coeff",
                        "values": (num, den, const, rhs.numerator),
                        "canonical_key": f"fraction_coeff:{num}:{den}:{const}:{rhs.numerator}",
                        "case_id": f"fraction_coeff:{num}:{den}:{const}:{rhs.numerator}",
                        "family_id": "fraction_coeff",
                    }
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
        for shift in range(-10, 11):
            for solution in range(-15, 16):
                for const in range(-12, 13):
                    rhs = a * (solution + shift) + const
                    yield {
                        "family": "grouped_linear",
                        "values": (a, shift, const, rhs),
                        "canonical_key": f"grouped_linear:{a}:{shift}:{const}:{rhs}",
                        "case_id": f"grouped_linear:{a}:{shift}:{const}:{rhs}",
                        "family_id": "grouped_linear",
                    }
                    emitted += 1
                    if emitted >= budgets["grouped_linear"]:
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
        "level_1": ["solves equations of the form ax + b = c with integer solutions"],
        "level_2": ["adds subtraction constants and division-first two-step forms"],
        "level_3": ["adds signed coefficients and negative constants"],
        "level_4": ["adds fractional or decimal right-hand sides while preserving exact answers"],
        "level_5": ["adds fractional coefficients and grouped linear expressions"],
    }


