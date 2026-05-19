from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
from typing import Iterable
import itertools

OPS = [">", "<", ">=", "<="]
FLIP = {">": "<", "<": ">", ">=": "<=", "<=": ">="}

LEVEL4_SYSTEM_AND_SOLUTIONS = list(
    (Fraction(left), Fraction(right))
    for left in range(-10, 8)
    for right in range(-7, 11)
    if left < right
)
LEVEL4_SYSTEM_AND_LEFT_COEFFS = [2, 3, -2, -3]
LEVEL4_SYSTEM_AND_RIGHT_COEFFS = [2, 3, -2, -3]
LEVEL4_SYSTEM_AND_OFFSETS = range(-6, 7)
LEVEL4_SYSTEM_OR_LEFTS = range(-12, 0)
LEVEL4_SYSTEM_OR_RIGHTS = range(1, 13)
LEVEL4_SYSTEM_OR_LEFT_COEFFS = [2, -2, 3, -3]
LEVEL4_SYSTEM_OR_RIGHT_COEFFS = [2, -2, 4, -4]
LEVEL4_SYSTEM_OR_OFFSETS = range(-6, 7)
LEVEL4_RATIONAL_BOUNDS = [
    Fraction(n, d)
    for d in [2, 3, 4]
    for n in range(-9, 10)
    if n != 0 and abs(n) < 9
]
LEVEL4_RATIONAL_COEFFS = [2, 3, -2, -3]
LEVEL4_RATIONAL_OFFSETS = range(-9, 10)


def frac_text(value: Fraction | int) -> str:
    if not isinstance(value, Fraction):
        value = Fraction(value)
    return str(value.numerator) if value.denominator == 1 else f"{value.numerator}/{value.denominator}"


def signed_num(n: int) -> str:
    return f"+ {n}" if n >= 0 else f"- {abs(n)}"


def normalize_expr(a: int, b: int, var: str = "x") -> str:
    pieces: list[str] = []
    if a != 0:
        if a == 1:
            pieces.append(var)
        elif a == -1:
            pieces.append(f"-{var}")
        else:
            pieces.append(f"{a}{var}")
    if b != 0 or not pieces:
        if pieces:
            pieces.append(f"+ {b}" if b >= 0 else f"- {abs(b)}")
        else:
            pieces.append(str(b))
    return " ".join(pieces)


def interval_from_bounds(left: Fraction | None, left_closed: bool, right: Fraction | None, right_closed: bool) -> str:
    if left is None and right is None:
        return "(-∞, ∞)"
    if left is not None and right is not None and left == right and left_closed and right_closed:
        return "{" + frac_text(left) + "}"
    l_br = "[" if left_closed else "("
    r_br = "]" if right_closed else ")"
    l_txt = "-∞" if left is None else frac_text(left)
    r_txt = "∞" if right is None else frac_text(right)
    return f"{l_br}{l_txt}, {r_txt}{r_br}"


def inequality_solution_text(var: str, op: str, bound: Fraction | int) -> str:
    return f"{var} {op} {frac_text(bound)}"


def combine_and(parts: list[str]) -> str:
    return " and ".join(parts)


def combine_or(parts: list[str]) -> str:
    return " or ".join(parts)


def solve_linear_inequality(a: int, b: int, op: str, c: Fraction | int):
    c = Fraction(c)
    rhs = c - b
    if a == 0:
        return {
            "kind": "all" if _truth(Fraction(b), op, c) else "none",
            "op": None,
            "bound": None,
            "interval": "(-∞, ∞)" if _truth(Fraction(b), op, c) else "∅",
        }
    bound = rhs / a
    new_op = FLIP[op] if a < 0 else op
    interval = _interval_for_single(new_op, bound)
    return {
        "kind": "single",
        "op": new_op,
        "bound": bound,
        "interval": interval,
    }


def _truth(left: Fraction, op: str, right: Fraction) -> bool:
    if op == ">":
        return left > right
    if op == "<":
        return left < right
    if op == ">=":
        return left >= right
    return left <= right


def _interval_for_single(op: str, bound: Fraction) -> str:
    if op == ">":
        return interval_from_bounds(bound, False, None, False)
    if op == ">=":
        return interval_from_bounds(bound, True, None, False)
    if op == "<":
        return interval_from_bounds(None, False, bound, False)
    return interval_from_bounds(None, False, bound, True)


@dataclass(frozen=True)
class Step:
    text: str


@dataclass(frozen=True)
class WorkedAnswer:
    steps: tuple[str, ...]
    final_answer: str
    interval: str | None = None

    def render(self) -> str:
        numbered = [f"Step {i + 1}: {t}" for i, t in enumerate(self.steps)]
        if self.interval:
            numbered.append(f"Solution in interval notation: {self.interval}")
        numbered.append(f"Final answer: {self.final_answer}")
        return "\n".join(numbered)


def render_by_level(level: int, steps: list[str], final_answer: str, interval: str | None = None) -> str:
    if level <= 2:
        compact = steps[:3]
    elif level == 3:
        compact = steps[:4]
    else:
        compact = steps
    return WorkedAnswer(tuple(compact), final_answer, interval).render()


def _lcm(a: int, b: int) -> int:
    import math
    return abs(a * b) // math.gcd(a, b)


def _scaled_eq(a1: int, b1: int, c1: int, a2: int, b2: int, c2: int) -> tuple[tuple[int, int, int], tuple[int, int, int]]:
    k = _lcm(abs(a1), abs(a2))
    m1 = k // abs(a1)
    m2 = k // abs(a2)
    s1 = 1 if a1 > 0 else -1
    s2 = -1 if a2 > 0 else 1
    return (a1 * m1 * s1, b1 * m1 * s1, c1 * m1 * s1), (a2 * m2 * s2, b2 * m2 * s2, c2 * m2 * s2)


def _int_range(start: int, stop: int) -> Iterable[int]:
    return range(start, stop + 1)


def iter_level1_specs() -> Iterable[dict]:
    var = "x"
    for op in OPS:
        for family in ("add", "sub", "mul", "div"):
            for sol in _int_range(-12, 12):
                for c in _int_range(-9, 9):
                    if family in {"add", "sub"}:
                        if family == "add":
                            rhs = sol + c
                            if abs(rhs) > 30:
                                continue
                            yield {"family": family, "var": var, "op": op, "sol": Fraction(sol), "c": c, "rhs": Fraction(rhs)}
                        else:
                            rhs = sol - c
                            if abs(rhs) > 30:
                                continue
                            yield {"family": family, "var": var, "op": op, "sol": Fraction(sol), "c": c, "rhs": Fraction(rhs)}
                    elif family == "mul":
                        if c in (0, 1, -1):
                            continue
                        rhs = c * sol
                        if abs(rhs) > 50:
                            continue
                        yield {"family": family, "var": var, "op": op, "sol": Fraction(sol), "c": c, "rhs": Fraction(rhs)}
                    else:
                        if c in (0, 1, -1):
                            continue
                        rhs = Fraction(sol, c)
                        if abs(rhs.numerator) > 50:
                            continue
                        yield {"family": family, "var": var, "op": op, "sol": Fraction(sol), "c": c, "rhs": rhs}


def iter_level2_specs() -> Iterable[dict]:
    var = "x"
    for op in OPS:
        for family in ("two_step", "distributed", "fractional"):
            for sol in _int_range(-12, 12):
                if family == "two_step":
                    for a, b in itertools.product([2, 3, 4, 5, -2, -3, -4, -5], _int_range(-10, 10)):
                        rhs = a * sol + b
                        if abs(rhs) > 80:
                            continue
                        yield {"family": family, "var": var, "op": op, "sol": Fraction(sol), "a": a, "b": b, "rhs": Fraction(rhs)}
                elif family == "distributed":
                    for a, inner, b in itertools.product([2, 3, 4, -2, -3, -4], _int_range(-6, 6), _int_range(-12, 12)):
                        rhs = a * (sol + inner) + b
                        if abs(rhs) > 100:
                            continue
                        yield {"family": family, "var": var, "op": op, "sol": Fraction(sol), "a": a, "inner": inner, "b": b, "rhs": Fraction(rhs)}
                else:
                    for den, b in itertools.product([2, 3, 4, -2, -3, -4], _int_range(-10, 10)):
                        rhs = Fraction(sol + b, den)
                        if abs(rhs.numerator) > 100:
                            continue
                        yield {"family": family, "var": var, "op": op, "sol": Fraction(sol), "den": den, "b": b, "rhs": rhs}


def iter_level3_specs() -> Iterable[dict]:
    var = "x"
    # unique solution
    for op in OPS:
        for sol in _int_range(-15, 15):
            for a, c in itertools.product([2, 3, 4, 5, -2, -3, -4, -5], repeat=2):
                if a == c:
                    continue
                for b, d in itertools.product(_int_range(-12, 12), repeat=2):
                    if abs((a - c) * sol + b - d) > 120:
                        continue
                    yield {"family": "both_sides_unique", "var": var, "op": op, "sol": Fraction(sol), "a": a, "b": b, "c": c, "d": d}
    # all real / none
    for op in OPS:
        for a, b in itertools.product([1, 2, 3, -1, -2, -3], _int_range(-12, 12)):
            for delta in [0, 1, 2, 3]:
                d = b + delta
                fam = "both_sides_all" if _truth(Fraction(b), op, Fraction(d)) else "both_sides_none"
                yield {"family": fam, "var": var, "op": op, "a": a, "b": b, "c": a, "d": d}
    # compound and/or from pair of single inequalities
    bounds = list(_int_range(-12, 12))
    for left, right in itertools.product(bounds, bounds):
        if left >= right:
            continue
        yield {"family": "compound_and", "var": var, "left": Fraction(left), "right": Fraction(right), "left_closed": False, "right_closed": True}
        yield {"family": "compound_or", "var": var, "left": Fraction(left), "right": Fraction(right), "left_closed": True, "right_closed": False}


def iter_level4_specs() -> Iterable[dict]:
    var = "x"
    # intersections of two transformed inequalities
    for op1, op2 in itertools.product(OPS, repeat=2):
        for sol_left, sol_right in LEVEL4_SYSTEM_AND_SOLUTIONS:
            for a1, b1 in itertools.product(LEVEL4_SYSTEM_AND_LEFT_COEFFS, LEVEL4_SYSTEM_AND_OFFSETS):
                for a2, b2 in itertools.product(LEVEL4_SYSTEM_AND_RIGHT_COEFFS, LEVEL4_SYSTEM_AND_OFFSETS):
                    rhs1 = a1 * sol_left + b1
                    rhs2 = a2 * sol_right + b2
                    if abs(rhs1) > 120 or abs(rhs2) > 120:
                        continue
                    yield {"family": "system_and", "var": var, "op1": ">=" if op1 in {">", ">="} else ">", "op2": "<=" if op2 in {"<", "<="} else "<", "a1": a1, "b1": b1, "rhs1": Fraction(rhs1), "a2": a2, "b2": b2, "rhs2": Fraction(rhs2), "left": sol_left, "right": sol_right}
    # union systems
    for left, right in itertools.product(LEVEL4_SYSTEM_OR_LEFTS, LEVEL4_SYSTEM_OR_RIGHTS):
        for a1, b1 in itertools.product(LEVEL4_SYSTEM_OR_LEFT_COEFFS, LEVEL4_SYSTEM_OR_OFFSETS):
            for a2, b2 in itertools.product(LEVEL4_SYSTEM_OR_RIGHT_COEFFS, LEVEL4_SYSTEM_OR_OFFSETS):
                rhs1 = a1 * left + b1
                rhs2 = a2 * right + b2
                yield {"family": "system_or", "var": var, "a1": a1, "b1": b1, "rhs1": Fraction(rhs1), "a2": a2, "b2": b2, "rhs2": Fraction(rhs2), "left": Fraction(left), "right": Fraction(right)}
    # rational bounds
    for bound in LEVEL4_RATIONAL_BOUNDS:
        for op in OPS:
            for a, b in itertools.product(LEVEL4_RATIONAL_COEFFS, LEVEL4_RATIONAL_OFFSETS):
                rhs = a * bound + b
                yield {"family": "rational_bound", "var": var, "op": op, "a": a, "b": b, "rhs": rhs, "bound": bound}


def iter_level5_specs() -> Iterable[dict]:
    # budgets, age minimum/maximum, rates, mixtures, ticket constraints
    for budget in _int_range(20, 120):
        for cost in [3, 4, 5, 6, 7, 8, 9, 10, 12, 15]:
            yield {"family": "budget", "budget": budget, "cost": cost}
    for current in _int_range(3, 40):
        for years in _int_range(1, 12):
            for target in [18, 21, 65]:
                yield {"family": "age_requirement", "current": current, "years": years, "target": target}
    for speed in _int_range(20, 75):
        for limit in _int_range(30, 240):
            yield {"family": "distance_limit", "speed": speed, "limit": limit}
    for total in _int_range(10, 200):
        for kids, adults in itertools.product([4, 5, 6, 7, 8], [10, 12, 15, 18, 20]):
            if kids >= adults:
                continue
            yield {"family": "ticket_budget", "total": total, "kids": kids, "adults": adults}
    for low in [10, 15, 20, 25, 30]:
        for high in [40, 50, 60, 70, 80]:
            if low >= high:
                continue
            for target in [25, 30, 35, 40, 45, 50, 55, 60]:
                if not (low < target < high):
                    continue
                yield {"family": "mixture_minimum", "low": low, "high": high, "target": target}


def render_spec(spec: dict, level: int) -> tuple[str, str, dict]:
    fam = spec["family"]
    if level == 1:
        return _render_level1(spec)
    if level == 2:
        return _render_level2(spec)
    if level == 3:
        return _render_level3(spec)
    if level == 4:
        return _render_level4(spec)
    return _render_level5(spec)


def _render_level1(spec: dict):
    x = spec["var"]
    op = spec["op"]
    c = spec["c"]
    rhs = spec["rhs"]
    sol = spec["sol"]
    fam = spec["family"]
    if fam == "add":
        problem = f"{x} + {c} {op} {frac_text(rhs)}"
        steps = [f"Subtract {c} from both sides to isolate {x}.", f"This gives {x} {op} {frac_text(sol)}."]
    elif fam == "sub":
        problem = f"{x} - {c} {op} {frac_text(rhs)}"
        steps = [f"Add {c} to both sides.", f"This gives {x} {op} {frac_text(sol)}."]
    elif fam == "mul":
        problem = f"{c}{x} {op} {frac_text(rhs)}"
        new_op = FLIP[op] if c < 0 else op
        move = f"Divide both sides by {c}. Because {c} is negative, reverse the inequality sign." if c < 0 else f"Divide both sides by {c}."
        steps = [move, f"This gives {x} {new_op} {frac_text(sol)}."]
        op = new_op
    else:
        problem = f"{x}/{c} {op} {frac_text(rhs)}"
        new_op = FLIP[op] if c < 0 else op
        move = f"Multiply both sides by {c}. Because {c} is negative, reverse the inequality sign." if c < 0 else f"Multiply both sides by {c}."
        steps = [move, f"This gives {x} {new_op} {frac_text(sol)}."]
        op = new_op
    final = inequality_solution_text(x, op, sol)
    answer = render_by_level(1, steps, final, _interval_for_single(op, sol))
    meta = {"family": fam, "structured": True, "final_answer": final, "interval": _interval_for_single(op, sol)}
    return problem, answer, meta


def _render_level2(spec: dict):
    x = spec["var"]
    op = spec["op"]
    sol = spec["sol"]
    fam = spec["family"]
    if fam == "two_step":
        a, b, rhs = spec["a"], spec["b"], spec["rhs"]
        problem = f"{a}{x} + {b} {op} {frac_text(rhs)}"
        s1 = f"Subtract {b} from both sides: {a}{x} {op} {frac_text(rhs - b)}."
        new_op = FLIP[op] if a < 0 else op
        s2 = f"Divide both sides by {a}." + (" Reverse the inequality sign because the divisor is negative." if a < 0 else "")
        s3 = f"So {x} {new_op} {frac_text(sol)}."
        op = new_op
    elif fam == "distributed":
        a, inner, b, rhs = spec["a"], spec["inner"], spec["b"], spec["rhs"]
        inside = f"{x} + {inner}" if inner >= 0 else f"{x} - {abs(inner)}"
        problem = f"{a}({inside}) + {b} {op} {frac_text(rhs)}"
        expanded_const = a * inner + b
        s1 = f"Distribute {a}: {a}{x} {signed_num(expanded_const)} {op} {frac_text(rhs)}."
        s2 = f"Move the constant term to the right: {a}{x} {op} {frac_text(rhs - expanded_const)}."
        new_op = FLIP[op] if a < 0 else op
        s3 = f"Divide by {a}." + (" Reverse the inequality sign because the divisor is negative." if a < 0 else "")
        s4 = f"So {x} {new_op} {frac_text(sol)}."
        op = new_op
        steps = [s1, s2, s3, s4]
        final = inequality_solution_text(x, op, sol)
        answer = render_by_level(2, steps, final, _interval_for_single(op, sol))
        meta = {"family": fam, "structured": True, "final_answer": final, "interval": _interval_for_single(op, sol)}
        return problem, answer, meta
    else:
        den, b, rhs = spec["den"], spec["b"], spec["rhs"]
        num = f"{x} + {b}" if b >= 0 else f"{x} - {abs(b)}"
        problem = f"({num})/{den} {op} {frac_text(rhs)}"
        new_op = FLIP[op] if den < 0 else op
        s1 = f"Multiply both sides by {den}." + (" Reverse the inequality sign because the multiplier is negative." if den < 0 else "")
        s2 = f"This gives {num} {new_op} {frac_text(sol + b)}."
        s3 = f"Subtract {b}: {x} {new_op} {frac_text(sol)}."
        op = new_op
        steps = [s1, s2, s3]
        final = inequality_solution_text(x, op, sol)
        answer = render_by_level(2, steps, final, _interval_for_single(op, sol))
        meta = {"family": fam, "structured": True, "final_answer": final, "interval": _interval_for_single(op, sol)}
        return problem, answer, meta
    steps = [s1, s2, s3]
    final = inequality_solution_text(x, op, sol)
    answer = render_by_level(2, steps, final, _interval_for_single(op, sol))
    meta = {"family": fam, "structured": True, "final_answer": final, "interval": _interval_for_single(op, sol)}
    return problem, answer, meta


def _render_level3(spec: dict):
    x = spec["var"]
    fam = spec["family"]
    if fam == "both_sides_unique":
        a, b, c, d, op, sol = spec["a"], spec["b"], spec["c"], spec["d"], spec["op"], spec["sol"]
        right_val = (a - c) * sol + b + d
        # ensure c*sol + right constant equals left
        rhs_const = int(a * sol + b - c * sol)
        problem = f"{a}{x} + {b} {op} {c}{x} + {rhs_const}"
        steps = [
            f"Subtract {c}{x} from both sides to collect the variable terms.",
            f"This gives {(a-c)}{x} + {b} {op} {rhs_const}.",
            f"Subtract {b} from both sides, then divide by {a-c}." + (" Reverse the inequality sign if needed because the divisor is negative." if a - c < 0 else ""),
        ]
        result = solve_linear_inequality(a - c, b, op, rhs_const)
        final = inequality_solution_text(x, result["op"], result["bound"])
        return problem, render_by_level(3, steps + [f"So {final}."], final, result["interval"]), {"family": fam, "structured": True, "final_answer": final, "interval": result["interval"]}
    if fam == "both_sides_all":
        a, b, c, d, op = spec["a"], spec["b"], spec["c"], spec["d"], spec["op"]
        problem = f"{a}{x} + {b} {op} {c}{x} + {d}"
        steps = [f"Subtract {c}{x} from both sides and then subtract {b} from both sides.", f"The inequality simplifies to {b} {op} {d}, which is always true."]
        final = "All real numbers"
        return problem, render_by_level(3, steps, final, "(-∞, ∞)"), {"family": fam, "structured": True, "final_answer": final, "interval": "(-∞, ∞)"}
    if fam == "both_sides_none":
        a, b, c, d, op = spec["a"], spec["b"], spec["c"], spec["d"], spec["op"]
        problem = f"{a}{x} + {b} {op} {c}{x} + {d}"
        steps = [f"Subtract {c}{x} from both sides and then subtract {b} from both sides.", f"The inequality simplifies to {b} {op} {d}, which is false."]
        final = "No solution"
        return problem, render_by_level(3, steps, final, "∅"), {"family": fam, "structured": True, "final_answer": final, "interval": "∅"}
    if fam == "compound_and":
        left, right = spec["left"], spec["right"]
        problem = f"{frac_text(left)} < {x} <= {frac_text(right)}"
        steps = ["Read the compound inequality as two conditions that must both be true.", f"The variable must be greater than {frac_text(left)} and at most {frac_text(right)}."]
        final = f"{frac_text(left)} < {x} <= {frac_text(right)}"
        interval = interval_from_bounds(left, False, right, True)
        return problem, render_by_level(3, steps, final, interval), {"family": fam, "structured": True, "final_answer": final, "interval": interval}
    left, right = spec["left"], spec["right"]
    problem = f"{x} <= {frac_text(left)} or {x} > {frac_text(right)}"
    steps = ["Read the compound inequality as two separate regions.", f"The solution is everything at or below {frac_text(left)}, or everything above {frac_text(right)}."]
    final = f"{x} <= {frac_text(left)} or {x} > {frac_text(right)}"
    interval = interval_from_bounds(None, False, left, True) + " ∪ " + interval_from_bounds(right, False, None, False)
    return problem, render_by_level(3, steps, final, interval), {"family": fam, "structured": True, "final_answer": final, "interval": interval}


def _render_level4(spec: dict):
    x = spec["var"]
    fam = spec["family"]
    if fam == "system_and":
        a1, b1, rhs1, a2, b2, rhs2 = spec["a1"], spec["b1"], spec["rhs1"], spec["a2"], spec["b2"], spec["rhs2"]
        op1, op2 = spec["op1"], spec["op2"]
        problem = f"Solve the system of inequalities:\n{a1}{x} + {b1} {op1} {frac_text(rhs1)}\n{a2}{x} + {b2} {op2} {frac_text(rhs2)}"
        s1 = solve_linear_inequality(a1, b1, op1, rhs1)
        s2 = solve_linear_inequality(a2, b2, op2, rhs2)
        left = s1["bound"] if s1["op"] in {">", ">="} else s2["bound"]
        right = s2["bound"] if s2["op"] in {"<", "<="} else s1["bound"]
        left_closed = (s1["op"] == ">=") or (s2["op"] == ">=")
        right_closed = (s1["op"] == "<=") or (s2["op"] == "<=")
        interval = interval_from_bounds(left, left_closed, right, right_closed)
        left_txt = inequality_solution_text(x, s1["op"], s1["bound"])
        right_txt = inequality_solution_text(x, s2["op"], s2["bound"])
        final = combine_and([left_txt, right_txt])
        steps = [
            "Solve each inequality separately.",
            f"The first inequality gives {left_txt}.",
            f"The second inequality gives {right_txt}.",
            "Take the intersection because both conditions must hold at the same time.",
        ]
        return problem, render_by_level(4, steps, final, interval), {"family": fam, "structured": True, "final_answer": final, "interval": interval}
    if fam == "system_or":
        a1, b1, rhs1, a2, b2, rhs2 = spec["a1"], spec["b1"], spec["rhs1"], spec["a2"], spec["b2"], spec["rhs2"]
        problem = f"Solve the compound inequality:\n{a1}{x} + {b1} <= {frac_text(rhs1)} or {a2}{x} + {b2} > {frac_text(rhs2)}"
        s1 = solve_linear_inequality(a1, b1, "<=", rhs1)
        s2 = solve_linear_inequality(a2, b2, ">", rhs2)
        part1 = inequality_solution_text(x, s1["op"], s1["bound"])
        part2 = inequality_solution_text(x, s2["op"], s2["bound"])
        final = combine_or([part1, part2])
        interval = s1["interval"] + " ∪ " + s2["interval"]
        steps = [
            "Solve each inequality separately.",
            f"The first part gives {part1}.",
            f"The second part gives {part2}.",
            "Take the union because either condition may be true.",
        ]
        return problem, render_by_level(4, steps, final, interval), {"family": fam, "structured": True, "final_answer": final, "interval": interval}
    a, b, rhs, op = spec["a"], spec["b"], spec["rhs"], spec["op"]
    problem = f"{a}{x} + {b} {op} {frac_text(rhs)}"
    result = solve_linear_inequality(a, b, op, rhs)
    final = inequality_solution_text(x, result["op"], result["bound"])
    steps = [
        f"Subtract {b} from both sides.",
        f"Then divide by {a}." + (" Reverse the inequality sign because the divisor is negative." if a < 0 else ""),
        f"This gives {final}.",
    ]
    return problem, render_by_level(4, steps, final, result["interval"]), {"family": fam, "structured": True, "final_answer": final, "interval": result["interval"]}


def _render_level5(spec: dict):
    fam = spec["family"]
    if fam == "budget":
        budget, cost = spec["budget"], spec["cost"]
        max_items = budget // cost
        problem = f"Each notebook costs ${cost}. You have at most ${budget}. How many notebooks can you buy? Let n be the number of notebooks."
        steps = [
            f"Set up the inequality {cost}n <= {budget} because the total cost cannot exceed the budget.",
            f"Divide both sides by {cost}: n <= {max_items}.",
            "Since n counts notebooks, use whole numbers only.",
        ]
        final = f"n <= {max_items}, so you can buy at most {max_items} notebooks"
        return problem, render_by_level(5, steps, final, interval_from_bounds(None, False, Fraction(max_items), True)), {"family": fam, "structured": True, "final_answer": final, "interval": interval_from_bounds(None, False, Fraction(max_items), True)}
    if fam == "age_requirement":
        current, years, target = spec["current"], spec["years"], spec["target"]
        need = max(0, target - current)
        problem = f"A person is currently {current} years old. In how many years y will the person be at least {target} years old?"
        steps = [
            f"Write the inequality {current} + y >= {target}.",
            f"Subtract {current} from both sides: y >= {need}.",
            "Because y measures years in the future, y should be a whole number and y >= 0.",
        ]
        final = f"y >= {need}, so the person will be at least {target} in {need} or more years"
        return problem, render_by_level(5, steps, final, interval_from_bounds(Fraction(need), True, None, False)), {"family": fam, "structured": True, "final_answer": final, "interval": interval_from_bounds(Fraction(need), True, None, False)}
    if fam == "distance_limit":
        speed, limit = spec["speed"], spec["limit"]
        bound = Fraction(limit, speed)
        problem = f"A car travels at {speed} miles per hour. For a trip of at most {limit} miles, how many hours h can the trip last?"
        steps = [
            f"Use distance = rate × time, so {speed}h <= {limit}.",
            f"Divide by {speed}: h <= {frac_text(bound)}.",
            "Also h must be nonnegative.",
        ]
        final = f"0 <= h <= {frac_text(bound)}"
        interval = interval_from_bounds(Fraction(0), True, bound, True)
        return problem, render_by_level(5, steps, final, interval), {"family": fam, "structured": True, "final_answer": final, "interval": interval}
    if fam == "ticket_budget":
        total, kids, adults = spec["total"], spec["kids"], spec["adults"]
        bound = Fraction(total - adults, kids - adults)
        # solve kids*x + adults*(1-x)? Let's instead use k adult tickets max with kid tickets remaining.
        max_adults = total // adults
        problem = f"Adult tickets cost ${adults} and child tickets cost ${kids}. You have at most ${total}. If a is the number of adult tickets and you buy no child tickets, what inequality bounds a?"
        steps = [
            f"Use the cost inequality {adults}a <= {total}.",
            f"Divide by {adults}: a <= {max_adults}.",
            "Since a counts tickets, only whole numbers make sense.",
        ]
        final = f"a <= {max_adults}, so you can buy at most {max_adults} adult tickets"
        return problem, render_by_level(5, steps, final, interval_from_bounds(None, False, Fraction(max_adults), True)), {"family": fam, "structured": True, "final_answer": final, "interval": interval_from_bounds(None, False, Fraction(max_adults), True)}
    low, high, target = spec["low"], spec["high"], spec["target"]
    coeff = Fraction(target - low, high - low)
    problem = f"A solution is made by mixing {low}% acid solution with {high}% acid solution. If m cups of the {high}% solution are mixed with 1 cup of the {low}% solution, what inequality on m ensures the final concentration is at least {target}%?"
    # (low + high m)/(1+m) >= target => m >= (target-low)/(high-target)
    bound = Fraction(target - low, high - target)
    steps = [
        f"Set up the concentration inequality ({low} + {high}m)/(1 + m) >= {target}.",
        f"Multiply both sides by 1 + m, which is positive when m >= 0.",
        f"Solve: {low} + {high}m >= {target} + {target}m, so ({high-target})m >= {target-low}.",
        f"Divide by {high-target}: m >= {frac_text(bound)}.",
    ]
    final = f"m >= {frac_text(bound)}"
    return problem, render_by_level(5, steps, final, interval_from_bounds(bound, True, None, False)), {"family": fam, "structured": True, "final_answer": final, "interval": interval_from_bounds(bound, True, None, False)}






