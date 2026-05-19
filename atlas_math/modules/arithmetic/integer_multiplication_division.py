from __future__ import annotations

import itertools
import random
from typing import Iterable

from atlas_math.modules.shared.common import make_sample

MODULE_INFO = {
    "module_id": "arithmetic.integer_multiplication_division",
    "name": "Integer Multiplication and Division",
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
    "level_1": {"times_table": 1200},
    "level_2": {"multiply_signed": 900, "divide_exact": 700},
    "level_3": {"multiply_chain": 900, "mixed_md": 1100},
    "level_4": {"paren_md": 1200, "ratio_mix": 1200},
    "level_5": {"paren_md": 1400, "ratio_mix": 1400},
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
    a = spec["values"]
    if family in {"times_table", "multiply_signed"}:
        return a[0] * a[1]
    if family == "divide_exact":
        return a[0] // a[1]
    if family == "multiply_chain":
        return a[0] * a[1] * a[2]
    if family == "mixed_md":
        return (a[0] * a[1]) // a[2]
    if family == "paren_md":
        return (a[0] * a[1]) // a[2]
    if family == "ratio_mix":
        return (a[0] // a[1]) * a[2]
    raise ValueError(f"Unknown family: {family}")


def _problem_text(spec: dict) -> str:
    family = spec["family"]
    a = spec["values"]
    if family in {"times_table", "multiply_signed"}:
        return f"{a[0]} × {a[1]}"
    if family == "divide_exact":
        return f"{a[0]} ÷ {a[1]}"
    if family == "multiply_chain":
        return f"{a[0]} × {a[1]} × {a[2]}"
    if family == "mixed_md":
        return f"{a[0]} × {a[1]} ÷ {a[2]}"
    if family == "paren_md":
        return f"({a[0]} × {a[1]}) ÷ {a[2]}"
    if family == "ratio_mix":
        return f"({a[0]} ÷ {a[1]}) × {a[2]}"
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
    family = "times_table"
    limit = FAMILY_CAPS["level_1"][family]
    emitted = 0
    for a in range(0, 13):
        for b in range(0, 13):
            yield {"family": family, "values": (a, b), "canonical_key": f"{family}:{a}:{b}", "case_id": f"{family}:{a}:{b}", "family_id": family}
            emitted += 1
            if emitted >= limit:
                return


def iter_level2_specs() -> Iterable[dict]:
    budgets = FAMILY_CAPS["level_2"]
    emitted = 0
    for a in range(-12, 13):
        for b in range(0, 13):
            yield {"family": "multiply_signed", "values": (a, b), "canonical_key": f"multiply_signed:{a}:{b}", "case_id": f"multiply_signed:{a}:{b}", "family_id": "multiply_signed"}
            emitted += 1
            if emitted >= budgets["multiply_signed"]:
                break
        if emitted >= budgets["multiply_signed"]:
            break

    emitted = 0
    for q in range(0, 25):
        for d in (2, 3, 4, 5, 6, 8, 9, 10, 12):
            n = q * d
            yield {"family": "divide_exact", "values": (n, d), "canonical_key": f"divide_exact:{n}:{d}", "case_id": f"divide_exact:{n}:{d}", "family_id": "divide_exact"}
            emitted += 1
            if emitted >= budgets["divide_exact"]:
                return


def iter_level3_specs() -> Iterable[dict]:
    budgets = FAMILY_CAPS["level_3"]
    emitted = 0
    for a in range(-5, 6):
        for b in range(-5, 6):
            for c in range(0, 6):
                yield {"family": "multiply_chain", "values": (a, b, c), "canonical_key": f"multiply_chain:{a}:{b}:{c}", "case_id": f"multiply_chain:{a}:{b}:{c}", "family_id": "multiply_chain"}
                emitted += 1
                if emitted >= budgets["multiply_chain"]:
                    break
            if emitted >= budgets["multiply_chain"]:
                break
        if emitted >= budgets["multiply_chain"]:
            break

    emitted = 0
    for a in range(2, 21):
        for b in range(2, 13):
            for c in (2, 3, 4, 5, 6, 8, 9, 10):
                dividend = b * c
                yield {"family": "mixed_md", "values": (a, dividend, c), "canonical_key": f"mixed_md:{a}:{dividend}:{c}", "case_id": f"mixed_md:{a}:{dividend}:{c}", "family_id": "mixed_md"}
                emitted += 1
                if emitted >= budgets["mixed_md"]:
                    return


def iter_level4_specs() -> Iterable[dict]:
    budgets = FAMILY_CAPS["level_4"]
    emitted = 0
    for a in range(-12, 13):
        for b in range(2, 13):
            for c in (2, 3, 4, 5, 6, 8, 9, 10):
                yield {"family": "paren_md", "values": (a, b * c, c), "canonical_key": f"paren_md:{a}:{b * c}:{c}", "case_id": f"paren_md:{a}:{b * c}:{c}", "family_id": "paren_md"}
                emitted += 1
                if emitted >= budgets["paren_md"]:
                    break
            if emitted >= budgets["paren_md"]:
                break
        if emitted >= budgets["paren_md"]:
            break

    emitted = 0
    for dividend in range(6, 121):
        for divisor in (2, 3, 4, 5, 6, 8, 10):
            if dividend % divisor != 0:
                continue
            for scale in range(-5, 6):
                yield {"family": "ratio_mix", "values": (dividend, divisor, scale), "canonical_key": f"ratio_mix:{dividend}:{divisor}:{scale}", "case_id": f"ratio_mix:{dividend}:{divisor}:{scale}", "family_id": "ratio_mix"}
                emitted += 1
                if emitted >= budgets["ratio_mix"]:
                    return


def iter_level5_specs() -> Iterable[dict]:
    budgets = FAMILY_CAPS["level_5"]
    emitted = 0
    for a in range(-15, 16):
        for b in range(3, 16):
            for c in (2, 3, 4, 5, 6, 8, 9, 10, 12):
                yield {"family": "paren_md", "values": (a, b * c, c), "canonical_key": f"paren_md_l5:{a}:{b * c}:{c}", "case_id": f"paren_md_l5:{a}:{b * c}:{c}", "family_id": "paren_md"}
                emitted += 1
                if emitted >= budgets["paren_md"]:
                    break
            if emitted >= budgets["paren_md"]:
                break
        if emitted >= budgets["paren_md"]:
            break

    emitted = 0
    for dividend in range(12, 181):
        for divisor in (2, 3, 4, 5, 6, 8, 9, 10, 12):
            if dividend % divisor != 0:
                continue
            for scale in range(-8, 9):
                yield {"family": "ratio_mix", "values": (dividend, divisor, scale), "canonical_key": f"ratio_mix_l5:{dividend}:{divisor}:{scale}", "case_id": f"ratio_mix_l5:{dividend}:{divisor}:{scale}", "family_id": "ratio_mix"}
                emitted += 1
                if emitted >= budgets["ratio_mix"]:
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
        "level_1": ["basic multiplication facts"],
        "level_2": ["adds signed multiplication and exact division"],
        "level_3": ["adds three-factor products and mixed multiply/divide expressions"],
        "level_4": ["adds parentheses and multi-step multiply-divide reasoning"],
        "level_5": ["widens signed and exact mixed-operation cases while remaining finite"],
    }


