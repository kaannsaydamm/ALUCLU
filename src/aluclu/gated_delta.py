from __future__ import annotations

import math

import torch
import torch.nn.functional as F
from torch import Tensor, nn

from .config import GatedDeltaConfig
from .ops import StreamingDepthwiseConv1d, l2_normalize
from .state import GatedDeltaState


class GatedDeltaRule2(nn.Module):
    """Numerically conservative recurrent reference for Gated Delta Rule-2.

    This implementation follows the token recurrence rather than a chunkwise
    accelerator kernel. It is the correctness oracle and CPU fallback. The
    fast-weight accumulator and decay path remain fp32 under mixed precision.
    """

    def __init__(self, config: GatedDeltaConfig) -> None:
        super().__init__()
        self.config = config
        d_model = config.d_model
        key_width = config.n_heads * config.head_key_dim
        value_width = config.n_heads * config.head_value_dim

        self.stem = StreamingDepthwiseConv1d(d_model, config.conv_kernel)
        self.query_projection = nn.Linear(d_model, key_width, bias=False)
        self.key_projection = nn.Linear(d_model, key_width, bias=False)
        self.value_projection = nn.Linear(d_model, value_width, bias=False)
        self.erase_projection = nn.Linear(d_model, key_width, bias=True)
        self.write_projection = nn.Linear(d_model, value_width, bias=True)
        self.decay_projection = nn.Linear(d_model, key_width, bias=False)
        self.output_gate_projection = nn.Linear(d_model, value_width, bias=False)
        self.output_projection = nn.Linear(value_width, d_model, bias=False)

        rates = torch.linspace(0.01, 0.10, key_width).log()
        self.decay_log_scale = nn.Parameter(rates)
        self.decay_offset = nn.Parameter(torch.full((key_width,), -2.0))
        self.reset_parameters()

    def reset_parameters(self) -> None:
        for projection in (
            self.query_projection,
            self.key_projection,
            self.value_projection,
            self.output_gate_projection,
            self.output_projection,
        ):
            nn.init.xavier_uniform_(projection.weight)
        nn.init.xavier_uniform_(self.erase_projection.weight)
        nn.init.constant_(self.erase_projection.bias, -1.0)
        nn.init.xavier_uniform_(self.write_projection.weight)
        nn.init.constant_(self.write_projection.bias, 1.0)
        nn.init.zeros_(self.decay_projection.weight)

    def initial_state(
        self,
        batch_size: int,
        *,
        device: torch.device,
        dtype: torch.dtype,
    ) -> GatedDeltaState:
        config = self.config
        return GatedDeltaState(
            conv_history=self.stem.empty_history(
                batch_size,
                device=device,
                dtype=dtype,
            ),
            fast_weight=torch.zeros(
                batch_size,
                config.n_heads,
                config.head_key_dim,
                config.head_value_dim,
                device=device,
                dtype=torch.float32,
            ),
            tokens_seen=0,
        )

    def _reshape_key(self, x: Tensor) -> Tensor:
        config = self.config
        return x.reshape(
            x.shape[0],
            x.shape[1],
            config.n_heads,
            config.head_key_dim,
        )

    def _reshape_value(self, x: Tensor) -> Tensor:
        config = self.config
        return x.reshape(
            x.shape[0],
            x.shape[1],
            config.n_heads,
            config.head_value_dim,
        )

    def forward(
        self,
        x: Tensor,
        state: GatedDeltaState | None = None,
        *,
        return_state: bool = False,
        return_write_surprise: bool = False,
    ) -> (
        Tensor
        | tuple[Tensor, GatedDeltaState]
        | tuple[Tensor, Tensor]
        | tuple[Tensor, GatedDeltaState, Tensor]
    ):
        config = self.config
        if x.ndim != 3 or x.shape[-1] != config.d_model:
            raise ValueError(f"x must have shape [batch, time, {config.d_model}]")
        if state is None:
            state = self.initial_state(
                x.shape[0],
                device=x.device,
                dtype=x.dtype,
            )
        if state.conv_history.shape[0] != x.shape[0]:
            raise ValueError("state batch size does not match x")

        hidden, next_history = self.stem(x, state.conv_history)
        query = l2_normalize(
            self._reshape_key(self.query_projection(hidden)),
            config.eps,
        )
        key = l2_normalize(
            self._reshape_key(self.key_projection(hidden)),
            config.eps,
        )
        value = self._reshape_value(self.value_projection(hidden))
        erase = torch.sigmoid(self._reshape_key(self.erase_projection(hidden)))
        write = torch.sigmoid(self._reshape_value(self.write_projection(hidden)))
        output_gate = F.silu(self._reshape_value(self.output_gate_projection(hidden)))

        batch, time = x.shape[:2]
        decay_logits = self.decay_projection(hidden).reshape(
            batch,
            time,
            config.n_heads,
            config.head_key_dim,
        )
        decay_scale = self.decay_log_scale.exp().reshape(
            config.n_heads,
            config.head_key_dim,
        )
        decay_offset = self.decay_offset.reshape(
            config.n_heads,
            config.head_key_dim,
        )
        log_decay = -decay_scale * F.softplus(decay_logits.float() + decay_offset)
        decay = log_decay.exp().clamp_min(config.decay_min)

        fast_weight = state.fast_weight.float()
        outputs = []
        write_surprises = []
        for index in range(time):
            key_t = key[:, index].float()
            query_t = query[:, index].float()
            value_t = value[:, index].float()
            erase_t = erase[:, index].float()
            write_t = write[:, index].float()

            decayed = decay[:, index].unsqueeze(-1) * fast_weight
            erase_direction = erase_t * key_t
            old_value = torch.einsum(
                "bhkv,bhk->bhv",
                decayed,
                erase_direction,
            )
            target = write_t * value_t
            residual = target - old_value
            write_surprises.append(
                torch.linalg.vector_norm(
                    residual,
                    dim=(-2, -1),
                )
                / math.sqrt(config.n_heads * config.head_value_dim)
            )
            fast_weight = decayed + key_t.unsqueeze(-1) * residual.unsqueeze(-2)
            output = torch.einsum(
                "bhkv,bhk->bhv",
                fast_weight,
                query_t,
            )
            outputs.append(output)

        stacked = torch.stack(outputs, dim=1).to(x.dtype)
        stacked = stacked * output_gate
        stacked = stacked.reshape(
            batch,
            time,
            config.n_heads * config.head_value_dim,
        )
        output = self.output_projection(stacked)
        next_state = GatedDeltaState(
            conv_history=next_history,
            fast_weight=fast_weight,
            tokens_seen=state.tokens_seen + time,
        )
        surprise = torch.stack(write_surprises, dim=1)
        if return_state and return_write_surprise:
            return output, next_state, surprise
        if return_state:
            return output, next_state
        if return_write_surprise:
            return output, surprise
        return output

    def step(
        self,
        x: Tensor,
        state: GatedDeltaState | None = None,
    ) -> tuple[Tensor, GatedDeltaState]:
        if x.ndim != 2:
            raise ValueError("step expects [batch, d_model]")
        output, next_state = self.forward(
            x.unsqueeze(1),
            state,
            return_state=True,
        )
        return output[:, 0], next_state

    @staticmethod
    def detach_state(state: GatedDeltaState) -> GatedDeltaState:
        return state.detach()
