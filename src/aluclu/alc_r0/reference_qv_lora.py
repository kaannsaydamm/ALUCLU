"""Factor/projection substrate for the separately reported all-layer reference.

Not a host wrapper, checkpoint guard, serializer, or training authority. This
larger q+v reference is not the parameter-matched capsule comparator.
"""

from __future__ import annotations

import math
from collections.abc import Callable

import torch
from torch import nn
from torch.nn import functional as F


class _ProjectionFactors(nn.Module):
    def __init__(self, output_width: int, generator: torch.Generator) -> None:
        super().__init__()
        self.A = nn.Parameter(torch.empty(8, 576, dtype=torch.float32, device="cpu"))
        self.B = nn.Parameter(
            torch.zeros(output_width, 8, dtype=torch.float32, device="cpu")
        )
        nn.init.kaiming_uniform_(self.A, a=math.sqrt(5), generator=generator)


class ReferenceQVLoRA(nn.Module):
    """Fixed rank-8 q+v factors for all 30 pinned SmolLM2-135M blocks.

    FP32 masters, private CPU initialization, alpha/rank=1; no base mutation.
    Binding captures references, not an integrity snapshot. Host checkpoint
    execution must separately guard captured bindings and in-flight mutations.
    """

    def __init__(self, *, seed: int) -> None:
        super().__init__()
        if isinstance(seed, bool) or not isinstance(seed, int) or not 0 <= seed < 2**63:
            raise ValueError("seed must be a nonnegative signed 63-bit integer")
        self.initialization_seed = seed
        generator = torch.Generator(device="cpu").manual_seed(seed)
        self.factors = nn.ModuleDict(
            {
                str(layer): nn.ModuleDict(
                    {
                        "q": _ProjectionFactors(576, generator),
                        "v": _ProjectionFactors(192, generator),
                    }
                )
                for layer in range(30)
            }
        )

    def bind_projection(
        self, *, layer: int, target: str, base: nn.Linear
    ) -> Callable[[torch.Tensor], torch.Tensor]:
        """Explicit projection operation; never replace/patch the base module."""

        if isinstance(layer, bool) or not isinstance(layer, int) or not 0 <= layer < 30:
            raise ValueError("layer must be an integer in [0, 29]")
        if target not in ("q", "v"):
            raise ValueError("reference target must be q or v")
        output_width = 576 if target == "q" else 192
        if (
            not isinstance(base, nn.Linear)
            or base.in_features != 576
            or base.out_features != output_width
            or base.bias is not None
            or any(parameter.requires_grad for parameter in base.parameters())
        ):
            raise ValueError("base must be a frozen bias-free pinned projection")
        factors = self.factors[str(layer)][target]
        factor_a, factor_b = factors.A, factors.B

        def project(hidden_states: torch.Tensor) -> torch.Tensor:
            if (
                hidden_states.ndim < 1
                or hidden_states.shape[-1] != 576
                or not hidden_states.is_floating_point()
                or hidden_states.device != base.weight.device
                or hidden_states.dtype != base.weight.dtype
                or factor_a.device != hidden_states.device
                or factor_b.device != hidden_states.device
                or factor_a.dtype != torch.float32
                or factor_b.dtype != torch.float32
                or factor_a.shape != (8, 576)
                or factor_b.shape != (output_width, 8)
                or base.weight.requires_grad
            ):
                raise ValueError("projection input/base/factor contract changed")
            result = base(hidden_states)
            with torch.autocast(device_type=hidden_states.device.type, enabled=False):
                delta = F.linear(F.linear(hidden_states.float(), factor_a), factor_b)
            return result + delta.to(dtype=result.dtype)

        return project
