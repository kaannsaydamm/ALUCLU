"""Reference Devign code normalization and five-token shingle primitives.

These are development-only primitives. They do not perform MinHash, clone
grouping, or any operation on the independently sealed official test split.
"""

from __future__ import annotations

import re
import unicodedata
from collections.abc import Sequence

_STRING = r'(?:u8|u|U|L)?"(?:\\.|[^"\\])*"'
_CHAR = r"(?:u|U|L)?'(?:\\.|[^'\\])*'"
_NUMBER = (
    r"(?:0[xX](?:[0-9a-fA-F]+(?:\.[0-9a-fA-F]*)?|\.[0-9a-fA-F]+)"
    r"(?:[pP][+-]?[0-9]+)?|0[bB][01]+|"
    r"(?:[0-9]+(?:\.[0-9]*)?|\.[0-9]+)(?:[eE][+-]?[0-9]+)?)"
    r"[uUlLfF]*"
)
_IDENTIFIER = r"[A-Za-z_][A-Za-z_0-9]*"
DEVIGN_TOKEN_REGEX = rf"{_STRING}|{_CHAR}|{_NUMBER}|{_IDENTIFIER}|[^\s]"
_TOKENS = re.compile(DEVIGN_TOKEN_REGEX, flags=re.DOTALL)
_TRAILING_ASCII_WHITESPACE = " \t\v\f"


class DevignPreprocessError(ValueError):
    """Code bytes or tokens violate the development preprocessing contract."""


def normalize_devign_code(data: bytes) -> str:
    """Strict UTF-8, NFC, LF, trailing ASCII trim, then outer blank lines."""

    if type(data) is not bytes:
        raise DevignPreprocessError("code input must be bytes")
    try:
        text = data.decode("utf-8", errors="strict")
    except UnicodeDecodeError as exc:
        raise DevignPreprocessError("invalid UTF-8 code") from exc
    text = unicodedata.normalize("NFC", text).replace("\r\n", "\n").replace("\r", "\n")
    lines = [line.rstrip(_TRAILING_ASCII_WHITESPACE) for line in text.split("\n")]
    while lines and not lines[0]:
        lines.pop(0)
    while lines and not lines[-1]:
        lines.pop()
    if not lines:
        raise DevignPreprocessError("normalized code is empty")
    return "\n".join(lines)


def tokenize_devign_code(normalized_code: str) -> tuple[str, ...]:
    """Tokenize literals/identifiers/numbers, then each punctuation character."""

    if not isinstance(normalized_code, str) or not normalized_code:
        raise DevignPreprocessError("normalized code must be nonempty text")
    tokens = tuple(match.group(0) for match in _TOKENS.finditer(normalized_code))
    if not tokens:
        raise DevignPreprocessError("code contains no tokens")
    return tokens


def code_five_shingles(tokens: Sequence[str]) -> frozenset[tuple[str, ...]]:
    """Return unique contiguous five-token shingles in source order."""

    if any(not isinstance(token, str) or not token for token in tokens):
        raise DevignPreprocessError("shingle tokens must be nonempty text")
    return frozenset(
        tuple(tokens[index : index + 5]) for index in range(len(tokens) - 4)
    )
