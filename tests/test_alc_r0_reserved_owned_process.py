"""Harmless Windows lease fixtures; no model, GPU or experiment authority."""

import os
import sys
import time

import pytest

from aluclu.alc_r0.canonical import canonical_json_bytes, parse_canonical_json
from aluclu.alc_r0.reservation_store import ReservationStore
from aluclu.alc_r0.reserved_owned_process import ReservedOwnedLease

pytestmark = pytest.mark.skipif(os.name != "nt", reason="Windows owned lease")
ROOT = "a" * 64


def fixture(tmp_path, *, seconds=15, source=None, **overrides):
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
        stdout_limit_bytes="1024", stderr_limit_bytes="1024")),)
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
