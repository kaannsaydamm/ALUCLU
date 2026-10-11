"""Temporary local reservation storage only; no model or scientific launch."""

import pytest
from concurrent.futures import ThreadPoolExecutor
from aluclu.cognition.contracts import UnsafePathError

from aluclu.alc_r0.canonical import canonical_json_bytes, parse_canonical_json, sha256_bytes
from aluclu.alc_r0.reservation_store import PreparedReservationIntent

from aluclu.alc_r0.reservation_store import ReservationStore, ReservationStoreError


def test_explicit_store_requires_absolute_existing_namespace():
    with pytest.raises(ReservationStoreError):
        ReservationStore("relative", ())


ROOT, OTHER = "a" * 64, "b" * 64


def declarations():
    return (canonical_json_bytes(dict(experiment_id="alc-r0-smollm2-135m-v1", reservation_id="r1",
        run_id="alc-r0-v1-pilot-fixture-s20260916", attempt_id="a001", segment="initial",
        declaration_root=ROOT, device="gpu", useful_wall_ceiling_ns="100",
        cleanup_ceiling_ns="10000000000", charge_envelope_ns="10000000100",
        gpu_reservation_ns="10000000100", research_growth_bytes="50", physical_growth_bytes="100",
        stdout_limit_bytes="20", stderr_limit_bytes="20")),)


def setup(tmp_path, cls=ReservationStore):
    (tmp_path / "intents").mkdir()
    store = cls(tmp_path, declarations())
    initial = store.initialize(store.initialization_intent())
    return store, initial


def reserve(receipt):
    return canonical_json_bytes(dict(sequence=str(receipt.snapshot.event_count + 1),
        previous_root=receipt.snapshot.root, reservation_id="r1", kind="reserve", evidence_root=ROOT,
        declaration_root=ROOT, entry_utc_ns="1", clock_domain_root=ROOT,
        entry_monotonic_ns="1", useful_deadline_monotonic_ns="101"))


def inventory(root):
    return {str(path.relative_to(root)): path.read_bytes() for path in root.rglob("*") if path.is_file()}


def test_durable_initialize_commit_fresh_instance_and_reacknowledge(tmp_path):
    store, initial = setup(tmp_path)
    assert store.initialize(store.initialization_intent()) == initial
    intent = store.prepare(initial.sha256, reserve(initial), ROOT)
    assert not (tmp_path / "intents" / "intent-000001.json").exists()
    receipt = store.commit(intent)
    assert receipt.snapshot.reservations[0].state == "RESERVED"
    assert receipt.snapshot.outstanding_gpu_ns == 10000000100
    fresh = ReservationStore(tmp_path, declarations())
    assert fresh.read(receipt.sha256) == receipt
    journal = (tmp_path / "journal.jsonl").read_bytes()
    assert fresh.resume(intent) == receipt
    assert fresh.resume(intent) == receipt
    assert (tmp_path / "journal.jsonl").read_bytes() == journal
    with pytest.raises(ValueError):
        store.read(initial.sha256)
    with pytest.raises(ValueError):
        store.commit(intent)


class FailAfterIntent(ReservationStore):
    def _persist(self, path, intent):
        super()._persist(path, intent)
        if path.name.startswith("intent-"):
            raise OSError("fixture after durable intent")


class FailBeforePublish(ReservationStore):
    def _publish(self, candidate):
        if parse_canonical_json(candidate)["generation"] != "0":
            raise OSError("fixture durable journal, before owner")
        super()._publish(candidate)


class FailAfterPublish(ReservationStore):
    def _publish(self, candidate):
        super()._publish(candidate)
        if parse_canonical_json(candidate)["generation"] != "0":
            raise OSError("fixture owner visible, response lost")


@pytest.mark.parametrize("cls", [FailAfterIntent, FailBeforePublish, FailAfterPublish])
def test_explicit_forward_recovery_never_duplicates_or_releases(tmp_path, cls):
    store, initial = setup(tmp_path, cls)
    intent = store.prepare(initial.sha256, reserve(initial), ROOT)
    with pytest.raises(OSError):
        store.commit(intent)
    fresh = ReservationStore(tmp_path, declarations())
    receipt = fresh.resume(intent)
    assert receipt.snapshot.event_count == 1
    assert receipt.snapshot.outstanding_gpu_ns == 10000000100
    assert receipt.snapshot.reservations[0].state == "RESERVED"
    assert fresh.read(receipt.sha256) == receipt


class InitAfterIntent(ReservationStore):
    def _persist(self, path, intent):
        super()._persist(path, intent)
        raise OSError("fixture after initialization intent")


class InitBeforeOwner(ReservationStore):
    def _publish(self, candidate):
        raise OSError("fixture empty journal, no genesis owner")


class InitAfterOwner(ReservationStore):
    def _publish(self, candidate):
        super()._publish(candidate)
        raise OSError("fixture genesis visible, response lost")


@pytest.mark.parametrize("cls", [InitAfterIntent, InitBeforeOwner, InitAfterOwner])
def test_explicit_initialization_uncertainty_matrix(tmp_path, cls):
    (tmp_path / "intents").mkdir()
    store = cls(tmp_path, declarations())
    intent = store.initialization_intent()
    with pytest.raises(OSError):
        store.initialize(intent)
    fresh = ReservationStore(tmp_path, declarations())
    receipt = fresh.initialize(intent)
    assert receipt.snapshot.event_count == 0
    assert fresh.read(receipt.sha256) == receipt


def test_candidate_owner_old_journal_denied_without_repair(tmp_path):
    store, initial = setup(tmp_path)
    old_journal = (tmp_path / "journal.jsonl").read_bytes()
    intent = store.prepare(initial.sha256, reserve(initial), ROOT)
    receipt = store.commit(intent)
    # Deliberate fixture rollback, not an implementation repair API.
    (tmp_path / "journal.jsonl").write_bytes(old_journal)
    before = inventory(tmp_path)
    with pytest.raises(ValueError, match="recovery pair"):
        store.resume(intent)
    assert inventory(tmp_path) == before
    assert (tmp_path / "owner.json").read_bytes() == receipt.data


@pytest.mark.parametrize("mutation", ["missing-intent", "changed-review", "partial-journal", "missing-owner"])
def test_tampering_or_rollback_cannot_be_adopted(tmp_path, mutation):
    store, initial = setup(tmp_path)
    intent = store.prepare(initial.sha256, reserve(initial), ROOT)
    receipt = store.commit(intent)
    path = tmp_path / "intents" / "intent-000001.json"
    if mutation == "missing-intent":
        path.unlink()
    elif mutation == "changed-review":
        value = parse_canonical_json(path.read_bytes())
        value["review_root"] = OTHER
        path.write_bytes(canonical_json_bytes(value))
    elif mutation == "partial-journal":
        journal = tmp_path / "journal.jsonl"
        journal.write_bytes(journal.read_bytes()[:-1])
    else:
        (tmp_path / "owner.json").unlink()
    before = inventory(tmp_path)
    with pytest.raises((ValueError, RuntimeError, FileNotFoundError)):
        store.read(receipt.sha256)
    with pytest.raises((ValueError, RuntimeError, FileNotFoundError)):
        store.resume(intent)
    assert inventory(tmp_path) == before


def test_exact_old_owner_new_journal_forward_recovery_preserves_new_reservation(tmp_path):
    store, initial = setup(tmp_path)
    intent = store.prepare(initial.sha256, reserve(initial), ROOT)
    receipt = store.commit(intent)
    (tmp_path / "owner.json").write_bytes(initial.data)
    journal = (tmp_path / "journal.jsonl").read_bytes()
    assert store.resume(intent) == receipt
    assert (tmp_path / "journal.jsonl").read_bytes() == journal
    assert store.read(receipt.sha256).snapshot.outstanding_gpu_ns == 10000000100


def test_bad_semantic_event_rejected_before_any_write(tmp_path):
    store, initial = setup(tmp_path)
    value = parse_canonical_json(reserve(initial))
    value["previous_root"] = OTHER
    before = inventory(tmp_path)
    with pytest.raises(ValueError):
        store.prepare(initial.sha256, canonical_json_bytes(value), ROOT)
    assert inventory(tmp_path) == before


def test_pending_intent_requires_explicit_resume_not_read_or_commit(tmp_path):
    store, initial = setup(tmp_path, FailAfterIntent)
    intent = store.prepare(initial.sha256, reserve(initial), ROOT)
    with pytest.raises(OSError):
        store.commit(intent)
    fresh = ReservationStore(tmp_path, declarations())
    before = inventory(tmp_path)
    for action in (lambda: fresh.read(initial.sha256), lambda: fresh.prepare(initial.sha256, reserve(initial), ROOT), lambda: fresh.commit(intent)):
        with pytest.raises(ValueError):
            action()
    assert inventory(tmp_path) == before
    assert fresh.resume(intent).snapshot.event_count == 1


def test_two_coordinators_one_predecessor_exactly_one_commit(tmp_path):
    store, initial = setup(tmp_path)
    second = ReservationStore(tmp_path, declarations())
    one = store.prepare(initial.sha256, reserve(initial), ROOT)
    two = second.prepare(initial.sha256, reserve(initial), OTHER)
    def compete(args):
        writer, intent = args
        try:
            return writer.commit(intent)
        except ValueError:
            return None
    with ThreadPoolExecutor(max_workers=2) as pool:
        results = tuple(pool.map(compete, ((store, one), (second, two))))
    winners = [receipt for receipt in results if receipt is not None]
    assert len(winners) == 1
    assert store.read(winners[0].sha256) == winners[0]
    assert winners[0].snapshot.event_count == 1


def test_modified_self_hashed_intent_not_authority(tmp_path):
    store, initial = setup(tmp_path)
    intent = store.prepare(initial.sha256, reserve(initial), ROOT)
    value = parse_canonical_json(intent.data)
    value["candidate_owner"]["reservation_root"] = OTHER
    data = canonical_json_bytes(value)
    forged = PreparedReservationIntent(data, sha256_bytes(data))
    before = inventory(tmp_path)
    with pytest.raises(ValueError):
        store.commit(forged)
    assert inventory(tmp_path) == before


@pytest.mark.parametrize("name", ["unexpected", "intent-000003.json"])
def test_unexpected_inventory_denies_without_reset(tmp_path, name):
    store, initial = setup(tmp_path)
    (tmp_path / "intents" / name).write_bytes(b"{}")
    before = inventory(tmp_path)
    with pytest.raises(ValueError):
        store.read(initial.sha256)
    assert inventory(tmp_path) == before


def test_missing_initialization_intent_cannot_adopt_empty_storage(tmp_path):
    store, initial = setup(tmp_path)
    (tmp_path / "intents" / "initialization.json").unlink()
    before = inventory(tmp_path)
    with pytest.raises(ValueError):
        store.initialize(store.initialization_intent())
    assert inventory(tmp_path) == before


def test_multiple_link_owner_rejected_before_read(tmp_path):
    store, initial = setup(tmp_path)
    import os
    outside = tmp_path.parent / (tmp_path.name + "-owner-link")
    try:
        os.link(tmp_path / "owner.json", outside)
        with pytest.raises(ValueError, match="single-link"):
            store.read(initial.sha256)
    finally:
        if outside.exists():
            outside.unlink()


@pytest.mark.parametrize("action", ["read", "resume"])
def test_hardlinked_empty_journal_lock_rejected_before_alias_mutation(tmp_path, action):
    store, initial = setup(tmp_path)
    intent = store.prepare(initial.sha256, reserve(initial), ROOT)
    receipt = store.commit(intent)
    lock = tmp_path / "journal.jsonl.lock"
    lock.write_bytes(b"")
    import os
    alias = tmp_path.parent / (tmp_path.name + "-lock-link")
    try:
        os.link(lock, alias)
        before = inventory(tmp_path)
        with pytest.raises(ValueError, match="single-link"):
            store.read(receipt.sha256) if action == "read" else store.resume(intent)
        assert inventory(tmp_path) == before
        assert lock.read_bytes() == alias.read_bytes() == b""
    finally:
        if alias.exists():
            alias.unlink()


def test_projected_capacity_checks_preserve_predecessor(tmp_path):
    store, initial = setup(tmp_path)
    intent = store.prepare(initial.sha256, reserve(initial), ROOT)
    before = inventory(tmp_path)
    # Exact virtual planner boundary values, not fake observed disk usage.
    for generation, retained_bytes in ((65536, 0), (0, 128 * 1024 * 1024 - len(intent.data) + 1)):
        with pytest.raises(ValueError, match="projected"):
            store._project(intent, generation, retained_bytes)
    store._project(intent, 65535, 128 * 1024 * 1024 - len(intent.data))
    assert inventory(tmp_path) == before


@pytest.mark.parametrize("target,limit", [("owner.json", 4096), ("intents/initialization.json", 16384)])
def test_oversized_records_rejected_before_parse_or_repair(tmp_path, target, limit):
    store, initial = setup(tmp_path)
    (tmp_path / target).write_bytes(b"x" * (limit + 1))
    before = inventory(tmp_path)
    with pytest.raises(ValueError):
        store.read(initial.sha256)
    assert inventory(tmp_path) == before


def test_multi_generation_retained_chain_tamper_and_global_aggregate(tmp_path):
    (tmp_path / "intents").mkdir()
    second = parse_canonical_json(declarations()[0])
    second["reservation_id"] = "r2"
    second["run_id"] = "alc-r0-v1-pilot-second-s20260916"
    specs = declarations() + (canonical_json_bytes(second),)
    store = ReservationStore(tmp_path, specs)
    initial = store.initialize(store.initialization_intent())
    first = store.commit(store.prepare(initial.sha256, reserve(initial), ROOT))
    value = parse_canonical_json(reserve(first))
    value["reservation_id"] = "r2"
    next_intent = store.prepare(first.sha256, canonical_json_bytes(value), OTHER)
    final = store.commit(next_intent)
    fresh = ReservationStore(tmp_path, specs)
    assert fresh.read(final.sha256) == final
    assert final.snapshot.event_count == 2
    assert final.snapshot.outstanding_gpu_ns == 20000000200
    path = tmp_path / "intents" / "intent-000001.json"
    corrupted = parse_canonical_json(path.read_bytes())
    corrupted["review_root"] = OTHER
    path.write_bytes(canonical_json_bytes(corrupted))
    before = inventory(tmp_path)
    with pytest.raises(ValueError, match="retained intent chain"):
        fresh.read(final.sha256)
    with pytest.raises(ValueError):
        fresh.resume(next_intent)
    assert inventory(tmp_path) == before


def test_symlink_owner_rejected_where_host_allows_fixture(tmp_path):
    store, initial = setup(tmp_path)
    alias = tmp_path.parent / (tmp_path.name + "-symlink-target")
    alias.write_bytes(initial.data)
    owner = tmp_path / "owner.json"
    owner.unlink()
    try:
        try:
            owner.symlink_to(alias)
        except OSError:
            pytest.skip("host does not permit temporary symlink fixture")
        with pytest.raises(UnsafePathError):
            store.read(initial.sha256)
        assert alias.read_bytes() == initial.data
    finally:
        if owner.is_symlink():
            owner.unlink()
        alias.unlink()


def worker_command(root, declaration_path, intent_path, output_path, mode):
    import sys
    from pathlib import Path
    return [sys.executable, str(Path(__file__).with_name("alc_r0_reservation_store_worker.py")),
        mode, str(root), str(declaration_path), str(intent_path), str(output_path)]


def run_worker(command):
    import subprocess
    process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    try:
        out, err = process.communicate(timeout=10)
        return process.returncode, out, err
    finally:
        if process.poll() is None:
            process.kill()
        process.wait(timeout=5)


@pytest.mark.parametrize("boundary", ["intent", "journal", "owner"])
def test_actual_process_exit_and_fresh_process_recovery(tmp_path, boundary):
    root = tmp_path / "store"
    root.mkdir()
    store, initial = setup(root)
    intent = store.prepare(initial.sha256, reserve(initial), ROOT)
    declaration_path, intent_path, output_path = (tmp_path / name for name in ("declaration.json", "intent.json", "receipt.json"))
    declaration_path.write_bytes(declarations()[0])
    intent_path.write_bytes(intent.data)
    code, out, err = run_worker(worker_command(root, declaration_path, intent_path, output_path, boundary))
    assert code == 73, (code, out, err)
    assert out == err == b""
    code, out, err = run_worker(worker_command(root, declaration_path, intent_path, output_path, "recover"))
    assert code == 0, (code, out, err)
    receipt = parse_canonical_json(output_path.read_bytes())
    assert receipt["events"] == 1
    assert receipt["outstanding_gpu_ns"] == "10000000100"
    assert receipt["state"] == "RESERVED"
    recovered = store.read(receipt["owner_root"])
    assert recovered.snapshot.event_count == 1
    assert recovered.snapshot.outstanding_gpu_ns == 10000000100


def test_actual_two_process_coordinators_same_head(tmp_path):
    import subprocess
    root = tmp_path / "store"
    root.mkdir()
    store, initial = setup(root)
    declaration_path = tmp_path / "declaration.json"
    declaration_path.write_bytes(declarations()[0])
    processes, outputs = [], []
    try:
        for index, review in enumerate((ROOT, OTHER)):
            intent = store.prepare(initial.sha256, reserve(initial), review)
            intent_path = tmp_path / f"intent-{index}.json"
            output_path = tmp_path / f"receipt-{index}.json"
            intent_path.write_bytes(intent.data)
            outputs.append(output_path)
        # Both intents are prepared before either competitor is launched.
        for index in range(2):
            command = worker_command(root, declaration_path, tmp_path / f"intent-{index}.json", outputs[index], "compete")
            processes.append(subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE))
        statuses = []
        for process in processes:
            out, err = process.communicate(timeout=10)
            assert out == err == b""
            statuses.append(process.returncode)
        assert sorted(statuses) == [0, 74]
        receipt = parse_canonical_json(outputs[statuses.index(0)].read_bytes())
        assert store.read(receipt["owner_root"]).snapshot.event_count == 1
    finally:
        for process in processes:
            if process.poll() is None:
                process.kill()
            process.wait(timeout=5)
