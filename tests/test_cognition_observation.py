from __future__ import annotations

import hashlib
import inspect
import struct
from collections.abc import Callable
from dataclasses import FrozenInstanceError, fields, replace
from enum import Enum
from typing import Any, cast

import pytest
from aluclu.cognition.observation import (
    BoundarySignalDigestsV1,
    CanonicalJsonValue,
    CanonicalObservationV1,
    EpisodeBoundaryDecisionV1,
    EpisodeBoundaryReason,
    ObservationRequestV1,
    ProvenanceV1,
    SensoriumCoreStateV1,
    SourceKind,
    build_canonical_observation,
    canonical_observation_from_json_value,
    canonical_observation_to_json_value,
    decode_canonical_observation,
    decode_observation_request,
    decode_provenance,
    decode_sensorium_core_state,
    derive_boundary_signal_digests,
    derive_content_digest,
    derive_episode_id,
    derive_request_digest,
    derive_sensorium_core_state_digest,
    encode_canonical_observation,
    encode_observation_request,
    encode_provenance,
    encode_sensorium_core_state,
    observation_request_from_json_value,
    observation_request_to_json_value,
    sensorium_core_state_from_json_value,
    sensorium_core_state_to_json_value,
)

import aluclu.cognition as cognition
from aluclu.cognition import InputBoundaryError, canonical_json_bytes, strict_json_loads
from aluclu.cognition import codec as task1_codec
from aluclu.cognition import observation as observation_module

MAX_I63 = (1 << 63) - 1
OBSERVATION_ENVELOPE_MAX_BYTES = 262_144
SENSORIUM_CORE_MAX_BYTES = 3_072
BOUNDARY_PROFILE_ID = "boundary-profile:" + ("a" * 64)
EPISODE_ID = "episode:" + ("b" * 64)
ZERO_HASH = "0" * 64

PROVENANCE_KEYS = {
    "schema",
    "source_kind",
    "source_instance_id",
    "origin_id",
    "observed_at_ns",
    "parent_observation_ids",
    "capture_method",
    "capture_version",
}
REQUEST_KEYS = {
    "schema",
    "observation_id",
    "session_id",
    "turn_id",
    "provenance",
    "content",
    "retrieval_text",
    "topic_key",
    "goal_ids",
    "participant_ids",
    "tool_invocation_id",
    "tool_phase",
    "force_boundary",
}
BOUNDARY_DECISION_KEYS = {"schema", "episode_id", "reasons"}
CORE_KEYS = {
    "schema",
    "boundary_profile_id",
    "session_signal_digest",
    "current_episode_id",
    "episode_observation_count",
    "episode_canonical_request_bytes",
    "goal_ids_signal_digest",
    "participant_ids_signal_digest",
    "tool_signal_digest",
    "topic_signal_digest",
    "last_observation_id",
    "last_observation_sequence",
    "last_observed_at_ns",
}
OBSERVATION_KEYS = {
    "schema",
    "request",
    "request_digest",
    "content_digest",
    "boundary_decision",
    "pre_core_state_digest",
    "post_core_state",
    "post_core_state_digest",
    "pre_append_head_sequence",
    "pre_append_head_hash",
    "boundary_profile_id",
}

TASK1_PUBLIC_EXPORTS = (
    "AppendOutcome",
    "CognitionError",
    "DirectoryRecordKeyStore",
    "EncryptedLedger",
    "FileKeyProvider",
    "FileRecordKeyStore",
    "InputBoundaryError",
    "KeyProvider",
    "KeyProviderUnavailable",
    "KeyringKeyProvider",
    "KeyringRecordKeyStore",
    "LedgerCapabilityUnavailable",
    "LedgerConflictError",
    "LedgerCursorCheckpoint",
    "LedgerError",
    "LedgerIntegrityError",
    "LedgerKeyError",
    "LedgerLifecycleError",
    "LedgerMigrationRequired",
    "LedgerRecord",
    "LedgerRollbackError",
    "LedgerSecurityScope",
    "LedgerSnapshotChanged",
    "LedgerVerificationStats",
    "PersistenceError",
    "RecordKeyReference",
    "RecordKeyState",
    "RecordKeyStore",
    "RecordKeyStoreProfile",
    "SafeStateCodec",
    "StateIntegrityError",
    "StaticKeyProvider",
    "UnsafePathError",
    "VerifiedLedgerCursor",
    "VerifiedLedgerSession",
    "atomic_write_bytes",
    "canonical_json_bytes",
    "create_record_key_store",
    "exclusive_file_lock",
    "resolve_ledger_path",
    "strict_json_loads",
    "validate_event_id",
)

TASK2_OBSERVATION_PUBLIC_EXPORTS = (
    "BoundarySignalDigestsV1",
    "CanonicalJsonValue",
    "CanonicalObservationV1",
    "EpisodeBoundaryDecisionV1",
    "EpisodeBoundaryReason",
    "ObservationRequestV1",
    "ProvenanceV1",
    "SensoriumCoreStateV1",
    "SourceKind",
    "build_canonical_observation",
    "canonical_observation_from_json_value",
    "canonical_observation_to_json_value",
    "decode_canonical_observation",
    "decode_observation_request",
    "decode_provenance",
    "decode_sensorium_core_state",
    "derive_boundary_signal_digests",
    "derive_content_digest",
    "derive_episode_id",
    "derive_request_digest",
    "derive_sensorium_core_state_digest",
    "encode_canonical_observation",
    "encode_observation_request",
    "encode_provenance",
    "encode_sensorium_core_state",
    "observation_request_from_json_value",
    "observation_request_to_json_value",
    "sensorium_core_state_from_json_value",
    "sensorium_core_state_to_json_value",
)


def _domain_digest(domain: bytes, payload: bytes) -> str:
    framed = (
        struct.pack(">Q", len(domain))
        + domain
        + struct.pack(">Q", len(payload))
        + payload
    )
    return hashlib.sha256(framed).hexdigest()


def _provenance(**overrides: object) -> ProvenanceV1:
    values: dict[str, object] = {
        "source_kind": SourceKind.USER,
        "source_instance_id": "chat-ui:primary",
        "origin_id": "account@example.test",
        "observed_at_ns": 1_725_000_000_000_000_000,
        "parent_observation_ids": ("obs:parent-1", "obs:parent-2"),
        "capture_method": "adapter",
        "capture_version": "1.0.0",
    }
    values.update(overrides)
    return ProvenanceV1(**values)  # type: ignore[arg-type]


def _request(**overrides: object) -> ObservationRequestV1:
    values: dict[str, object] = {
        "observation_id": "obs:0001",
        "session_id": "session:alpha",
        "turn_id": "turn:0001",
        "provenance": _provenance(),
        "content": CanonicalJsonValue.from_value(
            {"nested": [{"text": "Istanbul"}, [1, True, None]]}
        ),
        "retrieval_text": "Istanbul memory",
        "topic_key": "topic:travel",
        "goal_ids": ("goal:alpha", "goal:beta"),
        "participant_ids": ("participant:assistant", "participant:user"),
        "tool_invocation_id": "tool:0001",
        "tool_phase": "result",
        "force_boundary": False,
    }
    values.update(overrides)
    return ObservationRequestV1(**values)  # type: ignore[arg-type]


def _initial_core(**overrides: object) -> SensoriumCoreStateV1:
    values: dict[str, object] = {
        "boundary_profile_id": BOUNDARY_PROFILE_ID,
        "session_signal_digest": None,
        "current_episode_id": None,
        "episode_observation_count": 0,
        "episode_canonical_request_bytes": 0,
        "goal_ids_signal_digest": None,
        "participant_ids_signal_digest": None,
        "tool_signal_digest": None,
        "topic_signal_digest": None,
        "last_observation_id": None,
        "last_observation_sequence": 0,
        "last_observed_at_ns": None,
    }
    values.update(overrides)
    return SensoriumCoreStateV1(**values)  # type: ignore[arg-type]


def _post_core(
    request: ObservationRequestV1 | None = None,
    *,
    request_bytes: int | None = None,
    **overrides: object,
) -> SensoriumCoreStateV1:
    active_request = request or _request()
    signals = derive_boundary_signal_digests(active_request)
    episode_id = derive_episode_id(
        boundary_profile_id=BOUNDARY_PROFILE_ID,
        first_observation_id=active_request.observation_id,
        session_id=active_request.session_id,
    )
    values: dict[str, object] = {
        "boundary_profile_id": BOUNDARY_PROFILE_ID,
        "session_signal_digest": signals.session_signal_digest,
        "current_episode_id": episode_id,
        "episode_observation_count": 1,
        "episode_canonical_request_bytes": (
            len(encode_observation_request(active_request))
            if request_bytes is None
            else request_bytes
        ),
        "goal_ids_signal_digest": signals.goal_ids_signal_digest,
        "participant_ids_signal_digest": signals.participant_ids_signal_digest,
        "tool_signal_digest": signals.tool_signal_digest,
        "topic_signal_digest": signals.topic_signal_digest,
        "last_observation_id": active_request.observation_id,
        "last_observation_sequence": 1,
        "last_observed_at_ns": active_request.provenance.observed_at_ns,
    }
    values.update(overrides)
    return SensoriumCoreStateV1(**values)  # type: ignore[arg-type]


def _decision(request: ObservationRequestV1 | None = None) -> EpisodeBoundaryDecisionV1:
    active_request = request or _request()
    return EpisodeBoundaryDecisionV1(
        episode_id=derive_episode_id(
            boundary_profile_id=BOUNDARY_PROFILE_ID,
            first_observation_id=active_request.observation_id,
            session_id=active_request.session_id,
        ),
        reasons=(EpisodeBoundaryReason.FIRST_OBSERVATION,),
    )


def _observation(
    request: ObservationRequestV1 | None = None,
    *,
    post_core_state: SensoriumCoreStateV1 | None = None,
) -> CanonicalObservationV1:
    active_request = request or _request()
    return build_canonical_observation(
        request=active_request,
        boundary_decision=_decision(active_request),
        pre_core_state_digest=derive_sensorium_core_state_digest(_initial_core()),
        post_core_state=post_core_state or _post_core(active_request),
        pre_append_head_sequence=0,
        pre_append_head_hash=ZERO_HASH,
        boundary_profile_id=BOUNDARY_PROFILE_ID,
    )


def _assert_frozen_kw_only_slotted(instance: object, field_names: tuple[str, ...]) -> None:
    assert tuple(field.name for field in fields(instance)) == field_names
    assert not hasattr(instance, "__dict__")
    first_field = field_names[0]
    with pytest.raises((FrozenInstanceError, AttributeError)):
        setattr(instance, first_field, getattr(instance, first_field))
    with pytest.raises(TypeError):
        type(instance)(*[getattr(instance, name) for name in field_names])


def _mutated_canonical_bytes(
    encoded: bytes,
    mutation: Callable[[dict[str, Any]], None],
) -> bytes:
    value = strict_json_loads(encoded)
    assert type(value) is dict
    mutable = cast(dict[str, Any], value)
    mutation(mutable)
    return canonical_json_bytes(mutable)


def _assert_strict_object_decoder(
    encoded: bytes,
    decoder: Callable[[bytes], object],
) -> None:
    decoded = strict_json_loads(encoded)
    assert type(decoded) is dict
    wire = cast(dict[str, Any], decoded)

    missing = dict(wire)
    missing.pop(next(iter(missing)))
    with pytest.raises(InputBoundaryError):
        decoder(canonical_json_bytes(missing))

    unknown = dict(wire)
    unknown["unknown"] = None
    with pytest.raises(InputBoundaryError):
        decoder(canonical_json_bytes(unknown))

    wrong_schema = dict(wire)
    wrong_schema["schema"] = "aluclu.wrong.v1"
    with pytest.raises(InputBoundaryError):
        decoder(canonical_json_bytes(wrong_schema))

    with pytest.raises(InputBoundaryError):
        decoder(b" " + encoded)
    with pytest.raises(InputBoundaryError):
        decoder(cast(Any, bytearray(encoded)))


def test_task1_exports_are_preserved_and_task2_exports_are_strictly_additive() -> None:
    exported = tuple(cognition.__all__)
    assert len(exported) == len(set(exported))
    assert set(TASK1_PUBLIC_EXPORTS) < set(exported)
    assert set(TASK2_OBSERVATION_PUBLIC_EXPORTS) <= set(exported)

    for name in TASK1_PUBLIC_EXPORTS:
        assert getattr(cognition, name) is getattr(
            __import__("aluclu.cognition", fromlist=[name]), name
        )
    for name in TASK2_OBSERVATION_PUBLIC_EXPORTS:
        assert getattr(cognition, name) is getattr(observation_module, name)


def test_source_kind_is_a_closed_distinct_string_enum() -> None:
    assert issubclass(SourceKind, str)
    assert issubclass(SourceKind, Enum)
    assert [(kind.name, kind.value) for kind in SourceKind] == [
        ("USER", "user"),
        ("TOOL", "tool"),
        ("WEB", "web"),
        ("DATABASE", "database"),
        ("FILE", "file"),
        ("ENVIRONMENT", "environment"),
        ("MODEL", "model"),
    ]
    assert len({kind.value for kind in SourceKind}) == 7
    assert not hasattr(SourceKind, "OTHER")


@pytest.mark.parametrize("source_kind", list(SourceKind))
def test_every_source_kind_round_trips_without_collapsing(
    source_kind: SourceKind,
) -> None:
    value = _provenance(source_kind=source_kind)
    decoded = decode_provenance(encode_provenance(value))
    assert decoded == value
    assert decoded.source_kind is source_kind


def test_model_provenance_cannot_decode_as_user_tool_or_external_evidence() -> None:
    model = _provenance(source_kind=SourceKind.MODEL)
    wire = strict_json_loads(encode_provenance(model))
    assert type(wire) is dict
    assert wire["source_kind"] == "model"
    assert decode_provenance(encode_provenance(model)).source_kind is SourceKind.MODEL
    assert decode_provenance(encode_provenance(model)).source_kind not in {
        SourceKind.USER,
        SourceKind.TOOL,
        SourceKind.WEB,
        SourceKind.DATABASE,
        SourceKind.FILE,
        SourceKind.ENVIRONMENT,
    }

    wire["source_kind"] = "other"
    with pytest.raises(InputBoundaryError):
        decode_provenance(canonical_json_bytes(wire))


def test_canonical_json_value_has_only_validated_deeply_immutable_bytes() -> None:
    caller_value: dict[str, Any] = {"outer": [{"inner": [1, 2]}]}
    canonical = CanonicalJsonValue.from_value(caller_value)
    expected = b'{"outer":[{"inner":[1,2]}]}'

    assert canonical.canonical_bytes == expected
    assert tuple(field.name for field in fields(canonical)) == ("canonical_bytes",)
    assert not hasattr(canonical, "__dict__")
    with pytest.raises((FrozenInstanceError, AttributeError)):
        canonical.canonical_bytes = b"null"  # type: ignore[misc]

    caller_value["outer"][0]["inner"].append(3)
    assert canonical.canonical_bytes == expected
    first_read = cast(dict[str, Any], canonical.to_value())
    cast(list[Any], first_read["outer"])[0]["inner"].append(4)
    second_read = canonical.to_value()
    assert second_read == {"outer": [{"inner": [1, 2]}]}
    assert second_read is not first_read


def test_canonical_json_value_constructor_is_disabled_and_decoder_is_exact() -> None:
    with pytest.raises(TypeError):
        cast(Any, CanonicalJsonValue)(b"{}")
    with pytest.raises(InputBoundaryError):
        CanonicalJsonValue.from_canonical_bytes(b'{"z":1,"a":2}')
    with pytest.raises(InputBoundaryError):
        CanonicalJsonValue.from_canonical_bytes(b'{"x":1,"x":2}')
    with pytest.raises(InputBoundaryError):
        CanonicalJsonValue.from_canonical_bytes(cast(Any, bytearray(b"null")))
    with pytest.raises(InputBoundaryError):
        CanonicalJsonValue.from_value({"bad": "\ud800"})

    canonical = CanonicalJsonValue.from_canonical_bytes(b'{"a":2,"z":1}')
    assert canonical.to_value() == {"a": 2, "z": 1}


def test_content_preserves_unicode_code_points_and_digest_distinguishes_nfc_nfd() -> None:
    composed = CanonicalJsonValue.from_value({"text": "é"})
    decomposed = CanonicalJsonValue.from_value({"text": "e\u0301"})

    assert composed.canonical_bytes != decomposed.canonical_bytes
    assert composed.to_value() == {"text": "é"}
    assert decomposed.to_value() == {"text": "e\u0301"}
    assert derive_content_digest(composed) != derive_content_digest(decomposed)


def test_provenance_is_frozen_keyword_only_slotted_and_has_exact_wire_schema() -> None:
    provenance = _provenance()
    _assert_frozen_kw_only_slotted(
        provenance,
        (
            "source_kind",
            "source_instance_id",
            "origin_id",
            "observed_at_ns",
            "parent_observation_ids",
            "capture_method",
            "capture_version",
        ),
    )
    wire = strict_json_loads(encode_provenance(provenance))
    assert type(wire) is dict
    assert set(wire) == PROVENANCE_KEYS
    assert wire == {
        "schema": "aluclu.provenance.v1",
        "source_kind": "user",
        "source_instance_id": "chat-ui:primary",
        "origin_id": "account@example.test",
        "observed_at_ns": 1_725_000_000_000_000_000,
        "parent_observation_ids": ["obs:parent-1", "obs:parent-2"],
        "capture_method": "adapter",
        "capture_version": "1.0.0",
    }
    assert decode_provenance(encode_provenance(provenance)) == provenance
    _assert_strict_object_decoder(encode_provenance(provenance), decode_provenance)


@pytest.mark.parametrize(
    ("field_name", "value"),
    [
        ("source_instance_id", "-bad"),
        ("source_instance_id", "x" * 129),
        ("source_instance_id", "ışık"),
        ("origin_id", ""),
        ("origin_id", "bad space"),
        ("origin_id", "x" * 129),
        ("capture_method", "-bad"),
        ("capture_method", "x" * 65),
        ("capture_method", "é"),
        ("capture_version", ""),
        ("capture_version", "bad:token"),
        ("capture_version", "x" * 65),
        ("observed_at_ns", True),
        ("observed_at_ns", -1),
        ("observed_at_ns", MAX_I63 + 1),
        ("parent_observation_ids", ["obs:parent"]),
        ("parent_observation_ids", ("obs:z", "obs:a")),
        ("parent_observation_ids", ("obs:a", "obs:a")),
        ("parent_observation_ids", tuple(f"obs:{index:02d}" for index in range(33))),
        ("parent_observation_ids", ("event:not-observation",)),
    ],
)
def test_provenance_rejects_invalid_types_bounds_and_collections(
    field_name: str,
    value: object,
) -> None:
    with pytest.raises(InputBoundaryError):
        _provenance(**{field_name: value})


def test_provenance_accepts_all_exact_inclusive_boundaries() -> None:
    provenance = _provenance(
        source_instance_id="a" * 128,
        origin_id="z" * 128,
        observed_at_ns=MAX_I63,
        parent_observation_ids=tuple(f"obs:{index:02d}" for index in range(32)),
        capture_method="m" * 64,
        capture_version="v" * 64,
    )
    assert decode_provenance(encode_provenance(provenance)) == provenance


def test_observation_request_is_frozen_keyword_only_slotted_and_exactly_shaped() -> None:
    request = _request()
    _assert_frozen_kw_only_slotted(
        request,
        (
            "observation_id",
            "session_id",
            "turn_id",
            "provenance",
            "content",
            "retrieval_text",
            "topic_key",
            "goal_ids",
            "participant_ids",
            "tool_invocation_id",
            "tool_phase",
            "force_boundary",
        ),
    )
    wire = observation_request_to_json_value(request)
    assert set(wire) == REQUEST_KEYS
    assert wire["schema"] == "aluclu.observation-request.v1"
    assert wire["content"] == request.content.to_value()
    assert type(wire["content"]) is dict
    assert wire["goal_ids"] == ["goal:alpha", "goal:beta"]
    assert wire["participant_ids"] == [
        "participant:assistant",
        "participant:user",
    ]
    assert observation_request_from_json_value(wire) == request
    assert decode_observation_request(encode_observation_request(request)) == request
    _assert_strict_object_decoder(
        encode_observation_request(request), decode_observation_request
    )


def test_observation_request_serializes_every_optional_field_as_null_or_array() -> None:
    request = _request(
        provenance=_provenance(parent_observation_ids=()),
        retrieval_text=None,
        topic_key=None,
        goal_ids=(),
        participant_ids=(),
        tool_invocation_id=None,
        tool_phase=None,
    )
    wire = observation_request_to_json_value(request)
    assert set(wire) == REQUEST_KEYS
    assert wire["retrieval_text"] is None
    assert wire["topic_key"] is None
    assert wire["goal_ids"] == []
    assert wire["participant_ids"] == []
    assert wire["tool_invocation_id"] is None
    assert wire["tool_phase"] is None
    assert cast(dict[str, Any], wire["provenance"])["parent_observation_ids"] == []


@pytest.mark.parametrize(
    ("field_name", "value"),
    [
        ("observation_id", "obs:"),
        ("observation_id", "evt:not-observation"),
        ("observation_id", "obs:" + ("a" * 253)),
        ("observation_id", "obs:bad space"),
        ("observation_id", "obs:é"),
        ("session_id", "-bad"),
        ("session_id", "s" * 257),
        ("turn_id", ""),
        ("turn_id", "t" * 257),
        ("retrieval_text", b"text"),
        ("retrieval_text", "\ud800"),
        ("topic_key", "-bad"),
        ("topic_key", "x" * 129),
        ("topic_key", "é"),
        ("goal_ids", ["goal:a"]),
        ("goal_ids", ("goal:z", "goal:a")),
        ("goal_ids", ("goal:a", "goal:a")),
        ("goal_ids", tuple(f"goal:{index:02d}" for index in range(33))),
        ("goal_ids", ("g" * 257,)),
        ("participant_ids", ["participant:a"]),
        ("participant_ids", ("participant:z", "participant:a")),
        ("participant_ids", ("participant:a", "participant:a")),
        (
            "participant_ids",
            tuple(f"participant:{index:02d}" for index in range(33)),
        ),
        ("tool_invocation_id", ""),
        ("tool_invocation_id", "é"),
        ("tool_phase", "bad:phase"),
        ("tool_phase", "x" * 65),
        ("force_boundary", 0),
        ("force_boundary", "false"),
    ],
)
def test_observation_request_rejects_invalid_ids_types_and_collections(
    field_name: str,
    value: object,
) -> None:
    with pytest.raises(InputBoundaryError):
        _request(**{field_name: value})


def test_observation_request_rejects_self_parent() -> None:
    with pytest.raises(InputBoundaryError):
        _request(provenance=_provenance(parent_observation_ids=("obs:0001",)))


def test_observation_request_accepts_exact_id_and_collection_boundaries() -> None:
    request = _request(
        observation_id="obs:" + ("a" * 252),
        session_id="s" * 256,
        turn_id="t" * 256,
        provenance=_provenance(parent_observation_ids=()),
        topic_key="k" * 128,
        goal_ids=tuple(f"g{index:031d}" for index in range(32)),
        participant_ids=tuple(f"p{index:031d}" for index in range(32)),
        tool_invocation_id="i" * 256,
        tool_phase="p" * 64,
    )
    assert decode_observation_request(encode_observation_request(request)) == request


def test_retrieval_text_raw_and_normalized_utf8_limits_are_independent() -> None:
    assert _request(retrieval_text="x" * 4096).retrieval_text == "x" * 4096
    with pytest.raises(InputBoundaryError):
        _request(retrieval_text="x" * 4097)

    # U+0958 is three UTF-8 bytes but NFC expands it to two three-byte code points.
    # 682 copies normalize to 4,092 bytes; 683 normalize to 4,098 bytes.
    assert _request(retrieval_text="\u0958" * 682).retrieval_text == "\u0958" * 682
    with pytest.raises(InputBoundaryError):
        _request(retrieval_text="\u0958" * 683)


def test_request_decoder_rejects_noncanonical_arrays_unknown_source_and_bad_schema() -> None:
    encoded = encode_observation_request(_request())

    def unsort_goals(wire: dict[str, Any]) -> None:
        wire["goal_ids"] = ["goal:z", "goal:a"]

    def unknown_source(wire: dict[str, Any]) -> None:
        cast(dict[str, Any], wire["provenance"])["source_kind"] = "other"

    def missing_optional(wire: dict[str, Any]) -> None:
        wire.pop("retrieval_text")

    for mutation in (unsort_goals, unknown_source, missing_optional):
        with pytest.raises(InputBoundaryError):
            decode_observation_request(_mutated_canonical_bytes(encoded, mutation))


def test_episode_boundary_reason_is_closed_and_has_fixed_precedence() -> None:
    assert [(reason.name, reason.value) for reason in EpisodeBoundaryReason] == [
        ("FIRST_OBSERVATION", "first_observation"),
        ("PROFILE_CHANGED", "profile_changed"),
        ("FORCED", "forced"),
        ("SESSION_CHANGED", "session_changed"),
        ("TIME_GAP", "time_gap"),
        ("GOAL_CHANGED", "goal_changed"),
        ("TOOL_PHASE_CHANGED", "tool_phase_changed"),
        ("PARTICIPANTS_CHANGED", "participants_changed"),
        ("TOPIC_KEY_CHANGED", "topic_key_changed"),
        ("EPISODE_COUNT_LIMIT", "episode_count_limit"),
        ("EPISODE_BYTE_LIMIT", "episode_byte_limit"),
        ("CONTINUE", "continue"),
    ]
    assert not hasattr(EpisodeBoundaryReason, "TIME_REVERSED_INVALID")


def test_episode_boundary_decision_is_frozen_keyword_only_slotted() -> None:
    decision = EpisodeBoundaryDecisionV1(
        episode_id=EPISODE_ID,
        reasons=(
            EpisodeBoundaryReason.FORCED,
            EpisodeBoundaryReason.GOAL_CHANGED,
            EpisodeBoundaryReason.TOPIC_KEY_CHANGED,
        ),
    )
    _assert_frozen_kw_only_slotted(decision, ("episode_id", "reasons"))


@pytest.mark.parametrize(
    ("episode_id", "reasons"),
    [
        ("episode:", (EpisodeBoundaryReason.CONTINUE,)),
        ("episode:" + ("A" * 64), (EpisodeBoundaryReason.CONTINUE,)),
        ("episode:" + ("a" * 63), (EpisodeBoundaryReason.CONTINUE,)),
        (EPISODE_ID, ()),
        (
            EPISODE_ID,
            (EpisodeBoundaryReason.GOAL_CHANGED, EpisodeBoundaryReason.FORCED),
        ),
        (
            EPISODE_ID,
            (EpisodeBoundaryReason.FORCED, EpisodeBoundaryReason.FORCED),
        ),
        (
            EPISODE_ID,
            (EpisodeBoundaryReason.CONTINUE, EpisodeBoundaryReason.TIME_GAP),
        ),
        (EPISODE_ID, [EpisodeBoundaryReason.CONTINUE]),
    ],
)
def test_episode_boundary_decision_rejects_invalid_ids_order_and_reason_sets(
    episode_id: str,
    reasons: object,
) -> None:
    with pytest.raises(InputBoundaryError):
        EpisodeBoundaryDecisionV1(episode_id=episode_id, reasons=reasons)  # type: ignore[arg-type]


def test_sensorium_core_initial_and_populated_shapes_are_exact() -> None:
    initial = _initial_core()
    _assert_frozen_kw_only_slotted(
        initial,
        (
            "boundary_profile_id",
            "session_signal_digest",
            "current_episode_id",
            "episode_observation_count",
            "episode_canonical_request_bytes",
            "goal_ids_signal_digest",
            "participant_ids_signal_digest",
            "tool_signal_digest",
            "topic_signal_digest",
            "last_observation_id",
            "last_observation_sequence",
            "last_observed_at_ns",
        ),
    )
    initial_wire = sensorium_core_state_to_json_value(initial)
    assert set(initial_wire) == CORE_KEYS
    assert initial_wire == {
        "schema": "aluclu.sensorium-core-state.v1",
        "boundary_profile_id": BOUNDARY_PROFILE_ID,
        "session_signal_digest": None,
        "current_episode_id": None,
        "episode_observation_count": 0,
        "episode_canonical_request_bytes": 0,
        "goal_ids_signal_digest": None,
        "participant_ids_signal_digest": None,
        "tool_signal_digest": None,
        "topic_signal_digest": None,
        "last_observation_id": None,
        "last_observation_sequence": 0,
        "last_observed_at_ns": None,
    }
    assert sensorium_core_state_from_json_value(initial_wire) == initial
    assert decode_sensorium_core_state(encode_sensorium_core_state(initial)) == initial
    _assert_strict_object_decoder(
        encode_sensorium_core_state(initial), decode_sensorium_core_state
    )

    populated = _post_core()
    populated_wire = sensorium_core_state_to_json_value(populated)
    assert set(populated_wire) == CORE_KEYS
    for field_name in (
        "session_signal_digest",
        "current_episode_id",
        "goal_ids_signal_digest",
        "participant_ids_signal_digest",
        "tool_signal_digest",
        "topic_signal_digest",
        "last_observation_id",
        "last_observed_at_ns",
    ):
        assert populated_wire[field_name] is not None


@pytest.mark.parametrize(
    ("field_name", "value"),
    [
        ("boundary_profile_id", "boundary-profile:"),
        ("boundary_profile_id", "boundary-profile:" + ("A" * 64)),
        ("episode_observation_count", True),
        ("episode_observation_count", -1),
        ("episode_observation_count", MAX_I63 + 1),
        ("episode_canonical_request_bytes", True),
        ("episode_canonical_request_bytes", -1),
        ("last_observation_sequence", True),
        ("last_observation_sequence", -1),
        ("last_observed_at_ns", True),
        ("last_observed_at_ns", -1),
        ("last_observed_at_ns", MAX_I63 + 1),
        ("session_signal_digest", "a" * 63),
        ("session_signal_digest", "A" * 64),
        ("current_episode_id", "episode:" + ("A" * 64)),
        ("last_observation_id", "event:not-observation"),
    ],
)
def test_sensorium_core_rejects_bad_types_bounds_and_identifiers(
    field_name: str,
    value: object,
) -> None:
    with pytest.raises(InputBoundaryError):
        _initial_core(**{field_name: value})


def test_sensorium_core_rejects_partial_initial_or_partial_populated_state() -> None:
    with pytest.raises(InputBoundaryError):
        _initial_core(session_signal_digest="a" * 64)
    with pytest.raises(InputBoundaryError):
        replace(_post_core(), topic_signal_digest=None)
    with pytest.raises(InputBoundaryError):
        replace(_post_core(), episode_observation_count=0)


def test_boundary_signal_digests_have_exact_domains_payloads_and_shape() -> None:
    request = _request()
    result = derive_boundary_signal_digests(request)
    _assert_frozen_kw_only_slotted(
        result,
        (
            "session_signal_digest",
            "goal_ids_signal_digest",
            "participant_ids_signal_digest",
            "tool_signal_digest",
            "topic_signal_digest",
        ),
    )
    assert isinstance(result, BoundarySignalDigestsV1)

    expected = {
        "session_signal_digest": _domain_digest(
            b"aluclu.task2.signal.session.v1",
            canonical_json_bytes("session:alpha"),
        ),
        "goal_ids_signal_digest": _domain_digest(
            b"aluclu.task2.signal.goals.v1",
            canonical_json_bytes(["goal:alpha", "goal:beta"]),
        ),
        "participant_ids_signal_digest": _domain_digest(
            b"aluclu.task2.signal.participants.v1",
            canonical_json_bytes(["participant:assistant", "participant:user"]),
        ),
        "tool_signal_digest": _domain_digest(
            b"aluclu.task2.signal.tool.v1",
            canonical_json_bytes(
                {"tool_invocation_id": "tool:0001", "tool_phase": "result"}
            ),
        ),
        "topic_signal_digest": _domain_digest(
            b"aluclu.task2.signal.topic.v1",
            canonical_json_bytes("topic:travel"),
        ),
    }
    assert {name: getattr(result, name) for name in expected} == expected


def test_boundary_signal_null_payloads_are_hashed_not_stored_as_null_digests() -> None:
    request = _request(
        provenance=_provenance(parent_observation_ids=()),
        topic_key=None,
        goal_ids=(),
        participant_ids=(),
        tool_invocation_id=None,
        tool_phase=None,
    )
    signals = derive_boundary_signal_digests(request)
    assert signals.goal_ids_signal_digest == _domain_digest(
        b"aluclu.task2.signal.goals.v1", canonical_json_bytes([])
    )
    assert signals.participant_ids_signal_digest == _domain_digest(
        b"aluclu.task2.signal.participants.v1", canonical_json_bytes([])
    )
    assert signals.tool_signal_digest == _domain_digest(
        b"aluclu.task2.signal.tool.v1",
        canonical_json_bytes({"tool_invocation_id": None, "tool_phase": None}),
    )
    assert signals.topic_signal_digest == _domain_digest(
        b"aluclu.task2.signal.topic.v1", canonical_json_bytes(None)
    )


def test_request_content_episode_and_core_digests_use_exact_framed_domains() -> None:
    request = _request()
    request_bytes = encode_observation_request(request)
    assert derive_request_digest(request) == _domain_digest(
        b"aluclu.task2.observation-request.v1", request_bytes
    )
    assert derive_content_digest(request.content) == _domain_digest(
        b"aluclu.task2.observation-content.v1", request.content.canonical_bytes
    )

    episode_payload = canonical_json_bytes(
        {
            "boundary_profile_id": BOUNDARY_PROFILE_ID,
            "first_observation_id": request.observation_id,
            "session_id": request.session_id,
        }
    )
    expected_episode_id = "episode:" + _domain_digest(
        b"aluclu.task2.episode-id.v1", episode_payload
    )
    assert (
        derive_episode_id(
            boundary_profile_id=BOUNDARY_PROFILE_ID,
            first_observation_id=request.observation_id,
            session_id=request.session_id,
        )
        == expected_episode_id
    )

    core = _post_core(request)
    assert derive_sensorium_core_state_digest(core) == _domain_digest(
        b"aluclu.task2.sensorium-core-state.v1",
        encode_sensorium_core_state(core),
    )


def test_episode_id_is_deterministic_keyword_only_and_validates_every_input() -> None:
    kwargs = {
        "boundary_profile_id": BOUNDARY_PROFILE_ID,
        "first_observation_id": "obs:first",
        "session_id": "session:alpha",
    }
    assert derive_episode_id(**kwargs) == derive_episode_id(**kwargs)
    assert derive_episode_id(**kwargs).startswith("episode:")
    assert len(derive_episode_id(**kwargs)) == len("episode:") + 64
    with pytest.raises(TypeError):
        derive_episode_id(BOUNDARY_PROFILE_ID, "obs:first", "session:alpha")  # type: ignore[misc]
    for field_name, bad_value in (
        ("boundary_profile_id", "bad"),
        ("first_observation_id", "event:first"),
        ("session_id", "bad session"),
    ):
        bad_kwargs = dict(kwargs)
        bad_kwargs[field_name] = bad_value
        with pytest.raises(InputBoundaryError):
            derive_episode_id(**bad_kwargs)


def test_maximum_goal_and_participant_sets_leave_only_fixed_digests_in_core() -> None:
    goals = tuple(f"g{index:03d}-" + ("a" * 251) for index in range(32))
    participants = tuple(f"p{index:03d}-" + ("b" * 251) for index in range(32))
    request = _request(
        provenance=_provenance(parent_observation_ids=()),
        goal_ids=goals,
        participant_ids=participants,
    )
    core = _post_core(request)
    encoded = encode_sensorium_core_state(core)

    assert len(encoded) <= SENSORIUM_CORE_MAX_BYTES
    assert set(cast(dict[str, Any], strict_json_loads(encoded))) == CORE_KEYS
    assert goals[0].encode("ascii") not in encoded
    assert participants[0].encode("ascii") not in encoded
    assert b"goal_ids" not in encoded
    assert b"participant_ids" not in encoded


def test_core_decoder_rejects_checkpoint_fields_and_checks_size_before_parsing(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    encoded = encode_sensorium_core_state(_initial_core())

    def add_checkpoint(wire: dict[str, Any]) -> None:
        wire["task1_checkpoint"] = {
            "ledger_id": "ledger",
            "snapshot_head_sequence": 0,
            "snapshot_head_hash": ZERO_HASH,
            "next_sequence": 1,
        }

    with pytest.raises(InputBoundaryError):
        decode_sensorium_core_state(_mutated_canonical_bytes(encoded, add_checkpoint))

    def parser_must_not_run(_: bytes) -> object:
        raise AssertionError("oversized core reached JSON parser")

    monkeypatch.setattr(observation_module, "strict_json_loads", parser_must_not_run)
    monkeypatch.setattr(task1_codec, "strict_json_loads", parser_must_not_run)
    with pytest.raises(InputBoundaryError):
        decode_sensorium_core_state(b"x" * (SENSORIUM_CORE_MAX_BYTES + 1))


def test_canonical_observation_builds_all_derived_fields_and_exact_wire_shape() -> None:
    request = _request()
    post_core = _post_core(request)
    observation = _observation(request, post_core_state=post_core)
    _assert_frozen_kw_only_slotted(
        observation,
        (
            "request",
            "request_digest",
            "content_digest",
            "boundary_decision",
            "pre_core_state_digest",
            "post_core_state",
            "post_core_state_digest",
            "pre_append_head_sequence",
            "pre_append_head_hash",
            "boundary_profile_id",
        ),
    )
    wire = canonical_observation_to_json_value(observation)
    assert set(wire) == OBSERVATION_KEYS
    assert wire["schema"] == "aluclu.observation.v1"
    assert set(cast(dict[str, Any], wire["request"])) == REQUEST_KEYS
    assert set(cast(dict[str, Any], wire["post_core_state"])) == CORE_KEYS
    assert set(cast(dict[str, Any], wire["boundary_decision"])) == (
        BOUNDARY_DECISION_KEYS
    )
    assert observation.request_digest == derive_request_digest(request)
    assert observation.content_digest == derive_content_digest(request.content)
    assert observation.post_core_state_digest == derive_sensorium_core_state_digest(
        post_core
    )
    assert canonical_observation_from_json_value(wire) == observation
    assert decode_canonical_observation(encode_canonical_observation(observation)) == (
        observation
    )
    _assert_strict_object_decoder(
        encode_canonical_observation(observation), decode_canonical_observation
    )


def test_boundary_decision_nested_wire_shape_and_continue_rule_are_enforced() -> None:
    request = _request()
    observation = _observation(request)
    wire = canonical_observation_to_json_value(observation)
    decision = cast(dict[str, Any], wire["boundary_decision"])
    assert decision == {
        "schema": "aluclu.episode-boundary-decision.v1",
        "episode_id": derive_episode_id(
            boundary_profile_id=BOUNDARY_PROFILE_ID,
            first_observation_id=request.observation_id,
            session_id=request.session_id,
        ),
        "reasons": ["first_observation"],
    }

    encoded = encode_canonical_observation(observation)

    def unknown_reason(value: dict[str, Any]) -> None:
        cast(dict[str, Any], value["boundary_decision"])["reasons"] = ["unknown"]

    def continue_plus_reason(value: dict[str, Any]) -> None:
        cast(dict[str, Any], value["boundary_decision"])["reasons"] = [
            "time_gap",
            "continue",
        ]

    def extra_decision_key(value: dict[str, Any]) -> None:
        cast(dict[str, Any], value["boundary_decision"])["confidence"] = 1

    for mutation in (unknown_reason, continue_plus_reason, extra_decision_key):
        with pytest.raises(InputBoundaryError):
            decode_canonical_observation(_mutated_canonical_bytes(encoded, mutation))


@pytest.mark.parametrize(
    ("field_name", "value"),
    [
        ("pre_core_state_digest", "a" * 63),
        ("pre_core_state_digest", "A" * 64),
        ("pre_append_head_sequence", True),
        ("pre_append_head_sequence", -1),
        ("pre_append_head_sequence", MAX_I63 + 1),
        ("pre_append_head_hash", "0" * 63),
        ("pre_append_head_hash", "F" * 64),
        ("boundary_profile_id", "boundary-profile:" + ("A" * 64)),
    ],
)
def test_canonical_observation_builder_rejects_invalid_envelope_inputs(
    field_name: str,
    value: object,
) -> None:
    request = _request()
    kwargs: dict[str, object] = {
        "request": request,
        "boundary_decision": _decision(request),
        "pre_core_state_digest": derive_sensorium_core_state_digest(_initial_core()),
        "post_core_state": _post_core(request),
        "pre_append_head_sequence": 0,
        "pre_append_head_hash": ZERO_HASH,
        "boundary_profile_id": BOUNDARY_PROFILE_ID,
    }
    kwargs[field_name] = value
    with pytest.raises(InputBoundaryError):
        build_canonical_observation(**kwargs)  # type: ignore[arg-type]


def test_canonical_observation_builder_rejects_profile_and_episode_mismatches() -> None:
    request = _request()
    other_profile = "boundary-profile:" + ("c" * 64)
    with pytest.raises(InputBoundaryError):
        build_canonical_observation(
            request=request,
            boundary_decision=_decision(request),
            pre_core_state_digest=derive_sensorium_core_state_digest(_initial_core()),
            post_core_state=replace(_post_core(request), boundary_profile_id=other_profile),
            pre_append_head_sequence=0,
            pre_append_head_hash=ZERO_HASH,
            boundary_profile_id=BOUNDARY_PROFILE_ID,
        )
    with pytest.raises(InputBoundaryError):
        build_canonical_observation(
            request=request,
            boundary_decision=EpisodeBoundaryDecisionV1(
                episode_id="episode:" + ("c" * 64),
                reasons=(EpisodeBoundaryReason.FIRST_OBSERVATION,),
            ),
            pre_core_state_digest=derive_sensorium_core_state_digest(_initial_core()),
            post_core_state=_post_core(request),
            pre_append_head_sequence=0,
            pre_append_head_hash=ZERO_HASH,
            boundary_profile_id=BOUNDARY_PROFILE_ID,
        )


def test_observation_decoder_recomputes_request_content_and_post_core_digests() -> None:
    encoded = encode_canonical_observation(_observation())

    def mutate_request(value: dict[str, Any]) -> None:
        cast(dict[str, Any], value["request"])["turn_id"] = "turn:tampered"

    def mutate_content(value: dict[str, Any]) -> None:
        cast(dict[str, Any], value["request"])["content"] = {"tampered": True}

    def mutate_post_core(value: dict[str, Any]) -> None:
        cast(dict[str, Any], value["post_core_state"])[
            "episode_observation_count"
        ] = 2

    def mutate_request_digest(value: dict[str, Any]) -> None:
        value["request_digest"] = "d" * 64

    def mutate_content_digest(value: dict[str, Any]) -> None:
        value["content_digest"] = "e" * 64

    def mutate_post_core_digest(value: dict[str, Any]) -> None:
        value["post_core_state_digest"] = "f" * 64

    for mutation in (
        mutate_request,
        mutate_content,
        mutate_post_core,
        mutate_request_digest,
        mutate_content_digest,
        mutate_post_core_digest,
    ):
        with pytest.raises(InputBoundaryError):
            decode_canonical_observation(_mutated_canonical_bytes(encoded, mutation))


def test_post_core_and_digest_basis_exclude_task1_checkpoint_and_post_head() -> None:
    observation = _observation()
    core_bytes = encode_sensorium_core_state(observation.post_core_state)
    wire = canonical_observation_to_json_value(observation)
    post_core_wire = cast(dict[str, Any], wire["post_core_state"])

    assert set(post_core_wire) == CORE_KEYS
    for forbidden in (
        "task1_checkpoint",
        "ledger_id",
        "snapshot_head_sequence",
        "snapshot_head_hash",
        "next_sequence",
        "post_append_head_hash",
    ):
        assert forbidden not in post_core_wire
        assert forbidden.encode("ascii") not in core_bytes

    build_parameters = inspect.signature(build_canonical_observation).parameters
    assert "post_append_head_hash" not in build_parameters
    digest_parameters = inspect.signature(
        derive_sensorium_core_state_digest
    ).parameters
    assert tuple(digest_parameters) == ("core",)


def _observation_with_exact_encoded_size(target_size: int) -> CanonicalObservationV1:
    low = 0
    high = target_size
    while low <= high:
        filler_size = (low + high) // 2
        request = _request(
            provenance=_provenance(parent_observation_ids=()),
            content=CanonicalJsonValue.from_value({"blob": "x" * filler_size}),
            retrieval_text=None,
            topic_key=None,
            goal_ids=(),
            participant_ids=(),
            tool_invocation_id=None,
            tool_phase=None,
        )
        try:
            observation = _observation(request)
        except InputBoundaryError:
            high = filler_size - 1
            continue
        encoded_size = len(encode_canonical_observation(observation))
        if encoded_size == target_size:
            return observation
        if encoded_size < target_size:
            low = filler_size + 1
        else:
            high = filler_size - 1
    raise AssertionError(f"could not construct {target_size}-byte envelope")


def test_complete_observation_envelope_accepts_262144_and_rejects_262145() -> None:
    maximum = _observation_with_exact_encoded_size(OBSERVATION_ENVELOPE_MAX_BYTES)
    encoded = encode_canonical_observation(maximum)
    assert len(encoded) == OBSERVATION_ENVELOPE_MAX_BYTES
    assert decode_canonical_observation(encoded) == maximum

    request_value = maximum.request.content.to_value()
    assert type(request_value) is dict
    oversized_content = dict(cast(dict[str, Any], request_value))
    oversized_content["blob"] = cast(str, oversized_content["blob"]) + "x"
    oversized_request = replace(
        maximum.request,
        content=CanonicalJsonValue.from_value(oversized_content),
    )
    with pytest.raises(InputBoundaryError):
        _observation(oversized_request)


def test_oversized_observation_is_rejected_before_json_parsing(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def parser_must_not_run(_: bytes) -> object:
        raise AssertionError("oversized observation reached JSON parser")

    monkeypatch.setattr(observation_module, "strict_json_loads", parser_must_not_run)
    monkeypatch.setattr(task1_codec, "strict_json_loads", parser_must_not_run)
    with pytest.raises(InputBoundaryError):
        decode_canonical_observation(b"x" * (OBSERVATION_ENVELOPE_MAX_BYTES + 1))
