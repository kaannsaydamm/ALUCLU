from __future__ import annotations

import importlib.util
from pathlib import Path
from types import ModuleType


def _load_harness() -> ModuleType:
    script = Path(__file__).parents[1] / "scripts" / "verify_alc_r0_host.py"
    spec = importlib.util.spec_from_file_location("verify_alc_r0_host", script)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_two_host_observations_use_one_ephemeral_commit_export(
    tmp_path: Path,
    monkeypatch,
) -> None:
    harness = _load_harness()
    snapshot = tmp_path / "snapshot"
    snapshot.mkdir()
    exported_roots: list[Path] = []
    commits: list[str] = []

    def fake_export(source_commit: str, destination: Path) -> None:
        commits.append(source_commit)
        destination.mkdir()
        (destination / "immutable-marker").write_text(source_commit, encoding="utf-8")

    def fake_observation(snapshot_arg: Path, *, project_root: Path):
        assert snapshot_arg == snapshot
        assert (project_root / "immutable-marker").read_text(encoding="utf-8") == (
            "a" * 40
        )
        exported_roots.append(project_root)
        return {"worker": len(exported_roots)}

    monkeypatch.setattr(harness, "_export_source_commit", fake_export)
    monkeypatch.setattr(harness, "_fresh_observation", fake_observation)

    observations = harness._fresh_observations_from_commit(snapshot, "a" * 40)

    assert observations == [{"worker": 1}, {"worker": 2}]
    assert commits == ["a" * 40]
    assert len(set(exported_roots)) == 1
    assert exported_roots[0] != harness.PROJECT_ROOT
    assert not exported_roots[0].exists()


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
