"""Enumerated eager/SDPA helper globals; not a complete native/kernel audit."""

import types

import torch
from torch import nn
from transformers.models.llama import modeling_llama as llama

from .checkpoint_execution import CheckpointExecutionError


def attention_dependencies(implementation, attention, freeze):
    # Lazy import preserves wrapper/state/matched-LoRA import order.
    from . import matched_lora

    result = []

    def function(namespace, name):
        value = namespace.get(name)
        if not isinstance(value, types.FunctionType):
            raise CheckpointExecutionError("unsupported attention helper")
        return value

    llama_globals = vars(llama)
    q_helper = function(vars(matched_lora), "_q_attention_with_projection")
    q_globals = q_helper.__globals__
    selected_globals = attention.__globals__
    for namespace in (llama_globals, q_globals, selected_globals):
        if namespace.get("torch") is not torch:
            raise CheckpointExecutionError("unsupported attention Torch namespace")
        result.append(id(namespace))
    functions = [
        function(llama_globals, "apply_rotary_pos_emb"),
        function(llama_globals, "rotate_half"),
        q_helper,
        function(q_globals, "apply_rotary_pos_emb"),
        function(selected_globals, "repeat_kv"),
    ]
    if implementation == "sdpa":
        functions.extend(
            function(selected_globals, name)
            for name in ("use_gqa_in_sdpa", "create_position_bias_mask")
        )
        for name in (
            "_is_torch_xpu_available",
            "_is_torch_npu_available",
            "_is_torch_greater_or_equal_than_2_8",
        ):
            value = selected_globals.get(name)
            if type(value) is not bool:
                raise CheckpointExecutionError("unsupported attention route flag")
            result.append([name, value])
    elif selected_globals.get("nn") is not nn:
        raise CheckpointExecutionError("unsupported attention NN namespace")
    result.extend(freeze(fn) for fn in functions)
    # Bind resolved native/Python endpoints only, not their transitive semantics.
    for operation in (
        torch.cat,
        torch.matmul,
        nn.functional.softmax,
        nn.functional.dropout,
        nn.functional.scaled_dot_product_attention,
    ):
        if not isinstance(operation, (types.FunctionType, types.BuiltinFunctionType)):
            raise CheckpointExecutionError("unsupported attention runtime operation")
        result.append(freeze(operation))
    return result
