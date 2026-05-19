from __future__ import annotations

import itertools
import random
from fractions import Fraction
from typing import Iterable

from atlas_math.modules.shared.common import make_sample

MODULE_INFO = {
    "module_id": "arithmetic.ratio_rate_unit_rate",
    "name": "Ratio, Rate, and Unit Rate",
    "topic": "arithmetic",
    "subtopic": "core_arithmetic",
    "difficulty_levels": ["level_1", "level_2", "level_3", "level_4", "level_5"],
    "enabled": True,
}

INSTRUCTIONS = [
    "Solve the ratio or rate problem: {problem}",
    "Work through the ratio or unit-rate calculation: {problem}",
    "Find the requested ratio, rate, or equivalent quantity: {problem}",
    "Evaluate the proportional relationship carefully: {problem}",
]

LEVEL_SPEC_CAPS = {
    "level_1": 1200,
    "level_2": 1500,
    "level_3": 1800,
    "level_4": 2200,
    "level_5": 2600,
}

FAMILY_CAPS = {
    "level_1": {"simplify_ratio": 1200},
    "level_2": {"equivalent_ratio": 750, "basic_rate": 750},
    "level_3": {"unit_rate_integer": 900, "unit_rate_decimal": 900},
    "level_4": {"missing_value_ratio": 1100, "compare_unit_rates": 1100},
    "level_5": {"multi_step_rate": 1300, "best_buy": 1300},
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
        if value.denominator == 1:
            return str(value.numerator)
        return f"{float(value):.2f}".rstrip("0").rstrip(".")
    if float(value).is_integer():
        return str(int(value))
    return f"{float(value):.2f}".rstrip("0").rstrip(".")


def _evaluate(spec: dict):
    family = spec["family"]
    v = spec["values"]
    if family == "simplify_ratio":
        a, b = v
        g = __import__("math").gcd(a, b)
        return (a // g, b // g)
    if family == "equivalent_ratio":
        a, b, factor = v
        return (a * factor, b * factor)
    if family == "basic_rate":
        quantity, units = v
        return Fraction(quantity, units)
    if family in {"unit_rate_integer", "unit_rate_decimal"}:
        total, units = v
        return Fraction(total, units)
    if family == "missing_value_ratio":
        a, b, new_a = v
        return Fraction(b * new_a, a)
    if family == "compare_unit_rates":
        a1, b1, a2, b2 = v
        return Fraction(a1, b1) - Fraction(a2, b2)
    if family == "multi_step_rate":
        distance, minutes, days = v
        return Fraction(distance, minutes) * days
    if family == "best_buy":
        p1, q1, p2, q2 = v
        return Fraction(p1, q1) - Fraction(p2, q2)
    raise ValueError(f"Unknown family: {family}")


def _problem_text(spec: dict) -> str:
    family = spec["family"]
    v = spec["values"]
    if family == "simplify_ratio":
        return f"Simplify the ratio {v[0]}:{v[1]}."
    if family == "equivalent_ratio":
        return f"Find an equivalent ratio to {v[0]}:{v[1]} by multiplying both terms by {v[2]}."
    if family == "basic_rate":
        return f"A machine makes {v[0]} parts in {v[1]} hours. What is the rate in parts per hour?"
    if family == "unit_rate_integer":
        return f"Find the unit rate: {v[0]} miles in {v[1]} hours."
    if family == "unit_rate_decimal":
        return f"Find the unit rate: {_fmt_number(v[0])} liters in {v[1]} bottles."
    if family == "missing_value_ratio":
        return f"If {v[0]}:{v[1]} = {v[2]}:x, find x."
    if family == "compare_unit_rates":
        return (
            f"Compare these unit rates: {v[0]} in {v[1]} units and {v[2]} in {v[3]} units. "
            "Give the signed difference (first minus second)."
        )
    if family == "multi_step_rate":
        return f"A person travels {v[0]} miles in {v[1]} minutes each day. How many miles do they travel in {v[2]} days at the same rate?"
    if family == "best_buy":
        return (
            f"Pack A costs ${_fmt_number(v[0])} for {v[1]} items and pack B costs ${_fmt_number(v[2])} for {v[3]} items. "
            "Give the signed difference in cost per item (A minus B)."
        )
    raise ValueError(f"Unknown family: {family}")


def _answer_text(spec: dict) -> str:
    family = spec["family"]
    result = _evaluate(spec)
    if family in {"simplify_ratio", "equivalent_ratio"}:
        return f"{result[0]}:{result[1]}"
    return _fmt_number(result)


def _sample_from_spec(spec: dict, difficulty: str, instruction_idx: int = 0) -> dict:
    problem = _problem_text(spec)
    answer = _answer_text(spec)
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
    family = "simplify_ratio"
    limit = FAMILY_CAPS["level_1"][family]
    emitted = 0
    for a in range(2, 41):
        for b in range(2, 41):
            if __import__("math").gcd(a, b) == 1:
                continue
            yield {
                "family": family,
                "values": (a, b),
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
    for a in range(1, 21):
        for b in range(1, 21):
            for factor in range(2, 11):
                yield {
                    "family": "equivalent_ratio",
                    "values": (a, b, factor),
                    "canonical_key": f"equivalent_ratio:{a}:{b}:{factor}",
                    "case_id": f"equivalent_ratio:{a}:{b}:{factor}",
                    "family_id": "equivalent_ratio",
                }
                emitted += 1
                if emitted >= budgets["equivalent_ratio"]:
                    break
            if emitted >= budgets["equivalent_ratio"]:
                break
        if emitted >= budgets["equivalent_ratio"]:
            break

    emitted = 0
    for quantity in range(12, 181):
        for units in range(2, 13):
            if quantity % units != 0:
                continue
            yield {
                "family": "basic_rate",
                "values": (quantity, units),
                "canonical_key": f"basic_rate:{quantity}:{units}",
                "case_id": f"basic_rate:{quantity}:{units}",
                "family_id": "basic_rate",
            }
            emitted += 1
            if emitted >= budgets["basic_rate"]:
                return


def iter_level3_specs() -> Iterable[dict]:
    budgets = FAMILY_CAPS["level_3"]
    emitted = 0
    for total in range(24, 241):
        for units in range(2, 16):
            if total % units != 0:
                continue
            yield {
                "family": "unit_rate_integer",
                "values": (total, units),
                "canonical_key": f"unit_rate_integer:{total}:{units}",
                "case_id": f"unit_rate_integer:{total}:{units}",
                "family_id": "unit_rate_integer",
            }
            emitted += 1
            if emitted >= budgets["unit_rate_integer"]:
                break
        if emitted >= budgets["unit_rate_integer"]:
            break

    emitted = 0
    for total_tenths in range(50, 601, 5):
        total = Fraction(total_tenths, 10)
        for units in range(2, 13):
            yield {
                "family": "unit_rate_decimal",
                "values": (total, units),
                "canonical_key": f"unit_rate_decimal:{total}:{units}",
                "case_id": f"unit_rate_decimal:{total}:{units}",
                "family_id": "unit_rate_decimal",
            }
            emitted += 1
            if emitted >= budgets["unit_rate_decimal"]:
                return


def iter_level4_specs() -> Iterable[dict]:
    budgets = FAMILY_CAPS["level_4"]
    emitted = 0
    for a in range(1, 31):
        for b in range(1, 31):
            for new_a in range(2, 61):
                yield {
                    "family": "missing_value_ratio",
                    "values": (a, b, new_a),
                    "canonical_key": f"missing_value_ratio:{a}:{b}:{new_a}",
                    "case_id": f"missing_value_ratio:{a}:{b}:{new_a}",
                    "family_id": "missing_value_ratio",
                }
                emitted += 1
                if emitted >= budgets["missing_value_ratio"]:
                    break
            if emitted >= budgets["missing_value_ratio"]:
                break
        if emitted >= budgets["missing_value_ratio"]:
            break

    emitted = 0
    for a1 in range(10, 121, 5):
        for b1 in range(2, 13):
            for a2 in range(10, 121, 5):
                for b2 in range(2, 13):
                    yield {
                        "family": "compare_unit_rates",
                        "values": (a1, b1, a2, b2),
                        "canonical_key": f"compare_unit_rates:{a1}:{b1}:{a2}:{b2}",
                        "case_id": f"compare_unit_rates:{a1}:{b1}:{a2}:{b2}",
                        "family_id": "compare_unit_rates",
                    }
                    emitted += 1
                    if emitted >= budgets["compare_unit_rates"]:
                        return


def iter_level5_specs() -> Iterable[dict]:
    budgets = FAMILY_CAPS["level_5"]
    emitted = 0
    for distance in range(10, 121, 5):
        for minutes in range(5, 61, 5):
            for days in range(2, 16):
                yield {
                    "family": "multi_step_rate",
                    "values": (distance, minutes, days),
                    "canonical_key": f"multi_step_rate:{distance}:{minutes}:{days}",
                    "case_id": f"multi_step_rate:{distance}:{minutes}:{days}",
                    "family_id": "multi_step_rate",
                }
                emitted += 1
                if emitted >= budgets["multi_step_rate"]:
                    break
            if emitted >= budgets["multi_step_rate"]:
                break
        if emitted >= budgets["multi_step_rate"]:
            break

    emitted = 0
    for p1_cents in range(100, 1601, 25):
        p1 = Fraction(p1_cents, 100)
        for q1 in range(2, 25):
            for p2_cents in range(100, 1601, 25):
                p2 = Fraction(p2_cents, 100)
                for q2 in range(2, 25):
                    yield {
                        "family": "best_buy",
                        "values": (p1, q1, p2, q2),
                        "canonical_key": f"best_buy:{p1}:{q1}:{p2}:{q2}",
                        "case_id": f"best_buy:{p1}:{q1}:{p2}:{q2}",
                        "family_id": "best_buy",
                    }
                    emitted += 1
                    if emitted >= budgets["best_buy"]:
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
        "level_1": ["simplifies ratios"],
        "level_2": ["builds equivalent ratios and basic whole-number rates"],
        "level_3": ["computes integer and decimal unit rates"],
        "level_4": ["solves missing-value ratios and compares unit rates"],
        "level_5": ["handles multi-step rate contexts and best-buy style comparisons"],
    }


