from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

from aluclu.alc_r0.source_checkout import (
    SourceCheckoutError,
    inspect_clean_source_checkout,
    verify_frozen_source_checkout,
)


def _git(root: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", *args],
        cwd=root,
        capture_output=True,
        check=True,
        text=True,
    )
    return result.stdout.strip()


@pytest.fixture
def repository(tmp_path: Path) -> Path:
    root = tmp_path / "checkout"
    root.mkdir()
    _git(root, "init", "--quiet")
    _git(root, "config", "user.name", "ALC-R0 Test")
    _git(root, "config", "user.email", "alc-r0@example.invalid")
    _git(root, "config", "core.autocrlf", "false")
    (root / "source.py").write_bytes(b"print('frozen')\n")
    _git(root, "add", "source.py")
    _git(root, "commit", "--quiet", "-m", "freeze fixture")
    return root


def test_clean_checkout_receipt_is_stable_and_verifiable(repository: Path) -> None:
    receipt = inspect_clean_source_checkout(repository)

    assert receipt.source_commit == _git(repository, "rev-parse", "HEAD")
    assert len(receipt.source_tree_sha256) == 64
    assert receipt.tracked_file_count == 1
    assert (
        verify_frozen_source_checkout(
            repository,
            expected_commit=receipt.source_commit,
            expected_source_tree_sha256=receipt.source_tree_sha256,
        )
        == receipt
    )


@pytest.mark.parametrize("change", ["tracked", "untracked", "staged"])
def test_checkout_rejects_any_porcelain_change(repository: Path, change: str) -> None:
    if change == "untracked":
        (repository / "new.py").write_bytes(b"pass\n")
    else:
        (repository / "source.py").write_bytes(b"print('changed')\n")
        if change == "staged":
            _git(repository, "add", "source.py")

    with pytest.raises(SourceCheckoutError, match="not clean"):
        inspect_clean_source_checkout(repository)


def test_checkout_rejects_wrong_commit_or_tree_digest(repository: Path) -> None:
    receipt = inspect_clean_source_checkout(repository)

    with pytest.raises(SourceCheckoutError, match="commit mismatch"):
        verify_frozen_source_checkout(
            repository,
            expected_commit="0" * 40,
            expected_source_tree_sha256=receipt.source_tree_sha256,
        )
    with pytest.raises(SourceCheckoutError, match="tree digest mismatch"):
        verify_frozen_source_checkout(
            repository,
            expected_commit=receipt.source_commit,
            expected_source_tree_sha256="0" * 64,
        )


@pytest.mark.parametrize("flag", ["--assume-unchanged", "--skip-worktree"])
def test_checkout_rejects_index_flags_that_hide_dirty_bytes(
    repository: Path, flag: str
) -> None:
    _git(repository, "update-index", flag, "source.py")
    (repository / "source.py").write_bytes(b"print('hidden change')\n")

    with pytest.raises(SourceCheckoutError, match="index flag"):
        inspect_clean_source_checkout(repository)


def test_equal_git_tree_content_has_equal_digest_across_commits(
    repository: Path,
) -> None:
    first = inspect_clean_source_checkout(repository)
    _git(repository, "commit", "--allow-empty", "--quiet", "-m", "same tree")

    second = inspect_clean_source_checkout(repository)

    assert first.source_commit != second.source_commit
    assert first.source_tree_sha256 == second.source_tree_sha256


def test_changed_committed_bytes_change_source_digest(repository: Path) -> None:
    first = inspect_clean_source_checkout(repository)
    (repository / "source.py").write_bytes(b"print('new source')\n")
    _git(repository, "add", "source.py")
    _git(repository, "commit", "--quiet", "-m", "change source")

    second = inspect_clean_source_checkout(repository)

    assert first.source_tree_sha256 != second.source_tree_sha256


def test_checkout_rejects_gitlink_until_submodule_verification_exists(
    repository: Path,
) -> None:
    vendor_source = repository.parent / "vendor-source"
    vendor_source.mkdir()
    _git(vendor_source, "init", "--quiet")
    _git(vendor_source, "config", "user.name", "ALC-R0 Test")
    _git(vendor_source, "config", "user.email", "alc-r0@example.invalid")
    (vendor_source / "vendor.py").write_bytes(b"pass\n")
    _git(vendor_source, "add", "vendor.py")
    _git(vendor_source, "commit", "--quiet", "-m", "vendor fixture")
    _git(
        repository,
        "-c",
        "protocol.file.allow=always",
        "submodule",
        "add",
        "--quiet",
        str(vendor_source),
        "vendor",
    )
    _git(repository, "commit", "--quiet", "-m", "gitlink fixture")

    with pytest.raises(SourceCheckoutError, match="submodule"):
        inspect_clean_source_checkout(repository)


def test_checkout_rejects_nested_root(repository: Path) -> None:
    nested = repository / "nested"
    nested.mkdir()

    with pytest.raises(SourceCheckoutError, match="repository root"):
        inspect_clean_source_checkout(nested)
