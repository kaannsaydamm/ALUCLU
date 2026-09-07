from __future__ import annotations

from dataclasses import FrozenInstanceError, fields
from pathlib import Path

import pytest

from aluclu.cognition import (
    CanonicalJsonValue,
    EncryptedLedger,
    ObservationRequestV1,
    ProvenanceV1,
    SourceKind,
    StaticKeyProvider,
)
from aluclu.cognition.sensorium import (
    ObservationAcceptedV1,
    SensoriumReplayCompleteV1,
    SensoriumReplayContinuationV1,
    SensoriumReplayIncompleteV1,
    SensoriumReplayPagePolicyV1,
    SensoriumReplayPageWorkV1,
    SensoriumStateV1,
    baseline_boundary_profile,
    ingest_observation,
    initialize_empty_sensorium_state,
    replay_complete_to_json_value,
    replay_continuation_to_json_value,
    replay_incomplete_to_json_value,
    replay_sensorium_page,
)

MASTER_KEY = b"m" * 32


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
