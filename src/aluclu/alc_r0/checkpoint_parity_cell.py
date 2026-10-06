"""Execute all section-D comparisons for one synthetic parity cell.

The cooperating factory accepts (state, checkpoint) and returns fresh wrappers
over ONE already authenticated base. No loading/tokenization/launch authority
is provided. Caller verifies framing/source/runtime and owns quiescent state.
An exception is terminal for this attempt: record it and discard the wrappers;
there is no retry, tolerance adjustment or scientific learning claim here.
The separate matrix/launcher must still run all cells and official regressions.
"""

from dataclasses import dataclass, replace
from weakref import WeakSet, ref

import torch
from torch import nn

from .checkpoint_accumulation_pair import _storage, run_accumulation_pair
from .checkpoint_execution import _digest
from .checkpoint_observation import (
    ObservationError,
    _base_digest,
    _bindings,
    _fixture,
    _roster_stamp,
    compare_observations,
    compare_pending_observations,
    observe_forward_backward,
    observe_pending_pair,
)
from .checkpoint_optimizer import AdamWComparison


@dataclass(frozen=True)
class CaseComparison:
    state: str
    repeat: int
    fixture_index: int
    losses: tuple[float, float]
    scores: tuple[float, float]
    base_digest: str
    factor_digest: str


@dataclass(frozen=True)
class ParityCell:
    cases: tuple[CaseComparison, ...]
    pending_losses: tuple[float, float]
    accumulation: AdamWComparison
    parameter_names: tuple[str, ...]
    parameter_count: int
    base_digest: str


SINGLE_SCHEDULE = tuple(
    (state, repeat, index)
    for state, repeat in (("zero", 0), ("nonzero", 0), ("nonzero", 1))
    for index in range(6)
)


@dataclass(frozen=True)
class ParityCellFailure:
    """Bounded observations only; not rollback or a durable process-kill journal."""

    stage: str
    completed: tuple[CaseComparison, ...]
    current: tuple[str, int, int] | None
    unrun: tuple[tuple[str, int, int], ...]
    pending_losses: tuple[float, float] | None


class ParityCellError(ObservationError):
    def __init__(self, message, failure):
        super().__init__(message)
        self.failure = failure


class ParityCellInterrupted(KeyboardInterrupt):
    def __init__(self, message, failure):
        super().__init__(message)
        self.failure = failure


class _Progress:
    def __init__(self):
        self.stage = "single_factory_off"
        self.completed = ()
        self.current = SINGLE_SCHEDULE[0]
        self.attempted = False
        self.pending_losses = None

    def failure(self):
        next_index = len(self.completed) + int(
            self.current is not None and self.attempted
        )
        return ParityCellFailure(
            self.stage,
            self.completed,
            self.current,
            SINGLE_SCHEDULE[next_index:],
            self.pending_losses,
        )


def _schedule(fixtures):
    if type(fixtures) is not tuple or len(fixtures) != 6:
        raise ObservationError("six ordered immutable D fixtures required")
    for fixture in fixtures:
        _fixture(fixture, 49152)
    candidates = tuple(f.candidate_ids for f in fixtures[:2])
    if candidates[0] == candidates[1]:
        raise ObservationError("distinct safe/vulnerable candidates required")
    for index, (length, padding) in enumerate(((32, 0), (64, 0), (64, 7))):
        pair = fixtures[2 * index : 2 * index + 2]
        if (
            max(len(f.input_ids) for f in pair) != length + padding
            or any(
                len(f.input_ids) - f.prompt_length - len(f.candidate_ids) != padding
                for f in pair
            )
            or tuple(f.candidate_ids for f in pair) != candidates
            or pair[0].prompt_length != pair[1].prompt_length
            or pair[0].input_ids[: pair[0].prompt_length]
            != pair[1].input_ids[: pair[1].prompt_length]
        ):
            raise ObservationError("fixed D length/padding/common prompt required")
    for original, padded in zip(fixtures[2:4], fixtures[4:6], strict=True):
        if (
            padded.input_ids[:-7] != original.input_ids
            or len(set(padded.input_ids[-7:])) != 1
        ):
            raise ObservationError("right EOS padding must preserve length64 input")


class _FactoryGuard:
    def __init__(self, factory, exact):
        self.factory, self.exact = factory, exact
        self.wrappers, self.factors = WeakSet(), WeakSet()
        # Tensor equality is elementwise: never use tensors as weak-set keys.
        self.parameters = {}
        self.base = None
        self.states = {}
        self.progress = _Progress()

    def make(self, state, checkpoint):
        wrapper = self.factory(state, checkpoint)
        if not isinstance(wrapper, nn.Module):
            raise ObservationError("cooperating wrapper required")
        factors = wrapper._checkpoint_factors()
        previous = tuple(
            p for weak in self.parameters.values() if (p := weak()) is not None
        )
        incoming = tuple(factors.parameters())
        # Register even rejected ownership so exception cleanup reaches it.
        for parameter in incoming:
            self.parameters[id(parameter)] = ref(parameter)
        if {id(p) for p in previous} & {id(p) for p in incoming} or {
            _storage(p) for p in previous
        } & {_storage(p) for p in incoming}:
            raise ObservationError(
                "fresh live factor parameter/storage ownership required"
            )
        base, factors, named, device = _bindings(wrapper, state)
        if {_storage(p) for _, p in named} & {_storage(b) for b in base.buffers()}:
            raise ObservationError("factor/base buffer storage overlap")
        if (
            self.exact != (device.type == "cpu")
            or any(
                p.dtype != (torch.float32 if device.type == "cpu" else torch.bfloat16)
                for p in base.parameters()
            )
            or any(p.grad is not None for _, p in named)
        ):
            raise ObservationError("fresh factors and CPU exact/GPU BF16 required")
        signature = (
            _base_digest(base),
            _roster_stamp(base.named_parameters()),
            _roster_stamp(base.named_buffers()),
            device,
        )
        if self.base is None:
            self.base, self.signature = base, signature
            self.names = tuple(name for name, _ in named)
            self.count = sum(p.numel() for _, p in named)
        if (
            base is not self.base
            or signature != self.signature
            or wrapper in self.wrappers
            or factors in self.factors
            or tuple(name for name, _ in named) != self.names
            or sum(p.numel() for _, p in named) != self.count
        ):
            raise ObservationError(
                "one unchanged base and fresh matched roster required"
            )
        digest = _digest(named)
        if state in self.states and digest != self.states[state]:
            raise ObservationError(
                "every attempt must start from identical factor state"
            )
        self.states[state] = digest
        a_digest = _digest(
            tuple((name, p) for name, p in named if name.rsplit(".", 1)[-1] == "A")
        )
        if hasattr(self, "a_digest") and a_digest != self.a_digest:
            raise ObservationError("zero/nonzero states require identical original A")
        self.a_digest = a_digest
        if state == "nonzero":
            for name, parameter in named:
                if name.rsplit(".", 1)[-1] == "B":
                    expected = (
                        torch.arange(parameter.numel(), device="cpu") % 17 - 8
                    ).float() * 1e-4
                    actual = parameter.detach().cpu().contiguous().reshape(-1)
                    if not torch.equal(
                        expected.view(torch.uint8), actual.view(torch.uint8)
                    ):
                        raise ObservationError("fixed nonzero B pattern required")
        self.wrappers.add(wrapper)
        self.factors.add(factors)
        return wrapper

    def clear(self):
        for weak in self.parameters.values():
            if (parameter := weak()) is not None:
                parameter.grad = None


def _order(scores):
    return (scores[0] > scores[1]) - (scores[0] < scores[1])


def _singles(guard, fixtures):
    records, repeats = [], {}
    for state, repeat in (("zero", 0), ("nonzero", 0), ("nonzero", 1)):
        scores = []
        for index, fixture in enumerate(fixtures):
            guard.progress.current = state, repeat, index
            guard.progress.attempted = False
            guard.progress.stage = "single_factory_off"
            off = guard.make(state, False)
            guard.progress.stage = "single_off"
            guard.progress.attempted = True
            reference = observe_forward_backward(
                off,
                fixture,
                checkpoint=False,
                state=state,
            )
            guard.progress.stage = "single_factory_on"
            on = guard.make(state, True)
            guard.progress.stage = "single_on"
            actual = observe_forward_backward(
                on,
                fixture,
                checkpoint=True,
                state=state,
            )
            guard.progress.stage = "single_compare"
            compare_observations(reference, actual, exact=guard.exact)
            if state == "nonzero":
                if repeat:
                    guard.progress.stage = "single_repeat"
                    # Same-mode repetition uses the existing complete comparator;
                    # the metadata flag alone is normalized, never tensor bytes.
                    old_off, old_on = repeats[index]
                    compare_observations(
                        old_off, replace(reference, checkpoint=True), exact=guard.exact
                    )
                    compare_observations(
                        replace(old_on, checkpoint=False), actual, exact=guard.exact
                    )
                else:
                    repeats[index] = reference, actual
            scores.append((reference.candidate_score, actual.candidate_score))
            guard.progress.stage = "single_order"
            if index % 2 and _order(tuple(s[0] for s in scores[-2:])) != _order(
                tuple(s[1] for s in scores[-2:])
            ):
                raise ObservationError("candidate ordering or exact tie changed")
            guard.progress.stage = "single_receipt"
            records.append(
                CaseComparison(
                    state,
                    repeat,
                    index,
                    (reference.loss.item(), actual.loss.item()),
                    scores[-1],
                    reference.base_digest,
                    reference.factor_digest,
                )
            )
            guard.progress.completed = tuple(records)
    guard.progress.current = None
    guard.progress.attempted = False
    return tuple(records)


def run_parity_cell(factory, fixtures, *, exact):
    """Run 18 off/on singles, repeated nonzero, pending pair and fixed step.

    Fixtures are ordered safe/vulnerable for L32, L64 and L64+padding7. Their
    labels/provenance must be authenticated externally. Success is one synthetic
    cell only, not full-matrix/actual-host/resource/scientific acceptance.
    No full logits, autograd graphs or optimizer objects survive in the receipt.
    Execution failures now wrap the original cause in ObservationError or
    KeyboardInterrupt subclasses with bounded progress; invalid admission still
    fails before execution. Accumulation is one delegated stage, not a claim of
    microbatch-level or durable timeout journaling. No retry or rollback occurs.
    """
    if not callable(factory) or type(exact) is not bool:
        raise ObservationError("callable factory and exact boolean required")
    _schedule(fixtures)
    guard = _FactoryGuard(factory, exact)
    try:
        cases = _singles(guard, fixtures)
        guard.progress.stage = "pending_factory_off"
        off = guard.make("nonzero", False)
        guard.progress.stage = "pending_off"
        reference = observe_pending_pair(off, fixtures[:2], checkpoint=False)
        guard.progress.stage = "pending_factory_on"
        on = guard.make("nonzero", True)
        guard.progress.stage = "pending_on"
        actual = observe_pending_pair(on, fixtures[:2], checkpoint=True)
        guard.progress.stage = "pending_compare"
        compare_pending_observations(reference, actual, exact=exact)
        pending = reference.summed_loss.item(), actual.summed_loss.item()
        guard.progress.pending_losses = pending
        del reference, actual, off, on
        guard.progress.stage = "accumulation"
        accumulation = run_accumulation_pair(
            lambda checkpoint: guard.make("nonzero", checkpoint),
            fixtures[2:4] * 8,
            exact=exact,
        )
        guard.progress.stage = "final_base"
        if _base_digest(guard.base) != guard.signature[0]:
            raise ObservationError("base changed after complete cell")
        return ParityCell(
            cases,
            pending,
            accumulation.comparison,
            guard.names,
            guard.count,
            guard.signature[0],
        )
    except KeyboardInterrupt as exc:
        guard.clear()
        raise ParityCellInterrupted(str(exc), guard.progress.failure()) from exc
    except Exception as exc:
        guard.clear()
        raise ParityCellError(str(exc), guard.progress.failure()) from exc
    except BaseException:
        guard.clear()
        raise
