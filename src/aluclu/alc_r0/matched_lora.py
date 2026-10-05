"""Explicit non-merged q_proj LoRA control for the pinned R0 host.

No base module is replaced, patched, merged, or made trainable. This reference
path reproduces only the pinned Transformers 5.17.0 Llama attention semantics.
"""

from __future__ import annotations

import math
from collections.abc import Callable
from typing import cast

import torch
from torch import nn
from torch.nn import functional as F
from transformers.cache_utils import Cache
from transformers.modeling_utils import ALL_ATTENTION_FUNCTIONS
from transformers.models.llama.modeling_llama import (
    LlamaAttention,
    LlamaDecoderLayer,
    apply_rotary_pos_emb,
    eager_attention_forward,
)

from aluclu.alc_r0.checkpoint_execution import CheckpointExecutionError
from aluclu.alc_r0.host import VerifiedHost
from aluclu.alc_r0.host_wrapper import HostWrapperError, PinnedLlamaCapsuleWrapper
from aluclu.alc_r0.research_capsule import (
    ALLOWED_PORTS,
    ALLOWED_RANKS,
    CANONICAL_WIDTH,
    ResearchCapsuleV0,
)


class _QFactors(nn.Module):
    def __init__(self, rank: int, generator: torch.Generator) -> None:
        super().__init__()
        self.A = nn.Parameter(torch.empty(rank, CANONICAL_WIDTH, dtype=torch.float32))
        self.B = nn.Parameter(torch.zeros(CANONICAL_WIDTH, rank, dtype=torch.float32))
        nn.init.kaiming_uniform_(self.A, a=math.sqrt(5), generator=generator)


class MatchedQProjLoRA(nn.Module):
    """One exactly parameter-matched native q-only LoRA grid entry."""

    def __init__(self, *, ports: tuple[int, ...], rank: int, seed: int) -> None:
        super().__init__()
        if ports not in ALLOWED_PORTS:
            raise ValueError("ports are outside the preregistered R0 grid")
        if isinstance(rank, bool) or rank not in ALLOWED_RANKS:
            raise ValueError("rank is outside the preregistered R0 grid")
        if isinstance(seed, bool) or not isinstance(seed, int) or not 0 <= seed < 2**63:
            raise ValueError("seed must be a nonnegative signed 63-bit integer")
        self.ports = ports
        self.rank = rank
        self.initialization_seed = seed
        generator = torch.Generator(device="cpu").manual_seed(seed)
        self.factors = nn.ModuleDict(
            {str(port): _QFactors(rank, generator) for port in ports}
        )

    def q_projection(
        self, port: int, attention: LlamaAttention, hidden_states: torch.Tensor
    ) -> torch.Tensor:
        """Return frozen q projection plus alpha/rank=1 low-rank delta."""

        return self.bind_q_projection(port, attention)(hidden_states)

    def bind_q_projection(
        self, port: int, attention: LlamaAttention
    ) -> Callable[[torch.Tensor], torch.Tensor]:
        """Capture A/B and q_proj references, not mutable mount lookups.

        This is not an integrity snapshot. The checkpoint session must guard
        captured module/parameter bindings before execution and recomputation.
        """

        if port not in self.ports:
            raise ValueError("port is not selected by the matched LoRA grid")
        factors = cast(_QFactors, self.factors[str(port)])
        factor_a, factor_b = factors.A, factors.B
        q_proj = attention.q_proj

        def project(hidden_states: torch.Tensor) -> torch.Tensor:
            if (
                factor_a.device != hidden_states.device
                or factor_b.device != hidden_states.device
            ):
                raise HostWrapperError(
                    "LoRA factors and attention input must share a device"
                )
            if factor_a.dtype != torch.float32 or factor_b.dtype != torch.float32:
                raise HostWrapperError("LoRA master factors must remain FP32")
            base = q_proj(hidden_states)
            with torch.autocast(device_type=hidden_states.device.type, enabled=False):
                low_rank = F.linear(hidden_states.float(), factor_a)
                delta = F.linear(low_rank, factor_b)
            return base + delta.to(dtype=base.dtype)

        return project


class PinnedLlamaLoRAWrapper(PinnedLlamaCapsuleWrapper):
    """Run selected decoder blocks with explicit q-only LoRA attention."""

    def __init__(self, host: VerifiedHost) -> None:
        super().__init__(host)
        self.lora: MatchedQProjLoRA | None = None

    def mount(self, capsule: ResearchCapsuleV0) -> None:
        self._assert_checkpoint_mutation_allowed()
        raise HostWrapperError("matched LoRA arm cannot co-mount a capsule")

    def _checkpoint_factors(self) -> nn.Module:
        if self.lora is None:
            raise CheckpointExecutionError("checkpoint requires mounted LoRA")
        return self.lora

    def mount_lora(self, lora: MatchedQProjLoRA) -> None:
        self._assert_checkpoint_mutation_allowed()
        if not isinstance(lora, MatchedQProjLoRA):
            raise TypeError("mount requires MatchedQProjLoRA")
        base_parameter = next(self.base.parameters())
        if any(
            p.device != base_parameter.device or p.dtype != torch.float32
            for p in lora.parameters()
        ):
            raise HostWrapperError("LoRA factors must be FP32 on the base device")
        self.lora = lora
        lora.train(self.training)

    def detach_lora(self) -> None:
        self._assert_checkpoint_mutation_allowed()
        self.lora = None

    def detach(self) -> None:
        self.detach_lora()

    def _run_decoder_layer(
        self,
        index: int,
        decoder_layer: LlamaDecoderLayer,
        hidden_states: torch.Tensor,
        *,
        attention_mask: torch.Tensor | None,
        position_embeddings: tuple[torch.Tensor, torch.Tensor],
        position_ids: torch.Tensor,
        past_key_values: Cache | None,
        use_cache: bool,
    ) -> torch.Tensor:
        if self.lora is None or index not in self.lora.ports:
            return super()._run_decoder_layer(
                index,
                decoder_layer,
                hidden_states,
                attention_mask=attention_mask,
                position_embeddings=position_embeddings,
                position_ids=position_ids,
                past_key_values=past_key_values,
                use_cache=use_cache,
            )

        residual = hidden_states
        attention_input = decoder_layer.input_layernorm(hidden_states)
        attention_output = self._q_lora_attention(
            index,
            decoder_layer.self_attn,
            attention_input,
            attention_mask=attention_mask,
            position_embeddings=position_embeddings,
            past_key_values=past_key_values,
        )
        hidden_states = residual + attention_output
        residual = hidden_states
        hidden_states = decoder_layer.post_attention_layernorm(hidden_states)
        hidden_states = decoder_layer.mlp(hidden_states)
        return residual + hidden_states

    def _q_lora_attention(
        self,
        index: int,
        attention: LlamaAttention,
        hidden_states: torch.Tensor,
        *,
        attention_mask: torch.Tensor | None,
        position_embeddings: tuple[torch.Tensor, torch.Tensor],
        past_key_values: Cache | None,
    ) -> torch.Tensor:
        assert self.lora is not None
        return _q_attention_with_projection(
            attention,
            hidden_states,
            q_projection=self.lora.bind_q_projection(index, attention),
            attention_mask=attention_mask,
            position_embeddings=position_embeddings,
            past_key_values=past_key_values,
        )

    def _bind_checkpoint_block(self, index: int, decoder_layer: nn.Module):
        """Capture q-only factors inside a complete cache-free decoder block."""
        if type(index) is not int or not 0 <= index < 30:
            raise CheckpointExecutionError("bound decoder index outside host depth")
        if not isinstance(decoder_layer, nn.Module):
            raise CheckpointExecutionError("bound decoder module required")
        lora = self.lora
        if lora is None or index not in lora.ports:
            return super()._bind_checkpoint_block(index, decoder_layer)
        attention = decoder_layer.self_attn
        projection = lora.bind_q_projection(index, attention)
        input_norm = decoder_layer.input_layernorm
        post_norm, mlp = decoder_layer.post_attention_layernorm, decoder_layer.mlp
        attention_operation = _q_attention_with_projection

        def block(hidden, metadata):
            attended = attention_operation(
                attention,
                input_norm(hidden),
                q_projection=projection,
                attention_mask=metadata["attention_mask"],
                position_embeddings=(metadata["cos"], metadata["sin"]),
                past_key_values=None,
            )
            residual = hidden + attended
            return residual + mlp(post_norm(residual))

        return block


def _q_attention_with_projection(
    attention: LlamaAttention,
    hidden_states: torch.Tensor,
    *,
    q_projection: Callable[[torch.Tensor], torch.Tensor],
    attention_mask: torch.Tensor | None,
    position_embeddings: tuple[torch.Tensor, torch.Tensor],
    past_key_values: Cache | None,
    v_projection: Callable[[torch.Tensor], torch.Tensor] | None = None,
) -> torch.Tensor:
    """Pinned attention with explicit q and optional v projection operations.

    Existing q-only callers keep the exact base-v path. The larger q+v
    reference supplies v explicitly; no module replacement or target discovery.
    """
    input_shape = hidden_states.shape[:-1]
    hidden_shape = (*input_shape, -1, attention.head_dim)
    query_states = q_projection(hidden_states)
    query_states = query_states.view(hidden_shape).transpose(1, 2)
    key_states = attention.k_proj(hidden_states).view(hidden_shape).transpose(1, 2)
    values = (
        attention.v_proj(hidden_states)
        if v_projection is None
        else v_projection(hidden_states)
    )
    value_states = values.view(hidden_shape).transpose(1, 2)

    cos, sin = position_embeddings
    query_states, key_states = apply_rotary_pos_emb(query_states, key_states, cos, sin)
    if past_key_values is not None:
        key_states, value_states = past_key_values.update(
            key_states, value_states, attention.layer_idx
        )
    attention_interface = ALL_ATTENTION_FUNCTIONS.get_interface(
        attention.config._attn_implementation or "eager", eager_attention_forward
    )
    attention_output, _ = attention_interface(
        attention,
        query_states,
        key_states,
        value_states,
        attention_mask,
        dropout=0.0 if not attention.training else attention.attention_dropout,
        scaling=attention.scaling,
    )
    attention_output = attention_output.reshape(*input_shape, -1).contiguous()
    return attention.o_proj(attention_output)
