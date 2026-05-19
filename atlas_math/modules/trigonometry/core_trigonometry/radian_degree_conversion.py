from __future__ import annotations

import itertools
import random
from fractions import Fraction
from typing import Iterable

from atlas_math.modules.shared.common import make_sample

MODULE_INFO = {
    "module_id": "trigonometry.radian_degree_conversion",
    "name": "Radian Degree Conversion",
    "topic": "trigonometry",
    "subtopic": "core_trigonometry",
    "difficulty_levels": ["level_1", "level_2", "level_3", "level_4", "level_5"],
    "enabled": True,
}
INSTRUCTIONS = ["Convert the angle measure: {problem}", "Rewrite the angle in the requested units: {problem}", "Perform the radian-degree conversion: {problem}"]
LEVEL_SPEC_CAPS = {"level_1": 600, "level_2": 800, "level_3": 1000, "level_4": 1200, "level_5": 1400}
FAMILY_CAPS = {"level_1": {"deg_to_rad": 600}, "level_2": {"rad_to_deg": 800}, "level_3": {"special_angles": 1000}, "level_4": {"signed_and_large": 1200}, "level_5": {"contextual_conversion": 1400}}
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


def _rad_str(numer: int, denom: int = 1) -> str:
    frac = Fraction(numer, denom)
    if frac == 0:
        return "0"
    if frac.denominator == 1:
        if frac.numerator == 1:
            return "π"
        if frac.numerator == -1:
            return "-π"
        return f"{frac.numerator}π"
    if frac.numerator == 1:
        return f"π/{frac.denominator}"
    if frac.numerator == -1:
        return f"-π/{frac.denominator}"
    return f"{frac.numerator}π/{frac.denominator}"


def _spec(family: str, values: tuple, prompt: str, answer: str):
    canonical = ":".join([family] + [str(v) for v in values])
    return {"family": family, "values": values, "prompt": prompt, "answer": answer, "canonical_key": canonical, "case_id": canonical, "family_id": family}


def _sample_from_spec(spec: dict, difficulty: str, instruction_idx: int = 0) -> dict:
    metadata = {"family": spec["family"], "level_number": _level_num(difficulty), "structured": True, "canonical_key": spec["canonical_key"], "case_id": spec["case_id"], "family_id": spec["family_id"], "template_id": spec["family"], "final_answer": spec["answer"], "values": list(spec.get("values", []))}
    instruction = INSTRUCTIONS[instruction_idx % len(INSTRUCTIONS)].format(problem=spec["prompt"])
    return make_sample(module_id=MODULE_INFO["module_id"], topic=MODULE_INFO["topic"], subtopic=MODULE_INFO["subtopic"], difficulty=difficulty, instruction=instruction, input_text=spec["prompt"], answer=spec["answer"], metadata=metadata)


def iter_level1_specs():
    for idx, deg in enumerate([0, 30, 45, 60, 90, 120, 135, 150, 180]):
        if idx >= FAMILY_CAPS["level_1"]["deg_to_rad"]:
            return
        yield _spec("deg_to_rad", (deg,), f"Convert {deg}° to radians.", _rad_str(deg, 180))


def iter_level2_specs():
    emitted = 0
    for numer, denom in [(1, 6), (1, 4), (1, 3), (1, 2), (2, 3), (3, 4), (5, 6), (1, 1), (3, 2)]:
        degrees = int(180 * numer / denom)
        yield _spec("rad_to_deg", (numer, denom), f"Convert {_rad_str(numer, denom)} radians to degrees.", f"{degrees}°")
        emitted += 1
        if emitted >= FAMILY_CAPS["level_2"]["rad_to_deg"]:
            return


def iter_level3_specs():
    for idx, deg in enumerate([210, 225, 240, 270, 300, 315, 330, 360]):
        if idx >= FAMILY_CAPS["level_3"]["special_angles"]:
            return
        yield _spec("special_angles", (deg,), f"Express {deg}° in radians using π.", _rad_str(deg, 180))


def iter_level4_specs():
    for idx, deg in enumerate([-150, -90, -45, 405, 540, 720]):
        if idx >= FAMILY_CAPS["level_4"]["signed_and_large"]:
            return
        yield _spec("signed_and_large", (deg,), f"Convert {deg}° to radians in simplest terms.", _rad_str(deg, 180))


def iter_level5_specs():
    for idx, rev in enumerate([Fraction(1, 6), Fraction(1, 4), Fraction(1, 3), Fraction(3, 4), Fraction(5, 4), Fraction(3, 2)]):
        if idx >= FAMILY_CAPS["level_5"]["contextual_conversion"]:
            return
        yield _spec("contextual_conversion", (rev.numerator, rev.denominator), f"A wheel turns through {rev} of a full revolution. Express the rotation in radians.", _rad_str(rev.numerator * 2, rev.denominator))


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
    return {"level_1": ["basic degree-to-radian conversion"], "level_2": ["basic radian-to-degree conversion"], "level_3": ["extends to larger special angles"], "level_4": ["adds signed and multiple-turn angles"], "level_5": ["adds contextual revolution-to-radian conversion"]}


