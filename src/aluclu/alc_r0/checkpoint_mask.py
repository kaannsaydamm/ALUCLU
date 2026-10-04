"""Enumerated causal-mask dependencies, not full transitive/kernel coverage."""

import types

import torch
from torch.nn import functional as F
from transformers import masking_utils as masks
from transformers.models.llama import modeling_llama as llama

from .checkpoint_execution import CheckpointExecutionError


def mask_dependencies(freeze):
    # Resolve aliases actually used by the explicit wrapper and upstream host.
    # Import lazily to preserve the wrapper/state import order.
    from . import host_wrapper

    namespace = vars(masks)
    if namespace.get("torch") is not torch:
        raise CheckpointExecutionError("unsupported mask Torch namespace")
    if namespace.get("F") is not F:
        raise CheckpointExecutionError("unsupported mask functional namespace")
    result = [id(namespace)]
    names = (
        "prepare_padding_mask",
        "_ignore_causal_mask_sdpa",
        "_ignore_bidirectional_mask_sdpa",
        "_non_vmap_expansion_sdpa",
        "padding_mask_function",
        "and_masks",
        "causal_mask_function",
        "_preprocess_mask_arguments",
        "fast_all",
        "is_tracing",
        "create_causal_mask",
        "sdpa_mask",
        "eager_mask",
        "find_packed_sequence_indices",
        "packed_sequence_mask_function",
        "or_masks",
        "blockwise_overlay",
        "maybe_pad_block_sequence_ids",
        "_can_skip_bidirectional_mask_xpu",
        "bidirectional_mask_function",
        "create_bidirectional_mask",
        "_vmap_expansion_sdpa",
    )
    bindings = [(namespace, name) for name in names]
    bindings.extend(
        (vars(module), "create_causal_mask") for module in (host_wrapper, llama)
    )
    for globals_dict, name in bindings:
        function = globals_dict.get(name)
        if not isinstance(function, types.FunctionType):
            raise CheckpointExecutionError("unsupported mask helper")
        result.append([id(globals_dict), name, freeze(function)])
    for name in ("_is_torch_greater_or_equal_than_2_6", "_is_torch_xpu_available"):
        value = namespace.get(name)
        if type(value) is not bool:
            raise CheckpointExecutionError("unsupported mask route flag")
        result.append([name, value])
    for operation in (torch.arange, torch.diff, torch.where, F.pad):
        if not isinstance(operation, (types.FunctionType, types.BuiltinFunctionType)):
            raise CheckpointExecutionError("unsupported mask runtime operation")
        result.append(freeze(operation))
    # Endpoint binding is not native semantics coverage. Vmap context classes,
    # registry dispatch, tensor methods and transitive globals remain separate.
    return result
