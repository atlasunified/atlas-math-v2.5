from __future__ import annotations

import itertools
import math
import random
from fractions import Fraction
from typing import Iterable

from atlas_math.modules.shared.common import make_sample

MODULE_INFO = {
    "module_id": "trigonometry.arc_length_and_sector_with_radians",
    "name": "Arc Length And Sector With Radians",
    "topic": "trigonometry",
    "subtopic": "core_trigonometry",
    "difficulty_levels": ["level_1", "level_2", "level_3", "level_4", "level_5"],
    "enabled": True,
}
INSTRUCTIONS = ["Find the requested arc length or sector area: {problem}", "Use the radian formulas to solve: {problem}", "Compute the geometric quantity: {problem}"]
LEVEL_SPEC_CAPS = {"level_1": 600, "level_2": 800, "level_3": 1000, "level_4": 1200, "level_5": 1400}
FAMILY_CAPS = {"level_1": {"arc_length_basic": 600}, "level_2": {"sector_area_basic": 800}, "level_3": {"convert_then_arc": 1000}, "level_4": {"convert_then_sector": 1200}, "level_5": {"combined_reasoning": 1400}}
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
    return f"{value:.3f}".rstrip("0").rstrip(".")


def _spec(family: str, values: tuple, prompt: str, answer: str):
    canonical = ":".join([family] + [str(v) for v in values])
    return {"family": family, "values": values, "prompt": prompt, "answer": answer, "canonical_key": canonical, "case_id": canonical, "family_id": family}


def _sample_from_spec(spec: dict, difficulty: str, instruction_idx: int = 0) -> dict:
    metadata = {"family": spec["family"], "level_number": _level_num(difficulty), "structured": True, "canonical_key": spec["canonical_key"], "case_id": spec["case_id"], "family_id": spec["family_id"], "template_id": spec["family"], "final_answer": spec["answer"], "values": list(spec.get("values", []))}
    instruction = INSTRUCTIONS[instruction_idx % len(INSTRUCTIONS)].format(problem=spec["prompt"])
    return make_sample(module_id=MODULE_INFO["module_id"], topic=MODULE_INFO["topic"], subtopic=MODULE_INFO["subtopic"], difficulty=difficulty, instruction=instruction, input_text=spec["prompt"], answer=spec["answer"], metadata=metadata)


def iter_level1_specs():
    emitted = 0
    for r in [2, 3, 4, 5, 6, 8, 10]:
        for theta in [Fraction(1, 6), Fraction(1, 4), Fraction(1, 3), Fraction(1, 2), Fraction(3, 4)]:
            arc = r * float(theta * math.pi)
            yield _spec("arc_length_basic", (r, theta.numerator, theta.denominator), f"A circle has radius {r}. Find the arc length for a central angle of {theta.numerator}π/{theta.denominator} radians.", _fmt(arc))
            emitted += 1
            if emitted >= FAMILY_CAPS["level_1"]["arc_length_basic"]:
                return


def iter_level2_specs():
    emitted = 0
    for r in [2, 3, 4, 5, 6, 8]:
        for theta in [Fraction(1, 6), Fraction(1, 4), Fraction(1, 3), Fraction(1, 2), Fraction(2, 3)]:
            area = 0.5 * r * r * float(theta * math.pi)
            yield _spec("sector_area_basic", (r, theta.numerator, theta.denominator), f"A circle has radius {r}. Find the sector area for a central angle of {theta.numerator}π/{theta.denominator} radians.", _fmt(area))
            emitted += 1
            if emitted >= FAMILY_CAPS["level_2"]["sector_area_basic"]:
                return


def iter_level3_specs():
    emitted = 0
    for r in [3, 4, 5, 6, 8, 10]:
        for deg in [30, 45, 60, 90, 120, 135, 150]:
            yield _spec("convert_then_arc", (r, deg), f"A circle has radius {r}. Convert {deg}° to radians and then find the arc length.", _fmt(r * math.radians(deg)))
            emitted += 1
            if emitted >= FAMILY_CAPS["level_3"]["convert_then_arc"]:
                return


def iter_level4_specs():
    emitted = 0
    for r in [3, 4, 5, 6, 8]:
        for deg in [30, 45, 60, 90, 120, 150, 210]:
            yield _spec("convert_then_sector", (r, deg), f"A circle has radius {r}. Convert {deg}° to radians and then find the sector area.", _fmt(0.5 * r * r * math.radians(deg)))
            emitted += 1
            if emitted >= FAMILY_CAPS["level_4"]["convert_then_sector"]:
                return


def iter_level5_specs():
    emitted = 0
    for r in [4, 5, 6, 8, 10]:
        for theta in [Fraction(1, 3), Fraction(1, 2), Fraction(2, 3), Fraction(3, 4)]:
            radians = float(theta * math.pi)
            result = r * radians + 0.5 * r * r * radians
            yield _spec("combined_reasoning", (r, theta.numerator, theta.denominator), f"A sector has radius {r} and central angle {theta.numerator}π/{theta.denominator} radians. Find arc length plus sector area.", _fmt(result))
            emitted += 1
            if emitted >= FAMILY_CAPS["level_5"]["combined_reasoning"]:
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
    return {"level_1": ["direct arc-length computation from radians"], "level_2": ["direct sector-area computation from radians"], "level_3": ["adds degree-to-radian conversion before arc length"], "level_4": ["adds degree-to-radian conversion before sector area"], "level_5": ["adds a bounded combined arc-plus-area task"]}


