from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np
import torch
import torch.nn.functional as F
from torch import Tensor

ZOOLOGY_ICLR24_COMMIT = "de4e258784224e09909c257ff3ea040f089ed660"
ZOOLOGY_ICLR24_RAW_PROTOCOL_ID = "aluclu_zoology_mqar_iclr24_raw_v1"
ZOOLOGY_ICLR24_REPAIRED_PROTOCOL_ID = "aluclu_zoology_mqar_iclr24_repaired_v1"
ZOOLOGY_MQAR_IGNORE_INDEX = -100


@dataclass(frozen=True)
class ZoologyMQARConfig:
    """Configuration for one split of the tagged Zoology MQAR generator.

    The default filler policy matches the ICLR-2024 Figure 2 experiment rather
    than the generic upstream function default. Labels are already aligned with
    query-token positions and must not be shifted again by a training pipeline.
    """

    num_examples: int
    input_seq_len: int
    num_kv_pairs: int
    vocab_size: int = 8_192
    seed: int = 0
    power_a: float = 0.01
    random_non_queries: bool = False

    def __post_init__(self) -> None:
        integer_fields = {
            "num_examples": self.num_examples,
            "input_seq_len": self.input_seq_len,
            "num_kv_pairs": self.num_kv_pairs,
            "vocab_size": self.vocab_size,
            "seed": self.seed,
        }
        for name, value in integer_fields.items():
            if isinstance(value, bool) or not isinstance(value, int):
                raise TypeError(f"{name} must be an integer")
        for name in ("num_examples", "input_seq_len", "num_kv_pairs"):
            value = getattr(self, name)
            if value < 1:
                raise ValueError(f"{name} must be >= 1, got {value}")
        if self.vocab_size < 1:
            raise ValueError(f"vocab_size must be >= 1, got {self.vocab_size}")
        if not 0 <= self.seed <= np.iinfo(np.uint32).max:
            raise ValueError("seed must be in the uint32 range")
        if not isinstance(self.random_non_queries, bool):
            raise TypeError("random_non_queries must be a bool")
        if isinstance(self.power_a, bool) or not isinstance(
            self.power_a,
            (int, float),
        ):
            raise TypeError("power_a must be a real number")
        if not math.isfinite(self.power_a) or self.power_a <= 0:
            raise ValueError("power_a must be finite and positive")
        if self.input_seq_len % 2:
            raise ValueError("input_seq_len must be even")
        if self.vocab_size <= self.input_seq_len:
            raise ValueError("vocab_size must be greater than input_seq_len")
        if self.num_kv_pairs * 4 > self.input_seq_len:
            raise ValueError("num_kv_pairs * 4 cannot exceed input_seq_len")

        key_choice_count = self.vocab_size // 2 - 1
        value_choice_count = self.vocab_size - self.vocab_size // 2
        if self.num_kv_pairs > key_choice_count:
            raise ValueError("key vocabulary is too small for unique keys")
        if self.num_kv_pairs > value_choice_count:
            raise ValueError("value vocabulary is too small for unique values")

    @property
    def context_size(self) -> int:
        return 2 * self.num_kv_pairs


@dataclass(frozen=True)
class ZoologyMQARBatch:
    """A generated Zoology MQAR split plus explicit answer metadata."""

    input_ids: Tensor
    labels: Tensor
    loss_mask: Tensor
    query_positions: Tensor
    answer_tokens: Tensor
    config: ZoologyMQARConfig


def _sample_rows_without_replacement(
    rng: np.random.RandomState,
    choices: np.ndarray,
    *,
    num_rows: int,
    sample_size: int,
    probabilities: np.ndarray | None = None,
) -> np.ndarray:
    """Match ``np.apply_along_axis(np.random.choice, ...)`` without tiled input."""

    rows = [
        rng.choice(
            choices,
            size=sample_size,
            replace=False,
            p=probabilities,
        )
        for _ in range(num_rows)
    ]
    return np.asarray(rows, dtype=np.int64)


def generate_zoology_mqar_batch(
    config: ZoologyMQARConfig,
    *,
    device: torch.device | str = "cpu",
    filler_generator: torch.Generator | None = None,
) -> ZoologyMQARBatch:
    """Generate one split with the tagged Zoology ICLR-2024 MQAR semantics.

    Array values and random-number consumption match the upstream legacy NumPy
    implementation at :data:`ZOOLOGY_ICLR24_COMMIT`. A local ``RandomState``
    avoids mutating NumPy's process-global RNG, and row-wise sampling avoids the
    upstream implementation's vocabulary-sized tiled temporary arrays.

    When ``random_non_queries`` is true, ``filler_generator`` controls the
    upstream Torch filler operation. Figure 2 sets that option to false.
    """

    if not isinstance(config, ZoologyMQARConfig):
        raise TypeError("config must be a ZoologyMQARConfig")

    rng = np.random.RandomState(config.seed)
    key_vocab_size = config.vocab_size // 2
    key_choices = np.arange(1, key_vocab_size)
    value_choices = np.arange(key_vocab_size, config.vocab_size)

    keys = _sample_rows_without_replacement(
        rng,
        key_choices,
        num_rows=config.num_examples,
        sample_size=config.num_kv_pairs,
    )
    values = _sample_rows_without_replacement(
        rng,
        value_choices,
        num_rows=config.num_examples,
        sample_size=config.num_kv_pairs,
    )

    key_values = np.zeros(
        (config.num_examples, config.context_size),
        dtype=np.int64,
    )
    key_values[:, 0::2] = keys
    key_values[:, 1::2] = values

    query_space = (config.input_seq_len - config.context_size) // 2
    probability = config.power_a * (
        np.arange(1, query_space + 1) ** (config.power_a - 1)
    )
    probability_sum = probability.sum()
    if not np.isfinite(probability).all() or not np.isfinite(probability_sum):
        raise ValueError("power_a produced a non-finite query distribution")
    probability = probability / probability_sum
    if np.count_nonzero(probability) < config.num_kv_pairs:
        raise ValueError("query distribution has too few non-zero positions")

    gaps = _sample_rows_without_replacement(
        rng,
        np.arange(query_space, dtype=int),
        num_rows=config.num_examples,
        sample_size=config.num_kv_pairs,
        probabilities=probability,
    )

    queries = np.zeros(
        (
            config.num_examples,
            config.input_seq_len - config.context_size + 1,
        ),
        dtype=np.int64,
    )
    np.put_along_axis(queries, gaps * 2, values=keys, axis=1)
    examples = np.concatenate((key_values, queries), axis=1)

    labels = np.full(
        (config.num_examples, config.input_seq_len + 1),
        ZOOLOGY_MQAR_IGNORE_INDEX,
        dtype=np.int64,
    )
    np.put_along_axis(
        labels,
        gaps * 2 + config.context_size + 1,
        values=values,
        axis=1,
    )

    input_ids = torch.tensor(examples[:, :-1], dtype=torch.long)
    label_tensor = torch.tensor(labels[:, 1:], dtype=torch.long)
    if config.random_non_queries:
        random_tokens = torch.randint(
            config.vocab_size,
            size=input_ids.shape,
            generator=filler_generator,
            dtype=torch.long,
        )
        zero_mask = input_ids == 0
        input_ids[zero_mask] = random_tokens[zero_mask]

    query_positions = torch.from_numpy(gaps * 2 + config.context_size).to(
        dtype=torch.long
    )
    answer_tokens = torch.from_numpy(values).to(dtype=torch.long)
    loss_mask = label_tensor != ZOOLOGY_MQAR_IGNORE_INDEX
    target_device = torch.device(device)

    return ZoologyMQARBatch(
        input_ids=input_ids.to(target_device),
        labels=label_tensor.to(target_device),
        loss_mask=loss_mask.to(target_device),
        query_positions=query_positions.to(target_device),
        answer_tokens=answer_tokens.to(target_device),
        config=config,
    )


def zoology_mqar_loss(logits: Tensor, batch: ZoologyMQARBatch) -> Tensor:
    """Compute the historical same-position loss without an LM shift."""

    if logits.ndim != 3 or logits.shape[:2] != batch.input_ids.shape:
        raise ValueError("logits shape does not match Zoology MQAR batch")
    if logits.shape[-1] < batch.config.vocab_size:
        raise ValueError("logits vocabulary does not cover protocol vocabulary")
    return F.cross_entropy(
        logits.reshape(-1, logits.shape[-1]),
        batch.labels.reshape(-1),
        ignore_index=ZOOLOGY_MQAR_IGNORE_INDEX,
    )


def zoology_mqar_accuracy(logits: Tensor, batch: ZoologyMQARBatch) -> Tensor:
    """Measure accuracy at historical query-aligned target positions."""

    if logits.ndim != 3 or logits.shape[:2] != batch.input_ids.shape:
        raise ValueError("logits shape does not match Zoology MQAR batch")
    selected_logits = logits[batch.loss_mask]
    selected_labels = batch.labels[batch.loss_mask]
    if selected_labels.numel() == 0:
        raise ValueError("Zoology MQAR batch contains no supervised targets")
    predictions = selected_logits.argmax(dim=-1)
    return (predictions == selected_labels).to(torch.float32).mean()
