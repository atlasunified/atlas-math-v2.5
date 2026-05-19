from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
from functools import lru_cache
from typing import Iterable


INSTRUCTIONS = [
    "Solve the algebra problem step by step: {problem}",
    "Work through the mathematics carefully: {problem}",
    "Show the reasoning and solve: {problem}",
]


@dataclass(frozen=True)
class ProblemSpec:
    family: str
    prompt: str
    answer: str
    final_answer: str
    skills: tuple[str, ...]
    solution_class: str
    level: int
    canonical_key: str
    metadata: dict


def level_num(difficulty: str | None) -> int:
    if not difficulty:
        return 1
    try:
        return max(1, int(str(difficulty).rsplit("_", 1)[-1]))
    except Exception:
        return 1


def fmt_frac(x: Fraction | int) -> str:
    if isinstance(x, int):
        return str(x)
    if x.denominator == 1:
        return str(x.numerator)
    sign = "-" if x < 0 else ""
    x = abs(x)
    return f"{sign}{x.numerator}/{x.denominator}"


def fmt_num(x: Fraction | int) -> str:
    return fmt_frac(x if isinstance(x, Fraction) else Fraction(x))


def maybe_paren(n: int) -> str:
    return f"({n})" if n < 0 else str(n)


def signed_term(coeff: int, var: str = "x", first: bool = False) -> str:
    if coeff == 0:
        return ""
    sign = "-" if coeff < 0 else "+"
    mag = abs(coeff)
    body = var if mag == 1 else f"{mag}{var}"
    if first:
        return body if coeff > 0 else f"-{body}"
    return f" {sign} {body}"


def signed_const(n: int, first: bool = False) -> str:
    sign = "-" if n < 0 else "+"
    mag = abs(n)
    if first:
        return str(n)
    return f" {sign} {mag}"


def linear_expr(a: int, var: str = "x", b: int = 0) -> str:
    out = signed_term(a, var=var, first=True) if a else "0"
    if b:
        out += signed_const(b, first=False)
    return out


def solve_label(var: str, value: Fraction) -> str:
    return f"{var} = {fmt_frac(value)}"


def emit(out: list[ProblemSpec], seen: set[str], *, family: str, prompt: str, answer: str, final_answer: str,
         skills: tuple[str, ...], solution_class: str, level: int, metadata: dict) -> None:
    key = prompt.strip()
    if key in seen:
        return
    seen.add(key)
    out.append(
        ProblemSpec(
            family=family,
            prompt=prompt,
            answer=answer,
            final_answer=final_answer,
            skills=skills,
            solution_class=solution_class,
            level=level,
            canonical_key=key,
            metadata=metadata,
        )
    )


def l1_answer(var: str, before: str, operation: str, after: str, final_value: Fraction) -> str:
    return "\n".join([
        f"Step 1: {operation}",
        f"{before} \u2192 {after}",
        f"Final answer: {var} = {fmt_frac(final_value)}",
    ])


def l2_answer(steps: list[tuple[str, str]], final: str) -> str:
    lines = []
    for i, (why, state) in enumerate(steps, start=1):
        lines.append(f"Step {i}: {why}")
        lines.append(state)
    lines.append(f"Final answer: {final}")
    return "\n".join(lines)


def l3_answer(strategy: str, steps: list[tuple[str, str]], conclusion: str) -> str:
    lines = [strategy]
    for i, (why, state) in enumerate(steps, start=1):
        lines.append(f"Step {i}: {why}")
        lines.append(state)
    lines.append(f"Final answer: {conclusion}")
    return "\n".join(lines)


def l4_answer(strategy: str, steps: list[tuple[str, str]], conclusion: str) -> str:
    lines = [strategy]
    for i, (why, state) in enumerate(steps, start=1):
        lines.append(f"Step {i}: {why}")
        lines.append(state)
    lines.append(f"Final answer: {conclusion}")
    return "\n".join(lines)


def l5_answer(intro: list[str], steps: list[tuple[str, str]], conclusion: str) -> str:
    lines = list(intro)
    for i, (why, state) in enumerate(steps, start=1):
        lines.append(f"Step {i}: {why}")
        lines.append(state)
    lines.append(f"Final answer: {conclusion}")
    return "\n".join(lines)


# --------------------------- Level 1 ---------------------------------

def _iter_level_1() -> tuple[ProblemSpec, ...]:
    out: list[ProblemSpec] = []
    seen: set[str] = set()
    var = "x"

    for x in range(-20, 21):
        if x == 0:
            continue
        for a in range(-15, 16):
            if a == 0:
                continue
            # x + a = b
            b = x + a
            prompt = f"Solve for {var}: {var} {signed_const(a)} = {b}" if a else f"Solve for {var}: {var} = {b}"
            ans = l1_answer(var, f"{var} {signed_const(a)} = {b}", f"Subtract {a} from both sides.", f"{var} = {x}", Fraction(x))
            emit(out, seen, family="one_step_additive", prompt=prompt, answer=ans, final_answer=solve_label(var, Fraction(x)),
                 skills=("inverse_operations",), solution_class="unique", level=1,
                 metadata={"target_solution": x, "op": "addition"})

        for a in range(-12, 13):
            if a in (0, 1, -1):
                continue
            b = a * x
            prompt = f"Solve for {var}: {a}{var} = {b}"
            ans = l1_answer(var, f"{a}{var} = {b}", f"Divide both sides by {a}.", f"{var} = {x}", Fraction(x))
            emit(out, seen, family="one_step_multiplicative", prompt=prompt, answer=ans,
                 final_answer=solve_label(var, Fraction(x)), skills=("inverse_operations",), solution_class="unique", level=1,
                 metadata={"target_solution": x, "op": "multiplication"})

        for d in range(2, 10):
            if x % d != 0:
                continue
            q = x // d
            prompt = f"Solve for {var}: {var}/{d} = {q}"
            ans = l1_answer(var, f"{var}/{d} = {q}", f"Multiply both sides by {d}.", f"{var} = {x}", Fraction(x))
            emit(out, seen, family="one_step_division", prompt=prompt, answer=ans, final_answer=solve_label(var, Fraction(x)),
                 skills=("inverse_operations",), solution_class="unique", level=1,
                 metadata={"target_solution": x, "op": "division"})

    return tuple(out)


# --------------------------- Level 2 ---------------------------------

def _iter_level_2() -> tuple[ProblemSpec, ...]:
    out: list[ProblemSpec] = []
    seen: set[str] = set()
    var = "x"

    # ax + b = c
    for x in range(-18, 19):
        for a in range(-9, 10):
            if a in (0, 1, -1):
                continue
            for b in range(-15, 16):
                c = a * x + b
                expr = linear_expr(a, var, b)
                steps = [
                    (f"Subtract {b} from both sides.", f"{a}{var} = {c - b}"),
                    (f"Divide both sides by {a}.", f"{var} = {x}"),
                ]
                ans = l2_answer(steps, solve_label(var, Fraction(x)))
                emit(out, seen, family="two_step_linear", prompt=f"Solve for {var}: {expr} = {c}", answer=ans,
                     final_answer=solve_label(var, Fraction(x)), skills=("inverse_operations", "sequencing"),
                     solution_class="unique", level=2,
                     metadata={"target_solution": x, "a": a, "b": b})

    # a(x+b)=c
    for x in range(-15, 16):
        for a in range(-8, 9):
            if a in (0, 1, -1):
                continue
            for b in range(-10, 11):
                c = a * (x + b)
                lhs = f"{a}({var} {signed_const(b).strip()})"
                expanded = f"{a}{var}{signed_const(a*b)} = {c}"
                steps = [
                    (f"Distribute {a}.", expanded),
                    (f"Subtract {a*b} from both sides.", f"{a}{var} = {c - a*b}"),
                    (f"Divide both sides by {a}.", f"{var} = {x}"),
                ]
                ans = l2_answer(steps, solve_label(var, Fraction(x)))
                emit(out, seen, family="distributed_linear", prompt=f"Solve for {var}: {lhs} = {c}", answer=ans,
                     final_answer=solve_label(var, Fraction(x)), skills=("inverse_operations", "distribution", "sequencing"),
                     solution_class="unique", level=2,
                     metadata={"target_solution": x, "a": a, "b": b})

    # (x+b)/d = q gives rational-friendly setup
    for d in range(2, 10):
        for x in range(-18, 19):
            for b in range(-12, 13):
                q = Fraction(x + b, d)
                if abs(q.numerator) > 24:
                    continue
                steps = [
                    (f"Multiply both sides by {d}.", f"{var} {signed_const(b)} = {fmt_frac(Fraction(x+b))}"),
                    (f"Subtract {b} from both sides.", f"{var} = {x}"),
                ]
                ans = l2_answer(steps, solve_label(var, Fraction(x)))
                emit(out, seen, family="fractional_linear", prompt=f"Solve for {var}: ({var} {signed_const(b).strip()})/{d} = {fmt_frac(q)}", answer=ans,
                     final_answer=solve_label(var, Fraction(x)), skills=("inverse_operations", "fractions", "sequencing"),
                     solution_class="unique", level=2,
                     metadata={"target_solution": x, "b": b, "d": d})

    return tuple(out)


# --------------------------- Level 3 ---------------------------------

def _iter_level_3() -> tuple[ProblemSpec, ...]:
    out: list[ProblemSpec] = []
    seen: set[str] = set()
    var = "x"

    # unique solutions: ax+b = cx+d
    for x in range(-20, 21):
        for a in range(-9, 10):
            if a == 0:
                continue
            for c in range(-9, 10):
                if c == 0 or a == c:
                    continue
                for b in range(-12, 13, 2):
                    d = (a - c) * x + b
                    lhs = linear_expr(a, var, b)
                    rhs = linear_expr(c, var, d)
                    steps = [
                        (f"Subtract {c}{var} from both sides.", f"{linear_expr(a-c, var, b)} = {d}"),
                        (f"Subtract {b} from both sides.", f"{a-c}{var} = {d-b}"),
                        (f"Divide both sides by {a-c}.", f"{var} = {x}"),
                    ]
                    ans = l3_answer("Strategy: collect variable terms on one side and constants on the other.", steps, solve_label(var, Fraction(x)))
                    emit(out, seen, family="both_sides_unique", prompt=f"Solve for {var}: {lhs} = {rhs}", answer=ans,
                         final_answer=solve_label(var, Fraction(x)), skills=("inverse_operations", "equivalence", "collect_like_terms"),
                         solution_class="unique", level=3,
                         metadata={"target_solution": x, "a": a, "b": b, "c": c, "d": d})

    # no solution and infinitely many
    for a in range(-8, 9):
        if a == 0:
            continue
        for b in range(-12, 13):
            for d in range(-12, 13):
                if b == d:
                    continue
                lhs = linear_expr(a, var, b)
                rhs = linear_expr(a, var, d)
                steps = [
                    (f"Subtract {a}{var} from both sides.", f"{b} = {d}"),
                    ("The resulting statement is false.", "So the equation has no solution."),
                ]
                ans = l3_answer("Strategy: compare what remains after the variable terms cancel.", steps, "no solution")
                emit(out, seen, family="both_sides_none", prompt=f"Determine the solution set: {lhs} = {rhs}", answer=ans,
                     final_answer="no solution", skills=("equivalence", "solution_classification"), solution_class="none", level=3,
                     metadata={"a": a, "b": b, "d": d})

                rhs2 = linear_expr(a, var, b)
                steps2 = [
                    (f"Subtract {a}{var} from both sides.", f"{b} = {b}"),
                    ("The resulting statement is always true.", "So every real number satisfies the equation."),
                ]
                ans2 = l3_answer("Strategy: compare what remains after the variable terms cancel.", steps2, "infinitely many solutions")
                emit(out, seen, family="both_sides_infinite", prompt=f"Determine the solution set: {lhs} = {rhs2}", answer=ans2,
                     final_answer="infinitely many solutions", skills=("equivalence", "solution_classification"), solution_class="infinite", level=3,
                     metadata={"a": a, "b": b})

    return tuple(out)


# --------------------------- Level 4 ---------------------------------

def _iter_level_4() -> tuple[ProblemSpec, ...]:
    out: list[ProblemSpec] = []
    seen: set[str] = set()

    # substitution-ready unique systems
    for x in range(-12, 13):
        for y in range(-12, 13):
            if x == y:
                continue
            for a in range(-6, 7):
                if a in (0, 1, -1):
                    continue
                for b in range(-8, 9):
                    c = a * x + y
                    d = x - y
                    eq1 = f"{a}x + y = {c}"
                    eq2 = f"x - y = {d}"
                    steps = [
                        ("Use the second equation to write y in terms of x.", f"y = x - {d}"),
                        ("Substitute into the first equation.", f"{a}x + (x - {d}) = {c}"),
                        ("Combine like terms.", f"{a+1}x = {c + d}"),
                        (f"Divide by {a+1}.", f"x = {x}"),
                        ("Substitute back to find y.", f"y = {y}"),
                    ]
                    ans = l4_answer("Strategy: substitution works well because one equation already relates x and y directly.", steps, f"x = {x}, y = {y}")
                    emit(out, seen, family="system_substitution_unique", prompt=f"Solve the system:\n{eq1}\n{eq2}", answer=ans,
                         final_answer=f"x = {x}, y = {y}", skills=("substitution", "equivalence", "systems"), solution_class="unique", level=4,
                         metadata={"x": x, "y": y, "method": "substitution"})

    # elimination with scaling and rational solutions
    for xn in range(-10, 11):
        for xd in (1, 2, 3, 4):
            x = Fraction(xn, xd)
            for yn in range(-10, 11):
                for yd in (1, 2, 3, 4):
                    y = Fraction(yn, yd)
                    if x.denominator == 1 and y.denominator == 1:
                        continue
                    for a1, b1, a2, b2 in [(2, 3, 5, -4), (3, -2, 4, 5), (4, 3, -6, 5), (5, -3, 2, 7)]:
                        c1 = a1 * x + b1 * y
                        c2 = a2 * x + b2 * y
                        eq1 = f"{a1}x {signed_term(b1, 'y')} = {fmt_frac(c1)}"
                        eq2 = f"{a2}x {signed_term(b2, 'y')} = {fmt_frac(c2)}"
                        s1, s2 = abs(a2), abs(a1)
                        new1y = b1 * s1
                        new2y = b2 * s2
                        if new1y + new2y == 0:
                            elim_text = f"Multiply the first equation by {s1} and the second by {s2}, then add."
                            combined_coeff = a1 * s1 + a2 * s2
                            combined_rhs = c1 * s1 + c2 * s2
                            steps = [
                                (elim_text, f"{combined_coeff}x = {fmt_frac(combined_rhs)}"),
                                (f"Divide by {combined_coeff}.", f"x = {fmt_frac(x)}"),
                                ("Substitute back to find y.", f"y = {fmt_frac(y)}"),
                            ]
                            ans = l4_answer("Strategy: eliminate one variable so the system becomes a single linear equation.", steps,
                                            f"x = {fmt_frac(x)}, y = {fmt_frac(y)}")
                            emit(out, seen, family="system_elimination_scaled", prompt=f"Solve the system:\n{eq1}\n{eq2}", answer=ans,
                                 final_answer=f"x = {fmt_frac(x)}, y = {fmt_frac(y)}", skills=("elimination", "systems", "fractions"),
                                 solution_class="unique", level=4, metadata={"x": fmt_frac(x), "y": fmt_frac(y), "method": "elimination"})


    # mixed-form substitution systems y = mx + b and ax + cy = d
    for x in range(-15, 16):
        for y in range(-15, 16):
            for m in (-4, -3, -2, -1, 1, 2, 3, 4):
                b = y - m * x
                if abs(b) > 20:
                    continue
                for a, c in [(2, 3), (3, -2), (4, 5), (-5, 4), (6, -3)]:
                    d = a * x + c * y
                    eq1 = f"y = {m}x{signed_const(b)}" if b else f"y = {m}x"
                    eq2 = f"{a}x {signed_term(c, 'y')} = {d}"
                    coeff = a + c * m
                    if coeff == 0:
                        continue
                    rhs = d - c * b
                    steps = [
                        ("Substitute the expression for y into the second equation.", f"{a}x {signed_const(c*b)} = {d}" if c*m == 0 else f"{coeff}x {signed_const(c*b)} = {d}"),
                        ("Move the constant term to the other side.", f"{coeff}x = {rhs}"),
                        (f"Divide by {coeff}.", f"x = {x}"),
                        ("Substitute back into y = mx + b.", f"y = {y}"),
                    ]
                    ans = l4_answer("Strategy: substitution is natural because one variable is already isolated.", steps, f"x = {x}, y = {y}")
                    emit(out, seen, family="system_substitution_isolated", prompt=f"Solve the system:\n{eq1}\n{eq2}", answer=ans,
                         final_answer=f"x = {x}, y = {y}", skills=("substitution", "systems", "rearrangement"), solution_class="unique", level=4,
                         metadata={"x": x, "y": y, "method": "substitution"})

    # integer elimination families with nontrivial scaling
    for x in range(-15, 16):
        for y in range(-15, 16):
            for a1, b1, a2, b2 in [(2, 5, 3, -4), (3, 4, 5, -2), (4, -3, 6, 5), (5, 2, 7, -3), (6, 5, 4, -7)]:
                c1 = a1 * x + b1 * y
                c2 = a2 * x + b2 * y
                l1, l2 = abs(a2), abs(a1)
                coeff_y = b1 * l1 + b2 * l2
                if coeff_y == 0:
                    continue
                coeff_x = a1 * l1 + a2 * l2
                if coeff_x == 0:
                    continue
                eq1 = f"{a1}x {signed_term(b1, 'y')} = {c1}"
                eq2 = f"{a2}x {signed_term(b2, 'y')} = {c2}"
                steps = [
                    (f"Multiply the first equation by {l1} and the second by {l2}.", f"{coeff_x}x {signed_term(coeff_y, 'y')} = {c1*l1 + c2*l2}"),
                    ("Solve the resulting equation for one variable, then substitute back.", f"x = {x}, y = {y}"),
                ]
                ans = l4_answer("Strategy: scale the equations so elimination creates a simpler single-variable equation.", steps, f"x = {x}, y = {y}")
                emit(out, seen, family="system_elimination_integer_scaled", prompt=f"Solve the system:\n{eq1}\n{eq2}", answer=ans,
                     final_answer=f"x = {x}, y = {y}", skills=("elimination", "systems"), solution_class="unique", level=4,
                     metadata={"x": x, "y": y, "method": "elimination"})

    # inconsistent and dependent systems
    for a, b in [(2, 3), (3, -4), (5, 2), (-4, 5)]:
        for x in range(-6, 7):
            for y in range(-6, 7):
                c = a * x + b * y
                k = 2
                eq1 = f"{a}x {signed_term(b, 'y')} = {c}"
                eq2_dep = f"{k*a}x {signed_term(k*b, 'y')} = {k*c}"
                steps_dep = [
                    ("Multiply the first equation by 2.", f"{k*a}x {signed_term(k*b, 'y')} = {k*c}"),
                    ("The scaled equation matches the second equation exactly.", "So the system represents the same line twice."),
                ]
                ans_dep = l4_answer("Strategy: compare the equations structurally before solving.", steps_dep, "infinitely many solutions")
                emit(out, seen, family="system_dependent", prompt=f"Determine the solution set of the system:\n{eq1}\n{eq2_dep}", answer=ans_dep,
                     final_answer="infinitely many solutions", skills=("systems", "solution_classification"), solution_class="infinite", level=4,
                     metadata={"method": "classification"})

                eq2_inc = f"{k*a}x {signed_term(k*b, 'y')} = {k*c + 1}"
                steps_inc = [
                    ("Multiply the first equation by 2.", f"{k*a}x {signed_term(k*b, 'y')} = {k*c}"),
                    ("Now compare with the second equation.", f"{k*c} \u2260 {k*c + 1}, so the lines are parallel and distinct."),
                ]
                ans_inc = l4_answer("Strategy: compare the equations structurally before solving.", steps_inc, "no solution")
                emit(out, seen, family="system_inconsistent", prompt=f"Determine the solution set of the system:\n{eq1}\n{eq2_inc}", answer=ans_inc,
                     final_answer="no solution", skills=("systems", "solution_classification"), solution_class="none", level=4,
                     metadata={"method": "classification"})

    return tuple(out)


# --------------------------- Level 5 ---------------------------------

def _iter_level_5() -> tuple[ProblemSpec, ...]:
    out: list[ProblemSpec] = []
    seen: set[str] = set()

    # Age problems with fractional ratios and offsets
    for child in range(4, 31):
        for gap in range(12, 41, 2):
            parent = child + gap
            for years in range(1, 11):
                for ratio in [Fraction(2, 1), Fraction(3, 1), Fraction(5, 2), Fraction(7, 3)]:
                    if parent + years != ratio * (child + years):
                        continue
                    prompt = (
                        f"A parent is {gap} years older than a child. In {years} years, the parent's age will be "
                        f"{fmt_frac(ratio)} times the child's age. How old is the child now?"
                    )
                    intro = [
                        "Let x be the child's current age.",
                        f"Then the parent's current age is x + {gap}.",
                        f"In {years} years, their ages will be x + {years} and x + {gap + years}.",
                        f"Set up the equation: x + {gap + years} = {fmt_frac(ratio)}(x + {years})",
                    ]
                    coeff = Fraction(1) - ratio
                    rhs = ratio * years - (gap + years)
                    steps = [
                        (f"Distribute {fmt_frac(ratio)} and collect x-terms.", f"{fmt_frac(coeff)}x = {fmt_frac(rhs)}"),
                        (f"Divide by {fmt_frac(coeff)}.", f"x = {child}"),
                    ]
                    conclusion = f"The child is {child} years old."
                    ans = l5_answer(intro, steps, conclusion)
                    emit(out, seen, family="age_ratio_model", prompt=prompt, answer=ans, final_answer=conclusion,
                         skills=("modeling", "linear_equation", "fractions"), solution_class="unique", level=5,
                         metadata={"child": child, "parent": parent, "ratio": fmt_frac(ratio)})

    # Consecutive integers
    for n in range(-40, 60):
        for k in range(2, 6):
            total = sum(n + i for i in range(k))
            prompt = f"The sum of {k} consecutive integers is {total}. Find the integers."
            intro = [
                "Let x be the smallest integer.",
                "Then the integers are " + ", ".join(f"x + {i}" if i else "x" for i in range(k)) + ".",
                f"Set up the equation: {' + '.join('x' if i == 0 else f'(x + {i})' for i in range(k))} = {total}",
            ]
            lhs_coeff = k
            lhs_const = k * (k - 1) // 2
            steps = [
                ("Combine like terms.", f"{lhs_coeff}x + {lhs_const} = {total}"),
                (f"Subtract {lhs_const}.", f"{lhs_coeff}x = {total - lhs_const}"),
                (f"Divide by {lhs_coeff}.", f"x = {n}"),
            ]
            nums = [n + i for i in range(k)]
            conclusion = "The integers are " + ", ".join(str(v) for v in nums) + "."
            ans = l5_answer(intro, steps, conclusion)
            emit(out, seen, family="consecutive_integers_model", prompt=prompt, answer=ans, final_answer=conclusion,
                 skills=("modeling", "sequencing"), solution_class="unique", level=5,
                 metadata={"start": n, "count": k})

    # Ticket sales systems with integer solutions
    for adult in range(5, 81):
        for student in range(5, 81):
            for pa, ps in [(12, 7), (15, 9), (18, 11), (20, 13)]:
                total_tickets = adult + student
                revenue = pa * adult + ps * student
                prompt = (
                    f"At a school event, adult tickets cost ${pa} and student tickets cost ${ps}. "
                    f"A total of {total_tickets} tickets were sold for ${revenue}. How many adult tickets were sold?"
                )
                intro = [
                    "Let a be the number of adult tickets and s be the number of student tickets.",
                    f"The ticket count gives a + s = {total_tickets}.",
                    f"The revenue equation gives {pa}a + {ps}s = {revenue}.",
                ]
                steps = [
                    ("Use the count equation to write s in terms of a.", f"s = {total_tickets} - a"),
                    ("Substitute into the revenue equation.", f"{pa}a + {ps}({total_tickets} - a) = {revenue}"),
                    ("Simplify.", f"{pa-ps}a = {revenue - ps*total_tickets}"),
                    (f"Divide by {pa-ps}.", f"a = {adult}"),
                ]
                conclusion = f"{adult} adult tickets were sold."
                ans = l5_answer(intro, steps, conclusion)
                emit(out, seen, family="ticket_sales_system", prompt=prompt, answer=ans, final_answer=conclusion,
                     skills=("modeling", "systems", "substitution"), solution_class="unique", level=5,
                     metadata={"adult": adult, "student": student, "adult_price": pa, "student_price": ps})

    # Mixture problems with rational concentration answers
    for total in range(20, 101, 5):
        for acid in [Fraction(1, 10), Fraction(1, 5), Fraction(1, 4), Fraction(3, 10), Fraction(2, 5)]:
            for water in [Fraction(0), Fraction(1, 20), Fraction(1, 10)]:
                if acid <= water:
                    continue
                for x in range(2, total-1):
                    final = (acid * x + water * (total - x)) / total
                    if final.denominator not in (1, 2, 4, 5, 10, 20):
                        continue
                    prompt = (
                        f"A chemist mixes a {fmt_frac(acid*100)}% solution with a {fmt_frac(water*100)}% solution to make {total} liters of a "
                        f"{fmt_frac(final*100)}% solution. How many liters of the {fmt_frac(acid*100)}% solution are used?"
                    )
                    intro = [
                        f"Let x be the liters of {fmt_frac(acid*100)}% solution.",
                        f"Then {total} - x liters must come from the {fmt_frac(water*100)}% solution.",
                        f"Set up the concentration equation: {fmt_frac(acid)}x + {fmt_frac(water)}({total} - x) = {fmt_frac(final*total)}",
                    ]
                    left_coeff = acid - water
                    rhs = final * total - water * total
                    steps = [
                        ("Distribute and combine like terms.", f"{fmt_frac(left_coeff)}x = {fmt_frac(rhs)}"),
                        (f"Divide by {fmt_frac(left_coeff)}.", f"x = {x}"),
                    ]
                    conclusion = f"{x} liters of the {fmt_frac(acid*100)}% solution are used."
                    ans = l5_answer(intro, steps, conclusion)
                    emit(out, seen, family="mixture_model", prompt=prompt, answer=ans, final_answer=conclusion,
                         skills=("modeling", "fractions", "linear_equation"), solution_class="unique", level=5,
                         metadata={"strong_pct": fmt_frac(acid*100), "weak_pct": fmt_frac(water*100), "result_pct": fmt_frac(final*100), "liters": x})

    # Number relation systems with rational answers
    for small in range(-20, 31):
        for diff in range(2, 19):
            large = small + diff
            for ratio in [Fraction(3, 2), Fraction(4, 3), Fraction(5, 4), Fraction(7, 5)]:
                total = small + large
                prompt = (
                    f"Two numbers differ by {diff} and add to {total}. Find the larger number, then verify whether it is "
                    f"{fmt_frac(ratio)} times the smaller after adding {diff} to the smaller."
                )
                intro = [
                    "Let s be the smaller number and l be the larger number.",
                    f"Then l - s = {diff} and l + s = {total}.",
                ]
                steps = [
                    ("Add the two equations to eliminate s.", f"2l = {total + diff}"),
                    ("Divide by 2.", f"l = {large}"),
                    ("Find the smaller number.", f"s = {small}"),
                    ("Check the extra relation.", f"l/(s + {diff}) = {fmt_frac(Fraction(large, small + diff)) if small + diff != 0 else 'undefined'}"),
                ]
                conclusion = f"The larger number is {large}."
                ans = l5_answer(intro, steps, conclusion)
                emit(out, seen, family="number_system_model", prompt=prompt, answer=ans, final_answer=conclusion,
                     skills=("modeling", "systems", "verification"), solution_class="unique", level=5,
                     metadata={"small": small, "large": large, "diff": diff})

    return tuple(out)


@lru_cache(maxsize=None)
def specs_for_level(level: int) -> tuple[ProblemSpec, ...]:
    if level <= 1:
        return _iter_level_1()
    if level == 2:
        return _iter_level_2()
    if level == 3:
        return _iter_level_3()
    if level == 4:
        return _iter_level_4()
    return _iter_level_5()


@lru_cache(maxsize=None)
def specs_for_difficulty(difficulty: str) -> tuple[ProblemSpec, ...]:
    return specs_for_level(level_num(difficulty))


def metadata_for_spec(spec: ProblemSpec) -> dict:
    data = dict(spec.metadata)
    data.update({
        "family": spec.family,
        "solution_class": spec.solution_class,
        "skills": list(spec.skills),
        "final_answer": spec.final_answer,
        "structured": True,
        "canonical_key": spec.canonical_key,
        "level": spec.level,
    })
    return data






