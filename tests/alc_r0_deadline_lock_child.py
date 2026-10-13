"""Closed harmless native contention holder, never experiment launcher."""
import sys
import time
from pathlib import Path
from aluclu.cognition.persistence import exclusive_file_lock


def main():
    if len(sys.argv)!=5 or sys.argv[1] not in ('legacy','bounded'): raise ValueError('closed holder mode')
    kind,path,ready,release=sys.argv[1],*(Path(v) for v in sys.argv[2:])
    deadline=time.monotonic_ns()+5_000_000_000
    if kind=='legacy': context=exclusive_file_lock(path)
    else:
        from aluclu.alc_r0.deadline_file_lock import deadline_file_lock
        context=deadline_file_lock(path,deadline)
    with context:
        ready.write_bytes(b'held')
        while not release.exists():
            if time.monotonic_ns()>=deadline: raise TimeoutError('finite holder expired')
            time.sleep(.01)


if __name__=='__main__': main()
