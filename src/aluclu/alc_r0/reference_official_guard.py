"""Read-only q/v official-phase mount guard; no forward or launch authority.

Caller owns quiescent authenticated base and independently checks its complete
bytes/configuration between rows. This guard checks mounts and masters only;
it is neither a host certificate nor the complete 72-row qualification suite.
"""

import math

import torch

from .checkpoint_execution import _digest
from .checkpoint_observation import _roster_stamp
from .checkpoint_parity_factory import PARITY_SEED
from .reference_qv_artifact import _live_factors, _storage
from .reference_qv_lora import ReferenceQVLoRA
from .reference_qv_wrapper import PinnedLlamaQVReferenceWrapper


class ReferencePhaseGuard:
    """Snapshot exact seeded A/B0 or declared B=.01 witness in eval mode.

    Factors must be ordinary versioned tensors, even if subsequent checks occur
    inside inference_mode. No mutation, gradient clearing or repair is performed.
    Byte-equivalent replacement and shared factor/base storage are rejected.
    """

    def __init__(self, wrapper, base, *, mounted, expected_b=0.0):
        if (
            type(wrapper) is not PinnedLlamaQVReferenceWrapper
            or type(mounted) is not bool
            or type(expected_b) is not float
            or expected_b not in (0.0, 0.01)
            or math.copysign(1.0, expected_b) < 0
            or (not mounted and expected_b != 0.0)
        ):
            raise ValueError("exact q/v official-phase arguments required")
        self.wrapper, self.base = wrapper, base
        self.mounted, self.expected_b = mounted, expected_b
        self.factor = wrapper.reference
        self.snapshot = self._state()
        if mounted:
            # Private CPU generator does not alter caller RNG. Reconstruct only
            # bounded masters, never copy/load a base or execute a model.
            with torch.inference_mode(False):
                fresh = ReferenceQVLoRA(seed=PARITY_SEED)
            actual = _live_factors(self.factor)
            for name, original in fresh.named_parameters():
                if name.endswith(".A") and not torch.equal(
                    original.detach().view(torch.uint8),
                    actual[name].detach().cpu().contiguous().view(torch.uint8),
                ):
                    raise ValueError("original seeded A bytes required")

    def _state(self):
        wrapper = self.wrapper
        if (
            wrapper.base is not self.base
            or any(module.training for module in wrapper.modules())
            or wrapper.capsule is not None
            or getattr(wrapper, "lora", None) is not None
        ):
            raise ValueError("one eval base and no co-mount required")
        wrapper._assert_checkpoint_mutation_allowed()
        base_parameters = tuple(self.base.parameters())
        if not base_parameters or any(
            p.requires_grad or p.grad is not None for p in base_parameters
        ):
            raise ValueError("frozen gradient-free base required")
        device = base_parameters[0].device
        dtype = torch.float32 if device.type == "cpu" else torch.bfloat16
        base_tensors = base_parameters + tuple(self.base.buffers())
        if device not in (torch.device("cpu"), torch.device("cuda:0")) or any(
            p.device != device
            or p.layout != torch.strided
            or p.requires_grad
            or (p.is_floating_point() and p.dtype != dtype)
            for p in base_tensors
        ):
            raise ValueError("one CPU FP32/cuda:0 BF16 base required")
        if not self.mounted:
            if wrapper.reference is not None:
                raise ValueError("absent effective reference mount required")
            return None
        if (
            wrapper.reference is not self.factor
            or type(self.factor) is not ReferenceQVLoRA
            or type(self.factor.initialization_seed) is not int
            or self.factor.initialization_seed != PARITY_SEED
        ):
            raise ValueError("original exact reference identity and seed required")
        named = tuple(_live_factors(self.factor).items())
        base_storages = {_storage(p) for p in base_tensors}
        for name, parameter in named:
            if (
                parameter.device != device
                or parameter.grad is not None
                or parameter.is_inference()
                or _storage(parameter) in base_storages
            ):
                raise ValueError("ordinary clean independently owned masters required")
            if name.endswith(".B") and not torch.equal(
                parameter.detach().contiguous().view(torch.uint8),
                torch.full_like(parameter, self.expected_b).view(torch.uint8),
            ):
                raise ValueError("exact declared phase B bytes required")
        return _roster_stamp(named), _digest(named)

    def check(self):
        if self._state() != self.snapshot:
            raise ValueError("reference bytes or bindings changed during phase")
