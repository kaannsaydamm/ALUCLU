"""Exclusion diagnostics only; no installed operator or scientific permit."""
import importlib
import os
from pathlib import Path
import subprocess
import sys
import threading
import time

import pytest
from aluclu.cognition.persistence import exclusive_file_lock


def api():
    module = importlib.import_module('aluclu.alc_r0.deadline_file_lock')
    return module.deadline_file_lock, module.DeadlineLockError


def end(seconds=2): return time.monotonic_ns()+int(seconds*10**9)


def test_normal_nested_and_legacy_inner(tmp_path):
    lock, _ = api()
    path = tmp_path/'operator.lock'
    with lock(path,end()):
        with lock(path,end()):
            with exclusive_file_lock(path): pass
    assert path.read_bytes() == b'\0'
    with exclusive_file_lock(path): pass
    with lock(path,end()): pass


@pytest.mark.parametrize('value',[True,0,-1,2**63,1.0,None])
def test_bad_original_deadline_no_file(value,tmp_path):
    lock, _ = api()
    path = tmp_path/'operator.lock'
    with pytest.raises(ValueError):
        with lock(path,value): pytest.fail('body entered')
    assert not path.exists()


def test_expired_original_deadline_no_body(tmp_path):
    lock, _ = api()
    path = tmp_path/'operator.lock'
    with pytest.raises(TimeoutError):
        with lock(path,time.monotonic_ns()-1): pytest.fail('body entered')
    assert not path.exists()


@pytest.mark.parametrize('data',[b'\0',b'x',b'bad'])
def test_legacy_only_outer_does_not_supply_validated_handle(tmp_path,data):
    lock, Error = api()
    path = tmp_path/'operator.lock'; path.write_bytes(data)
    with exclusive_file_lock(path):
        with pytest.raises(Error):
            with lock(path,end()): pytest.fail('inherited unknown bytes accepted')
        with exclusive_file_lock(path): pass
    assert path.read_bytes() == data


@pytest.mark.parametrize('exception',[ValueError,KeyboardInterrupt])
def test_body_failure_releases_but_keeps_lockfile(tmp_path,exception):
    lock, _ = api()
    path = tmp_path/'operator.lock'
    with pytest.raises(exception):
        with lock(path,end()): raise exception()
    assert path.read_bytes() == b'\0'
    with lock(path,end()): pass
    with exclusive_file_lock(path): pass


@pytest.mark.parametrize('kind',['non-nul','oversize','directory','hardlink','missing-parent','relative'])
def test_unsafe_namespace_never_enters(tmp_path,kind):
    lock, _ = api()
    path = tmp_path/'operator.lock'
    if kind=='non-nul': path.write_bytes(b'x')
    elif kind=='oversize': path.write_bytes(b'xx')
    elif kind=='directory': path.mkdir()
    elif kind=='hardlink':
        path.write_bytes(b'\0'); os.link(path,tmp_path/'alias.lock')
    elif kind=='missing-parent': path=tmp_path/'missing'/'operator.lock'
    else: path=Path('relative-operator.lock')
    with pytest.raises((ValueError,OSError)):
        with lock(path,end()): pytest.fail('unsafe lock admitted')
    if kind=='missing-parent': assert not path.parent.exists()


@pytest.mark.parametrize('holder',['legacy','bounded','registry'])
def test_thread_contention_expires_without_body(tmp_path,holder):
    import aluclu.cognition.persistence as persistence
    lock, _ = api()
    path=tmp_path/'operator.lock'
    entered=threading.Event(); release=threading.Event(); errors=[]
    def hold():
        context = (exclusive_file_lock(path) if holder=='legacy' else
                   lock(path,end(3)) if holder=='bounded' else persistence._PROCESS_PATH_LOCKS_GUARD)
        try:
            with context:
                entered.set(); assert release.wait(2)
        except BaseException as error: errors.append(error)
    worker=threading.Thread(target=hold); worker.start()
    try:
        assert entered.wait(2)
        with pytest.raises(TimeoutError):
            with lock(path,end(.15)): pytest.fail('contended body entered')
    finally:
        release.set(); worker.join(3)
    assert not worker.is_alive() and not errors
    with lock(path,end()): pass


@pytest.mark.parametrize('holder',['legacy','bounded'])
def test_native_process_contention_then_original_deadline_success(tmp_path,holder):
    lock, _ = api()
    path=tmp_path/'operator.lock'; path.write_bytes(b'\0')
    ready, release=tmp_path/'ready',tmp_path/'release'
    child=subprocess.Popen((sys.executable,'-B',str(Path(__file__).with_name('alc_r0_deadline_lock_child.py')),
        holder,str(path),str(ready),str(release)),stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
    try:
        stop=end(3)
        while not ready.exists():
            assert child.poll() is None and time.monotonic_ns()<stop
            time.sleep(.01)
        with pytest.raises(TimeoutError):
            with lock(path,end(.15)): pytest.fail('native contention admitted')
        original=end(3)
        release.write_bytes(b'release')
        with lock(path,original): assert time.monotonic_ns()<original
        assert child.wait(timeout=3)==0
    finally:
        if child.poll() is None: child.terminate(); child.wait(timeout=3)
    assert path.read_bytes()==b'\0'


@pytest.mark.skipif(os.name!='nt',reason='Windows isolated native audit faults')
@pytest.mark.parametrize('mode',['unknown','unlock','post-native-expiry','badbytes'])
def test_post_acquisition_faults_prove_all_owned_cleanup(tmp_path,mode):
    from aluclu.alc_r0.checkpoint_owned_process import run_owned_process
    args=(sys.executable,'-B',str(Path(__file__).with_name('alc_r0_deadline_lock_fault_child.py')),
          mode,str(tmp_path/'operator.lock'))
    result=run_owned_process(args,cwd=tmp_path,environment=dict(os.environ),
        stdout_path=tmp_path/'fault.stdout',stderr_path=tmp_path/'fault.stderr',deadline_ns=end(10))
    assert result.exit_code==0 and result.active_processes==0 and not result.timed_out
    import json
    value=json.loads((tmp_path/'fault.stdout').read_bytes())
    assert value['mode']==mode and value['markers_empty'] and value['thread_reacquired']
    assert value['native_reacquired'] and value['file_retained']
    assert (tmp_path/'fault.stderr').read_bytes()==b''


def test_nested_validation_failure_preserves_outer(tmp_path):
    lock,Error=api(); module=importlib.import_module('aluclu.alc_r0.deadline_file_lock')
    import aluclu.cognition.persistence as persistence
    path=tmp_path/'operator.lock'; key=os.path.normcase(os.path.normpath(str(path)))
    with lock(path,end()):
        stream,_=module._OWNED.paths[key]
        # a+b uses append writes: truncate only this diagnostic-owned lock stream.
        stream.seek(0); stream.truncate(0); stream.write(b'x')
        with pytest.raises(Error):
            with lock(path,end()): pytest.fail('modified nested bytes accepted')
        assert not stream.closed and key in persistence._HELD_PROCESS_PATHS.paths
        assert key in module._OWNED.paths
        stream.seek(0); stream.truncate(0); stream.write(b'\0')
        with lock(path,end()): pass
    with lock(path,end()): pass


def test_stale_ancestor_validation_preserves_outer(tmp_path):
    lock,_=api(); module=importlib.import_module('aluclu.alc_r0.deadline_file_lock')
    import aluclu.cognition.persistence as persistence
    parent=tmp_path/'parent'; parent.mkdir()
    path=parent/'operator.lock'; moved=tmp_path/'moved'
    path.write_bytes(b'\0')
    old_ancestors=module._ancestors(path,end())
    # Windows refuses parent rename while an ordinary Python lock handle is
    # open. Replace before acquisition, then exercise stale evidence rejection.
    parent.rename(moved); parent.mkdir(); path.write_bytes(b'\0')
    key=os.path.normcase(os.path.normpath(str(path)))
    with lock(path,end()):
        stream,_=module._OWNED.paths[key]
        with pytest.raises(ValueError): module._validate(path,stream,old_ancestors,end())
        assert not stream.closed and key in persistence._HELD_PROCESS_PATHS.paths
        with lock(path,end()): pass
    with lock(path,end()): pass


@pytest.mark.skipif(os.name!='nt',reason='Windows junction rejection')
def test_junction_ancestor_is_rejected(tmp_path):
    lock,_=api(); target=tmp_path/'target'; target.mkdir(); alias=tmp_path/'alias'
    # Both exact targets are inside this diagnostic temporary directory.
    assert target.resolve().is_relative_to(tmp_path.resolve())
    result=subprocess.run(('cmd.exe','/c','mklink','/J',str(alias),str(target)),
                          capture_output=True,timeout=3)
    assert result.returncode==0,result.stderr
    with pytest.raises(ValueError):
        with lock(alias/'operator.lock',end()): pytest.fail('junction ancestor accepted')
    assert not (target/'operator.lock').exists()


def test_expiry_after_thread_acquisition_releases_count():
    module=importlib.import_module('aluclu.alc_r0.deadline_file_lock')
    class DelayedAcquisition:
        releases=0
        def acquire(self,blocking): time.sleep(.02); return True
        def release(self): self.releases+=1
    lock=DelayedAcquisition()
    with pytest.raises(TimeoutError):
        with module._thread_lock(lock,end(.01)): pytest.fail('late body entered')
    assert lock.releases==1
