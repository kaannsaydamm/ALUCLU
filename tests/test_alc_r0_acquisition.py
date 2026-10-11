from __future__ import annotations

import hashlib
from pathlib import Path

import pytest

from aluclu.alc_r0.acquisition import (
    AcquisitionError,
    SnapshotExpectation,
    verify_model_snapshot,
)


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _snapshot(tmp_path: Path) -> tuple[Path, SnapshotExpectation]:
    root = tmp_path / "snapshot"
    root.mkdir()
    files = {
        "config.json": b'{"model_type":"llama"}',
        "model.safetensors": b"SAFE",
        "tokenizer.json": b'{"version":"1.0"}',
        "tokenizer_config.json": b"{}",
    }
    for relative, data in files.items():
        (root / relative).write_bytes(data)
    expectation = SnapshotExpectation(
        repository="example/model",
        revision="a" * 40,
        required_sha256={relative: _sha256(data) for relative, data in files.items()},
    )
    return root, expectation


def test_verify_model_snapshot_inventories_exact_bytes(tmp_path: Path) -> None:
    root, expectation = _snapshot(tmp_path)
    (root / "README.md").write_text("license", encoding="utf-8")

    receipt = verify_model_snapshot(root.resolve(), expectation=expectation)

    assert receipt["repository"] == "example/model"
    assert receipt["revision"] == "a" * 40
    assert receipt["trust_remote_code"] is False
    assert receipt["safetensors_only"] is True
    assert [item["path"] for item in receipt["files"]] == [
        "README.md",
        "config.json",
        "model.safetensors",
        "tokenizer.json",
        "tokenizer_config.json",
    ]
    assert len(receipt["inventory_sha256"]) == 64


def test_snapshot_expectation_rejects_moving_or_short_revision() -> None:
    with pytest.raises(AcquisitionError, match="40-hex"):
        SnapshotExpectation("example/model", "main", {"config.json": "0" * 64})


def test_verify_model_snapshot_rejects_missing_or_changed_required_file(
    tmp_path: Path,
) -> None:
    root, expectation = _snapshot(tmp_path)
    (root / "config.json").unlink()
    with pytest.raises(AcquisitionError, match="missing"):
        verify_model_snapshot(root.resolve(), expectation=expectation)

    (root / "config.json").write_bytes(b"changed")
    with pytest.raises(AcquisitionError, match="hash mismatch"):
        verify_model_snapshot(root.resolve(), expectation=expectation)


@pytest.mark.parametrize("name", ["weights.bin", "model.pt", "state.ckpt", "x.pkl"])
def test_verify_model_snapshot_rejects_unsafe_weight_formats(
    tmp_path: Path,
    name: str,
) -> None:
    root, expectation = _snapshot(tmp_path)
    (root / name).write_bytes(b"unsafe")

    with pytest.raises(AcquisitionError, match="unsafe weight"):
        verify_model_snapshot(root.resolve(), expectation=expectation)


def test_verify_model_snapshot_rejects_symlinks(tmp_path: Path) -> None:
    root, expectation = _snapshot(tmp_path)
    target = tmp_path / "outside.json"
    target.write_text("{}", encoding="utf-8")
    link = root / "linked.json"
    try:
        link.symlink_to(target)
    except OSError:
        pytest.skip("symlink creation is not available for this Windows token")

    with pytest.raises(AcquisitionError, match="symlink"):
        verify_model_snapshot(root.resolve(), expectation=expectation)


def test_verify_model_snapshot_requires_absolute_root(tmp_path: Path) -> None:
    _, expectation = _snapshot(tmp_path)
    with pytest.raises(AcquisitionError, match="absolute"):
        verify_model_snapshot(Path("relative"), expectation=expectation)


def test_exact_snapshot_expectation_rejects_an_extra_file(tmp_path: Path) -> None:
    root, expectation = _snapshot(tmp_path)
    exact = SnapshotExpectation(
        repository=expectation.repository,
        revision=expectation.revision,
        required_sha256=expectation.required_sha256,
        exact_file_set=True,
    )
    (root / "unexpected.json").write_bytes(b"{}")

    with pytest.raises(AcquisitionError, match="file set"):
        verify_model_snapshot(root.resolve(), expectation=exact)
