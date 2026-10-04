"""Single offline loading path for the pinned ALC-R0 host model."""

from __future__ import annotations

import os
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Protocol

import torch
from torch import nn

from aluclu.alc_r0.acquisition import (
    SMOLLM2_135M,
    SnapshotExpectation,
    verify_model_snapshot,
)

_OFFLINE_FLAGS = ("HF_HUB_OFFLINE", "TRANSFORMERS_OFFLINE", "HF_DATASETS_OFFLINE")


class HostLoadError(RuntimeError):
    """Raised when the pinned host cannot be loaded without contract drift."""


@dataclass(frozen=True)
class PinnedHostConfig:
    architectures: tuple[str, ...]
    model_type: str
    hidden_size: int
    intermediate_size: int
    num_hidden_layers: int
    num_attention_heads: int
    num_key_value_heads: int
    vocab_size: int
    max_position_embeddings: int
    tie_word_embeddings: bool
    bos_token_id: int
    eos_token_id: int

    def as_dict(self) -> dict[str, object]:
        return {
            "architectures": list(self.architectures),
            "model_type": self.model_type,
            "hidden_size": self.hidden_size,
            "intermediate_size": self.intermediate_size,
            "num_hidden_layers": self.num_hidden_layers,
            "num_attention_heads": self.num_attention_heads,
            "num_key_value_heads": self.num_key_value_heads,
            "vocab_size": self.vocab_size,
            "max_position_embeddings": self.max_position_embeddings,
            "tie_word_embeddings": self.tie_word_embeddings,
            "bos_token_id": self.bos_token_id,
            "eos_token_id": self.eos_token_id,
        }


SMOLLM2_135M_CONFIG = PinnedHostConfig(
    architectures=("LlamaForCausalLM",),
    model_type="llama",
    hidden_size=576,
    intermediate_size=1536,
    num_hidden_layers=30,
    num_attention_heads=9,
    num_key_value_heads=3,
    vocab_size=49152,
    max_position_embeddings=8192,
    tie_word_embeddings=True,
    bos_token_id=0,
    eos_token_id=0,
)


class HostBackend(Protocol):
    def load_config(self, snapshot_root: Path) -> object: ...

    def load_model(
        self,
        snapshot_root: Path,
        *,
        config: object,
        dtype: torch.dtype,
    ) -> nn.Module: ...


class TransformersHostBackend:
    """The production backend; all Hub fallbacks are disabled explicitly."""

    def load_config(self, snapshot_root: Path) -> object:
        from transformers import AutoConfig

        return AutoConfig.from_pretrained(
            str(snapshot_root),
            local_files_only=True,
            trust_remote_code=False,
        )

    def load_model(
        self,
        snapshot_root: Path,
        *,
        config: object,
        dtype: torch.dtype,
    ) -> nn.Module:
        from transformers import AutoModelForCausalLM

        model = AutoModelForCausalLM.from_pretrained(
            str(snapshot_root),
            config=config,
            local_files_only=True,
            trust_remote_code=False,
            use_safetensors=True,
            dtype=dtype,
        )
        if not isinstance(model, nn.Module):
            raise HostLoadError("Transformers backend did not return a torch module")
        return model


@dataclass(frozen=True)
class VerifiedHost:
    model: nn.Module
    acquisition_receipt: Mapping[str, Any]
    config_identity: Mapping[str, object]
    parameter_count: int
    trainable_parameter_count: int

    @property
    def training(self) -> bool:
        return self.model.training


def _assert_offline(environment: Mapping[str, str]) -> None:
    missing = [name for name in _OFFLINE_FLAGS if environment.get(name) != "1"]
    if missing:
        raise HostLoadError(
            "offline host loading requires flags set to 1: " + ", ".join(missing)
        )


def _validate_config(config: object, expected: PinnedHostConfig) -> dict[str, object]:
    expected_fields = expected.as_dict()
    observed: dict[str, object] = {}
    for name, expected_value in expected_fields.items():
        try:
            value = getattr(config, name)
        except AttributeError as exc:
            raise HostLoadError(f"host config is missing {name}") from exc
        if name == "architectures":
            try:
                value = list(value)
            except TypeError as exc:
                raise HostLoadError(
                    "host config architectures is not iterable"
                ) from exc
        if value != expected_value:
            raise HostLoadError(
                f"host config mismatch for {name}: {value!r} != {expected_value!r}"
            )
        observed[name] = value
    return observed


def load_verified_host(
    snapshot_root: Path,
    *,
    snapshot_expectation: SnapshotExpectation = SMOLLM2_135M,
    config_expectation: PinnedHostConfig = SMOLLM2_135M_CONFIG,
    backend: HostBackend | None = None,
    environment: Mapping[str, str] = os.environ,
    device: str | torch.device = "cpu",
    dtype: torch.dtype = torch.bfloat16,
) -> VerifiedHost:
    """Verify, load, freeze, and return the only accepted ALC-R0 host."""

    _assert_offline(environment)
    receipt = verify_model_snapshot(snapshot_root, expectation=snapshot_expectation)
    selected_backend = backend if backend is not None else TransformersHostBackend()
    try:
        config = selected_backend.load_config(snapshot_root)
    except HostLoadError:
        raise
    except Exception as exc:
        raise HostLoadError("offline host config load failed") from exc
    config_identity = _validate_config(config, config_expectation)
    try:
        model = selected_backend.load_model(snapshot_root, config=config, dtype=dtype)
    except HostLoadError:
        raise
    except Exception as exc:
        raise HostLoadError("offline SafeTensors host load failed") from exc
    if not isinstance(model, nn.Module):
        raise HostLoadError("host backend did not return a torch module")

    model.to(device=device)
    model.eval()
    for parameter in model.parameters():
        parameter.requires_grad_(False)
    parameter_count = sum(parameter.numel() for parameter in model.parameters())
    trainable_parameter_count = sum(
        parameter.numel() for parameter in model.parameters() if parameter.requires_grad
    )
    if parameter_count <= 0:
        raise HostLoadError("host model has no parameters")
    if trainable_parameter_count != 0:
        raise HostLoadError("host base parameters are not completely frozen")
    return VerifiedHost(
        model=model,
        acquisition_receipt=receipt,
        config_identity=config_identity,
        parameter_count=parameter_count,
        trainable_parameter_count=trainable_parameter_count,
    )
