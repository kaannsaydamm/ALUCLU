"""Explicit decoder-block interposition for the pinned R0 Llama host.

This is a research reference path, not the R0.0 authorization gate. The same
layer iteration runs with and without a mounted capsule so no-capsule parity
can be tested independently against the official Transformers forward.
"""

from __future__ import annotations

from importlib.metadata import version
from typing import cast

import torch
from torch import nn
from transformers.cache_utils import Cache, DynamicCache
from transformers.masking_utils import create_causal_mask
from transformers.modeling_outputs import CausalLMOutputWithPast
from transformers.models.llama.modeling_llama import LlamaDecoderLayer, LlamaForCausalLM

from aluclu.alc_r0.checkpoint_execution import (
    CheckpointController,
    CheckpointExecutionError,
    CheckpointSession,
)
from aluclu.alc_r0.host import SMOLLM2_135M_CONFIG, VerifiedHost
from aluclu.alc_r0.research_capsule import ResearchCapsuleV0


class HostWrapperError(ValueError):
    """A base, runtime, or mount is outside the pinned R0 wrapper contract."""


class PinnedLlamaCapsuleWrapper(nn.Module):
    """Run the real pinned decoder blocks, applying factors after named ports."""

    def __init__(self, host: VerifiedHost) -> None:
        super().__init__()
        if not isinstance(host, VerifiedHost):
            raise TypeError("a verified host object is required")
        if version("transformers") != "5.17.0":
            raise HostWrapperError("wrapper requires pinned Transformers 5.17.0")
        if not isinstance(host.model, LlamaForCausalLM):
            raise HostWrapperError("wrapper requires the pinned LlamaForCausalLM")
        if host.config_identity != SMOLLM2_135M_CONFIG.as_dict():
            raise HostWrapperError("host configuration identity drift")
        if host.model.training or any(p.requires_grad for p in host.model.parameters()):
            raise HostWrapperError("host base must be frozen and in eval mode")
        if len(host.model.model.layers) != 30:
            raise HostWrapperError("host decoder depth drift")

        self.base = host.model
        self.capsule: ResearchCapsuleV0 | None = None
        self._initialize_checkpoint_controller()
        self.eval()

    def _initialize_checkpoint_controller(self) -> None:
        self._assert_checkpoint_mutation_allowed()
        if "_checkpoint_controller" in self.__dict__:
            raise CheckpointExecutionError("checkpoint controller already initialized")
        self._checkpoint_controller = CheckpointController(
            self,
            base_getter=lambda: self.base,
            factor_getter=self._checkpoint_factors,
            layer_count=30,
        )

    def _checkpoint_factors(self) -> nn.Module:
        if self.capsule is None:
            raise CheckpointExecutionError("checkpoint requires mounted capsule")
        return self.capsule

    def checkpoint_session(self) -> CheckpointSession:
        """Create an owner-local lease; this does not authorize model training.

        The checkpoint forward path and host computational inventory are separate
        integration gates. Default forward is denied during an active lease.
        """
        return self._checkpoint_controller.session()

    def _assert_checkpoint_mutation_allowed(self) -> None:
        controller = self.__dict__.get("_checkpoint_controller")
        if controller is not None:
            controller.assert_mutation_allowed()

    def __setattr__(self, name, value) -> None:
        self._assert_checkpoint_mutation_allowed()
        if name == "_checkpoint_controller" and name in self.__dict__:
            raise CheckpointExecutionError("checkpoint controller already initialized")
        super().__setattr__(name, value)

    def __delattr__(self, name) -> None:
        self._assert_checkpoint_mutation_allowed()
        if name == "_checkpoint_controller":
            raise CheckpointExecutionError("checkpoint controller cannot be deleted")
        super().__delattr__(name)

    def _apply(self, fn, recurse=True):
        self._assert_checkpoint_mutation_allowed()
        return super()._apply(fn, recurse=recurse)

    def load_state_dict(self, state_dict, strict=True, assign=False):
        self._assert_checkpoint_mutation_allowed()
        return super().load_state_dict(state_dict, strict=strict, assign=assign)

    def requires_grad_(self, requires_grad=True):
        self._assert_checkpoint_mutation_allowed()
        return super().requires_grad_(requires_grad)

    def zero_grad(self, set_to_none=True) -> None:
        self._assert_checkpoint_mutation_allowed()
        super().zero_grad(set_to_none=set_to_none)

    def add_module(self, name, module) -> None:
        self._assert_checkpoint_mutation_allowed()
        super().add_module(name, module)

    def register_module(self, name, module) -> None:
        # nn.Module's alias otherwise bypasses this class's add_module override.
        self.add_module(name, module)

    def set_submodule(self, target, module, strict=False) -> None:
        self._assert_checkpoint_mutation_allowed()
        super().set_submodule(target, module, strict=strict)

    def register_parameter(self, name, param) -> None:
        self._assert_checkpoint_mutation_allowed()
        super().register_parameter(name, param)

    def register_buffer(self, name, tensor, persistent=True) -> None:
        self._assert_checkpoint_mutation_allowed()
        super().register_buffer(name, tensor, persistent=persistent)

    def train(self, mode: bool = True) -> PinnedLlamaCapsuleWrapper:
        self._assert_checkpoint_mutation_allowed()
        super().train(mode)
        self.base.eval()
        return self

    def mount(self, capsule: ResearchCapsuleV0) -> None:
        self._assert_checkpoint_mutation_allowed()
        if not isinstance(capsule, ResearchCapsuleV0):
            raise TypeError("mount requires ResearchCapsuleV0")
        base_parameter = next(self.base.parameters())
        for parameter in capsule.parameters():
            if (
                parameter.device != base_parameter.device
                or parameter.dtype != torch.float32
            ):
                raise HostWrapperError(
                    "capsule factors must be FP32 on the base device"
                )
        self.capsule = capsule
        capsule.train(self.training)

    def detach(self) -> None:
        self._assert_checkpoint_mutation_allowed()
        self.capsule = None

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
        return decoder_layer(
            hidden_states,
            attention_mask=attention_mask,
            position_embeddings=position_embeddings,
            position_ids=position_ids,
            past_key_values=past_key_values,
            use_cache=use_cache,
        )

    def forward(
        self,
        input_ids: torch.Tensor | None = None,
        attention_mask: torch.Tensor | None = None,
        position_ids: torch.Tensor | None = None,
        past_key_values: Cache | None = None,
        inputs_embeds: torch.Tensor | None = None,
        labels: torch.Tensor | None = None,
        use_cache: bool | None = None,
        logits_to_keep: int | torch.Tensor = 0,
    ) -> CausalLMOutputWithPast:
        # No default-forward escape hatch while a checkpoint lease is active.
        self._assert_checkpoint_mutation_allowed()
        if self.base.training or any(p.requires_grad for p in self.base.parameters()):
            raise HostWrapperError("host base mode or frozen parameters drifted")
        if (input_ids is None) ^ (inputs_embeds is not None):
            raise ValueError(
                "You must specify exactly one of input_ids or inputs_embeds"
            )

        body = self.base.model
        if inputs_embeds is None:
            assert input_ids is not None
            inputs_embeds = body.embed_tokens(input_ids)
        assert inputs_embeds is not None
        if use_cache is None:
            use_cache = bool(self.base.config.use_cache)
        if use_cache and past_key_values is None:
            past_key_values = DynamicCache(config=self.base.config)
        if position_ids is None:
            past_seen_tokens = (
                past_key_values.get_seq_length() if past_key_values is not None else 0
            )
            position_ids = (
                torch.arange(inputs_embeds.shape[1], device=inputs_embeds.device)
                + past_seen_tokens
            )
            position_ids = position_ids.unsqueeze(0)

        causal_mask = create_causal_mask(
            config=self.base.config,
            inputs_embeds=inputs_embeds,
            attention_mask=attention_mask,
            past_key_values=past_key_values,
            position_ids=position_ids,
        )
        hidden_states = inputs_embeds
        position_embeddings = body.rotary_emb(hidden_states, position_ids=position_ids)
        for index, decoder_layer in enumerate(body.layers):
            hidden_states = self._run_decoder_layer(
                index,
                cast(LlamaDecoderLayer, decoder_layer),
                hidden_states,
                attention_mask=causal_mask,
                position_embeddings=position_embeddings,
                position_ids=position_ids,
                past_key_values=past_key_values,
                use_cache=use_cache,
            )
            if self.capsule is not None and index in self.capsule.ports:
                hidden_states = self.capsule.apply_port(index, hidden_states)

        hidden_states = body.norm(hidden_states)
        slice_indices = (
            slice(-logits_to_keep, None)
            if isinstance(logits_to_keep, int)
            else logits_to_keep
        )
        logits = self.base.lm_head(hidden_states[:, slice_indices, :])
        loss = None
        if labels is not None:
            loss = self.base.loss_function(
                logits=logits, labels=labels, vocab_size=self.base.config.vocab_size
            )
        return CausalLMOutputWithPast(
            loss=loss,
            logits=logits,
            past_key_values=past_key_values,
        )
