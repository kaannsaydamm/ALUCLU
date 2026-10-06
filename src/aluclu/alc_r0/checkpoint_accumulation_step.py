"""One disposable fixed AdamW step after a caller-compared accumulation.

Cooperating/quiescent caller contract, not launch or task-training authority.
Caller compares BOTH pre-clip accumulations before invoking either step. Own
all mutable records/optimizer state exclusively; discard/rebuild on failure,
never catch-and-continue or assume rollback. No host/assets are loaded here.
"""

from dataclasses import dataclass

import torch

from .checkpoint_accumulation_progress import (
    _admit_ticket,
    _arm_begin,
    _arm_finish,
    _cleanup_journaled,
)
from .checkpoint_execution import _digest, _tensor_stamp
from .checkpoint_fidelity import compare_named_tensors, compare_tensor
from .checkpoint_observation import (
    AccumulationObservation,
    ObservationError,
    _base_digest,
    _bindings,
    _gradient_mapping,
    _roster_stamp,
    compare_accumulations,
)
from .checkpoint_optimizer import _group, _snapshot, compare_adamw_states


@dataclass(frozen=True)
class AccumulationStep:
    observation: AccumulationObservation
    gradient_norm: torch.Tensor
    clipped_gradients: tuple[tuple[str, torch.Tensor], ...]
    optimizer: torch.optim.AdamW
    factors: dict[str, torch.nn.Parameter]
    base_parameters: tuple[torch.nn.Parameter, ...]


def _structure(named):
    return tuple(
        (name, stamp[0], *stamp[2:])
        for name, value in named
        for stamp in (_tensor_stamp(value),)
    )


def step_accumulation(wrapper, observation, *, _accumulation_ticket=None):
    """Caller must already have compared off/on pre-clip gradients.

    Returns live optimizer/factor bindings for complete step1 comparison.
    This does not prove that caller comparison/authentication/launch occurred.
    """
    ticket = _accumulation_ticket
    _admit_ticket(ticket)
    _arm_begin(ticket, "step_admit")
    if (
        type(observation) is not AccumulationObservation
        or type(observation.forwards) is not tuple
        or len(observation.forwards) != 16
    ):
        raise ObservationError("complete16-forward accumulation required")
    base, factors, named, device = _bindings(wrapper, "nonzero")
    captured = observation.forwards[0]
    before_base, before_factor = _base_digest(base), _digest(named)
    if (
        captured.base_digest != before_base
        or captured.factor_digest != before_factor
        or captured.source_device != str(device)
        or captured.state != "nonzero"
    ):
        raise ObservationError("live state differs from pre-clip observation")
    _arm_finish(ticket, "step_admit")
    _arm_begin(ticket, "step_live_gradients")
    gradients = _gradient_mapping(captured.gradients)
    if set(gradients) != {name for name, _ in named}:
        raise ObservationError("complete pre-clip gradient roster required")
    used = {
        (value.device, value.untyped_storage().data_ptr())
        for value in (*base.parameters(), *base.buffers(), *factors.parameters())
    }
    for name, parameter in named:
        gradient = parameter.grad
        if gradient is None:
            raise ObservationError("live accumulated gradient required")
        _tensor_stamp(gradient)
        storage = (gradient.device, gradient.untyped_storage().data_ptr())
        if storage in used:
            raise ObservationError("gradient storage aliases state/gradient")
        used.add(storage)
        compare_tensor(gradients[name], gradient.detach().cpu().clone(), exact=True)
    base_parameters = tuple(base.parameters())
    base_stamp = _roster_stamp(base.named_parameters())
    buffer_stamp = _roster_stamp(base.named_buffers())
    structure = _structure(named)
    _arm_finish(ticket, "step_live_gradients")
    _arm_begin(ticket, "step_guard")
    # Explicit mutation guard: no stepping inside a still-active lease.
    guard = getattr(wrapper, "_assert_checkpoint_mutation_allowed", None)
    if guard is None:
        guard = wrapper.controller.assert_mutation_allowed
    guard()
    _arm_finish(ticket, "step_guard")
    _arm_begin(ticket, "step_optimizer_create")
    optimizer = torch.optim.AdamW(
        [p for _, p in named],
        lr=3e-4,
        betas=(0.9, 0.999),
        eps=1e-8,
        weight_decay=0,
        foreach=False,
        fused=False,
    )
    _arm_finish(ticket, "step_optimizer_create")
    _arm_begin(ticket, "step_optimizer_group")
    _group(optimizer)
    _arm_finish(ticket, "step_optimizer_group")
    try:
        _arm_begin(ticket, "step_clip")
        norm = torch.nn.utils.clip_grad_norm_(
            [p for _, p in named], 1.0, error_if_nonfinite=True, foreach=False
        )
        _arm_finish(ticket, "step_clip")
        _arm_begin(ticket, "step_clipped_capture")
        clipped = tuple((name, p.grad.detach().cpu().clone()) for name, p in named)
        _arm_finish(ticket, "step_clipped_capture")
        _arm_begin(ticket, "step_optimizer_call")
        optimizer.step()
        _arm_finish(ticket, "step_optimizer_call")
        _arm_begin(ticket, "step_postconditions")
        live_named = tuple(sorted(factors.named_parameters(remove_duplicate=False)))
        if (
            wrapper.base is not base
            or wrapper._checkpoint_factors() is not factors
            or not wrapper.training
            or not factors.training
            or any(module.training for module in base.modules())
            or _roster_stamp(base.named_parameters()) != base_stamp
            or _roster_stamp(base.named_buffers()) != buffer_stamp
            or _structure(live_named) != structure
            or _base_digest(base) != before_base
            or any(p.grad is not None for p in base_parameters)
        ):
            raise ObservationError("frozen/binding invariant changed across step")
        _arm_finish(ticket, "step_postconditions")
        _arm_begin(ticket, "step_snapshot")
        mapping = dict(named)
        _snapshot(optimizer, mapping, base_parameters, 1)
        _arm_finish(ticket, "step_snapshot")
        _arm_begin(ticket, "step_record")
        result = AccumulationStep(
            observation,
            norm.detach().cpu().clone(),
            clipped,
            optimizer,
            mapping,
            base_parameters,
        )
        _arm_finish(ticket, "step_record")
        return result
    except BaseException:
        if ticket is None:
            for _, parameter in named:
                parameter.grad = None
        else:
            _cleanup_journaled(ticket, (parameter for _, parameter in named))
        raise


def compare_accumulation_steps(reference, actual, *, exact):
    if type(reference) is not AccumulationStep or type(actual) is not AccumulationStep:
        raise ObservationError("typed fixed-step comparison required")
    compare_accumulations(reference.observation, actual.observation, exact=exact)
    compare_tensor(reference.gradient_norm, actual.gradient_norm, exact=exact)
    compare_named_tensors(
        _gradient_mapping(reference.clipped_gradients),
        _gradient_mapping(actual.clipped_gradients),
        exact=exact,
    )
    return compare_adamw_states(
        reference.optimizer,
        actual.optimizer,
        reference.factors,
        actual.factors,
        reference_base_parameters=reference.base_parameters,
        actual_base_parameters=actual.base_parameters,
        expected_step=1,
        exact=exact,
    )
