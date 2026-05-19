from __future__ import annotations

import itertools
import math
import random
from fractions import Fraction
from typing import Iterable

from atlas_math.modules.shared.common import make_sample

MODULE_INFO = {
    "module_id": "arithmetic.fraction_arithmetic_mixed",
    "name": "Fraction Arithmetic Mixed",
    "topic": "arithmetic",
    "subtopic": "core_arithmetic",
    "difficulty_levels": ["level_1", "level_2", "level_3", "level_4", "level_5"],
    "enabled": True,
}

INSTRUCTIONS = [
    "Compute the mixed-number expression and simplify the result: {problem}",
    "Evaluate the fraction expression carefully: {problem}",
    "Work through the mixed fractions and give the simplified answer: {problem}",
    "Solve the mixed-number arithmetic problem: {problem}",
]

LEVEL_SPEC_CAPS = {
    "level_1": 1200,
    "level_2": 1600,
    "level_3": 2000,
    "level_4": 2400,
    "level_5": 2800,
}

FAMILY_CAPS = {
    "level_1": {"mixed_add_sub": 1200},
    "level_2": {"mixed_to_improper": 800, "mixed_with_integer": 800},
    "level_3": {"mixed_multiply": 1000, "mixed_divide": 1000},
    "level_4": {"mixed_parentheses": 1200, "mixed_cross_operation": 1200},
    "level_5": {"mixed_nested": 1400, "mixed_ratio": 1400},
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


def _mixed_text(whole: int, num: int, den: int) -> str:
    return f"{whole} {num}/{den}"


def _fraction_text(value: Fraction) -> str:
    if value.denominator == 1:
        return str(value.numerator)
    sign = "-" if value < 0 else ""
    value = abs(value)
    whole = value.numerator // value.denominator
    remainder = value.numerator % value.denominator
    if whole and remainder:
        return f"{sign}{whole} {remainder}/{value.denominator}"
    if whole:
        return f"{sign}{whole}"
    return f"{sign}{value.numerator}/{value.denominator}"


def _mixed_to_fraction(whole: int, num: int, den: int) -> Fraction:
    return Fraction(whole * den + num, den)


def _make_spec(family: str, display: str, tag: str, data: tuple, op: str | None = None) -> dict:
    spec = {
        "family": family,
        "display": display,
        "data": data,
        "canonical_key": f"{family}:{tag}",
        "case_id": f"{family}:{tag}",
        "family_id": family,
    }
    if op is not None:
        spec["op"] = op
    return spec


def _evaluate(spec: dict) -> Fraction:
    family = spec["family"]
    data = spec["data"]
    if family in {"mixed_add_sub", "mixed_to_improper", "mixed_multiply", "mixed_divide"}:
        left = _mixed_to_fraction(*data[0])
        right = _mixed_to_fraction(*data[1])
        op = spec["op"]
        if op == "+":
            return left + right
        if op == "-":
            return left - right
        if op == "×":
            return left * right
        if op == "÷":
            return left / right
    if family == "mixed_with_integer":
        left = _mixed_to_fraction(*data[0])
        whole = Fraction(data[1], 1)
        return left + whole if spec["op"] == "+" else left - whole
    if family == "mixed_parentheses":
        left = _mixed_to_fraction(*data[0]) + _mixed_to_fraction(*data[1])
        right = _mixed_to_fraction(*data[2])
        return left * right
    if family == "mixed_cross_operation":
        left = _mixed_to_fraction(*data[0]) * _mixed_to_fraction(*data[1])
        right = _mixed_to_fraction(*data[2])
        return left - right
    if family == "mixed_nested":
        left = _mixed_to_fraction(*data[0]) - _mixed_to_fraction(*data[1])
        right = _mixed_to_fraction(*data[2]) + _mixed_to_fraction(*data[3])
        return left / right
    if family == "mixed_ratio":
        numerator = _mixed_to_fraction(*data[0]) + _mixed_to_fraction(*data[1])
        denominator = _mixed_to_fraction(*data[2])
        return numerator / denominator
    raise ValueError(f"Unknown family: {family}")


def _sample_from_spec(spec: dict, difficulty: str, instruction_idx: int = 0) -> dict:
    problem = spec["display"]
    answer = _fraction_text(_evaluate(spec))
    metadata = {
        "family": spec["family"],
        "level_number": _level_num(difficulty),
        "structured": True,
        "canonical_key": spec["canonical_key"],
        "case_id": spec["case_id"],
        "family_id": spec["family_id"],
        "template_id": spec["family"],
        "final_answer": answer,
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


def _mixed_pool(wholes: range, denominators: tuple[int, ...], num_limit: int) -> list[tuple[int, int, int]]:
    out: list[tuple[int, int, int]] = []
    for whole in wholes:
        for den in denominators:
            for num in range(1, min(den, num_limit + 1)):
                if math.gcd(num, den) != 1:
                    continue
                out.append((whole, num, den))
    return out


def iter_level1_specs() -> Iterable[dict]:
    family = "mixed_add_sub"
    limit = FAMILY_CAPS["level_1"][family]
    emitted = 0
    pool = _mixed_pool(range(1, 6), (2, 3, 4, 5, 6, 8), 7)
    for left in pool:
        for right in pool:
            op = "+" if emitted % 2 == 0 else "-"
            yield _make_spec(
                family,
                f"{_mixed_text(*left)} {op} { _mixed_text(*right)}",
                f"{left}:{right}:{op}",
                (left, right),
                op,
            )
            emitted += 1
            if emitted >= limit:
                return


def iter_level2_specs() -> Iterable[dict]:
    budgets = FAMILY_CAPS["level_2"]
    pool = _mixed_pool(range(1, 7), (2, 3, 4, 5, 6, 8), 7)

    emitted = 0
    for left in pool:
        for right in pool:
            op = "+" if (left[0] + right[0] + left[1]) % 2 == 0 else "-"
            yield _make_spec(
                "mixed_to_improper",
                f"{_mixed_text(*left)} {op} {_mixed_text(*right)}",
                f"{left}:{right}:{op}",
                (left, right),
                op,
            )
            emitted += 1
            if emitted >= budgets["mixed_to_improper"]:
                break
        if emitted >= budgets["mixed_to_improper"]:
            break

    emitted = 0
    for mixed in pool:
        for whole in range(1, 16):
            op = "+" if (whole + mixed[0] + mixed[1]) % 2 == 0 else "-"
            yield _make_spec(
                "mixed_with_integer",
                f"{_mixed_text(*mixed)} {op} {whole}",
                f"{mixed}:{whole}:{op}",
                (mixed, whole),
                op,
            )
            emitted += 1
            if emitted >= budgets["mixed_with_integer"]:
                return


def iter_level3_specs() -> Iterable[dict]:
    budgets = FAMILY_CAPS["level_3"]
    pool = _mixed_pool(range(1, 7), (2, 3, 4, 5, 6, 8, 10), 9)

    emitted = 0
    for left in pool:
        for right in pool:
            yield _make_spec(
                "mixed_multiply",
                f"{_mixed_text(*left)} × {_mixed_text(*right)}",
                f"{left}:{right}",
                (left, right),
                "×",
            )
            emitted += 1
            if emitted >= budgets["mixed_multiply"]:
                break
        if emitted >= budgets["mixed_multiply"]:
            break

    emitted = 0
    for left in pool:
        for right in pool:
            if _mixed_to_fraction(*right) == 0:
                continue
            yield _make_spec(
                "mixed_divide",
                f"{_mixed_text(*left)} ÷ {_mixed_text(*right)}",
                f"{left}:{right}",
                (left, right),
                "÷",
            )
            emitted += 1
            if emitted >= budgets["mixed_divide"]:
                return


def iter_level4_specs() -> Iterable[dict]:
    budgets = FAMILY_CAPS["level_4"]
    pool = _mixed_pool(range(1, 6), (2, 3, 4, 5, 6, 8), 7)

    emitted = 0
    for a in pool:
        for b in pool:
            for c in pool:
                yield _make_spec(
                    "mixed_parentheses",
                    f"({_mixed_text(*a)} + {_mixed_text(*b)}) × {_mixed_text(*c)}",
                    f"{a}:{b}:{c}",
                    (a, b, c),
                )
                emitted += 1
                if emitted >= budgets["mixed_parentheses"]:
                    break
            if emitted >= budgets["mixed_parentheses"]:
                break
        if emitted >= budgets["mixed_parentheses"]:
            break

    emitted = 0
    for a in pool:
        for b in pool:
            for c in pool:
                yield _make_spec(
                    "mixed_cross_operation",
                    f"({_mixed_text(*a)} × {_mixed_text(*b)}) - {_mixed_text(*c)}",
                    f"{a}:{b}:{c}",
                    (a, b, c),
                )
                emitted += 1
                if emitted >= budgets["mixed_cross_operation"]:
                    return


def iter_level5_specs() -> Iterable[dict]:
    budgets = FAMILY_CAPS["level_5"]
    pool = _mixed_pool(range(1, 6), (2, 3, 4, 5, 6, 8, 10), 9)

    emitted = 0
    for a in pool:
        for b in pool:
            for c in pool:
                for d in pool:
                    if _mixed_to_fraction(*c) + _mixed_to_fraction(*d) == 0:
                        continue
                    yield _make_spec(
                        "mixed_nested",
                        f"({_mixed_text(*a)} - {_mixed_text(*b)}) ÷ ({_mixed_text(*c)} + {_mixed_text(*d)})",
                        f"{a}:{b}:{c}:{d}",
                        (a, b, c, d),
                    )
                    emitted += 1
                    if emitted >= budgets["mixed_nested"]:
                        break
                if emitted >= budgets["mixed_nested"]:
                    break
            if emitted >= budgets["mixed_nested"]:
                break
        if emitted >= budgets["mixed_nested"]:
            break

    emitted = 0
    for a in pool:
        for b in pool:
            for c in pool:
                if _mixed_to_fraction(*c) == 0:
                    continue
                yield _make_spec(
                    "mixed_ratio",
                    f"({_mixed_text(*a)} + {_mixed_text(*b)}) ÷ {_mixed_text(*c)}",
                    f"{a}:{b}:{c}",
                    (a, b, c),
                )
                emitted += 1
                if emitted >= budgets["mixed_ratio"]:
                    return


def _iter_specs(difficulty: str) -> Iterable[dict]:
    level = _level_num(difficulty)
    emitted = 0
    for lvl in range(1, level + 1):
        for spec in _take(globals()[f"iter_level{lvl}_specs"](), LEVEL_SPEC_CAPS[_difficulty_name(lvl)]):
            yield spec
            emitted += 1
            if emitted >= LEVEL_SPEC_CAPS.get(difficulty, LEVEL_SPEC_CAPS["level_5"]):
                return


def estimate_capacity(difficulty: str = "level_1"):
    return CAPACITY_HINTS.get(difficulty, {"value": None, "quality": "unknown"})


def generate(count: int = 10, difficulty: str = "level_1", seed=None) -> list[dict]:
    prefix = min(max(int(count) * MAX_GENERATE_MULTIPLIER, 256), MAX_SPEC_PREFIX, LEVEL_SPEC_CAPS.get(difficulty, 2000))
    pool = list(itertools.islice(_iter_specs(difficulty), 0, prefix))
    if not pool:
        return []
    rng = random.Random(_stable_seed(seed, difficulty, "generate"))
    rng.shuffle(pool)
    out: list[dict] = []
    seen: set[str] = set()
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
    pool_cap = min(LEVEL_SPEC_CAPS.get(difficulty, 2000), MAX_SPEC_PREFIX)
    pool = list(itertools.islice(_iter_specs(difficulty), 0, pool_cap))
    rng = random.Random(_stable_seed(seed, difficulty, offset, stride, "generate_unique"))
    rng.shuffle(pool)
    out: list[dict] = []
    seen: set[str] = set()
    start = max(0, int(offset))
    step = max(1, int(stride))
    for local_idx, spec in enumerate(pool[start::step]):
        sample = _sample_from_spec(spec, difficulty, instruction_idx=start + local_idx * step)
        key = sample.get("input", "")
        if key in seen:
            continue
        seen.add(key)
        out.append(sample)
        if len(out) >= count:
            break
    return out


def iter_samples(difficulty: str = "level_1", seed=None):
    max_items = min(LEVEL_SPEC_CAPS.get(difficulty, 2000), MAX_ITER_SAMPLES)
    pool = list(itertools.islice(_iter_specs(difficulty), 0, max_items))
    rng = random.Random(_stable_seed(seed, difficulty, "iter_samples"))
    rng.shuffle(pool)
    seen: set[str] = set()
    for idx, spec in enumerate(pool):
        sample = _sample_from_spec(spec, difficulty, instruction_idx=idx)
        key = sample.get("input", "")
        if key in seen:
            continue
        seen.add(key)
        yield sample


def curriculum() -> dict:
    return {
        "level_1": ["add and subtract mixed numbers with small denominators"],
        "level_2": ["extends level 1 with more mixed pairs and mixed-number plus integer combinations"],
        "level_3": ["adds multiplication and division of mixed numbers"],
        "level_4": ["adds parenthesized and multi-step mixed-number expressions"],
        "level_5": ["adds nested division and ratio-style mixed-number expressions while staying capped"],
    }


