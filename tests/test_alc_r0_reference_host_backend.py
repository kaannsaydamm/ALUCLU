"""Stub Transformers load contract; no actual config/model/snapshot loading."""

import sys
from types import SimpleNamespace

import pytest
import torch

from aluclu.alc_r0.host import HostLoadError, TransformersHostBackend


@pytest.fixture
def stub_transformers(monkeypatch):
    calls = []
    model = torch.nn.Linear(1, 1)
    model.config = SimpleNamespace(_attn_implementation="eager")

    def load(path, **kwargs):
        calls.append((path, kwargs))
        return model

    monkeypatch.setitem(
        sys.modules,
        "transformers",
        SimpleNamespace(
            AutoModelForCausalLM=SimpleNamespace(from_pretrained=load),
        ),
    )
    return calls, model


def test_default_backend_preserves_original_load_arguments(stub_transformers, tmp_path):
    calls, model = stub_transformers
    config = object()
    assert (
        TransformersHostBackend().load_model(
            tmp_path, config=config, dtype=torch.float32
        )
        is model
    )
    assert calls == [
        (
            str(tmp_path),
            {
                "config": config,
                "local_files_only": True,
                "trust_remote_code": False,
                "use_safetensors": True,
                "dtype": torch.float32,
            },
        )
    ]


def test_explicit_reference_backend_loads_eager_without_mutating_default(
    stub_transformers, tmp_path
):
    calls, model = stub_transformers
    config = object()
    backend = TransformersHostBackend(attention_implementation="eager")
    assert backend.load_model(tmp_path, config=config, dtype=torch.bfloat16) is model
    assert calls[0][1]["attn_implementation"] == "eager"
    assert calls[0][1]["local_files_only"] is True
    assert calls[0][1]["trust_remote_code"] is False
    assert calls[0][1]["use_safetensors"] is True
    TransformersHostBackend().load_model(tmp_path, config=config, dtype=torch.float32)
    assert "attn_implementation" not in calls[1][1]


@pytest.mark.parametrize("route", [True, False, 1, "sdpa", "flash_attention_2"])
def test_unreviewed_reference_route_rejected_before_backend_import(route):
    with pytest.raises(HostLoadError):
        TransformersHostBackend(attention_implementation=route)


def test_backend_ignoring_declared_eager_route_rejected(stub_transformers, tmp_path):
    _, model = stub_transformers
    model.config._attn_implementation = "sdpa"
    with pytest.raises(HostLoadError, match="eager"):
        TransformersHostBackend(attention_implementation="eager").load_model(
            tmp_path,
            config=object(),
            dtype=torch.float32,
        )
