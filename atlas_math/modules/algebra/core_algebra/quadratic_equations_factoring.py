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
    "Solve the quadratic equation by factoring: {problem}",
    "Factor and solve: {problem}",
    "Find all real solutions: {problem}",
    "Solve for x: {problem}",
]

MODULE_INFO = {
    "module_id": "algebra.quadratic_equations_factoring",
    "name": "Quadratic Equations Factoring",
    "topic": "algebra",
    "subtopic": "core_algebra",
    "difficulty_levels": ["level_1", "level_2", "level_3", "level_4", "level_5"],
    "enabled": True,
}
LEVEL_SPEC_CAPS = {"level_1": 700, "level_2": 900, "level_3": 1100, "level_4": 1300, "level_5": 1500}
FAMILY_CAPS = {
    "level_1": {"monic_positive_roots": 700},
    "level_2": {"monic_mixed_sign_roots": 900},
    "level_3": {"leading_coefficient_gt1": 1100},
    "level_4": {"gcf_then_factor": 1300},
    "level_5": {"quadratic_equals_constant": 1500},
}
CAPACITY_HINTS = {k: {"value": v, "quality": "capped"} for k, v in LEVEL_SPEC_CAPS.items()}

def curriculum():
    return {
        "level_1": ["solve monic quadratics with two positive integer roots"],
        "level_2": ["solve monic quadratics with opposite-sign roots"],
        "level_3": ["solve nonmonic quadratics that factor over integers"],
        "level_4": ["factor out a GCF before solving"],
        "level_5": ["rearrange quadratic equations and solve by factoring"],
    }

def _sol_text(*roots):
    uniq = sorted(set(roots))
    return ", ".join(_fmt_number(r) for r in uniq)

def iter_level1_specs():
    limit = FAMILY_CAPS["level_1"]["monic_positive_roots"]
    emitted = 0
    for r1 in range(1, 26):
        for r2 in range(r1, 26):
            b = -(r1 + r2)
            c = r1 * r2
            problem = f"x^2 {b:+d}x + {c} = 0"
            answer = _sol_text(Fraction(r1), Fraction(r2))
            yield _spec("monic_positive_roots", (r1, r2), problem, answer)
            emitted += 1
            if emitted >= limit:
                return

def iter_level2_specs():
    limit = FAMILY_CAPS["level_2"]["monic_mixed_sign_roots"]
    emitted = 0
    for p in range(1, 26):
        for q in range(1, 26):
            b = q - p
            c = -p * q
            problem = f"x^2 {b:+d}x {c:+d} = 0"
            answer = _sol_text(Fraction(p), Fraction(-q))
            yield _spec("monic_mixed_sign_roots", (p, q), problem, answer)
            emitted += 1
            if emitted >= limit:
                return

def iter_level3_specs():
    limit = FAMILY_CAPS["level_3"]["leading_coefficient_gt1"]
    emitted = 0
    for a in range(2, 11):
        for r1 in range(-12, 13):
            if r1 == 0:
                continue
            for r2 in range(r1, 13):
                if r2 == 0:
                    continue
                b = -a * (r1 + r2)
                c = a * r1 * r2
                problem = f"{a}x^2 {b:+d}x {c:+d} = 0"
                answer = _sol_text(Fraction(r1), Fraction(r2))
                yield _spec("leading_coefficient_gt1", (a, r1, r2), problem, answer)
                emitted += 1
                if emitted >= limit:
                    return

def iter_level4_specs():
    limit = FAMILY_CAPS["level_4"]["gcf_then_factor"]
    emitted = 0
    for g in range(2, 11):
        for r1 in range(1, 16):
            for r2 in range(1, 16):
                b = -g * (r1 + r2)
                c = g * r1 * r2
                problem = f"{g}x^2 {b:+d}x + {c} = 0"
                answer = _sol_text(Fraction(r1), Fraction(r2))
                yield _spec("gcf_then_factor", (g, r1, r2), problem, answer)
                emitted += 1
                if emitted >= limit:
                    return

def iter_level5_specs():
    limit = FAMILY_CAPS["level_5"]["quadratic_equals_constant"]
    emitted = 0
    for r1 in range(-12, 13):
        if r1 == 0:
            continue
        for r2 in range(r1, 13):
            if r2 == 0:
                continue
            for k in range(-12, 13):
                b = -(r1 + r2)
                c = r1 * r2
                rhs = k
                lhs_c = c + k
                problem = f"x^2 {b:+d}x + {lhs_c} = {rhs}"
                answer = _sol_text(Fraction(r1), Fraction(r2))
                yield _spec("quadratic_equals_constant", (r1, r2, k), problem, answer)
                emitted += 1
                if emitted >= limit:
                    return


