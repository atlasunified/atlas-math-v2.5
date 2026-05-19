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
    "Rewrite or interpret the quadratic in vertex form and answer: {problem}",
    "Work with the vertex form and transformations: {problem}",
    "Find the requested vertex-form information: {problem}",
    "Give the vertex-form result: {problem}",
]
MODULE_INFO = {
    "module_id": "algebra.vertex_form_and_transformations",
    "name": "Vertex Form and Transformations",
    "topic": "algebra",
    "subtopic": "core_algebra",
    "difficulty_levels": ["level_1", "level_2", "level_3", "level_4", "level_5"],
    "enabled": True,
}
LEVEL_SPEC_CAPS = {"level_1": 700, "level_2": 900, "level_3": 1000, "level_4": 1200, "level_5": 1400}
FAMILY_CAPS = {
    "level_1": {"identify_vertex": 700},
    "level_2": {"convert_standard_to_vertex": 900},
    "level_3": {"write_from_vertex_point": 1000},
    "level_4": {"describe_transformations": 1200},
    "level_5": {"match_equivalent_forms": 1400},
}
CAPACITY_HINTS = {k: {"value": v, "quality": "capped"} for k, v in LEVEL_SPEC_CAPS.items()}

def curriculum():
    return {
        "level_1": ["identify vertex and axis from vertex form"],
        "level_2": ["convert standard form to vertex form"],
        "level_3": ["write a quadratic from its vertex and a point"],
        "level_4": ["describe quadratic transformations from parameters"],
        "level_5": ["recognize equivalent standard and vertex forms"],
    }

def iter_level1_specs():
    limit = FAMILY_CAPS["level_1"]["identify_vertex"]
    emitted = 0
    for a in [-4, -3, -2, -1, 1, 2, 3, 4]:
        for h in range(-12, 13):
            for k in range(-12, 13):
                problem = f"For y = {a}(x - {h})^2 + {k}, state the vertex."
                answer = f"({h}, {k})"
                yield _spec("identify_vertex", (a, h, k), problem, answer)
                emitted += 1
                if emitted >= limit:
                    return

def iter_level2_specs():
    limit = FAMILY_CAPS["level_2"]["convert_standard_to_vertex"]
    emitted = 0
    for a in [-3, -2, -1, 1, 2, 3]:
        for h in range(-10, 11):
            for k in range(-10, 11):
                b = -2 * a * h
                c = a * h * h + k
                problem = f"Rewrite y = {a}x^2 {b:+d}x {c:+d} in vertex form."
                answer = f"y = {a}(x - {h})^2 + {k}"
                yield _spec("convert_standard_to_vertex", (a, h, k), problem, answer)
                emitted += 1
                if emitted >= limit:
                    return

def iter_level3_specs():
    limit = FAMILY_CAPS["level_3"]["write_from_vertex_point"]
    emitted = 0
    for a in [-4, -3, -2, -1, 1, 2, 3, 4]:
        for h in range(-10, 11):
            for k in range(-10, 11):
                x1 = h + 1
                y1 = a + k
                problem = f"Write the quadratic in vertex form with vertex ({h}, {k}) passing through ({x1}, {y1})."
                answer = f"y = {a}(x - {h})^2 + {k}"
                yield _spec("write_from_vertex_point", (a, h, k), problem, answer)
                emitted += 1
                if emitted >= limit:
                    return

def iter_level4_specs():
    limit = FAMILY_CAPS["level_4"]["describe_transformations"]
    emitted = 0
    for a in [1, 2, 3, -1, -2, -3]:
        for h in range(-10, 11):
            for k in range(-10, 11):
                horizontal = f"right {h}" if h >= 0 else f"left {abs(h)}"
                vertical = f"up {k}" if k >= 0 else f"down {abs(k)}"
                opening = "opens up" if a > 0 else "opens down"
                problem = f"Describe the transformations from y = x^2 to y = {a}(x - {h})^2 + {k}."
                answer = f"{horizontal}; {vertical}; {opening}; vertical stretch factor {abs(a)}"
                yield _spec("describe_transformations", (a, h, k), problem, answer)
                emitted += 1
                if emitted >= limit:
                    return

def iter_level5_specs():
    limit = FAMILY_CAPS["level_5"]["match_equivalent_forms"]
    emitted = 0
    for a in [-3, -2, -1, 1, 2, 3]:
        for h in range(-10, 11):
            for k in range(-10, 11):
                b = -2 * a * h
                c = a * h * h + k
                problem = f"Give the equivalent standard form of y = {a}(x - {h})^2 + {k}."
                answer = f"y = {a}x^2 {b:+d}x {c:+d}"
                yield _spec("match_equivalent_forms", (a, h, k), problem, answer)
                emitted += 1
                if emitted >= limit:
                    return


