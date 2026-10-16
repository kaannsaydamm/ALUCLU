"""Fixed D matrix over one supplied frozen host; no loader or launch authority.

Caller authenticates exact host/factory/source/tokenizer/runtime and owns the
quiescent invocation. CPU and GPU are separate invocations. This binding runs
all cells in original v1 order, without retries or skipped cells. Partial
receipts survive a terminal error; no synthetic comparison confers learning,
resource fit, official-forward regression or complete experiment acceptance.
"""

import math
from dataclasses import dataclass

from .checkpoint_execution import _digest
from .checkpoint_fidelity import TensorComparison
from .checkpoint_observation import _base_digest, _bindings, _roster_stamp
from .checkpoint_optimizer import AdamWComparison
from .checkpoint_parity_cell import (
    CaseComparison,
    ParityCell,
    _schedule,
    run_parity_cell,
)
from .checkpoint_parity_factory import PARITY_SEED, _base_device, make_parity_wrapper
from .host_wrapper import PinnedLlamaCapsuleWrapper
from .matched_lora import MatchedQProjLoRA, PinnedLlamaLoRAWrapper
from .research_capsule import ResearchCapsuleV0


@dataclass(frozen=True)
class CellKey:
    grid_id: str
    ports: tuple[int, ...]
    rank: int
    arm: str


PARITY_CELLS = tuple(
    CellKey(f"{prefix}-r{rank}", ports, rank, arm)
    for prefix, ports in (("M", (14,)), ("L", (29,)), ("ML", (14, 29)))
    for rank in (4, 8, 16)
    for arm in ("capsule", "q_lora")
)


@dataclass(frozen=True)
class MatrixCell:
    key: CellKey
    result: ParityCell


@dataclass(frozen=True)
class MatrixFailure:
    completed: tuple[MatrixCell, ...]
    current: CellKey
    unrun: tuple[CellKey, ...]


class ParityMatrixError(RuntimeError):
    def __init__(self, failure):
        super().__init__(f"terminal parity matrix error at {failure.current}")
        self.failure = failure


class ParityMatrixInterrupted(KeyboardInterrupt):
    def __init__(self, failure):
        super().__init__(f"parity matrix interrupted at {failure.current}")
        self.failure = failure


@dataclass(frozen=True)
class ParityMatrix:
    source_device: str
    source_dtype: str
    seed: int
    base_digest: str
    cells: tuple[MatrixCell, ...]


def _names(key):
    return tuple(f"factors.{port}.{role}" for port in key.ports for role in ("A", "B"))


def _receipt(result, key, base_digest):
    if (
        type(result) is not ParityCell
        or result.base_digest != base_digest
        or type(result.parameter_count) is not int
        or result.parameter_count != 1152 * key.rank * len(key.ports)
        or result.parameter_names != _names(key)
        or type(result.cases) is not tuple
        or len(result.cases) != 18
        or type(result.accumulation) is not AdamWComparison
        or type(result.accumulation.step) is not int
        or result.accumulation.step != 1
    ):
        raise ValueError("complete matched cell receipt required")
    for index, case in enumerate(result.cases):
        state, repeat = (("zero", 0), ("nonzero", 0), ("nonzero", 1))[index // 6]
        if (
            type(case) is not CaseComparison
            or case.state != state
            or type(case.repeat) is not int
            or case.repeat != repeat
            or type(case.fixture_index) is not int
            or case.fixture_index != index % 6
            or case.base_digest != base_digest
        ):
            raise ValueError("fixed cell case schedule/base receipt required")
        for pair in (case.losses, case.scores):
            if (
                type(pair) is not tuple
                or len(pair) != 2
                or any(
                    type(value) is not float or not math.isfinite(value)
                    for value in pair
                )
            ):
                raise ValueError("finite scalar case receipts required")
    for mapping in (
        result.accumulation.factors,
        result.accumulation.exp_avg,
        result.accumulation.exp_avg_sq,
    ):
        if (
            type(mapping) is not tuple
            or tuple(name for name, _ in mapping) != _names(key)
            or any(type(value) is not TensorComparison for _, value in mapping)
        ):
            raise ValueError("complete named AdamW comparison receipt required")
    if (
        type(result.pending_losses) is not tuple
        or len(result.pending_losses) != 2
        or any(
            type(value) is not float or not math.isfinite(value)
            for value in result.pending_losses
        )
    ):
        raise ValueError("finite pending loss receipt required")


def run_parity_matrix(host, fixtures, *, exact):
    """Compose the exact reviewed factory and cell, retaining only small receipts.

    No injectable execution/factory callback in production. Missing host/device,
    failure, OOM or interruption is not a skipped/PASS cell or retry. Launcher
    owns durable journaling, wall limit, budget/asset/source qualification and
    official-forward regressions; none is inferred from this returned matrix.
    """
    if type(exact) is not bool:
        raise ValueError("exact boolean required")
    _schedule(fixtures)
    device = _base_device(host)
    if exact != (device.type == "cpu"):
        raise ValueError("CPU exact/GPU fixed tolerance mode required")
    base = host.model
    signature = (
        _base_digest(base),
        _roster_stamp(base.named_parameters()),
        _roster_stamp(base.named_buffers()),
    )
    completed, original_a = [], {}

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
            raise ValueError("one unchanged frozen base required across matrix")

    for index, key in enumerate(PARITY_CELLS):
        try:
            unchanged()

            def factory(state, checkpoint):
                unchanged()
                wrapper = make_parity_wrapper(
                    host,
                    checkpoint,
                    arm=key.arm,
                    ports=key.ports,
                    rank=key.rank,
                    state=state,
                )
                expected_wrapper = (
                    PinnedLlamaCapsuleWrapper
                    if key.arm == "capsule"
                    else PinnedLlamaLoRAWrapper
                )
                expected_factors = (
                    ResearchCapsuleV0 if key.arm == "capsule" else MatchedQProjLoRA
                )
                owned_base, factors, named, _ = _bindings(wrapper, state)
                if (
                    type(wrapper) is not expected_wrapper
                    or type(factors) is not expected_factors
                    or owned_base is not base
                    or factors.ports != key.ports
                    or factors.rank != key.rank
                    or factors.initialization_seed != PARITY_SEED
                    or tuple(name for name, _ in named) != _names(key)
                    or sum(p.numel() for _, p in named)
                    != 1152 * key.rank * len(key.ports)
                ):
                    raise ValueError(
                        "exact parameter-matched pinned factory binding required"
                    )
                for name, parameter in named:
                    expected_shape = (
                        (key.rank, 576) if name.endswith(".A") else (576, key.rank)
                    )
                    if tuple(parameter.shape) != expected_shape:
                        raise ValueError(
                            "fixed D factor shapes required before comparison"
                        )
                a_digest = _digest(
                    tuple((name, p) for name, p in named if name.endswith(".A"))
                )
                if key.grid_id in original_a and original_a[key.grid_id] != a_digest:
                    raise ValueError("identical seeded A across capsule/LoRA required")
                original_a[key.grid_id] = a_digest
                unchanged()
                return wrapper

            result = run_parity_cell(factory, fixtures, exact=exact)
            unchanged()
            _receipt(result, key, signature[0])
            completed.append(MatrixCell(key, result))
        except KeyboardInterrupt as exc:
            raise ParityMatrixInterrupted(
                MatrixFailure(tuple(completed), key, PARITY_CELLS[index + 1 :])
            ) from exc
        except Exception as exc:
            raise ParityMatrixError(
                MatrixFailure(tuple(completed), key, PARITY_CELLS[index + 1 :])
            ) from exc
    return ParityMatrix(
        str(device),
        str(next(base.parameters()).dtype),
        PARITY_SEED,
        signature[0],
        tuple(completed),
    )
