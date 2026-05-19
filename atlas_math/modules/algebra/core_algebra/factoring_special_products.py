from __future__ import annotations

import itertools
import random
from fractions import Fraction
from math import isqrt
from typing import Iterable

from atlas_math.modules.shared.common import make_sample

MAX_SPEC_PREFIX = 5000
MAX_GENERATE_MULTIPLIER = 8
MAX_ITER_SAMPLES = 4096


def _level_num(difficulty: str) -> int:
    try:
        value = int(str(difficulty).rsplit("_", 1)[-1])
    except Exception:
        value = 1
    return max(1, min(5, value))


def _stable_seed(*parts) -> str:
    return "|".join(str(p) for p in parts)


def _take(iterable: Iterable[dict], n: int) -> Iterable[dict]:
    for idx, item in enumerate(iterable):
        if idx >= max(0, int(n)):
            break
        yield item


def _fmt_number(value) -> str:
    if isinstance(value, Fraction):
        if value.denominator == 1:
            return str(value.numerator)
        return f"{value.numerator}/{value.denominator}"
    return str(value)


def _fmt_signed(value) -> str:
    if isinstance(value, Fraction):
        if value.denominator == 1:
            value = value.numerator
        else:
            return ("+ " if value >= 0 else "- ") + _fmt_number(abs(value))
    return ("+ " if value >= 0 else "- ") + str(abs(value))


def _clean_linear(a, b=0, variable="x") -> str:
    parts = []
    if a != 0:
        if a == 1:
            parts.append(variable)
        elif a == -1:
            parts.append(f"-{variable}")
        else:
            parts.append(f"{a}{variable}")
    if b != 0:
        if parts:
            parts.append((" + " if b > 0 else " - ") + str(abs(b)))
        else:
            parts.append(str(b))
    return "".join(parts) if parts else "0"


def _sample_from_spec(spec: dict, difficulty: str, instruction_idx: int = 0) -> dict:
    answer = spec["answer"]
    metadata = {
        "family": spec["family"],
        "level_number": _level_num(difficulty),
        "structured": True,
        "canonical_key": spec["canonical_key"],
        "case_id": spec["case_id"],
        "family_id": spec["family_id"],
        "template_id": spec["family"],
        "final_answer": answer,
        "values": list(spec.get("values", [])),
    }
    instruction = INSTRUCTIONS[instruction_idx % len(INSTRUCTIONS)].format(problem=spec["problem"])
    return make_sample(
        module_id=MODULE_INFO["module_id"],
        topic=MODULE_INFO["topic"],
        subtopic=MODULE_INFO["subtopic"],
        difficulty=difficulty,
        instruction=instruction,
        input_text=spec["problem"],
        answer=answer,
        metadata=metadata,
    )


def _spec(family: str, values: tuple, problem: str, answer: str):
    canonical = ":".join([family] + [str(v) for v in values])
    return {
        "family": family,
        "values": values,
        "problem": problem,
        "answer": answer,
        "canonical_key": canonical,
        "case_id": canonical,
        "family_id": family,
    }


def _iter_specs(difficulty="level_1"):
    level = _level_num(difficulty)
    if level == 1:
        return _take(iter_level1_specs(), LEVEL_SPEC_CAPS["level_1"])
    if level == 2:
        return _take(iter_level2_specs(), LEVEL_SPEC_CAPS["level_2"])
    if level == 3:
        return _take(iter_level3_specs(), LEVEL_SPEC_CAPS["level_3"])
    if level == 4:
        return _take(iter_level4_specs(), LEVEL_SPEC_CAPS["level_4"])
    return _take(iter_level5_specs(), LEVEL_SPEC_CAPS["level_5"])


def estimate_capacity(difficulty="level_1"):
    return dict(CAPACITY_HINTS.get(difficulty, {"value": None, "quality": "unknown"}))


def generate(count=10, difficulty="level_1", seed=None):
    count = max(0, int(count))
    prefix = min(max(count * MAX_GENERATE_MULTIPLIER, 256), MAX_SPEC_PREFIX)
    pool = list(itertools.islice(_iter_specs(difficulty), 0, prefix))
    if not pool or count == 0:
        return []
    rng = random.Random(_stable_seed(MODULE_INFO["module_id"], difficulty, seed, "generate"))
    rng.shuffle(pool)
    return [_sample_from_spec(spec, difficulty, i) for i, spec in enumerate(pool[:count])]


def generate_unique(count=10, difficulty="level_1", offset=0, stride=1, seed=None):
    count = max(0, int(count))
    offset = max(0, int(offset))
    stride = max(1, int(stride))
    pool = list(itertools.islice(_iter_specs(difficulty), 0, MAX_SPEC_PREFIX))
    rng = random.Random(_stable_seed(MODULE_INFO["module_id"], difficulty, seed, offset, stride, "unique"))
    rng.shuffle(pool)
    seen = set()
    ordered = []
    for spec in pool:
        key = spec["canonical_key"]
        if key in seen:
            continue
        seen.add(key)
        ordered.append(spec)
    return [_sample_from_spec(spec, difficulty, i) for i, spec in enumerate(ordered[offset::stride][:count])]


def iter_samples(difficulty="level_1", seed=None):
    max_items = min(LEVEL_SPEC_CAPS.get(difficulty, 1000), MAX_ITER_SAMPLES)
    pool = list(itertools.islice(_iter_specs(difficulty), 0, max_items))
    rng = random.Random(_stable_seed(MODULE_INFO["module_id"], difficulty, seed, "iter"))
    rng.shuffle(pool)
    seen = set()
    for idx, spec in enumerate(pool):
        key = spec["canonical_key"]
        if key in seen:
            continue
        seen.add(key)
        yield _sample_from_spec(spec, difficulty, idx)

INSTRUCTIONS = [
    "Factor the polynomial completely: {problem}",
    "Use a special-product pattern to factor: {problem}",
    "Rewrite in factored form: {problem}",
    "Factor and report the result: {problem}",
]

MODULE_INFO = {
    "module_id": "algebra.factoring_special_products",
    "name": "Factoring Special Products",
    "topic": "algebra",
    "subtopic": "core_algebra",
    "difficulty_levels": ["level_1", "level_2", "level_3", "level_4", "level_5"],
    "enabled": True,
}
LEVEL_SPEC_CAPS = {"level_1": 600, "level_2": 700, "level_3": 900, "level_4": 1000, "level_5": 1200}
FAMILY_CAPS = {
    "level_1": {"difference_of_squares_monomial": 600},
    "level_2": {"difference_of_squares_binomial": 700},
    "level_3": {"perfect_square_trinomial_positive": 900},
    "level_4": {"perfect_square_trinomial_negative": 1000},
    "level_5": {"gcf_then_special": 1200},
}
CAPACITY_HINTS = {k: {"value": v, "quality": "capped"} for k, v in LEVEL_SPEC_CAPS.items()}

def curriculum():
    return {
        "level_1": ["factor differences of squares like a^2x^2 - b^2"],
        "level_2": ["factor differences of squares with binomial square terms"],
        "level_3": ["factor perfect-square trinomials with positive middle term"],
        "level_4": ["factor perfect-square trinomials with negative middle term"],
        "level_5": ["factor out a GCF and then apply a special-product identity"],
    }

def iter_level1_specs():
    limit = FAMILY_CAPS["level_1"]["difference_of_squares_monomial"]
    emitted = 0
    for a in range(1, 26):
        for b in range(1, 26):
            problem = f"{a*a}x^2 - {b*b}"
            answer = f"({a}x - {b})({a}x + {b})"
            yield _spec("difference_of_squares_monomial", (a, b), problem, answer)
            emitted += 1
            if emitted >= limit:
                return

def iter_level2_specs():
    limit = FAMILY_CAPS["level_2"]["difference_of_squares_binomial"]
    emitted = 0
    for a in range(1, 16):
        for b in range(1, 16):
            for c in range(1, 13):
                left = f"x {'+ ' if b > 0 else '- '}{abs(b)}"
                right = f"{a}"
                problem = f"(x + {b})^2 - {a*a}"
                answer = f"(x + {b} - {a})(x + {b} + {a})"
                yield _spec("difference_of_squares_binomial", (a, b, c), problem, answer)
                emitted += 1
                if emitted >= limit:
                    return

def iter_level3_specs():
    limit = FAMILY_CAPS["level_3"]["perfect_square_trinomial_positive"]
    emitted = 0
    for a in range(1, 21):
        for b in range(1, 21):
            problem = f"{a*a}x^2 + {2*a*b}x + {b*b}"
            answer = f"({a}x + {b})^2"
            yield _spec("perfect_square_trinomial_positive", (a, b), problem, answer)
            emitted += 1
            if emitted >= limit:
                return

def iter_level4_specs():
    limit = FAMILY_CAPS["level_4"]["perfect_square_trinomial_negative"]
    emitted = 0
    for a in range(1, 21):
        for b in range(1, 21):
            problem = f"{a*a}x^2 - {2*a*b}x + {b*b}"
            answer = f"({a}x - {b})^2"
            yield _spec("perfect_square_trinomial_negative", (a, b), problem, answer)
            emitted += 1
            if emitted >= limit:
                return

def iter_level5_specs():
    limit = FAMILY_CAPS["level_5"]["gcf_then_special"]
    emitted = 0
    for g in range(2, 16):
        for a in range(1, 13):
            for b in range(1, 13):
                problem = f"{g*a*a}x^2 - {g*b*b}"
                answer = f"{g}({a}x - {b})({a}x + {b})"
                yield _spec("gcf_then_special", (g, a, b), problem, answer)
                emitted += 1
                if emitted >= limit:
                    return


