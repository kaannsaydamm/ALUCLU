"""Enforce shared-base two-arm accumulation parity BEFORE either fixed step.

Factory is a cooperating, separately authenticated integration boundary. It
must return fresh wrappers/factors over ONE existing frozen base, not load two
bases or run an experiment implicitly. Caller owns all mutable state/results,
provides verified fixtures and records failure then discards/rebuilds both arms.
No full matrix, host/tokenizer/callback authentication or launch authority here.
"""

from dataclasses import dataclass, replace

from torch import nn

from .checkpoint_accumulation_progress import (
    _clear_owned,
    _fresh_owner,
    _owner_faults,
    _pair_phase,
    _safe_snapshot,
)
from .checkpoint_accumulation_step import (
    AccumulationStep,
    compare_accumulation_steps,
    step_accumulation,
)
from .checkpoint_execution import _digest, _tensor_stamp
from .checkpoint_fidelity import compare_named_tensors
from .checkpoint_observation import (
    ObservationError,
    _base_digest,
    _bindings,
    _roster_stamp,
    compare_accumulations,
    observe_accumulation,
)
from .checkpoint_optimizer import AdamWComparison


@dataclass(frozen=True)
class AccumulationPair:
    reference: AccumulationStep
    actual: AccumulationStep
    comparison: AdamWComparison


class AccumulationError(ObservationError):
    def __init__(self, message, failure, *, journal_fault=False, cleanup_fault=False):
        super().__init__(message)
        self.failure = failure
        self.journal_fault = journal_fault
        self.cleanup_fault = cleanup_fault


class AccumulationInterrupted(KeyboardInterrupt):
    def __init__(self, message, failure, *, journal_fault=False, cleanup_fault=False):
        super().__init__(message)
        self.failure = failure
        self.journal_fault = journal_fault
        self.cleanup_fault = cleanup_fault


def _storage(value):
    _tensor_stamp(value)
    return value.device, value.untyped_storage().data_ptr()


def run_accumulation_pair(factory, fixtures, *, exact, _accumulation_owner=None):
    """Observe off, observe on, compare pre-clip, step off/on, compare full state.

    CPU exact comparison is mandatory. GPU uses the existing fixed tolerance
    contract; factory qualification/resource budgeting remain outside this API.
    Success is scoped pipeline execution, NOT actual-host/matrix/learning PASS.
    """
    if not callable(factory) or type(exact) is not bool:
        raise ObservationError("callable factory and exact boolean required")
    owned = []
    owner = None
    try:
        owner = _fresh_owner(_accumulation_owner)
        with _pair_phase(owner, "off_factory"):
            off = factory(False)
        with _pair_phase(owner, "off_bindings"):
            if not isinstance(off, nn.Module):
                raise ObservationError("factory must return a cooperating wrapper")
            base_ids = {id(p) for p in off.base.parameters()}
            owned.extend(
                p
                for p in off._checkpoint_factors().parameters()
                if id(p) not in base_ids
            )
            base, off_factors, off_named, device = _bindings(off, "nonzero")
            if exact != (device.type == "cpu"):
                raise ObservationError("CPU exact/GPU fixed tolerance mode required")
            base_stamp = _roster_stamp(base.named_parameters())
            buffer_stamp = _roster_stamp(base.named_buffers())
            factor_stamp = _roster_stamp(off_named)
        with _pair_phase(owner, "off_observation"):
            reference = observe_accumulation(
                off,
                fixtures,
                checkpoint=False,
                _accumulation_ticket=owner.ticket("off"),
            )

        with _pair_phase(owner, "on_factory"):
            on = factory(True)
        with _pair_phase(owner, "on_bindings"):
            if not isinstance(on, nn.Module):
                raise ObservationError("factory must return a cooperating wrapper")
            protected = base_ids | {id(p) for p in on.base.parameters()}
            owned.extend(
                p
                for p in on._checkpoint_factors().parameters()
                if id(p) not in protected
            )
            on_base, on_factors, on_named, on_device = _bindings(on, "nonzero")
            if (
                on is off
                or on_base is not base
                or on_factors is off_factors
                or on_device != device
                or off.base is not base
                or off._checkpoint_factors() is not off_factors
                or _roster_stamp(base.named_parameters()) != base_stamp
                or _roster_stamp(base.named_buffers()) != buffer_stamp
                or _roster_stamp(
                    sorted(
                        off_factors.named_parameters(remove_duplicate=False),
                        key=lambda item: item[0].encode("utf-8"),
                    )
                )
                != factor_stamp
                or _base_digest(base) != reference.forwards[0].base_digest
                or _digest(off_named) != reference.forwards[0].factor_digest
                or {_storage(p) for _, p in off_named}
                & {_storage(p) for _, p in on_named}
            ):
                raise ObservationError("factory changed state or reused comparison arm")
            compare_named_tensors(dict(off_named), dict(on_named), exact=True)
        with _pair_phase(owner, "on_observation"):
            actual = observe_accumulation(
                on, fixtures, checkpoint=True, _accumulation_ticket=owner.ticket("on")
            )

        # This ordering is the integration invariant, not just documentation.
        with _pair_phase(owner, "preclip_compare"):
            compare_accumulations(reference, actual, exact=exact)
        with _pair_phase(owner, "cross_arm_storage"):
            used = {
                _storage(value)
                for value in (
                    *base.parameters(),
                    *base.buffers(),
                    *off_factors.parameters(),
                    *on_factors.parameters(),
                )
            }
            for parameter in owned:
                if parameter.grad is None:
                    raise ObservationError("both live accumulated gradients required")
                storage = _storage(parameter.grad)
                if storage in used:
                    raise ObservationError("cross-arm gradient/state storage alias")
                used.add(storage)
        with _pair_phase(owner, "off_step"):
            reference_step = step_accumulation(
                off, reference, _accumulation_ticket=owner.ticket("off")
            )
        with _pair_phase(owner, "on_step"):
            actual_step = step_accumulation(
                on, actual, _accumulation_ticket=owner.ticket("on")
            )
        with _pair_phase(owner, "full_step_compare"):
            comparison = compare_accumulation_steps(
                reference_step, actual_step, exact=exact
            )
        with _pair_phase(owner, "pair_record"):
            result = AccumulationPair(reference_step, actual_step, comparison)
        owner.close()
        return result
    except BaseException as exc:
        failure, journal_fault = _safe_snapshot(owner)
        owner_journal, owner_cleanup = _owner_faults(owner)
        journal_fault = journal_fault or owner_journal
        cleanup_fault = _clear_owned(owned)
        cleanup_fault = cleanup_fault or owner_cleanup
        if failure is not None:
            journal_fault = journal_fault or failure.journal_fault
            cleanup_fault = cleanup_fault or failure.cleanup_fault
        if owner is not None:
            try:
                owner.close()
            except BaseException:
                journal_fault = True
        if failure is not None:
            failure = replace(
                failure, journal_fault=journal_fault, cleanup_fault=cleanup_fault
            )
        if isinstance(exc, (Exception, KeyboardInterrupt)):
            error = (
                AccumulationInterrupted
                if isinstance(exc, KeyboardInterrupt)
                else AccumulationError
            )
            raise error(
                str(exc),
                failure,
                journal_fault=journal_fault,
                cleanup_fault=cleanup_fault,
            ) from exc
        raise
