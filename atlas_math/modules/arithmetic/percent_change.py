from __future__ import annotations

import itertools
import random
from fractions import Fraction
from typing import Iterable

from atlas_math.modules.shared.common import make_sample

MODULE_INFO = {
    "module_id": "arithmetic.percent_change",
    "name": "Percent Change",
    "topic": "arithmetic",
    "subtopic": "core_arithmetic",
    "difficulty_levels": ["level_1", "level_2", "level_3", "level_4", "level_5"],
    "enabled": True,
}

INSTRUCTIONS = [
    "Solve the percent problem: {problem}",
    "Compute the percent change carefully: {problem}",
    "Find the percent increase or decrease: {problem}",
    "Evaluate the percent relationship and give the final value: {problem}",
]

LEVEL_SPEC_CAPS = {
    "level_1": 1200,
    "level_2": 1500,
    "level_3": 1800,
    "level_4": 2200,
    "level_5": 2600,
}

FAMILY_CAPS = {
    "level_1": {"increase_whole": 1200},
    "level_2": {"decrease_whole": 750, "increase_decimal": 750},
    "level_3": {"signed_percent_change": 900, "fractional_percent_change": 900},
    "level_4": {"reverse_new_from_old": 1100, "reverse_old_from_new": 1100},
    "level_5": {"multi_step_change": 1300, "compare_two_changes": 1300},
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


def _fmt_percent(percent) -> str:
    if isinstance(percent, Fraction):
        if percent.denominator == 1:
            return f"{percent.numerator}%"
        value = float(percent)
    else:
        value = float(percent)
    if value.is_integer():
        return f"{int(value)}%"
    return f"{value:.1f}%"


def _fmt_decimal(value: float) -> str:
    if float(value).is_integer():
        return str(int(value))
    return f"{value:.2f}".rstrip("0").rstrip(".")


def _evaluate(spec: dict):
    family = spec["family"]
    values = spec["values"]
    if family in {"increase_whole", "decrease_whole", "increase_decimal", "signed_percent_change", "fractional_percent_change"}:
        old, new = values
        return Fraction(new - old, old) * 100
    if family == "reverse_new_from_old":
        old, percent = values
        return Fraction(old) * (Fraction(100) + percent) / 100
    if family == "reverse_old_from_new":
        new, percent = values
        return Fraction(new) * 100 / (Fraction(100) + percent)
    if family == "multi_step_change":
        base, p1, p2 = values
        return Fraction(base) * (Fraction(100) + p1) * (Fraction(100) + p2) / 10000
    if family == "compare_two_changes":
        old_a, new_a, old_b, new_b = values
        change_a = Fraction(new_a - old_a, old_a) * 100
        change_b = Fraction(new_b - old_b, old_b) * 100
        return change_a - change_b
    raise ValueError(f"Unknown family: {family}")


def _problem_text(spec: dict) -> str:
    family = spec["family"]
    v = spec["values"]
    if family == "increase_whole":
        return f"Find the percent change from {v[0]} to {v[1]}."
    if family == "decrease_whole":
        return f"Find the percent change from {v[0]} to {v[1]}."
    if family == "increase_decimal":
        return f"A value changes from {_fmt_decimal(v[0])} to {_fmt_decimal(v[1])}. Find the percent change."
    if family == "signed_percent_change":
        return f"A quantity changes from {v[0]} to {v[1]}. Give the signed percent change."
    if family == "fractional_percent_change":
        return f"A quantity changes from {v[0]} to {v[1]}. Express the percent change."
    if family == "reverse_new_from_old":
        return f"A quantity is {v[0]} and changes by {_fmt_percent(v[1])}. What is the new value?"
    if family == "reverse_old_from_new":
        return f"After a {_fmt_percent(v[1])} change, the new value is {v[0]}. What was the original value?"
    if family == "multi_step_change":
        return f"Starting from {v[0]}, apply {_fmt_percent(v[1])} and then {_fmt_percent(v[2])}. What is the final value?"
    if family == "compare_two_changes":
        return (
            f"Item A changes from {v[0]} to {v[1]}, and item B changes from {v[2]} to {v[3]}. "
            "What is the signed difference in percent change (A minus B)?"
        )
    raise ValueError(f"Unknown family: {family}")


def _answer_text(spec: dict) -> str:
    family = spec["family"]
    result = _evaluate(spec)
    if family in {"increase_whole", "decrease_whole", "increase_decimal", "signed_percent_change", "fractional_percent_change", "compare_two_changes"}:
        return _fmt_percent(result)
    if isinstance(result, Fraction) and result.denominator == 1:
        return str(result.numerator)
    return _fmt_decimal(float(result))


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
    family = "increase_whole"
    limit = FAMILY_CAPS["level_1"][family]
    emitted = 0
    for old in range(20, 121, 5):
        for pct in range(5, 55, 5):
            new = old * (100 + pct) // 100
            if old * (100 + pct) % 100 != 0:
                continue
            yield {
                "family": family,
                "values": (old, new),
                "canonical_key": f"{family}:{old}:{new}",
                "case_id": f"{family}:{old}:{new}",
                "family_id": family,
            }
            emitted += 1
            if emitted >= limit:
                return


def iter_level2_specs() -> Iterable[dict]:
    budgets = FAMILY_CAPS["level_2"]
    emitted = 0
    for old in range(20, 181, 5):
        for pct in range(5, 55, 5):
            new_num = old * (100 - pct)
            if new_num <= 0 or new_num % 100 != 0:
                continue
            new = new_num // 100
            yield {
                "family": "decrease_whole",
                "values": (old, new),
                "canonical_key": f"decrease_whole:{old}:{new}",
                "case_id": f"decrease_whole:{old}:{new}",
                "family_id": "decrease_whole",
            }
            emitted += 1
            if emitted >= budgets["decrease_whole"]:
                break
        if emitted >= budgets["decrease_whole"]:
            break

    emitted = 0
    for tenths in range(100, 501, 5):
        old = tenths / 10
        for pct in range(5, 55, 5):
            new = old * (100 + pct) / 100
            yield {
                "family": "increase_decimal",
                "values": (old, new),
                "canonical_key": f"increase_decimal:{old}:{new}",
                "case_id": f"increase_decimal:{old}:{new}",
                "family_id": "increase_decimal",
            }
            emitted += 1
            if emitted >= budgets["increase_decimal"]:
                return


def iter_level3_specs() -> Iterable[dict]:
    budgets = FAMILY_CAPS["level_3"]
    emitted = 0
    for old in range(10, 151, 5):
        for delta in range(-45, 50, 5):
            if delta == 0:
                continue
            new_num = old * (100 + delta)
            if new_num <= 0 or new_num % 100 != 0:
                continue
            new = new_num // 100
            yield {
                "family": "signed_percent_change",
                "values": (old, new),
                "canonical_key": f"signed_percent_change:{old}:{new}",
                "case_id": f"signed_percent_change:{old}:{new}",
                "family_id": "signed_percent_change",
            }
            emitted += 1
            if emitted >= budgets["signed_percent_change"]:
                break
        if emitted >= budgets["signed_percent_change"]:
            break

    emitted = 0
    for old in range(8, 81, 4):
        for step in range(-3, 4):
            if step == 0:
                continue
            new = old + step
            if new <= 0:
                continue
            pct = Fraction(new - old, old) * 100
            if pct.denominator not in {1, 2, 4, 5, 10, 20, 25, 50}:
                continue
            yield {
                "family": "fractional_percent_change",
                "values": (old, new),
                "canonical_key": f"fractional_percent_change:{old}:{new}",
                "case_id": f"fractional_percent_change:{old}:{new}",
                "family_id": "fractional_percent_change",
            }
            emitted += 1
            if emitted >= budgets["fractional_percent_change"]:
                return


def iter_level4_specs() -> Iterable[dict]:
    budgets = FAMILY_CAPS["level_4"]
    emitted = 0
    for old in range(20, 201, 5):
        for pct in range(-40, 55, 5):
            if pct == 0:
                continue
            result = Fraction(old) * (100 + pct) / 100
            if result <= 0:
                continue
            yield {
                "family": "reverse_new_from_old",
                "values": (old, Fraction(pct)),
                "canonical_key": f"reverse_new_from_old:{old}:{pct}",
                "case_id": f"reverse_new_from_old:{old}:{pct}",
                "family_id": "reverse_new_from_old",
            }
            emitted += 1
            if emitted >= budgets["reverse_new_from_old"]:
                break
        if emitted >= budgets["reverse_new_from_old"]:
            break

    emitted = 0
    for old in range(20, 201, 5):
        for pct in range(-40, 55, 5):
            if pct == 0 or pct == -100:
                continue
            new = Fraction(old) * (100 + pct) / 100
            if new <= 0:
                continue
            yield {
                "family": "reverse_old_from_new",
                "values": (new, Fraction(pct)),
                "canonical_key": f"reverse_old_from_new:{old}:{pct}",
                "case_id": f"reverse_old_from_new:{old}:{pct}",
                "family_id": "reverse_old_from_new",
            }
            emitted += 1
            if emitted >= budgets["reverse_old_from_new"]:
                return


def iter_level5_specs() -> Iterable[dict]:
    budgets = FAMILY_CAPS["level_5"]
    emitted = 0
    for base in range(20, 181, 5):
        for p1 in range(-30, 35, 5):
            for p2 in range(-30, 35, 5):
                if p1 == 0 and p2 == 0:
                    continue
                result = Fraction(base) * (100 + p1) * (100 + p2) / 10000
                if result <= 0:
                    continue
                yield {
                    "family": "multi_step_change",
                    "values": (base, Fraction(p1), Fraction(p2)),
                    "canonical_key": f"multi_step_change:{base}:{p1}:{p2}",
                    "case_id": f"multi_step_change:{base}:{p1}:{p2}",
                    "family_id": "multi_step_change",
                }
                emitted += 1
                if emitted >= budgets["multi_step_change"]:
                    break
            if emitted >= budgets["multi_step_change"]:
                break
        if emitted >= budgets["multi_step_change"]:
            break

    emitted = 0
    for old_a in range(20, 121, 5):
        for pct_a in range(-30, 35, 5):
            if pct_a == 0:
                continue
            new_a = Fraction(old_a) * (100 + pct_a) / 100
            if new_a <= 0:
                continue
            for old_b in range(20, 121, 5):
                for pct_b in range(-30, 35, 5):
                    if pct_b == 0:
                        continue
                    new_b = Fraction(old_b) * (100 + pct_b) / 100
                    if new_b <= 0:
                        continue
                    yield {
                        "family": "compare_two_changes",
                        "values": (old_a, new_a, old_b, new_b),
                        "canonical_key": f"compare_two_changes:{old_a}:{pct_a}:{old_b}:{pct_b}",
                        "case_id": f"compare_two_changes:{old_a}:{pct_a}:{old_b}:{pct_b}",
                        "family_id": "compare_two_changes",
                    }
                    emitted += 1
                    if emitted >= budgets["compare_two_changes"]:
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
        "level_1": ["computes basic whole-number percent increases"],
        "level_2": ["adds whole-number decreases and decimal starting values"],
        "level_3": ["adds signed percent change and non-integer percent answers"],
        "level_4": ["solves reverse percent-change problems in both directions"],
        "level_5": ["handles chained percent changes and comparisons between two percent changes"],
    }


