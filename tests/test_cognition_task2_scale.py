from __future__ import annotations

from pathlib import Path

from aluclu.cognition import (
    CanonicalJsonValue,
    EncryptedLedger,
    ObservationRequestV1,
    ProvenanceV1,
    SourceKind,
    StaticKeyProvider,
    encode_sensorium_state,
)
from aluclu.cognition.sensorium import (
    ObservationAcceptedV1,
    SensoriumReplayCompleteV1,
    SensoriumReplayPagePolicyV1,
    SensoriumStateV1,
    baseline_boundary_profile,
    ingest_observation,
    initialize_empty_sensorium_state,
    replay_sensorium_page,
)

MASTER_KEY = b"m" * 32


def _request(index: int) -> ObservationRequestV1:
    return ObservationRequestV1(
        observation_id=f"obs:t23-scale-{index:04d}",
        session_id="session:t23-scale",
        turn_id=f"turn:t23-scale-{index:04d}",
        provenance=ProvenanceV1(
            source_kind=SourceKind.USER,
            source_instance_id="user:local",
            origin_id=f"fixture:t23-scale-{index:04d}",
            observed_at_ns=1_725_000_000_000_000_000 + index,
            parent_observation_ids=(),
            capture_method="test",
            capture_version="1.0.0",
        ),
        content=CanonicalJsonValue.from_value({"index": index}),
        retrieval_text=f"scale observation {index}",
        topic_key="topic:scale",
        goal_ids=(),
        participant_ids=("participant:user",),
        tool_invocation_id=None,
        tool_phase=None,
        force_boundary=False,
    )


def test_8192_observation_replay_keeps_completed_state_bounded(
    tmp_path: Path,
) -> None:
    profile = baseline_boundary_profile()
    with EncryptedLedger(
        tmp_path / "memory.sqlite3", StaticKeyProvider(MASTER_KEY)
    ) as ledger:
        with ledger.verified_session() as session:
            state = initialize_empty_sensorium_state(session, profile)
            assert type(state) is SensoriumStateV1
            for index in range(1, 8_193):
                accepted = ingest_observation(session, _request(index), profile, state)
                assert type(accepted) is ObservationAcceptedV1
                state = accepted.next_state

            completed = replay_sensorium_page(
                session,
                SensoriumReplayPagePolicyV1(max_records=8_192),
                profile,
            )

    assert type(completed) is SensoriumReplayCompleteV1
    assert completed.state == state
    assert completed.state.core.last_observation_sequence == 8_192
    assert completed.page_work.records_examined == 8_192
    assert completed.page_work.observations_applied == 8_192
    assert len(encode_sensorium_state(completed.state)) <= 4_096
