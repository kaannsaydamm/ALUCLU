"""Owned factual layout fixtures and separately selected real read-only scan."""
import hashlib
import importlib
import json
import os
import subprocess
import sys
from dataclasses import asdict
from pathlib import Path

import pytest

from aluclu.alc_r0.canonical import canonical_json_bytes
from test_alc_r0_reserved_owned_process import ROOT, fixture
from test_alc_r0_owned_stop import RetainedHandles

pytestmark = pytest.mark.skipif(os.name != 'nt', reason='Windows CPython binding')
ENV_KEYS = ('PYTHONPATH','PYTHONHOME','PYTHONNOUSERSITE','PYTHONDONTWRITEBYTECODE',
    'HF_HUB_OFFLINE','TRANSFORMERS_OFFLINE','HF_DATASETS_OFFLINE',
    'CUDA_VISIBLE_DEVICES','CUBLAS_WORKSPACE_CONFIG')
FLAGS = dict(isolated=0,ignore_environment=0,no_user_site=1,safe_path=False,
             dont_write_bytecode=1,optimize=0)


def api():
    return importlib.import_module('aluclu.alc_r0.python_runtime_binding')


@pytest.fixture
def layout(tmp_path):
    base, venv = tmp_path/'base', tmp_path/'venv'
    base.mkdir(); venv.mkdir(); (venv/'Scripts').mkdir()
    (base/'python.exe').write_bytes(b'base')
    (venv/'Scripts'/'python.exe').write_bytes(b'venv')
    (venv/'pyvenv.cfg').write_bytes(b'home=fixture')
    return base, venv


def inspect_owned(tmp_path, layout=None, *, alter='', bounds=None, actual=False, expired=False):
    api()
    from aluclu.alc_r0.reserved_owned_process import ReservedOwnedLease
    actual_seconds = 900 if os.environ.get('ALUCLU_TEST_ONLY_RUNTIME_SCAN_MODE') in ('actual_v4','actual_v5') else 240
    arguments, store, _, _ = fixture(tmp_path, seconds=actual_seconds if actual else 15,
                                    stdout_cap=8*1024**2, stderr_cap=4096)
    bounds = bounds or dict(entry_count=65536 if actual else 64,path_bytes=4*1024**2,
        file_bytes=4*1024**3 if actual else 1024**2,
        total_file_bytes=16*1024**3 if actual else 4*1024**2)
    source = (
        'import sys,json,os,importlib.abc\nfrom pathlib import Path\nfrom types import SimpleNamespace\n'
        'class DenyHeavy(importlib.abc.MetaPathFinder):\n'
        ' def find_spec(self,fullname,path=None,target=None):\n'
        '  if fullname.split(".")[0] in ("torch","transformers"):raise ImportError("heavy import denied")\n'
        'sys.meta_path.insert(0,DenyHeavy())\n'
        'from aluclu.alc_r0.python_runtime_binding import inspect_current_python_runtime\n'
        'from aluclu.alc_r0.runtime_tree_inventory import RuntimeTreeBounds\n'
        # Load the canonical key-order codec before test-only sys.path replacement.
        'from aluclu.alc_r0.canonical import canonical_json_bytes\n'
        'canonical_json_bytes(dict(fixture_codec_warmup=True))\n'
    )
    if not actual:
        base, venv = layout
        source += (
            # Load native observer dependencies before test-only sys mutation.
            'from aluclu.alc_r0.windows_directory_metadata import observe_directory\n'
            f'sys.prefix=sys.exec_prefix={str(venv)!r}\n'
            f'sys.base_prefix=sys.base_exec_prefix={str(base)!r}\n'
            f'sys.executable={str(venv/"Scripts"/"python.exe")!r}\n'
            f'sys._base_executable={str(base/"python.exe")!r}\n'
            'sys.version="3.12.12 fixture"\n'
            'sys.implementation=SimpleNamespace(name="cpython",cache_tag="cpython-312")\n'
            f'sys.flags=SimpleNamespace(**{FLAGS!r})\n'
            f'sys.path={[str(base/"Lib"),str(base/"missing.zip")]!r}\n'
            f'for key in {ENV_KEYS!r}:os.environ.pop(key,None)\n'
            'os.environ["PYTHONDONTWRITEBYTECODE"]="1"\n'
        )
    source += alter + '\ntry:\n'
    cause_probe = os.environ.get('ALUCLU_TEST_ONLY_RUNTIME_CAUSE')=='1' and not actual
    failure_source = ('except ValueError as e:\n print(json.dumps(dict(ok=False,error=str(e),'
        'cause_type=type(e.__cause__).__name__,cause_message=str(e.__cause__)[:512])))\n'
        if cause_probe else 'except ValueError as e:\n print(json.dumps(dict(ok=False,error=str(e))))\n')
    source += (f' r=inspect_current_python_runtime(deadline_ns={1 if expired else arguments["deadline_ns"]},'
               f'bounds=RuntimeTreeBounds(**{bounds!r}))\n'
               ' print(json.dumps(dict(ok=True,payload=json.loads(r.data),sha256=r.sha256)))\n'
               + failure_source)
    environment = dict(os.environ,PYTHONPATH=str(Path(__file__).resolve().parents[1]/'src'),
        PYTHONNOUSERSITE='1',PYTHONDONTWRITEBYTECODE='1',CUDA_VISIBLE_DEVICES='-1')
    arguments.update(command=(sys.executable,'-c',source),environment=environment)
    with ReservedOwnedLease(**arguments) as lease:
        handles = RetainedHandles(lease)
        try:
            ready=lease.publish_identity(ROOT,ROOT)
            running=lease.resume_verified(ready.sha256)
            terminal=lease.wait_terminal()
            handles.drained(exit_code=terminal.process.exit_code if actual else 0)
        finally:
            handles.close()
    assert terminal.output.valid and terminal.process.active_processes==0
    assert arguments['stderr_path'].read_bytes()==b''
    assert store.read(running.sha256).snapshot.reservations[0].state=='RUNNING'
    if actual:
        if terminal.process.timed_out or terminal.process.exit_code!=0:
            return dict(ok=False,error='owned runtime diagnostic did not complete',
                        process=asdict(terminal.process))
        result=json.loads(arguments['stdout_path'].read_bytes())
        result['process']=asdict(terminal.process)
        return result
    assert terminal.process.exit_code==0 and not terminal.process.timed_out
    return json.loads(arguments['stdout_path'].read_bytes())


def tree_row(root, component):
    rows=[]
    for path in sorted(root.rglob('*'),key=lambda p:p.relative_to(root).as_posix().encode()):
        data=path.read_bytes() if path.is_file() else None
        rows.append(dict(path=path.relative_to(root).as_posix(),kind='file' if data is not None else 'directory',
            byte_length=len(data) if data is not None else 0,
            sha256=hashlib.sha256(data).hexdigest() if data is not None else None))
    return dict(component=component,absolute_root=root.as_posix(),
        inventory_sha256=hashlib.sha256(canonical_json_bytes(rows)).hexdigest(),
        entry_count=str(len(rows)+1),file_count=str(sum(r['kind']=='file' for r in rows)),
        logical_file_bytes=str(sum(r['byte_length'] for r in rows)))


def test_exact_current_runtime_binding(tmp_path,layout):
    base,venv=layout
    result=inspect_owned(tmp_path,layout)
    observed=dict(executable=str(venv/'Scripts'/'python.exe'),base_executable=str(base/'python.exe'),
        prefix=str(venv),exec_prefix=str(venv),base_prefix=str(base),base_exec_prefix=str(base),
        version='3.12.12 fixture',implementation='cpython',cache_tag='cpython-312',
        platform='win32',pointer_bits='64',byteorder=sys.byteorder,flags=FLAGS,
        path=[str(base/'Lib'),str(base/'missing.zip')],
        environment={key:'1' if key=='PYTHONDONTWRITEBYTECODE' else None for key in ENV_KEYS})
    special=[]
    for role,path in [('venv-executable',venv/'Scripts'/'python.exe'),
                      ('base-executable',base/'python.exe'),('venv-config',venv/'pyvenv.cfg')]:
        data=path.read_bytes()
        special.append(dict(role=role,absolute_path=path.as_posix(),byte_length=str(len(data)),
                            sha256=hashlib.sha256(data).hexdigest()))
    payload=dict(schema='alc-r0-current-python-runtime-v1',observed=observed,base_prefix_alias=None,
        components=[tree_row(base,'python-base'),tree_row(venv,'python-venv')],special_files=special)
    assert result==dict(ok=True,payload=payload,sha256=hashlib.sha256(canonical_json_bytes(payload)).hexdigest())


@pytest.mark.parametrize('alter',[
    'sys.prefix="relative"', 'sys.exec_prefix=sys.base_prefix',
    'sys.base_prefix=sys.base_exec_prefix=sys.prefix', 'sys.executable=sys._base_executable',
    'sys.path=[None]', 'sys.path=["x"]*257', 'sys.path=["x"*32769]',
    'sys.flags.safe_path=0', 'sys.flags.optimize=True', 'sys.implementation.name="pypy"',
    'sys.version="x"*32769', 'os.environ["PYTHONHOME"]="é"*20000',
    'sys.path=["x"*32768]*128',
    'Path(sys.prefix,"pyvenv.cfg").write_bytes(b"x"*65537)',
    'Path(sys.prefix,"pyvenv.cfg").unlink()',
    'Path(sys.executable).unlink()',
])
def test_invalid_current_observation_denied(tmp_path,layout,alter):
    assert not inspect_owned(tmp_path,layout,alter=alter)['ok']


@pytest.mark.parametrize('alter',[
    'Path(sys.prefix,"pyvenv.cfg").write_bytes(b"changed")',
    'Path(sys.executable).write_bytes(b"changed")',
    'sys.path.append("literal-import-label")', 'os.environ["PYTHONHOME"]=""',
])
def test_layout_and_bytes_participate_in_binding(tmp_path,layout,alter):
    first=tmp_path/'first'; first.mkdir()
    second=tmp_path/'second'; second.mkdir()
    before=inspect_owned(first,layout)
    after=inspect_owned(second,layout,alter=alter)
    assert before['ok'] and after['ok'] and before['sha256']!=after['sha256']


def test_component_bounds_remain_enforced(tmp_path,layout):
    assert not inspect_owned(tmp_path,layout,bounds=dict(entry_count=1,path_bytes=1,
        file_bytes=0,total_file_bytes=0))['ok']


def test_original_deadline_expiry_denied(tmp_path,layout):
    assert not inspect_owned(tmp_path,layout,expired=True)['ok']


def test_executable_metadata_sources(layout):
    from aluclu.alc_r0.runtime_tree_inventory import _fingerprint, _same_open_identity
    path=layout[0]/'python.exe'
    before=_fingerprint(path.lstat())
    with path.open('rb',buffering=0) as stream:
        opened=_fingerprint(os.fstat(stream.fileno()))
    assert _same_open_identity(before,opened), (before,opened)


def junction(link,target):
    subprocess.run(('cmd.exe','/c','mklink','/J',str(link),str(target)),
                   check=True,capture_output=True,timeout=3)


def test_current_base_single_junction_bound(tmp_path,layout):
    base,venv=layout
    alias=tmp_path/'base-alias'
    junction(alias,base)
    result=inspect_owned(tmp_path,(alias,venv))
    assert result['ok'], result
    assert result['payload']['observed']['base_prefix']==str(alias)
    assert result['payload']['components'][0]==tree_row(base,'python-base')
    assert result['payload']['base_prefix_alias']==dict(absolute_path=alias.as_posix(),
        immediate_target=os.readlink(alias),resolved_root=base.as_posix(),reparse_tag=str(0xA0000003))
    assert result['payload']['special_files'][1]['absolute_path']==(base/'python.exe').as_posix()


def test_current_base_chained_junction_denied(tmp_path,layout):
    base,venv=layout
    inner,outer=tmp_path/'inner',tmp_path/'outer'
    junction(inner,base); junction(outer,inner)
    assert not inspect_owned(tmp_path,(outer,venv))['ok']


def test_alias_target_utf8_bound(layout):
    base,_=layout
    with pytest.raises(ValueError,match='bound'):
        api()._alias_payload((base,(),'é'*20000,base))


def test_alias_text_uses_shared_aggregate_bound():
    observed=dict(path=['x'*32768]*127,environment={})
    alias=dict(absolute_path='a'*100,immediate_target='b'*32700,
               resolved_root='c'*100,reparse_tag='1')
    with pytest.raises(ValueError,match='aggregate bound'):
        api()._retained_text_bound(observed,[],[],alias)


@pytest.mark.skipif(os.environ.get('ALUCLU_TEST_ONLY_RUNTIME_SCAN')!='1',
                    reason='separately selected read-only runtime diagnostic')
def test_actual_current_runtime_read_only(tmp_path):
    result=inspect_owned(tmp_path,actual=True)
    mode=os.environ['ALUCLU_TEST_ONLY_RUNTIME_SCAN_MODE']
    assert mode in ('actual','actual_v2','actual_v3','actual_v4','actual_v5')
    target=Path(__file__).resolve().parents[1]/'results'/f'alc_r0_python_runtime_{mode}_20261011.binding.json'
    with target.open('xb') as out:
        out.write(canonical_json_bytes(result))
    assert result['ok'], result
    assert result['sha256']==hashlib.sha256(canonical_json_bytes(result['payload'])).hexdigest()
