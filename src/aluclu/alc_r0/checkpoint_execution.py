"""Explicit scoped non-reentrant execution; no model/update authority.

The owner must keep ONE controller and supply complete live module getters.
Wrapper-specific cache/input/port checks are separate integration obligations.
This is a cooperating-process contract, not protection from a compromised host.
"""

from __future__ import annotations

import hashlib
import threading
from collections.abc import Callable, Mapping
from types import MappingProxyType

import torch
from torch import nn
from torch.utils.checkpoint import checkpoint

from .checkpoint_fidelity import _canonical_keys


class CheckpointExecutionError(ValueError):
    """A lease, binding, replay or backward violates the explicit contract."""


def _tensor_stamp(value: torch.Tensor):
    if value.layout != torch.strided or value.device.type not in {"cpu", "cuda"}:
        raise CheckpointExecutionError("materialized CPU/CUDA dense tensors required")
    return (
        id(value),
        value._version,
        value.shape,
        value.dtype,
        value.device,
        value.requires_grad,
        value.untyped_storage().data_ptr(),
        value.stride(),
        value.storage_offset(),
    )


def _digest(parameters) -> str:
    digest = hashlib.sha256()
    for name, parameter in parameters:
        digest.update(name.encode("utf-8"))
        raw = parameter.detach().contiguous().reshape(-1).view(torch.uint8)
        for offset in range(0, raw.numel(), 2 * 1024 * 1024):
            digest.update(
                raw[offset : offset + 2 * 1024 * 1024].cpu().numpy().tobytes()
            )
    return digest.hexdigest()


class CheckpointController:
    """Owner-local lease. Mutators must call assert_mutation_allowed first."""

    def __init__(
        self,
        owner: nn.Module,
        *,
        base_getter: Callable[[], nn.Module],
        factor_getter: Callable[[], nn.Module],
        layer_count: int,
        state_fingerprint_getter: Callable[[], str] | None = None,
    ) -> None:
        if (
            not isinstance(owner, nn.Module)
            or not callable(base_getter)
            or not callable(factor_getter)
            or type(layer_count) is not int
            or not 1 <= layer_count <= 30
            or (
                state_fingerprint_getter is not None
                and not callable(state_fingerprint_getter)
            )
        ):
            raise CheckpointExecutionError("invalid owner/getters/layer count")
        self.owner = owner
        self.base_getter = base_getter
        self.factor_getter = factor_getter
        self.layer_count = layer_count
        self.state_fingerprint_getter = state_fingerprint_getter
        self._lock = threading.Lock()
        self._active: CheckpointSession | None = None

    def session(self) -> CheckpointSession:
        return CheckpointSession(self)

    def assert_mutation_allowed(self) -> None:
        with self._lock:
            if self._active is not None:
                raise CheckpointExecutionError("owner mutation denied during lease")


class CheckpointSession:
    """One-shot context; only session.backward may traverse ticket graphs."""

    def __init__(self, controller: CheckpointController) -> None:
        self._controller = controller
        self._status = "created"
        self._thread = None
        self._pending: set[_ForwardTicket] = set()
        self._backward_active = False
        self._visited: set[_ForwardTicket] = set()
        self._blocks: dict[_ForwardTicket, set[int]] = {}

    @property
    def pending_count(self) -> int:
        return len(self._pending)

    def __enter__(self) -> CheckpointSession:
        controller = self._controller
        with controller._lock:
            if self._status != "created" or controller._active is not None:
                raise CheckpointExecutionError("session reuse/nesting denied")
            self._thread = threading.current_thread()
            try:
                self._capture()
            except BaseException:
                self._status = "invalid"
                raise
            self._status = "active"
            controller._active = self
        return self

    def _capture(self) -> None:
        controller = self._controller
        if (
            type(controller.layer_count) is not int
            or not 1 <= controller.layer_count <= 30
        ):
            raise CheckpointExecutionError("invalid declared layer count")
        self._layer_count = controller.layer_count
        base, factors = controller.base_getter(), controller.factor_getter()
        if (
            not isinstance(base, nn.Module)
            or not isinstance(factors, nn.Module)
            or not controller.owner.training
            or not factors.training
            or any(module.training for module in base.modules())
        ):
            raise CheckpointExecutionError(
                "training owner/factors and eval base required"
            )
        self._base, self._factors = base, factors
        self._base_parameters = tuple(base.parameters())
        self._factor_parameters = tuple(factors.parameters())
        if not self._base_parameters or not self._factor_parameters:
            raise CheckpointExecutionError(
                "nonempty complete base/factor bindings required"
            )
        if any(
            p.requires_grad or p.dtype not in {torch.float32, torch.bfloat16}
            for p in self._base_parameters
        ):
            raise CheckpointExecutionError("base must remain frozen FP32/BF16")
        if any(
            not p.requires_grad or p.dtype != torch.float32
            for p in self._factor_parameters
        ):
            raise CheckpointExecutionError("factors must be trainable FP32")
        self._parameters = tuple(controller.owner.named_parameters())
        base_ids = {id(p) for p in self._base_parameters}
        factor_ids = {id(p) for p in self._factor_parameters}
        if (
            base_ids & factor_ids
            or {id(p) for _, p in self._parameters} != base_ids | factor_ids
        ):
            raise CheckpointExecutionError(
                "owner roster must equal disjoint base plus factors"
            )
        if len({p.device for _, p in self._parameters}) != 1:
            raise CheckpointExecutionError("one base/factor device required")
        self._stamps = tuple(_tensor_stamp(p) for _, p in self._parameters)
        self._buffers = tuple(controller.owner.named_buffers())
        _canonical_keys(dict(self._buffers))
        if any(value.requires_grad for _, value in self._buffers):
            raise CheckpointExecutionError("registered buffers must not be trainable")
        self._buffer_stamps = tuple(_tensor_stamp(value) for _, value in self._buffers)
        base_storage = {
            (value.device, value.untyped_storage().data_ptr())
            for value in (*self._base_parameters, *base.buffers())
        }
        factor_storage = [
            (p.device, p.untyped_storage().data_ptr()) for p in self._factor_parameters
        ]
        if len(set(factor_storage)) != len(factor_storage) or base_storage & set(
            factor_storage
        ):
            raise CheckpointExecutionError("factor/base storage alias denied")
        self._modules = tuple(
            (name, id(module), module.training)
            for name, module in controller.owner.named_modules()
        )
        self._fingerprint = self._state_digest()
        self._state_getter = controller.state_fingerprint_getter
        self._extra_fingerprint = self._read_extra_fingerprint()

    def _read_extra_fingerprint(self):
        if self._state_getter is None:
            return None
        value = self._state_getter()
        if (
            type(value) is not str
            or len(value) != 64
            or any(c not in "0123456789abcdef" for c in value)
        ):
            raise CheckpointExecutionError(
                "canonical SHA256 state fingerprint required"
            )
        return value

    def _state_digest(self) -> str:
        return _digest(
            tuple((f"parameter/{name}", value) for name, value in self._parameters)
            + tuple((f"buffer/{name}", value) for name, value in self._buffers)
        )

    def _require_owner(self, owner=None) -> None:
        if self._thread is not threading.current_thread():
            raise CheckpointExecutionError("session belongs to another thread")
        if owner is not None and owner is not self._controller.owner:
            raise CheckpointExecutionError("session belongs to another wrapper")
        if self._status != "active" or self._controller._active is not self:
            raise CheckpointExecutionError("session is not active")

    def _guard(self) -> None:
        self._require_owner()
        controller = self._controller
        if (
            controller.state_fingerprint_getter is not self._state_getter
            or self._read_extra_fingerprint() != self._extra_fingerprint
        ):
            raise CheckpointExecutionError("computational state fingerprint drifted")
        parameters = tuple(controller.owner.named_parameters())
        buffers = tuple(controller.owner.named_buffers())
        modules = tuple(
            (name, id(module), module.training)
            for name, module in controller.owner.named_modules()
        )
        if (
            type(controller.layer_count) is not int
            or controller.layer_count != self._layer_count
            or controller.base_getter() is not self._base
            or controller.factor_getter() is not self._factors
            or tuple((name, id(p)) for name, p in parameters)
            != tuple((name, id(p)) for name, p in self._parameters)
            or modules != self._modules
            or tuple(_tensor_stamp(p) for _, p in parameters) != self._stamps
            or tuple((name, id(value)) for name, value in buffers)
            != tuple((name, id(value)) for name, value in self._buffers)
            or tuple(_tensor_stamp(value) for _, value in buffers)
            != self._buffer_stamps
        ):
            raise CheckpointExecutionError("bound module/parameter state drifted")

    def _abort(self) -> None:
        if self._status != "active":
            return
        self._status = "invalid"
        self._backward_active = False
        self._pending.clear()
        for parameter in self._factor_parameters:
            parameter.grad = None
        with self._controller._lock:
            if self._controller._active is self:
                self._controller._active = None

    def __exit__(self, exc_type, exc, traceback) -> bool:
        if self._thread is not threading.current_thread():
            raise CheckpointExecutionError("foreign thread cannot close a lease")
        if exc_type is not None:
            self._abort()
            return False
        try:
            self._guard()
            if self._pending:
                raise CheckpointExecutionError("unconsumed forward graphs remain")
            if self._state_digest() != self._fingerprint:
                raise CheckpointExecutionError(
                    "parameter/buffer bytes changed during lease"
                )
        except BaseException:
            self._abort()
            raise
        self._status = "closed"
        with self._controller._lock:
            self._controller._active = None
        return False

    def begin_forward(
        self, owner: nn.Module, metadata: Mapping[str, torch.Tensor | None]
    ):
        self._require_owner(owner)
        try:
            self._guard()
            if self._backward_active or len(self._pending) >= 32:
                raise CheckpointExecutionError("backward/32-graph limit denies forward")
            ticket = _ForwardTicket(self, metadata)
            self._pending.add(ticket)
            return ticket
        except BaseException:
            self._abort()
            raise

    def backward(self, loss: torch.Tensor, *, retain_graph: bool = False) -> None:
        self._require_owner()
        try:
            self._guard()
            if (
                retain_graph is not False
                or self._backward_active
                or not isinstance(loss, torch.Tensor)
                or loss.ndim != 0
                or not loss.is_floating_point()
                or not loss.requires_grad
                or not torch.isfinite(loss.detach()).item()
            ):
                raise CheckpointExecutionError(
                    "finite scalar loss/nonretained backward required"
                )
            self._visited.clear()
            self._blocks.clear()
            self._backward_active = True
            loss.backward(retain_graph=False)
            self._guard()
            if (
                not self._visited
                or any(
                    self._blocks.get(ticket, set()) != ticket._gradient_blocks
                    for ticket in self._visited
                )
                or set(self._blocks) - self._visited
            ):
                raise CheckpointExecutionError(
                    "complete owned graph traversal required"
                )
            for ticket in self._visited:
                ticket._consumed = True
                self._pending.remove(ticket)
        except BaseException:
            self._abort()
            raise
        finally:
            self._backward_active = False


class _ForwardTicket:
    def __init__(self, session: CheckpointSession, metadata) -> None:
        if not isinstance(metadata, Mapping) or not metadata:
            raise CheckpointExecutionError("nonempty named metadata mapping required")
        private = {}
        for name in _canonical_keys(metadata):
            value = metadata[name]
            if value is not None:
                if not isinstance(value, torch.Tensor) or value.requires_grad:
                    raise CheckpointExecutionError(
                        "detached tensor/None metadata required"
                    )
                _tensor_stamp(value)
                value = value.detach().clone()
            private[name] = value
        self._metadata = MappingProxyType(private)
        self._metadata_stamps = tuple(
            (name, _tensor_stamp(value))
            for name, value in private.items()
            if value is not None
        )
        self._session = session
        self._next_layer = 0
        self._sealed = False
        self._consumed = False
        self._gradient_blocks: set[int] = set()

    def _guard(self) -> None:
        self._session._guard()
        if self._consumed or self not in self._session._pending:
            raise CheckpointExecutionError("ticket already consumed/invalidated")
        stamps = tuple(
            (name, _tensor_stamp(value))
            for name, value in self._metadata.items()
            if value is not None
        )
        if stamps != self._metadata_stamps:
            raise CheckpointExecutionError("private replay metadata drifted")

    def _hook(self, gradient, index=None):
        # A foreign thread/retired graph must not abort an owner's live lease.
        self._session._require_owner()
        try:
            self._guard()
            if not self._sealed or not self._session._backward_active:
                raise CheckpointExecutionError(
                    "backward outside owned completion denied"
                )
            if index is None:
                if self in self._session._visited:
                    raise CheckpointExecutionError("duplicate output traversal")
                self._session._visited.add(self)
            else:
                self._session._blocks.setdefault(self, set()).add(index)
            return gradient
        except BaseException:
            self._session._abort()
            raise

    def run(self, index: int, block: Callable, hidden: torch.Tensor) -> torch.Tensor:
        self._session._require_owner()
        try:
            self._guard()
            if (
                type(index) is not int
                or index != self._next_layer
                or self._sealed
                or index >= self._session._layer_count
                or not callable(block)
                or self._session._backward_active
            ):
                raise CheckpointExecutionError("ordered bound block execution required")
            entered = False

            def bound(value):
                nonlocal entered
                self._guard()
                if entered and not self._session._backward_active:
                    raise CheckpointExecutionError(
                        "replay outside owned backward denied"
                    )
                entered = True
                result = block(value, self._metadata)
                self._guard()
                return result

            result = checkpoint(
                bound, hidden, use_reentrant=False, preserve_rng_state=True
            )
            if not isinstance(result, torch.Tensor):
                raise CheckpointExecutionError("block must return a single tensor")
            if result.requires_grad:
                self._gradient_blocks.add(index)
                result.register_hook(lambda gradient: self._hook(gradient, index))
            self._next_layer += 1
            return result
        except BaseException:
            self._session._abort()
            raise

    def bind_output(self, logits: torch.Tensor) -> None:
        self._session._require_owner()
        try:
            self._guard()
            if (
                self._sealed
                or self._next_layer != self._session._layer_count
                or not self._gradient_blocks
                or not isinstance(logits, torch.Tensor)
                or not logits.requires_grad
                or not logits.is_floating_point()
            ):
                raise CheckpointExecutionError(
                    "complete forward/differentiable logits required"
                )
            self._sealed = True
            logits.register_hook(self._hook)
        except BaseException:
            self._session._abort()
            raise
