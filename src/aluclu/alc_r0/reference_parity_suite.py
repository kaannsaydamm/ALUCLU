"""Fixed separate q/v cell binding; no loader or public execution callback.

Caller authenticates host/fixtures/source/runtime and admits inclusive resources.
Digest binding does not authenticate supplied metadata. This is disposable
synthetic parity, not task training, E3, learning or complete host qualification.
Cooperative exclusive ownership is required; failures are terminal, not rollback.
"""

from dataclasses import asdict, dataclass, replace
from weakref import WeakSet, ref

import torch

from .checkpoint_execution import CheckpointController, _digest
from .checkpoint_observation import _bindings
from .checkpoint_parity_cell import (
    SINGLE_SCHEDULE,
    CaseComparison,
    ParityCell,
    ParityCellError,
    ParityCellFailure,
    ParityCellInterrupted,
    _FactoryGuard,
    _schedule,
    run_parity_cell,
)
from .checkpoint_parity_factory import PARITY_SEED, make_reference_wrapper
from .reference_official_suite import _json_digest, _sha, _signature
from .reference_parity_receipt import (
    REFERENCE_NAMES,
    ReferenceParityIdentity,
    ReferenceParityReceipt,
    _pair,
    validate_reference_parity_receipt,
)
from .reference_qv_artifact import _live_factors
from .reference_qv_lora import ReferenceQVLoRA
from .reference_qv_wrapper import PinnedLlamaQVReferenceWrapper


@dataclass(frozen=True)
class ReferenceParityFailure:
    stage: str
    cell_failure: ParityCellFailure | None


class ReferenceParityError(RuntimeError):
    def __init__(self, failure):
        super().__init__(f"terminal q/v parity failure at {failure.stage}")
        self.failure = failure


class ReferenceParityInterrupted(KeyboardInterrupt):
    def __init__(self, failure):
        super().__init__(f"q/v parity interrupted at {failure.stage}")
        self.failure = failure


def _completed_progress(cell):
    """Retain only bounded scalar observations, even if final admission fails.

    This is shape/finite framing, not success validation. Invalid/corrupt
    observations are not copied into a supposedly bounded failure payload.
    """
    if (
        type(cell) is not ParityCell
        or type(cell.cases) is not tuple
        or len(cell.cases) != 18
    ):
        return None
    try:
        for expected, row in zip(SINGLE_SCHEDULE, cell.cases, strict=True):
            if (
                type(row) is not CaseComparison
                or type(row.state) is not str
                or type(row.repeat) is not int
                or type(row.fixture_index) is not int
                or (row.state, row.repeat, row.fixture_index) != expected
            ):
                return None
            _pair(row.losses, exact=False)
            _pair(row.scores, exact=False)
            _sha(row.base_digest)
            _sha(row.factor_digest)
        _pair(cell.pending_losses, exact=False)
    except ValueError:
        return None
    return ParityCellFailure("cell_returned", cell.cases, None, (), cell.pending_losses)


class _ReferenceFactory:
    def __init__(self, host, signature, exact):
        self.host, self.signature = host, signature
        self.base = host.model
        self.controllers = WeakSet()
        self.guard = _FactoryGuard(self._make, exact)
        self.cleanup_parameters = {}
        # Reconstruct only bounded private CPU masters, never host assets.
        original = ReferenceQVLoRA(seed=PARITY_SEED)
        named = tuple(_live_factors(original).items())
        self.digests = {"zero": _digest(named)}
        with torch.no_grad():
            for name, parameter in named:
                if name.endswith(".B"):
                    values = (
                        torch.arange(parameter.numel(), device="cpu") % 17 - 8
                    ).float() * 1e-4
                    parameter.copy_(values.reshape(parameter.shape))
        self.digests["nonzero"] = _digest(named)

    def unchanged(self):
        if self.host.model is not self.base or _signature(self.host) != self.signature:
            raise ValueError("one unchanged base/configuration/host identity required")

    def _make(self, state, checkpoint):
        self.unchanged()
        wrapper = make_reference_wrapper(self.host, checkpoint, state=state)
        if type(wrapper) is not PinnedLlamaQVReferenceWrapper:
            raise ValueError("exact q/v wrapper required")
        # Keep separate cleanup ownership BEFORE validation can throw. Do not
        # pre-register in the generic freshness guard (it would see a duplicate).
        # Never clear caller-base parameters, including a malicious mount alias.
        candidate = wrapper.reference
        base_ids = {id(p) for p in self.base.parameters()}
        if type(candidate) is ReferenceQVLoRA:
            for parameter in candidate.parameters():
                if id(parameter) not in base_ids:
                    self.cleanup_parameters[id(parameter)] = ref(parameter)
        base, factors, named, device = _bindings(wrapper, state)
        controller = wrapper._checkpoint_controller
        if (
            base is not self.base
            or device != self.signature[0]
            or wrapper.capsule is not None
            or getattr(wrapper, "lora", None) is not None
            or type(factors) is not ReferenceQVLoRA
            or wrapper.reference is not factors
            or type(factors.initialization_seed) is not int
            or factors.initialization_seed != PARITY_SEED
            or tuple(_live_factors(factors)) != REFERENCE_NAMES
            or sum(p.numel() for _, p in named) != 460800
            or any(p.grad is not None or p.is_inference() for _, p in named)
            or _digest(named) != self.digests[state]
            or type(controller) is not CheckpointController
            or controller.owner is not wrapper
            or controller in self.controllers
            or controller._active is not None
            or type(controller.layer_count) is not int
            or controller.layer_count != 30
            or controller.base_getter() is not base
            or controller.factor_getter() is not factors
            or (checkpoint and not callable(controller.state_fingerprint_getter))
            or (not checkpoint and controller.state_fingerprint_getter is not None)
        ):
            raise ValueError(
                "original120 q/v masters and independent controller binding required"
            )
        self.controllers.add(controller)
        self.unchanged()
        return wrapper

    def make(self, state, checkpoint):
        # Existing generic guard enforces fresh wrapper/factor/parameter/storage
        # ownership even if a caller test replaces the execution engine.
        return self.guard.make(state, checkpoint)

    def clear(self):
        self.guard.clear()
        for weak in self.cleanup_parameters.values():
            if (parameter := weak()) is not None:
                parameter.grad = None


def run_reference_parity_suite(host, fixtures, *, exact, expected_fixture_digest):
    """Bind fixed factory, generic cell and bounded separate success receipt.

    No public loader/factory/execution callback. The fixture digest must originate
    in caller-authenticated framing; equality alone does not confer provenance.
    Original cell keeps18 singles/pending pair/16 accumulation/preclip comparisons
    and fixed step1. Failures retain the inner journal, whose accumulation stage
    remains coarse. Outer owner persists scalar evidence and discards live chained
    exceptions/wrappers; this function neither journals process kills nor retries.
    """
    if (
        type(exact) is not bool
        or torch.is_inference_mode_enabled()
        or not torch.is_grad_enabled()
    ):
        raise ValueError(
            "explicit mode and ordinary grad-enabled construction required"
        )
    _schedule(fixtures)
    _sha(expected_fixture_digest)
    fixture_digest = _json_digest([asdict(fixture) for fixture in fixtures])
    if fixture_digest != expected_fixture_digest:
        raise ValueError("expected six-fixture digest required")
    signature = _signature(host)
    if exact != (signature[0].type == "cpu"):
        raise ValueError("CPU exact/GPU fixed tolerance mode required")
    identity = ReferenceParityIdentity(
        str(signature[0]),
        str(next(host.model.parameters()).dtype),
        signature[1],
        signature[5],
        signature[6],
        fixture_digest,
    )
    stage, factory, completed_progress = "prepare", None, None
    try:
        factory = _ReferenceFactory(host, signature, exact)
        stage = "cell"
        cell = run_parity_cell(factory.make, fixtures, exact=exact)
        completed_progress = _completed_progress(cell)
        stage = "final_base"
        factory.unchanged()
        stage = "receipt"
        result = ReferenceParityReceipt(identity, PARITY_SEED, cell)
        validate_reference_parity_receipt(result, expected_identity=identity)
        if any(row.factor_digest != factory.digests[row.state] for row in cell.cases):
            raise ValueError("receipt must bind original seeded factor state bytes")
        factory.unchanged()
        return result
    except KeyboardInterrupt as exc:
        if factory is not None:
            factory.clear()
        inner = (
            exc.failure
            if type(exc) is ParityCellInterrupted
            else (
                replace(completed_progress, stage=stage)
                if completed_progress is not None
                else None
            )
        )
        raise ReferenceParityInterrupted(ReferenceParityFailure(stage, inner)) from exc
    except Exception as exc:
        if factory is not None:
            factory.clear()
        inner = (
            exc.failure
            if type(exc) is ParityCellError
            else (
                replace(completed_progress, stage=stage)
                if completed_progress is not None
                else None
            )
        )
        raise ReferenceParityError(ReferenceParityFailure(stage, inner)) from exc
    except BaseException:
        if factory is not None:
            factory.clear()
        raise
