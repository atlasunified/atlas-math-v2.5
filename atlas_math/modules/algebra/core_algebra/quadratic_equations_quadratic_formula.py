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
    "Solve the quadratic equation using the quadratic formula: {problem}",
    "Apply the quadratic formula and solve: {problem}",
    "Find all real solutions: {problem}",
    "Solve for x: {problem}",
]
MODULE_INFO = {
    "module_id": "algebra.quadratic_equations_quadratic_formula",
    "name": "Quadratic Equations Quadratic Formula",
    "topic": "algebra",
    "subtopic": "core_algebra",
    "difficulty_levels": ["level_1", "level_2", "level_3", "level_4", "level_5"],
    "enabled": True,
}
LEVEL_SPEC_CAPS = {"level_1": 700, "level_2": 900, "level_3": 1000, "level_4": 1200, "level_5": 1400}
FAMILY_CAPS = {
    "level_1": {"integer_roots": 700},
    "level_2": {"rational_roots": 900},
    "level_3": {"irrational_roots": 1000},
    "level_4": {"double_root": 1200},
    "level_5": {"no_real_solution": 1400},
}
CAPACITY_HINTS = {k: {"value": v, "quality": "capped"} for k, v in LEVEL_SPEC_CAPS.items()}

def curriculum():
    return {
        "level_1": ["solve quadratics with integer roots by formula"],
        "level_2": ["solve quadratics with rational roots"],
        "level_3": ["solve quadratics with irrational real roots"],
        "level_4": ["identify and solve repeated-root quadratics"],
        "level_5": ["recognize discriminant-negative quadratics with no real roots"],
    }

def iter_level1_specs():
    limit = FAMILY_CAPS["level_1"]["integer_roots"]
    emitted = 0
    for a in range(1, 11):
        for r1 in range(-12, 13):
            if r1 == 0:
                continue
            for r2 in range(r1, 13):
                if r2 == 0:
                    continue
                b = -a * (r1 + r2)
                c = a * r1 * r2
                problem = f"{a}x^2 {b:+d}x {c:+d} = 0"
                answer = ", ".join(_fmt_number(v) for v in sorted({Fraction(r1), Fraction(r2)}))
                yield _spec("integer_roots", (a, r1, r2), problem, answer)
                emitted += 1
                if emitted >= limit:
                    return

def iter_level2_specs():
    limit = FAMILY_CAPS["level_2"]["rational_roots"]
    emitted = 0
    for denom in range(2, 8):
        for p in range(-10, 11):
            if p == 0:
                continue
            for q in range(-10, 11):
                if q == 0:
                    continue
                r1 = Fraction(p, denom)
                r2 = Fraction(q, denom)
                a = denom * denom
                b = -a * (r1 + r2)
                c = a * r1 * r2
                if b.denominator != 1 or c.denominator != 1:
                    continue
                problem = f"{a}x^2 {int(b):+d}x {int(c):+d} = 0"
                answer = ", ".join(_fmt_number(v) for v in sorted({r1, r2}))
                yield _spec("rational_roots", (denom, p, q), problem, answer)
                emitted += 1
                if emitted >= limit:
                    return

def iter_level3_specs():
    limit = FAMILY_CAPS["level_3"]["irrational_roots"]
    emitted = 0
    nonsq = [n for n in range(2, 51) if isqrt(n) ** 2 != n]
    for h in range(-12, 13):
        for k in nonsq:
            problem = f"x^2 {(-2*h):+d}x + {h*h-k} = 0"
            answer = f"{h} - sqrt({k}), {h} + sqrt({k})"
            yield _spec("irrational_roots", (h, k), problem, answer)
            emitted += 1
            if emitted >= limit:
                return

def iter_level4_specs():
    limit = FAMILY_CAPS["level_4"]["double_root"]
    emitted = 0
    for a in range(1, 16):
        for r in range(-20, 21):
            b = -2 * a * r
            c = a * r * r
            problem = f"{a}x^2 {b:+d}x {c:+d} = 0"
            answer = _fmt_number(Fraction(r))
            yield _spec("double_root", (a, r), problem, answer)
            emitted += 1
            if emitted >= limit:
                return

def iter_level5_specs():
    limit = FAMILY_CAPS["level_5"]["no_real_solution"]
    emitted = 0
    for h in range(-12, 13):
        for k in range(1, 41):
            problem = f"x^2 {(-2*h):+d}x + {h*h + k} = 0"
            answer = "no real solution"
            yield _spec("no_real_solution", (h, k), problem, answer)
            emitted += 1
            if emitted >= limit:
                return


