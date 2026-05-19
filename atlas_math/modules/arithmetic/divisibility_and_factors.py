from __future__ import annotations

import itertools
import math
import random
from typing import Iterable

from atlas_math.modules.shared.common import make_sample

MODULE_INFO = {
    "module_id": "arithmetic.divisibility_and_factors",
    "name": "Divisibility and Factors",
    "topic": "arithmetic",
    "subtopic": "core_arithmetic",
    "difficulty_levels": ["level_1", "level_2", "level_3", "level_4", "level_5"],
    "enabled": True,
}

INSTRUCTIONS = [
    "Solve the divisibility or factors problem: {problem}",
    "Work with the factors carefully: {problem}",
    "Use divisibility reasoning to answer: {problem}",
    "Find the requested factor information: {problem}",
]

LEVEL_SPEC_CAPS = {
    "level_1": 1200,
    "level_2": 1500,
    "level_3": 1800,
    "level_4": 2200,
    "level_5": 2600,
}

FAMILY_CAPS = {
    "level_1": {"is_divisible": 1200},
    "level_2": {"greatest_factor_pair": 750, "count_factors_small": 750},
    "level_3": {"prime_or_composite": 900, "gcf_two_numbers": 900},
    "level_4": {"lcm_two_numbers": 1100, "missing_factor": 1100},
    "level_5": {"divisibility_multi_check": 1300, "prime_factor_count": 1300},
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


def _factor_count(n: int) -> int:
    count = 0
    root = int(math.isqrt(n))
    for d in range(1, root + 1):
        if n % d == 0:
            count += 1 if d * d == n else 2
    return count


def _prime_factor_count(n: int) -> int:
    total = 0
    d = 2
    value = n
    while d * d <= value:
        while value % d == 0:
            total += 1
            value //= d
        d += 1
    if value > 1:
        total += 1
    return total


def _evaluate(spec: dict) -> str:
    family = spec["family"]
    v = spec["values"]
    if family == "is_divisible":
        return "yes" if v[0] % v[1] == 0 else "no"
    if family == "greatest_factor_pair":
        smaller = int(math.isqrt(v[0]))
        while smaller > 0 and v[0] % smaller != 0:
            smaller -= 1
        larger = v[0] // smaller
        return f"{smaller} and {larger}"
    if family == "count_factors_small":
        return str(_factor_count(v[0]))
    if family == "prime_or_composite":
        return "prime" if _factor_count(v[0]) == 2 else "composite"
    if family == "gcf_two_numbers":
        return str(math.gcd(v[0], v[1]))
    if family == "lcm_two_numbers":
        return str(abs(v[0] * v[1]) // math.gcd(v[0], v[1]))
    if family == "missing_factor":
        return str(v[0] // v[1])
    if family == "divisibility_multi_check":
        divisors = [d for d in (2, 3, 5, 9, 10) if v[0] % d == 0]
        return ", ".join(str(d) for d in divisors) if divisors else "none"
    if family == "prime_factor_count":
        return str(_prime_factor_count(v[0]))
    raise ValueError(f"Unknown family: {family}")


def _problem_text(spec: dict) -> str:
    family = spec["family"]
    v = spec["values"]
    if family == "is_divisible":
        return f"Is {v[0]} divisible by {v[1]}?"
    if family == "greatest_factor_pair":
        return f"Find the factor pair of {v[0]} whose two factors are closest together."
    if family == "count_factors_small":
        return f"How many positive factors does {v[0]} have?"
    if family == "prime_or_composite":
        return f"Is {v[0]} prime or composite?"
    if family == "gcf_two_numbers":
        return f"Find the greatest common factor of {v[0]} and {v[1]}."
    if family == "lcm_two_numbers":
        return f"Find the least common multiple of {v[0]} and {v[1]}."
    if family == "missing_factor":
        return f"Complete the multiplication: {v[1]} × ? = {v[0]}."
    if family == "divisibility_multi_check":
        return f"Which of 2, 3, 5, 9, and 10 divide {v[0]} evenly?"
    if family == "prime_factor_count":
        return f"How many prime factors does {v[0]} have when counted with multiplicity?"
    raise ValueError(f"Unknown family: {family}")


def _sample_from_spec(spec: dict, difficulty: str, instruction_idx: int = 0) -> dict:
    problem = _problem_text(spec)
    answer = _evaluate(spec)
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
    family = "is_divisible"
    limit = FAMILY_CAPS["level_1"][family]
    emitted = 0
    for n in range(10, 300):
        for d in (2, 3, 5, 10):
            yield {
                "family": family,
                "values": (n, d),
                "canonical_key": f"{family}:{n}:{d}",
                "case_id": f"{family}:{n}:{d}",
                "family_id": family,
            }
            emitted += 1
            if emitted >= limit:
                return


def iter_level2_specs() -> Iterable[dict]:
    budgets = FAMILY_CAPS["level_2"]
    emitted = 0
    for n in range(12, 3001):
        yield {
            "family": "greatest_factor_pair",
            "values": (n,),
            "canonical_key": f"greatest_factor_pair:{n}",
            "case_id": f"greatest_factor_pair:{n}",
            "family_id": "greatest_factor_pair",
        }
        emitted += 1
        if emitted >= budgets["greatest_factor_pair"]:
            break

    emitted = 0
    for n in range(12, 1500):
        yield {
            "family": "count_factors_small",
            "values": (n,),
            "canonical_key": f"count_factors_small:{n}",
            "case_id": f"count_factors_small:{n}",
            "family_id": "count_factors_small",
        }
        emitted += 1
        if emitted >= budgets["count_factors_small"]:
            return


def iter_level3_specs() -> Iterable[dict]:
    budgets = FAMILY_CAPS["level_3"]
    emitted = 0
    for n in range(2, 500):
        yield {
            "family": "prime_or_composite",
            "values": (n,),
            "canonical_key": f"prime_or_composite:{n}",
            "case_id": f"prime_or_composite:{n}",
            "family_id": "prime_or_composite",
        }
        emitted += 1
        if emitted >= budgets["prime_or_composite"]:
            break

    emitted = 0
    for a in range(12, 400):
        for b in range(12, 400):
            yield {
                "family": "gcf_two_numbers",
                "values": (a, b),
                "canonical_key": f"gcf_two_numbers:{a}:{b}",
                "case_id": f"gcf_two_numbers:{a}:{b}",
                "family_id": "gcf_two_numbers",
            }
            emitted += 1
            if emitted >= budgets["gcf_two_numbers"]:
                return


def iter_level4_specs() -> Iterable[dict]:
    budgets = FAMILY_CAPS["level_4"]
    emitted = 0
    for a in range(6, 120):
        for b in range(6, 120):
            yield {
                "family": "lcm_two_numbers",
                "values": (a, b),
                "canonical_key": f"lcm_two_numbers:{a}:{b}",
                "case_id": f"lcm_two_numbers:{a}:{b}",
                "family_id": "lcm_two_numbers",
            }
            emitted += 1
            if emitted >= budgets["lcm_two_numbers"]:
                break
        if emitted >= budgets["lcm_two_numbers"]:
            break

    emitted = 0
    for product in range(24, 5000):
        for known in range(2, 50):
            if product % known != 0:
                continue
            yield {
                "family": "missing_factor",
                "values": (product, known),
                "canonical_key": f"missing_factor:{product}:{known}",
                "case_id": f"missing_factor:{product}:{known}",
                "family_id": "missing_factor",
            }
            emitted += 1
            if emitted >= budgets["missing_factor"]:
                return


def iter_level5_specs() -> Iterable[dict]:
    budgets = FAMILY_CAPS["level_5"]
    emitted = 0
    for n in range(10, 10000):
        yield {
            "family": "divisibility_multi_check",
            "values": (n,),
            "canonical_key": f"divisibility_multi_check:{n}",
            "case_id": f"divisibility_multi_check:{n}",
            "family_id": "divisibility_multi_check",
        }
        emitted += 1
        if emitted >= budgets["divisibility_multi_check"]:
            break

    emitted = 0
    for n in range(12, 10000):
        yield {
            "family": "prime_factor_count",
            "values": (n,),
            "canonical_key": f"prime_factor_count:{n}",
            "case_id": f"prime_factor_count:{n}",
            "family_id": "prime_factor_count",
        }
        emitted += 1
        if emitted >= budgets["prime_factor_count"]:
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
        "level_1": ["checks simple divisibility by common small divisors"],
        "level_2": ["adds factor-pair reasoning and counting factors"],
        "level_3": ["adds prime/composite classification and greatest common factor"],
        "level_4": ["adds least common multiple and missing-factor equations"],
        "level_5": ["adds multi-divisor checks and counting prime factors with multiplicity"],
    }


