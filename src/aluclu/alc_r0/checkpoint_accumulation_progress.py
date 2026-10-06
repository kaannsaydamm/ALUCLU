"""Fixed primitive execution journal, not numerical/launch/rollback authority.

The immutable transcript defines admissible metadata, never performs an operation.
Cooperating callers mark entry and return around the unchanged computation. No
callables, Torch imports, tensors, models or exceptions are retained here. Payload
validation proves framing only; it cannot authenticate execution by a caller.
"""

from contextlib import contextmanager
from dataclasses import dataclass, fields, replace


class JournalError(ValueError):
    """Invalid private journal identity, transition or primitive framing."""


@dataclass(frozen=True, slots=True)
class ArmProgress:
    forwards: int = 0
    backwards: int = 0
    captured: int = 0
    completed_observation: int = 0
    completed_step: int = 0


@dataclass(frozen=True, slots=True)
class AccumulationFailure:
    phase: str
    arm: str | None
    index: int | None
    completed_pair: int
    off: ArmProgress
    on: ArmProgress
    journal_fault: bool = False
    cleanup_fault: bool = False


_PAIR_PHASES = (
    "off_factory",
    "off_bindings",
    "off_observation",
    "on_factory",
    "on_bindings",
    "on_observation",
    "preclip_compare",
    "cross_arm_storage",
    "off_step",
    "on_step",
    "full_step_compare",
    "pair_record",
)
_OBSERVATION_PHASES = (
    "observe_admit",
    "observe_prepare",
    "observe_session_enter",
    "micro_forward",
    "micro_loss",
    "micro_backward",
    "micro_capture",
    "observe_total",
    "observe_session_exit",
    "observe_bindings",
    "observe_frozen",
    "observe_outputs",
    "observe_gradients",
    "observe_capture",
    "observe_record",
)
_STEP_PHASES = (
    "step_admit",
    "step_live_gradients",
    "step_guard",
    "step_optimizer_create",
    "step_optimizer_group",
    "step_clip",
    "step_clipped_capture",
    "step_optimizer_call",
    "step_postconditions",
    "step_snapshot",
    "step_record",
)


def _transcript():
    """Build constant-size primitive metadata at import, not runtime history."""
    rows = []
    state = AccumulationFailure(
        "off_factory", "off", None, 0, ArmProgress(), ArmProgress()
    )

    def emit(kind, phase, arm, index=None, **changes):
        nonlocal state
        state = replace(state, phase=phase, arm=arm, index=index, **changes)
        rows.append(((kind, phase, arm, index), state))

    def nested(arm, phase, index=None):
        emit("arm_begin", phase, arm, index)
        progress = getattr(state, arm)
        if phase in _OBSERVATION_PHASES:
            updates = {"completed_observation": _OBSERVATION_PHASES.index(phase) + 1}
            counter = {
                "micro_forward": "forwards",
                "micro_backward": "backwards",
                "micro_capture": "captured",
            }.get(phase)
            if counter is not None:
                updates[counter] = index + 1
        else:
            updates = {"completed_step": _STEP_PHASES.index(phase) + 1}
        emit("arm_return", phase, arm, index, **{arm: replace(progress, **updates)})

    for ordinal, phase in enumerate(_PAIR_PHASES, 1):
        arm = phase.split("_", 1)[0] if phase.startswith(("off_", "on_")) else None
        emit("pair_begin", phase, arm)
        if phase.endswith("_observation"):
            for nested_phase in _OBSERVATION_PHASES[:3]:
                nested(arm, nested_phase)
            for index in range(16):
                for nested_phase in _OBSERVATION_PHASES[3:7]:
                    nested(arm, nested_phase, index)
            for nested_phase in _OBSERVATION_PHASES[7:]:
                nested(arm, nested_phase)
        elif phase.endswith("_step"):
            for nested_phase in _STEP_PHASES:
                nested(arm, nested_phase)
        emit("pair_return", phase, arm, completed_pair=ordinal)
    return tuple(rows)


_ROWS = _transcript()
_VALID = frozenset(state for _, state in _ROWS)


def validate_accumulation_failure(value):
    """Exact primitive framing and full cross-field reachability, not execution."""
    if type(value) is not AccumulationFailure:
        raise JournalError("exact accumulation snapshot required")
    if (
        type(value.phase) is not str
        or (value.arm is not None and type(value.arm) is not str)
        or (value.index is not None and type(value.index) is not int)
        or type(value.completed_pair) is not int
        or type(value.journal_fault) is not bool
        or type(value.cleanup_fault) is not bool
    ):
        raise JournalError("exact primitive snapshot fields required")
    for progress in (value.off, value.on):
        if type(progress) is not ArmProgress or any(
            type(getattr(progress, field.name)) is not int
            for field in fields(ArmProgress)
        ):
            raise JournalError("exact primitive arm fields required")
    ordinary = replace(value, journal_fault=False, cleanup_fault=False)
    if ordinary not in _VALID:
        raise JournalError("unreachable accumulation phase/count/ordinal combination")
    return value


@dataclass(frozen=True, slots=True, eq=False)
class _ArmTicket:
    owner: object
    token: object
    arm: str


class _AccumulationOwner:
    """One cooperating attempt; tickets are identity-bound, not authorization."""

    __slots__ = (
        "_token",
        "_tickets",
        "_cursor",
        "_closed",
        "_journal_fault",
        "_cleanup_fault",
    )

    def __init__(self):
        self._token = object()
        self._tickets = tuple(
            _ArmTicket(self, self._token, arm) for arm in ("off", "on")
        )
        self._cursor = -1
        self._closed = False
        self._journal_fault = False
        self._cleanup_fault = False

    def _admit(self):
        if (
            type(self) is not _AccumulationOwner
            or type(self._cursor) is not int
            or not -1 <= self._cursor < len(_ROWS)
            or type(self._closed) is not bool
            or type(self._journal_fault) is not bool
            or type(self._cleanup_fault) is not bool
        ):
            raise JournalError("exact valid attempt owner required")

    def ticket(self, arm):
        self._admit()
        if type(arm) is not str or arm not in ("off", "on"):
            raise JournalError("exact off/on ticket arm required")
        return self._tickets[arm == "on"]

    def _ticket(self, ticket):
        self._admit()
        if (
            type(ticket) is not _ArmTicket
            or ticket.owner is not self
            or ticket.token is not self._token
            or type(ticket.arm) is not str
            or ticket.arm not in ("off", "on")
            or ticket is not self._tickets[ticket.arm == "on"]
        ):
            raise JournalError("foreign, forged or subclass arm ticket")
        return ticket.arm

    def _advance(self, kind, phase, arm, index):
        self._admit()
        if (
            self._closed
            or self._cursor + 1 == len(_ROWS)
            or type(phase) is not str
            or (index is not None and type(index) is not int)
        ):
            raise JournalError("closed attempt or invalid phase/index")
        action = (kind, phase, arm, index)
        if action != _ROWS[self._cursor + 1][0]:
            raise JournalError("skipped, repeated or out-of-order journal operation")
        self._cursor += 1

    def begin_pair(self, phase):
        arm = (
            phase.split("_", 1)[0]
            if type(phase) is str and phase.startswith(("off_", "on_"))
            else None
        )
        self._advance("pair_begin", phase, arm, None)

    def finish_pair(self, phase):
        arm = (
            phase.split("_", 1)[0]
            if type(phase) is str and phase.startswith(("off_", "on_"))
            else None
        )
        self._advance("pair_return", phase, arm, None)

    def begin_arm(self, ticket, phase, index=None):
        self._advance("arm_begin", phase, self._ticket(ticket), index)

    def finish_arm(self, ticket, phase, index=None):
        self._advance("arm_return", phase, self._ticket(ticket), index)

    def snapshot(self):
        self._admit()
        if self._cursor == -1:
            return None
        value = _ROWS[self._cursor][1]
        # Never hand out shared transcript objects, even to a cooperating caller.
        result = replace(
            value,
            off=replace(value.off),
            on=replace(value.on),
            journal_fault=self._journal_fault,
            cleanup_fault=self._cleanup_fault,
        )
        return validate_accumulation_failure(result)

    def _mark_fault(self, *, journal=False, cleanup=False):
        self._admit()
        if type(journal) is not bool or type(cleanup) is not bool:
            raise JournalError("exact bounded diagnostic booleans required")
        self._journal_fault = self._journal_fault or journal
        self._cleanup_fault = self._cleanup_fault or cleanup

    def close(self):
        self._admit()
        self._closed = True


def _fresh_owner(value):
    """Admit data only, before any cooperating computation or state mutation."""
    if value is None:
        return _AccumulationOwner()
    if type(value) is not _AccumulationOwner:
        raise JournalError("exact private accumulation owner required")
    value._admit()
    if (
        value._closed
        or value._cursor != -1
        or value._journal_fault
        or value._cleanup_fault
    ):
        raise JournalError("fresh unused accumulation attempt required")
    return value


def _admit_ticket(ticket, *, checkpoint=None):
    if ticket is None:
        return
    if type(ticket) is not _ArmTicket or type(ticket.owner) is not _AccumulationOwner:
        raise JournalError("exact private accumulation ticket required")
    arm = ticket.owner._ticket(ticket)
    if checkpoint is not None and (
        type(checkpoint) is not bool or (arm == "on") != checkpoint
    ):
        raise JournalError("ticket/checkpoint arm mismatch")


@contextmanager
def _arm_phase(ticket, phase, index=None):
    """Mark return only when the unchanged operation actually returns normally."""
    _arm_begin(ticket, phase, index)
    yield
    _arm_finish(ticket, phase, index)


def _arm_begin(ticket, phase, index=None):
    _admit_ticket(ticket)
    if ticket is not None:
        ticket.owner.begin_arm(ticket, phase, index)


def _arm_finish(ticket, phase, index=None):
    _admit_ticket(ticket)
    if ticket is not None:
        ticket.owner.finish_arm(ticket, phase, index)


@contextmanager
def _pair_phase(owner, phase):
    owner.begin_pair(phase)
    yield
    owner.finish_pair(phase)


def _safe_snapshot(owner):
    """Secondary instrumentation failure must never replace a primary cause."""
    try:
        if type(owner) is not _AccumulationOwner:
            raise JournalError("exact private accumulation owner required")
        record = owner.snapshot()
        if record is not None:
            validate_accumulation_failure(record)
        return record, owner._journal_fault
    except BaseException:
        return None, True


def _bounded_faults(journal, cleanup):
    """A bad payload or marker cannot erase a separately valid diagnostic."""
    return (
        (journal if type(journal) is bool else True) or type(cleanup) is not bool,
        cleanup if type(cleanup) is bool else False,
    )


def _owner_faults(owner):
    if type(owner) is not _AccumulationOwner:
        return True, False
    try:
        journal = owner._journal_fault
    except BaseException:
        journal = None
    try:
        cleanup = owner._cleanup_fault
    except BaseException:
        cleanup = None
    return _bounded_faults(journal, cleanup)


def _clear_owned(parameters):
    """Best-effort every already registered factor; never retain cleanup errors."""
    fault = False
    for parameter in parameters:
        try:
            parameter.grad = None
        except BaseException:
            fault = True
    return fault


def _cleanup_journaled(ticket, parameters):
    """Cleanup diagnostics cannot replace the active computation exception."""
    try:
        fault = _clear_owned(parameters)
    except BaseException:
        fault = True
    if fault:
        try:
            _admit_ticket(ticket)
            ticket.owner._mark_fault(cleanup=True)
        except BaseException:
            # A corrupt owner will fail snapshot framing; retain no exception.
            try:
                ticket.owner._journal_fault = True
            except BaseException:
                pass
