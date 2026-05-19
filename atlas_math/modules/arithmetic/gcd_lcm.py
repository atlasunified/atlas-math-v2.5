from __future__ import annotations

import itertools
import math
import random
from typing import Iterable

from atlas_math.modules.shared.common import make_sample

MODULE_INFO = {
    "module_id": "arithmetic.gcd_lcm",
    "name": "GCD and LCM",
    "topic": "arithmetic",
    "subtopic": "core_arithmetic",
    "difficulty_levels": ["level_1", "level_2", "level_3", "level_4", "level_5"],
    "enabled": True,
}

INSTRUCTIONS = [
    "Solve the greatest-common-factor or least-common-multiple problem: {problem}",
    "Work through the divisibility reasoning carefully: {problem}",
    "Compute the requested GCD or LCM: {problem}",
    "Evaluate the number theory question step by step: {problem}",
]

LEVEL_SPEC_CAPS = {
    "level_1": 1000,
    "level_2": 1400,
    "level_3": 1800,
    "level_4": 2200,
    "level_5": 2600,
}

FAMILY_CAPS = {
    "level_1": {"gcd_two": 1000},
    "level_2": {"lcm_two": 700, "gcd_multiples": 700},
    "level_3": {"gcd_lcm_pair": 900, "gcd_wording": 900},
    "level_4": {"gcd_three": 1100, "lcm_three": 1100},
    "level_5": {"mixed_compare": 1300, "shared_schedule": 1300},
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


def _gcd_many(values) -> int:
    out = abs(int(values[0]))
    for value in values[1:]:
        out = math.gcd(out, abs(int(value)))
    return out


def _lcm_two(a: int, b: int) -> int:
    return abs(a * b) // math.gcd(a, b)


def _lcm_many(values) -> int:
    out = abs(int(values[0]))
    for value in values[1:]:
        out = _lcm_two(out, abs(int(value)))
    return out


def _evaluate(spec: dict):
    family = spec["family"]
    values = spec["values"]
    if family in {"gcd_two", "gcd_multiples", "gcd_wording", "gcd_three"}:
        return _gcd_many(values)
    if family in {"lcm_two", "lcm_three", "shared_schedule"}:
        return _lcm_many(values)
    if family == "gcd_lcm_pair":
        return f"GCD = {_gcd_many(values)}, LCM = {_lcm_many(values)}"
    if family == "mixed_compare":
        return _lcm_many(values) - _gcd_many(values)
    raise ValueError(f"Unknown family: {family}")


def _problem_text(spec: dict) -> str:
    family = spec["family"]
    v = spec["values"]
    if family == "gcd_two":
        return f"Find the greatest common divisor of {v[0]} and {v[1]}."
    if family == "lcm_two":
        return f"Find the least common multiple of {v[0]} and {v[1]}."
    if family == "gcd_multiples":
        return f"Compute gcd({v[0]}, {v[1]})."
    if family == "gcd_lcm_pair":
        return f"For the numbers {v[0]} and {v[1]}, find both the GCD and the LCM."
    if family == "gcd_wording":
        return f"What is the greatest number that divides both {v[0]} and {v[1]} without remainder?"
    if family == "gcd_three":
        return f"Find the greatest common divisor of {v[0]}, {v[1]}, and {v[2]}."
    if family == "lcm_three":
        return f"Find the least common multiple of {v[0]}, {v[1]}, and {v[2]}."
    if family == "mixed_compare":
        return f"Find the difference between the LCM and the GCD of {v[0]} and {v[1]}."
    if family == "shared_schedule":
        return (
            f"A bell rings every {v[0]} minutes and another bell rings every {v[1]} minutes. "
            "If they ring together now, after how many minutes will they ring together again?"
        )
    raise ValueError(f"Unknown family: {family}")


def _answer_text(spec: dict) -> str:
    result = _evaluate(spec)
    return str(result)


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
    family = "gcd_two"
    limit = FAMILY_CAPS["level_1"][family]
    emitted = 0
    for g in range(2, 21):
        for a in range(2, 13):
            for b in range(a + 1, 15):
                if math.gcd(a, b) != 1:
                    continue
                x, y = g * a, g * b
                yield {
                    "family": family,
                    "values": (x, y),
                    "canonical_key": f"{family}:{x}:{y}",
                    "case_id": f"{family}:{x}:{y}",
                    "family_id": family,
                }
                emitted += 1
                if emitted >= limit:
                    return


def iter_level2_specs() -> Iterable[dict]:
    budgets = FAMILY_CAPS["level_2"]
    emitted = 0
    for a in range(2, 26):
        for b in range(a + 1, 31):
            if a * b > 240:
                continue
            yield {
                "family": "lcm_two",
                "values": (a, b),
                "canonical_key": f"lcm_two:{a}:{b}",
                "case_id": f"lcm_two:{a}:{b}",
                "family_id": "lcm_two",
            }
            emitted += 1
            if emitted >= budgets["lcm_two"]:
                break
        if emitted >= budgets["lcm_two"]:
            break

    emitted = 0
    for base in range(3, 25):
        for m1 in range(2, 10):
            for m2 in range(m1 + 1, 11):
                x, y = base * m1, base * m2
                yield {
                    "family": "gcd_multiples",
                    "values": (x, y),
                    "canonical_key": f"gcd_multiples:{x}:{y}",
                    "case_id": f"gcd_multiples:{x}:{y}",
                    "family_id": "gcd_multiples",
                }
                emitted += 1
                if emitted >= budgets["gcd_multiples"]:
                    return


def iter_level3_specs() -> Iterable[dict]:
    budgets = FAMILY_CAPS["level_3"]
    emitted = 0
    for a in range(4, 25):
        for b in range(a + 1, 31):
            if a * b > 300:
                continue
            yield {
                "family": "gcd_lcm_pair",
                "values": (a, b),
                "canonical_key": f"gcd_lcm_pair:{a}:{b}",
                "case_id": f"gcd_lcm_pair:{a}:{b}",
                "family_id": "gcd_lcm_pair",
            }
            emitted += 1
            if emitted >= budgets["gcd_lcm_pair"]:
                break
        if emitted >= budgets["gcd_lcm_pair"]:
            break

    emitted = 0
    for g in range(2, 21):
        for a in range(3, 11):
            for b in range(a + 1, 12):
                if math.gcd(a, b) != 1:
                    continue
                x, y = g * a, g * b
                yield {
                    "family": "gcd_wording",
                    "values": (x, y),
                    "canonical_key": f"gcd_wording:{x}:{y}",
                    "case_id": f"gcd_wording:{x}:{y}",
                    "family_id": "gcd_wording",
                }
                emitted += 1
                if emitted >= budgets["gcd_wording"]:
                    return


def iter_level4_specs() -> Iterable[dict]:
    budgets = FAMILY_CAPS["level_4"]
    emitted = 0
    for g in range(2, 19):
        for a in range(2, 8):
            for b in range(a + 1, 9):
                for c in range(b + 1, 10):
                    if math.gcd(math.gcd(a, b), c) != 1:
                        continue
                    vals = (g * a, g * b, g * c)
                    yield {
                        "family": "gcd_three",
                        "values": vals,
                        "canonical_key": f"gcd_three:{vals[0]}:{vals[1]}:{vals[2]}",
                        "case_id": f"gcd_three:{vals[0]}:{vals[1]}:{vals[2]}",
                        "family_id": "gcd_three",
                    }
                    emitted += 1
                    if emitted >= budgets["gcd_three"]:
                        break
                if emitted >= budgets["gcd_three"]:
                    break
            if emitted >= budgets["gcd_three"]:
                break
        if emitted >= budgets["gcd_three"]:
            break

    emitted = 0
    for a in range(2, 11):
        for b in range(a + 1, 12):
            for c in range(b + 1, 13):
                if a * b * c > 450:
                    continue
                vals = (a, b, c)
                yield {
                    "family": "lcm_three",
                    "values": vals,
                    "canonical_key": f"lcm_three:{a}:{b}:{c}",
                    "case_id": f"lcm_three:{a}:{b}:{c}",
                    "family_id": "lcm_three",
                }
                emitted += 1
                if emitted >= budgets["lcm_three"]:
                    return


def iter_level5_specs() -> Iterable[dict]:
    budgets = FAMILY_CAPS["level_5"]
    emitted = 0
    for a in range(6, 41):
        for b in range(a + 1, 46):
            if a * b > 420:
                continue
            yield {
                "family": "mixed_compare",
                "values": (a, b),
                "canonical_key": f"mixed_compare:{a}:{b}",
                "case_id": f"mixed_compare:{a}:{b}",
                "family_id": "mixed_compare",
            }
            emitted += 1
            if emitted >= budgets["mixed_compare"]:
                break
        if emitted >= budgets["mixed_compare"]:
            break

    emitted = 0
    for a in range(4, 31):
        for b in range(a + 1, 36):
            if a * b > 360:
                continue
            yield {
                "family": "shared_schedule",
                "values": (a, b),
                "canonical_key": f"shared_schedule:{a}:{b}",
                "case_id": f"shared_schedule:{a}:{b}",
                "family_id": "shared_schedule",
            }
            emitted += 1
            if emitted >= budgets["shared_schedule"]:
                return


def _iter_specs(difficulty: str) -> Iterable[dict]:
    level = _level_num(difficulty)
    cap = LEVEL_SPEC_CAPS[_difficulty_name(level)]
    if level == 1:
        return _take(iter_level1_specs(), cap)
    if level == 2:
        return _take(itertools.chain(iter_level1_specs(), iter_level2_specs()), cap)
    if level == 3:
        return _take(itertools.chain(iter_level1_specs(), iter_level2_specs(), iter_level3_specs()), cap)
    if level == 4:
        return _take(itertools.chain(iter_level1_specs(), iter_level2_specs(), iter_level3_specs(), iter_level4_specs()), cap)
    return _take(itertools.chain(iter_level1_specs(), iter_level2_specs(), iter_level3_specs(), iter_level4_specs(), iter_level5_specs()), cap)


def generate(count: int = 10, difficulty: str = "level_1", seed=None):
    pool_size = min(MAX_SPEC_PREFIX, max(int(count) * MAX_GENERATE_MULTIPLIER, int(count), 64))
    pool = list(itertools.islice(_iter_specs(difficulty), 0, pool_size))
    rng = random.Random(_stable_seed(seed, difficulty, "generate"))
    rng.shuffle(pool)
    out = []
    seen = set()
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


def generate_unique(count: int = 10, difficulty: str = "level_1", offset: int = 0, stride: int = 1, seed=None):
    level = _difficulty_name(_level_num(difficulty))
    pool_size = min(LEVEL_SPEC_CAPS[level], MAX_ITER_SAMPLES)
    pool = list(itertools.islice(_iter_specs(difficulty), 0, pool_size))
    rng = random.Random(_stable_seed(seed, difficulty, offset, stride, "generate_unique"))
    rng.shuffle(pool)
    out = []
    seen = set()
    start = max(0, int(offset))
    step = max(1, int(stride))
    for idx in range(start, len(pool), step):
        sample = _sample_from_spec(pool[idx], difficulty, instruction_idx=idx)
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
        "level_1": ["basic GCD of two positive integers"],
        "level_2": ["adds LCM and more direct divisor-multiple structure"],
        "level_3": ["adds paired GCD/LCM requests and wording variants"],
        "level_4": ["extends to three-number GCD and LCM computations"],
        "level_5": ["adds mixed GCD-vs-LCM comparisons and common-multiple schedule contexts"],
    }


