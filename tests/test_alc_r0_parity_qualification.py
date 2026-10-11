"""Stub composition controls, not pinned host execution or learning evidence."""

import hashlib
import importlib
from dataclasses import FrozenInstanceError, asdict, replace
from types import SimpleNamespace

import pytest
import torch
from test_alc_r0_parity_cell import fixtures
from test_alc_r0_parity_matrix import stub_cells

from aluclu.alc_r0.acquisition import SMOLLM2_135M
from aluclu.alc_r0.canonical import canonical_json_bytes
from aluclu.alc_r0.checkpoint_official_forward import (
    FORWARD_CASES,
    NonzeroWitness,
    OfficialCase,
    OfficialKey,
    OfficialSuite,
)
from aluclu.alc_r0.checkpoint_parity_matrix import (
    PARITY_CELLS,
    MatrixCell,
)
from aluclu.alc_r0.checkpoint_parity_tokenizer import TokenizedParityFixtures
from aluclu.alc_r0.host import VerifiedHost


@pytest.fixture
def module():
    return importlib.import_module("aluclu.alc_r0.checkpoint_parity_qualification")


@pytest.fixture
def wiring(module, monkeypatch, tmp_path):
    for flag in ("HF_HUB_OFFLINE", "TRANSFORMERS_OFFLINE", "HF_DATASETS_OFFLINE"):
        monkeypatch.setenv(flag, "1")
    monkeypatch.setattr(torch, "are_deterministic_algorithms_enabled", lambda: True)
    monkeypatch.setattr(
        torch, "is_deterministic_algorithms_warn_only_enabled", lambda: False
    )
    calls = []
    snapshot = tmp_path / "snapshot"
    inventory = {"revision": SMOLLM2_135M.revision, "inventory_sha256": "a" * 64}
    inputs = fixtures()
    payload = {
        "fixtures": [asdict(value) for value in inputs],
        "revision": inventory["revision"],
        "snapshot_inventory_sha256": inventory["inventory_sha256"],
    }
    tokenized = TokenizedParityFixtures(
        inventory["inventory_sha256"],
        inventory["revision"],
        "stub.Tokenizer",
        hashlib.sha256(canonical_json_bytes(payload)).hexdigest(),
        inputs,
    )
    base = torch.nn.Linear(1, 1, bias=False)
    base.config = SimpleNamespace(_attn_implementation="eager")
    base.eval().requires_grad_(False)
    host = VerifiedHost(base, inventory, {}, 1, 0)
    digest = module._base_digest(base)
    official = OfficialSuite(
        "cpu",
        "torch.float32",
        digest,
        tuple(
            OfficialCase(
                OfficialKey(cell.grid_id, cell.arm, phase),
                case,
                "b" * 64,
                "b" * 64,
                "c" * 64 if case.cached else None,
                "c" * 64 if case.cached else None,
            )
            for cell in PARITY_CELLS
            for phase in ("unmounted", "zero", "detached")
            for case in FORWARD_CASES
        ),
        tuple(
            NonzeroWitness(cell.grid_id, cell.arm, "b" * 64, "c" * 64)
            for cell in PARITY_CELLS
        ),
    )
    # Reuse the existing typed-cell fixture constructor without any host forward.
    matrix_module = importlib.import_module("aluclu.alc_r0.checkpoint_parity_matrix")
    _, cell = stub_cells(monkeypatch, matrix_module)
    from test_alc_r0_parity_factory import FakeBase

    from aluclu.alc_r0 import host_wrapper
    from aluclu.alc_r0.host import SMOLLM2_135M_CONFIG

    monkeypatch.setattr(host_wrapper, "LlamaForCausalLM", FakeBase)
    fake = VerifiedHost(FakeBase(), {}, SMOLLM2_135M_CONFIG.as_dict(), 2, 0)
    matrix = matrix_module.run_parity_matrix(fake, inputs, exact=True)
    matrix = replace(
        matrix,
        base_digest=digest,
        cells=tuple(
            MatrixCell(
                row.key,
                replace(
                    row.result,
                    base_digest=digest,
                    cases=tuple(
                        replace(case, base_digest=digest) for case in row.result.cases
                    ),
                ),
            )
            for row in matrix.cells
        ),
    )

    def tokenize(path):
        assert path == snapshot
        calls.append("tokenizer")
        return tokenized

    def load(path, **kwargs):
        assert path == snapshot
        backend = kwargs.pop("backend")
        assert type(backend) is module.TransformersHostBackend
        assert backend._attention_implementation == "eager"
        assert kwargs == {"device": "cpu", "dtype": torch.float32}
        calls.append("host")
        return host

    def forward(value, *, exact):
        assert value is host and exact is True
        calls.append("official")
        return official

    def parity(value, values, *, exact):
        assert value is host and values is tokenized.fixtures and exact is True
        calls.append("matrix")
        return matrix

    def verify(path):
        assert path == snapshot
        calls.append("terminal-assets")
        return dict(inventory)

    monkeypatch.setattr(module, "load_parity_fixtures", tokenize)
    monkeypatch.setattr(module, "load_verified_host", load)
    monkeypatch.setattr(module, "run_official_forward_suite", forward)
    monkeypatch.setattr(module, "run_parity_matrix", parity)
    monkeypatch.setattr(module, "verify_model_snapshot", verify)
    return snapshot, host, tokenized, official, matrix, calls


def test_fixed_full_order_same_host_and_immutable_result(module, wiring):
    snapshot, host, tokenized, official, matrix, calls = wiring
    result = module.run_parity_qualification(snapshot, device="cpu")
    assert calls == ["tokenizer", "host", "official", "matrix", "terminal-assets"]
    assert (
        result.fixtures is tokenized
        and result.official is official
        and result.matrix is matrix
    )
    assert result.base_digest == module._base_digest(host.model)
    assert result.source_device == "cpu" and result.source_dtype == "torch.float32"
    with pytest.raises(FrozenInstanceError):
        result.base_digest = "d" * 64


@pytest.mark.parametrize(
    "device", [None, True, "cuda", "cuda:1", "mps", torch.device("cpu")]
)
def test_invalid_device_before_snapshot_access(module, wiring, device):
    snapshot, *_, calls = wiring
    with pytest.raises(ValueError):
        module.run_parity_qualification(snapshot, device=device)
    assert calls == []


def test_relative_path_before_snapshot_access(module, wiring):
    from pathlib import Path

    with pytest.raises(ValueError):
        module.run_parity_qualification(Path("relative"), device="cpu")
    assert wiring[-1] == []


@pytest.mark.parametrize(
    "flag", ["HF_HUB_OFFLINE", "TRANSFORMERS_OFFLINE", "HF_DATASETS_OFFLINE"]
)
def test_missing_offline_flag_before_snapshot_access(module, wiring, monkeypatch, flag):
    monkeypatch.delenv(flag)
    with pytest.raises(ValueError):
        module.run_parity_qualification(wiring[0], device="cpu")
    assert wiring[-1] == []


@pytest.mark.parametrize(
    "mode", ["inference", "no-grad", "nondeterministic", "warn-only"]
)
def test_invalid_execution_context_before_snapshot_access(
    module, wiring, monkeypatch, mode
):
    from contextlib import nullcontext

    if mode == "nondeterministic":
        monkeypatch.setattr(
            torch, "are_deterministic_algorithms_enabled", lambda: False
        )
    if mode == "warn-only":
        monkeypatch.setattr(
            torch, "is_deterministic_algorithms_warn_only_enabled", lambda: True
        )
    context = (
        torch.inference_mode()
        if mode == "inference"
        else torch.no_grad()
        if mode == "no-grad"
        else nullcontext()
    )
    with context, pytest.raises(ValueError):
        module.run_parity_qualification(wiring[0], device="cpu")
    assert wiring[-1] == []


@pytest.mark.parametrize(
    "stage,callback,prefix",
    [
        ("tokenizer", "load_parity_fixtures", []),
        ("host", "load_verified_host", ["tokenizer"]),
        ("official", "run_official_forward_suite", ["tokenizer", "host"]),
        ("matrix", "run_parity_matrix", ["tokenizer", "host", "official"]),
        (
            "terminal-assets",
            "verify_model_snapshot",
            ["tokenizer", "host", "official", "matrix"],
        ),
    ],
)
@pytest.mark.parametrize("interrupt", [False, True])
def test_terminal_failure_preserves_stage_prior_evidence_and_cause_without_retry(
    module,
    wiring,
    monkeypatch,
    stage,
    callback,
    prefix,
    interrupt,
):
    cause = (
        KeyboardInterrupt("owned interruption")
        if interrupt
        else RuntimeError("owned failure")
    )

    def failed(*args, **kwargs):
        raise cause

    monkeypatch.setattr(module, callback, failed)
    error = (
        module.ParityQualificationInterrupted
        if interrupt
        else module.ParityQualificationError
    )
    with pytest.raises(error) as captured:
        module.run_parity_qualification(wiring[0], device="cpu")
    assert captured.value.__cause__ is cause
    assert captured.value.failure.stage == stage
    assert (captured.value.failure.fixtures is not None) == (stage != "tokenizer")
    assert (captured.value.failure.official is not None) == (
        stage in ("matrix", "terminal-assets")
    )
    assert (captured.value.failure.matrix is not None) == (stage == "terminal-assets")
    assert wiring[-1] == prefix


@pytest.mark.parametrize(
    "kind", ["type", "revision", "fixture-digest", "inventory", "schedule"]
)
def test_bad_tokenizer_binding_rejected_before_host_load(
    module, wiring, monkeypatch, kind
):
    value = wiring[2]
    if kind == "type":
        value = None
    elif kind == "revision":
        value = replace(value, model_revision="0" * 40)
    elif kind == "fixture-digest":
        value = replace(value, fixture_sha256="0" * 64)
    elif kind == "inventory":
        value = replace(value, snapshot_inventory_sha256="bad")
    else:
        value = replace(value, fixtures=value.fixtures[:-1])
    monkeypatch.setattr(module, "load_parity_fixtures", lambda path: value)
    with pytest.raises(module.ParityQualificationError):
        module.run_parity_qualification(wiring[0], device="cpu")
    assert wiring[-1] == []


@pytest.mark.parametrize("kind", ["host", "terminal"])
def test_asset_binding_drift_rejected(module, wiring, monkeypatch, kind):
    if kind == "host":
        wiring[1].acquisition_receipt["inventory_sha256"] = "d" * 64
    else:
        monkeypatch.setattr(
            module,
            "verify_model_snapshot",
            lambda path: {
                "revision": SMOLLM2_135M.revision,
                "inventory_sha256": "d" * 64,
            },
        )
    with pytest.raises(module.ParityQualificationError) as caught:
        module.run_parity_qualification(wiring[0], device="cpu")
    assert caught.value.failure.stage == (
        "host" if kind == "host" else "terminal-assets"
    )
    assert "official" not in wiring[-1] if kind == "host" else "matrix" in wiring[-1]


@pytest.mark.parametrize("stage", ["official", "matrix"])
def test_base_mutation_rejected_before_admitting_stage_receipt(
    module, wiring, monkeypatch, stage
):
    callback = (
        "run_official_forward_suite" if stage == "official" else "run_parity_matrix"
    )
    good = getattr(module, callback)

    def mutate(*args, **kwargs):
        value = good(*args, **kwargs)
        wiring[1].model.weight.data.add_(1)
        return value

    monkeypatch.setattr(module, callback, mutate)
    with pytest.raises(module.ParityQualificationError) as caught:
        module.run_parity_qualification(wiring[0], device="cpu")
    assert getattr(caught.value.failure, stage) is None


@pytest.mark.parametrize(
    "stage,kind",
    [
        ("official", "type"),
        ("official", "count"),
        ("official", "device"),
        ("official", "base"),
        ("official", "order"),
        ("official", "witness"),
        ("matrix", "type"),
        ("matrix", "count"),
        ("matrix", "seed"),
        ("matrix", "base"),
        ("matrix", "order"),
        ("matrix", "cell"),
    ],
)
def test_incomplete_misattributed_component_receipts_rejected(
    module, wiring, monkeypatch, stage, kind
):
    value = wiring[3 if stage == "official" else 4]
    if kind == "type":
        value = None
    elif kind == "count":
        field = "cases" if stage == "official" else "cells"
        value = replace(value, **{field: getattr(value, field)[:-1]})
    elif kind == "device":
        value = replace(value, source_device="cuda:0")
    elif kind == "base":
        value = replace(value, base_digest="d" * 64)
    elif kind == "seed":
        value = replace(value, seed=1)
    elif kind == "order":
        field = "cases" if stage == "official" else "cells"
        value = replace(value, **{field: tuple(reversed(getattr(value, field)))})
    elif kind == "witness":
        value = replace(
            value,
            nonzero_witnesses=tuple(
                replace(row, mounted_sha256=row.official_sha256)
                for row in value.nonzero_witnesses
            ),
        )
    else:
        row = value.cells[0]
        value = replace(
            value,
            cells=(
                replace(row, result=replace(row.result, parameter_count=1)),
                *value.cells[1:],
            ),
        )
    callback = (
        "run_official_forward_suite" if stage == "official" else "run_parity_matrix"
    )
    monkeypatch.setattr(module, callback, lambda *args, **kwargs: value)
    with pytest.raises(module.ParityQualificationError):
        module.run_parity_qualification(wiring[0], device="cpu")
    assert "terminal-assets" not in wiring[-1]


def test_environment_drift_after_official_does_not_run_matrix(
    module, wiring, monkeypatch
):
    good = module.run_official_forward_suite

    def drift(*args, **kwargs):
        value = good(*args, **kwargs)
        monkeypatch.setenv("HF_HUB_OFFLINE", "0")
        return value

    monkeypatch.setattr(module, "run_official_forward_suite", drift)
    with pytest.raises(module.ParityQualificationError):
        module.run_parity_qualification(wiring[0], device="cpu")
    assert wiring[-1] == ["tokenizer", "host", "official"]


@pytest.fixture
def simulated_cuda(monkeypatch):
    # GPU policy simulation only: do not initialize CUDA or allocate GPU tensors.
    monkeypatch.setenv("CUBLAS_WORKSPACE_CONFIG", ":4096:8")
    monkeypatch.setattr(torch.cuda, "is_available", lambda: True)
    monkeypatch.setattr(torch.cuda, "current_device", lambda: 0)
    monkeypatch.setattr(torch.cuda, "is_bf16_supported", lambda: True)
    for name, value in (
        ("math_sdp_enabled", True),
        ("flash_sdp_enabled", False),
        ("mem_efficient_sdp_enabled", False),
        ("cudnn_sdp_enabled", False),
    ):
        monkeypatch.setattr(torch.backends.cuda, name, lambda value=value: value)
    monkeypatch.setattr(torch.backends.cuda.matmul, "allow_tf32", False)
    monkeypatch.setattr(torch.backends.cudnn, "allow_tf32", False)
    monkeypatch.setattr(torch.backends.cudnn, "benchmark", False)
    monkeypatch.setattr(torch.backends.cudnn, "deterministic", True)


@pytest.mark.parametrize(
    "policy",
    [
        "cublas",
        "available",
        "device",
        "bf16",
        "matmul_tf32",
        "cudnn_tf32",
        "benchmark",
        "cudnn_deterministic",
        "math",
        "flash",
        "efficient",
        "cudnn_sdp",
    ],
)
def test_cuda_policy_failure_before_asset_access(
    module, wiring, simulated_cuda, monkeypatch, policy
):
    if policy == "cublas":
        monkeypatch.setenv("CUBLAS_WORKSPACE_CONFIG", "bad")
    elif policy in ("available", "device", "bf16"):
        name = {
            "available": "is_available",
            "device": "current_device",
            "bf16": "is_bf16_supported",
        }[policy]
        monkeypatch.setattr(
            torch.cuda, name, lambda: 1 if policy == "device" else False
        )
    elif policy == "matmul_tf32":
        monkeypatch.setattr(torch.backends.cuda.matmul, "allow_tf32", True)
    elif policy in ("cudnn_tf32", "benchmark", "cudnn_deterministic"):
        name = {
            "cudnn_tf32": "allow_tf32",
            "benchmark": "benchmark",
            "cudnn_deterministic": "deterministic",
        }[policy]
        monkeypatch.setattr(torch.backends.cudnn, name, policy != "cudnn_deterministic")
    else:
        name = {
            "math": "math_sdp_enabled",
            "flash": "flash_sdp_enabled",
            "efficient": "mem_efficient_sdp_enabled",
            "cudnn_sdp": "cudnn_sdp_enabled",
        }[policy]
        monkeypatch.setattr(torch.backends.cuda, name, lambda: policy != "math")
    with pytest.raises(ValueError):
        module.run_parity_qualification(wiring[0], device="cuda:0")
    assert wiring[-1] == []


def test_simulated_cuda_uses_bf16_and_fixed_tolerance_not_cpu_mode(
    module,
    wiring,
    simulated_cuda,
    monkeypatch,
):
    snapshot, host, tokenized, official, matrix, calls = wiring
    host.model.to(dtype=torch.bfloat16)
    digest = module._base_digest(host.model)
    monkeypatch.setattr(module, "_base_device", lambda host: torch.device("cuda:0"))

    def load(path, **kwargs):
        assert path == snapshot
        assert kwargs["device"] == "cuda:0" and kwargs["dtype"] == torch.bfloat16
        assert type(kwargs["backend"]) is module.TransformersHostBackend
        assert kwargs["backend"]._attention_implementation == "eager"
        calls.append("host")
        return host

    def forward(value, *, exact):
        assert value is host and exact is False
        calls.append("official")
        return replace(
            official,
            source_device="cuda:0",
            source_dtype="torch.bfloat16",
            base_digest=digest,
        )

    def parity(value, values, *, exact):
        assert value is host and values is tokenized.fixtures and exact is False
        calls.append("matrix")
        return replace(
            matrix,
            source_device="cuda:0",
            source_dtype="torch.bfloat16",
            base_digest=digest,
            cells=tuple(
                replace(
                    row,
                    result=replace(
                        row.result,
                        base_digest=digest,
                        cases=tuple(
                            replace(case, base_digest=digest)
                            for case in row.result.cases
                        ),
                    ),
                )
                for row in matrix.cells
            ),
        )

    monkeypatch.setattr(module, "load_verified_host", load)
    monkeypatch.setattr(module, "run_official_forward_suite", forward)
    monkeypatch.setattr(module, "run_parity_matrix", parity)
    result = module.run_parity_qualification(snapshot, device="cuda:0")
    assert result.source_device == "cuda:0" and result.source_dtype == "torch.bfloat16"
    assert calls == ["tokenizer", "host", "official", "matrix", "terminal-assets"]


def test_non_eager_host_rejected_before_official_forward(module, wiring):
    wiring[1].model.config._attn_implementation = "sdpa"
    with pytest.raises(module.ParityQualificationError):
        module.run_parity_qualification(wiring[0], device="cpu")
    assert wiring[-1] == ["tokenizer", "host"]


def test_eager_route_drift_rejected_after_official(module, wiring, monkeypatch):
    good = module.run_official_forward_suite

    def drift(*args, **kwargs):
        result = good(*args, **kwargs)
        wiring[1].model.config._attn_implementation = "sdpa"
        return result

    monkeypatch.setattr(module, "run_official_forward_suite", drift)
    with pytest.raises(module.ParityQualificationError):
        module.run_parity_qualification(wiring[0], device="cpu")
    assert wiring[-1] == ["tokenizer", "host", "official"]
