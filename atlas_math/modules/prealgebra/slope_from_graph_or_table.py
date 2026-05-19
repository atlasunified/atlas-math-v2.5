from __future__ import annotations

import random
from fractions import Fraction
from typing import Iterable

from atlas_math.modules.shared.common import make_sample

MODULE_INFO = {
    "module_id": "prealgebra.slope_from_graph_or_table",
    "name": "Slope from Graph or Table",
    "topic": "prealgebra",
    "subtopic": "core_prealgebra",
    "difficulty_levels": ["level_1", "level_2", "level_3", "level_4", "level_5"],
    "enabled": True,
}
INSTRUCTIONS = [
    "Find the slope: {problem}",
    "Determine the rate of change: {problem}",
    "Use the graph or table information: {problem}",
    "Compute the slope from the data shown: {problem}",
]
LEVEL_SPEC_CAPS = {"level_1": 900, "level_2": 1100, "level_3": 1300, "level_4": 1500, "level_5": 1700}
FAMILY_CAPS = {"level_1": {"table_integer": 900}, "level_2": {"table_negative": 1100}, "level_3": {"table_fraction": 1300}, "level_4": {"graph_horizontal": 1500}, "level_5": {"graph_vertical": 1700}}
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

def _stable_seed(*parts) -> str:
    return "|".join(str(p) for p in parts)

def _take(iterable: Iterable[dict], n: int) -> Iterable[dict]:
    for idx, item in enumerate(iterable):
        if idx >= max(0, int(n)):
            break
        yield item

def _fmt(value) -> str:
    if isinstance(value, Fraction):
        return str(value.numerator) if value.denominator == 1 else f"{value.numerator}/{value.denominator}"
    return str(value)

def _solve(spec: dict):
    family = spec["family"]
    x1, y1, x2, y2 = spec["values"]
    if family == "graph_vertical":
        return "undefined"
    return Fraction(y2 - y1, x2 - x1)

def _problem_text(spec: dict) -> str:
    family = spec["family"]
    x1, y1, x2, y2 = spec["values"]
    if family.startswith("table"):
        return f"Use the table values x: {x1}, {x2} and y: {y1}, {y2}. Find the slope."
    return f"A graph shows points ({x1}, {y1}) and ({x2}, {y2}). Find the slope of the line."

def _sample_from_spec(spec: dict, difficulty: str, instruction_idx: int = 0) -> dict:
    problem = _problem_text(spec)
    answer = _fmt(_solve(spec))
    metadata = {"family": spec["family"], "level_number": _level_num(difficulty), "structured": True, "canonical_key": spec["canonical_key"], "case_id": spec["case_id"], "family_id": spec["family_id"], "template_id": spec["family"], "final_answer": answer, "values": list(spec["values"])}
    instruction = INSTRUCTIONS[instruction_idx % len(INSTRUCTIONS)].format(problem=problem)
    return make_sample(module_id=MODULE_INFO["module_id"], topic=MODULE_INFO["topic"], subtopic=MODULE_INFO["subtopic"], difficulty=difficulty, instruction=instruction, input_text=problem, answer=answer, metadata=metadata)

def iter_level1_specs() -> Iterable[dict]:
    emitted = 0
    for x1 in range(-10, 11):
        for step in range(1, 11):
            for m in range(1, 11):
                y1 = x1 - 3
                yield {"family": "table_integer", "values": (x1, y1, x1 + step, y1 + m * step), "canonical_key": f"table_integer:{x1}:{y1}:{x1+step}:{y1+m*step}", "case_id": f"table_integer:{x1}:{y1}:{x1+step}:{y1+m*step}", "family_id": "table_integer"}
                emitted += 1
                if emitted >= FAMILY_CAPS["level_1"]["table_integer"]:
                    return

def iter_level2_specs() -> Iterable[dict]:
    emitted = 0
    for x1 in range(-10, 11):
        for step in range(1, 11):
            for m in range(1, 11):
                y1 = 2 * x1 + 1
                yield {"family": "table_negative", "values": (x1, y1, x1 + step, y1 - m * step), "canonical_key": f"table_negative:{x1}:{y1}:{x1+step}:{y1-m*step}", "case_id": f"table_negative:{x1}:{y1}:{x1+step}:{y1-m*step}", "family_id": "table_negative"}
                emitted += 1
                if emitted >= FAMILY_CAPS["level_2"]["table_negative"]:
                    return

def iter_level3_specs() -> Iterable[dict]:
    emitted = 0
    for x1 in range(-10, 11):
        for dx in range(2, 13):
            for dy in range(1, dx):
                if Fraction(dy, dx).denominator == 1:
                    continue
                y1 = 3 - x1
                yield {"family": "table_fraction", "values": (x1, y1, x1 + dx, y1 + dy), "canonical_key": f"table_fraction:{x1}:{y1}:{x1+dx}:{y1+dy}", "case_id": f"table_fraction:{x1}:{y1}:{x1+dx}:{y1+dy}", "family_id": "table_fraction"}
                emitted += 1
                if emitted >= FAMILY_CAPS["level_3"]["table_fraction"]:
                    return

def iter_level4_specs() -> Iterable[dict]:
    emitted = 0
    for y in range(-30, 31):
        for x1 in range(-20, 21):
            for dx in range(1, 21):
                yield {"family": "graph_horizontal", "values": (x1, y, x1 + dx, y), "canonical_key": f"graph_horizontal:{x1}:{y}:{x1+dx}:{y}", "case_id": f"graph_horizontal:{x1}:{y}:{x1+dx}:{y}", "family_id": "graph_horizontal"}
                emitted += 1
                if emitted >= FAMILY_CAPS["level_4"]["graph_horizontal"]:
                    return

def iter_level5_specs() -> Iterable[dict]:
    emitted = 0
    for x in range(-30, 31):
        for y1 in range(-20, 21):
            for dy in range(1, 21):
                yield {"family": "graph_vertical", "values": (x, y1, x, y1 + dy), "canonical_key": f"graph_vertical:{x}:{y1}:{x}:{y1+dy}", "case_id": f"graph_vertical:{x}:{y1}:{x}:{y1+dy}", "family_id": "graph_vertical"}
                emitted += 1
                if emitted >= FAMILY_CAPS["level_5"]["graph_vertical"]:
                    return

def iter_specs(difficulty: str) -> Iterable[dict]:
    level = _level_num(difficulty)
    if level == 1:
        yield from iter_level1_specs()
    elif level == 2:
        yield from iter_level2_specs()
    elif level == 3:
        yield from iter_level3_specs()
    elif level == 4:
        yield from iter_level4_specs()
    else:
        yield from iter_level5_specs()

def generate(difficulty: str = "level_1", seed: int | None = None) -> dict:
    pool = list(_take(iter_specs(difficulty), min(LEVEL_SPEC_CAPS.get(difficulty, 1000), MAX_GENERATE_MULTIPLIER * 256)))
    rng = random.Random(seed if seed is not None else _stable_seed(MODULE_INFO["module_id"], difficulty))
    spec = rng.choice(pool)
    return _sample_from_spec(spec, difficulty, instruction_idx=rng.randrange(len(INSTRUCTIONS)))

def generate_unique(difficulty: str = "level_1", limit: int | None = None, seed: int | None = None) -> Iterable[dict]:
    max_items = min(LEVEL_SPEC_CAPS.get(difficulty, 1000), limit if limit is not None else LEVEL_SPEC_CAPS.get(difficulty, 1000), MAX_SPEC_PREFIX)
    pool = list(_take(iter_specs(difficulty), max_items))
    rng = random.Random(seed if seed is not None else _stable_seed(MODULE_INFO["module_id"], difficulty, "unique"))
    rng.shuffle(pool)
    for idx, spec in enumerate(pool):
        yield _sample_from_spec(spec, difficulty, instruction_idx=idx)

def iter_samples(difficulty: str = "level_1", limit: int | None = None) -> Iterable[dict]:
    max_items = min(limit if limit is not None else LEVEL_SPEC_CAPS.get(difficulty, 1000), LEVEL_SPEC_CAPS.get(difficulty, 1000), MAX_ITER_SAMPLES)
    for idx, spec in enumerate(_take(iter_specs(difficulty), max_items)):
        yield _sample_from_spec(spec, difficulty, instruction_idx=idx)

def estimate_capacity(difficulty: str | None = None) -> dict:
    if difficulty is None:
        return {level: CAPACITY_HINTS[level] for level in MODULE_INFO["difficulty_levels"]}
    return CAPACITY_HINTS.get(difficulty, {"value": 0, "quality": "none"})

def curriculum() -> dict:
    return {"module_id": MODULE_INFO["module_id"], "topic": MODULE_INFO["topic"], "subtopic": MODULE_INFO["subtopic"], "difficulty_levels": MODULE_INFO["difficulty_levels"], "capacity": estimate_capacity()}


