from __future__ import annotations

import itertools
import random
from typing import Iterable

from atlas_math.modules.shared.common import make_sample

MODULE_INFO = {
    "module_id": "arithmetic.integer_addition_subtraction",
    "name": "Integer Addition and Subtraction",
    "topic": "arithmetic",
    "subtopic": "core_arithmetic",
    "difficulty_levels": ["level_1", "level_2", "level_3", "level_4", "level_5"],
    "enabled": True,
}

INSTRUCTIONS = [
    "Solve the arithmetic problem: {problem}",
    "Work through the calculation carefully: {problem}",
    "Compute the value and show clear arithmetic: {problem}",
    "Evaluate the expression step by step: {problem}",
]

LEVEL_SPEC_CAPS = {
    "level_1": 1200,
    "level_2": 1600,
    "level_3": 2000,
    "level_4": 2400,
    "level_5": 2800,
}

FAMILY_CAPS = {
    "level_1": {"add_two": 1200},
    "level_2": {"add_sub": 800, "add_sub_chain": 800},
    "level_3": {"balanced": 1000, "parentheses_bridge": 1000},
    "level_4": {"subtract_group": 1200, "nested_subtract": 1200},
    "level_5": {"four_terms": 1400, "double_parentheses": 1400},
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
    values = spec["values"]
    if family in {"add_two", "add_sub", "add_sub_chain", "balanced", "four_terms"}:
        total = values[0]
        for op, value in zip(spec["ops"], values[1:]):
            total = total + value if op == "+" else total - value
        return total
    if family == "parentheses_bridge":
        return (values[0] + values[1]) - values[2]
    if family == "subtract_group":
        return values[0] - (values[1] + values[2])
    if family == "nested_subtract":
        return values[0] - (values[1] - values[2])
    if family == "double_parentheses":
        return (values[0] - values[1]) + (values[2] + values[3])
    raise ValueError(f"Unknown family: {family}")


def _problem_text(spec: dict) -> str:
    family = spec["family"]
    values = spec["values"]
    if family == "add_two":
        return f"{values[0]} + {values[1]}"
    if family in {"add_sub", "add_sub_chain", "balanced", "four_terms"}:
        pieces = [str(values[0])]
        for op, value in zip(spec["ops"], values[1:]):
            pieces.extend([op, str(value)])
        return " ".join(pieces)
    if family == "parentheses_bridge":
        return f"({values[0]} + {values[1]}) - {values[2]}"
    if family == "subtract_group":
        return f"{values[0]} - ({values[1]} + {values[2]})"
    if family == "nested_subtract":
        return f"{values[0]} - ({values[1]} - {values[2]})"
    if family == "double_parentheses":
        return f"({values[0]} - {values[1]}) + ({values[2]} + {values[3]})"
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
        "operators": list(spec.get("ops", [])),
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
    family = "add_two"
    limit = FAMILY_CAPS["level_1"][family]
    emitted = 0
    for a in range(0, 26):
        for b in range(0, 26):
            yield {
                "family": family,
                "values": (a, b),
                "ops": ("+",),
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
    for a in range(4, 41):
        for b in range(0, 31):
            yield {
                "family": "add_sub",
                "values": (a, b),
                "ops": ("-",),
                "canonical_key": f"add_sub:{a}:{b}",
                "case_id": f"add_sub:{a}:{b}",
                "family_id": "add_sub",
            }
            emitted += 1
            if emitted >= budgets["add_sub"]:
                break
        if emitted >= budgets["add_sub"]:
            break

    emitted = 0
    for a in range(0, 21):
        for b in range(0, 21):
            for c in range(0, 16):
                yield {
                    "family": "add_sub_chain",
                    "values": (a, b, c),
                    "ops": ("+", "-"),
                    "canonical_key": f"add_sub_chain:{a}:{b}:{c}",
                    "case_id": f"add_sub_chain:{a}:{b}:{c}",
                    "family_id": "add_sub_chain",
                }
                emitted += 1
                if emitted >= budgets["add_sub_chain"]:
                    return


def iter_level3_specs() -> Iterable[dict]:
    budgets = FAMILY_CAPS["level_3"]
    emitted = 0
    for a in range(5, 36):
        for b in range(0, 21):
            for c in range(0, 21):
                yield {
                    "family": "balanced",
                    "values": (a, b, c),
                    "ops": ("-", "+"),
                    "canonical_key": f"balanced:{a}:{b}:{c}",
                    "case_id": f"balanced:{a}:{b}:{c}",
                    "family_id": "balanced",
                }
                emitted += 1
                if emitted >= budgets["balanced"]:
                    break
            if emitted >= budgets["balanced"]:
                break
        if emitted >= budgets["balanced"]:
            break

    emitted = 0
    for a in range(0, 21):
        for b in range(0, 21):
            for c in range(0, 21):
                yield {
                    "family": "parentheses_bridge",
                    "values": (a, b, c),
                    "ops": ("+", "-"),
                    "canonical_key": f"parentheses_bridge:{a}:{b}:{c}",
                    "case_id": f"parentheses_bridge:{a}:{b}:{c}",
                    "family_id": "parentheses_bridge",
                }
                emitted += 1
                if emitted >= budgets["parentheses_bridge"]:
                    return


def iter_level4_specs() -> Iterable[dict]:
    budgets = FAMILY_CAPS["level_4"]
    emitted = 0
    for a in range(10, 61):
        for b in range(0, 21):
            for c in range(0, 21):
                yield {
                    "family": "subtract_group",
                    "values": (a, b, c),
                    "ops": ("-", "+"),
                    "canonical_key": f"subtract_group:{a}:{b}:{c}",
                    "case_id": f"subtract_group:{a}:{b}:{c}",
                    "family_id": "subtract_group",
                }
                emitted += 1
                if emitted >= budgets["subtract_group"]:
                    break
            if emitted >= budgets["subtract_group"]:
                break
        if emitted >= budgets["subtract_group"]:
            break

    emitted = 0
    for a in range(8, 51):
        for b in range(0, 21):
            for c in range(0, 21):
                yield {
                    "family": "nested_subtract",
                    "values": (a, b, c),
                    "ops": ("-", "-"),
                    "canonical_key": f"nested_subtract:{a}:{b}:{c}",
                    "case_id": f"nested_subtract:{a}:{b}:{c}",
                    "family_id": "nested_subtract",
                }
                emitted += 1
                if emitted >= budgets["nested_subtract"]:
                    return


def iter_level5_specs() -> Iterable[dict]:
    budgets = FAMILY_CAPS["level_5"]
    emitted = 0
    for a in range(10, 31):
        for b in range(0, 16):
            for c in range(0, 16):
                for d in range(0, 16):
                    yield {
                        "family": "four_terms",
                        "values": (a, b, c, d),
                        "ops": ("+", "-", "+"),
                        "canonical_key": f"four_terms:{a}:{b}:{c}:{d}",
                        "case_id": f"four_terms:{a}:{b}:{c}:{d}",
                        "family_id": "four_terms",
                    }
                    emitted += 1
                    if emitted >= budgets["four_terms"]:
                        break
                if emitted >= budgets["four_terms"]:
                    break
            if emitted >= budgets["four_terms"]:
                break
        if emitted >= budgets["four_terms"]:
            break

    emitted = 0
    for a in range(5, 26):
        for b in range(0, 16):
            for c in range(0, 16):
                for d in range(0, 16):
                    yield {
                        "family": "double_parentheses",
                        "values": (a, b, c, d),
                        "ops": ("-", "+", "+"),
                        "canonical_key": f"double_parentheses:{a}:{b}:{c}:{d}",
                        "case_id": f"double_parentheses:{a}:{b}:{c}:{d}",
                        "family_id": "double_parentheses",
                    }
                    emitted += 1
                    if emitted >= budgets["double_parentheses"]:
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
        "level_1": ["adds two nonnegative integers"],
        "level_2": ["adds subtraction and short add/subtract chains"],
        "level_3": ["adds three-term balancing and a single parenthesized group"],
        "level_4": ["adds subtraction of grouped expressions and nested subtraction"],
        "level_5": ["adds four-term expressions and two parenthesized groups while staying bounded"],
    }


