from __future__ import annotations

import math
import os
from pathlib import Path

import pytest
import torch

from aluclu.alc_r0.defect_prompt import (
    DEFECT_LABELS,
    DefectPromptError,
    prepare_defect_prompt,
)


class _ByteTokenizer:
    bos_token_id = None
    eos_token_id = None

    def encode(self, text: str, *, add_special_tokens: bool) -> list[int]:
        assert add_special_tokens is False
        return list(text.encode("utf-8"))


def test_defect_prompt_normalizes_code_and_fixes_label_order() -> None:
    template = prepare_defect_prompt(_ByteTokenizer())
    prompt = template.build(b"\r\nint f() { return 1; } \r\n")

    assert DEFECT_LABELS == ("safe", "vulnerable")
    assert prompt.normalized_code == "int f() { return 1; }"
    assert bytes(prompt.token_ids) == (
        b"Labels: safe vulnerable\nInput: int f() { return 1; }\nVerdict:"
    )
    assert template.safe_candidate_ids == tuple(b" safe")
    assert template.vulnerable_candidate_ids == tuple(b" vulnerable")
    assert len(prompt.token_ids) + template.max_candidate_tokens <= 512


def test_code_truncation_reserves_answer_and_longest_candidate() -> None:
    prefix = b"Labels: safe vulnerable\nInput: "
    suffix = b"\nVerdict:"
    max_tokens = len(prefix) + len(suffix) + len(b" vulnerable") + 7
    template = prepare_defect_prompt(_ByteTokenizer(), max_tokens=max_tokens)

    prompt = template.build(b"abcdefghijklmnopqrstuvwxyz")

    assert prompt.token_ids == tuple(prefix + b"abcdxyz" + suffix)
    assert prompt.original_code_tokens == 26
    assert prompt.retained_code_tokens == 7
    assert len(prompt.token_ids) + template.max_candidate_tokens == max_tokens


def test_training_labels_mask_every_prompt_and_padding_token() -> None:
    template = prepare_defect_prompt(_ByteTokenizer())
    prompt = template.build(b"int f() { return 0; }")
    pad_to = len(prompt.token_ids) + len(template.safe_candidate_ids) + 3

    labels = template.training_labels(prompt, "safe", pad_to=pad_to)

    assert labels == (
        (-100,) * len(prompt.token_ids) + template.safe_candidate_ids + (-100,) * 3
    )
    with pytest.raises(DefectPromptError, match="unknown defect label"):
        template.training_labels(prompt, "SAFE")


def test_each_candidate_gets_a_complete_uncached_forward() -> None:
    template = prepare_defect_prompt(_ByteTokenizer())
    prompt = template.build(b"int f() { return 0; }")
    calls: list[tuple[int, ...]] = []

    def forward(input_ids: tuple[int, ...]) -> torch.Tensor:
        calls.append(input_ids)
        return torch.zeros((len(input_ids), 256), dtype=torch.float32)

    label, scores = template.rank(prompt, forward)

    assert calls == [
        prompt.token_ids + template.safe_candidate_ids,
        prompt.token_ids + template.vulnerable_candidate_ids,
    ]
    assert label == "safe"  # equal mean scores use UTF-8 lexical tie order
    assert scores["safe"] == scores["vulnerable"]


@pytest.mark.parametrize("code", [b"", b" \r\n ", b"\xff"])
def test_empty_or_invalid_utf8_code_fails_closed(code: bytes) -> None:
    template = prepare_defect_prompt(_ByteTokenizer())

    with pytest.raises(DefectPromptError, match="code"):
        template.build(code)


def test_no_room_for_one_code_token_fails_closed() -> None:
    prefix = b"Labels: safe vulnerable\nInput: "
    suffix = b"\nVerdict:"
    with pytest.raises(DefectPromptError, match="code token"):
        prepare_defect_prompt(
            _ByteTokenizer(),
            max_tokens=len(prefix) + len(suffix) + len(b" vulnerable"),
        )


def test_special_token_inside_prompt_fails_closed() -> None:
    class _BadTokenizer(_ByteTokenizer):
        eos_token_id = ord(":")

    with pytest.raises(DefectPromptError, match="EOS"):
        prepare_defect_prompt(_BadTokenizer())


def test_pinned_smolllm2_scores_both_defect_candidates_if_available() -> None:
    snapshot_raw = os.environ.get("ALUCLU_R0_SNAPSHOT")
    if not snapshot_raw:
        pytest.skip("pinned offline model snapshot path not supplied")
    snapshot = Path(snapshot_raw)
    if not snapshot.is_dir():
        pytest.skip("pinned offline model snapshot unavailable")
    from transformers import AutoTokenizer

    from aluclu.alc_r0.host import load_verified_host

    tokenizer = AutoTokenizer.from_pretrained(
        str(snapshot), local_files_only=True, trust_remote_code=False
    )
    template = prepare_defect_prompt(tokenizer)
    prompt = template.build(b"int safe_add(int a, int b) { return a + b; }")
    host = load_verified_host(
        snapshot,
        environment={
            "HF_HUB_OFFLINE": "1",
            "TRANSFORMERS_OFFLINE": "1",
            "HF_DATASETS_OFFLINE": "1",
        },
        device="cpu",
        dtype=torch.float32,
    )

    def forward(input_ids: tuple[int, ...]) -> torch.Tensor:
        ids = torch.tensor([input_ids], dtype=torch.long)
        with torch.inference_mode():
            output = host.model(input_ids=ids, use_cache=False)
        return output.logits[0]

    label, scores = template.rank(prompt, forward)

    assert label in DEFECT_LABELS
    assert set(scores) == set(DEFECT_LABELS)
    assert all(math.isfinite(value) for value in scores.values())
    assert host.trainable_parameter_count == 0
    assert len(prompt.token_ids) + template.max_candidate_tokens <= 512
