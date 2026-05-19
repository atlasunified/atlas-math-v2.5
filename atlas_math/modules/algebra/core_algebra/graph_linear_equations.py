from __future__ import annotations

import itertools
import random
from fractions import Fraction
from typing import Iterable

from atlas_math.modules.shared.common import make_sample

INSTRUCTIONS = [
    "{instruction}: {problem}",
    "Solve and report the result: {problem}",
    "Work the problem and give the final answer: {problem}",
    "Compute the requested result: {problem}",
]

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

MODULE_INFO = {
    "module_id": "algebra.graph_linear_equations",
    "name": "Graph Linear Equations",
    "topic": "algebra",
    "subtopic": "core_algebra",
    "difficulty_levels": ["level_1", "level_2", "level_3", "level_4", "level_5"],
    "enabled": True,
}

LEVEL_SPEC_CAPS = {"level_1": 700, "level_2": 900, "level_3": 1100, "level_4": 1200, "level_5": 1400}
FAMILY_CAPS = {
    "level_1": {"slope_intercept_easy": 700},
    "level_2": {"integer_slope_points": 900},
    "level_3": {"standard_to_table": 1100},
    "level_4": {"fraction_slope": 1200},
    "level_5": {"parallel_perpendicular": 1400},
}
CAPACITY_HINTS = {k: {"value": v, "quality": "capped"} for k, v in LEVEL_SPEC_CAPS.items()}


def _spec(family: str, values: tuple, problem: str, answer: str):
    canonical = ":".join([family] + [str(v) for v in values])
    return {"family": family, "values": values, "problem": problem, "answer": answer, "canonical_key": canonical, "case_id": canonical, "family_id": family}


def _sample_from_spec(spec: dict, difficulty: str, instruction_idx: int = 0) -> dict:
    answer = spec["answer"]
    metadata = {"family": spec["family"], "level_number": _level_num(difficulty), "structured": True, "canonical_key": spec["canonical_key"], "case_id": spec["case_id"], "family_id": spec["family_id"], "template_id": spec["family"], "final_answer": answer, "values": list(spec.get("values", []))}
    instruction = INSTRUCTIONS[instruction_idx % len(INSTRUCTIONS)].format(instruction="Graph the linear equation", problem=spec["problem"])
    return make_sample(module_id=MODULE_INFO["module_id"], topic=MODULE_INFO["topic"], subtopic=MODULE_INFO["subtopic"], difficulty=difficulty, instruction=instruction, input_text=spec["problem"], answer=answer, metadata=metadata)


def iter_level1_specs():
    limit = FAMILY_CAPS["level_1"]["slope_intercept_easy"]
    emitted = 0
    for m in range(-5, 6):
        if m == 0:
            continue
        for b in range(-12, 13):
            problem = f"Graph y = {m}x + {b}. State two points on the line."
            answer = f"(0, {b}), (1, {m + b})"
            yield _spec("slope_intercept_easy", (m, b), problem, answer)
            emitted += 1
            if emitted >= limit:
                return


def iter_level2_specs():
    limit = FAMILY_CAPS["level_2"]["integer_slope_points"]
    emitted = 0
    for x1 in range(-4, 5):
        for m in range(-4, 5):
            if m == 0:
                continue
            for b in range(-8, 9):
                y1 = m * x1 + b
                x2 = x1 + 2
                y2 = m * x2 + b
                problem = f"Graph the line through points ({x1}, {y1}) and ({x2}, {y2}). Write an equation in slope-intercept form."
                answer = f"y = {m}x + {b}"
                yield _spec("integer_slope_points", (x1, m, b), problem, answer)
                emitted += 1
                if emitted >= limit:
                    return


def iter_level3_specs():
    limit = FAMILY_CAPS["level_3"]["standard_to_table"]
    emitted = 0
    for a in range(1, 6):
        for b in range(1, 6):
            for c in range(-12, 13):
                x0 = 0
                if c % b != 0:
                    continue
                y0 = c // b
                x1 = b
                y1 = (c - a * x1) // b
                problem = f"Graph {a}x + {b}y = {c}. Give two lattice points on the graph."
                answer = f"(0, {y0}), ({x1}, {y1})"
                yield _spec("standard_to_table", (a, b, c), problem, answer)
                emitted += 1
                if emitted >= limit:
                    return


def iter_level4_specs():
    limit = FAMILY_CAPS["level_4"]["fraction_slope"]
    emitted = 0
    for m_num in range(-5, 6):
        if m_num == 0:
            continue
        for m_den in range(2, 6):
            for b in range(-8, 9):
                m = Fraction(m_num, m_den)
                x2 = m_den
                y2 = m_num + b
                problem = f"Graph y = {m_num}/{m_den}x + {b}. State two convenient points."
                answer = f"(0, {b}), ({x2}, {y2})"
                yield _spec("fraction_slope", (m_num, m_den, b), problem, answer)
                emitted += 1
                if emitted >= limit:
                    return


def iter_level5_specs():
    limit = FAMILY_CAPS["level_5"]["parallel_perpendicular"]
    emitted = 0
    for m in [-4, -3, -2, -1, 1, 2, 3, 4]:
        for b in range(-6, 7):
            for mode in ["parallel", "perpendicular"]:
                if mode == "parallel":
                    target_m = m
                else:
                    target_m = Fraction(-1, m)
                x0 = 0
                y0 = b
                problem = f"Graph the line {mode} to y = {m}x + {b} passing through ({x0}, {y0}). Give its equation."
                answer = f"y = {_fmt_number(target_m)}x + {b}"
                yield _spec("parallel_perpendicular", (m, b, mode), problem, answer)
                emitted += 1
                if emitted >= limit:
                    return


def _iter_specs(difficulty="level_1"):
    level = _level_num(difficulty)
    if level == 1: return _take(iter_level1_specs(), LEVEL_SPEC_CAPS["level_1"])
    if level == 2: return _take(iter_level2_specs(), LEVEL_SPEC_CAPS["level_2"])
    if level == 3: return _take(iter_level3_specs(), LEVEL_SPEC_CAPS["level_3"])
    if level == 4: return _take(iter_level4_specs(), LEVEL_SPEC_CAPS["level_4"])
    return _take(iter_level5_specs(), LEVEL_SPEC_CAPS["level_5"])


def curriculum():
    return {"level_1": ["graph slope-intercept lines from equations"], "level_2": ["graph lines from two integer points"], "level_3": ["graph standard form lines via lattice points"], "level_4": ["graph fractional-slope lines"], "level_5": ["graph parallel and perpendicular lines"]}


def estimate_capacity(difficulty="level_1"):
    return dict(CAPACITY_HINTS.get(difficulty, {"value": None, "quality": "unknown"}))


def generate(count=10, difficulty="level_1", seed=None):
    count = max(0, int(count)); prefix = min(max(count * MAX_GENERATE_MULTIPLIER, 256), MAX_SPEC_PREFIX)
    pool = list(itertools.islice(_iter_specs(difficulty), 0, prefix))
    if not pool or count == 0: return []
    rng = random.Random(_stable_seed(MODULE_INFO["module_id"], difficulty, seed, "generate")); rng.shuffle(pool)
    return [_sample_from_spec(spec, difficulty, i) for i, spec in enumerate(pool[:count])]


def generate_unique(count=10, difficulty="level_1", offset=0, stride=1, seed=None):
    count = max(0, int(count)); offset = max(0, int(offset)); stride = max(1, int(stride))
    pool = list(itertools.islice(_iter_specs(difficulty), 0, MAX_SPEC_PREFIX))
    rng = random.Random(_stable_seed(MODULE_INFO["module_id"], difficulty, seed, offset, stride, "unique")); rng.shuffle(pool)
    seen = set(); ordered = []
    for spec in pool:
        key = spec["canonical_key"]
        if key in seen: continue
        seen.add(key); ordered.append(spec)
    return [_sample_from_spec(spec, difficulty, i) for i, spec in enumerate(ordered[offset::stride][:count])]


def iter_samples(difficulty="level_1", seed=None):
    max_items = min(LEVEL_SPEC_CAPS.get(difficulty, 1000), MAX_ITER_SAMPLES)
    pool = list(itertools.islice(_iter_specs(difficulty), 0, max_items))
    rng = random.Random(_stable_seed(MODULE_INFO["module_id"], difficulty, seed, "iter")); rng.shuffle(pool)
    seen = set()
    for idx, spec in enumerate(pool):
        key = spec["canonical_key"]
        if key in seen: continue
        seen.add(key)
        yield _sample_from_spec(spec, difficulty, idx)


