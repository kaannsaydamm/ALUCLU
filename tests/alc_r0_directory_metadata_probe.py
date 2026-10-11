"""Closed read-only Windows directory metadata probe; no runtime acceptance."""
import ctypes
import hashlib
import json
import os
import struct
import sys
import tempfile
from ctypes import wintypes as W
from dataclasses import asdict
from pathlib import Path


def probe(enumerate_directory=False):
    if os.name!='nt' or struct.calcsize('P')!=8: raise ValueError('Windows64 only')
    path=Path(sys.prefix)/'Lib/site-packages/huggingface_hub/inference/_mcp'
    if path.resolve(strict=True)!=path: raise ValueError('resolved directory required')
    class Basic(ctypes.Structure):
        _fields_=[(n,ctypes.c_longlong) for n in ('FileId','CreationTime','LastAccessTime',
            'LastWriteTime','ChangeTime','AllocationSize','EndOfFile')]+[
            (n,W.DWORD) for n in ('FileAttributes','ReparseTag','NumberOfLinks',
            'DeviceType','DeviceCharacteristics','Reserved')]+[
            ('VolumeSerialNumber',ctypes.c_longlong),('FileId128',ctypes.c_ubyte*16)]
    class Legacy(ctypes.Structure):
        _fields_=[('attributes',W.DWORD)]+[(n,W.FILETIME) for n in
            ('creation','access','write')]+[(n,W.DWORD) for n in
            ('volume','size_high','size_low','links','index_high','index_low')]
    assert ctypes.sizeof(Basic)==104 and ctypes.sizeof(Legacy)==52
    byname=ctypes.WinDLL('api-ms-win-core-file-l2-1-4.dll',use_last_error=True).GetFileInformationByName
    byname.argtypes=[W.LPCWSTR,ctypes.c_int,ctypes.c_void_p,W.DWORD]; byname.restype=W.BOOL
    kernel=ctypes.WinDLL('kernel32',use_last_error=True)
    create=kernel.CreateFileW; create.argtypes=[W.LPCWSTR,W.DWORD,W.DWORD,ctypes.c_void_p,W.DWORD,W.DWORD,W.HANDLE]; create.restype=W.HANDLE
    info=kernel.GetFileInformationByHandle; info.argtypes=[W.HANDLE,ctypes.POINTER(Legacy)]; info.restype=W.BOOL
    close=kernel.CloseHandle; close.argtypes=[W.HANDLE]; close.restype=W.BOOL
    def named():
        value=Basic()
        if not byname(str(path),3,ctypes.byref(value),ctypes.sizeof(value)): raise ctypes.WinError(ctypes.get_last_error())
        return dict(size=value.EndOfFile,allocation=value.AllocationSize,
            file_id128=bytes(value.FileId128).hex(),volume=value.VolumeSerialNumber,
            attributes=value.FileAttributes,reparse_tag=value.ReparseTag)
    def fp():
        s=path.lstat()
        if not s.st_mode & 0o040000 or s.st_file_attributes & 0x400: raise ValueError('regular directory required')
        return [s.st_mode,s.st_dev,s.st_ino,s.st_size,s.st_mtime_ns,s.st_ctime_ns,s.st_nlink,s.st_file_attributes]
    rows=[]
    for _ in range(16):
        before=fp(); first=named()
        handle=create(str(path),0x80,7,None,3,0x02200000,None)
        if handle==ctypes.c_void_p(-1).value: raise ctypes.WinError(ctypes.get_last_error())
        try:
            value=Legacy()
            if not info(handle,ctypes.byref(value)): raise ctypes.WinError(ctypes.get_last_error())
            legacy=dict(size=(value.size_high<<32)|value.size_low,
                inode=(value.index_high<<32)|value.index_low,volume32=value.volume,
                attributes=value.attributes,links=value.links)
        finally:
            if not close(handle): raise ctypes.WinError(ctypes.get_last_error())
        enumeration=None
        if enumerate_directory:
            names=[]; length=0
            with os.scandir(path) as entries:
                for entry in entries:
                    if len(names)>=256: raise ValueError('enumeration entry bound')
                    length+=len(entry.name.encode('utf-8'))
                    if length>32768: raise ValueError('enumeration name byte bound')
                    names.append(entry.name)
            encoded=json.dumps(sorted(names),ensure_ascii=True,separators=(',',':')).encode()
            enumeration=dict(count=len(names),names_sha256=hashlib.sha256(encoded).hexdigest())
        rows.append(dict(before=before,by_name_before=first,by_handle=legacy,
                         enumeration=enumeration,by_name_after=named(),after=fp()))
    print(json.dumps(dict(schema='alc-r0-directory-metadata-probe-v1',
        python=sys.version,absolute_path=str(path),rounds=rows),sort_keys=True,separators=(',',':')))


def main():
    if sys.argv[1:]==['--owned-probe']: return probe()
    if sys.argv[1:]==['--owned-probe-enumerate']: return probe(True)
    if sys.argv[1:] not in ([],['--enumerate']): raise ValueError('closed probe mode required')
    enumerate_directory=sys.argv[1:]==['--enumerate']
    from aluclu.alc_r0.reserved_owned_process import ReservedOwnedLease
    from test_alc_r0_reserved_owned_process import fixture,ROOT
    from test_alc_r0_owned_stop import RetainedHandles
    cwd=Path(__file__).resolve().parents[1]
    stem=cwd/('results/alc_r0_directory_metadata_probe_v2_20261011' if enumerate_directory
              else 'results/alc_r0_directory_metadata_probe_20261011')
    paths={s:Path(str(stem)+s) for s in ('.stdout.log','.stderr.log','.exit.json')}
    if any(p.exists() for p in paths.values()): raise FileExistsError('retained evidence exists')
    environment=dict(os.environ,PYTHONDONTWRITEBYTECODE='1',PYTHONNOUSERSITE='1',CUDA_VISIBLE_DEVICES='-1')
    temporary=Path(tempfile.mkdtemp(prefix='alc-r0-directory-probe-'))
    arguments,store,_,_=fixture(temporary,seconds=60,stdout_cap=65536,stderr_cap=4096)
    internal='--owned-probe-enumerate' if enumerate_directory else '--owned-probe'
    arguments.update(command=(sys.executable,'-I','-B',str(Path(__file__).resolve()),internal),
        cwd=cwd,environment=environment,stdout_path=paths['.stdout.log'],stderr_path=paths['.stderr.log'])
    with ReservedOwnedLease(**arguments) as lease:
        handles=RetainedHandles(lease)
        try:
            ready=lease.publish_identity(ROOT,ROOT)
            running=lease.resume_verified(ready.sha256)
            terminal=lease.wait_terminal()
            handles.drained(exit_code=terminal.process.exit_code)
        finally:
            handles.close()
    data=json.dumps(dict(process=asdict(terminal.process),output=asdict(terminal.output),
        synthetic_reservation_state=store.read(running.sha256).snapshot.reservations[0].state,
        scope='readonly-directory-metadata-diagnostic'),sort_keys=True,separators=(',',':')).encode()
    with paths['.exit.json'].open('xb') as out: out.write(data)
    print(data.decode())


if __name__=='__main__': main()
