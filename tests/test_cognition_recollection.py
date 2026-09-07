from __future__ import annotations

from pathlib import Path

import pytest

from aluclu.cognition import (
    CanonicalJsonValue,
    CanonicalObservationV1,
    EncryptedLedger,
    InputBoundaryError,
    ObservationRequestV1,
    ProvenanceV1,
    SourceKind,
    StaticKeyProvider,
    build_canonical_observation,
    canonical_observation_to_json_value,
    derive_sensorium_core_state_digest,
)
from aluclu.cognition.recollection import (
    EventIdRecallQuery,
    ExactRecollection,
    NoRecollection,
    RecallBasis,
    recall,
)
from aluclu.cognition.sensorium import (
    ObservationAcceptedV1,
    ReceiptClass,
    SensoriumStateV1,
    baseline_boundary_profile,
    canonicalize_observation,
    classify_observation_receipt,
    ingest_observation,
    initialize_empty_sensorium_state,
)

MASTER_KEY = b"m" * 32


def _request() -> ObservationRequestV1:
    return ObservationRequestV1(
        observation_id="obs:recall-0001",
        session_id="session:recall",
        turn_id="turn:recall-0001",
        provenance=ProvenanceV1(
            source_kind=SourceKind.MODEL,
            source_instance_id="model:fixture",
            origin_id="fixture:recall",
            observed_at_ns=1_725_000_000_000_000_000,
            parent_observation_ids=(),
            capture_method="test",
            capture_version="1.0.0",
        ),
        content=CanonicalJsonValue.from_value(
            {"text": "exact bytes", "truth_status": "observation_only"}
        ),
        retrieval_text="exact bytes",
        topic_key=None,
        goal_ids=(),
        participant_ids=("participant:assistant",),
        tool_invocation_id=None,
        tool_phase=None,
        force_boundary=False,
    )


def test_direct_id_recall_returns_authenticated_exact_observation(
    tmp_path: Path,
) -> None:
    profile = baseline_boundary_profile()
    request = _request()
    with EncryptedLedger(
        tmp_path / "memory.sqlite3", StaticKeyProvider(MASTER_KEY)
    ) as ledger:
        with ledger.verified_session() as session:
            state = initialize_empty_sensorium_state(session, profile)
            assert type(state) is SensoriumStateV1
            accepted = ingest_observation(session, request, profile, state)
            assert type(accepted) is ObservationAcceptedV1

            result = recall(
                session, EventIdRecallQuery(observation_id=request.observation_id)
            )

    assert type(result) is ExactRecollection
    assert result.basis is RecallBasis.DIRECT_ID
    assert result.observation_id == request.observation_id
    assert result.episode_id == accepted.stored_observation.boundary_decision.episode_id
    assert result.sequence == accepted.next_state.last_applied_sequence
    assert result.record_hash == accepted.next_state.task1_checkpoint.snapshot_head_hash
    assert result.content_digest == accepted.stored_observation.content_digest
    assert result.content.canonical_bytes == request.content.canonical_bytes
    assert result.provenance == request.provenance
    assert result.content_is_observation is True
    assert result.content_is_verified_fact is False


def test_missing_or_nonobservation_id_cannot_be_exact_recollection(
    tmp_path: Path,
) -> None:
    with EncryptedLedger(
        tmp_path / "memory.sqlite3", StaticKeyProvider(MASTER_KEY)
    ) as ledger:
        with ledger.verified_session() as session:
            missing = recall(session, EventIdRecallQuery(observation_id="obs:missing"))
            session.append_once("obs:not-memory", {"schema": "other.v1", "value": 1})
            nonobservation = recall(
                session, EventIdRecallQuery(observation_id="obs:not-memory")
            )

        with pytest.raises(InputBoundaryError):
            recall(ledger, EventIdRecallQuery(observation_id="obs:missing"))  # type: ignore[arg-type]

    assert type(missing) is NoRecollection
    assert type(nonobservation) is NoRecollection
    assert not isinstance(nonobservation, ExactRecollection)
    with pytest.raises((InputBoundaryError, TypeError)):
        EventIdRecallQuery(observation_id="evt:not-observation")


def test_valid_looking_observation_at_wrong_ledger_position_is_not_memory(
    tmp_path: Path,
) -> None:
    profile = baseline_boundary_profile()
    request = _request()
    with EncryptedLedger(
        tmp_path / "memory.sqlite3", StaticKeyProvider(MASTER_KEY)
    ) as ledger:
        with ledger.verified_session() as session:
            state = initialize_empty_sensorium_state(session, profile)
            assert type(state) is SensoriumStateV1
            canonical = canonicalize_observation(request, profile, state.core)
            fake = build_canonical_observation(
                request=request,
                boundary_decision=canonical.boundary_decision,
                pre_core_state_digest=derive_sensorium_core_state_digest(state.core),
                post_core_state=canonical.post_core_state,
                pre_append_head_sequence=0,
                pre_append_head_hash="0" * 64,
                boundary_profile_id=profile.profile_id,
            )
            assert type(fake) is CanonicalObservationV1
            session.append_once("unrelated:before", {"schema": "other.v1"})
            session.append_once(
                request.observation_id,
                canonical_observation_to_json_value(fake),
            )
            result = recall(
                session, EventIdRecallQuery(observation_id=request.observation_id)
            )
            receipt = classify_observation_receipt(session, request)

    assert type(result) is NoRecollection
    assert receipt.receipt_class is ReceiptClass.CONFLICT
