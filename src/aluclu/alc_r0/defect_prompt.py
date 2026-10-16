"""Non-authorizing candidate reference prompt for the family-B defect task.

This source-agnostic interface can consume already-verified C/C++ function
bytes from a development source. It does not acquire data or train a model.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

import torch

from .banking_scoring import (
    BankingScoringError,
    CandidateTokenizer,
    candidate_token_ids,
    masked_training_labels,
    rank_banking_candidates,
)
from .devign_preprocess import DevignPreprocessError, normalize_devign_code

DEFECT_LABELS = ("safe", "vulnerable")
_PREFIX = "Labels: safe vulnerable\nInput: "
_SUFFIX = "\nVerdict:"


class DefectPromptError(ValueError):
    """Code, label, or tokenization violates the family-B prompt contract."""


def _ids(tokenizer: CandidateTokenizer, text: str, *, field: str) -> tuple[int, ...]:
    encoded = tokenizer.encode(text, add_special_tokens=False)
    if not encoded or any(
        type(token_id) is not int or token_id < 0 for token_id in encoded
    ):
        raise DefectPromptError(f"{field} must encode to nonempty token IDs")
    specials = {tokenizer.bos_token_id, tokenizer.eos_token_id} - {None}
    if any(token_id in specials for token_id in encoded):
        raise DefectPromptError(f"{field} contains a BOS or EOS token")
    return tuple(encoded)


@dataclass(frozen=True)
class DefectPrompt:
    token_ids: tuple[int, ...]
    normalized_code: str
    original_code_tokens: int
    retained_code_tokens: int


@dataclass(frozen=True)
class DefectPromptTemplate:
    tokenizer: CandidateTokenizer
    prefix_ids: tuple[int, ...]
    suffix_ids: tuple[int, ...]
    safe_candidate_ids: tuple[int, ...]
    vulnerable_candidate_ids: tuple[int, ...]
    max_candidate_tokens: int
    code_budget: int
    max_tokens: int

    def build(self, code: bytes) -> DefectPrompt:
        """Normalize and retain token-ID head/tail without losing the boundary."""

        try:
            normalized = normalize_devign_code(code)
        except DevignPreprocessError as exc:
            raise DefectPromptError("code failed frozen normalization") from exc
        code_ids = _ids(self.tokenizer, normalized, field="code")
        original_length = len(code_ids)
        if original_length > self.code_budget:
            head = (self.code_budget + 1) // 2
            tail = self.code_budget // 2
            code_ids = code_ids[:head] + (code_ids[-tail:] if tail else ())
        prompt_ids = self.prefix_ids + code_ids + self.suffix_ids
        if len(prompt_ids) + self.max_candidate_tokens > self.max_tokens:
            raise DefectPromptError("prompt exceeds common sequence budget")
        return DefectPrompt(prompt_ids, normalized, original_length, len(code_ids))

    def training_labels(
        self, prompt: DefectPrompt, label: str, *, pad_to: int | None = None
    ) -> tuple[int, ...]:
        """Expose only the intended label tokens to the training loss."""

        if label not in DEFECT_LABELS:
            raise DefectPromptError("unknown defect label")
        candidate = (
            self.safe_candidate_ids
            if label == "safe"
            else self.vulnerable_candidate_ids
        )
        try:
            return masked_training_labels(prompt.token_ids, candidate, pad_to=pad_to)
        except BankingScoringError as exc:
            raise DefectPromptError("invalid defect training labels") from exc

    def rank(
        self,
        prompt: DefectPrompt,
        forward_logits: Callable[[tuple[int, ...]], torch.Tensor],
    ) -> tuple[str, dict[str, float]]:
        """Score both complete candidates with independent uncached forwards."""

        return rank_banking_candidates(
            prompt.token_ids,
            DEFECT_LABELS,
            {
                "safe": self.safe_candidate_ids,
                "vulnerable": self.vulnerable_candidate_ids,
            },
            forward_logits,
        )


def prepare_defect_prompt(
    tokenizer: CandidateTokenizer, *, max_tokens: int = 512
) -> DefectPromptTemplate:
    """Fix ordered labels and reserve the longest complete candidate."""

    if type(max_tokens) is not int or max_tokens < 1:
        raise DefectPromptError("max_tokens must be a positive integer")
    try:
        safe_ids = candidate_token_ids(tokenizer, DEFECT_LABELS[0])
        vulnerable_ids = candidate_token_ids(tokenizer, DEFECT_LABELS[1])
    except BankingScoringError as exc:
        raise DefectPromptError("defect candidate tokenization failed") from exc
    prefix = _ids(tokenizer, _PREFIX, field="prefix")
    suffix = _ids(tokenizer, _SUFFIX, field="answer boundary")
    max_candidate = max(len(safe_ids), len(vulnerable_ids))
    code_budget = max_tokens - len(prefix) - len(suffix) - max_candidate
    if code_budget < 1:
        raise DefectPromptError("no code token fits after candidate reserve")
    return DefectPromptTemplate(
        tokenizer,
        prefix,
        suffix,
        safe_ids,
        vulnerable_ids,
        max_candidate,
        code_budget,
        max_tokens,
    )
