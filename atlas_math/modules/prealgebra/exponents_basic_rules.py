from __future__ import annotations

import random
from typing import Iterable

from atlas_math.modules.shared.common import make_sample

MODULE_INFO = {
    "module_id": "prealgebra.exponents_basic_rules",
    "name": "Exponents: Basic Rules",
    "topic": "prealgebra",
    "subtopic": "core_prealgebra",
    "difficulty_levels": ["level_1", "level_2", "level_3", "level_4", "level_5"],
    "enabled": True,
}

INSTRUCTIONS = [
    "Simplify: {problem}",
    "Use the exponent rules: {problem}",
    "Rewrite in simplest form: {problem}",
    "Evaluate or simplify: {problem}",
]

LEVEL_SPEC_CAPS = {"level_1": 1000, "level_2": 1200, "level_3": 1200, "level_4": 1400, "level_5": 1600}
FAMILY_CAPS = {
    "level_1": {"evaluate_powers": 1000},
    "level_2": {"product_same_base": 1200},
    "level_3": {"quotient_same_base": 1200},
    "level_4": {"power_of_power": 1400},
    "level_5": {"negative_exponent_numeric": 1600},
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
    if family == "evaluate_powers":
        return v[0] ** v[1]
    if family == "product_same_base":
        return f"{v[0]}^{v[1] + v[2]}"
    if family == "quotient_same_base":
        return f"{v[0]}^{v[1] - v[2]}"
    if family == "power_of_power":
        return f"{v[0]}^{v[1] * v[2]}"
    if family == "negative_exponent_numeric":
        return f"1/{v[0] ** v[1]}"
    raise ValueError(f"Unknown family: {family}")


def _problem_text(spec: dict) -> str:
    family = spec["family"]
    v = spec["values"]
    if family == "evaluate_powers":
        return f"{v[0]}^{v[1]}"
    if family == "product_same_base":
        return f"{v[0]}^{v[1]} · {v[0]}^{v[2]}"
    if family == "quotient_same_base":
        return f"{v[0]}^{v[1]} / {v[0]}^{v[2]}"
    if family == "power_of_power":
        return f"({v[0]}^{v[1]})^{v[2]}"
    if family == "negative_exponent_numeric":
        return f"{v[0]}^(-{v[1]})"
    raise ValueError(f"Unknown family: {family}")


def _sample_from_spec(spec: dict, difficulty: str, instruction_idx: int = 0) -> dict:
    problem = _problem_text(spec)
    answer = str(_solve(spec))
    metadata = {"family": spec["family"], "level_number": _level_num(difficulty), "structured": True, "canonical_key": spec["canonical_key"], "case_id": spec["case_id"], "family_id": spec["family_id"], "template_id": spec["family"], "final_answer": answer, "values": list(spec["values"])}
    instruction = INSTRUCTIONS[instruction_idx % len(INSTRUCTIONS)].format(problem=problem)
    return make_sample(module_id=MODULE_INFO["module_id"], topic=MODULE_INFO["topic"], subtopic=MODULE_INFO["subtopic"], difficulty=difficulty, instruction=instruction, input_text=problem, answer=answer, metadata=metadata)


def iter_level1_specs() -> Iterable[dict]:
    emitted = 0
    for base in range(2, 11):
        for exp in range(2, 6):
            yield {"family": "evaluate_powers", "values": (base, exp), "canonical_key": f"evaluate_powers:{base}:{exp}", "case_id": f"evaluate_powers:{base}:{exp}", "family_id": "evaluate_powers"}
            emitted += 1
            if emitted >= FAMILY_CAPS["level_1"]["evaluate_powers"]:
                return


def iter_level2_specs() -> Iterable[dict]:
    emitted = 0
    for base in "xyzab":
        for e1 in range(1, 13):
            for e2 in range(1, 13):
                yield {"family": "product_same_base", "values": (base, e1, e2), "canonical_key": f"product_same_base:{base}:{e1}:{e2}", "case_id": f"product_same_base:{base}:{e1}:{e2}", "family_id": "product_same_base"}
                emitted += 1
                if emitted >= FAMILY_CAPS["level_2"]["product_same_base"]:
                    return


def iter_level3_specs() -> Iterable[dict]:
    emitted = 0
    for base in "xyzab":
        for e1 in range(2, 16):
            for e2 in range(1, e1 + 1):
                yield {"family": "quotient_same_base", "values": (base, e1, e2), "canonical_key": f"quotient_same_base:{base}:{e1}:{e2}", "case_id": f"quotient_same_base:{base}:{e1}:{e2}", "family_id": "quotient_same_base"}
                emitted += 1
                if emitted >= FAMILY_CAPS["level_3"]["quotient_same_base"]:
                    return


def iter_level4_specs() -> Iterable[dict]:
    emitted = 0
    for base in "xyzab":
        for e1 in range(2, 8):
            for e2 in range(2, 8):
                yield {"family": "power_of_power", "values": (base, e1, e2), "canonical_key": f"power_of_power:{base}:{e1}:{e2}", "case_id": f"power_of_power:{base}:{e1}:{e2}", "family_id": "power_of_power"}
                emitted += 1
                if emitted >= FAMILY_CAPS["level_4"]["power_of_power"]:
                    return


def iter_level5_specs() -> Iterable[dict]:
    emitted = 0
    for base in range(2, 13):
        for exp in range(1, 7):
            yield {"family": "negative_exponent_numeric", "values": (base, exp), "canonical_key": f"negative_exponent_numeric:{base}:{exp}", "case_id": f"negative_exponent_numeric:{base}:{exp}", "family_id": "negative_exponent_numeric"}
            emitted += 1
            if emitted >= FAMILY_CAPS["level_5"]["negative_exponent_numeric"]:
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


