"""Compose pinned offline fixtures, one base, official regressions and full D.

This callable loads a real host when invoked. It is not a launcher or permission
to execute: parent must first authenticate committed source/runtime/assets and
reserve reconciled program resources, journal attempts, enforce owned wall
timeouts and qualify two fresh GPU processes/Linux independently. No dataset,
training authority, capability claim or final .alc artifact is supplied here.
"""

import hashlib
import os
import re
from dataclasses import asdict, dataclass
from pathlib import Path

import torch

from .acquisition import SMOLLM2_135M, verify_model_snapshot
from .canonical import canonical_json_bytes
from .checkpoint_observation import _base_digest, _roster_stamp
from .checkpoint_official_forward import (
    FORWARD_CASES,
    NonzeroWitness,
    OfficialKey,
    OfficialSuite,
    run_official_forward_suite,
)
from .checkpoint_official_forward import (
    _receipt as _official_receipt,
)
from .checkpoint_parity_cell import _schedule
from .checkpoint_parity_factory import PARITY_SEED, _base_device
from .checkpoint_parity_matrix import (
    PARITY_CELLS,
    MatrixCell,
    ParityMatrix,
    run_parity_matrix,
)
from .checkpoint_parity_matrix import (
    _receipt as _matrix_receipt,
)
from .checkpoint_parity_tokenizer import TokenizedParityFixtures, load_parity_fixtures
from .host import TransformersHostBackend, load_verified_host


@dataclass(frozen=True)
class ParityQualification:
    source_device: str
    source_dtype: str
    base_digest: str
    fixtures: TokenizedParityFixtures
    official: OfficialSuite
    matrix: ParityMatrix


@dataclass(frozen=True)
class QualificationFailure:
    stage: str
    fixtures: TokenizedParityFixtures | None
    official: OfficialSuite | None
    matrix: ParityMatrix | None


class ParityQualificationError(RuntimeError):
    def __init__(self, failure):
        super().__init__(f"terminal pinned qualification error at {failure.stage}")
        self.failure = failure


class ParityQualificationInterrupted(KeyboardInterrupt):
    def __init__(self, failure):
        super().__init__(f"pinned qualification interrupted at {failure.stage}")
        self.failure = failure


def _hash(value):
    return type(value) is str and re.fullmatch(r"[0-9a-f]{64}", value) is not None


def _context(device):
    if (
        any(
            os.environ.get(flag) != "1"
            for flag in (
                "HF_HUB_OFFLINE",
                "TRANSFORMERS_OFFLINE",
                "HF_DATASETS_OFFLINE",
            )
        )
        or torch.is_inference_mode_enabled()
        or not torch.is_grad_enabled()
        or not torch.are_deterministic_algorithms_enabled()
        or torch.is_deterministic_algorithms_warn_only_enabled()
        or torch.get_default_device() != torch.device("cpu")
    ):
        raise ValueError(
            "offline deterministic grad-enabled ordinary CPU-default context required"
        )
    if device == "cuda:0" and (
        os.environ.get("CUBLAS_WORKSPACE_CONFIG") != ":4096:8"
        or not torch.cuda.is_available()
        or torch.cuda.current_device() != 0
        or not torch.cuda.is_bf16_supported()
        or torch.backends.cuda.matmul.allow_tf32
        or torch.backends.cudnn.allow_tf32
        or torch.backends.cudnn.benchmark
        or not torch.backends.cudnn.deterministic
        or not torch.backends.cuda.math_sdp_enabled()
        or torch.backends.cuda.flash_sdp_enabled()
        or torch.backends.cuda.mem_efficient_sdp_enabled()
        or torch.backends.cuda.cudnn_sdp_enabled()
    ):
        raise ValueError(
            "fixed deterministic CUDA0 BF16 math-reference context required"
        )


def _tokenized(value):
    if (
        type(value) is not TokenizedParityFixtures
        or value.model_revision != SMOLLM2_135M.revision
        or not _hash(value.snapshot_inventory_sha256)
        or not _hash(value.fixture_sha256)
        or type(value.tokenizer_class) is not str
        or not value.tokenizer_class
    ):
        raise ValueError("typed pinned tokenizer binding required")
    _schedule(value.fixtures)
    payload = {
        "fixtures": [asdict(fixture) for fixture in value.fixtures],
        "revision": value.model_revision,
        "snapshot_inventory_sha256": value.snapshot_inventory_sha256,
    }
    if (
        hashlib.sha256(canonical_json_bytes(payload)).hexdigest()
        != value.fixture_sha256
    ):
        raise ValueError("tokenizer fixture digest mismatch")


def _assets(receipt, tokenized):
    if (
        receipt.get("revision") != tokenized.model_revision
        or receipt.get("inventory_sha256") != tokenized.snapshot_inventory_sha256
    ):
        raise ValueError("same pinned snapshot across tokenizer and host required")
    return canonical_json_bytes(dict(receipt))


def _signature(host, device):
    if str(_base_device(host)) != device:
        raise ValueError("loaded host must use the requested exact device/dtype")
    if (
        getattr(getattr(host.model, "config", None), "_attn_implementation", None)
        != "eager"
    ):
        raise ValueError("declared eager reference host route required throughout")
    return (
        _base_digest(host.model),
        _roster_stamp(host.model.named_parameters()),
        _roster_stamp(host.model.named_buffers()),
        canonical_json_bytes(dict(host.config_identity)),
        canonical_json_bytes(dict(host.acquisition_receipt)),
    )


def _official(value, device, dtype, digest):
    schedule = tuple(
        (OfficialKey(cell.grid_id, cell.arm, phase), case)
        for cell in PARITY_CELLS
        for phase in ("unmounted", "zero", "detached")
        for case in FORWARD_CASES
    )
    if (
        type(value) is not OfficialSuite
        or (value.source_device, value.source_dtype, value.base_digest)
        != (device, dtype, digest)
        or type(value.cases) is not tuple
        or len(value.cases) != len(schedule)
        or type(value.nonzero_witnesses) is not tuple
        or len(value.nonzero_witnesses) != len(PARITY_CELLS)
    ):
        raise ValueError("complete same-base official-forward receipt required")
    for row, (key, case) in zip(value.cases, schedule, strict=True):
        _official_receipt(row, key, case)
    for row, cell in zip(value.nonzero_witnesses, PARITY_CELLS, strict=True):
        if (
            type(row) is not NonzeroWitness
            or (row.grid_id, row.arm) != (cell.grid_id, cell.arm)
            or not _hash(row.official_sha256)
            or not _hash(row.mounted_sha256)
            or row.official_sha256 == row.mounted_sha256
        ):
            raise ValueError("ordered changed-logit nonzero witnesses required")


def _matrix(value, device, dtype, digest):
    if (
        type(value) is not ParityMatrix
        or (value.source_device, value.source_dtype, value.base_digest)
        != (device, dtype, digest)
        or type(value.seed) is not int
        or value.seed != PARITY_SEED
        or type(value.cells) is not tuple
        or len(value.cells) != len(PARITY_CELLS)
    ):
        raise ValueError("complete same-base fixed D matrix receipt required")
    for row, key in zip(value.cells, PARITY_CELLS, strict=True):
        if type(row) is not MatrixCell or row.key != key:
            raise ValueError("fixed D grid/arm receipt order required")
        _matrix_receipt(row.result, key, digest)


def run_parity_qualification(snapshot: Path, *, device: str) -> ParityQualification:
    """Run fixed D and official suite over one offline CPU FP32/GPU BF16 host.

    Caller owns approved invocation/resources and durable journal/timeout. No
    injectable host/tokenizer/cell callback in this production boundary, retry,
    smaller-grid fallback, skip, process launch, output write or global setting
    mutation. Inner partial failure receipts remain accessible in chained causes.
    A returned observation is not P11, resource, scientific or training approval.
    """
    if not isinstance(snapshot, Path) or not snapshot.is_absolute():
        raise ValueError("absolute pinned snapshot path required")
    if type(device) is not str or device not in ("cpu", "cuda:0"):
        raise ValueError("separate CPU or CUDA0 invocation required")
    _context(device)
    dtype = torch.float32 if device == "cpu" else torch.bfloat16
    exact = device == "cpu"
    tokenized, official, matrix = None, None, None
    stage = "tokenizer"
    try:
        candidate = load_parity_fixtures(snapshot)
        _tokenized(candidate)
        _context(device)
        tokenized = candidate
        stage = "host"
        host = load_verified_host(
            snapshot,
            device=device,
            dtype=dtype,
            backend=TransformersHostBackend(attention_implementation="eager"),
        )
        assets = _assets(host.acquisition_receipt, tokenized)
        base = host.model
        signature = _signature(host, device)

        def unchanged():
            _context(device)
            _tokenized(tokenized)
            if host.model is not base or _signature(host, device) != signature:
                raise ValueError(
                    "one unchanged frozen base and host identity across qualification required"
                )

        unchanged()
        stage = "official"
        candidate = run_official_forward_suite(host, exact=exact)
        unchanged()
        _official(candidate, device, str(dtype), signature[0])
        official = candidate
        stage = "matrix"
        candidate = run_parity_matrix(host, tokenized.fixtures, exact=exact)
        unchanged()
        _matrix(candidate, device, str(dtype), signature[0])
        matrix = candidate
        stage = "terminal-assets"
        if _assets(verify_model_snapshot(snapshot), tokenized) != assets:
            raise ValueError("snapshot changed during qualification")
        unchanged()
        _official(official, device, str(dtype), signature[0])
        _matrix(matrix, device, str(dtype), signature[0])
    except KeyboardInterrupt as exc:
        raise ParityQualificationInterrupted(
            QualificationFailure(stage, tokenized, official, matrix)
        ) from exc
    except Exception as exc:
        raise ParityQualificationError(
            QualificationFailure(stage, tokenized, official, matrix)
        ) from exc
    return ParityQualification(
        device, str(dtype), signature[0], tokenized, official, matrix
    )
