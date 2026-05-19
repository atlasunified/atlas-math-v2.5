from __future__ import annotations

import itertools
import random
from typing import Iterable

from atlas_math.modules.shared.common import make_sample

MODULE_INFO = {
    "module_id": "arithmetic.integer_word_problems",
    "name": "Integer Word Problems",
    "topic": "arithmetic",
    "subtopic": "core_arithmetic",
    "difficulty_levels": ["level_1", "level_2", "level_3", "level_4", "level_5"],
    "enabled": True,
}

INSTRUCTIONS = [
    "Solve the word problem and give the final value: {problem}",
    "Read carefully and compute the answer: {problem}",
    "Translate the story into arithmetic and solve: {problem}",
    "Work through the integer word problem step by step: {problem}",
]

LEVEL_SPEC_CAPS = {
    "level_1": 900,
    "level_2": 1300,
    "level_3": 1700,
    "level_4": 2100,
    "level_5": 2500,
}

FAMILY_CAPS = {
    "level_1": {"combine_change": 900},
    "level_2": {"difference_compare": 650, "temperature_change": 650},
    "level_3": {"multi_step_money": 850, "inventory_change": 850},
    "level_4": {"distance_round_trip": 1050, "consecutive_days": 1050},
    "level_5": {"two_person_compare": 1250, "balance_after_sequence": 1250},
}

CAPACITY_HINTS = {level: {"value": cap, "quality": "capped"} for level, cap in LEVEL_SPEC_CAPS.items()}
MAX_SPEC_PREFIX = 5000
MAX_GENERATE_MULTIPLIER = 8
MAX_ITER_SAMPLES = 4096
NAMES = ("Ava", "Ben", "Cara", "Diego", "Eli", "Faye")
ITEMS = ("books", "stickers", "marbles", "cards", "tickets")


def _level_num(difficulty: str) -> int:
    try:
        value = int(str(difficulty).rsplit("_", 1)[-1])
    except Exception:
        value = 1
    return max(1, min(5, value))


def _difficulty_name(level: int) -> str:
    return f"level_{max(1, min(5, int(level)))}"


def _stable_seed(*parts) -> str:
    return "|".join(str(part) for part in parts)


def _take(iterable: Iterable[dict], n: int) -> Iterable[dict]:
    for idx, item in enumerate(iterable):
        if idx >= max(0, int(n)):
            break
        yield item


def _evaluate(spec: dict):
    family = spec["family"]
    v = spec["values"]
    if family == "combine_change":
        return v[0] + v[1]
    if family == "difference_compare":
        return v[0] - v[1]
    if family == "temperature_change":
        return v[0] + v[1]
    if family == "multi_step_money":
        return v[0] + v[1] - v[2]
    if family == "inventory_change":
        return v[0] - v[1] + v[2]
    if family == "distance_round_trip":
        return 2 * v[0] - v[1]
    if family == "consecutive_days":
        return v[0] + v[1] + v[2]
    if family == "two_person_compare":
        return (v[0] + v[1]) - (v[2] - v[3])
    if family == "balance_after_sequence":
        return v[0] + v[1] - v[2] + v[3]
    raise ValueError(f"Unknown family: {family}")


def _problem_text(spec: dict) -> str:
    family = spec["family"]
    v = spec["values"]
    names = spec["names"]
    item = spec["item"]
    if family == "combine_change":
        return f"{names[0]} has {v[0]} {item}. Then {names[0]} gets {v[1]} more. How many {item} does {names[0]} have now?"
    if family == "difference_compare":
        return f"{names[0]} has {v[0]} {item} and gives {v[1]} away. How many {item} remain?"
    if family == "temperature_change":
        return f"The temperature is {v[0]}°C in the morning and changes by {v[1]}°C by noon. What is the noon temperature?"
    if family == "multi_step_money":
        return f"{names[0]} starts with ${v[0]}, earns ${v[1]}, and then spends ${v[2]}. How much money is left?"
    if family == "inventory_change":
        return f"A box has {v[0]} {item}. {v[1]} are removed and then {v[2]} are added. How many are in the box now?"
    if family == "distance_round_trip":
        return f"A hiker walks {v[0]} miles out, then returns {v[1]} miles toward home. How far from home is the hiker now?"
    if family == "consecutive_days":
        return f"Over three days, a team scores {v[0]}, {v[1]}, and {v[2]} points. How many points in all?"
    if family == "two_person_compare":
        return (
            f"{names[0]} has {v[0]} {item} and gains {v[1]} more. {names[1]} has {v[2]} {item} but loses {v[3]}. "
            f"How many more {item} does {names[0]} have than {names[1]} after the changes?"
        )
    if family == "balance_after_sequence":
        return f"An account starts at {v[0]}. Then it changes by +{v[1]}, -{v[2]}, and +{v[3]}. What is the final balance?"
    raise ValueError(f"Unknown family: {family}")


def _sample_from_spec(spec: dict, difficulty: str, instruction_idx: int = 0) -> dict:
    problem = _problem_text(spec)
    answer = str(_evaluate(spec))
    metadata = {
        "family": spec["family"],
        "level_number": _level_num(difficulty),
        "structured": True,
        "canonical_key": spec["canonical_key"],
        "case_id": spec["case_id"],
        "family_id": spec["family_id"],
        "template_id": spec["family"],
        "final_answer": answer,
        "values": list(spec["values"]),
    }
    instruction = INSTRUCTIONS[instruction_idx % len(INSTRUCTIONS)].format(problem=problem)
    return make_sample(
        module_id=MODULE_INFO["module_id"],
        topic=MODULE_INFO["topic"],
        subtopic=MODULE_INFO["subtopic"],
        difficulty=difficulty,
        instruction=instruction,
        input_text=problem,
        answer=answer,
        metadata=metadata,
    )


def iter_level1_specs() -> Iterable[dict]:
    family = "combine_change"
    limit = FAMILY_CAPS["level_1"][family]
    emitted = 0
    for start in range(5, 81, 5):
        for change in range(1, 31):
            for idx, name in enumerate(NAMES):
                item = ITEMS[idx % len(ITEMS)]
                yield {
                    "family": family,
                    "values": (start, change),
                    "names": (name,),
                    "item": item,
                    "canonical_key": f"{family}:{start}:{change}:{name}:{item}",
                    "case_id": f"{family}:{start}:{change}:{name}:{item}",
                    "family_id": family,
                }
                emitted += 1
                if emitted >= limit:
                    return


def iter_level2_specs() -> Iterable[dict]:
    budgets = FAMILY_CAPS["level_2"]
    emitted = 0
    for start in range(10, 121, 5):
        for give in range(1, min(40, start)):
            name = NAMES[(start + give) % len(NAMES)]
            item = ITEMS[(start // 5 + give) % len(ITEMS)]
            yield {
                "family": "difference_compare",
                "values": (start, give),
                "names": (name,),
                "item": item,
                "canonical_key": f"difference_compare:{start}:{give}:{name}:{item}",
                "case_id": f"difference_compare:{start}:{give}:{name}:{item}",
                "family_id": "difference_compare",
            }
            emitted += 1
            if emitted >= budgets["difference_compare"]:
                break
        if emitted >= budgets["difference_compare"]:
            break

    emitted = 0
    for temp in range(-20, 31):
        for delta in range(-12, 13):
            if delta == 0:
                continue
            yield {
                "family": "temperature_change",
                "values": (temp, delta),
                "names": ("",),
                "item": "",
                "canonical_key": f"temperature_change:{temp}:{delta}",
                "case_id": f"temperature_change:{temp}:{delta}",
                "family_id": "temperature_change",
            }
            emitted += 1
            if emitted >= budgets["temperature_change"]:
                return


def iter_level3_specs() -> Iterable[dict]:
    budgets = FAMILY_CAPS["level_3"]
    emitted = 0
    for start in range(10, 101, 5):
        for earn in range(5, 46, 5):
            for spend in range(5, 41, 5):
                if start + earn - spend < 0:
                    continue
                name = NAMES[(start + earn + spend) % len(NAMES)]
                yield {
                    "family": "multi_step_money",
                    "values": (start, earn, spend),
                    "names": (name,),
                    "item": "dollars",
                    "canonical_key": f"multi_step_money:{start}:{earn}:{spend}:{name}",
                    "case_id": f"multi_step_money:{start}:{earn}:{spend}:{name}",
                    "family_id": "multi_step_money",
                }
                emitted += 1
                if emitted >= budgets["multi_step_money"]:
                    break
            if emitted >= budgets["multi_step_money"]:
                break
        if emitted >= budgets["multi_step_money"]:
            break

    emitted = 0
    for start in range(20, 151, 5):
        for removed in range(5, 51, 5):
            for added in range(5, 41, 5):
                if start - removed < 0:
                    continue
                item = ITEMS[(start + removed + added) % len(ITEMS)]
                yield {
                    "family": "inventory_change",
                    "values": (start, removed, added),
                    "names": ("",),
                    "item": item,
                    "canonical_key": f"inventory_change:{start}:{removed}:{added}:{item}",
                    "case_id": f"inventory_change:{start}:{removed}:{added}:{item}",
                    "family_id": "inventory_change",
                }
                emitted += 1
                if emitted >= budgets["inventory_change"]:
                    return


def iter_level4_specs() -> Iterable[dict]:
    budgets = FAMILY_CAPS["level_4"]
    emitted = 0
    for out_trip in range(6, 81):
        for back in range(1, out_trip + 1):
            yield {
                "family": "distance_round_trip",
                "values": (out_trip, back),
                "names": ("",),
                "item": "miles",
                "canonical_key": f"distance_round_trip:{out_trip}:{back}",
                "case_id": f"distance_round_trip:{out_trip}:{back}",
                "family_id": "distance_round_trip",
            }
            emitted += 1
            if emitted >= budgets["distance_round_trip"]:
                break
        if emitted >= budgets["distance_round_trip"]:
            break

    emitted = 0
    for a in range(-20, 31, 5):
        for b in range(-20, 31, 5):
            for c in range(-20, 31, 5):
                yield {
                    "family": "consecutive_days",
                    "values": (a, b, c),
                    "names": ("",),
                    "item": "points",
                    "canonical_key": f"consecutive_days:{a}:{b}:{c}",
                    "case_id": f"consecutive_days:{a}:{b}:{c}",
                    "family_id": "consecutive_days",
                }
                emitted += 1
                if emitted >= budgets["consecutive_days"]:
                    return


def iter_level5_specs() -> Iterable[dict]:
    budgets = FAMILY_CAPS["level_5"]
    emitted = 0
    for a in range(10, 91, 5):
        for gain in range(5, 31, 5):
            for b in range(10, 91, 5):
                for loss in range(5, 31, 5):
                    n1 = NAMES[(a + gain) % len(NAMES)]
                    n2 = NAMES[(b + loss + 1) % len(NAMES)]
                    if n1 == n2:
                        continue
                    item = ITEMS[(a + b) % len(ITEMS)]
                    yield {
                        "family": "two_person_compare",
                        "values": (a, gain, b, loss),
                        "names": (n1, n2),
                        "item": item,
                        "canonical_key": f"two_person_compare:{a}:{gain}:{b}:{loss}:{n1}:{n2}:{item}",
                        "case_id": f"two_person_compare:{a}:{gain}:{b}:{loss}:{n1}:{n2}:{item}",
                        "family_id": "two_person_compare",
                    }
                    emitted += 1
                    if emitted >= budgets["two_person_compare"]:
                        break
                if emitted >= budgets["two_person_compare"]:
                    break
            if emitted >= budgets["two_person_compare"]:
                break
        if emitted >= budgets["two_person_compare"]:
            break

    emitted = 0
    for start in range(-50, 101, 5):
        for a in range(5, 36, 5):
            for b in range(5, 31, 5):
                for c in range(5, 26, 5):
                    yield {
                        "family": "balance_after_sequence",
                        "values": (start, a, b, c),
                        "names": ("",),
                        "item": "balance",
                        "canonical_key": f"balance_after_sequence:{start}:{a}:{b}:{c}",
                        "case_id": f"balance_after_sequence:{start}:{a}:{b}:{c}",
                        "family_id": "balance_after_sequence",
                    }
                    emitted += 1
                    if emitted >= budgets["balance_after_sequence"]:
                        return


def _iter_specs(difficulty: str) -> Iterable[dict]:
    level = _level_num(difficulty)
    cap = LEVEL_SPEC_CAPS[_difficulty_name(level)]
    if level == 1:
        return _take(iter_level1_specs(), cap)
    if level == 2:
        return _take(itertools.chain(iter_level1_specs(), iter_level2_specs()), cap)
    if level == 3:
        return _take(itertools.chain(iter_level1_specs(), iter_level2_specs(), iter_level3_specs()), cap)
    if level == 4:
        return _take(itertools.chain(iter_level1_specs(), iter_level2_specs(), iter_level3_specs(), iter_level4_specs()), cap)
    return _take(itertools.chain(iter_level1_specs(), iter_level2_specs(), iter_level3_specs(), iter_level4_specs(), iter_level5_specs()), cap)


def generate(count: int = 10, difficulty: str = "level_1", seed=None):
    pool_size = min(MAX_SPEC_PREFIX, max(int(count) * MAX_GENERATE_MULTIPLIER, int(count), 64))
    pool = list(itertools.islice(_iter_specs(difficulty), 0, pool_size))
    rng = random.Random(_stable_seed(seed, difficulty, "generate"))
    rng.shuffle(pool)
    out = []
    seen = set()
    for idx, spec in enumerate(pool):
        sample = _sample_from_spec(spec, difficulty, instruction_idx=idx)
        key = sample.get("input", "")
        if key in seen:
            continue
        seen.add(key)
        out.append(sample)
        if len(out) >= count:
            break
    return out


def generate_unique(count: int = 10, difficulty: str = "level_1", offset: int = 0, stride: int = 1, seed=None):
    level = _difficulty_name(_level_num(difficulty))
    pool = list(itertools.islice(_iter_specs(difficulty), 0, min(LEVEL_SPEC_CAPS[level], MAX_ITER_SAMPLES)))
    rng = random.Random(_stable_seed(seed, difficulty, offset, stride, "generate_unique"))
    rng.shuffle(pool)
    out = []
    seen = set()
    for idx in range(max(0, int(offset)), len(pool), max(1, int(stride))):
        sample = _sample_from_spec(pool[idx], difficulty, instruction_idx=idx)
        key = sample.get("input", "")
        if key in seen:
            continue
        seen.add(key)
        out.append(sample)
        if len(out) >= count:
            break
    return out


def iter_samples(difficulty: str = "level_1", seed=None):
    level = _difficulty_name(_level_num(difficulty))
    pool = list(itertools.islice(_iter_specs(difficulty), 0, min(LEVEL_SPEC_CAPS[level], MAX_ITER_SAMPLES)))
    rng = random.Random(_stable_seed(seed, difficulty, "iter_samples"))
    rng.shuffle(pool)
    seen = set()
    for idx, spec in enumerate(pool):
        sample = _sample_from_spec(spec, difficulty, instruction_idx=idx)
        key = sample.get("input", "")
        if key in seen:
            continue
        seen.add(key)
        yield sample


def estimate_capacity(difficulty: str = "level_1"):
    return CAPACITY_HINTS.get(_difficulty_name(_level_num(difficulty)), {"value": None, "quality": "unknown"})


def curriculum() -> dict:
    return {
        "level_1": ["single-step integer increase stories"],
        "level_2": ["adds subtraction and signed temperature-change contexts"],
        "level_3": ["adds two-step money and inventory stories"],
        "level_4": ["adds multi-step travel and multi-day totals, including negatives"],
        "level_5": ["adds comparisons between people and longer signed balance sequences"],
    }


