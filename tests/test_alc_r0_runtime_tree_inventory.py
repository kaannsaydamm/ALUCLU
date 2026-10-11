"""Harmless owned file-tree diagnostics; no actual runtime/model/GPU scan."""
import hashlib
import importlib
import json
import os
import subprocess
import sys
import time
from dataclasses import asdict
from pathlib import Path

import pytest

from aluclu.alc_r0.canonical import canonical_json_bytes
from test_alc_r0_reserved_owned_process import ROOT, fixture
from test_alc_r0_owned_stop import RetainedHandles

pytestmark = pytest.mark.skipif(os.name != 'nt', reason='Windows owned inventory')


def api():
    return importlib.import_module('aluclu.alc_r0.runtime_tree_inventory')


@pytest.fixture
def tree(tmp_path):
    root = tmp_path / 'installed'
    root.mkdir()
    (root / 'python.dll').write_bytes(b'runtime')
    return root


def inspect_owned(tmp_path, tree, *, bounds=None, component='python-venv', expired=False):
    api()
    from aluclu.alc_r0.reserved_owned_process import ReservedOwnedLease
    bounds = bounds or dict(entry_count=100, path_bytes=4096,
                            file_bytes=100000, total_file_bytes=200000)
    arguments, store, reserved, _ = fixture(tmp_path, stdout_cap=2048, stderr_cap=4096)
    source = (
        'import sys,json,importlib.abc\nfrom pathlib import Path\nfrom dataclasses import asdict\n'
        'class DenyHeavy(importlib.abc.MetaPathFinder):\n'
        ' def find_spec(self,fullname,path=None,target=None):\n'
        '  if fullname.split(".")[0] in ("torch","transformers"):raise ImportError("heavy import denied")\n'
        'sys.meta_path.insert(0,DenyHeavy())\n'
        'from aluclu.alc_r0.runtime_tree_inventory import inspect_runtime_tree,RuntimeTreeBounds\n'
        'try:\n'
        f' r=inspect_runtime_tree(Path({str(tree)!r}), component={component!r},'
        f'deadline_ns={1 if expired else arguments["deadline_ns"]},bounds=RuntimeTreeBounds(**{bounds!r}))\n'
        ' print(json.dumps(dict(ok=True,evidence=asdict(r))))\n'
        'except ValueError as e:\n print(json.dumps(dict(ok=False,error=str(e))))\n'
    )
    environment = dict(os.environ, PYTHONPATH=str(Path(__file__).resolve().parents[1] / 'src'),
        PYTHONNOUSERSITE='1', PYTHONDONTWRITEBYTECODE='1', CUDA_VISIBLE_DEVICES='-1')
    arguments.update(command=(sys.executable, '-c', source), environment=environment)
    with ReservedOwnedLease(**arguments) as lease:
        handles = RetainedHandles(lease)
        try:
            ready = lease.publish_identity(ROOT, ROOT)
            running = lease.resume_verified(ready.sha256)
            terminal = lease.wait_terminal()
            handles.drained(exit_code=0)
        finally:
            handles.close()
    assert terminal.process.exit_code == 0 and not terminal.process.timed_out
    assert terminal.process.active_processes == 0 and terminal.output.valid
    assert arguments['stderr_path'].read_bytes() == b''
    assert store.read(running.sha256).snapshot.reservations[0].state == 'RUNNING'
    return json.loads(arguments['stdout_path'].read_bytes())


def test_exact_canonical_runtime_inventory(tmp_path, tree):
    result = inspect_owned(tmp_path, tree)
    rows = [dict(path='python.dll',kind='file',byte_length=7,
                 sha256=hashlib.sha256(b'runtime').hexdigest())]
    assert result == dict(ok=True, evidence=dict(component='python-venv',
        absolute_root=tree.as_posix(), inventory_sha256=hashlib.sha256(canonical_json_bytes(rows)).hexdigest(),
        entry_count=2, file_count=1, logical_file_bytes=7))


def test_enumerated_identity_matches_path_and_open_file(tree):
    module = api()
    bounds = module.RuntimeTreeBounds(entry_count=2,path_bytes=10,file_bytes=7,total_file_bytes=7)
    nodes, files, total = module._walk(tree,bounds,time.monotonic_ns()+1_000_000_000)
    retained = nodes['python.dll'][1]
    assert files == 1 and total == 7
    assert retained == module._fingerprint((tree/'python.dll').lstat())
    with (tree/'python.dll').open('rb') as stream:
        opened = module._fingerprint(os.fstat(stream.fileno()))
        assert module._same_open_identity(retained,opened)
        assert opened == module._fingerprint(os.fstat(stream.fileno()))
    assert retained == module._fingerprint((tree/'python.dll').lstat())


@pytest.mark.parametrize('position,field', list(enumerate(
    ('mode','device','inode','size','mtime_ns','ctime_ns','nlink','attributes'))))
def test_change_diagnostic_identifies_exact_field(position,field):
    fp=(0o100666,17,23,7,101,103,1,32)
    changed=list(fp); changed[position]+=1
    before={'python.dll':('file',fp)}
    after={'python.dll':('file',tuple(changed))}
    message=api()._tree_change_message('python-base',before,after,time.monotonic_ns()+10**9)
    assert message.startswith('runtime tree changed during inspection: ')
    detail=json.loads(message.split(': ',1)[1])
    assert detail==dict(component='python-base',path_prefix='python.dll',
        path_sha256=hashlib.sha256(b'python.dll').hexdigest(),path_utf8_bytes=10,
        path_truncated=False,before_kind='file',after_kind='file',
        differing_fields=[field],before=list(fp),after=changed)


@pytest.mark.parametrize('case', ['added','removed','kind'])
def test_change_diagnostic_membership_and_kind(case):
    fp=(0o100666,17,23,7,101,103,1,32)
    before={'':('directory',fp),'z':('file',fp)}
    after=dict(before)
    if case=='added': after['a']=('file',fp)
    elif case=='removed': del after['z']
    else: after['z']=('directory',fp)
    detail=json.loads(api()._tree_change_message('python-venv',before,after,
        time.monotonic_ns()+10**9).split(': ',1)[1])
    assert detail['component']=='python-venv'
    assert detail['path_prefix']==('a' if case=='added' else 'z')
    assert detail['differing_fields']==(['kind'] if case=='kind' else ['membership'])
    assert detail['before_kind']==(None if case=='added' else 'file')
    assert detail['after_kind']==(None if case=='removed' else 'directory' if case=='kind' else 'file')


def test_change_diagnostic_bounded_path_and_deterministic_first():
    fp=(0o100666,17,23,7,101,103,1,32)
    changed=fp[:3]+(8,)+fp[4:]
    path='a'+chr(0x1f600)*300
    before={'z':('file',fp),path:('file',fp)}
    after={path:('file',changed),'z':('file',changed)}
    message=api()._tree_change_message('python-base',before,after,time.monotonic_ns()+10**9)
    detail=json.loads(message.split(': ',1)[1])
    assert detail['path_prefix']==path[:128] and detail['path_truncated'] is True
    assert detail['path_utf8_bytes']==len(path.encode())
    assert detail['path_sha256']==hashlib.sha256(path.encode()).hexdigest()
    assert len(message.encode())<2048


def test_change_diagnostic_original_deadline():
    with pytest.raises(ValueError,match='original runtime inventory deadline expired'):
        api()._tree_change_message('python-base',{}, {'a':('file',(1,)*8)},1)


def test_native_directory_walk_root_and_nested(tree):
    from aluclu.alc_r0.windows_directory_metadata import DirectoryObservation,observe_directory
    (tree/'empty').mkdir()
    deadline=time.monotonic_ns()+10**9
    nodes,files,total=api()._walk(tree,api().RuntimeTreeBounds(
        entry_count=3,path_bytes=15,file_bytes=7,total_file_bytes=7),deadline)
    assert type(nodes[''][1]) is DirectoryObservation
    assert type(nodes['empty'][1]) is DirectoryObservation
    assert nodes[''][1]==observe_directory(tree,deadline_ns=deadline)
    assert nodes['empty'][1]==observe_directory(tree/'empty',deadline_ns=deadline)
    assert type(nodes['python.dll'][1]) is tuple and len(nodes['python.dll'][1])==8
    assert (files,total)==(1,7)


def test_native_directory_diagnostic_schema_change():
    from aluclu.alc_r0.windows_directory_metadata import DirectoryObservation
    native=DirectoryObservation(0o40777,17,'01'*16,4096,101,103,1,16,107,4096,23,7,32,0)
    detail=json.loads(api()._tree_change_message('python-base',
        {'':('directory',(0o40777,17,23,4096,101,103,1,16))},
        {'':('directory',native)},time.monotonic_ns()+10**9).split(': ',1)[1])
    assert detail['differing_fields']==['observation_schema']
    assert detail['before_schema']=='python-stat-v1'
    assert detail['after_schema']=='windows-directory-by-name-v1'


@pytest.mark.parametrize('field', (
    'mode','volume_serial','file_id128','size','write_ticks','creation_ticks',
    'link_count','attributes','change_ticks','allocation_size','legacy_file_id',
    'device_type','device_characteristics','reparse_tag'))
def test_native_directory_diagnostic_each_field(field):
    from dataclasses import replace
    from aluclu.alc_r0.windows_directory_metadata import DirectoryObservation
    old=DirectoryObservation(0o40777,17,'01'*16,4096,101,103,1,16,107,4096,23,7,32,0)
    new=replace(old,**{field:'02'*16 if field=='file_id128' else getattr(old,field)+1})
    detail=json.loads(api()._tree_change_message('python-venv',
        {'folder':('directory',old)},{'folder':('directory',new)},
        time.monotonic_ns()+10**9).split(': ',1)[1])
    assert detail['differing_fields']==[field]
    assert detail['before']==asdict(old) and detail['after']==asdict(new)
    assert detail['before_kind']==detail['after_kind']=='directory'


@pytest.mark.parametrize('field,value', [
    ('entry_count', 0), ('entry_count', True), ('entry_count', 65537),
    ('path_bytes', 0), ('path_bytes', 4*1024**2+1),
    ('file_bytes', -1), ('file_bytes', 4*1024**3+1),
    ('total_file_bytes', 16*1024**3+1), ('total_file_bytes', 1.0),
])
def test_exact_finite_bounds(field, value):
    values = dict(entry_count=10,path_bytes=100,file_bytes=100,total_file_bytes=100)
    values[field] = value
    with pytest.raises(ValueError, match='bound'):
        api().RuntimeTreeBounds(**values)


def test_exact_all_bounds(tmp_path, tree):
    result = inspect_owned(tmp_path, tree, bounds=dict(entry_count=2,path_bytes=10,
                                                     file_bytes=7,total_file_bytes=7))
    assert result['ok'] and result['evidence']['logical_file_bytes'] == 7


@pytest.mark.parametrize('field,value', [('entry_count',1),('path_bytes',9),
                                       ('file_bytes',6),('total_file_bytes',6)])
def test_one_byte_or_node_over_bound_denies(tmp_path, tree, field, value):
    bounds = dict(entry_count=2,path_bytes=10,file_bytes=7,total_file_bytes=7)
    bounds[field] = value
    result = inspect_owned(tmp_path, tree, bounds=bounds)
    assert not result['ok'] and 'bound' in result['error']


def test_empty_directories_are_counted_and_hashed(tmp_path, tree):
    (tree / 'empty').mkdir()
    result = inspect_owned(tmp_path, tree, bounds=dict(entry_count=3,path_bytes=15,
                                                     file_bytes=7,total_file_bytes=7))
    rows = [dict(path='empty',kind='directory',byte_length=0,sha256=None),
            dict(path='python.dll',kind='file',byte_length=7,
                 sha256=hashlib.sha256(b'runtime').hexdigest())]
    assert result['evidence']['entry_count'] == 3
    assert result['evidence']['inventory_sha256'] == hashlib.sha256(canonical_json_bytes(rows)).hexdigest()


def test_empty_directory_cannot_bypass_node_bound(tmp_path, tree):
    (tree / 'empty').mkdir()
    result = inspect_owned(tmp_path, tree, bounds=dict(entry_count=2,path_bytes=100,
                                                     file_bytes=7,total_file_bytes=7))
    assert not result['ok'] and 'bound' in result['error']


def test_zero_length_file_and_zero_byte_allowances(tmp_path, tree):
    (tree / 'python.dll').write_bytes(b'')
    result = inspect_owned(tmp_path, tree, bounds=dict(entry_count=2,path_bytes=10,
                                                     file_bytes=0,total_file_bytes=0))
    assert result['ok'] and result['evidence']['logical_file_bytes'] == 0


def test_multiple_chunks_and_binary_unicode_path(tmp_path, tree):
    data = b'\0\xff' * 65537
    (tree / 'python.dll').unlink()
    (tree / 'çalışma.pyd').write_bytes(data)
    result = inspect_owned(tmp_path, tree, bounds=dict(entry_count=2,path_bytes=100,
        file_bytes=len(data),total_file_bytes=len(data)))
    rows = [dict(path='çalışma.pyd',kind='file',byte_length=len(data),
                 sha256=hashlib.sha256(data).hexdigest())]
    assert result['ok'] and result['evidence']['inventory_sha256'] == hashlib.sha256(canonical_json_bytes(rows)).hexdigest()


def test_hardlinks_charge_each_logical_path(tmp_path, tree):
    os.link(tree / 'python.dll', tree / 'alias.dll')
    result = inspect_owned(tmp_path, tree, bounds=dict(entry_count=3,path_bytes=100,
                                                     file_bytes=7,total_file_bytes=14))
    assert result['ok'] and result['evidence']['file_count'] == 2
    assert result['evidence']['logical_file_bytes'] == 14


def test_junction_denies_without_following_target(tmp_path, tree):
    target = tmp_path / 'outside'
    target.mkdir()
    (target / 'not-runtime').write_bytes(b'not part of inventory')
    cmd = Path(os.environ['SystemRoot']) / 'System32' / 'cmd.exe'
    subprocess.run((str(cmd), '/c', 'mklink', '/J', str(tree / 'link'), str(target)),
                   capture_output=True, check=True, timeout=3)
    result = inspect_owned(tmp_path, tree)
    assert not result['ok'] and 'reparse' in result['error']


@pytest.mark.parametrize('kind', ['expired','component','relative','missing','file','empty'])
def test_invalid_inputs_deny(tmp_path, tree, kind):
    root = tree
    if kind == 'relative': root = Path('relative')
    elif kind == 'missing': root = tree / 'missing'
    elif kind == 'file': root = tree / 'python.dll'
    elif kind == 'empty': (tree / 'python.dll').unlink()
    result = inspect_owned(tmp_path, root, component='not-runtime' if kind == 'component' else 'python-base',
                           expired=kind == 'expired')
    assert not result['ok']


@pytest.mark.parametrize('position', range(8))
def test_cross_source_identity_exception_is_only_windows_ctime(position):
    fingerprint = (33206,17,23,7,101,103,1,32)
    changed = list(fingerprint)
    changed[position] += 1
    assert api()._same_open_identity(fingerprint,tuple(changed)) is (position == 5)


def test_non_windows_requires_full_timestamp_identity(monkeypatch):
    from types import SimpleNamespace
    module = api()
    monkeypatch.setattr(module,'os',SimpleNamespace(name='posix'))
    fingerprint = (33206,17,23,7,101,103,1,32)
    changed = fingerprint[:5] + (104,) + fingerprint[6:]
    assert module._same_open_identity(fingerprint,fingerprint)
    assert not module._same_open_identity(fingerprint,changed)


@pytest.mark.parametrize('path_mode,opened_mode,allowed',[
    (0o100777,0o100666,True), (0o100766,0o100666,False),
    (0o100777,0o100667,False), (0o100777,0o100444,False),
    (0o100666,0o100777,False), (0o040777,0o100666,False),
])
def test_windows_executable_mode_exception_is_directed(path_mode,opened_mode,allowed):
    rest=(17,23,7,101,103,1,32)
    assert api()._same_open_identity((path_mode,*rest),(opened_mode,*rest)) is allowed


def test_changed_path_and_bytes_change_inventory(tmp_path, tree):
    first = tmp_path / 'first'
    first.mkdir()
    before = inspect_owned(first, tree)['evidence']['inventory_sha256']
    (tree / 'python.dll').rename(tree / 'renamed.dll')
    second = tmp_path / 'second'
    second.mkdir()
    renamed = inspect_owned(second, tree)['evidence']['inventory_sha256']
    (tree / 'renamed.dll').write_bytes(b'changed')
    third = tmp_path / 'third'
    third.mkdir()
    changed = inspect_owned(third, tree)['evidence']['inventory_sha256']
    assert len({before,renamed,changed}) == 3
