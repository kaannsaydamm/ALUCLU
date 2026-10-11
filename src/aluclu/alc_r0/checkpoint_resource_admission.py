"""Pure resource arithmetic, NOT a reservation, authentication or launch permit.

Caller-provided accounting must be independently reconciled and authenticated.
Unknown history stays unknown. This module neither accesses assets nor journals
attempts; fsync-before-launch, exclusion, measured consumption, exact invocation
review and runtime qualification remain separate mandatory boundaries.
"""

from __future__ import annotations

from dataclasses import dataclass
from types import MappingProxyType

_NS = 10**9
_GPU_LIMIT_NS = 600 * 3600 * _NS
_PROGRAM_WINDOW_NS = 45 * 86400 * _NS
_RESEARCH_LIMIT_BYTES = 25 * (1 << 30)
_C_FREE_FLOOR_BYTES = 20 * (1 << 30)
_MAX_INTEGER = (1 << 63) - 1
_CEILINGS_NS = MappingProxyType(
    {"D": 45 * 60 * _NS, "E1": 30 * 60 * _NS, "E2": 10 * 60 * _NS, "E3": 30 * 60 * _NS}
)


@dataclass(frozen=True, slots=True)
class ProgramAccounting:
    """Trusted observation claims, not proof supplied by a hash string."""

    complete: bool
    first_development_utc_ns: int | None
    consumed_gpu_ns: int | None
    evidence_sha256: str | None


@dataclass(frozen=True, slots=True)
class ResourceRequest:
    accounting: ProgramAccounting
    phase: str
    device: str
    now_utc_ns: int
    research_bytes: int
    free_c_bytes: int
    projected_growth_bytes: int
    pending_gpu_ns: int
    pending_growth_bytes: int


@dataclass(frozen=True, slots=True)
class ResourceAssessment:
    resource_fit: bool
    reasons: tuple[str, ...]
    required_gpu_reservation_ns: int
    remaining_gpu_ns: int | None
    program_deadline_utc_ns: int | None


def _integer(value: object, name: str) -> None:
    if type(value) is not int or not 0 <= value <= _MAX_INTEGER:
        raise ValueError(f"{name} must be a nonnegative signed-64-bit integer")


def _validate(request: ResourceRequest) -> None:
    if (
        type(request) is not ResourceRequest
        or type(request.accounting) is not ProgramAccounting
    ):
        raise ValueError("exact ResourceRequest and ProgramAccounting required")
    if type(request.phase) is not str or request.phase not in _CEILINGS_NS:
        raise ValueError("unknown checkpoint phase")
    if type(request.device) is not str or request.device not in ("cpu", "gpu"):
        raise ValueError("device must be cpu or gpu")
    if request.phase != "D" and request.device != "gpu":
        raise ValueError("E resource matrix requires gpu")
    for name in (
        "now_utc_ns",
        "research_bytes",
        "free_c_bytes",
        "projected_growth_bytes",
        "pending_gpu_ns",
        "pending_growth_bytes",
    ):
        _integer(getattr(request, name), name)
    history = request.accounting
    if type(history.complete) is not bool:
        raise ValueError("history completeness must be bool")
    for name in ("first_development_utc_ns", "consumed_gpu_ns"):
        value = getattr(history, name)
        if value is not None:
            _integer(value, name)
    root = history.evidence_sha256
    if root is not None and (
        type(root) is not str
        or len(root) != 64
        or any(c not in "0123456789abcdef" for c in root)
    ):
        raise ValueError("accounting root must be canonical SHA256 or None")


def assess_resources(request: ResourceRequest) -> ResourceAssessment:
    """Check supplied observations without reserving or authorizing anything.

    GPU D/E is single-device: reserve its full wrapper ceiling conservatively.
    CPU D requires zero CUDA activity. Pending amounts MUST come from an exclusive
    durable journal; this helper cannot authenticate their completeness.
    """
    _validate(request)
    ceiling = _CEILINGS_NS[request.phase]
    required_gpu = ceiling if request.device == "gpu" else 0
    history = request.accounting
    reasons: list[str] = []
    remaining = deadline = None
    if (
        not history.complete
        or history.first_development_utc_ns is None
        or history.consumed_gpu_ns is None
        or history.evidence_sha256 is None
    ):
        reasons.append("history-unreconciled")
    else:
        remaining = _GPU_LIMIT_NS - history.consumed_gpu_ns - request.pending_gpu_ns
        deadline = history.first_development_utc_ns + _PROGRAM_WINDOW_NS
        if remaining < required_gpu:
            reasons.append("gpu-budget-insufficient")
        if (
            deadline > _MAX_INTEGER
            or request.now_utc_ns < history.first_development_utc_ns
            or request.now_utc_ns >= deadline
            or request.now_utc_ns + ceiling > deadline
        ):
            reasons.append("program-window-invalid")
    growth = request.pending_growth_bytes + request.projected_growth_bytes
    if request.research_bytes + growth > _RESEARCH_LIMIT_BYTES:
        reasons.append("research-storage-insufficient")
    if request.free_c_bytes - growth < _C_FREE_FLOOR_BYTES:
        reasons.append("c-free-space-insufficient")
    return ResourceAssessment(
        not reasons, tuple(reasons), required_gpu, remaining, deadline
    )
