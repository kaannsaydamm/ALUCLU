from __future__ import annotations

import math

import torch
import torch.nn.functional as F
from torch import Tensor, nn

from .state import LocalAttentionState


class BoundedLocalAttention(nn.Module):
    """Exact causal softmax attention over a fixed rolling window."""

    def __init__(
        self,
        d_model: int,
        n_heads: int,
        window_size: int,
        dropout: float = 0.0,
    ) -> None:
        super().__init__()
        if d_model < 1 or n_heads < 1 or window_size < 1:
            raise ValueError("dimensions and window_size must be positive")
        if d_model % n_heads:
            raise ValueError("d_model must be divisible by n_heads")
        if not 0 <= dropout < 1:
            raise ValueError("dropout must be in [0, 1)")
        self.d_model = d_model
        self.n_heads = n_heads
        self.head_dim = d_model // n_heads
        self.window_size = window_size
        self.dropout = dropout

        self.query_projection = nn.Linear(d_model, d_model, bias=False)
        self.key_projection = nn.Linear(d_model, d_model, bias=False)
        self.value_projection = nn.Linear(d_model, d_model, bias=False)
        self.output_projection = nn.Linear(d_model, d_model, bias=False)
        initial_slopes = torch.linspace(0.10, 1.0, n_heads)
        self.slope_raw = nn.Parameter(torch.log(torch.expm1(initial_slopes)))
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
    ) -> LocalAttentionState:
        empty = torch.empty(
            batch_size,
            self.n_heads,
            0,
            self.head_dim,
            device=device,
            dtype=dtype,
        )
        return LocalAttentionState(
            key=empty,
            value=empty.clone(),
            tokens_seen=0,
        )

    def _reshape(self, x: Tensor) -> Tensor:
        batch, time, _ = x.shape
        return x.reshape(
            batch,
            time,
            self.n_heads,
            self.head_dim,
        ).transpose(1, 2)

    def forward(
        self,
        x: Tensor,
        state: LocalAttentionState | None = None,
        *,
        return_state: bool = False,
    ) -> Tensor | tuple[Tensor, LocalAttentionState]:
        if x.ndim != 3 or x.shape[-1] != self.d_model:
            raise ValueError(f"x must have shape [batch, time, {self.d_model}]")
        if state is None:
            state = self.initial_state(
                x.shape[0],
                device=x.device,
                dtype=x.dtype,
            )
        if state.key.shape[0] != x.shape[0]:
            raise ValueError("state batch size does not match x")

        query = self._reshape(self.query_projection(x))
        key = self._reshape(self.key_projection(x))
        value = self._reshape(self.value_projection(x))
        key_memory = state.key
        value_memory = state.value
        outputs = []
        scale = 1 / math.sqrt(self.head_dim)
        slopes = F.softplus(self.slope_raw)

        for index in range(x.shape[1]):
            key_memory = torch.cat(
                (key_memory, key[:, :, index : index + 1]),
                dim=2,
            )[:, :, -self.window_size :]
            value_memory = torch.cat(
                (value_memory, value[:, :, index : index + 1]),
                dim=2,
            )[:, :, -self.window_size :]
            scores = (
                torch.einsum(
                    "bhd,bhld->bhl",
                    query[:, :, index],
                    key_memory,
                )
                * scale
            )
            distance = torch.arange(
                key_memory.shape[2] - 1,
                -1,
                -1,
                device=x.device,
                dtype=scores.dtype,
            )
            scores = scores - slopes[None, :, None] * distance[None, None, :]
            weights = F.softmax(scores.float(), dim=-1).to(x.dtype)
            weights = F.dropout(
                weights,
                p=self.dropout,
                training=self.training,
            )
            outputs.append(torch.einsum("bhl,bhld->bhd", weights, value_memory))

        stacked = torch.stack(outputs, dim=2).transpose(1, 2)
        stacked = stacked.reshape(x.shape[0], x.shape[1], self.d_model)
        output = self.output_projection(stacked)
        next_state = LocalAttentionState(
            key=key_memory,
            value=value_memory,
            tokens_seen=state.tokens_seen + x.shape[1],
        )
        if return_state:
            return output, next_state
        return output

    def step(
        self,
        x: Tensor,
        state: LocalAttentionState | None = None,
    ) -> tuple[Tensor, LocalAttentionState]:
        if x.ndim != 2:
            raise ValueError("step expects [batch, d_model]")
        output, next_state = self.forward(
            x.unsqueeze(1),
            state,
            return_state=True,
        )
        return output[:, 0], next_state

    @staticmethod
    def detach_state(state: LocalAttentionState) -> LocalAttentionState:
        return state.detach()
