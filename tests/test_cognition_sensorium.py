from __future__ import annotations

import hashlib
import json
import struct
from dataclasses import FrozenInstanceError, fields, replace
from pathlib import Path

import pytest

import aluclu.cognition as cognition
from aluclu.cognition import (
    CanonicalJsonValue,
    EncryptedLedger,
    InputBoundaryError,
    LedgerCursorCheckpoint,
    ObservationRequestV1,
    ProvenanceV1,
    SensoriumCoreStateV1,
    SourceKind,
    StaticKeyProvider,
    build_canonical_observation,
    canonical_observation_to_json_value,
    derive_sensorium_core_state_digest,
)
from aluclu.cognition.sensorium import (
    BoundaryProfileV1,
    IngestRejectionCode,
    IngestStatus,
    ObservationAcceptedV1,
    ObservationRejectedV1,
    ReceiptClass,
    SensoriumBootstrapReplayRequiredV1,
    SensoriumStateV1,
    baseline_boundary_profile,
    bootstrap_replay_to_json_value,
    canonicalize_observation,
    classify_observation_receipt,
    decode_sensorium_state,
    encode_sensorium_state,
    ingest_observation,
    initialize_empty_sensorium_state,
    observation_accepted_to_json_value,
    observation_receipt_to_json_value,
    observation_rejected_to_json_value,
)

MASTER_KEY = b"m" * 32
MAX_I63 = (1 << 63) - 1


def _request(**overrides: object) -> ObservationRequestV1:
    values: dict[str, object] = {
        "observation_id": "obs:task2-0001",
        "session_id": "session:task2",
        "turn_id": "turn:0001",
        "provenance": ProvenanceV1(
            source_kind=SourceKind.USER,
            source_instance_id="user:local",
            origin_id="fixture:task2-2",
            observed_at_ns=1_725_000_000_000_000_000,
            parent_observation_ids=(),
            capture_method="test",
            capture_version="1.0.0",
        ),
        "content": CanonicalJsonValue.from_value({"text": "remember this"}),
        "retrieval_text": "remember this",
        "topic_key": "topic:test",
        "goal_ids": ("goal:test",),
        "participant_ids": ("participant:user",),
        "tool_invocation_id": None,
        "tool_phase": None,
        "force_boundary": False,
    }
    values.update(overrides)
    return ObservationRequestV1(**values)  # type: ignore[arg-type]


def _profile_identity(profile: BoundaryProfileV1) -> str:
    value = {
        "schema": "aluclu.boundary-profile.v1",
        "name": profile.name,
        "max_inter_observation_gap_ns": profile.max_inter_observation_gap_ns,
        "max_observations": profile.max_observations,
        "max_canonical_request_bytes": profile.max_canonical_request_bytes,
        "max_goal_ids": profile.max_goal_ids,
        "max_participant_ids": profile.max_participant_ids,
    }
    payload = json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    domain = b"aluclu.task2.boundary-profile.v1"
    framed = (
        struct.pack(">Q", len(domain))
        + domain
        + struct.pack(">Q", len(payload))
        + payload
    )
    return "boundary-profile:" + hashlib.sha256(framed).hexdigest()


def _ledger(path: Path) -> EncryptedLedger:
    return EncryptedLedger(path, StaticKeyProvider(MASTER_KEY))


def _tail_checkpoint(session: object) -> LedgerCursorCheckpoint:
    cursor = session.cursor(after_sequence=MAX_I63, batch_size=1)  # type: ignore[attr-defined]
    return cursor.suspend()


def test_baseline_profile_is_frozen_content_addressed_and_exact() -> None:
    profile = baseline_boundary_profile()

    assert profile == BoundaryProfileV1(
        name="task2-baseline-v1",
        max_inter_observation_gap_ns=1_800_000_000_000,
        max_observations=64,
        max_canonical_request_bytes=8 * 1024 * 1024,
        max_goal_ids=32,
        max_participant_ids=32,
    )
    assert profile.profile_id == _profile_identity(profile)
    assert not hasattr(profile, "__dict__")
    with pytest.raises(FrozenInstanceError):
        profile.name = "changed"  # type: ignore[misc]
    with pytest.raises((InputBoundaryError, TypeError)):
        BoundaryProfileV1(
            name="bad profile",
            max_inter_observation_gap_ns=1,
            max_observations=True,  # type: ignore[arg-type]
            max_canonical_request_bytes=1,
            max_goal_ids=1,
            max_participant_ids=1,
        )


def test_task2_2_public_exports_are_additive() -> None:
    expected = {
        "BoundaryProfileV1",
        "EventIdRecallQuery",
        "ExactRecollection",
        "IngestRejectionCode",
        "IngestStatus",
        "NoRecollection",
        "ObservationAcceptedV1",
        "ObservationReceiptV1",
        "ObservationRejectedV1",
        "RecallBasis",
        "ReceiptClass",
        "SensoriumBootstrapReplayRequiredV1",
        "SensoriumStateV1",
        "baseline_boundary_profile",
        "classify_observation_receipt",
        "ingest_observation",
        "recall",
    }
    assert expected <= set(cognition.__all__)
    assert all(getattr(cognition, name) is not None for name in expected)


def test_empty_bootstrap_binds_real_tail_and_nonempty_requires_replay(
    tmp_path: Path,
) -> None:
    profile = baseline_boundary_profile()
    with _ledger(tmp_path / "memory.sqlite3") as ledger:
        with ledger.verified_session() as session:
            state = initialize_empty_sensorium_state(session, profile)
            assert type(state) is SensoriumStateV1
            assert state.core.boundary_profile_id == profile.profile_id
            assert state.last_applied_sequence == 0
            assert state.task1_checkpoint.ledger_id == ledger.ledger_id
            assert state.task1_checkpoint.snapshot_head_hash == "0" * 64
            assert state.task1_checkpoint.next_sequence == 1
            assert decode_sensorium_state(encode_sensorium_state(state)) == state
            assert len(encode_sensorium_state(state)) <= 4096

            session.append_once("unrelated:1", {"schema": "other.v1"})
            replay = initialize_empty_sensorium_state(session, profile)
            assert type(replay) is SensoriumBootstrapReplayRequiredV1
            assert replay.snapshot_head_sequence == 1
            assert replay.replay_from_sequence == 0
            assert set(bootstrap_replay_to_json_value(replay)) == {
                "schema",
                "snapshot_head_sequence",
                "snapshot_head_hash",
                "replay_from_sequence",
            }


def test_canonicalize_first_observation_is_pure_and_bounded(tmp_path: Path) -> None:
    profile = baseline_boundary_profile()
    request = _request()
    with _ledger(tmp_path / "memory.sqlite3") as ledger:
        with ledger.verified_session() as session:
            state = initialize_empty_sensorium_state(session, profile)
            assert type(state) is SensoriumStateV1
            before = (session.event_count(), _tail_checkpoint(session))
            canonical = canonicalize_observation(request, profile, state.core, 1)
            after = (session.event_count(), _tail_checkpoint(session))

    assert before == after
    assert canonical.request == request
    assert canonical.pre_core_state == state.core
    assert canonical.post_core_state.last_observation_sequence == 1
    assert canonical.boundary_decision.reasons[0].value == "first_observation"


def test_classification_is_storage_pure_for_new_nonobservation_and_tombstone(
    tmp_path: Path,
) -> None:
    request = _request()
    with _ledger(tmp_path / "memory.sqlite3") as ledger:
        with ledger.verified_session() as session:
            new_before = _tail_checkpoint(session)
            new = classify_observation_receipt(session, request)
            assert new.receipt_class is ReceiptClass.NEW
            assert tuple(field.name for field in fields(new)) == (
                "receipt_class",
                "observation_id",
                "incoming_request_digest",
                "existing_request_digest",
                "existing_sequence",
                "existing_record_hash",
            )
            assert (new.existing_sequence, new.existing_record_hash) == (None, None)
            assert _tail_checkpoint(session) == new_before

            other = session.append_once(request.observation_id, {"schema": "other.v1"})
            conflict_before = _tail_checkpoint(session)
            conflict = classify_observation_receipt(session, request)
            assert conflict.receipt_class is ReceiptClass.CONFLICT
            assert conflict.existing_request_digest is None
            assert conflict.existing_sequence == other.record.sequence
            assert conflict.existing_record_hash == other.record.record_hash
            assert _tail_checkpoint(session) == conflict_before

            assert session.shred(request.observation_id) is True
            tombstone_before = _tail_checkpoint(session)
            tombstoned = classify_observation_receipt(session, request)
            assert tombstoned.receipt_class is ReceiptClass.TOMBSTONED
            assert tombstoned.existing_sequence is None
            assert tombstoned.existing_record_hash is None
            assert tombstoned.existing_request_digest is None
            assert _tail_checkpoint(session) == tombstone_before


def test_new_ingest_appends_once_and_duplicate_retry_converges(tmp_path: Path) -> None:
    profile = baseline_boundary_profile()
    request = _request()
    with _ledger(tmp_path / "memory.sqlite3") as ledger:
        with ledger.verified_session() as session:
            state = initialize_empty_sensorium_state(session, profile)
            assert type(state) is SensoriumStateV1
            accepted = ingest_observation(session, request, profile, state)
            assert type(accepted) is ObservationAcceptedV1
            assert accepted.status is IngestStatus.APPLIED
            assert accepted.receipt.receipt_class is ReceiptClass.NEW
            assert session.event_count() == 1
            assert accepted.next_state.last_applied_sequence == 1
            accepted_wire = observation_accepted_to_json_value(accepted)
            assert set(accepted_wire) == {
                "schema",
                "status",
                "receipt",
                "stored_observation",
                "next_state",
            }
            assert accepted_wire["schema"] == "aluclu.observation-ingest-accepted.v1"
            receipt_wire = observation_receipt_to_json_value(accepted.receipt)
            assert set(receipt_wire) == {
                "schema",
                "receipt_class",
                "observation_id",
                "incoming_request_digest",
                "existing_request_digest",
                "existing_sequence",
                "existing_record_hash",
            }

            retry = ingest_observation(session, request, profile, state)
            assert type(retry) is ObservationAcceptedV1
            assert retry.status is IngestStatus.DUPLICATE
            assert retry.receipt.receipt_class is ReceiptClass.DUPLICATE
            assert retry.next_state == accepted.next_state
            assert retry.stored_observation == accepted.stored_observation
            assert session.event_count() == 1

            equal = ingest_observation(session, request, profile, accepted.next_state)
            assert type(equal) is ObservationAcceptedV1
            assert equal.status is IngestStatus.DUPLICATE
            assert equal.next_state == accepted.next_state
            assert session.event_count() == 1


def test_second_new_observation_advances_same_episode_and_remains_bounded(
    tmp_path: Path,
) -> None:
    profile = baseline_boundary_profile()
    first_request = _request()
    second_request = _request(
        observation_id="obs:task2-0002",
        turn_id="turn:0002",
        provenance=replace(
            first_request.provenance,
            observed_at_ns=first_request.provenance.observed_at_ns + 1,
        ),
        content=CanonicalJsonValue.from_value({"text": "remember this too"}),
        retrieval_text="remember this too",
    )
    with _ledger(tmp_path / "memory.sqlite3") as ledger:
        with ledger.verified_session() as session:
            initial = initialize_empty_sensorium_state(session, profile)
            assert type(initial) is SensoriumStateV1
            first = ingest_observation(session, first_request, profile, initial)
            assert type(first) is ObservationAcceptedV1
            second = ingest_observation(
                session, second_request, profile, first.next_state
            )

            assert type(second) is ObservationAcceptedV1
            assert second.status is IngestStatus.APPLIED
            assert second.next_state.last_applied_sequence == 2
            assert second.next_state.core.episode_observation_count == 2
            assert second.stored_observation.boundary_decision.reasons == (
                cognition.EpisodeBoundaryReason.CONTINUE,
            )
            assert (
                decode_sensorium_state(encode_sensorium_state(second.next_state))
                == second.next_state
            )
            assert len(encode_sensorium_state(second.next_state)) <= 4096
            assert session.event_count() == 2


def test_conflict_tombstone_and_state_mismatch_are_typed_no_write_rejections(
    tmp_path: Path,
) -> None:
    profile = baseline_boundary_profile()
    request = _request()
    with _ledger(tmp_path / "memory.sqlite3") as ledger:
        with ledger.verified_session() as session:
            state = initialize_empty_sensorium_state(session, profile)
            assert type(state) is SensoriumStateV1
            accepted = ingest_observation(session, request, profile, state)
            assert type(accepted) is ObservationAcceptedV1
            count = session.event_count()

            changed = replace(
                request,
                content=CanonicalJsonValue.from_value({"text": "different"}),
            )
            conflict = ingest_observation(
                session, changed, profile, accepted.next_state
            )
            assert type(conflict) is ObservationRejectedV1
            assert conflict.rejection_code is IngestRejectionCode.OBSERVATION_CONFLICT
            rejected_wire = observation_rejected_to_json_value(conflict)
            assert set(rejected_wire) == {
                "schema",
                "receipt",
                "rejection_code",
                "replay_from_sequence",
            }
            assert rejected_wire["schema"] == "aluclu.observation-ingest-rejected.v1"
            assert session.event_count() == count

            bad_core = replace(
                accepted.next_state.core,
                last_observed_at_ns=accepted.next_state.core.last_observed_at_ns + 1,  # type: ignore[operator]
            )
            bad_state = replace(accepted.next_state, core=bad_core)
            state_conflict = ingest_observation(session, request, profile, bad_state)
            assert type(state_conflict) is ObservationRejectedV1
            assert state_conflict.rejection_code is IngestRejectionCode.STATE_CONFLICT
            assert session.event_count() == count

            assert session.shred(request.observation_id) is True
            shredded_count = session.event_count()
            tombstoned = ingest_observation(
                session, request, profile, accepted.next_state
            )
            assert type(tombstoned) is ObservationRejectedV1
            assert (
                tombstoned.rejection_code is IngestRejectionCode.OBSERVATION_TOMBSTONED
            )
            assert session.event_count() == shredded_count


def test_duplicate_ahead_and_stale_branches_never_roll_state_backward(
    tmp_path: Path,
) -> None:
    profile = baseline_boundary_profile()
    request = _request()
    with _ledger(tmp_path / "memory.sqlite3") as ledger:
        with ledger.verified_session() as session:
            initial = initialize_empty_sensorium_state(session, profile)
            assert type(initial) is SensoriumStateV1
            accepted = ingest_observation(session, request, profile, initial)
            assert type(accepted) is ObservationAcceptedV1
            session.append_once("unrelated:after", {"schema": "other.v1"})
            ahead = replace(
                accepted.next_state,
                task1_checkpoint=_tail_checkpoint(session),
            )
            historical = ingest_observation(session, request, profile, ahead)
            assert type(historical) is ObservationAcceptedV1
            assert historical.status is IngestStatus.DUPLICATE
            assert historical.next_state == ahead

            stale = ingest_observation(session, request, profile, initial)
            assert type(stale) is ObservationRejectedV1
            assert stale.rejection_code is IngestRejectionCode.REPLAY_REQUIRED
            assert stale.replay_from_sequence == 0
            assert session.event_count() == 2


def test_exactly_behind_duplicate_with_wrong_pre_core_digest_fails_closed(
    tmp_path: Path,
) -> None:
    profile = baseline_boundary_profile()
    request = _request()
    with _ledger(tmp_path / "memory.sqlite3") as ledger:
        with ledger.verified_session() as session:
            initial = initialize_empty_sensorium_state(session, profile)
            assert type(initial) is SensoriumStateV1
            canonical = canonicalize_observation(request, profile, initial.core)
            forged = build_canonical_observation(
                request=request,
                boundary_decision=canonical.boundary_decision,
                pre_core_state_digest="f" * 64,
                post_core_state=canonical.post_core_state,
                pre_append_head_sequence=(
                    initial.task1_checkpoint.snapshot_head_sequence
                ),
                pre_append_head_hash=initial.task1_checkpoint.snapshot_head_hash,
                boundary_profile_id=profile.profile_id,
            )
            assert forged.pre_core_state_digest != derive_sensorium_core_state_digest(
                initial.core
            )
            session.append_once(
                request.observation_id,
                canonical_observation_to_json_value(forged),
            )

            rejected = ingest_observation(session, request, profile, initial)

            assert type(rejected) is ObservationRejectedV1
            assert rejected.rejection_code is IngestRejectionCode.STATE_CONFLICT
            assert session.event_count() == 1


def test_far_behind_duplicate_requires_replay_and_bare_ledger_is_rejected(
    tmp_path: Path,
) -> None:
    profile = baseline_boundary_profile()
    request = _request()
    with _ledger(tmp_path / "memory.sqlite3") as ledger:
        with ledger.verified_session() as session:
            initial = initialize_empty_sensorium_state(session, profile)
            assert type(initial) is SensoriumStateV1
            session.append_once("unrelated:1", {"schema": "other.v1"})
            session.append_once("unrelated:2", {"schema": "other.v1"})
            state_at_two = replace(initial, task1_checkpoint=_tail_checkpoint(session))
            accepted = ingest_observation(session, request, profile, state_at_two)
            assert type(accepted) is ObservationAcceptedV1
            assert accepted.next_state.last_applied_sequence == 3

            stale = ingest_observation(session, request, profile, initial)
            assert type(stale) is ObservationRejectedV1
            assert stale.rejection_code is IngestRejectionCode.REPLAY_REQUIRED
            assert session.event_count() == 3

        with pytest.raises(InputBoundaryError):
            ingest_observation(ledger, request, profile, initial)  # type: ignore[arg-type]


def test_sensorium_state_rejects_nonexhaustive_or_oversized_checkpoint() -> None:
    profile = baseline_boundary_profile()
    core = SensoriumCoreStateV1(
        boundary_profile_id=profile.profile_id,
        session_signal_digest=None,
        current_episode_id=None,
        episode_observation_count=0,
        episode_canonical_request_bytes=0,
        goal_ids_signal_digest=None,
        participant_ids_signal_digest=None,
        tool_signal_digest=None,
        topic_signal_digest=None,
        last_observation_id=None,
        last_observation_sequence=0,
        last_observed_at_ns=None,
    )
    with pytest.raises(InputBoundaryError):
        SensoriumStateV1(
            core=core,
            task1_checkpoint=LedgerCursorCheckpoint(
                ledger_id="ledger",
                snapshot_head_sequence=1,
                snapshot_head_hash="0" * 64,
                next_sequence=1,
            ),
        )


def test_new_ingest_rejects_forged_populated_core_at_current_head(
    tmp_path: Path,
) -> None:
    profile = baseline_boundary_profile()
    first_request = _request()
    second_request = _request(
        observation_id="obs:task2-0002",
        turn_id="turn:0002",
        provenance=replace(
            first_request.provenance,
            observed_at_ns=first_request.provenance.observed_at_ns + 1,
        ),
    )
    with _ledger(tmp_path / "memory.sqlite3") as ledger:
        with ledger.verified_session() as session:
            initial = initialize_empty_sensorium_state(session, profile)
            assert type(initial) is SensoriumStateV1
            first = ingest_observation(session, first_request, profile, initial)
            assert type(first) is ObservationAcceptedV1
            forged = replace(
                first.next_state,
                core=replace(
                    first.next_state.core,
                    last_observed_at_ns=first.next_state.core.last_observed_at_ns + 1,  # type: ignore[operator]
                ),
            )
            before = session.event_count()
            rejected = ingest_observation(session, second_request, profile, forged)

            assert type(rejected) is ObservationRejectedV1
            assert rejected.rejection_code is IngestRejectionCode.STATE_CONFLICT
            assert session.event_count() == before


def test_one_request_cannot_exceed_profile_episode_byte_limit(tmp_path: Path) -> None:
    profile = replace(baseline_boundary_profile(), max_canonical_request_bytes=1)
    request = _request()
    with _ledger(tmp_path / "memory.sqlite3") as ledger:
        with ledger.verified_session() as session:
            state = initialize_empty_sensorium_state(session, profile)
            assert type(state) is SensoriumStateV1
            with pytest.raises(InputBoundaryError):
                canonicalize_observation(request, profile, state.core)
            with pytest.raises(InputBoundaryError):
                ingest_observation(session, request, profile, state)
            assert session.event_count() == 0


def test_task2_apis_reuse_the_single_caller_owned_verified_session(
    tmp_path: Path,
) -> None:
    profile = baseline_boundary_profile()
    request = _request()
    with _ledger(tmp_path / "memory.sqlite3") as ledger:
        with ledger.verified_session() as session:
            stats = ledger.verification_stats
            state = initialize_empty_sensorium_state(session, profile)
            assert type(state) is SensoriumStateV1
            classify_observation_receipt(session, request)
            ingest_observation(session, request, profile, state)
            assert ledger.verification_stats == stats
