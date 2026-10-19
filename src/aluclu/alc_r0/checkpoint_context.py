"""Explicit no_grad decorator factory schema, not arbitrary context support."""

import inspect
import types

import torch
from torch.utils._contextlib import (
    _DecoratorContextManager,
    _NoParamDecoratorContextManager,
)

from .checkpoint_execution import CheckpointExecutionError

NO_GRAD = torch.no_grad
SET_GRAD_ENABLED = torch.set_grad_enabled
CONTEXT_CLASSES = (NO_GRAD, _DecoratorContextManager, _NoParamDecoratorContextManager)
_CLONE = NO_GRAD.clone


def no_grad_factory_dependencies(method):
    """Validate one reviewed clone binding and enumerate its execution helpers."""
    owner = method.__self__
    if type(owner) is not NO_GRAD or method.__func__ is not _CLONE:
        raise CheckpointExecutionError("foreign bound method state unsupported")
    if set(vars(owner)) != {"prev"} or type(vars(owner)["prev"]) is not bool:
        raise CheckpointExecutionError("unsupported no_grad context state")
    if torch.no_grad is not NO_GRAD or torch.set_grad_enabled is not SET_GRAD_ENABLED:
        raise CheckpointExecutionError("unsupported no_grad runtime binding")
    functions = [method.__func__]
    for cls, names in (
        (NO_GRAD, ("__new__", "__init__", "clone", "__enter__", "__exit__")),
        (SET_GRAD_ENABLED, ("__init__",)),
    ):
        for name in names:
            function = inspect.getattr_static(cls, name)
            if isinstance(function, staticmethod):
                function = function.__func__
            if not isinstance(function, types.FunctionType):
                raise CheckpointExecutionError("unsupported no_grad context operation")
            # Bodies refer to their module's torch global; require the reviewed
            # namespace where present, without generic transitive traversal.
            if (
                "torch" in function.__globals__
                and function.__globals__["torch"] is not torch
            ):
                raise CheckpointExecutionError("unsupported no_grad Torch namespace")
            functions.append(function)
    getters = (
        torch.is_grad_enabled,
        torch._C._set_grad_enabled,
        torch._jit_internal.is_scripting,
    )
    if any(
        not isinstance(fn, (types.FunctionType, types.BuiltinFunctionType))
        for fn in getters
    ):
        raise CheckpointExecutionError("unsupported no_grad runtime operation")
    # Native descriptors/metaclass dispatch are identity-bound, not code audited.
    dispatch = [id(torch._C), id(torch._jit_internal)]
    for cls in (*CONTEXT_CLASSES, SET_GRAD_ENABLED):
        dispatch.extend(
            (
                id(cls),
                id(type(cls)),
                id(inspect.getattr_static(type(cls), "__call__")),
                id(inspect.getattr_static(cls, "__getattribute__")),
            )
        )
    return vars(owner)["prev"], functions, getters, dispatch
