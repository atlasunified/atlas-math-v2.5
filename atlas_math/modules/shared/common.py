from __future__ import annotations

import re

from atlas_math.utils.text_normalization import number_words


_TOKEN_PATTERN = re.compile(
    r"<=|>=|!=|==|→|-?\d+(?:\.\d+)?|[A-Za-z]+|[=+\-*/^(){}\[\],:.;<>]|\S"
)

_OPERATOR_WORDS = {
    "=": "equals",
    "==": "equals",
    "!=": "does not equal",
    "<": "is less than",
    ">": "is greater than",
    "<=": "is less than or equal to",
    ">=": "is greater than or equal to",
    "+": "plus",
    "-": "minus",
    "*": "times",
    "/": "divided by",
    "^": "to the power of",
    "→": "therefore",
}


def _verbalize_token(token: str) -> str:
    if re.fullmatch(r"-?\d+(?:\.\d+)?", token):
        if token.startswith("-"):
            return "negative " + number_words(token[1:])
        return number_words(token)
    return _OPERATOR_WORDS.get(token, token)


def _cleanup_spacing(text: str) -> str:
    text = re.sub(r"\s+([,.:;!?])", r"\1", text)
    text = re.sub(r"([({\[])\s+", r"\1", text)
    text = re.sub(r"\s+([)}\]])", r"\1", text)
    return re.sub(r"\s+", " ", text).strip()


def _verbalize_text(text: str) -> str:
    lines: list[str] = []
    for raw_line in str(text).splitlines():
        stripped = raw_line.strip()
        if not stripped:
            lines.append("")
            continue
        pieces = [_verbalize_token(token) for token in _TOKEN_PATTERN.findall(stripped)]
        lines.append(_cleanup_spacing(" ".join(piece for piece in pieces if piece)))
    return "\n".join(lines)


def _build_final_answer_words(final_answer: str) -> str:
    spoken = _verbalize_text(final_answer)
    if not spoken:
        return ""
    if spoken.endswith((".", "!", "?")):
        return f"Final answer is: {spoken}"
    return f"Final answer is: {spoken}."


def make_sample(
    *,
    module_id: str,
    topic: str,
    subtopic: str,
    difficulty: str,
    instruction: str,
    input_text: str,
    answer,
    metadata: dict | None = None,
) -> dict:
    metadata = dict(metadata or {})

    output_text = "" if answer is None else str(answer)
    short_answer = str(metadata.get("final_answer", output_text))
    output_words_text = _verbalize_text(output_text)
    answer_words_text = _build_final_answer_words(short_answer)

    metadata.setdefault("final_answer", short_answer)
    metadata["final_answer_words"] = answer_words_text

    return {
        "module_id": module_id,
        "topic": topic,
        "subtopic": subtopic,
        "difficulty": difficulty,
        "difficulty_level": difficulty,
        "instruction": instruction,
        "input": input_text,
        "output": output_text,
        "output_words": output_words_text,
        "answer": short_answer,
        "answer_words": answer_words_text,
        "metadata": metadata,
    }

