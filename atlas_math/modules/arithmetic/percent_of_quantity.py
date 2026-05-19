from __future__ import annotations

import itertools
import random
from decimal import Decimal, getcontext
from typing import Iterable

from atlas_math.modules.shared.common import make_sample

getcontext().prec = 28

MODULE_INFO = {
    "module_id": "arithmetic.percent_of_quantity",
    "name": "Percent of Quantity",
    "topic": "arithmetic",
    "subtopic": "core_arithmetic",
    "difficulty_levels": ["level_1", "level_2", "level_3", "level_4", "level_5"],
    "enabled": True,
}

INSTRUCTIONS = [
    "Find the requested percent of the quantity: {problem}",
    "Compute the percentage value carefully: {problem}",
    "Evaluate the percent expression: {problem}",
    "Work out the percent-of-quantity problem: {problem}",
]

LEVEL_SPEC_CAPS = {
    "level_1": 1200,
    "level_2": 1600,
    "level_3": 2000,
    "level_4": 2400,
    "level_5": 2800,
}

FAMILY_CAPS = {
    "level_1": {"whole_percent": 1200},
    "level_2": {"fractional_percent": 800, "decimal_quantity": 800},
    "level_3": {"percent_increase_decrease": 1000, "reverse_percent": 1000},
    "level_4": {"percent_of_sum": 1200, "stacked_percentage": 1200},
    "level_5": {"nested_percent": 1400, "discount_tax_combo": 1400},
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


def _dec(value: str | int) -> Decimal:
    return Decimal(str(value))


def _fmt_decimal(value: Decimal) -> str:
    text = format(value.normalize(), 'f')
    if '.' in text:
        text = text.rstrip('0').rstrip('.')
    if text == '-0':
        text = '0'
    return text


def _percent_value(percent: str | int, quantity: str | int) -> Decimal:
    return _dec(percent) / Decimal(100) * _dec(quantity)


def _make_spec(family: str, display: str, tag: str, data: tuple) -> dict:
    return {
        "family": family,
        "display": display,
        "data": data,
        "canonical_key": f"{family}:{tag}",
        "case_id": f"{family}:{tag}",
        "family_id": family,
    }


def _evaluate(spec: dict) -> Decimal:
    family = spec["family"]
    data = spec["data"]
    if family in {"whole_percent", "fractional_percent", "decimal_quantity"}:
        return _percent_value(data[0], data[1])
    if family == "percent_increase_decrease":
        base = _dec(data[1])
        amount = _percent_value(data[0], data[1])
        return base + amount if data[2] == "increase" else base - amount
    if family == "reverse_percent":
        final = _dec(data[1])
        percent_remaining = Decimal(100) - _dec(data[0])
        return final / (percent_remaining / Decimal(100))
    if family == "percent_of_sum":
        total = _dec(data[1]) + _dec(data[2])
        return _dec(data[0]) / Decimal(100) * total
    if family == "stacked_percentage":
        first = _percent_value(data[0], data[2])
        return _dec(data[1]) / Decimal(100) * first
    if family == "nested_percent":
        inner = _percent_value(data[1], data[2])
        return _dec(data[0]) / Decimal(100) * inner
    if family == "discount_tax_combo":
        price = _dec(data[2])
        after_discount = price - _percent_value(data[0], data[2])
        return after_discount + (_dec(data[1]) / Decimal(100) * after_discount)
    raise ValueError(f"Unknown family: {family}")


def _sample_from_spec(spec: dict, difficulty: str, instruction_idx: int = 0) -> dict:
    problem = spec["display"]
    answer = _fmt_decimal(_evaluate(spec))
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


def iter_level1_specs() -> Iterable[dict]:
    family = "whole_percent"
    limit = FAMILY_CAPS["level_1"][family]
    emitted = 0
    percents = [5, 10, 20, 25, 50, 75]
    quantities = range(4, 201, 4)
    for p in percents:
        for q in quantities:
            yield _make_spec(family, f"What is {p}% of {q}?", f"{p}:{q}", (p, q))
            emitted += 1
            if emitted >= limit:
                return


def iter_level2_specs() -> Iterable[dict]:
    budgets = FAMILY_CAPS["level_2"]

    emitted = 0
    percents = ["12.5", "37.5", "62.5", "150"]
    quantities = range(8, 201, 8)
    for p in percents:
        for q in quantities:
            yield _make_spec("fractional_percent", f"What is {p}% of {q}?", f"{p}:{q}", (p, q))
            emitted += 1
            if emitted >= budgets["fractional_percent"]:
                break
        if emitted >= budgets["fractional_percent"]:
            break

    emitted = 0
    percents = [5, 10, 12.5, 20, 25, 40]
    quantities = [f"{whole}.{digit}" for whole in range(1, 26) for digit in (0, 2, 4, 5, 8)]
    for p in percents:
        for q in quantities:
            yield _make_spec("decimal_quantity", f"What is {p}% of {q}?", f"{p}:{q}", (p, q))
            emitted += 1
            if emitted >= budgets["decimal_quantity"]:
                return


def iter_level3_specs() -> Iterable[dict]:
    budgets = FAMILY_CAPS["level_3"]

    emitted = 0
    changes = [5, 10, 12.5, 20, 25, 40]
    amounts = range(20, 401, 5)
    for p in changes:
        for amount in amounts:
            mode = "increase" if emitted % 2 == 0 else "decrease"
            verb = "increased" if mode == "increase" else "decreased"
            yield _make_spec(
                "percent_increase_decrease",
                f"A value of {amount} is {verb} by {p}%. What is the new value?",
                f"{p}:{amount}:{mode}",
                (p, amount, mode),
            )
            emitted += 1
            if emitted >= budgets["percent_increase_decrease"]:
                break
        if emitted >= budgets["percent_increase_decrease"]:
            break

    emitted = 0
    discounts = [5, 10, 20, 25, 40]
    finals = range(18, 361, 3)
    for p in discounts:
        for final in finals:
            yield _make_spec(
                "reverse_percent",
                f"After a {p}% discount, an item costs {final}. What was the original price?",
                f"{p}:{final}",
                (p, final),
            )
            emitted += 1
            if emitted >= budgets["reverse_percent"]:
                return


def iter_level4_specs() -> Iterable[dict]:
    budgets = FAMILY_CAPS["level_4"]

    emitted = 0
    percents = [10, 12.5, 20, 25, 40, 60]
    a_vals = range(10, 161, 5)
    b_vals = range(15, 176, 5)
    for p in percents:
        for a in a_vals:
            for b in b_vals:
                yield _make_spec(
                    "percent_of_sum",
                    f"What is {p}% of ({a} + {b})?",
                    f"{p}:{a}:{b}",
                    (p, a, b),
                )
                emitted += 1
                if emitted >= budgets["percent_of_sum"]:
                    break
            if emitted >= budgets["percent_of_sum"]:
                break
        if emitted >= budgets["percent_of_sum"]:
            break

    emitted = 0
    p1_vals = [10, 20, 25, 40, 50]
    p2_vals = [10, 25, 50, 80]
    bases = range(20, 241, 4)
    for p1 in p1_vals:
        for p2 in p2_vals:
            for base in bases:
                yield _make_spec(
                    "stacked_percentage",
                    f"What is {p2}% of {p1}% of {base}?",
                    f"{p1}:{p2}:{base}",
                    (p1, p2, base),
                )
                emitted += 1
                if emitted >= budgets["stacked_percentage"]:
                    return


def iter_level5_specs() -> Iterable[dict]:
    budgets = FAMILY_CAPS["level_5"]

    emitted = 0
    outer = [10, 20, 25, 40, 50]
    inner = [12.5, 20, 25, 40, 60, 80]
    bases = range(25, 401, 5)
    for p_outer in outer:
        for p_inner in inner:
            for base in bases:
                yield _make_spec(
                    "nested_percent",
                    f"What is {p_outer}% of {p_inner}% of {base}?",
                    f"{p_outer}:{p_inner}:{base}",
                    (p_outer, p_inner, base),
                )
                emitted += 1
                if emitted >= budgets["nested_percent"]:
                    break
            if emitted >= budgets["nested_percent"]:
                break
        if emitted >= budgets["nested_percent"]:
            break

    emitted = 0
    discounts = [5, 10, 15, 20, 25, 40]
    taxes = [5, 6, 7.5, 8, 10, 12.5]
    prices = range(20, 321, 5)
    for d in discounts:
        for t in taxes:
            for price in prices:
                yield _make_spec(
                    "discount_tax_combo",
                    f"An item costs {price}. It gets a {d}% discount, then {t}% tax is added. What is the final price?",
                    f"{d}:{t}:{price}",
                    (d, t, price),
                )
                emitted += 1
                if emitted >= budgets["discount_tax_combo"]:
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
        "level_1": ["find common whole-number percentages of whole quantities"],
        "level_2": ["extends level 1 with fractional percentages and decimal quantities"],
        "level_3": ["adds percent increase/decrease and reverse-percent problems"],
        "level_4": ["adds percent of sums and stacked percent-of-percent patterns"],
        "level_5": ["adds nested percentage chains and discount-plus-tax combinations while staying bounded"],
    }


