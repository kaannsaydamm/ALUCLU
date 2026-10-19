"""Enumerate only the reviewed disabled HF __call__/super dispatch route.

No general class support, function execution, assets or implicit HF checkpointing.
Runtime/source authentication and hostile concurrent mutation remain external.
"""

import builtins
import inspect
import types

from torch import nn
from transformers import modeling_layers
from transformers.modeling_layers import GradientCheckpointingLayer

from .checkpoint_execution import CheckpointExecutionError

_CLASS = GradientCheckpointingLayer
_CALL = _CLASS.__call__
_CODE = _CALL.__code__
_SUPER = builtins.super


def disabled_hf_dispatch(module, operation, freeze):
    """Return a scoped binding, or None for unrelated module dispatch."""
    mro = type(module).__mro__
    if _CLASS not in mro:
        return None
    namespace = _CALL.__globals__
    builtin_namespace = namespace.get("__builtins__")
    if type(builtin_namespace) is types.ModuleType:
        builtin_namespace = vars(builtin_namespace)
    # Python caches the fallback mapping on the function at construction;
    # changing globals['__builtins__'] does not change that effective mapping.
    actual_builtins = _CALL.__builtins__
    if type(actual_builtins) is not dict or builtin_namespace is not actual_builtins:
        raise CheckpointExecutionError("unreviewed HF dispatch builtins")
    effective_super = namespace.get("super", actual_builtins.get("super"))
    index = mro.index(_CLASS)
    if (
        len(mro) > 64
        or mro[index:] != (_CLASS, nn.Module, object)
        or modeling_layers.GradientCheckpointingLayer is not _CLASS
        or vars(_CLASS).get("__call__") is not _CALL
        or operation is not _CALL
        or _CALL.__code__ is not _CODE
        or _CODE.co_freevars != ("__class__",)
        or _CALL.__closure__ is None
        or len(_CALL.__closure__) != 1
        or _CALL.__closure__[0].cell_contents is not _CLASS
        or effective_super is not _SUPER
        or inspect.getattr_static(module, "gradient_checkpointing") is not False
    ):
        raise CheckpointExecutionError("unreviewed disabled HF dispatch route")
    # Class cell is represented only here, never passed to generic freeze.
    # Bind super's exact suffix and the endpoints it dynamically resolves.
    endpoints = []
    for name in ("__call__", "_wrapped_call_impl", "_call_impl"):
        target = inspect.getattr_static(nn.Module, name)
        if type(target) is not types.FunctionType:
            raise CheckpointExecutionError("unsupported HF super endpoint")
        endpoints.append([name, freeze(target)])
    return [
        "disabled_hf_dispatch",
        id(_CALL),
        id(_CODE),
        freeze(_CALL.__defaults__),
        freeze(_CALL.__kwdefaults__),
        ["scoped_class_cell", id(_CLASS)],
        [[id(cls), [id(base) for base in cls.__bases__]] for cls in mro],
        id(namespace),
        id(actual_builtins),
        id(effective_super),
        endpoints,
    ]
