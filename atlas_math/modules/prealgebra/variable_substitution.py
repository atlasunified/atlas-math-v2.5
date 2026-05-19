from __future__ import annotations

import itertools
import random
from fractions import Fraction
from typing import Iterable

from atlas_math.modules.shared.common import make_sample

MODULE_INFO = {
    "module_id": "prealgebra.variable_substitution",
    "name": "Variable Substitution",
    "topic": "prealgebra",
    "subtopic": "core_prealgebra",
    "difficulty_levels": ["level_1", "level_2", "level_3", "level_4", "level_5"],
    "enabled": True,
}

INSTRUCTIONS = [
    "Substitute the given value and evaluate: {problem}",
    "Replace the variable and compute the result: {problem}",
    "Evaluate the expression after substitution: {problem}",
    "Work through the substitution carefully: {problem}",
]

LEVEL_SPEC_CAPS = {
    "level_1": 1000,
    "level_2": 1400,
    "level_3": 1800,
    "level_4": 2200,
    "level_5": 2600,
}

FAMILY_CAPS = {
    "level_1": {"single_variable_linear": 1000},
    "level_2": {"multiply_then_add": 700, "signed_substitution": 700},
    "level_3": {"two_variable_sum": 900, "power_substitution": 900},
    "level_4": {"fractional_coefficient": 1100, "nested_parentheses": 1100},
    "level_5": {"two_variable_product": 1300, "expression_difference": 1300},
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
    return str(value)


def _evaluate(spec: dict):
    family = spec["family"]
    v = spec["values"]
    if family == "single_variable_linear":
        return v[0] + v[1]
    if family == "multiply_then_add":
        return v[0] * v[1] + v[2]
    if family == "signed_substitution":
        return v[0] - v[1]
    if family == "two_variable_sum":
        return v[0] + 2 * v[1]
    if family == "power_substitution":
        return v[0] ** 2 + v[1]
    if family == "fractional_coefficient":
        return Fraction(v[0], v[1]) * v[2]
    if family == "nested_parentheses":
        return v[0] * (v[1] + v[2])
    if family == "two_variable_product":
        return v[0] * v[1] + v[2]
    if family == "expression_difference":
        return (v[0] + v[1]) - (v[2] - v[3])
    raise ValueError(f"Unknown family: {family}")


def _problem_text(spec: dict) -> str:
    family = spec["family"]
    v = spec["values"]
    if family == "single_variable_linear":
        return f"If x = {v[0]}, evaluate x + {v[1]}."
    if family == "multiply_then_add":
        return f"If n = {v[1]}, evaluate {v[0]}n + {v[2]}."
    if family == "signed_substitution":
        return f"If a = {v[0]}, evaluate a - {v[1]}."
    if family == "two_variable_sum":
        return f"If x = {v[0]} and y = {v[1]}, evaluate x + 2y."
    if family == "power_substitution":
        return f"If t = {v[0]}, evaluate t^2 + {v[1]}."
    if family == "fractional_coefficient":
        return f"If m = {v[2]}, evaluate ({v[0]}/{v[1]})m."
    if family == "nested_parentheses":
        return f"If p = {v[1]}, evaluate {v[0]}(p + {v[2]})."
    if family == "two_variable_product":
        return f"If x = {v[0]} and y = {v[1]}, evaluate xy + {v[2]}."
    if family == "expression_difference":
        return f"If a = {v[0]}, b = {v[1]}, c = {v[2]}, and d = {v[3]}, evaluate (a + b) - (c - d)."
    raise ValueError(f"Unknown family: {family}")


def _sample_from_spec(spec: dict, difficulty: str, instruction_idx: int = 0) -> dict:
    problem = _problem_text(spec)
    answer = _fmt_number(_evaluate(spec))
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
    family = "single_variable_linear"
    limit = FAMILY_CAPS["level_1"][family]
    emitted = 0
    for x in range(-20, 31):
        for add in range(-15, 16):
            yield {
                "family": family,
                "values": (x, add),
                "canonical_key": f"{family}:{x}:{add}",
                "case_id": f"{family}:{x}:{add}",
                "family_id": family,
            }
            emitted += 1
            if emitted >= limit:
                return


def iter_level2_specs() -> Iterable[dict]:
    budgets = FAMILY_CAPS["level_2"]
    emitted = 0
    for coeff in range(2, 10):
        for n in range(-12, 13):
            for const in range(-15, 16):
                yield {
                    "family": "multiply_then_add",
                    "values": (coeff, n, const),
                    "canonical_key": f"multiply_then_add:{coeff}:{n}:{const}",
                    "case_id": f"multiply_then_add:{coeff}:{n}:{const}",
                    "family_id": "multiply_then_add",
                }
                emitted += 1
                if emitted >= budgets["multiply_then_add"]:
                    break
            if emitted >= budgets["multiply_then_add"]:
                break
        if emitted >= budgets["multiply_then_add"]:
            break

    emitted = 0
    for a in range(-20, 31):
        for sub in range(-15, 16):
            yield {
                "family": "signed_substitution",
                "values": (a, sub),
                "canonical_key": f"signed_substitution:{a}:{sub}",
                "case_id": f"signed_substitution:{a}:{sub}",
                "family_id": "signed_substitution",
            }
            emitted += 1
            if emitted >= budgets["signed_substitution"]:
                return


def iter_level3_specs() -> Iterable[dict]:
    budgets = FAMILY_CAPS["level_3"]
    emitted = 0
    for x in range(-12, 13):
        for y in range(-12, 13):
            yield {
                "family": "two_variable_sum",
                "values": (x, y),
                "canonical_key": f"two_variable_sum:{x}:{y}",
                "case_id": f"two_variable_sum:{x}:{y}",
                "family_id": "two_variable_sum",
            }
            emitted += 1
            if emitted >= budgets["two_variable_sum"]:
                break
        if emitted >= budgets["two_variable_sum"]:
            break

    emitted = 0
    for t in range(-12, 13):
        for add in range(-20, 21):
            yield {
                "family": "power_substitution",
                "values": (t, add),
                "canonical_key": f"power_substitution:{t}:{add}",
                "case_id": f"power_substitution:{t}:{add}",
                "family_id": "power_substitution",
            }
            emitted += 1
            if emitted >= budgets["power_substitution"]:
                return


def iter_level4_specs() -> Iterable[dict]:
    budgets = FAMILY_CAPS["level_4"]
    emitted = 0
    for num in range(1, 8):
        for den in range(2, 10):
            for m in range(-12, 13):
                yield {
                    "family": "fractional_coefficient",
                    "values": (num, den, m),
                    "canonical_key": f"fractional_coefficient:{num}:{den}:{m}",
                    "case_id": f"fractional_coefficient:{num}:{den}:{m}",
                    "family_id": "fractional_coefficient",
                }
                emitted += 1
                if emitted >= budgets["fractional_coefficient"]:
                    break
            if emitted >= budgets["fractional_coefficient"]:
                break
        if emitted >= budgets["fractional_coefficient"]:
            break

    emitted = 0
    for coeff in range(2, 11):
        for p in range(-10, 11):
            for add in range(-10, 11):
                yield {
                    "family": "nested_parentheses",
                    "values": (coeff, p, add),
                    "canonical_key": f"nested_parentheses:{coeff}:{p}:{add}",
                    "case_id": f"nested_parentheses:{coeff}:{p}:{add}",
                    "family_id": "nested_parentheses",
                }
                emitted += 1
                if emitted >= budgets["nested_parentheses"]:
                    return


def iter_level5_specs() -> Iterable[dict]:
    budgets = FAMILY_CAPS["level_5"]
    emitted = 0
    for x in range(-10, 11):
        for y in range(-10, 11):
            for const in range(-20, 21):
                yield {
                    "family": "two_variable_product",
                    "values": (x, y, const),
                    "canonical_key": f"two_variable_product:{x}:{y}:{const}",
                    "case_id": f"two_variable_product:{x}:{y}:{const}",
                    "family_id": "two_variable_product",
                }
                emitted += 1
                if emitted >= budgets["two_variable_product"]:
                    break
            if emitted >= budgets["two_variable_product"]:
                break
        if emitted >= budgets["two_variable_product"]:
            break

    emitted = 0
    for a in range(-8, 9):
        for b in range(-8, 9):
            for c in range(-8, 9):
                for d in range(-8, 9):
                    yield {
                        "family": "expression_difference",
                        "values": (a, b, c, d),
                        "canonical_key": f"expression_difference:{a}:{b}:{c}:{d}",
                        "case_id": f"expression_difference:{a}:{b}:{c}:{d}",
                        "family_id": "expression_difference",
                    }
                    emitted += 1
                    if emitted >= budgets["expression_difference"]:
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
        "level_1": ["substitute into one-variable addition expressions"],
        "level_2": ["adds multiplication, constants, and signed substitutions"],
        "level_3": ["adds two variables and squares"],
        "level_4": ["adds fractional coefficients and grouped substitution"],
        "level_5": ["adds two-variable products and larger symbolic expression comparisons"],
    }


