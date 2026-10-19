"""Synthetic D resource IDs, not scientific runs or host/process evidence."""

import pytest

from aluclu.alc_r0.attempt_state import AttemptReplay, AttemptStateError, RunSpec
from aluclu.alc_r0.canonical import canonical_json_bytes, sha256_bytes
from aluclu.alc_r0.reservation_state import (
    ReservationReplay, ReservationStateError, replay_reservations,
)
from aluclu.alc_r0.reservation_store import ReservationStore, ReservationStoreError

ROOT = "a" * 64
IDS = (
    "alc-r0-qualification-v1-d-cpu-fresh1-s20260916",
    "alc-r0-qualification-v1-d-gpu-fresh1-s20260916",
    "alc-r0-qualification-v1-d-gpu-fresh2-s20260916",
)
USEFUL, ENVELOPE = 2_700_000_000_000, 2_710_000_000_000


def declaration(run_id, **changes):
    device = "cpu" if run_id == IDS[0] else "gpu"
    item = dict(experiment_id="alc-r0-smollm2-135m-v1", reservation_id="d1",
        run_id=run_id, attempt_id="a001", segment="initial", declaration_root=ROOT,
        device=device, useful_wall_ceiling_ns=str(USEFUL),
        cleanup_ceiling_ns="10000000000", charge_envelope_ns=str(ENVELOPE),
        gpu_reservation_ns="0" if device == "cpu" else str(ENVELOPE),
        research_growth_bytes="50", physical_growth_bytes="100",
        stdout_limit_bytes="20", stderr_limit_bytes="20")
    item.update(changes)
    return canonical_json_bytes(item)


def event(snapshot, kind, **fields):
    return canonical_json_bytes(dict(sequence=str(snapshot.event_count + 1),
        previous_root=snapshot.root, reservation_id="d1", kind=kind,
        evidence_root=ROOT, **fields))


def reserve(snapshot):
    return event(snapshot, "reserve", declaration_root=ROOT, entry_utc_ns="1",
        clock_domain_root=ROOT, entry_monotonic_ns="1",
        useful_deadline_monotonic_ns=str(1 + USEFUL))


@pytest.mark.parametrize("run_id", IDS)
def test_exact_d_resource_identity_is_accepted_without_execution(run_id):
    data = declaration(run_id)
    replay = ReservationReplay((data,))
    view = replay.snapshot()
    assert view.reservations[0].declaration == data
    assert view.reservations[0].state == "ABSENT"
    assert view.event_count == 0 and replay.events == ()
    assert view.outstanding_gpu_ns == view.consumed_gpu_ns == 0


@pytest.mark.parametrize("run_id", IDS)
def test_resource_identity_is_not_a_scientific_run_spec(run_id):
    with pytest.raises(AttemptStateError):
        AttemptReplay((RunSpec(run_id, True, ("fixture",)),))


@pytest.mark.parametrize("run_id", [
    IDS[0].replace("fresh1", "fresh2"), IDS[1].replace("fresh1", "fresh0"),
    IDS[1].replace("fresh1", "fresh3"), IDS[1].replace("fresh1", "fresh01"),
    IDS[1].replace("d-gpu", "qv-gpu"), IDS[1].replace("d-gpu", "e1-gpu"),
    IDS[1].replace("d-gpu", "pilot-gpu"), IDS[1].replace("gpu", "cuda0"),
    IDS[1].replace("20260916", "20260917"), IDS[1].replace("v1", "v2"),
    IDS[1].upper(), IDS[1] + "-extra", " " + IDS[1], IDS[1] + "\n",
    None, True, 1, [], {}, "alc-r0-v1-qualification-d-s20260916",
])
def test_closed_namespace_rejects_drift_and_malformed_types(run_id):
    with pytest.raises(ReservationStateError):
        ReservationReplay((declaration(run_id),))


@pytest.mark.parametrize("run_id", IDS)
@pytest.mark.parametrize("changes", [
    {"useful_wall_ceiling_ns": str(USEFUL - 1)},
    {"useful_wall_ceiling_ns": str(USEFUL + 1)},
    {"cleanup_ceiling_ns": "9999999999"},
    {"charge_envelope_ns": str(ENVELOPE - 1)},
    {"charge_envelope_ns": str(ENVELOPE + 1)},
    {"gpu_reservation_ns": "1"},
    {"gpu_reservation_ns": str(ENVELOPE + 1)},
    {"useful_wall_ceiling_ns": True},
    {"useful_wall_ceiling_ns": USEFUL},
])
def test_fixed_d_envelope_cannot_be_shortened_enlarged_or_mistyped(run_id, changes):
    with pytest.raises(ReservationStateError):
        ReservationReplay((declaration(run_id, **changes),))


@pytest.mark.parametrize("run_id", IDS)
def test_identity_device_binding_cannot_be_swapped(run_id):
    device = "gpu" if run_id == IDS[0] else "cpu"
    with pytest.raises(ReservationStateError):
        ReservationReplay((declaration(run_id, device=device,
            gpu_reservation_ns=str(ENVELOPE) if device == "gpu" else "0"),))


@pytest.mark.parametrize("phase", ["pilot", "dev", "confirm", "eval"])
def test_legacy_scientific_resource_semantics_and_genesis_are_unchanged(phase):
    run_id = f"alc-r0-v1-{phase}-fixture-s20260916"
    data = declaration(run_id, useful_wall_ceiling_ns="100",
        charge_envelope_ns="10000000100", gpu_reservation_ns="10000000101")
    replay = ReservationReplay((data,))
    from aluclu.alc_r0.canonical import parse_canonical_json
    expected = sha256_bytes(canonical_json_bytes(dict(schema="alc-r0-reservations-v1",
        declarations=[parse_canonical_json(data)])))
    assert replay.snapshot().root == expected
    assert replay.snapshot().reservations[0].declaration == data
    AttemptReplay((RunSpec(run_id, True, ("fixture",)),))


@pytest.mark.parametrize("run_id", IDS)
def test_synthetic_no_child_lifecycle_transfers_charge_once_and_pins_complete_history(run_id):
    declarations = (declaration(run_id),)
    replay = ReservationReplay(declarations)
    replay.append(reserve(replay.snapshot()))
    gpu = 0 if run_id == IDS[0] else ENVELOPE
    assert replay.snapshot().outstanding_gpu_ns == gpu
    replay.append(event(replay.snapshot(), "terminal", fact_kind="verified_no_child",
        identity_receipt_root=None, exit_code=None, terminal_fact_root=ROOT))
    replay.append(event(replay.snapshot(), "reconcile", resource_charge_root=ROOT,
        wall_kind="allocation_upper_bound", effective_wall_ns="123",
        effective_gpu_ns="0" if run_id == IDS[0] else "123",
        growth_observation_root=ROOT, materialized_research_bytes="0",
        materialized_physical_bytes="0"))
    assert replay.snapshot().outstanding_gpu_ns == gpu
    assert replay.snapshot().consumed_gpu_ns == 0
    replay.append(event(replay.snapshot(), "release", global_publication_root=ROOT))
    final = replay.snapshot()
    assert final.reservations[0].state == "RELEASED"
    assert final.outstanding_gpu_ns == 0
    assert final.consumed_gpu_ns == (0 if run_id == IDS[0] else 123)
    assert replay_reservations(declarations, replay.events, final.root) == final
    with pytest.raises(ReservationStateError):
        replay_reservations(declarations, replay.events[:-1], final.root)


@pytest.mark.parametrize("run_id", IDS)
def test_temporary_store_roundtrip_cannot_rewrite_a_historical_genesis(tmp_path, run_id):
    (tmp_path / "intents").mkdir()
    declarations = (declaration(run_id),)
    store = ReservationStore(tmp_path, declarations)
    initial = store.initialize(store.initialization_intent())
    reserved = store.commit(store.prepare(initial.sha256, reserve(initial.snapshot), ROOT))
    assert ReservationStore(tmp_path, declarations).read(reserved.sha256) == reserved
    before = {str(p.relative_to(tmp_path)): p.read_bytes()
              for p in tmp_path.rglob("*") if p.is_file()}
    altered = (declaration(run_id, declaration_root="b" * 64),)
    replacement = ReservationStore(tmp_path, altered)
    with pytest.raises(ReservationStoreError):
        replacement.read(reserved.sha256)
    with pytest.raises(ReservationStoreError):
        replacement.initialize(replacement.initialization_intent())
    assert {str(p.relative_to(tmp_path)): p.read_bytes()
            for p in tmp_path.rglob("*") if p.is_file()} == before
