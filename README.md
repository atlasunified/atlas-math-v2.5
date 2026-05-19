# Atlas Math 2.5

Atlas Math 2.5 is a modular framework for generating, curating, exporting, rebuilding, and reporting on mathematical reasoning datasets.

It extends Atlas Math 2.0 with a repository-native workflow: generate once, store consistently, rebuild deterministically, and evaluate on stable grouped splits.

## What it includes

- registry-driven generator discovery
- difficulty-aware dataset construction
- structured and random generation modes
- repository export and repository rebuild workflows
- canonical identity fields for deduplication and split safety
- coverage analysis and report generation
- Hugging Face export support

## Evolution

| Version | Focus |
|---|---|
| v1.0 | Core mathematical computation generators |
| v2.0 | Modular generator registry and direct dataset building |
| v2.5 | Repository export, repository rebuild, grouped identity-aware datasets, reporting, and stronger generator contracts |

Previous versions:

- v1.0: <https://github.com/atlasunified/atlas-mathematical-computations>
- v2.0: <https://github.com/atlasunified/atlas-math>

## Pipeline

Atlas Math 2.5 supports both direct dataset generation and repository-backed release workflows:

```text
Generators -> Dataset
Generators -> Repository -> Dataset -> Evaluation
```

The repository layer makes it possible to:

- preserve reusable sample and case inventories
- rebuild datasets from curated sources instead of regenerating from scratch
- apply stable deduplication using canonical, case-level, or family-level identities
- construct grouped, split-safe datasets
- inspect repository coverage and export JSON / CSV reports

## Current validation status

Local upload-readiness checks for the prepared Atlas Math 2.5 bundle:

| Check | Result |
|---|---:|
| Registered modules | 152 |
| Declared module/difficulty buckets | 750 |
| Bucket smoke failures | 0 |
| 100-record direct build | Pass |
| Repository export/report smoke test | Pass |
| Hugging Face export smoke test | Pass |
| Registry smoke tests | Pass |

Topic coverage:

| Topic | Modules |
|---|---:|
| algebra | 32 |
| arithmetic | 20 |
| calculus | 22 |
| geometry | 20 |
| prealgebra | 20 |
| precalculus | 25 |
| trigonometry | 13 |

## Installation

From source:

```bash
git clone https://github.com/atlasunified/atlas-math-v2.5.git
cd atlas-math-v2.5
pip install -e .
```

For development checks:

```bash
python -m compileall -q atlas_math tests
python -m pytest -q
```

## CLI overview

```bash
atlas-math <command> [options]
```

Available commands:

- `list`
- `build`
- `repository`
- `repository-build`
- `hf-export`
- `report`

If no subcommand is provided, the CLI falls back to the interactive menu.

## Quick start

List registered modules:

```bash
atlas-math list --json
```

Build a dataset directly from modules:

```bash
atlas-math build \
  --target-records 100 \
  --workers 1 \
  --output outputs/smoke.jsonl
```

Export a repository:

```bash
atlas-math repository \
  --topics algebra geometry \
  --samples-per-level 100 \
  --cases-per-level 100 \
  --output-dir repository
```

Build a dataset from a repository:

```bash
atlas-math repository-build \
  --repository-dir repository \
  --size large \
  --source-kind auto \
  --dedupe-mode canonical \
  --output outputs/repository_build.jsonl
```

Export a Hugging Face-ready dataset directory:

```bash
atlas-math hf-export \
  --repository-dir repository \
  --output-dir outputs/hf_dataset \
  --format hf \
  --source-kind auto \
  --split-mode grouped_canonical
```

Generate repository coverage reports:

```bash
atlas-math report \
  --repository-dir repository \
  --dashboard
```

## CLI commands

### `list`

Lists registered modules from the registry.

```bash
atlas-math list
atlas-math list --json
```

The command surfaces:

- module ID
- module name
- topic
- difficulty levels
- whether the module appears structured or random-only

### `build`

Builds a dataset directly from registered modules.

```bash
atlas-math build \
  --topic algebra \
  --size medium \
  --difficulty-mix balanced \
  --generation-mode auto \
  --format clean \
  --output outputs/output.jsonl
```

Key options:

| Option | Description |
|---|---|
| `--topic` / `--topics` | Filter by topic |
| `--modules` | Target explicit module IDs |
| `--size` | One of `small`, `medium`, `large`, `full` |
| `--target-records` | Exact target count; overrides `--size` |
| `--difficulty-mix` | `balanced`, `curriculum`, `advanced`, or `middle_heavy` |
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

### `repository`

Exports repository content from selected modules.

```bash
atlas-math repository \
  --topic geometry \
  --output-dir repository \
  --samples-per-level 50 \
  --format rich
```

### `repository-build`

Builds a release dataset from repository content.

```bash
atlas-math repository-build \
  --repository-dir repository \
  --topics algebra \
  --difficulties level_3 level_4 \
  --source-kind auto \
  --dedupe-mode canonical \
  --output outputs/repository_build.jsonl
```

### `hf-export`

Exports a Hugging Face-ready dataset directory from repository content.

```bash
atlas-math hf-export \
  --repository-dir repository \
  --output-dir outputs/hf_dataset \
  --format hf \
  --source-kind auto \
  --split-mode grouped_canonical
```

### `report`

Analyzes a repository and writes coverage reports.

```bash
atlas-math report \
  --repository-dir repository \
  --dashboard
```

Default outputs:

- `repository/coverage_report.json`
- `repository/coverage_report.csv`

## Output formats

Direct builds support:

| Format | Shape |
|---|---|
| `clean` | `instruction`, `input`, `answer`, `answer_words`, `difficulty` |
| `extended` | `clean` + `topic`, `subtopic` |
| `rich` | full normalized record with metadata and identity fields |

Hugging Face export supports:

| Format | Shape |
|---|---|
| `hf` | instruction-style dataset rows |
| `chatml` | chat-format rows |
| `alpaca` | Alpaca-style instruction rows |

## Difficulty levels

Most generators use five canonical levels:

- `level_1`
- `level_2`
- `level_3`
- `level_4`
- `level_5`

Some legacy trigonometry modules explicitly support only `level_1` through `level_3`; their `MODULE_INFO["difficulty_levels"]` reflects that.

Built-in difficulty mixes:

| Mix | Distribution |
|---|---|
| `balanced` | 20 / 20 / 20 / 20 / 20 |
| `curriculum` | 35 / 25 / 20 / 12 / 8 |
| `advanced` | 8 / 12 / 20 / 25 / 35 |
| `middle_heavy` | 10 / 20 / 40 / 20 / 10 |

## Deduplication and identity fields

Supported dedupe modes:

| Mode | Uniqueness basis |
|---|---|
| `input_answer` | normalized input + answer |
| `input_only` | normalized input |
| `full` | full serialized record |
| `canonical` | `canonical_key` |
| `case_id` | `case_id` |
| `family` | `family_id` |

The runtime normalizes identity and grouping fields across records, including:

- `sample_id`
- `canonical_key`
- `case_id`
- `family_id`
- `template_id`
- `split_group_key`

These fields support canonical deduplication, grouped splits, leakage reduction, repository rebuild quality, and dataset auditability.

## Record model

A rich record may include fields like:

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

## Generator contract

Atlas Math 2.5 supports legacy modules, but new modules should follow the stricter generator contract.

A production-ready generator should be:

- finite
- deterministic
- difficulty-cascading
- operationally bounded
- identity-aware
- repository-safe
- split-safe

Full contributor guidance is in the generator builder document:

- [MATH_GENERATOR.md](./MATH_GENERATOR.md)
- Pinned reference: <https://github.com/atlasunified/atlas-math-v2.5/blob/f6d5dd6e92c9eaf9d957bb44e81dc3b8332df840/MATH_GENERATOR.md>

Preferred exported functions:

```python
generate(count: int = 10, difficulty: str = "level_1", seed=None) -> list[dict]
generate_unique(count: int = 10, difficulty: str = "level_1", offset: int = 0, stride: int = 1, seed=None) -> list[dict]
iter_samples(difficulty: str = "level_1", seed=None)
estimate_capacity(difficulty: str = "level_1")
curriculum() -> dict
```

Common helper functions:

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

Recommended metadata:

- `canonical_key`
- `case_id`
- `family_id`
- `template_id`
- `structured`
- family-specific audit values

## Generator design rules

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
- `level_4`: composition, branching, or deeper reasoning
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

Older structured modules may still use offset slicing over a fully materialized or exact finite spec stream. That path is tolerated by the runtime, but it is not the preferred pattern for new Atlas Math 2.5 modules.

For new generators, prefer:

- bounded candidate pools
- deterministic shuffling
- hard level caps
- family budgets

## Recommended project structure

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

## Dataset card

The Hugging Face dataset card draft is in [`DATASET_CARD.md`](./DATASET_CARD.md). Copy it to the dataset repository as `README.md` when publishing generated JSONL files.

## Use cases

Atlas Math 2.5 is suitable for:

- synthetic math dataset generation
- curriculum-based training corpora
- reasoning benchmark construction
- repository-backed release datasets
- grouped-split evaluation sets
- data audits using canonical and family identities

## Contributing checklist

When adding or updating a module:

- [ ] `MODULE_INFO` is accurate
- [ ] difficulty levels are explicit
- [ ] generation is finite
- [ ] generation is operationally bounded
- [ ] record shape is runtime-compatible
- [ ] metadata includes stable identities where possible
- [ ] difficulty progression is coherent
- [ ] repository workflows remain usable

## License

MIT. See [`LICENSE`](./LICENSE).
