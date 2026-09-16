from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

from aluclu.cognition import (
    CanonicalJsonValue,
    EncryptedLedger,
    IngestStatus,
    ObservationAcceptedV1,
    ObservationRequestV1,
    ProvenanceV1,
    SensoriumStateV1,
    SourceKind,
    StaticKeyProvider,
    baseline_boundary_profile,
    encode_sensorium_state,
    ingest_observation,
    initialize_empty_sensorium_state,
)

MASTER_KEY = b"p" * 32
WORKER = Path(__file__).resolve().parent / "helpers" / "task2_portability_worker.py"
SRC_ROOT = Path(__file__).resolve().parents[1] / "src"


def _request(index: int) -> ObservationRequestV1:
    source_kind = (SourceKind.USER, SourceKind.MODEL, SourceKind.TOOL)[
        (index - 1) % 3
    ]
    is_tool = source_kind is SourceKind.TOOL
    return ObservationRequestV1(
        observation_id=f"obs:portable-{index:04d}",
        session_id="session:portable-256",
        turn_id=f"turn:portable-{index:04d}",
        provenance=ProvenanceV1(
            source_kind=source_kind,
            source_instance_id=f"{source_kind.value}:portable",
            origin_id=f"fixture:portable-{index:04d}",
            observed_at_ns=1_725_000_000_000_000_000 + index,
            parent_observation_ids=(),
            capture_method="task2-portability-smoke",
            capture_version="1.0.0",
        ),
        content=CanonicalJsonValue.from_value(
            {"index": index, "status": "observation_not_fact"}
        ),
        retrieval_text=(
            "portable terminal sentinel 256"
            if index == 256
            else f"portable observation {index:04d}"
        ),
        topic_key="topic:portable",
        goal_ids=("goal:portable",),
        participant_ids=("participant:model", "participant:user"),
        tool_invocation_id=f"tool:portable-{index:04d}" if is_tool else None,
        tool_phase="result" if is_tool else None,
        force_boundary=index in {1, 64, 128, 192, 256},
    )


def test_256_observation_reopen_replay_and_recall_on_this_host(
    tmp_path: Path,
) -> None:
    path = tmp_path / "portable.sqlite3"
    profile = baseline_boundary_profile()
    first_request = _request(1)
    final_request = _request(256)
    expected_state: SensoriumStateV1 | None = None
    expected_hash = ""

    with EncryptedLedger(path, StaticKeyProvider(MASTER_KEY)) as ledger:
        with ledger.verified_session() as session:
            state = initialize_empty_sensorium_state(session, profile)
            assert type(state) is SensoriumStateV1
            before_first = state
            for index in range(1, 257):
                accepted = ingest_observation(
                    session, _request(index), profile, state
                )
                assert type(accepted) is ObservationAcceptedV1
                assert accepted.status is IngestStatus.APPLIED
                state = accepted.next_state
                if index == 1:
                    duplicate = ingest_observation(
                        session, first_request, profile, before_first
                    )
                    assert type(duplicate) is ObservationAcceptedV1
                    assert duplicate.status is IngestStatus.DUPLICATE
                    assert session.event_count() == 1
                if index == 256:
                    expected_hash = accepted.next_state.task1_checkpoint.snapshot_head_hash
            assert session.event_count() == 256
            expected_state = state

    assert type(expected_state) is SensoriumStateV1
    assert len(encode_sensorium_state(expected_state)) <= 4_096
    environment = os.environ.copy()
    environment["PYTHONPATH"] = os.pathsep.join(
        (str(SRC_ROOT), environment["PYTHONPATH"])
        if environment.get("PYTHONPATH")
        else (str(SRC_ROOT),)
    )
    completed = subprocess.run(
        [sys.executable, str(WORKER), str(path), final_request.observation_id],
        cwd=Path(__file__).resolve().parents[1],
        env=environment,
        capture_output=True,
        text=True,
        check=False,
        timeout=180,
    )
    assert completed.returncode == 0, (completed.stdout, completed.stderr)
    assert completed.stderr == ""
    result = json.loads(completed.stdout)
    assert type(result) is dict
    assert result["event_count"] == 256
    assert result["one_shot_state_hex"] == encode_sensorium_state(expected_state).hex()
    assert result["paged_state_hex"] == result["one_shot_state_hex"]
    assert result["replay_records_examined"] == 256
    assert result["replay_observations_applied"] == 256
    assert result["paged_replay_steps"] == 7
    assert result["exact_observation_id"] == final_request.observation_id
    assert result["exact_content_hex"] == final_request.content.canonical_bytes.hex()
    assert result["exact_record_hash"] == expected_hash
    assert result["content_is_observation"] is True
    assert result["content_is_verified_fact"] is False
    assert result["one_shot_recall_ids"] == result["paged_recall_ids"]
    assert result["one_shot_recall_ids"][0] == final_request.observation_id
    assert result["recall_records_scanned"] == 256
