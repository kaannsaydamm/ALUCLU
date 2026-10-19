"""Read-only, model-free AdamW fidelity for the pinned prospective runner.

The runner supplies COMPLETE factor/base bindings and the expected step. This
cannot discover omitted model parameters or prove that an optimizer ran. Calls
must be quiescent: no concurrent mutation, optimizer step or model execution.
No update/training authority is conferred by a successful synthetic comparison.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass

import torch

from .checkpoint_fidelity import (
    CheckpointFidelityError,
    TensorComparison,
    _canonical_keys,
    compare_named_tensors,
    compare_tensor,
)

_NUMERIC = {"lr": 3e-4, "eps": 1e-8, "weight_decay": 0}
_BOOLEAN = {
    "amsgrad": False,
    "maximize": False,
    "foreach": False,
    "capturable": False,
    "differentiable": False,
    "fused": False,
    "decoupled_weight_decay": True,
}
_GROUP_KEYS = frozenset({"params", "betas", *_NUMERIC, *_BOOLEAN})
_STATE_KEYS = frozenset({"step", "exp_avg", "exp_avg_sq"})


@dataclass(frozen=True)
class AdamWComparison:
    step: int
    factors: tuple[tuple[str, TensorComparison], ...]
    exp_avg: tuple[tuple[str, TensorComparison], ...]
    exp_avg_sq: tuple[tuple[str, TensorComparison], ...]


@dataclass
class _Snapshot:
    factors: dict[str, torch.Tensor]
    exp_avg: dict[str, torch.Tensor]
    exp_avg_sq: dict[str, torch.Tensor]
    owned_storages: set[tuple[torch.device, int]]
    base_storages: set[tuple[torch.device, int]]


def _storage(value: torch.Tensor) -> tuple[torch.device, int]:
    if value.layout != torch.strided or value.device.type not in {"cpu", "cuda"}:
        raise CheckpointFidelityError("only materialized CPU/CUDA dense storage")
    return value.device, value.untyped_storage().data_ptr()


def _group(optimizer: torch.optim.AdamW) -> Sequence[torch.nn.Parameter]:
    if type(optimizer) is not torch.optim.AdamW or len(optimizer.param_groups) != 1:
        raise CheckpointFidelityError("exact AdamW with one fixed group required")
    group = optimizer.param_groups[0]
    if not isinstance(group, Mapping) or set(group) != _GROUP_KEYS:
        raise CheckpointFidelityError("optimizer group key set differs")
    for key, expected in _NUMERIC.items():
        if type(group[key]) not in {int, float} or group[key] != expected:
            raise CheckpointFidelityError(f"fixed optimizer hyperparameter: {key}")
    for key, expected in _BOOLEAN.items():
        if type(group[key]) is not bool or group[key] is not expected:
            raise CheckpointFidelityError(f"fixed optimizer flag: {key}")
    betas = group["betas"]
    if (
        type(betas) is not tuple
        or len(betas) != 2
        or any(type(value) is not float for value in betas)
        or betas != (0.9, 0.999)
    ):
        raise CheckpointFidelityError("fixed optimizer betas required")
    parameters = group["params"]
    if not isinstance(parameters, (list, tuple)):
        raise CheckpointFidelityError("optimizer parameters require a sequence")
    return parameters


def _bindings(factors, base_parameters):
    if not isinstance(factors, Mapping) or not factors:
        raise CheckpointFidelityError("complete nonempty factor mapping required")
    names = _canonical_keys(factors)
    if not isinstance(base_parameters, (list, tuple)) or not base_parameters:
        raise CheckpointFidelityError("complete nonempty frozen-base sequence required")
    base_ids: set[int] = set()
    base_storage: set[tuple[torch.device, int]] = set()
    for parameter in base_parameters:
        if (
            not isinstance(parameter, torch.nn.Parameter)
            or parameter.requires_grad
            or not parameter.is_leaf
            or parameter.numel() == 0
            or id(parameter) in base_ids
        ):
            raise CheckpointFidelityError("invalid or duplicate frozen-base binding")
        base_ids.add(id(parameter))
        base_storage.add(_storage(parameter))
    ids: set[int] = set()
    storages: set[tuple[torch.device, int]] = set()
    for name in names:
        parameter = factors[name]
        if (
            not isinstance(parameter, torch.nn.Parameter)
            or parameter.dtype != torch.float32
            or not parameter.requires_grad
            or not parameter.is_leaf
            or id(parameter) in ids
            or id(parameter) in base_ids
        ):
            raise CheckpointFidelityError("invalid, duplicate or base factor binding")
        compare_tensor(parameter, parameter)
        storage = _storage(parameter)
        if storage in storages or storage in base_storage:
            raise CheckpointFidelityError("factor storage aliases factor/base")
        ids.add(id(parameter))
        storages.add(storage)
    return names, ids, storages, base_storage


def _snapshot(optimizer, factors, base_parameters, expected_step: int) -> _Snapshot:
    parameters = _group(optimizer)
    names, ids, storages, base_storage = _bindings(factors, base_parameters)
    if len(parameters) != len(ids) or {id(p) for p in parameters} != ids:
        raise CheckpointFidelityError("optimizer parameters are not a factor bijection")
    if (
        not isinstance(optimizer.state, Mapping)
        or len(optimizer.state) != len(ids)
        or {id(p) for p in optimizer.state} != ids
    ):
        raise CheckpointFidelityError("complete populated factor state required")
    result = _Snapshot({}, {}, {}, storages.copy(), base_storage.copy())
    used = storages | base_storage
    for name in names:
        parameter = factors[name]
        state = optimizer.state[parameter]
        if not isinstance(state, Mapping) or set(state) != _STATE_KEYS:
            raise CheckpointFidelityError("exact AdamW state keys required")
        step = state["step"]
        if (
            not isinstance(step, torch.Tensor)
            or step.dtype != torch.float32
            or step.device.type != "cpu"
            or step.layout != torch.strided
            or step.shape != torch.Size([])
            or step.requires_grad
            or float(step.item()) != expected_step
        ):
            raise CheckpointFidelityError("exact CPU FP32 scalar step required")
        for key in ("step", "exp_avg", "exp_avg_sq"):
            value = state[key]
            if key != "step":
                if (
                    not isinstance(value, torch.Tensor)
                    or value.requires_grad
                    or value.shape != parameter.shape
                    or value.dtype != parameter.dtype
                    or value.device != parameter.device
                ):
                    raise CheckpointFidelityError("moment metadata differs from factor")
                compare_tensor(value, value)
                if key == "exp_avg_sq" and (value < 0).any().item():
                    raise CheckpointFidelityError("second moment must be nonnegative")
                getattr(result, key)[name] = value.detach().clone()
            storage = _storage(value)
            if storage in used:
                raise CheckpointFidelityError("optimizer buffers alias live state")
            used.add(storage)
            result.owned_storages.add(storage)
        result.factors[name] = parameter.detach().clone()
    return result


def compare_adamw_states(
    reference: torch.optim.AdamW,
    actual: torch.optim.AdamW,
    reference_factors: Mapping[str, torch.nn.Parameter],
    actual_factors: Mapping[str, torch.nn.Parameter],
    *,
    reference_base_parameters: Sequence[torch.nn.Parameter],
    actual_base_parameters: Sequence[torch.nn.Parameter],
    expected_step: int,
    exact: bool = False,
) -> AdamWComparison:
    """Compare cloned complete states, never serialized integer parameter IDs.

    Pins the Torch2.14 AdamW group schema and synthetic step1/2 contract. Rejects
    unknown flags rather than accepting future optimizer behavior silently.
    Independent factor/state storage is mandatory; the frozen base may be shared.
    CPU callers must explicitly request exact=True for the later parity gate.
    """
    if type(expected_step) is not int or expected_step not in (1, 2):
        raise CheckpointFidelityError("expected synthetic step must be integer1/2")
    if type(exact) is not bool:
        raise CheckpointFidelityError("exact mode must be an actual boolean")
    left = _snapshot(
        reference, reference_factors, reference_base_parameters, expected_step
    )
    right = _snapshot(actual, actual_factors, actual_base_parameters, expected_step)
    if left.owned_storages & right.owned_storages:
        raise CheckpointFidelityError("comparison arms share factor/optimizer storage")
    bases = left.base_storages | right.base_storages
    if (left.owned_storages | right.owned_storages) & bases:
        raise CheckpointFidelityError(
            "comparison state aliases either arm's frozen base"
        )
    return AdamWComparison(
        expected_step,
        compare_named_tensors(left.factors, right.factors, exact=exact),
        compare_named_tensors(left.exp_avg, right.exp_avg, exact=exact),
        compare_named_tensors(left.exp_avg_sq, right.exp_avg_sq, exact=exact),
    )
