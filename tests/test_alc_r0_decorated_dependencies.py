"""Actual rotary decorator binding fixture; no host construction or forward."""

import types

import pytest
import torch
from torch import nn
from transformers.models.llama.modeling_llama import LlamaRotaryEmbedding

from aluclu.alc_r0.checkpoint_execution import CheckpointExecutionError
from aluclu.alc_r0.checkpoint_state import computational_state_fingerprint


def test_actual_rotary_decorator_can_be_fingerprinted_without_execution():
    root = nn.Module()
    # Borrow only the installed decorated callable, not a model or rotary module.
    # The fixture never invokes it and has no model dimensions/weights/config.
    root.forward = types.MethodType(LlamaRotaryEmbedding.forward, root)
    first = computational_state_fingerprint({"decorator_fixture": root})
    assert len(first) == 64
    assert first == computational_state_fingerprint({"decorator_fixture": root})


def test_arbitrary_foreign_bound_method_remains_rejected():
    class Foreign:
        def operation(self):
            raise AssertionError("foreign method must never execute")

    root = nn.Module()
    root.callback = Foreign().operation
    with pytest.raises(
        CheckpointExecutionError, match="foreign bound method state unsupported"
    ):
        computational_state_fingerprint({"decorator_fixture": root})


@pytest.mark.parametrize("operation", ["__init__", "clone", "__enter__", "__exit__"])
def test_no_grad_class_operation_replacement_changes_binding(monkeypatch, operation):
    root = nn.Module()
    root.forward = types.MethodType(LlamaRotaryEmbedding.forward, root)
    before = computational_state_fingerprint({"decorator_fixture": root})
    monkeypatch.setattr(torch.no_grad, operation, lambda *args, **kwargs: None)
    assert before != computational_state_fingerprint({"decorator_fixture": root})


@pytest.mark.parametrize("kind", ["extra", "bad_prev", "subclass", "other_method"])
def test_unsupported_context_schema_is_rejected(kind):
    context = torch.no_grad()
    if kind == "extra":
        context.extra = True
    elif kind == "bad_prev":
        context.prev = 1
    elif kind == "subclass":

        class ForeignContext(torch.no_grad):
            pass

        context = ForeignContext()
    root = nn.Module()
    root.factory = context.__enter__ if kind == "other_method" else context.clone
    with pytest.raises(CheckpointExecutionError):
        computational_state_fingerprint({"decorator_fixture": root})


def test_supported_no_grad_decorator_restores_phase_context():
    root = nn.Module()

    @torch.no_grad()
    def forward():
        assert not torch.is_grad_enabled()
        return torch.ones(1, requires_grad=True) * 2

    root.forward = forward
    before = computational_state_fingerprint({"decorator_fixture": root})
    with torch.enable_grad():
        result = root()
        assert not result.requires_grad
        assert torch.is_grad_enabled()
        assert before == computational_state_fingerprint({"decorator_fixture": root})
    with torch.no_grad():
        root()
        assert not torch.is_grad_enabled()
        assert before == computational_state_fingerprint({"decorator_fixture": root})


@pytest.mark.parametrize("operation", ["is_grad_enabled", "set_grad_enabled"])
def test_grad_operation_binding_replacement_is_not_ignored(monkeypatch, operation):
    root = nn.Module()
    root.forward = types.MethodType(LlamaRotaryEmbedding.forward, root)
    before = computational_state_fingerprint({"decorator_fixture": root})
    monkeypatch.setattr(torch, operation, lambda *args, **kwargs: False)
    if operation == "set_grad_enabled":
        with pytest.raises(CheckpointExecutionError, match="no_grad runtime binding"):
            computational_state_fingerprint({"decorator_fixture": root})
    else:
        assert before != computational_state_fingerprint({"decorator_fixture": root})
