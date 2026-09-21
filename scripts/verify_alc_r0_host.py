from __future__ import annotations

import argparse
import hashlib
import os
import subprocess
import sys
import tempfile
from pathlib import Path

from aluclu.alc_r0.acquisition import verify_model_snapshot
from aluclu.alc_r0.canonical import (
    canonical_json_bytes,
    parse_canonical_json,
)
from aluclu.alc_r0.host import load_verified_host
from aluclu.alc_r0.host_evidence import (
    build_host_evidence_receipt,
    observe_verified_host,
)
from aluclu.alc_r0.schema_validation import validate_r0_document

PROJECT_ROOT = Path(__file__).resolve().parents[1]


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


def _worker(snapshot: Path) -> None:
    observation = observe_verified_host(load_verified_host(snapshot))
    sys.stdout.buffer.write(canonical_json_bytes(observation))


def _fresh_observation(snapshot: Path) -> dict[str, object]:
    environment = dict(os.environ)
    environment.update(
        {
            "HF_DATASETS_OFFLINE": "1",
            "HF_HUB_OFFLINE": "1",
            "PYTHONHASHSEED": "0",
            "PYTHONPATH": str(PROJECT_ROOT / "src"),
            "TRANSFORMERS_OFFLINE": "1",
        }
    )
    completed = subprocess.run(
        [
            sys.executable,
            str(Path(__file__).resolve()),
            "--worker",
            "--snapshot",
            str(snapshot),
        ],
        cwd=PROJECT_ROOT,
        env=environment,
        capture_output=True,
        check=False,
    )
    sys.stderr.buffer.write(completed.stderr)
    if completed.returncode != 0:
        raise RuntimeError(f"fresh host worker exited {completed.returncode}")
    observation = parse_canonical_json(completed.stdout)
    if not isinstance(observation, dict):
        raise RuntimeError("fresh host worker returned a non-object")
    return observation


def _parent(args: argparse.Namespace) -> None:
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
    _assert_tracked_clean()
    source_commit = _source_commit()
    if source_commit != args.expected_source_commit:
        raise RuntimeError("current HEAD does not match expected source commit")

    acquisition_bytes = canonical_json_bytes(verify_model_snapshot(snapshot))
    validate_r0_document(
        acquisition_bytes,
        schema_name="acquisition-receipt",
        schema_root=schema_root,
    )
    observations = [_fresh_observation(snapshot), _fresh_observation(snapshot)]
    base_receipt = build_host_evidence_receipt(
        observations,
        source_commit=source_commit,
        acquisition_receipt_bytes=acquisition_bytes,
        windows_lock_bytes=windows_lock.read_bytes(),
        lock_manifest_bytes=lock_manifest.read_bytes(),
    )
    base_bytes = canonical_json_bytes(base_receipt)
    validate_r0_document(
        base_bytes,
        schema_name="base-digest-receipt",
        schema_root=schema_root,
    )
    _exclusive_write(acquisition_output, acquisition_bytes)
    _exclusive_write(base_output, base_bytes)
    summary = {
        "acquisition_receipt_sha256": hashlib.sha256(acquisition_bytes).hexdigest(),
        "base_digest_receipt_sha256": hashlib.sha256(base_bytes).hexdigest(),
        "source_commit": source_commit,
    }
    sys.stdout.buffer.write(canonical_json_bytes(summary) + b"\n")


def main() -> None:
    parser = argparse.ArgumentParser(description="Verify the pinned ALC-R0 host twice.")
    parser.add_argument("--worker", action="store_true", help=argparse.SUPPRESS)
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
    _parent(args)


if __name__ == "__main__":
    main()
