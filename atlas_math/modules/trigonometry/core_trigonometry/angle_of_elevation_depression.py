from __future__ import annotations

import itertools
import math
import random
from typing import Iterable

from atlas_math.modules.shared.common import make_sample

MODULE_INFO = {
    "module_id": "trigonometry.angle_of_elevation_depression",
    "name": "Angle Of Elevation Depression",
    "topic": "trigonometry",
    "subtopic": "core_trigonometry",
    "difficulty_levels": ["level_1", "level_2", "level_3", "level_4", "level_5"],
    "enabled": True,
}
INSTRUCTIONS = [
    "Solve the elevation or depression problem: {problem}",
    "Use right triangle trigonometry in context: {problem}",
    "Find the requested measure: {problem}",
]
LEVEL_SPEC_CAPS = {"level_1": 600, "level_2": 800, "level_3": 1000, "level_4": 1200, "level_5": 1400}
FAMILY_CAPS = {"level_1": {"find_angle": 600}, "level_2": {"find_height": 800}, "level_3": {"find_distance": 1000}, "level_4": {"depression_context": 1200}, "level_5": {"multi_step_context": 1400}}
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


def _fmt(value: float) -> str:
    if abs(value - round(value)) < 1e-9:
        return str(int(round(value)))
    return f"{value:.2f}".rstrip("0").rstrip(".")


def _spec(family: str, values: tuple, prompt: str, answer: str):
    canonical = ":".join([family] + [str(v) for v in values])
    return {"family": family, "values": values, "prompt": prompt, "answer": answer, "canonical_key": canonical, "case_id": canonical, "family_id": family}


def _sample_from_spec(spec: dict, difficulty: str, instruction_idx: int = 0) -> dict:
    metadata = {"family": spec["family"], "level_number": _level_num(difficulty), "structured": True, "canonical_key": spec["canonical_key"], "case_id": spec["case_id"], "family_id": spec["family_id"], "template_id": spec["family"], "final_answer": spec["answer"], "values": list(spec.get("values", []))}
    instruction = INSTRUCTIONS[instruction_idx % len(INSTRUCTIONS)].format(problem=spec["prompt"])
    return make_sample(module_id=MODULE_INFO["module_id"], topic=MODULE_INFO["topic"], subtopic=MODULE_INFO["subtopic"], difficulty=difficulty, instruction=instruction, input_text=spec["prompt"], answer=spec["answer"], metadata=metadata)


def iter_level1_specs():
    for idx, (rise, run) in enumerate([(3, 4), (5, 12), (8, 15), (7, 24), (9, 12)]):
        if idx >= FAMILY_CAPS["level_1"]["find_angle"]:
            return
        angle = round(math.degrees(math.atan(rise / run)))
        yield _spec("find_angle", (rise, run), f"An observer sees the top of a building with vertical rise {rise} units and horizontal distance {run} units. Find the angle of elevation to the nearest degree.", str(angle))


def iter_level2_specs():
    emitted = 0
    for run in [10, 12, 15, 20, 24, 30]:
        for angle in [30, 45, 60]:
            yield _spec("find_height", (run, angle), f"From a point {run} units from a tree, the angle of elevation to the top is {angle}°. Find the height of the tree.", _fmt(run * math.tan(math.radians(angle))))
            emitted += 1
            if emitted >= FAMILY_CAPS["level_2"]["find_height"]:
                return


def iter_level3_specs():
    emitted = 0
    for height in [5, 6, 8, 10, 12, 15, 18]:
        for angle in [30, 45, 60]:
            yield _spec("find_distance", (height, angle), f"The top of a pole is {height} units above the ground and the angle of elevation from a point on the ground is {angle}°. Find the horizontal distance to the pole.", _fmt(height / math.tan(math.radians(angle))))
            emitted += 1
            if emitted >= FAMILY_CAPS["level_3"]["find_distance"]:
                return


def iter_level4_specs():
    emitted = 0
    for height in [12, 20, 24, 30, 36]:
        for angle in [30, 45, 60]:
            yield _spec("depression_context", (height, angle), f"From the top of a lighthouse {height} units tall, the angle of depression to a boat is {angle}°. Find the horizontal distance from the lighthouse to the boat.", _fmt(height / math.tan(math.radians(angle))))
            emitted += 1
            if emitted >= FAMILY_CAPS["level_4"]["depression_context"]:
                return


def iter_level5_specs():
    emitted = 0
    for base_height in [4, 5, 6]:
        for run in [12, 16, 20, 24]:
            for angle in [30, 45, 60]:
                total = base_height + run * math.tan(math.radians(angle))
                yield _spec("multi_step_context", (base_height, run, angle), f"A person standing on a platform {base_height} units high measures the angle of elevation to the top of a tower as {angle}° from a point {run} units away. Find the tower's total height.", _fmt(total))
                emitted += 1
                if emitted >= FAMILY_CAPS["level_5"]["multi_step_context"]:
                    return


def _iter_specs(difficulty: str):
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


def generate(count: int = 10, difficulty: str = "level_1", seed=None) -> list[dict]:
    rng = random.Random(_stable_seed(seed, MODULE_INFO["module_id"], difficulty, "generate"))
    pool = list(itertools.islice(_iter_specs(difficulty), 0, min(max(count * MAX_GENERATE_MULTIPLIER, 256), MAX_SPEC_PREFIX)))
    rng.shuffle(pool)
    out, seen = [], set()
    for idx, spec in enumerate(pool):
        sample = _sample_from_spec(spec, difficulty, idx)
        key = sample.get("input", "")
        if key in seen:
            continue
        seen.add(key)
        out.append(sample)
        if len(out) >= count:
            break
    return out


def generate_unique(count: int = 10, difficulty: str = "level_1", offset: int = 0, stride: int = 1, seed=None) -> list[dict]:
    pool = list(itertools.islice(_iter_specs(difficulty), 0, min(max(count * max(1, stride) * 16 + max(0, offset), 512), MAX_SPEC_PREFIX)))
    rng = random.Random(_stable_seed(seed, MODULE_INFO["module_id"], difficulty, offset, stride, "unique"))
    rng.shuffle(pool)
    uniq, seen = [], set()
    for spec in pool:
        if spec["canonical_key"] in seen:
            continue
        seen.add(spec["canonical_key"])
        uniq.append(spec)
    out, used = [], set()
    for idx, spec in enumerate(uniq[max(0, offset)::max(1, stride)]):
        sample = _sample_from_spec(spec, difficulty, idx)
        key = sample.get("input", "")
        if key in used:
            continue
        used.add(key)
        out.append(sample)
        if len(out) >= count:
            break
    return out


def iter_samples(difficulty: str = "level_1", seed=None):
    rng = random.Random(_stable_seed(seed, MODULE_INFO["module_id"], difficulty, "iter_samples"))
    pool = list(itertools.islice(_iter_specs(difficulty), 0, min(MAX_ITER_SAMPLES, LEVEL_SPEC_CAPS.get(difficulty, 600))))
    rng.shuffle(pool)
    seen = set()
    for idx, spec in enumerate(pool):
        sample = _sample_from_spec(spec, difficulty, idx)
        key = sample.get("input", "")
        if key in seen:
            continue
        seen.add(key)
        yield sample


def estimate_capacity(difficulty: str = "level_1"):
    return CAPACITY_HINTS.get(difficulty, {"value": None, "quality": "unknown"})


def curriculum() -> dict:
    return {"level_1": ["direct angle-of-elevation from rise and run"], "level_2": ["adds finding a height from distance and angle"], "level_3": ["adds finding a horizontal distance from height and angle"], "level_4": ["adds angle-of-depression contexts"], "level_5": ["adds two-step contextual height problems"]}


