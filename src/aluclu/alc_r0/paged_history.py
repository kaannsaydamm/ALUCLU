"""Manifest-bound per-run page reader; caller owns witness freshness/authority."""

from __future__ import annotations

import hashlib
import os
import stat
from dataclasses import asdict
from pathlib import Path

from aluclu.cognition.persistence import resolve_ledger_path

from .attempt_journal import AttemptJournal, JournalHead
from .attempt_state import AttemptReplay, RunSpec, RunView
from .canonical import (
    CanonicalEvidenceError,
    canonical_json_bytes,
    parse_canonical_json,
)


class PagedHistoryError(ValueError):
    """Manifest, page identity, inventory or operational bound is invalid."""


def _hash(value: object) -> bool:
    return (
        type(value) is str
        and len(value) == 64
        and all(c in "0123456789abcdef" for c in value)
    )


def declaration_root(spec: RunSpec) -> str:
    """Bind the complete ordered declaration, not source/review authorization."""
    AttemptReplay((spec,))  # Reuse the exact declaration validation contract.
    return hashlib.sha256(
        b"ALC-R0-PAGED-DECLARATION-V1\0" + canonical_json_bytes(asdict(spec))
    ).hexdigest()


def _page_head(value: object) -> JournalHead:
    if (
        type(value) is not dict
        or value.keys() != {"count", "byte_length", "digest"}
        or type(value["count"]) is not int
        or not 1 <= value["count"] <= 65536
        or type(value["byte_length"]) is not int
        or not 1 <= value["byte_length"] <= 32 * (1 << 20)
        or not _hash(value["digest"])
    ):
        raise PagedHistoryError("invalid nonempty page head")
    return JournalHead(value["count"], value["byte_length"], value["digest"])


def page_identity(spec_sha256: str, index: int, previous: JournalHead | None) -> str:
    """Derive a journal identity bound to declaration, position and predecessor."""
    if (
        not _hash(spec_sha256)
        or type(index) is not int
        or not 0 <= index < 8
        or (index == 0 and previous is not None)
        or (index > 0 and type(previous) is not JournalHead)
    ):
        raise PagedHistoryError("invalid page predecessor/position")
    prior = None if previous is None else asdict(previous)
    if prior is not None:
        _page_head(prior)
    return hashlib.sha256(
        b"ALC-R0-PAGED-JOURNAL-V1\0"
        + canonical_json_bytes(
            dict(spec_sha256=spec_sha256, index=index, previous=prior)
        )
    ).hexdigest()


def _manifest(data: bytes, expected: str, spec_sha256: str) -> tuple[JournalHead, ...]:
    if (
        type(data) is not bytes
        or not 0 < len(data) <= 8192
        or not _hash(expected)
        or hashlib.sha256(data).hexdigest() != expected
    ):
        raise PagedHistoryError("invalid expected manifest root/bytes")
    try:
        item = parse_canonical_json(data)
    except (CanonicalEvidenceError, RecursionError) as exc:
        raise PagedHistoryError("malformed canonical manifest") from exc
    if (
        type(item) is not dict
        or item.keys() != {"version", "spec_sha256", "pages"}
        or type(item["version"]) is not int
        or item["version"] != 1
        or item["spec_sha256"] != spec_sha256
    ):
        raise PagedHistoryError("manifest schema/declaration mismatch")
    if type(item["pages"]) is not list or len(item["pages"]) > 8:
        raise PagedHistoryError("bounded page list required")
    heads = tuple(_page_head(value) for value in item["pages"])
    if sum(head.count for head in heads) > 262144 or sum(
        head.byte_length for head in heads
    ) > 256 * (1 << 20):
        raise PagedHistoryError("aggregate page bounds exceeded")
    return heads


def _inventory(directory: Path, count: int) -> None:
    pages = {f"page-{index:04d}.jsonl" for index in range(count)}
    allowed = pages | {name + ".lock" for name in pages}
    seen = set()
    with os.scandir(directory) as entries:
        for entry in entries:
            if entry.name not in allowed:
                raise PagedHistoryError("unexpected page directory entry")
            path = resolve_ledger_path(directory / entry.name)
            info = path.lstat()
            if not stat.S_ISREG(info.st_mode) or info.st_nlink != 1:
                raise PagedHistoryError("single-link regular page/lock required")
            seen.add(entry.name)
    if not pages <= seen:
        raise PagedHistoryError("missing expected page")


def read_paged_history(
    directory: Path, spec: RunSpec, manifest: bytes, expected_manifest_sha256: str
) -> RunView:
    """Return state only after validating the entire manifest-bound page set.

    Trusted closed namespace/cooperating writers only, no concurrent rotation.
    Expected root needs an independent current monotone owner; old root + old
    pages cannot reveal rollback. This is not a witness publisher or permit.
    Existing storage reads may create lock companions. No partial view escapes.
    """
    root = declaration_root(spec)
    heads = _manifest(manifest, expected_manifest_sha256, root)
    if not isinstance(directory, Path) or not directory.is_absolute():
        raise PagedHistoryError("absolute page directory Path required")
    directory = resolve_ledger_path(directory / "page-0000.jsonl").parent
    if not directory.is_dir():
        raise PagedHistoryError("page directory must already exist")
    _inventory(directory, len(heads))
    replay = AttemptReplay((spec,))
    previous = None
    for index, head in enumerate(heads):
        journal = AttemptJournal(
            directory / f"page-{index:04d}.jsonl", page_identity(root, index, previous)
        )
        snapshot = journal.read(head)
        for event in snapshot.events:
            replay.append(event)
        previous = head
    _inventory(directory, len(heads))
    return replay.snapshot()[0]
