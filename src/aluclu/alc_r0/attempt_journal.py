"""Bounded append-only storage, not attempt semantics or launch authority.

The expected head MUST come from an independently trusted monotone owner.
Concurrent cooperating writers compare and append under the existing path lock.
No recovery/truncation/retry is implicit; uncertain writes require reconciliation.
"""

from __future__ import annotations

import hashlib
import os
import stat
from dataclasses import dataclass
from pathlib import Path

from aluclu.cognition.persistence import (
    atomic_write_bytes,
    exclusive_file_lock,
    resolve_ledger_path,
)

from .canonical import (
    CanonicalEvidenceError,
    canonical_json_bytes,
    normalize_evidence_path,
    parse_canonical_json,
)

_MAX_EVENT = 8192
_MAX_RECORD = 16384
_MAX_BYTES = 32 * (1 << 20)
_MAX_RECORDS = 65536
_GENESIS_DOMAIN = b"ALC-R0-JOURNAL-GENESIS-V1\0"
_RECORD_DOMAIN = b"ALC-R0-JOURNAL-RECORD-V1\0"
_FIELDS = frozenset({"version", "journal_id", "sequence", "previous", "event"})


class JournalError(RuntimeError):
    """Malformed or unsafe storage; never repaired or treated as empty."""


class JournalConflict(JournalError):
    """Observed head differs from the caller's independently trusted head."""


@dataclass(frozen=True, slots=True)
class JournalHead:
    count: int
    byte_length: int
    digest: str


@dataclass(frozen=True, slots=True)
class JournalSnapshot:
    head: JournalHead
    events: tuple[bytes, ...]


@dataclass(frozen=True, slots=True)
class PlannedJournalAppend:
    """Exact intended bytes/head, not storage evidence or launch authority."""

    line: bytes
    head: JournalHead


def _digest(value: object) -> bool:
    return (
        type(value) is str
        and len(value) == 64
        and all(c in "0123456789abcdef" for c in value)
    )


def _head(head: JournalHead) -> None:
    if (
        type(head) is not JournalHead
        or any(
            type(value) is not int or not 0 <= value <= limit
            for value, limit in (
                (head.count, _MAX_RECORDS),
                (head.byte_length, _MAX_BYTES),
            )
        )
        or not _digest(head.digest)
    ):
        raise JournalError("invalid exact journal head")


def _object(data: bytes) -> dict:
    try:
        value = parse_canonical_json(data)
    except (CanonicalEvidenceError, RecursionError) as exc:
        raise JournalError("invalid canonical journal object") from exc
    if type(value) is not dict:
        raise JournalError("journal values must be objects")
    return value


def plan_journal_append(
    journal_id: str, expected: JournalHead, event: bytes
) -> PlannedJournalAppend:
    """Pure bounded exact record plan shared by actual append, no filesystem I/O."""
    if not _digest(journal_id):
        raise JournalError("canonical journal identity required")
    _head(expected)
    if type(event) is not bytes or not 0 < len(event) <= _MAX_EVENT:
        raise JournalError("bounded canonical event bytes required")
    value = _object(event)
    line = (
        canonical_json_bytes(
            {
                "version": 1,
                "journal_id": journal_id,
                "sequence": expected.count + 1,
                "previous": expected.digest,
                "event": value,
            }
        )
        + b"\n"
    )
    if (
        len(line) > _MAX_RECORD
        or expected.count >= _MAX_RECORDS
        or expected.byte_length + len(line) > _MAX_BYTES
    ):
        raise JournalError("journal append ceiling exceeded")
    return PlannedJournalAppend(
        line,
        JournalHead(
            expected.count + 1,
            expected.byte_length + len(line),
            hashlib.sha256(_RECORD_DOMAIN + line).hexdigest(),
        ),
    )


@dataclass(frozen=True, slots=True)
class AttemptJournal:
    """Storage in a trusted local directory, with caller-owned head authority.

    A fresh read never silently adopts a newer or older head. Fsync failure can
    leave bytes on disk, but returns no receipt. Caller must reconcile that
    uncertain state separately before any launch or another write.
    """

    path: Path
    journal_id: str

    def __post_init__(self) -> None:
        if not isinstance(self.path, Path) or not self.path.is_absolute():
            raise JournalError("absolute journal Path required")
        if not _digest(self.journal_id):
            raise JournalError("canonical journal identity required")
        try:
            normalize_evidence_path(self.path.name)
        except CanonicalEvidenceError as exc:
            raise JournalError("unsafe journal filename") from exc
        object.__setattr__(self, "path", resolve_ledger_path(self.path))
        if not self.path.parent.is_dir():
            raise JournalError("journal parent must already exist")

    def _genesis(self) -> JournalHead:
        return JournalHead(
            0,
            0,
            hashlib.sha256(
                _GENESIS_DOMAIN + self.journal_id.encode("ascii")
            ).hexdigest(),
        )

    def _lock_path(self) -> Path:
        return self.path.with_name(self.path.name + ".lock")

    def create(self) -> JournalHead:
        """Explicit exclusive durable creation, never reset an existing file."""
        with exclusive_file_lock(self._lock_path()):
            resolve_ledger_path(self.path)
            if self.path.exists():
                raise FileExistsError(self.path)
            atomic_write_bytes(self.path, b"")
            return self._genesis()

    def _scan(self, handle) -> JournalSnapshot:
        info = os.fstat(handle.fileno())
        if not stat.S_ISREG(info.st_mode) or info.st_nlink != 1:
            raise JournalError("single-link regular journal required")
        if info.st_size > _MAX_BYTES:
            raise JournalError("journal byte ceiling exceeded")
        head = self._genesis()
        events: list[bytes] = []
        handle.seek(0)
        while line := handle.readline(_MAX_RECORD + 1):
            if (
                len(line) > _MAX_RECORD
                or not line.endswith(b"\n")
                or b"\r" in line
                or head.count >= _MAX_RECORDS
                or head.byte_length + len(line) > _MAX_BYTES
            ):
                raise JournalError("invalid journal framing or resource bound")
            record = _object(line[:-1])
            if (
                record.keys() != _FIELDS
                or type(record["version"]) is not int
                or record["version"] != 1
                or record["journal_id"] != self.journal_id
                or type(record["sequence"]) is not int
                or record["sequence"] != head.count + 1
                or record["previous"] != head.digest
                or type(record["event"]) is not dict
            ):
                raise JournalError("journal identity/sequence/chain mismatch")
            event = canonical_json_bytes(record["event"])
            if len(event) > _MAX_EVENT:
                raise JournalError("journal event ceiling exceeded")
            events.append(event)
            head = JournalHead(
                head.count + 1,
                head.byte_length + len(line),
                hashlib.sha256(_RECORD_DOMAIN + line).hexdigest(),
            )
        return JournalSnapshot(head, tuple(events))

    def _open(self, mode: str):
        # Trusted-root/cooperating-writer scope; not hostile directory TOCTOU.
        resolve_ledger_path(self.path)
        info = self.path.lstat()
        if not stat.S_ISREG(info.st_mode) or info.st_nlink != 1:
            raise JournalError("single-link regular journal required before open")
        return self.path.open(mode)

    def read(self, expected: JournalHead) -> JournalSnapshot:
        _head(expected)
        with exclusive_file_lock(self._lock_path()):
            with self._open("rb") as handle:
                snapshot = self._scan(handle)
            if snapshot.head != expected:
                raise JournalConflict("journal differs from expected head")
            return snapshot

    def append(self, expected: JournalHead, event: bytes) -> JournalHead:
        """Compare, append and fsync before acknowledging; no automatic retry."""
        planned = plan_journal_append(self.journal_id, expected, event)
        line = planned.line
        with exclusive_file_lock(self._lock_path()):
            with self._open("r+b") as handle:
                if self._scan(handle).head != expected:
                    raise JournalConflict("journal differs from expected head")
                handle.seek(0, os.SEEK_END)
                if handle.write(line) != len(line):
                    raise OSError("short journal write; outcome uncertain")
                handle.flush()
                os.fsync(handle.fileno())
            return planned.head
