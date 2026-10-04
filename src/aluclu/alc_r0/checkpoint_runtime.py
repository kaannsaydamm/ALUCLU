"""Read enumerated backend settings; no RNG/autocast/grad-context snapshot.

This does not freeze native runtime code, all backend policy, or other threads.
Getter calls inspect settings only, not CUDA capability or model execution.
"""

import types

import torch

from .checkpoint_execution import CheckpointExecutionError


def read_runtime_state():
    """Return scalar settings and getter bindings for the pinned runtime schema."""
    getters = {
        "default_dtype": torch.get_default_dtype,
        "default_device": torch.get_default_device,
        "matmul_precision": torch.get_float32_matmul_precision,
        "deterministic": torch.are_deterministic_algorithms_enabled,
        "warn_only": torch.is_deterministic_algorithms_warn_only_enabled,
        "threads": torch.get_num_threads,
        "interop_threads": torch.get_num_interop_threads,
    }
    for name in (
        "flash_sdp_enabled",
        "math_sdp_enabled",
        "mem_efficient_sdp_enabled",
        "cudnn_sdp_enabled",
        "fp16_bf16_reduction_math_sdp_allowed",
    ):
        getters[f"cuda.{name}"] = getattr(torch.backends.cuda, name)
    values = {}
    for name, getter in getters.items():
        if not isinstance(getter, (types.FunctionType, types.BuiltinFunctionType)):
            raise CheckpointExecutionError("unsupported runtime getter")
        values[name] = getter()
    for name in (
        "allow_tf32",
        "allow_fp16_reduced_precision_reduction",
        "allow_bf16_reduced_precision_reduction",
    ):
        values[f"matmul.{name}"] = getattr(torch.backends.cuda.matmul, name)
    for name in ("enabled", "benchmark", "deterministic", "allow_tf32"):
        values[f"cudnn.{name}"] = getattr(torch.backends.cudnn, name)
    for name, value in values.items():
        if name == "default_dtype":
            valid = isinstance(value, torch.dtype)
        elif name == "default_device":
            valid = isinstance(value, torch.device)
        elif name == "matmul_precision":
            valid = type(value) is str and value in {"highest", "high", "medium"}
        elif name in {"threads", "interop_threads"}:
            valid = type(value) is int and 1 <= value <= 65536
        else:
            valid = type(value) is bool
        if not valid:
            raise CheckpointExecutionError(f"unsupported runtime setting: {name}")
    return values, getters
