"""Actual factors/guards, stubbed cell execution: NOT numerical parity evidence."""

import importlib
from dataclasses import asdict, replace

import pytest
import torch
from test_alc_r0_parity_cell import fixtures
from test_alc_r0_reference_parity_receipt import receipt
from torch import nn
from transformers import LlamaConfig

from aluclu.alc_r0.checkpoint_execution import _digest
from aluclu.alc_r0.checkpoint_parity_cell import (
    SINGLE_SCHEDULE,
    ParityCellError,
    ParityCellFailure,
    ParityCellInterrupted,
)
from aluclu.alc_r0.host import VerifiedHost
from aluclu.alc_r0.reference_official_suite import _base_digest, _json_digest
from aluclu.alc_r0.reference_qv_lora import ReferenceQVLoRA
from aluclu.alc_r0.reference_qv_wrapper import PinnedLlamaQVReferenceWrapper


@pytest.fixture
def wiring(monkeypatch):
    module = importlib.import_module("aluclu.alc_r0.reference_parity_suite")
    base = nn.Linear(576, 8, bias=False).requires_grad_(False).eval()
    base.config = LlamaConfig(vocab_size=49152, max_position_embeddings=8192)
    base.config._attn_implementation = "eager"
    host = VerifiedHost(base, {"fake": True}, {"fake": True}, 4608, 0)
    created = []

    def make(host, checkpoint, *, state):
        wrapper = PinnedLlamaQVReferenceWrapper.__new__(PinnedLlamaQVReferenceWrapper)
        nn.Module.__init__(wrapper)
        wrapper.base, wrapper.capsule = host.model, None
        wrapper.reference = ReferenceQVLoRA(seed=20260916)
        if state == "nonzero":
            with torch.no_grad():
                for name, p in wrapper.reference.named_parameters():
                    if name.endswith(".B"):
                        p.copy_(
                            ((torch.arange(p.numel()) % 17 - 8).float() * 1e-4).reshape(
                                p.shape
                            )
                        )
        wrapper._initialize_checkpoint_controller()
        if checkpoint:
            wrapper._checkpoint_controller.state_fingerprint_getter = lambda: (
                "synthetic"
            )
        wrapper.train()
        created.append(wrapper)
        return wrapper

    def cell(factory, inputs, *, exact):
        assert inputs == fixtures() and exact is True
        zero = factory("zero", False)
        nonzero = factory("nonzero", True)
        factory("zero", True)
        factory("nonzero", False)
        digest = _base_digest(host.model)
        hashes = {
            state: _digest(tuple(sorted(w.reference.named_parameters())))
            for state, w in (("zero", zero), ("nonzero", nonzero))
        }
        original = receipt().cell
        cases = tuple(
            replace(row, base_digest=digest, factor_digest=hashes[row.state])
            for row in original.cases
        )
        return replace(original, cases=cases, base_digest=digest)

    monkeypatch.setattr(module, "make_reference_wrapper", make)
    monkeypatch.setattr(module, "run_parity_cell", cell)
    return module, host, created


def run(wiring, **kwargs):
    module, host, _ = wiring
    args = dict(
        exact=True,
        expected_fixture_digest=_json_digest([asdict(f) for f in fixtures()]),
    )
    args.update(kwargs)
    return module.run_reference_parity_suite(host, fixtures(), **args)


def test_complete_bound_receipt_and_independent_live_ownership(wiring):
    result = run(wiring)
    _, host, created = wiring
    assert result.cell.parameter_count == 460800
    assert len(result.cell.cases) == 18
    assert result.identity.base_digest == _base_digest(host.model)
    assert len({id(w.reference) for w in created}) == 4
    assert len({id(w._checkpoint_controller) for w in created}) == 4
    assert all(w.base is host.model for w in created)


@pytest.mark.parametrize("mode", [False, 1, None])
def test_mode_denied_before_factory(wiring, mode):
    with pytest.raises(ValueError):
        run(wiring, exact=mode)
    assert not wiring[2]


@pytest.mark.parametrize("digest", ["0" * 64, "bad", None])
def test_fixture_identity_denied_before_factory(wiring, digest):
    with pytest.raises(ValueError):
        run(wiring, expected_fixture_digest=digest)
    assert not wiring[2]


@pytest.mark.parametrize(
    "bad",
    ["seed", "A", "B", "shape", "grad", "mode", "controller", "co_mount", "wrong_type"],
)
def test_factory_corruption_terminal_before_success(wiring, monkeypatch, bad):
    module, _, created = wiring
    good = module.make_reference_wrapper

    def corrupt(*args, **kwargs):
        wrapper = good(*args, **kwargs)
        block = wrapper.reference.factors["0"]["q"]
        if bad == "seed":
            wrapper.reference.initialization_seed = 1
        elif bad in ("A", "B"):
            with torch.no_grad():
                getattr(block, bad).add_(1)
        elif bad == "shape":
            block.A = nn.Parameter(torch.zeros(8, 575))
        elif bad == "grad":
            block.A.grad = torch.ones_like(block.A)
        elif bad == "mode":
            wrapper.eval()
        elif bad == "controller":
            wrapper._checkpoint_controller.owner = nn.Identity()
        elif bad == "co_mount":
            wrapper.capsule = nn.Identity()
        else:
            return nn.Identity()
        return wrapper

    monkeypatch.setattr(module, "make_reference_wrapper", corrupt)
    with pytest.raises(module.ReferenceParityError):
        run(wiring)
    assert len(created) == 1
    assert all(
        p.grad is None for wrapper in created for p in wrapper.reference.parameters()
    )


def test_reused_live_wrapper_rejected(wiring, monkeypatch):
    module, _, created = wiring
    good = module.make_reference_wrapper
    monkeypatch.setattr(
        module,
        "make_reference_wrapper",
        lambda *a, **k: created[0] if created else good(*a, **k),
    )
    with pytest.raises(module.ReferenceParityError):
        run(wiring)


@pytest.mark.parametrize("bad", ["base", "config", "identity", "receipt"])
def test_final_drift_or_bad_receipt_is_not_admitted(wiring, monkeypatch, bad):
    module, host, _ = wiring
    good = module.run_parity_cell

    def corrupt(*args, **kwargs):
        cell = good(*args, **kwargs)
        if bad == "base":
            with torch.no_grad():
                host.model.weight.add_(1)
        elif bad == "config":
            host.model.config.hidden_size += 1
        elif bad == "identity":
            host.acquisition_receipt["fake"] = False
        else:
            cell = replace(cell, parameter_names=cell.parameter_names[:-1])
        return cell

    monkeypatch.setattr(module, "run_parity_cell", corrupt)
    with pytest.raises(module.ReferenceParityError) as caught:
        run(wiring)
    assert caught.value.failure.stage in ("final_base", "receipt")
    assert len(caught.value.failure.cell_failure.completed) == 18
    assert caught.value.failure.cell_failure.pending_losses == (2.0, 2.0)
    assert caught.value.failure.cell_failure.current is None
    assert caught.value.failure.cell_failure.unrun == ()


def test_inner_failure_journal_preserved_without_retry(wiring, monkeypatch):
    module, _, created = wiring
    failure = ParityCellFailure(
        "single_off", (), SINGLE_SCHEDULE[0], SINGLE_SCHEDULE[1:], None
    )

    def failed(*args, **kwargs):
        raise ParityCellError("declared", failure)

    monkeypatch.setattr(module, "run_parity_cell", failed)
    with pytest.raises(module.ReferenceParityError) as caught:
        run(wiring)
    assert caught.value.failure.cell_failure is failure
    assert not created


def test_foreign_consistent_factor_hashes_rejected(wiring, monkeypatch):
    module, _, _ = wiring
    good = module.run_parity_cell

    def corrupt(*args, **kwargs):
        cell = good(*args, **kwargs)
        return replace(
            cell,
            cases=tuple(
                replace(row, factor_digest=("1" if row.state == "zero" else "2") * 64)
                for row in cell.cases
            ),
        )

    monkeypatch.setattr(module, "run_parity_cell", corrupt)
    with pytest.raises(module.ReferenceParityError):
        run(wiring)


def test_inner_interruption_preserved(wiring, monkeypatch):
    module, _, created = wiring
    failure = ParityCellFailure(
        "single_on", (), SINGLE_SCHEDULE[0], SINGLE_SCHEDULE[1:], None
    )

    def interrupted(*args, **kwargs):
        raise ParityCellInterrupted("declared", failure)

    monkeypatch.setattr(module, "run_parity_cell", interrupted)
    with pytest.raises(module.ReferenceParityInterrupted) as caught:
        run(wiring)
    assert caught.value.failure.cell_failure is failure
    assert isinstance(caught.value.__cause__, KeyboardInterrupt)
    assert not created


def test_post_cell_interruption_retains_completed_evidence(wiring, monkeypatch):
    module, _, created = wiring
    good = module.run_parity_cell

    def completed(*args, **kwargs):
        cell = good(*args, **kwargs)
        for wrapper in created:
            for parameter in wrapper.reference.parameters():
                parameter.grad = torch.ones_like(parameter)

        def interrupted(self):
            raise KeyboardInterrupt("final check interrupted")

        monkeypatch.setattr(module._ReferenceFactory, "unchanged", interrupted)
        return cell

    monkeypatch.setattr(module, "run_parity_cell", completed)
    with pytest.raises(module.ReferenceParityInterrupted) as caught:
        run(wiring)
    failure = caught.value.failure
    assert failure.stage == "final_base"
    assert len(failure.cell_failure.completed) == 18
    assert failure.cell_failure.pending_losses == (2.0, 2.0)
    assert failure.cell_failure.current is None
    assert failure.cell_failure.unrun == ()
    assert isinstance(caught.value.__cause__, KeyboardInterrupt)
    assert all(p.grad is None for w in created for p in w.reference.parameters())


@pytest.mark.parametrize(
    "bad", ["type", "count", "schedule", "nonfinite", "digest", "pending"]
)
def test_completed_failure_framing_rejects_corrupt_payload(wiring, bad):
    module, _, _ = wiring
    cell = receipt().cell
    if bad == "type":
        cell = object()
    elif bad == "count":
        cell = replace(cell, cases=cell.cases[:-1])
    elif bad == "pending":
        cell = replace(cell, pending_losses=(float("inf"), 2.0))
    else:
        changes = {
            "schedule": {"repeat": True},
            "nonfinite": {"losses": (float("nan"), 2.0)},
            "digest": {"factor_digest": "invalid"},
        }[bad]
        cell = replace(cell, cases=(replace(cell.cases[0], **changes), *cell.cases[1:]))
    assert module._completed_progress(cell) is None


@pytest.mark.parametrize("context", [torch.no_grad, torch.inference_mode])
def test_nonordinary_context_denied_before_factory(wiring, context):
    with context(), pytest.raises(ValueError):
        run(wiring)
    assert not wiring[2]
