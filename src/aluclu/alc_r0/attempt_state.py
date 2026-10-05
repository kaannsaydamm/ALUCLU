"""Pure declared-attempt replay; no authentication, reservation or launch permit."""

from __future__ import annotations

import re
from dataclasses import dataclass, replace

from .canonical import CanonicalEvidenceError, parse_canonical_json

_RUN_ID = re.compile(r"alc-r0-v1-(pilot|dev|confirm|eval)-[a-z0-9-]+-s[0-9]{8}\Z")
_WORK_ID = re.compile(r"[a-z0-9][a-z0-9-]*\Z")
_COMMON = frozenset({"run_id", "attempt_id", "kind"})
_FIELDS = {
    "intent": {
        "source_sha256",
        "invocation_sha256",
        "retry_kind",
        "prior_source_sha256",
        "prior_artifact_sha256",
        "review_sha256",
    },
    "start": {"receipt_sha256"},
    "work": {"work_id", "evidence_sha256"},
    "interrupt": {
        "checkpoint_sha256",
        "evidence_sha256",
        "gpu_ns",
        "wall_ns",
        "storage_growth_bytes",
    },
    "resume": {
        "checkpoint_sha256",
        "source_sha256",
        "invocation_sha256",
        "review_sha256",
    },
    "close": {
        "state",
        "failure_class",
        "evidence_sha256",
        "gpu_ns",
        "wall_ns",
        "storage_growth_bytes",
    },
    "result": {"state", "evidence_sha256"},
}
_MAX_METRIC = (1 << 53) - 1


class AttemptStateError(ValueError):
    """An event is malformed, undeclared or violates the original attempt rules."""


@dataclass(frozen=True, slots=True)
class RunSpec:
    run_id: str
    resource_run: bool
    work_ids: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class AttemptView:
    attempt_id: str
    state: str
    source_sha256: str
    invocation_sha256: str
    retry_kind: str
    prior_source_sha256: str | None
    prior_artifact_sha256: str | None
    review_sha256: str | None
    work: tuple[tuple[str, str], ...] = ()
    receipt_sha256: str | None = None
    evidence_sha256: str | None = None
    checkpoint_sha256: str | None = None
    failure_class: str | None = None
    gpu_ns: int | None = 0
    wall_ns: int | None = 0
    storage_growth_bytes: int | None = 0
    events: tuple[bytes, ...] = ()


@dataclass(frozen=True, slots=True)
class RunView:
    run_id: str
    state: str
    attempts: tuple[AttemptView, ...]
    resumes: int
    repairs: int


def _hash(value: object) -> bool:
    return (
        type(value) is str
        and len(value) == 64
        and all(c in "0123456789abcdef" for c in value)
    )


def _declarations(specs: tuple[RunSpec, ...]) -> dict[str, RunSpec]:
    if type(specs) is not tuple or not 0 < len(specs) <= 512:
        raise AttemptStateError("bounded immutable declarations required")
    result = {}
    for spec in specs:
        if (
            type(spec) is not RunSpec
            or type(spec.run_id) is not str
            or len(spec.run_id) > 128
            or not _RUN_ID.fullmatch(spec.run_id)
            or type(spec.resource_run) is not bool
            or type(spec.work_ids) is not tuple
            or not 0 < len(spec.work_ids) <= 65536
            or any(
                type(w) is not str or len(w) > 128 or not _WORK_ID.fullmatch(w)
                for w in spec.work_ids
            )
            or len(set(spec.work_ids)) != len(spec.work_ids)
            or spec.run_id in result
        ):
            raise AttemptStateError("invalid or duplicate declared run")
        result[spec.run_id] = spec
    if sum(len(s.work_ids) for s in specs) > 262144:
        raise AttemptStateError("declared work batch ceiling exceeded")
    return result


def _event(data: bytes) -> dict:
    if type(data) is not bytes or not 0 < len(data) <= 8192:
        raise AttemptStateError("bounded canonical event bytes required")
    try:
        item = parse_canonical_json(data)
    except (CanonicalEvidenceError, RecursionError) as exc:
        raise AttemptStateError("malformed canonical attempt event") from exc
    if (
        type(item) is not dict
        or type(item.get("kind")) is not str
        or item["kind"] not in _FIELDS
    ):
        raise AttemptStateError("unknown event kind")
    if item.keys() != _COMMON | _FIELDS[item["kind"]]:
        raise AttemptStateError("exact event fields required")
    if type(item["run_id"]) is not str or type(item["attempt_id"]) is not str:
        raise AttemptStateError("string run and attempt IDs required")
    for key, value in item.items():
        if key.endswith("_sha256"):
            optional = item["kind"] == "intent" and key in {
                "prior_source_sha256",
                "prior_artifact_sha256",
                "review_sha256",
            }
            if not (optional and value is None) and not _hash(value):
                raise AttemptStateError("canonical evidence root required")
    for key in ("gpu_ns", "wall_ns", "storage_growth_bytes"):
        if key in item and item[key] is not None:
            if type(item[key]) is not int or not 0 <= item[key] <= _MAX_METRIC:
                raise AttemptStateError("invalid measurement")
    return item


def _sum(left: int | None, right: int | None) -> int | None:
    if left is None or right is None:
        return None
    value = left + right
    if value > _MAX_METRIC:
        raise AttemptStateError("aggregate measurement exceeds exact integer bound")
    return value


def _new_attempt(spec: RunSpec, row: RunView, item: dict) -> RunView:
    number = len(row.attempts) + 1
    if number > 3 or item["attempt_id"] != f"a{number:03d}":
        raise AttemptStateError("nonconsecutive or excessive attempt")
    retry = item["retry_kind"]
    source, invocation = item["source_sha256"], item["invocation_sha256"]
    if not row.attempts:
        if retry != "INITIAL" or any(
            item[k] is not None
            for k in ("prior_source_sha256", "prior_artifact_sha256", "review_sha256")
        ):
            raise AttemptStateError("initial attempt must not invent prior authority")
    else:
        prior = row.attempts[-1]
        if (
            prior.state != "INVALID"
            or item["prior_source_sha256"] != prior.source_sha256
            or item["prior_artifact_sha256"] != prior.evidence_sha256
            or item["review_sha256"] is None
        ):
            raise AttemptStateError(
                "retry must bind previous INVALID evidence and review"
            )
        if retry == "REPAIR":
            if (
                number > 2
                or row.repairs
                or prior.failure_class != "IMPLEMENTATION"
                or source == prior.source_sha256
            ):
                raise AttemptStateError(
                    "only one documented implementation repair rerun"
                )
        elif retry == "ENVIRONMENT":
            if (
                not spec.resource_run
                or prior.failure_class != "ENVIRONMENT"
                or source != prior.source_sha256
            ):
                raise AttemptStateError(
                    "environment retry only for invalid resource attempt"
                )
        else:
            raise AttemptStateError("invalid retry kind")
    attempt = AttemptView(
        item["attempt_id"],
        "INTENT",
        source,
        invocation,
        retry,
        item["prior_source_sha256"],
        item["prior_artifact_sha256"],
        item["review_sha256"],
    )
    return replace(
        row,
        state="INTENT",
        attempts=row.attempts + (attempt,),
        repairs=row.repairs + (retry == "REPAIR"),
    )


def _advance(
    spec: RunSpec, row: RunView, item: dict, *, work_count: int | None = None
) -> RunView:
    if item["kind"] == "intent":
        return _new_attempt(spec, row, item)
    if not row.attempts or item["attempt_id"] != row.attempts[-1].attempt_id:
        raise AttemptStateError("event must bind current attempt")
    attempt = row.attempts[-1]
    kind = item["kind"]
    resumes = row.resumes
    if kind == "start":
        if attempt.state != "INTENT":
            raise AttemptStateError("start requires INTENT")
        attempt = replace(
            attempt, state="RUNNING", receipt_sha256=item["receipt_sha256"]
        )
    elif kind == "work":
        index = len(attempt.work) if work_count is None else work_count
        if (
            attempt.state != "RUNNING"
            or index >= len(spec.work_ids)
            or item["work_id"] != spec.work_ids[index]
        ):
            raise AttemptStateError("only next missing declared work is permitted")
        if work_count is None:
            attempt = replace(
                attempt,
                work=attempt.work + ((item["work_id"], item["evidence_sha256"]),),
            )
    elif kind == "resume":
        if (
            attempt.state != "INTERRUPTED"
            or resumes
            or item["source_sha256"] != attempt.source_sha256
            or item["invocation_sha256"] != attempt.invocation_sha256
            or item["checkpoint_sha256"] != attempt.checkpoint_sha256
        ):
            raise AttemptStateError("one exact same-attempt crash resume only")
        resumes += 1
        attempt = replace(attempt, state="RUNNING")
    elif kind in {"interrupt", "close"}:
        if kind == "interrupt":
            if attempt.state != "RUNNING":
                raise AttemptStateError("interrupt requires RUNNING")
            state, failure = "INTERRUPTED", None
        else:
            state, failure = item["state"], item["failure_class"]
            if attempt.state not in {"INTENT", "RUNNING", "INTERRUPTED"}:
                raise AttemptStateError("attempt already closed")
            if state == "PREPARED":
                if (
                    attempt.state != "RUNNING"
                    or (len(attempt.work) if work_count is None else work_count)
                    != len(spec.work_ids)
                    or failure is not None
                ):
                    raise AttemptStateError(
                        "PREPARED requires complete successful work"
                    )
            elif state == "INVALID":
                if failure not in ("ENVIRONMENT", "IMPLEMENTATION", "OTHER"):
                    raise AttemptStateError("INVALID requires failure classification")
            elif state != "BLOCKED" or failure != "OTHER":
                raise AttemptStateError("invalid close classification")
        attempt = replace(
            attempt,
            state=state,
            failure_class=failure,
            checkpoint_sha256=item.get("checkpoint_sha256", attempt.checkpoint_sha256),
            evidence_sha256=item["evidence_sha256"],
            gpu_ns=_sum(attempt.gpu_ns, item["gpu_ns"]),
            wall_ns=_sum(attempt.wall_ns, item["wall_ns"]),
            storage_growth_bytes=_sum(
                attempt.storage_growth_bytes, item["storage_growth_bytes"]
            ),
        )
    elif kind == "result":
        if attempt.state != "PREPARED" or item["state"] not in ("PASS", "FAIL"):
            raise AttemptStateError("scientific terminal requires PREPARED")
        attempt = replace(
            attempt, state=item["state"], evidence_sha256=item["evidence_sha256"]
        )
    state = "RUNNING" if attempt.state == "INTERRUPTED" else attempt.state
    return replace(
        row, state=state, attempts=row.attempts[:-1] + (attempt,), resumes=resumes
    )


def replay_attempts(
    specs: tuple[RunSpec, ...], events: tuple[bytes, ...]
) -> tuple[RunView, ...]:
    """Validate supplied journal history; hashes/measurements remain caller claims.

    UNSTARTED and attempt INTERRUPTED are internal views, not extra logical-run
    journal states. Open attempts' aggregate consumption is unknown, never zero.
    """
    declared = _declarations(specs)
    if type(events) is not tuple or len(events) > 262144:
        raise AttemptStateError("bounded immutable event history required")
    rows = {key: RunView(key, "UNSTARTED", (), 0, 0) for key in declared}
    references: dict[tuple[str, str], list[bytes]] = {}
    for data in events:
        item = _event(data)
        run_id = item["run_id"]
        if run_id not in declared:
            raise AttemptStateError("undeclared logical run")
        rows[run_id] = _advance(declared[run_id], rows[run_id], item)
        references.setdefault((run_id, item["attempt_id"]), []).append(data)
    result = []
    for row in rows.values():
        attempts = tuple(
            replace(
                a,
                gpu_ns=None,
                wall_ns=None,
                storage_growth_bytes=None,
                events=tuple(references[(row.run_id, a.attempt_id)]),
            )
            if a.state in {"INTENT", "RUNNING", "INTERRUPTED"}
            else replace(a, events=tuple(references[(row.run_id, a.attempt_id)]))
            for a in row.attempts
        )
        result.append(replace(row, attempts=attempts))
    return tuple(result)


class AttemptReplay:
    """Single-owner semantic replay with append-only private buffers.

    Start from declarations and feed the entire externally authenticated history
    in order. No cache import, durability, authentication or concurrency guarantee.
    Ordinary validation failures leave the accepted prefix unchanged. snapshot()
    copies complete history; calling it per event forfeits the append efficiency.
    """

    __slots__ = ("_declared", "_rows", "_work", "_references", "_count")

    def __init__(self, specs: tuple[RunSpec, ...]) -> None:
        self._declared = _declarations(specs)
        self._rows = {
            key: RunView(key, "UNSTARTED", (), 0, 0) for key in self._declared
        }
        self._work: dict[tuple[str, str], list[tuple[str, str]]] = {}
        self._references: dict[tuple[str, str], list[bytes]] = {}
        self._count = 0

    @property
    def event_count(self) -> int:
        return self._count

    def append(self, data: bytes) -> None:
        if self._count >= 262144:
            raise AttemptStateError("bounded immutable event history required")
        item = _event(data)
        run_id = item["run_id"]
        if run_id not in self._declared:
            raise AttemptStateError("undeclared logical run")
        key = (run_id, item["attempt_id"])
        row = _advance(
            self._declared[run_id],
            self._rows[run_id],
            item,
            work_count=len(self._work.get(key, ())),
        )
        # All semantic validation finishes before any accepted-prefix mutation.
        work = self._work.setdefault(key, [])
        if item["kind"] == "work":
            work.append((item["work_id"], item["evidence_sha256"]))
        self._references.setdefault(key, []).append(data)
        self._rows[run_id] = row
        self._count += 1

    def snapshot(self) -> tuple[RunView, ...]:
        result = []
        for row in self._rows.values():
            attempts = []
            for attempt in row.attempts:
                key = (row.run_id, attempt.attempt_id)
                changes = dict(
                    work=tuple(self._work[key]), events=tuple(self._references[key])
                )
                if attempt.state in {"INTENT", "RUNNING", "INTERRUPTED"}:
                    changes.update(gpu_ns=None, wall_ns=None, storage_growth_bytes=None)
                attempts.append(replace(attempt, **changes))
            result.append(replace(row, attempts=tuple(attempts)))
        return tuple(result)
