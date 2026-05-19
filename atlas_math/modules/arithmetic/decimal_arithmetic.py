from __future__ import annotations

import itertools
import random
from decimal import Decimal, getcontext
from typing import Iterable

from atlas_math.modules.shared.common import make_sample

getcontext().prec = 28

MODULE_INFO = {
    "module_id": "arithmetic.decimal_arithmetic",
    "name": "Decimal Arithmetic",
    "topic": "arithmetic",
    "subtopic": "core_arithmetic",
    "difficulty_levels": ["level_1", "level_2", "level_3", "level_4", "level_5"],
    "enabled": True,
}

INSTRUCTIONS = [
    "Compute the decimal expression: {problem}",
    "Evaluate the decimal arithmetic carefully: {problem}",
    "Find the value of the decimal expression: {problem}",
    "Work through the decimal operations and simplify the result: {problem}",
]

LEVEL_SPEC_CAPS = {
    "level_1": 1200,
    "level_2": 1600,
    "level_3": 2000,
    "level_4": 2400,
    "level_5": 2800,
}

FAMILY_CAPS = {
    "level_1": {"decimal_add_sub": 1200},
    "level_2": {"decimal_multiply_tenths": 800, "decimal_money_style": 800},
    "level_3": {"decimal_exact_division": 1000, "decimal_mixed_ops": 1000},
    "level_4": {"decimal_parentheses": 1200, "decimal_scale_shift": 1200},
    "level_5": {"decimal_nested": 1400, "decimal_ratio": 1400},
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


def _difficulty_name(level: int) -> str:
    return f"level_{max(1, min(5, int(level)))}"


def _stable_seed(*parts) -> str:
    return "|".join(str(part) for part in parts)


def _take(iterable: Iterable[dict], n: int) -> Iterable[dict]:
    for idx, item in enumerate(iterable):
        if idx >= max(0, int(n)):
            break
        yield item


def _dec(s: str) -> Decimal:
    return Decimal(s)


def _fmt_decimal(value: Decimal) -> str:
    normalized = value.normalize()
    text = format(normalized, 'f')
    if '.' in text:
        text = text.rstrip('0').rstrip('.')
    if text == '-0':
        text = '0'
    return text


def _make_spec(family: str, display: str, tag: str, data: tuple, op: str | None = None) -> dict:
    spec = {
        "family": family,
        "display": display,
        "data": data,
        "canonical_key": f"{family}:{tag}",
        "case_id": f"{family}:{tag}",
        "family_id": family,
    }
    if op is not None:
        spec["op"] = op
    return spec


def _evaluate(spec: dict) -> Decimal:
    family = spec["family"]
    data = spec["data"]
    if family in {"decimal_add_sub", "decimal_multiply_tenths", "decimal_exact_division"}:
        left = _dec(data[0])
        right = _dec(data[1])
        op = spec["op"]
        if op == "+":
            return left + right
        if op == "-":
            return left - right
        if op == "×":
            return left * right
        if op == "÷":
            return left / right
    if family == "decimal_money_style":
        left = _dec(data[0])
        right = _dec(data[1])
        return left + right if spec["op"] == "+" else left - right
    if family == "decimal_mixed_ops":
        return (_dec(data[0]) * _dec(data[1])) + _dec(data[2])
    if family == "decimal_parentheses":
        return (_dec(data[0]) + _dec(data[1])) * _dec(data[2])
    if family == "decimal_scale_shift":
        return (_dec(data[0]) * _dec(data[1])) - _dec(data[2])
    if family == "decimal_nested":
        return ((_dec(data[0]) - _dec(data[1])) / _dec(data[2])) + _dec(data[3])
    if family == "decimal_ratio":
        return (_dec(data[0]) + _dec(data[1])) / _dec(data[2])
    raise ValueError(f"Unknown family: {family}")


def _sample_from_spec(spec: dict, difficulty: str, instruction_idx: int = 0) -> dict:
    problem = spec["display"]
    answer = _fmt_decimal(_evaluate(spec))
    metadata = {
        "family": spec["family"],
        "level_number": _level_num(difficulty),
        "structured": True,
        "canonical_key": spec["canonical_key"],
        "case_id": spec["case_id"],
        "family_id": spec["family_id"],
        "template_id": spec["family"],
        "final_answer": answer,
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
    family = "decimal_add_sub"
    limit = FAMILY_CAPS["level_1"][family]
    emitted = 0
    tenths = [f"{whole}.{digit}" for whole in range(0, 16) for digit in range(10)]
    for left in tenths:
        for right in tenths:
            op = "+" if emitted % 2 == 0 else "-"
            yield _make_spec(family, f"{left} {op} {right}", f"{left}:{right}:{op}", (left, right), op)
            emitted += 1
            if emitted >= limit:
                return


def iter_level2_specs() -> Iterable[dict]:
    budgets = FAMILY_CAPS["level_2"]
    tenths = [f"{whole}.{digit}" for whole in range(0, 13) for digit in range(10)]
    hundredths = [f"{whole}.{d1}{d2}" for whole in range(0, 10) for d1 in range(10) for d2 in (0, 5)]

    emitted = 0
    for left in tenths:
        for right in ["0.1", "0.2", "0.25", "0.5", "1.5", "2.0"]:
            yield _make_spec(
                "decimal_multiply_tenths",
                f"{left} × {right}",
                f"{left}:{right}",
                (left, right),
                "×",
            )
            emitted += 1
            if emitted >= budgets["decimal_multiply_tenths"]:
                break
        if emitted >= budgets["decimal_multiply_tenths"]:
            break

    emitted = 0
    for left in hundredths:
        for right in hundredths:
            op = "+" if (len(left) + len(right) + emitted) % 2 == 0 else "-"
            yield _make_spec(
                "decimal_money_style",
                f"{left} {op} {right}",
                f"{left}:{right}:{op}",
                (left, right),
                op,
            )
            emitted += 1
            if emitted >= budgets["decimal_money_style"]:
                return


def iter_level3_specs() -> Iterable[dict]:
    budgets = FAMILY_CAPS["level_3"]

    emitted = 0
    quotients = [f"{whole}.{digit}" for whole in range(0, 11) for digit in (0, 2, 4, 5, 6, 8)]
    divisors = ["0.2", "0.4", "0.5", "0.8", "1.2", "1.25", "2.5", "4.0"]
    for q in quotients:
        for d in divisors:
            n = _fmt_decimal(_dec(q) * _dec(d))
            yield _make_spec(
                "decimal_exact_division",
                f"{n} ÷ {d}",
                f"{n}:{d}:{q}",
                (n, d),
                "÷",
            )
            emitted += 1
            if emitted >= budgets["decimal_exact_division"]:
                break
        if emitted >= budgets["decimal_exact_division"]:
            break

    emitted = 0
    a_vals = ["0.5", "1.2", "1.5", "2.4", "3.5", "4.8", "6.0"]
    b_vals = ["0.2", "0.25", "0.5", "1.5", "2.0"]
    c_vals = ["0.1", "0.3", "0.75", "1.25", "2.5"]
    for a in a_vals:
        for b in b_vals:
            for c in c_vals:
                yield _make_spec(
                    "decimal_mixed_ops",
                    f"({a} × {b}) + {c}",
                    f"{a}:{b}:{c}",
                    (a, b, c),
                )
                emitted += 1
                if emitted >= budgets["decimal_mixed_ops"]:
                    return


def iter_level4_specs() -> Iterable[dict]:
    budgets = FAMILY_CAPS["level_4"]
    a_vals = ["0.6", "1.2", "1.8", "2.4", "3.0", "4.5", "5.4"]
    b_vals = ["0.4", "0.5", "0.75", "1.25", "2.0"]
    c_vals = ["0.2", "0.5", "1.5", "2.5"]

    emitted = 0
    for a in a_vals:
        for b in b_vals:
            for c in c_vals:
                yield _make_spec(
                    "decimal_parentheses",
                    f"({a} + {b}) × {c}",
                    f"{a}:{b}:{c}",
                    (a, b, c),
                )
                emitted += 1
                if emitted >= budgets["decimal_parentheses"]:
                    break
            if emitted >= budgets["decimal_parentheses"]:
                break
        if emitted >= budgets["decimal_parentheses"]:
            break

    emitted = 0
    x_vals = ["0.12", "0.25", "0.4", "0.75", "1.2", "2.5", "3.6"]
    y_vals = ["10", "100", "0.1"]
    z_vals = ["0.2", "0.5", "1.0", "2.5", "4.0"]
    for x in x_vals:
        for y in y_vals:
            for z in z_vals:
                yield _make_spec(
                    "decimal_scale_shift",
                    f"({x} × {y}) - {z}",
                    f"{x}:{y}:{z}",
                    (x, y, z),
                )
                emitted += 1
                if emitted >= budgets["decimal_scale_shift"]:
                    return


def iter_level5_specs() -> Iterable[dict]:
    budgets = FAMILY_CAPS["level_5"]
    a_vals = ["2.4", "3.6", "4.8", "6.0", "7.2", "8.4"]
    b_vals = ["0.4", "0.6", "1.2", "1.8", "2.4"]
    c_vals = ["0.2", "0.3", "0.5", "0.6", "1.2"]
    d_vals = ["0.25", "0.5", "1.75", "2.5", "3.0"]

    emitted = 0
    for a in a_vals:
        for b in b_vals:
            for c in c_vals:
                for d in d_vals:
                    yield _make_spec(
                        "decimal_nested",
                        f"(({a} - {b}) ÷ {c}) + {d}",
                        f"{a}:{b}:{c}:{d}",
                        (a, b, c, d),
                    )
                    emitted += 1
                    if emitted >= budgets["decimal_nested"]:
                        break
                if emitted >= budgets["decimal_nested"]:
                    break
            if emitted >= budgets["decimal_nested"]:
                break
        if emitted >= budgets["decimal_nested"]:
            break

    emitted = 0
    p_vals = ["0.5", "1.25", "2.5", "3.75", "5.0"]
    q_vals = ["0.25", "0.75", "1.5", "2.25", "4.5"]
    r_vals = ["0.5", "1.0", "1.25", "2.5"]
    for p in p_vals:
        for q in q_vals:
            for r in r_vals:
                yield _make_spec(
                    "decimal_ratio",
                    f"({p} + {q}) ÷ {r}",
                    f"{p}:{q}:{r}",
                    (p, q, r),
                )
                emitted += 1
                if emitted >= budgets["decimal_ratio"]:
                    return


def _iter_specs(difficulty: str) -> Iterable[dict]:
    level = _level_num(difficulty)
    emitted = 0
    for lvl in range(1, level + 1):
        for spec in _take(globals()[f"iter_level{lvl}_specs"](), LEVEL_SPEC_CAPS[_difficulty_name(lvl)]):
            yield spec
            emitted += 1
            if emitted >= LEVEL_SPEC_CAPS.get(difficulty, LEVEL_SPEC_CAPS["level_5"]):
                return


def estimate_capacity(difficulty: str = "level_1"):
    return CAPACITY_HINTS.get(difficulty, {"value": None, "quality": "unknown"})


def generate(count: int = 10, difficulty: str = "level_1", seed=None) -> list[dict]:
    prefix = min(max(int(count) * MAX_GENERATE_MULTIPLIER, 256), MAX_SPEC_PREFIX, LEVEL_SPEC_CAPS.get(difficulty, 2000))
    pool = list(itertools.islice(_iter_specs(difficulty), 0, prefix))
    if not pool:
        return []
    rng = random.Random(_stable_seed(seed, difficulty, "generate"))
    rng.shuffle(pool)
    out: list[dict] = []
    seen: set[str] = set()
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


def generate_unique(count: int = 10, difficulty: str = "level_1", offset: int = 0, stride: int = 1, seed=None) -> list[dict]:
    pool_cap = min(LEVEL_SPEC_CAPS.get(difficulty, 2000), MAX_SPEC_PREFIX)
    pool = list(itertools.islice(_iter_specs(difficulty), 0, pool_cap))
    rng = random.Random(_stable_seed(seed, difficulty, offset, stride, "generate_unique"))
    rng.shuffle(pool)
    out: list[dict] = []
    seen: set[str] = set()
    start = max(0, int(offset))
    step = max(1, int(stride))
    for local_idx, spec in enumerate(pool[start::step]):
        sample = _sample_from_spec(spec, difficulty, instruction_idx=start + local_idx * step)
        key = sample.get("input", "")
        if key in seen:
            continue
        seen.add(key)
        out.append(sample)
        if len(out) >= count:
            break
    return out


def iter_samples(difficulty: str = "level_1", seed=None):
    max_items = min(LEVEL_SPEC_CAPS.get(difficulty, 2000), MAX_ITER_SAMPLES)
    pool = list(itertools.islice(_iter_specs(difficulty), 0, max_items))
    rng = random.Random(_stable_seed(seed, difficulty, "iter_samples"))
    rng.shuffle(pool)
    seen: set[str] = set()
    for idx, spec in enumerate(pool):
        sample = _sample_from_spec(spec, difficulty, instruction_idx=idx)
        key = sample.get("input", "")
        if key in seen:
            continue
        seen.add(key)
        yield sample


def curriculum() -> dict:
    return {
        "level_1": ["add and subtract decimals with tenths"],
        "level_2": ["extends level 1 with decimal multiplication and hundredths-style arithmetic"],
        "level_3": ["adds exact decimal division and mixed-operation expressions"],
        "level_4": ["adds parenthesized decimal expressions and scale-shift patterns"],
        "level_5": ["adds nested decimal expressions and ratio-style division while staying finite"],
    }


