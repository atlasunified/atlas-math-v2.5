from __future__ import annotations

import itertools
import random
from typing import Iterable

from atlas_math.modules.shared.common import make_sample

MODULE_INFO = {
    "module_id": "arithmetic.signed_number_arithmetic",
    "name": "Signed Number Arithmetic",
    "topic": "arithmetic",
    "subtopic": "core_arithmetic",
    "difficulty_levels": ["level_1", "level_2", "level_3", "level_4", "level_5"],
    "enabled": True,
}

INSTRUCTIONS = [
    "Evaluate the arithmetic expression with signed numbers: {problem}",
    "Compute carefully, paying attention to signs: {problem}",
    "Simplify the expression step by step: {problem}",
    "Find the value of the signed-number expression: {problem}",
]

LEVEL_SPEC_CAPS = {
    "level_1": 1200,
    "level_2": 1600,
    "level_3": 2000,
    "level_4": 2400,
    "level_5": 2800,
}

FAMILY_CAPS = {
    "level_1": {"signed_add_sub": 1200},
    "level_2": {"signed_multiply": 800, "signed_chain": 800},
    "level_3": {"signed_exact_division": 1000, "signed_parentheses": 1000},
    "level_4": {"signed_mixed_ops": 1200, "signed_distributed_difference": 1200},
    "level_5": {"signed_nested_mix": 1400, "signed_division_mix": 1400},
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


def _signed_text(value: int) -> str:
    return str(value) if value < 0 else str(value)


def _wrap(value: int) -> str:
    return f"({value})" if value < 0 else str(value)


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
    return {
        "family": family,
        "display": display,
        "expression": expression,
        "canonical_key": f"{family}:{tag}",
        "case_id": f"{family}:{tag}",
        "family_id": family,
    }


def iter_level1_specs() -> Iterable[dict]:
    family = "signed_add_sub"
    limit = FAMILY_CAPS["level_1"][family]
    emitted = 0
    nums = range(-15, 16)
    for a in nums:
        for b in nums:
            if b == 0:
                continue
            yield _make_spec(family, f"{_signed_text(a)} + {_wrap(b)}", f"{a}+({b})", f"{a}:{b}:add")
            emitted += 1
            if emitted >= limit:
                return


def iter_level2_specs() -> Iterable[dict]:
    budgets = FAMILY_CAPS["level_2"]
    nums = range(-12, 13)

    emitted = 0
    for a in nums:
        for b in nums:
            if a == 0 or b == 0:
                continue
            yield _make_spec("signed_multiply", f"{_wrap(a)} × {_wrap(b)}", f"({a})*({b})", f"{a}:{b}")
            emitted += 1
            if emitted >= budgets["signed_multiply"]:
                break
        if emitted >= budgets["signed_multiply"]:
            break

    emitted = 0
    for a in nums:
        for b in nums:
            for c in nums:
                if b == 0 and c == 0:
                    continue
                yield _make_spec(
                    "signed_chain",
                    f"{_signed_text(a)} - {_wrap(b)} + {_wrap(c)}",
                    f"{a}-({b})+({c})",
                    f"{a}:{b}:{c}",
                )
                emitted += 1
                if emitted >= budgets["signed_chain"]:
                    return


def iter_level3_specs() -> Iterable[dict]:
    budgets = FAMILY_CAPS["level_3"]
    divisors = (-10, -9, -8, -6, -5, -4, -3, -2, 2, 3, 4, 5, 6, 8, 9, 10)

    emitted = 0
    for q in range(-12, 13):
        for d in divisors:
            n = q * d
            yield _make_spec(
                "signed_exact_division",
                f"{_wrap(n)} ÷ {_wrap(d)}",
                f"({n})//({d})",
                f"{n}:{d}:{q}",
            )
            emitted += 1
            if emitted >= budgets["signed_exact_division"]:
                break
        if emitted >= budgets["signed_exact_division"]:
            break

    emitted = 0
    for a in range(-10, 11):
        for b in range(-10, 11):
            for c in range(-10, 11):
                yield _make_spec(
                    "signed_parentheses",
                    f"({_signed_text(a)} + {_wrap(b)}) - {_wrap(c)}",
                    f"({a}+({b}))-({c})",
                    f"{a}:{b}:{c}",
                )
                emitted += 1
                if emitted >= budgets["signed_parentheses"]:
                    return


def iter_level4_specs() -> Iterable[dict]:
    budgets = FAMILY_CAPS["level_4"]
    nums = range(-8, 9)

    emitted = 0
    for a in nums:
        for b in nums:
            for c in nums:
                for d in nums:
                    if c == 0:
                        continue
                    yield _make_spec(
                        "signed_mixed_ops",
                        f"{_wrap(a)} + ({_wrap(b)} × {_wrap(c)}) - {_wrap(d)}",
                        f"({a})+(({b})*({c}))-({d})",
                        f"{a}:{b}:{c}:{d}",
                    )
                    emitted += 1
                    if emitted >= budgets["signed_mixed_ops"]:
                        break
                if emitted >= budgets["signed_mixed_ops"]:
                    break
            if emitted >= budgets["signed_mixed_ops"]:
                break
        if emitted >= budgets["signed_mixed_ops"]:
            break

    emitted = 0
    for a in nums:
        for b in nums:
            for c in nums:
                for d in nums:
                    yield _make_spec(
                        "signed_distributed_difference",
                        f"({_wrap(a)} - {_wrap(b)}) × {_wrap(c)} + {_wrap(d)}",
                        f"(({a})-({b}))*({c})+({d})",
                        f"{a}:{b}:{c}:{d}",
                    )
                    emitted += 1
                    if emitted >= budgets["signed_distributed_difference"]:
                        return


def iter_level5_specs() -> Iterable[dict]:
    budgets = FAMILY_CAPS["level_5"]
    divisors = (-8, -6, -4, -3, -2, 2, 3, 4, 6, 8)

    emitted = 0
    for a in range(-8, 9):
        for b in range(-8, 9):
            for c in range(-6, 7):
                if c == 0:
                    continue
                for d in range(-8, 9):
                    yield _make_spec(
                        "signed_nested_mix",
                        f"(({_wrap(a)} + {_wrap(b)}) - ({_wrap(c)} × {_wrap(d)}))",
                        f"((({a})+({b}))-(({c})*({d})))",
                        f"{a}:{b}:{c}:{d}",
                    )
                    emitted += 1
                    if emitted >= budgets["signed_nested_mix"]:
                        break
                if emitted >= budgets["signed_nested_mix"]:
                    break
            if emitted >= budgets["signed_nested_mix"]:
                break
        if emitted >= budgets["signed_nested_mix"]:
            break

    emitted = 0
    for q in range(-10, 11):
        for d in divisors:
            for a in range(-8, 9):
                for b in range(-8, 9):
                    n = q * d
                    yield _make_spec(
                        "signed_division_mix",
                        f"(({_wrap(a)} - {_wrap(b)}) + ({_wrap(n)} ÷ {_wrap(d)}))",
                        f"((({a})-({b}))+(({n})//({d})))",
                        f"{a}:{b}:{n}:{d}:{q}",
                    )
                    emitted += 1
                    if emitted >= budgets["signed_division_mix"]:
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
        "level_1": ["adds and subtracts signed integers"],
        "level_2": ["adds signed multiplication and longer sign-sensitive chains"],
        "level_3": ["adds exact signed division and grouped expressions"],
        "level_4": ["adds mixed operations with parentheses and sign distribution"],
        "level_5": ["adds nested grouped expressions that combine multiplication and exact division"],
    }


