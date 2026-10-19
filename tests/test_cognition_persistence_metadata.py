"""One coherent classification per call; not hostile-namespace race protection."""
import os
from pathlib import Path
import stat
import subprocess
from types import SimpleNamespace

import pytest

from aluclu.cognition.persistence import _is_link_or_reparse, resolve_ledger_path
from aluclu.cognition.contracts import UnsafePathError


class ObservedPath:
    """Explicit observation seam; no monkeypatch or global filesystem mutation."""
    def __init__(self, first, later=None):
        self.first=first
        self.later=first if later is None else later
        self.calls=0

    def lstat(self):
        self.calls+=1
        value=self.first if self.calls==1 else self.later
        if isinstance(value,Exception): raise value
        return value

    def is_symlink(self):
        return stat.S_ISLNK(self.lstat().st_mode)


@pytest.mark.parametrize('mode,attributes,expected',[
    (stat.S_IFREG,0,False),(stat.S_IFDIR,0,False),
    (stat.S_IFLNK,0,True),(stat.S_IFLNK,0x400,True),
    (stat.S_IFDIR,0x400,True),(stat.S_IFREG,0x400,True),
    (stat.S_IFREG,0x20,False),
])
def test_one_metadata_observation_classifies_both_categories(mode,attributes,expected):
    path=ObservedPath(SimpleNamespace(st_mode=mode,st_file_attributes=attributes))
    assert _is_link_or_reparse(path) is expected
    assert path.calls==1


def test_posix_snapshot_without_windows_attributes():
    path=ObservedPath(SimpleNamespace(st_mode=stat.S_IFLNK))
    assert _is_link_or_reparse(path) is True
    assert path.calls==1


@pytest.mark.parametrize('first,later,expected',[
    (stat.S_IFLNK,stat.S_IFREG,True),(stat.S_IFREG,stat.S_IFLNK,False),
])
def test_classification_is_first_snapshot_not_mixed_mutation_samples(first,later,expected):
    path=ObservedPath(SimpleNamespace(st_mode=first),SimpleNamespace(st_mode=later))
    assert _is_link_or_reparse(path) is expected
    assert path.calls==1


def test_missing_path_preserves_false():
    path=ObservedPath(FileNotFoundError('missing'))
    assert _is_link_or_reparse(path) is False
    assert path.calls==1


@pytest.mark.parametrize('error',[PermissionError('denied'),OSError('I/O failure')])
def test_other_metadata_error_is_not_silently_accepted(error):
    path=ObservedPath(error)
    with pytest.raises(type(error)) as caught: _is_link_or_reparse(path)
    assert caught.value is error
    assert path.calls==1


def test_actual_regular_directory_file_and_missing(tmp_path):
    target=tmp_path/'regular'
    target.write_bytes(b'unchanged')
    assert _is_link_or_reparse(target) is False
    assert _is_link_or_reparse(tmp_path) is False
    assert _is_link_or_reparse(tmp_path/'missing') is False


@pytest.mark.parametrize('kind',['file','directory','dangling'])
def test_actual_symlink_is_rejected(tmp_path,kind):
    target=tmp_path/'target'
    if kind=='file': target.write_bytes(b'unchanged')
    if kind=='directory': target.mkdir()
    link=tmp_path/'link'
    try: link.symlink_to(target,target_is_directory=kind=='directory')
    except (OSError,NotImplementedError): pytest.skip('native symlink capability unavailable')
    assert _is_link_or_reparse(link) is True
    with pytest.raises(UnsafePathError): resolve_ledger_path(link)


@pytest.mark.skipif(os.name!='nt',reason='actual Windows junction')
def test_actual_junction_is_rejected(tmp_path):
    target=tmp_path/'target'
    target.mkdir()
    link=tmp_path/'junction'
    shell=Path(os.environ['SystemRoot'])/'System32/cmd.exe'
    result=subprocess.run([str(shell),'/d','/c','mklink','/J',str(link),str(target)],
        capture_output=True,timeout=10)
    assert result.returncode==0,(result.stdout,result.stderr)
    assert _is_link_or_reparse(link) is True
    with pytest.raises(UnsafePathError): resolve_ledger_path(link/'state.bin')
