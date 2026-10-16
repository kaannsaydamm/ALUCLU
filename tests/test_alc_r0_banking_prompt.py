from __future__ import annotations

import os
from pathlib import Path

import pytest

from aluclu.alc_r0.banking_prompt import (
    BankingPromptError,
    build_banking_prompt,
    prepare_banking_prompt,
)
from aluclu.alc_r0.banking_source import load_verified_banking77_development


class _CharacterTokenizer:
    bos_token_id = None
    eos_token_id = None

    def encode(self, text: str, *, add_special_tokens: bool) -> list[int]:
        assert add_special_tokens is False
        return list(text.encode("ascii"))


def test_prompt_has_fixed_ordered_labels_query_and_intent_boundary() -> None:
    labels = ("card_arrival", "cash_withdrawal")
    prompt = build_banking_prompt(_CharacterTokenizer(), labels, "  MY card\r\n  ")

    expected = b"Labels: card_arrival cash_withdrawal\nInput: MY card\nIntent:"
    assert bytes(prompt.token_ids) == expected
    assert prompt.normalized_query == "MY card"
    assert prompt.original_query_tokens == len(b"MY card")
    assert prompt.retained_query_tokens == len(b"MY card")
    assert prompt.max_candidate_tokens == len(b" cash_withdrawal")


def test_truncation_keeps_head_and_tail_after_reserving_longest_candidate() -> None:
    labels = ("a", "long_name")
    query = "abcdefghijklmnopqrstuvwxyz"
    prefix = b"Labels: a long_name\nInput: "
    suffix = b"\nIntent:"
    longest_candidate = len(b" long_name")
    budget = len(prefix) + len(suffix) + longest_candidate + 7

    prompt = build_banking_prompt(
        _CharacterTokenizer(), labels, query, max_tokens=budget
    )

    assert prompt.token_ids == tuple(prefix + b"abcdxyz" + suffix)
    assert prompt.original_query_tokens == 26
    assert prompt.retained_query_tokens == 7
    assert len(prompt.token_ids) + prompt.max_candidate_tokens == budget


def test_no_space_for_nonempty_query_fails_closed() -> None:
    labels = ("a", "b")
    prefix = b"Labels: a b\nInput: "
    suffix = b"\nIntent:"
    with pytest.raises(BankingPromptError, match="query token"):
        build_banking_prompt(
            _CharacterTokenizer(),
            labels,
            "hello",
            max_tokens=len(prefix) + len(suffix) + len(b" a"),
        )


def test_one_query_token_budget_keeps_only_the_first_token() -> None:
    labels = ("a", "b")
    prefix = b"Labels: a b\nInput: "
    suffix = b"\nIntent:"
    budget = len(prefix) + len(suffix) + len(b" a") + 1

    prompt = build_banking_prompt(
        _CharacterTokenizer(), labels, "hello", max_tokens=budget
    )

    assert prompt.token_ids == tuple(prefix + b"h" + suffix)
    assert len(prompt.token_ids) + prompt.max_candidate_tokens == budget


def test_invalid_labels_and_blank_query_fail_closed() -> None:
    with pytest.raises(BankingPromptError, match="distinct canonical"):
        build_banking_prompt(_CharacterTokenizer(), ("A", "b"), "hello")
    with pytest.raises(BankingPromptError, match="distinct canonical"):
        build_banking_prompt(_CharacterTokenizer(), ("a", "a"), "hello")
    with pytest.raises(BankingPromptError, match="empty"):
        build_banking_prompt(_CharacterTokenizer(), ("a", "b"), " \r\n ")


def test_pinned_development_rows_respect_512_token_limit_if_available() -> None:
    source_raw = os.environ.get("ALUCLU_R0_BANKING_DEVELOPMENT")
    snapshot_raw = os.environ.get("ALUCLU_R0_SNAPSHOT")
    if not source_raw or not snapshot_raw:
        pytest.skip("pinned development source and tokenizer paths not supplied")
    source = Path(source_raw)
    snapshot = Path(snapshot_raw)
    if not source.is_dir() or not snapshot.is_dir():
        pytest.skip("pinned development source and tokenizer unavailable")
    transformers = pytest.importorskip("transformers")
    development = load_verified_banking77_development(source)
    tokenizer = transformers.AutoTokenizer.from_pretrained(
        str(snapshot), local_files_only=True, trust_remote_code=False
    )
    template = prepare_banking_prompt(tokenizer, development.labels)
    assert (len(template.prefix_ids), len(template.suffix_ids)) == (472, 4)
    assert (template.max_candidate_tokens, template.query_budget) == (17, 19)

    rows = development.split.train + development.split.dev
    prompts = [template.build(row.utterance) for row in rows]
    assert len(rows) == 9999
    assert all(len(p.token_ids) + p.max_candidate_tokens <= 512 for p in prompts)
    assert (
        sum(p.retained_query_tokens < p.original_query_tokens for p in prompts) == 1483
    )
