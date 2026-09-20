from __future__ import annotations

import hashlib
from pathlib import Path
from types import SimpleNamespace

import pytest
import torch
from torch import nn

from aluclu.alc_r0.acquisition import SnapshotExpectation
from aluclu.alc_r0.host import (
    HostLoadError,
    PinnedHostConfig,
    load_verified_host,
)


class _FakeBackend:
    def __init__(self, config: object, model: nn.Module) -> None:
        self.config = config
        self.model = model
        self.config_calls: list[Path] = []
        self.model_calls: list[tuple[Path, object, torch.dtype]] = []

    def load_config(self, snapshot_root: Path) -> object:
        self.config_calls.append(snapshot_root)
        return self.config

    def load_model(
        self,
        snapshot_root: Path,
        *,
        config: object,
        dtype: torch.dtype,
    ) -> nn.Module:
        self.model_calls.append((snapshot_root, config, dtype))
        return self.model


def _snapshot(tmp_path: Path) -> tuple[Path, SnapshotExpectation]:
    root = tmp_path / "snapshot"
    root.mkdir()
    files = {
        "config.json": b"config",
        "model.safetensors": b"weights",
        "tokenizer.json": b"tokenizer",
        "tokenizer_config.json": b"tokenizer-config",
    }
    for name, data in files.items():
        (root / name).write_bytes(data)
    return root, SnapshotExpectation(
        repository="example/model",
        revision="a" * 40,
        required_sha256={
            name: hashlib.sha256(data).hexdigest() for name, data in files.items()
        },
    )


def _config() -> tuple[SimpleNamespace, PinnedHostConfig]:
    expected = PinnedHostConfig(
        architectures=("ExampleForCausalLM",),
        model_type="example",
        hidden_size=8,
        intermediate_size=16,
        num_hidden_layers=2,
        num_attention_heads=2,
        num_key_value_heads=1,
        vocab_size=32,
        max_position_embeddings=64,
        tie_word_embeddings=True,
        bos_token_id=0,
        eos_token_id=0,
    )
    return SimpleNamespace(**expected.as_dict()), expected


def _offline_environment() -> dict[str, str]:
    return {
        "HF_HUB_OFFLINE": "1",
        "TRANSFORMERS_OFFLINE": "1",
        "HF_DATASETS_OFFLINE": "1",
    }


def test_load_verified_host_is_offline_local_only_and_frozen(tmp_path: Path) -> None:
    root, snapshot = _snapshot(tmp_path)
    config, expected_config = _config()
    model = nn.Linear(2, 2)
    backend = _FakeBackend(config, model)

    loaded = load_verified_host(
        root.resolve(),
        snapshot_expectation=snapshot,
        config_expectation=expected_config,
        backend=backend,
        environment=_offline_environment(),
    )

    assert backend.config_calls == [root.resolve()]
    assert backend.model_calls == [(root.resolve(), config, torch.bfloat16)]
    assert loaded.model is model
    assert loaded.parameter_count == 6
    assert loaded.trainable_parameter_count == 0
    assert loaded.training is False
    assert all(not parameter.requires_grad for parameter in model.parameters())
    assert loaded.acquisition_receipt["revision"] == "a" * 40


@pytest.mark.parametrize(
    "environment",
    [
        {},
        {
            "HF_HUB_OFFLINE": "0",
            "TRANSFORMERS_OFFLINE": "1",
            "HF_DATASETS_OFFLINE": "1",
        },
        {"HF_HUB_OFFLINE": "1", "TRANSFORMERS_OFFLINE": "1"},
    ],
)
def test_load_verified_host_rejects_nonoffline_environment(
    tmp_path: Path,
    environment: dict[str, str],
) -> None:
    root, snapshot = _snapshot(tmp_path)
    config, expected_config = _config()
    backend = _FakeBackend(config, nn.Linear(1, 1))

    with pytest.raises(HostLoadError, match="offline"):
        load_verified_host(
            root.resolve(),
            snapshot_expectation=snapshot,
            config_expectation=expected_config,
            backend=backend,
            environment=environment,
        )
    assert backend.config_calls == []


def test_load_verified_host_rejects_config_drift_before_model_load(
    tmp_path: Path,
) -> None:
    root, snapshot = _snapshot(tmp_path)
    config, expected_config = _config()
    config.hidden_size = 9
    backend = _FakeBackend(config, nn.Linear(1, 1))

    with pytest.raises(HostLoadError, match="hidden_size"):
        load_verified_host(
            root.resolve(),
            snapshot_expectation=snapshot,
            config_expectation=expected_config,
            backend=backend,
            environment=_offline_environment(),
        )
    assert backend.model_calls == []


def test_load_verified_host_rejects_non_module_backend_result(tmp_path: Path) -> None:
    root, snapshot = _snapshot(tmp_path)
    config, expected_config = _config()
    backend = _FakeBackend(config, nn.Linear(1, 1))
    backend.model = "not-a-module"  # type: ignore[assignment]

    with pytest.raises(HostLoadError, match="torch module"):
        load_verified_host(
            root.resolve(),
            snapshot_expectation=snapshot,
            config_expectation=expected_config,
            backend=backend,
            environment=_offline_environment(),
        )
