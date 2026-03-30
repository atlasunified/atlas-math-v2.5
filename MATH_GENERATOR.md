# Math Generator Module Specification

## Overview

This document defines the **required interface**, **safety constraints**, and **implementation patterns** for Python math dataset generator modules.

The objective is to ensure every generator is:

- Finite
- Bounded in computational cost
- Deterministic
- Difficulty-cascading
- Safe for large-scale dataset pipelines

---

## Core Objective

Generators must:

1. Produce **finite enumerations**
2. Maintain **bounded generation cost**
3. Support **difficulty-based progression**
4. Avoid **hidden infinite or impractical behavior**

---

## Required Interface

Each module must implement:

```python
generate(count: int = 10, difficulty: str = "level_1", seed=None) -> list[dict]
generate_unique(count: int = 10, difficulty: str = "level_1", offset: int = 0, stride: int = 1, seed=None) -> list[dict]
iter_samples(difficulty: str = "level_1", seed=None)
estimate_capacity(difficulty: str = "level_1")
curriculum() -> dict
```

### Optional Helpers

```python
_level_num(difficulty: str) -> int
_iter_specs(difficulty: str)
iter_level1_specs()
iter_level2_specs()
iter_level3_specs()
iter_level4_specs()
iter_level5_specs()
_sample_from_spec(spec, difficulty, instruction_idx=0) -> dict
```

---

## Determinism

All generators must be:

- Deterministic for a given `(seed, difficulty)`
- Free of hidden randomness outside controlled sampling

---

## Safety Constraints

### 1. Finite Enumeration

Allowed:
- Bounded loops (`for`)
- Fixed ranges
- Predefined lists

Forbidden:
- `while True`
- Unbounded recursion
- Infinite generators
- Probabilistic termination

---

### 2. Operational Boundedness

A generator is invalid if it is:

- Technically finite but practically unbounded
- Based on massive Cartesian products without limits

#### Example (Forbidden)

```python
for a in range(10000):
    for b in range(10000):
        ...
```

---

### 3. No Full Enumeration Requirements

Forbidden:

```python
sum(1 for _ in _iter_specs(...))
```

Capacity estimation must be:

- Constant-time or near-constant
- Based on formula or bounded sampling

---

### 4. Controlled Sampling

All public APIs must:

- Sample from bounded pools
- Avoid unbounded filtering
- Use capped retries

---

## Difficulty System

Levels:

- `level_1`: basic operations
- `level_2`: intermediate reasoning
- `level_3`: multi-step logic
- `level_4`: complex structured reasoning
- `level_5`: advanced / compositional problems

Each level must:

- Build on previous levels
- Increase complexity incrementally
- Remain bounded

---

## Generator Architecture

### Spec → Sample Pattern

```text
spec (finite) → sample → formatted output
```

- Specs define structured problem templates
- Samples convert specs into final dataset entries

---

## Capacity Estimation

Must return:

```python
int
```

Requirements:

- Fast
- Approximate if necessary
- Never requires full iteration

---

## Output Format

Each sample must return:

```python
{
  "instruction": "...",
  "input": "...",
  "answer": "...",
  "difficulty": "level_X"
}
```

---

## Common Pitfalls

Avoid:

- Hidden infinite loops
- Large implicit combinatorics
- Expensive filtering
- Non-deterministic sampling
- Difficulty levels that do not scale properly

---

## Design Philosophy

- Prefer **clarity over cleverness**
- Prefer **boundedness over completeness**
- Prefer **predictability over randomness**

---

## Summary

A valid generator module is:

- Finite
- Deterministic
- Efficient
- Scalable
- Safe for repository-scale dataset construction
