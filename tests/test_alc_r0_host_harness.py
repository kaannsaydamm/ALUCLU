from __future__ import annotations

import importlib.util
import subprocess
from contextlib import contextmanager
from pathlib import Path
from types import ModuleType, SimpleNamespace
from typing import cast

import pytest


def _load_harness() -> ModuleType:
    script = Path(__file__).parents[1] / "scripts" / "verify_alc_r0_host.py"
    spec = importlib.util.spec_from_file_location("verify_alc_r0_host", script)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_bootstrap_reexecutes_parent_from_ephemeral_commit_export(
    tmp_path: Path,
    monkeypatch,
) -> None:
    harness = _load_harness()
    project_root = tmp_path / "project"
    project_root.mkdir()
    snapshot = tmp_path / "snapshot"
    snapshot.mkdir()
    schema_root = project_root / "schemas"
    schema_root.mkdir()
    windows_lock = project_root / "windows.lock"
    windows_lock.write_bytes(b"lock")
    lock_manifest = project_root / "manifest.json"
    lock_manifest.write_bytes(b"{}")
    output_root = tmp_path / "output"
    output_root.mkdir()
    export_root = tmp_path / "commit-export"
    captured: dict[str, object] = {}

    @contextmanager
    def fake_exported_source(source_commit: str):
        assert source_commit == "a" * 40
        yield export_root

    def fake_run(command, **kwargs):
        captured["command"] = command
        captured.update(kwargs)
        return subprocess.CompletedProcess(command, 0, stdout=b"proof\n", stderr=b"")

    monkeypatch.setattr(harness, "PROJECT_ROOT", project_root)
    monkeypatch.setattr(harness, "_assert_tracked_clean", lambda: None)
    monkeypatch.setattr(harness, "_source_commit", lambda: "a" * 40)
    monkeypatch.setattr(harness, "_exported_source", fake_exported_source)
    monkeypatch.setattr(harness.subprocess, "run", fake_run)
    args = SimpleNamespace(
        snapshot=snapshot,
        schema_root=schema_root,
        windows_lock=windows_lock,
        lock_manifest=lock_manifest,
        acquisition_output=output_root / "acquisition.json",
        base_output=output_root / "base.json",
        expected_source_commit="a" * 40,
    )

    harness._bootstrap_parent(args)

    command = cast(list[str], captured["command"])
    environment = cast(dict[str, str], captured["env"])
    assert command[1] == str(export_root / "scripts/verify_alc_r0_host.py")
    assert "--committed-parent" in command
    assert captured["cwd"] == export_root
    assert environment["PYTHONPATH"] == str(export_root / "src")
    assert environment[harness._COMMITTED_PARENT_ENV] == "a" * 40


def test_commit_export_contains_exact_tracked_host_source(tmp_path: Path) -> None:
    harness = _load_harness()
    source_commit = harness._source_commit()
    export_root = tmp_path / "source"
    second_export_root = tmp_path / "second-source"

    harness._export_source_commit(source_commit, export_root)
    harness._export_source_commit(source_commit, second_export_root)

    for relative in (
        Path("scripts/verify_alc_r0_host.py"),
        Path("src/aluclu/alc_r0/host.py"),
        Path("schemas/alc_r0/v1/acquisition-receipt.schema.json"),
        Path("locks/alc_r0/v1/windows-training.lock"),
    ):
        assert (export_root / relative).read_bytes() == (
            second_export_root / relative
        ).read_bytes()
    assert not (export_root / ".git").exists()


@pytest.mark.parametrize(
    "unsafe",
    [
        "C:/escape.txt",
        "../escape.txt",
        "/absolute.txt",
        "a\\b.txt",
        "a:b.txt",
        "COM¹.json",
        "LPT³.txt",
        "a?.txt",
    ],
)
def test_archive_path_guard_rejects_windows_and_posix_escape(unsafe: str) -> None:
    harness = _load_harness()

    with pytest.raises(RuntimeError, match="unsafe path"):
        harness._safe_archive_parts(unsafe)
