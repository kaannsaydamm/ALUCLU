"""Owner-local q/v inventory with fake CPU base; not actual-host admission."""

from types import ModuleType

import pytest
import torch
from test_alc_r0_reference_qv_wrapper import data, fake_layer, fake_wrapper, live
from transformers import LlamaConfig

from aluclu.alc_r0 import reference_qv_lora, reference_qv_wrapper
from aluclu.alc_r0.checkpoint_execution import CheckpointExecutionError
from aluclu.alc_r0.checkpoint_state import computational_state_fingerprint


def test_qv_inventory_enables_without_replacing_controller():
    wrapper = fake_wrapper().train()
    controller = wrapper._checkpoint_controller
    wrapper.enable_checkpoint_inventory()
    getter = controller.state_fingerprint_getter
    assert getter() == computational_state_fingerprint({"wrapper": wrapper})
    wrapper.enable_checkpoint_inventory()
    assert controller is wrapper._checkpoint_controller
    assert getter is controller.state_fingerprint_getter
    with wrapper.checkpoint_session():
        with pytest.raises(CheckpointExecutionError, match="lease"):
            wrapper.enable_checkpoint_inventory()


@pytest.mark.parametrize(
    "mutation", ["reference", "method", "base", "helper", "linear"]
)
def test_qv_guard_rejects_drift_before_forward(mutation, monkeypatch):
    wrapper = fake_wrapper().train()
    wrapper.enable_checkpoint_inventory()
    controller = wrapper._checkpoint_controller
    with pytest.raises(CheckpointExecutionError):
        with wrapper.checkpoint_session() as session:
            if mutation == "reference":
                wrapper.reference.factors["29"]["v"].B.data.add_(1)
            elif mutation == "base":
                wrapper.base.weight.data.add_(1)
            elif mutation == "method":
                method = type(wrapper)._bind_checkpoint_block
                monkeypatch.setattr(method, "__defaults__", (42,))
            elif mutation == "helper":
                monkeypatch.setattr(
                    reference_qv_wrapper, "_q_attention_with_projection", lambda: None
                )
            else:
                replacement = ModuleType("factor_fixture")
                replacement.__dict__.update(vars(reference_qv_lora.F))
                original = replacement.linear

                def changed(*args, **kwargs):
                    return original(*args, **kwargs) * 2

                replacement.linear = changed
                monkeypatch.setattr(reference_qv_lora, "F", replacement)
            session.begin_forward(wrapper, {"position_ids": torch.zeros(1)})
    assert controller._active is None
    assert all(parameter.grad is None for parameter in wrapper.parameters())


@pytest.mark.parametrize(
    "field", ["reference", "capsule", "lora", "_checkpoint_controller"]
)
def test_qv_class_field_shadow_rejected_without_property_call(field, monkeypatch):
    wrapper = fake_wrapper()
    controller = wrapper._checkpoint_controller
    calls = []

    def read(instance):
        calls.append(1)
        return None

    monkeypatch.setattr(type(wrapper), field, property(read), raising=False)
    with pytest.raises(CheckpointExecutionError, match="shadow"):
        wrapper.enable_checkpoint_inventory()
    assert calls == []
    assert controller.state_fingerprint_getter is None


def test_qv_wrong_arm_and_unknown_fields_not_admitted():
    wrapper = fake_wrapper()
    wrapper.lora = torch.nn.Linear(2, 2)
    with pytest.raises(CheckpointExecutionError):
        wrapper.enable_checkpoint_inventory()
    assert wrapper._checkpoint_controller.state_fingerprint_getter is None


def test_qv_factor_factory_mutation_changes_fingerprint(monkeypatch):
    wrapper = fake_wrapper()
    wrapper.enable_checkpoint_inventory()
    getter = wrapper._checkpoint_controller.state_fingerprint_getter
    before = getter()
    factory = reference_qv_lora.ReferenceQVLoRA.bind_projection
    monkeypatch.setattr(factory, "__kwdefaults__", {"base": None})
    assert getter() != before


@pytest.mark.parametrize(
    "drift", [None, "factor", "base", "registry", "factor_data", "base_data"]
)
def test_owned_qv_block_replay_guards_original_execution_objects(drift):
    wrapper = fake_wrapper()
    layer = fake_layer()
    layer.self_attn.config = LlamaConfig(
        hidden_size=576,
        num_attention_heads=9,
        num_key_value_heads=3,
    )
    layer.self_attn.config._attn_implementation = "eager"
    wrapper.base = layer
    wrapper.train()
    for target in ("q", "v"):
        with torch.no_grad():
            wrapper.reference.factors["29"][target].B.fill_(0.01)
    wrapper.enable_checkpoint_inventory()
    parameters = tuple(wrapper.reference.factors["29"].parameters())
    hidden = torch.linspace(-1, 1, 1152).reshape(1, 2, 576)
    expected = live(wrapper, 29, layer, hidden)
    gradients = torch.autograd.grad(expected.square().sum(), parameters)
    operation = wrapper._bind_checkpoint_block(29, layer)
    calls = []

    def block(value, metadata):
        calls.append(1)
        return operation(value, metadata)

    def execute():
        with wrapper.checkpoint_session() as session:
            ticket = session.begin_forward(wrapper, data())
            output = hidden
            for index in range(30):
                # The first29 fixture blocks are identities; only the final q/v
                # block is exercised. This is not a full-host all-layer proof.
                output = ticket.run(
                    index,
                    block if index == 29 else lambda value, metadata: value,
                    output,
                )
            ticket.bind_output(output)
            if drift == "factor":
                with torch.no_grad():
                    parameters[-1].add_(1)
            elif drift == "base":
                with torch.no_grad():
                    layer.self_attn.v_proj.weight.add_(1)
            elif drift == "factor_data":
                parameters[-1].data.add_(1)
            elif drift == "base_data":
                layer.self_attn.v_proj.weight.data.add_(1)
            elif drift == "registry":
                wrapper.reference.factors["29"]["v"].B = torch.nn.Parameter(
                    parameters[-1].detach().clone()
                )
            session.backward(output.square().sum())
            if drift is None:
                assert torch.equal(output, expected)

    if drift is None:
        execute()
        assert len(calls) == 2
        for parameter, gradient in zip(parameters, gradients, strict=True):
            assert torch.equal(parameter.grad, gradient)
    else:
        with pytest.raises(CheckpointExecutionError):
            execute()
        # Existing contract: versioned/registry drift rejects before replay;
        # unversioned .data writes are detected by the final byte digest only.
        assert len(calls) == (2 if drift in {"factor_data", "base_data"} else 1)
        assert all(parameter.grad is None for parameter in wrapper.parameters())
    assert wrapper._checkpoint_controller._active is None
