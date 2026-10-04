"""Enumerated causal-mask dependencies, not full transitive/kernel coverage."""

import types

import torch
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
    # Explicitly bounded: vmap context classes, packed/blockwise/bidirectional
    # subhelpers, registry dispatch and native operations need separate coverage.
    return result
