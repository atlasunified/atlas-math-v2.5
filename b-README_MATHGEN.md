# Math Generator Module Guide

This document defines the **recommended module contract** for Atlas Math 2.5 generators.

It is aligned to the current repository codebase, including:

- CLI-driven dataset building
- structured and random generation paths
- repository export and repository rebuild workflows
- post-hoc identity fields and split-grouping
- the `make_sample()` record shape used across modules

This guide is intended for contributors writing new generator modules or upgrading older ones.

---

## What the runtime expects

Atlas Math currently supports two broad generator styles:

1. **Structured generators**
   - finite, enumerable, deterministic
   - typically expose `generate_unique()`, `iter_samples()`, and `estimate_capacity()`

2. **Random-only generators**
   - stochastic sampling through `generate()`
   - may not support exact structured export

For new modules, the preferred standard is **structured + bounded + repository-safe**.

---

## Required exports

A production-ready structured module should export:

```python
generate(count: int = 10, difficulty: str = "level_1", seed=None) -> list[dict]
generate_unique(
    count: int = 10,
    difficulty: str = "level_1",
    offset: int = 0,
    stride: int = 1,
    seed=None,
) -> list[dict]
iter_samples(difficulty: str = "level_1", seed=None)
estimate_capacity(difficulty: str = "level_1")
curriculum() -> dict
```

Common optional helpers:

```python
_level_num(difficulty: str) -> int
_take(iterable, n)
_iter_specs(difficulty: str)
iter_level1_specs()
iter_level2_specs()
iter_level3_specs()
iter_level4_specs()
iter_level5_specs()
_sample_from_spec(spec, difficulty, instruction_idx=0) -> dict
```

### Optional repository-aware exports

These are not required for every module, but they are useful when a generator needs tighter control over repository export:

```python
iter_repository_cases(difficulty: str = "level_1")
repository_spec(difficulty: str = "level_1") -> dict
```

If these are not implemented, the repository system can often fall back to structured generation when capacity is known.

---

## Required module metadata

Each module should define `MODULE_INFO` in this shape:

```python
MODULE_INFO = {
    "module_id": "algebra.linears.example_module",
    "name": "Example Module",
    "topic": "algebra",
    "subtopic": "linears",
    "difficulty_levels": ["level_1", "level_2", "level_3", "level_4", "level_5"],
    "enabled": True,
}
```

### Notes

- `module_id`, `topic`, `subtopic`, and `difficulty_levels` are used by the registry and CLI.
- `difficulty_levels` should match what the module actually supports.
- New modules should include all supported levels explicitly.

---

## Output record shape

Most Atlas Math modules build records through:

```python
from atlas_math.modules.shared.common import make_sample
```

`make_sample()` returns records with at least these fields:

```python
{
    "module_id": "...",
    "topic": "...",
    "subtopic": "...",
    "difficulty": "level_3",
    "difficulty_level": "level_3",
    "instruction": "...",
    "input": "...",
    "output": "...",
    "output_words": "...",
    "answer": "...",
    "answer_words": "...",
    "metadata": {...},
}
```

### Recommendation

Use `make_sample()` unless you have a strong reason not to. It keeps module output consistent with:

- CLI serialization
- dataset building
- repository export
- downstream validation and deduplication

---

## Identity and repository fields

Repository and split-safe workflows derive identity fields from each record, either directly or from `metadata`.

These fields are important:

- `canonical_key`
- `case_id`
- `family_id`
- `template_id`
- `sample_id`
- `split_group_key`

The helper `attach_identity_fields()` will populate missing values from the record or from `metadata`, but **new modules should provide stable identity information whenever possible**, especially for structured tasks.

### Recommended metadata pattern

```python
metadata = {
    "family": "two_step_linear",
    "canonical_key": "two_step_linear:a=2:b=3:x=5",
    "case_id": "two_step_linear:a=2:b=3:x=5",
    "family_id": "two_step_linear",
    "template_id": "two_step_linear",
}
```

### Why this matters

These fields improve:

- canonical deduplication
- repository rebuild quality
- grouped dataset splitting
- leakage auditing
- stable benchmarking

---

## Core design requirements

A new structured module should satisfy all of the following.

### 1. Enumeration must be finite

Forbidden:

- `while True`
- open-ended search loops
- probabilistic termination
- unbounded recursion
- rejection loops without a hard attempt cap

Allowed:

- bounded `for` loops
- finite ranges
- bounded products
- capped iterators

### 2. Finite must also mean operationally bounded

A generator is not acceptable if it is mathematically finite but operationally huge.

Avoid:

- giant Cartesian products
- spec spaces that only terminate after traversing millions of combinations
- designs that become unusable during repository export or offset-based structured access

### 3. Difficulty progression must be cascading

Difficulty levels should feel like a coherent progression:

- `level_1`: simplest valid cases
- `level_2`: one additional complication
- `level_3`: more structure or multi-step reasoning
- `level_4`: composition, branching, or deeper reasoning
- `level_5`: hardest bounded variants

Levels should extend a common task family rather than switching to unrelated tasks.

### 4. Generation must be deterministic

For a fixed combination of:

- `seed`
- `difficulty`
- bounded candidate pool
- selection logic

the module should produce stable results.

This is especially important for repository export and reproducible builds.

---

## Recommended implementation standard

The current repository contains a mix of older and newer patterns. For new work, use the stricter pattern below.

### Hard per-level caps

Define explicit caps:

```python
LEVEL_SPEC_CAPS = {
    "level_1": 2000,
    "level_2": 3000,
    "level_3": 4000,
    "level_4": 5000,
    "level_5": 5000,
}
```

These values can vary by module, but every difficulty should have a hard upper bound.

### Optional per-family caps

If a difficulty contains multiple construction families, cap them independently:

```python
FAMILY_CAPS = {
    "level_1": {"basic": 2000},
    "level_2": {"basic": 1500, "variant": 1500},
    "level_3": {"family_a": 1500, "family_b": 1500, "family_c": 1000},
    "level_4": {"family_a": 2000, "family_b": 1500, "family_c": 1500},
    "level_5": {"family_a": 2000, "family_b": 1500, "family_c": 1500},
}
```

### Capped iterator helper

```python
def _take(iterable, n):
    for i, item in enumerate(iterable):
        if i >= n:
            break
        yield item
```

### Bounded `_iter_specs()`

```python
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
```

This pattern is already used by some of the repository's stronger structured modules.

---

## Capacity reporting

Atlas Math accepts both plain integer capacities and structured descriptors. The runtime will normalize either form.

### Best practice

Return a descriptor:

```python
CAPACITY_HINTS = {
    "level_1": {"value": 2000, "quality": "capped"},
    "level_2": {"value": 3000, "quality": "capped"},
    "level_3": {"value": 4000, "quality": "capped"},
    "level_4": {"value": 5000, "quality": "capped"},
    "level_5": {"value": 5000, "quality": "capped"},
}

def estimate_capacity(difficulty: str = "level_1"):
    return CAPACITY_HINTS.get(difficulty, {"value": None, "quality": "unknown"})
```

### Allowed `quality` values in practice

The generation and repository code handle values like:

- `exact`
- `estimated`
- `capped`
- `lower_bound`
- `unknown`

### Important rule

Do **not** compute exact capacity by traversing a large iterator.

Forbidden for large spaces:

```python
sum(1 for _ in _iter_specs(difficulty))
```

Use:

- a cap
- a formula
- a bounded estimate
- or `unknown`

### Repository compatibility note

The repository export path can iterate structured modules directly when capacity is exact and finite. That is useful, but new modules should still prioritize boundedness over exhaustive exactness.

---

## `generate()` standard

`generate()` should sample from a bounded pool only.

Recommended pattern:

```python
import itertools
import random

MAX_SPEC_PREFIX = 5000
MAX_GENERATE_MULTIPLIER = 8

def generate(count: int = 10, difficulty: str = "level_1", seed=None):
    if count <= 0:
        return []
    rng = random.Random(seed)
    prefix = min(max(count * MAX_GENERATE_MULTIPLIER, 256), MAX_SPEC_PREFIX)
    pool = list(itertools.islice(_iter_specs(difficulty), 0, prefix))
    if not pool:
        return []

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
```

### Why

This keeps generation:

- bounded
- deterministic
- deduplicated
- insensitive to huge underlying spec streams

---

## `generate_unique()` standard

`generate_unique()` should use a bounded pool plus deterministic shuffling.

Recommended pattern:

```python
def generate_unique(
    count: int = 10,
    difficulty: str = "level_1",
    offset: int = 0,
    stride: int = 1,
    seed=None,
):
    if count <= 0:
        return []

    stride = max(1, int(stride or 1))
    offset = max(0, int(offset or 0))

    pool = list(_iter_specs(difficulty))
    if not pool:
        return []

    rng = random.Random((seed, difficulty, offset, stride, count))
    indexed_pool = list(enumerate(pool))
    rng.shuffle(indexed_pool)

    start = offset % len(indexed_pool)
    ordered = indexed_pool[start::stride] + indexed_pool[:start:stride]

    out = []
    seen = set()
    for idx, spec in ordered:
        sample = _sample_from_spec(spec, difficulty, instruction_idx=idx + offset)
        key = sample.get("input", "")
        if key in seen:
            continue
        seen.add(key)
        out.append(sample)
        if len(out) >= count:
            break
    return out
```

### Strong recommendation

Do **not** implement `generate_unique()` by replaying a huge iterator from zero to `offset`.

Avoid this for large spaces:

```python
itertools.islice(_iter_specs(difficulty), offset, None, stride)
```

### Why this matters

The current repository still contains some older modules that use deep-offset slicing over exact structured spaces. That path is tolerated by the runtime, but it is **not the preferred pattern for new modules** because performance degrades as offsets grow.

---

## `iter_samples()` standard

`iter_samples()` should be explicitly finite.

Recommended pattern:

```python
def iter_samples(difficulty: str = "level_1", seed=None):
    max_items = LEVEL_SPEC_CAPS.get(difficulty, 2000)
    rng = random.Random((seed, difficulty, "iter_samples"))
    pool = list(_iter_specs(difficulty))
    rng.shuffle(pool)

    seen = set()
    for idx, spec in enumerate(pool[:max_items]):
        sample = _sample_from_spec(spec, difficulty, instruction_idx=idx)
        key = sample.get("input", "")
        if key in seen:
            continue
        seen.add(key)
        yield sample
```

### Rule

`iter_samples()` must terminate naturally after a bounded number of outputs.

---

## Search-space design rules

When building spec families:

- use small bounded integer ranges
- use small bounded coefficient sets
- use bounded operator sets
- use bounded structural variants
- prefer representative subsets over brute-force exhaustiveness

Avoid nested products that multiply into impractical search spaces.

### Prefer

- curated finite lists
- small products with hard caps
- per-family budgets

### Avoid

- combinatorial explosions hidden behind “finite”
- deep filtering over huge candidate spaces
- large rejection-based generators

---

## Curriculum contract

Every module should implement:

```python
def curriculum():
    return {
        "level_1": ["simple single-step cases"],
        "level_2": ["adds one new complication"],
        "level_3": ["adds more structure or multiple constraints"],
        "level_4": ["adds composition or branching"],
        "level_5": ["adds hardest bounded variants"],
    }
```

This function is primarily descriptive, but it helps contributors and reviewers check that the difficulty ladder is coherent.

---

## Repository-aware guidance

If a module is intended to be repository-friendly, it should do more than merely emit valid samples.

### Good repository behavior includes

- stable `canonical_key`
- stable `case_id`
- stable `family_id`
- deterministic rendering
- bounded structured access
- cheap capacity reporting

### Optional advanced support

If the module can cleanly expose repository cases directly, implement:

```python
iter_repository_cases(difficulty: str = "level_1")
repository_spec(difficulty: str = "level_1") -> dict
```

These are useful for:

- manifest generation
- repository introspection
- stable rebuilds
- preserving richer case-level metadata

---

## Example skeleton

```python
from __future__ import annotations

import itertools
import random

from atlas_math.modules.shared.common import make_sample

MODULE_INFO = {
    "module_id": "algebra.linears.example_module",
    "name": "Example Module",
    "topic": "algebra",
    "subtopic": "linears",
    "difficulty_levels": ["level_1", "level_2", "level_3", "level_4", "level_5"],
    "enabled": True,
}

LEVEL_SPEC_CAPS = {
    "level_1": 2000,
    "level_2": 3000,
    "level_3": 4000,
    "level_4": 5000,
    "level_5": 5000,
}

CAPACITY_HINTS = {
    level: {"value": cap, "quality": "capped"}
    for level, cap in LEVEL_SPEC_CAPS.items()
}

INSTRUCTIONS = [
    "Solve the problem: {problem}",
    "Work through the problem step by step: {problem}",
]

def _level_num(difficulty: str) -> int:
    try:
        n = int(str(difficulty).rsplit("_", 1)[-1])
    except Exception:
        n = 1
    return max(1, min(5, n))

def _take(iterable, n):
    for i, item in enumerate(iterable):
        if i >= n:
            break
        yield item

def iter_level1_specs():
    for a in range(1, 11):
        yield {"family": "basic", "a": a}

def iter_level2_specs():
    for spec in iter_level1_specs():
        yield {**spec, "variant": "level_2"}

def iter_level3_specs():
    for spec in iter_level2_specs():
        yield {**spec, "variant": "level_3"}

def iter_level4_specs():
    for spec in iter_level3_specs():
        yield {**spec, "variant": "level_4"}

def iter_level5_specs():
    for spec in iter_level4_specs():
        yield {**spec, "variant": "level_5"}

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

def _sample_from_spec(spec: dict, difficulty: str, instruction_idx: int = 0):
    problem = f"x + {spec['a']} = 10"
    answer = str(10 - spec["a"])
    metadata = {
        "family": spec.get("family", "basic"),
        "canonical_key": f"x+{spec['a']}=10",
        "case_id": f"x+{spec['a']}=10",
        "family_id": spec.get("family", "basic"),
        "template_id": spec.get("family", "basic"),
        "structured": True,
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

def generate_unique(count: int = 10, difficulty: str = "level_1", offset: int = 0, stride: int = 1, seed=None):
    if count <= 0:
        return []
    stride = max(1, int(stride or 1))
    offset = max(0, int(offset or 0))
    pool = list(_iter_specs(difficulty))
    if not pool:
        return []
    rng = random.Random((seed, difficulty, offset, stride, count))
    indexed_pool = list(enumerate(pool))
    rng.shuffle(indexed_pool)
    start = offset % len(indexed_pool)
    ordered = indexed_pool[start::stride] + indexed_pool[:start:stride]

    out = []
    seen = set()
    for idx, spec in ordered:
        sample = _sample_from_spec(spec, difficulty, instruction_idx=idx + offset)
        key = sample.get("input", "")
        if key in seen:
            continue
        seen.add(key)
        out.append(sample)
        if len(out) >= count:
            break
    return out

def generate(count: int = 10, difficulty: str = "level_1", seed=None):
    if count <= 0:
        return []
    rng = random.Random(seed)
    prefix = min(max(count * 8, 256), 5000)
    pool = list(itertools.islice(_iter_specs(difficulty), 0, prefix))
    if not pool:
        return []

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

def iter_samples(difficulty: str = "level_1", seed=None):
    pool = list(_iter_specs(difficulty))
    rng = random.Random((seed, difficulty, "iter_samples"))
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
    return CAPACITY_HINTS.get(difficulty, {"value": None, "quality": "unknown"})

def curriculum():
    return {
        "level_1": ["basic single-step equations"],
        "level_2": ["adds one extra complication"],
        "level_3": ["adds multi-step structure"],
        "level_4": ["adds composition or branching"],
        "level_5": ["adds hardest bounded variants"],
    }
```

---

## Review checklist

Before merging a new module, verify:

- [ ] `MODULE_INFO` is present and accurate
- [ ] supported difficulties are explicit
- [ ] enumeration is finite
- [ ] every difficulty has a hard cap
- [ ] large families have their own caps when needed
- [ ] `generate()` samples from a bounded pool
- [ ] `generate_unique()` does not degrade with large offsets
- [ ] `iter_samples()` is explicitly finite
- [ ] `estimate_capacity()` is cheap
- [ ] output records match the repository's sample shape
- [ ] metadata includes stable identity fields where possible
- [ ] difficulty progression is coherent
- [ ] the module imports cleanly

---

## Practical caveat

The current Atlas Math repository includes some older structured modules that still use exact-capacity and offset-slicing patterns. Those work with the current runtime, but they are not the preferred standard for new modules.

For Atlas Math 2.5, the recommended contributor standard is:

- bounded
- deterministic
- repository-safe
- identity-aware
- split-safe

That is the standard this document is intended to enforce.

---

## Summary

A strong Atlas Math 2.5 generator module should be:

- finite
- cheap to enumerate
- deterministic
- curriculum-structured
- dedupe-friendly
- repository-aware
- compatible with `make_sample()`
- safe for large-scale dataset and repository workflows
