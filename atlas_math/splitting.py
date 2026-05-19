from __future__ import annotations

import random
from collections import defaultdict
from typing import Any


SPLIT_MODES = {"random", "grouped_canonical", "grouped_case", "grouped_family"}


def split_mode_to_key(split_mode: str) -> str | None:
    if split_mode == "grouped_canonical":
        return "canonical_key"
    if split_mode == "grouped_case":
        return "case_id"
    if split_mode == "grouped_family":
        return "family_id"
    return None


def group_split(
    rows: list[dict[str, Any]],
    group_key: str = "split_group_key",
    split_ratios: dict[str, float] | None = None,
    seed: int = 42,
) -> dict[str, list[dict[str, Any]]]:
    split_ratios = split_ratios or {"train": 0.9, "validation": 0.05, "test": 0.05}
    groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        key = (
            str(row.get(group_key) or "")
            or str(row.get("canonical_key") or "")
            or str(row.get("case_id") or "")
            or str(row.get("family_id") or "")
            or str(row.get("sample_id") or "")
            or str(id(row))
        )
        groups[key].append(row)

    items = list(groups.items())
    rng = random.Random(seed)
    rng.shuffle(items)

    total = sum(len(v) for _, v in items)
    targets = {k: max(0, int(total * v)) for k, v in split_ratios.items()}
    out = {k: [] for k in split_ratios}
    counts = {k: 0 for k in split_ratios}

    for _, grouped_rows in items:
        split_name = min(split_ratios.keys(), key=lambda s: counts[s] / max(1, targets[s] or 1))
        out[split_name].extend(grouped_rows)
        counts[split_name] += len(grouped_rows)
    return out


def random_split(
    rows: list[dict[str, Any]],
    split_ratios: dict[str, float] | None = None,
) -> dict[str, list[dict[str, Any]]]:
    split_ratios = split_ratios or {"train": 0.9, "validation": 0.05, "test": 0.05}
    total = len(rows)
    train_end = int(total * split_ratios["train"])
    validation_end = train_end + int(total * split_ratios["validation"])
    return {
        "train": rows[:train_end],
        "validation": rows[train_end:validation_end],
        "test": rows[validation_end:],
    }


def split_rows(
    rows: list[dict[str, Any]],
    split_mode: str = "grouped_canonical",
    split_ratios: dict[str, float] | None = None,
    seed: int = 42,
) -> dict[str, list[dict[str, Any]]]:
    if split_mode not in SPLIT_MODES:
        raise ValueError(f"Unknown split mode: {split_mode}")
    if split_mode == "random":
        shuffled = list(rows)
        random.Random(seed).shuffle(shuffled)
        return random_split(shuffled, split_ratios=split_ratios)
    return group_split(rows, group_key=split_mode_to_key(split_mode) or "split_group_key", split_ratios=split_ratios, seed=seed)


def audit_split_leakage(splits: dict[str, list[dict[str, Any]]], key: str) -> dict[str, Any]:
    seen: dict[str, str] = {}
    collisions: list[dict[str, str]] = []
    for split_name, rows in splits.items():
        for row in rows:
            value = str(row.get(key) or "")
            if not value:
                continue
            previous = seen.get(value)
            if previous is not None and previous != split_name:
                collisions.append({"key": key, "value": value, "first_split": previous, "second_split": split_name})
            else:
                seen[value] = split_name
    return {"collision_count": len(collisions), "collisions": collisions[:50]}




