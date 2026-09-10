from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

import pytest

from aluclu.cognition import (
    CanonicalJsonValue,
    CanonicalObservationV1,
    EncryptedLedger,
    InputBoundaryError,
    LedgerIntegrityError,
    LedgerSnapshotChanged,
    ObservationRequestV1,
    ProvenanceV1,
    SourceKind,
    StaticKeyProvider,
    active_feature_spec_id,
    active_normalizer_id,
    build_canonical_observation,
    canonical_observation_to_json_value,
    derive_content_digest,
    derive_sensorium_core_state_digest,
)
from aluclu.cognition.recollection import (
    AbstainedRecollection,
    AbstainReason,
    AmbiguousExactRecollection,
    ContentDigestRecallQuery,
    EventIdRecallQuery,
    ExactRecollection,
    IncompleteRecollection,
    NoRecollection,
    NoScanRecollection,
    RecallBasis,
    RecallExecutionPolicyV1,
    RecallFiltersV1,
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
MAX_Q32 = 1 << 32


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
    allow_incomplete: bool = True,
) -> RecallExecutionPolicyV1:
    return RecallExecutionPolicyV1(
        max_records=max_records,
        top_k=top_k,
        max_returned_payload_bytes=max_returned_payload_bytes,
        active_normalizer_id=active_normalizer_id(),
        active_feature_spec_id=active_feature_spec_id(),
        minimum_score_q32=0,
        minimum_margin_q32=MAX_Q32,
        allow_approximate=False,
        allow_incomplete=allow_incomplete,
    )


def _same_content_request(
    index: int,
    *,
    session_id: str = "session:recall",
    source_kind: SourceKind = SourceKind.MODEL,
    observed_at_ns: int = 1_725_000_000_000_000_000,
    content: CanonicalJsonValue | None = None,
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
        retrieval_text="duplicate memory",
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
