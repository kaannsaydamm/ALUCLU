"""Enforce shared-base two-arm accumulation parity BEFORE either fixed step.

Factory is a cooperating, separately authenticated integration boundary. It
must return fresh wrappers/factors over ONE existing frozen base, not load two
bases or run an experiment implicitly. Caller owns all mutable state/results,
provides verified fixtures and records failure then discards/rebuilds both arms.
No full matrix, host/tokenizer/callback authentication or launch authority here.
"""

from dataclasses import dataclass

from torch import nn

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


def _storage(value):
    _tensor_stamp(value)
    return value.device, value.untyped_storage().data_ptr()


def run_accumulation_pair(factory, fixtures, *, exact):
    """Observe off, observe on, compare pre-clip, step off/on, compare full state.

    CPU exact comparison is mandatory. GPU uses the existing fixed tolerance
    contract; factory qualification/resource budgeting remain outside this API.
    Success is scoped pipeline execution, NOT actual-host/matrix/learning PASS.
    """
    if not callable(factory) or type(exact) is not bool:
        raise ObservationError("callable factory and exact boolean required")
    owned = []
    try:
        off = factory(False)
        if not isinstance(off, nn.Module):
            raise ObservationError("factory must return a cooperating wrapper")
        owned.extend(off._checkpoint_factors().parameters())
        base, off_factors, off_named, device = _bindings(off, "nonzero")
        if exact != (device.type == "cpu"):
            raise ObservationError("CPU exact/GPU fixed tolerance mode required")
        base_stamp = _roster_stamp(base.named_parameters())
        buffer_stamp = _roster_stamp(base.named_buffers())
        factor_stamp = _roster_stamp(off_named)
        reference = observe_accumulation(off, fixtures, checkpoint=False)

        on = factory(True)
        if not isinstance(on, nn.Module):
            raise ObservationError("factory must return a cooperating wrapper")
        owned.extend(on._checkpoint_factors().parameters())
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
            or {_storage(p) for _, p in off_named} & {_storage(p) for _, p in on_named}
        ):
            raise ObservationError("factory changed state or reused comparison arm")
        compare_named_tensors(dict(off_named), dict(on_named), exact=True)
        actual = observe_accumulation(on, fixtures, checkpoint=True)

        # This ordering is the integration invariant, not just documentation.
        compare_accumulations(reference, actual, exact=exact)
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
        reference_step = step_accumulation(off, reference)
        actual_step = step_accumulation(on, actual)
        comparison = compare_accumulation_steps(
            reference_step, actual_step, exact=exact
        )
        return AccumulationPair(reference_step, actual_step, comparison)
    except BaseException:
        for parameter in owned:
            parameter.grad = None
        raise
