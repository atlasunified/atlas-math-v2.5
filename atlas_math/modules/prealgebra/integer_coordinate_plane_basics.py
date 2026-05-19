from __future__ import annotations

import random
from typing import Iterable

from atlas_math.modules.shared.common import make_sample

MODULE_INFO = {
    "module_id": "prealgebra.integer_coordinate_plane_basics",
    "name": "Integer Coordinate Plane Basics",
    "topic": "prealgebra",
    "subtopic": "core_prealgebra",
    "difficulty_levels": ["level_1", "level_2", "level_3", "level_4", "level_5"],
    "enabled": True,
}

INSTRUCTIONS = [
    "Answer: {problem}",
    "Work on the coordinate-plane question: {problem}",
    "Use the ordered pair information: {problem}",
    "Determine the result: {problem}",
]

LEVEL_SPEC_CAPS = {"level_1": 900, "level_2": 1100, "level_3": 1200, "level_4": 1400, "level_5": 1600}
FAMILY_CAPS = {
    "level_1": {"quadrant": 900},
    "level_2": {"axis_or_origin": 1100},
    "level_3": {"reflection_x": 1200},
    "level_4": {"reflection_y": 1400},
    "level_5": {"distance_horizontal_vertical": 1600},
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


def _stable_seed(*parts) -> str:
    return "|".join(str(p) for p in parts)


def _take(iterable: Iterable[dict], n: int) -> Iterable[dict]:
    for idx, item in enumerate(iterable):
        if idx >= max(0, int(n)):
            break
        yield item


def _solve(spec: dict):
    family = spec["family"]
    v = spec["values"]
    if family == "quadrant":
        x, y = v
        if x > 0 and y > 0:
            return "Quadrant I"
        if x < 0 and y > 0:
            return "Quadrant II"
        if x < 0 and y < 0:
            return "Quadrant III"
        return "Quadrant IV"
    if family == "axis_or_origin":
        x, y = v
        if x == 0 and y == 0:
            return "origin"
        if x == 0:
            return "y-axis"
        return "x-axis"
    if family == "reflection_x":
        return f"({v[0]}, {-v[1]})"
    if family == "reflection_y":
        return f"({-v[0]}, {v[1]})"
    if family == "distance_horizontal_vertical":
        return abs(v[2] - v[0]) + abs(v[3] - v[1])
    raise ValueError(f"Unknown family: {family}")


def _problem_text(spec: dict) -> str:
    family = spec["family"]
    v = spec["values"]
    if family == "quadrant":
        return f"Which quadrant contains the point ({v[0]}, {v[1]})?"
    if family == "axis_or_origin":
        return f"Is the point ({v[0]}, {v[1]}) on the x-axis, y-axis, or at the origin?"
    if family == "reflection_x":
        return f"Reflect the point ({v[0]}, {v[1]}) across the x-axis."
    if family == "reflection_y":
        return f"Reflect the point ({v[0]}, {v[1]}) across the y-axis."
    if family == "distance_horizontal_vertical":
        return f"Find the distance between ({v[0]}, {v[1]}) and ({v[2]}, {v[3]}) along a horizontal or vertical line."
    raise ValueError(f"Unknown family: {family}")


def _sample_from_spec(spec: dict, difficulty: str, instruction_idx: int = 0) -> dict:
    problem = _problem_text(spec)
    answer = str(_solve(spec))
    metadata = {"family": spec["family"], "level_number": _level_num(difficulty), "structured": True, "canonical_key": spec["canonical_key"], "case_id": spec["case_id"], "family_id": spec["family_id"], "template_id": spec["family"], "final_answer": answer, "values": list(spec["values"])}
    instruction = INSTRUCTIONS[instruction_idx % len(INSTRUCTIONS)].format(problem=problem)
    return make_sample(module_id=MODULE_INFO["module_id"], topic=MODULE_INFO["topic"], subtopic=MODULE_INFO["subtopic"], difficulty=difficulty, instruction=instruction, input_text=problem, answer=answer, metadata=metadata)


def iter_level1_specs() -> Iterable[dict]:
    emitted = 0
    for x in range(-20, 21):
        for y in range(-20, 21):
            if x == 0 or y == 0:
                continue
            yield {"family": "quadrant", "values": (x, y), "canonical_key": f"quadrant:{x}:{y}", "case_id": f"quadrant:{x}:{y}", "family_id": "quadrant"}
            emitted += 1
            if emitted >= FAMILY_CAPS["level_1"]["quadrant"]:
                return


def iter_level2_specs() -> Iterable[dict]:
    emitted = 0
    for n in range(-200, 201):
        yield {"family": "axis_or_origin", "values": (n, 0), "canonical_key": f"axis_or_origin:{n}:0", "case_id": f"axis_or_origin:{n}:0", "family_id": "axis_or_origin"}
        emitted += 1
        if emitted >= FAMILY_CAPS["level_2"]["axis_or_origin"]:
            return
        if n != 0:
            yield {"family": "axis_or_origin", "values": (0, n), "canonical_key": f"axis_or_origin:0:{n}", "case_id": f"axis_or_origin:0:{n}", "family_id": "axis_or_origin"}
            emitted += 1
            if emitted >= FAMILY_CAPS["level_2"]["axis_or_origin"]:
                return


def iter_level3_specs() -> Iterable[dict]:
    emitted = 0
    for x in range(-30, 31):
        for y in range(-30, 31):
            yield {"family": "reflection_x", "values": (x, y), "canonical_key": f"reflection_x:{x}:{y}", "case_id": f"reflection_x:{x}:{y}", "family_id": "reflection_x"}
            emitted += 1
            if emitted >= FAMILY_CAPS["level_3"]["reflection_x"]:
                return


def iter_level4_specs() -> Iterable[dict]:
    emitted = 0
    for x in range(-30, 31):
        for y in range(-30, 31):
            yield {"family": "reflection_y", "values": (x, y), "canonical_key": f"reflection_y:{x}:{y}", "case_id": f"reflection_y:{x}:{y}", "family_id": "reflection_y"}
            emitted += 1
            if emitted >= FAMILY_CAPS["level_4"]["reflection_y"]:
                return


def iter_level5_specs() -> Iterable[dict]:
    emitted = 0
    for x in range(-20, 21):
        for y in range(-20, 21):
            for delta in range(1, 21):
                yield {"family": "distance_horizontal_vertical", "values": (x, y, x + delta, y), "canonical_key": f"distance_horizontal_vertical:h:{x}:{y}:{x + delta}:{y}", "case_id": f"distance_horizontal_vertical:h:{x}:{y}:{x + delta}:{y}", "family_id": "distance_horizontal_vertical"}
                emitted += 1
                if emitted >= FAMILY_CAPS["level_5"]["distance_horizontal_vertical"]:
                    return
                yield {"family": "distance_horizontal_vertical", "values": (x, y, x, y + delta), "canonical_key": f"distance_horizontal_vertical:v:{x}:{y}:{x}:{y + delta}", "case_id": f"distance_horizontal_vertical:v:{x}:{y}:{x}:{y + delta}", "family_id": "distance_horizontal_vertical"}
                emitted += 1
                if emitted >= FAMILY_CAPS["level_5"]["distance_horizontal_vertical"]:
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


