"""Fixed separate q/v cell binding; no loader or public execution callback.

Caller authenticates host/fixtures/source/runtime and admits inclusive resources.
Digest binding does not authenticate supplied metadata. This is disposable
synthetic parity, not task training, E3, learning or complete host qualification.
Cooperative exclusive ownership is required; failures are terminal, not rollback.
"""

from dataclasses import asdict, dataclass, replace
from weakref import WeakSet, ref

import torch

from .checkpoint_accumulation_progress import (
    _AccumulationOwner,
    _bounded_faults,
    _clear_owned,
    _owner_faults,
    _safe_snapshot,
    validate_accumulation_failure,
)
from .checkpoint_execution import CheckpointController, _digest
from .checkpoint_observation import _bindings
from .checkpoint_parity_cell import (
    SINGLE_SCHEDULE,
    CaseComparison,
    ParityCell,
    ParityCellError,
    ParityCellFailure,
    ParityCellInterrupted,
    _FactoryGuard,
    _schedule,
    run_parity_cell,
)
from .checkpoint_parity_factory import PARITY_SEED, make_reference_wrapper
from .reference_official_suite import _json_digest, _sha, _signature
from .reference_parity_receipt import (
    REFERENCE_NAMES,
    ReferenceParityIdentity,
    ReferenceParityReceipt,
    _pair,
    validate_reference_parity_receipt,
)
from .reference_qv_artifact import _live_factors
from .reference_qv_lora import ReferenceQVLoRA
from .reference_qv_wrapper import PinnedLlamaQVReferenceWrapper


@dataclass(frozen=True)
class ReferenceParityFailure:
    stage: str
    cell_failure: ParityCellFailure | None


class ReferenceParityError(RuntimeError):
    def __init__(self, failure, *, journal_fault=False, cleanup_fault=False):
        super().__init__(f"terminal q/v parity failure at {failure.stage}")
        self.failure = failure
        self.journal_fault, self.cleanup_fault = _bounded_faults(
            journal_fault, cleanup_fault
        )


class ReferenceParityInterrupted(KeyboardInterrupt):
    def __init__(self, failure, *, journal_fault=False, cleanup_fault=False):
        super().__init__(f"q/v parity interrupted at {failure.stage}")
        self.failure = failure
        self.journal_fault, self.cleanup_fault = _bounded_faults(
            journal_fault, cleanup_fault
        )


def _completed_progress(cell):
    """Retain only bounded scalar observations, even if final admission fails.

    This is shape/finite framing, not success validation. Invalid/corrupt
    observations are not copied into a supposedly bounded failure payload.
    """
    progress, invalid = _capture_completed_progress(cell)
    return None if invalid else progress


_FAILURE_STAGES = frozenset(
    (
        "single_factory_off",
        "single_off",
        "single_factory_on",
        "single_on",
        "single_compare",
        "single_repeat",
        "single_order",
        "single_receipt",
        "pending_factory_off",
        "pending_off",
        "pending_factory_on",
        "pending_on",
        "pending_compare",
        "accumulation",
        "final_base",
        "cell_returned",
        "receipt",
        "invalid_inner",
    )
)


def _case_key(value):
    return (
        type(value) is tuple
        and len(value) == 3
        and type(value[0]) is str
        and value[0] in ("zero", "nonzero")
        and type(value[1]) is int
        and type(value[2]) is int
        and value in SINGLE_SCHEDULE
    )


def _failure_row(row, expected):
    if type(row) is not CaseComparison or not _exact_fields(
        row,
        {
            "state",
            "repeat",
            "fixture_index",
            "losses",
            "scores",
            "base_digest",
            "factor_digest",
        },
    ):
        raise ValueError("exact bounded scalar comparison row required")
    key = row.state, row.repeat, row.fixture_index
    if not _case_key(key) or key != expected:
        raise ValueError("canonical completed single prefix required")
    _pair(row.losses, exact=False)
    _pair(row.scores, exact=False)
    _sha(row.base_digest)
    _sha(row.factor_digest)


def _exact_fields(value, names):
    values = vars(value)
    return (
        type(values) is dict
        and len(values) == len(names)
        and all(type(key) is str for key in values)
        and set(values) == names
    )


def _sanitize_cell_failure(value):
    """Keep independent bounded diagnostics, not acceptance or inferred progress."""
    if type(value) is not ParityCellFailure:
        return None, True
    fault = not _exact_fields(
        value,
        {
            "stage",
            "completed",
            "current",
            "unrun",
            "pending_losses",
            "accumulation",
        },
    )
    stage = getattr(value, "stage", None)
    if type(stage) is not str or len(stage) > 32 or stage not in _FAILURE_STAGES:
        fault = True
    completed = ()
    supplied = getattr(value, "completed", None)
    if type(supplied) is tuple and len(supplied) <= 18:
        for index, row in enumerate(supplied):
            try:
                _failure_row(row, SINGLE_SCHEDULE[index])
            except BaseException:
                fault = True
                break
            completed += (row,)
    else:
        fault = True
    current = getattr(value, "current", None)
    if current is not None and (
        not _case_key(current)
        or len(completed) == 18
        or current != SINGLE_SCHEDULE[len(completed)]
    ):
        current, fault = None, True
    unrun = getattr(value, "unrun", None)
    valid_unrun = (
        type(unrun) is tuple
        and len(unrun) <= 18
        and all(_case_key(key) for key in unrun)
        and any(
            unrun == SINGLE_SCHEDULE[start:]
            for start in (
                (len(completed), len(completed) + 1)
                if current is not None
                else (len(completed),)
            )
        )
    )
    if not valid_unrun:
        unrun, fault = (), True
    pending = getattr(value, "pending_losses", None)
    if pending is not None:
        try:
            _pair(pending, exact=False)
        except BaseException:
            pending, fault = None, True
    accumulation = getattr(value, "accumulation", None)
    if accumulation is not None:
        try:
            validate_accumulation_failure(accumulation)
        except BaseException:
            accumulation, fault = None, True
    if not fault:
        return value, False
    return ParityCellFailure(
        "invalid_inner", completed, current, unrun, pending, accumulation
    ), True


def _capture_completed_progress(cell):
    """Cache only bounded returned fields; retain independent valid diagnostics."""
    try:
        if (
            type(cell) is not ParityCell
            or type(cell.cases) is not tuple
            or len(cell.cases) != 18
        ):
            return None, True
        return _sanitize_cell_failure(
            ParityCellFailure(
                "cell_returned", cell.cases, None, (), cell.pending_losses
            )
        )
    except BaseException:
        # Diagnostic framing must not replace a subsequent primary failure.
        return None, True


class _ReferenceFactory:
    def __init__(self, host, signature, exact):
        self.host, self.signature = host, signature
        self.base = host.model
        self.controllers = WeakSet()
        self.guard = _FactoryGuard(self._make, exact)
        self.cleanup_parameters = {}
        # Reconstruct only bounded private CPU masters, never host assets.
        original = ReferenceQVLoRA(seed=PARITY_SEED)
        named = tuple(_live_factors(original).items())
        self.digests = {"zero": _digest(named)}
        with torch.no_grad():
            for name, parameter in named:
                if name.endswith(".B"):
                    values = (
                        torch.arange(parameter.numel(), device="cpu") % 17 - 8
                    ).float() * 1e-4
                    parameter.copy_(values.reshape(parameter.shape))
        self.digests["nonzero"] = _digest(named)

    def unchanged(self):
        if self.host.model is not self.base or _signature(self.host) != self.signature:
            raise ValueError("one unchanged base/configuration/host identity required")

    def _make(self, state, checkpoint):
        self.unchanged()
        wrapper = make_reference_wrapper(self.host, checkpoint, state=state)
        if type(wrapper) is not PinnedLlamaQVReferenceWrapper:
            raise ValueError("exact q/v wrapper required")
        # Keep separate cleanup ownership BEFORE validation can throw. Do not
        # pre-register in the generic freshness guard (it would see a duplicate).
        # Never clear caller-base parameters, including a malicious mount alias.
        candidate = wrapper.reference
        base_ids = {id(p) for p in self.base.parameters()}
        if type(candidate) is ReferenceQVLoRA:
            for parameter in candidate.parameters():
                if id(parameter) not in base_ids:
                    self.cleanup_parameters[id(parameter)] = ref(parameter)
        base, factors, named, device = _bindings(wrapper, state)
        controller = wrapper._checkpoint_controller
        if (
            base is not self.base
            or device != self.signature[0]
            or wrapper.capsule is not None
            or getattr(wrapper, "lora", None) is not None
            or type(factors) is not ReferenceQVLoRA
            or wrapper.reference is not factors
            or type(factors.initialization_seed) is not int
            or factors.initialization_seed != PARITY_SEED
            or tuple(_live_factors(factors)) != REFERENCE_NAMES
            or sum(p.numel() for _, p in named) != 460800
            or any(p.grad is not None or p.is_inference() for _, p in named)
            or _digest(named) != self.digests[state]
            or type(controller) is not CheckpointController
            or controller.owner is not wrapper
            or controller in self.controllers
            or controller._active is not None
            or type(controller.layer_count) is not int
            or controller.layer_count != 30
            or controller.base_getter() is not base
            or controller.factor_getter() is not factors
            or (checkpoint and not callable(controller.state_fingerprint_getter))
            or (not checkpoint and controller.state_fingerprint_getter is not None)
        ):
            raise ValueError(
                "original120 q/v masters and independent controller binding required"
            )
        self.controllers.add(controller)
        self.unchanged()
        return wrapper

    def make(self, state, checkpoint):
        # Existing generic guard enforces fresh wrapper/factor/parameter/storage
        # ownership even if a caller test replaces the execution engine.
        return self.guard.make(state, checkpoint)

    def clear(self):
        fault = False
        try:
            fault = self.guard.clear() is True
        except BaseException:
            fault = True
        try:
            own_fault = _clear_owned(
                parameter
                for weak in self.cleanup_parameters.values()
                if (parameter := weak()) is not None
            )
        except BaseException:
            own_fault = True
        return fault or own_fault


def _failure_progress(exc, completed, owner, stage, completed_fault=False):
    if type(exc) in (ParityCellError, ParityCellInterrupted):
        journal, cleanup = _bounded_faults(
            getattr(exc, "journal_fault", None), getattr(exc, "cleanup_fault", None)
        )
        try:
            inner, invalid = _sanitize_cell_failure(getattr(exc, "failure", None))
        except BaseException:
            inner, invalid = None, True
        journal = journal or invalid or completed_fault
        if inner is None:
            return None, journal, cleanup
        if inner.accumulation is not None:
            try:
                validate_accumulation_failure(inner.accumulation)
                journal = journal or inner.accumulation.journal_fault
                cleanup = cleanup or inner.accumulation.cleanup_fault
            except BaseException:
                inner, journal = replace(inner, accumulation=None), True
        return inner, journal, cleanup
    accumulation, journal = _safe_snapshot(owner)
    owner_journal, cleanup = _owner_faults(owner)
    invalid = False
    if completed is not None:
        try:
            completed, invalid = _sanitize_cell_failure(completed)
        except BaseException:
            completed, invalid = None, True
    inner = (
        replace(completed, stage=stage, accumulation=accumulation)
        if completed is not None
        else None
    )
    return inner, journal or owner_journal or completed_fault or invalid, cleanup


def run_reference_parity_suite(host, fixtures, *, exact, expected_fixture_digest):
    """Bind fixed factory, generic cell and bounded separate success receipt.

    No public loader/factory/execution callback. The fixture digest must originate
    in caller-authenticated framing; equality alone does not confer provenance.
    Original cell keeps18 singles/pending pair/16 accumulation/preclip comparisons
    and fixed step1. Failures retain bounded accumulation progress. Outer owner
    persists scalar evidence and discards live chained
    exceptions/wrappers; this function neither journals process kills nor retries.
    """
    if (
        type(exact) is not bool
        or torch.is_inference_mode_enabled()
        or not torch.is_grad_enabled()
    ):
        raise ValueError(
            "explicit mode and ordinary grad-enabled construction required"
        )
    _schedule(fixtures)
    _sha(expected_fixture_digest)
    fixture_digest = _json_digest([asdict(fixture) for fixture in fixtures])
    if fixture_digest != expected_fixture_digest:
        raise ValueError("expected six-fixture digest required")
    signature = _signature(host)
    if exact != (signature[0].type == "cpu"):
        raise ValueError("CPU exact/GPU fixed tolerance mode required")
    identity = ReferenceParityIdentity(
        str(signature[0]),
        str(next(host.model.parameters()).dtype),
        signature[1],
        signature[5],
        signature[6],
        fixture_digest,
    )
    stage, factory, completed_progress = "prepare", None, None
    completed_fault = False
    accumulation_owner = _AccumulationOwner()
    try:
        factory = _ReferenceFactory(host, signature, exact)
        stage = "cell"
        cell = run_parity_cell(
            factory.make, fixtures, exact=exact, _accumulation_owner=accumulation_owner
        )
        completed_progress, completed_fault = _capture_completed_progress(cell)
        stage = "final_base"
        factory.unchanged()
        stage = "receipt"
        result = ReferenceParityReceipt(identity, PARITY_SEED, cell)
        validate_reference_parity_receipt(result, expected_identity=identity)
        if any(row.factor_digest != factory.digests[row.state] for row in cell.cases):
            raise ValueError("receipt must bind original seeded factor state bytes")
        factory.unchanged()
        # Revalidate after the final outer check: frozen non-slotted records can
        # acquire extra fields after capture. A detected fault cannot be success.
        completed_progress, final_fault = _capture_completed_progress(cell)
        completed_fault = completed_fault or final_fault
        if completed_fault:
            raise ValueError("invalid returned cell diagnostic framing")
        return result
    except BaseException as exc:
        inner, journal_fault, cleanup_fault = _failure_progress(
            exc, completed_progress, accumulation_owner, stage, completed_fault
        )
        if factory is not None:
            try:
                local_cleanup = factory.clear() is True
            except BaseException:
                local_cleanup = True
            cleanup_fault = cleanup_fault or local_cleanup
        if inner is not None and inner.accumulation is not None:
            inner = replace(
                inner,
                accumulation=replace(
                    inner.accumulation,
                    journal_fault=journal_fault,
                    cleanup_fault=cleanup_fault,
                ),
            )
        if isinstance(exc, (Exception, KeyboardInterrupt)):
            error = (
                ReferenceParityInterrupted
                if isinstance(exc, KeyboardInterrupt)
                else ReferenceParityError
            )
            raise error(
                ReferenceParityFailure(stage, inner),
                journal_fault=journal_fault,
                cleanup_fault=cleanup_fault,
            ) from exc
        raise
