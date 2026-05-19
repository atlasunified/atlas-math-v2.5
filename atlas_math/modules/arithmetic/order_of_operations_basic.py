from __future__ import annotations

import itertools
import random
from typing import Iterable

from atlas_math.modules.shared.common import make_sample

MODULE_INFO = {
    "module_id": "arithmetic.order_of_operations_basic",
    "name": "Order of Operations Basic",
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
    "level_1": {"multiply_then_add": 1200},
    "level_2": {"grouped_add_then_multiply": 800, "mixed_three_ops": 800},
    "level_3": {"multiply_divide_then_add": 1000, "double_grouping": 1000},
    "level_4": {"grouped_then_divide": 1200, "difference_times_value": 1200},
    "level_5": {"outer_division": 1400, "two_group_mix": 1400},
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
    return int(eval(spec["expression"], {"__builtins__": {}}, {}))


def _sample_from_spec(spec: dict, difficulty: str, instruction_idx: int = 0) -> dict:
    problem = spec["display"]
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
        "expression": spec["expression"],
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


def _make_spec(family: str, display: str, expression: str, tag: str) -> dict:
    return {"family": family, "display": display, "expression": expression, "canonical_key": f"{family}:{tag}", "case_id": f"{family}:{tag}", "family_id": family}


def iter_level1_specs() -> Iterable[dict]:
    family = "multiply_then_add"
    limit = FAMILY_CAPS["level_1"][family]
    emitted = 0
    for a in range(0, 13):
        for b in range(0, 13):
            for c in range(0, 21):
                yield _make_spec(family, f"{a} + {b} × {c}", f"{a}+{b}*{c}", f"{a}:{b}:{c}")
                emitted += 1
                if emitted >= limit:
                    return


def iter_level2_specs() -> Iterable[dict]:
    budgets = FAMILY_CAPS["level_2"]
    emitted = 0
    for a in range(0, 13):
        for b in range(0, 13):
            for c in range(0, 13):
                yield _make_spec("grouped_add_then_multiply", f"({a} + {b}) × {c}", f"({a}+{b})*{c}", f"{a}:{b}:{c}")
                emitted += 1
                if emitted >= budgets["grouped_add_then_multiply"]:
                    break
            if emitted >= budgets["grouped_add_then_multiply"]:
                break
        if emitted >= budgets["grouped_add_then_multiply"]:
            break

    emitted = 0
    for a in range(0, 13):
        for b in range(0, 13):
            for c in range(1, 13):
                yield _make_spec("mixed_three_ops", f"{a} + {b} × {c} - {c}", f"{a}+{b}*{c}-{c}", f"{a}:{b}:{c}")
                emitted += 1
                if emitted >= budgets["mixed_three_ops"]:
                    return


def iter_level3_specs() -> Iterable[dict]:
    budgets = FAMILY_CAPS["level_3"]
    emitted = 0
    for a in range(0, 21):
        for b in range(2, 13):
            for c in (2, 3, 4, 5, 6, 8, 9, 10):
                yield _make_spec("multiply_divide_then_add", f"{a} + {b * c} ÷ {c}", f"{a}+({b * c}//{c})", f"{a}:{b * c}:{c}")
                emitted += 1
                if emitted >= budgets["multiply_divide_then_add"]:
                    break
            if emitted >= budgets["multiply_divide_then_add"]:
                break
        if emitted >= budgets["multiply_divide_then_add"]:
            break

    emitted = 0
    for a in range(0, 16):
        for b in range(0, 11):
            for c in range(0, 11):
                for d in range(0, 11):
                    yield _make_spec("double_grouping", f"({a} + {b}) × ({c} + {d})", f"({a}+{b})*({c}+{d})", f"{a}:{b}:{c}:{d}")
                    emitted += 1
                    if emitted >= budgets["double_grouping"]:
                        return


def iter_level4_specs() -> Iterable[dict]:
    budgets = FAMILY_CAPS["level_4"]
    emitted = 0
    for a in range(1, 16):
        for b in range(0, 13):
            for c in (2, 3, 4, 5, 6, 8, 9, 10):
                for d in range(0, 13):
                    yield _make_spec("grouped_then_divide", f"({a} + {b}) × {c} - {d * c} ÷ {c}", f"({a}+{b})*{c}-({d * c}//{c})", f"{a}:{b}:{c}:{d}")
                    emitted += 1
                    if emitted >= budgets["grouped_then_divide"]:
                        break
                if emitted >= budgets["grouped_then_divide"]:
                    break
            if emitted >= budgets["grouped_then_divide"]:
                break
        if emitted >= budgets["grouped_then_divide"]:
            break

    emitted = 0
    for a in range(0, 13):
        for b in range(0, 13):
            for c in range(0, 13):
                for d in range(1, 13):
                    yield _make_spec("difference_times_value", f"{a} + ({b} - {c}) × {d}", f"{a}+({b}-{c})*{d}", f"{a}:{b}:{c}:{d}")
                    emitted += 1
                    if emitted >= budgets["difference_times_value"]:
                        return


def iter_level5_specs() -> Iterable[dict]:
    budgets = FAMILY_CAPS["level_5"]
    emitted = 0
    for a in range(0, 13):
        for b in range(1, 13):
            for c in (2, 3, 4, 5, 6, 8, 9, 10, 12):
                for d in range(0, 13):
                    yield _make_spec("outer_division", f"(({a} + {b}) × {c} - {d * c}) ÷ {c}", f"((({a}+{b})*{c})-({d * c}))//{c}", f"{a}:{b}:{c}:{d}")
                    emitted += 1
                    if emitted >= budgets["outer_division"]:
                        break
                if emitted >= budgets["outer_division"]:
                    break
            if emitted >= budgets["outer_division"]:
                break
        if emitted >= budgets["outer_division"]:
            break

    emitted = 0
    for a in range(0, 11):
        for b in range(0, 11):
            for c in range(0, 11):
                for d in range(0, 11):
                    for e in range(1, 11):
                        yield _make_spec("two_group_mix", f"({a} + {b} × {c}) - ({d} + {e})", f"({a}+{b}*{c})-({d}+{e})", f"{a}:{b}:{c}:{d}:{e}")
                        emitted += 1
                        if emitted >= budgets["two_group_mix"]:
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
        "level_1": ["multiplies before adding with no parentheses"],
        "level_2": ["contrasts default precedence with one explicit grouped sum"],
        "level_3": ["adds exact division and two grouped subexpressions"],
        "level_4": ["adds grouped expressions combined with division or signed differences"],
        "level_5": ["adds outer division and multiple grouped parts in one bounded expression"],
    }


