"""Enumerated wrapper methods/schema; namespaces and host qualification separate."""

import inspect
import types
from _thread import LockType

from .checkpoint_execution import CheckpointController, CheckpointExecutionError
from .checkpoint_wrapper_namespaces import wrapper_namespace_dependencies

_MISSING = object()

# Explicit nn.Module instance schema, not 'ignore every private attribute'.
_MODULE_FIELDS = {
    "training",
    "_parameters",
    "_buffers",
    "_non_persistent_buffers_set",
    "_backward_pre_hooks",
    "_backward_hooks",
    "_is_full_backward_hook",
    "_forward_hooks",
    "_forward_hooks_with_kwargs",
    "_forward_hooks_always_called",
    "_forward_pre_hooks",
    "_forward_pre_hooks_with_kwargs",
    "_state_dict_hooks",
    "_state_dict_pre_hooks",
    "_load_state_dict_pre_hooks",
    "_load_state_dict_post_hooks",
    "_modules",
    "_compiled_call_impl",
}
_METHODS = (
    "forward",
    "_checkpoint_forward",
    "_checkpoint_factors",
    "_bind_checkpoint_block",
    "_run_decoder_layer",
    "checkpoint_session",
    "enable_checkpoint_inventory",
    "_assert_checkpoint_mutation_allowed",
    "__getattr__",
)


def wrapper_method_dependencies(module, freeze, wrapper_classes, factor_classes):
    """Never invoke wrapper methods, getters or controller lock here.

    Only the controller's enumerated stable bindings are recorded. Its active
    lease/thread/ticket bookkeeping is intentionally not computational drift.
    Selected actual aliases/builtins are enumerated, not all transitive globals
    or controller implementation semantics. This does not install any callback.
    """
    if not isinstance(module, wrapper_classes[0]):
        return None
    if type(module) not in wrapper_classes:
        raise CheckpointExecutionError("unreviewed wrapper subclass")
    is_lora = type(module) is wrapper_classes[1]
    is_reference = len(wrapper_classes) > 2 and type(module) is wrapper_classes[2]
    arm = 2 if is_reference else int(is_lora)
    factor_field = ("capsule", "lora", "reference")[arm]
    state = vars(module)
    if (
        set(state)
        - _MODULE_FIELDS
        - {"_checkpoint_controller", "capsule", factor_field}
    ):
        raise CheckpointExecutionError("unknown wrapper instance field")
    if not is_lora and "lora" in state:
        raise CheckpointExecutionError("wrong wrapper arm field")
    registered = state["_modules"]
    for field in ("base", "capsule", "lora", "reference", "_checkpoint_controller"):
        # Registered modules resolve via nn.Module.__getattr__, not class
        # properties. Reject class shadows without invoking their descriptor.
        if inspect.getattr_static(type(module), field, _MISSING) is not _MISSING:
            raise CheckpointExecutionError("wrapper class field shadow")
    allowed = {"base", "capsule", factor_field}
    if set(registered) - allowed or "base" not in registered:
        raise CheckpointExecutionError("unknown wrapper registered field")
    selected = registered.get(factor_field)
    if type(selected) is not factor_classes[arm][0]:
        raise CheckpointExecutionError("mounted exact wrapper factors required")
    if (is_lora or is_reference) and registered.get("capsule") is not None:
        raise CheckpointExecutionError("wrong wrapper arm mount")
    methods = []
    names = _METHODS + (("_q_lora_attention",) if is_lora else ())
    for name in names:
        if name in state:
            raise CheckpointExecutionError("wrapper instance method override")
        function = inspect.getattr_static(type(module), name)
        if type(function) is not types.FunctionType:
            raise CheckpointExecutionError("unsupported wrapper method descriptor")
        methods.append(
            [
                name,
                freeze(function),
                wrapper_namespace_dependencies(
                    function, name, is_lora, freeze, is_reference=is_reference
                ),
            ]
        )
    if is_lora or is_reference:
        # super() resolves these parent bodies on unselected ports. Binding the
        # selected override and a class-cell identity alone misses that route.
        for name in ("_bind_checkpoint_block", "_run_decoder_layer"):
            function = inspect.getattr_static(wrapper_classes[0], name)
            if type(function) is not types.FunctionType:
                raise CheckpointExecutionError("unsupported wrapper fallback method")
            methods.append(
                [
                    "super:" + name,
                    freeze(function),
                    wrapper_namespace_dependencies(function, name, False, freeze),
                ]
            )
    controller = state.get("_checkpoint_controller")
    if type(controller) is not CheckpointController or controller.owner is not module:
        raise CheckpointExecutionError("owned exact wrapper controller required")
    if type(controller._lock) is not LockType or controller.layer_count != 30:
        raise CheckpointExecutionError("wrapper controller lock/depth drift")
    factor_getter = controller.factor_getter
    if (
        type(factor_getter) is not types.MethodType
        or factor_getter.__self__ is not module
        or factor_getter.__func__
        is not inspect.getattr_static(type(module), "_checkpoint_factors")
        or type(controller.base_getter) is not types.FunctionType
    ):
        raise CheckpointExecutionError("wrapper controller getter binding drift")
    return [
        methods,
        id(controller),
        id(controller._lock),
        controller.layer_count,
        freeze(controller.base_getter),
        freeze(factor_getter),
        freeze(controller.state_fingerprint_getter),
    ]
