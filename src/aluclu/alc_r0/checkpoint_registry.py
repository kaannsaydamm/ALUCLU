"""Bounded pinned eager/SDPA registry bindings without executing resolvers.

Import-time Python dispatch/code references are a cooperating-process baseline,
not source authentication or a native semantic audit. Unknown registry classes,
instance dispatch overrides and nonreviewed route functions fail closed.
"""

import builtins
import inspect
import types
from collections.abc import Mapping

from transformers.integrations.sdpa_attention import sdpa_attention_forward
from transformers.modeling_utils import AttentionInterface
from transformers.models.llama import modeling_llama as llama
from transformers.utils.generic import GeneralInterface

from .checkpoint_execution import CheckpointExecutionError

_EAGER = llama.eager_attention_forward
_SUPER, _KEY_ERROR = builtins.super, builtins.KeyError
_DISPATCH = tuple(
    (
        name,
        function,
        function.__code__,
        tuple(cell.cell_contents for cell in function.__closure__ or ()),
    )
    for name, function in (
        ("get_interface", AttentionInterface.get_interface),
        ("get", Mapping.get),
        ("__contains__", Mapping.__contains__),
        ("__getitem__", GeneralInterface.__getitem__),
    )
)
_GETATTRIBUTE = object.__getattribute__


def _mapping_record(mapping):
    if type(mapping) is not dict or len(mapping) > 128:
        raise CheckpointExecutionError("unsupported attention registry mapping")
    if any(
        type(key) is not str
        or not key
        or len(key) > 256
        or not key.isascii()
        or not isinstance(value, types.FunctionType)
        for key, value in mapping.items()
    ):
        raise CheckpointExecutionError("unsupported attention registry entry")
    return [id(mapping), [(key, id(mapping[key])) for key in sorted(mapping)]]


def _builtin_binding(function, name, expected):
    namespace = function.__globals__
    # CPython retains this actual table when the function is created; rebinding
    # globals['__builtins__'] does not replace the function's builtin resolution.
    table = function.__builtins__
    if type(table) is not dict or namespace.get(name, table.get(name)) is not expected:
        raise CheckpointExecutionError("unreviewed attention resolver builtin")
    return [id(namespace), id(table), name, id(expected), name in namespace]


def _registry_binding(registry, implementation, fallback, freeze):
    if (
        type(registry) is not AttentionInterface
        or set(vars(registry)) != {"_local_mapping"}
        or inspect.getattr_static(type(registry), "__getattribute__")
        is not _GETATTRIBUTE
        or fallback is not _EAGER
    ):
        raise CheckpointExecutionError("unreviewed attention registry/fallback")
    dispatch = []
    for name, expected, code, closure in _DISPATCH:
        function = inspect.getattr_static(type(registry), name)
        if function is not expected or function.__code__ is not code:
            raise CheckpointExecutionError("unreviewed attention registry dispatch")
        cells = tuple(cell.cell_contents for cell in function.__closure__ or ())
        if len(cells) != len(closure) or any(
            a is not b for a, b in zip(cells, closure)
        ):
            raise CheckpointExecutionError("unreviewed attention registry closure")
        dispatch.append(
            [
                name,
                id(function),
                id(code),
                freeze(function.__defaults__),
                freeze(function.__kwdefaults__),
                [id(value) for value in cells],
                _builtin_binding(function, "KeyError", _KEY_ERROR),
            ]
        )
        if name == "get_interface":
            dispatch.append(_builtin_binding(function, "super", _SUPER))
    local = vars(registry)["_local_mapping"]
    if inspect.getattr_static(registry, "_local_mapping") is not local:
        raise CheckpointExecutionError("unreviewed attention registry descriptor")
    global_mapping = inspect.getattr_static(type(registry), "_global_mapping")
    tables = [_mapping_record(local), _mapping_record(global_mapping)]
    # Exactly the reviewed get/contains/getitem semantics for an admitted route,
    # but without invoking potentially altered resolver methods for inventory.
    selected = local.get(implementation, global_mapping.get(implementation, fallback))
    expected = _EAGER if implementation == "eager" else sdpa_attention_forward
    if selected is not expected:
        raise CheckpointExecutionError("unreviewed attention registry selection")
    return selected, [
        id(registry),
        id(type(registry)),
        dispatch,
        tables,
        freeze(fallback),
        freeze(selected),
    ]


def attention_registry_dependencies(implementation, registry, fallback, freeze):
    """Bind state/upstream/q-local aliases and their actual resolver closure."""
    if type(implementation) is not str or implementation not in {"eager", "sdpa"}:
        raise CheckpointExecutionError("unreviewed attention route")
    from . import matched_lora

    records = []
    selected = None
    for namespace, actual_registry, actual_fallback in (
        (None, registry, fallback),
        (
            vars(llama),
            vars(llama).get("ALL_ATTENTION_FUNCTIONS"),
            vars(llama).get("eager_attention_forward"),
        ),
        (
            vars(matched_lora),
            vars(matched_lora).get("ALL_ATTENTION_FUNCTIONS"),
            vars(matched_lora).get("eager_attention_forward"),
        ),
    ):
        actual, record = _registry_binding(
            actual_registry, implementation, actual_fallback, freeze
        )
        if selected is not None and actual is not selected:
            raise CheckpointExecutionError("attention registry selections disagree")
        selected = actual
        records.append([None if namespace is None else id(namespace), record])
    return selected, records
