from __future__ import annotations

from dataclasses import dataclass

import torch
import torch.nn.functional as F
from torch import Tensor, nn

from .config import (
    AlucluConfig,
    GatedDeltaConfig,
)
from .episodic import BoundedEpisodicMemory
from .exact_cache import ResidualSurpriseCache
from .gated_delta import GatedDeltaRule2
from .local_attention import BoundedLocalAttention
from .state import (
    AlucluBlockState,
    AlucluModelState,
)


class SwiGLU(nn.Module):
    def __init__(self, d_model: int, multiplier: int) -> None:
        super().__init__()
        hidden = d_model * multiplier
        self.input_projection = nn.Linear(d_model, 2 * hidden, bias=False)
        self.output_projection = nn.Linear(hidden, d_model, bias=False)

    def forward(self, x: Tensor) -> Tensor:
        gate, value = self.input_projection(x).chunk(2, dim=-1)
        return self.output_projection(F.silu(gate) * value)


class AlucluBlock(nn.Module):
    """Fuse learned-update, local, exact-surprise, and episodic lanes."""

    def __init__(self, config: AlucluConfig, layer_index: int) -> None:
        super().__init__()
        self.config = config
        self.layer_index = layer_index
        gated_config = config.gated_delta or GatedDeltaConfig(d_model=config.d_model)
        self.gated_delta = GatedDeltaRule2(gated_config)

        use_local = (layer_index + 1) % config.local_attention_every == 0
        self.local_attention = (
            BoundedLocalAttention(
                d_model=config.d_model,
                n_heads=config.local_heads,
                window_size=config.local_window,
                dropout=config.dropout,
            )
            if use_local
            else None
        )

        use_episodic = (
            config.episodic is not None
            and (layer_index + 1) % config.episodic_every == 0
        )
        self.episodic = BoundedEpisodicMemory(config.episodic) if use_episodic else None

        use_exact_cache = (
            config.exact_cache is not None
            and (layer_index + 1) % config.exact_cache_every == 0
        )
        self.exact_cache = (
            ResidualSurpriseCache(config.exact_cache) if use_exact_cache else None
        )

        self.mixer_norm = nn.RMSNorm(config.d_model)
        self.ffn_norm = nn.RMSNorm(config.d_model)
        self.ffn = SwiGLU(config.d_model, config.ffn_multiplier)
        self.dropout = nn.Dropout(config.dropout)

        branch_count = 1 + int(use_local) + int(use_episodic) + int(use_exact_cache)
        self.branch_norms = nn.ModuleList(
            nn.RMSNorm(config.d_model) for _ in range(branch_count)
        )
        self.branch_scale = nn.Parameter(torch.ones(branch_count))
        self.fusion_projection = (
            nn.Linear(config.d_model, branch_count, bias=True)
            if branch_count > 1
            else None
        )
        if self.fusion_projection is not None:
            nn.init.zeros_(self.fusion_projection.weight)
            nn.init.zeros_(self.fusion_projection.bias)

    def initial_state(
        self,
        batch_size: int,
        *,
        device: torch.device,
        dtype: torch.dtype,
    ) -> AlucluBlockState:
        return AlucluBlockState(
            gated_delta=self.gated_delta.initial_state(
                batch_size,
                device=device,
                dtype=dtype,
            ),
            local_attention=(
                None
                if self.local_attention is None
                else self.local_attention.initial_state(
                    batch_size,
                    device=device,
                    dtype=dtype,
                )
            ),
            episodic=(
                None
                if self.episodic is None
                else self.episodic.initial_state(
                    batch_size,
                    device=device,
                    dtype=dtype,
                )
            ),
            exact_cache=(
                None
                if self.exact_cache is None
                else self.exact_cache.initial_state(
                    batch_size,
                    device=device,
                    dtype=dtype,
                )
            ),
        )

    def _fuse(self, hidden: Tensor, branches: list[Tensor]) -> Tensor:
        normalized = [
            norm(branch) * self.branch_scale[index]
            for index, (norm, branch) in enumerate(
                zip(self.branch_norms, branches, strict=True)
            )
        ]
        if self.fusion_projection is None:
            return normalized[0]
        weights = self.fusion_projection(hidden).softmax(dim=-1)
        stacked = torch.stack(normalized, dim=-2)
        return (weights.unsqueeze(-1) * stacked).sum(dim=-2)

    def forward(
        self,
        x: Tensor,
        state: AlucluBlockState,
    ) -> tuple[Tensor, AlucluBlockState]:
        hidden = self.mixer_norm(x)
        gated_output, gated_state, write_surprise = self.gated_delta(
            hidden,
            state.gated_delta,
            return_state=True,
            return_write_surprise=True,
        )
        branches = [gated_output]

        local_state = state.local_attention
        if self.local_attention is not None:
            if local_state is None:
                raise ValueError("local attention state is missing")
            local_output, local_state = self.local_attention(
                hidden,
                local_state,
                return_state=True,
            )
            branches.append(local_output)

        episodic_state = state.episodic
        if self.episodic is not None:
            if episodic_state is None:
                raise ValueError("episodic state is missing")
            episodic_output, episodic_state = self.episodic(
                hidden,
                episodic_state,
                return_state=True,
            )
            branches.append(episodic_output)

        exact_cache_state = state.exact_cache
        if self.exact_cache is not None:
            if exact_cache_state is None:
                raise ValueError("exact cache state is missing")
            exact_cache_output, exact_cache_state = self.exact_cache(
                hidden,
                write_surprise,
                exact_cache_state,
                return_state=True,
            )
            branches.append(exact_cache_output)

        x = x + self.dropout(self._fuse(hidden, branches))
        x = x + self.dropout(self.ffn(self.ffn_norm(x)))
        return x, AlucluBlockState(
            gated_delta=gated_state,
            local_attention=local_state,
            episodic=episodic_state,
            exact_cache=exact_cache_state,
        )


@dataclass(frozen=True)
class AlucluLanguageModelOutput:
    logits: Tensor
    loss: Tensor | None
    state: AlucluModelState


class AlucluLanguageModel(nn.Module):
    """Decoder-only ALUCLU bounded-state language model."""

    def __init__(
        self,
        vocab_size: int,
        config: AlucluConfig,
        *,
        tie_embeddings: bool = True,
    ) -> None:
        super().__init__()
        if vocab_size < 2:
            raise ValueError("vocab_size must be >= 2")
        self.vocab_size = vocab_size
        self.config = config
        self.token_embedding = nn.Embedding(vocab_size, config.d_model)
        self.blocks = nn.ModuleList(
            AlucluBlock(config, layer_index) for layer_index in range(config.n_layers)
        )
        self.final_norm = nn.RMSNorm(config.d_model)
        self.lm_head = nn.Linear(config.d_model, vocab_size, bias=False)
        nn.init.normal_(self.token_embedding.weight, mean=0, std=0.02)
        if tie_embeddings:
            self.lm_head.weight = self.token_embedding.weight
        else:
            nn.init.normal_(self.lm_head.weight, mean=0, std=0.02)

    def initial_state(
        self,
        batch_size: int,
        *,
        device: torch.device | None = None,
        dtype: torch.dtype | None = None,
    ) -> AlucluModelState:
        if device is None:
            device = self.token_embedding.weight.device
        if dtype is None:
            dtype = self.token_embedding.weight.dtype
        return AlucluModelState(
            blocks=tuple(
                block.initial_state(
                    batch_size,
                    device=device,
                    dtype=dtype,
                )
                for block in self.blocks
            ),
            tokens_seen=0,
        )

    def forward(
        self,
        input_ids: Tensor,
        *,
        labels: Tensor | None = None,
        loss_mask: Tensor | None = None,
        state: AlucluModelState | None = None,
    ) -> AlucluLanguageModelOutput:
        if input_ids.ndim != 2:
            raise ValueError("input_ids must have shape [batch, time]")
        if input_ids.dtype != torch.long:
            raise ValueError("input_ids must use torch.long")
        if state is None:
            state = self.initial_state(
                input_ids.shape[0],
                device=input_ids.device,
                dtype=self.token_embedding.weight.dtype,
            )
        if len(state.blocks) != len(self.blocks):
            raise ValueError("state layer count does not match model")

        hidden = self.token_embedding(input_ids)
        next_block_states = []
        for block, block_state in zip(
            self.blocks,
            state.blocks,
            strict=True,
        ):
            hidden, next_block_state = block(hidden, block_state)
            next_block_states.append(next_block_state)
        logits = self.lm_head(self.final_norm(hidden))

        loss = None
        if labels is not None:
            if labels.shape != input_ids.shape:
                raise ValueError("labels must match input_ids shape")
            if input_ids.shape[1] < 2:
                raise ValueError("at least two tokens are required for LM loss")
            token_loss = F.cross_entropy(
                logits[:, :-1].reshape(-1, self.vocab_size),
                labels[:, 1:].reshape(-1),
                reduction="none",
            ).reshape(input_ids.shape[0], input_ids.shape[1] - 1)
            if loss_mask is None:
                loss = token_loss.mean()
            else:
                if loss_mask.shape != input_ids.shape:
                    raise ValueError("loss_mask must match input_ids shape")
                active = loss_mask[:, 1:].to(token_loss.dtype)
                active_count = active.sum()
                if active_count.item() == 0:
                    raise ValueError("loss_mask does not select any target")
                loss = (token_loss * active).sum() / active_count

        next_state = AlucluModelState(
            blocks=tuple(next_block_states),
            tokens_seen=state.tokens_seen + input_ids.shape[1],
        )
        return AlucluLanguageModelOutput(
            logits=logits,
            loss=loss,
            state=next_state,
        )

    def step(
        self,
        input_ids: Tensor,
        state: AlucluModelState | None = None,
    ) -> tuple[Tensor, AlucluModelState]:
        if input_ids.ndim != 1:
            raise ValueError("step expects input_ids with shape [batch]")
        output = self.forward(input_ids.unsqueeze(1), state=state)
        return output.logits[:, 0], output.state

    @staticmethod
    def detach_state(state: AlucluModelState) -> AlucluModelState:
        return state.detach()
