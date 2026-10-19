"""Exact-wrapper method inventory on tiny modules, not actual-host parity."""

import pytest
from torch import nn

from aluclu.alc_r0.checkpoint_execution import CheckpointExecutionError
from aluclu.alc_r0.checkpoint_state import computational_state_fingerprint
from aluclu.alc_r0.host_wrapper import PinnedLlamaCapsuleWrapper
from aluclu.alc_r0.matched_lora import MatchedQProjLoRA, PinnedLlamaLoRAWrapper
from aluclu.alc_r0.research_capsule import ResearchCapsuleV0

KINDS = (PinnedLlamaCapsuleWrapper, PinnedLlamaLoRAWrapper)
METHODS = (
    "forward",
    "_checkpoint_forward",
    "_checkpoint_factors",
    "_bind_checkpoint_block",
    "_run_decoder_layer",
)


def owner(kind):
    wrapper = kind.__new__(kind)
    nn.Module.__init__(wrapper)
    wrapper.base = nn.Linear(2, 2).requires_grad_(False).eval()
    wrapper.capsule = None
    factors = (
        MatchedQProjLoRA if kind is PinnedLlamaLoRAWrapper else ResearchCapsuleV0
    )(ports=(14,), rank=4, seed=7)
    setattr(wrapper, "lora" if kind is PinnedLlamaLoRAWrapper else "capsule", factors)
    wrapper._initialize_checkpoint_controller()
    wrapper.train()
    return wrapper


@pytest.mark.parametrize("kind", KINDS)
def test_exact_wrapper_inventory_stable_without_enabling_callback(kind):
    wrapper = owner(kind)
    first = computational_state_fingerprint({"wrapper": wrapper})
    assert computational_state_fingerprint({"wrapper": wrapper}) == first
    assert wrapper._checkpoint_controller.state_fingerprint_getter is None


@pytest.mark.parametrize("kind", KINDS)
@pytest.mark.parametrize("name", METHODS)
@pytest.mark.parametrize("changed", ["code", "defaults"])
def test_wrapper_method_state_drift_changes_fingerprint(
    kind, name, changed, monkeypatch
):
    wrapper = owner(kind)
    first = computational_state_fingerprint({"wrapper": wrapper})
    function = getattr(kind, name)
    if changed == "code":
        monkeypatch.setattr(
            function, "__code__", function.__code__.replace(co_name="drift")
        )
    else:
        monkeypatch.setattr(function, "__defaults__", (987,))
    assert computational_state_fingerprint({"wrapper": wrapper}) != first


@pytest.mark.parametrize("kind", KINDS)
@pytest.mark.parametrize("changed", ["override", "unknown", "foreign_controller"])
def test_wrapper_unreviewed_state_rejected(kind, changed):
    wrapper = owner(kind)
    if changed == "override":
        wrapper._bind_checkpoint_block = lambda *args: None
    elif changed == "unknown":
        wrapper.unreviewed_scale = 1.0
    else:
        wrapper.__dict__["_checkpoint_controller"] = owner(kind)._checkpoint_controller
    with pytest.raises(CheckpointExecutionError):
        computational_state_fingerprint({"wrapper": wrapper})


@pytest.mark.parametrize("kind", KINDS)
def test_wrapper_subclass_rejected(kind):
    subclass = type("Unreviewed", (kind,), {})
    wrapper = owner(subclass)
    with pytest.raises(CheckpointExecutionError):
        computational_state_fingerprint({"wrapper": wrapper})


@pytest.mark.parametrize("kind", KINDS)
@pytest.mark.parametrize("field", ["base", "capsule", "_checkpoint_controller"])
def test_wrapper_class_shadow_rejected_without_descriptor_execution(
    kind, field, monkeypatch
):
    wrapper = owner(kind)
    calls = []

    def read(instance):
        calls.append(1)
        return None

    monkeypatch.setattr(kind, field, property(read), raising=False)
    with pytest.raises(CheckpointExecutionError, match="class field shadow"):
        computational_state_fingerprint({"wrapper": wrapper})
    assert not calls


@pytest.mark.parametrize("changed", ["code", "defaults"])
def test_q_attention_wrapper_method_state_recorded(changed, monkeypatch):
    wrapper = owner(PinnedLlamaLoRAWrapper)
    first = computational_state_fingerprint({"wrapper": wrapper})
    function = PinnedLlamaLoRAWrapper._q_lora_attention
    if changed == "code":
        monkeypatch.setattr(
            function, "__code__", function.__code__.replace(co_name="drift")
        )
    else:
        monkeypatch.setattr(function, "__defaults__", (987,))
    assert computational_state_fingerprint({"wrapper": wrapper}) != first


@pytest.mark.parametrize("kind", KINDS)
@pytest.mark.parametrize("changed", ["missing", "wrong"])
def test_wrapper_missing_or_wrong_factor_arm_denied(kind, changed):
    wrapper = owner(kind)
    field = "lora" if kind is PinnedLlamaLoRAWrapper else "capsule"
    factor_kind = (
        ResearchCapsuleV0 if kind is PinnedLlamaLoRAWrapper else MatchedQProjLoRA
    )
    setattr(
        wrapper,
        field,
        None if changed == "missing" else factor_kind(ports=(14,), rank=4, seed=7),
    )
    with pytest.raises(CheckpointExecutionError, match="exact wrapper factors"):
        computational_state_fingerprint({"wrapper": wrapper})


@pytest.mark.parametrize("kind", KINDS)
def test_wrapper_method_drift_denied_at_owned_preparation_boundary(kind, monkeypatch):
    wrapper = owner(kind)
    controller = wrapper._checkpoint_controller
    controller._install_state_fingerprint_getter(
        lambda: computational_state_fingerprint({"wrapper": wrapper})
    )
    with pytest.raises(CheckpointExecutionError, match="fingerprint drifted"):
        with controller.session() as session:
            function = kind._bind_checkpoint_block
            monkeypatch.setattr(
                function, "__code__", function.__code__.replace(co_name="drift")
            )
            session.begin_forward(wrapper, {})
    assert controller._active is None
    assert all(parameter.grad is None for parameter in wrapper.parameters())
