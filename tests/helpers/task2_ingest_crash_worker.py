from __future__ import annotations

import os
import sys
from pathlib import Path

import aluclu.cognition.sensorium as sensorium_module
from aluclu.cognition import (
    CanonicalJsonValue,
    EncryptedLedger,
    ObservationRequestV1,
    ProvenanceV1,
    SourceKind,
    StaticKeyProvider,
)
from aluclu.cognition.sensorium import (
    baseline_boundary_profile,
    decode_sensorium_state,
    ingest_observation,
)

MASTER_KEY = b"m" * 32


def _request() -> ObservationRequestV1:
    return ObservationRequestV1(
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


def _crash_before_return(**_: object) -> None:
    os._exit(91)


def main() -> None:
    ledger_path = Path(sys.argv[1])
    state_path = Path(sys.argv[2])
    state = decode_sensorium_state(state_path.read_bytes())
    # Ingest reaches this constructor only after append and new-tail capture.
    sensorium_module.ObservationAcceptedV1 = _crash_before_return  # type: ignore[assignment]
    with EncryptedLedger(ledger_path, StaticKeyProvider(MASTER_KEY)) as ledger:
        with ledger.verified_session() as session:
            ingest_observation(
                session,
                _request(),
                baseline_boundary_profile(),
                state,
            )
    raise AssertionError("post-append crash hook was not reached")


if __name__ == "__main__":
    main()
