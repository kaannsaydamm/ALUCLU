from __future__ import annotations

import struct
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor
from dataclasses import fields, replace
from pathlib import Path
from typing import Any, cast

import pytest

from aluclu.cognition import (
    CanonicalJsonValue,
    CanonicalObservationV1,
    EncryptedLedger,
    InputBoundaryError,
    LedgerIntegrityError,
    LedgerLifecycleError,
    LedgerSnapshotChanged,
    ObservationRequestV1,
    ProvenanceV1,
    RetrievalFeatureVectorV1,
    SourceKind,
    StaticKeyProvider,
    active_feature_spec_id,
    active_normalizer_id,
    active_scorer_id,
    build_canonical_observation,
    canonical_observation_to_json_value,
    derive_content_digest,
    derive_sensorium_core_state_digest,
    encode_retrieval_text,
    measure_feature_similarity,
)
from aluclu.cognition.calibration import (
    ActiveCalibrationProfileV1,
    CalibrationCompatibilityRequirementsV1,
    CalibrationProfileUnavailableReason,
    CalibrationProfileUnavailableV1,
    CalibrationProfileV1,
    CalibrationPurpose,
    CalibrationSpecV1,
    LabelIndependenceStatus,
    LabelProvenanceManifestV1,
    ThresholdSelectionRule,
    activate_calibration_profile,
    build_calibration_artifact,
    derive_calibration_spec_digest,
    derive_label_provenance_manifest_digest,
    explicit_calibration_test_harness,
    labeled_recall_example,
)
from aluclu.cognition.recollection import (
    AbstainedRecollection,
    AbstainReason,
    AmbiguousExactRecollection,
    ApproximateCandidates,
    CalibratedTextMatchEvidenceV1,
    ConflictedRecollection,
    ContentDigestRecallQuery,
    EventIdRecallQuery,
    ExactRecollection,
    IncompleteRecollection,
    NoRecollection,
    NoScanRecollection,
    NoTextRecollection,
    RecallBasis,
    RecallExecutionPolicyV1,
    RecallFiltersV1,
    RecallPolicyTighteningV1,
    TextRecallQuery,
    recall,
    tighten_recall_policy,
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
MAX_Q32 = 1 << 32
FEATURE_DIMENSIONS = 1024
_GOLD_SOURCE_DIGEST = "a" * 64
_DATASET_MANIFEST_DIGEST = "b" * 64
_SCORER_INPUT_MANIFEST_DIGEST = "c" * 64
_GOLD_LABEL_MANIFEST_DIGEST = "d" * 64


def _provenance(**overrides: object) -> ProvenanceV1:
    values: dict[str, object] = {
        "source_kind": SourceKind.MODEL,
        "source_instance_id": "model:fixture",
        "origin_id": "fixture:recall",
        "observed_at_ns": 1_725_000_000_000_000_000,
        "parent_observation_ids": (),
        "capture_method": "test",
        "capture_version": "1.0.0",
    }
    values.update(overrides)
    return ProvenanceV1(**values)  # type: ignore[arg-type]


def _request(**overrides: object) -> ObservationRequestV1:
    values: dict[str, object] = {
        "observation_id": "obs:recall-0001",
        "session_id": "session:recall",
        "turn_id": "turn:recall-0001",
        "provenance": _provenance(),
        "content": CanonicalJsonValue.from_value(
            {"text": "exact bytes", "truth_status": "observation_only"}
        ),
        "retrieval_text": "exact bytes",
        "topic_key": None,
        "goal_ids": (),
        "participant_ids": ("participant:assistant",),
        "tool_invocation_id": None,
        "tool_phase": None,
        "force_boundary": False,
    }
    values.update(overrides)
    return ObservationRequestV1(**values)  # type: ignore[arg-type]


def _policy(
    *,
    max_records: int = 8192,
    top_k: int = 32,
    max_returned_payload_bytes: int = 262_144,
    minimum_score_q32: int = 0,
    minimum_margin_q32: int = MAX_Q32,
    allow_approximate: bool = False,
    allow_incomplete: bool = True,
) -> RecallExecutionPolicyV1:
    return RecallExecutionPolicyV1(
        max_records=max_records,
        top_k=top_k,
        max_returned_payload_bytes=max_returned_payload_bytes,
        active_normalizer_id=active_normalizer_id(),
        active_feature_spec_id=active_feature_spec_id(),
        minimum_score_q32=minimum_score_q32,
        minimum_margin_q32=minimum_margin_q32,
        allow_approximate=allow_approximate,
        allow_incomplete=allow_incomplete,
    )


def _label_manifest() -> LabelProvenanceManifestV1:
    return LabelProvenanceManifestV1(
        issuer_id="issuer:recall-test-team",
        adjudication_method_id="held-out-double-review.v1",
        gold_source_digest=_GOLD_SOURCE_DIGEST,
        dataset_manifest_digest=_DATASET_MANIFEST_DIGEST,
        scorer_input_manifest_digest=_SCORER_INPUT_MANIFEST_DIGEST,
        gold_label_manifest_digest=_GOLD_LABEL_MANIFEST_DIGEST,
        fit_example_ids=("example:fit-1",),
        calibration_example_ids=(
            "example:calibration-1",
            "example:calibration-2",
        ),
        external_evidence_reference="audit:recall-c3-red",
        external_signature_digest=None,
        independence_status=LabelIndependenceStatus.ASSERTED_NOT_PROVEN,
    )


def _active_calibration_profile(
    *,
    minimum_margin_q32: int = 0,
) -> ActiveCalibrationProfileV1:
    manifest = _label_manifest()
    spec = CalibrationSpecV1(
        purpose=CalibrationPurpose.PERSONAL_MEMORY_TEXT,
        query_stratum_id="personal-memory.en.v1",
        scorer_id=active_scorer_id(),
        normalizer_id=active_normalizer_id(),
        feature_spec_id=active_feature_spec_id(),
        boundary_schema_id="aluclu.boundary-profile.v1",
        dataset_manifest_digest=_DATASET_MANIFEST_DIGEST,
        label_provenance_manifest_digest=derive_label_provenance_manifest_digest(
            manifest
        ),
        threshold_grid_q32=(0, 2**31, 2**32),
        minimum_margin_q32=minimum_margin_q32,
        alpha_decimal="1",
        delta_decimal="0.05",
        minimum_selected=1,
        minimum_coverage_decimal="0",
        selection_rule=ThresholdSelectionRule.MAX_COVERAGE_THEN_HIGHER_THRESHOLD,
    )
    examples = (
        labeled_recall_example(
            example_id="example:calibration-1",
            calibration_spec_digest=derive_calibration_spec_digest(spec),
            label_provenance_manifest_digest=derive_label_provenance_manifest_digest(
                manifest
            ),
            score_q32=2**32,
            eligible=True,
            target_observation_id="obs:gold-1",
            predicted_observation_id="obs:gold-1",
        ),
        labeled_recall_example(
            example_id="example:calibration-2",
            calibration_spec_digest=derive_calibration_spec_digest(spec),
            label_provenance_manifest_digest=derive_label_provenance_manifest_digest(
                manifest
            ),
            score_q32=2**31,
            eligible=True,
            target_observation_id="obs:gold-2",
            predicted_observation_id="obs:gold-2",
        ),
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


def _calibrated_policy(
    active: ActiveCalibrationProfileV1,
    **overrides: object,
) -> RecallExecutionPolicyV1:
    values: dict[str, object] = {
        "max_records": 8192,
        "top_k": 32,
        "max_returned_payload_bytes": 262_144,
        "active_normalizer_id": active.normalizer_id,
        "active_feature_spec_id": active.feature_spec_id,
        "minimum_score_q32": active.minimum_score_q32,
        "minimum_margin_q32": active.minimum_margin_q32,
        "allow_approximate": True,
        "allow_incomplete": True,
    }
    values.update(overrides)
    return RecallExecutionPolicyV1(**values)  # type: ignore[arg-type]


def _clone_tightening(tightening: RecallPolicyTighteningV1) -> RecallPolicyTighteningV1:
    clone = object.__new__(RecallPolicyTighteningV1)
    for item in fields(tightening):
        object.__setattr__(clone, item.name, getattr(tightening, item.name))
    return clone


def _clone_active_profile(
    active: ActiveCalibrationProfileV1,
) -> ActiveCalibrationProfileV1:
    clone = object.__new__(ActiveCalibrationProfileV1)
    for item in fields(active):
        object.__setattr__(clone, item.name, getattr(active, item.name))
    return clone


def _recall_with_calibration(*args: object, **kwargs: object) -> object:
    return cast(Any, recall)(*args, **kwargs)


def _same_content_request(
    index: int,
    *,
    session_id: str = "session:recall",
    source_kind: SourceKind = SourceKind.MODEL,
    observed_at_ns: int = 1_725_000_000_000_000_000,
    content: CanonicalJsonValue | None = None,
    retrieval_text: str = "duplicate memory",
) -> ObservationRequestV1:
    body = content or CanonicalJsonValue.from_value({"text": "duplicate memory"})
    return _request(
        observation_id=f"obs:digest-{index:04d}",
        session_id=session_id,
        turn_id=f"turn:digest-{index:04d}",
        provenance=_provenance(
            source_kind=source_kind,
            observed_at_ns=observed_at_ns,
        ),
        content=body,
        retrieval_text=retrieval_text,
    )


def _ingest_requests(
    session: object,
    requests: tuple[ObservationRequestV1, ...],
) -> tuple[ObservationAcceptedV1, ...]:
    profile = baseline_boundary_profile()
    state = initialize_empty_sensorium_state(session, profile)  # type: ignore[arg-type]
    accepted: list[ObservationAcceptedV1] = []
    for request in requests:
        result = ingest_observation(session, request, profile, state)  # type: ignore[arg-type]
        assert type(result) is ObservationAcceptedV1
        accepted.append(result)
        state = result.next_state
    return tuple(accepted)


def _dense_feature_vector(
    *,
    default: int,
    overrides: dict[int, int] | None = None,
) -> RetrievalFeatureVectorV1:
    bins = [default] * FEATURE_DIMENSIONS
    for index, value in (overrides or {}).items():
        bins[index] = value
    return RetrievalFeatureVectorV1(
        feature_spec_id=active_feature_spec_id(),
        bins_i16be=struct.pack(f">{FEATURE_DIMENSIONS}h", *bins),
    )


def test_recall_filter_contract_accepts_sorted_unique_ids_and_source_kinds() -> None:
    filters = RecallFiltersV1(
        session_ids=("session:a", "session:z"),
        source_kinds=(SourceKind.MODEL, SourceKind.USER),
    )

    assert filters.session_ids == ("session:a", "session:z")
    assert filters.source_kinds == (SourceKind.MODEL, SourceKind.USER)


@pytest.mark.parametrize(
    ("factory", "field_name"),
    (
        (
            lambda: RecallFiltersV1(
                session_ids=tuple(f"session:{i:02d}" for i in range(33))
            ),
            "session_ids",
        ),
        (
            lambda: RecallFiltersV1(session_ids=("session:z", "session:a")),
            "session_ids",
        ),
        (
            lambda: RecallFiltersV1(session_ids=("session:a", "session:a")),
            "session_ids",
        ),
        (
            lambda: RecallFiltersV1(source_kinds=(SourceKind.USER, SourceKind.MODEL)),
            "source_kinds",
        ),
        (
            lambda: RecallFiltersV1(source_kinds=(SourceKind.USER, SourceKind.USER)),
            "source_kinds",
        ),
        (
            lambda: RecallFiltersV1(observed_at_ns_min=20, observed_at_ns_max=10),
            "observed_at_ns",
        ),
        (
            lambda: ContentDigestRecallQuery(content_digest="A" * 64),
            "content_digest",
        ),
        (
            lambda: RecallExecutionPolicyV1(
                max_records=8193,
                top_k=1,
                max_returned_payload_bytes=0,
                active_normalizer_id=active_normalizer_id(),
                active_feature_spec_id=active_feature_spec_id(),
                minimum_score_q32=0,
                minimum_margin_q32=0,
                allow_approximate=False,
                allow_incomplete=True,
            ),
            "max_records",
        ),
        (
            lambda: RecallExecutionPolicyV1(
                max_records=1,
                top_k=33,
                max_returned_payload_bytes=0,
                active_normalizer_id=active_normalizer_id(),
                active_feature_spec_id=active_feature_spec_id(),
                minimum_score_q32=0,
                minimum_margin_q32=0,
                allow_approximate=False,
                allow_incomplete=True,
            ),
            "top_k",
        ),
    ),
)
def test_scan_contracts_reject_out_of_bounds_values(
    factory: Callable[[], object],
    field_name: str,
) -> None:
    with pytest.raises(InputBoundaryError, match=field_name):
        factory()


def test_exhaustive_content_digest_recall_returns_no_scan_recollection_when_absent(
    tmp_path: Path,
) -> None:
    content_digest = derive_content_digest(
        CanonicalJsonValue.from_value({"text": "not stored"})
    )
    query = ContentDigestRecallQuery(content_digest=content_digest)

    with EncryptedLedger(
        tmp_path / "memory.sqlite3", StaticKeyProvider(MASTER_KEY)
    ) as ledger:
        with ledger.verified_session() as session:
            result = recall(session, query, policy=_policy())

    assert type(result) is NoScanRecollection
    assert result.content_digest == content_digest
    assert result.work.exhaustive is True
    assert result.work.records_scanned == 0


def test_exhaustive_content_digest_recall_returns_unique_exact_occurrence(
    tmp_path: Path,
) -> None:
    request = _same_content_request(1)
    query = ContentDigestRecallQuery(content_digest=derive_content_digest(request.content))

    with EncryptedLedger(
        tmp_path / "memory.sqlite3", StaticKeyProvider(MASTER_KEY)
    ) as ledger:
        with ledger.verified_session() as session:
            accepted = _ingest_requests(session, (request,))[0]
            result = recall(session, query, policy=_policy())

    assert type(result) is ExactRecollection
    assert result.basis is RecallBasis.CONTENT_DIGEST
    assert result.observation_id == request.observation_id
    assert result.sequence == accepted.next_state.last_applied_sequence
    assert result.content_digest == query.content_digest
    assert result.content == request.content


def test_exhaustive_content_digest_duplicates_return_ambiguous_without_content(
    tmp_path: Path,
) -> None:
    content = CanonicalJsonValue.from_value({"text": "duplicate memory"})
    first = _same_content_request(1, observed_at_ns=100, content=content)
    second = _same_content_request(2, observed_at_ns=200, content=content)
    query = ContentDigestRecallQuery(content_digest=derive_content_digest(content))

    with EncryptedLedger(
        tmp_path / "memory.sqlite3", StaticKeyProvider(MASTER_KEY)
    ) as ledger:
        with ledger.verified_session() as session:
            _ingest_requests(session, (first, second))
            result = recall(session, query, policy=_policy())

    assert type(result) is AmbiguousExactRecollection
    assert result.content_digest == query.content_digest
    assert result.exact_match_count == 2
    assert len(result.summaries) == 2
    assert all(not hasattr(summary, "content") for summary in result.summaries)
    assert tuple(summary.observation_id for summary in result.summaries) == (
        second.observation_id,
        first.observation_id,
    )


def test_content_digest_continuation_accumulates_duplicates_across_pages(
    tmp_path: Path,
) -> None:
    content = CanonicalJsonValue.from_value({"text": "duplicate memory"})
    first = _same_content_request(1, observed_at_ns=100, content=content)
    second = _same_content_request(2, observed_at_ns=200, content=content)
    query = ContentDigestRecallQuery(content_digest=derive_content_digest(content))

    with EncryptedLedger(
        tmp_path / "memory.sqlite3", StaticKeyProvider(MASTER_KEY)
    ) as ledger:
        with ledger.verified_session() as session:
            _ingest_requests(session, (first, second))
            first_page = recall(session, query, policy=_policy(max_records=1))
            assert type(first_page) is IncompleteRecollection
            assert first_page.work.exhaustive is False
            assert first_page.exact_match_count == 1

            result = recall(
                session,
                query,
                policy=_policy(max_records=1),
                continuation=first_page.continuation,
            )

    assert type(result) is AmbiguousExactRecollection
    assert result.exact_match_count == 2
    assert result.work.exhaustive is True
    assert tuple(summary.observation_id for summary in result.summaries) == (
        second.observation_id,
        first.observation_id,
    )


def test_zero_record_content_digest_page_cannot_claim_absence(
    tmp_path: Path,
) -> None:
    content = CanonicalJsonValue.from_value({"text": "duplicate memory"})
    request = _same_content_request(1, content=content)
    query = ContentDigestRecallQuery(content_digest=derive_content_digest(content))

    with EncryptedLedger(
        tmp_path / "memory.sqlite3", StaticKeyProvider(MASTER_KEY)
    ) as ledger:
        with ledger.verified_session() as session:
            _ingest_requests(session, (request,))
            result = recall(session, query, policy=_policy(max_records=0))

    assert type(result) is IncompleteRecollection
    assert result.work.exhaustive is False
    assert result.work.records_scanned == 0


def test_zero_record_content_digest_page_without_continuation_abstains(
    tmp_path: Path,
) -> None:
    content = CanonicalJsonValue.from_value({"text": "duplicate memory"})
    request = _same_content_request(1, content=content)
    query = ContentDigestRecallQuery(content_digest=derive_content_digest(content))

    with EncryptedLedger(
        tmp_path / "memory.sqlite3", StaticKeyProvider(MASTER_KEY)
    ) as ledger:
        with ledger.verified_session() as session:
            _ingest_requests(session, (request,))
            result = recall(
                session,
                query,
                policy=_policy(max_records=0, allow_incomplete=False),
            )

    assert type(result) is AbstainedRecollection
    assert result.reason is AbstainReason.WORK_BUDGET_EXHAUSTED
    assert result.continuation is None


def test_digest_duplicate_count_grows_while_summaries_remain_bounded(
    tmp_path: Path,
) -> None:
    content = CanonicalJsonValue.from_value({"text": "bounded duplicates"})
    requests = tuple(
        _same_content_request(
            index,
            observed_at_ns=100 + index,
            content=content,
        )
        for index in range(33)
    )
    query = ContentDigestRecallQuery(content_digest=derive_content_digest(content))

    with EncryptedLedger(
        tmp_path / "memory.sqlite3", StaticKeyProvider(MASTER_KEY)
    ) as ledger:
        with ledger.verified_session() as session:
            _ingest_requests(session, requests)
            result = recall(session, query, policy=_policy())

    assert type(result) is AmbiguousExactRecollection
    assert result.exact_match_count == 33
    assert len(result.summaries) == 32
    assert tuple(summary.observation_id for summary in result.summaries) == tuple(
        request.observation_id for request in reversed(requests[1:])
    )


def test_content_digest_filters_apply_before_uniqueness_decision(tmp_path: Path) -> None:
    content = CanonicalJsonValue.from_value({"text": "filtered duplicate"})
    included = _same_content_request(
        1,
        session_id="session:a",
        source_kind=SourceKind.USER,
        observed_at_ns=150,
        content=content,
    )
    excluded = _same_content_request(
        2,
        session_id="session:b",
        source_kind=SourceKind.MODEL,
        observed_at_ns=250,
        content=content,
    )
    query = ContentDigestRecallQuery(
        content_digest=derive_content_digest(content),
        filters=RecallFiltersV1(
            session_ids=("session:a",),
            source_kinds=(SourceKind.USER,),
            observed_at_ns_min=100,
            observed_at_ns_max=200,
        ),
    )

    with EncryptedLedger(
        tmp_path / "memory.sqlite3", StaticKeyProvider(MASTER_KEY)
    ) as ledger:
        with ledger.verified_session() as session:
            _ingest_requests(session, (included, excluded))
            result = recall(session, query, policy=_policy())

    assert type(result) is ExactRecollection
    assert result.observation_id == included.observation_id


def test_content_digest_continuation_rejects_query_policy_and_state_tampering(
    tmp_path: Path,
) -> None:
    content = CanonicalJsonValue.from_value({"text": "continuation binding"})
    request = _same_content_request(1, content=content)
    query = ContentDigestRecallQuery(content_digest=derive_content_digest(content))
    policy = _policy(max_records=0)

    with EncryptedLedger(
        tmp_path / "memory.sqlite3", StaticKeyProvider(MASTER_KEY)
    ) as ledger:
        with ledger.verified_session() as session:
            _ingest_requests(session, (request,))
            first_page = recall(session, query, policy=policy)
            assert type(first_page) is IncompleteRecollection

            changed_query = ContentDigestRecallQuery(content_digest="0" * 64)
            with pytest.raises(InputBoundaryError, match="query changed"):
                recall(
                    session,
                    changed_query,
                    policy=policy,
                    continuation=first_page.continuation,
                )
            with pytest.raises(InputBoundaryError, match="policy changed"):
                recall(
                    session,
                    query,
                    policy=_policy(max_records=1),
                    continuation=first_page.continuation,
                )

            object.__setattr__(first_page.continuation, "exact_match_count", 99)
            with pytest.raises(InputBoundaryError, match="authentication"):
                recall(
                    session,
                    query,
                    policy=policy,
                    continuation=first_page.continuation,
                )


def test_content_digest_continuation_rejects_changed_snapshot(tmp_path: Path) -> None:
    content = CanonicalJsonValue.from_value({"text": "snapshot binding"})
    request = _same_content_request(1, content=content)
    query = ContentDigestRecallQuery(content_digest=derive_content_digest(content))
    policy = _policy(max_records=0)

    with EncryptedLedger(
        tmp_path / "memory.sqlite3", StaticKeyProvider(MASTER_KEY)
    ) as ledger:
        with ledger.verified_session() as session:
            _ingest_requests(session, (request,))
            first_page = recall(session, query, policy=policy)
            assert type(first_page) is IncompleteRecollection
            session.append_once("unrelated:later", {"schema": "other.v1"})
            with pytest.raises(LedgerSnapshotChanged):
                recall(
                    session,
                    query,
                    policy=policy,
                    continuation=first_page.continuation,
                )


def test_scan_skips_unrelated_schema_but_rejects_malformed_claimed_observation(
    tmp_path: Path,
) -> None:
    query = ContentDigestRecallQuery(content_digest="0" * 64)
    with EncryptedLedger(
        tmp_path / "memory.sqlite3", StaticKeyProvider(MASTER_KEY)
    ) as ledger:
        with ledger.verified_session() as session:
            session.append_once("unrelated:one", {"schema": "other.v1"})
            skipped = recall(session, query, policy=_policy())
            assert type(skipped) is NoScanRecollection
            assert skipped.work.records_scanned == 1

            session.append_once("obs:malformed", {"schema": "aluclu.observation.v1"})
            with pytest.raises(LedgerIntegrityError, match="malformed"):
                recall(session, query, policy=_policy())
            appended = session.append_once("unrelated:after-malformed-scan", {"ok": True})

    assert appended.created is True


def test_unique_digest_direct_read_occurs_after_cursor_close_and_allows_mutation(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    request = _same_content_request(1)
    query = ContentDigestRecallQuery(content_digest=derive_content_digest(request.content))

    with EncryptedLedger(
        tmp_path / "memory.sqlite3", StaticKeyProvider(MASTER_KEY)
    ) as ledger:
        with ledger.verified_session() as session:
            _ingest_requests(session, (request,))
            original_read = type(session).read

            def guarded_read(active: object, event_id: str) -> object:
                assert not active._cursors  # type: ignore[attr-defined]
                return original_read(active, event_id)  # type: ignore[arg-type]

            monkeypatch.setattr(type(session), "read", guarded_read)
            result = recall(session, query, policy=_policy())
            appended = session.append_once("unrelated:after-recall", {"ok": True})

    assert type(result) is ExactRecollection
    assert appended.created is True


def test_text_recall_query_rejects_raw_text_over_4096_utf8_bytes() -> None:
    with pytest.raises(InputBoundaryError, match="4096"):
        TextRecallQuery(text="x" * 4097)


def test_text_recall_rejects_one_slot_policy_that_cannot_measure_margin(
    tmp_path: Path,
) -> None:
    query = TextRecallQuery(text="margin needs a runner-up")
    with EncryptedLedger(
        tmp_path / "memory.sqlite3", StaticKeyProvider(MASTER_KEY)
    ) as ledger:
        with ledger.verified_session() as session:
            with pytest.raises(InputBoundaryError, match="top_k"):
                recall(
                    session,
                    query,
                    policy=_policy(top_k=1, allow_approximate=True),
                )


def test_identical_features_with_different_content_remain_approximate(
    tmp_path: Path,
) -> None:
    request = _same_content_request(
        1,
        content=CanonicalJsonValue.from_value({"stored": "different bytes"}),
    )
    query = TextRecallQuery(text="duplicate memory")

    with EncryptedLedger(
        tmp_path / "memory.sqlite3", StaticKeyProvider(MASTER_KEY)
    ) as ledger:
        with ledger.verified_session() as session:
            _ingest_requests(session, (request,))
            result = recall(
                session,
                query,
                policy=_policy(
                    minimum_score_q32=MAX_Q32,
                    minimum_margin_q32=0,
                    allow_approximate=True,
                ),
            )

    assert type(result) is ApproximateCandidates
    assert result.margin_q32 == MAX_Q32
    assert len(result.candidates) == 1
    candidate = result.candidates[0]
    assert candidate.observation_id == request.observation_id
    assert candidate.score_q32 == MAX_Q32
    assert candidate.content == request.content
    assert candidate.content_omitted is False
    assert result.work.candidates_scored == 1
    assert result.work.candidates_returned == 1


def test_distinct_content_top_score_tie_returns_conflict_without_content(
    tmp_path: Path,
) -> None:
    first = _same_content_request(
        1,
        observed_at_ns=100,
        content=CanonicalJsonValue.from_value({"stored": "first"}),
    )
    second = _same_content_request(
        2,
        observed_at_ns=200,
        content=CanonicalJsonValue.from_value({"stored": "second"}),
    )
    query = TextRecallQuery(text="duplicate memory")

    with EncryptedLedger(
        tmp_path / "memory.sqlite3", StaticKeyProvider(MASTER_KEY)
    ) as ledger:
        with ledger.verified_session() as session:
            _ingest_requests(session, (first, second))
            result = recall(
                session,
                query,
                policy=_policy(
                    minimum_margin_q32=0,
                    allow_approximate=True,
                ),
            )

    assert type(result) is ConflictedRecollection
    assert result.margin_q32 == 0
    assert tuple(item.observation_id for item in result.candidates) == (
        second.observation_id,
        first.observation_id,
    )
    assert all(item.content is None for item in result.candidates)
    assert all(item.content_omitted is True for item in result.candidates)


def test_same_content_top_score_tie_does_not_create_false_conflict(
    tmp_path: Path,
) -> None:
    content = CanonicalJsonValue.from_value({"stored": "same"})
    first = _same_content_request(1, observed_at_ns=100, content=content)
    second = _same_content_request(2, observed_at_ns=200, content=content)
    query = TextRecallQuery(text="duplicate memory")

    with EncryptedLedger(
        tmp_path / "memory.sqlite3", StaticKeyProvider(MASTER_KEY)
    ) as ledger:
        with ledger.verified_session() as session:
            _ingest_requests(session, (first, second))
            result = recall(
                session,
                query,
                policy=_policy(
                    top_k=2,
                    minimum_margin_q32=0,
                    allow_approximate=True,
                ),
            )

    assert type(result) is ApproximateCandidates
    assert result.margin_q32 == MAX_Q32
    assert tuple(item.observation_id for item in result.candidates) == (
        second.observation_id,
        first.observation_id,
    )


def test_same_digest_duplicates_cannot_hide_distinct_digest_conflict(
    tmp_path: Path,
) -> None:
    duplicate_content = CanonicalJsonValue.from_value({"stored": "duplicate"})
    newest_duplicate = _same_content_request(
        1,
        observed_at_ns=300,
        content=duplicate_content,
    )
    older_duplicate = _same_content_request(
        2,
        observed_at_ns=200,
        content=duplicate_content,
    )
    distinct = _same_content_request(
        3,
        observed_at_ns=100,
        content=CanonicalJsonValue.from_value({"stored": "distinct"}),
    )
    query = TextRecallQuery(text="duplicate memory")

    with EncryptedLedger(
        tmp_path / "memory.sqlite3", StaticKeyProvider(MASTER_KEY)
    ) as ledger:
        with ledger.verified_session() as session:
            _ingest_requests(
                session,
                (distinct, older_duplicate, newest_duplicate),
            )
            one_shot = recall(
                session,
                query,
                policy=_policy(
                    top_k=2,
                    minimum_margin_q32=0,
                    allow_approximate=True,
                ),
            )
            page = recall(
                session,
                query,
                policy=_policy(
                    max_records=1,
                    top_k=2,
                    minimum_margin_q32=0,
                    allow_approximate=True,
                ),
            )
            while type(page) is IncompleteRecollection:
                page = recall(
                    session,
                    query,
                    policy=_policy(
                        max_records=1,
                        top_k=2,
                        minimum_margin_q32=0,
                        allow_approximate=True,
                    ),
                    continuation=page.continuation,
                )

    assert type(one_shot) is ConflictedRecollection
    assert type(page) is ConflictedRecollection
    assert one_shot.margin_q32 == 0
    assert page.margin_q32 == one_shot.margin_q32
    assert tuple(item.observation_id for item in one_shot.candidates) == (
        newest_duplicate.observation_id,
        distinct.observation_id,
    )
    assert page.candidates == one_shot.candidates


def test_text_continuation_preserves_top_candidates_across_pages(tmp_path: Path) -> None:
    content = CanonicalJsonValue.from_value({"stored": "same"})
    first = _same_content_request(1, observed_at_ns=100, content=content)
    second = _same_content_request(2, observed_at_ns=200, content=content)
    query = TextRecallQuery(text="duplicate memory")
    policy = _policy(
        max_records=1,
        top_k=2,
        minimum_margin_q32=0,
        allow_approximate=True,
    )

    with EncryptedLedger(
        tmp_path / "memory.sqlite3", StaticKeyProvider(MASTER_KEY)
    ) as ledger:
        with ledger.verified_session() as session:
            _ingest_requests(session, (first, second))
            first_page = recall(session, query, policy=policy)
            assert type(first_page) is IncompleteRecollection
            assert first_page.work.candidates_scored == 1
            result = recall(
                session,
                query,
                policy=policy,
                continuation=first_page.continuation,
            )

    assert type(result) is ApproximateCandidates
    assert result.work.exhaustive is True
    assert result.work.records_scanned == 2
    assert result.work.candidates_scored == 2
    assert tuple(item.observation_id for item in result.candidates) == (
        second.observation_id,
        first.observation_id,
    )


def test_text_scan_counts_content_without_retrieval_text_but_does_not_score_it(
    tmp_path: Path,
) -> None:
    request = _request(retrieval_text=None)
    query = TextRecallQuery(text="exact bytes")

    with EncryptedLedger(
        tmp_path / "memory.sqlite3", StaticKeyProvider(MASTER_KEY)
    ) as ledger:
        with ledger.verified_session() as session:
            _ingest_requests(session, (request,))
            result = recall(
                session,
                query,
                policy=_policy(allow_approximate=True),
            )

    assert type(result) is NoTextRecollection
    assert result.work.records_scanned == 1
    assert result.work.candidates_scored == 0
    assert result.work.exhaustive is True


def test_approximate_payload_over_budget_is_omitted_without_changing_rank(
    tmp_path: Path,
) -> None:
    request = _same_content_request(1)
    query = TextRecallQuery(text="duplicate memory")

    with EncryptedLedger(
        tmp_path / "memory.sqlite3", StaticKeyProvider(MASTER_KEY)
    ) as ledger:
        with ledger.verified_session() as session:
            _ingest_requests(session, (request,))
            result = recall(
                session,
                query,
                policy=_policy(
                    max_returned_payload_bytes=0,
                    minimum_margin_q32=0,
                    allow_approximate=True,
                ),
            )

    assert type(result) is ApproximateCandidates
    assert result.candidates[0].observation_id == request.observation_id
    assert result.candidates[0].content is None
    assert result.candidates[0].content_omitted is True
    assert result.work.candidates_returned == 1
    assert result.work.output_bytes == 0


def test_nonconflicted_personal_text_recall_reports_missing_profile(
    tmp_path: Path,
) -> None:
    request = _same_content_request(1)
    query = TextRecallQuery(text="duplicate memory")

    with EncryptedLedger(
        tmp_path / "memory.sqlite3", StaticKeyProvider(MASTER_KEY)
    ) as ledger:
        with ledger.verified_session() as session:
            _ingest_requests(session, (request,))
            result = recall(
                session,
                query,
                policy=_policy(
                    minimum_margin_q32=0,
                    allow_approximate=False,
                ),
            )

    assert type(result) is CalibrationProfileUnavailableV1
    assert result.reason is CalibrationProfileUnavailableReason.MISSING
    assert result.content_is_observation is False
    assert result.content_is_verified_fact is False


def test_text_ranking_uses_exact_cross_product_when_q32_scores_collide(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    query_vector = _dense_feature_vector(default=32767)
    closer_vector = _dense_feature_vector(default=32767, overrides={0: 32766})
    farther_vector = _dense_feature_vector(default=32767, overrides={0: 32748})
    vectors = {
        "query": query_vector,
        "closer": closer_vector,
        "farther": farther_vector,
    }

    def fake_encode(text: str, *, feature_spec_id: str) -> RetrievalFeatureVectorV1:
        assert feature_spec_id == active_feature_spec_id()
        return vectors[text]

    monkeypatch.setattr(
        "aluclu.cognition.recollection.encode_retrieval_text",
        fake_encode,
    )
    closer = _request(
        observation_id="obs:closer",
        turn_id="turn:closer",
        provenance=_provenance(observed_at_ns=100),
        content=CanonicalJsonValue.from_value({"stored": "closer"}),
        retrieval_text="closer",
    )
    farther = _request(
        observation_id="obs:farther",
        turn_id="turn:farther",
        provenance=_provenance(observed_at_ns=200),
        content=CanonicalJsonValue.from_value({"stored": "farther"}),
        retrieval_text="farther",
    )

    with EncryptedLedger(
        tmp_path / "memory.sqlite3", StaticKeyProvider(MASTER_KEY)
    ) as ledger:
        with ledger.verified_session() as session:
            _ingest_requests(session, (closer, farther))
            result = recall(
                session,
                TextRecallQuery(text="query"),
                policy=_policy(
                    top_k=2,
                    minimum_margin_q32=0,
                    allow_approximate=True,
                ),
            )

    assert type(result) is ConflictedRecollection
    assert result.margin_q32 == 0
    assert result.candidates[0].score_q32 == MAX_Q32 - 1
    assert result.candidates[1].score_q32 == MAX_Q32 - 1
    assert tuple(item.observation_id for item in result.candidates) == (
        closer.observation_id,
        farther.observation_id,
    )


def test_text_temporal_preference_precedes_newer_timestamp_on_similarity_tie(
    tmp_path: Path,
) -> None:
    content = CanonicalJsonValue.from_value({"stored": "same"})
    preferred = _same_content_request(1, observed_at_ns=100, content=content)
    newer = _same_content_request(2, observed_at_ns=200, content=content)
    query = TextRecallQuery(
        text="duplicate memory",
        filters=RecallFiltersV1(
            preferred_observed_at_ns_min=90,
            preferred_observed_at_ns_max=110,
        ),
    )

    with EncryptedLedger(
        tmp_path / "memory.sqlite3", StaticKeyProvider(MASTER_KEY)
    ) as ledger:
        with ledger.verified_session() as session:
            _ingest_requests(session, (preferred, newer))
            result = recall(
                session,
                query,
                policy=_policy(
                    top_k=2,
                    minimum_margin_q32=0,
                    allow_approximate=True,
                ),
            )

    assert type(result) is ApproximateCandidates
    assert tuple(item.observation_id for item in result.candidates) == (
        preferred.observation_id,
        newer.observation_id,
    )


def test_text_continuation_rejects_query_change_and_feature_vector_tamper(
    tmp_path: Path,
) -> None:
    first = _same_content_request(1)
    second = _same_content_request(2)
    query = TextRecallQuery(text="duplicate memory")
    policy = _policy(max_records=1, top_k=2, allow_approximate=True)

    with EncryptedLedger(
        tmp_path / "memory.sqlite3", StaticKeyProvider(MASTER_KEY)
    ) as ledger:
        with ledger.verified_session() as session:
            _ingest_requests(session, (first, second))
            first_page = recall(session, query, policy=policy)
            assert type(first_page) is IncompleteRecollection
            with pytest.raises(InputBoundaryError, match="query changed"):
                recall(
                    session,
                    TextRecallQuery(text="changed query"),
                    policy=policy,
                    continuation=first_page.continuation,
                )

            state = first_page.continuation.text_candidates[0]
            object.__setattr__(
                state,
                "feature_digest",
                "0" * 64,
            )
            with pytest.raises(InputBoundaryError, match="authentication failed"):
                recall(
                    session,
                    query,
                    policy=policy,
                    continuation=first_page.continuation,
                )


def test_text_one_shot_and_paged_recall_produce_identical_final_candidates(
    tmp_path: Path,
) -> None:
    requests = tuple(_same_content_request(index) for index in range(1, 4))
    query = TextRecallQuery(text="duplicate memory")
    one_shot_policy = _policy(
        top_k=3,
        minimum_margin_q32=0,
        allow_approximate=True,
    )
    paged_policy = _policy(
        max_records=1,
        top_k=3,
        minimum_margin_q32=0,
        allow_approximate=True,
    )

    with EncryptedLedger(
        tmp_path / "memory.sqlite3", StaticKeyProvider(MASTER_KEY)
    ) as ledger:
        with ledger.verified_session() as session:
            _ingest_requests(session, requests)
            one_shot = recall(session, query, policy=one_shot_policy)
            page = recall(session, query, policy=paged_policy)
            while type(page) is IncompleteRecollection:
                page = recall(
                    session,
                    query,
                    policy=paged_policy,
                    continuation=page.continuation,
                )

    assert type(one_shot) is ApproximateCandidates
    assert type(page) is ApproximateCandidates
    assert one_shot.candidates == page.candidates
    assert one_shot.margin_q32 == page.margin_q32
    assert one_shot.work.records_scanned == page.work.records_scanned
    assert one_shot.work.candidates_scored == page.work.candidates_scored


def test_text_top_k_remains_bounded_across_more_than_32_candidates(
    tmp_path: Path,
) -> None:
    content = CanonicalJsonValue.from_value({"stored": "same"})
    requests = tuple(
        _same_content_request(index, observed_at_ns=index, content=content)
        for index in range(1, 34)
    )
    query = TextRecallQuery(text="duplicate memory")

    with EncryptedLedger(
        tmp_path / "memory.sqlite3", StaticKeyProvider(MASTER_KEY)
    ) as ledger:
        with ledger.verified_session() as session:
            _ingest_requests(session, requests)
            result = recall(
                session,
                query,
                policy=_policy(
                    top_k=32,
                    minimum_margin_q32=0,
                    allow_approximate=True,
                ),
            )

    assert type(result) is ApproximateCandidates
    assert len(result.candidates) == 32
    assert result.work.candidates_scored == 33
    assert result.work.candidates_returned == 32
    assert tuple(item.observation_id for item in result.candidates) == tuple(
        request.observation_id for request in reversed(requests[1:])
    )


def test_text_filters_apply_before_scoring(tmp_path: Path) -> None:
    included = _same_content_request(1, session_id="session:a")
    excluded = _same_content_request(2, session_id="session:b")
    query = TextRecallQuery(
        text="duplicate memory",
        filters=RecallFiltersV1(session_ids=("session:a",)),
    )

    with EncryptedLedger(
        tmp_path / "memory.sqlite3", StaticKeyProvider(MASTER_KEY)
    ) as ledger:
        with ledger.verified_session() as session:
            _ingest_requests(session, (included, excluded))
            result = recall(
                session,
                query,
                policy=_policy(
                    minimum_margin_q32=0,
                    allow_approximate=True,
                ),
            )

    assert type(result) is ApproximateCandidates
    assert result.work.records_scanned == 2
    assert result.work.candidates_scored == 1
    assert tuple(item.observation_id for item in result.candidates) == (
        included.observation_id,
    )


def test_approximate_direct_reads_occur_after_cursor_close_and_allow_mutation(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    request = _same_content_request(1)
    query = TextRecallQuery(text="duplicate memory")

    with EncryptedLedger(
        tmp_path / "memory.sqlite3", StaticKeyProvider(MASTER_KEY)
    ) as ledger:
        with ledger.verified_session() as session:
            _ingest_requests(session, (request,))
            original_read = type(session).read

            def guarded_read(active: object, event_id: str) -> object:
                assert not active._cursors  # type: ignore[attr-defined]
                return original_read(active, event_id)  # type: ignore[arg-type]

            monkeypatch.setattr(type(session), "read", guarded_read)
            result = recall(
                session,
                query,
                policy=_policy(
                    minimum_margin_q32=0,
                    allow_approximate=True,
                ),
            )
            appended = session.append_once("unrelated:after-text-recall", {"ok": True})

    assert type(result) is ApproximateCandidates
    assert appended.created is True


def test_no_profile_text_recall_with_approximate_permission_remains_approximate(
    tmp_path: Path,
) -> None:
    request = _same_content_request(1)
    query = TextRecallQuery(text="duplicate memory")

    with EncryptedLedger(
        tmp_path / "memory.sqlite3", StaticKeyProvider(MASTER_KEY)
    ) as ledger:
        with ledger.verified_session() as session:
            _ingest_requests(session, (request,))
            result = recall(
                session,
                query,
                policy=_policy(
                    minimum_margin_q32=0,
                    allow_approximate=True,
                ),
            )

    assert type(result) is ApproximateCandidates
    assert result.candidates[0].observation_id == request.observation_id


def test_no_profile_text_recall_without_approximate_permission_reports_missing_profile_before_cursor(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    request = _same_content_request(1)
    query = TextRecallQuery(text="duplicate memory")

    with EncryptedLedger(
        tmp_path / "memory.sqlite3", StaticKeyProvider(MASTER_KEY)
    ) as ledger:
        with ledger.verified_session() as session:
            _ingest_requests(session, (request,))

            def forbidden_cursor(active: object, *args: object, **kwargs: object) -> object:
                raise AssertionError("missing calibrated profile must fail before cursor")

            monkeypatch.setattr(type(session), "cursor", forbidden_cursor)
            result = recall(
                session,
                query,
                policy=_policy(allow_approximate=False),
            )

    assert type(result) is CalibrationProfileUnavailableV1
    assert result.reason is CalibrationProfileUnavailableReason.MISSING


def test_calibrated_text_recall_rejects_partial_profile_pair_before_cursor(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    active = _active_calibration_profile()
    policy = _calibrated_policy(active)
    query = TextRecallQuery(text="duplicate memory")

    with EncryptedLedger(
        tmp_path / "memory.sqlite3", StaticKeyProvider(MASTER_KEY)
    ) as ledger:
        with ledger.verified_session() as session:

            def forbidden_cursor(active_session: object, *args: object, **kwargs: object) -> object:
                raise AssertionError("partial calibrated pair must fail before cursor")

            monkeypatch.setattr(type(session), "cursor", forbidden_cursor)
            with pytest.raises(InputBoundaryError, match="calibrat|policy_tightening"):
                _recall_with_calibration(
                    session,
                    query,
                    policy=policy,
                    active_profile=active,
                )


def test_calibrated_text_recall_rejects_forged_tightening_before_cursor(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    active = _active_calibration_profile()
    policy = _calibrated_policy(active)
    tightening = _clone_tightening(tighten_recall_policy(policy, active))
    query = TextRecallQuery(text="duplicate memory")

    with EncryptedLedger(
        tmp_path / "memory.sqlite3", StaticKeyProvider(MASTER_KEY)
    ) as ledger:
        with ledger.verified_session() as session:

            def forbidden_cursor(active_session: object, *args: object, **kwargs: object) -> object:
                raise AssertionError("forged calibrated pair must fail before cursor")

            monkeypatch.setattr(type(session), "cursor", forbidden_cursor)
            with pytest.raises(InputBoundaryError, match="policy tightening"):
                _recall_with_calibration(
                    session,
                    query,
                    policy=policy,
                    active_profile=active,
                    policy_tightening=tightening,
                )


def test_calibrated_text_recall_forced_abstention_happens_before_cursor(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    active = _active_calibration_profile()
    policy = _calibrated_policy(active)
    tightening = tighten_recall_policy(policy, active, force_abstain=True)
    query = TextRecallQuery(text="duplicate memory")

    with EncryptedLedger(
        tmp_path / "memory.sqlite3", StaticKeyProvider(MASTER_KEY)
    ) as ledger:
        with ledger.verified_session() as session:

            def forbidden_cursor(active_session: object, *args: object, **kwargs: object) -> object:
                raise AssertionError("forced calibrated abstention must not scan")

            monkeypatch.setattr(type(session), "cursor", forbidden_cursor)
            result = _recall_with_calibration(
                session,
                query,
                policy=policy,
                active_profile=active,
                policy_tightening=tightening,
            )

    assert type(result) is AbstainedRecollection
    assert result.reason.value == "policy_forced_abstention"
    assert result.work.records_scanned == 0


def test_no_scan_text_recall_paths_require_active_session(tmp_path: Path) -> None:
    active = _active_calibration_profile()
    policy = _calibrated_policy(active)
    tightening = tighten_recall_policy(policy, active, force_abstain=True)
    query = TextRecallQuery(text="duplicate memory")

    with EncryptedLedger(
        tmp_path / "memory.sqlite3", StaticKeyProvider(MASTER_KEY)
    ) as ledger:
        session = ledger.verified_session()
        session.close()

        with pytest.raises(LedgerLifecycleError, match="not active"):
            recall(
                session,
                query,
                policy=_policy(allow_approximate=False),
            )
        with pytest.raises(LedgerLifecycleError, match="not active"):
            _recall_with_calibration(
                session,
                query,
                policy=policy,
                active_profile=active,
                policy_tightening=tightening,
            )


def test_no_scan_text_recall_paths_reject_poisoned_session_before_work(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    active = _active_calibration_profile()
    policy = _calibrated_policy(active)
    tightening = tighten_recall_policy(policy, active, force_abstain=True)
    query = TextRecallQuery(text="duplicate memory")

    with EncryptedLedger(
        tmp_path / "memory.sqlite3", StaticKeyProvider(MASTER_KEY)
    ) as ledger:
        with ledger.verified_session() as session:
            session._poisoned = True

            def forbidden_cursor(
                active_session: object, *args: object, **kwargs: object
            ) -> object:
                raise AssertionError("poisoned session must fail before cursor")

            def forbidden_encode(*args: object, **kwargs: object) -> object:
                raise AssertionError("poisoned session must fail before text encoding")

            monkeypatch.setattr(type(session), "cursor", forbidden_cursor)
            monkeypatch.setattr(
                "aluclu.cognition.recollection.encode_retrieval_text",
                forbidden_encode,
            )

            with pytest.raises(LedgerLifecycleError, match="not active"):
                recall(
                    session,
                    query,
                    policy=_policy(allow_approximate=False),
                )
            with pytest.raises(LedgerLifecycleError, match="not active"):
                _recall_with_calibration(
                    session,
                    query,
                    policy=policy,
                    active_profile=active,
                    policy_tightening=tightening,
                )


def test_no_scan_text_recall_paths_reject_foreign_thread_session(
    tmp_path: Path,
) -> None:
    active = _active_calibration_profile()
    policy = _calibrated_policy(active)
    tightening = tighten_recall_policy(policy, active, force_abstain=True)
    query = TextRecallQuery(text="duplicate memory")

    with EncryptedLedger(
        tmp_path / "memory.sqlite3", StaticKeyProvider(MASTER_KEY)
    ) as ledger:
        with ledger.verified_session() as session:
            with ThreadPoolExecutor(max_workers=1) as pool:
                missing_profile = pool.submit(
                    recall,
                    session,
                    query,
                    policy=_policy(allow_approximate=False),
                )
                with pytest.raises(LedgerLifecycleError, match="another thread"):
                    missing_profile.result()

                forced_abstention = pool.submit(
                    _recall_with_calibration,
                    session,
                    query,
                    policy=policy,
                    active_profile=active,
                    policy_tightening=tightening,
                )
                with pytest.raises(LedgerLifecycleError, match="another thread"):
                    forced_abstention.result()


def test_calibrated_text_recall_returns_exact_evidence_for_same_digest_duplicates(
    tmp_path: Path,
) -> None:
    active = _active_calibration_profile()
    policy = _calibrated_policy(active, minimum_margin_q32=0)
    tightening = tighten_recall_policy(policy, active, minimum_margin_q32=0)
    content = CanonicalJsonValue.from_value({"stored": "same"})
    older = _same_content_request(1, observed_at_ns=100, content=content)
    newer = _same_content_request(2, observed_at_ns=200, content=content)
    query = TextRecallQuery(text="duplicate memory")

    with EncryptedLedger(
        tmp_path / "memory.sqlite3", StaticKeyProvider(MASTER_KEY)
    ) as ledger:
        with ledger.verified_session() as session:
            _ingest_requests(session, (older, newer))
            result = _recall_with_calibration(
                session,
                query,
                policy=policy,
                active_profile=active,
                policy_tightening=tightening,
            )

    assert type(result) is ExactRecollection
    assert result.basis is RecallBasis.CALIBRATED_TEXT_MATCH
    assert result.observation_id == newer.observation_id
    assert type(result.calibrated_evidence) is CalibratedTextMatchEvidenceV1
    assert result.calibrated_evidence.profile_digest == active.profile_digest
    assert (
        result.calibrated_evidence.effective_policy_digest
        == tightening.effective_policy_digest
    )
    assert result.calibrated_evidence.score_q32 >= active.minimum_score_q32
    assert (
        result.calibrated_evidence.margin_q32
        > tightening.minimum_margin_q32
    )


def test_calibrated_text_continuation_binds_effective_policy_and_profile(
    tmp_path: Path,
) -> None:
    active = _active_calibration_profile()
    policy = _calibrated_policy(active, max_records=1, minimum_margin_q32=0)
    tightening = tighten_recall_policy(
        policy,
        active,
        max_records=1,
        minimum_margin_q32=0,
    )
    content = CanonicalJsonValue.from_value({"stored": "same"})
    first = _same_content_request(1, observed_at_ns=100, content=content)
    second = _same_content_request(2, observed_at_ns=200, content=content)
    query = TextRecallQuery(text="duplicate memory")

    with EncryptedLedger(
        tmp_path / "memory.sqlite3", StaticKeyProvider(MASTER_KEY)
    ) as ledger:
        with ledger.verified_session() as session:
            _ingest_requests(session, (first, second))
            page = _recall_with_calibration(
                session,
                query,
                policy=policy,
                active_profile=active,
                policy_tightening=tightening,
            )
            assert type(page) is IncompleteRecollection
            assert page.continuation.policy_digest == tightening.effective_policy_digest
            assert page.continuation.profile_digest == active.profile_digest

            with pytest.raises(InputBoundaryError, match="policy|profile"):
                recall(session, query, policy=policy, continuation=page.continuation)

            result = _recall_with_calibration(
                session,
                query,
                policy=policy,
                active_profile=active,
                policy_tightening=tightening,
                continuation=page.continuation,
            )

    assert type(result) is ExactRecollection
    assert result.basis is RecallBasis.CALIBRATED_TEXT_MATCH
    assert result.observation_id == second.observation_id


def test_calibrated_text_recall_revalidates_distinct_runner_up_after_cursor_close(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    active = _active_calibration_profile()
    policy = _calibrated_policy(active, minimum_margin_q32=0)
    tightening = tighten_recall_policy(policy, active, minimum_margin_q32=0)
    winner = _same_content_request(
        1,
        observed_at_ns=200,
        content=CanonicalJsonValue.from_value({"stored": "winner"}),
    )
    runner_up = _same_content_request(
        2,
        observed_at_ns=100,
        content=CanonicalJsonValue.from_value({"stored": "runner-up"}),
        retrieval_text="duplicate memory runner up",
    )
    query = TextRecallQuery(text="duplicate memory")

    with EncryptedLedger(
        tmp_path / "memory.sqlite3", StaticKeyProvider(MASTER_KEY)
    ) as ledger:
        with ledger.verified_session() as session:
            _ingest_requests(session, (runner_up, winner))
            original_read = type(session).read
            reads: list[str] = []

            def guarded_read(active_session: object, event_id: str) -> object:
                assert not active_session._cursors  # type: ignore[attr-defined]
                reads.append(event_id)
                return original_read(active_session, event_id)  # type: ignore[arg-type]

            monkeypatch.setattr(type(session), "read", guarded_read)
            result = _recall_with_calibration(
                session,
                query,
                policy=policy,
                active_profile=active,
                policy_tightening=tightening,
            )

    assert type(result) is ExactRecollection
    assert result.basis is RecallBasis.CALIBRATED_TEXT_MATCH
    assert winner.observation_id in reads
    assert runner_up.observation_id in reads
    assert type(result.calibrated_evidence) is CalibratedTextMatchEvidenceV1
    assert result.calibrated_evidence.profile_digest == active.profile_digest
    assert (
        result.calibrated_evidence.effective_policy_digest
        == tightening.effective_policy_digest
    )


def test_calibrated_text_recall_rejects_forged_active_profile_before_cursor(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    active = _active_calibration_profile()
    policy = _calibrated_policy(active)
    tightening = tighten_recall_policy(policy, active)
    forged = _clone_active_profile(active)

    with EncryptedLedger(
        tmp_path / "memory.sqlite3", StaticKeyProvider(MASTER_KEY)
    ) as ledger:
        with ledger.verified_session() as session:

            def forbidden_cursor(*args: object, **kwargs: object) -> object:
                raise AssertionError("forged profile must fail before cursor")

            monkeypatch.setattr(type(session), "cursor", forbidden_cursor)
            with pytest.raises(InputBoundaryError, match="active calibration profile"):
                _recall_with_calibration(
                    session,
                    TextRecallQuery(text="duplicate memory"),
                    policy=policy,
                    active_profile=forged,
                    policy_tightening=tightening,
                )


def test_calibrated_text_recall_uses_tightened_work_and_incomplete_policy(
    tmp_path: Path,
) -> None:
    active = _active_calibration_profile()
    policy = _calibrated_policy(
        active,
        max_records=8,
        top_k=8,
        minimum_margin_q32=0,
        allow_incomplete=True,
    )
    tightening = tighten_recall_policy(
        policy,
        active,
        max_records=1,
        top_k=2,
        allow_incomplete=False,
    )

    with EncryptedLedger(
        tmp_path / "memory.sqlite3", StaticKeyProvider(MASTER_KEY)
    ) as ledger:
        with ledger.verified_session() as session:
            _ingest_requests(
                session,
                tuple(_same_content_request(index) for index in range(1, 4)),
            )
            result = _recall_with_calibration(
                session,
                TextRecallQuery(text="duplicate memory"),
                policy=policy,
                active_profile=active,
                policy_tightening=tightening,
            )

    assert type(result) is AbstainedRecollection
    assert result.reason is AbstainReason.WORK_BUDGET_EXHAUSTED
    assert result.work.records_scanned == 1
    assert result.work.exhaustive is False


def test_calibrated_continuation_retains_only_effective_top_k(
    tmp_path: Path,
) -> None:
    active = _active_calibration_profile()
    policy = _calibrated_policy(
        active,
        max_records=3,
        top_k=8,
        minimum_margin_q32=0,
    )
    tightening = tighten_recall_policy(
        policy,
        active,
        max_records=3,
        top_k=2,
    )

    with EncryptedLedger(
        tmp_path / "memory.sqlite3", StaticKeyProvider(MASTER_KEY)
    ) as ledger:
        with ledger.verified_session() as session:
            _ingest_requests(
                session,
                tuple(
                    _same_content_request(
                        index,
                        content=CanonicalJsonValue.from_value({"index": index}),
                    )
                    for index in range(1, 5)
                ),
            )
            page = _recall_with_calibration(
                session,
                TextRecallQuery(text="duplicate memory"),
                policy=policy,
                active_profile=active,
                policy_tightening=tightening,
            )

    assert type(page) is IncompleteRecollection
    assert page.work.records_scanned == 3
    assert len(page.continuation.text_candidates) == 2


def test_calibrated_text_recall_uses_effective_score_floor(
    tmp_path: Path,
) -> None:
    active = _active_calibration_profile()
    policy = _calibrated_policy(active, minimum_margin_q32=0)
    candidate_text = "duplicate memory extra"
    score = measure_feature_similarity(
        encode_retrieval_text(
            "duplicate memory", feature_spec_id=active_feature_spec_id()
        ),
        encode_retrieval_text(
            candidate_text, feature_spec_id=active_feature_spec_id()
        ),
    ).score_q32
    assert active.minimum_score_q32 <= score < MAX_Q32
    tightening = tighten_recall_policy(
        policy,
        active,
        minimum_score_q32=score + 1,
    )

    with EncryptedLedger(
        tmp_path / "memory.sqlite3", StaticKeyProvider(MASTER_KEY)
    ) as ledger:
        with ledger.verified_session() as session:
            _ingest_requests(
                session,
                (_same_content_request(1, retrieval_text=candidate_text),),
            )
            result = _recall_with_calibration(
                session,
                TextRecallQuery(text="duplicate memory"),
                policy=policy,
                active_profile=active,
                policy_tightening=tightening,
            )

    assert type(result) is NoTextRecollection
    assert result.work.candidates_scored == 1


def test_calibrated_text_recall_score_floor_is_inclusive(
    tmp_path: Path,
) -> None:
    active = _active_calibration_profile()
    policy = _calibrated_policy(active, minimum_margin_q32=0)
    tightening = tighten_recall_policy(
        policy,
        active,
        minimum_score_q32=MAX_Q32,
    )

    with EncryptedLedger(
        tmp_path / "memory.sqlite3", StaticKeyProvider(MASTER_KEY)
    ) as ledger:
        with ledger.verified_session() as session:
            request = _same_content_request(1)
            _ingest_requests(session, (request,))
            result = _recall_with_calibration(
                session,
                TextRecallQuery(text="duplicate memory"),
                policy=policy,
                active_profile=active,
                policy_tightening=tightening,
            )

    assert type(result) is ExactRecollection
    assert type(result.calibrated_evidence) is CalibratedTextMatchEvidenceV1
    assert result.calibrated_evidence.score_q32 == MAX_Q32


def test_calibrated_text_recall_margin_must_strictly_exceed_effective_floor(
    tmp_path: Path,
) -> None:
    active = _active_calibration_profile()
    policy = _calibrated_policy(active, minimum_margin_q32=0)
    query_text = "duplicate memory"
    runner_text = "duplicate memory extra"
    query_vector = encode_retrieval_text(
        query_text, feature_spec_id=active_feature_spec_id()
    )
    runner_score = measure_feature_similarity(
        query_vector,
        encode_retrieval_text(
            runner_text, feature_spec_id=active_feature_spec_id()
        ),
    ).score_q32
    margin = MAX_Q32 - runner_score
    assert 0 < margin < MAX_Q32
    at_floor = tighten_recall_policy(
        policy,
        active,
        minimum_margin_q32=margin,
    )
    below_floor = tighten_recall_policy(
        policy,
        active,
        minimum_margin_q32=margin - 1,
    )

    with EncryptedLedger(
        tmp_path / "memory.sqlite3", StaticKeyProvider(MASTER_KEY)
    ) as ledger:
        with ledger.verified_session() as session:
            _ingest_requests(
                session,
                (
                    _same_content_request(
                        1,
                        content=CanonicalJsonValue.from_value({"winner": True}),
                    ),
                    _same_content_request(
                        2,
                        content=CanonicalJsonValue.from_value({"runner": True}),
                        retrieval_text=runner_text,
                    ),
                ),
            )
            conflicted = _recall_with_calibration(
                session,
                TextRecallQuery(text=query_text),
                policy=policy,
                active_profile=active,
                policy_tightening=at_floor,
            )
            exact = _recall_with_calibration(
                session,
                TextRecallQuery(text=query_text),
                policy=policy,
                active_profile=active,
                policy_tightening=below_floor,
            )

    assert type(conflicted) is ConflictedRecollection
    assert conflicted.margin_q32 == margin
    assert type(exact) is ExactRecollection
    assert type(exact.calibrated_evidence) is CalibratedTextMatchEvidenceV1
    assert exact.calibrated_evidence.margin_q32 == margin


def test_calibrated_exact_ignores_approximate_return_permission(
    tmp_path: Path,
) -> None:
    active = _active_calibration_profile()
    policy = _calibrated_policy(
        active,
        minimum_margin_q32=0,
        allow_approximate=False,
    )
    tightening = tighten_recall_policy(policy, active)

    with EncryptedLedger(
        tmp_path / "memory.sqlite3", StaticKeyProvider(MASTER_KEY)
    ) as ledger:
        with ledger.verified_session() as session:
            request = _same_content_request(1)
            _ingest_requests(session, (request,))
            result = _recall_with_calibration(
                session,
                TextRecallQuery(text="duplicate memory"),
                policy=policy,
                active_profile=active,
                policy_tightening=tightening,
            )

    assert type(result) is ExactRecollection
    assert result.basis is RecallBasis.CALIBRATED_TEXT_MATCH


def test_calibrated_exact_uses_effective_output_budget(
    tmp_path: Path,
) -> None:
    active = _active_calibration_profile()
    policy = _calibrated_policy(active, minimum_margin_q32=0)
    tightening = tighten_recall_policy(
        policy,
        active,
        max_returned_payload_bytes=0,
    )

    with EncryptedLedger(
        tmp_path / "memory.sqlite3", StaticKeyProvider(MASTER_KEY)
    ) as ledger:
        with ledger.verified_session() as session:
            _ingest_requests(session, (_same_content_request(1),))
            result = _recall_with_calibration(
                session,
                TextRecallQuery(text="duplicate memory"),
                policy=policy,
                active_profile=active,
                policy_tightening=tightening,
            )

    assert type(result) is AbstainedRecollection
    assert result.reason is AbstainReason.PAYLOAD_BUDGET_EXCEEDED
    assert result.work.output_bytes == 0
    assert result.work.candidates_returned == 0


def test_calibrated_text_continuation_rejects_legacy_to_calibrated_resume(
    tmp_path: Path,
) -> None:
    active = _active_calibration_profile()
    policy = _calibrated_policy(
        active,
        max_records=1,
        minimum_margin_q32=0,
        allow_approximate=True,
    )
    tightening = tighten_recall_policy(policy, active)

    with EncryptedLedger(
        tmp_path / "memory.sqlite3", StaticKeyProvider(MASTER_KEY)
    ) as ledger:
        with ledger.verified_session() as session:
            _ingest_requests(
                session,
                (_same_content_request(1), _same_content_request(2)),
            )
            legacy_page = recall(
                session,
                TextRecallQuery(text="duplicate memory"),
                policy=policy,
            )
            assert type(legacy_page) is IncompleteRecollection
            with pytest.raises(InputBoundaryError, match="policy|profile"):
                _recall_with_calibration(
                    session,
                    TextRecallQuery(text="duplicate memory"),
                    policy=policy,
                    active_profile=active,
                    policy_tightening=tightening,
                    continuation=legacy_page.continuation,
                )


def test_forced_calibrated_recall_rejects_supplied_continuation(
    tmp_path: Path,
) -> None:
    active = _active_calibration_profile()
    policy = _calibrated_policy(active, max_records=1, minimum_margin_q32=0)
    live = tighten_recall_policy(policy, active)
    forced = tighten_recall_policy(policy, active, force_abstain=True)

    with EncryptedLedger(
        tmp_path / "memory.sqlite3", StaticKeyProvider(MASTER_KEY)
    ) as ledger:
        with ledger.verified_session() as session:
            _ingest_requests(
                session,
                (_same_content_request(1), _same_content_request(2)),
            )
            page = _recall_with_calibration(
                session,
                TextRecallQuery(text="duplicate memory"),
                policy=policy,
                active_profile=active,
                policy_tightening=live,
            )
            assert type(page) is IncompleteRecollection
            with pytest.raises(InputBoundaryError, match="policy|forced"):
                _recall_with_calibration(
                    session,
                    TextRecallQuery(text="duplicate memory"),
                    policy=policy,
                    active_profile=active,
                    policy_tightening=forced,
                    continuation=page.continuation,
                )


def test_calibration_state_is_rejected_for_nontext_recall_queries(
    tmp_path: Path,
) -> None:
    active = _active_calibration_profile()
    policy = _calibrated_policy(active)
    tightening = tighten_recall_policy(policy, active)

    with EncryptedLedger(
        tmp_path / "memory.sqlite3", StaticKeyProvider(MASTER_KEY)
    ) as ledger:
        with ledger.verified_session() as session:
            with pytest.raises(InputBoundaryError, match="direct-ID"):
                _recall_with_calibration(
                    session,
                    EventIdRecallQuery(observation_id="obs:missing"),
                    active_profile=active,
                    policy_tightening=tightening,
                )
            with pytest.raises(InputBoundaryError, match="content-digest"):
                _recall_with_calibration(
                    session,
                    ContentDigestRecallQuery(content_digest="0" * 64),
                    policy=policy,
                    active_profile=active,
                    policy_tightening=tightening,
                )


def test_calibrated_text_recall_rejects_runner_up_change_after_scan(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    active = _active_calibration_profile()
    policy = _calibrated_policy(active, minimum_margin_q32=0)
    tightening = tighten_recall_policy(policy, active)
    runner = _same_content_request(
        2,
        content=CanonicalJsonValue.from_value({"runner": True}),
        retrieval_text="duplicate memory extra",
    )

    with EncryptedLedger(
        tmp_path / "memory.sqlite3", StaticKeyProvider(MASTER_KEY)
    ) as ledger:
        with ledger.verified_session() as session:
            _ingest_requests(
                session,
                (
                    _same_content_request(
                        1,
                        content=CanonicalJsonValue.from_value({"winner": True}),
                    ),
                    runner,
                ),
            )
            original_read = type(session).read

            def changed_runner(active_session: object, event_id: str) -> object:
                if event_id == runner.observation_id:
                    return None
                return original_read(active_session, event_id)  # type: ignore[arg-type]

            monkeypatch.setattr(type(session), "read", changed_runner)
            with pytest.raises(LedgerIntegrityError, match="changed after scan"):
                _recall_with_calibration(
                    session,
                    TextRecallQuery(text="duplicate memory"),
                    policy=policy,
                    active_profile=active,
                    policy_tightening=tightening,
                )


def test_calibrated_policy_is_frozen_before_cursor_open(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    active = _active_calibration_profile()
    policy = _calibrated_policy(
        active,
        max_records=8,
        minimum_margin_q32=0,
        allow_incomplete=True,
    )
    tightening = tighten_recall_policy(
        policy,
        active,
        max_records=1,
        allow_incomplete=False,
    )

    with EncryptedLedger(
        tmp_path / "memory.sqlite3", StaticKeyProvider(MASTER_KEY)
    ) as ledger:
        with ledger.verified_session() as session:
            _ingest_requests(
                session,
                (_same_content_request(1), _same_content_request(2)),
            )
            original_cursor = type(session).cursor

            def mutating_cursor(
                active_session: object, *args: object, **kwargs: object
            ) -> object:
                object.__setattr__(tightening, "max_records", 8)
                object.__setattr__(tightening, "allow_incomplete", True)
                return original_cursor(
                    active_session, *args, **kwargs  # type: ignore[arg-type]
                )

            monkeypatch.setattr(type(session), "cursor", mutating_cursor)
            result = _recall_with_calibration(
                session,
                TextRecallQuery(text="duplicate memory"),
                policy=policy,
                active_profile=active,
                policy_tightening=tightening,
            )

    assert type(result) is AbstainedRecollection
    assert result.reason is AbstainReason.WORK_BUDGET_EXHAUSTED
    assert result.work.records_scanned == 1


def test_calibrated_conflict_precedes_approximate_permission(
    tmp_path: Path,
) -> None:
    active = _active_calibration_profile()
    policy = _calibrated_policy(
        active,
        minimum_margin_q32=0,
        allow_approximate=False,
    )
    tightening = tighten_recall_policy(policy, active)

    with EncryptedLedger(
        tmp_path / "memory.sqlite3", StaticKeyProvider(MASTER_KEY)
    ) as ledger:
        with ledger.verified_session() as session:
            _ingest_requests(
                session,
                (
                    _same_content_request(
                        1,
                        content=CanonicalJsonValue.from_value({"value": "left"}),
                    ),
                    _same_content_request(
                        2,
                        content=CanonicalJsonValue.from_value({"value": "right"}),
                    ),
                ),
            )
            result = _recall_with_calibration(
                session,
                TextRecallQuery(text="duplicate memory"),
                policy=policy,
                active_profile=active,
                policy_tightening=tightening,
            )

    assert type(result) is ConflictedRecollection
    assert result.margin_q32 == 0


@pytest.mark.parametrize("allow_approximate", (True, False))
def test_single_calibrated_candidate_at_margin_floor_is_not_exact(
    tmp_path: Path,
    allow_approximate: bool,
) -> None:
    query_text = "duplicate memory"
    candidate_text = "duplicate memory extra"
    score = measure_feature_similarity(
        encode_retrieval_text(
            query_text, feature_spec_id=active_feature_spec_id()
        ),
        encode_retrieval_text(
            candidate_text, feature_spec_id=active_feature_spec_id()
        ),
    ).score_q32
    active = _active_calibration_profile(minimum_margin_q32=score)
    policy = _calibrated_policy(
        active,
        allow_approximate=allow_approximate,
    )
    tightening = tighten_recall_policy(policy, active)

    with EncryptedLedger(
        tmp_path / "memory.sqlite3", StaticKeyProvider(MASTER_KEY)
    ) as ledger:
        with ledger.verified_session() as session:
            request = _same_content_request(1, retrieval_text=candidate_text)
            _ingest_requests(session, (request,))
            result = _recall_with_calibration(
                session,
                TextRecallQuery(text=query_text),
                policy=policy,
                active_profile=active,
                policy_tightening=tightening,
            )

    if allow_approximate:
        assert type(result) is ApproximateCandidates
        assert result.margin_q32 == score
        assert result.candidates[0].observation_id == request.observation_id
    else:
        assert type(result) is AbstainedRecollection
        assert result.reason is AbstainReason.APPROXIMATE_DISABLED
        assert result.work.exhaustive is True


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


def test_direct_id_recall_rejects_mismatched_post_core_observation_id(
    tmp_path: Path,
) -> None:
    profile = baseline_boundary_profile()
    request = _request(observation_id="obs:recall-position-mismatch")

    with EncryptedLedger(
        tmp_path / "memory.sqlite3", StaticKeyProvider(MASTER_KEY)
    ) as ledger:
        with ledger.verified_session() as session:
            state = initialize_empty_sensorium_state(session, profile)
            assert type(state) is SensoriumStateV1
            canonical = canonicalize_observation(request, profile, state.core)
            malformed = build_canonical_observation(
                request=request,
                boundary_decision=canonical.boundary_decision,
                pre_core_state_digest=derive_sensorium_core_state_digest(state.core),
                post_core_state=replace(
                    canonical.post_core_state,
                    last_observation_id="obs:recall-position-different",
                ),
                pre_append_head_sequence=0,
                pre_append_head_hash="0" * 64,
                boundary_profile_id=profile.profile_id,
            )
            session.append_once(
                request.observation_id,
                canonical_observation_to_json_value(malformed),
            )

            result = recall(
                session,
                EventIdRecallQuery(observation_id=request.observation_id),
            )

    assert type(result) is NoRecollection
