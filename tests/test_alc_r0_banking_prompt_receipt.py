from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import pytest

from aluclu.alc_r0.banking_preprocess import (
    BankingDevelopmentSplit,
    BankingPreparedRecord,
)
from aluclu.alc_r0.banking_prompt_receipt import (
    BankingPromptReceiptError,
    build_banking_prompt_candidate_receipt,
)
from aluclu.alc_r0.banking_source import (
    VerifiedBankingDevelopment,
    load_verified_banking77_development,
)
from aluclu.alc_r0.canonical import canonical_json_bytes

_REPO = Path(__file__).resolve().parents[1]
_CANDIDATE = _REPO / "results" / "alc_r0_banking77_prompt_candidate_20260925.json"


class _CharacterTokenizer:
    bos_token_id = None
    eos_token_id = None

    def encode(self, text: str, *, add_special_tokens: bool) -> list[int]:
        assert add_special_tokens is False
        return list(text.encode("ascii"))


def _development(
    train: tuple[BankingPreparedRecord, ...],
    dev: tuple[BankingPreparedRecord, ...],
) -> VerifiedBankingDevelopment:
    return VerifiedBankingDevelopment(
        ("a", "b"),
        BankingDevelopmentSplit(train, dev, 0, "d", "t", "v"),
        {"receipt_version": 1, "training_authority": False},
    )


def _record(source_id: str, utterance: str) -> BankingPreparedRecord:
    return BankingPreparedRecord(source_id, "a", utterance, "digest")


def test_receipt_binds_source_and_ordered_prompt_ids_without_raw_text() -> None:
    development = _development(
        (_record("train:0", "sensitive card detail"),),
        (_record("train:1", "other detail"),),
    )

    receipt = build_banking_prompt_candidate_receipt(
        development, _CharacterTokenizer(), max_tokens=80
    )

    assert receipt["status"] == "candidate-non-authorizing"
    assert receipt["training_authority"] is False
    assert receipt["train_rows"] == 1
    assert receipt["dev_rows"] == 1
    assert receipt["query_budget"] > 0
    assert b"sensitive" not in canonical_json_bytes(receipt)
    assert receipt == build_banking_prompt_candidate_receipt(
        development, _CharacterTokenizer(), max_tokens=80
    )


def test_prompt_root_changes_on_reorder_or_text_change() -> None:
    original = _development(
        (_record("train:0", "card detail"), _record("train:1", "other detail")),
        (_record("train:2", "dev detail"),),
    )
    reordered = _development(original.split.train[::-1], original.split.dev)
    changed = _development(
        (_record("train:0", "card changed"), original.split.train[1]),
        original.split.dev,
    )

    base = build_banking_prompt_candidate_receipt(
        original, _CharacterTokenizer(), max_tokens=80
    )
    reversed_receipt = build_banking_prompt_candidate_receipt(
        reordered, _CharacterTokenizer(), max_tokens=80
    )
    changed_receipt = build_banking_prompt_candidate_receipt(
        changed, _CharacterTokenizer(), max_tokens=80
    )

    assert (
        base["ordered_train_prompt_ids_sha256"]
        != reversed_receipt["ordered_train_prompt_ids_sha256"]
    )
    assert (
        base["ordered_train_prompt_ids_sha256"]
        != changed_receipt["ordered_train_prompt_ids_sha256"]
    )
    assert (
        base["ordered_dev_prompt_ids_sha256"]
        == changed_receipt["ordered_dev_prompt_ids_sha256"]
    )


def test_empty_split_fails_closed() -> None:
    with pytest.raises(BankingPromptReceiptError, match="nonempty"):
        build_banking_prompt_candidate_receipt(
            _development((_record("train:0", "hello"),), ()),
            _CharacterTokenizer(),
            max_tokens=80,
        )


def test_pinned_development_candidate_receipt_when_assets_supplied() -> None:
    source_raw = os.environ.get("ALUCLU_R0_BANKING_DEVELOPMENT")
    snapshot_raw = os.environ.get("ALUCLU_R0_SNAPSHOT")
    if not source_raw or not snapshot_raw:
        pytest.skip("pinned development source and tokenizer paths not supplied")
    transformers = pytest.importorskip("transformers")
    development = load_verified_banking77_development(Path(source_raw))
    tokenizer = transformers.AutoTokenizer.from_pretrained(
        snapshot_raw, local_files_only=True, trust_remote_code=False
    )

    receipt = build_banking_prompt_candidate_receipt(development, tokenizer)

    assert receipt["train_rows"] == 8030
    assert receipt["dev_rows"] == 1969
    assert receipt["train_truncated_rows"] + receipt["dev_truncated_rows"] == 1483
    assert receipt["prefix_tokens"] == 472
    assert receipt["suffix_tokens"] == 4
    assert receipt["max_candidate_tokens"] == 17
    assert receipt["query_budget"] == 19
    assert receipt["ordered_train_prompt_ids_sha256"] == (
        "8575d83d2f2356807bd35a51d7e6e02cfc47ee4da2c5c68d9715a443e368686a"
    )
    assert receipt["ordered_dev_prompt_ids_sha256"] == (
        "3885747387075700f6b292c55d66669bc607c425fcc6cd0a10642727a76d3cc4"
    )
    assert _CANDIDATE.read_bytes() == canonical_json_bytes(receipt) + b"\n"


def test_pinned_cli_emits_exact_canonical_receipt_when_assets_supplied() -> None:
    source_raw = os.environ.get("ALUCLU_R0_BANKING_DEVELOPMENT")
    snapshot_raw = os.environ.get("ALUCLU_R0_SNAPSHOT")
    if not source_raw or not snapshot_raw:
        pytest.skip("pinned development source and tokenizer paths not supplied")

    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "aluclu.alc_r0.banking_prompt_receipt",
            source_raw,
            snapshot_raw,
        ],
        cwd=_REPO,
        capture_output=True,
        check=True,
    )

    assert result.stdout == _CANDIDATE.read_bytes()
