from __future__ import annotations

import time
import tracemalloc
from collections.abc import Callable
from dataclasses import fields
from functools import cmp_to_key
from pathlib import Path
from typing import TypeVar

import aluclu.cognition.recollection as recollection_module
from aluclu.cognition import (
    ApproximateCandidates,
    CanonicalJsonValue,
    ConflictedRecollection,
    EncryptedLedger,
    FeatureSimilarityV1,
    IncompleteRecollection,
    ObservationRequestV1,
    ProvenanceV1,
    RecallExecutionPolicyV1,
    SourceKind,
    StaticKeyProvider,
    TextRecallQuery,
    active_feature_spec_id,
    active_normalizer_id,
    canonical_json_bytes,
    encode_retrieval_text,
    encode_sensorium_state,
    measure_feature_similarity,
    recall,
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
_CONTINUATION_STATE_LIMIT_BYTES = 64 * 1_024
_RECALL_TRACED_MEMORY_LIMIT_BYTES = 64 * 1_024 * 1_024
_T = TypeVar("_T")


def _request(
    index: int,
    *,
    retrieval_text: str | None = None,
    observed_at_ns: int | None = None,
) -> ObservationRequestV1:
    return ObservationRequestV1(
        observation_id=f"obs:t23-scale-{index:04d}",
        session_id="session:t23-scale",
        turn_id=f"turn:t23-scale-{index:04d}",
        provenance=ProvenanceV1(
            source_kind=SourceKind.USER,
            source_instance_id="user:local",
            origin_id=f"fixture:t23-scale-{index:04d}",
            observed_at_ns=(
                1_725_000_000_000_000_000 + index
                if observed_at_ns is None
                else observed_at_ns
            ),
            parent_observation_ids=(),
            capture_method="test",
            capture_version="1.0.0",
        ),
        content=CanonicalJsonValue.from_value({"index": index}),
        retrieval_text=(
            f"scale observation {index}"
            if retrieval_text is None
            else retrieval_text
        ),
        topic_key="topic:scale",
        goal_ids=(),
        participant_ids=("participant:user",),
        tool_invocation_id=None,
        tool_phase=None,
        force_boundary=False,
    )


def _recall_policy(*, max_records: int, top_k: int = 32) -> RecallExecutionPolicyV1:
    return RecallExecutionPolicyV1(
        max_records=max_records,
        top_k=top_k,
        max_returned_payload_bytes=262_144,
        active_normalizer_id=active_normalizer_id(),
        active_feature_spec_id=active_feature_spec_id(),
        minimum_score_q32=0,
        minimum_margin_q32=0,
        allow_approximate=True,
        allow_incomplete=True,
    )


def _measure_call(call: Callable[[], _T]) -> tuple[_T, float, int]:
    tracemalloc.start()
    try:
        started = time.perf_counter()
        result = call()
        elapsed_seconds = time.perf_counter() - started
        peak_bytes = tracemalloc.get_traced_memory()[1]
    finally:
        tracemalloc.stop()
    return result, elapsed_seconds, peak_bytes


def _reference_similarity_compare(
    left: tuple[int, ObservationRequestV1, FeatureSimilarityV1],
    right: tuple[int, ObservationRequestV1, FeatureSimilarityV1],
) -> int:
    left_similarity = left[2]
    right_similarity = right[2]
    left_denominator = (
        left_similarity.query_squared_norm * left_similarity.candidate_squared_norm
    )
    right_denominator = (
        right_similarity.query_squared_norm * right_similarity.candidate_squared_norm
    )
    left_positive = left_similarity.dot_product > 0 and left_denominator > 0
    right_positive = right_similarity.dot_product > 0 and right_denominator > 0
    if left_positive != right_positive:
        return -1 if left_positive else 1
    if left_positive:
        left_cross = (
            left_similarity.dot_product
            * left_similarity.dot_product
            * right_denominator
        )
        right_cross = (
            right_similarity.dot_product
            * right_similarity.dot_product
            * left_denominator
        )
        if left_cross != right_cross:
            return -1 if left_cross > right_cross else 1

    left_request = left[1]
    right_request = right[1]
    left_time = left_request.provenance.observed_at_ns
    right_time = right_request.provenance.observed_at_ns
    if left_time != right_time:
        return -1 if left_time > right_time else 1
    if left[0] != right[0]:
        return -1 if left[0] > right[0] else 1
    return (
        (left_request.observation_id > right_request.observation_id)
        - (left_request.observation_id < right_request.observation_id)
    )


def test_streaming_recall_matches_independent_exhaustive_reference(
    tmp_path: Path,
) -> None:
    requests = tuple(
        _request(
            index,
            retrieval_text=(
                "independent exhaustive target"
                if index == 7
                else f"independent candidate {index}"
            ),
            observed_at_ns=1_725_000_000_000_001_000 + index,
        )
        for index in range(1, 13)
    )
    query = TextRecallQuery(text="independent exhaustive target")
    query_vector = encode_retrieval_text(
        query.text,
        feature_spec_id=active_feature_spec_id(),
    )
    reference = [
        (
            sequence,
            request,
            measure_feature_similarity(
                query_vector,
                encode_retrieval_text(
                    request.retrieval_text or "",
                    feature_spec_id=active_feature_spec_id(),
                ),
            ),
        )
        for sequence, request in enumerate(requests, start=1)
    ]
    reference.sort(key=cmp_to_key(_reference_similarity_compare))
    expected_ids = tuple(item[1].observation_id for item in reference[:5])

    profile = baseline_boundary_profile()
    with EncryptedLedger(
        tmp_path / "reference.sqlite3", StaticKeyProvider(MASTER_KEY)
    ) as ledger:
        with ledger.verified_session() as session:
            state = initialize_empty_sensorium_state(session, profile)
            assert type(state) is SensoriumStateV1
            for request in requests:
                accepted = ingest_observation(session, request, profile, state)
                assert type(accepted) is ObservationAcceptedV1
                state = accepted.next_state

            one_shot = recall(
                session,
                query,
                policy=_recall_policy(max_records=12, top_k=5),
            )
            paged = recall(
                session,
                query,
                policy=_recall_policy(max_records=3, top_k=5),
            )
            while type(paged) is IncompleteRecollection:
                paged = recall(
                    session,
                    query,
                    policy=_recall_policy(max_records=3, top_k=5),
                    continuation=paged.continuation,
                )

    assert type(one_shot) is ApproximateCandidates
    assert type(paged) is ApproximateCandidates
    assert tuple(item.observation_id for item in one_shot.candidates) == expected_ids
    assert paged == one_shot


def test_8192_observation_replay_keeps_completed_state_bounded(
    tmp_path: Path,
    record_testsuite_property: Callable[[str, object], None],
) -> None:
    profile = baseline_boundary_profile()
    query = TextRecallQuery(text="scale observation 8192")
    result_2048: ApproximateCandidates | ConflictedRecollection | None = None
    elapsed_2048 = 0.0
    peak_2048 = 0
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
                if index == 2_048:
                    measured, elapsed_2048, peak_2048 = _measure_call(
                        lambda: recall(
                            session,
                            query,
                            policy=_recall_policy(max_records=2_048),
                        )
                    )
                    assert isinstance(
                        measured,
                        (ApproximateCandidates, ConflictedRecollection),
                    )
                    result_2048 = measured

            completed = replay_sensorium_page(
                session,
                SensoriumReplayPagePolicyV1(max_records=8_192),
                profile,
            )

            one_shot_8192, elapsed_8192, peak_8192 = _measure_call(
                lambda: recall(
                    session,
                    query,
                    policy=_recall_policy(max_records=8_192),
                )
            )
            assert isinstance(
                one_shot_8192,
                (ApproximateCandidates, ConflictedRecollection),
            )

            paged_policy = _recall_policy(max_records=2_048)
            continuation_sizes: list[int] = []

            def paged_recall() -> ApproximateCandidates | ConflictedRecollection:
                page = recall(session, query, policy=paged_policy)
                while type(page) is IncompleteRecollection:
                    continuation = page.continuation
                    assert len(continuation.text_candidates) <= paged_policy.top_k
                    assert len(continuation.conflict_candidates) <= 2
                    for candidate in (
                        *continuation.text_candidates,
                        *continuation.conflict_candidates,
                    ):
                        field_names = {item.name for item in fields(type(candidate))}
                        assert "feature_digest" in field_names
                        assert all(
                            "vector" not in field_name and "bins" not in field_name
                            for field_name in field_names
                        )
                    authenticated_state = canonical_json_bytes(
                        recollection_module._continuation_payload(continuation)
                    )
                    assert b"feature_vector" not in authenticated_state
                    assert b"bins_i16be" not in authenticated_state
                    continuation_sizes.append(len(authenticated_state))
                    page = recall(
                        session,
                        query,
                        policy=paged_policy,
                        continuation=continuation,
                    )
                assert isinstance(page, (ApproximateCandidates, ConflictedRecollection))
                return page

            paged_8192, paged_elapsed_8192, paged_peak_8192 = _measure_call(
                paged_recall
            )

    assert type(completed) is SensoriumReplayCompleteV1
    assert completed.state == state
    assert completed.state.core.last_observation_sequence == 8_192
    assert completed.page_work.records_examined == 8_192
    assert completed.page_work.observations_applied == 8_192
    assert len(encode_sensorium_state(completed.state)) <= 4_096
    assert result_2048 is not None
    assert result_2048.work.records_scanned == 2_048
    assert result_2048.work.candidates_scored == 2_048
    assert one_shot_8192.work.records_scanned == 8_192
    assert one_shot_8192.work.candidates_scored == 8_192
    assert one_shot_8192.work.records_scanned == 4 * result_2048.work.records_scanned
    assert (
        one_shot_8192.work.candidates_scored
        == 4 * result_2048.work.candidates_scored
    )
    assert paged_8192 == one_shot_8192
    assert len(continuation_sizes) == 3
    assert max(continuation_sizes) <= _CONTINUATION_STATE_LIMIT_BYTES
    assert peak_2048 <= _RECALL_TRACED_MEMORY_LIMIT_BYTES
    assert peak_8192 <= _RECALL_TRACED_MEMORY_LIMIT_BYTES
    assert paged_peak_8192 <= _RECALL_TRACED_MEMORY_LIMIT_BYTES

    record_testsuite_property("recall_2048_elapsed_seconds", elapsed_2048)
    record_testsuite_property("recall_2048_peak_traced_bytes", peak_2048)
    record_testsuite_property("recall_8192_one_shot_elapsed_seconds", elapsed_8192)
    record_testsuite_property("recall_8192_one_shot_peak_traced_bytes", peak_8192)
    record_testsuite_property("recall_8192_paged_elapsed_seconds", paged_elapsed_8192)
    record_testsuite_property("recall_8192_paged_peak_traced_bytes", paged_peak_8192)
    record_testsuite_property(
        "continuation_authenticated_state_bytes", continuation_sizes
    )
