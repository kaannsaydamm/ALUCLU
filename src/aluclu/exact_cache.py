from __future__ import annotations

import math

import torch
import torch.nn.functional as F
from torch import Tensor, nn

from .config import ExactCacheConfig
from .state import ExactCacheState


class ResidualSurpriseCache(nn.Module):
    """Keep the highest-write-residual tokens in a bounded exact KV cache.

    The cache complements a compressive recurrent state. While capacity is
    available every token is retained. Once full, an incoming token replaces
    the minimum-priority entry only when its Gated Delta write residual is
    larger. Reads are exact causal softmax attention over the retained entries.
    """

    def __init__(self, config: ExactCacheConfig) -> None:
        super().__init__()
        self.config = config
        self.head_dim = config.d_model // config.n_heads
        self.query_projection = nn.Linear(
            config.d_model,
            config.d_model,
            bias=False,
        )
        self.key_projection = nn.Linear(
            config.d_model,
            config.d_model,
            bias=False,
        )
        self.value_projection = nn.Linear(
            config.d_model,
            config.d_model,
            bias=False,
        )
        self.output_projection = nn.Linear(
            config.d_model,
            config.d_model,
            bias=False,
        )
        self.reset_parameters()

    def reset_parameters(self) -> None:
        for projection in (
            self.query_projection,
            self.key_projection,
            self.value_projection,
            self.output_projection,
        ):
            nn.init.xavier_uniform_(projection.weight)

    def initial_state(
        self,
        batch_size: int,
        *,
        device: torch.device,
        dtype: torch.dtype,
    ) -> ExactCacheState:
        config = self.config
        shape = (
            batch_size,
            config.n_heads,
            config.capacity,
            self.head_dim,
        )
        priority_dtype = torch.float64 if dtype == torch.float64 else torch.float32
        return ExactCacheState(
            key=torch.zeros(shape, device=device, dtype=dtype),
            value=torch.zeros(shape, device=device, dtype=dtype),
            priority=torch.full(
                (batch_size, config.capacity),
                -torch.inf,
                device=device,
                dtype=priority_dtype,
            ),
            valid=torch.zeros(
                batch_size,
                config.capacity,
                device=device,
                dtype=torch.bool,
            ),
            tokens_seen=0,
        )

    def _validate_state(
        self,
        state: ExactCacheState,
        x: Tensor,
    ) -> None:
        config = self.config
        expected_key_value = (
            x.shape[0],
            config.n_heads,
            config.capacity,
            self.head_dim,
        )
        expected_metadata = (x.shape[0], config.capacity)
        if state.key.shape != expected_key_value:
            raise ValueError(
                f"state.key must have shape {expected_key_value}, "
                f"got {tuple(state.key.shape)}"
            )
        if state.value.shape != expected_key_value:
            raise ValueError(
                f"state.value must have shape {expected_key_value}, "
                f"got {tuple(state.value.shape)}"
            )
        if state.priority.shape != expected_metadata:
            raise ValueError(
                f"state.priority must have shape {expected_metadata}, "
                f"got {tuple(state.priority.shape)}"
            )
        if state.valid.shape != expected_metadata:
            raise ValueError(
                f"state.valid must have shape {expected_metadata}, "
                f"got {tuple(state.valid.shape)}"
            )

        tensors = (state.key, state.value, state.priority, state.valid)
        if any(tensor.device != x.device for tensor in tensors):
            raise ValueError("all state tensors must be on the same device as x")
        if state.key.dtype != x.dtype or state.value.dtype != x.dtype:
            raise ValueError("state key/value dtype must match x")
        expected_priority_dtype = (
            torch.float64 if x.dtype == torch.float64 else torch.float32
        )
        if state.priority.dtype != expected_priority_dtype:
            raise ValueError(f"state.priority must use {expected_priority_dtype}")
        if state.valid.dtype != torch.bool:
            raise ValueError("state.valid must use torch.bool")

    def _reshape(self, x: Tensor) -> Tensor:
        batch, time, _ = x.shape
        return x.reshape(
            batch,
            time,
            self.config.n_heads,
            self.head_dim,
        )

    def _insert(
        self,
        state: ExactCacheState,
        key: Tensor,
        value: Tensor,
        priority: Tensor,
    ) -> ExactCacheState:
        invalid = ~state.valid
        has_space = invalid.any(dim=1)
        first_invalid = invalid.to(torch.int64).argmax(dim=1)
        minimum_index = state.priority.argmin(dim=1)
        insertion_index = torch.where(
            has_space,
            first_invalid,
            minimum_index,
        )
        minimum_priority = state.priority.gather(
            1,
            minimum_index.unsqueeze(1),
        ).squeeze(1)
        detached_priority = priority.detach().to(state.priority.dtype)
        should_write = has_space | (detached_priority > minimum_priority)
        selection = F.one_hot(
            insertion_index,
            num_classes=self.config.capacity,
        ).to(torch.bool)
        selection = selection & should_write.unsqueeze(1)

        cache_mask = selection[:, None, :, None]
        next_key = torch.where(
            cache_mask,
            key[:, :, None, :],
            state.key,
        )
        next_value = torch.where(
            cache_mask,
            value[:, :, None, :],
            state.value,
        )
        next_priority = torch.where(
            selection,
            detached_priority.unsqueeze(1),
            state.priority,
        )
        return ExactCacheState(
            key=next_key,
            value=next_value,
            priority=next_priority,
            valid=state.valid | selection,
            tokens_seen=state.tokens_seen + 1,
        )

    def _read(self, query: Tensor, state: ExactCacheState) -> Tensor:
        scores = torch.einsum(
            "bhd,bhcd->bhc",
            query,
            state.key,
        ) / math.sqrt(self.head_dim)
        scores = scores.masked_fill(
            ~state.valid[:, None, :],
            torch.finfo(scores.dtype).min,
        )
        softmax_dtype = (
            torch.float32
            if scores.dtype in (torch.float16, torch.bfloat16)
            else scores.dtype
        )
        weights = F.softmax(
            scores,
            dim=-1,
            dtype=softmax_dtype,
        ).to(query.dtype)
        weights = F.dropout(
            weights,
            p=self.config.dropout,
            training=self.training,
        )
        return torch.einsum("bhc,bhcd->bhd", weights, state.value)

    def forward(
        self,
        x: Tensor,
        write_surprise: Tensor,
        state: ExactCacheState | None = None,
        *,
        return_state: bool = False,
    ) -> Tensor | tuple[Tensor, ExactCacheState]:
        config = self.config
        if x.ndim != 3 or x.shape[-1] != config.d_model:
            raise ValueError(f"x must have shape [batch, time, {config.d_model}]")
        if x.shape[1] < 1:
            raise ValueError("x must contain at least one token")
        if write_surprise.shape != x.shape[:2]:
            raise ValueError("write_surprise must have shape [batch, time]")
        if state is None:
            state = self.initial_state(
                x.shape[0],
                device=x.device,
                dtype=x.dtype,
            )
        self._validate_state(state, x)
        if write_surprise.device != x.device:
            raise ValueError("write_surprise must be on the same device as x")

        query = self._reshape(self.query_projection(x))
        key = self._reshape(self.key_projection(x))
        value = self._reshape(self.value_projection(x))
        outputs = []
        for index in range(x.shape[1]):
            state = self._insert(
                state,
                key[:, index],
                value[:, index],
                write_surprise[:, index],
            )
            outputs.append(self._read(query[:, index], state))

        stacked = torch.stack(outputs, dim=1).reshape(
            x.shape[0],
            x.shape[1],
            config.d_model,
        )
        output = self.output_projection(stacked)
        if return_state:
            return output, state
        return output

    def step(
        self,
        x: Tensor,
        write_surprise: Tensor,
        state: ExactCacheState | None = None,
    ) -> tuple[Tensor, ExactCacheState]:
        if x.ndim != 2:
            raise ValueError("step expects x with shape [batch, d_model]")
        if write_surprise.shape != x.shape[:1]:
            raise ValueError("step expects write_surprise with shape [batch]")
        output, next_state = self.forward(
            x.unsqueeze(1),
            write_surprise.unsqueeze(1),
            state,
            return_state=True,
        )
        return output[:, 0], next_state

    def state_elements_per_batch(self) -> int:
        config = self.config
        return 2 * config.capacity * config.d_model + 2 * config.capacity

    @staticmethod
    def detach_state(state: ExactCacheState) -> ExactCacheState:
        return state.detach()
