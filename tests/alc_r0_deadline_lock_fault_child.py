"""Isolated native audit faults, not production callback injection."""
import errno
import json
import os
from pathlib import Path
import subprocess
import sys
import threading
import time

from aluclu.alc_r0 import deadline_file_lock as module
from aluclu.cognition import persistence


def main():
    if os.name!='nt' or len(sys.argv)!=3 or sys.argv[1] not in (
            'unknown','unlock','post-native-expiry','badbytes'):
        raise ValueError('closed Windows fault mode')
    mode=sys.argv[1]; path=Path(sys.argv[2]); path.write_bytes(b'x' if mode=='badbytes' else b'\0')
    deadline=time.monotonic_ns()+200_000_000
    key,entry=module._registry(path,deadline)  # retain SAME shared RLock strongly
    counters={'acquire':0,'unlock':0}; armed=True; body=False
    def audit(event,args):
        nonlocal armed
        if event!='msvcrt.locking': return
        _,operation,_=args
        if operation==0:
            counters['unlock']+=1
            if mode=='unlock' and armed:
                armed=False; raise OSError(errno.EIO,'diagnostic unlock refusal')
        else:
            counters['acquire']+=1
            if armed and mode=='unknown':
                armed=False; raise OSError(errno.EIO,'diagnostic acquisition refusal')
            if armed and mode=='post-native-expiry':
                armed=False
                while time.monotonic_ns()<deadline: time.sleep(.002)
    sys.addaudithook(audit)  # isolated child only, parent/native API not patched
    expected=(ValueError if mode=='badbytes' else TimeoutError if mode=='post-native-expiry' else OSError)
    try:
        with module.deadline_file_lock(path,deadline): body=True
    except expected: pass
    else: raise AssertionError('fault did not propagate')
    assert body==(mode=='unlock')
    assert counters['acquire']==1 and counters['unlock']==(0 if mode=='unknown' else 1)
    assert key==os.path.normcase(os.path.normpath(str(path)))
    assert key not in getattr(persistence._HELD_PROCESS_PATHS,'paths',set())
    assert key not in getattr(module._OWNED,'paths',{})
    # Different thread tests RLock cleanup (same-thread recursion would hide leaks).
    acquired=[]
    def verify_thread():
        found=entry.lock.acquire(blocking=False); acquired.append(found)
        if found: entry.lock.release()
    thread=threading.Thread(target=verify_thread); thread.start(); thread.join(2)
    assert not thread.is_alive() and acquired==[True]
    # Different native process proves handle/OS-lock release, including unlock error.
    ready,release=path.with_name('native-ready'),path.with_name('native-release')
    child=subprocess.Popen((sys.executable,'-B',str(Path(__file__).with_name('alc_r0_deadline_lock_child.py')),
        'legacy',str(path),str(ready),str(release)),stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
    try:
        stop=time.monotonic_ns()+3_000_000_000
        while not ready.exists():
            assert child.poll() is None and time.monotonic_ns()<stop
            time.sleep(.01)
        release.write_bytes(b'release')
        assert child.wait(timeout=3)==0
    finally:
        if child.poll() is None: child.terminate(); child.wait(timeout=3)
    print(json.dumps(dict(mode=mode,body=body,native_calls_before_reacquire=counters,
        markers_empty=True,thread_reacquired=True,native_reacquired=True,file_retained=path.exists()),sort_keys=True))


if __name__=='__main__': main()
