"""Reference factor math for the preregistered, same-base R0 capsule.

This module contains no host wrapper, trainer, serializer, or authorization gate.
Its parameters are research-only until those independent contracts are proven.
"""

from __future__ import annotations

import math
from typing import cast

import torch
from torch import nn
from torch.nn import functional as F

CANONICAL_WIDTH = 576
ALLOWED_PORTS = ((14,), (29,), (14, 29))
ALLOWED_RANKS = (4, 8, 16)
NORMALIZATION_EPSILON = 1e-5


class _PortFactors(nn.Module):
    def __init__(self, rank: int, generator: torch.Generator) -> None:
        super().__init__()
        self.A = nn.Parameter(torch.empty(rank, CANONICAL_WIDTH, dtype=torch.float32))
        self.B = nn.Parameter(torch.zeros(CANONICAL_WIDTH, rank, dtype=torch.float32))
        nn.init.kaiming_uniform_(self.A, a=math.sqrt(5), generator=generator)


class ResearchCapsuleV0(nn.Module):
    """Explicit post-block residual factors for one frozen R0 grid entry."""

    def __init__(self, *, ports: tuple[int, ...], rank: int, seed: int) -> None:
        super().__init__()
        if ports not in ALLOWED_PORTS:
            raise ValueError("ports are outside the preregistered R0 grid")
        if isinstance(rank, bool) or rank not in ALLOWED_RANKS:
            raise ValueError("rank is outside the preregistered R0 grid")
        if isinstance(seed, bool) or not isinstance(seed, int) or not 0 <= seed < 2**63:
            raise ValueError("seed must be a nonnegative signed 63-bit integer")

        self.ports = ports
        self.rank = rank
        self.initialization_seed = seed
        self.control_kind = "trainable_init"
        generator = torch.Generator(device="cpu").manual_seed(seed)
        self.factors = nn.ModuleDict(
            {str(port): _PortFactors(rank, generator) for port in ports}
        )

    @classmethod
    def zero_control(
        cls, *, ports: tuple[int, ...], rank: int
    ) -> ResearchCapsuleV0:
        """Build the distinct never-trained P6 all-positive-zero control."""

        capsule = cls(ports=ports, rank=rank, seed=0)
        with torch.no_grad():
            for parameter in capsule.parameters():
                parameter.zero_()
                parameter.requires_grad_(False)
        capsule.control_kind = "all_factors_zero"
        return capsule

    def apply_port(self, port: int, hidden: torch.Tensor) -> torch.Tensor:
        """Return h + B(A(RMS(h))) with FP32 math and host-dtype residual."""

        if port not in self.ports:
            raise ValueError("port is not mounted in this capsule")
        if hidden.ndim != 3 or hidden.shape[-1] != CANONICAL_WIDTH:
            raise ValueError("hidden state must have [batch, sequence, 576] shape")
        if hidden.dtype not in (torch.float32, torch.bfloat16):
            raise ValueError("hidden state must be FP32 or BF16")

        factors = cast(_PortFactors, self.factors[str(port)])
        if factors.A.dtype != torch.float32 or factors.B.dtype != torch.float32:
            raise ValueError("capsule factors must remain FP32")
        if factors.A.device != hidden.device or factors.B.device != hidden.device:
            raise ValueError("capsule factors and hidden state must share a device")

        with torch.autocast(device_type=hidden.device.type, enabled=False):
            fp32 = hidden.float()
            normalized = fp32 / torch.sqrt(
                fp32.square().mean(dim=-1, keepdim=True) + NORMALIZATION_EPSILON
            )
            low_rank = F.linear(normalized, factors.A)
            delta = F.linear(low_rank, factors.B)
        return hidden + delta.to(dtype=hidden.dtype)
