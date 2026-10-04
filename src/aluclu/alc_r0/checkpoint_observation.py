"""Single synthetic parity observation; not a host authenticator or launch gate.

The separately reviewed runner must authenticate host/tokenizer/callback and
execute the complete matrix. This component accepts a cooperating wrapper and
does not load assets, step an optimizer, or confer learning acceptance.
The caller must retain exclusive ownership of mutable observation tensors.
Failure clears original factor gradients, not wrapper state: record the failure
and discard/rebuild that state before another arm; no automatic retry or rollback.
"""

from dataclasses import dataclass

import torch
from torch import nn

from .banking_scoring import score_banking_candidate
from .checkpoint_execution import _digest, _tensor_stamp
from .checkpoint_fidelity import compare_named_tensors, compare_tensor
from .checkpoint_parity_inputs import ParityInput


class ObservationError(ValueError):
    """A forward/backward observation failed a declared invariant."""


@dataclass(frozen=True)
class Observation:
    fixture: ParityInput
    checkpoint: bool
    state: str
    source_device: str
    source_dtype: str
    loss: torch.Tensor
    logits: torch.Tensor
    candidate_score: float
    gradients: tuple[tuple[str, torch.Tensor], ...]
    base_digest: str
    factor_digest: str


@dataclass(frozen=True)
class PendingObservation:
    """Each forward carries the SAME summed-backward gradients, not individual ones."""

    summed_loss: torch.Tensor
    forwards: tuple[Observation, Observation]


def _fixture(fixture, vocab):
    if (
        type(fixture) is not ParityInput
        or type(vocab) is not int
        or not 1 <= vocab <= 49152
    ):
        raise ObservationError("typed fixture and bounded vocabulary required")
    fields = (
        fixture.input_ids,
        fixture.labels,
        fixture.attention_mask,
        fixture.position_ids,
    )
    if any(type(field) is not tuple for field in fields):
        raise ObservationError("immutable input tuples required")
    size = len(fixture.input_ids)
    if not 3 <= size <= 71 or any(len(field) != size for field in fields):
        raise ObservationError("bounded matching input arrays required")
    if any(type(value) is not int for field in fields for value in field):
        raise ObservationError("exact integer input arrays required")
    candidate = fixture.candidate_ids
    prompt = fixture.prompt_length
    if (
        type(candidate) is not tuple
        or not candidate
        or type(prompt) is not int
        or prompt < 1
        or any(type(value) is not int for value in candidate)
    ):
        raise ObservationError("complete candidate and prompt required")
    end = prompt + len(candidate)
    padding = size - end
    if (
        padding not in (0, 7)
        or fixture.input_ids[prompt:end] != candidate
        or fixture.labels != (-100,) * prompt + candidate + (-100,) * padding
        or fixture.attention_mask != (1,) * end + (0,) * padding
        or fixture.position_ids != tuple(range(size))
        or any(not 0 <= value < vocab for value in fixture.input_ids)
    ):
        raise ObservationError("candidate supervision/mask/positions differ")


def _bindings(wrapper, state):
    if not isinstance(wrapper, nn.Module) or not wrapper.training:
        raise ObservationError("training cooperating wrapper required")
    base, factors = wrapper.base, wrapper._checkpoint_factors()
    base_parameters = tuple(base.parameters())
    named = tuple(
        sorted(
            factors.named_parameters(remove_duplicate=False),
            key=lambda item: item[0].encode("utf-8"),
        )
    )
    if (
        not base_parameters
        or not named
        or any(module.training for module in base.modules())
        or not factors.training
        or any(p.requires_grad or p.grad is not None for p in base_parameters)
    ):
        raise ObservationError("frozen eval base and training factors required")
    device = base_parameters[0].device
    if device.type not in ("cpu", "cuda"):
        raise ObservationError("materialized CPU/CUDA required")
    base_ids = {id(p) for p in base_parameters}
    factor_ids = {id(p) for _, p in named}
    if (
        len(factor_ids) != len(named)
        or base_ids & factor_ids
        or {id(p) for p in wrapper.parameters()} != base_ids | factor_ids
        or any(p.device != device for p in base_parameters)
    ):
        raise ObservationError("complete distinct parameter roster required")
    roles = {name.rsplit(".", 1)[-1] for name, _ in named}
    if roles != {"A", "B"}:
        raise ObservationError("complete A/B factors required")
    base_storages = {p.untyped_storage().data_ptr() for p in base_parameters}
    factor_storages = set()
    for name, parameter in named:
        storage = parameter.untyped_storage().data_ptr()
        if (
            parameter.device != device
            or parameter.dtype != torch.float32
            or not parameter.requires_grad
            or not torch.isfinite(parameter).all().item()
            or storage in base_storages
            or storage in factor_storages
        ):
            raise ObservationError("finite trainable distinct FP32 factors required")
        factor_storages.add(storage)
        if name.rsplit(".", 1)[-1] == "B":
            zero = not torch.count_nonzero(parameter).item()
            if zero != (state == "zero"):
                raise ObservationError("factor state differs before forward")
    return base, factors, named, device


def _base_digest(base):
    return _digest(
        tuple(("parameter/" + name, value) for name, value in base.named_parameters())
        + tuple(("buffer/" + name, value) for name, value in base.named_buffers())
    )


def _roster_stamp(named):
    return tuple((name, _tensor_stamp(value)) for name, value in named)


def observe_forward_backward(wrapper, fixture, *, checkpoint, state):
    forwards, _ = _observe_group(
        wrapper, (fixture,), checkpoint=checkpoint, state=state
    )
    return forwards[0]


def _observe_group(wrapper, fixtures, *, checkpoint, state):
    if (
        type(checkpoint) is not bool
        or type(state) is not str
        or state not in ("zero", "nonzero")
    ):
        raise ObservationError(
            "explicit checkpoint bool and fixed factor state required"
        )
    base, factors, named, device = _bindings(wrapper, state)
    base_roster = _roster_stamp(base.named_parameters())
    buffer_roster = _roster_stamp(base.named_buffers())
    factor_roster = _roster_stamp(named)
    for fixture in fixtures:
        _fixture(fixture, base.config.vocab_size)
    before_base, before_factor = _base_digest(base), _digest(named)
    arguments_group = tuple(
        {
            name: torch.tensor(
                [getattr(fixture, name)], dtype=torch.int64, device=device
            )
            for name in ("input_ids", "labels", "attention_mask", "position_ids")
        }
        for fixture in fixtures
    )
    inputs_before = tuple(
        {name: value.clone() for name, value in arguments.items()}
        for arguments in arguments_group
    )
    input_stamps = tuple(
        _roster_stamp(arguments.items()) for arguments in arguments_group
    )
    for _, parameter in named:
        parameter.grad = None
    try:
        if checkpoint:
            with wrapper.checkpoint_session() as session:
                results = tuple(
                    wrapper(**arguments, use_cache=False, checkpoint_session=session)
                    for arguments in arguments_group
                )
                loss = _summed_loss(results)
                session.backward(loss)
        else:
            results = tuple(
                wrapper(**arguments, use_cache=False) for arguments in arguments_group
            )
            loss = _summed_loss(results)
            loss.backward()
        live_base, live_factors, live_named, live_device = _bindings(wrapper, state)
        if (
            live_base is not base
            or live_factors is not factors
            or live_device != device
            or _roster_stamp(live_named) != factor_roster
            or _roster_stamp(base.named_parameters()) != base_roster
            or _roster_stamp(base.named_buffers()) != buffer_roster
            or tuple(_roster_stamp(arguments.items()) for arguments in arguments_group)
            != input_stamps
        ):
            raise ObservationError("live bindings changed during observation")
        if (
            before_base != _base_digest(base)
            or before_factor != _digest(named)
            or any(p.grad is not None or p.requires_grad for p in base.parameters())
        ):
            raise ObservationError("output/input/frozen-state invariant failed")
        for fixture, result, arguments, original in zip(
            fixtures, results, arguments_group, inputs_before, strict=True
        ):
            if (
                not isinstance(result.logits, torch.Tensor)
                or result.logits.shape
                != (1, len(fixture.input_ids), base.config.vocab_size)
                or not torch.isfinite(result.logits).all().item()
                or any(
                    not torch.equal(value, original[name])
                    for name, value in arguments.items()
                )
            ):
                raise ObservationError("output/input invariant failed")
        gradients = []
        for name, parameter in named:
            gradient = parameter.grad
            if (
                gradient is None
                or gradient.shape != parameter.shape
                or gradient.dtype != torch.float32
                or not torch.isfinite(gradient).all().item()
            ):
                raise ObservationError("complete finite factor gradients required")
            should_zero = state == "zero" and name.rsplit(".", 1)[-1] == "A"
            if (not torch.count_nonzero(gradient).item()) != should_zero:
                raise ObservationError(
                    "individual factor gradient zero/nonzero rule failed"
                )
            gradients.append((name, gradient.detach().cpu().clone()))
        forwards = tuple(
            Observation(
                fixture,
                checkpoint,
                state,
                str(device),
                str(next(base.parameters()).dtype),
                result.loss.detach().cpu().clone(),
                result.logits.detach().cpu().clone(),
                score_banking_candidate(
                    result.logits[
                        0, : fixture.prompt_length + len(fixture.candidate_ids)
                    ],
                    fixture.prompt_length,
                    fixture.candidate_ids,
                ),
                tuple((name, value.clone()) for name, value in gradients),
                before_base,
                before_factor,
            )
            for fixture, result in zip(fixtures, results, strict=True)
        )
        return forwards, loss.detach().cpu().clone()
    except BaseException:
        for _, parameter in named:
            parameter.grad = None
        raise


def _summed_loss(results):
    for result in results:
        if (
            not isinstance(result.loss, torch.Tensor)
            or result.loss.ndim != 0
            or not result.loss.requires_grad
            or not torch.isfinite(result.loss).item()
        ):
            raise ObservationError("finite differentiable scalar losses required")
    loss = results[0].loss
    for result in results[1:]:
        loss = loss + result.loss
    if not torch.isfinite(loss).item():
        raise ObservationError("finite summed loss required")
    return loss


def observe_pending_pair(wrapper, fixtures, *, checkpoint):
    """Section-D length32 nonzero-state pair, both graphs BEFORE one backward.

    Same ownership, provenance and failure discard/rebuild limits as single mode.
    No optimizer, accumulation, full matrix or launch authority is supplied.
    """
    if type(fixtures) is not tuple or len(fixtures) != 2:
        raise ObservationError("exactly two immutable fixtures required")
    base, _, _, _ = _bindings(wrapper, "nonzero")
    for fixture in fixtures:
        _fixture(fixture, base.config.vocab_size)
    left, right = fixtures
    if (
        max(len(left.input_ids), len(right.input_ids)) != 32
        or any(0 in fixture.attention_mask for fixture in fixtures)
        or left.prompt_length != right.prompt_length
        or left.input_ids[: left.prompt_length]
        != right.input_ids[: right.prompt_length]
        or left.candidate_ids == right.candidate_ids
    ):
        raise ObservationError(
            "distinct complete candidates with common length32 prompt required"
        )
    forwards, summed_loss = _observe_group(
        wrapper, fixtures, checkpoint=checkpoint, state="nonzero"
    )
    return PendingObservation(summed_loss, forwards)


def compare_pending_observations(reference, actual, *, exact):
    if (
        type(reference) is not PendingObservation
        or type(actual) is not PendingObservation
        or type(reference.forwards) is not tuple
        or type(actual.forwards) is not tuple
        or len(reference.forwards) != 2
        or len(actual.forwards) != 2
    ):
        raise ObservationError("matched two-forward observations required")
    compare_tensor(reference.summed_loss, actual.summed_loss, exact=exact)
    for left, right in zip(reference.forwards, actual.forwards, strict=True):
        compare_observations(left, right, exact=exact)


def _gradient_mapping(gradients):
    if type(gradients) is not tuple or not gradients:
        raise ObservationError("nonempty immutable gradient roster required")
    mapping = {}
    for item in gradients:
        if (
            type(item) is not tuple
            or len(item) != 2
            or type(item[0]) is not str
            or not item[0]
            or item[0] in mapping
            or not isinstance(item[1], torch.Tensor)
        ):
            raise ObservationError("unique named tensor gradients required")
        mapping[item[0]] = item[1]
    return mapping


def compare_observations(reference, actual, *, exact):
    if (
        type(reference) is not Observation
        or type(actual) is not Observation
        or reference.checkpoint is not False
        or actual.checkpoint is not True
        or any(
            getattr(reference, field) != getattr(actual, field)
            for field in (
                "fixture",
                "state",
                "source_device",
                "source_dtype",
                "base_digest",
                "factor_digest",
            )
        )
    ):
        raise ObservationError("matched off/on observation metadata required")
    compare_tensor(reference.loss, actual.loss, exact=exact)
    compare_tensor(reference.logits, actual.logits, exact=exact)
    compare_tensor(
        torch.tensor(reference.candidate_score, dtype=torch.float64),
        torch.tensor(actual.candidate_score, dtype=torch.float64),
        exact=exact,
    )
    compare_named_tensors(
        _gradient_mapping(reference.gradients),
        _gradient_mapping(actual.gradients),
        exact=exact,
    )
