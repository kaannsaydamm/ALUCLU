"""Read-only start inspection for the prospective single-wrapper E3 executor.

Caller owns authenticated, quiescent host/runtime/schedule exclusively. This
does not authenticate assets/tokenizer, admit resources, forward, create an
optimizer or authorize a GPU run. CPU substituted hosts prove checks only.
Seed reconstruction and digesting allocate bounded factor copies, not a base.
Returned hashes describe this instant, not a lock or later-state certificate.
"""

from dataclasses import dataclass
from functools import partial

import torch

from .checkpoint_execution import (
    CheckpointController,
    CheckpointExecutionError,
    _digest,
)
from .checkpoint_fidelity import CheckpointFidelityError, compare_tensor
from .checkpoint_inventory import _wrapper_fingerprint
from .checkpoint_observation import _base_digest
from .checkpoint_parity_factory import PARITY_SEED
from .reference_qv_artifact import ReferenceArtifactError, reference_bindings
from .reference_qv_lora import ReferenceQVLoRA
from .reference_stress_inputs import StressInputError, stress_schedule_sha256


class StressStartError(ValueError):
    """The supplied state is not a fresh E3 engineering start."""


@dataclass(frozen=True)
class StressStart:
    device: str
    base_dtype: str
    factor_count: int
    parameter_count: int
    sequence_lengths: tuple[int, ...]
    base_digest: str
    factor_digest: str
    schedule_digest: str


def inspect_reference_stress_start(wrapper, schedule) -> StressStart:
    """Validate before optimizer creation; never clear gradients or repair state.

    Accept CPU FP32 for fake engineering only, or cuda:0 BF16 for separately
    admitted actual execution. Neither accepted device constitutes admission.
    Complete seeded A identity is checked, rather than just zero B/seed metadata.
    Existing enabled owned inventory must validate current computational state.
    """
    try:
        schedule_digest = stress_schedule_sha256(schedule)
        factors, base = reference_bindings(wrapper)
        _inventory(wrapper)
        device, dtype = base[0].device, base[0].dtype
        expected = torch.float32 if device.type == "cpu" else torch.bfloat16
        if (
            device not in (torch.device("cpu"), torch.device("cuda:0"))
            or dtype != expected
            or any(p.device != device or p.dtype != dtype for p in base)
            or any(p.device != device or p.grad is not None for p in factors.values())
            or any(
                b.device != device or b.requires_grad or b.layout != torch.strided
                for b in wrapper.base.buffers()
            )
        ):
            raise StressStartError(
                "single CPU FP32/cuda:0 BF16 base and clean masters required"
            )
        config = wrapper.base.config
        if (
            type(config.vocab_size) is not int
            or config.vocab_size != 49152
            or type(config.max_position_embeddings) is not int
            or config.max_position_embeddings < 4096
        ):
            raise StressStartError("pinned vocabulary and common4096 capacity required")
        if (
            wrapper.reference.initialization_seed != PARITY_SEED
            or not torch.is_grad_enabled()
            or torch.is_inference_mode_enabled()
            or torch.is_autocast_enabled(device.type)
            or torch.get_default_device() != torch.device("cpu")
        ):
            raise StressStartError(
                "fixed seed and explicit ordinary grad context required"
            )
        fresh = ReferenceQVLoRA(seed=PARITY_SEED)
        for name, original in fresh.named_parameters():
            compare_tensor(original.detach(), factors[name].detach().cpu(), exact=True)
        return StressStart(
            str(device),
            str(dtype),
            len(factors),
            sum(p.numel() for p in factors.values()),
            tuple(len(item.input_ids) for item in schedule.inputs),
            _base_digest(wrapper.base),
            _digest(tuple(factors.items())),
            schedule_digest,
        )
    except (
        StressInputError,
        ReferenceArtifactError,
        CheckpointExecutionError,
        CheckpointFidelityError,
    ) as exc:
        raise StressStartError(
            "invalid schedule, ownership or checkpoint inventory"
        ) from exc


def _inventory(wrapper):
    controller = wrapper.__dict__.get("_checkpoint_controller")
    if type(controller) is not CheckpointController:
        raise StressStartError("owned exact controller required")
    getter = controller.state_fingerprint_getter
    if not (
        type(getter) is partial
        and getter.func is _wrapper_fingerprint
        and len(getter.args) == 1
        and getter.args[0] is wrapper
        and not getter.keywords
    ):
        raise StressStartError("existing owned computational inventory required")
    getter()
