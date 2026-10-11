"""Explicit q/v attention with fake CPU blocks, not actual host qualification."""

import pytest
import torch
from test_alc_r0_bound_decoder_blocks import FakeLoRALayer
from torch import nn
from torch.utils.checkpoint import checkpoint

from aluclu.alc_r0.checkpoint_execution import CheckpointExecutionError
from aluclu.alc_r0.matched_lora import _q_attention_with_projection
from aluclu.alc_r0.reference_qv_lora import ReferenceQVLoRA
from aluclu.alc_r0.reference_qv_wrapper import PinnedLlamaQVReferenceWrapper


def fake_layer():
    layer = FakeLoRALayer()
    attention = layer.self_attn
    attention.k_proj = nn.Linear(576, 192, bias=False)
    attention.v_proj = nn.Linear(576, 192, bias=False)
    attention.head_dim = 64
    attention.num_key_value_groups = 3
    attention.scaling = 64**-0.5
    attention.layer_idx = 0
    return layer.requires_grad_(False).eval()


def fake_wrapper():
    cls = PinnedLlamaQVReferenceWrapper
    wrapper = cls.__new__(cls)
    nn.Module.__init__(wrapper)
    wrapper.capsule = None
    wrapper.reference = ReferenceQVLoRA(seed=17)
    wrapper.base = nn.Linear(576, 576, bias=False).requires_grad_(False).eval()
    wrapper._initialize_checkpoint_controller()
    return wrapper


def data():
    return {
        "attention_mask": None,
        "position_ids": torch.tensor([[0, 1]]),
        "cos": torch.ones(1, 2, 64),
        "sin": torch.zeros(1, 2, 64),
    }


def live(wrapper, index, layer, hidden):
    metadata = data()
    return wrapper._run_decoder_layer(
        index,
        layer,
        hidden,
        attention_mask=None,
        position_embeddings=(metadata["cos"], metadata["sin"]),
        position_ids=metadata["position_ids"],
        past_key_values=None,
        use_cache=False,
    )


@pytest.mark.parametrize("index", [0, 14, 29])
def test_qv_live_bound_replay_and_gradients(index):
    wrapper, layer = fake_wrapper(), fake_layer()
    hidden = torch.linspace(-1, 1, 1152).reshape(1, 2, 576)
    for target in ("q", "v"):
        with torch.no_grad():
            wrapper.reference.factors[str(index)][target].B.fill_(0.01)
    parameters = tuple(wrapper.reference.factors[str(index)].parameters())
    expected = live(wrapper, index, layer, hidden)
    expected_grad = torch.autograd.grad(expected.square().sum(), parameters)
    block = wrapper._bind_checkpoint_block(index, layer)
    actual = checkpoint(lambda x: block(x, data()), hidden, use_reentrant=False)
    wrapper.reference = None  # Raw closure is not an integrity guard.
    actual.square().sum().backward()
    assert torch.equal(actual, expected)
    for parameter, gradient in zip(parameters, expected_grad, strict=True):
        assert torch.equal(parameter.grad, gradient)
        assert torch.count_nonzero(gradient) > 0
    assert all(parameter.grad is None for parameter in layer.parameters())


def test_every_layer_has_q_and_v_binding_and_v_delta_changes_output():
    wrapper, layer = fake_wrapper(), fake_layer()
    blocks = [wrapper._bind_checkpoint_block(i, layer) for i in range(30)]
    assert len(blocks) == 30
    hidden = torch.ones(1, 2, 576)
    original = live(wrapper, 0, layer, hidden)
    with torch.no_grad():
        wrapper.reference.factors["0"]["v"].B.fill_(0.02)
    assert not torch.equal(live(wrapper, 0, layer, hidden), original)


@pytest.mark.parametrize("index", [True, -1, 30, 1.5])
def test_invalid_bound_index(index):
    with pytest.raises(CheckpointExecutionError):
        fake_wrapper()._bind_checkpoint_block(index, fake_layer())


def test_active_lease_denies_detach_and_default_forward():
    wrapper = fake_wrapper().train()
    reference = wrapper.reference
    with wrapper.checkpoint_session():
        with pytest.raises(CheckpointExecutionError):
            wrapper.detach()
        with pytest.raises(CheckpointExecutionError):
            wrapper(input_ids=torch.ones(1, 2, dtype=torch.long), use_cache=False)
    assert wrapper.reference is reference
    wrapper.detach()
    with pytest.raises(CheckpointExecutionError):
        with wrapper.checkpoint_session():
            pass


def test_mount_validates_all_targets_before_publication():
    wrapper = fake_wrapper()
    wrapper.base = nn.Module()
    wrapper.base.model = nn.Module()
    wrapper.base.model.layers = nn.ModuleList([fake_layer() for _ in range(30)])
    wrapper.base.requires_grad_(False).eval()
    incoming = ReferenceQVLoRA(seed=2)
    wrapper.mount_reference(incoming)
    assert wrapper.reference is incoming
    wrapper.base.model.layers[29].self_attn.v_proj = nn.Linear(576, 2, bias=False)
    previous = wrapper.reference
    with pytest.raises(ValueError):
        wrapper.mount_reference(ReferenceQVLoRA(seed=3))
    assert wrapper.reference is previous


def test_checkpoint_forward_still_denies_missing_inventory():
    wrapper = fake_wrapper().train()
    with pytest.raises(CheckpointExecutionError, match="inventory"):
        with wrapper.checkpoint_session() as session:
            wrapper(
                input_ids=torch.ones(1, 2, dtype=torch.long),
                use_cache=False,
                checkpoint_session=session,
            )


def test_zero_reference_preserves_base_projection_attention_and_cache_values():
    wrapper, layer = fake_wrapper(), fake_layer()
    attention = layer.self_attn
    hidden = torch.randn(1, 2, 576)
    metadata = data()
    query = wrapper.reference.bind_projection(
        layer=0, target="q", base=attention.q_proj
    )
    value = wrapper.reference.bind_projection(
        layer=0, target="v", base=attention.v_proj
    )

    class RecordingCache:
        def update(self, keys, values, index):
            self.keys, self.values, self.index = keys, values, index
            return keys, values

    expected_cache, actual_cache = RecordingCache(), RecordingCache()
    expected = _q_attention_with_projection(
        attention,
        hidden,
        q_projection=attention.q_proj,
        attention_mask=None,
        position_embeddings=(metadata["cos"], metadata["sin"]),
        past_key_values=expected_cache,
    )
    actual = _q_attention_with_projection(
        attention,
        hidden,
        q_projection=query,
        v_projection=value,
        attention_mask=None,
        position_embeddings=(metadata["cos"], metadata["sin"]),
        past_key_values=actual_cache,
    )
    assert torch.equal(actual, expected)
    assert torch.equal(actual_cache.keys, expected_cache.keys)
    assert torch.equal(actual_cache.values, expected_cache.values)
    assert actual_cache.index == expected_cache.index == 0
    with torch.no_grad():
        wrapper.reference.factors["0"]["v"].B.fill_(0.02)
    _q_attention_with_projection(
        attention,
        hidden,
        q_projection=query,
        v_projection=value,
        attention_mask=None,
        position_embeddings=(metadata["cos"], metadata["sin"]),
        past_key_values=actual_cache,
    )
    assert not torch.equal(actual_cache.values, expected_cache.values)
    assert torch.equal(actual_cache.keys, expected_cache.keys)
