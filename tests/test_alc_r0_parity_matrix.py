"""Matrix wiring with real construction but stub cell execution: no host PASS."""

import importlib
from dataclasses import replace

import pytest
import torch
from test_alc_r0_parity_cell import fixtures
from test_alc_r0_parity_factory import FakeBase

from aluclu.alc_r0 import host_wrapper
from aluclu.alc_r0.checkpoint_fidelity import TensorComparison
from aluclu.alc_r0.checkpoint_optimizer import AdamWComparison
from aluclu.alc_r0.checkpoint_parity_cell import CaseComparison, ParityCell
from aluclu.alc_r0.host import SMOLLM2_135M_CONFIG, VerifiedHost


@pytest.fixture
def fake_host(monkeypatch):
    monkeypatch.setattr(host_wrapper, "LlamaForCausalLM", FakeBase)
    return VerifiedHost(FakeBase(), {}, SMOLLM2_135M_CONFIG.as_dict(), 2, 0)


def module():
    return importlib.import_module("aluclu.alc_r0.checkpoint_parity_matrix")


def stub_cells(monkeypatch, matrix):
    calls = []

    def cell(factory, inputs, *, exact):
        off = factory("zero", False)
        on = factory("nonzero", True)
        assert off.base is on.base
        assert inputs == fixtures() and exact is True
        factors = off._checkpoint_factors()
        names = tuple(sorted(dict(factors.named_parameters())))
        digest = matrix._base_digest(off.base)
        calls.append((factors.ports, factors.rank, type(factors).__name__))
        cases = tuple(
            CaseComparison(
                state, repeat, index, (1.0, 1.0), (-1.0, -1.0), digest, "0" * 64
            )
            for state, repeat in (("zero", 0), ("nonzero", 0), ("nonzero", 1))
            for index in range(6)
        )
        metrics = tuple(
            (name, TensorComparison(1.0, 1.0, 0.0, 0.0, 1.0, False)) for name in names
        )
        return ParityCell(
            cases,
            (2.0, 2.0),
            AdamWComparison(1, metrics, metrics, metrics),
            names,
            sum(p.numel() for p in factors.parameters()),
            digest,
        )

    monkeypatch.setattr(matrix, "run_parity_cell", cell)
    return calls, cell


def test_complete_fixed_order_real_factories_shared_base(fake_host, monkeypatch):
    matrix = module()
    calls, _ = stub_cells(monkeypatch, matrix)
    result = matrix.run_parity_matrix(fake_host, fixtures(), exact=True)
    expected = [
        (ports, rank, kind)
        for ports in ((14,), (29,), (14, 29))
        for rank in (4, 8, 16)
        for kind in ("ResearchCapsuleV0", "MatchedQProjLoRA")
    ]
    assert calls == expected
    assert len(result.cells) == 18
    assert result.source_device == "cpu"
    assert result.seed == 20260916
    assert [c.result.parameter_count for c in result.cells] == [
        1152 * rank * len(ports) for ports, rank, _ in expected
    ]


@pytest.mark.parametrize("mode", [False, None, 1, "true"])
def test_invalid_cpu_mode_never_runs_cell(fake_host, monkeypatch, mode):
    matrix = module()
    calls, _ = stub_cells(monkeypatch, matrix)
    with pytest.raises(ValueError):
        matrix.run_parity_matrix(fake_host, fixtures(), exact=mode)
    assert not calls


@pytest.mark.parametrize("index", [0, 7, 17])
def test_failure_preserves_prefix_current_unrun_no_retry(fake_host, monkeypatch, index):
    matrix = module()
    calls, good = stub_cells(monkeypatch, matrix)

    def failed(*args, **kwargs):
        if len(calls) == index:
            raise ValueError("declared synthetic failure")
        return good(*args, **kwargs)

    monkeypatch.setattr(matrix, "run_parity_cell", failed)
    with pytest.raises(matrix.ParityMatrixError) as captured:
        matrix.run_parity_matrix(fake_host, fixtures(), exact=True)
    failure = captured.value.failure
    assert len(failure.completed) == index
    assert failure.current == matrix.PARITY_CELLS[index]
    assert failure.unrun == matrix.PARITY_CELLS[index + 1 :]
    assert len(calls) == index
    assert type(captured.value.__cause__) is ValueError


def test_interruption_keeps_keyboardinterrupt_semantics_and_prefix(
    fake_host, monkeypatch
):
    matrix = module()
    calls, good = stub_cells(monkeypatch, matrix)

    def interrupted(*args, **kwargs):
        if len(calls) == 2:
            raise KeyboardInterrupt("interrupted")
        return good(*args, **kwargs)

    monkeypatch.setattr(matrix, "run_parity_cell", interrupted)
    with pytest.raises(KeyboardInterrupt) as captured:
        matrix.run_parity_matrix(fake_host, fixtures(), exact=True)
    assert len(captured.value.failure.completed) == 2
    assert len(calls) == 2


@pytest.mark.parametrize(
    "bad",
    [
        "base",
        "count",
        "names",
        "cases",
        "step",
        "optimizer_names",
        "case_schedule",
        "nan",
    ],
)
def test_invalid_cell_receipt_is_terminal(fake_host, monkeypatch, bad):
    matrix = module()
    calls, good = stub_cells(monkeypatch, matrix)

    def corrupted(*args, **kwargs):
        result = good(*args, **kwargs)
        changes = {
            "base": {"base_digest": "f" * 64},
            "count": {"parameter_count": 1},
            "names": {"parameter_names": ("A", "B")},
            "cases": {"cases": result.cases[:-1]},
            "step": {"accumulation": replace(result.accumulation, step=2)},
            "optimizer_names": {
                "accumulation": replace(result.accumulation, exp_avg=())
            },
            "case_schedule": {
                "cases": (replace(result.cases[0], repeat=True),) + result.cases[1:]
            },
            "nan": {"pending_losses": (float("nan"), 2.0)},
        }
        return replace(result, **changes[bad])

    monkeypatch.setattr(matrix, "run_parity_cell", corrupted)
    with pytest.raises(matrix.ParityMatrixError):
        matrix.run_parity_matrix(fake_host, fixtures(), exact=True)
    assert len(calls) == 1


@pytest.mark.parametrize("bad", ["shape", "seed", "names"])
def test_factory_binding_denied_before_stub_observation(fake_host, monkeypatch, bad):
    matrix = module()
    calls, _ = stub_cells(monkeypatch, matrix)
    original = matrix.make_parity_wrapper

    def altered(*args, **kwargs):
        wrapper = original(*args, **kwargs)
        factors = wrapper._checkpoint_factors()
        if bad == "shape":
            block = factors.factors["14"]
            block.A = torch.nn.Parameter(block.A.detach().T.contiguous())
        elif bad == "seed":
            factors.initialization_seed += 1
        else:
            factors.factors["15"] = factors.factors.pop("14")
        return wrapper

    monkeypatch.setattr(matrix, "make_parity_wrapper", altered)
    with pytest.raises(matrix.ParityMatrixError) as captured:
        matrix.run_parity_matrix(fake_host, fixtures(), exact=True)
    assert not calls
    assert not captured.value.failure.completed


def test_cross_arm_initial_A_mismatch_denied_before_q_cell_observation(
    fake_host, monkeypatch
):
    matrix = module()
    calls, _ = stub_cells(monkeypatch, matrix)
    original = matrix.make_parity_wrapper

    def altered(*args, **kwargs):
        wrapper = original(*args, **kwargs)
        if kwargs["arm"] == "q_lora":
            with torch.no_grad():
                wrapper._checkpoint_factors().factors["14"].A.add_(1)
        return wrapper

    monkeypatch.setattr(matrix, "make_parity_wrapper", altered)
    with pytest.raises(matrix.ParityMatrixError) as captured:
        matrix.run_parity_matrix(fake_host, fixtures(), exact=True)
    assert len(calls) == len(captured.value.failure.completed) == 1
    assert captured.value.failure.current.arm == "q_lora"


@pytest.mark.parametrize("bad", ["bytes", "buffer_metadata"])
def test_base_drift_after_cell_cannot_enter_completed_prefix(
    fake_host, monkeypatch, bad
):
    matrix = module()
    calls, good = stub_cells(monkeypatch, matrix)

    def mutated(*args, **kwargs):
        result = good(*args, **kwargs)
        if bad == "bytes":
            with torch.no_grad():
                fake_host.model.weight.add_(1)
        else:
            fake_host.model.register_buffer("unexpected", torch.ones(1))
        return result

    monkeypatch.setattr(matrix, "run_parity_cell", mutated)
    with pytest.raises(matrix.ParityMatrixError) as captured:
        matrix.run_parity_matrix(fake_host, fixtures(), exact=True)
    assert len(calls) == 1
    assert not captured.value.failure.completed
