from __future__ import annotations

from pathlib import Path

import pytest

from aluclu.cognition import (
    AbstainedRecollection,
    ActiveCalibrationProfileV1,
    CalibrationCompatibilityRequirementsV1,
    CalibrationProfileV1,
    CalibrationPurpose,
    CalibrationSpecV1,
    CanonicalJsonValue,
    ConflictedRecollection,
    EncryptedLedger,
    EventIdRecallQuery,
    ExactRecollection,
    IngestStatus,
    InputBoundaryError,
    LabelIndependenceStatus,
    LabelProvenanceManifestV1,
    NoRecollection,
    ObservationAcceptedV1,
    ObservationRequestV1,
    ProvenanceV1,
    RecallBasis,
    RecallExecutionPolicyV1,
    ReconsolidationReason,
    SensoriumReplayCompleteV1,
    SensoriumReplayContinuationV1,
    SensoriumReplayIncompleteV1,
    SensoriumReplayPagePolicyV1,
    SensoriumStateV1,
    SourceKind,
    StaticKeyProvider,
    TextRecallQuery,
    ThresholdSelectionRule,
    activate_calibration_profile,
    active_feature_spec_id,
    active_normalizer_id,
    active_scorer_id,
    baseline_boundary_profile,
    build_calibration_artifact,
    commit_reconsolidation,
    derive_calibration_spec_digest,
    derive_label_provenance_manifest_digest,
    explicit_calibration_test_harness,
    ingest_observation,
    initialize_empty_sensorium_state,
    labeled_recall_example,
    propose_reconsolidation,
    recall,
    reconsolidation_record_from_json_value,
    replay_sensorium_page,
    tighten_recall_policy,
)
from aluclu.cognition.ledger import VerifiedLedgerSession

MASTER_KEY = b"v" * 32
DATASET_DIGEST = "b" * 64


def _request(
    index: int,
    *,
    source_kind: SourceKind,
    content: str,
    retrieval_text: str,
    force_boundary: bool,
) -> ObservationRequestV1:
    is_tool = source_kind is SourceKind.TOOL
    return ObservationRequestV1(
        observation_id=f"obs:vertical-{index:04d}",
        session_id="session:vertical",
        turn_id=f"turn:vertical-{index:04d}",
        provenance=ProvenanceV1(
            source_kind=source_kind,
            source_instance_id=f"{source_kind.value}:vertical",
            origin_id=f"fixture:vertical-{index:04d}",
            observed_at_ns=1_725_000_000_000_000_000 + index,
            parent_observation_ids=(),
            capture_method="task2-vertical-test",
            capture_version="1.0.0",
        ),
        content=CanonicalJsonValue.from_value(
            {"content": content, "truth_status": "observation_only"}
        ),
        retrieval_text=retrieval_text,
        topic_key="topic:vertical",
        goal_ids=("goal:vertical",),
        participant_ids=("participant:model", "participant:user"),
        tool_invocation_id="tool:vertical-0003" if is_tool else None,
        tool_phase="result" if is_tool else None,
        force_boundary=force_boundary,
    )


def _active_profile() -> ActiveCalibrationProfileV1:
    manifest = LabelProvenanceManifestV1(
        issuer_id="issuer:vertical-test-team",
        adjudication_method_id="held-out-double-review.v1",
        gold_source_digest="a" * 64,
        dataset_manifest_digest=DATASET_DIGEST,
        scorer_input_manifest_digest="c" * 64,
        gold_label_manifest_digest="d" * 64,
        fit_example_ids=("example:fit-1",),
        calibration_example_ids=("example:calibration-1", "example:calibration-2"),
        external_evidence_reference="audit:task2-vertical-test-only",
        external_signature_digest=None,
        independence_status=LabelIndependenceStatus.ASSERTED_NOT_PROVEN,
    )
    manifest_digest = derive_label_provenance_manifest_digest(manifest)
    spec = CalibrationSpecV1(
        purpose=CalibrationPurpose.PERSONAL_MEMORY_TEXT,
        query_stratum_id="personal-memory.en.v1",
        scorer_id=active_scorer_id(),
        normalizer_id=active_normalizer_id(),
        feature_spec_id=active_feature_spec_id(),
        boundary_schema_id="aluclu.boundary-profile.v1",
        dataset_manifest_digest=DATASET_DIGEST,
        label_provenance_manifest_digest=manifest_digest,
        threshold_grid_q32=(0, 2**31, 2**32),
        minimum_margin_q32=0,
        alpha_decimal="1",
        delta_decimal="0.05",
        minimum_selected=1,
        minimum_coverage_decimal="0",
        selection_rule=ThresholdSelectionRule.MAX_COVERAGE_THEN_HIGHER_THRESHOLD,
    )
    spec_digest = derive_calibration_spec_digest(spec)
    examples = tuple(
        labeled_recall_example(
            example_id=f"example:calibration-{index}",
            calibration_spec_digest=spec_digest,
            label_provenance_manifest_digest=manifest_digest,
            score_q32=score,
            eligible=True,
            target_observation_id=f"obs:gold-{index}",
            predicted_observation_id=f"obs:gold-{index}",
        )
        for index, score in ((1, 2**32), (2, 2**31))
    )
    active = activate_calibration_profile(
        CalibrationProfileV1(
            spec=spec,
            artifact=build_calibration_artifact(spec, manifest, examples),
        ),
        CalibrationCompatibilityRequirementsV1(
            purpose=spec.purpose,
            query_stratum_id=spec.query_stratum_id,
            scorer_id=spec.scorer_id,
            normalizer_id=spec.normalizer_id,
            feature_spec_id=spec.feature_spec_id,
            boundary_schema_id=spec.boundary_schema_id,
            dataset_manifest_digest=spec.dataset_manifest_digest,
        ),
        test_harness=explicit_calibration_test_harness(),
    )
    assert type(active) is ActiveCalibrationProfileV1
    return active


def _policy(active: ActiveCalibrationProfileV1) -> RecallExecutionPolicyV1:
    return RecallExecutionPolicyV1(
        max_records=64,
        top_k=8,
        max_returned_payload_bytes=262_144,
        active_normalizer_id=active.normalizer_id,
        active_feature_spec_id=active.feature_spec_id,
        minimum_score_q32=active.minimum_score_q32,
        minimum_margin_q32=active.minimum_margin_q32,
        allow_approximate=False,
        allow_incomplete=False,
    )


def _complete_replay(
    session: VerifiedLedgerSession, *, page_size: int
) -> SensoriumReplayCompleteV1:
    start = baseline_boundary_profile()
    while True:
        result = replay_sensorium_page(
            session,
            SensoriumReplayPagePolicyV1(max_records=page_size),
            start,
        )
        if type(result) is SensoriumReplayCompleteV1:
            return result
        assert type(result) is SensoriumReplayIncompleteV1
        assert type(result.continuation) is SensoriumReplayContinuationV1
        start = result.continuation


def test_task2_full_vertical_restart_lineage_and_no_authority_promotion(
    tmp_path: Path,
) -> None:
    path = tmp_path / "vertical.sqlite3"
    profile = baseline_boundary_profile()
    requests = (
        _request(
            1,
            source_kind=SourceKind.USER,
            content="original personal observation",
            retrieval_text="cedar protocol stable",
            force_boundary=True,
        ),
        _request(
            2,
            source_kind=SourceKind.MODEL,
            content="unique model observation",
            retrieval_text="violet gasket checksum",
            force_boundary=True,
        ),
        _request(
            3,
            source_kind=SourceKind.TOOL,
            content="near tie candidate a",
            retrieval_text="shared near tie signal",
            force_boundary=False,
        ),
        _request(
            4,
            source_kind=SourceKind.MODEL,
            content="near tie candidate b",
            retrieval_text="shared near tie signal",
            force_boundary=False,
        ),
        _request(
            5,
            source_kind=SourceKind.USER,
            content="explicit correction observation",
            retrieval_text="correction trigger",
            force_boundary=True,
        ),
    )
    active = _active_profile()
    policy = _policy(active)
    tightening = tighten_recall_policy(policy, active)

    with EncryptedLedger(path, StaticKeyProvider(MASTER_KEY)) as ledger:
        with ledger.verified_session() as session:
            state = initialize_empty_sensorium_state(session, profile)
            assert type(state) is SensoriumStateV1
            initial = state
            accepted: list[ObservationAcceptedV1] = []
            first = ingest_observation(session, requests[0], profile, state)
            assert type(first) is ObservationAcceptedV1
            assert first.status is IngestStatus.APPLIED
            accepted.append(first)
            state = first.next_state

            duplicate = ingest_observation(session, requests[0], profile, initial)
            assert type(duplicate) is ObservationAcceptedV1
            assert duplicate.status is IngestStatus.DUPLICATE
            assert duplicate.next_state == first.next_state
            assert session.event_count() == 1

            for request in requests[1:]:
                outcome = ingest_observation(session, request, profile, state)
                assert type(outcome) is ObservationAcceptedV1
                assert outcome.status is IngestStatus.APPLIED
                accepted.append(outcome)
                state = outcome.next_state
            expected_state = state
            assert session.event_count() == len(requests)

            parent = recall(session, EventIdRecallQuery(observation_id=requests[0].observation_id))
            trigger = recall(session, EventIdRecallQuery(observation_id=requests[4].observation_id))
            assert type(parent) is ExactRecollection
            assert type(trigger) is ExactRecollection
            assert parent.content_is_observation and not parent.content_is_verified_fact

            selected = recall(
                session,
                TextRecallQuery(text=requests[1].retrieval_text or ""),
                policy=policy,
                active_profile=active,
                policy_tightening=tightening,
            )
            assert type(selected) is ExactRecollection
            assert selected.basis is RecallBasis.CALIBRATED_TEXT_MATCH
            assert selected.observation_id == requests[1].observation_id
            assert selected.content_is_observation and not selected.content_is_verified_fact

            conflict = recall(
                session,
                TextRecallQuery(text="shared near tie signal"),
                policy=policy,
                active_profile=active,
                policy_tightening=tightening,
            )
            assert type(conflict) is ConflictedRecollection
            forced = recall(
                session,
                TextRecallQuery(text="violet gasket checksum"),
                policy=policy,
                active_profile=active,
                policy_tightening=tighten_recall_policy(
                    policy, active, force_abstain=True
                ),
            )
            assert type(forced) is AbstainedRecollection

            proposal = propose_reconsolidation(
                parent, trigger, reason=ReconsolidationReason.CORRECTION
            )
            created = commit_reconsolidation(session, proposal)
            assert created.created is True
            expected_parent_hash = parent.record_hash
            expected_trigger_hash = trigger.record_hash

    with EncryptedLedger(path, StaticKeyProvider(MASTER_KEY)) as reopened:
        with reopened.verified_session() as session:
            replayed = _complete_replay(session, page_size=1)
            assert replayed.state.core == expected_state.core
            assert replayed.state.core.last_observation_sequence == len(requests)
            assert replayed.state.task1_checkpoint.snapshot_head_sequence == (
                len(requests) + 1
            )
            parent_after = recall(
                session, EventIdRecallQuery(observation_id=parent.observation_id)
            )
            trigger_after = recall(
                session, EventIdRecallQuery(observation_id=trigger.observation_id)
            )
            assert type(parent_after) is ExactRecollection
            assert type(trigger_after) is ExactRecollection
            assert parent_after.record_hash == expected_parent_hash
            assert trigger_after.record_hash == expected_trigger_hash

            child = session.read(proposal.reconsolidation_id)
            assert child is not None
            decoded = reconsolidation_record_from_json_value(child.payload)
            assert decoded == proposal.record
            with pytest.raises(InputBoundaryError, match="observation_id is invalid"):
                EventIdRecallQuery(observation_id=proposal.reconsolidation_id)
            assert session.shred(parent.observation_id)

    with EncryptedLedger(path, StaticKeyProvider(MASTER_KEY)) as reopened:
        with reopened.verified_session() as session:
            assert type(
                recall(session, EventIdRecallQuery(observation_id=parent.observation_id))
            ) is NoRecollection
            child = session.read(proposal.reconsolidation_id)
            assert child is not None
            assert "original personal observation" not in str(child.payload)
            assert session.is_tombstoned(parent.observation_id)
