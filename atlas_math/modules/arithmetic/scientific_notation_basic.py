from __future__ import annotations

import itertools
import random
from typing import Iterable

from atlas_math.modules.shared.common import make_sample

MODULE_INFO = {
    "module_id": "arithmetic.scientific_notation_basic",
    "name": "Scientific Notation Basic",
    "topic": "arithmetic",
    "subtopic": "core_arithmetic",
    "difficulty_levels": ["level_1", "level_2", "level_3", "level_4", "level_5"],
    "enabled": True,
}

INSTRUCTIONS = [
    "Write the number in the requested form: {problem}",
    "Convert carefully using scientific notation: {problem}",
    "Solve the scientific notation conversion: {problem}",
    "Express the quantity correctly: {problem}",
]

LEVEL_SPEC_CAPS = {
    "level_1": 1200,
    "level_2": 1500,
    "level_3": 1800,
    "level_4": 2200,
    "level_5": 2600,
}

FAMILY_CAPS = {
    "level_1": {"whole_to_sci": 1200},
    "level_2": {"decimal_to_sci": 750, "sci_to_whole": 750},
    "level_3": {"sci_to_decimal": 900, "negative_exponent_from_decimal": 900},
    "level_4": {"compare_magnitude": 1100, "normalize_not_scientific": 1100},
    "level_5": {"choose_equivalent": 1300, "place_decimal_steps": 1300},
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


def _sci(mantissa, exponent: int) -> str:
    m = _fmt_decimal(float(mantissa))
    return f"{m} × 10^{exponent}"


def _to_plain_text(mantissa, exponent: int) -> str:
    value = float(mantissa) * (10 ** exponent)
    if exponent >= 0 and value.is_integer():
        return str(int(value))
    return _fmt_decimal(value)


def _evaluate(spec: dict) -> str:
    family = spec["family"]
    vals = spec["values"]
    if family in {"whole_to_sci", "decimal_to_sci", "negative_exponent_from_decimal", "normalize_not_scientific", "choose_equivalent"}:
        return _sci(vals[1], vals[2])
    if family in {"sci_to_whole", "sci_to_decimal", "place_decimal_steps"}:
        return _to_plain_text(vals[0], vals[1])
    if family == "compare_magnitude":
        left = float(vals[0]) * (10 ** vals[1])
        right = float(vals[2]) * (10 ** vals[3])
        return ">" if left > right else "<" if left < right else "="
    raise ValueError(f"Unknown family: {family}")


def _problem_text(spec: dict) -> str:
    family = spec["family"]
    vals = spec["values"]
    if family == "whole_to_sci":
        return f"Write {vals[0]} in scientific notation."
    if family == "decimal_to_sci":
        return f"Write {_fmt_decimal(vals[0])} in scientific notation."
    if family == "sci_to_whole":
        return f"Write {_sci(vals[0], vals[1])} as an ordinary number."
    if family == "sci_to_decimal":
        return f"Convert {_sci(vals[0], vals[1])} to standard decimal form."
    if family == "negative_exponent_from_decimal":
        return f"Express {_fmt_decimal(vals[0])} in scientific notation."
    if family == "compare_magnitude":
        return f"Compare {_sci(vals[0], vals[1])} and {_sci(vals[2], vals[3])} using >, <, or =."
    if family == "normalize_not_scientific":
        return f"Rewrite {vals[0]} × 10^{vals[1]} in proper scientific notation."
    if family == "choose_equivalent":
        return f"Which scientific notation is equivalent to the number represented by {vals[0]} × 10^{vals[1]}?"
    if family == "place_decimal_steps":
        direction = "right" if vals[1] >= 0 else "left"
        return f"Move the decimal point in {vals[0]} {abs(vals[1])} places to the {direction}. What number do you get?"
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
    family = "whole_to_sci"
    limit = FAMILY_CAPS["level_1"][family]
    emitted = 0
    for mantissa in range(11, 100):
        for exponent in range(2, 8):
            number = mantissa * (10 ** exponent)
            yield {
                "family": family,
                "values": (number, mantissa / 10, exponent + 1),
                "canonical_key": f"{family}:{number}",
                "case_id": f"{family}:{number}",
                "family_id": family,
            }
            emitted += 1
            if emitted >= limit:
                return


def iter_level2_specs() -> Iterable[dict]:
    budgets = FAMILY_CAPS["level_2"]
    emitted = 0
    for mantissa in range(11, 100):
        for exponent in range(1, 6):
            number = (mantissa / 10) * (10 ** exponent)
            if 1 <= abs(number) < 10:
                continue
            yield {
                "family": "decimal_to_sci",
                "values": (number, mantissa / 10, exponent),
                "canonical_key": f"decimal_to_sci:{number}",
                "case_id": f"decimal_to_sci:{number}",
                "family_id": "decimal_to_sci",
            }
            emitted += 1
            if emitted >= budgets["decimal_to_sci"]:
                break
        if emitted >= budgets["decimal_to_sci"]:
            break

    emitted = 0
    for mantissa in (1.2, 1.5, 2.3, 3.4, 4.8, 5.6, 6.7, 7.2, 8.9, 9.1):
        for exponent in range(2, 9):
            yield {
                "family": "sci_to_whole",
                "values": (mantissa, exponent),
                "canonical_key": f"sci_to_whole:{mantissa}:{exponent}",
                "case_id": f"sci_to_whole:{mantissa}:{exponent}",
                "family_id": "sci_to_whole",
            }
            emitted += 1
            if emitted >= budgets["sci_to_whole"]:
                return


def iter_level3_specs() -> Iterable[dict]:
    budgets = FAMILY_CAPS["level_3"]
    emitted = 0
    for mantissa in (1.2, 1.5, 2.3, 3.4, 4.8, 5.6, 6.7, 7.2, 8.9, 9.1):
        for exponent in range(-5, 0):
            yield {
                "family": "sci_to_decimal",
                "values": (mantissa, exponent),
                "canonical_key": f"sci_to_decimal:{mantissa}:{exponent}",
                "case_id": f"sci_to_decimal:{mantissa}:{exponent}",
                "family_id": "sci_to_decimal",
            }
            emitted += 1
            if emitted >= budgets["sci_to_decimal"]:
                break
        if emitted >= budgets["sci_to_decimal"]:
            break

    emitted = 0
    for mantissa in range(11, 100):
        for exponent in range(1, 7):
            value = (mantissa / 10) / (10 ** exponent)
            yield {
                "family": "negative_exponent_from_decimal",
                "values": (value, mantissa / 10, -exponent),
                "canonical_key": f"negative_exponent_from_decimal:{mantissa}:{exponent}",
                "case_id": f"negative_exponent_from_decimal:{mantissa}:{exponent}",
                "family_id": "negative_exponent_from_decimal",
            }
            emitted += 1
            if emitted >= budgets["negative_exponent_from_decimal"]:
                return


def iter_level4_specs() -> Iterable[dict]:
    budgets = FAMILY_CAPS["level_4"]
    emitted = 0
    mantissas = (1.2, 1.5, 2.4, 3.6, 4.8, 5.1, 6.3, 7.4, 8.5, 9.7)
    for left_m in mantissas:
        for left_e in range(-3, 7):
            for right_m in mantissas:
                for right_e in range(-3, 7):
                    yield {
                        "family": "compare_magnitude",
                        "values": (left_m, left_e, right_m, right_e),
                        "canonical_key": f"compare_magnitude:{left_m}:{left_e}:{right_m}:{right_e}",
                        "case_id": f"compare_magnitude:{left_m}:{left_e}:{right_m}:{right_e}",
                        "family_id": "compare_magnitude",
                    }
                    emitted += 1
                    if emitted >= budgets["compare_magnitude"]:
                        break
                if emitted >= budgets["compare_magnitude"]:
                    break
            if emitted >= budgets["compare_magnitude"]:
                break
        if emitted >= budgets["compare_magnitude"]:
            break

    emitted = 0
    for mantissa in range(12, 100):
        for exponent in range(-4, 7):
            raw_m = mantissa
            yield {
                "family": "normalize_not_scientific",
                "values": (raw_m, exponent, raw_m / 10, exponent + 1),
                "canonical_key": f"normalize_not_scientific:{raw_m}:{exponent}",
                "case_id": f"normalize_not_scientific:{raw_m}:{exponent}",
                "family_id": "normalize_not_scientific",
            }
            emitted += 1
            if emitted >= budgets["normalize_not_scientific"]:
                return


def iter_level5_specs() -> Iterable[dict]:
    budgets = FAMILY_CAPS["level_5"]
    emitted = 0
    for raw_m in range(12, 100):
        for exponent in range(-5, 8):
            yield {
                "family": "choose_equivalent",
                "values": (raw_m, exponent, raw_m / 10, exponent + 1),
                "canonical_key": f"choose_equivalent:{raw_m}:{exponent}",
                "case_id": f"choose_equivalent:{raw_m}:{exponent}",
                "family_id": "choose_equivalent",
            }
            emitted += 1
            if emitted >= budgets["choose_equivalent"]:
                break
        if emitted >= budgets["choose_equivalent"]:
            break

    emitted = 0
    for mantissa in (1.2, 1.5, 2.3, 3.4, 4.8, 5.6, 6.7, 7.2, 8.9, 9.1):
        for exponent in range(-7, 8):
            yield {
                "family": "place_decimal_steps",
                "values": (mantissa, exponent),
                "canonical_key": f"place_decimal_steps:{mantissa}:{exponent}",
                "case_id": f"place_decimal_steps:{mantissa}:{exponent}",
                "family_id": "place_decimal_steps",
            }
            emitted += 1
            if emitted >= budgets["place_decimal_steps"]:
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
        "level_1": ["writes large whole numbers in scientific notation"],
        "level_2": ["adds decimal-to-scientific conversion and whole-number expansion from notation"],
        "level_3": ["extends to negative exponents and decimal-form expansions"],
        "level_4": ["adds comparing magnitudes and normalizing non-standard forms"],
        "level_5": ["adds equivalent-form reasoning and explicit decimal-point movement"],
    }


