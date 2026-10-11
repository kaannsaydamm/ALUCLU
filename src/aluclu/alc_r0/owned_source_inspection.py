"""Finite Git inventory INSIDE an externally owned, deadline-enforced child.

This callable does not establish ownership, provenance or launch authority.
Blocking pipe reads require the outer ReservedOwnedLease's original deadline.
Git/configuration/environment are trusted; native Git memory is not capped here.
"""
from __future__ import annotations

import hashlib
import subprocess
import time
from dataclasses import dataclass
from pathlib import Path

from .canonical import CanonicalEvidenceError, canonical_json_bytes, validate_evidence_paths
from .source_checkout import SourceCheckoutError, SourceCheckoutEvidence

_CHUNK = 65536
_MAX = (1 << 63) - 1


@dataclass(frozen=True, slots=True)
class SourceInspectionBounds:
    metadata_bytes: int
    file_count: int
    blob_bytes: int
    total_blob_bytes: int

    def __post_init__(self):
        for value, minimum, maximum in (
            (self.metadata_bytes, 1, 4 * 1024**2),
            (self.file_count, 1, 65536),
            (self.blob_bytes, 0, 512 * 1024**2),
            (self.total_blob_bytes, 0, 8 * 1024**3),
        ):
            if type(value) is not int or not minimum <= value <= maximum:
                raise SourceCheckoutError('invalid source inspection bound')


def _oid(value):
    return len(value) in (40, 64) and all(c in '0123456789abcdef' for c in value)


class _Inspector:
    def __init__(self, root, git, environment, deadline, bounds):
        if type(bounds) is not SourceInspectionBounds:
            raise SourceCheckoutError('exact source inspection bounds required')
        SourceInspectionBounds.__post_init__(bounds)
        if type(deadline) is not int or not 0 < deadline <= _MAX:
            raise SourceCheckoutError('invalid original deadline')
        if type(environment) is not dict or any(
            type(k) is not str or type(v) is not str or not k or '=' in k
            or '\0' in k or '\0' in v for k, v in environment.items()
        ):
            raise SourceCheckoutError('explicit string environment required')
        for path in (root, git):
            if not isinstance(path, Path) or not path.is_absolute() or path.is_symlink():
                raise SourceCheckoutError('absolute resolved paths required')
            try:
                if path.resolve(strict=True) != path:
                    raise SourceCheckoutError('absolute resolved paths required')
            except OSError as exc:
                raise SourceCheckoutError('source inspection path unavailable') from exc
        if not root.is_dir() or not git.is_file():
            raise SourceCheckoutError('repository and Git binary required')
        self.root, self.git = root, git
        self.environment, self.deadline, self.bounds = dict(environment), deadline, bounds
        self.total = 0

    def check_deadline(self):
        if time.monotonic_ns() >= self.deadline:
            raise SourceCheckoutError('original source inspection deadline expired')

    def _read(self, arguments, limit, *, blob=False):
        self.check_deadline()
        try:
            process = subprocess.Popen((str(self.git), *arguments), cwd=self.root,
                env=self.environment, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE,
                stderr=subprocess.DEVNULL, bufsize=0)
        except OSError as exc:
            raise SourceCheckoutError('Git unavailable during source inspection') from exc
        data, digest, count = bytearray(), hashlib.sha256(), 0
        try:
            while True:
                self.check_deadline()
                # Only one overflow-detection byte is read beyond the allowance.
                chunk = process.stdout.read(min(_CHUNK, limit - count + 1))
                self.check_deadline()
                if not chunk:
                    break
                count += len(chunk)
                if count > limit:
                    raise SourceCheckoutError('Git output exceeds source inspection bound')
                if blob:
                    digest.update(chunk)
                else:
                    data.extend(chunk)
            self.check_deadline()
            code = process.wait(timeout=max(0, (self.deadline - time.monotonic_ns()) / 1e9))
            if code:
                raise SourceCheckoutError('Git operation failed during source inspection')
            self.check_deadline()
            return (count, digest.hexdigest()) if blob else bytes(data)
        except subprocess.TimeoutExpired as exc:
            raise SourceCheckoutError('original source inspection deadline expired') from exc
        finally:
            # No unbounded Popen context-manager wait. The outer owned job remains
            # responsible for descendants, including blocked helpers after errors.
            process.stdout.close()
            if process.poll() is None:
                process.kill()
            try:
                process.wait(timeout=max(0, (self.deadline - time.monotonic_ns()) / 1e9))
            except subprocess.TimeoutExpired as exc:
                raise SourceCheckoutError('Git terminal state unobserved before deadline') from exc

    def metadata(self, *arguments):
        return self._read(arguments, self.bounds.metadata_bytes)

    def head(self):
        try:
            head = self.metadata('rev-parse', '--verify', 'HEAD').decode('ascii').strip()
        except UnicodeDecodeError as exc:
            raise SourceCheckoutError('Git HEAD is not ASCII') from exc
        if not _oid(head):
            raise SourceCheckoutError('Git HEAD is not a full object ID')
        return head

    def require_root(self):
        try:
            root = Path(self.metadata('rev-parse', '--show-toplevel').decode('utf-8').strip())
            if root.resolve(strict=True) != self.root:
                raise SourceCheckoutError('path is not the repository root')
        except (OSError, UnicodeDecodeError) as exc:
            raise SourceCheckoutError('repository root unavailable') from exc

    def require_clean(self):
        if self.metadata('status', '--porcelain=v1', '--untracked-files=all',
                         '--ignore-submodules=none', '-z'):
            raise SourceCheckoutError('checkout is not clean')
        flags = self.metadata('ls-files', '-v', '-z')
        if not flags or not flags.endswith(b'\0'):
            raise SourceCheckoutError('Git index flags unavailable')
        for entry in flags[:-1].split(b'\0'):
            self.check_deadline()
            if not entry.startswith(b'H '):
                raise SourceCheckoutError('unsafe Git index flag')

    def tree(self, head):
        tree = self.metadata('ls-tree', '-r', '-z', head)
        if not tree or not tree.endswith(b'\0'):
            raise SourceCheckoutError('committed source tree empty or malformed')
        if tree.count(b'\0') > self.bounds.file_count:
            raise SourceCheckoutError('committed file count exceeds source inspection bound')
        parsed = []
        for entry in tree[:-1].split(b'\0'):
            self.check_deadline()
            try:
                header, path = entry.split(b'\t', 1)
                mode, kind, oid = header.decode('ascii').split(' ')
                path = path.decode('utf-8')
            except (ValueError, UnicodeDecodeError) as exc:
                raise SourceCheckoutError('committed tree entry malformed') from exc
            if mode == '160000' or kind == 'commit':
                raise SourceCheckoutError('submodule verification is not implemented')
            if mode not in {'100644', '100755', '120000'} or kind != 'blob' or not _oid(oid):
                raise SourceCheckoutError('unsupported committed tree entry')
            parsed.append((path, mode, oid))
        try:
            validate_evidence_paths(row[0] for row in parsed)
        except CanonicalEvidenceError as exc:
            raise SourceCheckoutError('committed tree contains unsafe paths') from exc
        parsed.sort(key=lambda row: row[0].encode('utf-8'))
        inventory = []
        for path, mode, oid in parsed:
            self.check_deadline()
            limit = min(self.bounds.blob_bytes, self.bounds.total_blob_bytes - self.total)
            length, digest = self._read(('cat-file', 'blob', oid), limit, blob=True)
            self.total += length
            inventory.append(dict(path=path, mode=mode, byte_length=length, sha256=digest))
        self.check_deadline()
        digest = hashlib.sha256(canonical_json_bytes(inventory)).hexdigest()
        self.check_deadline()
        return digest, len(inventory)


def inspect_owned_source_checkout(repo_root: Path, *, git_executable: Path,
        environment: dict[str, str], deadline_ns: int,
        bounds: SourceInspectionBounds) -> SourceCheckoutEvidence:
    """Inspect exact committed bytes inside a caller-owned, deadline-enforced job.

    No standalone execution-time guarantee or verified launch context is supplied.
    The caller must observe the entire owned tree terminal before accepting this
    evidence. A returned digest is neither source provenance nor training consent.
    """
    inspector = _Inspector(repo_root, git_executable, environment, deadline_ns, bounds)
    inspector.check_deadline()
    inspector.require_root()
    inspector.require_clean()
    head = inspector.head()
    digest, count = inspector.tree(head)
    inspector.require_clean()
    if inspector.head() != head:
        raise SourceCheckoutError('Git HEAD changed during inspection')
    inspector.check_deadline()
    return SourceCheckoutEvidence(head, digest, count)
