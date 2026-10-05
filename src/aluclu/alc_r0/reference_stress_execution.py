"""Trusted E3 two-update mechanics; not an authenticated/admitted launcher.

Exclusive cooperating caller ownership is mandatory. Actual host/tokenizer,
runtime, resource history, timing/peaks and invocation must be admitted outside
this function. CPU fake/mocked tests do not qualify E3 or learning. No retry,
resume, rollback, GPU-to-CPU execution fallback or artifact IO is provided.
On any Python failure discard the mutated wrapper/optimizer. Process kills must
be recorded by the outer owned launcher; no in-process receipt survives a kill.
"""

from dataclasses import dataclass, replace

import torch

from .checkpoint_execution import _digest, _tensor_stamp
from .checkpoint_observation import _base_digest, _roster_stamp
from .checkpoint_optimizer import _group, _snapshot
from .reference_qv_artifact import make_reference_optimizer, reference_bindings
from .reference_stress_start import _inventory, inspect_reference_stress_start


@dataclass(frozen=True)
class StressProgress:
    stage: str = "preflight"
    attempted_updates: int = 0
    completed_updates: int = 0
    attempted_microbatches: int = 0
    completed_microbatches: int = 0
    attempted_steps: int = 0
    returned_steps: int = 0


class StressExecutionError(RuntimeError):
    """Terminal Python failure with partial counts; state is NOT rolled back."""

    def __init__(self, progress):
        self.progress = progress
        super().__init__(f"stress execution failed at {progress.stage}; discard state")


@dataclass(frozen=True)
class StressUpdate:
    step: int
    averaged_loss: float
    preclip_norm: float
    factor_digest: str
    moment_digest: str


@dataclass(frozen=True)
class StressExecution:
    start: object
    progress: StressProgress
    updates: tuple[StressUpdate, ...]


def _identity(factors):
    # Versions change on the two permitted optimizer steps; all other metadata
    # and bindings must remain identical. Within each update bytes are guarded.
    return tuple(
        (name, _tensor_stamp(p)[:1] + _tensor_stamp(p)[2:])
        for name, p in factors.items()
    )


def _topology(wrapper):
    return tuple(
        (name, id(module), type(module), module.training)
        for name, module in wrapper.named_modules(remove_duplicate=False)
    )


def _guard(wrapper, base, identities, base_stamps, buffer_stamps, topology):
    live, live_base = reference_bindings(wrapper)
    _inventory(wrapper)
    if (
        _identity(live) != identities
        or _topology(wrapper) != topology
        or tuple(map(id, live_base)) != tuple(map(id, base))
        or _roster_stamp(wrapper.base.named_parameters()) != base_stamps
        or _roster_stamp(wrapper.base.named_buffers()) != buffer_stamps
        or any(module.training for module in wrapper.base.modules())
        or not wrapper.training
        or not wrapper.reference.training
        or any(p.grad is not None or p.requires_grad for p in base)
    ):
        raise ValueError("live base/factor bindings or modes changed")
    wrapper._assert_checkpoint_mutation_allowed()


def _gradients(factors, frozen, optimizer):
    protected = {
        (p.device, p.untyped_storage().data_ptr()) for p in (*factors.values(), *frozen)
    }
    protected.update(
        (value.device, value.untyped_storage().data_ptr())
        for state in optimizer.state.values()
        for value in state.values()
        if isinstance(value, torch.Tensor)
    )
    used = set()
    for parameter in factors.values():
        gradient = parameter.grad
        if (
            not isinstance(gradient, torch.Tensor)
            or gradient.layout != torch.strided
            or gradient.shape != parameter.shape
            or gradient.dtype != torch.float32
            or gradient.device != parameter.device
            or gradient.requires_grad
            or not torch.isfinite(gradient).all().item()
        ):
            raise ValueError("every factor requires a present finite FP32 gradient")
        storage = (gradient.device, gradient.untyped_storage().data_ptr())
        if storage in protected or storage in used:
            raise ValueError("gradient storage aliases factors/base/state/gradient")
        used.add(storage)
        # Initial zero-B legitimately yields zero A gradients: no nonzero rule.


def _output(result, size, vocab, device):
    loss, logits = result.loss, result.logits
    if (
        not isinstance(loss, torch.Tensor)
        or loss.ndim != 0
        or loss.device != device
        or not loss.requires_grad
        or not torch.isfinite(loss).item()
        or not isinstance(logits, torch.Tensor)
        or logits.layout != torch.strided
        or not logits.is_floating_point()
        or logits.device != device
        or logits.shape != (1, size, vocab)
    ):
        raise ValueError(
            "finite differentiable scalar loss and complete logits required"
        )
    # Bound temporary boolean allocation, never flatten/copy expanded logits.
    for offset in range(0, size, 32):
        if not torch.isfinite(logits[:, offset : offset + 32]).all().item():
            raise ValueError("nonfinite logits")


def _microbatch(wrapper, item, device):
    arguments = {
        name: torch.tensor([getattr(item, name)], dtype=torch.int64, device=device)
        for name in ("input_ids", "labels", "attention_mask", "position_ids")
    }
    original = {name: value.clone() for name, value in arguments.items()}
    stamps = _roster_stamp(arguments.items())
    with wrapper.checkpoint_session() as session:
        result = wrapper(**arguments, use_cache=False, checkpoint_session=session)
        _output(result, len(item.input_ids), wrapper.base.config.vocab_size, device)
        scaled = result.loss / 16
        session.backward(scaled)
        if session.pending_count != 0:
            raise ValueError("microbatch backward left pending graphs")
    if _roster_stamp(arguments.items()) != stamps or any(
        not torch.equal(value, original[name]) for name, value in arguments.items()
    ):
        raise ValueError("microbatch inputs changed")
    return float(scaled.detach().item())


def execute_reference_stress(wrapper, schedule) -> StressExecution:
    """Run exactly two16-microbatch updates with ONE retained fixed AdamW.

    Successful counts report mechanics only. Outer verification/admission and
    actual CUDA receipt remain mandatory; this cannot declare resource/E3 PASS.
    Attempts start before execution; completions follow successful verification.
    A step which mutates then raises has attempted_steps>returned_steps, not a
    rollback. Exceptions (including interruption) carry the last exact stage.
    """
    progress, updates = StressProgress(), []
    try:
        start = inspect_reference_stress_start(wrapper, schedule)
        factors, base = reference_bindings(wrapper)
        identities = _identity(factors)
        base_stamps = _roster_stamp(wrapper.base.named_parameters())
        buffer_stamps = _roster_stamp(wrapper.base.named_buffers())
        topology = _topology(wrapper)
        device = base[0].device

        def guard():
            _guard(wrapper, base, identities, base_stamps, buffer_stamps, topology)

        progress = replace(progress, stage="optimizer_create")
        optimizer = make_reference_optimizer(wrapper)
        if optimizer.state:
            raise ValueError("fresh optimizer must have no populated state")
        for step in (1, 2):
            progress = replace(progress, stage="update_start", attempted_updates=step)
            guard()
            _group(optimizer)
            optimizer.zero_grad(set_to_none=True)
            before = _digest(tuple(factors.items()))
            averaged_loss = 0.0
            for item in schedule.inputs:
                progress = replace(
                    progress,
                    stage="microbatch",
                    attempted_microbatches=progress.attempted_microbatches + 1,
                )
                averaged_loss += _microbatch(wrapper, item, device)
                guard()
                _gradients(factors, (*base, *wrapper.base.buffers()), optimizer)
                progress = replace(
                    progress, completed_microbatches=progress.completed_microbatches + 1
                )
            progress = replace(progress, stage="preclip")
            if (
                _base_digest(wrapper.base) != start.base_digest
                or _digest(tuple(factors.items())) != before
            ):
                raise ValueError("base/factor bytes changed outside optimizer step")
            guard()
            norm = torch.nn.utils.clip_grad_norm_(
                list(factors.values()), 1.0, error_if_nonfinite=True, foreach=False
            )
            _gradients(factors, (*base, *wrapper.base.buffers()), optimizer)
            guard()
            if (
                _base_digest(wrapper.base) != start.base_digest
                or _digest(tuple(factors.items())) != before
            ):
                raise ValueError("clipping mutated factor/base bytes")
            progress = replace(
                progress,
                stage="optimizer_step",
                attempted_steps=progress.attempted_steps + 1,
            )
            optimizer.step()
            progress = replace(
                progress,
                stage="optimizer_state",
                returned_steps=progress.returned_steps + 1,
            )
            guard()
            state = _snapshot(optimizer, factors, base, step)
            buffers = {
                (b.device, b.untyped_storage().data_ptr())
                for b in wrapper.base.buffers()
            }
            if (
                state.owned_storages & buffers
                or _base_digest(wrapper.base) != start.base_digest
            ):
                raise ValueError("optimizer aliases/mutates frozen base buffers")
            updates.append(
                StressUpdate(
                    step,
                    averaged_loss,
                    float(norm.item()),
                    _digest(tuple(state.factors.items())),
                    _digest(
                        tuple(("avg/" + n, p) for n, p in state.exp_avg.items())
                        + tuple(("sq/" + n, p) for n, p in state.exp_avg_sq.items())
                    ),
                )
            )
            del state
            progress = replace(progress, completed_updates=step)
        progress = replace(progress, stage="finalize")
        optimizer.zero_grad(set_to_none=True)
        guard()
        return StressExecution(
            start, replace(progress, stage="complete"), tuple(updates)
        )
    except BaseException as exc:
        raise StressExecutionError(progress) from exc
