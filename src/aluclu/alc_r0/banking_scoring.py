"""Reference candidate-label scoring for the frozen Banking77 R0 target.

The caller supplies one full, uncached forward pass per complete candidate.
This module deliberately does not read a dataset or confer training authority.
"""

from __future__ import annotations

import hashlib
import math
import re
from collections.abc import Callable, Mapping, Sequence
from typing import Protocol

import torch

from .canonical import canonical_json_bytes

_CANONICAL_LABEL = re.compile(r"[a-z0-9_]+\??\Z")
_IGNORE_INDEX = -100


class BankingScoringError(ValueError):
    """Candidate tokenization or conditional scoring violates the R0 contract."""


class CandidateTokenizer(Protocol):
    @property
    def bos_token_id(self) -> int | None: ...

    @property
    def eos_token_id(self) -> int | None: ...

    def encode(self, text: str, *, add_special_tokens: bool) -> Sequence[int]: ...


def _validate_ids(ids: Sequence[int], *, field: str) -> tuple[int, ...]:
    if not ids or any(type(token_id) is not int or token_id < 0 for token_id in ids):
        raise BankingScoringError(f"{field} must contain nonnegative token IDs")
    return tuple(ids)


def candidate_token_ids(tokenizer: CandidateTokenizer, label: str) -> tuple[int, ...]:
    """Encode exactly one ASCII space and one canonical lowercase label."""

    if not isinstance(label, str) or not _CANONICAL_LABEL.fullmatch(label):
        raise BankingScoringError("candidate requires a canonical lowercase label")
    ids = _validate_ids(
        tokenizer.encode(" " + label, add_special_tokens=False), field="candidate"
    )
    specials = {tokenizer.bos_token_id, tokenizer.eos_token_id} - {None}
    if any(token_id in specials for token_id in ids):
        raise BankingScoringError("candidate contains a BOS or EOS token")
    return ids


def candidate_token_map_root(
    tokenizer: CandidateTokenizer, labels: Sequence[str]
) -> str:
    """Bind ordered canonical labels to exact no-special leading-space IDs."""

    if not labels or len(set(labels)) != len(labels):
        raise BankingScoringError("labels must be distinct")
    rows = [
        {"label": label, "token_ids": list(candidate_token_ids(tokenizer, label))}
        for label in labels
    ]
    return hashlib.sha256(canonical_json_bytes(rows)).hexdigest()


def masked_training_labels(
    prompt_ids: Sequence[int],
    candidate_ids: Sequence[int],
    *,
    pad_to: int | None = None,
) -> tuple[int, ...]:
    """Mask every prompt/padding token; loss is only on candidate IDs."""

    prompt = _validate_ids(prompt_ids, field="prompt")
    candidate = _validate_ids(candidate_ids, field="candidate")
    size = len(prompt) + len(candidate)
    if pad_to is not None and (type(pad_to) is not int or pad_to < size):
        raise BankingScoringError("pad_to must cover the prompt and candidate")
    return (
        (_IGNORE_INDEX,) * len(prompt)
        + candidate
        + (_IGNORE_INDEX,) * ((pad_to or size) - size)
    )


def score_banking_candidate(
    logits: torch.Tensor, prompt_length: int, candidate_ids: Sequence[int]
) -> float:
    """Mean next-token log probability over the complete candidate only."""

    candidate = _validate_ids(candidate_ids, field="candidate")
    if type(prompt_length) is not int or prompt_length < 1:
        raise BankingScoringError("prompt length must be positive")
    if (
        not isinstance(logits, torch.Tensor)
        or logits.ndim != 2
        or logits.shape[0] != prompt_length + len(candidate)
        or logits.shape[1] < 1
    ):
        raise BankingScoringError("logits shape must be [prompt+candidate, vocab]")
    if any(token_id >= logits.shape[1] for token_id in candidate):
        raise BankingScoringError("candidate token ID exceeds logits vocabulary")
    if not torch.isfinite(logits).all().item():
        raise BankingScoringError("nonfinite candidate forward logits")
    rows = logits[prompt_length - 1 : prompt_length - 1 + len(candidate)].to(
        torch.float64
    )
    target = torch.tensor(candidate, device=rows.device, dtype=torch.long)
    log_probs = rows.gather(1, target[:, None]).squeeze(1) - torch.logsumexp(
        rows, dim=1
    )
    score = float(log_probs.mean().item())
    if not math.isfinite(score):
        raise BankingScoringError("nonfinite candidate score")
    return score


def rank_banking_candidates(
    prompt_ids: Sequence[int],
    labels: Sequence[str],
    candidate_ids_by_label: Mapping[str, Sequence[int]],
    forward_logits: Callable[[tuple[int, ...]], torch.Tensor],
) -> tuple[str, dict[str, float]]:
    """Rescore every complete label separately; tie-break by UTF-8 label bytes."""

    prompt = _validate_ids(prompt_ids, field="prompt")
    if (
        not labels
        or len(set(labels)) != len(labels)
        or any(
            not isinstance(label, str) or not _CANONICAL_LABEL.fullmatch(label)
            for label in labels
        )
    ):
        raise BankingScoringError("labels must be distinct canonical lowercase text")
    if set(candidate_ids_by_label) != set(labels):
        raise BankingScoringError("candidate map must exactly match labels")
    scores: dict[str, float] = {}
    for label in labels:
        candidate = _validate_ids(candidate_ids_by_label[label], field="candidate")
        logits = forward_logits(prompt + candidate)
        scores[label] = score_banking_candidate(logits, len(prompt), candidate)
    winner = min(scores, key=lambda label: (-scores[label], label.encode("utf-8")))
    return winner, scores
