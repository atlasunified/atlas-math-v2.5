from __future__ import annotations

import itertools
import math
import random
from typing import Iterable

from atlas_math.modules.shared.common import make_sample

MODULE_INFO = {
    "module_id": "arithmetic.prime_factorization",
    "name": "Prime Factorization",
    "topic": "arithmetic",
    "subtopic": "core_arithmetic",
    "difficulty_levels": ["level_1", "level_2", "level_3", "level_4", "level_5"],
    "enabled": True,
}

INSTRUCTIONS = [
    "Find the prime factorization: {problem}",
    "Break the number into primes carefully: {problem}",
    "Compute the factorization using prime factors: {problem}",
    "Solve the prime-factor question step by step: {problem}",
]

LEVEL_SPEC_CAPS = {
    "level_1": 1000,
    "level_2": 1400,
    "level_3": 1800,
    "level_4": 2200,
    "level_5": 2600,
}

FAMILY_CAPS = {
    "level_1": {"factor_small": 1000},
    "level_2": {"factor_with_powers": 700, "count_prime_factors": 700},
    "level_3": {"greatest_prime_factor": 900, "missing_factor": 900},
    "level_4": {"factor_large_composite": 1100, "reconstruct_from_factorization": 1100},
    "level_5": {"compare_factorizations": 1300, "lcm_from_factorizations": 1300},
}

CAPACITY_HINTS = {level: {"value": cap, "quality": "capped"} for level, cap in LEVEL_SPEC_CAPS.items()}
MAX_SPEC_PREFIX = 5000
MAX_GENERATE_MULTIPLIER = 8
MAX_ITER_SAMPLES = 4096
PRIMES = (2, 3, 5, 7, 11, 13)


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


def _factor_map(n: int) -> dict[int, int]:
    value = int(n)
    out: dict[int, int] = {}
    for p in PRIMES:
        while value % p == 0:
            out[p] = out.get(p, 0) + 1
            value //= p
    if value > 1:
        out[value] = out.get(value, 0) + 1
    return out


def _factor_text(n: int) -> str:
    items = []
    for p, exp in sorted(_factor_map(n).items()):
        items.append(str(p) if exp == 1 else f"{p}^{exp}")
    return " × ".join(items)


def _count_prime_factors(n: int) -> int:
    return sum(_factor_map(n).values())


def _largest_prime_factor(n: int) -> int:
    return max(_factor_map(n))


def _build_number(exponents: tuple[int, ...]) -> int:
    value = 1
    for p, exp in zip(PRIMES, exponents):
        value *= p ** exp
    return value


def _evaluate(spec: dict):
    family = spec["family"]
    values = spec["values"]
    if family in {"factor_small", "factor_with_powers", "factor_large_composite"}:
        return _factor_text(values[0])
    if family == "count_prime_factors":
        return _count_prime_factors(values[0])
    if family == "greatest_prime_factor":
        return _largest_prime_factor(values[0])
    if family == "missing_factor":
        whole, partial = values
        return whole // partial
    if family == "reconstruct_from_factorization":
        return values[0]
    if family == "compare_factorizations":
        a, b = values
        return _count_prime_factors(a) - _count_prime_factors(b)
    if family == "lcm_from_factorizations":
        a, b = values
        return abs(a * b) // math.gcd(a, b)
    raise ValueError(f"Unknown family: {family}")


def _problem_text(spec: dict) -> str:
    family = spec["family"]
    v = spec["values"]
    if family in {"factor_small", "factor_with_powers", "factor_large_composite"}:
        return f"Write {v[0]} as a product of prime factors."
    if family == "count_prime_factors":
        return f"How many prime factors does {v[0]} have, counting repeats?"
    if family == "greatest_prime_factor":
        return f"What is the greatest prime factor of {v[0]}?"
    if family == "missing_factor":
        return f"A number has prime factorization {_factor_text(v[0])}. If one factor is {v[1]}, what missing factor remains?"
    if family == "reconstruct_from_factorization":
        return f"Evaluate the prime-factor form {_factor_text(v[0])}."
    if family == "compare_factorizations":
        return (
            f"Find the difference between the number of prime factors of {v[0]} and {v[1]}, "
            "counting repeated factors (first minus second)."
        )
    if family == "lcm_from_factorizations":
        return f"Using prime factors, find the LCM of {v[0]} and {v[1]}."
    raise ValueError(f"Unknown family: {family}")


def _answer_text(spec: dict) -> str:
    return str(_evaluate(spec))


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
    family = "factor_small"
    limit = FAMILY_CAPS["level_1"][family]
    emitted = 0
    for exponents in itertools.product(range(0, 4), range(0, 3), range(0, 3)):
        if sum(exponents) < 2:
            continue
        n = (2 ** exponents[0]) * (3 ** exponents[1]) * (5 ** exponents[2])
        if n < 12 or n > 240:
            continue
        yield {
            "family": family,
            "values": (n,),
            "canonical_key": f"{family}:{n}",
            "case_id": f"{family}:{n}",
            "family_id": family,
        }
        emitted += 1
        if emitted >= limit:
            return


def iter_level2_specs() -> Iterable[dict]:
    budgets = FAMILY_CAPS["level_2"]
    emitted = 0
    for exponents in itertools.product(range(1, 5), range(0, 4), range(0, 3), range(0, 2)):
        n = (2 ** exponents[0]) * (3 ** exponents[1]) * (5 ** exponents[2]) * (7 ** exponents[3])
        if n < 24 or n > 900:
            continue
        yield {
            "family": "factor_with_powers",
            "values": (n,),
            "canonical_key": f"factor_with_powers:{n}",
            "case_id": f"factor_with_powers:{n}",
            "family_id": "factor_with_powers",
        }
        emitted += 1
        if emitted >= budgets["factor_with_powers"]:
            break

    emitted = 0
    for exponents in itertools.product(range(0, 5), range(0, 4), range(0, 3)):
        if sum(exponents) < 2:
            continue
        n = (2 ** exponents[0]) * (3 ** exponents[1]) * (5 ** exponents[2])
        if n < 18 or n > 600:
            continue
        yield {
            "family": "count_prime_factors",
            "values": (n,),
            "canonical_key": f"count_prime_factors:{n}",
            "case_id": f"count_prime_factors:{n}",
            "family_id": "count_prime_factors",
        }
        emitted += 1
        if emitted >= budgets["count_prime_factors"]:
            return


def iter_level3_specs() -> Iterable[dict]:
    budgets = FAMILY_CAPS["level_3"]
    emitted = 0
    for exponents in itertools.product(range(0, 5), range(0, 4), range(0, 3), range(0, 3)):
        if sum(exponents) < 2:
            continue
        n = (2 ** exponents[0]) * (3 ** exponents[1]) * (5 ** exponents[2]) * (7 ** exponents[3])
        if n < 24 or n > 1260:
            continue
        yield {
            "family": "greatest_prime_factor",
            "values": (n,),
            "canonical_key": f"greatest_prime_factor:{n}",
            "case_id": f"greatest_prime_factor:{n}",
            "family_id": "greatest_prime_factor",
        }
        emitted += 1
        if emitted >= budgets["greatest_prime_factor"]:
            break

    emitted = 0
    for exponents in itertools.product(range(1, 4), range(1, 3), range(0, 3), range(0, 2)):
        n = (2 ** exponents[0]) * (3 ** exponents[1]) * (5 ** exponents[2]) * (7 ** exponents[3])
        if n > 900:
            continue
        partial = 2 ** exponents[0]
        if exponents[2]:
            partial *= 5
        yield {
            "family": "missing_factor",
            "values": (n, partial),
            "canonical_key": f"missing_factor:{n}:{partial}",
            "case_id": f"missing_factor:{n}:{partial}",
            "family_id": "missing_factor",
        }
        emitted += 1
        if emitted >= budgets["missing_factor"]:
            return


def iter_level4_specs() -> Iterable[dict]:
    budgets = FAMILY_CAPS["level_4"]
    emitted = 0
    for exponents in itertools.product(range(1, 6), range(1, 4), range(0, 4), range(0, 3), range(0, 2)):
        n = (2 ** exponents[0]) * (3 ** exponents[1]) * (5 ** exponents[2]) * (7 ** exponents[3]) * (11 ** exponents[4])
        if n < 90 or n > 4000:
            continue
        yield {
            "family": "factor_large_composite",
            "values": (n,),
            "canonical_key": f"factor_large_composite:{n}",
            "case_id": f"factor_large_composite:{n}",
            "family_id": "factor_large_composite",
        }
        emitted += 1
        if emitted >= budgets["factor_large_composite"]:
            break

    emitted = 0
    for exponents in itertools.product(range(0, 5), range(0, 4), range(0, 3), range(0, 2)):
        if sum(exponents) < 2:
            continue
        n = (2 ** exponents[0]) * (3 ** exponents[1]) * (5 ** exponents[2]) * (7 ** exponents[3])
        if n < 24 or n > 1800:
            continue
        yield {
            "family": "reconstruct_from_factorization",
            "values": (n,),
            "canonical_key": f"reconstruct_from_factorization:{n}",
            "case_id": f"reconstruct_from_factorization:{n}",
            "family_id": "reconstruct_from_factorization",
        }
        emitted += 1
        if emitted >= budgets["reconstruct_from_factorization"]:
            return


def iter_level5_specs() -> Iterable[dict]:
    budgets = FAMILY_CAPS["level_5"]
    emitted = 0
    numbers = []
    for exponents in itertools.product(range(0, 5), range(0, 4), range(0, 3), range(0, 2)):
        if sum(exponents) < 2:
            continue
        n = (2 ** exponents[0]) * (3 ** exponents[1]) * (5 ** exponents[2]) * (7 ** exponents[3])
        if 30 <= n <= 1200:
            numbers.append(n)
    numbers = sorted(set(numbers))
    for a in numbers:
        for b in numbers:
            if a >= b:
                continue
            yield {
                "family": "compare_factorizations",
                "values": (a, b),
                "canonical_key": f"compare_factorizations:{a}:{b}",
                "case_id": f"compare_factorizations:{a}:{b}",
                "family_id": "compare_factorizations",
            }
            emitted += 1
            if emitted >= budgets["compare_factorizations"]:
                break
        if emitted >= budgets["compare_factorizations"]:
            break

    emitted = 0
    for i, a in enumerate(numbers):
        for b in numbers[i + 1:]:
            if abs(a * b) // math.gcd(a, b) > 3000:
                continue
            yield {
                "family": "lcm_from_factorizations",
                "values": (a, b),
                "canonical_key": f"lcm_from_factorizations:{a}:{b}",
                "case_id": f"lcm_from_factorizations:{a}:{b}",
                "family_id": "lcm_from_factorizations",
            }
            emitted += 1
            if emitted >= budgets["lcm_from_factorizations"]:
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
    pool = list(itertools.islice(_iter_specs(difficulty), 0, min(LEVEL_SPEC_CAPS[level], MAX_ITER_SAMPLES)))
    rng = random.Random(_stable_seed(seed, difficulty, offset, stride, "generate_unique"))
    rng.shuffle(pool)
    out = []
    seen = set()
    for idx in range(max(0, int(offset)), len(pool), max(1, int(stride))):
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
    pool = list(itertools.islice(_iter_specs(difficulty), 0, min(LEVEL_SPEC_CAPS[level], MAX_ITER_SAMPLES)))
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
        "level_1": ["basic prime factorizations of small composites"],
        "level_2": ["adds exponent notation and counting repeated prime factors"],
        "level_3": ["adds greatest-prime-factor questions and missing-factor reasoning"],
        "level_4": ["extends to larger composites and reconstructing values from prime powers"],
        "level_5": ["adds comparisons across factorizations and LCM reasoning from prime factors"],
    }


