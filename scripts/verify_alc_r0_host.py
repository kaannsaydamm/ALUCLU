from __future__ import annotations

import argparse
import contextlib
import hashlib
import os
import re
import stat
import subprocess
import sys
import tempfile
import zipfile
from collections.abc import Iterator
from pathlib import Path, PurePosixPath

PROJECT_ROOT = Path(__file__).resolve().parents[1]
_WINDOWS_DEVICE = re.compile(
    r"^(con|prn|aux|nul|com[1-9¹²³]|lpt[1-9¹²³])$",
    re.IGNORECASE,
)
_COMMITTED_PARENT_ENV = "ALUCLU_R0_COMMITTED_PARENT_SHA"


def _absolute_file(path: Path, *, label: str) -> Path:
    if not path.is_absolute():
        raise ValueError(f"{label} must be absolute")
    if path.is_symlink():
        raise ValueError(f"{label} must not be a symlink")
    return path.resolve(strict=True)


def _new_output(path: Path, *, label: str) -> Path:
    if not path.is_absolute():
        raise ValueError(f"{label} must be absolute")
    if path.exists() or path.is_symlink():
        raise ValueError(f"{label} already exists")
    parent = path.parent.resolve(strict=True)
    if parent.is_symlink():
        raise ValueError(f"{label} parent must not be a symlink")
    return parent / path.name


def _exclusive_write(path: Path, data: bytes) -> None:
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=path.name,
        suffix=".tmp",
        dir=path.parent,
    )
    try:
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        os.link(temporary_name, path)
    finally:
        if os.path.exists(temporary_name):
            os.unlink(temporary_name)


def _source_commit() -> str:
    completed = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="strict",
        check=True,
    )
    return completed.stdout.strip()


def _assert_tracked_clean() -> None:
    for arguments in (
        ["git", "diff", "--quiet"],
        ["git", "diff", "--cached", "--quiet"],
    ):
        completed = subprocess.run(arguments, cwd=PROJECT_ROOT, check=False)
        if completed.returncode != 0:
            raise RuntimeError("host evidence requires a tracked-clean source checkout")


def _export_source_commit(source_commit: str, destination: Path) -> None:
    if destination.exists() or destination.is_symlink():
        raise ValueError("source export destination must not exist")
    destination.parent.mkdir(parents=True, exist_ok=True)
    archive_path = destination.parent / f"{destination.name}.zip"
    if archive_path.exists() or archive_path.is_symlink():
        raise ValueError("source export archive path already exists")
    completed = subprocess.run(
        [
            "git",
            "archive",
            "--format=zip",
            f"--output={archive_path}",
            source_commit,
        ],
        cwd=PROJECT_ROOT,
        capture_output=True,
        check=False,
    )
    if completed.returncode != 0:
        raise RuntimeError(f"git archive exited {completed.returncode}")
    destination.mkdir()
    try:
        seen_paths: set[str] = set()
        with zipfile.ZipFile(archive_path) as archive:
            for member in archive.infolist():
                parts = _safe_archive_parts(member.filename)
                folded = "/".join(parts).casefold()
                if folded in seen_paths:
                    raise RuntimeError("commit archive contains colliding paths")
                seen_paths.add(folded)
                mode = (member.external_attr >> 16) & 0xFFFF
                if stat.S_ISLNK(mode):
                    raise RuntimeError("commit archive contains a symlink")
                target = destination.joinpath(*parts)
                try:
                    target.resolve(strict=False).relative_to(
                        destination.resolve(strict=True)
                    )
                except ValueError as exc:
                    raise RuntimeError(
                        "commit archive path escapes export root"
                    ) from exc
                if member.is_dir():
                    target.mkdir(parents=True, exist_ok=True)
                    continue
                target.parent.mkdir(parents=True, exist_ok=True)
                with archive.open(member) as source, target.open("xb") as output:
                    while chunk := source.read(1024 * 1024):
                        output.write(chunk)
    finally:
        archive_path.unlink(missing_ok=True)


def _safe_archive_parts(name: str) -> tuple[str, ...]:
    stripped = name.rstrip("/")
    candidate = PurePosixPath(stripped)
    parts = candidate.parts
    if (
        not stripped
        or "\\" in name
        or ":" in name
        or any(character in '<>"|?*' or ord(character) < 0x20 for character in name)
        or candidate.is_absolute()
        or not parts
        or any(part in {"", ".", ".."} for part in parts)
        or candidate.as_posix() != stripped
    ):
        raise RuntimeError("commit archive contains an unsafe path")
    if any(
        part.endswith((" ", "."))
        or _WINDOWS_DEVICE.fullmatch(part.split(".", 1)[0].rstrip(" "))
        for part in parts
    ):
        raise RuntimeError("commit archive contains a Windows-unsafe path")
    return parts


@contextlib.contextmanager
def _exported_source(source_commit: str) -> Iterator[Path]:
    with tempfile.TemporaryDirectory(prefix="alc-r0-source-") as temporary:
        export_root = Path(temporary) / "source"
        _export_source_commit(source_commit, export_root)
        yield export_root


def _project_relative(path: Path, *, label: str) -> Path:
    try:
        return path.relative_to(PROJECT_ROOT.resolve(strict=True))
    except ValueError as exc:
        raise ValueError(f"{label} must be inside the source checkout") from exc


def _worker(snapshot: Path) -> None:
    from aluclu.alc_r0 import canonical, host, host_evidence

    _assert_module_origins(canonical, host, host_evidence)

    observation = host_evidence.observe_verified_host(host.load_verified_host(snapshot))
    sys.stdout.buffer.write(canonical.canonical_json_bytes(observation))


def _fresh_observation(
    snapshot: Path,
    *,
    project_root: Path,
) -> dict[str, object]:
    from aluclu.alc_r0 import canonical

    _assert_module_origins(canonical)

    environment = dict(os.environ)
    environment.update(
        {
            "HF_DATASETS_OFFLINE": "1",
            "HF_HUB_OFFLINE": "1",
            "PYTHONHASHSEED": "0",
            "PYTHONPATH": str(project_root / "src"),
            "TRANSFORMERS_OFFLINE": "1",
        }
    )
    completed = subprocess.run(
        [
            sys.executable,
            str(project_root / "scripts" / "verify_alc_r0_host.py"),
            "--worker",
            "--snapshot",
            str(snapshot),
        ],
        cwd=project_root,
        env=environment,
        capture_output=True,
        check=False,
    )
    sys.stderr.buffer.write(completed.stderr)
    if completed.returncode != 0:
        raise RuntimeError(f"fresh host worker exited {completed.returncode}")
    observation = canonical.parse_canonical_json(completed.stdout)
    if not isinstance(observation, dict):
        raise RuntimeError("fresh host worker returned a non-object")
    return observation


def _committed_parent(args: argparse.Namespace) -> None:
    from aluclu.alc_r0 import acquisition, canonical, host_evidence, schema_validation

    if os.environ.get(_COMMITTED_PARENT_ENV) != args.expected_source_commit:
        raise RuntimeError("committed parent bootstrap binding is missing")
    if (PROJECT_ROOT / ".git").exists():
        raise RuntimeError("committed parent must run from a Git-free export")
    _assert_module_origins(acquisition, canonical, host_evidence, schema_validation)

    snapshot = _absolute_file(args.snapshot, label="snapshot")
    schema_root = _absolute_file(args.schema_root, label="schema root")
    windows_lock = _absolute_file(args.windows_lock, label="Windows lock")
    lock_manifest = _absolute_file(args.lock_manifest, label="lock manifest")
    acquisition_output = _new_output(
        args.acquisition_output,
        label="acquisition output",
    )
    base_output = _new_output(args.base_output, label="base output")
    if acquisition_output == base_output:
        raise ValueError("acquisition and base outputs must differ")
    acquisition_bytes = canonical.canonical_json_bytes(
        acquisition.verify_model_snapshot(snapshot)
    )
    schema_validation.validate_r0_document(
        acquisition_bytes,
        schema_name="acquisition-receipt",
        schema_root=schema_root,
    )
    observations = [
        _fresh_observation(snapshot, project_root=PROJECT_ROOT),
        _fresh_observation(snapshot, project_root=PROJECT_ROOT),
    ]
    base_receipt = host_evidence.build_host_evidence_receipt(
        observations,
        source_commit=args.expected_source_commit,
        acquisition_receipt_bytes=acquisition_bytes,
        windows_lock_bytes=windows_lock.read_bytes(),
        lock_manifest_bytes=lock_manifest.read_bytes(),
    )
    base_bytes = canonical.canonical_json_bytes(base_receipt)
    schema_validation.validate_r0_document(
        base_bytes,
        schema_name="base-digest-receipt",
        schema_root=schema_root,
    )
    _exclusive_write(acquisition_output, acquisition_bytes)
    _exclusive_write(base_output, base_bytes)
    summary = {
        "acquisition_receipt_sha256": hashlib.sha256(acquisition_bytes).hexdigest(),
        "base_digest_receipt_sha256": hashlib.sha256(base_bytes).hexdigest(),
        "source_commit": args.expected_source_commit,
    }
    sys.stdout.buffer.write(canonical.canonical_json_bytes(summary) + b"\n")


def _assert_module_origins(*modules: object) -> None:
    root = PROJECT_ROOT.resolve(strict=True)
    for module in modules:
        origin = getattr(module, "__file__", None)
        if not isinstance(origin, str):
            raise RuntimeError("host proof module has no filesystem origin")
        try:
            Path(origin).resolve(strict=True).relative_to(root)
        except ValueError as exc:
            raise RuntimeError(
                "host proof imported code outside commit export"
            ) from exc


def _bootstrap_parent(args: argparse.Namespace) -> None:
    snapshot = _absolute_file(args.snapshot, label="snapshot")
    schema_root = _absolute_file(args.schema_root, label="schema root")
    windows_lock = _absolute_file(args.windows_lock, label="Windows lock")
    lock_manifest = _absolute_file(args.lock_manifest, label="lock manifest")
    acquisition_output = _new_output(
        args.acquisition_output,
        label="acquisition output",
    )
    base_output = _new_output(args.base_output, label="base output")
    schema_relative = _project_relative(schema_root, label="schema root")
    windows_lock_relative = _project_relative(windows_lock, label="Windows lock")
    lock_manifest_relative = _project_relative(lock_manifest, label="lock manifest")
    _assert_tracked_clean()
    source_commit = _source_commit()
    if source_commit != args.expected_source_commit:
        raise RuntimeError("current HEAD does not match expected source commit")

    with _exported_source(source_commit) as project_root:
        environment = dict(os.environ)
        environment["PYTHONPATH"] = str(project_root / "src")
        environment[_COMMITTED_PARENT_ENV] = source_commit
        completed = subprocess.run(
            [
                sys.executable,
                str(project_root / "scripts" / "verify_alc_r0_host.py"),
                "--committed-parent",
                "--snapshot",
                str(snapshot),
                "--schema-root",
                str(project_root / schema_relative),
                "--windows-lock",
                str(project_root / windows_lock_relative),
                "--lock-manifest",
                str(project_root / lock_manifest_relative),
                "--acquisition-output",
                str(acquisition_output),
                "--base-output",
                str(base_output),
                "--expected-source-commit",
                source_commit,
            ],
            cwd=project_root,
            env=environment,
            capture_output=True,
            check=False,
        )
        sys.stderr.buffer.write(completed.stderr)
        sys.stdout.buffer.write(completed.stdout)
        if completed.returncode != 0:
            raise RuntimeError(f"committed host parent exited {completed.returncode}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Verify the pinned ALC-R0 host twice.")
    parser.add_argument("--worker", action="store_true", help=argparse.SUPPRESS)
    parser.add_argument(
        "--committed-parent",
        action="store_true",
        help=argparse.SUPPRESS,
    )
    parser.add_argument("--snapshot", type=Path, required=True)
    parser.add_argument("--schema-root", type=Path)
    parser.add_argument("--windows-lock", type=Path)
    parser.add_argument("--lock-manifest", type=Path)
    parser.add_argument("--acquisition-output", type=Path)
    parser.add_argument("--base-output", type=Path)
    parser.add_argument("--expected-source-commit")
    args = parser.parse_args()
    if args.worker:
        _worker(_absolute_file(args.snapshot, label="snapshot"))
        return
    required = {
        "schema_root": args.schema_root,
        "windows_lock": args.windows_lock,
        "lock_manifest": args.lock_manifest,
        "acquisition_output": args.acquisition_output,
        "base_output": args.base_output,
        "expected_source_commit": args.expected_source_commit,
    }
    missing = sorted(name for name, value in required.items() if value is None)
    if missing:
        parser.error("missing parent arguments: " + ", ".join(missing))
    if args.committed_parent:
        _committed_parent(args)
    else:
        _bootstrap_parent(args)


if __name__ == "__main__":
    main()
