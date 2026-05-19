from __future__ import annotations

import itertools
import random
from typing import Iterable

from atlas_math.modules.shared.common import make_sample

MODULE_INFO = {
    "module_id": "trigonometry.right_triangle_trig_sin_cos_tan",
    "name": "Right Triangle Trig Sin Cos Tan",
    "topic": "trigonometry",
    "subtopic": "core_trigonometry",
    "difficulty_levels": ["level_1", "level_2", "level_3", "level_4", "level_5"],
    "enabled": True,
}

INSTRUCTIONS = [
    "Evaluate the trig ratio in the right triangle setting: {problem}",
    "Find the requested sine, cosine, or tangent value: {problem}",
    "Use right triangle trigonometry: {problem}",
]

LEVEL_SPEC_CAPS = {"level_1": 600, "level_2": 800, "level_3": 1000, "level_4": 1200, "level_5": 1400}
FAMILY_CAPS = {
    "level_1": {"direct_ratio": 600},
    "level_2": {"find_side": 400, "direct_ratio": 400},
    "level_3": {"pythagorean_then_ratio": 500, "find_side": 500},
    "level_4": {"scaled_triangles": 600, "mixed_ratio": 600},
    "level_5": {"word_context": 700, "multi_given": 700},
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


def _fmt(value: float) -> str:
    if abs(value - round(value)) < 1e-9:
        return str(int(round(value)))
    return f"{value:.3f}".rstrip("0").rstrip(".")


def _spec(family: str, values: tuple, prompt: str, answer: str):
    canonical = ":".join([family] + [str(v) for v in values])
    return {
        "family": family,
        "values": values,
        "prompt": prompt,
        "answer": answer,
        "canonical_key": canonical,
        "case_id": canonical,
        "family_id": family,
    }


def _sample_from_spec(spec: dict, difficulty: str, instruction_idx: int = 0) -> dict:
    metadata = {
        "family": spec["family"],
        "level_number": _level_num(difficulty),
        "structured": True,
        "canonical_key": spec["canonical_key"],
        "case_id": spec["case_id"],
        "family_id": spec["family_id"],
        "template_id": spec["family"],
        "final_answer": spec["answer"],
        "values": list(spec.get("values", [])),
    }
    instruction = INSTRUCTIONS[instruction_idx % len(INSTRUCTIONS)].format(problem=spec["prompt"])
    return make_sample(
        module_id=MODULE_INFO["module_id"],
        topic=MODULE_INFO["topic"],
        subtopic=MODULE_INFO["subtopic"],
        difficulty=difficulty,
        instruction=instruction,
        input_text=spec["prompt"],
        answer=spec["answer"],
        metadata=metadata,
    )


def _triples():
    return [(3, 4, 5), (5, 12, 13), (8, 15, 17), (7, 24, 25), (9, 12, 15), (6, 8, 10)]


def iter_level1_specs():
    limit = FAMILY_CAPS["level_1"]["direct_ratio"]
    emitted = 0
    for opp, adj, hyp in _triples():
        prompts = [
            ("sin", opp / hyp),
            ("cos", adj / hyp),
            ("tan", opp / adj),
        ]
        for fn, value in prompts:
            prompt = f"A right triangle has opposite={opp}, adjacent={adj}, and hypotenuse={hyp}. Find {fn}(θ)."
            yield _spec("direct_ratio", (fn, opp, adj, hyp), prompt, _fmt(value))
            emitted += 1
            if emitted >= limit:
                return


def iter_level2_specs():
    emitted = 0
    for opp, adj, hyp in _triples():
        prompt = f"In a right triangle, tan(θ)={opp}/{adj} and the adjacent side is {adj}. Find the opposite side."
        yield _spec("find_side", (opp, adj), prompt, str(opp))
        emitted += 1
        if emitted >= FAMILY_CAPS["level_2"]["find_side"]:
            break
    emitted = 0
    for opp, adj, hyp in _triples():
        for fn, value in [("sin", opp / hyp), ("cos", adj / hyp), ("tan", opp / adj)]:
            prompt = f"For a right triangle with side lengths {opp}, {adj}, and {hyp}, determine {fn}(θ) where θ is opposite the side of length {opp}."
            yield _spec("direct_ratio", (fn, opp, adj, hyp, "theta"), prompt, _fmt(value))
            emitted += 1
            if emitted >= FAMILY_CAPS["level_2"]["direct_ratio"]:
                return


def iter_level3_specs():
    emitted = 0
    for a, b, hyp in [(3, 4, 5), (5, 12, 13), (8, 15, 17), (7, 24, 25)]:
        for fn, value in [("sin", a / hyp), ("cos", b / hyp), ("tan", a / b)]:
            prompt = f"A right triangle has legs {a} and {b}. First determine the hypotenuse, then compute {fn}(θ) where θ is opposite the side of length {a}."
            yield _spec("pythagorean_then_ratio", (fn, a, b), prompt, _fmt(value))
            emitted += 1
            if emitted >= FAMILY_CAPS["level_3"]["pythagorean_then_ratio"]:
                break
        if emitted >= FAMILY_CAPS["level_3"]["pythagorean_then_ratio"]:
            break
    emitted = 0
    for opp, adj, hyp in _triples():
        for fn, target, known in [("sin", opp, hyp), ("cos", adj, hyp)]:
            prompt = f"In a right triangle, {fn}(θ)={target}/{known} and the hypotenuse is {known}. Find the {'opposite' if fn == 'sin' else 'adjacent'} side."
            yield _spec("find_side", (fn, target, known), prompt, str(target))
            emitted += 1
            if emitted >= FAMILY_CAPS["level_3"]["find_side"]:
                return


def iter_level4_specs():
    emitted = 0
    for opp, adj, hyp in _triples():
        for scale in [6, 7, 8, 9]:
            O, A, H = opp * scale, adj * scale, hyp * scale
            prompt = f"A scaled right triangle has side lengths {O}, {A}, and {H}. Compute sin(θ), cos(θ), and tan(θ) for the angle opposite {O}. Give tan(θ)."
            yield _spec("scaled_triangles", (O, A, H), prompt, _fmt(O / A))
            emitted += 1
            if emitted >= FAMILY_CAPS["level_4"]["scaled_triangles"]:
                break
        if emitted >= FAMILY_CAPS["level_4"]["scaled_triangles"]:
            break
    emitted = 0
    for opp, adj, hyp in _triples():
        prompt = f"A ladder makes a right triangle with height {opp}, base {adj}, and ladder length {hyp}. Find cos(θ) where θ is the angle the ladder makes with the ground."
        yield _spec("mixed_ratio", (opp, adj, hyp), prompt, _fmt(adj / hyp))
        emitted += 1
        if emitted >= FAMILY_CAPS["level_4"]["mixed_ratio"]:
            return


def iter_level5_specs():
    emitted = 0
    for opp, adj, hyp in _triples():
        for label in ["ramp", "kite string", "support cable", "beam"]:
            prompt = f"A {label} forms a right triangle with vertical rise {opp} and horizontal run {adj}. Find tan(θ) for the angle of elevation."
            yield _spec("word_context", (label, opp, adj), prompt, _fmt(opp / adj))
            emitted += 1
            if emitted >= FAMILY_CAPS["level_5"]["word_context"]:
                break
        if emitted >= FAMILY_CAPS["level_5"]["word_context"]:
            break
    emitted = 0
    for opp, adj, hyp in _triples():
        prompt = f"In a right triangle, the legs are {opp} and {adj}. Compute the hypotenuse and then find sin(θ)+cos(θ) for the angle opposite {opp}."
        yield _spec("multi_given", (opp, adj, hyp), prompt, _fmt(opp / hyp + adj / hyp))
        emitted += 1
        if emitted >= FAMILY_CAPS["level_5"]["multi_given"]:
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
    prefix = min(max(count * MAX_GENERATE_MULTIPLIER, 256), MAX_SPEC_PREFIX)
    pool = list(itertools.islice(_iter_specs(difficulty), 0, prefix))
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
    prefix = min(max(count * max(1, stride) * 16 + max(0, offset), 512), MAX_SPEC_PREFIX)
    pool = list(itertools.islice(_iter_specs(difficulty), 0, prefix))
    rng = random.Random(_stable_seed(seed, MODULE_INFO["module_id"], difficulty, offset, stride, "unique"))
    rng.shuffle(pool)
    deduped = []
    seen = set()
    for spec in pool:
        key = spec["canonical_key"]
        if key in seen:
            continue
        seen.add(key)
        deduped.append(spec)
    out = []
    used = set()
    for idx, spec in enumerate(deduped[max(0, offset)::max(1, stride)]):
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
        "level_1": ["direct ratio evaluation from labeled right-triangle sides"],
        "level_2": ["adds missing-side recovery using one ratio"],
        "level_3": ["adds Pythagorean setup before taking ratios"],
        "level_4": ["adds scaled and contextual right-triangle interpretations"],
        "level_5": ["adds composed multi-step reasoning while keeping bounded triples"],
    }


