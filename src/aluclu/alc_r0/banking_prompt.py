"""Non-authorizing reference prompt for the frozen Banking77 interface.

The shared prompt is the same in every comparison arm. Candidate IDs are
appended separately by the scorer; no dataset or held-out split is read here.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass

from .banking_preprocess import normalize_banking_utterance
from .banking_scoring import (
    BankingScoringError,
    CandidateTokenizer,
    candidate_token_ids,
)


class BankingPromptError(ValueError):
    """Prompt, query, or fixed-vocabulary tokenization violates the R0 budget."""


def _ids(tokenizer: CandidateTokenizer, text: str, *, field: str) -> tuple[int, ...]:
    encoded = tokenizer.encode(text, add_special_tokens=False)
    if not encoded or any(
        type(token_id) is not int or token_id < 0 for token_id in encoded
    ):
        raise BankingPromptError(f"{field} must encode to nonempty token IDs")
    specials = {tokenizer.bos_token_id, tokenizer.eos_token_id} - {None}
    if any(token_id in specials for token_id in encoded):
        raise BankingPromptError(f"{field} contains a BOS or EOS token")
    return tuple(encoded)


@dataclass(frozen=True)
class BankingPrompt:
    token_ids: tuple[int, ...]
    normalized_query: str
    original_query_tokens: int
    retained_query_tokens: int
    max_candidate_tokens: int


@dataclass(frozen=True)
class BankingPromptTemplate:
    tokenizer: CandidateTokenizer
    prefix_ids: tuple[int, ...]
    suffix_ids: tuple[int, ...]
    max_candidate_tokens: int
    query_budget: int
    max_tokens: int

    def build(self, utterance: str) -> BankingPrompt:
        """Keep the first ceil(n/2) and last floor(n/2) query IDs if needed."""

        normalized = normalize_banking_utterance(utterance)
        if not normalized:
            raise BankingPromptError("query is empty after normalization")
        try:
            normalized.encode("utf-8", errors="strict")
        except UnicodeEncodeError as exc:
            raise BankingPromptError("query is not valid UTF-8 text") from exc
        query_ids = _ids(self.tokenizer, normalized, field="query")
        original_length = len(query_ids)
        if original_length > self.query_budget:
            head = (self.query_budget + 1) // 2
            tail = self.query_budget // 2
            query_ids = query_ids[:head] + (query_ids[-tail:] if tail else ())
        prompt_ids = self.prefix_ids + query_ids + self.suffix_ids
        if len(prompt_ids) + self.max_candidate_tokens > self.max_tokens:
            raise BankingPromptError("prompt exceeds common sequence budget")
        return BankingPrompt(
            prompt_ids,
            normalized,
            original_length,
            len(query_ids),
            self.max_candidate_tokens,
        )


def prepare_banking_prompt(
    tokenizer: CandidateTokenizer,
    labels: Sequence[str],
    *,
    max_tokens: int = 512,
) -> BankingPromptTemplate:
    """Freeze the ordered label vocabulary and reserve the longest candidate."""

    if (
        not labels
        or any(not isinstance(label, str) for label in labels)
        or len(set(labels)) != len(labels)
    ):
        raise BankingPromptError("labels must be distinct canonical lowercase text")
    try:
        candidate_lengths = [
            len(candidate_token_ids(tokenizer, label)) for label in labels
        ]
    except (BankingScoringError, TypeError) as exc:
        raise BankingPromptError(
            "labels must be distinct canonical lowercase text"
        ) from exc
    if type(max_tokens) is not int or max_tokens < 1:
        raise BankingPromptError("max_tokens must be a positive integer")
    prefix = _ids(
        tokenizer, "Labels: " + " ".join(labels) + "\nInput: ", field="prefix"
    )
    suffix = _ids(tokenizer, "\nIntent:", field="answer boundary")
    max_candidate = max(candidate_lengths)
    query_budget = max_tokens - len(prefix) - len(suffix) - max_candidate
    if query_budget < 1:
        raise BankingPromptError(
            "no query token fits after label and candidate reserve"
        )
    return BankingPromptTemplate(
        tokenizer, prefix, suffix, max_candidate, query_budget, max_tokens
    )


def build_banking_prompt(
    tokenizer: CandidateTokenizer,
    labels: Sequence[str],
    utterance: str,
    *,
    max_tokens: int = 512,
) -> BankingPrompt:
    """Convenience wrapper; prepare once for full-dataset operation."""

    return prepare_banking_prompt(tokenizer, labels, max_tokens=max_tokens).build(
        utterance
    )
