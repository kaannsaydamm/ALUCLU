from __future__ import annotations

import hashlib

import pytest

from aluclu.alc_r0.devign_preprocess import (
    DevignPreprocessError,
    code_five_shingles,
    normalize_devign_code,
    tokenize_devign_code,
)


def test_normalization_is_strict_utf8_nfc_lf_and_outer_blank_line_only() -> None:
    raw = b" \r\nint cafe\xcc\x81 = 1;  \t\r\n  // keep comment  \r\n\t\r\n"

    normalized = normalize_devign_code(raw)

    assert normalized == "int café = 1;\n  // keep comment"
    assert hashlib.sha256(normalized.encode("utf-8")).hexdigest() == (
        "695d3ab3810a585f3bb40954d0593af136f3b88cf3a5878e714b75c517d6a9ed"
    )


def test_invalid_utf8_empty_code_and_wrong_input_type_fail_closed() -> None:
    with pytest.raises(DevignPreprocessError, match="UTF-8"):
        normalize_devign_code(b"\xff")
    with pytest.raises(DevignPreprocessError, match="empty"):
        normalize_devign_code(b" \r\n\t\n ")
    with pytest.raises(DevignPreprocessError, match="bytes"):
        normalize_devign_code("int x;")  # type: ignore[arg-type]


def test_tokenizer_keeps_literals_comments_and_individual_punctuation() -> None:
    code = "int x=0x1fUL + .5e-2F; // x++\nchar c='\\n';"

    assert tokenize_devign_code(code) == (
        "int",
        "x",
        "=",
        "0x1fUL",
        "+",
        ".5e-2F",
        ";",
        "/",
        "/",
        "x",
        "+",
        "+",
        "char",
        "c",
        "=",
        "'\\n'",
        ";",
    )


def test_five_shingles_use_token_content_not_whitespace() -> None:
    a = code_five_shingles(tokenize_devign_code("int x=1; return x;"))
    b = code_five_shingles(tokenize_devign_code("int  x = 1 ;\nreturn x ;"))

    assert a == b
    assert ("int", "x", "=", "1", ";") in a
    assert code_five_shingles(("int", "x", "=", "1")) == frozenset()
