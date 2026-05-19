from __future__ import annotations

import itertools
import math
import random
from fractions import Fraction
from typing import Iterable

from atlas_math.modules.shared.common import make_sample

MODULE_INFO = {
    "module_id": "arithmetic.fraction_arithmetic_basic",
    "name": "Fraction Arithmetic Basic",
    "topic": "arithmetic",
    "subtopic": "core_arithmetic",
    "difficulty_levels": ["level_1", "level_2", "level_3", "level_4", "level_5"],
    "enabled": True,
}

INSTRUCTIONS = [
    "Compute the fraction expression and simplify the result: {problem}",
    "Work through the fraction arithmetic carefully: {problem}",
    "Evaluate and write the answer in simplest form: {problem}",
    "Solve the fraction problem step by step: {problem}",
]

LEVEL_SPEC_CAPS = {
    "level_1": 1200,
    "level_2": 1600,
    "level_3": 2000,
    "level_4": 2400,
    "level_5": 2800,
}

FAMILY_CAPS = {
    "level_1": {"fraction_add_sub": 1200},
    "level_2": {"fraction_common_denominator": 800, "fraction_integer_mix": 800},
    "level_3": {"fraction_multiply": 1000, "fraction_divide": 1000},
    "level_4": {"fraction_parentheses": 1200, "fraction_mixed_ops": 1200},
    "level_5": {"fraction_nested_mix": 1400, "fraction_complex_ratio": 1400},
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


def _fmt_fraction(value: Fraction) -> str:
    if value.denominator == 1:
        return str(value.numerator)
    sign = "-" if value < 0 else ""
    value = abs(value)
    return f"{sign}{value.numerator}/{value.denominator}"


def _frac(n: int, d: int) -> Fraction:
    return Fraction(n, d)


def _frac_text(n: int, d: int) -> str:
    return f"{n}/{d}"


def _evaluate(spec: dict) -> Fraction:
    family = spec["family"]
    data = spec["data"]
    if family in {"fraction_add_sub", "fraction_common_denominator", "fraction_multiply", "fraction_divide"}:
        left = _frac(*data[0])
        right = _frac(*data[1])
        op = spec["op"]
        if op == "+":
            return left + right
        if op == "-":
            return left - right
        if op == "×":
            return left * right
        if op == "÷":
            return left / right
    if family == "fraction_integer_mix":
        whole = Fraction(data[0], 1)
        part = _frac(*data[1])
        return whole + part if spec["op"] == "+" else whole - part
    if family == "fraction_parentheses":
        left = _frac(*data[0]) + _frac(*data[1])
        right = _frac(*data[2])
        return left * right
    if family == "fraction_mixed_ops":
        left = _frac(*data[0]) * _frac(*data[1])
        right = _frac(*data[2])
        return left + right
    if family == "fraction_nested_mix":
        left = _frac(*data[0]) + _frac(*data[1])
        right = _frac(*data[2]) - _frac(*data[3])
        return left / right
    if family == "fraction_complex_ratio":
        numerator = (_frac(*data[0]) * _frac(*data[1])) + _frac(*data[2])
        denominator = _frac(*data[3])
        return numerator / denominator
    raise ValueError(f"Unknown family: {family}")


def _sample_from_spec(spec: dict, difficulty: str, instruction_idx: int = 0) -> dict:
    problem = spec["display"]
    answer_fraction = _evaluate(spec)
    answer = _fmt_fraction(answer_fraction)
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


def _coprime_pairs(denominators: tuple[int, ...], numerators: range) -> list[tuple[int, int]]:
    pairs: list[tuple[int, int]] = []
    for d in denominators:
        for n in numerators:
            if n <= 0:
                continue
            if math.gcd(n, d) == 1:
                pairs.append((n, d))
    return pairs


def iter_level1_specs() -> Iterable[dict]:
    family = "fraction_add_sub"
    limit = FAMILY_CAPS["level_1"][family]
    emitted = 0
    pairs = _coprime_pairs((2, 3, 4, 5, 6, 8), range(1, 9))
    for left in pairs:
        for right in pairs:
            op = "+" if emitted % 2 == 0 else "-"
            yield _make_spec(
                family,
                f"{_frac_text(*left)} {op} {_frac_text(*right)}",
                f"{left}:{right}:{op}",
                (left, right),
                op,
            )
            emitted += 1
            if emitted >= limit:
                return


def iter_level2_specs() -> Iterable[dict]:
    budgets = FAMILY_CAPS["level_2"]
    pairs = _coprime_pairs((3, 4, 5, 6, 8, 10, 12), range(1, 11))

    emitted = 0
    for d in (3, 4, 5, 6, 8, 10, 12):
        same_den = [(n, d) for n in range(1, d) if math.gcd(n, d) == 1]
        for left in same_den:
            for right in same_den:
                op = "+" if (left[0] + right[0]) % 2 == 0 else "-"
                yield _make_spec(
                    "fraction_common_denominator",
                    f"{_frac_text(*left)} {op} {_frac_text(*right)}",
                    f"{left}:{right}:{op}",
                    (left, right),
                    op,
                )
                emitted += 1
                if emitted >= budgets["fraction_common_denominator"]:
                    break
            if emitted >= budgets["fraction_common_denominator"]:
                break
        if emitted >= budgets["fraction_common_denominator"]:
            break

    emitted = 0
    for whole in range(1, 13):
        for part in pairs:
            op = "+" if (whole + part[0]) % 2 == 0 else "-"
            yield _make_spec(
                "fraction_integer_mix",
                f"{whole} {op} {_frac_text(*part)}",
                f"{whole}:{part}:{op}",
                (whole, part),
                op,
            )
            emitted += 1
            if emitted >= budgets["fraction_integer_mix"]:
                return


def iter_level3_specs() -> Iterable[dict]:
    budgets = FAMILY_CAPS["level_3"]
    pairs = _coprime_pairs((2, 3, 4, 5, 6, 8, 10, 12), range(1, 11))

    emitted = 0
    for left in pairs:
        for right in pairs:
            yield _make_spec(
                "fraction_multiply",
                f"{_frac_text(*left)} × {_frac_text(*right)}",
                f"{left}:{right}",
                (left, right),
                "×",
            )
            emitted += 1
            if emitted >= budgets["fraction_multiply"]:
                break
        if emitted >= budgets["fraction_multiply"]:
            break

    emitted = 0
    nonzero_pairs = [pair for pair in pairs if pair[0] != 0]
    for left in pairs:
        for right in nonzero_pairs:
            yield _make_spec(
                "fraction_divide",
                f"{_frac_text(*left)} ÷ {_frac_text(*right)}",
                f"{left}:{right}",
                (left, right),
                "÷",
            )
            emitted += 1
            if emitted >= budgets["fraction_divide"]:
                return


def iter_level4_specs() -> Iterable[dict]:
    budgets = FAMILY_CAPS["level_4"]
    pairs = _coprime_pairs((2, 3, 4, 5, 6, 8, 10, 12), range(1, 11))

    emitted = 0
    for a in pairs:
        for b in pairs:
            for c in pairs:
                yield _make_spec(
                    "fraction_parentheses",
                    f"({_frac_text(*a)} + {_frac_text(*b)}) × {_frac_text(*c)}",
                    f"{a}:{b}:{c}",
                    (a, b, c),
                )
                emitted += 1
                if emitted >= budgets["fraction_parentheses"]:
                    break
            if emitted >= budgets["fraction_parentheses"]:
                break
        if emitted >= budgets["fraction_parentheses"]:
            break

    emitted = 0
    for a in pairs:
        for b in pairs:
            for c in pairs:
                yield _make_spec(
                    "fraction_mixed_ops",
                    f"({_frac_text(*a)} × {_frac_text(*b)}) + {_frac_text(*c)}",
                    f"{a}:{b}:{c}",
                    (a, b, c),
                )
                emitted += 1
                if emitted >= budgets["fraction_mixed_ops"]:
                    return


def iter_level5_specs() -> Iterable[dict]:
    budgets = FAMILY_CAPS["level_5"]
    pairs = _coprime_pairs((2, 3, 4, 5, 6, 8, 10, 12), range(1, 11))

    emitted = 0
    for a in pairs:
        for b in pairs:
            for c in pairs:
                for d in pairs:
                    right = _frac(*c) - _frac(*d)
                    if right == 0:
                        continue
                    yield _make_spec(
                        "fraction_nested_mix",
                        f"({_frac_text(*a)} + {_frac_text(*b)}) ÷ ({_frac_text(*c)} - {_frac_text(*d)})",
                        f"{a}:{b}:{c}:{d}",
                        (a, b, c, d),
                    )
                    emitted += 1
                    if emitted >= budgets["fraction_nested_mix"]:
                        break
                if emitted >= budgets["fraction_nested_mix"]:
                    break
            if emitted >= budgets["fraction_nested_mix"]:
                break
        if emitted >= budgets["fraction_nested_mix"]:
            break

    emitted = 0
    for a in pairs:
        for b in pairs:
            for c in pairs:
                for d in pairs:
                    yield _make_spec(
                        "fraction_complex_ratio",
                        f"(({_frac_text(*a)} × {_frac_text(*b)}) + {_frac_text(*c)}) ÷ {_frac_text(*d)}",
                        f"{a}:{b}:{c}:{d}",
                        (a, b, c, d),
                    )
                    emitted += 1
                    if emitted >= budgets["fraction_complex_ratio"]:
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
        "level_1": ["adds and subtracts two proper fractions"],
        "level_2": ["adds common denominators and mixes fractions with whole numbers"],
        "level_3": ["adds multiplication and division of fractions"],
        "level_4": ["adds grouped fraction expressions with two operations"],
        "level_5": ["adds nested multi-step fraction expressions while keeping all cases finite and exact"],
    }


