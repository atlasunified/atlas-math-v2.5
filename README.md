# Atlas Math 2.5

**Atlas Math 2.5** is a modular framework for generating, curating, exporting, rebuilding, and reporting on mathematical reasoning datasets.

It combines:

- **registry-driven generator discovery**
- **difficulty-aware dataset construction**
- **structured and random generation modes**
- **repository export and repository rebuild workflows**
- **canonical identity fields for deduplication and split safety**
- **coverage analysis and report generation**

Atlas Math 2.5 extends the earlier Atlas Math line with a repository-native workflow: generate once, store consistently, rebuild deterministically, and evaluate on stable grouped splits.

---

## Evolution

| Version | Focus |
|---|---|
| **v1.0** | Core mathematical computation generators |
| **v2.0** | Modular generator registry and direct dataset building |
| **v2.5** | Repository export, repository rebuild, grouped identity-aware datasets, reporting, and stronger generator contracts |

Previous versions:

- **v1.0**: https://github.com/atlasunified/atlas-mathematical-computations
- **v2.0**: https://github.com/atlasunified/atlas-math

---

## What Atlas Math 2.5 Adds

Atlas Math 2.5 is built around a fuller pipeline than simple one-shot sample generation:

```text
Generators → Dataset
Generators → Repository → Dataset → Evaluation
```

That repository layer makes it possible to:

- preserve reusable sample and case inventories
- rebuild datasets from curated sources instead of regenerating from scratch
- apply stable deduplication using canonical or case-level identities
- construct split-safe datasets using grouped identities
- inspect repository coverage and export JSON / CSV reports

---

## Core Capabilities

### 1. Generator registry

Modules are registered and surfaced through the CLI. Each module declares metadata such as:

- `module_id`
- `name`
- `topic`
- `subtopic`
- `difficulty_levels`
- `enabled`

The CLI can list modules, filter by topic, or target explicit module IDs.

---

### 2. Multiple generation styles

Atlas Math supports two broad module styles:

- **Structured generators**
  - finite
  - enumerable
  - often deterministic by construction
  - usually support `generate_unique()`, `iter_samples()`, and `estimate_capacity()`

- **Random-only generators**
  - stochastic sampling through `generate()`
  - useful when exact structured traversal is not available

For Atlas Math 2.5, the preferred standard for new modules is:

- bounded
- deterministic
- repository-safe
- identity-aware
- split-safe

---

### 3. Difficulty-aware dataset building

The `build` command constructs datasets directly from registered modules using:

- preset sizes or exact target counts
- configurable difficulty mixes
- structured vs random generation preferences
- adaptive batching
- retry rounds
- low-yield exhaustion handling
- post-hoc deduplication

Built-in size presets:

| Size | Target records |
|---|---:|
| `small` | 100 |
| `medium` | 1,000 |
| `large` | 5,000 |
| `full` | 20,000 |

Built-in difficulty mixes:

| Mix | Distribution |
|---|---|
| `balanced` | 20 / 20 / 20 / 20 / 20 |
| `curriculum` | 35 / 25 / 20 / 12 / 8 |
| `advanced` | 8 / 12 / 20 / 25 / 35 |
| `middle_heavy` | 10 / 20 / 40 / 20 / 10 |

Difficulty levels are standardized as:

- `level_1`
- `level_2`
- `level_3`
- `level_4`
- `level_5`

---

### 4. Repository export and rebuild

Atlas Math 2.5 introduces first-class repository workflows:

- export repository content from selected modules
- store per-module / per-level generated records
- optionally use sample rows or case rows during rebuild
- rebuild datasets from a repository with topic / module / generator / difficulty filters
- shuffle or preserve ordering
- apply post-hoc dedupe during dataset reconstruction

This supports more stable benchmarking and release construction than repeated raw generation.

---

### 5. Identity-aware records

The runtime normalizes identity and grouping fields across records, including:

- `sample_id`
- `canonical_key`
- `case_id`
- `family_id`
- `template_id`
- `split_group_key`

These fields are used to improve:

- canonical deduplication
- case-level grouping
- family-level grouping
- leakage reduction across splits
- repository rebuild quality
- dataset auditability

The system will derive missing identity fields from the record and its `metadata`, but modules are stronger when they emit stable identity metadata directly.

---

### 6. Coverage analysis and reporting

The `report` command analyzes a repository and writes report files. It supports:

- repository coverage analysis
- dashboard rendering in the CLI
- JSON report output
- CSV report output

By default, reports are written under the repository directory as coverage reports.

---

## Installation

### From PyPI

```bash
pip install atlas-math
```

### From source

```bash
git clone https://github.com/atlasunified/atlas-math.git
cd atlas-math
pip install -e .
```

---

## CLI Overview

```bash
atlas-math <command> [options]
```

Available commands:

- `list`
- `build`
- `repository`
- `repository-build`
- `report`

If no subcommand is provided, the CLI falls back to the interactive menu.

---

## Quick Start

### List registered modules

```bash
atlas-math list
```

### List registered modules as JSON

```bash
atlas-math list --json
```

### Build a dataset directly from modules

```bash
atlas-math build   --topic algebra   --size medium   --output outputs/algebra.jsonl
```

### Export a repository

```bash
atlas-math repository   --topics algebra geometry   --samples-per-level 100   --output-dir repository
```

### Build a dataset from a repository

```bash
atlas-math repository-build   --repository-dir repository   --size large   --output outputs/dataset.jsonl
```

### Generate coverage reports

```bash
atlas-math report   --repository-dir repository   --dashboard
```

---

## CLI Commands

## `list`

Lists registered modules from the registry.

### Examples

```bash
atlas-math list
atlas-math list --json
```

### Output

The command surfaces, for each module:

- module ID
- module name
- topic
- difficulty levels
- whether the module appears structured or random-only

---

## `build`

Builds a dataset directly from registered modules.

### Key options

```bash
atlas-math build   --topic algebra   --size medium   --difficulty-mix balanced   --generation-mode auto   --format clean   --output outputs/output.jsonl
```

### Build options

| Option | Description |
|---|---|
| `--topic` / `--topics` | Filter by topic |
| `--modules` | Target explicit module IDs |
| `--size` | One of `small`, `medium`, `large`, `full` |
| `--target-records` | Exact target count; overrides `--size` |
| `--difficulty-mix` | One of `balanced`, `curriculum`, `advanced`, `middle_heavy` |
| `--generation-mode` | `auto`, `structured`, or `random` |
| `--format` | `clean`, `extended`, or `rich` |
| `--run-to-completion` | Enumerate all exact finite structured cases when available |
| `--output` | Output JSONL path |
| `--progress` | Show progress |
| `--dedupe-mode` | Post-hoc uniqueness key |
| `--workers` | Worker count |
| `--max-batch-size` | Max adaptive chunk size |
| `--min-yield-ratio` | Low-yield threshold |
| `--exhaustion-patience` | Rounds before treating a bucket as exhausted |
| `--target-tolerance` | Acceptable miss window around target |
| `--max-rounds` | Maximum generation rounds including retries |

### Output formats

| Format | Shape |
|---|---|
| `clean` | instruction, input, answer, answer_words, difficulty |
| `extended` | clean + topic, subtopic |
| `rich` | full normalized record with metadata and identity fields |

### Deduplication modes

| Mode | Uniqueness basis |
|---|---|
| `input_answer` | normalized input + answer |
| `input_only` | normalized input |
| `full` | full serialized record |
| `canonical` | `canonical_key` |
| `case_id` | `case_id` |
| `family` | `family_id` |

---

## `repository`

Exports repository content from selected modules.

### Example

```bash
atlas-math repository   --topic geometry   --output-dir repository   --samples-per-level 50   --format rich
```

### Options

| Option | Description |
|---|---|
| `--topic` / `--topics` | Filter by topic |
| `--modules` | Target explicit modules |
| `--output-dir` | Repository output directory |
| `--samples-per-level` | Sample rows exported per level |
| `--cases-per-level` | Optional case-row budget |
| `--format` | `clean`, `extended`, or `rich` |
| `--generation-mode` | `auto`, `structured`, or `random` |
| `--progress` | Show progress |

---

## `repository-build`

Builds a release dataset from repository content.

### Example

```bash
atlas-math repository-build   --repository-dir repository   --topics algebra   --difficulties level_3 level_4   --source-kind auto   --dedupe-mode canonical   --output outputs/repository_build.jsonl
```

### Options

| Option | Description |
|---|---|
| `--repository-dir` | Repository path |
| `--topic` / `--topics` | Topic filters |
| `--modules` | Module filters |
| `--generators` | Generator filters |
| `--difficulties` | Difficulty filters |
| `--size` | Size preset |
| `--target-records` | Exact target size |
| `--difficulty-mix` | Difficulty allocation strategy |
| `--dedupe-mode` | Post-hoc uniqueness strategy |
| `--shuffle` / `--no-shuffle` | Shuffle selection |
| `--seed` | RNG seed |
| `--output` | Output JSONL path |
| `--source-kind` | `samples`, `cases`, or `auto` |
| `--split-mode` | `random`, `grouped_canonical`, `grouped_case`, `grouped_family` |

### Split modes

| Split mode | Grouping behavior |
|---|---|
| `random` | no grouping guarantee |
| `grouped_canonical` | groups by canonical identity |
| `grouped_case` | groups by case identity |
| `grouped_family` | groups by family identity |

---

## `report`

Analyzes a repository and writes coverage reports.

### Example

```bash
atlas-math report   --repository-dir repository   --dashboard
```

### Outputs

By default:

- `repository/coverage_report.json`
- `repository/coverage_report.csv`

You can override these with:

- `--json-out`
- `--csv-out`

---

## Record Model

Atlas Math serializes and normalizes records through a common path. A rich record may include fields like:

```json
{
  "module_id": "algebra.linears.cascading_linear_reasoning",
  "topic": "algebra",
  "subtopic": "linears",
  "difficulty": "level_3",
  "difficulty_level": "level_3",
  "instruction": "Solve the algebra problem step by step: ...",
  "input": "...",
  "output": "...",
  "output_words": "...",
  "answer": "...",
  "answer_words": "...",
  "metadata": {
    "canonical_key": "...",
    "case_id": "...",
    "family_id": "...",
    "template_id": "...",
    "structured": true
  },
  "sample_id": "...",
  "case_id": "...",
  "canonical_key": "...",
  "family_id": "...",
  "template_id": "...",
  "split_group_key": "..."
}
```

The runtime attaches missing identity fields automatically, including `sample_id` and `split_group_key`, which improves consistency across repository and rebuild workflows.

---

## Generator Contract

Atlas Math 2.5 supports legacy modules, but the recommended contributor standard is stricter.

A strong generator module should be:

- finite
- deterministic
- difficulty-cascading
- bounded in operational cost
- identity-aware
- repository-safe

### Preferred exported functions

```python
generate(count: int = 10, difficulty: str = "level_1", seed=None) -> list[dict]
generate_unique(count: int = 10, difficulty: str = "level_1", offset: int = 0, stride: int = 1, seed=None) -> list[dict]
iter_samples(difficulty: str = "level_1", seed=None)
estimate_capacity(difficulty: str = "level_1")
curriculum() -> dict
```

### Common helper functions

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

### Recommended metadata

Modules should provide stable metadata where possible:

- `canonical_key`
- `case_id`
- `family_id`
- `template_id`
- `structured`
- family-specific values useful for auditing

### Why this matters

These identities improve:

- canonical dedupe
- release dataset quality
- split safety
- leakage auditing
- reproducibility

---

## Generator Design Rules

Atlas Math 2.5 is most effective when modules follow the stronger generator guide.

### 1. Enumeration must be finite

Avoid:

- `while True`
- unbounded search loops
- unbounded recursion
- rejection loops without a hard attempt cap

Prefer:

- bounded ranges
- capped products
- finite iterators
- hard per-family budgets

### 2. Finite must also mean operationally bounded

A generator is not acceptable if it is technically finite but operationally massive. Very large Cartesian products and deep replay-based access patterns degrade repository workflows.

### 3. Difficulty progression should cascade

The preferred pattern is:

- `level_1`: simplest valid instances
- `level_2`: one additional complication
- `level_3`: more structure or multistep reasoning
- `level_4`: composition, branching, or more difficult reasoning
- `level_5`: hardest bounded variant

### 4. Capacity should be cheap

`estimate_capacity()` should return a cheap value:

- exact for genuinely small finite spaces
- capped
- estimated
- lower bound
- unknown

It should not require expensive full traversal for large spaces.

### 5. Avoid deep offset replay

Older structured modules may still use offset slicing over a fully materialized or exact finite spec stream. That is tolerated by the runtime, but it is not the preferred pattern for new Atlas Math 2.5 modules.

For new generators, use:

- bounded candidate pools
- deterministic shuffling
- hard level caps
- family budgets

---

## Example Module Shape

A typical structured module includes:

- `MODULE_INFO`
- level-specific spec iterators
- a `_sample_from_spec()` builder using `make_sample()`
- stable metadata for identity fields
- `generate()`
- `generate_unique()`
- `iter_samples()`
- `estimate_capacity()`
- `curriculum()`

Example characteristics seen in current modules include:

- `make_sample()`-based record construction
- `MODULE_INFO` with topic / subtopic / difficulty levels
- stable `canonical_key`, `case_id`, and `family_id` in metadata
- explicit family caps and level caps in stronger modules

---

## Recommended Project Structure

```text
atlas_math/
├── cli.py
├── cli_commands.py
├── cli_common.py
├── cli_config.py
├── modules/
│   ├── algebra/
│   ├── geometry/
│   └── shared/
├── repository.py
├── repository_dataset.py
├── repository_report.py
└── registry.py
```

Actual internal structure can evolve, but the top-level system is organized around CLI orchestration, generator modules, repository workflows, and reporting.

---

## Use Cases

Atlas Math 2.5 is suitable for:

- synthetic math dataset generation
- curriculum-based training corpora
- reasoning benchmark construction
- repository-backed release datasets
- evaluation sets with grouped split controls
- data audits using canonical and family identities

---

## Contributing

When adding a new module:

1. Define `MODULE_INFO` accurately.
2. Implement the supported difficulty ladder explicitly.
3. Prefer `make_sample()` for consistent record shape.
4. Keep enumeration finite and operationally bounded.
5. Add stable identity metadata where possible.
6. Keep `estimate_capacity()` cheap.
7. Make the module repository-safe and split-safe.

A practical review checklist:

- [ ] module imports cleanly
- [ ] difficulty levels are explicit
- [ ] generation is finite
- [ ] generation is operationally bounded
- [ ] record shape is runtime-compatible
- [ ] metadata includes stable identities where possible
- [ ] difficulty progression is coherent
- [ ] repository workflows remain usable

---

## Roadmap

Near-term directions suggested by the current architecture include:

- stronger repository manifests
- richer case-level exports
- improved split-aware release tooling
- stricter generator validation
- expanded reasoning coverage across topics

---

## License

Add project license details here.

---

## Summary

Atlas Math 2.5 is not just a sample generator. It is a full **generation + repository + rebuild + reporting** system for mathematical reasoning datasets.

It shifts the workflow from:

```text
generate → use
```

to:

```text
generate → store → analyze → rebuild → evaluate
```
