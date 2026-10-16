"""Abrupt-parent diagnostic inside an outer owned job; no experiment launch."""

import json
import os
import sys
import time
from pathlib import Path

from aluclu.alc_r0.reservation_store import ReservationStore
from aluclu.alc_r0.reserved_owned_process import ReservedOwnedLease


def main():
    directory = Path(sys.argv[1])
    owner_root, declaration, deadline, phase = sys.argv[2:]
    deadline = int(deadline)
    store = ReservationStore(directory / "reservations", (bytes.fromhex(declaration),))
    sentinel = directory / "sentinel"
    source = ("import subprocess,sys,time;from pathlib import Path;"
        "subprocess.Popen([sys.executable,'-I','-c','import time;time.sleep(60)']);"
        f"Path({str(sentinel)!r}).write_text('executed');time.sleep(60)")

    def abrupt(root):
        print(json.dumps(dict(phase=phase, owner_root=root)), flush=True)
        os._exit(73)

    class InterruptedCreation(ReservedOwnedLease):
        def _observe_creation_time(self):
            result = super()._observe_creation_time()
            abrupt(owner_root)
            return result

    lease_class = InterruptedCreation if phase == "creation" else ReservedOwnedLease
    with lease_class(store, owner_root, "r1", (sys.executable, "-I", "-c", source),
        cwd=directory, environment=dict(os.environ), stdout_path=directory / "inner.stdout",
        stderr_path=directory / "inner.stderr", deadline_ns=deadline,
        clock_domain_root="a" * 64) as lease:
        ready = lease.publish_identity("a" * 64, "a" * 64)
        if phase == "ready":
            abrupt(ready.sha256)
        running = lease.resume_verified(ready.sha256)
        while not sentinel.exists():
            if time.monotonic_ns() >= deadline:
                raise TimeoutError("fixture child marker absent within original deadline")
            time.sleep(0.01)
        abrupt(running.sha256)


if __name__ == "__main__":
    main()
