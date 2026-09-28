"""Read-only, non-authorizing committed-source check for the R0.0 freeze gate.

The digest binds exact Git blob bytes, modes, and normalized paths. A clean
porcelain status is separately required so a committed inventory cannot stand
in for a dirty development checkout. This module never grants training access.
"""

from __future__ import annotations

import hashlib
import subprocess
from dataclasses import dataclass
from pathlib import Path

from aluclu.alc_r0.canonical import (
    CanonicalEvidenceError,
    canonical_json_bytes,
    validate_evidence_paths,
)


class SourceCheckoutError(ValueError):
    """Raised when committed source cannot be bound to a clean checkout."""


@dataclass(frozen=True)
class SourceCheckoutEvidence:
    source_commit: str
    source_tree_sha256: str
    tracked_file_count: int


def _git(root: Path, *arguments: str) -> bytes:
    try:
        result = subprocess.run(
            ["git", *arguments],
            cwd=root,
            capture_output=True,
            check=False,
        )
    except OSError as exc:
        raise SourceCheckoutError("Git is unavailable") from exc
    if result.returncode != 0:
        raise SourceCheckoutError(
            f"Git {arguments[0]} failed with exit {result.returncode}"
        )
    return result.stdout


def _head(root: Path) -> str:
    raw = _git(root, "rev-parse", "--verify", "HEAD")
    try:
        head = raw.decode("ascii").strip()
    except UnicodeDecodeError as exc:
        raise SourceCheckoutError("Git HEAD is not ASCII") from exc
    if len(head) not in (40, 64) or any(
        char not in "0123456789abcdef" for char in head
    ):
        raise SourceCheckoutError("Git HEAD is not a full object ID")
    return head


def _require_root(root: Path) -> Path:
    if not root.is_absolute() or root.is_symlink():
        raise SourceCheckoutError("repository root must be absolute and symlink-free")
    try:
        resolved = root.resolve(strict=True)
        git_root = Path(
            _git(resolved, "rev-parse", "--show-toplevel").decode("utf-8").strip()
        ).resolve(strict=True)
    except (OSError, UnicodeDecodeError) as exc:
        raise SourceCheckoutError("repository root is unavailable") from exc
    if resolved != root or git_root != root:
        raise SourceCheckoutError("path is not the repository root")
    return root


def _require_clean(root: Path) -> None:
    status = _git(
        root,
        "status",
        "--porcelain=v1",
        "--untracked-files=all",
        "--ignore-submodules=none",
        "-z",
    )
    if status:
        raise SourceCheckoutError("checkout is not clean")
    flags = _git(root, "ls-files", "-v", "-z")
    if not flags or not flags.endswith(b"\0"):
        raise SourceCheckoutError("Git index flags are unavailable")
    for entry in flags[:-1].split(b"\0"):
        if not entry.startswith(b"H "):
            raise SourceCheckoutError("unsafe Git index flag")


def _source_tree_digest(root: Path, head: str) -> tuple[str, int]:
    tree = _git(root, "ls-tree", "-r", "-z", head)
    if not tree or not tree.endswith(b"\0"):
        raise SourceCheckoutError("committed source tree is empty or malformed")

    entries: list[dict[str, object]] = []
    for raw_entry in tree[:-1].split(b"\0"):
        try:
            header, raw_path = raw_entry.split(b"\t", 1)
            mode, kind, oid = header.decode("ascii").split(" ")
            path = raw_path.decode("utf-8")
        except (ValueError, UnicodeDecodeError) as exc:
            raise SourceCheckoutError("committed tree entry is malformed") from exc
        if mode == "160000" or kind == "commit":
            raise SourceCheckoutError("submodule verification is not implemented")
        if mode not in {"100644", "100755", "120000"} or kind != "blob":
            raise SourceCheckoutError("unsupported committed tree entry")
        if len(oid) not in (40, 64) or any(c not in "0123456789abcdef" for c in oid):
            raise SourceCheckoutError("committed tree object ID is malformed")
        blob = _git(root, "cat-file", "blob", oid)
        entries.append(
            {
                "path": path,
                "mode": mode,
                "byte_length": len(blob),
                "sha256": hashlib.sha256(blob).hexdigest(),
            }
        )

    entries.sort(key=lambda entry: str(entry["path"]).encode("utf-8"))
    try:
        validate_evidence_paths(str(entry["path"]) for entry in entries)
    except CanonicalEvidenceError as exc:
        raise SourceCheckoutError("committed tree contains unsafe paths") from exc
    return hashlib.sha256(canonical_json_bytes(entries)).hexdigest(), len(entries)


def inspect_clean_source_checkout(repo_root: Path) -> SourceCheckoutEvidence:
    """Bind the exact committed blob tree to one tracked-clean checkout.

    The result is evidence for a future freeze validator, not training authority.
    Gitlinks fail closed until an explicit submodule-state contract exists.
    """

    root = _require_root(repo_root)
    _require_clean(root)
    head = _head(root)
    digest, count = _source_tree_digest(root, head)
    _require_clean(root)
    if _head(root) != head:
        raise SourceCheckoutError("Git HEAD changed during inspection")
    return SourceCheckoutEvidence(head, digest, count)


def verify_frozen_source_checkout(
    repo_root: Path,
    *,
    expected_commit: str,
    expected_source_tree_sha256: str,
) -> SourceCheckoutEvidence:
    """Reject any commit/tree mismatch against an externally frozen receipt."""

    evidence = inspect_clean_source_checkout(repo_root)
    if evidence.source_commit != expected_commit:
        raise SourceCheckoutError("source commit mismatch")
    if evidence.source_tree_sha256 != expected_source_tree_sha256:
        raise SourceCheckoutError("source tree digest mismatch")
    return evidence
