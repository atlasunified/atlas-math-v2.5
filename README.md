# Atlas Math 2.5

Atlas Math 2.5 is a modular synthetic mathematics dataset generator. It builds on Atlas Math 2.0 with a repository-native workflow, structured generation, identity-aware deduplication, grouped split support, coverage reporting, and Hugging Face export tooling.

## Status

This branch includes the upload-readiness fixes from the May 2026 review. Current local checks:

| Check | Result |
|---|---:|
| Registered modules | 152 |
| Declared module/difficulty buckets | 750 |
| Bucket smoke failures | 0 |
| 100-record direct build | Pass |
| Repository export/report smoke test | Pass |
| Hugging Face export smoke test | Pass |

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

```bash
pip install -e .
```

## CLI

```bash
atlas-math <command> [options]
```

Commands:

- `list` — list registered generator modules.
- `build` — build a dataset directly from generators.
- `repository` — export reusable repository content from generators.
- `repository-build` — build a dataset from an exported repository.
- `hf-export` — export train/validation/test JSONL files for Hugging Face.
- `report` — generate repository coverage reports.

## Quick start

List modules:

```bash
atlas-math list --json
```

Build a small dataset directly from registered modules:

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
  --samples-per-level 50 \
  --cases-per-level 50 \
  --output-dir repository
```

Build from a repository:

```bash
atlas-math repository-build \
  --repository-dir repository \
  --size large \
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

Generate coverage reports:

```bash
atlas-math report \
  --repository-dir repository \
  --dashboard
```

## Difficulty levels

Most generators use five canonical levels:

- `level_1`
- `level_2`
- `level_3`
- `level_4`
- `level_5`

Some legacy trigonometry modules explicitly support only `level_1` through `level_3`; their `MODULE_INFO["difficulty_levels"]` reflects that.

## Output formats

Direct builds support:

- `clean`
- `extended`
- `rich`

Hugging Face export supports:

- `hf`
- `chatml`
- `alpaca`

## Deduplication

Supported dedupe modes:

- `input_answer`
- `input_only`
- `full`
- `canonical`
- `case_id`
- `family`

## Generator guidance

See [`MATH_GENERATOR.md`](./MATH_GENERATOR.md) for the recommended module contract. New generators should be finite, deterministic, operationally bounded, repository-safe, identity-aware, and split-safe.

## Dataset card

The Hugging Face dataset card draft is in [`DATASET_CARD.md`](./DATASET_CARD.md). Copy it to the dataset repository as `README.md` when publishing the generated JSONL files.

## Development checks

```bash
python -m compileall -q atlas_math
python -m atlas_math.cli list --json
pytest
```

## License

MIT. See [`LICENSE`](./LICENSE).
