from __future__ import annotations

import itertools
import random
from typing import Iterable

from atlas_math.modules.shared.common import make_sample

MODULE_INFO = {
    "module_id": "arithmetic.scientific_notation_operations",
    "name": "Scientific Notation Operations",
    "topic": "arithmetic",
    "subtopic": "core_arithmetic",
    "difficulty_levels": ["level_1", "level_2", "level_3", "level_4", "level_5"],
    "enabled": True,
}

INSTRUCTIONS = [
    "Compute the expression in scientific notation: {problem}",
    "Work through the scientific notation operation: {problem}",
    "Evaluate and simplify the result: {problem}",
    "Solve the scientific notation problem carefully: {problem}",
]

LEVEL_SPEC_CAPS = {
    "level_1": 1200,
    "level_2": 1500,
    "level_3": 1800,
    "level_4": 2200,
    "level_5": 2600,
}

FAMILY_CAPS = {
    "level_1": {"multiply_powers_of_ten": 1200},
    "level_2": {"multiply_sci": 750, "divide_powers_of_ten": 750},
    "level_3": {"divide_sci": 900, "add_same_exponent": 900},
    "level_4": {"add_adjust_needed": 1100, "subtract_same_exponent": 1100},
    "level_5": {"mixed_two_step": 1300, "word_style_scale": 1300},
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


def _fmt_decimal(value: float) -> str:
    return f"{value:.10f}".rstrip("0").rstrip(".")


def _normalize(mantissa: float, exponent: int):
    while abs(mantissa) >= 10:
        mantissa /= 10
        exponent += 1
    while 0 < abs(mantissa) < 1:
        mantissa *= 10
        exponent -= 1
    return round(mantissa, 10), exponent


def _sci(mantissa: float, exponent: int) -> str:
    return f"{_fmt_decimal(mantissa)} × 10^{exponent}"


def _evaluate(spec: dict) -> str:
    family = spec["family"]
    v = spec["values"]
    if family == "multiply_powers_of_ten":
        return _sci(1.0, v[0] + v[1])
    if family == "multiply_sci":
        m, e = _normalize(v[0] * v[2], v[1] + v[3])
        return _sci(m, e)
    if family == "divide_powers_of_ten":
        return _sci(1.0, v[0] - v[1])
    if family == "divide_sci":
        m, e = _normalize(v[0] / v[2], v[1] - v[3])
        return _sci(m, e)
    if family == "add_same_exponent":
        m, e = _normalize(v[0] + v[2], v[1])
        return _sci(m, e)
    if family == "add_adjust_needed":
        total = v[0] * (10 ** v[1]) + v[2] * (10 ** v[3])
        m, e = _normalize(total, 0)
        return _sci(m, e)
    if family == "subtract_same_exponent":
        m, e = _normalize(v[0] - v[2], v[1])
        return _sci(m, e)
    if family == "mixed_two_step":
        total = (v[0] * (10 ** v[1]) * v[2] * (10 ** v[3])) / (v[4] * (10 ** v[5]))
        m, e = _normalize(total, 0)
        return _sci(m, e)
    if family == "word_style_scale":
        total = v[0] * (10 ** v[1]) * v[2]
        m, e = _normalize(total, 0)
        return _sci(m, e)
    raise ValueError(f"Unknown family: {family}")


def _problem_text(spec: dict) -> str:
    family = spec["family"]
    v = spec["values"]
    if family == "multiply_powers_of_ten":
        return f"Compute 10^{v[0]} × 10^{v[1]}. Write the answer in scientific notation."
    if family == "multiply_sci":
        return f"Compute {_sci(v[0], v[1])} × {_sci(v[2], v[3])}."
    if family == "divide_powers_of_ten":
        return f"Compute 10^{v[0]} ÷ 10^{v[1]}. Write the answer in scientific notation."
    if family == "divide_sci":
        return f"Compute {_sci(v[0], v[1])} ÷ {_sci(v[2], v[3])}."
    if family == "add_same_exponent":
        return f"Add {_sci(v[0], v[1])} + {_sci(v[2], v[1])}."
    if family == "add_adjust_needed":
        return f"Add {_sci(v[0], v[1])} + {_sci(v[2], v[3])}."
    if family == "subtract_same_exponent":
        return f"Subtract {_sci(v[2], v[1])} from {_sci(v[0], v[1])}."
    if family == "mixed_two_step":
        return f"Compute ({_sci(v[0], v[1])} × {_sci(v[2], v[3])}) ÷ {_sci(v[4], v[5])}."
    if family == "word_style_scale":
        return f"A quantity of {_sci(v[0], v[1])} is scaled by a factor of {v[2]}. What is the result in scientific notation?"
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
    family = "multiply_powers_of_ten"
    limit = FAMILY_CAPS["level_1"][family]
    emitted = 0
    for e1 in range(-6, 13):
        for e2 in range(-6, 13):
            yield {
                "family": family,
                "values": (e1, e2),
                "canonical_key": f"{family}:{e1}:{e2}",
                "case_id": f"{family}:{e1}:{e2}",
                "family_id": family,
            }
            emitted += 1
            if emitted >= limit:
                return


def iter_level2_specs() -> Iterable[dict]:
    budgets = FAMILY_CAPS["level_2"]
    emitted = 0
    mantissas = (1.2, 1.5, 2.0, 2.4, 3.0, 3.5, 4.0, 4.8, 5.0, 6.0, 7.5, 8.0)
    for m1 in mantissas:
        for e1 in range(-4, 7):
            for m2 in mantissas:
                for e2 in range(-4, 7):
                    yield {
                        "family": "multiply_sci",
                        "values": (m1, e1, m2, e2),
                        "canonical_key": f"multiply_sci:{m1}:{e1}:{m2}:{e2}",
                        "case_id": f"multiply_sci:{m1}:{e1}:{m2}:{e2}",
                        "family_id": "multiply_sci",
                    }
                    emitted += 1
                    if emitted >= budgets["multiply_sci"]:
                        break
                if emitted >= budgets["multiply_sci"]:
                    break
            if emitted >= budgets["multiply_sci"]:
                break
        if emitted >= budgets["multiply_sci"]:
            break

    emitted = 0
    for e1 in range(-6, 13):
        for e2 in range(-6, 13):
            yield {
                "family": "divide_powers_of_ten",
                "values": (e1, e2),
                "canonical_key": f"divide_powers_of_ten:{e1}:{e2}",
                "case_id": f"divide_powers_of_ten:{e1}:{e2}",
                "family_id": "divide_powers_of_ten",
            }
            emitted += 1
            if emitted >= budgets["divide_powers_of_ten"]:
                return


def iter_level3_specs() -> Iterable[dict]:
    budgets = FAMILY_CAPS["level_3"]
    emitted = 0
    mantissas = (1.2, 1.5, 2.0, 2.4, 3.0, 3.5, 4.0, 4.8, 5.0, 6.0, 7.5, 8.0)
    for m1 in mantissas:
        for e1 in range(-4, 7):
            for m2 in mantissas:
                for e2 in range(-4, 7):
                    if m2 == 0:
                        continue
                    yield {
                        "family": "divide_sci",
                        "values": (m1, e1, m2, e2),
                        "canonical_key": f"divide_sci:{m1}:{e1}:{m2}:{e2}",
                        "case_id": f"divide_sci:{m1}:{e1}:{m2}:{e2}",
                        "family_id": "divide_sci",
                    }
                    emitted += 1
                    if emitted >= budgets["divide_sci"]:
                        break
                if emitted >= budgets["divide_sci"]:
                    break
            if emitted >= budgets["divide_sci"]:
                break
        if emitted >= budgets["divide_sci"]:
            break

    emitted = 0
    for exponent in range(-5, 7):
        for m1 in (1.2, 1.5, 2.3, 3.4, 4.8, 5.6, 6.7, 7.2, 8.1, 9.4):
            for m2 in (1.1, 1.4, 2.2, 3.1, 4.0, 5.2, 6.3, 7.5, 8.0, 9.0):
                yield {
                    "family": "add_same_exponent",
                    "values": (m1, exponent, m2),
                    "canonical_key": f"add_same_exponent:{m1}:{exponent}:{m2}",
                    "case_id": f"add_same_exponent:{m1}:{exponent}:{m2}",
                    "family_id": "add_same_exponent",
                }
                emitted += 1
                if emitted >= budgets["add_same_exponent"]:
                    return


def iter_level4_specs() -> Iterable[dict]:
    budgets = FAMILY_CAPS["level_4"]
    emitted = 0
    for m1 in (1.2, 1.5, 2.3, 3.4, 4.8, 5.6, 6.7, 7.2, 8.1, 9.4):
        for e1 in range(-4, 7):
            for m2 in (1.1, 1.4, 2.2, 3.1, 4.0, 5.2, 6.3, 7.5, 8.0, 9.0):
                for e2 in range(-4, 7):
                    if e1 == e2:
                        continue
                    yield {
                        "family": "add_adjust_needed",
                        "values": (m1, e1, m2, e2),
                        "canonical_key": f"add_adjust_needed:{m1}:{e1}:{m2}:{e2}",
                        "case_id": f"add_adjust_needed:{m1}:{e1}:{m2}:{e2}",
                        "family_id": "add_adjust_needed",
                    }
                    emitted += 1
                    if emitted >= budgets["add_adjust_needed"]:
                        break
                if emitted >= budgets["add_adjust_needed"]:
                    break
            if emitted >= budgets["add_adjust_needed"]:
                break
        if emitted >= budgets["add_adjust_needed"]:
            break

    emitted = 0
    for exponent in range(-5, 7):
        for m1 in (2.2, 3.5, 4.3, 5.4, 6.1, 7.6, 8.8, 9.5):
            for m2 in (1.1, 1.4, 2.0, 2.3, 3.2, 4.4, 5.1, 6.0):
                if m1 <= m2:
                    continue
                yield {
                    "family": "subtract_same_exponent",
                    "values": (m1, exponent, m2),
                    "canonical_key": f"subtract_same_exponent:{m1}:{exponent}:{m2}",
                    "case_id": f"subtract_same_exponent:{m1}:{exponent}:{m2}",
                    "family_id": "subtract_same_exponent",
                }
                emitted += 1
                if emitted >= budgets["subtract_same_exponent"]:
                    return


def iter_level5_specs() -> Iterable[dict]:
    budgets = FAMILY_CAPS["level_5"]
    emitted = 0
    mantissas = (1.2, 1.5, 2.0, 2.4, 3.0, 3.5, 4.0, 4.8, 5.0, 6.0, 7.5, 8.0)
    for a in mantissas:
        for ea in range(-3, 6):
            for b in mantissas:
                for eb in range(-3, 6):
                    for c in mantissas:
                        for ec in range(-3, 6):
                            yield {
                                "family": "mixed_two_step",
                                "values": (a, ea, b, eb, c, ec),
                                "canonical_key": f"mixed_two_step:{a}:{ea}:{b}:{eb}:{c}:{ec}",
                                "case_id": f"mixed_two_step:{a}:{ea}:{b}:{eb}:{c}:{ec}",
                                "family_id": "mixed_two_step",
                            }
                            emitted += 1
                            if emitted >= budgets["mixed_two_step"]:
                                break
                        if emitted >= budgets["mixed_two_step"]:
                            break
                    if emitted >= budgets["mixed_two_step"]:
                        break
                if emitted >= budgets["mixed_two_step"]:
                    break
            if emitted >= budgets["mixed_two_step"]:
                break
        if emitted >= budgets["mixed_two_step"]:
            break

    emitted = 0
    for mantissa in (1.2, 1.5, 2.3, 3.4, 4.8, 5.6, 6.7, 7.2, 8.1, 9.4):
        for exponent in range(-7, 8):
            for factor in (2, 3, 4, 5, 6, 7, 8, 9):
                yield {
                    "family": "word_style_scale",
                    "values": (mantissa, exponent, factor),
                    "canonical_key": f"word_style_scale:{mantissa}:{exponent}:{factor}",
                    "case_id": f"word_style_scale:{mantissa}:{exponent}:{factor}",
                    "family_id": "word_style_scale",
                }
                emitted += 1
                if emitted >= budgets["word_style_scale"]:
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
        "level_1": ["multiplies powers of ten"],
        "level_2": ["adds multiplication of numbers in scientific notation and division of powers of ten"],
        "level_3": ["adds division in scientific notation and addition with matching exponents"],
        "level_4": ["adds exponent-adjusted addition and same-exponent subtraction"],
        "level_5": ["adds multi-step operation chains and scale-factor word-style prompts"],
    }


