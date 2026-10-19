from __future__ import annotations

import subprocess
import sys
from pathlib import Path

from aluclu.cognition import (
    CanonicalJsonValue,
    EncryptedLedger,
    ObservationRequestV1,
    ProvenanceV1,
    SourceKind,
    StaticKeyProvider,
)
from aluclu.cognition.recollection import EventIdRecallQuery, ExactRecollection, recall
from aluclu.cognition.sensorium import (
    IngestStatus,
    ObservationAcceptedV1,
    SensoriumStateV1,
    baseline_boundary_profile,
    encode_sensorium_state,
    ingest_observation,
    initialize_empty_sensorium_state,
)

MASTER_KEY = b"m" * 32
CRASH_WORKER = (
    Path(__file__).resolve().parent / "helpers" / "task2_ingest_crash_worker.py"
)


def _request() -> ObservationRequestV1:
    return ObservationRequestV1(
        observation_id="obs:e2e-0001",
        session_id="session:e2e",
        turn_id="turn:e2e-0001",
        provenance=ProvenanceV1(
            source_kind=SourceKind.USER,
            source_instance_id="user:e2e",
            origin_id="fixture:e2e",
            observed_at_ns=1_725_000_000_000_000_000,
            parent_observation_ids=(),
            capture_method="test",
            capture_version="1.0.0",
        ),
        content=CanonicalJsonValue.from_value(
            {"memory": "survives reopen", "unicode": "e\u0301"}
        ),
        retrieval_text="survives reopen",
        topic_key="topic:e2e",
        goal_ids=("goal:e2e",),
        participant_ids=("participant:user",),
        tool_invocation_id=None,
        tool_phase=None,
        force_boundary=False,
    )


def test_ingest_retry_after_lost_return_and_reopen_exact_recall(tmp_path: Path) -> None:
    path = tmp_path / "memory.sqlite3"
    request = _request()
    profile = baseline_boundary_profile()

    with EncryptedLedger(path, StaticKeyProvider(MASTER_KEY)) as ledger:
        with ledger.verified_session() as session:
            before = initialize_empty_sensorium_state(session, profile)
            assert type(before) is SensoriumStateV1
            first = ingest_observation(session, request, profile, before)
            assert type(first) is ObservationAcceptedV1
            expected_bytes = first.stored_observation.request.content.canonical_bytes
            expected_hash = first.next_state.task1_checkpoint.snapshot_head_hash
        # The return value is deliberately discarded across the session boundary.
        with ledger.verified_session() as retry_session:
            retry = ingest_observation(retry_session, request, profile, before)
            assert type(retry) is ObservationAcceptedV1
            assert retry.status is IngestStatus.DUPLICATE
            assert retry.next_state == first.next_state
            assert retry_session.event_count() == 1

    with EncryptedLedger(path, StaticKeyProvider(MASTER_KEY)) as reopened:
        with reopened.verified_session() as session:
            result = recall(
                session, EventIdRecallQuery(observation_id=request.observation_id)
            )
            assert type(result) is ExactRecollection
            assert result.content.canonical_bytes == expected_bytes
            assert result.record_hash == expected_hash
            assert session.event_count() == 1


def test_real_process_death_after_append_converges_on_retry(tmp_path: Path) -> None:
    path = tmp_path / "crash-memory.sqlite3"
    state_path = tmp_path / "pre-state.json"
    profile = baseline_boundary_profile()
    request = ObservationRequestV1(
        observation_id="obs:crash-0001",
        session_id="session:crash",
        turn_id="turn:crash-0001",
        provenance=ProvenanceV1(
            source_kind=SourceKind.USER,
            source_instance_id="user:crash",
            origin_id="fixture:crash",
            observed_at_ns=1_725_000_000_000_000_000,
            parent_observation_ids=(),
            capture_method="subprocess",
            capture_version="1.0.0",
        ),
        content=CanonicalJsonValue.from_value({"memory": "committed before crash"}),
        retrieval_text="committed before crash",
        topic_key="topic:crash",
        goal_ids=("goal:crash",),
        participant_ids=("participant:user",),
        tool_invocation_id=None,
        tool_phase=None,
        force_boundary=False,
    )
    with EncryptedLedger(path, StaticKeyProvider(MASTER_KEY)) as ledger:
        with ledger.verified_session() as session:
            state = initialize_empty_sensorium_state(session, profile)
            assert type(state) is SensoriumStateV1
            state_path.write_bytes(encode_sensorium_state(state))

    completed = subprocess.run(
        [sys.executable, str(CRASH_WORKER), str(path), str(state_path)],
        capture_output=True,
        check=False,
        text=True,
        timeout=30,
    )
    assert completed.returncode == 91, (completed.stdout, completed.stderr)
    assert completed.stdout == ""
    assert completed.stderr == ""

    with EncryptedLedger(path, StaticKeyProvider(MASTER_KEY)) as reopened:
        with reopened.verified_session() as session:
            retry = ingest_observation(session, request, profile, state)
            assert type(retry) is ObservationAcceptedV1
            assert retry.status is IngestStatus.DUPLICATE
            assert session.event_count() == 1
            exact = recall(
                session, EventIdRecallQuery(observation_id=request.observation_id)
            )
            assert type(exact) is ExactRecollection
            assert exact.content.canonical_bytes == request.content.canonical_bytes
