"""Owner-locked single-event transaction, not launch or learning authority.

Closed trusted namespace and cooperating coordinator writers only. Lower-level
journal APIs can bypass this lock. Caller pins current owner and exact intent;
local records cannot detect rollback of BOTH storage and caller authority.
Completed intentions are retained, bounded individually and in total count.
Global research storage/time reservations remain a separate mandatory gate.
"""

from __future__ import annotations

import os
import re
import stat
from dataclasses import asdict, dataclass
from pathlib import Path

from aluclu.cognition.persistence import (
    atomic_write_bytes,
    exclusive_file_lock,
    resolve_ledger_path,
)

from .attempt_journal import AttemptJournal, JournalError, plan_journal_append
from .attempt_state import AttemptReplay
from .canonical import canonical_json_bytes, parse_canonical_json
from .manifest_publication import (
    ManifestOwner,
    PublicationConflict,
    PublicationError,
    _hash,
    _record,
    _sha,
    prepare_publication,
)
from .paged_history import (
    _inventory,
    _manifest,
    _prefix_head,
    declaration_root,
    page_identity,
)

_MAX_INTENT = 65536
_NAME = re.compile(r"intent-([0-9]{6})\.json\Z")


@dataclass(frozen=True, slots=True)
class AppendIntent:
    data: bytes
    sha256: str


@dataclass(frozen=True, slots=True)
class OwnedAppend:
    owner: ManifestOwner
    intents: Path

    def __post_init__(self):
        if type(self.owner) is not ManifestOwner:
            raise PublicationError("exact owner required")
        if not isinstance(self.intents, Path) or not self.intents.is_absolute():
            raise PublicationError("absolute existing intent directory required")
        path = resolve_ledger_path(self.intents / "intent-000001.json").parent
        if (
            not path.is_dir()
            or path == self.owner.pages
            or path.is_relative_to(self.owner.pages)
            or self.owner.pages.is_relative_to(path)
            or self.owner.path.is_relative_to(path)
        ):
            raise PublicationError("separate closed intent namespace required")
        object.__setattr__(self, "intents", path)

    def _build(self, previous, previous_root, event, review, rotate):
        if type(rotate) is not bool:
            raise PublicationError("exact rotation boolean required")
        item, manifest = _record(self.owner.spec, previous, previous_root)
        root = declaration_root(self.owner.spec)
        heads = _manifest(manifest, _sha(manifest), root)
        index = len(heads) - 1 if heads and not rotate else len(heads)
        if heads and heads[-1].count == 65536:
            index = len(heads)
        identity = page_identity(root, index, heads[index - 1] if index else None)
        journal = AttemptJournal(self.owner.pages / f"page-{index:04d}.jsonl", identity)
        new_page = index == len(heads)
        prior = journal._genesis() if new_page else heads[index]
        try:
            planned = plan_journal_append(identity, prior, event)
        except JournalError as exc:
            # The planner validates event/schema FIRST. Rotate ONLY its exact
            # capacity rejection, never malformed inputs or arbitrary I/O errors.
            if new_page or str(exc) != "journal append ceiling exceeded":
                raise
            index = len(heads)
            identity = page_identity(root, index, heads[-1])
            journal = AttemptJournal(
                self.owner.pages / f"page-{index:04d}.jsonl", identity
            )
            prior = journal._genesis()
            planned = plan_journal_append(identity, prior, event)
            new_page = True
        updated = heads + (planned.head,) if new_page else heads[:-1] + (planned.head,)
        candidate_manifest = canonical_json_bytes(
            dict(version=1, spec_sha256=root, pages=[asdict(h) for h in updated])
        )
        prepared = prepare_publication(
            self.owner.spec,
            previous,
            previous_root,
            candidate_manifest,
            _sha(candidate_manifest),
            review,
        )
        data = canonical_json_bytes(
            dict(
                version=1,
                previous=parse_canonical_json(previous),
                previous_sha256=previous_root,
                candidate=parse_canonical_json(prepared.candidate),
                candidate_sha256=prepared.candidate_sha256,
                event=parse_canonical_json(event),
                review_sha256=review,
                rotate=rotate,
                target=index,
                journal_id=identity,
                prior=asdict(prior),
                next=asdict(planned.head),
            )
        )
        if len(data) > _MAX_INTENT:
            raise PublicationError("intent byte ceiling exceeded")
        return (
            AppendIntent(data, _sha(data)),
            prepared,
            journal,
            prior,
            planned.head,
            new_page,
        )

    def _decode(self, intent):
        if (
            type(intent) is not AppendIntent
            or type(intent.data) is not bytes
            or not 0 < len(intent.data) <= _MAX_INTENT
            or not _hash(intent.sha256)
            or _sha(intent.data) != intent.sha256
        ):
            raise PublicationError("bounded exact independently pinned intent required")
        item = parse_canonical_json(intent.data)
        fields = {
            "version",
            "previous",
            "previous_sha256",
            "candidate",
            "candidate_sha256",
            "event",
            "review_sha256",
            "rotate",
            "target",
            "journal_id",
            "prior",
            "next",
        }
        if type(item) is not dict or item.keys() != fields:
            raise PublicationError("exact intent schema required")
        rebuilt = self._build(
            canonical_json_bytes(item["previous"]),
            item["previous_sha256"],
            canonical_json_bytes(item["event"]),
            item["review_sha256"],
            item["rotate"],
        )
        if rebuilt[0] != intent:
            raise PublicationError("intent differs from exact reconstructed transition")
        return rebuilt

    def _path(self, prepared):
        generation = parse_canonical_json(prepared.candidate)["generation"]
        return self.intents / f"intent-{generation:06d}.json"

    def _intent_inventory(self, generation, allowed=None):
        count = 0
        with os.scandir(self.intents) as entries:
            for entry in entries:
                count += 1
                match = _NAME.fullmatch(entry.name)
                if (
                    not match
                    or not 1 <= int(match[1]) <= 262144
                    or count > 262144
                    or (int(match[1]) > generation and entry.name != allowed)
                ):
                    raise PublicationError("unexpected/orphan intent inventory")
                path = self.intents / entry.name
                self.owner._regular(path)
                if not 0 < path.stat().st_size <= _MAX_INTENT:
                    raise PublicationError("unsafe/oversized retained intent")

    def _intent_read(self, path):
        self.owner._regular(path)
        with path.open("rb") as handle:
            info = os.fstat(handle.fileno())
            if (
                not stat.S_ISREG(info.st_mode)
                or info.st_nlink != 1
                or not 0 < info.st_size <= _MAX_INTENT
            ):
                raise PublicationError("unsafe intent descriptor")
            return handle.read(_MAX_INTENT + 1)

    def _observed(self, intent, prepared, journal, prior, next_head, new_page):
        """Read all pages, prove exact old prefix and semantic event BEFORE mutation."""
        _, old_manifest = _record(
            self.owner.spec, prepared.previous, prepared.previous_sha256
        )
        root = declaration_root(self.owner.spec)
        heads = _manifest(old_manifest, _sha(old_manifest), root)
        exists = journal.path.exists()
        _inventory(self.owner.pages, len(heads) + int(new_page and exists))
        replay = AttemptReplay((self.owner.spec,))
        target = len(heads) if new_page else len(heads) - 1
        for index, head in enumerate(heads):
            if index == target:
                continue
            identity = page_identity(root, index, heads[index - 1] if index else None)
            snapshot = AttemptJournal(
                self.owner.pages / f"page-{index:04d}.jsonl", identity
            ).read(head)
            for event in snapshot.events:
                replay.append(event)
        observed = prior
        events = ()
        if exists:
            with exclusive_file_lock(journal._lock_path()):
                with journal._open("rb") as handle:
                    snapshot = journal._scan(handle)
            observed, events = snapshot.head, snapshot.events
            if observed not in (prior, next_head):
                raise PublicationConflict(
                    "target page is neither exact old nor intended new"
                )
            if observed == next_head:
                expected_event = canonical_json_bytes(
                    parse_canonical_json(intent.data)["event"]
                )
                if not events or events[-1] != expected_event:
                    raise PublicationConflict("intended event differs")
                events = events[:-1]
            if _prefix_head(journal.journal_id, events, len(events)) != prior:
                raise PublicationConflict(
                    "target prefix differs from exact predecessor"
                )
        elif not new_page:
            raise PublicationConflict("missing old target page")
        for event in events:
            replay.append(event)
        replay.append(canonical_json_bytes(parse_canonical_json(intent.data)["event"]))
        return exists, observed

    def prepare(self, expected_owner_root, event, review_root, *, rotate=False):
        with self.owner._lock():
            old = self.owner.read(expected_owner_root)
            built = self._build(old.data, old.sha256, event, review_root, rotate)
            generation = parse_canonical_json(old.data)["generation"]
            self._intent_inventory(generation)
            self._observed(*built)
            return built[0]

    def _persist(self, path, intent):
        atomic_write_bytes(path, intent.data)

    def _publish(self, prepared):
        return self.owner.publish(prepared)

    def _advance(self, intent, prepared, journal, prior, next_head, new_page):
        exists, observed = self._observed(
            intent, prepared, journal, prior, next_head, new_page
        )
        if observed == prior:
            if not exists:
                journal.create()
            else:
                journal.reconcile(prior)
            event = canonical_json_bytes(parse_canonical_json(intent.data)["event"])
            if journal.append(prior, event) != next_head:
                raise PublicationError("actual append differs from exact intent")
        else:
            journal.reconcile(
                next_head
            )  # Visible bytes alone are NOT durable acknowledgement.
        return self._publish(prepared)

    def commit(self, intent):
        built = self._decode(intent)
        prepared = built[1]
        with self.owner._lock():
            if self.owner._load() != prepared.previous:
                raise PublicationConflict("stale append predecessor")
            generation = parse_canonical_json(prepared.previous)["generation"]
            self._intent_inventory(generation)
            exists, head = self._observed(*built)
            if head != built[3] or (built[5] and exists):
                raise PublicationConflict(
                    "unrecorded page mutation; not an adoptable intent"
                )
            path = self._path(prepared)
            if path.exists():
                raise PublicationConflict(
                    "intent already exists; explicit resume required"
                )
            self._persist(path, intent)  # MUST finish before ANY page mutation.
            return self._advance(*built)

    def resume(self, intent):
        built = self._decode(intent)
        prepared = built[1]
        with self.owner._lock():
            observed = self.owner._load()
            if observed not in (prepared.previous, prepared.candidate):
                raise PublicationConflict(
                    "owner is neither exact predecessor nor candidate"
                )
            path = self._path(prepared)
            generation = parse_canonical_json(observed)["generation"]
            self._intent_inventory(generation, path.name)
            if self._intent_read(path) != intent.data:
                raise PublicationConflict(
                    "persisted intent differs from independently pinned intent"
                )
            exists, head = self._observed(*built)
            if observed == prepared.candidate:
                if not exists or head != built[4]:
                    raise PublicationConflict(
                        "published target is not exact intended page"
                    )
                self._persist(path, intent)
                built[2].reconcile(head)
                return self.owner.reconcile(prepared)
            # Re-acknowledge exact visible intent after complete preflight.
            self._persist(path, intent)
            return self._advance(*built)
