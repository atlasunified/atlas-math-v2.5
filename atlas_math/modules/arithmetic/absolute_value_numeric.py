from __future__ import annotations

import itertools
import random
from typing import Iterable

from atlas_math.modules.shared.common import make_sample

MODULE_INFO = {
    "module_id": "arithmetic.absolute_value_numeric",
    "name": "Absolute Value Numeric",
    "topic": "arithmetic",
    "subtopic": "core_arithmetic",
    "difficulty_levels": ["level_1", "level_2", "level_3", "level_4", "level_5"],
    "enabled": True,
}

INSTRUCTIONS = [
    "Evaluate the absolute value expression: {problem}",
    "Compute the value carefully: {problem}",
    "Simplify the numeric absolute value problem: {problem}",
    "Work through the absolute value arithmetic: {problem}",
]

LEVEL_SPEC_CAPS = {
    "level_1": 1200,
    "level_2": 1500,
    "level_3": 1800,
    "level_4": 2200,
    "level_5": 2600,
}

FAMILY_CAPS = {
    "level_1": {"single_absolute": 1200},
    "level_2": {"absolute_sum": 750, "absolute_difference": 750},
    "level_3": {"outside_minus_inside": 900, "double_absolute_sum": 900},
    "level_4": {"nested_parentheses": 1100, "product_with_absolute": 1100},
    "level_5": {"combined_operations": 1300, "difference_of_absolutes": 1300},
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


def _evaluate(spec: dict) -> int:
    family = spec["family"]
    v = spec["values"]
    if family == "single_absolute":
        return abs(v[0])
    if family == "absolute_sum":
        return abs(v[0] + v[1])
    if family == "absolute_difference":
        return abs(v[0] - v[1])
    if family == "outside_minus_inside":
        return v[0] - abs(v[1])
    if family == "double_absolute_sum":
        return abs(v[0]) + abs(v[1])
    if family == "nested_parentheses":
        return abs(v[0] - (v[1] + v[2]))
    if family == "product_with_absolute":
        return v[0] * abs(v[1])
    if family == "combined_operations":
        return abs(v[0] + v[1]) - abs(v[2])
    if family == "difference_of_absolutes":
        return abs(v[0] - v[1]) + abs(v[2] - v[3])
    raise ValueError(f"Unknown family: {family}")


def _problem_text(spec: dict) -> str:
    family = spec["family"]
    v = spec["values"]
    if family == "single_absolute":
        return f"|{v[0]}|"
    if family == "absolute_sum":
        return f"|{v[0]} + {v[1]}|"
    if family == "absolute_difference":
        return f"|{v[0]} - {v[1]}|"
    if family == "outside_minus_inside":
        return f"{v[0]} - |{v[1]}|"
    if family == "double_absolute_sum":
        return f"|{v[0]}| + |{v[1]}|"
    if family == "nested_parentheses":
        return f"|{v[0]} - ({v[1]} + {v[2]})|"
    if family == "product_with_absolute":
        return f"{v[0]} × |{v[1]}|"
    if family == "combined_operations":
        return f"|{v[0]} + {v[1]}| - |{v[2]}|"
    if family == "difference_of_absolutes":
        return f"|{v[0]} - {v[1]}| + |{v[2]} - {v[3]}|"
    raise ValueError(f"Unknown family: {family}")


def _sample_from_spec(spec: dict, difficulty: str, instruction_idx: int = 0) -> dict:
    problem = _problem_text(spec)
    answer = str(_evaluate(spec))
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
    family = "single_absolute"
    limit = FAMILY_CAPS["level_1"][family]
    emitted = 0
    for a in range(-120, 121):
        yield {
            "family": family,
            "values": (a,),
            "canonical_key": f"{family}:{a}",
            "case_id": f"{family}:{a}",
            "family_id": family,
        }
        emitted += 1
        if emitted >= limit:
            return


def iter_level2_specs() -> Iterable[dict]:
    budgets = FAMILY_CAPS["level_2"]
    emitted = 0
    for a in range(-40, 41):
        for b in range(-40, 41):
            yield {
                "family": "absolute_sum",
                "values": (a, b),
                "canonical_key": f"absolute_sum:{a}:{b}",
                "case_id": f"absolute_sum:{a}:{b}",
                "family_id": "absolute_sum",
            }
            emitted += 1
            if emitted >= budgets["absolute_sum"]:
                break
        if emitted >= budgets["absolute_sum"]:
            break

    emitted = 0
    for a in range(-40, 41):
        for b in range(-40, 41):
            yield {
                "family": "absolute_difference",
                "values": (a, b),
                "canonical_key": f"absolute_difference:{a}:{b}",
                "case_id": f"absolute_difference:{a}:{b}",
                "family_id": "absolute_difference",
            }
            emitted += 1
            if emitted >= budgets["absolute_difference"]:
                return


def iter_level3_specs() -> Iterable[dict]:
    budgets = FAMILY_CAPS["level_3"]
    emitted = 0
    for outside in range(-30, 31):
        for inside in range(-40, 41):
            yield {
                "family": "outside_minus_inside",
                "values": (outside, inside),
                "canonical_key": f"outside_minus_inside:{outside}:{inside}",
                "case_id": f"outside_minus_inside:{outside}:{inside}",
                "family_id": "outside_minus_inside",
            }
            emitted += 1
            if emitted >= budgets["outside_minus_inside"]:
                break
        if emitted >= budgets["outside_minus_inside"]:
            break

    emitted = 0
    for a in range(-40, 41):
        for b in range(-40, 41):
            yield {
                "family": "double_absolute_sum",
                "values": (a, b),
                "canonical_key": f"double_absolute_sum:{a}:{b}",
                "case_id": f"double_absolute_sum:{a}:{b}",
                "family_id": "double_absolute_sum",
            }
            emitted += 1
            if emitted >= budgets["double_absolute_sum"]:
                return


def iter_level4_specs() -> Iterable[dict]:
    budgets = FAMILY_CAPS["level_4"]
    emitted = 0
    for a in range(-50, 51):
        for b in range(-25, 26):
            for c in range(-25, 26):
                yield {
                    "family": "nested_parentheses",
                    "values": (a, b, c),
                    "canonical_key": f"nested_parentheses:{a}:{b}:{c}",
                    "case_id": f"nested_parentheses:{a}:{b}:{c}",
                    "family_id": "nested_parentheses",
                }
                emitted += 1
                if emitted >= budgets["nested_parentheses"]:
                    break
            if emitted >= budgets["nested_parentheses"]:
                break
        if emitted >= budgets["nested_parentheses"]:
            break

    emitted = 0
    for a in range(-15, 16):
        for b in range(-30, 31):
            yield {
                "family": "product_with_absolute",
                "values": (a, b),
                "canonical_key": f"product_with_absolute:{a}:{b}",
                "case_id": f"product_with_absolute:{a}:{b}",
                "family_id": "product_with_absolute",
            }
            emitted += 1
            if emitted >= budgets["product_with_absolute"]:
                return


def iter_level5_specs() -> Iterable[dict]:
    budgets = FAMILY_CAPS["level_5"]
    emitted = 0
    for a in range(-30, 31):
        for b in range(-30, 31):
            for c in range(-30, 31):
                yield {
                    "family": "combined_operations",
                    "values": (a, b, c),
                    "canonical_key": f"combined_operations:{a}:{b}:{c}",
                    "case_id": f"combined_operations:{a}:{b}:{c}",
                    "family_id": "combined_operations",
                }
                emitted += 1
                if emitted >= budgets["combined_operations"]:
                    break
            if emitted >= budgets["combined_operations"]:
                break
        if emitted >= budgets["combined_operations"]:
            break

    emitted = 0
    for a in range(-30, 31):
        for b in range(-30, 31):
            for c in range(-30, 31):
                for d in range(-30, 31):
                    yield {
                        "family": "difference_of_absolutes",
                        "values": (a, b, c, d),
                        "canonical_key": f"difference_of_absolutes:{a}:{b}:{c}:{d}",
                        "case_id": f"difference_of_absolutes:{a}:{b}:{c}:{d}",
                        "family_id": "difference_of_absolutes",
                    }
                    emitted += 1
                    if emitted >= budgets["difference_of_absolutes"]:
                        return


def _iter_specs(difficulty: str) -> Iterable[dict]:
    level = _difficulty_name(_level_num(difficulty))
    if level == "level_1":
        return _take(iter_level1_specs(), LEVEL_SPEC_CAPS[level])
    if level == "level_2":
        return _take(iter_level2_specs(), LEVEL_SPEC_CAPS[level])
    if level == "level_3":
        return _take(iter_level3_specs(), LEVEL_SPEC_CAPS[level])
    if level == "level_4":
        return _take(iter_level4_specs(), LEVEL_SPEC_CAPS[level])
    return _take(iter_level5_specs(), LEVEL_SPEC_CAPS[level])


def generate(count: int = 10, difficulty: str = "level_1", seed=None) -> list[dict]:
    if count <= 0:
        return []
    prefix = min(max(int(count) * MAX_GENERATE_MULTIPLIER, 256), MAX_SPEC_PREFIX)
    pool = list(itertools.islice(_iter_specs(difficulty), 0, prefix))
    rng = random.Random(_stable_seed(seed, difficulty, count, "generate"))
    rng.shuffle(pool)
    out, seen = [], set()
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


def generate_unique(count: int = 10, difficulty: str = "level_1", offset: int = 0, stride: int = 1, seed=None) -> list[dict]:
    if count <= 0:
        return []
    stride = max(1, int(stride or 1))
    offset = max(0, int(offset or 0))
    level = _difficulty_name(_level_num(difficulty))
    prefix = min(max(count * 16, 512), LEVEL_SPEC_CAPS[level], MAX_SPEC_PREFIX)
    pool = list(itertools.islice(_iter_specs(difficulty), 0, prefix))
    indexed_pool = list(enumerate(pool))
    rng = random.Random(_stable_seed(seed, difficulty, offset, stride, count, "generate_unique"))
    rng.shuffle(indexed_pool)
    if not indexed_pool:
        return []
    start = offset % len(indexed_pool)
    ordered = indexed_pool[start::stride] + indexed_pool[:start:stride]
    out, seen = [], set()
    for idx, spec in ordered:
        sample = _sample_from_spec(spec, difficulty, instruction_idx=idx + offset)
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
    max_items = min(LEVEL_SPEC_CAPS[level], MAX_ITER_SAMPLES)
    pool = list(itertools.islice(_iter_specs(difficulty), 0, max_items))
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
        "level_1": ["evaluates the absolute value of a single integer"],
        "level_2": ["finds absolute values of sums and differences"],
        "level_3": ["combines absolute values with outside subtraction or addition"],
        "level_4": ["handles grouped expressions and multiplication with absolute value"],
        "level_5": ["solves multi-part absolute value expressions with several operations"],
    }


