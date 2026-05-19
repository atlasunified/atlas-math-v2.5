from __future__ import annotations

import random
from fractions import Fraction
from typing import Iterable

from atlas_math.modules.shared.common import make_sample

MODULE_INFO = {
    "module_id": "prealgebra.verbal_to_algebraic_expression",
    "name": "Verbal to Algebraic Expression",
    "topic": "prealgebra",
    "subtopic": "core_prealgebra",
    "difficulty_levels": ["level_1", "level_2", "level_3", "level_4", "level_5"],
    "enabled": True,
}
INSTRUCTIONS = [
    "Write an algebraic expression: {problem}",
    "Translate the words into an expression: {problem}",
    "Use the variable shown and write the expression: {problem}",
    "Convert the verbal phrase into algebra: {problem}",
]
LEVEL_SPEC_CAPS = {"level_1": 900, "level_2": 1100, "level_3": 1300, "level_4": 1500, "level_5": 1700}
FAMILY_CAPS = {"level_1": {"sum_difference": 900}, "level_2": {"product_quotient": 1100}, "level_3": {"multi_step_words": 1300}, "level_4": {"reversed_order": 1500}, "level_5": {"fractional_phrase": 1700}}
CAPACITY_HINTS = {level: {"value": cap, "quality": "capped"} for level, cap in LEVEL_SPEC_CAPS.items()}
MAX_SPEC_PREFIX = 5000
MAX_GENERATE_MULTIPLIER = 8
MAX_ITER_SAMPLES = 4096
VARIABLES = ("x", "y", "n", "t", "m")

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

def _build_problem_and_answer(spec: dict):
    family = spec["family"]
    v = spec["values"]
    if family == "sum_difference":
        var, a, op = v
        if op == "sum":
            return f"the sum of {var} and {a}", f"{var} + {a}"
        return f"{a} less than {var}", f"{var} - {a}"
    if family == "product_quotient":
        var, a, op = v
        if op == "product":
            return f"{a} times {var}", f"{a}{var}"
        return f"the quotient of {var} and {a}", f"{var}/{a}"
    if family == "multi_step_words":
        var, a, b = v
        return f"{a} more than twice {var}", f"2{var} + {a}"
    if family == "reversed_order":
        var, a, b = v
        return f"{a} decreased by {b} times {var}", f"{a} - {b}{var}"
    var, a, b = v
    return f"one-half of the quantity {var} plus {a}", f"({var} + {a})/2"

def _sample_from_spec(spec: dict, difficulty: str, instruction_idx: int = 0) -> dict:
    phrase, answer = _build_problem_and_answer(spec)
    problem = f"Use the variable exactly as written. Write an algebraic expression for {phrase}."
    metadata = {"family": spec["family"], "level_number": _level_num(difficulty), "structured": True, "canonical_key": spec["canonical_key"], "case_id": spec["case_id"], "family_id": spec["family_id"], "template_id": spec["family"], "final_answer": answer, "values": list(spec["values"])}
    instruction = INSTRUCTIONS[instruction_idx % len(INSTRUCTIONS)].format(problem=problem)
    return make_sample(module_id=MODULE_INFO["module_id"], topic=MODULE_INFO["topic"], subtopic=MODULE_INFO["subtopic"], difficulty=difficulty, instruction=instruction, input_text=problem, answer=answer, metadata=metadata)

def iter_level1_specs() -> Iterable[dict]:
    emitted = 0
    for var in VARIABLES:
        for a in range(1, 31):
            for op in ("sum", "difference"):
                yield {"family": "sum_difference", "values": (var, a, op), "canonical_key": f"sum_difference:{var}:{a}:{op}", "case_id": f"sum_difference:{var}:{a}:{op}", "family_id": "sum_difference"}
                emitted += 1
                if emitted >= FAMILY_CAPS["level_1"]["sum_difference"]:
                    return

def iter_level2_specs() -> Iterable[dict]:
    emitted = 0
    for var in VARIABLES:
        for a in range(2, 21):
            for op in ("product", "quotient"):
                yield {"family": "product_quotient", "values": (var, a, op), "canonical_key": f"product_quotient:{var}:{a}:{op}", "case_id": f"product_quotient:{var}:{a}:{op}", "family_id": "product_quotient"}
                emitted += 1
                if emitted >= FAMILY_CAPS["level_2"]["product_quotient"]:
                    return

def iter_level3_specs() -> Iterable[dict]:
    emitted = 0
    for var in VARIABLES:
        for a in range(1, 31):
            for b in range(0, 1):
                yield {"family": "multi_step_words", "values": (var, a, b), "canonical_key": f"multi_step_words:{var}:{a}:{b}", "case_id": f"multi_step_words:{var}:{a}:{b}", "family_id": "multi_step_words"}
                emitted += 1
                if emitted >= FAMILY_CAPS["level_3"]["multi_step_words"]:
                    return

def iter_level4_specs() -> Iterable[dict]:
    emitted = 0
    for var in VARIABLES:
        for a in range(5, 41):
            for b in range(2, 13):
                yield {"family": "reversed_order", "values": (var, a, b), "canonical_key": f"reversed_order:{var}:{a}:{b}", "case_id": f"reversed_order:{var}:{a}:{b}", "family_id": "reversed_order"}
                emitted += 1
                if emitted >= FAMILY_CAPS["level_4"]["reversed_order"]:
                    return

def iter_level5_specs() -> Iterable[dict]:
    emitted = 0
    for var in VARIABLES:
        for a in range(-20, 21):
            for b in range(0, 1):
                yield {"family": "fractional_phrase", "values": (var, a, b), "canonical_key": f"fractional_phrase:{var}:{a}:{b}", "case_id": f"fractional_phrase:{var}:{a}:{b}", "family_id": "fractional_phrase"}
                emitted += 1
                if emitted >= FAMILY_CAPS["level_5"]["fractional_phrase"]:
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


