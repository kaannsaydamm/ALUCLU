from __future__ import annotations

from dataclasses import dataclass

import torch
from torch import Tensor


@dataclass(frozen=True)
class MQARBatch:
    input_ids: Tensor
    labels: Tensor
    loss_mask: Tensor
    answer_positions: Tensor
    answer_tokens: Tensor
    vocab_size: int


def generate_mqar_batch(
    batch_size: int,
    n_pairs: int,
    n_queries: int,
    *,
    key_vocab_size: int,
    value_vocab_size: int,
    device: torch.device | str = "cpu",
    generator: torch.Generator | None = None,
) -> MQARBatch:
    """Generate an unambiguous diagnostic MQAR batch.

    Keys and values are sampled without replacement within each example.
    This compact diagnostic is intentionally not labeled as the historical
    Zoology protocol, whose gaps, filler tokens, dataset caching, and sweep
    policy are different.
    """

    positive = {
        "batch_size": batch_size,
        "n_pairs": n_pairs,
        "n_queries": n_queries,
        "key_vocab_size": key_vocab_size,
        "value_vocab_size": value_vocab_size,
    }
    for name, value in positive.items():
        if value < 1:
            raise ValueError(f"{name} must be positive")
    if n_queries > n_pairs:
        raise ValueError("n_queries cannot exceed n_pairs")
    if n_pairs > key_vocab_size:
        raise ValueError("key vocabulary is too small for unique keys")
    if n_pairs > value_vocab_size:
        raise ValueError("value vocabulary is too small for unique values")

    device = torch.device(device)
    key_order = torch.rand(
        batch_size,
        key_vocab_size,
        device=device,
        generator=generator,
    ).argsort(dim=1)
    value_order = torch.rand(
        batch_size,
        value_vocab_size,
        device=device,
        generator=generator,
    ).argsort(dim=1)
    keys = key_order[:, :n_pairs] + 1
    values = value_order[:, :n_pairs] + key_vocab_size + 1

    context = torch.empty(
        batch_size,
        2 * n_pairs,
        device=device,
        dtype=torch.long,
    )
    context[:, 0::2] = keys
    context[:, 1::2] = values

    query_order = torch.rand(
        batch_size,
        n_pairs,
        device=device,
        generator=generator,
    ).argsort(dim=1)
    query_indices = query_order[:, :n_queries]
    query_keys = keys.gather(1, query_indices)
    answer_tokens = values.gather(1, query_indices)
    query_block = torch.empty(
        batch_size,
        2 * n_queries,
        device=device,
        dtype=torch.long,
    )
    query_block[:, 0::2] = query_keys
    query_block[:, 1::2] = answer_tokens

    separator = key_vocab_size + value_vocab_size + 1
    separator_column = torch.full(
        (batch_size, 1),
        separator,
        device=device,
        dtype=torch.long,
    )
    input_ids = torch.cat((context, separator_column, query_block), dim=1)
    answer_offset = 2 * n_pairs + 2
    answer_positions = (
        torch.arange(
            answer_offset,
            answer_offset + 2 * n_queries,
            2,
            device=device,
            dtype=torch.long,
        )
        .view(1, n_queries)
        .expand(batch_size, n_queries)
    )
    loss_mask = torch.zeros_like(input_ids, dtype=torch.bool)
    loss_mask.scatter_(1, answer_positions, True)
    vocab_size = separator + 1
    return MQARBatch(
        input_ids=input_ids,
        labels=input_ids.clone(),
        loss_mask=loss_mask,
        answer_positions=answer_positions,
        answer_tokens=answer_tokens,
        vocab_size=vocab_size,
    )


def mqar_accuracy(logits: Tensor, batch: MQARBatch) -> Tensor:
    if logits.ndim != 3 or logits.shape[:2] != batch.input_ids.shape:
        raise ValueError("logits shape does not match MQAR batch")
    query_positions = batch.answer_positions - 1
    batch_indices = torch.arange(
        logits.shape[0],
        device=logits.device,
    ).view(-1, 1)
    selected = logits[batch_indices, query_positions]
    predictions = selected.argmax(dim=-1)
    return (predictions == batch.answer_tokens).to(torch.float32).mean()
