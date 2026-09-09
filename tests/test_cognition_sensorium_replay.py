from __future__ import annotations

import sqlite3
from dataclasses import FrozenInstanceError, fields, replace
from pathlib import Path

import pytest

import aluclu.cognition as cognition
from aluclu.cognition import (
    CanonicalJsonValue,
    EncryptedLedger,
    EpisodeBoundaryDecisionV1,
    EpisodeBoundaryReason,
    InputBoundaryError,
    LedgerIntegrityError,
    LedgerSnapshotChanged,
    ObservationRequestV1,
    ProvenanceV1,
    SourceKind,
    StaticKeyProvider,
    VerifiedLedgerSession,
    build_canonical_observation,
    canonical_observation_to_json_value,
    derive_sensorium_core_state_digest,
    encode_sensorium_state,
)
from aluclu.cognition.sensorium import (
    BoundaryProfileV1,
    ObservationAcceptedV1,
    SensoriumReplayCompleteV1,
    SensoriumReplayContinuationV1,
    SensoriumReplayIncompleteV1,
    SensoriumReplayPagePolicyV1,
    SensoriumReplayPageWorkV1,
    SensoriumStateV1,
    baseline_boundary_profile,
    canonicalize_observation,
    ingest_observation,
    initialize_empty_sensorium_state,
    replay_complete_from_json_value,
    replay_complete_to_json_value,
    replay_continuation_from_json_value,
    replay_continuation_to_json_value,
    replay_incomplete_from_json_value,
    replay_incomplete_to_json_value,
    replay_page_policy_from_json_value,
    replay_page_policy_to_json_value,
    replay_page_work_from_json_value,
    replay_page_work_to_json_value,
    replay_sensorium_page,
)

MASTER_KEY = b"m" * 32


def test_task2_3_public_exports_are_additive() -> None:
    expected = {
        "SENSORIUM_REPLAY_CONTINUATION_MAX_BYTES",
        "SENSORIUM_REPLAY_MAX_RECORDS",
        "SensoriumReplayCompleteV1",
        "SensoriumReplayContinuationV1",
        "SensoriumReplayIncompleteV1",
        "SensoriumReplayPagePolicyV1",
        "SensoriumReplayPageWorkV1",
        "replay_complete_to_json_value",
        "replay_complete_from_json_value",
        "replay_continuation_from_json_value",
        "replay_continuation_to_json_value",
        "replay_incomplete_from_json_value",
        "replay_incomplete_to_json_value",
        "replay_page_policy_from_json_value",
        "replay_page_policy_to_json_value",
        "replay_page_work_from_json_value",
        "replay_page_work_to_json_value",
        "replay_sensorium_page",
    }
    assert expected <= set(cognition.__all__)
    assert all(getattr(cognition, name) is not None for name in expected)


def _request() -> ObservationRequestV1:
    return ObservationRequestV1(
        observation_id="obs:t23-replay-0001",
        session_id="session:t23-replay",
        turn_id="turn:t23-replay-0001",
        provenance=ProvenanceV1(
            source_kind=SourceKind.USER,
            source_instance_id="user:local",
            origin_id="fixture:t23-replay",
            observed_at_ns=1_725_000_000_000_000_000,
            parent_observation_ids=(),
            capture_method="test",
            capture_version="1.0.0",
        ),
        content=CanonicalJsonValue.from_value({"text": "replay me"}),
        retrieval_text="replay me",
        topic_key="topic:replay",
        goal_ids=(),
        participant_ids=("participant:user",),
        tool_invocation_id=None,
        tool_phase=None,
        force_boundary=False,
    )


def _indexed_request(index: int) -> ObservationRequestV1:
    return ObservationRequestV1(
        observation_id=f"obs:t23-replay-{index:04d}",
        session_id="session:t23-replay",
        turn_id=f"turn:t23-replay-{index:04d}",
        provenance=ProvenanceV1(
            source_kind=SourceKind.USER,
            source_instance_id="user:local",
            origin_id=f"fixture:t23-replay-{index:04d}",
            observed_at_ns=1_725_000_000_000_000_000 + index,
            parent_observation_ids=(),
            capture_method="test",
            capture_version="1.0.0",
        ),
        content=CanonicalJsonValue.from_value({"index": index}),
        retrieval_text=f"replay observation {index}",
        topic_key="topic:replay",
        goal_ids=(),
        participant_ids=("participant:user",),
        tool_invocation_id=None,
        tool_phase=None,
        force_boundary=False,
    )


def _complete_replay(
    session: VerifiedLedgerSession,
    *,
    page_size: int,
) -> SensoriumReplayCompleteV1:
    start: BoundaryProfileV1 | SensoriumReplayContinuationV1 = (
        baseline_boundary_profile()
    )
    while True:
        result = replay_sensorium_page(
            session,
            SensoriumReplayPagePolicyV1(max_records=page_size),
            start,
        )
        if type(result) is SensoriumReplayCompleteV1:
            return result
        assert type(result) is SensoriumReplayIncompleteV1
        start = result.continuation


def test_zero_budget_is_typed_incomplete_then_resume_completes_exactly(
    tmp_path: Path,
) -> None:
    profile = baseline_boundary_profile()
    with EncryptedLedger(
        tmp_path / "memory.sqlite3", StaticKeyProvider(MASTER_KEY)
    ) as ledger:
        with ledger.verified_session() as session:
            initial = initialize_empty_sensorium_state(session, profile)
            assert type(initial) is SensoriumStateV1
            accepted = ingest_observation(session, _request(), profile, initial)
            assert type(accepted) is ObservationAcceptedV1

            incomplete = replay_sensorium_page(
                session,
                SensoriumReplayPagePolicyV1(max_records=0),
                profile,
            )
            assert type(incomplete) is SensoriumReplayIncompleteV1
            assert type(incomplete.continuation) is SensoriumReplayContinuationV1
            assert not isinstance(incomplete.continuation, SensoriumStateV1)
            assert incomplete.page_work == SensoriumReplayPageWorkV1(
                records_examined=0,
                observations_applied=0,
                canonical_payload_bytes_examined=0,
            )
            assert incomplete.continuation.task1_checkpoint.next_sequence == 1

            completed = replay_sensorium_page(
                session,
                SensoriumReplayPagePolicyV1(max_records=1),
                incomplete.continuation,
            )

    assert type(completed) is SensoriumReplayCompleteV1
    assert completed.state == accepted.next_state
    assert completed.page_work == SensoriumReplayPageWorkV1(
        records_examined=1,
        observations_applied=1,
        canonical_payload_bytes_examined=completed.page_work.canonical_payload_bytes_examined,
    )


def test_replay_wire_shapes_are_exact_frozen_and_bounded(tmp_path: Path) -> None:
    profile = baseline_boundary_profile()
    policy = SensoriumReplayPagePolicyV1(max_records=0)
    with pytest.raises(FrozenInstanceError):
        policy.max_records = 1  # type: ignore[misc]

    with EncryptedLedger(
        tmp_path / "memory.sqlite3", StaticKeyProvider(MASTER_KEY)
    ) as ledger:
        with ledger.verified_session() as session:
            session.append_once("unrelated:1", {"schema": "other.v1"})
            incomplete = replay_sensorium_page(session, policy, profile)

    assert type(incomplete) is SensoriumReplayIncompleteV1
    assert tuple(field.name for field in fields(incomplete.continuation)) == (
        "core",
        "task1_checkpoint",
        "records_examined",
        "observations_applied",
        "canonical_payload_bytes_examined",
    )
    continuation_wire = replay_continuation_to_json_value(incomplete.continuation)
    assert set(continuation_wire) == {
        "schema",
        "core",
        "task1_checkpoint",
        "records_examined",
        "observations_applied",
        "canonical_payload_bytes_examined",
    }
    assert continuation_wire["schema"] == ("aluclu.sensorium-replay-continuation.v1")
    assert (
        len(CanonicalJsonValue.from_value(continuation_wire).canonical_bytes) <= 5_120
    )
    assert set(replay_incomplete_to_json_value(incomplete)) == {
        "schema",
        "continuation",
        "page_work",
    }
    assert (
        replay_continuation_from_json_value(continuation_wire)
        == incomplete.continuation
    )
    assert (
        replay_incomplete_from_json_value(replay_incomplete_to_json_value(incomplete))
        == incomplete
    )
    assert (
        replay_page_policy_from_json_value(replay_page_policy_to_json_value(policy))
        == policy
    )
    assert (
        replay_page_work_from_json_value(
            replay_page_work_to_json_value(incomplete.page_work)
        )
        == incomplete.page_work
    )


def test_replay_wire_decoders_reject_unknown_fields_and_bool_counters() -> None:
    policy_wire = replay_page_policy_to_json_value(
        SensoriumReplayPagePolicyV1(max_records=1)
    )
    policy_wire["unknown"] = 1
    with pytest.raises(InputBoundaryError):
        replay_page_policy_from_json_value(policy_wire)

    work_wire = replay_page_work_to_json_value(
        SensoriumReplayPageWorkV1(
            records_examined=1,
            observations_applied=1,
            canonical_payload_bytes_examined=10,
        )
    )
    work_wire["records_examined"] = True
    with pytest.raises(InputBoundaryError):
        replay_page_work_from_json_value(work_wire)


def test_empty_snapshot_completes_even_with_zero_budget(tmp_path: Path) -> None:
    profile = baseline_boundary_profile()
    with EncryptedLedger(
        tmp_path / "memory.sqlite3", StaticKeyProvider(MASTER_KEY)
    ) as ledger:
        with ledger.verified_session() as session:
            result = replay_sensorium_page(
                session, SensoriumReplayPagePolicyV1(max_records=0), profile
            )

    assert type(result) is SensoriumReplayCompleteV1
    assert type(result.state) is SensoriumStateV1
    assert result.state.last_applied_sequence == 0
    assert set(replay_complete_to_json_value(result)) == {
        "schema",
        "state",
        "page_work",
    }
    assert replay_complete_from_json_value(replay_complete_to_json_value(result)) == (
        result
    )


def test_changed_head_continuation_raises_and_does_not_resume(
    tmp_path: Path,
) -> None:
    profile = baseline_boundary_profile()
    with EncryptedLedger(
        tmp_path / "memory.sqlite3", StaticKeyProvider(MASTER_KEY)
    ) as ledger:
        with ledger.verified_session() as session:
            initial = initialize_empty_sensorium_state(session, profile)
            assert type(initial) is SensoriumStateV1
            accepted = ingest_observation(session, _request(), profile, initial)
            assert type(accepted) is ObservationAcceptedV1
            incomplete = replay_sensorium_page(
                session, SensoriumReplayPagePolicyV1(max_records=0), profile
            )
            assert type(incomplete) is SensoriumReplayIncompleteV1

            session.append_once("unrelated:changed-head", {"schema": "other.v1"})
            with pytest.raises(LedgerSnapshotChanged):
                replay_sensorium_page(
                    session,
                    SensoriumReplayPagePolicyV1(max_records=1),
                    incomplete.continuation,
                )


def test_one_shot_and_page_partitions_produce_identical_final_state(
    tmp_path: Path,
) -> None:
    profile = baseline_boundary_profile()
    with EncryptedLedger(
        tmp_path / "memory.sqlite3", StaticKeyProvider(MASTER_KEY)
    ) as ledger:
        with ledger.verified_session() as session:
            state = initialize_empty_sensorium_state(session, profile)
            assert type(state) is SensoriumStateV1
            for index in range(1, 18):
                accepted = ingest_observation(
                    session, _indexed_request(index), profile, state
                )
                assert type(accepted) is ObservationAcceptedV1
                state = accepted.next_state

            expected_bytes = encode_sensorium_state(
                _complete_replay(session, page_size=64).state
            )
            for page_size in (1, 2, 3, 7, 16):
                completed = _complete_replay(session, page_size=page_size)
                assert encode_sensorium_state(completed.state) == expected_bytes
                assert completed.state == state


def test_shred_safe_replay_adopts_only_surviving_authenticated_post_core(
    tmp_path: Path,
) -> None:
    profile = baseline_boundary_profile()
    first_request = _indexed_request(1)
    second_request = _indexed_request(2)
    with EncryptedLedger(
        tmp_path / "memory.sqlite3", StaticKeyProvider(MASTER_KEY)
    ) as ledger:
        with ledger.verified_session() as session:
            state = initialize_empty_sensorium_state(session, profile)
            assert type(state) is SensoriumStateV1
            first = ingest_observation(session, first_request, profile, state)
            assert type(first) is ObservationAcceptedV1
            second = ingest_observation(
                session, second_request, profile, first.next_state
            )
            assert type(second) is ObservationAcceptedV1
            assert session.shred(first_request.observation_id)

            completed = _complete_replay(session, page_size=1)
            assert session.read(first_request.observation_id) is None
            assert session.is_tombstoned(first_request.observation_id)

    assert completed.state.core == second.next_state.core
    assert completed.state.core.last_observation_id == second_request.observation_id
    assert completed.state.core.last_observation_sequence == 2
    assert first_request.retrieval_text is not None
    assert first_request.retrieval_text.encode() not in encode_sensorium_state(
        completed.state
    )


def test_shred_gap_survives_unrelated_record_and_page_boundary(
    tmp_path: Path,
) -> None:
    profile = baseline_boundary_profile()
    first_request = _indexed_request(1)
    second_request = _indexed_request(2)
    with EncryptedLedger(
        tmp_path / "memory.sqlite3", StaticKeyProvider(MASTER_KEY)
    ) as ledger:
        with ledger.verified_session() as session:
            state = initialize_empty_sensorium_state(session, profile)
            assert type(state) is SensoriumStateV1
            first = ingest_observation(session, first_request, profile, state)
            assert type(first) is ObservationAcceptedV1

            unrelated = session.append_once(
                "unrelated:between-observations", {"schema": "other.v1"}
            )
            refreshed = _complete_replay(session, page_size=1).state
            assert refreshed.core == first.next_state.core
            assert refreshed.task1_checkpoint.snapshot_head_sequence == (
                unrelated.record.sequence
            )
            second = ingest_observation(
                session,
                second_request,
                profile,
                refreshed,
            )
            assert type(second) is ObservationAcceptedV1
            assert session.shred(first_request.observation_id)

            one_shot = _complete_replay(session, page_size=4)
            paged = _complete_replay(session, page_size=1)

    assert one_shot.state.core == second.next_state.core
    assert paged.state == one_shot.state
    assert paged.state.core.last_observation_id == second_request.observation_id
    assert paged.state.core.last_observation_sequence == (
        second.stored_observation.post_core_state.last_observation_sequence
    )


def test_unrelated_live_record_does_not_authorize_predecessor_mismatch(
    tmp_path: Path,
) -> None:
    profile = baseline_boundary_profile()
    first_request = _indexed_request(1)
    second_request = _indexed_request(2)
    with EncryptedLedger(
        tmp_path / "memory.sqlite3", StaticKeyProvider(MASTER_KEY)
    ) as ledger:
        with ledger.verified_session() as session:
            state = initialize_empty_sensorium_state(session, profile)
            assert type(state) is SensoriumStateV1
            first = ingest_observation(session, first_request, profile, state)
            assert type(first) is ObservationAcceptedV1
            unrelated = session.append_once(
                "unrelated:without-shred", {"schema": "other.v1"}
            )
            canonical = canonicalize_observation(
                second_request,
                profile,
                first.next_state.core,
                unrelated.record.sequence + 1,
            )
            forged = build_canonical_observation(
                request=second_request,
                boundary_decision=canonical.boundary_decision,
                pre_core_state_digest="0" * 64,
                post_core_state=canonical.post_core_state,
                pre_append_head_sequence=unrelated.record.sequence,
                pre_append_head_hash=unrelated.record.record_hash,
                boundary_profile_id=profile.profile_id,
            )
            session.append_once(
                second_request.observation_id,
                canonical_observation_to_json_value(forged),
            )

            with pytest.raises(
                LedgerIntegrityError,
                match="predecessor core digest does not match",
            ):
                _complete_replay(session, page_size=1)


def test_unrelated_shredded_record_does_not_authorize_predecessor_mismatch(
    tmp_path: Path,
) -> None:
    profile = baseline_boundary_profile()
    first_request = _indexed_request(1)
    second_request = _indexed_request(2)
    with EncryptedLedger(
        tmp_path / "memory.sqlite3", StaticKeyProvider(MASTER_KEY)
    ) as ledger:
        with ledger.verified_session() as session:
            state = initialize_empty_sensorium_state(session, profile)
            assert type(state) is SensoriumStateV1
            first = ingest_observation(session, first_request, profile, state)
            assert type(first) is ObservationAcceptedV1
            session.append_once(
                "unrelated:shredded-before-forgery", {"schema": "other.v1"}
            )
            assert session.shred("unrelated:shredded-before-forgery")
            tail = session.cursor(after_sequence=3, batch_size=1).suspend()
            canonical = canonicalize_observation(
                second_request,
                profile,
                first.next_state.core,
                tail.snapshot_head_sequence + 1,
            )
            forged = build_canonical_observation(
                request=second_request,
                boundary_decision=canonical.boundary_decision,
                pre_core_state_digest="0" * 64,
                post_core_state=canonical.post_core_state,
                pre_append_head_sequence=tail.snapshot_head_sequence,
                pre_append_head_hash=tail.snapshot_head_hash,
                boundary_profile_id=profile.profile_id,
            )
            session.append_once(
                second_request.observation_id,
                canonical_observation_to_json_value(forged),
            )

            with pytest.raises(
                LedgerIntegrityError,
                match="predecessor core digest does not match",
            ):
                _complete_replay(session, page_size=1)


def test_raw_task2_append_without_ingest_witness_cannot_bridge_after_shred(
    tmp_path: Path,
) -> None:
    profile = baseline_boundary_profile()
    first_request = _indexed_request(1)
    missing_request = _indexed_request(2)
    surviving_request = _indexed_request(3)
    with EncryptedLedger(
        tmp_path / "memory.sqlite3", StaticKeyProvider(MASTER_KEY)
    ) as ledger:
        with ledger.verified_session() as session:
            state = initialize_empty_sensorium_state(session, profile)
            assert type(state) is SensoriumStateV1
            first = ingest_observation(session, first_request, profile, state)
            assert type(first) is ObservationAcceptedV1

            missing = canonicalize_observation(
                missing_request,
                profile,
                first.next_state.core,
                2,
            )
            raw_missing = build_canonical_observation(
                request=missing_request,
                boundary_decision=missing.boundary_decision,
                pre_core_state_digest=derive_sensorium_core_state_digest(
                    first.next_state.core
                ),
                post_core_state=missing.post_core_state,
                pre_append_head_sequence=1,
                pre_append_head_hash=first.next_state.task1_checkpoint.snapshot_head_hash,
                boundary_profile_id=profile.profile_id,
            )
            missing_outcome = session.append_once(
                missing_request.observation_id,
                canonical_observation_to_json_value(raw_missing),
            )
            surviving = canonicalize_observation(
                surviving_request,
                profile,
                missing.post_core_state,
                3,
            )
            raw_surviving = build_canonical_observation(
                request=surviving_request,
                boundary_decision=surviving.boundary_decision,
                pre_core_state_digest=derive_sensorium_core_state_digest(
                    missing.post_core_state
                ),
                post_core_state=surviving.post_core_state,
                pre_append_head_sequence=missing_outcome.record.sequence,
                pre_append_head_hash=missing_outcome.record.record_hash,
                boundary_profile_id=profile.profile_id,
            )
            session.append_once(
                surviving_request.observation_id,
                canonical_observation_to_json_value(raw_surviving),
            )
            assert session.shred(missing_request.observation_id)

            with pytest.raises(
                LedgerIntegrityError,
                match="predecessor core digest does not match",
            ):
                _complete_replay(session, page_size=1)


def test_raw_gap_successor_cannot_borrow_valid_shredded_ingest_witness(
    tmp_path: Path,
) -> None:
    profile = baseline_boundary_profile()
    with EncryptedLedger(
        tmp_path / "memory.sqlite3", StaticKeyProvider(MASTER_KEY)
    ) as ledger:
        with ledger.verified_session() as session:
            state = initialize_empty_sensorium_state(session, profile)
            assert type(state) is SensoriumStateV1
            first = ingest_observation(session, _indexed_request(1), profile, state)
            assert type(first) is ObservationAcceptedV1
            missing = ingest_observation(
                session,
                _indexed_request(2),
                profile,
                first.next_state,
            )
            assert type(missing) is ObservationAcceptedV1
            successor_request = _indexed_request(3)
            canonical = canonicalize_observation(
                successor_request,
                profile,
                missing.next_state.core,
                3,
            )
            raw_successor = build_canonical_observation(
                request=successor_request,
                boundary_decision=canonical.boundary_decision,
                pre_core_state_digest=derive_sensorium_core_state_digest(
                    missing.next_state.core
                ),
                post_core_state=canonical.post_core_state,
                pre_append_head_sequence=2,
                pre_append_head_hash=(
                    missing.next_state.task1_checkpoint.snapshot_head_hash
                ),
                boundary_profile_id=profile.profile_id,
            )
            session.append_once(
                successor_request.observation_id,
                canonical_observation_to_json_value(raw_successor),
            )
            assert session.shred(_indexed_request(2).observation_id)

            with pytest.raises(
                LedgerIntegrityError,
                match="successor lacks authenticated ingest witness",
            ):
                _complete_replay(session, page_size=1)


def test_two_consecutive_shredded_ingests_bridge_exactly_across_pages(
    tmp_path: Path,
) -> None:
    profile = baseline_boundary_profile()
    requests = [_indexed_request(index) for index in range(1, 5)]
    with EncryptedLedger(
        tmp_path / "memory.sqlite3", StaticKeyProvider(MASTER_KEY)
    ) as ledger:
        with ledger.verified_session() as session:
            state = initialize_empty_sensorium_state(session, profile)
            assert type(state) is SensoriumStateV1
            accepted: list[ObservationAcceptedV1] = []
            for request in requests:
                result = ingest_observation(session, request, profile, state)
                assert type(result) is ObservationAcceptedV1
                accepted.append(result)
                state = result.next_state
            assert session.shred(requests[1].observation_id)
            assert session.shred(requests[2].observation_id)

            one_shot = _complete_replay(session, page_size=64)
            paged = _complete_replay(session, page_size=1)

    assert one_shot.state.core == accepted[-1].next_state.core
    assert paged.state == one_shot.state
    assert paged.state.core.last_observation_id == requests[-1].observation_id


def test_deleted_lineage_witness_causes_fail_closed_replay_without_content_leak(
    tmp_path: Path,
) -> None:
    path = tmp_path / "memory.sqlite3"
    profile = baseline_boundary_profile()
    first_request = _indexed_request(1)
    with EncryptedLedger(path, StaticKeyProvider(MASTER_KEY)) as ledger:
        with ledger.verified_session() as session:
            state = initialize_empty_sensorium_state(session, profile)
            assert type(state) is SensoriumStateV1
            first = ingest_observation(session, first_request, profile, state)
            assert type(first) is ObservationAcceptedV1
            second = ingest_observation(
                session,
                _indexed_request(2),
                profile,
                first.next_state,
            )
            assert type(second) is ObservationAcceptedV1
            assert session.shred(first_request.observation_id)

    connection = sqlite3.connect(path)
    try:
        row = connection.execute(
            "SELECT witness_body FROM append_witnesses WHERE event_id = ?",
            (first_request.observation_id,),
        ).fetchone()
        assert row is not None
        witness_bytes = row[0]
        assert type(witness_bytes) is bytes
        assert first_request.retrieval_text is not None
        assert first_request.retrieval_text.encode("utf-8") not in witness_bytes
        assert b'"index":1' not in witness_bytes
        connection.execute(
            "DELETE FROM append_witnesses WHERE event_id = ?",
            (first_request.observation_id,),
        )
        connection.commit()
    finally:
        connection.close()

    with EncryptedLedger(path, StaticKeyProvider(MASTER_KEY)) as reopened:
        with reopened.verified_session() as session:
            with pytest.raises(
                LedgerIntegrityError,
                match="predecessor core digest does not match",
            ):
                _complete_replay(session, page_size=1)


def test_unrelated_shred_is_ignored_when_exact_task2_bridge_exists(
    tmp_path: Path,
) -> None:
    profile = baseline_boundary_profile()
    with EncryptedLedger(
        tmp_path / "memory.sqlite3", StaticKeyProvider(MASTER_KEY)
    ) as ledger:
        with ledger.verified_session() as session:
            state = initialize_empty_sensorium_state(session, profile)
            assert type(state) is SensoriumStateV1
            first = ingest_observation(session, _indexed_request(1), profile, state)
            assert type(first) is ObservationAcceptedV1
            session.append_once("unrelated:shred-near-bridge", {"kind": "other"})
            assert session.shred("unrelated:shred-near-bridge")
            refreshed = _complete_replay(session, page_size=1).state
            assert refreshed.core == first.next_state.core
            missing = ingest_observation(
                session,
                _indexed_request(2),
                profile,
                refreshed,
            )
            assert type(missing) is ObservationAcceptedV1
            surviving = ingest_observation(
                session,
                _indexed_request(3),
                profile,
                missing.next_state,
            )
            assert type(surviving) is ObservationAcceptedV1
            assert session.shred(_indexed_request(2).observation_id)

            one_shot = _complete_replay(session, page_size=64)
            paged = _complete_replay(session, page_size=1)

    assert one_shot.state.core == surviving.next_state.core
    assert paged.state == one_shot.state


def test_unavailable_profile_requires_live_ingest_witness(
    tmp_path: Path,
) -> None:
    baseline = baseline_boundary_profile()
    custom = replace(baseline, name="custom-unavailable-profile")
    request = _indexed_request(1)
    with EncryptedLedger(
        tmp_path / "memory.sqlite3", StaticKeyProvider(MASTER_KEY)
    ) as ledger:
        with ledger.verified_session() as session:
            initial = initialize_empty_sensorium_state(session, baseline)
            assert type(initial) is SensoriumStateV1
            canonical = canonicalize_observation(request, custom, initial.core, 1)
            raw = build_canonical_observation(
                request=request,
                boundary_decision=canonical.boundary_decision,
                pre_core_state_digest=derive_sensorium_core_state_digest(initial.core),
                post_core_state=canonical.post_core_state,
                pre_append_head_sequence=0,
                pre_append_head_hash="0" * 64,
                boundary_profile_id=custom.profile_id,
            )
            session.append_once(
                request.observation_id,
                canonical_observation_to_json_value(raw),
            )

            with pytest.raises(
                LedgerIntegrityError,
                match="unavailable profile lacks authenticated ingest witness",
            ):
                _complete_replay(session, page_size=1)


def test_ingested_profile_change_replays_via_exact_live_witness(
    tmp_path: Path,
) -> None:
    baseline = baseline_boundary_profile()
    custom = replace(baseline, name="custom-ingested-profile")
    with EncryptedLedger(
        tmp_path / "memory.sqlite3", StaticKeyProvider(MASTER_KEY)
    ) as ledger:
        with ledger.verified_session() as session:
            state = initialize_empty_sensorium_state(session, baseline)
            assert type(state) is SensoriumStateV1
            first = ingest_observation(session, _indexed_request(1), baseline, state)
            assert type(first) is ObservationAcceptedV1
            changed = ingest_observation(
                session,
                _indexed_request(2),
                custom,
                first.next_state,
            )
            assert type(changed) is ObservationAcceptedV1

            one_shot = _complete_replay(session, page_size=64)
            paged = _complete_replay(session, page_size=1)

    assert one_shot.state.core == changed.next_state.core
    assert paged.state == one_shot.state


def test_claimed_malformed_observation_fails_closed_and_closes_cursor(
    tmp_path: Path,
) -> None:
    profile = baseline_boundary_profile()
    with EncryptedLedger(
        tmp_path / "memory.sqlite3", StaticKeyProvider(MASTER_KEY)
    ) as ledger:
        with ledger.verified_session() as session:
            session.append_once(
                "obs:t23-malformed",
                {"schema": "aluclu.observation.v1"},
            )
            with pytest.raises(LedgerIntegrityError):
                replay_sensorium_page(
                    session,
                    SensoriumReplayPagePolicyV1(max_records=1),
                    profile,
                )
            appended = session.append_once(
                "unrelated:after-malformed", {"schema": "other.v1"}
            )
            assert appended.created


def test_replay_recomputes_unbroken_transition_and_rejects_forged_decision(
    tmp_path: Path,
) -> None:
    profile = baseline_boundary_profile()
    request = _request()
    with EncryptedLedger(
        tmp_path / "memory.sqlite3", StaticKeyProvider(MASTER_KEY)
    ) as ledger:
        with ledger.verified_session() as session:
            initial = initialize_empty_sensorium_state(session, profile)
            assert type(initial) is SensoriumStateV1
            canonical = canonicalize_observation(
                request, profile, initial.core, observation_sequence=1
            )
            forged = build_canonical_observation(
                request=request,
                boundary_decision=EpisodeBoundaryDecisionV1(
                    episode_id=canonical.boundary_decision.episode_id,
                    reasons=(EpisodeBoundaryReason.FORCED,),
                ),
                pre_core_state_digest=derive_sensorium_core_state_digest(initial.core),
                post_core_state=canonical.post_core_state,
                pre_append_head_sequence=0,
                pre_append_head_hash="0" * 64,
                boundary_profile_id=profile.profile_id,
            )
            session.append_once(
                request.observation_id,
                canonical_observation_to_json_value(forged),
            )

            with pytest.raises(LedgerIntegrityError):
                replay_sensorium_page(
                    session,
                    SensoriumReplayPagePolicyV1(max_records=1),
                    profile,
                )
            assert session.append_once(
                "unrelated:after-forged-decision", {"schema": "other.v1"}
            ).created


def test_replay_rejects_post_core_with_different_last_observation_id(
    tmp_path: Path,
) -> None:
    profile = baseline_boundary_profile()
    request = _request()
    with EncryptedLedger(
        tmp_path / "memory.sqlite3", StaticKeyProvider(MASTER_KEY)
    ) as ledger:
        with ledger.verified_session() as session:
            initial = initialize_empty_sensorium_state(session, profile)
            assert type(initial) is SensoriumStateV1
            canonical = canonicalize_observation(
                request, profile, initial.core, observation_sequence=1
            )
            forged = build_canonical_observation(
                request=request,
                boundary_decision=canonical.boundary_decision,
                pre_core_state_digest=derive_sensorium_core_state_digest(initial.core),
                post_core_state=replace(
                    canonical.post_core_state,
                    last_observation_id="obs:t23-different",
                ),
                pre_append_head_sequence=0,
                pre_append_head_hash="0" * 64,
                boundary_profile_id=profile.profile_id,
            )
            session.append_once(
                request.observation_id,
                canonical_observation_to_json_value(forged),
            )

            with pytest.raises(LedgerIntegrityError):
                replay_sensorium_page(
                    session,
                    SensoriumReplayPagePolicyV1(max_records=1),
                    profile,
                )


def test_restart_replay_at_same_head_is_byte_identical(tmp_path: Path) -> None:
    ledger_path = tmp_path / "memory.sqlite3"
    profile = baseline_boundary_profile()
    with EncryptedLedger(ledger_path, StaticKeyProvider(MASTER_KEY)) as ledger:
        with ledger.verified_session() as session:
            state = initialize_empty_sensorium_state(session, profile)
            assert type(state) is SensoriumStateV1
            for index in range(1, 6):
                accepted = ingest_observation(
                    session, _indexed_request(index), profile, state
                )
                assert type(accepted) is ObservationAcceptedV1
                state = accepted.next_state
            before = encode_sensorium_state(
                _complete_replay(session, page_size=2).state
            )

    with EncryptedLedger(ledger_path, StaticKeyProvider(MASTER_KEY)) as ledger:
        with ledger.verified_session() as session:
            after = encode_sensorium_state(_complete_replay(session, page_size=3).state)

    assert after == before
