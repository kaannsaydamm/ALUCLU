"""Actual rotary decorator binding fixture; no host construction or forward."""

import types

import pytest
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
