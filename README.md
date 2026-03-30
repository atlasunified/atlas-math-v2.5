# Atlas Math 2.5

**Atlas Math 2.5** is a modular dataset generation and repository-building framework for mathematical reasoning.

It provides:

- structured and stochastic problem generation
- difficulty-aware dataset construction
- canonical deduplication and grouping
- reproducible repository exports
- dataset reconstruction from curated repositories
- coverage analysis and reporting

This version extends prior releases with **repository-native workflows**, **reasoning-aware generation**, and **multi-stage dataset pipelines**.

---

## Evolution

| Version | Focus |
|--------|------|
| **v1.0** | Core mathematical computation generators |
| **v2.0** | Modular generator registry + dataset builder |
| **v2.5 (current)** | Repository system, reasoning control, canonical grouping, rebuild pipelines |

Previous versions:

- v1.0 → https://github.com/atlasunified/atlas-mathematical-computations  
- v2.0 → https://github.com/atlasunified/atlas-math  

---

## Key Capabilities

### 1. Generator System

- Registry-based module system
- Supports:
  - structured generators (finite, enumerable)
  - random generators (stochastic sampling)
- Topic + subtopic organization
- Difficulty levels: `level_1` → `level_5`

---

### 2. Dataset Builder

- Build datasets directly from generators
- Supports:
  - difficulty distributions
  - deduplication strategies
  - batching + parallel workers
  - exhaustion-aware generation

---

### 3. Repository System (New in 2.5)

Atlas Math introduces a **repository layer**:

- persistent dataset storage by module
- per-difficulty sample pools
- reusable dataset source
- canonical grouping metadata:
  - `canonical_key`
  - `case_id`
  - `family_id`

This enables:

- deterministic dataset reconstruction
- evaluation dataset consistency
- split-safe grouping

---

### 4. Repository → Dataset Pipeline

Instead of generating data each time:

```
Generators → Repository → Dataset
```

Benefits:

- reproducibility
- controlled sampling
- stable benchmarking
- reduced generation cost

---

### 5. Coverage & Reporting

- repository analysis
- difficulty distribution tracking
- module coverage inspection
- JSON + CSV export
- optional CLI dashboard

---

## Installation

```bash
pip install atlas-math
```

Or from source:

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

Commands:

- `list`
- `build`
- `repository`
- `repository-build`
- `report`

---

## Quick Start

### 1. List available modules

```bash
atlas-math list
```

### 2. Build a dataset

```bash
atlas-math build \
  --topic algebra \
  --size medium \
  --output outputs/algebra.jsonl
```

### 3. Create a repository

```bash
atlas-math repository \
  --topics algebra geometry \
  --samples-per-level 100 \
  --output-dir repository
```

### 4. Build from repository

```bash
atlas-math repository-build \
  --repository-dir repository \
  --size large \
  --output outputs/dataset.jsonl
```

### 5. Generate reports

```bash
atlas-math report \
  --repository-dir repository \
  --dashboard
```

---

## Core Concepts

### Difficulty Levels

- `level_1` → basic
- `level_2` → intermediate
- `level_3` → standard reasoning
- `level_4` → multi-step reasoning
- `level_5` → advanced / complex reasoning

---

### Difficulty Mixes

| Mix | Distribution |
|-----|-------------|
| balanced | equal across levels |
| curriculum | easier-heavy |
| advanced | harder-heavy |
| middle_heavy | centered on level_3 |

---

### Generation Modes

| Mode | Behavior |
|------|--------|
| auto | selects best available mode |
| structured | enumerates deterministic cases |
| random | stochastic sampling |

---

### Output Formats

| Format | Description |
|--------|------------|
| clean | minimal fields |
| extended | + topic metadata |
| rich | full metadata + IDs |

---

### Deduplication Modes

| Mode | Key |
|------|----|
| input_answer | input + answer |
| input_only | input |
| full | full record |
| canonical | canonical_key |
| case_id | case grouping |
| family | template family |

---

## Repository Architecture

Each record may include:

```json
{
  "module_id": "...",
  "topic": "...",
  "subtopic": "...",
  "difficulty": "level_3",
  "input": "...",
  "answer": "...",
  "canonical_key": "...",
  "case_id": "...",
  "family_id": "...",
  "template_id": "...",
  "metadata": {...}
}
```

---

## Build Pipeline

### Direct Generation

```
Generators → Dataset
```

### Repository-Based (Recommended)

```
Generators → Repository → Dataset → Evaluation
```

---

## Advanced Usage

### Target-controlled generation

```bash
atlas-math build \
  --target-records 5000 \
  --target-tolerance 0.05 \
  --max-rounds 4
```

### Parallel generation

```bash
atlas-math build \
  --workers 8 \
  --max-batch-size 64
```

### Exhaustion-aware structured generation

```bash
atlas-math build \
  --run-to-completion \
  --min-yield-ratio 0.1 \
  --exhaustion-patience 3
```

### Repository filtering

```bash
atlas-math repository-build \
  --topics algebra \
  --difficulties level_3 level_4 \
  --generators generator_a \
  --no-shuffle
```

### Split-safe dataset construction

```bash
atlas-math repository-build \
  --split-mode grouped_canonical
```

Options:

- `random`
- `grouped_canonical`
- `grouped_case`
- `grouped_family`

---

## Design Principles

- Determinism where possible
- Controlled randomness where necessary
- Separation of generation and sampling
- Reproducibility first
- Dataset auditability
- Composable pipelines

---

## Project Structure

```
atlas_math/
├── cli/
├── generators/
├── registry/
├── repository/
├── dataset_builder/
├── reporting/
└── utils/
```

---

## Use Cases

- LLM training datasets
- reasoning benchmark construction
- curriculum learning pipelines
- synthetic math dataset generation
- evaluation set standardization

---

## Limitations

- depends on generator coverage
- structured generators may be finite
- deduplication reduces yield in constrained domains
- repository size can grow quickly

---

## Roadmap

- reasoning trace generation (chain-of-thought variants)
- symbolic validation hooks
- adaptive difficulty sampling
- curriculum-aware dataset builders
- distributed generation

---

## Contributing

1. Add new generator modules
2. Register them in the registry
3. Ensure:
   - difficulty coverage
   - canonical key stability
   - reproducibility

---

## License

Add license here.

---

## Summary

Atlas Math 2.5 is a dataset generation system + repository framework designed for:

- structured reasoning data
- reproducible pipelines
- scalable dataset construction

It shifts the workflow from:

```
generate → use
```

to:

```
generate → store → analyze → reuse → evaluate
```
