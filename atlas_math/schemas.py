from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True)
class Sample:
    module_id: str
    topic: str
    subtopic: str
    difficulty: str
    difficulty_level: int
    instruction: str
    input: str
    output: str
    output_words: str
    answer: str
    answer_words: str
    metadata: dict[str, Any] = field(default_factory=dict)
    sample_id: str = ""
    case_id: str = ""
    canonical_key: str = ""
    family_id: str = ""
    template_id: str = ""
    source_mode: str = ""
    generator_version: str = ""
    split_group_key: str = ""


@dataclass(slots=True)
class ModuleInfo:
    module_id: str
    name: str
    topic: str
    subtopic: str
    tags: list[str]
    description: str
    difficulty_levels: list[str]
    enabled: bool = True

