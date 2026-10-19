from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor

import pytest
import torch
from torch import nn

from aluclu.alc_r0.checkpoint_execution import (
    CheckpointController,
    CheckpointExecutionError,
)


class Owner(nn.Module):
    def __init__(self):
        super().__init__()
        self.base = nn.Linear(2, 2, bias=False)
        self.base.weight.data.copy_(torch.tensor([[0.7, 0.2], [0.1, 0.8]]))
        self.base.requires_grad_(False)
        self.factors = nn.ParameterList(
            [
                nn.Parameter(torch.tensor([0.1, -0.2])),
                nn.Parameter(torch.tensor([0.3, 0.4])),
                nn.Parameter(torch.tensor([-0.1, 0.2])),
            ]
        )
        self.train()
        self.base.eval()
        self.controller = CheckpointController(
            self,
            base_getter=lambda: self.base,
            factor_getter=lambda: self.factors,
            layer_count=3,
        )


def forward(owner, session, *, x=None, mask=None, calls=None):
    x = torch.tensor([[0.2, -0.4]]) if x is None else x
    mask = torch.ones_like(x) if mask is None else mask
    ticket = session.begin_forward(owner, {"mask": mask, "position": torch.zeros(1)})
    hidden = x
    for index, factor in enumerate(owner.factors):

        def block(value, metadata, index=index, factor=factor):
            if calls is not None:
                calls.append(index)
            return torch.sin(owner.base(value) + factor * metadata["mask"])

        hidden = ticket.run(index, block, hidden)
    ticket.bind_output(hidden)
    return hidden


def reference(owner, x):
    for factor in owner.factors:
        x = torch.sin(owner.base(x) + factor)
    return x


def test_nonreentrant_matches_off_path_with_frozen_inputs_and_all_factors():
    owner, off = Owner(), Owner()
    x = torch.tensor([[0.2, -0.4]])
    assert not x.requires_grad
    expected = reference(off, x)
    expected.square().sum().backward()
    calls = []
    with owner.controller.session() as session:
        actual = forward(owner, session, x=x, calls=calls)
        assert torch.equal(actual, expected)
        assert session.pending_count == 1
        session.backward(actual.square().sum())
        assert session.pending_count == 0
    assert calls == [0, 1, 2, 2, 1, 0]
    for factor, expected_factor in zip(owner.factors, off.factors, strict=True):
        assert factor.grad is not None and torch.count_nonzero(factor.grad) == 2
        assert torch.equal(factor.grad, expected_factor.grad)
    assert owner.base.weight.grad is None
    owner.controller.assert_mutation_allowed()


def test_two_pending_graphs_summed_backward_and_separate_accumulation():
    owner, off = Owner(), Owner()
    xs = [torch.tensor([[0.2, -0.4]]), torch.tensor([[-0.3, 0.1]])]
    sum(reference(off, x).square().sum() for x in xs).backward()
    with owner.controller.session() as session:
        outputs = [forward(owner, session, x=x) for x in xs]
        assert session.pending_count == 2
        session.backward(sum(output.square().sum() for output in outputs))
        assert session.pending_count == 0
    for p, q in zip(owner.factors, off.factors, strict=True):
        assert torch.equal(p.grad, q.grad)
    owner = Owner()
    with owner.controller.session() as session:
        for _ in range(16):
            session.backward(forward(owner, session).square().sum() / 16)
            assert session.pending_count == 0


def test_metadata_original_mutation_is_isolated():
    owner = Owner()
    mask = torch.ones(1, 2)
    with owner.controller.session() as session:
        output = forward(owner, session, mask=mask)
        mask.zero_()
        session.backward(output.square().sum())
    off = Owner()
    reference(off, torch.tensor([[0.2, -0.4]])).square().sum().backward()
    for p, q in zip(owner.factors, off.factors, strict=True):
        assert torch.equal(p.grad, q.grad)


def test_omitted_loss_invalidates_all_graphs_and_clears_partial_gradients():
    owner = Owner()
    with pytest.raises(CheckpointExecutionError):
        with owner.controller.session() as session:
            first, omitted = forward(owner, session), forward(owner, session)
            session.backward(first.sum())
            assert session.pending_count == 1
    assert all(p.grad is None for p in owner.factors)
    with pytest.raises(CheckpointExecutionError):
        omitted.sum().backward()
    with owner.controller.session() as fresh:
        fresh.backward(forward(owner, fresh).sum())


@pytest.mark.parametrize(
    "mutation",
    ["factor_version", "base_version", "mode", "base_grad", "replace_factor"],
)
def test_replay_entry_rejects_drift_before_block_side_effect(mutation):
    owner, calls = Owner(), []
    with pytest.raises(CheckpointExecutionError):
        with owner.controller.session() as session:
            output = forward(owner, session, calls=calls)
            if mutation == "factor_version":
                with torch.no_grad():
                    owner.factors[0].add_(1)
            elif mutation == "base_version":
                with torch.no_grad():
                    owner.base.weight.add_(1)
            elif mutation == "mode":
                owner.base.train()
            elif mutation == "base_grad":
                owner.base.requires_grad_(True)
            elif mutation == "replace_factor":
                owner.factors[0] = nn.Parameter(owner.factors[0].detach().clone())
            session.backward(output.sum())
    assert calls == [0, 1, 2]
    assert all(p.grad is None for p in owner.factors)
    owner.controller.assert_mutation_allowed()


@pytest.mark.parametrize("which", ["factor", "base"])
def test_unversioned_data_drift_detected_at_exit(which):
    owner = Owner()
    with pytest.raises(CheckpointExecutionError):
        with owner.controller.session() as session:
            session.backward(forward(owner, session).sum())
            target = owner.factors[0] if which == "factor" else owner.base.weight
            before = target._version
            target.data.add_(1)
            assert target._version == before
    assert all(p.grad is None for p in owner.factors)
    owner.controller.assert_mutation_allowed()


def test_nested_foreign_owner_and_foreign_thread_cannot_release_lease():
    owner, other = Owner(), Owner()
    with owner.controller.session() as session:
        with pytest.raises(CheckpointExecutionError):
            with owner.controller.session():
                pass
        with pytest.raises(CheckpointExecutionError):
            session.begin_forward(other, {"x": torch.ones(1)})
        with ThreadPoolExecutor(max_workers=1) as pool:
            with pytest.raises(CheckpointExecutionError):
                pool.submit(session.begin_forward, owner, {"x": torch.ones(1)}).result()
        with pytest.raises(CheckpointExecutionError):
            owner.controller.assert_mutation_allowed()
        session.backward(forward(owner, session).sum())


def test_raw_backward_in_scope_invalidates_and_graph_cannot_be_reused():
    owner = Owner()
    with pytest.raises(CheckpointExecutionError):
        with owner.controller.session() as session:
            output = forward(owner, session)
            output.sum().backward()
    assert all(p.grad is None for p in owner.factors)
    with pytest.raises(CheckpointExecutionError):
        output.sum().backward()
    owner.controller.assert_mutation_allowed()


def test_consumed_graph_and_closed_session_rejected():
    owner = Owner()
    with pytest.raises(CheckpointExecutionError):
        with owner.controller.session() as invalid:
            consumed = forward(owner, invalid)
            invalid.backward(consumed.sum())
            # Catching the denial cannot turn an invalidated lease into success.
            with pytest.raises(CheckpointExecutionError):
                consumed.sum().backward()
    assert all(p.grad is None for p in owner.factors)
    with owner.controller.session() as session:
        output = forward(owner, session)
        session.backward(output.sum())
    with pytest.raises(CheckpointExecutionError):
        output.sum().backward()
    with pytest.raises(CheckpointExecutionError):
        session.backward(output.sum())
    with pytest.raises(CheckpointExecutionError):
        with session:
            pass


def test_foreign_raw_backward_cannot_invalidate_owner_lease():
    owner = Owner()
    with owner.controller.session() as session:
        output = forward(owner, session)
        with ThreadPoolExecutor(max_workers=1) as pool:
            with pytest.raises(CheckpointExecutionError):
                pool.submit(lambda: output.sum().backward()).result()
        assert session.pending_count == 1
        with pytest.raises(CheckpointExecutionError):
            owner.controller.assert_mutation_allowed()
        session.backward(output.sum())


def test_retired_graph_denial_does_not_clear_new_session_gradients():
    owner = Owner()
    with owner.controller.session() as old:
        previous = forward(owner, old)
        old.backward(previous.sum())
    with owner.controller.session() as fresh:
        fresh.backward(forward(owner, fresh).sum())
        before = [p.grad.clone() for p in owner.factors]
        with pytest.raises(CheckpointExecutionError):
            previous.sum().backward()
        assert all(
            torch.equal(p.grad, value)
            for p, value in zip(owner.factors, before, strict=True)
        )


def test_recompute_guard_runs_before_block_not_only_after_backward_preflight():
    owner, calls = Owner(), []
    with pytest.raises(CheckpointExecutionError):
        with owner.controller.session() as session:
            output = forward(owner, session, calls=calls)

            def drift_after_traversal(gradient):
                with torch.no_grad():
                    owner.factors[0].add_(1)
                return gradient

            output.register_hook(drift_after_traversal)
            session.backward(output.sum())
    assert calls == [0, 1, 2]
    assert all(p.grad is None for p in owner.factors)


@pytest.mark.parametrize(
    "bad", ["retain", "nan", "vector", "detached", "integer", "unrelated"]
)
def test_invalid_loss_fails_closed_and_releases(bad):
    owner = Owner()
    with pytest.raises(CheckpointExecutionError):
        with owner.controller.session() as session:
            output = forward(owner, session)
            loss = output.sum()
            if bad == "nan":
                loss = loss * float("nan")
            elif bad == "vector":
                loss = output
            elif bad == "detached":
                loss = loss.detach()
            elif bad == "integer":
                loss = torch.tensor(1)
            elif bad == "unrelated":
                loss = torch.tensor(1.0, requires_grad=True)
            session.backward(loss, retain_graph=bad == "retain")
    assert all(p.grad is None for p in owner.factors)
    owner.controller.assert_mutation_allowed()


def test_backward_exception_after_output_hook_does_not_consume_ticket():
    class Fail(torch.autograd.Function):
        @staticmethod
        def forward(ctx, value):
            return value.clone()

        @staticmethod
        def backward(ctx, grad):
            raise RuntimeError("intentional backward failure")

    owner = Owner()
    with pytest.raises(RuntimeError, match="intentional backward failure"):
        with owner.controller.session() as session:
            ticket = session.begin_forward(owner, {"mask": torch.ones(1, 2)})
            value = torch.ones(1, 2)
            for index, factor in enumerate(owner.factors):

                def block(x, metadata, factor=factor):
                    return Fail.apply(torch.sin(owner.base(x) + factor))

                value = ticket.run(index, block, value)
            ticket.bind_output(value)
            session.backward(value.sum())
    assert all(p.grad is None for p in owner.factors)
    with pytest.raises(CheckpointExecutionError):
        value.sum().backward()
    owner.controller.assert_mutation_allowed()


def test_pending_limit_and_sequential_layer_order():
    owner = Owner()
    with pytest.raises(CheckpointExecutionError):
        with owner.controller.session() as session:
            for _ in range(32):
                forward(owner, session)
            assert session.pending_count == 32
            forward(owner, session)
    with pytest.raises(CheckpointExecutionError):
        with owner.controller.session() as session:
            ticket = session.begin_forward(owner, {"x": torch.ones(1)})
            ticket.run(2, lambda x, metadata: x, torch.ones(1))
    owner.controller.assert_mutation_allowed()


def test_unrelated_bound_output_cannot_consume_executed_blocks():
    owner = Owner()
    with pytest.raises(CheckpointExecutionError, match="complete owned graph"):
        with owner.controller.session() as session:
            ticket = session.begin_forward(owner, {"mask": torch.ones(1, 2)})
            value = torch.ones(1, 2)
            for index, factor in enumerate(owner.factors):

                def block(x, metadata, factor=factor):
                    return torch.sin(owner.base(x) + factor)

                value = ticket.run(index, block, value)
            unrelated = torch.ones(1, 2, requires_grad=True)
            ticket.bind_output(unrelated)
            session.backward(unrelated.sum())
    assert all(p.grad is None for p in owner.factors)


def test_unbound_intermediate_backward_is_rejected_before_factor_gradient():
    owner = Owner()
    with pytest.raises(CheckpointExecutionError):
        with owner.controller.session() as session:
            ticket = session.begin_forward(owner, {"mask": torch.ones(1, 2)})
            intermediate = ticket.run(
                0,
                lambda x, metadata: torch.sin(owner.base(x) + owner.factors[0]),
                torch.ones(1, 2),
            )
            intermediate.sum().backward()
    assert all(p.grad is None for p in owner.factors)


def test_error_clears_prior_successful_accumulation_and_all_replay():
    owner = Owner()
    with pytest.raises(RuntimeError, match="abandon accumulated attempt"):
        with owner.controller.session() as session:
            session.backward(forward(owner, session).sum())
            assert all(p.grad is not None for p in owner.factors)
            pending = forward(owner, session)
            raise RuntimeError("abandon accumulated attempt")
    assert all(p.grad is None for p in owner.factors)
    with pytest.raises(CheckpointExecutionError):
        pending.sum().backward()
    owner.controller.assert_mutation_allowed()


@pytest.mark.parametrize(
    "metadata",
    [
        {},
        None,
        {" bad ": torch.ones(1)},
        {"x": 1},
        {"x": torch.ones(1, requires_grad=True)},
        {"x": torch.empty(1, device="meta")},
    ],
)
def test_bad_metadata_rejects_and_releases(metadata):
    owner = Owner()
    with pytest.raises(ValueError):
        with owner.controller.session() as session:
            session.begin_forward(owner, metadata)
    owner.controller.assert_mutation_allowed()


def test_private_metadata_mutation_by_block_invalidates_forward():
    owner = Owner()
    with pytest.raises(CheckpointExecutionError, match="metadata drifted"):
        with owner.controller.session() as session:
            ticket = session.begin_forward(owner, {"mask": torch.ones(1, 2)})

            def block(x, metadata):
                metadata["mask"].zero_()
                return torch.sin(owner.base(x) + owner.factors[0])

            ticket.run(0, block, torch.ones(1, 2))
    owner.controller.assert_mutation_allowed()


@pytest.mark.parametrize(
    "mutation",
    [
        "eval_owner",
        "eval_factors",
        "train_base",
        "base_grad",
        "factor_dtype",
        "frozen_factor",
        "missing_factor",
        "extra_parameter",
        "storage_alias",
    ],
)
def test_entry_validation_failure_is_not_an_acquired_lease(mutation):
    owner = Owner()
    if mutation == "eval_owner":
        owner.training = False
    elif mutation == "eval_factors":
        owner.factors.eval()
    elif mutation == "train_base":
        owner.base.train()
    elif mutation == "base_grad":
        owner.base.requires_grad_(True)
    elif mutation == "factor_dtype":
        owner.factors.double()
    elif mutation == "frozen_factor":
        owner.factors.requires_grad_(False)
    elif mutation == "missing_factor":
        owner.factors = None
    elif mutation == "extra_parameter":
        owner.extra = nn.Parameter(torch.ones(1))
    elif mutation == "storage_alias":
        owner.factors[0].data = owner.base.weight.data[0]
    with pytest.raises(CheckpointExecutionError):
        with owner.controller.session():
            pass
    owner.controller.assert_mutation_allowed()


def test_frozen_early_blocks_do_not_require_fake_input_gradients():
    owner = Owner()
    with owner.controller.session() as session:
        ticket = session.begin_forward(owner, {"mask": torch.ones(1, 2)})
        value = torch.ones(1, 2)
        for index in range(3):
            factor = owner.factors[2] if index == 2 else None

            def block(x, metadata, factor=factor):
                result = owner.base(x)
                return torch.sin(result if factor is None else result + factor)

            value = ticket.run(index, block, value)
            assert value.requires_grad == (index == 2)
        ticket.bind_output(value)
        session.backward(value.sum())
    assert owner.factors[0].grad is None and owner.factors[1].grad is None
    assert owner.factors[2].grad is not None
    assert owner.base.weight.grad is None


@pytest.mark.parametrize("mutation", ["version", "replacement", "data"])
def test_registered_buffer_drift_cannot_change_replay(mutation):
    class BufferedBase(nn.Linear):
        def __init__(self):
            super().__init__(2, 2, bias=False)
            self.register_buffer("scale", torch.ones(2))

        def forward(self, value):
            return super().forward(value) * self.scale

    owner, calls = Owner(), []
    buffered = BufferedBase()
    buffered.weight.data.copy_(owner.base.weight)
    buffered.requires_grad_(False).eval()
    owner.base = buffered
    with pytest.raises(CheckpointExecutionError):
        with owner.controller.session() as session:
            output = forward(owner, session, calls=calls)
            if mutation == "version":
                owner.base.scale.add_(1)
            elif mutation == "replacement":
                owner.base.scale = owner.base.scale.clone() + 1
            else:
                session.backward(output.sum())
                old_version = owner.base.scale._version
                owner.base.scale.data.add_(1)
                assert old_version == owner.base.scale._version
            if mutation != "data":
                session.backward(output.sum())
    if mutation != "data":
        assert calls == [0, 1, 2]
    assert all(p.grad is None for p in owner.factors)
    owner.controller.assert_mutation_allowed()


def test_no_gradient_bearing_checkpoint_cannot_accept_unrelated_output():
    owner = Owner()
    with pytest.raises(CheckpointExecutionError):
        with owner.controller.session() as session:
            ticket = session.begin_forward(owner, {"mask": torch.ones(1, 2)})
            value = torch.ones(1, 2)
            for index in range(3):
                value = ticket.run(index, lambda x, metadata: owner.base(x), value)
            assert not value.requires_grad
            unrelated = torch.ones(1, 2, requires_grad=True)
            ticket.bind_output(unrelated)
            session.backward(unrelated.sum())


def test_factors_cannot_alias_frozen_base_buffer():
    owner = Owner()
    owner.base.register_buffer("alias", owner.factors[0].detach())
    with pytest.raises(CheckpointExecutionError):
        with owner.controller.session():
            pass
    owner.controller.assert_mutation_allowed()


def test_static_registered_scalar_and_integer_buffers_are_valid():
    owner = Owner()
    owner.base.register_buffer("counter", torch.tensor(0, dtype=torch.int64))
    owner.factors.register_buffer("flag", torch.tensor(True))
    with owner.controller.session() as session:
        session.backward(forward(owner, session).sum())
    assert owner.base.counter.item() == 0 and owner.factors.flag.item()


def test_trainable_buffer_is_not_an_optimizer_owned_factor():
    owner = Owner()
    owner.base.register_buffer("bad", torch.ones(2, requires_grad=True))
    with pytest.raises(CheckpointExecutionError):
        with owner.controller.session():
            pass


def test_declared_layer_count_cannot_shrink_during_lease():
    owner = Owner()
    with pytest.raises(CheckpointExecutionError):
        with owner.controller.session() as session:
            ticket = session.begin_forward(owner, {"mask": torch.ones(1, 2)})
            owner.controller.layer_count = 1
            output = ticket.run(
                0,
                lambda x, metadata: torch.sin(owner.base(x) + owner.factors[0]),
                torch.ones(1, 2),
            )
            ticket.bind_output(output)
            session.backward(output.sum())
