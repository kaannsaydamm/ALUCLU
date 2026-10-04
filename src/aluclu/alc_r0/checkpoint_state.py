"""Bounded cooperating-process attribute inventory, not hostile-host security.

Registered tensors/modules remain the session engine's responsibility. This
helper rejects unknown attribute types instead of treating object identity as
proof of immutable computational state. Real-host coverage needs separate audit.
"""

from __future__ import annotations

import functools
import hashlib
import inspect
import json
import math
import types
from collections import OrderedDict
from collections.abc import Mapping

import torch
from torch import nn
from transformers import GenerationConfig, PretrainedConfig, PreTrainedModel
from transformers.loss.loss_utils import ForCausalLMLoss, fixed_cross_entropy
from transformers.masking_utils import ALL_MASK_ATTENTION_FUNCTIONS
from transformers.modeling_utils import ALL_ATTENTION_FUNCTIONS
from transformers.models.llama.modeling_llama import (
    LlamaAttention,
    LlamaForCausalLM,
    eager_attention_forward,
)

from .checkpoint_attention import attention_dependencies
from .checkpoint_context import CONTEXT_CLASSES, no_grad_factory_dependencies
from .checkpoint_execution import CheckpointExecutionError, _digest, _tensor_stamp
from .checkpoint_fidelity import _canonical_keys
from .checkpoint_runtime import read_runtime_state

_CAUSAL_LOSS_PROPERTY = PreTrainedModel.loss_function
_MISSING = object()


def _loss_dependencies(module, freeze):
    """Bind the enumerated causal-loss route without invoking its property."""
    if not isinstance(module, LlamaForCausalLM):
        return None
    descriptor = inspect.getattr_static(type(module), "loss_function", None)
    if descriptor is not _CAUSAL_LOSS_PROPERTY:
        raise CheckpointExecutionError("unreviewed loss property")
    namespace = descriptor.fget.__globals__
    mapping = namespace.get("LOSS_MAPPING")
    if type(mapping) is not dict or len(mapping) > 2048:
        raise CheckpointExecutionError("unsupported loss registry")
    override = inspect.getattr_static(module, "_loss_function", _MISSING)
    loss_type = inspect.getattr_static(module, "loss_type", None)
    if override is _MISSING:
        if type(loss_type) is not str or loss_type != "ForCausalLM":
            raise CheckpointExecutionError("unreviewed loss route")
        selected = mapping.get(loss_type)
    else:
        selected = override
    if selected is not ForCausalLMLoss:
        raise CheckpointExecutionError("unreviewed selected causal loss")
    loss_namespace = selected.__globals__
    helper = loss_namespace.get("fixed_cross_entropy")
    if helper is not fixed_cross_entropy:
        raise CheckpointExecutionError("unreviewed causal loss helper")
    helper_namespace = helper.__globals__
    neural, runtime = loss_namespace.get("nn"), helper_namespace.get("torch")
    if type(neural) is not types.ModuleType or type(runtime) is not types.ModuleType:
        raise CheckpointExecutionError("unsupported loss runtime namespace")
    # Both functions are reviewed as sharing the same loss_utils globals.
    if helper_namespace is not loss_namespace:
        raise CheckpointExecutionError("unreviewed causal loss namespace")
    functional = vars(neural).get("functional")
    if type(functional) is not types.ModuleType:
        raise CheckpointExecutionError("unsupported loss functional namespace")
    operations = []
    for name, native_name in (("pad", "pad"), ("cross_entropy", "cross_entropy_loss")):
        operation = vars(functional).get(name)
        if not isinstance(operation, types.FunctionType):
            raise CheckpointExecutionError("unsupported loss functional callable")
        op_runtime = operation.__globals__.get("torch")
        if type(op_runtime) is not types.ModuleType:
            raise CheckpointExecutionError("unsupported loss operation namespace")
        native = vars(op_runtime).get("_C")
        if type(native) is not types.ModuleType:
            raise CheckpointExecutionError("unsupported loss native namespace")
        native_nn = vars(native).get("_nn")
        if type(native_nn) is not types.ModuleType:
            raise CheckpointExecutionError("unsupported loss native namespace")
        native_operation = vars(native_nn).get(native_name)
        if not isinstance(native_operation, types.BuiltinFunctionType):
            raise CheckpointExecutionError("unsupported loss native callable")
        operations.append(
            [
                name,
                freeze(operation),
                id(op_runtime),
                id(native),
                id(native_nn),
                freeze(native_operation),
            ]
        )
    is_tensor = vars(runtime).get("is_tensor")
    if not isinstance(is_tensor, types.FunctionType):
        raise CheckpointExecutionError("unsupported loss runtime callable")
    return [
        id(descriptor),
        freeze(descriptor.fget),
        id(namespace),
        id(mapping),
        freeze(loss_type),
        override is not _MISSING,
        freeze(selected),
        freeze(helper),
        id(loss_namespace),
        id(neural),
        id(functional),
        id(runtime),
        freeze(is_tensor),
        operations,
    ]


def _factor_dependencies(module, freeze, factor_classes):
    """Bind enumerated factor globals; not generic transitive global traversal."""
    factory_name = None
    for cls, name in factor_classes:
        if isinstance(module, cls):
            factory_name = name
            break
    if factory_name is None:
        return None
    factory = getattr(module, factory_name)
    if not isinstance(factory, types.MethodType) or factory.__self__ is not module:
        raise CheckpointExecutionError("unsupported factor factory binding")
    namespace = factory.__func__.__globals__
    functional, runtime = namespace.get("F"), namespace.get("torch")
    if (
        type(functional) is not types.ModuleType
        or type(runtime) is not types.ModuleType
    ):
        raise CheckpointExecutionError("unsupported factor runtime namespace")

    def callable_binding(value):
        if not isinstance(value, (types.FunctionType, types.BuiltinFunctionType)):
            raise CheckpointExecutionError("unsupported factor runtime callable")
        return freeze(value)

    autocast = vars(runtime).get("autocast")
    if isinstance(autocast, type):
        autocast_binding = [
            id(autocast),
            [
                callable_binding(getattr(autocast, name, None))
                for name in ("__init__", "__enter__", "__exit__")
            ],
        ]
    else:
        autocast_binding = callable_binding(autocast)
    result = [
        freeze(factory),
        id(namespace),
        id(functional),
        id(runtime),
        callable_binding(vars(functional).get("linear")),
        autocast_binding,
    ]
    dtype = vars(runtime).get("float32")
    if not isinstance(dtype, torch.dtype):
        raise CheckpointExecutionError("unsupported factor runtime dtype")
    result.append(freeze(dtype))
    if factory_name == "bind_port":
        width, epsilon = (
            namespace.get("CANONICAL_WIDTH"),
            namespace.get("NORMALIZATION_EPSILON"),
        )
        if type(width) is not int or type(epsilon) is not float:
            raise CheckpointExecutionError("unsupported factor scalar binding")
        bf16 = vars(runtime).get("bfloat16")
        if not isinstance(bf16, torch.dtype):
            raise CheckpointExecutionError("unsupported factor runtime dtype")
        result.extend(
            [
                freeze(width),
                freeze(epsilon),
                freeze(bf16),
                callable_binding(vars(runtime).get("sqrt")),
            ]
        )
    return result


def _module_inventory(roots, names):
    inventory = []
    for root_name in names:
        root = roots[root_name]
        if not isinstance(root, nn.Module):
            raise CheckpointExecutionError("module roots required")
        seen, ancestors = set(), set()
        stack = [("", root, 0, False)]
        while stack:
            name, module, depth, leaving = stack.pop()
            identity = id(module)
            if leaving:
                ancestors.remove(identity)
                continue
            if identity in ancestors:
                raise CheckpointExecutionError("registered module cycle")
            if identity in seen:
                continue
            if depth > 64 or len(inventory) >= 4096:
                raise CheckpointExecutionError("module inventory bound exceeded")
            children = vars(module).get("_modules")
            if type(children) is not dict or len(children) > 2048:
                raise CheckpointExecutionError("module registry bound/type violation")
            seen.add(identity)
            ancestors.add(identity)
            inventory.append((root_name, name, module))
            stack.append((name, module, depth, True))
            for key, child in reversed(tuple(children.items())):
                if type(key) is not str or len(key) > 256:
                    raise CheckpointExecutionError("module name bound/type violation")
                if child is not None:
                    if not isinstance(child, nn.Module):
                        raise CheckpointExecutionError("invalid registered module")
                    stack.append(
                        (f"{name}.{key}" if name else key, child, depth + 1, False)
                    )
    return inventory


def computational_state_fingerprint(roots: Mapping[str, nn.Module]) -> str:
    """Fingerprint module attributes, config, forward bindings and small tensors.

    Bounds: roots16, modules4096/depth64, value depth32/nodes100000, containers2048,
    UTF8 strings64KiB/integers256bits, unregistered tensors64KiB, JSON stream16MiB.
    These are component limits, NOT a measured peak-memory/latency guarantee.
    Class call/dispatch bindings are identity-bound, not fully inventoried.
    Eager/SDPA selected attention and mask callables are bound, not their global
    helper dependencies or native kernels. Other attention routes are rejected.
    Capsule/LoRA factor factories bind enumerated scalar/namespace/math/autocast
    dependencies. Builtin callables are identity-bound, not native-code audited.
    Llama causal loss binds its reviewed property/route/helpers and enumerated
    functional/native callable identities, not generic Torch execution semantics.
    Enumerated backend settings/getters are bound; checkpoint-preserved RNG,
    autocast and grad context are intentionally not ambient drift fields.
    Function globals, arbitrary class/property dependencies and external state
    are NOT inventoried; later host-specific audit must separately bind/reject them.
    No fallback repr/pickle or arbitrary object attribute traversal.
    The result binds identity and state inside one process, not a portable hash.
    """
    if not isinstance(roots, Mapping) or not roots or len(roots) > 16:
        raise CheckpointExecutionError("nonempty module roots required")
    if any(type(name) is not str or len(name) > 256 for name in roots):
        raise CheckpointExecutionError("root name bound/type violation")
    names = _canonical_keys(roots)
    # Lazy imports avoid a wrapper/state/matched-LoRA import cycle. Only known
    # factor classes receive this explicit dependency inventory.
    from .matched_lora import MatchedQProjLoRA
    from .research_capsule import ResearchCapsuleV0

    factor_classes = (
        (ResearchCapsuleV0, "bind_port"),
        (MatchedQProjLoRA, "bind_q_projection"),
    )
    active = set()
    memo = {}
    nodes = 0
    inventory = _module_inventory(roots, names)
    module_ids = {id(module) for _, _, module in inventory}

    def freeze(value, depth=0):
        nonlocal nodes
        nodes += 1
        if depth > 32 or nodes > 100000:
            raise CheckpointExecutionError(
                "computational state resource bound exceeded"
            )
        if value is None or type(value) in {bool, int, str}:
            if type(value) is int and value.bit_length() > 256:
                raise CheckpointExecutionError("integer state bound exceeded")
            if type(value) is str:
                if len(value) > 65536 or len(value.encode("utf-8")) > 65536:
                    raise CheckpointExecutionError("string state bound exceeded")
            return [type(value).__name__, value]
        if type(value) is float:
            if not math.isfinite(value):
                raise CheckpointExecutionError("nonfinite computational state")
            return ["float", value.hex()]
        if isinstance(value, (torch.dtype, torch.device)):
            return [type(value).__name__, str(value)]
        if isinstance(value, types.MethodType):
            if id(value.__self__) not in module_ids:
                previous, functions, getters, dispatch = no_grad_factory_dependencies(
                    value
                )
                return [
                    "no_grad_factory",
                    id(value.__self__),
                    previous,
                    [freeze(fn, depth + 1) for fn in functions],
                    [freeze(fn, depth + 1) for fn in getters],
                    dispatch,
                ]
            # Attribute access constructs ephemeral method objects; never memoize
            # their recycled IDs. Their stable binding is self plus function.
            return ["method", id(value.__self__), freeze(value.__func__, depth + 1)]
        if any(value is cls for cls in CONTEXT_CLASSES):
            # Only class cells in the separately enumerated context operations.
            # Method bodies/state are bound above; this is not generic class support.
            return ["context_class", id(value)]
        identity = id(value)
        if identity in active:
            raise CheckpointExecutionError("computational state cycle")
        if identity in memo:
            return ["reference", identity]
        active.add(identity)
        try:
            if isinstance(value, torch.Tensor):
                if value.requires_grad or value.numel() * value.element_size() > 65536:
                    raise CheckpointExecutionError(
                        "unsupported unregistered tensor state"
                    )
                stamp = _tensor_stamp(value)
                result = [
                    "tensor",
                    identity,
                    [str(item) for item in stamp],
                    _digest((("value", value),)),
                ]
            elif type(value) in {dict, OrderedDict}:
                if len(value) > 2048:
                    raise CheckpointExecutionError(
                        "computational container bound exceeded"
                    )
                items = [
                    (freeze(key, depth + 1), freeze(item, depth + 1))
                    for key, item in value.items()
                ]
                items.sort(key=lambda pair: pair[0])
                result = ["mapping", identity, items]
            elif type(value) in {list, tuple, set, frozenset}:
                if len(value) > 2048:
                    raise CheckpointExecutionError(
                        "computational container bound exceeded"
                    )
                items = [freeze(item, depth + 1) for item in value]
                if isinstance(value, (set, frozenset)):
                    items.sort()
                result = [type(value).__name__, identity, items]
            elif isinstance(value, (PretrainedConfig, GenerationConfig)):
                result = [
                    "config",
                    identity,
                    id(type(value)),
                    freeze(vars(value), depth + 1),
                ]
            elif isinstance(value, types.FunctionType):
                closure = tuple(cell.cell_contents for cell in value.__closure__ or ())
                # Ephemeral closure tuples themselves are not fingerprint identities.
                result = [
                    "function",
                    identity,
                    id(value.__code__),
                    freeze(value.__defaults__, depth + 1),
                    freeze(value.__kwdefaults__, depth + 1),
                    [freeze(item, depth + 1) for item in closure],
                ]
            elif isinstance(value, types.BuiltinFunctionType):
                # Python cannot expose native implementation state here. This
                # binds the resolved callable only; runtime qualification is separate.
                result = ["builtin", identity, id(value.__self__)]
            elif isinstance(value, functools.partial):
                result = [
                    "partial",
                    identity,
                    freeze(value.func, depth + 1),
                    freeze(value.args, depth + 1),
                    freeze(value.keywords, depth + 1),
                ]
            else:
                raise CheckpointExecutionError(
                    f"unsupported computational attribute type: {type(value).__name__}"
                )
            memo[identity] = result
            return result
        finally:
            active.remove(identity)

    framework = torch.nn.modules.module
    for name in (
        "_global_forward_hooks",
        "_global_forward_pre_hooks",
        "_global_backward_hooks",
        "_global_backward_pre_hooks",
        "_global_module_registration_hooks",
        "_global_parameter_registration_hooks",
        "_global_buffer_registration_hooks",
    ):
        if getattr(framework, name):
            raise CheckpointExecutionError("global module hooks unsupported")
    runtime_values, runtime_getters = read_runtime_state()
    # Newly created snapshot dict identities are not process state.
    records = [
        [
            "runtime",
            [(key, freeze(runtime_values[key])) for key in sorted(runtime_values)],
            [(key, freeze(runtime_getters[key])) for key in sorted(runtime_getters)],
        ]
    ]
    for root_name, name, module in inventory:
        if len(vars(module)) > 2048:
            raise CheckpointExecutionError("module attribute bound exceeded")
        attributes = {}
        for key, value in vars(module).items():
            if key in {"_parameters", "_buffers", "_modules"}:
                continue
            if "hook" in key and value:
                raise CheckpointExecutionError("module hooks unsupported")
            if key == "_compiled_call_impl" and value is not None:
                raise CheckpointExecutionError("compiled module execution unsupported")
            attributes[key] = value
        if getattr(module, "gradient_checkpointing", False):
            raise CheckpointExecutionError("implicit HF checkpointing unsupported")
        if getattr(module, "rope_type", "default") != "default":
            raise CheckpointExecutionError("dynamic/nondefault RoPE unsupported")
        # Do not fingerprint the ephemeral attributes dict identity.
        state = [(key, freeze(attributes[key])) for key in sorted(attributes)]
        interface = None
        if isinstance(module, LlamaAttention):
            implementation = module.config._attn_implementation
            if type(implementation) is not str or implementation not in {
                "eager",
                "sdpa",
            }:
                raise CheckpointExecutionError("unreviewed attention route")
            try:
                attention = ALL_ATTENTION_FUNCTIONS.get_interface(
                    implementation, eager_attention_forward
                )
                mask = ALL_MASK_ATTENTION_FUNCTIONS[implementation]
            except KeyError as error:
                raise CheckpointExecutionError(
                    "missing selected attention/mask route"
                ) from error
            if not isinstance(attention, types.FunctionType) or not isinstance(
                mask, types.FunctionType
            ):
                raise CheckpointExecutionError("unsupported attention/mask callable")
            interface = [
                implementation,
                freeze(attention),
                freeze(mask),
                attention_dependencies(implementation, attention, freeze),
            ]
        records.append(
            [
                root_name,
                name,
                id(module),
                id(type(module)),
                id(type(module).forward),
                [
                    (key, id(getattr(type(module), key)))
                    for key in (
                        "__call__",
                        "_call_impl",
                        "_wrapped_call_impl",
                        "__getattribute__",
                    )
                ],
                freeze(module.forward),
                interface,
                _factor_dependencies(module, freeze, factor_classes),
                _loss_dependencies(module, freeze),
                state,
            ]
        )
    digest = hashlib.sha256()
    total = 0
    encoder = json.JSONEncoder(
        ensure_ascii=True, allow_nan=False, separators=(",", ":")
    )
    for chunk in encoder.iterencode(records):
        raw = chunk.encode("utf-8")
        total += len(raw)
        if total > 16 * 1024 * 1024:
            raise CheckpointExecutionError("serialized state bound exceeded")
        digest.update(raw)
    return digest.hexdigest()
