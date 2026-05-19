from __future__ import annotations

import itertools
import math
import random
from typing import Iterable

from atlas_math.modules.shared.common import make_sample

MODULE_INFO = {
    "module_id": "trigonometry.inverse_trig_right_triangle",
    "name": "Inverse Trig Right Triangle",
    "topic": "trigonometry",
    "subtopic": "core_trigonometry",
    "difficulty_levels": ["level_1", "level_2", "level_3", "level_4", "level_5"],
    "enabled": True,
}
INSTRUCTIONS = [
    "Find the acute angle in the right triangle: {problem}",
    "Use inverse trigonometry to determine the angle: {problem}",
    "Compute the requested angle measure: {problem}",
]
LEVEL_SPEC_CAPS = {"level_1": 600, "level_2": 800, "level_3": 1000, "level_4": 1200, "level_5": 1400}
FAMILY_CAPS = {
    "level_1": {"exact_from_ratio": 600},
    "level_2": {"triangle_from_sides": 800},
    "level_3": {"complementary_angles": 1000},
    "level_4": {"decimal_ratio": 1200},
    "level_5": {"contextual_angle": 1400},
}
CAPACITY_HINTS = {level: {"value": cap, "quality": "capped"} for level, cap in LEVEL_SPEC_CAPS.items()}
MAX_SPEC_PREFIX = 5000
MAX_GENERATE_MULTIPLIER = 8
MAX_ITER_SAMPLES = 4096
ANGLE_TABLE = [
    (30, "sin", 0.5), (30, "cos", 0.866), (30, "tan", 0.577),
    (45, "sin", 0.707), (45, "cos", 0.707), (45, "tan", 1.0),
    (60, "sin", 0.866), (60, "cos", 0.5), (60, "tan", 1.732),
]
TRIPLES = [(3, 4, 5), (5, 12, 13), (8, 15, 17), (7, 24, 25)]


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


def _spec(family: str, values: tuple, prompt: str, answer: str):
    canonical = ":".join([family] + [str(v) for v in values])
    return {"family": family, "values": values, "prompt": prompt, "answer": answer, "canonical_key": canonical, "case_id": canonical, "family_id": family}


def _sample_from_spec(spec: dict, difficulty: str, instruction_idx: int = 0) -> dict:
    metadata = {"family": spec["family"], "level_number": _level_num(difficulty), "structured": True, "canonical_key": spec["canonical_key"], "case_id": spec["case_id"], "family_id": spec["family_id"], "template_id": spec["family"], "final_answer": spec["answer"], "values": list(spec.get("values", []))}
    instruction = INSTRUCTIONS[instruction_idx % len(INSTRUCTIONS)].format(problem=spec["prompt"])
    return make_sample(module_id=MODULE_INFO["module_id"], topic=MODULE_INFO["topic"], subtopic=MODULE_INFO["subtopic"], difficulty=difficulty, instruction=instruction, input_text=spec["prompt"], answer=spec["answer"], metadata=metadata)


def _nearest_angle(value: float, fn: str) -> int:
    best = None
    for angle in range(1, 90):
        rad = math.radians(angle)
        calc = {"sin": math.sin, "cos": math.cos, "tan": math.tan}[fn](rad)
        cand = (abs(calc - value), angle)
        if best is None or cand < best:
            best = cand
    return best[1]


def iter_level1_specs():
    for idx, (angle, fn, value) in enumerate(ANGLE_TABLE):
        if idx >= FAMILY_CAPS["level_1"]["exact_from_ratio"]:
            return
        yield _spec("exact_from_ratio", (angle, fn, value), f"Find θ in degrees if {fn}(θ)≈{value} and 0°<θ<90°.", str(angle))


def iter_level2_specs():
    emitted = 0
    for opp, adj, hyp in TRIPLES:
        for fn, value in [("sin", opp / hyp), ("cos", adj / hyp), ("tan", opp / adj)]:
            angle = _nearest_angle(value, fn)
            yield _spec("triangle_from_sides", (fn, opp, adj, hyp), f"A right triangle has opposite={opp}, adjacent={adj}, and hypotenuse={hyp}. Estimate θ in degrees using {fn} for the angle opposite {opp}.", str(angle))
            emitted += 1
            if emitted >= FAMILY_CAPS["level_2"]["triangle_from_sides"]:
                return


def iter_level3_specs():
    for idx, angle in enumerate([18, 24, 32, 37, 41, 53, 58, 66]):
        if idx >= FAMILY_CAPS["level_3"]["complementary_angles"]:
            return
        yield _spec("complementary_angles", (angle,), f"One acute angle of a right triangle is {angle}°. Find the other acute angle.", str(90 - angle))


def iter_level4_specs():
    emitted = 0
    for fn in ["sin", "cos", "tan"]:
        for angle in [12, 18, 25, 33, 41, 52, 67, 74]:
            value = {"sin": math.sin, "cos": math.cos, "tan": math.tan}[fn](math.radians(angle))
            yield _spec("decimal_ratio", (fn, angle), f"Estimate θ to the nearest degree if {fn}(θ)={value:.3f} and 0°<θ<90°.", str(angle))
            emitted += 1
            if emitted >= FAMILY_CAPS["level_4"]["decimal_ratio"]:
                return


def iter_level5_specs():
    emitted = 0
    for rise, run in [(3, 4), (5, 12), (8, 15), (7, 24), (9, 12)]:
        angle = _nearest_angle(rise / run, "tan")
        yield _spec("contextual_angle", (rise, run), f"A wheelchair ramp rises {rise} units for every {run} horizontal units. Estimate the angle of elevation in degrees.", str(angle))
        emitted += 1
        if emitted >= FAMILY_CAPS["level_5"]["contextual_angle"]:
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
    out = []
    seen = set()
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
    return {
        "level_1": ["exact acute-angle recovery from standard trig values"],
        "level_2": ["adds angle estimation from triangle side ratios"],
        "level_3": ["adds complementary-angle reasoning in right triangles"],
        "level_4": ["adds decimal inverse-trig estimation"],
        "level_5": ["adds contextual right-triangle interpretation"],
    }


