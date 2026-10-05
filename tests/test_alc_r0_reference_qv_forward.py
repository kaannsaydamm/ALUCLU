"""Thirty independent fake q/v decoder blocks, never pinned-host/E3 evidence.

The constructor's Llama type check is substituted explicitly. Random fake
weights, identity norms and linear MLPs are not SmolLM2 or a learned capability.
"""

import pytest
import torch
from test_alc_r0_reference_qv_wrapper import fake_layer
from torch import nn
from torch.nn import functional as F
from transformers import LlamaConfig

from aluclu.alc_r0 import host_wrapper
from aluclu.alc_r0.checkpoint_execution import CheckpointExecutionError
from aluclu.alc_r0.checkpoint_parity_factory import make_reference_wrapper
from aluclu.alc_r0.host import SMOLLM2_135M_CONFIG, VerifiedHost


class Rotary64(nn.Module):
    def forward(self, hidden, position_ids):
        angle = position_ids.float().unsqueeze(-1).expand(-1, -1, 64) * 0.01
        return angle.cos().to(hidden.dtype), angle.sin().to(hidden.dtype)


class IndependentQVLM(nn.Module):
    def __init__(self):
        super().__init__()
        self.config = LlamaConfig(
            vocab_size=8,
            hidden_size=576,
            num_hidden_layers=30,
            num_attention_heads=9,
            num_key_value_heads=3,
            max_position_embeddings=128,
        )
        self.config._attn_implementation = "eager"
        self.model = nn.Module()
        self.model.layers = nn.ModuleList(fake_layer() for _ in range(30))
        for index, layer in enumerate(self.model.layers):
            layer.self_attn.config = self.config
            layer.self_attn.layer_idx = index
        self.model.embed_tokens = nn.Embedding(8, 576)
        self.model.norm = nn.Identity()
        self.model.rotary_emb = Rotary64()
        self.lm_head = nn.Linear(576, 8, bias=False)
        self.requires_grad_(False).eval()

    @staticmethod
    def loss_function(*, logits, labels, vocab_size):
        return F.cross_entropy(
            logits[:, :-1].float().reshape(-1, vocab_size),
            labels[:, 1:].reshape(-1),
            ignore_index=-100,
        )


@pytest.fixture
def host(monkeypatch):
    monkeypatch.setattr(host_wrapper, "LlamaForCausalLM", IndependentQVLM)
    with torch.random.fork_rng(devices=[]):
        torch.manual_seed(20260916)
        base = IndependentQVLM()
    return VerifiedHost(
        base,
        {},
        SMOLLM2_135M_CONFIG.as_dict(),
        sum(p.numel() for p in base.parameters()),
        0,
    )


@pytest.mark.parametrize("state", ["zero", "nonzero"])
def test_distinct_thirty_qv_blocks_exact_full_forward_and_replay(host, state):
    off = make_reference_wrapper(host, False, state=state)
    on = make_reference_wrapper(host, True, state=state)
    layers = host.model.model.layers
    assert len({id(layer) for layer in layers}) == 30
    for target in ("q_proj", "v_proj"):
        assert (
            len(
                {getattr(layer.self_attn, target).weight.data_ptr() for layer in layers}
            )
            == 30
        )
    ids = torch.tensor([[1, 2, 3]])
    labels = torch.tensor([[-100, 2, 3]])
    args = dict(input_ids=ids, labels=labels, use_cache=False)
    expected = off(**args)
    expected_gradients = torch.autograd.grad(
        expected.loss, tuple(off.reference.parameters())
    )
    with on.checkpoint_session() as session:
        actual = on(**args, checkpoint_session=session)
        assert session.pending_count == 1
        session.backward(actual.loss)
        assert session.pending_count == 0
    assert torch.equal(actual.logits, expected.logits)
    assert torch.equal(actual.loss, expected.loss)
    assert torch.isfinite(actual.logits).all()
    parameters = tuple(on.reference.parameters())
    assert len(parameters) == 120
    for parameter, expected_gradient in zip(
        parameters, expected_gradients, strict=True
    ):
        assert torch.equal(parameter.grad, expected_gradient)
        assert torch.isfinite(parameter.grad).all()
    assert all(p.grad is None and not p.requires_grad for p in host.model.parameters())


def test_late_qv_projection_drift_rejects_owned_forward(host):
    wrapper = make_reference_wrapper(host, True, state="nonzero")
    with pytest.raises(CheckpointExecutionError):
        with wrapper.checkpoint_session() as session:
            with torch.no_grad():
                host.model.model.layers[29].self_attn.v_proj.weight.add_(0.01)
            wrapper(torch.tensor([[1, 2]]), use_cache=False, checkpoint_session=session)
    assert wrapper._checkpoint_controller._active is None
    assert all(p.grad is None for p in wrapper.reference.parameters())
