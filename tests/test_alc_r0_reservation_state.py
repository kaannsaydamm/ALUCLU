"""Synthetic reservation contracts; no processes, runtime, model or launch."""

import pytest

from aluclu.alc_r0.canonical import canonical_json_bytes
from aluclu.alc_r0.reservation_state import ReservationReplay, ReservationStateError, replay_reservations

ROOT = "a" * 64
OTHER = "b" * 64


def declaration(**changes):
    value = dict(experiment_id="alc-r0-smollm2-135m-v1", reservation_id="r1",
        run_id="alc-r0-v1-pilot-fixture-s20260916", attempt_id="a001", segment="initial",
        declaration_root=ROOT, device="gpu", useful_wall_ceiling_ns="100",
        cleanup_ceiling_ns="10000000000", charge_envelope_ns="10000000100",
        gpu_reservation_ns="10000000100", research_growth_bytes="50",
        physical_growth_bytes="100", stdout_limit_bytes="20", stderr_limit_bytes="20")
    value.update(changes)
    return canonical_json_bytes(value)


def append(replay, kind, **fields):
    value = dict(sequence=str(replay.snapshot().event_count + 1),
        previous_root=replay.snapshot().root, reservation_id="r1", kind=kind, evidence_root=ROOT)
    value.update(fields)
    replay.append(canonical_json_bytes(value))


def reserve(replay):
    append(replay, "reserve", declaration_root=ROOT, entry_utc_ns="9223372036854775807",
        clock_domain_root=ROOT, entry_monotonic_ns="9007199254740993",
        useful_deadline_monotonic_ns="9007199254741093")


def created(replay):
    append(replay, "child_created", pid="4294967295", creation_filetime_100ns="18446744073709551615",
        owner_nonce="c" * 32, identity_receipt_root=ROOT)


def terminal(replay, no_child=False):
    append(replay, "terminal", fact_kind="verified_no_child" if no_child else "verified_owned_tree_terminal",
        identity_receipt_root=None if no_child else ROOT, exit_code=None if no_child else "4294967295",
        terminal_fact_root=ROOT)


def reconcile(replay, **changes):
    fields = dict(resource_charge_root=ROOT, wall_kind="allocation_upper_bound", effective_wall_ns="100",
        effective_gpu_ns="100", growth_observation_root=ROOT, materialized_research_bytes="20",
        materialized_physical_bytes="30")
    fields.update(changes)
    append(replay, "reconcile", **fields)


def test_reservation_replay_requires_explicit_complete_declarations():
    with pytest.raises(ReservationStateError):
        ReservationReplay(())


def test_owned_lifecycle_preserves_large_identity_and_transfers_charge_once():
    replay = ReservationReplay((declaration(),))
    original = replay.snapshot()
    reserve(replay)
    created(replay)
    append(replay, "identity_published", identity_receipt_root=ROOT, publication_root=OTHER)
    append(replay, "running", resume_receipt_root=ROOT)
    terminal(replay)
    reconcile(replay)
    held = replay.snapshot(ROOT)
    assert held.outstanding_gpu_ns == 10000000100
    assert held.consumed_gpu_ns == 0
    assert (held.pending_research_bytes, held.pending_physical_bytes) == (30, 70)
    append(replay, "release", global_publication_root=ROOT)
    final = replay.snapshot()
    assert (final.outstanding_gpu_ns, final.consumed_gpu_ns) == (0, 100)
    assert (final.pending_research_bytes, final.pending_physical_bytes) == (0, 0)
    assert final.reservations[0].creation_filetime_100ns == (1 << 64) - 1
    assert final.reservations[0].exit_code == (1 << 32) - 1
    assert original.reservations[0].state == "ABSENT"
    assert replay_reservations((declaration(),), replay.events, final.root) == final


def test_no_child_unknown_charge_can_complete_later_without_forgiveness():
    replay = ReservationReplay((declaration(),))
    reserve(replay)
    append(replay, "uncertain", reason="creation", prior_state="RESERVED")
    terminal(replay, no_child=True)
    before = replay.snapshot()
    with pytest.raises(ReservationStateError):
        reconcile(replay, effective_gpu_ns=None)
    assert replay.snapshot() == before
    reconcile(replay)
    append(replay, "release", global_publication_root=ROOT)
    assert replay.snapshot().consumed_gpu_ns == 100


def test_known_identity_survives_uncertainty_and_blocks_no_child():
    replay = ReservationReplay((declaration(),))
    reserve(replay)
    created(replay)
    append(replay, "uncertain", reason="reboot", prior_state="CREATED")
    before = replay.snapshot()
    with pytest.raises(ReservationStateError):
        terminal(replay, no_child=True)
    assert replay.snapshot() == before
    assert before.reservations[0].pid == (1 << 32) - 1
    terminal(replay)


@pytest.mark.parametrize("reason", ["publication", "resume", "timeout", "reboot", "terminal"])
def test_noncreation_uncertainty_cannot_become_no_child(reason):
    replay = ReservationReplay((declaration(),))
    reserve(replay)
    append(replay, "uncertain", reason=reason, prior_state="RESERVED")
    before = replay.snapshot()
    assert before.reservations[0].uncertainty_reason == reason
    with pytest.raises(ReservationStateError):
        terminal(replay, no_child=True)
    assert replay.snapshot() == before


@pytest.mark.parametrize("value", [True, 1, 1.0, "01", "+1", "-1", "1e3", " 1", "1 ", "", "9" * 21, "9223372036854775808"])
def test_noncanonical_numeric_declarations_rejected(value):
    with pytest.raises(ReservationStateError):
        ReservationReplay((declaration(research_growth_bytes=value),))


@pytest.mark.parametrize("changes", [dict(extra="field"), dict(previous_root=OTHER), dict(sequence="2"),
    dict(reservation_id="missing"), dict(declaration_root=OTHER), dict(useful_deadline_monotonic_ns="1"),
    dict(clock_domain_root="not-a-root"), dict(entry_utc_ns=True)])
def test_reserve_rejection_is_atomic(changes):
    replay = ReservationReplay((declaration(),))
    before = replay.snapshot()
    fields = dict(declaration_root=ROOT, entry_utc_ns="1", clock_domain_root=ROOT,
        entry_monotonic_ns="1", useful_deadline_monotonic_ns="101")
    fields.update(changes)
    with pytest.raises(ReservationStateError):
        append(replay, "reserve", **fields)
    assert replay.snapshot() == before
    assert replay.events == ()
    reserve(replay)


def test_identity_mismatch_duplicate_event_and_truncated_history_rejected():
    replay = ReservationReplay((declaration(),))
    reserve(replay)
    created(replay)
    before = replay.snapshot()
    for fields in (dict(identity_receipt_root=OTHER, publication_root=ROOT),):
        with pytest.raises(ReservationStateError):
            append(replay, "identity_published", **fields)
    with pytest.raises(ReservationStateError):
        replay.append(replay.events[-1])
    assert replay.snapshot() == before
    with pytest.raises(ReservationStateError):
        replay_reservations((declaration(),), replay.events[:-1], before.root)
    with pytest.raises(ReservationStateError):
        replay_reservations((declaration(),), replay.events[1:], before.root)


def test_overrun_retained_not_clamped():
    replay = ReservationReplay((declaration(),))
    reserve(replay)
    terminal(replay, no_child=True)
    reconcile(replay, effective_wall_ns="10000000101", effective_gpu_ns="10000000101")
    assert replay.snapshot().overrun
    append(replay, "release", global_publication_root=ROOT)
    assert replay.snapshot().consumed_gpu_ns == 10000000101


@pytest.mark.parametrize("kind,fields", [("running", dict(resume_receipt_root=ROOT)),
    ("release", dict(global_publication_root=ROOT)), ("uncertain", dict(reason="bad", prior_state="ABSENT"))])
def test_illegal_predecessors_rejected(kind, fields):
    replay = ReservationReplay((declaration(),))
    before = replay.snapshot()
    with pytest.raises(ReservationStateError):
        append(replay, kind, **fields)
    assert replay.snapshot() == before


def test_bad_materialization_and_repeated_uncertainty_hold_reservation():
    replay = ReservationReplay((declaration(),))
    reserve(replay)
    append(replay, "uncertain", reason="creation", prior_state="RESERVED")
    before = replay.snapshot()
    with pytest.raises(ReservationStateError):
        append(replay, "uncertain", reason="reboot", prior_state="UNCERTAIN")
    assert replay.snapshot() == before
    terminal(replay, no_child=True)
    before = replay.snapshot()
    with pytest.raises(ReservationStateError):
        reconcile(replay, materialized_research_bytes="51")
    assert replay.snapshot() == before


def test_record_bomb_and_duplicate_declarations_rejected():
    with pytest.raises(ReservationStateError):
        ReservationReplay((declaration(), declaration()))
    replay = ReservationReplay((declaration(),))
    before = replay.snapshot()
    with pytest.raises(ReservationStateError):
        replay.append(b" " * 16385)
    assert replay.snapshot() == before


def test_aggregate_overflow_is_atomic():
    second = declaration(reservation_id="r2", run_id="alc-r0-v1-pilot-second-s20260916",
        gpu_reservation_ns=str((1 << 63) - 1))
    replay = ReservationReplay((declaration(), second))
    reserve(replay)
    before = replay.snapshot()
    with pytest.raises(ReservationStateError):
        append(replay, "reserve", reservation_id="r2", declaration_root=ROOT, entry_utc_ns="1",
            clock_domain_root=ROOT, entry_monotonic_ns="1", useful_deadline_monotonic_ns="101")
    assert replay.snapshot() == before


def test_materialization_requires_matching_observation_not_combined_roots():
    specs = (declaration(), declaration(reservation_id="r2", run_id="alc-r0-v1-pilot-second-s20260916"))
    replay = ReservationReplay(specs)
    reserve(replay)
    terminal(replay, no_child=True)
    reconcile(replay)
    append(replay, "reserve", reservation_id="r2", declaration_root=ROOT, entry_utc_ns="1",
        clock_domain_root=ROOT, entry_monotonic_ns="1", useful_deadline_monotonic_ns="101")
    append(replay, "terminal", reservation_id="r2", fact_kind="verified_no_child",
        identity_receipt_root=None, exit_code=None, terminal_fact_root=ROOT)
    reconcile(replay, reservation_id="r2", growth_observation_root=OTHER)
    assert replay.snapshot().pending_research_bytes == 100
    assert replay.snapshot(ROOT).pending_research_bytes == 80
    assert replay.snapshot(OTHER).pending_research_bytes == 80
    assert replay.snapshot("d" * 64).pending_research_bytes == 100


def test_lifetime_byte_and_event_batch_caps_checked_before_decode():
    with pytest.raises(ReservationStateError, match="declarations"):
        ReservationReplay((declaration(),) * 4097)
    with pytest.raises(ReservationStateError, match="byte cap"):
        ReservationReplay((b"x" * 16384,) * 257)
    with pytest.raises(ReservationStateError, match="bounded history"):
        replay_reservations((declaration(),), (b"x",) * 262145, ROOT)
    with pytest.raises(ReservationStateError, match="byte cap"):
        replay_reservations((declaration(),), (b"x" * 16384,) * 2049, ROOT)


def test_cpu_charge_and_resume_gating_and_released_event_rejection():
    specs = (declaration(device="cpu", gpu_reservation_ns="0"),
        declaration(reservation_id="r2", segment="resume", device="cpu", gpu_reservation_ns="0"))
    replay = ReservationReplay(specs)
    fields = dict(reservation_id="r2", declaration_root=ROOT, entry_utc_ns="1",
        clock_domain_root=ROOT, entry_monotonic_ns="1", useful_deadline_monotonic_ns="101")
    with pytest.raises(ReservationStateError, match="released initial"):
        append(replay, "reserve", **fields)
    reserve(replay)
    with pytest.raises(ReservationStateError, match="overlapping"):
        append(replay, "reserve", **fields)
    terminal(replay, no_child=True)
    with pytest.raises(ReservationStateError):
        reconcile(replay)
    reconcile(replay, effective_gpu_ns="0")
    append(replay, "release", global_publication_root=ROOT)
    with pytest.raises(ReservationStateError):
        reserve(replay)
    append(replay, "reserve", **fields)
    assert replay.snapshot().outstanding_gpu_ns == 0
    assert replay.snapshot().consumed_gpu_ns == 0


def test_nonce_reuse_across_reservations_rejected_atomically():
    replay = ReservationReplay((declaration(), declaration(reservation_id="r2",
        run_id="alc-r0-v1-pilot-second-s20260916")))
    reserve(replay)
    created(replay)
    append(replay, "reserve", reservation_id="r2", declaration_root=ROOT, entry_utc_ns="1",
        clock_domain_root=ROOT, entry_monotonic_ns="1", useful_deadline_monotonic_ns="101")
    before = replay.snapshot()
    with pytest.raises(ReservationStateError, match="unique owner nonce"):
        append(replay, "child_created", reservation_id="r2", pid="1", creation_filetime_100ns="1",
            owner_nonce="c" * 32, identity_receipt_root=ROOT)
    assert replay.snapshot() == before


def test_live_reservation_boundary_retains_complete_history():
    specs = tuple(declaration(reservation_id=f"r{i:03}",
        run_id=f"alc-r0-v1-pilot-fixture-{i}-s20260916") for i in range(513))
    replay = ReservationReplay(specs)
    for i in range(512):
        append(replay, "reserve", reservation_id=f"r{i:03}", declaration_root=ROOT,
            entry_utc_ns="1", clock_domain_root=ROOT, entry_monotonic_ns="1",
            useful_deadline_monotonic_ns="101")
    before = replay.snapshot()
    with pytest.raises(ReservationStateError, match="live reservation cap"):
        append(replay, "reserve", reservation_id="r512", declaration_root=ROOT,
            entry_utc_ns="1", clock_domain_root=ROOT, entry_monotonic_ns="1",
            useful_deadline_monotonic_ns="101")
    assert replay.snapshot() == before


@pytest.mark.parametrize("data", [b"{", b"{}", b"[]", b'{"kind":"reserve","kind":"reserve"}', b"\xff"])
def test_malformed_canonical_events_rejected_without_mutation(data):
    replay = ReservationReplay((declaration(),))
    before = replay.snapshot()
    with pytest.raises(ReservationStateError):
        replay.append(data)
    assert replay.snapshot() == before
