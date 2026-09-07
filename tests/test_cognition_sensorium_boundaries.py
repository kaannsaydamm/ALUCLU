from __future__ import annotations

from dataclasses import replace
from pathlib import Path

from aluclu.cognition import (
    CanonicalJsonValue,
    EncryptedLedger,
    EpisodeBoundaryReason,
    ObservationRequestV1,
    ProvenanceV1,
    SensoriumCoreStateV1,
    SourceKind,
    StaticKeyProvider,
    encode_observation_request,
)
from aluclu.cognition.sensorium import (
    BoundaryProfileV1,
    IngestRejectionCode,
    IngestStatus,
    ObservationAcceptedV1,
    ObservationRejectedV1,
    SensoriumStateV1,
    baseline_boundary_profile,
    canonicalize_observation,
    ingest_observation,
    initialize_empty_sensorium_state,
)

MASTER_KEY = b"m" * 32
BASE_NS = 1_725_000_000_000_000_000


def _request(index: int, **overrides: object) -> ObservationRequestV1:
    values: dict[str, object] = {
        "observation_id": f"obs:t23-{index:04d}",
        "session_id": "session:task2",
        "turn_id": f"turn:t23-{index:04d}",
        "provenance": ProvenanceV1(
            source_kind=SourceKind.USER,
            source_instance_id="user:local",
            origin_id=f"fixture:t23-{index:04d}",
            observed_at_ns=BASE_NS + index,
            parent_observation_ids=(),
            capture_method="test",
            capture_version="1.0.0",
        ),
        "content": CanonicalJsonValue.from_value({"index": index}),
        "retrieval_text": f"task 2.3 observation {index}",
        "topic_key": "topic:test",
        "goal_ids": ("goal:test",),
        "participant_ids": ("participant:user",),
        "tool_invocation_id": None,
        "tool_phase": None,
        "force_boundary": False,
    }
    values.update(overrides)
    return ObservationRequestV1(**values)  # type: ignore[arg-type]


def _initial_core(profile: BoundaryProfileV1) -> SensoriumCoreStateV1:
    return SensoriumCoreStateV1(
        boundary_profile_id=profile.profile_id,
        session_signal_digest=None,
        current_episode_id=None,
        episode_observation_count=0,
        episode_canonical_request_bytes=0,
        goal_ids_signal_digest=None,
        participant_ids_signal_digest=None,
        tool_signal_digest=None,
        topic_signal_digest=None,
        last_observation_id=None,
        last_observation_sequence=0,
        last_observed_at_ns=None,
    )


def test_first_continue_and_combined_boundary_precedence_are_literal() -> None:
    profile = baseline_boundary_profile()
    first = canonicalize_observation(_request(1), profile, _initial_core(profile), 1)
    second = canonicalize_observation(_request(2), profile, first.post_core_state, 2)
    combo_request = _request(
        3,
        observation_id="obs:t23-combo",
        session_id="session:combo",
        provenance=replace(
            _request(3).provenance,
            observed_at_ns=(
                first.request.provenance.observed_at_ns
                + profile.max_inter_observation_gap_ns
                + 10
            ),
        ),
        topic_key="topic:z",
        goal_ids=("goal:z",),
        participant_ids=("participant:z",),
        tool_invocation_id="tool:combo",
        tool_phase="done",
        force_boundary=True,
    )
    combo = canonicalize_observation(combo_request, profile, second.post_core_state, 3)

    assert tuple(reason.value for reason in first.boundary_decision.reasons) == (
        "first_observation",
    )
    assert first.boundary_decision.episode_id == (
        "episode:7c8a12d211223b0d98c7d5fa11b7e6958bea53c648895b5b7c361bd39e243310"
    )
    assert second.boundary_decision.reasons == (EpisodeBoundaryReason.CONTINUE,)
    assert second.boundary_decision.episode_id == first.boundary_decision.episode_id
    assert tuple(reason.value for reason in combo.boundary_decision.reasons) == (
        "forced",
        "session_changed",
        "time_gap",
        "goal_changed",
        "tool_phase_changed",
        "participants_changed",
        "topic_key_changed",
    )
    assert combo.boundary_decision.episode_id == (
        "episode:653a284f9e6c0eaa27b59feca1fc33057d36a7e2615898e62df73ffe61951ab4"
    )


def test_profile_change_precedes_other_reasons_and_ingest_accepts_it(
    tmp_path: Path,
) -> None:
    baseline = baseline_boundary_profile()
    alternate = BoundaryProfileV1(
        name="task2-alt-v1",
        max_inter_observation_gap_ns=10,
        max_observations=2,
        max_canonical_request_bytes=2_000,
        max_goal_ids=32,
        max_participant_ids=32,
    )
    first_request = _request(1)
    changed_request = _request(
        2,
        observation_id="obs:t23-combo",
        session_id="session:combo",
        provenance=replace(_request(2).provenance, observed_at_ns=BASE_NS + 100),
        topic_key="topic:z",
        goal_ids=("goal:z",),
        participant_ids=("participant:z",),
        tool_invocation_id="tool:combo",
        tool_phase="done",
        force_boundary=True,
    )

    with EncryptedLedger(
        tmp_path / "memory.sqlite3", StaticKeyProvider(MASTER_KEY)
    ) as ledger:
        with ledger.verified_session() as session:
            initial = initialize_empty_sensorium_state(session, baseline)
            assert type(initial) is SensoriumStateV1
            first = ingest_observation(session, first_request, baseline, initial)
            assert type(first) is ObservationAcceptedV1
            changed = ingest_observation(
                session, changed_request, alternate, first.next_state
            )

    assert type(changed) is ObservationAcceptedV1
    assert changed.status is IngestStatus.APPLIED
    assert tuple(
        reason.value for reason in changed.stored_observation.boundary_decision.reasons
    ) == (
        "profile_changed",
        "forced",
        "session_changed",
        "time_gap",
        "goal_changed",
        "tool_phase_changed",
        "participants_changed",
        "topic_key_changed",
    )
    assert changed.stored_observation.boundary_decision.episode_id == (
        "episode:d6d1246c36e9d186f05a439fecc85cc7b1ff2aa0a1a15e4832947a3103e49b76"
    )


def test_time_gap_is_strict_integer_nanoseconds_and_reversal_is_typed(
    tmp_path: Path,
) -> None:
    profile = baseline_boundary_profile()
    first_request = _request(1)
    first_transition = canonicalize_observation(
        first_request, profile, _initial_core(profile), 1
    )
    at_limit = _request(
        2,
        provenance=replace(
            _request(2).provenance,
            observed_at_ns=(
                first_request.provenance.observed_at_ns
                + profile.max_inter_observation_gap_ns
            ),
        ),
    )
    beyond_limit = _request(
        3,
        provenance=replace(
            _request(3).provenance,
            observed_at_ns=(
                first_request.provenance.observed_at_ns
                + profile.max_inter_observation_gap_ns
                + 1
            ),
        ),
    )
    assert canonicalize_observation(
        at_limit, profile, first_transition.post_core_state, 2
    ).boundary_decision.reasons == (EpisodeBoundaryReason.CONTINUE,)
    assert canonicalize_observation(
        beyond_limit, profile, first_transition.post_core_state, 2
    ).boundary_decision.reasons == (EpisodeBoundaryReason.TIME_GAP,)

    reversed_request = _request(
        4,
        provenance=replace(
            _request(4).provenance,
            observed_at_ns=first_request.provenance.observed_at_ns - 1,
        ),
    )
    with EncryptedLedger(
        tmp_path / "memory.sqlite3", StaticKeyProvider(MASTER_KEY)
    ) as ledger:
        with ledger.verified_session() as session:
            initial = initialize_empty_sensorium_state(session, profile)
            assert type(initial) is SensoriumStateV1
            first = ingest_observation(session, first_request, profile, initial)
            assert type(first) is ObservationAcceptedV1
            reversed_result = ingest_observation(
                session, reversed_request, profile, first.next_state
            )
            assert session.event_count() == 1

    assert type(reversed_result) is ObservationRejectedV1
    assert reversed_result.rejection_code is IngestRejectionCode.TIME_REVERSED_INVALID
    assert "time_reversed_invalid" not in {
        reason.value for reason in EpisodeBoundaryReason
    }


def test_count_and_request_byte_limits_use_strict_greater_than() -> None:
    first_request = _request(1)
    second_request = _request(2)
    byte_cap = len(encode_observation_request(first_request)) + len(
        encode_observation_request(second_request)
    )
    profile = BoundaryProfileV1(
        name="task2-limit-v1",
        max_inter_observation_gap_ns=1_000,
        max_observations=2,
        max_canonical_request_bytes=byte_cap,
        max_goal_ids=32,
        max_participant_ids=32,
    )
    first = canonicalize_observation(first_request, profile, _initial_core(profile), 1)
    second = canonicalize_observation(second_request, profile, first.post_core_state, 2)
    third = canonicalize_observation(_request(3), profile, second.post_core_state, 3)

    assert second.boundary_decision.reasons == (EpisodeBoundaryReason.CONTINUE,)
    assert third.boundary_decision.reasons == (
        EpisodeBoundaryReason.EPISODE_COUNT_LIMIT,
        EpisodeBoundaryReason.EPISODE_BYTE_LIMIT,
    )


def test_duplicate_retry_preserves_every_episode_counter(tmp_path: Path) -> None:
    profile = baseline_boundary_profile()
    request = _request(1)
    with EncryptedLedger(
        tmp_path / "memory.sqlite3", StaticKeyProvider(MASTER_KEY)
    ) as ledger:
        with ledger.verified_session() as session:
            initial = initialize_empty_sensorium_state(session, profile)
            assert type(initial) is SensoriumStateV1
            first = ingest_observation(session, request, profile, initial)
            assert type(first) is ObservationAcceptedV1
            retry = ingest_observation(session, request, profile, initial)
            equal = ingest_observation(session, request, profile, first.next_state)

    assert type(retry) is ObservationAcceptedV1
    assert type(equal) is ObservationAcceptedV1
    assert retry.status is IngestStatus.DUPLICATE
    assert equal.status is IngestStatus.DUPLICATE
    assert retry.next_state == first.next_state == equal.next_state
    assert retry.next_state.core.episode_observation_count == 1
    assert retry.next_state.core.episode_canonical_request_bytes == len(
        encode_observation_request(request)
    )
    assert retry.next_state.core.last_observation_sequence == 1
    assert (
        retry.next_state.core.last_observed_at_ns == request.provenance.observed_at_ns
    )
