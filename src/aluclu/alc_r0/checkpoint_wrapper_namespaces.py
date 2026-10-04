"""Enumerated actual wrapper aliases/builtins, not full transitive semantics."""

import builtins
import types
from typing import cast

import torch
from torch import nn
from transformers.cache_utils import DynamicCache
from transformers.masking_utils import create_causal_mask
from transformers.modeling_outputs import CausalLMOutputWithPast

from .checkpoint_execution import CheckpointExecutionError, CheckpointSession
from .matched_lora import _q_attention_with_projection

# Import-time cooperating references, not authentication of source/runtime.
_ALIASES = {
    "torch": torch,
    "nn": nn,
    "cast": cast,
    "CheckpointSession": CheckpointSession,
    "CheckpointExecutionError": CheckpointExecutionError,
    "CausalLMOutputWithPast": CausalLMOutputWithPast,
    "DynamicCache": DynamicCache,
    "create_causal_mask": create_causal_mask,
    "_q_attention_with_projection": _q_attention_with_projection,
}
_BUILTINS = {
    name: getattr(builtins, name)
    for name in (
        "isinstance",
        "type",
        "next",
        "any",
        "enumerate",
        "tuple",
        "slice",
        "super",
        "len",
        "bool",
        "int",
        "ValueError",
        "AttributeError",
    )
}
_MODULE = nn.Module
_TENSOR = torch.Tensor
_CONSTANTS = {name: getattr(torch, name) for name in ("int64", "strided")}


def wrapper_namespace_dependencies(function, name, is_lora, freeze):
    """Bind enumerated aliases from the function's actual globals and builtins.

    Classes/module namespaces are identity-bound, not complete method inventories.
    Native endpoints are identity-bound; helper functions use existing bounded
    code/default/closure freezing, not generic transitive-global recursion.
    No alias, resolver, getter or native operation is called to inspect it.
    """
    names = {
        "forward": (
            "torch",
            "cast",
            "DynamicCache",
            "create_causal_mask",
            "CausalLMOutputWithPast",
        ),
        "_checkpoint_forward": (
            "torch",
            "CheckpointSession",
            "CheckpointExecutionError",
            "create_causal_mask",
            "CausalLMOutputWithPast",
        ),
        "_checkpoint_factors": ("CheckpointExecutionError",),
        "_bind_checkpoint_block": ("nn", "CheckpointExecutionError")
        + (("_q_attention_with_projection",) if is_lora else ()),
        "_q_lora_attention": ("_q_attention_with_projection",),
    }.get(name, ())
    namespace = function.__globals__
    records = [id(namespace)]
    for key in names:
        value = namespace.get(key)
        if value is not _ALIASES[key]:
            raise CheckpointExecutionError("unreviewed wrapper namespace alias")
        binding = (
            freeze(value)
            if type(value) is types.FunctionType
            else ["namespace_identity", id(value)]
        )
        records.append([key, binding])
    table = function.__builtins__
    if type(table) is not dict or len(table) > 512:
        raise CheckpointExecutionError("unsupported wrapper builtin namespace")
    if any(type(key) is not str or len(key) > 256 for key in table):
        raise CheckpointExecutionError("wrapper builtin namespace key bound")
    builtin_records = []
    for key, expected in _BUILTINS.items():
        shadow = key in namespace
        actual = namespace[key] if shadow else table.get(key)
        if actual is not expected:
            raise CheckpointExecutionError(
                "unreviewed wrapper builtin namespace binding"
            )
        builtin_records.append([key, shadow, id(actual)])
    records.append(["effective_builtins", id(table), builtin_records])
    if "torch" in names:
        runtime = vars(namespace["torch"])
        if runtime.get("Tensor") is not _TENSOR:
            raise CheckpointExecutionError("unreviewed wrapper Tensor namespace")
        records.append(["Tensor", id(_TENSOR)])
        for key, expected in _CONSTANTS.items():
            if runtime.get(key) is not expected:
                raise CheckpointExecutionError(
                    "unreviewed wrapper dtype/layout namespace"
                )
            records.append([key, id(expected)])
        operation = runtime.get("arange")
        if not isinstance(operation, (types.FunctionType, types.BuiltinFunctionType)):
            raise CheckpointExecutionError("unsupported wrapper arange namespace")
        records.append(["arange", freeze(operation)])
    if "nn" in names:
        if vars(namespace["nn"]).get("Module") is not _MODULE:
            raise CheckpointExecutionError("unreviewed wrapper Module namespace")
        records.append(["Module", id(_MODULE)])
    return records
