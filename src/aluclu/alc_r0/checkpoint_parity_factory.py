"""Fresh D parity arms over one caller-supplied frozen host; no model loader.

The caller authenticates host/assets/source and exclusively owns quiescent state.
Construction is not actual-host parity, resource fit or training authority.
"""

import torch
from torch import nn

from .host import VerifiedHost
from .host_wrapper import PinnedLlamaCapsuleWrapper
from .matched_lora import MatchedQProjLoRA, PinnedLlamaLoRAWrapper
from .research_capsule import ALLOWED_PORTS, ALLOWED_RANKS, ResearchCapsuleV0

PARITY_SEED = 20260916


def _base_device(host):
    if type(host) is not VerifiedHost:
        raise ValueError("exact caller-verified host required")
    base = host.model
    if not isinstance(base, nn.Module):
        raise ValueError("verified host must retain its module base")
    parameters = tuple(base.parameters())
    if (
        not parameters
        or any(module.training for module in base.modules())
        or any(p.requires_grad or p.grad is not None for p in parameters)
        or type(host.parameter_count) is not int
        or host.parameter_count != sum(p.numel() for p in parameters)
        or type(host.trainable_parameter_count) is not int
        or host.trainable_parameter_count != 0
    ):
        raise ValueError("existing completely frozen eval base required")
    device = parameters[0].device
    dtype = torch.float32 if device.type == "cpu" else torch.bfloat16
    if device.type not in {"cpu", "cuda"} or any(
        p.device != device or p.dtype != dtype or p.layout != torch.strided
        for p in parameters
    ):
        raise ValueError("D requires one CPU FP32 or CUDA BF16 base")
    if any(
        buffer.device != device
        or buffer.requires_grad
        or buffer.layout != torch.strided
        for buffer in base.buffers()
    ):
        raise ValueError("base buffers must be dense, frozen and on the same device")
    if torch.get_default_device() != torch.device("cpu"):
        raise ValueError("CPU default device required for seeded factor construction")
    return device


def make_parity_wrapper(host, checkpoint, *, arm, ports, rank, state):
    """Build one fresh wrapper with deterministic independent master factors.

    Use a partial of this function as the accumulation-pair factory. Calls never
    load/copy a base, execute forward/backward or step an optimizer. Repeated
    calls share only the supplied base, not factors/controllers. The nonzero B
    pattern is constructed in CPU FP32 before moving masters to the base device.
    Zero means original seeded A/B0, NOT the all-factors-zero control.
    """
    if (
        type(arm) is not str
        or arm not in {"capsule", "q_lora"}
        or type(state) is not str
        or state not in {"zero", "nonzero"}
        or type(ports) is not tuple
        or ports not in ALLOWED_PORTS
        or any(type(port) is not int for port in ports)
        or type(rank) is not int
        or rank not in ALLOWED_RANKS
        or type(checkpoint) is not bool
    ):
        raise ValueError("exact D arm/grid/state/checkpoint arguments required")
    device = _base_device(host)
    factor_cls = ResearchCapsuleV0 if arm == "capsule" else MatchedQProjLoRA
    factors = factor_cls(ports=ports, rank=rank, seed=PARITY_SEED)
    if state == "nonzero":
        with torch.no_grad():
            for block in factors.factors.values():
                values = (torch.arange(block.B.numel()) % 17 - 8).float() * 1e-4
                block.B.copy_(values.reshape(block.B.shape))
    factors.to(device=device, dtype=torch.float32)
    wrapper_cls = (
        PinnedLlamaCapsuleWrapper if arm == "capsule" else PinnedLlamaLoRAWrapper
    )
    wrapper = wrapper_cls(host)
    wrapper.train()
    if arm == "capsule":
        wrapper.mount(factors)
    else:
        wrapper.mount_lora(factors)
    if checkpoint:
        wrapper.enable_checkpoint_inventory()
    return wrapper
