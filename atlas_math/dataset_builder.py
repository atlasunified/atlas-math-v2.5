from __future__ import annotations

import random
from collections import Counter
from pathlib import Path
from typing import Any

from atlas_math.cli_common import dedupe_records_posthoc, serialize_sample, write_jsonl


class DatasetBuilder:
    def __init__(self, seed: int = 42, export_format: str = "clean", dedupe_mode: str = "input_answer") -> None:
        self.seed = seed
        self.export_format = export_format
        self.dedupe_mode = dedupe_mode
        self.records: list[dict[str, Any]] = []

    def add_samples(self, samples: list[Any]) -> None:
        self.records.extend(serialize_sample(sample, fmt=self.export_format) for sample in samples)

    def add_records(self, records: list[dict[str, Any]]) -> None:
        self.records.extend(dict(record) for record in records)

    @property
    def samples(self) -> list[dict[str, Any]]:
        return self.records

    @samples.setter
    def samples(self, values: list[Any]) -> None:
        self.records = []
        self.add_samples(values)

    def dedupe(self) -> int:
        self.records, duplicates = dedupe_records_posthoc(self.records, self.dedupe_mode)
        return duplicates

    def shuffle(self) -> None:
        random.Random(self.seed).shuffle(self.records)

    def write_jsonl(self, output_path: str) -> Path:
        write_jsonl(self.records, output_path)
        return Path(output_path)

    save_jsonl = write_jsonl

    def summary(self) -> dict[str, object]:
        by_module = Counter(str(record.get("module_id", "")) for record in self.records)
        by_difficulty = Counter(str(record.get("difficulty", "")) for record in self.records)
        return {
            "seed": self.seed,
            "export_format": self.export_format,
            "dedupe_mode": self.dedupe_mode,
            "sample_count": len(self.records),
            "modules": dict(sorted(by_module.items())),
            "difficulty_counts": dict(sorted(by_difficulty.items())),
        }

