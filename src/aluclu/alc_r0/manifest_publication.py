"""Local publication CAS; independent current roots and launch authority external."""

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

from .attempt_state import RunSpec, RunView
from .canonical import (
    CanonicalEvidenceError,
    canonical_json_bytes,
    parse_canonical_json,
)
from .paged_history import (
    _manifest,
    declaration_root,
    read_paged_history,
    verify_paged_extension,
)

_MAX_BYTES = 16384
_FIELDS = {"version", "generation", "spec_sha256", "previous", "manifest", "review"}


class PublicationError(ValueError):
    """Malformed publication contract; never reset or implicitly recovered."""


class PublicationConflict(PublicationError):
    """Local record is not the independently expected exact old/new record."""


def _hash(value: object) -> bool:
    return (
        type(value) is str
        and len(value) == 64
        and all(c in "0123456789abcdef" for c in value)
    )


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _record(spec: RunSpec, data: bytes, expected: str) -> tuple[dict, bytes]:
    if (
        type(data) is not bytes
        or not 0 < len(data) <= _MAX_BYTES
        or not _hash(expected)
        or _sha(data) != expected
    ):
        raise PublicationError("invalid bounded record/root")
    try:
        item = parse_canonical_json(data)
    except (CanonicalEvidenceError, RecursionError) as exc:
        raise PublicationError("invalid canonical owner record") from exc
    root = declaration_root(spec)
    if (
        type(item) is not dict
        or item.keys() != _FIELDS
        or type(item["version"]) is not int
        or item["version"] != 1
        or type(item["generation"]) is not int
        or not 0 <= item["generation"] <= 262144
        or item["spec_sha256"] != root
    ):
        raise PublicationError("owner schema/declaration/generation mismatch")
    manifest = canonical_json_bytes(item["manifest"])
    heads = _manifest(manifest, _sha(manifest), root)
    if item["generation"] == 0:
        if heads or item["previous"] is not None or item["review"] is not None:
            raise PublicationError("genesis must be empty with null previous/review")
    elif not heads or not _hash(item["previous"]) or not _hash(item["review"]):
        raise PublicationError("published record needs prior/review roots and events")
    return item, manifest


@dataclass(frozen=True, slots=True)
class PreparedPublication:
    previous: bytes
    previous_sha256: str
    candidate: bytes
    candidate_sha256: str


@dataclass(frozen=True, slots=True)
class PublishedManifest:
    data: bytes
    sha256: str
    view: RunView


def prepare_publication(
    spec: RunSpec,
    previous: bytes,
    previous_sha256: str,
    candidate_manifest: bytes,
    candidate_sha256: str,
    review_sha256: str,
) -> PreparedPublication:
    """Construct exact candidate bytes, not an approval or durable receipt."""
    item, prior_manifest = _record(spec, previous, previous_sha256)
    root = declaration_root(spec)
    prior = _manifest(prior_manifest, _sha(prior_manifest), root)
    new = _manifest(candidate_manifest, candidate_sha256, root)
    if (
        not _hash(review_sha256)
        or item["generation"] >= 262144
        or len(new) < len(prior)
        or sum(h.count for h in new) <= sum(h.count for h in prior)
        or new[: max(0, len(prior) - 1)] != prior[:-1]
        or (
            prior
            and (
                new[len(prior) - 1].count < prior[-1].count
                or new[len(prior) - 1].byte_length < prior[-1].byte_length
            )
        )
    ):
        raise PublicationError("invalid reviewed strict publication extension")
    candidate = canonical_json_bytes(
        dict(
            version=1,
            generation=item["generation"] + 1,
            spec_sha256=root,
            previous=previous_sha256,
            manifest=parse_canonical_json(candidate_manifest),
            review=review_sha256,
        )
    )
    _record(spec, candidate, _sha(candidate))
    return PreparedPublication(previous, previous_sha256, candidate, _sha(candidate))


@dataclass(frozen=True, slots=True)
class ManifestOwner:
    """Cooperating writers MUST hold this owner's lock for ALL page mutations.

    Closed trusted namespace only. Never discovers a latest trusted root. Write
    errors leave uncertainty and return no receipt. Read does not repair it.
    """

    path: Path
    pages: Path
    spec: RunSpec

    def __post_init__(self) -> None:
        declaration_root(self.spec)
        if any(
            not isinstance(p, Path) or not p.is_absolute()
            for p in (self.path, self.pages)
        ):
            raise PublicationError("absolute owner/page Paths required")
        path = resolve_ledger_path(self.path)
        pages = resolve_ledger_path(self.pages / "page-0000.jsonl").parent
        if path.is_relative_to(pages) or not path.parent.is_dir() or not pages.is_dir():
            raise PublicationError(
                "owner must be outside existing closed page directory"
            )
        object.__setattr__(self, "path", path)
        object.__setattr__(self, "pages", pages)

    def _lock(self):
        path = resolve_ledger_path(self.path.with_name(self.path.name + ".lock"))
        if path.exists():
            self._regular(path)
        return exclusive_file_lock(path)

    @staticmethod
    def _regular(path: Path) -> None:
        info = resolve_ledger_path(path).lstat()
        if not stat.S_ISREG(info.st_mode) or info.st_nlink != 1:
            raise PublicationError("single-link regular owner/lock required")

    def _load(self) -> bytes:
        self._regular(self.path)
        with self.path.open("rb") as handle:
            info = os.fstat(handle.fileno())
            if (
                not stat.S_ISREG(info.st_mode)
                or info.st_nlink != 1
                or info.st_size > _MAX_BYTES
            ):
                raise PublicationError("unsafe or oversized owner")
            data = handle.read(_MAX_BYTES + 1)
        if not 0 < len(data) <= _MAX_BYTES:
            raise PublicationError("bounded nonempty owner required")
        return data

    def create(self) -> PublishedManifest:
        manifest = canonical_json_bytes(
            dict(version=1, spec_sha256=declaration_root(self.spec), pages=[])
        )
        data = canonical_json_bytes(
            dict(
                version=1,
                generation=0,
                spec_sha256=declaration_root(self.spec),
                previous=None,
                manifest=parse_canonical_json(manifest),
                review=None,
            )
        )
        with self._lock():
            if self.path.exists():
                raise FileExistsError(self.path)
            view = read_paged_history(self.pages, self.spec, manifest, _sha(manifest))
            atomic_write_bytes(self.path, data)
            return PublishedManifest(data, _sha(data), view)

    def read(self, expected_sha256: str) -> PublishedManifest:
        if not _hash(expected_sha256):
            raise PublicationError("independent expected current root required")
        with self._lock():
            data = self._load()
            if _sha(data) != expected_sha256:
                raise PublicationConflict("owner differs from expected current record")
            _, manifest = _record(self.spec, data, expected_sha256)
            view = read_paged_history(self.pages, self.spec, manifest, _sha(manifest))
            return PublishedManifest(data, expected_sha256, view)

    def _prepared(self, prepared: PreparedPublication) -> tuple[bytes, bytes]:
        if type(prepared) is not PreparedPublication:
            raise PublicationError("exact prepared publication required")
        item, manifest = _record(
            self.spec, prepared.candidate, prepared.candidate_sha256
        )
        rebuilt = prepare_publication(
            self.spec,
            prepared.previous,
            prepared.previous_sha256,
            manifest,
            _sha(manifest),
            item["review"],
        )
        if rebuilt != prepared:
            raise PublicationError("prepared envelope does not match exact transition")
        _, old = _record(self.spec, prepared.previous, prepared.previous_sha256)
        return old, manifest

    def _commit(
        self, prepared: PreparedPublication, reconcile: bool
    ) -> PublishedManifest:
        old, candidate = self._prepared(prepared)
        with self._lock():
            observed = self._load()
            expected = prepared.candidate if reconcile else prepared.previous
            if observed != expected:
                raise PublicationConflict(
                    "owner is not the exact publication predecessor/candidate"
                )
            view = verify_paged_extension(
                self.pages, self.spec, old, _sha(old), candidate, _sha(candidate)
            )
            atomic_write_bytes(self.path, prepared.candidate)
            return PublishedManifest(
                prepared.candidate, prepared.candidate_sha256, view
            )

    def publish(self, prepared: PreparedPublication) -> PublishedManifest:
        return self._commit(prepared, False)

    def reconcile(self, prepared: PreparedPublication) -> PublishedManifest:
        """Re-acknowledge only the exact already-visible candidate, no new generation."""
        return self._commit(prepared, True)
