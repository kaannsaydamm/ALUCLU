from __future__ import annotations

import pytest
from test_alc_r0_primevul_pair_clone_full import _fixture

from aluclu.alc_r0.paired_prompt_contrast import (
    PairedPromptContrastError,
    audit_paired_prompt_contrast,
    run_pinned_paired_prompt_contrast,
)


class _ByteTokenizer:
    bos_token_id = None
    eos_token_id = None

    def encode(self, text: str, *, add_special_tokens: bool) -> list[int]:
        assert add_special_tokens is False
        return list(text.encode("utf-8"))


def test_pair_prompt_collapse_and_retained_contrast_are_distinct() -> None:
    pairs = (
        ("AAAA" + "x" * 20 + "ZZZZ", "AAAA" + "y" * 20 + "ZZZZ"),
        ("BAAA" + "x" * 20 + "ZZZZ", "CAAA" + "x" * 20 + "ZZZZ"),
        ("abc", "abd"),
    )
    result = audit_paired_prompt_contrast(pairs, _ByteTokenizer(), max_tokens=59)

    assert result["pairs"] == 3
    assert result["collapsed_pairs"] == 1
    assert result["both_truncated_pairs"] == 2
    assert result["neither_truncated_pairs"] == 1
    assert result["one_truncated_pairs"] == 0
    assert result["training_authority"] is False
    assert result["held_out_data_present"] is False
    assert len(result["ordered_pair_prompt_ids_sha256"]) == 64
    assert (
        result["ordered_pair_prompt_ids_sha256"]
        != audit_paired_prompt_contrast(
            tuple(reversed(pairs)), _ByteTokenizer(), max_tokens=59
        )["ordered_pair_prompt_ids_sha256"]
    )
    assert "AAAA" not in str(result)


def test_one_sided_truncation_is_counted() -> None:
    result = audit_paired_prompt_contrast(
        (("a" * 30, "short"),), _ByteTokenizer(), max_tokens=59
    )

    assert result["pairs"] == 1
    assert result["one_truncated_pairs"] == 1
    assert result["both_truncated_pairs"] == 0
    assert result["neither_truncated_pairs"] == 0
    assert result["collapsed_pairs"] == 0


def test_more_context_can_resolve_exact_middle_only_pair_collision() -> None:
    pair = (("AAAA" + "x" * 20 + "ZZZZ", "AAAA" + "y" * 20 + "ZZZZ"),)

    short = audit_paired_prompt_contrast(pair, _ByteTokenizer(), max_tokens=59)
    long = audit_paired_prompt_contrast(pair, _ByteTokenizer(), max_tokens=1024)

    assert short["collapsed_pairs"] == 1
    assert long["collapsed_pairs"] == 0
    assert long["neither_truncated_pairs"] == 1


@pytest.mark.parametrize(
    "pairs",
    [(), (("same", "same"),), (("valid", ""),), (("valid", 5),)],
)
def test_invalid_or_uninformative_pair_fails_closed(pairs: tuple) -> None:
    with pytest.raises(PairedPromptContrastError):
        audit_paired_prompt_contrast(pairs, _ByteTokenizer(), max_tokens=59)


def test_fixture_runner_binds_verified_sources_and_emits_only_aggregates(
    tmp_path,
) -> None:
    full, paired, source_expectation, pair_expectation = _fixture(tmp_path)

    receipt = run_pinned_paired_prompt_contrast(
        full,
        paired,
        _ByteTokenizer(),
        model_inventory_sha256="a" * 64,
        source_expectation=source_expectation,
        pair_expectation=pair_expectation,
    )

    assert receipt["source_scope"] == "fixture"
    assert receipt["train"]["pairs"] == 1
    assert receipt["validation"]["pairs"] == 1
    assert receipt["train"]["collapsed_pairs"] == 0
    assert receipt["training_authority"] is False
    assert receipt["held_out_data_present"] is False
    assert "red blue" not in str(receipt)
    assert "primevul:" not in str(receipt)


def test_fixture_runner_records_requested_common_budget(tmp_path) -> None:
    full, paired, source_expectation, pair_expectation = _fixture(tmp_path)
    default_receipt = run_pinned_paired_prompt_contrast(
        full,
        paired,
        _ByteTokenizer(),
        model_inventory_sha256="a" * 64,
        source_expectation=source_expectation,
        pair_expectation=pair_expectation,
    )
    receipt = run_pinned_paired_prompt_contrast(
        full,
        paired,
        _ByteTokenizer(),
        model_inventory_sha256="a" * 64,
        max_common_tokens=1024,
        source_expectation=source_expectation,
        pair_expectation=pair_expectation,
    )

    assert default_receipt["max_common_tokens"] == 512
    assert default_receipt["train"] == audit_paired_prompt_contrast(
        (("red blue green yellow orange", "alpha beta gamma delta epsilon"),),
        _ByteTokenizer(),
        max_tokens=512,
    )
    assert receipt["max_common_tokens"] == 1024
    assert receipt["train"] == audit_paired_prompt_contrast(
        (("red blue green yellow orange", "alpha beta gamma delta epsilon"),),
        _ByteTokenizer(),
        max_tokens=1024,
    )


@pytest.mark.parametrize("budget", [511, 1536, 8193, True, "1024"])
def test_fixture_runner_rejects_undeclared_common_budget(tmp_path, budget) -> None:
    full, paired, source_expectation, pair_expectation = _fixture(tmp_path)

    with pytest.raises(PairedPromptContrastError, match="outside declared grid"):
        run_pinned_paired_prompt_contrast(
            full,
            paired,
            _ByteTokenizer(),
            model_inventory_sha256="a" * 64,
            max_common_tokens=budget,
            source_expectation=source_expectation,
            pair_expectation=pair_expectation,
        )


def test_fixture_runner_rejects_changed_paired_bytes(tmp_path) -> None:
    full, paired, source_expectation, pair_expectation = _fixture(tmp_path)
    path = paired / "primevul_train_paired.jsonl"
    path.write_bytes(path.read_bytes().replace(b"red", b"RED", 1))

    with pytest.raises(ValueError):
        run_pinned_paired_prompt_contrast(
            full,
            paired,
            _ByteTokenizer(),
            model_inventory_sha256="a" * 64,
            source_expectation=source_expectation,
            pair_expectation=pair_expectation,
        )
