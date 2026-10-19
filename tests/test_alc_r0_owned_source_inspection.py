"""Owned harmless Git fixtures; no model, CUDA, or scientific authority."""
import importlib
import json
import os
import shutil
import stat
import sys
from dataclasses import asdict
from pathlib import Path

import pytest

from aluclu.alc_r0.source_checkout import inspect_clean_source_checkout
from test_alc_r0_source_checkout import repository, _git
from test_alc_r0_reserved_owned_process import ROOT, fixture
from test_alc_r0_owned_stop import RetainedHandles

pytestmark = pytest.mark.skipif(os.name != 'nt', reason='Windows owned inspection')


def api():
    return importlib.import_module('aluclu.alc_r0.owned_source_inspection')


def inspect_owned(tmp_path, repository, *, bounds=None, seconds=15, expired=False):
    api()
    from aluclu.alc_r0.reserved_owned_process import ReservedOwnedLease
    bounds = bounds or dict(metadata_bytes=4096, file_count=100,
                           blob_bytes=1_000_000, total_blob_bytes=2_000_000)
    source = (
        'import os,json;from pathlib import Path;from dataclasses import asdict;'
        'from aluclu.alc_r0.owned_source_inspection import inspect_owned_source_checkout,SourceInspectionBounds;'
        f'b=SourceInspectionBounds(**{bounds!r});'
        'try:\n'
    )
    # Newline before try is intentional: a compound statement cannot follow ';'.
    source = source.replace(';try:\n', '\ntry:\n')
    arguments, store, reserved, _ = fixture(tmp_path, seconds=seconds,
                                           stdout_cap=2048, stderr_cap=4096)
    deadline = 1 if expired else arguments['deadline_ns']
    source += (
        f' r=inspect_owned_source_checkout(Path({str(repository)!r}),'
        f'git_executable=Path({shutil.which("git")!r}),environment=dict(os.environ),'
        f'deadline_ns={deadline},bounds=b)\n'
        ' print(json.dumps(dict(ok=True,evidence=asdict(r))))\n'
        'except ValueError as e:\n print(json.dumps(dict(ok=False,error=str(e))))\n'
    )
    environment = dict(os.environ, PYTHONPATH=str(Path(__file__).resolve().parents[1] / 'src'),
                       PYTHONNOUSERSITE='1', PYTHONDONTWRITEBYTECODE='1', CUDA_VISIBLE_DEVICES='-1')
    arguments.update(command=(sys.executable, '-c', source), environment=environment)
    with ReservedOwnedLease(**arguments) as lease:
        retained = RetainedHandles(lease)
        try:
            ready = lease.publish_identity(ROOT, ROOT)
            running = lease.resume_verified(ready.sha256)
            terminal = lease.wait_terminal()
            retained.drained(exit_code=terminal.process.exit_code)
        finally:
            retained.close()
    assert terminal.process.active_processes == 0
    assert terminal.output.valid
    assert arguments['stderr_path'].read_bytes() == b''
    assert store.read(running.sha256).snapshot.reservations[0].state == 'RUNNING'
    data = arguments['stdout_path'].read_bytes()
    return terminal, json.loads(data) if data else None


def test_clean_source_matches_existing_oracle(tmp_path, repository):
    expected = inspect_clean_source_checkout(repository)
    native, result = inspect_owned(tmp_path, repository)
    assert native.process.exit_code == 0 and not native.process.timed_out
    assert native.process.total_processes >= 11  # inspector and real Git commands
    assert result == dict(ok=True, evidence=asdict(expected))


@pytest.mark.parametrize('field,value', [
    ('metadata_bytes', 0), ('metadata_bytes', True), ('metadata_bytes', 4 * 1024**2 + 1),
    ('file_count', 0), ('file_count', 65537), ('blob_bytes', -1),
    ('blob_bytes', 512 * 1024**2 + 1), ('total_blob_bytes', 8 * 1024**3 + 1),
    ('total_blob_bytes', 1.0),
])
def test_exact_finite_bounds(field, value):
    bounds = dict(metadata_bytes=4096, file_count=100, blob_bytes=100, total_blob_bytes=100)
    bounds[field] = value
    with pytest.raises(ValueError, match='bound'):
        api().SourceInspectionBounds(**bounds)


@pytest.mark.parametrize('kind', ['blob', 'total', 'metadata', 'count'])
def test_one_beyond_declared_bound_denies(tmp_path, repository, kind):
    # Two files allow independent aggregate and file-count refusal.
    (repository / 'other.py').write_bytes(b'x' * 19)
    _git(repository, 'add', 'other.py')
    _git(repository, 'commit', '--quiet', '-m', 'two blobs')
    bounds = dict(metadata_bytes=4096, file_count=2, blob_bytes=19, total_blob_bytes=35)
    if kind == 'blob':
        bounds.update(blob_bytes=18, total_blob_bytes=100)
    elif kind == 'total':
        bounds.update(total_blob_bytes=34)
    elif kind == 'metadata':
        # The earliest metadata command exceeding 40 bytes must refuse.
        bounds.update(metadata_bytes=40, total_blob_bytes=100)
    else:
        bounds.update(file_count=1, total_blob_bytes=100)
    _, result = inspect_owned(tmp_path, repository, bounds=bounds)
    assert not result['ok'] and 'bound' in result['error']


def test_exact_blob_and_total_bounds_and_empty_blob(tmp_path, repository):
    (repository / 'source.py').write_bytes(b'x' * 65537)
    (repository / 'empty.py').write_bytes(b'')
    _git(repository, 'add', '.')
    _git(repository, 'commit', '--quiet', '-m', 'chunk boundary')
    _, result = inspect_owned(tmp_path, repository, bounds=dict(
        metadata_bytes=4096, file_count=2, blob_bytes=65537, total_blob_bytes=65537))
    assert result == dict(ok=True, evidence=asdict(inspect_clean_source_checkout(repository)))


def test_zero_length_blob_with_zero_allowance(tmp_path, repository):
    (repository / 'source.py').write_bytes(b'')
    _git(repository, 'add', '.')
    _git(repository, 'commit', '--quiet', '-m', 'zero bytes')
    _, result = inspect_owned(tmp_path, repository, bounds=dict(
        metadata_bytes=4096, file_count=1, blob_bytes=0, total_blob_bytes=0))
    assert result == dict(ok=True, evidence=asdict(inspect_clean_source_checkout(repository)))


@pytest.mark.parametrize('change', ['tracked', 'untracked', 'staged',
                                     '--skip-worktree', '--assume-unchanged'])
def test_dirty_and_hidden_index_state_denies(tmp_path, repository, change):
    if change == 'untracked':
        (repository / 'new.py').write_bytes(b'pass')
    else:
        if change.startswith('--'):
            _git(repository, 'update-index', change, 'source.py')
        (repository / 'source.py').write_bytes(b'dirty')
        if change == 'staged':
            _git(repository, 'add', '.')
    _, result = inspect_owned(tmp_path, repository)
    assert not result['ok']
    assert ('index flag' if change.startswith('--') else 'not clean') in result['error']


def test_expired_original_deadline_denies(tmp_path, repository):
    native, result = inspect_owned(tmp_path, repository, expired=True)
    assert not result['ok'] and 'deadline' in result['error']
    assert native.process.total_processes <= 3  # no Git process


def test_wrong_repository_root_denies(tmp_path, repository):
    nested = repository / 'nested'
    nested.mkdir()
    _, result = inspect_owned(tmp_path, nested)
    assert not result['ok'] and 'repository root' in result['error']


def test_changed_commit_and_bytes_preserve_oracle_semantics(tmp_path, repository):
    first_dir = tmp_path / 'first'
    first_dir.mkdir()
    _, first = inspect_owned(first_dir, repository)
    _git(repository, 'commit', '--allow-empty', '--quiet', '-m', 'same tree')
    second_dir = tmp_path / 'second'
    second_dir.mkdir()
    _, second = inspect_owned(second_dir, repository)
    assert first['evidence']['source_commit'] != second['evidence']['source_commit']
    assert first['evidence']['source_tree_sha256'] == second['evidence']['source_tree_sha256']
    (repository / 'source.py').write_bytes(b'new committed bytes\x00\xff')
    _git(repository, 'add', '.')
    _git(repository, 'commit', '--quiet', '-m', 'different tree')
    third_dir = tmp_path / 'third'
    third_dir.mkdir()
    _, third = inspect_owned(third_dir, repository)
    assert third == dict(ok=True, evidence=asdict(inspect_clean_source_checkout(repository)))
    assert first['evidence']['source_tree_sha256'] != third['evidence']['source_tree_sha256']


def test_submodule_denies(tmp_path, repository):
    vendor = repository.parent / 'vendor-source'
    vendor.mkdir()
    _git(vendor, 'init', '--quiet')
    _git(vendor, 'config', 'user.name', 'ALC-R0 Test')
    _git(vendor, 'config', 'user.email', 'alc-r0@example.invalid')
    (vendor / 'vendor.py').write_bytes(b'pass\n')
    _git(vendor, 'add', '.')
    _git(vendor, 'commit', '--quiet', '-m', 'vendor')
    _git(repository, '-c', 'protocol.file.allow=always', 'submodule',
         'add', '--quiet', str(vendor), 'vendor')
    _git(repository, 'commit', '--quiet', '-m', 'gitlink')
    _, result = inspect_owned(tmp_path, repository)
    assert not result['ok'] and 'submodule' in result['error']


def test_nonzero_git_exit_does_not_accept_empty_blob(tmp_path, repository):
    oid = _git(repository, 'rev-parse', 'HEAD:source.py')
    # Delete only the exact disposable fixture blob; cat-file must exit nonzero.
    blob = repository / '.git' / 'objects' / oid[:2] / oid[2:]
    blob.chmod(stat.S_IREAD | stat.S_IWRITE)  # Git objects are read-only on Windows.
    blob.unlink()
    _, result = inspect_owned(tmp_path, repository)
    assert not result['ok'] and 'Git operation failed' in result['error']


def test_real_git_fsmonitor_block_is_owned_and_drained(tmp_path, repository):
    # Trusted fixture Git config calls a deliberately blocking helper during status.
    marker = repository.parent / 'fsmonitor-started'
    helper = repository.parent / 'fsmonitor.py'
    helper.write_text('from pathlib import Path\nimport time\n'
                      f'Path({str(marker)!r}).write_bytes(b"started")\ntime.sleep(60)\n')
    command = f'"{sys.executable.replace(chr(92), chr(47))}" "{str(helper).replace(chr(92), chr(47))}"'
    _git(repository, 'config', 'core.fsmonitor', command)
    native, result = inspect_owned(tmp_path, repository, seconds=4)
    assert marker.read_bytes() == b'started'
    assert native.process.timed_out and native.process.exit_code == 124
    assert native.process.total_processes >= 4
    assert result is None
