"""Reviewer regression: class None is not a missing registered field."""

import pytest
from test_alc_r0_wrapper_method_inventory import KINDS, owner

from aluclu.alc_r0.checkpoint_execution import CheckpointExecutionError
from aluclu.alc_r0.checkpoint_state import computational_state_fingerprint
from aluclu.alc_r0.matched_lora import PinnedLlamaLoRAWrapper


@pytest.mark.parametrize("kind", KINDS)
@pytest.mark.parametrize("selected", ["base", "mount"])
def test_none_class_shadow_rejected_even_when_registered_module_unchanged(
    kind, selected, monkeypatch
):
    wrapper = owner(kind)
    field = (
        selected
        if selected == "base"
        else ("lora" if kind is PinnedLlamaLoRAWrapper else "capsule")
    )
    original = wrapper._modules[field]
    before = computational_state_fingerprint({"wrapper": wrapper})
    assert len(before) == 64
    monkeypatch.setattr(kind, field, None, raising=False)
    assert wrapper._modules[field] is original
    assert getattr(wrapper, field) is None
    with pytest.raises(CheckpointExecutionError, match="class field shadow"):
        computational_state_fingerprint({"wrapper": wrapper})
