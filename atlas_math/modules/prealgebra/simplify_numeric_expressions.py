from __future__ import annotations

import itertools
import random
from fractions import Fraction
from typing import Iterable

from atlas_math.modules.shared.common import make_sample

MODULE_INFO = {
    "module_id": "prealgebra.simplify_numeric_expressions",
    "name": "Simplify Numeric Expressions",
    "topic": "prealgebra",
    "subtopic": "core_prealgebra",
    "difficulty_levels": ["level_1", "level_2", "level_3", "level_4", "level_5"],
    "enabled": True,
}

INSTRUCTIONS = [
    "Simplify the expression: {problem}",
    "Evaluate the numeric expression carefully: {problem}",
    "Work through the expression step by step: {problem}",
    "Compute the final simplified value: {problem}",
]

LEVEL_SPEC_CAPS = {
    "level_1": 1000,
    "level_2": 1400,
    "level_3": 1800,
    "level_4": 2200,
    "level_5": 2600,
}

FAMILY_CAPS = {
    "level_1": {"two_op": 1000},
    "level_2": {"parentheses": 700, "signed_chain": 700},
    "level_3": {"distributive_numeric": 900, "fraction_mix": 900},
    "level_4": {"nested_grouping": 1100, "power_then_operations": 1100},
    "level_5": {"complex_fractional": 1300, "double_nested": 1300},
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


def _evaluate(spec: dict):
    family = spec["family"]
    v = spec["values"]
    if family == "two_op":
        return v[0] + v[1] * v[2]
    if family == "parentheses":
        return (v[0] + v[1]) * v[2]
    if family == "signed_chain":
        return v[0] - v[1] + v[2]
    if family == "distributive_numeric":
        return v[0] * (v[1] + v[2])
    if family == "fraction_mix":
        return Fraction(v[0], v[1]) + Fraction(v[2], v[3])
    if family == "nested_grouping":
        return (v[0] - (v[1] + v[2])) * v[3]
    if family == "power_then_operations":
        return (v[0] ** 2) + v[1] * v[2]
    if family == "complex_fractional":
        return (Fraction(v[0], v[1]) - Fraction(v[2], v[3])) * v[4]
    if family == "double_nested":
        return (v[0] + v[1]) * (v[2] - v[3]) + v[4]
    raise ValueError(f"Unknown family: {family}")


def _problem_text(spec: dict) -> str:
    family = spec["family"]
    v = spec["values"]
    if family == "two_op":
        return f"{v[0]} + {v[1]} × {v[2]}"
    if family == "parentheses":
        return f"({v[0]} + {v[1]}) × {v[2]}"
    if family == "signed_chain":
        return f"{v[0]} - {v[1]} + {v[2]}"
    if family == "distributive_numeric":
        return f"{v[0]}({v[1]} + {v[2]})"
    if family == "fraction_mix":
        return f"{v[0]}/{v[1]} + {v[2]}/{v[3]}"
    if family == "nested_grouping":
        return f"({v[0]} - ({v[1]} + {v[2]})) × {v[3]}"
    if family == "power_then_operations":
        return f"{v[0]}^2 + {v[1]} × {v[2]}"
    if family == "complex_fractional":
        return f"({v[0]}/{v[1]} - {v[2]}/{v[3]}) × {v[4]}"
    if family == "double_nested":
        return f"({v[0]} + {v[1]})({v[2]} - {v[3]}) + {v[4]}"
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
    family = "two_op"
    limit = FAMILY_CAPS["level_1"][family]
    emitted = 0
    for a in range(1, 31):
        for b in range(1, 13):
            for c in range(1, 13):
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
    for a in range(1, 21):
        for b in range(1, 21):
            for c in range(2, 13):
                yield {
                    "family": "parentheses",
                    "values": (a, b, c),
                    "canonical_key": f"parentheses:{a}:{b}:{c}",
                    "case_id": f"parentheses:{a}:{b}:{c}",
                    "family_id": "parentheses",
                }
                emitted += 1
                if emitted >= budgets["parentheses"]:
                    break
            if emitted >= budgets["parentheses"]:
                break
        if emitted >= budgets["parentheses"]:
            break

    emitted = 0
    for a in range(-20, 21):
        for b in range(-15, 16):
            for c in range(-15, 16):
                yield {
                    "family": "signed_chain",
                    "values": (a, b, c),
                    "canonical_key": f"signed_chain:{a}:{b}:{c}",
                    "case_id": f"signed_chain:{a}:{b}:{c}",
                    "family_id": "signed_chain",
                }
                emitted += 1
                if emitted >= budgets["signed_chain"]:
                    return


def iter_level3_specs() -> Iterable[dict]:
    budgets = FAMILY_CAPS["level_3"]
    emitted = 0
    for a in range(2, 16):
        for b in range(1, 16):
            for c in range(1, 16):
                yield {
                    "family": "distributive_numeric",
                    "values": (a, b, c),
                    "canonical_key": f"distributive_numeric:{a}:{b}:{c}",
                    "case_id": f"distributive_numeric:{a}:{b}:{c}",
                    "family_id": "distributive_numeric",
                }
                emitted += 1
                if emitted >= budgets["distributive_numeric"]:
                    break
            if emitted >= budgets["distributive_numeric"]:
                break
        if emitted >= budgets["distributive_numeric"]:
            break

    emitted = 0
    for a in range(1, 8):
        for b in range(2, 9):
            for c in range(1, 8):
                for d in range(2, 9):
                    yield {
                        "family": "fraction_mix",
                        "values": (a, b, c, d),
                        "canonical_key": f"fraction_mix:{a}:{b}:{c}:{d}",
                        "case_id": f"fraction_mix:{a}:{b}:{c}:{d}",
                        "family_id": "fraction_mix",
                    }
                    emitted += 1
                    if emitted >= budgets["fraction_mix"]:
                        return


def iter_level4_specs() -> Iterable[dict]:
    budgets = FAMILY_CAPS["level_4"]
    emitted = 0
    for a in range(5, 31):
        for b in range(1, 11):
            for c in range(1, 11):
                for d in range(2, 11):
                    yield {
                        "family": "nested_grouping",
                        "values": (a, b, c, d),
                        "canonical_key": f"nested_grouping:{a}:{b}:{c}:{d}",
                        "case_id": f"nested_grouping:{a}:{b}:{c}:{d}",
                        "family_id": "nested_grouping",
                    }
                    emitted += 1
                    if emitted >= budgets["nested_grouping"]:
                        break
                if emitted >= budgets["nested_grouping"]:
                    break
            if emitted >= budgets["nested_grouping"]:
                break
        if emitted >= budgets["nested_grouping"]:
            break

    emitted = 0
    for a in range(2, 16):
        for b in range(-8, 9):
            for c in range(-8, 9):
                yield {
                    "family": "power_then_operations",
                    "values": (a, b, c),
                    "canonical_key": f"power_then_operations:{a}:{b}:{c}",
                    "case_id": f"power_then_operations:{a}:{b}:{c}",
                    "family_id": "power_then_operations",
                }
                emitted += 1
                if emitted >= budgets["power_then_operations"]:
                    return


def iter_level5_specs() -> Iterable[dict]:
    budgets = FAMILY_CAPS["level_5"]
    emitted = 0
    for a in range(1, 9):
        for b in range(2, 10):
            for c in range(1, 9):
                for d in range(2, 10):
                    for m in range(-6, 7):
                        if m == 0:
                            continue
                        yield {
                            "family": "complex_fractional",
                            "values": (a, b, c, d, m),
                            "canonical_key": f"complex_fractional:{a}:{b}:{c}:{d}:{m}",
                            "case_id": f"complex_fractional:{a}:{b}:{c}:{d}:{m}",
                            "family_id": "complex_fractional",
                        }
                        emitted += 1
                        if emitted >= budgets["complex_fractional"]:
                            break
                    if emitted >= budgets["complex_fractional"]:
                        break
                if emitted >= budgets["complex_fractional"]:
                    break
            if emitted >= budgets["complex_fractional"]:
                break
        if emitted >= budgets["complex_fractional"]:
            break

    emitted = 0
    for a in range(-8, 13):
        for b in range(-8, 13):
            for c in range(-8, 13):
                for d in range(-8, 13):
                    for e in range(-15, 16):
                        yield {
                            "family": "double_nested",
                            "values": (a, b, c, d, e),
                            "canonical_key": f"double_nested:{a}:{b}:{c}:{d}:{e}",
                            "case_id": f"double_nested:{a}:{b}:{c}:{d}:{e}",
                            "family_id": "double_nested",
                        }
                        emitted += 1
                        if emitted >= budgets["double_nested"]:
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
        "level_1": ["basic order-of-operations numeric expressions"],
        "level_2": ["adds parentheses and signed integer chains"],
        "level_3": ["adds distributive structure and fraction addition"],
        "level_4": ["adds nested grouping and simple exponents"],
        "level_5": ["adds multi-layer fraction expressions and double-nested grouped forms"],
    }


