You are writing a Python dataset generator module.

Your output must be a SINGLE self-contained Python module that follows the rules below exactly.

The purpose of this prompt is to force:
1. finite enumeration,
2. bounded generation cost,
3. cascading / level-based construction,
4. no hidden infinite or practically-unbounded behavior.

The module must be production-safe for dataset building.

==================================================
CORE REQUIREMENTS
==================================================

The module must implement a difficulty-cascading generator with these exported functions:

- generate(count: int = 10, difficulty: str = "level_1", seed=None) -> list[dict]
- generate_unique(count: int = 10, difficulty: str = "level_1", offset: int = 0, stride: int = 1, seed=None) -> list[dict]
- iter_samples(difficulty: str = "level_1", seed=None)
- estimate_capacity(difficulty: str = "level_1")
- curriculum() -> dict

If helpful, also implement:
- _level_num(difficulty: str) -> int
- _iter_specs(difficulty: str)
- iter_level1_specs(), iter_level2_specs(), ...
- _sample_from_spec(spec, difficulty, instruction_idx=0) -> dict

The module must be deterministic for a given seed and difficulty.

==================================================
NON-NEGOTIABLE SAFETY RULES
==================================================

1. ALL ENUMERATION MUST BE FINITE
- No `while True` in spec enumeration.
- No open-ended search loops.
- No rejection loops without a hard attempt cap.
- Every iterator must terminate naturally from bounded ranges / bounded lists / bounded products.

2. FINITE MUST ALSO MEAN OPERATIONALLY BOUNDED
A generator is NOT acceptable if it is only mathematically finite but effectively enormous.
Do NOT create huge Cartesian products that can explode into millions of specs unless they are immediately capped.

3. NEVER REQUIRE FULL ENUMERATION TO FUNCTION
Forbidden patterns:
- `sum(1 for _ in _iter_specs(...))` for large spaces
- exact capacity by exhaustively traversing a giant iterator
- deep skipping into a giant generator with `islice(..., offset, None, stride)` when offset can grow large

4. EACH DIFFICULTY MUST HAVE A HARD SPEC CAP
Define explicit per-difficulty limits such as:
- level_1: 2000
- level_2: 3000
- level_3: 4000
- level_4: 5000
- level_5: 5000

These can be adjusted by the module, but every level must have a hard maximum emitted spec count.

5. EACH SUBFAMILY MUST HAVE A HARD BUDGET
If a difficulty contains multiple construction families, each family must have its own cap so one family cannot dominate or explode.

6. NO DEEP OFFSET REPLAY
`generate_unique()` must NOT work by replaying the whole spec stream from zero to `offset`.
Instead, use a bounded candidate pool and deterministic shuffling keyed by seed/difficulty/offset/stride.

7. CAPACITY MUST BE CHEAP
`estimate_capacity()` must return:
- a capped value,
- or an estimate,
- or a lower bound,
- or unknown,
but must never require expensive full traversal.

==================================================
CASCADING DIFFICULTY REQUIREMENTS
==================================================

The module must follow a cascading design:

- `level_1` = simplest valid instances
- `level_2` = all patterns from level_1 plus one added complication
- `level_3` = level_2 plus additional structure
- `level_4` = more composition / branching / multi-step reasoning
- `level_5` = hardest but still bounded and finite

The levels must feel progressive and related, not like unrelated tasks.

The spec builders should preferably be organized like:
- iter_level1_specs()
- iter_level2_specs()
- iter_level3_specs()
- iter_level4_specs()
- iter_level5_specs()

Each level may reuse or extend earlier construction ideas, but must remain bounded.

==================================================
REQUIRED IMPLEMENTATION PATTERNS
==================================================

Use these patterns.

1. PER-LEVEL HARD CAPS

Include something like:

```python
LEVEL_SPEC_CAPS = {
    "level_1": 2000,
    "level_2": 3000,
    "level_3": 4000,
    "level_4": 5000,
    "level_5": 5000,
}
````

2. OPTIONAL PER-FAMILY CAPS

Include something like:

```python
FAMILY_CAPS = {
    "level_1": {"basic": 2000},
    "level_2": {"basic": 1500, "variant": 1500},
    "level_3": {"family_a": 1500, "family_b": 1500, "family_c": 1000},
    "level_4": {"family_a": 2000, "family_b": 1500, "family_c": 1500},
    "level_5": {"family_a": 2000, "family_b": 1500, "family_c": 1500},
}
```

3. CAPPED ITERATION HELPER

Include a helper like:

```python
def _take(iterable, n):
    for i, item in enumerate(iterable):
        if i >= n:
            break
        yield item
```

4. BOUNDED _iter_specs

`_iter_specs(difficulty)` must return a capped finite iterable, for example:

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

5. CHEAP estimate_capacity()

Use a capped or estimated return, for example:

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

Do NOT compute exact capacity by traversing the whole iterator unless the space is trivially tiny.

6. BOUNDED generate()

`generate()` must sample from a bounded prefix only.

Required pattern:

```python
prefix = min(max(count * 8, 256), 5000)
pool = list(itertools.islice(_iter_specs(difficulty), 0, prefix))
```

Then sample from `pool` with seeded randomness.

7. BOUNDED generate_unique()

`generate_unique()` must:

* build a bounded pool from a capped prefix of `_iter_specs(difficulty)`
* shuffle deterministically using seed/difficulty/offset/stride
* dedupe by a stable key such as the rendered input or canonicalized spec
* return up to `count` items

It must NOT use:

```python
itertools.islice(_iter_specs(difficulty), offset, None, stride)
```

on a huge stream.

8. FINITE iter_samples()

`iter_samples()` must be explicitly finite.
It may yield from a bounded shuffled pool or from repeated bounded batches, but total emitted items must be capped.

Acceptable pattern:

```python
def iter_samples(difficulty: str = "level_1", seed=None):
    max_items = LEVEL_SPEC_CAPS.get(difficulty, 2000)
    rng = random.Random((seed, difficulty, "iter_samples"))
    pool = list(itertools.islice(_iter_specs(difficulty), 0, max_items))
    rng.shuffle(pool)
    seen = set()
    for idx, spec in enumerate(pool):
        sample = _sample_from_spec(spec, difficulty, instruction_idx=idx)
        key = sample.get("input", "")
        if key in seen:
            continue
        seen.add(key)
        yield sample
```

==================================================
SEARCH SPACE DESIGN RULES
=========================

When building specs:

* use small bounded integer ranges,
* bounded operator sets,
* bounded coefficient sets,
* bounded structural variants.

Do NOT write nested products that multiply into enormous spaces unless they are aggressively capped at the family level.

If a family would naturally generate too many combinations:

* reduce ranges,
* reduce allowed coefficients,
* reduce allowed operator pairs,
* or use representative subsets instead of exhaustive products.

Prefer:

* carefully curated finite sets
  over
* brute-force exhaustive enumeration.

==================================================
DEDUPLICATION RULES
===================

The module must avoid duplicate prompts/examples.

Use a stable dedupe key:

* rendered input text,
* canonicalized spec tuple,
* or another deterministic normalized representation.

Dedupe must also be bounded:

* do not keep growing unbounded state across an infinite process,
* only dedupe within a capped pool or capped batch.

==================================================
OUTPUT FORMAT RULES
===================

Each generated sample should be a dict with at least fields like:

* "input"
* "output"

Optional fields:

* "difficulty"
* "metadata"
* "reasoning"

Keep the shape consistent across all samples.

==================================================
CURRICULUM REQUIREMENT
======================

Implement `curriculum()` returning a mapping that explains what changes across levels.

Example shape:

```python
def curriculum():
    return {
        "level_1": ["simple single-step cases"],
        "level_2": ["adds sign flips or basic composition"],
        "level_3": ["adds multiple constraints or branching"],
        "level_4": ["adds nested structure / multi-step reasoning"],
        "level_5": ["adds hardest bounded variants while staying finite"],
    }
```

==================================================
STYLE REQUIREMENTS
==================

* Use only the Python standard library unless absolutely necessary.
* Keep the module self-contained.
* Add clear comments around finite-enumeration safeguards.
* Prefer readable helper functions over clever compressed code.
* Include type hints where practical.
* Ensure the module imports cleanly.

==================================================
MANDATORY SELF-CHECK BEFORE FINALIZING
======================================

Before you produce the final module, verify all of the following:

* [ ] No infinite loops in any spec iterator
* [ ] No exact full traversal capacity computation for large spaces
* [ ] No deep offset replay over huge generators
* [ ] Every difficulty has a hard cap
* [ ] Every large family has a hard cap
* [ ] `generate()` only samples from a bounded prefix
* [ ] `generate_unique()` uses a bounded pool, deterministic shuffle, and dedupe
* [ ] `iter_samples()` is explicitly finite
* [ ] Difficulty progression is cascading and coherent
* [ ] The code is valid Python

==================================================
IMPORTANT FAILURE MODES TO AVOID
================================

Do NOT do any of these:

1. Do not compute:

```python
count = sum(1 for _ in _iter_specs(difficulty))
```

unless the iterator is trivially tiny.

2. Do not use:

```python
while True:
    ...
```

for spec generation.

3. Do not rely on rejection sampling without a hard attempt cap.

4. Do not use gigantic nested Cartesian products without a cap.

5. Do not make `generate_unique()` slower as offset grows.

6. Do not produce a module where “finite” still means tens of millions of candidate specs.

==================================================
FINAL OUTPUT INSTRUCTION
========================

Return only the Python module code, nothing else.

The module must satisfy all requirements above and must be safe for dataset-building pipelines that expect finite, bounded, deterministic generation.

````

A shorter version for everyday use:

```text
Write a self-contained Python dataset generator module with:
- generate
- generate_unique
- iter_samples
- estimate_capacity
- curriculum

Hard requirements:
- all enumeration must be finite
- all difficulties must have explicit hard caps
- no exact capacity by exhausting the spec iterator
- no deep offset replay with islice(offset, ...)
- generate() must sample from a bounded prefix only
- generate_unique() must use a bounded candidate pool + deterministic shuffle + dedupe
- iter_samples() must be explicitly finite
- difficulty levels must cascade coherently from level_1 to level_5
- large Cartesian products must be reduced or capped per family
- use only standard library
- return only code

Include:
- LEVEL_SPEC_CAPS
- optional FAMILY_CAPS
- _take helper
- bounded _iter_specs(difficulty)
- cheap estimate_capacity() returning capped/estimated values
- comments explaining the finite-enumeration safeguards
````
