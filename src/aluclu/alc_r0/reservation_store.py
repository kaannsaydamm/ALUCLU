"""Global cooperating reservation publication, not model launch authority.

Caller pins current owner and exact intents independently. All mutations use the
global-then-journal lock order. No latest discovery or implicit repair/recovery.
"""

from __future__ import annotations

import os
import re
import stat
from dataclasses import asdict, dataclass, field
from pathlib import Path

from aluclu.cognition.persistence import atomic_write_bytes, exclusive_file_lock, resolve_ledger_path

from .attempt_journal import AttemptJournal, JournalHead, plan_journal_append
from .canonical import canonical_json_bytes, parse_canonical_json, sha256_bytes
from .reservation_state import ReservationReplay, ReservationSnapshot

_ROOT = re.compile(r"[0-9a-f]{64}\Z")
_GENERATION = re.compile(r"(?:0|[1-9][0-9]{0,4})\Z")
_OWNER_FIELDS = {"schema", "generation", "declaration_genesis_root", "previous_owner_root",
                 "review_root", "journal_head", "reservation_root"}
_INTENT_FIELDS = {"schema", "previous_owner", "candidate_owner", "event", "review_root"}
_MAX_INTENT_BYTES = 128 * 1024 * 1024


class ReservationStoreError(ValueError):
    """Invalid, conflicting or uncertain publication; never implicitly adopted."""


def _hash(value):
    return type(value) is str and _ROOT.fullmatch(value) is not None


@dataclass(frozen=True, slots=True)
class PreparedReservationIntent:
    data: bytes
    sha256: str


@dataclass(frozen=True, slots=True)
class PublishedReservation:
    data: bytes
    sha256: str
    snapshot: ReservationSnapshot


@dataclass(frozen=True, slots=True)
class ReservationStore:
    root: Path
    declarations: tuple[bytes, ...]
    _genesis_root: str = field(init=False, repr=False)
    _journal: AttemptJournal = field(init=False, repr=False)

    def __post_init__(self):
        if not isinstance(self.root, Path) or not self.root.is_absolute():
            raise ReservationStoreError("absolute existing namespace required")
        root = resolve_ledger_path(self.root / "owner.json").parent
        intents = resolve_ledger_path(root / "intents" / "initialization.json").parent
        if not root.is_dir() or not intents.is_dir():
            raise ReservationStoreError("namespace and intent directory must exist")
        genesis = ReservationReplay(self.declarations).snapshot().root
        object.__setattr__(self, "root", root)
        object.__setattr__(self, "_genesis_root", genesis)
        object.__setattr__(self, "_journal", AttemptJournal(root / "journal.jsonl", genesis))

    @property
    def owner_path(self):
        return self.root / "owner.json"

    def _lock(self):
        path = self.root / "global.lock"
        if path.exists():
            self._regular(path)
        return exclusive_file_lock(path)

    @staticmethod
    def _regular(path):
        info = resolve_ledger_path(path).lstat()
        if not stat.S_ISREG(info.st_mode) or info.st_nlink != 1:
            raise ReservationStoreError("single-link regular file required")
        return info

    def _load(self, path, limit):
        self._regular(path)
        with path.open("rb") as handle:
            info = os.fstat(handle.fileno())
            if not stat.S_ISREG(info.st_mode) or info.st_nlink != 1 or not 0 < info.st_size <= limit:
                raise ReservationStoreError("unsafe or oversized record")
            return handle.read(limit + 1)

    def _inventory(self, generation, pending=None, initializing=False):
        allowed = {"owner.json", "global.lock", "journal.jsonl", "journal.jsonl.lock", "intents"}
        for entry in self.root.iterdir():
            if entry.name not in allowed:
                raise ReservationStoreError("unexpected namespace inventory")
            if entry.name == "intents":
                resolve_ledger_path(entry / "initialization.json")
                if not entry.is_dir():
                    raise ReservationStoreError("intent directory required")
            else:
                self._regular(entry)
        expected = {"initialization.json"} | {f"intent-{i:06d}.json" for i in range(1, generation + 1)}
        names, total = set(), 0
        for entry in (self.root / "intents").iterdir():
            names.add(entry.name)
            info = self._regular(entry)
            if not 0 < info.st_size <= 16384 or len(names) > 65537:
                raise ReservationStoreError("intent size/count exceeded")
            total += info.st_size
            if total > _MAX_INTENT_BYTES:
                raise ReservationStoreError("aggregate intent bytes exceeded")
        permitted = expected | ({pending} if pending else set())
        if initializing and not names:
            return total
        if not expected <= names or not names <= permitted:
            raise ReservationStoreError("missing or orphan retained intent")
        return total

    def _owner(self, data):
        if type(data) is not bytes or not 0 < len(data) <= 4096:
            raise ReservationStoreError("bounded owner bytes required")
        item = parse_canonical_json(data)
        if (type(item) is not dict or item.keys() != _OWNER_FIELDS
                or item["schema"] != "alc-r0-reservation-owner-v1"
                or item["declaration_genesis_root"] != self._genesis_root
                or type(item["generation"]) is not str
                or not _GENERATION.fullmatch(item["generation"])
                or not _hash(item["reservation_root"])):
            raise ReservationStoreError("owner schema mismatch")
        generation = int(item["generation"])
        head = item["journal_head"]
        if (generation > 65536 or type(head) is not dict
                or head.keys() != {"count", "byte_length", "digest"}
                or type(head["count"]) is not int or head["count"] != generation
                or type(head["byte_length"]) is not int or not 0 <= head["byte_length"] <= 32 * 1024 * 1024
                or not _hash(head["digest"])):
            raise ReservationStoreError("owner journal head mismatch")
        if generation == 0:
            if item["previous_owner_root"] is not None or item["review_root"] is not None:
                raise ReservationStoreError("genesis predecessor must be null")
        elif not _hash(item["previous_owner_root"]) or not _hash(item["review_root"]):
            raise ReservationStoreError("published predecessor/review required")
        return item, JournalHead(**head)

    def _encode_owner(self, generation, head, semantic_root, previous=None, review=None):
        data = canonical_json_bytes(dict(schema="alc-r0-reservation-owner-v1",
            generation=str(generation), declaration_genesis_root=self._genesis_root,
            previous_owner_root=previous, review_root=review, journal_head=asdict(head),
            reservation_root=semantic_root))
        self._owner(data)
        return data

    def _intent(self, previous, candidate, event, review):
        data = canonical_json_bytes(dict(schema="alc-r0-reservation-intent-v1",
            previous_owner=None if previous is None else parse_canonical_json(previous),
            candidate_owner=parse_canonical_json(candidate),
            event=None if event is None else parse_canonical_json(event), review_root=review))
        if len(data) > 16384:
            raise ReservationStoreError("intent record cap exceeded")
        return PreparedReservationIntent(data, sha256_bytes(data))

    def initialization_intent(self):
        owner = self._encode_owner(0, self._journal._genesis(), self._genesis_root)
        return self._intent(None, owner, None, None)

    def _decode(self, intent):
        if (type(intent) is not PreparedReservationIntent or type(intent.data) is not bytes
                or not 0 < len(intent.data) <= 16384 or not _hash(intent.sha256)
                or sha256_bytes(intent.data) != intent.sha256):
            raise ReservationStoreError("exact independently pinned intent required")
        item = parse_canonical_json(intent.data)
        if type(item) is not dict or item.keys() != _INTENT_FIELDS or item["schema"] != "alc-r0-reservation-intent-v1":
            raise ReservationStoreError("exact intent schema required")
        candidate = canonical_json_bytes(item["candidate_owner"])
        self._owner(candidate)
        if item["previous_owner"] is None:
            if intent != self.initialization_intent():
                raise ReservationStoreError("initialization intent mismatch")
            return None, candidate, None, None
        previous = canonical_json_bytes(item["previous_owner"])
        self._owner(previous)
        if not _hash(item["review_root"]) or type(item["event"]) is not dict:
            raise ReservationStoreError("append review/event required")
        return previous, candidate, canonical_json_bytes(item["event"]), item["review_root"]

    def _build(self, previous, event, review, replay):
        if not _hash(review):
            raise ReservationStoreError("review root required")
        item, head = self._owner(previous)
        planned = plan_journal_append(self._genesis_root, head, event)
        replay.append(event)
        candidate = self._encode_owner(int(item["generation"]) + 1, planned.head,
            replay.snapshot().root, sha256_bytes(previous), review)
        return self._intent(previous, candidate, event, review), candidate, planned.head

    def _scan(self):
        with exclusive_file_lock(self._journal._lock_path()):
            with self._journal._open("rb") as handle:
                return self._journal._scan(handle)

    def _audit(self, owner, events, pending=None):
        item, expected_head = self._owner(owner)
        generation = int(item["generation"])
        if len(events) != generation:
            raise ReservationStoreError("complete journal length mismatch")
        total = self._inventory(generation, pending)
        initial = self.initialization_intent()
        if self._load(self.root / "intents" / "initialization.json", 16384) != initial.data:
            raise ReservationStoreError("retained initialization differs")
        previous = self._decode(initial)[1]
        replay = ReservationReplay(self.declarations)
        head = self._journal._genesis()
        for index, event in enumerate(events, 1):
            data = self._load(self.root / "intents" / f"intent-{index:06d}.json", 16384)
            retained = PreparedReservationIntent(data, sha256_bytes(data))
            _, _, _, review = self._decode(retained)
            rebuilt, previous, head = self._build(previous, event, review, replay)
            if rebuilt != retained:
                raise ReservationStoreError("retained intent chain differs")
        if previous != owner or head != expected_head or replay.snapshot().root != item["reservation_root"]:
            raise ReservationStoreError("owner differs from complete retained history")
        return replay, total

    def _receipt(self, owner, replay):
        return PublishedReservation(owner, sha256_bytes(owner), replay.snapshot())

    def _read_locked(self, expected):
        if not _hash(expected):
            raise ReservationStoreError("independent owner root required")
        owner = self._load(self.owner_path, 4096)
        if sha256_bytes(owner) != expected:
            raise ReservationStoreError("stale owner root")
        _, head = self._owner(owner)
        self._inventory(head.count)
        journal = self._journal.read(head)
        replay, total = self._audit(owner, journal.events)
        return owner, replay, total

    def read(self, expected_owner_root):
        with self._lock():
            owner, replay, _ = self._read_locked(expected_owner_root)
            return self._receipt(owner, replay)

    @staticmethod
    def _project(intent, generation, total):
        if generation >= 65536 or total + len(intent.data) > _MAX_INTENT_BYTES:
            raise ReservationStoreError("projected storage capacity exceeded")

    def _persist(self, path, intent):
        atomic_write_bytes(path, intent.data)

    def _publish(self, candidate):
        atomic_write_bytes(self.owner_path, candidate)

    def initialize(self, intent):
        previous, candidate, _, _ = self._decode(intent)
        if previous is not None:
            raise ReservationStoreError("initialization intent required")
        with self._lock():
            self._inventory(0, initializing=True)
            path = self.root / "intents" / "initialization.json"
            stored = path.exists()
            journal_exists, owner_exists = self._journal.path.exists(), self.owner_path.exists()
            if (not stored and (journal_exists or owner_exists)) or (owner_exists and not journal_exists):
                raise ReservationStoreError("unsupported initialization state")
            if stored and self._load(path, 16384) != intent.data:
                raise ReservationStoreError("initialization differs")
            if owner_exists and self._load(self.owner_path, 4096) != candidate:
                raise ReservationStoreError("existing owner is not genesis")
            genesis_head = self._journal._genesis()
            if journal_exists:
                self._journal.read(genesis_head)
            self._persist(path, intent)
            if journal_exists:
                self._journal.reconcile(genesis_head)
            else:
                self._journal.create()
            self._publish(candidate)
            return self._receipt(candidate, ReservationReplay(self.declarations))

    def prepare(self, expected_owner_root, event, review_root):
        with self._lock():
            previous, replay, total = self._read_locked(expected_owner_root)
            intent, _, _ = self._build(previous, event, review_root, replay)
            self._project(intent, int(self._owner(previous)[0]["generation"]), total)
            return intent

    def commit(self, intent):
        previous, candidate, event, review = self._decode(intent)
        if previous is None:
            raise ReservationStoreError("append intent required")
        with self._lock():
            old, replay, total = self._read_locked(sha256_bytes(previous))
            if old != previous:
                raise ReservationStoreError("exact predecessor required")
            rebuilt, rebuilt_candidate, next_head = self._build(previous, event, review, replay)
            if rebuilt != intent or rebuilt_candidate != candidate:
                raise ReservationStoreError("intent differs from exact transition")
            generation = int(self._owner(previous)[0]["generation"])
            self._project(intent, generation, total)
            path = self.root / "intents" / f"intent-{generation + 1:06d}.json"
            self._persist(path, intent)
            actual = self._journal.append(self._owner(previous)[1], event)
            if actual != next_head:
                raise ReservationStoreError("actual journal differs from plan")
            self._publish(candidate)
            return self._receipt(candidate, replay)

    def resume(self, intent):
        previous, candidate, event, review = self._decode(intent)
        if previous is None:
            raise ReservationStoreError("use explicit initialize for genesis")
        with self._lock():
            observed = self._load(self.owner_path, 4096)
            if observed not in (previous, candidate):
                raise ReservationStoreError("owner is neither exact previous nor candidate")
            old_item, old_head = self._owner(previous)
            _, candidate_head = self._owner(candidate)
            generation = int(old_item["generation"])
            path = self.root / "intents" / f"intent-{generation + 1:06d}.json"
            self._inventory(generation, path.name)
            journal = self._scan()
            if journal.head not in (old_head, candidate_head) or (observed == candidate and journal.head != candidate_head):
                raise ReservationStoreError("unsupported owner/journal recovery pair")
            events = journal.events
            if journal.head == candidate_head:
                if not events or events[-1] != event:
                    raise ReservationStoreError("candidate journal event differs")
                events = events[:-1]
            replay, _ = self._audit(previous, events, path.name)
            if self._load(path, 16384) != intent.data:
                raise ReservationStoreError("persisted recovery intent differs")
            rebuilt, rebuilt_candidate, next_head = self._build(previous, event, review, replay)
            if rebuilt != intent or rebuilt_candidate != candidate:
                raise ReservationStoreError("recovery intent differs from exact transition")
            self._persist(path, intent)
            if journal.head == old_head:
                if self._journal.append(old_head, event) != next_head:
                    raise ReservationStoreError("actual recovery append differs")
            else:
                self._journal.reconcile(next_head)
            self._publish(candidate)
            return self._receipt(candidate, replay)
