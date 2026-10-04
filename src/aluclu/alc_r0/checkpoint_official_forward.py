"""Fixed official-forward regression over one supplied frozen host.

No loader, launcher, checkpoint session, optimizer, dataset or launch authority.
Keep original no-mount cases and exercise them in both arms/all grids for zero
initialization and detach. Actual host/source/runtime/assets, deterministic GPU
settings, two fresh-process reproducibility and resource limits are external.
"""

import hashlib
import re
from dataclasses import dataclass

import torch

from .checkpoint_execution import _digest
from .checkpoint_observation import _base_digest, _roster_stamp
from .checkpoint_parity_factory import PARITY_SEED, _base_device, make_parity_wrapper
from .checkpoint_parity_matrix import PARITY_CELLS
from .host_wrapper import PinnedLlamaCapsuleWrapper
from .matched_lora import MatchedQProjLoRA, PinnedLlamaLoRAWrapper
from .research_capsule import ResearchCapsuleV0


@dataclass(frozen=True)
class ForwardCase:
    batch: int
    length: int
    padding_side: str
    explicit_positions: bool
    cached: bool = False


FORWARD_CASES = tuple(
    [
        ForwardCase(1, n, "none", explicit)
        for n in (1, 8, 127, 512)
        for explicit in (False, True)
    ]
    + [
        ForwardCase(2, n, side, explicit)
        for n in (8, 127, 512)
        for side in ("left", "right")
        for explicit in (False, True)
    ]
    + [ForwardCase(1, n, "none", False, True) for n in (1, 8, 127, 512)]
)


@dataclass(frozen=True)
class OfficialKey:
    grid_id: str
    arm: str
    phase: str


@dataclass(frozen=True)
class OfficialCase:
    key: OfficialKey
    case: ForwardCase
    official_sha256: str
    wrapper_sha256: str
    incremental_official_sha256: str | None
    incremental_wrapper_sha256: str | None


@dataclass(frozen=True)
class NonzeroWitness:
    grid_id: str
    arm: str
    official_sha256: str
    mounted_sha256: str


@dataclass(frozen=True)
class OfficialSuite:
    source_device: str
    source_dtype: str
    base_digest: str
    cases: tuple[OfficialCase, ...]
    nonzero_witnesses: tuple[NonzeroWitness, ...]


@dataclass(frozen=True)
class OfficialFailure:
    completed: tuple[OfficialCase, ...]
    current: tuple[OfficialKey, ForwardCase]
    unrun: tuple[tuple[OfficialKey, ForwardCase], ...]
    nonzero_witnesses: tuple[NonzeroWitness, ...]
    stage: str


class OfficialForwardError(RuntimeError):
    def __init__(self, failure):
        super().__init__(f"terminal official-forward error at {failure.current}")
        self.failure = failure


class OfficialForwardInterrupted(KeyboardInterrupt):
    def __init__(self, failure):
        super().__init__(f"official-forward interrupted at {failure.current}")
        self.failure = failure


def _inputs(case, device):
    full = torch.arange(1, case.length + 1, dtype=torch.long, device=device)
    if case.batch == 1:
        ids, mask = full.unsqueeze(0), None
    else:
        short = torch.arange(
            100, 100 + case.length // 2, dtype=torch.long, device=device
        )
        pad = torch.zeros(case.length - len(short), dtype=torch.long, device=device)
        padded = (
            torch.cat((pad, short))
            if case.padding_side == "left"
            else torch.cat((short, pad))
        )
        ids = torch.stack((full, padded))
        mask = ids.ne(0).long()
    positions = (
        torch.arange(case.length, dtype=torch.long, device=device)
        .unsqueeze(0)
        .expand(case.batch, -1)
        if case.explicit_positions
        else None
    )
    return ids, mask, positions


def _tensor_digest(tensor):
    return hashlib.sha256(
        tensor.detach().contiguous().cpu().view(torch.uint8).numpy().tobytes()
    ).hexdigest()


def _valid_logits(tensor, shape, device):
    dtype = torch.float32 if device.type == "cpu" else torch.bfloat16
    if (
        not isinstance(tensor, torch.Tensor)
        or tensor.layout != torch.strided
        or tuple(tensor.shape) != (*shape, 49152)
        or tensor.dtype != dtype
        or tensor.device != device
        or tensor.requires_grad
        or not torch.isfinite(tensor).all().item()
    ):
        raise ValueError(
            "finite correctly shaped/device/dtype inference logits required"
        )


def _compare_logits(official, wrapped, shape, device, exact):
    _valid_logits(official, shape, device)
    _valid_logits(wrapped, shape, device)
    if exact:
        if not torch.equal(
            official.contiguous().view(torch.uint8),
            wrapped.contiguous().view(torch.uint8),
        ):
            raise ValueError("CPU official logits must be bitwise equal")
    elif not torch.allclose(wrapped, official, rtol=1e-3, atol=1e-3):
        raise ValueError("GPU official logits fixed tolerance failed")
    if not torch.equal(wrapped.argmax(-1), official.argmax(-1)):
        raise ValueError("official/wrapper argmax mismatch")
    return _tensor_digest(official), _tensor_digest(wrapped)


def _cache_pair(official, wrapped, length):
    if official is None or wrapped is None or official is wrapped:
        raise ValueError("distinct nonempty official/wrapper caches required")
    lengths = (official.get_seq_length(), wrapped.get_seq_length())
    if any(type(value) is not int or value != length for value in lengths):
        raise ValueError("both caches must retain the exact sequence length")


def _case(wrapper, key, case, *, exact):
    device = next(wrapper.base.parameters()).device
    ids, mask, positions = _inputs(case, device)
    arguments = dict(
        input_ids=ids,
        attention_mask=mask,
        position_ids=positions,
        use_cache=case.cached,
    )
    official, wrapped = wrapper.base(**arguments), wrapper(**arguments)
    first = _compare_logits(
        official.logits, wrapped.logits, tuple(ids.shape), device, exact
    )
    incremental = (None, None)
    if not case.cached:
        if official.past_key_values is not None or wrapped.past_key_values is not None:
            raise ValueError("cache-free forward returned a cache")
    else:
        _cache_pair(official.past_key_values, wrapped.past_key_values, case.length)
        next_ids = torch.tensor([[42]], dtype=torch.long, device=device)
        next_mask = torch.ones((1, case.length + 1), dtype=torch.long, device=device)
        official_next = wrapper.base(
            input_ids=next_ids,
            attention_mask=next_mask,
            past_key_values=official.past_key_values,
            use_cache=True,
        )
        wrapped_next = wrapper(
            input_ids=next_ids,
            attention_mask=next_mask,
            past_key_values=wrapped.past_key_values,
            use_cache=True,
        )
        incremental = _compare_logits(
            official_next.logits, wrapped_next.logits, (1, 1), device, exact
        )
        _cache_pair(
            official_next.past_key_values, wrapped_next.past_key_values, case.length + 1
        )
    return OfficialCase(key, case, *first, *incremental)


def _nonzero_witness(wrapper, device):
    ids = torch.tensor([[10, 20, 30]], dtype=torch.long, device=device)
    official = wrapper.base(input_ids=ids, use_cache=False)
    mounted = wrapper(input_ids=ids, use_cache=False)
    _valid_logits(official.logits, (1, 3), device)
    _valid_logits(mounted.logits, (1, 3), device)
    if torch.equal(official.logits, mounted.logits):
        raise ValueError("nonzero mounted witness must change official logits")
    return _tensor_digest(official.logits), _tensor_digest(mounted.logits)


class _PhaseGuard:
    """Observe declared mounts and ordinary versioned factor state, not logits alone."""

    def __init__(self, wrapper, base, cell, *, mounted, expected_b=0.0):
        self.wrapper, self.base, self.cell = wrapper, base, cell
        self.mounted, self.expected_b = mounted, expected_b
        self.factor = wrapper.capsule if cell.arm == "capsule" else wrapper.lora
        self.snapshot = self._state()

    def _state(self):
        wrapper, cell = self.wrapper, self.cell
        if wrapper.base is not self.base or any(m.training for m in wrapper.modules()):
            raise ValueError("fixed one-base eval wrapper phase required")
        capsule, lora = wrapper.capsule, getattr(wrapper, "lora", None)
        factor, other = (capsule, lora) if cell.arm == "capsule" else (lora, capsule)
        if other is not None or (not self.mounted and factor is not None):
            raise ValueError("absent effective mount required for this phase")
        if not self.mounted:
            return None
        factor_class = ResearchCapsuleV0 if cell.arm == "capsule" else MatchedQProjLoRA
        if factor is not self.factor or type(factor) is not factor_class:
            raise ValueError("original exact factor module identity required")
        if (
            factor.ports != cell.ports
            or type(factor.rank) is not int
            or factor.rank != cell.rank
            or type(factor.initialization_seed) is not int
            or factor.initialization_seed != PARITY_SEED
        ):
            raise ValueError("fixed factor grid/rank/seed required")
        named = tuple(factor.named_parameters())
        names = tuple(
            f"factors.{port}.{role}" for port in cell.ports for role in ("A", "B")
        )
        if tuple(name for name, _ in named) != names or tuple(factor.buffers()):
            raise ValueError(
                "complete canonical factor roster without buffers required"
            )
        device = next(self.base.parameters()).device
        for name, parameter in named:
            shape = (cell.rank, 576) if name.endswith(".A") else (576, cell.rank)
            if (
                tuple(parameter.shape) != shape
                or parameter.dtype != torch.float32
                or parameter.device != device
                or not parameter.requires_grad
                or parameter.grad is not None
                or parameter.is_inference()
                or not torch.isfinite(parameter).all().item()
            ):
                raise ValueError(
                    "ordinary finite FP32 factors in eval/no-gradient state required"
                )
            if name.endswith(".B") and (
                not torch.equal(parameter, torch.full_like(parameter, self.expected_b))
                or (self.expected_b == 0.0 and torch.signbit(parameter).any().item())
            ):
                raise ValueError("fixed phase B values required")
        return _roster_stamp(named), _digest(named)

    def check(self):
        if self._state() != self.snapshot:
            raise ValueError("factor bytes/bindings changed during official phase")


def _prepare(host, cell, phase):
    # Factors must be normal tensors with version counters even though only
    # subsequent forward execution uses inference_mode.
    with torch.inference_mode(False):
        wrapper = make_parity_wrapper(
            host, False, arm=cell.arm, ports=cell.ports, rank=cell.rank, state="zero"
        )
    wrapper.eval()
    if (
        type(wrapper)
        is not (
            PinnedLlamaCapsuleWrapper
            if cell.arm == "capsule"
            else PinnedLlamaLoRAWrapper
        )
        or wrapper.base is not host.model
    ):
        raise ValueError("exact fresh wrapper over one base required")
    factors = wrapper.capsule if cell.arm == "capsule" else wrapper.lora
    _PhaseGuard(wrapper, host.model, cell, mounted=True).check()
    original_a = _digest(
        tuple(
            (name, p) for name, p in factors.named_parameters() if name.endswith(".A")
        )
    )
    if phase == "detached":
        # Existing official detach witness uses fixed B=.125, NOT the D parity
        # nonzero-state pattern and not a learned/trained artifact.
        with torch.no_grad():
            for name, parameter in factors.named_parameters():
                if name.endswith(".B"):
                    parameter.fill_(0.125)
    if phase == "unmounted":
        wrapper.detach()
        if (wrapper.capsule if cell.arm == "capsule" else wrapper.lora) is not None:
            raise ValueError("detach must remove the effective factor mount")
    return wrapper, original_a


def _receipt(result, key, case):
    if type(result) is not OfficialCase or result.key != key or result.case != case:
        raise ValueError("typed schedule-associated official receipt required")
    digests = (result.official_sha256, result.wrapper_sha256)
    incremental = (
        result.incremental_official_sha256,
        result.incremental_wrapper_sha256,
    )
    if case.cached:
        digests += incremental
    elif incremental != (None, None):
        raise ValueError("cache-free receipt cannot claim incremental results")
    if any(
        type(value) is not str or not re.fullmatch(r"[0-9a-f]{64}", value)
        for value in digests
    ):
        raise ValueError("canonical SHA256 receipt digests required")


def run_official_forward_suite(host, *, exact):
    """Run all fixed grid/arm/phase cases without skip/retry or base copies.

    Parent owns durable journal, launch permission, source/runtime authentication,
    wall ceiling and two fresh GPU-process comparison. Preserve old workers/tests;
    this returns small digest-only observations, not a model/capability receipt.
    """
    if type(exact) is not bool:
        raise ValueError("exact boolean required")
    device = _base_device(host)
    if exact != (device.type == "cpu"):
        raise ValueError("CPU exact/GPU fixed tolerance mode required")
    base = host.model
    signature = (
        _base_digest(base),
        _roster_stamp(base.named_parameters()),
        _roster_stamp(base.named_buffers()),
    )
    schedule = tuple(
        (OfficialKey(cell.grid_id, cell.arm, phase), case)
        for cell in PARITY_CELLS
        for phase in ("unmounted", "zero", "detached")
        for case in FORWARD_CASES
    )
    completed, witnesses = [], []
    current_phase, wrapper, guard = None, None, None
    original_a = {}

    def unchanged():
        if (
            host.model is not base
            or _base_device(host) != device
            or (
                _base_digest(base),
                _roster_stamp(base.named_parameters()),
                _roster_stamp(base.named_buffers()),
            )
            != signature
        ):
            raise ValueError(
                "one byte-identical frozen base required throughout official suite"
            )

    with torch.inference_mode():
        for index, (key, case) in enumerate(schedule):
            stage, attempted = "case-preflight", False
            try:
                unchanged()
                if current_phase != key:
                    # Never retain the old wrapper/factors while building the next.
                    guard, wrapper = None, None
                    cell = PARITY_CELLS[index // (3 * len(FORWARD_CASES))]
                    stage = "preparation"
                    wrapper, a_digest = _prepare(host, cell, key.phase)
                    if (
                        cell.grid_id in original_a
                        and original_a[cell.grid_id] != a_digest
                    ):
                        raise ValueError(
                            "identical original seeded A across phases/arms required"
                        )
                    original_a[cell.grid_id] = a_digest
                    unchanged()
                    if key.phase == "detached":
                        stage = "witness"
                        witness_guard = _PhaseGuard(
                            wrapper, base, cell, mounted=True, expected_b=0.125
                        )
                        witness = NonzeroWitness(
                            cell.grid_id, cell.arm, *_nonzero_witness(wrapper, device)
                        )
                        witness_guard.check()
                        unchanged()
                        witnesses.append(witness)
                        witness_guard = None
                        stage = "detach"
                        wrapper.detach()
                    guard = _PhaseGuard(
                        wrapper, base, cell, mounted=key.phase == "zero"
                    )
                    current_phase = key
                stage = "case-preflight"
                guard.check()
                stage, attempted = "case", True
                result = _case(wrapper, key, case, exact=exact)
                stage = "case-validation"
                unchanged()
                guard.check()
                _receipt(result, key, case)
                completed.append(result)
            except KeyboardInterrupt as exc:
                raise OfficialForwardInterrupted(
                    OfficialFailure(
                        tuple(completed),
                        (key, case),
                        schedule[index + int(attempted) :],
                        tuple(witnesses),
                        stage,
                    )
                ) from exc
            except Exception as exc:
                raise OfficialForwardError(
                    OfficialFailure(
                        tuple(completed),
                        (key, case),
                        schedule[index + int(attempted) :],
                        tuple(witnesses),
                        stage,
                    )
                ) from exc
    return OfficialSuite(
        str(device),
        str(next(base.parameters()).dtype),
        signature[0],
        tuple(completed),
        tuple(witnesses),
    )
