"""Captured decoder closures with CPU fake blocks, not actual-host acceptance."""

from types import SimpleNamespace

import pytest
import torch
from torch import nn

from aluclu.alc_r0.checkpoint_execution import CheckpointExecutionError
from aluclu.alc_r0.host_wrapper import PinnedLlamaCapsuleWrapper
from aluclu.alc_r0.matched_lora import MatchedQProjLoRA, PinnedLlamaLoRAWrapper
from aluclu.alc_r0.research_capsule import ResearchCapsuleV0


class FakeDecoder(nn.Module):
    def __init__(self, scale):
        super().__init__()
        self.weight = nn.Parameter(torch.tensor(scale), requires_grad=False)

    def forward(self, hidden, **kwargs):
        assert kwargs["use_cache"] is False
        assert kwargs["past_key_values"] is None
        return hidden * self.weight + kwargs["position_ids"].unsqueeze(-1)


def metadata():
    return {
        "attention_mask": None,
        "position_ids": torch.tensor([[0, 1]]),
        "cos": torch.ones(1, 2, 2),
        "sin": torch.zeros(1, 2, 2),
    }


def capsule_wrapper():
    wrapper = PinnedLlamaCapsuleWrapper.__new__(PinnedLlamaCapsuleWrapper)
    nn.Module.__init__(wrapper)
    wrapper.capsule = ResearchCapsuleV0(ports=(14, 29), rank=4, seed=7)
    with torch.no_grad():
        for item in wrapper.capsule.factors.values():
            item.B.fill_(0.01)
    return wrapper


@pytest.mark.parametrize("index", [0, 14, 29])
def test_capsule_block_places_bound_factor_after_exact_layer(index):
    wrapper = capsule_wrapper()
    layer = FakeDecoder(2.0)
    hidden = torch.linspace(-1, 1, 1152).reshape(1, 2, 576)
    block = wrapper._bind_checkpoint_block(index, layer)
    expected = layer(
        hidden,
        position_ids=metadata()["position_ids"],
        use_cache=False,
        past_key_values=None,
    )
    if index in wrapper.capsule.ports:
        expected = wrapper.capsule.apply_port(index, expected)
    assert torch.equal(block(hidden, metadata()), expected)


def test_capsule_blocks_bind_each_layer_and_survive_mount_replacement():
    wrapper = capsule_wrapper()
    hidden = torch.ones(1, 2, 576)
    blocks = [
        wrapper._bind_checkpoint_block(i, FakeDecoder(float(i + 1))) for i in range(30)
    ]
    expected = [block(hidden, metadata()).detach().clone() for block in blocks]
    wrapper.capsule = ResearchCapsuleV0(ports=(14,), rank=4, seed=0)
    for block, value in zip(blocks, expected, strict=True):
        assert torch.equal(block(hidden, metadata()), value)


@pytest.mark.parametrize("index", [14, 29])
def test_capsule_block_replay_retains_original_factors_and_gradients(index):
    wrapper = capsule_wrapper()
    old = wrapper.capsule
    layer = FakeDecoder(2.0)
    block = wrapper._bind_checkpoint_block(index, layer)
    hidden = torch.linspace(-1, 1, 1152).reshape(1, 2, 576)
    parameters = tuple(old.factors[str(index)].parameters())
    expected = block(hidden, metadata())
    expected_grad = torch.autograd.grad(expected.square().sum(), parameters)
    from torch.utils.checkpoint import checkpoint

    actual = checkpoint(
        lambda h: block(h, metadata()),
        hidden,
        use_reentrant=False,
        preserve_rng_state=True,
    )
    wrapper.capsule = None
    actual.square().sum().backward()
    assert torch.equal(actual, expected)
    for parameter, gradient in zip(parameters, expected_grad, strict=True):
        assert torch.equal(parameter.grad, gradient)


class FakeAttention(nn.Module):
    def __init__(self):
        super().__init__()
        self.q_proj = nn.Linear(576, 576, bias=False)
        self.k_proj = nn.Linear(576, 2, bias=False)
        self.v_proj = nn.Linear(576, 2, bias=False)
        self.o_proj = nn.Linear(576, 576, bias=False)
        self.head_dim = 2
        self.num_key_value_groups = 288
        self.scaling = 2**-0.5
        self.attention_dropout = 0.0
        self.config = SimpleNamespace(_attn_implementation="eager")


class FakeLoRALayer(nn.Module):
    def __init__(self):
        super().__init__()
        self.input_layernorm = nn.Identity()
        self.post_attention_layernorm = nn.Identity()
        self.self_attn = FakeAttention()
        self.mlp = nn.Linear(576, 576, bias=False)
        self.requires_grad_(False).eval()


@pytest.mark.parametrize("index", [14, 29])
def test_lora_bound_block_equals_live_path_without_reading_mount_on_replay(index):
    wrapper = PinnedLlamaLoRAWrapper.__new__(PinnedLlamaLoRAWrapper)
    nn.Module.__init__(wrapper)
    wrapper.lora = MatchedQProjLoRA(ports=(14, 29), rank=4, seed=7)
    with torch.no_grad():
        for item in wrapper.lora.factors.values():
            item.B.fill_(0.01)
    layer = FakeLoRALayer()
    hidden = torch.linspace(-1, 1, 1152).reshape(1, 2, 576)
    data = metadata()
    parameters = tuple(wrapper.lora.factors[str(index)].parameters())
    expected = wrapper._run_decoder_layer(
        index,
        layer,
        hidden,
        attention_mask=None,
        position_embeddings=(data["cos"], data["sin"]),
        position_ids=data["position_ids"],
        past_key_values=None,
        use_cache=False,
    )
    expected_grad = torch.autograd.grad(expected.square().sum(), parameters)
    block = wrapper._bind_checkpoint_block(index, layer)
    from torch.utils.checkpoint import checkpoint

    actual = checkpoint(
        lambda h: block(h, data), hidden, use_reentrant=False, preserve_rng_state=True
    )
    wrapper.lora = None
    actual.square().sum().backward()
    assert torch.equal(actual, expected)
    for parameter, gradient in zip(parameters, expected_grad, strict=True):
        assert torch.equal(parameter.grad, gradient)


@pytest.mark.parametrize("kind", [PinnedLlamaCapsuleWrapper, PinnedLlamaLoRAWrapper])
@pytest.mark.parametrize("index", [-1, 30, True, 1.5])
def test_invalid_bound_layer_index_denied(kind, index):
    wrapper = kind.__new__(kind)
    nn.Module.__init__(wrapper)
    with pytest.raises(ValueError):
        wrapper._bind_checkpoint_block(index, FakeDecoder(1.0))


def engine_wrapper(kind):
    wrapper = kind.__new__(kind)
    nn.Module.__init__(wrapper)
    wrapper.capsule = None
    factors = (
        MatchedQProjLoRA if kind is PinnedLlamaLoRAWrapper else ResearchCapsuleV0
    )(ports=(14, 29), rank=4, seed=7)
    with torch.no_grad():
        for item in factors.factors.values():
            item.B.fill_(0.01)
    setattr(wrapper, "lora" if kind is PinnedLlamaLoRAWrapper else "capsule", factors)
    wrapper.base = (
        nn.ModuleList(
            [
                FakeLoRALayer()
                if kind is PinnedLlamaLoRAWrapper and i in factors.ports
                else FakeDecoder(1.0001)
                for i in range(30)
            ]
        )
        .requires_grad_(False)
        .eval()
    )
    wrapper._initialize_checkpoint_controller()
    wrapper.train()
    return wrapper, factors


@pytest.mark.parametrize("kind", [PinnedLlamaCapsuleWrapper, PinnedLlamaLoRAWrapper])
@pytest.mark.parametrize("pending", [1, 2])
def test_full_fake_layer_traversal_matches_reference_through_owned_engine(
    kind, pending
):
    wrapper, factors = engine_wrapper(kind)
    hidden = torch.linspace(-1, 1, 1152).reshape(1, 2, 576)
    blocks = [
        wrapper._bind_checkpoint_block(i, layer) for i, layer in enumerate(wrapper.base)
    ]
    data = metadata()
    references = []
    for _ in range(pending):
        reference = hidden
        for i, layer in enumerate(wrapper.base):
            reference = wrapper._run_decoder_layer(
                i,
                layer,
                reference,
                attention_mask=None,
                position_embeddings=(data["cos"], data["sin"]),
                position_ids=data["position_ids"],
                past_key_values=None,
                use_cache=False,
            )
            if kind is PinnedLlamaCapsuleWrapper and i in factors.ports:
                reference = factors.apply_port(i, reference)
        references.append(reference)
    parameters = tuple(factors.parameters())
    expected_grads = torch.autograd.grad(
        sum(reference.square().sum() for reference in references), parameters
    )
    with wrapper.checkpoint_session() as session:
        outputs = []
        for _ in range(pending):
            ticket = session.begin_forward(wrapper, data)
            output = hidden
            for i, block in enumerate(blocks):
                output = ticket.run(i, block, output)
            ticket.bind_output(output)
            outputs.append(output)
        assert session.pending_count == pending
        # Caller tensors may change; engine's private metadata must not.
        data["position_ids"].fill_(99)
        data["cos"].zero_()
        session.backward(sum(output.square().sum() for output in outputs))
        assert session.pending_count == 0
    for output, reference in zip(outputs, references, strict=True):
        assert torch.equal(output, reference)
    for parameter, expected in zip(parameters, expected_grads, strict=True):
        assert torch.equal(parameter.grad, expected)
    assert all(p.grad is None for p in wrapper.base.parameters())


@pytest.mark.parametrize("kind", [PinnedLlamaCapsuleWrapper, PinnedLlamaLoRAWrapper])
def test_bound_block_owned_replay_denies_factor_drift_and_clears_gradients(kind):
    wrapper, factors = engine_wrapper(kind)
    blocks = [
        wrapper._bind_checkpoint_block(i, layer) for i, layer in enumerate(wrapper.base)
    ]
    session = wrapper.checkpoint_session()
    with pytest.raises(CheckpointExecutionError):
        with session:
            ticket = session.begin_forward(wrapper, metadata())
            output = torch.ones(1, 2, 576)
            for i, block in enumerate(blocks):
                output = ticket.run(i, block, output)
            ticket.bind_output(output)
            with torch.no_grad():
                next(factors.parameters()).add_(0.1)
            session.backward(output.sum())
    assert session.pending_count == 0
    assert all(p.grad is None for p in factors.parameters())
    with wrapper.checkpoint_session():
        pass
