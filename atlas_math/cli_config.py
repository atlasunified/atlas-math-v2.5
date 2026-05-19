from __future__ import annotations

SIZE_PRESETS = {
    "small": 100,
    "medium": 1000,
    "large": 5000,
    "full": 20000,
}

DEFAULT_LEVELS = ["level_1", "level_2", "level_3", "level_4", "level_5"]

DEFAULT_DIFFICULTY_MIXES = {
    "balanced": {
        "level_1": 0.20,
        "level_2": 0.20,
        "level_3": 0.20,
        "level_4": 0.20,
        "level_5": 0.20,
    },
    "curriculum": {
        "level_1": 0.35,
        "level_2": 0.25,
        "level_3": 0.20,
        "level_4": 0.12,
        "level_5": 0.08,
    },
    "advanced": {
        "level_1": 0.08,
        "level_2": 0.12,
        "level_3": 0.20,
        "level_4": 0.25,
        "level_5": 0.35,
    },
    "middle_heavy": {
        "level_1": 0.10,
        "level_2": 0.20,
        "level_3": 0.40,
        "level_4": 0.20,
        "level_5": 0.10,
    },
}

DEFAULT_MAX_BATCH_SIZE = 64
DEFAULT_MIN_YIELD_RATIO = 0.10
DEFAULT_EXHAUSTION_PATIENCE = 3
DEFAULT_TARGET_TOLERANCE = 0.05
DEFAULT_MAX_ROUNDS = 4
DEFAULT_MIN_UNIQUE_RATE = 0.01
DEFAULT_RETRY_OVERSHOOT = 1.10
DEFAULT_GENERATION_MODE = "auto"
DEFAULT_DEDUPE_MODE = "input_answer"

