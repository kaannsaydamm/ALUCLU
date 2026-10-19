"""Single-route native candidate tests; no runtime inventory integration."""
import importlib
import os
import subprocess
import time
from dataclasses import fields, replace
from pathlib import Path

import pytest

pytestmark = pytest.mark.skipif(os.name != 'nt', reason='Windows native metadata')


def api():
    return importlib.import_module('aluclu.alc_r0.windows_directory_metadata')


def record():
    value = api()._NativeBasic()
    value.FileId = -3
    value.CreationTime = 101
    value.LastAccessTime = 103
    value.LastWriteTime = 107
    value.ChangeTime = 109
    value.AllocationSize = 4096
    value.EndOfFile = 4096
    value.FileAttributes = 16
    value.NumberOfLinks = 1
    value.DeviceType = 7
    value.DeviceCharacteristics = 32
    value.VolumeSerialNumber = -2
    value.FileId128[:] = bytes(range(1,17))
    return value


def test_native_decoder_exact_and_full_identity():
    value = api()._decode(bytes(record()))
    assert value.mode == 0o40777
    assert value.volume_serial == 2**64-2 and value.legacy_file_id == 2**64-3
    assert value.file_id128 == bytes(range(1,17)).hex()
    assert (value.size,value.allocation_size,value.write_ticks,value.creation_ticks,
            value.change_ticks,value.link_count,value.attributes,value.device_type,
            value.device_characteristics,value.reparse_tag) == (4096,4096,107,101,109,1,16,7,32,0)
    assert tuple(f.name for f in fields(value)) == (
        'mode','volume_serial','file_id128','size','write_ticks','creation_ticks',
        'link_count','attributes','change_ticks','allocation_size','legacy_file_id',
        'device_type','device_characteristics','reparse_tag')


def test_native_readonly_mode_and_access_padding_exclusion():
    raw=record(); raw.FileAttributes |= 1
    value=api()._decode(bytes(raw))
    assert value.mode == 0o40555
    raw.LastAccessTime=999; raw.Reserved=123
    assert value == api()._decode(bytes(raw))


@pytest.mark.parametrize('field', (
    'mode','volume_serial','file_id128','size','write_ticks','creation_ticks',
    'link_count','attributes','change_ticks','allocation_size','legacy_file_id',
    'device_type','device_characteristics','reparse_tag'))
def test_native_all_retained_fields_exact_equality(field):
    value=api()._decode(bytes(record()))
    current=getattr(value,field)
    assert value != replace(value,**{field: '00'*16 if field=='file_id128' else current+1})


@pytest.mark.parametrize('field,value', (
    ('EndOfFile',-1),('AllocationSize',-1),('CreationTime',-1),
    ('LastWriteTime',-1),('ChangeTime',-1),('NumberOfLinks',0),
    ('FileAttributes',0),('FileAttributes',16|0x400),('ReparseTag',1)))
def test_native_decoder_invalid_metadata(field,value):
    raw=record(); setattr(raw,field,value)
    with pytest.raises(ValueError,match='native directory'):
        api()._decode(bytes(raw))


def test_native_decoder_zero_complete_identity():
    raw=record(); raw.FileId128[:]=bytes(16)
    with pytest.raises(ValueError,match='native directory'):
        api()._decode(bytes(raw))


@pytest.mark.parametrize('raw', (b'',bytes(103),bytes(105),bytearray(104),None))
def test_native_decoder_exact_fixed_bytes(raw):
    with pytest.raises(ValueError,match='native directory'):
        api()._decode(raw)


@pytest.mark.parametrize('path', (
    Path('relative'),Path(r'\\server\share\directory'),Path(r'\\?\C:\directory'),
    Path(r'\\.\C:\directory'),Path('C:/bad\0name'),Path('C:/'+('x'*32768)), 'C:/'))
def test_native_path_labels_deny_before_os(path):
    with pytest.raises(ValueError,match='directory path'):
        api().observe_directory(path,deadline_ns=time.monotonic_ns()+10**9)


def test_native_original_expired_deadline(tmp_path):
    with pytest.raises(ValueError,match='original runtime inventory deadline expired'):
        api().observe_directory(tmp_path,deadline_ns=1)


def test_native_exact_repeated_owned_directory(tmp_path):
    # Same native operation twice; no path-stat/native fingerprint equivalence claim.
    from aluclu.alc_r0.reserved_owned_process import ReservedOwnedLease
    from test_alc_r0_reserved_owned_process import fixture, ROOT
    from test_alc_r0_owned_stop import RetainedHandles
    import json
    import sys
    directory=tmp_path/'plain.exe'; directory.mkdir()
    arguments,store,_,_=fixture(tmp_path,seconds=15,stdout_cap=2048,stderr_cap=4096)
    command=(sys.executable,'-c',
        'import json,time\nfrom dataclasses import asdict\nfrom pathlib import Path\n'
        'from aluclu.alc_r0.windows_directory_metadata import observe_directory\n'
        f'p=Path({str(directory)!r}); d={arguments["deadline_ns"]}\n'
        'a=observe_directory(p,deadline_ns=d); b=observe_directory(p,deadline_ns=d)\n'
        'print(json.dumps(dict(equal=a==b,value=asdict(a))))')
    arguments.update(command=command,cwd=Path(__file__).resolve().parents[1],
        environment=dict(os.environ,PYTHONPATH=str(Path(__file__).resolve().parents[1]/'src'),
            PYTHONDONTWRITEBYTECODE='1',PYTHONNOUSERSITE='1',CUDA_VISIBLE_DEVICES='-1'),
        stdout_path=tmp_path/'native.stdout',stderr_path=tmp_path/'native.stderr')
    with ReservedOwnedLease(**arguments) as lease:
        handles=RetainedHandles(lease)
        try:
            ready=lease.publish_identity(ROOT,ROOT)
            running=lease.resume_verified(ready.sha256)
            terminal=lease.wait_terminal()
            handles.drained(exit_code=0)
        finally:
            handles.close()
    assert terminal.output.valid and terminal.process.active_processes==0
    assert not terminal.process.timed_out and terminal.process.exit_code==0
    assert store.read(running.sha256).snapshot.reservations[0].state=='RUNNING'
    assert (tmp_path/'native.stderr').read_bytes()==b''
    data=json.loads((tmp_path/'native.stdout').read_bytes())
    assert data['equal'] and data['value']['mode']==0o40777
    assert len(data['value']['file_id128'])==32


def test_native_regular_file_denied(tmp_path):
    path=tmp_path/'file'; path.write_bytes(b'x')
    with pytest.raises(ValueError,match='directory path'):
        api().observe_directory(path,deadline_ns=time.monotonic_ns()+10**9)


def test_native_junction_and_intermediate_alias_denied(tmp_path):
    target=tmp_path/'target'; target.mkdir(); (target/'sub').mkdir()
    alias=tmp_path/'alias'
    result=subprocess.run(('cmd','/c','mklink','/J',str(alias),str(target)),
                          capture_output=True,timeout=10)
    assert result.returncode==0
    for path in (alias,alias/'sub'):
        with pytest.raises(ValueError,match='directory path'):
            api().observe_directory(path,deadline_ns=time.monotonic_ns()+10**9)
