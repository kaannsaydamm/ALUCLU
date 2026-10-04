"""Pinned eager/SDPA mask registry closure, without executing its resolver.

Import-time references are a cooperating baseline, not source authentication or
complete mask/native semantics. Unsupported registry dispatch/schema fails closed.
"""

import inspect
import types

from transformers import masking_utils as masks
from transformers.utils.generic import GeneralInterface

from .checkpoint_execution import CheckpointExecutionError
from .checkpoint_registry import _mapping_record

_REGISTRY_CLASS = masks.AttentionMaskInterface
_GETITEM = GeneralInterface.__getitem__
_CODE = _GETITEM.__code__
_GETATTRIBUTE = object.__getattribute__
_DICT_DESCRIPTOR = GeneralInterface.__dict__["__dict__"]
_MISSING = object()
_ROUTES = {"eager": masks.eager_mask, "sdpa": masks.sdpa_mask}


def _registry_record(registry, implementation, freeze):
    if (
        type(registry) is not _REGISTRY_CLASS
        or inspect.getattr_static(type(registry), "__getattribute__")
        is not _GETATTRIBUTE
        or inspect.getattr_static(type(registry), "__getattr__", _MISSING)
        is not _MISSING
        or inspect.getattr_static(type(registry), "__dict__") is not _DICT_DESCRIPTOR
    ):
        raise CheckpointExecutionError("unsupported mask registry class/lookup")
    state = vars(registry)
    if set(state) != {"_local_mapping"}:
        raise CheckpointExecutionError("unsupported mask registry instance schema")
    function = inspect.getattr_static(type(registry), "__getitem__")
    if (
        function is not _GETITEM
        or function.__code__ is not _CODE
        or function.__closure__ is not None
    ):
        raise CheckpointExecutionError("unreviewed mask registry dispatch")
    local = state["_local_mapping"]
    if inspect.getattr_static(registry, "_local_mapping") is not local:
        raise CheckpointExecutionError("unreviewed mask registry descriptor")
    global_mapping = inspect.getattr_static(type(registry), "_global_mapping")
    try:
        maps = [_mapping_record(local), _mapping_record(global_mapping)]
    except CheckpointExecutionError as error:
        raise CheckpointExecutionError("unsupported mask registry mapping") from error
    # The actual preprocessing route checks GLOBAL presence before getitem.
    # A local-only implementation must not silently qualify an early-exit path.
    if implementation not in global_mapping:
        raise CheckpointExecutionError("mask registry global route absent")
    selected = local.get(implementation, global_mapping[implementation])
    if selected is not _ROUTES[implementation]:
        raise CheckpointExecutionError("unreviewed mask registry selection")
    return selected, [id(registry), freeze(function), maps, freeze(selected)]


def mask_registry_dependencies(implementation, registry, freeze):
    """Bind inventory and actual producer/preprocessor registry namespaces.

    Only eager/SDPA direct map lookup is admitted. No registry descriptor or
    resolver is invoked. Transitive globals/tensor/vmap/native semantics remain
    separate qualification obligations.
    """
    if type(implementation) is not str or implementation not in _ROUTES:
        raise CheckpointExecutionError("unsupported mask registry route")
    from transformers.models.llama import modeling_llama as llama

    from . import host_wrapper

    selected, first = _registry_record(registry, implementation, freeze)
    records = [["inventory_alias", first]]
    for namespace in (vars(masks), vars(host_wrapper), vars(llama)):
        producer = namespace.get("create_causal_mask")
        if type(producer) is not types.FunctionType:
            raise CheckpointExecutionError("unsupported mask registry producer")
        actual = producer.__globals__
        preprocess = actual.get("_preprocess_mask_arguments")
        if type(preprocess) is not types.FunctionType:
            raise CheckpointExecutionError("unsupported mask registry preprocessor")
        for role, function in (("producer", producer), ("preprocess", preprocess)):
            globals_dict = function.__globals__
            candidate, record = _registry_record(
                globals_dict.get("ALL_MASK_ATTENTION_FUNCTIONS"),
                implementation,
                freeze,
            )
            if candidate is not selected:
                raise CheckpointExecutionError("mask registry selections disagree")
            records.append([role, id(globals_dict), freeze(function), record])
    return selected, records
