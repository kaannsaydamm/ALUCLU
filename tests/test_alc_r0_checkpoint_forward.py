"""Full wrapper orchestration with fake CPU host, not actual-host authority."""

import pytest
import torch
from test_alc_r0_bound_decoder_blocks import engine_wrapper
from torch import nn
from torch.nn import functional as F
from transformers import LlamaConfig

from aluclu.alc_r0.checkpoint_execution import CheckpointExecutionError
from aluclu.alc_r0.host_wrapper import PinnedLlamaCapsuleWrapper
from aluclu.alc_r0.matched_lora import PinnedLlamaLoRAWrapper


class FakeRotary(nn.Module):
    def forward(self, hidden, position_ids):
        angle = position_ids.float().unsqueeze(-1).expand(-1, -1, 2) * 0.01
        return angle.cos().to(hidden.dtype), angle.sin().to(hidden.dtype)


class FakeLM(nn.Module):
    def __init__(self, layers):
        super().__init__()
        self.config = LlamaConfig(
            vocab_size=8,
            hidden_size=576,
            num_hidden_layers=30,
            num_attention_heads=288,
            num_key_value_heads=1,
            max_position_embeddings=128,
        )
        self.config._attn_implementation = "eager"
        self.model = nn.Module()
        self.model.layers = layers
        self.model.embed_tokens = nn.Embedding(8, 576)
        self.model.norm = nn.Identity()
        self.model.rotary_emb = FakeRotary()
        self.lm_head = nn.Linear(576, 8, bias=False)
        self.requires_grad_(False).eval()

    @staticmethod
    def loss_function(*, logits, labels, vocab_size):
        return F.cross_entropy(
            logits[:, :-1].float().reshape(-1, vocab_size),
            labels[:, 1:].reshape(-1),
            ignore_index=-100,
        )


def make_forward_wrapper(kind):
    wrapper, factors = engine_wrapper(kind)
    wrapper.base = FakeLM(wrapper.base)
    # FAKE-only constant callback; explicitly not a real-host inventory certificate.
    wrapper._checkpoint_controller.state_fingerprint_getter = lambda: "0" * 64
    return wrapper, factors


@pytest.mark.parametrize("kind", [PinnedLlamaCapsuleWrapper, PinnedLlamaLoRAWrapper])
@pytest.mark.parametrize("pending", [1, 2])
def test_full_checkpoint_forward_matches_default_loss_logits_and_gradients(
    kind, pending
):
    wrapper, factors = make_forward_wrapper(kind)
    ids = torch.tensor([[1, 2, 3, 0]])
    mask = torch.tensor([[1, 1, 1, 0]])
    positions = torch.arange(4).unsqueeze(0)
    labels = torch.tensor([[-100, 2, 3, -100]])
    references = [
        wrapper(
            ids,
            attention_mask=mask,
            position_ids=positions,
            labels=labels,
            use_cache=False,
        )
        for _ in range(pending)
    ]
    parameters = tuple(factors.parameters())
    expected_grads = torch.autograd.grad(
        sum(item.loss for item in references), parameters
    )
    with wrapper.checkpoint_session() as session:
        outputs = [
            wrapper(
                ids,
                attention_mask=mask,
                position_ids=positions,
                labels=labels,
                use_cache=False,
                checkpoint_session=session,
            )
            for _ in range(pending)
        ]
        assert session.pending_count == pending
        ids.zero_()
        mask.zero_()
        positions.fill_(77)
        labels.fill_(7)
        session.backward(sum(item.loss for item in outputs))
        assert session.pending_count == 0
    for actual, expected in zip(outputs, references, strict=True):
        assert actual.past_key_values is None
        assert torch.equal(actual.logits, expected.logits)
        assert torch.equal(actual.loss, expected.loss)
    for parameter, expected in zip(parameters, expected_grads, strict=True):
        assert torch.equal(parameter.grad, expected)
    assert all(p.grad is None for p in wrapper.base.parameters())


@pytest.mark.parametrize("kind", [PinnedLlamaCapsuleWrapper, PinnedLlamaLoRAWrapper])
@pytest.mark.parametrize(
    "bad",
    [
        "cache",
        "implicit_cache",
        "past",
        "embeds",
        "batch",
        "dtype",
        "mask",
        "position",
        "labels",
        "logits",
        "inventory",
    ],
)
def test_checkpoint_forward_invalid_input_aborts_owned_scope(kind, bad):
    wrapper, factors = make_forward_wrapper(kind)
    kwargs = {"input_ids": torch.tensor([[1, 2]]), "use_cache": False}
    if bad == "cache":
        kwargs["use_cache"] = True
    elif bad == "implicit_cache":
        kwargs["use_cache"] = None
    elif bad == "past":
        kwargs["past_key_values"] = object()
    elif bad == "embeds":
        kwargs["inputs_embeds"] = torch.ones(1, 2, 576)
    elif bad == "batch":
        kwargs["input_ids"] = torch.ones(2, 2, dtype=torch.long)
    elif bad == "dtype":
        kwargs["input_ids"] = torch.ones(1, 2)
    elif bad == "mask":
        kwargs["attention_mask"] = torch.ones(1, 3)
    elif bad == "position":
        kwargs["position_ids"] = torch.tensor([[-1, 0]])
    elif bad == "labels":
        kwargs["labels"] = torch.tensor([[1, 99]])
    elif bad == "logits":
        kwargs["logits_to_keep"] = 1
    else:
        wrapper._checkpoint_controller.state_fingerprint_getter = None
    session = wrapper.checkpoint_session()
    with pytest.raises(CheckpointExecutionError):
        with session:
            wrapper(**kwargs, checkpoint_session=session)
    assert session.pending_count == 0
    assert all(p.grad is None for p in factors.parameters())
    with wrapper.checkpoint_session():
        pass


def test_foreign_session_rejection_does_not_abort_its_owner():
    wrapper, _ = make_forward_wrapper(PinnedLlamaCapsuleWrapper)
    other, _ = make_forward_wrapper(PinnedLlamaCapsuleWrapper)
    with other.checkpoint_session() as session:
        with pytest.raises(CheckpointExecutionError):
            wrapper(torch.tensor([[1, 2]]), checkpoint_session=session, use_cache=False)
        assert session._status == "active"


def test_missing_backward_keeps_graph_outstanding_and_denies_clean_exit():
    wrapper, _ = make_forward_wrapper(PinnedLlamaCapsuleWrapper)
    with pytest.raises(CheckpointExecutionError, match="unconsumed"):
        with wrapper.checkpoint_session() as session:
            wrapper(torch.tensor([[1, 2]]), checkpoint_session=session, use_cache=False)


@pytest.mark.parametrize("bad", ["replace", "grad", "late"])
def test_derived_metadata_extension_rejects_invalid_lifecycle(bad):
    wrapper, factors = make_forward_wrapper(PinnedLlamaCapsuleWrapper)
    session = wrapper.checkpoint_session()
    with pytest.raises(CheckpointExecutionError):
        with session:
            ticket = session.begin_forward(
                wrapper, {"input_ids": torch.ones(1, 2, dtype=torch.long)}
            )
            if bad == "replace":
                ticket._extend_metadata(
                    {"input_ids": torch.zeros(1, 2, dtype=torch.long)}
                )
            elif bad == "grad":
                ticket._extend_metadata({"mask": torch.ones(1, requires_grad=True)})
            else:
                ticket.run(0, lambda h, m: h * 2, torch.ones(1, 2, 576))
                ticket._extend_metadata({"mask": torch.ones(1)})
    assert session.pending_count == 0
    assert all(p.grad is None for p in factors.parameters())


def test_no_labels_supports_owned_logits_loss_and_default_positions():
    wrapper, factors = make_forward_wrapper(PinnedLlamaCapsuleWrapper)
    ids = torch.tensor([[1, 2]])
    reference = wrapper(ids, use_cache=False).logits
    expected = torch.autograd.grad(
        reference.square().sum(), tuple(factors.parameters())
    )
    with wrapper.checkpoint_session() as session:
        output = wrapper(ids, checkpoint_session=session, use_cache=False)
        assert output.loss is None
        session.backward(output.logits.square().sum())
    assert torch.equal(output.logits, reference)
    for parameter, gradient in zip(factors.parameters(), expected, strict=True):
        assert torch.equal(parameter.grad, gradient)
