from __future__ import annotations

import hashlib
import math
import os
from pathlib import Path

import pytest
import torch

from aluclu.alc_r0.banking_scoring import (
    BankingScoringError,
    candidate_token_ids,
    candidate_token_map_root,
    masked_training_labels,
    rank_banking_candidates,
    score_banking_candidate,
)
from aluclu.alc_r0.banking_source import load_verified_banking77_development
from aluclu.alc_r0.canonical import canonical_json_bytes


class _Tokenizer:
    bos_token_id = 0
    eos_token_id = 0

    def __init__(self) -> None:
        self.calls: list[tuple[str, bool]] = []

    def encode(self, text: str, *, add_special_tokens: bool) -> list[int]:
        self.calls.append((text, add_special_tokens))
        return [2, 3] if text == " card_arrival" else [4]


def test_candidate_encoding_uses_exact_one_leading_space_without_specials() -> None:
    tokenizer = _Tokenizer()

    assert candidate_token_ids(tokenizer, "card_arrival") == (2, 3)
    assert tokenizer.calls == [(" card_arrival", False)]
    with pytest.raises(BankingScoringError, match="canonical lowercase"):
        candidate_token_ids(tokenizer, "Card_Arrival")


def test_candidate_token_map_root_binds_order_and_exact_ids() -> None:
    tokenizer = _Tokenizer()
    labels = ("card_arrival", "cash_withdrawal")
    expected = [
        {"label": "card_arrival", "token_ids": [2, 3]},
        {"label": "cash_withdrawal", "token_ids": [4]},
    ]
    assert (
        candidate_token_map_root(tokenizer, labels)
        == hashlib.sha256(canonical_json_bytes(expected)).hexdigest()
    )
    assert candidate_token_map_root(tokenizer, labels[::-1]) != (
        candidate_token_map_root(tokenizer, labels)
    )


def test_training_labels_mask_prompt_and_padding_but_not_candidate() -> None:
    assert masked_training_labels((8, 9), (2, 3), pad_to=7) == (
        -100,
        -100,
        2,
        3,
        -100,
        -100,
        -100,
    )
    with pytest.raises(BankingScoringError, match="candidate"):
        masked_training_labels((8,), (), pad_to=2)


def test_conditional_log_likelihood_mean_uses_only_candidate_predictions() -> None:
    # At prompt-final position 1: p(token 1) = 2/4.
    # At candidate-first position 2: p(token 2) = 3/5.
    logits = torch.tensor(
        [
            [100.0, -100.0, -100.0],  # prompt-only prediction ignored
            [0.0, math.log(2.0), 0.0],
            [0.0, 0.0, math.log(3.0)],
            [0.0, 0.0, 0.0],  # candidate-final prediction ignored
        ],
        dtype=torch.float64,
    )

    score = score_banking_candidate(logits, prompt_length=2, candidate_ids=(1, 2))

    assert score == pytest.approx((math.log(2 / 4) + math.log(3 / 5)) / 2)


def test_each_candidate_requires_its_own_complete_forward_logits() -> None:
    labels = ("a", "b")
    candidates = {"a": (1, 2), "b": (2,)}
    seen: list[tuple[int, ...]] = []

    def forward(ids: tuple[int, ...]) -> torch.Tensor:
        seen.append(ids)
        return torch.zeros((len(ids), 4), dtype=torch.float64)

    prediction, scores = rank_banking_candidates((3, 3), labels, candidates, forward)

    assert seen == [(3, 3, 1, 2), (3, 3, 2)]
    assert prediction == "a"  # exact score tie breaks by UTF-8 label bytes
    assert scores == {
        "a": pytest.approx(-math.log(4)),
        "b": pytest.approx(-math.log(4)),
    }


def test_wrong_logits_shape_and_nonfinite_values_fail_closed() -> None:
    with pytest.raises(BankingScoringError, match="shape"):
        score_banking_candidate(torch.zeros((1, 3)), 2, (1,))
    with pytest.raises(BankingScoringError, match="nonfinite"):
        score_banking_candidate(torch.tensor([[0.0, math.nan], [0.0, 0.0]]), 1, (1,))
    with pytest.raises(BankingScoringError, match="token ID"):
        score_banking_candidate(torch.zeros((2, 3)), 1, (3,))


def test_duplicate_labels_and_missing_candidate_map_fail_closed() -> None:
    with pytest.raises(BankingScoringError, match="distinct"):
        rank_banking_candidates(
            (1,), ("a", "a"), {"a": (1,)}, lambda _: torch.zeros((2, 3))
        )
    with pytest.raises(BankingScoringError, match="candidate map"):
        rank_banking_candidates(
            (1,), ("a", "b"), {"a": (1,)}, lambda _: torch.zeros((2, 3))
        )


def test_pinned_real_tokenizer_candidate_map_root_when_snapshot_is_present() -> None:
    source = Path(
        os.environ.get(
            "ALUCLU_R0_BANKING_DEVELOPMENT",
            "C:/Users/kaann/AppData/Local/ALUCLU/research/alc-r0-smollm2-135m-v1/"
            "datasets/banking77/9d081458ff52e53cf7e848f414e6e9344e4e6696",
        )
    )
    snapshot = Path(
        os.environ.get(
            "ALUCLU_R0_SNAPSHOT",
            "C:/Users/kaann/AppData/Local/ALUCLU/research/alc-r0-smollm2-135m-v1/"
            "model/SmolLM2-135M-93efa2f",
        )
    )
    if not source.is_dir() or not snapshot.is_dir():
        pytest.skip("pinned Banking77 development source and tokenizer unavailable")
    transformers = pytest.importorskip("transformers")
    labels = load_verified_banking77_development(source).labels
    tokenizer = transformers.AutoTokenizer.from_pretrained(
        str(snapshot), local_files_only=True, trust_remote_code=False
    )

    assert candidate_token_map_root(tokenizer, labels) == (
        "ce33efdc137af58036402da1fff96ccdcea9663843fa564c6f64def7d0e31878"
    )
    assert candidate_token_ids(tokenizer, labels[0]) == (3421, 79, 2110, 2264)
    assert candidate_token_ids(tokenizer, labels[-1]) == (1798, 79, 22610)
