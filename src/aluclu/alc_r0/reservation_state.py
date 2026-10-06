"""Bounded pure reservation replay. Integrity/arithmetic, never a launch permit."""

from __future__ import annotations

import re
from dataclasses import dataclass, replace

from .canonical import CanonicalEvidenceError, canonical_json_bytes, parse_canonical_json, sha256_bytes

_MAX = (1 << 63) - 1
_RECORD_BYTES = 16384
_DECL_BYTES = 4 * 1024 * 1024
_EVENT_BYTES = 32 * 1024 * 1024
_EVENT_COUNT = 262144
_ID = re.compile(r"[A-Za-z0-9_-]{1,128}\Z")
_RUN = re.compile(r"alc-r0-v1-(pilot|dev|confirm|eval)-[a-z0-9-]+-s[0-9]{8}\Z")
_ROOT = re.compile(r"[0-9a-f]{64}\Z")
_NONCE = re.compile(r"[0-9a-f]{32}\Z")
_DECIMAL = re.compile(r"(?:0|[1-9][0-9]{0,19})\Z")
_DECL = frozenset({
    "experiment_id", "reservation_id", "run_id", "attempt_id", "segment",
    "declaration_root", "device", "useful_wall_ceiling_ns", "cleanup_ceiling_ns",
    "charge_envelope_ns", "gpu_reservation_ns", "research_growth_bytes",
    "physical_growth_bytes", "stdout_limit_bytes", "stderr_limit_bytes",
})
_COMMON = frozenset({"sequence", "previous_root", "reservation_id", "kind", "evidence_root"})
_FIELDS = {
    "reserve": {"declaration_root", "entry_utc_ns", "clock_domain_root", "entry_monotonic_ns", "useful_deadline_monotonic_ns"},
    "child_created": {"pid", "creation_filetime_100ns", "owner_nonce", "identity_receipt_root"},
    "identity_published": {"identity_receipt_root", "publication_root"},
    "running": {"resume_receipt_root"},
    "terminal": {"fact_kind", "identity_receipt_root", "exit_code", "terminal_fact_root"},
    "uncertain": {"reason", "prior_state"},
    "reconcile": {"resource_charge_root", "wall_kind", "effective_wall_ns", "effective_gpu_ns", "growth_observation_root", "materialized_research_bytes", "materialized_physical_bytes"},
    "release": {"global_publication_root"},
}


class ReservationStateError(ValueError):
    """Malformed, incomplete or illegal reservation history."""


def _matches(value: object, pattern: re.Pattern) -> bool:
    return type(value) is str and pattern.fullmatch(value) is not None


def _number(value: object, maximum: int = _MAX, minimum: int = 0) -> int:
    if not _matches(value, _DECIMAL):
        raise ReservationStateError("canonical decimal string required")
    number = int(value)
    if not minimum <= number <= maximum:
        raise ReservationStateError("numeric range exceeded")
    return number


def _sum(values) -> int:
    total = sum(values)
    if not 0 <= total <= _MAX:
        raise ReservationStateError("aggregate overflow")
    return total


def _parse(data: bytes) -> dict:
    if type(data) is not bytes or not 0 < len(data) <= _RECORD_BYTES:
        raise ReservationStateError("bounded canonical bytes required")
    try:
        item = parse_canonical_json(data)
    except (CanonicalEvidenceError, RecursionError) as exc:
        raise ReservationStateError("invalid canonical record") from exc
    if type(item) is not dict:
        raise ReservationStateError("object required")
    return item


@dataclass(frozen=True, slots=True)
class ReservationView:
    reservation_id: str
    declaration: bytes
    state: str = "ABSENT"
    pid: int | None = None
    creation_filetime_100ns: int | None = None
    owner_nonce: str | None = None
    identity_receipt_root: str | None = None
    exit_code: int | None = None
    effective_gpu_ns: int | None = None
    materialized_research_bytes: int = 0
    materialized_physical_bytes: int = 0
    growth_observation_root: str | None = None
    uncertainty_reason: str | None = None


@dataclass(frozen=True, slots=True)
class ReservationSnapshot:
    root: str
    event_count: int
    event_bytes: int
    reservations: tuple[ReservationView, ...]
    outstanding_gpu_ns: int
    consumed_gpu_ns: int
    pending_research_bytes: int
    pending_physical_bytes: int
    overrun: bool


def _declaration(data: bytes) -> dict:
    item = _parse(data)
    if item.keys() != _DECL:
        raise ReservationStateError("exact declaration fields required")
    if (item["experiment_id"] != "alc-r0-smollm2-135m-v1"
            or not _matches(item["reservation_id"], _ID)
            or not _matches(item["run_id"], _RUN)
            or len(item["run_id"]) > 128
            or item["attempt_id"] not in ("a001", "a002", "a003")
            or item["segment"] not in ("initial", "resume")
            or item["device"] not in ("cpu", "gpu")
            or not _matches(item["declaration_root"], _ROOT)):
        raise ReservationStateError("invalid declaration identity")
    for field in _DECL:
        if field.endswith("_ns") or field.endswith("_bytes"):
            item[field] = _number(item[field])
    envelope = _sum((item["useful_wall_ceiling_ns"], item["cleanup_ceiling_ns"]))
    if (item["useful_wall_ceiling_ns"] == 0 or item["cleanup_ceiling_ns"] != 10000000000
            or item["charge_envelope_ns"] < envelope
            or (item["device"] == "gpu" and item["gpu_reservation_ns"] < item["charge_envelope_ns"])
            or (item["device"] == "cpu" and item["gpu_reservation_ns"] != 0)):
        raise ReservationStateError("invalid resource envelope")
    return item


class ReservationReplay:
    """Incremental prefix validation; complete replay additionally needs pinned root."""

    def __init__(self, declarations: tuple[bytes, ...]):
        if type(declarations) is not tuple or not 0 < len(declarations) <= 4096:
            raise ReservationStateError("complete immutable declarations required")
        if any(type(data) is not bytes for data in declarations) or sum(map(len, declarations)) > _DECL_BYTES:
            raise ReservationStateError("declaration byte cap exceeded")
        self._decls = {}
        self._views = {}
        pairs = set()
        for data in declarations:
            item = _declaration(data)
            key = item["reservation_id"]
            pair = (item["run_id"], item["attempt_id"], item["segment"])
            if key in self._decls or pair in pairs:
                raise ReservationStateError("duplicate declaration")
            pairs.add(pair)
            self._decls[key] = item
            self._views[key] = ReservationView(key, data)
        ordered = sorted(self._decls)
        genesis = {"schema": "alc-r0-reservations-v1", "declarations": [
            parse_canonical_json(self._views[key].declaration) for key in ordered
        ]}
        self._root = sha256_bytes(canonical_json_bytes(genesis))
        self._events: list[bytes] = []
        self._event_bytes = 0
        self._nonces: set[str] = set()

    def _snapshot(self, views, root, count, byte_count, observation_root=None):
        held = [v for v in views.values() if v.state not in ("ABSENT", "RELEASED")]
        released = [v for v in views.values() if v.state == "RELEASED"]
        if len(held) > 512:
            raise ReservationStateError("live reservation cap exceeded")
        pending = []
        for field, materialized in (("research_growth_bytes", "materialized_research_bytes"),
                                    ("physical_growth_bytes", "materialized_physical_bytes")):
            pending.append(_sum(self._decls[v.reservation_id][field] - (
                getattr(v, materialized) if v.state == "RECONCILED" and
                v.growth_observation_root == observation_root else 0) for v in held))
        return ReservationSnapshot(root, count, byte_count,
            tuple(views[key] for key in sorted(views)),
            _sum(self._decls[v.reservation_id]["gpu_reservation_ns"] for v in held),
            _sum(v.effective_gpu_ns for v in released), *pending,
            any(v.effective_gpu_ns is not None and v.effective_gpu_ns >
                self._decls[v.reservation_id]["gpu_reservation_ns"] for v in views.values()))

    def snapshot(self, observation_root: str | None = None) -> ReservationSnapshot:
        """Default growth is conservative; reduction requires matching observation."""
        if observation_root is not None and not _matches(observation_root, _ROOT):
            raise ReservationStateError("observation root required")
        return self._snapshot(self._views, self._root, len(self._events), self._event_bytes, observation_root)

    @property
    def events(self) -> tuple[bytes, ...]:
        return tuple(self._events)

    def append(self, data: bytes) -> None:
        if (type(data) is not bytes or len(self._events) >= _EVENT_COUNT
                or self._event_bytes + len(data) > _EVENT_BYTES):
            raise ReservationStateError("event count/byte cap exceeded")
        item = _parse(data)
        kind = item.get("kind")
        if type(kind) is not str or kind not in _FIELDS or item.keys() != _COMMON | _FIELDS[kind]:
            raise ReservationStateError("exact known event fields required")
        if (_number(item["sequence"], _EVENT_COUNT, 1) != len(self._events) + 1
                or item["previous_root"] != self._root
                or not _matches(item["reservation_id"], _ID)
                or item["reservation_id"] not in self._views):
            raise ReservationStateError("history continuity/identity mismatch")
        for field, value in item.items():
            if field.endswith("_root") and not (kind == "terminal" and field == "identity_receipt_root" and value is None):
                if not _matches(value, _ROOT):
                    raise ReservationStateError("root required")
        key = item["reservation_id"]
        view = self._transition(self._views[key], self._decls[key], item)
        candidate = dict(self._views)
        candidate[key] = view
        root = sha256_bytes(data)
        self._snapshot(candidate, root, len(self._events) + 1, self._event_bytes + len(data))
        self._views = candidate
        self._root = root
        self._event_bytes += len(data)
        self._events.append(data)
        if kind == "child_created":
            self._nonces.add(view.owner_nonce)

    def _transition(self, view, declaration, item):
        kind, state = item["kind"], view.state
        successors = {"reserve": ("ABSENT",), "child_created": ("RESERVED",),
            "identity_published": ("CREATED",), "running": ("READY",),
            "terminal": ("RESERVED", "CREATED", "READY", "RUNNING", "UNCERTAIN"),
            "uncertain": ("RESERVED", "CREATED", "READY", "RUNNING"),
            "reconcile": ("TERMINAL_PENDING",), "release": ("RECONCILED",)}
        if state not in successors[kind]:
            raise ReservationStateError("illegal predecessor")
        if kind == "reserve":
            if item["declaration_root"] != declaration["declaration_root"]:
                raise ReservationStateError("declaration root mismatch")
            _number(item["entry_utc_ns"])
            origin = _number(item["entry_monotonic_ns"])
            if _number(item["useful_deadline_monotonic_ns"]) != _sum((origin, declaration["useful_wall_ceiling_ns"])):
                raise ReservationStateError("deadline mismatch")
            for key, other in self._decls.items():
                if (other["run_id"], other["attempt_id"]) == (declaration["run_id"], declaration["attempt_id"]):
                    if self._views[key].state not in ("ABSENT", "RELEASED"):
                        raise ReservationStateError("overlapping attempt segments")
            if declaration["segment"] == "resume" and not any(
                other["segment"] == "initial" and (other["run_id"], other["attempt_id"]) ==
                (declaration["run_id"], declaration["attempt_id"]) and self._views[key].state == "RELEASED"
                for key, other in self._decls.items()):
                raise ReservationStateError("resume requires released initial segment")
            return replace(view, state="RESERVED")
        if kind == "child_created":
            nonce = item["owner_nonce"]
            if not _matches(nonce, _NONCE) or nonce in self._nonces:
                raise ReservationStateError("unique owner nonce required")
            return replace(view, state="CREATED", pid=_number(item["pid"], (1 << 32) - 1, 1),
                creation_filetime_100ns=_number(item["creation_filetime_100ns"], (1 << 64) - 1, 1),
                owner_nonce=nonce, identity_receipt_root=item["identity_receipt_root"])
        if kind == "identity_published":
            if item["identity_receipt_root"] != view.identity_receipt_root:
                raise ReservationStateError("published identity mismatch")
            return replace(view, state="READY")
        if kind == "running":
            return replace(view, state="RUNNING")
        if kind == "uncertain":
            if item["prior_state"] != state or item["reason"] not in ("creation", "publication", "resume", "timeout", "reboot", "terminal"):
                raise ReservationStateError("uncertainty predecessor/reason mismatch")
            return replace(view, state="UNCERTAIN", uncertainty_reason=item["reason"])
        if kind == "terminal":
            identity, code = item["identity_receipt_root"], item["exit_code"]
            if item["fact_kind"] == "verified_no_child":
                if (identity is not None or code is not None or view.identity_receipt_root is not None
                        or (state != "RESERVED" and not (state == "UNCERTAIN" and view.uncertainty_reason == "creation"))):
                    raise ReservationStateError("no-child contradicts known identity")
            elif item["fact_kind"] == "verified_owned_tree_terminal":
                if identity is None or identity != view.identity_receipt_root:
                    raise ReservationStateError("owned terminal identity mismatch")
            else:
                raise ReservationStateError("verified terminal fact kind required")
            return replace(view, state="TERMINAL_PENDING", exit_code=None if code is None else _number(code, (1 << 32) - 1))
        if kind == "reconcile":
            wall, gpu = _number(item["effective_wall_ns"]), _number(item["effective_gpu_ns"])
            research, physical = _number(item["materialized_research_bytes"]), _number(item["materialized_physical_bytes"])
            if (item["wall_kind"] not in ("observed", "allocation_upper_bound")
                    or gpu != (wall if declaration["device"] == "gpu" else 0)
                    or research > declaration["research_growth_bytes"]
                    or physical > declaration["physical_growth_bytes"]):
                raise ReservationStateError("charge/materialization mismatch")
            return replace(view, state="RECONCILED", effective_gpu_ns=gpu,
                materialized_research_bytes=research, materialized_physical_bytes=physical,
                growth_observation_root=item["growth_observation_root"])
        return replace(view, state="RELEASED")


def replay_reservations(declarations: tuple[bytes, ...], events: tuple[bytes, ...], expected_root: str) -> ReservationSnapshot:
    """Replay complete history against an independently pinned final root."""
    if type(events) is not tuple or len(events) > _EVENT_COUNT or not _matches(expected_root, _ROOT):
        raise ReservationStateError("complete bounded history and pinned root required")
    if any(type(data) is not bytes for data in events) or sum(map(len, events)) > _EVENT_BYTES:
        raise ReservationStateError("complete history byte cap exceeded")
    replay = ReservationReplay(declarations)
    for event in events:
        replay.append(event)
    result = replay.snapshot()
    if result.root != expected_root:
        raise ReservationStateError("incomplete or mismatched final history")
    return result
