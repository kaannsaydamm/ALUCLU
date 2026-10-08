"""Harmless Windows lease fixtures; no model, GPU or experiment authority."""

import os
import sys
import time

import pytest

from aluclu.alc_r0.canonical import canonical_json_bytes, sha256_bytes
from aluclu.alc_r0.reservation_store import ReservationStore
from aluclu.alc_r0.reserved_owned_process import ReservedOwnedLease

pytestmark = pytest.mark.skipif(os.name != "nt", reason="Windows owned lease")
ROOT = "a" * 64


def fixture(tmp_path, *, seconds=15, source=None, stdout_cap=1024, stderr_cap=1024,
            **overrides):
    namespace = tmp_path / "reservations"
    namespace.mkdir()
    (namespace / "intents").mkdir()
    ceiling = int(seconds * 1_000_000_000)
    declarations = (canonical_json_bytes(dict(
        experiment_id="alc-r0-smollm2-135m-v1", reservation_id="r1",
        run_id="alc-r0-v1-pilot-fixture-s20260916", attempt_id="a001", segment="initial",
        declaration_root=ROOT, device="cpu", useful_wall_ceiling_ns=str(ceiling),
        cleanup_ceiling_ns="10000000000", charge_envelope_ns=str(ceiling + 10_000_000_000),
        gpu_reservation_ns="0", research_growth_bytes="1024", physical_growth_bytes="4096",
        stdout_limit_bytes=str(stdout_cap), stderr_limit_bytes=str(stderr_cap))),)
    store = ReservationStore(namespace, declarations)
    initial = store.initialize(store.initialization_intent())
    origin = time.monotonic_ns()
    event = canonical_json_bytes(dict(sequence="1", previous_root=initial.snapshot.root,
        reservation_id="r1", kind="reserve", evidence_root=ROOT, declaration_root=ROOT,
        entry_utc_ns=str(time.time_ns()), clock_domain_root=ROOT,
        entry_monotonic_ns=str(origin), useful_deadline_monotonic_ns=str(origin + ceiling)))
    reserved = store.commit(store.prepare(initial.sha256, event, ROOT))
    sentinel = tmp_path / "sentinel"
    source = source or f"from pathlib import Path; Path({str(sentinel)!r}).write_text('executed')"
    arguments = dict(store=store, expected_owner_root=reserved.sha256, reservation_id="r1",
        command=(sys.executable, "-I", "-c", source), cwd=tmp_path,
        environment=dict(os.environ), stdout_path=tmp_path / "stdout.log",
        stderr_path=tmp_path / "stderr.log", deadline_ns=origin + ceiling,
        clock_domain_root=ROOT)
    arguments.update(overrides)
    return arguments, store, reserved, sentinel


def test_identity_is_durable_before_any_execution(tmp_path):
    arguments, store, reserved, sentinel = fixture(tmp_path)
    with ReservedOwnedLease(**arguments) as lease:
        assert not sentinel.exists()
        identity = lease.identity
        assert identity.pid > 0 and identity.creation_filetime_100ns > 0
        assert len(identity.owner_nonce) == 32
        assert store.read(reserved.sha256).snapshot.reservations[0].state == "RESERVED"
        ready = lease.publish_identity(ROOT, ROOT)
        view = ReservationStore(store.root, store.declarations).read(ready.sha256).snapshot.reservations[0]
        assert view.state == "READY"
        assert (view.pid, view.creation_filetime_100ns, view.owner_nonce) == (
            identity.pid, identity.creation_filetime_100ns, identity.owner_nonce)
        assert not sentinel.exists()
        running = lease.resume_verified(ready.sha256)
        assert store.read(running.sha256).snapshot.reservations[0].state == "RUNNING"
        terminal = lease.wait_terminal()
        assert terminal.process.exit_code == 0 and not terminal.process.timed_out
        assert terminal.process.active_processes == 0
        assert terminal.identity == identity and terminal.owner_root == running.sha256
    assert sentinel.read_text() == "executed"
    # Observing terminal is not automatic charge reconciliation/release.
    assert store.read(running.sha256).snapshot.reservations[0].state == "RUNNING"


def test_close_ready_child_never_executes_or_releases(tmp_path):
    arguments, store, _, sentinel = fixture(tmp_path)
    with ReservedOwnedLease(**arguments) as lease:
        ready = lease.publish_identity(ROOT, ROOT)
    assert not sentinel.exists()
    view = store.read(ready.sha256).snapshot
    assert view.reservations[0].state == "READY" and view.pending_physical_bytes == 4096
    with pytest.raises(RuntimeError):
        lease.resume_verified(ready.sha256)


@pytest.mark.parametrize("override", [dict(expected_owner_root="b" * 64),
    dict(clock_domain_root="b" * 64), dict(deadline_ns=1)])
def test_invalid_reservation_denied_before_outputs(tmp_path, override):
    arguments, store, reserved, sentinel = fixture(tmp_path, **override)
    with pytest.raises((ValueError, TimeoutError)):
        with ReservedOwnedLease(**arguments):
            pytest.fail("invalid lease entered")
    assert not sentinel.exists() and not (tmp_path / "stdout.log").exists()
    assert store.read(reserved.sha256).snapshot.reservations[0].state == "RESERVED"


def test_resume_requires_local_exact_ready_root_and_one_call(tmp_path):
    arguments, _, _, sentinel = fixture(tmp_path)
    with ReservedOwnedLease(**arguments) as lease:
        with pytest.raises(RuntimeError):
            lease.resume_verified(ROOT)
        ready = lease.publish_identity(ROOT, ROOT)
        with pytest.raises(ValueError):
            lease.resume_verified("b" * 64)
        assert not sentinel.exists()
        lease.resume_verified(ready.sha256)
        with pytest.raises(RuntimeError):
            lease.resume_verified(ready.sha256)
        lease.wait_terminal()
        with pytest.raises(RuntimeError):
            lease.wait_terminal()


def test_nonzero_exit_retained(tmp_path):
    arguments, _, _, _ = fixture(tmp_path, source="raise SystemExit(7)")
    with ReservedOwnedLease(**arguments) as lease:
        ready = lease.publish_identity(ROOT, ROOT)
        lease.resume_verified(ready.sha256)
        assert lease.wait_terminal().process.exit_code == 7


def test_declared_stdout_cap_enforced_on_real_child(tmp_path):
    # Exactly one byte above the existing audited fixture declaration, not an
    # invented cap. The current direct-to-file lease must reproduce this gap.
    gate = tmp_path / "output-ready"
    source = ("import os,time;from pathlib import Path;"
        f"gate=Path({str(gate)!r})\n"
        "while not gate.exists():time.sleep(0.005)\n"
        "os.write(1,b'x'*1025)")
    arguments, store, _, _ = fixture(tmp_path, source=source)
    with ReservedOwnedLease(**arguments) as lease:
        ready = lease.publish_identity(ROOT, ROOT)
        running = lease.resume_verified(ready.sha256)
        gate.write_bytes(b"ready")
        terminal = lease.wait_terminal()
        assert terminal.process.active_processes == 0
    assert arguments["stdout_path"].read_bytes() == b"x" * 1024
    assert not terminal.output.valid and terminal.output.stdout.excess
    assert terminal.output.stdout.limit_bytes == 1024
    assert terminal.output.stdout.persisted_bytes == 1024
    assert store.read(running.sha256).snapshot.reservations[0].state == "RUNNING"


@pytest.mark.parametrize("payload,cap", [(b"",0), (b"\x00\xff\r\n",4),
    (b"abc",8)], ids=["empty-zero","binary-exact","under-cap"])
def test_real_child_independent_binary_caps_and_digests(tmp_path, payload, cap):
    import hashlib
    gate = tmp_path / "output-ready"
    source = ("import os,time;from pathlib import Path;"
        f"gate=Path({str(gate)!r})\n"
        "while not gate.exists():time.sleep(0.005)\n"
        f"os.write(1,{payload!r});os.write(2,{payload!r})")
    arguments, _, _, _ = fixture(tmp_path, source=source,
        stdout_cap=cap, stderr_cap=cap)
    with ReservedOwnedLease(**arguments) as lease:
        ready = lease.publish_identity(ROOT,ROOT)
        lease.resume_verified(ready.sha256)
        gate.write_bytes(b"ready")
        receipt = lease.wait_terminal()
        assert receipt.process.exit_code == 0 and receipt.output.valid
        assert receipt.output.cleanup_deadline_ns == lease._job.cleanup_deadline_ns
        assert receipt.output.cleanup_deadline_ns <= arguments["deadline_ns"] + 10_000_000_000
    for name in ("stdout","stderr"):
        facts = getattr(receipt.output,name)
        assert facts.limit_bytes == cap and facts.received_bytes == len(payload)
        assert facts.persisted_bytes == len(payload) and facts.resources_closed
        assert facts.file_sha256 == hashlib.sha256(payload).hexdigest()
        assert arguments[name + "_path"].read_bytes() == payload


@pytest.mark.parametrize("descriptor", [1,2])
def test_excess_child_stopped_without_timeout_or_unbounded_file(tmp_path, descriptor):
    gate = tmp_path / "output-ready"
    source = ("import os,time;from pathlib import Path;"
        f"gate=Path({str(gate)!r})\n"
        "while not gate.exists():time.sleep(0.005)\n"
        f"while True:os.write({descriptor},b'z'*4096)")
    arguments, _, _, _ = fixture(tmp_path, source=source)
    with ReservedOwnedLease(**arguments) as lease:
        ready = lease.publish_identity(ROOT,ROOT)
        lease.resume_verified(ready.sha256)
        gate.write_bytes(b"ready")
        receipt = lease.wait_terminal()
    assert receipt.process.exit_code == 124 and not receipt.process.timed_out
    assert receipt.process.active_processes == 0 and not receipt.output.valid
    facts = receipt.output.stdout if descriptor == 1 else receipt.output.stderr
    assert facts.excess and facts.persisted_bytes == 1024
    for target in (arguments["stdout_path"],arguments["stderr_path"]):
        assert target.stat().st_size <= 1024


@pytest.mark.parametrize("expire", [False,True], ids=["timely","incomplete"])
def test_partial_output_entry_pins_tail_before_internal_wait(tmp_path, expire):
    import threading
    from aluclu.alc_r0.bounded_process_output import OutputCleanupError
    from aluclu.alc_r0.reserved_owned_process import _LeaseOutputPair
    gate, pinned = threading.Event(), threading.Event()
    recorded = []
    arguments, store, reserved, _ = fixture(tmp_path)

    class FaultPair(_LeaseOutputPair):
        starts = 0
        def _read(self, reader):
            assert gate.wait(3), "bounded diagnostic gate timed out"
            return super()._read(reader)
        def _start_pump(self, thread):
            super()._start_pump(thread)
            self.starts += 1
            if self.starts == 2:
                raise OSError("fixture after actual second pump start")
        def _observe_terminal(self, deadline):
            # Capture all actual retained bounds BEFORE the observer can open
            # the read gate, inside the original partial-observation path.
            recorded.append((self._lease._cleanup_deadline,
                self._lease._job.cleanup_deadline_ns,self._deadline,deadline))
            pinned.set()
            return super()._observe_terminal(deadline)

    class FaultLease(ReservedOwnedLease):
        def _new_output(self, **values):
            return FaultPair(self, **values)
        def _pin_cleanup_deadline(self):
            first = self._cleanup_deadline is None
            result = super()._pin_cleanup_deadline()
            if first and expire:
                # Explicit diagnostic-only shorter observation seam. The
                # audited declaration's scientific ten-second tail is unchanged.
                self._cleanup_deadline = min(result,time.monotonic_ns()+20_000_000)
                self._job.cleanup_deadline_ns = self._cleanup_deadline
                result = self._cleanup_deadline
            return result

    def release_owned_gate():
        if pinned.wait(3) and expire:
            time.sleep(0.08)
        gate.set()

    observer = threading.Thread(target=release_owned_gate)
    observer.start()
    lease = FaultLease(**arguments)
    try:
        with pytest.raises(OutputCleanupError if expire else OSError):
            with lease:
                pytest.fail("partial entry succeeded")
        assert len(recorded) == 1
        assert len(set(recorded[0])) == 1
        assert recorded[0][0] == lease._output._deadline
        assert lease._information.process is None and lease._lock is None
        assert store.read(reserved.sha256).snapshot.reservations[0].state == "RESERVED"
        if expire:
            assert any("cleanup_deadline" in item.failure_kinds
                       for item in lease._output.observations())
    finally:
        gate.set()
        observer.join(3)
        assert not observer.is_alive()
        for stream in lease._output._streams:
            stream.thread.join(3)
            assert not stream.thread.is_alive()


def test_exited_root_with_live_writing_descendant_is_drained(tmp_path):
    import _winapi
    gate = tmp_path / "output-ready"
    descendant_gate = tmp_path / "root-observed-terminal"
    child = ("import os,time;from pathlib import Path;"
        f"gate=Path({str(descendant_gate)!r})\n"
        "while not gate.exists():time.sleep(0.005)\n"
        "while True:os.write(2,b'd'*4096)")
    source = ("import subprocess,sys,time;from pathlib import Path;"
        f"gate=Path({str(gate)!r})\n"
        "while not gate.exists():time.sleep(0.005)\n"
        f"subprocess.Popen([sys.executable,'-I','-c',{child!r}])")
    arguments, _, _, _ = fixture(tmp_path, source=source)
    with ReservedOwnedLease(**arguments) as lease:
        ready = lease.publish_identity(ROOT,ROOT)
        lease.resume_verified(ready.sha256)
        gate.write_bytes(b"ready")
        assert _winapi.WaitForSingleObject(lease._information.process,5000) == 0
        assert _winapi.GetExitCodeProcess(lease._information.process) == 0
        descendant_gate.write_bytes(b"root terminal")
        receipt = lease.wait_terminal()
    assert not receipt.process.timed_out and receipt.process.active_processes == 0
    assert receipt.process.total_processes >= 2
    assert not receipt.output.valid and receipt.output.stderr.excess
    assert arguments["stderr_path"].read_bytes() == b"d" * 1024


def test_timeout_drains_root_and_descendant(tmp_path):
    source = ("import subprocess,sys,time; "
        "subprocess.Popen([sys.executable,'-I','-c','import time;time.sleep(60)']); "
        "print('root-ready',flush=True);time.sleep(60)")
    arguments, _, _, _ = fixture(tmp_path, seconds=3, source=source)
    with ReservedOwnedLease(**arguments) as lease:
        ready = lease.publish_identity(ROOT, ROOT)
        lease.resume_verified(ready.sha256)
        terminal = lease.wait_terminal().process
        assert terminal.timed_out and terminal.exit_code == 124
        assert terminal.active_processes == 0 and terminal.total_processes >= 2
    assert "root-ready" in (tmp_path / "stdout.log").read_text()


class FailAfterEvent(ReservedOwnedLease):
    """Explicit diagnostic boundary, not monkeypatch or production retry."""
    fail_kind = None

    def _publish_event(self, kind, **fields):
        receipt = super()._publish_event(kind, **fields)
        if kind == self.fail_kind:
            raise OSError("fixture durable event response lost")
        return receipt


@pytest.mark.parametrize("kind,state", [("child_created", "CREATED"),
    ("identity_published", "READY"), ("running", "RUNNING")])
def test_publication_response_loss_closes_child_without_release(tmp_path, kind, state):
    arguments, store, _, sentinel = fixture(tmp_path)
    class FaultLease(FailAfterEvent):
        fail_kind = kind
    with FaultLease(**arguments) as lease:
        with pytest.raises(OSError, match="response lost"):
            ready = lease.publish_identity(ROOT, ROOT)
            lease.resume_verified(ready.sha256)
        assert lease._information.process is None and lease._information.thread is None
        assert lease._state == "CLOSED"
    owner = (store.root / "owner.json").read_bytes()
    from aluclu.alc_r0.canonical import sha256_bytes
    retained = ReservationStore(store.root, store.declarations).read(sha256_bytes(owner))
    assert retained.snapshot.reservations[0].state == state
    assert retained.snapshot.pending_physical_bytes == 4096
    if kind != "running":
        assert not sentinel.exists()


def test_global_lock_released_before_wait_and_unrelated_child_survives(tmp_path):
    import subprocess
    from concurrent.futures import ThreadPoolExecutor
    unrelated = subprocess.Popen((sys.executable, "-I", "-c", "import time;time.sleep(60)"))
    try:
        arguments, store, _, _ = fixture(tmp_path, source="import time;time.sleep(0.2)")
        with ReservedOwnedLease(**arguments) as lease:
            ready = lease.publish_identity(ROOT, ROOT)
            running = lease.resume_verified(ready.sha256)
            with ThreadPoolExecutor(max_workers=1) as executor:
                reread = executor.submit(store.read, running.sha256).result(timeout=3)
            assert reread.snapshot.reservations[0].state == "RUNNING"
            lease.wait_terminal()
        assert unrelated.poll() is None
    finally:
        unrelated.terminate()
        unrelated.wait(timeout=10)


@pytest.mark.parametrize("failure", [OSError, KeyboardInterrupt])
def test_enter_failure_after_creation_drains_owned_handle_and_unlocks(tmp_path, failure):
    import _winapi
    from concurrent.futures import ThreadPoolExecutor
    arguments, store, reserved, sentinel = fixture(tmp_path)
    captured = []

    class FailIdentity(ReservedOwnedLease):
        def _observe_creation_time(self):
            current = _winapi.GetCurrentProcess()
            captured.append(_winapi.DuplicateHandle(current, self._information.process,
                current, 0, False, _winapi.DUPLICATE_SAME_ACCESS))
            super()._observe_creation_time()
            raise failure("fixture after actual creation, before identity")

    lease = FailIdentity(**arguments)
    try:
        with pytest.raises(failure, match="before identity"):
            with lease:
                pass
        assert len(captured) == 1
        assert _winapi.WaitForSingleObject(captured[0], 5000) == 0
        assert _winapi.GetExitCodeProcess(captured[0]) == 124
        assert not sentinel.exists()
        assert lease._information.process is None and lease._information.thread is None
        with ThreadPoolExecutor(max_workers=1) as executor:
            receipt = executor.submit(store.read, reserved.sha256).result(timeout=3)
        assert receipt.snapshot.reservations[0].state == "RESERVED"
        assert receipt.snapshot.pending_physical_bytes == 4096
    finally:
        for handle in captured:
            _winapi.CloseHandle(handle)


@pytest.mark.parametrize("stream", ["stdout", "stderr"])
def test_output_collision_preserves_data_and_releases_global_lock(tmp_path, stream):
    from concurrent.futures import ThreadPoolExecutor
    arguments, store, reserved, sentinel = fixture(tmp_path)
    target = tmp_path / f"{stream}.log"
    target.write_bytes(b"existing diagnostic bytes")
    lease = ReservedOwnedLease(**arguments)
    with pytest.raises(FileExistsError):
        with lease:
            pytest.fail("exclusive output collision entered")
    assert target.read_bytes() == b"existing diagnostic bytes"
    assert not sentinel.exists() and lease._information.process is None
    with ThreadPoolExecutor(max_workers=1) as executor:
        receipt = executor.submit(store.read, reserved.sha256).result(timeout=3)
    assert receipt.snapshot.reservations[0].state == "RESERVED"


def test_lifecycle_and_foreign_thread_cannot_publish_resume_or_close(tmp_path):
    from concurrent.futures import ThreadPoolExecutor
    arguments, store, _, sentinel = fixture(tmp_path)
    lease = ReservedOwnedLease(**arguments)
    with lease:
        with pytest.raises(RuntimeError):
            lease.__enter__()
        ready = lease.publish_identity(ROOT, ROOT)
        with pytest.raises(RuntimeError):
            lease.publish_identity(ROOT, ROOT)
        with ThreadPoolExecutor(max_workers=1) as executor:
            for method, values in ((lease.resume_verified, (ready.sha256,)),
                                   (lease.__exit__, (None, None, None))):
                with pytest.raises(RuntimeError, match="thread"):
                    executor.submit(method, *values).result(timeout=3)
        assert not sentinel.exists()
        assert store.read(ready.sha256).snapshot.reservations[0].state == "READY"
    with pytest.raises(RuntimeError):
        lease.__enter__()
    with pytest.raises(RuntimeError):
        lease.publish_identity(ROOT, ROOT)
    with pytest.raises(RuntimeError):
        lease.wait_terminal()


def test_ready_deadline_expiry_does_not_resume_or_renew(tmp_path):
    arguments, store, _, sentinel = fixture(tmp_path, seconds=2)
    with ReservedOwnedLease(**arguments) as lease:
        ready = lease.publish_identity(ROOT, ROOT)
        time.sleep(max(0, (arguments["deadline_ns"] - time.monotonic_ns()) / 1e9) + 0.02)
        with pytest.raises(TimeoutError, match="original reservation deadline"):
            lease.resume_verified(ready.sha256)
        assert lease._information.process is None
    assert not sentinel.exists()
    assert store.read(ready.sha256).snapshot.reservations[0].state == "READY"


def test_identity_receipt_binds_exact_handle_fields_and_reservation(tmp_path):
    arguments, _, _, _ = fixture(tmp_path)
    with ReservedOwnedLease(**arguments) as lease:
        identity = lease.identity
        expected = sha256_bytes(canonical_json_bytes(dict(schema="alc-r0-owned-child-v1",
            reservation_id="r1", pid=str(identity.pid),
            creation_filetime_100ns=str(identity.creation_filetime_100ns),
            owner_nonce=identity.owner_nonce)))
        assert identity.receipt_root == expected


def test_nonreserved_current_owner_denied_before_second_child(tmp_path):
    arguments, store, _, sentinel = fixture(tmp_path)
    with ReservedOwnedLease(**arguments) as lease:
        ready = lease.publish_identity(ROOT, ROOT)
    arguments.update(expected_owner_root=ready.sha256,
        stdout_path=tmp_path / "second.stdout", stderr_path=tmp_path / "second.stderr")
    with pytest.raises(ValueError, match="reservation state"):
        with ReservedOwnedLease(**arguments):
            pytest.fail("READY is not a fresh creation reservation")
    assert not (tmp_path / "second.stdout").exists() and not sentinel.exists()
    assert store.read(ready.sha256).snapshot.reservations[0].state == "READY"


def test_future_but_changed_deadline_is_not_a_renewal(tmp_path):
    arguments, store, reserved, sentinel = fixture(tmp_path)
    arguments["deadline_ns"] += 1
    with pytest.raises(ValueError, match="original clock/deadline"):
        with ReservedOwnedLease(**arguments):
            pytest.fail("changed future deadline admitted")
    assert not (tmp_path / "stdout.log").exists() and not sentinel.exists()
    assert store.read(reserved.sha256).snapshot.reservations[0].state == "RESERVED"


def test_caller_receipt_dataclass_is_not_resume_authority(tmp_path):
    from dataclasses import replace
    arguments, _, _, sentinel = fixture(tmp_path)
    with ReservedOwnedLease(**arguments) as lease:
        ready = lease.publish_identity(ROOT, ROOT)
        forged = replace(ready, snapshot=replace(ready.snapshot, root="b" * 64))
        with pytest.raises(ValueError, match="locally retained exact READY"):
            lease.resume_verified(forged)
        assert not sentinel.exists()
        lease.resume_verified(ready.sha256)
        assert lease.wait_terminal().process.exit_code == 0


@pytest.mark.parametrize("phase", ["creation", "ready", "running"])
def test_abrupt_lease_parent_exit_leaves_no_owned_orphan(tmp_path, phase):
    import json
    from pathlib import Path
    from aluclu.alc_r0.checkpoint_owned_process import run_owned_process
    arguments, store, reserved, sentinel = fixture(tmp_path, seconds=12)
    worker = Path(__file__).with_name("alc_r0_reserved_owned_worker.py")
    receipt = run_owned_process((sys.executable, "-s", str(worker), str(tmp_path),
        reserved.sha256, store.declarations[0].hex(), str(arguments["deadline_ns"]), phase),
        cwd=tmp_path, environment=dict(os.environ), stdout_path=tmp_path / "outer.stdout",
        stderr_path=tmp_path / "outer.stderr", deadline_ns=arguments["deadline_ns"])
    assert receipt.exit_code == 73 and not receipt.timed_out
    assert receipt.active_processes == 0 and receipt.total_processes >= 2
    if phase == "running":
        assert receipt.total_processes >= 3
        assert sentinel.read_text() == "executed"
    else:
        assert not sentinel.exists()
    report = json.loads((tmp_path / "outer.stdout").read_text())
    assert report["phase"] == phase
    fresh = ReservationStore(store.root, store.declarations).read(report["owner_root"])
    assert fresh.snapshot.reservations[0].state == {
        "creation": "RESERVED", "ready": "READY", "running": "RUNNING"}[phase]
    assert fresh.snapshot.pending_physical_bytes == 4096
    assert (tmp_path / "outer.stderr").read_bytes() == b""
