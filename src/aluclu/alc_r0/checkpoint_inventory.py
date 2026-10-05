"""Explicit bounded inventory integration, not host qualification/authority."""

from functools import partial

from .checkpoint_execution import CheckpointController, CheckpointExecutionError


def _wrapper_fingerprint(owner):
    # Lazy import breaks the state/wrapper/LoRA cycle. Preparation warms it before
    # session capture invokes this observational getter under the controller lock.
    from .checkpoint_state import computational_state_fingerprint

    return computational_state_fingerprint({"wrapper": owner})


def enable_wrapper_inventory(owner):
    """Prepare outside the lock, then bind atomically on the original controller.

    Callers must exclusively own quiescent wrapper mutation while preparing.
    Racing first installations may reject; neither replaces an existing binding.
    This does not certify caller callbacks or authorize an actual model run.
    """
    owner._assert_checkpoint_mutation_allowed()
    # Do not invoke a class shadow/property before schema inspection rejects it.
    controller = owner.__dict__.get("_checkpoint_controller")
    if type(controller) is not CheckpointController:
        raise CheckpointExecutionError("owned exact wrapper controller required")
    getter = controller.state_fingerprint_getter
    if getter is None:
        getter = partial(_wrapper_fingerprint, owner)
    elif not (
        type(getter) is partial
        and getter.func is _wrapper_fingerprint
        and len(getter.args) == 1
        and getter.args[0] is owner
        and not getter.keywords
    ):
        raise CheckpointExecutionError("foreign computational state getter")
    # Reject unsupported schema/factors before publication. The result is not
    # cached: every capture/guard inventories the CURRENT mounts and methods.
    _wrapper_fingerprint(owner)
    controller._install_state_fingerprint_getter(getter)
