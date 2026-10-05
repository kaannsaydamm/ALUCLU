"""Explicit all-layer q+v reference wiring; not real-host qualification.

The inherited verified-host constructor remains mandatory for actual use.
Checkpoint inventory is explicit opt-in; fake-block closure/inventory tests do
not establish actual-host qualification or grant execution authority.
"""

from __future__ import annotations

import torch
from torch import nn

from .checkpoint_execution import CheckpointExecutionError
from .host import VerifiedHost
from .host_wrapper import HostWrapperError, PinnedLlamaCapsuleWrapper
from .matched_lora import _q_attention_with_projection
from .reference_qv_lora import ReferenceQVLoRA


class PinnedLlamaQVReferenceWrapper(PinnedLlamaCapsuleWrapper):
    """Larger, separately reported rank-8 q+v arm, never the matched comparator."""

    def __init__(self, host: VerifiedHost) -> None:
        super().__init__(host)
        self.reference: ReferenceQVLoRA | None = None

    def mount(self, capsule) -> None:
        self._assert_checkpoint_mutation_allowed()
        raise HostWrapperError("q+v reference cannot co-mount a capsule")

    def mount_reference(self, reference: ReferenceQVLoRA) -> None:
        self._assert_checkpoint_mutation_allowed()
        if type(reference) is not ReferenceQVLoRA:
            raise TypeError("mount requires exact ReferenceQVLoRA")
        layers = self.base.model.layers
        if len(layers) != 30:
            raise HostWrapperError("q+v reference requires all 30 layers")
        # Validate every target before publishing a new mount; factories perform
        # no forward or mutation. Actual host identity is the constructor's job.
        for index, layer in enumerate(layers):
            for target in ("q", "v"):
                reference.bind_projection(
                    layer=index,
                    target=target,
                    base=getattr(layer.self_attn, f"{target}_proj"),
                )
        base_parameter = next(self.base.parameters())
        if any(
            parameter.device != base_parameter.device
            or parameter.dtype != torch.float32
            or not parameter.requires_grad
            for parameter in reference.parameters()
        ):
            raise HostWrapperError("reference requires trainable FP32 on base device")
        self.reference = reference
        reference.train(self.training)

    def detach(self) -> None:
        self._assert_checkpoint_mutation_allowed()
        self.reference = None

    def _checkpoint_factors(self) -> nn.Module:
        if self.reference is None:
            raise CheckpointExecutionError("checkpoint requires mounted q+v reference")
        return self.reference

    def enable_checkpoint_inventory(self) -> None:
        super().enable_checkpoint_inventory()

    def _bind_checkpoint_block(self, index: int, decoder_layer: nn.Module):
        if type(index) is not int or not 0 <= index < 30:
            raise CheckpointExecutionError("bound decoder index outside host depth")
        if not isinstance(decoder_layer, nn.Module):
            raise CheckpointExecutionError("bound decoder module required")
        reference = self.reference
        if reference is None:
            return super()._bind_checkpoint_block(index, decoder_layer)
        attention = decoder_layer.self_attn
        query = reference.bind_projection(
            layer=index, target="q", base=attention.q_proj
        )
        value = reference.bind_projection(
            layer=index, target="v", base=attention.v_proj
        )
        input_norm = decoder_layer.input_layernorm
        post_norm, mlp = decoder_layer.post_attention_layernorm, decoder_layer.mlp
        operation = _q_attention_with_projection

        def block(hidden, metadata):
            attended = operation(
                attention,
                input_norm(hidden),
                q_projection=query,
                v_projection=value,
                attention_mask=metadata["attention_mask"],
                position_embeddings=(metadata["cos"], metadata["sin"]),
                past_key_values=None,
            )
            residual = hidden + attended
            return residual + mlp(post_norm(residual))

        return block

    def _run_decoder_layer(
        self,
        index,
        decoder_layer,
        hidden_states,
        *,
        attention_mask,
        position_embeddings,
        position_ids,
        past_key_values,
        use_cache,
    ):
        if self.reference is None:
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
        attention = decoder_layer.self_attn
        query = self.reference.bind_projection(
            layer=index, target="q", base=attention.q_proj
        )
        value = self.reference.bind_projection(
            layer=index, target="v", base=attention.v_proj
        )
        attended = _q_attention_with_projection(
            attention,
            decoder_layer.input_layernorm(hidden_states),
            q_projection=query,
            v_projection=value,
            attention_mask=attention_mask,
            position_embeddings=position_embeddings,
            past_key_values=past_key_values,
        )
        residual = hidden_states + attended
        return residual + decoder_layer.mlp(
            decoder_layer.post_attention_layernorm(residual)
        )
