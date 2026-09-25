"""Explicit decoder-block interposition for the pinned R0 Llama host.

This is a research reference path, not the R0.0 authorization gate. The same
layer iteration runs with and without a mounted capsule so no-capsule parity
can be tested independently against the official Transformers forward.
"""

from __future__ import annotations

from importlib.metadata import version

import torch
from torch import nn
from transformers.cache_utils import Cache, DynamicCache
from transformers.masking_utils import create_causal_mask
from transformers.modeling_outputs import CausalLMOutputWithPast
from transformers.models.llama.modeling_llama import LlamaForCausalLM

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
        self.eval()

    def train(self, mode: bool = True) -> PinnedLlamaCapsuleWrapper:
        super().train(mode)
        self.base.eval()
        return self

    def mount(self, capsule: ResearchCapsuleV0) -> None:
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
        self.capsule = None

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
            hidden_states = decoder_layer(
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
