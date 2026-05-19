from __future__ import annotations

import itertools
import random
from fractions import Fraction
from typing import Iterable

from atlas_math.modules.shared.common import make_sample

MODULE_INFO = {
    "module_id": "prealgebra.equations_with_distribution",
    "name": "Equations with Distribution",
    "topic": "prealgebra",
    "subtopic": "core_prealgebra",
    "difficulty_levels": ["level_1", "level_2", "level_3", "level_4", "level_5"],
    "enabled": True,
}

INSTRUCTIONS = [
    "Solve the equation by distributing first: {problem}",
    "Use the distributive property and solve: {problem}",
    "Expand the expression and isolate the variable: {problem}",
    "Work through the distribution carefully: {problem}",
]

LEVEL_SPEC_CAPS = {
    "level_1": 1000,
    "level_2": 1400,
    "level_3": 1800,
    "level_4": 2200,
    "level_5": 2600,
}

FAMILY_CAPS = {
    "level_1": {"a_x_plus_b": 1000},
    "level_2": {"a_x_minus_b": 700, "negative_inside": 700},
    "level_3": {"double_distribution": 900, "combine_like_terms_rhs": 900},
    "level_4": {"signed_outer": 1100, "fractional_result": 1100},
    "level_5": {"distribution_both_sides": 1300, "fraction_coeff_distribute": 1300},
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


def _solve(spec: dict):
    family = spec["family"]
    v = spec["values"]
    if family == "a_x_plus_b":
        return Fraction(v[2], 1)
    if family == "a_x_minus_b":
        return Fraction(v[2], 1)
    if family == "negative_inside":
        return Fraction(v[2], 1)
    if family == "double_distribution":
        return Fraction(v[4], 1)
    if family == "combine_like_terms_rhs":
        return Fraction(v[3], 1)
    if family == "signed_outer":
        return Fraction(v[3], 1)
    if family == "fractional_result":
        return Fraction(v[4], v[5])
    if family == "distribution_both_sides":
        return Fraction(v[6], 1)
    if family == "fraction_coeff_distribute":
        return Fraction(v[4], 1)
    raise ValueError(f"Unknown family: {family}")


def _problem_text(spec: dict) -> str:
    family = spec["family"]
    v = spec["values"]
    if family == "a_x_plus_b":
        return f"{v[0]}(x + {v[1]}) = {v[0] * (v[2] + v[1])}"
    if family == "a_x_minus_b":
        return f"{v[0]}(x - {v[1]}) = {v[0] * (v[2] - v[1])}"
    if family == "negative_inside":
        return f"{v[0]}(x - {v[1]}) = {v[0] * (v[2] - v[1])}"
    if family == "double_distribution":
        return f"{v[0]}(x + {v[1]}) + {v[2]}(x + {v[3]}) = {(v[0] + v[2]) * v[4] + v[0] * v[1] + v[2] * v[3]}"
    if family == "combine_like_terms_rhs":
        return f"{v[0]}(x + {v[1]}) = {v[2]}x + {v[0] * v[1] + (v[0] - v[2]) * v[3]}"
    if family == "signed_outer":
        return f"{v[0]}(x + {v[1]}) = {v[0] * (v[3] + v[1])}"
    if family == "fractional_result":
        return f"{v[0]}(x + {v[1]}) = {v[2]}/{v[3]}"
    if family == "distribution_both_sides":
        left = v[0] * (v[6] + v[1])
        right = v[2] * (v[6] + v[3]) + v[4]
        return f"{v[0]}(x + {v[1]}) = {v[2]}(x + {v[3]}) + {v[4]}"
    if family == "fraction_coeff_distribute":
        rhs = Fraction(v[0], v[1]) * (v[4] + v[2]) + v[3]
        return f"({v[0]}/{v[1]})(x + {v[2]}) + {v[3]} = {rhs.numerator}/{rhs.denominator}"
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
    family = "a_x_plus_b"
    limit = FAMILY_CAPS["level_1"][family]
    emitted = 0
    for a in range(2, 13):
        for b in range(-12, 13):
            for solution in range(-20, 21):
                yield {
                    "family": family,
                    "values": (a, b, solution),
                    "canonical_key": f"{family}:{a}:{b}:{solution}",
                    "case_id": f"{family}:{a}:{b}:{solution}",
                    "family_id": family,
                }
                emitted += 1
                if emitted >= limit:
                    return


def iter_level2_specs() -> Iterable[dict]:
    budgets = FAMILY_CAPS["level_2"]
    emitted = 0
    for a in range(2, 13):
        for b in range(1, 16):
            for solution in range(-20, 21):
                yield {
                    "family": "a_x_minus_b",
                    "values": (a, b, solution),
                    "canonical_key": f"a_x_minus_b:{a}:{b}:{solution}",
                    "case_id": f"a_x_minus_b:{a}:{b}:{solution}",
                    "family_id": "a_x_minus_b",
                }
                emitted += 1
                if emitted >= budgets["a_x_minus_b"]:
                    break
            if emitted >= budgets["a_x_minus_b"]:
                break
        if emitted >= budgets["a_x_minus_b"]:
            break

    emitted = 0
    for a in range(-12, 13):
        if a in {0, 1, -1}:
            continue
        for b in range(1, 16):
            for solution in range(-15, 16):
                yield {
                    "family": "negative_inside",
                    "values": (a, b, solution),
                    "canonical_key": f"negative_inside:{a}:{b}:{solution}",
                    "case_id": f"negative_inside:{a}:{b}:{solution}",
                    "family_id": "negative_inside",
                }
                emitted += 1
                if emitted >= budgets["negative_inside"]:
                    return


def iter_level3_specs() -> Iterable[dict]:
    budgets = FAMILY_CAPS["level_3"]
    emitted = 0
    for a in range(1, 10):
        for c in range(1, 10):
            for b in range(-8, 9):
                for d in range(-8, 9):
                    for solution in range(-10, 11):
                        if a + c == 0:
                            continue
                        yield {
                            "family": "double_distribution",
                            "values": (a, b, c, d, solution),
                            "canonical_key": f"double_distribution:{a}:{b}:{c}:{d}:{solution}",
                            "case_id": f"double_distribution:{a}:{b}:{c}:{d}:{solution}",
                            "family_id": "double_distribution",
                        }
                        emitted += 1
                        if emitted >= budgets["double_distribution"]:
                            break
                    if emitted >= budgets["double_distribution"]:
                        break
                if emitted >= budgets["double_distribution"]:
                    break
            if emitted >= budgets["double_distribution"]:
                break
        if emitted >= budgets["double_distribution"]:
            break

    emitted = 0
    for a in range(2, 13):
        for rhs_coeff in range(-8, 13):
            if rhs_coeff == a:
                continue
            for b in range(-12, 13):
                for solution in range(-12, 13):
                    yield {
                        "family": "combine_like_terms_rhs",
                        "values": (a, b, rhs_coeff, solution),
                        "canonical_key": f"combine_like_terms_rhs:{a}:{b}:{rhs_coeff}:{solution}",
                        "case_id": f"combine_like_terms_rhs:{a}:{b}:{rhs_coeff}:{solution}",
                        "family_id": "combine_like_terms_rhs",
                    }
                    emitted += 1
                    if emitted >= budgets["combine_like_terms_rhs"]:
                        return


def iter_level4_specs() -> Iterable[dict]:
    budgets = FAMILY_CAPS["level_4"]
    emitted = 0
    for a in range(-12, 13):
        if a in {0, 1, -1}:
            continue
        for b in range(-10, 11):
            for solution in range(-15, 16):
                yield {
                    "family": "signed_outer",
                    "values": (a, b, a * (solution + b), solution),
                    "canonical_key": f"signed_outer:{a}:{b}:{solution}",
                    "case_id": f"signed_outer:{a}:{b}:{solution}",
                    "family_id": "signed_outer",
                }
                emitted += 1
                if emitted >= budgets["signed_outer"]:
                    break
            if emitted >= budgets["signed_outer"]:
                break
        if emitted >= budgets["signed_outer"]:
            break

    emitted = 0
    for a in range(2, 13):
        for b in range(-8, 9):
            for num in range(-30, 31):
                rhs = Fraction(num, a) + b
                yield {
                    "family": "fractional_result",
                    "values": (a, b, rhs.numerator, rhs.denominator, num, a),
                    "canonical_key": f"fractional_result:{a}:{b}:{rhs.numerator}:{rhs.denominator}:{num}",
                    "case_id": f"fractional_result:{a}:{b}:{rhs.numerator}:{rhs.denominator}:{num}",
                    "family_id": "fractional_result",
                }
                emitted += 1
                if emitted >= budgets["fractional_result"]:
                    return


def iter_level5_specs() -> Iterable[dict]:
    budgets = FAMILY_CAPS["level_5"]
    emitted = 0
    for a in range(2, 12):
        for c in range(-10, 11):
            if c in {a, 0}:
                continue
            for b in range(-8, 9):
                for d in range(-8, 9):
                    for solution in range(-10, 11):
                        k = a * (solution + b) - c * (solution + d)
                        yield {
                            "family": "distribution_both_sides",
                            "values": (a, b, c, d, k, 0, solution),
                            "canonical_key": f"distribution_both_sides:{a}:{b}:{c}:{d}:{k}:{solution}",
                            "case_id": f"distribution_both_sides:{a}:{b}:{c}:{d}:{k}:{solution}",
                            "family_id": "distribution_both_sides",
                        }
                        emitted += 1
                        if emitted >= budgets["distribution_both_sides"]:
                            break
                    if emitted >= budgets["distribution_both_sides"]:
                        break
                if emitted >= budgets["distribution_both_sides"]:
                    break
            if emitted >= budgets["distribution_both_sides"]:
                break
        if emitted >= budgets["distribution_both_sides"]:
            break

    emitted = 0
    for num in range(1, 10):
        for den in range(2, 10):
            for b in range(-8, 9):
                for const in range(-8, 9):
                    for solution in range(-10, 11):
                        rhs = Fraction(num, den) * (solution + b) + const
                        if rhs.denominator == 1:
                            continue
                        yield {
                            "family": "fraction_coeff_distribute",
                            "values": (num, den, b, const, solution),
                            "canonical_key": f"fraction_coeff_distribute:{num}:{den}:{b}:{const}:{solution}",
                            "case_id": f"fraction_coeff_distribute:{num}:{den}:{b}:{const}:{solution}",
                            "family_id": "fraction_coeff_distribute",
                        }
                        emitted += 1
                        if emitted >= budgets["fraction_coeff_distribute"]:
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
        "level_1": ["solves equations that require one distribution step"],
        "level_2": ["adds subtraction inside parentheses and signed outer coefficients"],
        "level_3": ["adds multiple distributed terms and variable terms on both sides"],
        "level_4": ["adds negative multipliers and fractional outcomes"],
        "level_5": ["adds distribution on both sides and fractional distributed coefficients"],
    }


