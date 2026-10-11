"""Allocation policy arithmetic; never authentication, reservation or permission.

Kinds preserve observed facts versus justified upper bounds. The trusted real
coordinator must verify their provenance, complete coverage and clock domain.
Synthetic consistency cannot supply missing history or launch a scientific job.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, fields
from types import MappingProxyType

_MAX = (1 << 63) - 1
_NS = 10**9
_TAIL = 10 * _NS
_GPU_LIMIT = 600 * 3600 * _NS
_WINDOW = 45 * 86400 * _NS
_RESEARCH_LIMIT = 25 * (1 << 30)
_FREE_FLOOR = 20 * (1 << 30)
_ROOT = re.compile(r"[0-9a-f]{64}\Z")
_CEILINGS = MappingProxyType({"D":45*60*_NS,"E1":30*60*_NS,
    "E2":10*60*_NS,"E3":30*60*_NS,"pilot":2*3600*_NS})
_REASONS = ("history-unreconciled","clock-unreconciled","gpu-budget-insufficient",
    "monotonic-window-invalid","program-window-invalid","resource-arithmetic-overflow",
    "research-storage-insufficient","c-free-space-insufficient")


@dataclass(frozen=True, slots=True)
class AllocationAccounting:
    policy_root: str | None
    coverage_root: str | None
    charge_kind: str
    effective_gpu_ns: int | None
    clock_kind: str
    clock_utc_ns: int | None


@dataclass(frozen=True, slots=True)
class AllocationRequest:
    accounting: AllocationAccounting
    phase: str
    device: str
    now_utc_ns: int
    entry_monotonic_ns: int
    now_monotonic_ns: int
    research_bytes: int
    free_c_bytes: int
    projected_research_growth_bytes: int
    projected_physical_growth_bytes: int
    pending_research_growth_bytes: int
    pending_physical_growth_bytes: int
    pending_gpu_ns: int


@dataclass(frozen=True, slots=True)
class AllocationAssessment:
    resource_fit: bool
    reasons: tuple[str, ...]
    useful_deadline_monotonic_ns: int | None
    cleanup_deadline_monotonic_ns: int | None
    required_gpu_reservation_ns: int | None
    remaining_gpu_ns: int | None
    program_deadline_utc_ns: int | None


def _integer(value):
    if type(value) is not int or not 0 <= value <= _MAX:
        raise ValueError("exact nonnegative signed64 observation required")


def _validate(request):
    if type(request) is not AllocationRequest or type(request.accounting) is not AllocationAccounting:
        raise ValueError("exact allocation request/accounting required")
    if type(request.phase) is not str or request.phase not in _CEILINGS:
        raise ValueError("fixed declared phase required")
    if type(request.device) is not str or request.device not in ("cpu","gpu"):
        raise ValueError("explicit cpu/gpu device required")
    if request.device == "cpu" and request.phase != "D":
        raise ValueError("E and original pilot require single GPU")
    for field in fields(AllocationRequest):
        if field.name not in ("accounting","phase","device"):
            _integer(getattr(request,field.name))
    facts = request.accounting
    for root in (facts.policy_root,facts.coverage_root):
        if root is not None and (type(root) is not str or not _ROOT.fullmatch(root)):
            raise ValueError("canonical evidence root or unknown required")
    if type(facts.charge_kind) is not str or facts.charge_kind not in (
            "observed","allocation_upper_bound","unknown"):
        raise ValueError("explicit charge kind required")
    if type(facts.clock_kind) is not str or facts.clock_kind not in (
            "observed","conservative_boundary","prospective_pending","unknown"):
        raise ValueError("explicit clock kind required")
    if (facts.charge_kind == "unknown") != (facts.effective_gpu_ns is None):
        raise ValueError("charge kind/value mismatch")
    if (facts.clock_kind in ("unknown","prospective_pending")) != (facts.clock_utc_ns is None):
        raise ValueError("clock kind/value mismatch")
    for value in (facts.effective_gpu_ns,facts.clock_utc_ns):
        if value is not None:
            _integer(value)


def assess_allocation(request: AllocationRequest) -> AllocationAssessment:
    """Assess supplied kinds/numbers, not their truth, authority or reservation.

    Entry/current monotonic observations must share a verified clock domain.
    Effective prior charge includes released work without overlapping history;
    pending values require a current durable complete reservation snapshot.
    """
    _validate(request)
    facts = request.accounting
    failures = set()

    def checked(value):
        if value > _MAX:
            failures.add("resource-arithmetic-overflow")
            return None
        return value

    ceiling = _CEILINGS[request.phase]
    useful = checked(request.entry_monotonic_ns + ceiling)
    cleanup = checked(request.entry_monotonic_ns + ceiling + _TAIL)
    required = ceiling + _TAIL if request.device == "gpu" else 0
    if (useful is None or request.now_monotonic_ns < request.entry_monotonic_ns
            or request.now_monotonic_ns >= useful):
        failures.add("monotonic-window-invalid")

    remaining = None
    if (facts.effective_gpu_ns is None or facts.policy_root is None
            or facts.coverage_root is None):
        failures.add("history-unreconciled")
    else:
        # Bounded exact temporary arithmetic establishes insufficiency even
        # when the checked sum cannot be emitted as a signed64 remaining value.
        charged = facts.effective_gpu_ns + request.pending_gpu_ns
        if _GPU_LIMIT - charged < required:
            failures.add("gpu-budget-insufficient")
        if checked(charged) is not None:
            remaining = _GPU_LIMIT - charged

    program = None
    if facts.clock_utc_ns is None:
        failures.add("clock-unreconciled")
    else:
        program = checked(facts.clock_utc_ns + _WINDOW)
        completion = None if useful is None else checked(request.now_utc_ns
            + max(0,useful-request.now_monotonic_ns) + _TAIL)
        if (program is None or completion is None
                or request.now_utc_ns < facts.clock_utc_ns
                or request.now_utc_ns >= program or completion > program):
            failures.add("program-window-invalid")

    research_growth = request.pending_research_growth_bytes + request.projected_research_growth_bytes
    physical_growth = request.pending_physical_growth_bytes + request.projected_physical_growth_bytes
    research_total = request.research_bytes + research_growth
    for total in (research_growth,physical_growth,research_total):
        checked(total)
    if research_total > _RESEARCH_LIMIT:
        failures.add("research-storage-insufficient")
    if request.free_c_bytes-physical_growth < _FREE_FLOOR:
        failures.add("c-free-space-insufficient")
    reasons = tuple(reason for reason in _REASONS if reason in failures)
    return AllocationAssessment(not reasons,reasons,useful,cleanup,required,remaining,program)
