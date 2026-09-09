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


def test_every_boundary_reason_has_an_isolated_literal_decision() -> None:
    profile = baseline_boundary_profile()
    first_request = _request(1)
    first = canonicalize_observation(first_request, profile, _initial_core(profile), 1)
    isolated = (
        (
            _request(
                2,
                observation_id="obs:t23-only-forced",
                force_boundary=True,
            ),
            profile,
            EpisodeBoundaryReason.FORCED,
            "episode:da80fa7e1d6a9ff7670f80010186f036b490f2bbc2339e3774e16f3ccb12615f",
        ),
        (
            _request(
                2,
                observation_id="obs:t23-only-session",
                session_id="session:changed",
            ),
            profile,
            EpisodeBoundaryReason.SESSION_CHANGED,
            "episode:8a1e0f4bd8f8755c498022ca3bb2bab4198c809a2a25d999c0b51c8bf796c17d",
        ),
        (
            _request(
                2,
                observation_id="obs:t23-only-time",
                provenance=replace(
                    _request(2).provenance,
                    observed_at_ns=(
                        first_request.provenance.observed_at_ns
                        + profile.max_inter_observation_gap_ns
                        + 1
                    ),
                ),
            ),
            profile,
            EpisodeBoundaryReason.TIME_GAP,
            "episode:b42054ebcac934c9bee3960013ab87f332e9f0db782c7bed28504d0f41c71bea",
        ),
        (
            _request(
                2,
                observation_id="obs:t23-only-goal",
                goal_ids=("goal:changed",),
            ),
            profile,
            EpisodeBoundaryReason.GOAL_CHANGED,
            "episode:a1b2f565ab2b08d46c11b6d7637eb2b121199eb7ab07a9a8007e116bcac91abb",
        ),
        (
            _request(
                2,
                observation_id="obs:t23-only-tool",
                tool_invocation_id="tool:changed",
                tool_phase="done",
            ),
            profile,
            EpisodeBoundaryReason.TOOL_PHASE_CHANGED,
            "episode:075605c5f65198bc7a040ac0ad64c11f85cc6a8b009e5c344033a4af95b77637",
        ),
        (
            _request(
                2,
                observation_id="obs:t23-only-participants",
                participant_ids=("participant:changed",),
            ),
            profile,
            EpisodeBoundaryReason.PARTICIPANTS_CHANGED,
            "episode:3a78e6d29a06bef6e8c128f8b64c3e6d3250968fb0f297b730807c419a5333ad",
        ),
        (
            _request(
                2,
                observation_id="obs:t23-only-topic",
                topic_key="topic:changed",
            ),
            profile,
            EpisodeBoundaryReason.TOPIC_KEY_CHANGED,
            "episode:6ed50550fe1c36a1f5849b56a8c1133b65c5f8865790974b352c8abd1966e1be",
        ),
    )
    for request, case_profile, expected_reason, expected_episode_id in isolated:
        transition = canonicalize_observation(
            request, case_profile, first.post_core_state, 2
        )
        assert transition.boundary_decision.reasons == (expected_reason,)
        assert transition.boundary_decision.episode_id == expected_episode_id

    alternate = BoundaryProfileV1(
        name="task2-profile-only-v1",
        max_inter_observation_gap_ns=9_999_999_999_999,
        max_observations=99,
        max_canonical_request_bytes=8 * 1024 * 1024,
        max_goal_ids=32,
        max_participant_ids=32,
    )
    profile_only = canonicalize_observation(
        _request(2, observation_id="obs:t23-only-profile"),
        alternate,
        first.post_core_state,
        2,
    )
    assert profile_only.boundary_decision.reasons == (
        EpisodeBoundaryReason.PROFILE_CHANGED,
    )
    assert profile_only.boundary_decision.episode_id == (
        "episode:3d7fab5933f2e38e515662fbb925b928ea348e853931557cd8d85652f924594f"
    )

    count_profile = BoundaryProfileV1(
        name="task2-count-only-v1",
        max_inter_observation_gap_ns=profile.max_inter_observation_gap_ns,
        max_observations=1,
        max_canonical_request_bytes=8 * 1024 * 1024,
        max_goal_ids=32,
        max_participant_ids=32,
    )
    count_first = canonicalize_observation(
        first_request, count_profile, _initial_core(count_profile), 1
    )
    count_only = canonicalize_observation(
        _request(2, observation_id="obs:t23-only-count"),
        count_profile,
        count_first.post_core_state,
        2,
    )
    assert count_only.boundary_decision.reasons == (
        EpisodeBoundaryReason.EPISODE_COUNT_LIMIT,
    )
    assert count_only.boundary_decision.episode_id == (
        "episode:713707d779bfc62a4a6112e4f0b312ab24ddc1112e48a69bf5230428ad430b5e"
    )

    byte_request = _request(2, observation_id="obs:t23-only-byte")
    byte_cap = (
        len(encode_observation_request(first_request))
        + len(encode_observation_request(byte_request))
        - 1
    )
    assert byte_cap == 1_198
    byte_profile = BoundaryProfileV1(
        name="task2-byte-only-v1",
        max_inter_observation_gap_ns=profile.max_inter_observation_gap_ns,
        max_observations=99,
        max_canonical_request_bytes=byte_cap,
        max_goal_ids=32,
        max_participant_ids=32,
    )
    byte_first = canonicalize_observation(
        first_request, byte_profile, _initial_core(byte_profile), 1
    )
    byte_only = canonicalize_observation(
        byte_request, byte_profile, byte_first.post_core_state, 2
    )
    assert byte_only.boundary_decision.reasons == (
        EpisodeBoundaryReason.EPISODE_BYTE_LIMIT,
    )
    assert byte_only.boundary_decision.episode_id == (
        "episode:d8080f3899a36933a53c93d6fe82f2fec900a878d3e56479e303b614b2a56435"
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


def test_profile_change_duplicate_retry_converges_without_second_write(
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
    changed_request = _request(2, observation_id="obs:t23-profile-retry")

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
            retried = ingest_observation(
                session, changed_request, alternate, first.next_state
            )
            assert session.event_count() == 2

    assert type(retried) is ObservationAcceptedV1
    assert retried.status is IngestStatus.DUPLICATE
    assert retried.next_state == changed.next_state


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
