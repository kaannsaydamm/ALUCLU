from __future__ import annotations

import hashlib
import re
import struct
from dataclasses import dataclass
from enum import Enum
from typing import Any, TypeAlias, cast

from .codec import canonical_json_bytes, strict_json_loads, validate_event_id
from .contracts import InputBoundaryError, JsonValue
from .recall_features import active_normalizer_id, search_view_utf8

MAX_I63 = (1 << 63) - 1
MAX_COLLECTION_ITEMS = 32
MAX_RETRIEVAL_TEXT_BYTES = 4_096
SENSORIUM_CORE_MAX_BYTES = 3_072
OBSERVATION_ENVELOPE_MAX_BYTES = 262_144

_PROVENANCE_SCHEMA = "aluclu.provenance.v1"
_OBSERVATION_REQUEST_SCHEMA = "aluclu.observation-request.v1"
_BOUNDARY_DECISION_SCHEMA = "aluclu.episode-boundary-decision.v1"
_SENSORIUM_CORE_SCHEMA = "aluclu.sensorium-core-state.v1"
_OBSERVATION_SCHEMA = "aluclu.observation.v1"

_REQUEST_DOMAIN = b"aluclu.task2.observation-request.v1"
_CONTENT_DOMAIN = b"aluclu.task2.observation-content.v1"
_EPISODE_DOMAIN = b"aluclu.task2.episode-id.v1"
_CORE_DOMAIN = b"aluclu.task2.sensorium-core-state.v1"
_SESSION_SIGNAL_DOMAIN = b"aluclu.task2.signal.session.v1"
_GOAL_SIGNAL_DOMAIN = b"aluclu.task2.signal.goals.v1"
_PARTICIPANT_SIGNAL_DOMAIN = b"aluclu.task2.signal.participants.v1"
_TOOL_SIGNAL_DOMAIN = b"aluclu.task2.signal.tool.v1"
_TOPIC_SIGNAL_DOMAIN = b"aluclu.task2.signal.topic.v1"

_OBSERVATION_ID_PATTERN = re.compile(r"obs:[A-Za-z0-9][A-Za-z0-9._:-]{0,251}\Z")
_SOURCE_ID_PATTERN = re.compile(r"[A-Za-z0-9][A-Za-z0-9._:@+-]{0,127}\Z")
_CAPTURE_TOKEN_PATTERN = re.compile(r"[A-Za-z0-9][A-Za-z0-9._+-]{0,63}\Z")
_BOUNDARY_PROFILE_ID_PATTERN = re.compile(r"boundary-profile:[0-9a-f]{64}\Z")
_EPISODE_ID_PATTERN = re.compile(r"episode:[0-9a-f]{64}\Z")
_DIGEST_PATTERN = re.compile(r"[0-9a-f]{64}\Z")
_PROVENANCE_KEYS = frozenset(
    {
        "schema",
        "source_kind",
        "source_instance_id",
        "origin_id",
        "observed_at_ns",
        "parent_observation_ids",
        "capture_method",
        "capture_version",
    }
)
_REQUEST_KEYS = frozenset(
    {
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
)
_BOUNDARY_DECISION_KEYS = frozenset({"schema", "episode_id", "reasons"})
_CORE_KEYS = frozenset(
    {
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
)
_OBSERVATION_KEYS = frozenset(
    {
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
)

_JsonObject: TypeAlias = dict[str, JsonValue]


class SourceKind(str, Enum):
    USER = "user"
    TOOL = "tool"
    WEB = "web"
    DATABASE = "database"
    FILE = "file"
    ENVIRONMENT = "environment"
    MODEL = "model"


class EpisodeBoundaryReason(str, Enum):
    FIRST_OBSERVATION = "first_observation"
    PROFILE_CHANGED = "profile_changed"
    FORCED = "forced"
    SESSION_CHANGED = "session_changed"
    TIME_GAP = "time_gap"
    GOAL_CHANGED = "goal_changed"
    TOOL_PHASE_CHANGED = "tool_phase_changed"
    PARTICIPANTS_CHANGED = "participants_changed"
    TOPIC_KEY_CHANGED = "topic_key_changed"
    EPISODE_COUNT_LIMIT = "episode_count_limit"
    EPISODE_BYTE_LIMIT = "episode_byte_limit"
    CONTINUE = "continue"


_BOUNDARY_REASON_PRECEDENCE = {
    reason: position for position, reason in enumerate(EpisodeBoundaryReason)
}


@dataclass(frozen=True, slots=True, init=False)
class CanonicalJsonValue:
    """A JSON value retained only as validated canonical bytes.

    Parsing on each access prevents mutable containers from crossing the
    observation boundary in either direction.
    """

    canonical_bytes: bytes

    def __new__(cls) -> CanonicalJsonValue:
        raise TypeError("use from_value or from_canonical_bytes")

    @classmethod
    def from_value(cls, value: JsonValue) -> CanonicalJsonValue:
        return cls._from_validated_bytes(canonical_json_bytes(value))

    @classmethod
    def from_canonical_bytes(cls, data: bytes) -> CanonicalJsonValue:
        value = _decode_canonical_json(data)
        canonical = canonical_json_bytes(value)
        if canonical != data:
            raise InputBoundaryError("JSON bytes are not canonical")
        return cls._from_validated_bytes(canonical)

    @classmethod
    def _from_validated_bytes(cls, data: bytes) -> CanonicalJsonValue:
        instance = object.__new__(cls)
        object.__setattr__(instance, "canonical_bytes", data)
        return instance

    def to_value(self) -> JsonValue:
        return strict_json_loads(self.canonical_bytes)


@dataclass(frozen=True, kw_only=True, slots=True)
class ProvenanceV1:
    source_kind: SourceKind
    source_instance_id: str
    origin_id: str
    observed_at_ns: int
    parent_observation_ids: tuple[str, ...]
    capture_method: str
    capture_version: str

    def __post_init__(self) -> None:
        if type(self.source_kind) is not SourceKind:
            raise InputBoundaryError("source_kind must be a SourceKind")
        _validate_ascii_token(
            self.source_instance_id,
            pattern=_SOURCE_ID_PATTERN,
            field_name="source_instance_id",
        )
        _validate_ascii_token(
            self.origin_id,
            pattern=_SOURCE_ID_PATTERN,
            field_name="origin_id",
        )
        _validate_i63(self.observed_at_ns, "observed_at_ns")
        _validate_sorted_id_tuple(
            self.parent_observation_ids,
            field_name="parent_observation_ids",
            validator=_validate_observation_id,
        )
        _validate_ascii_token(
            self.capture_method,
            pattern=_CAPTURE_TOKEN_PATTERN,
            field_name="capture_method",
        )
        _validate_ascii_token(
            self.capture_version,
            pattern=_CAPTURE_TOKEN_PATTERN,
            field_name="capture_version",
        )


@dataclass(frozen=True, kw_only=True, slots=True)
class ObservationRequestV1:
    observation_id: str
    session_id: str
    turn_id: str
    provenance: ProvenanceV1
    content: CanonicalJsonValue
    retrieval_text: str | None
    topic_key: str | None
    goal_ids: tuple[str, ...]
    participant_ids: tuple[str, ...]
    tool_invocation_id: str | None
    tool_phase: str | None
    force_boundary: bool

    def __post_init__(self) -> None:
        _validate_observation_id(self.observation_id)
        _validate_event_id_field(self.session_id, "session_id")
        _validate_event_id_field(self.turn_id, "turn_id")
        if type(self.provenance) is not ProvenanceV1:
            raise InputBoundaryError("provenance must be ProvenanceV1")
        if type(self.content) is not CanonicalJsonValue:
            raise InputBoundaryError("content must be CanonicalJsonValue")
        if self.observation_id in self.provenance.parent_observation_ids:
            raise InputBoundaryError("an observation cannot be its own parent")
        _validate_retrieval_text(self.retrieval_text)
        _validate_optional_ascii_token(
            self.topic_key,
            pattern=_SOURCE_ID_PATTERN,
            field_name="topic_key",
        )
        _validate_sorted_id_tuple(
            self.goal_ids,
            field_name="goal_ids",
            validator=validate_event_id,
        )
        _validate_sorted_id_tuple(
            self.participant_ids,
            field_name="participant_ids",
            validator=validate_event_id,
        )
        if self.tool_invocation_id is not None:
            _validate_event_id_field(self.tool_invocation_id, "tool_invocation_id")
        _validate_optional_ascii_token(
            self.tool_phase,
            pattern=_CAPTURE_TOKEN_PATTERN,
            field_name="tool_phase",
        )
        if type(self.force_boundary) is not bool:
            raise InputBoundaryError("force_boundary must be a bool")


@dataclass(frozen=True, kw_only=True, slots=True)
class EpisodeBoundaryDecisionV1:
    episode_id: str
    reasons: tuple[EpisodeBoundaryReason, ...]

    def __post_init__(self) -> None:
        _validate_episode_id(self.episode_id)
        if type(self.reasons) is not tuple or not self.reasons:
            raise InputBoundaryError("reasons must be a nonempty tuple")
        if any(type(reason) is not EpisodeBoundaryReason for reason in self.reasons):
            raise InputBoundaryError("every reason must be an EpisodeBoundaryReason")
        if len(set(self.reasons)) != len(self.reasons):
            raise InputBoundaryError("boundary reasons must be unique")
        if tuple(sorted(self.reasons, key=_BOUNDARY_REASON_PRECEDENCE.__getitem__)) != (
            self.reasons
        ):
            raise InputBoundaryError("boundary reasons are not in precedence order")
        if EpisodeBoundaryReason.CONTINUE in self.reasons and self.reasons != (
            EpisodeBoundaryReason.CONTINUE,
        ):
            raise InputBoundaryError("continue must be the sole boundary reason")


@dataclass(frozen=True, kw_only=True, slots=True)
class SensoriumCoreStateV1:
    boundary_profile_id: str
    session_signal_digest: str | None
    current_episode_id: str | None
    episode_observation_count: int
    episode_canonical_request_bytes: int
    goal_ids_signal_digest: str | None
    participant_ids_signal_digest: str | None
    tool_signal_digest: str | None
    topic_signal_digest: str | None
    last_observation_id: str | None
    last_observation_sequence: int
    last_observed_at_ns: int | None

    def __post_init__(self) -> None:
        _validate_boundary_profile_id(self.boundary_profile_id)
        for field_name, value in (
            ("session_signal_digest", self.session_signal_digest),
            ("goal_ids_signal_digest", self.goal_ids_signal_digest),
            ("participant_ids_signal_digest", self.participant_ids_signal_digest),
            ("tool_signal_digest", self.tool_signal_digest),
            ("topic_signal_digest", self.topic_signal_digest),
        ):
            if value is not None:
                _validate_digest(value, field_name)
        if self.current_episode_id is not None:
            _validate_episode_id(self.current_episode_id)
        if self.last_observation_id is not None:
            _validate_observation_id(self.last_observation_id)
        for field_name, value in (
            ("episode_observation_count", self.episode_observation_count),
            (
                "episode_canonical_request_bytes",
                self.episode_canonical_request_bytes,
            ),
            ("last_observation_sequence", self.last_observation_sequence),
        ):
            _validate_i63(value, field_name)
        if self.last_observed_at_ns is not None:
            _validate_i63(self.last_observed_at_ns, "last_observed_at_ns")

        nullable_values = (
            self.session_signal_digest,
            self.current_episode_id,
            self.goal_ids_signal_digest,
            self.participant_ids_signal_digest,
            self.tool_signal_digest,
            self.topic_signal_digest,
            self.last_observation_id,
            self.last_observed_at_ns,
        )
        if all(value is None for value in nullable_values):
            if (
                self.episode_observation_count != 0
                or self.episode_canonical_request_bytes != 0
                or self.last_observation_sequence != 0
            ):
                raise InputBoundaryError("initial core counters must be zero")
            return
        if any(value is None for value in nullable_values):
            raise InputBoundaryError("sensorium core cannot be partially populated")
        if (
            self.episode_observation_count == 0
            or self.episode_canonical_request_bytes == 0
            or self.last_observation_sequence == 0
        ):
            raise InputBoundaryError("populated core counters must be positive")


@dataclass(frozen=True, kw_only=True, slots=True)
class BoundarySignalDigestsV1:
    session_signal_digest: str
    goal_ids_signal_digest: str
    participant_ids_signal_digest: str
    tool_signal_digest: str
    topic_signal_digest: str

    def __post_init__(self) -> None:
        for field_name, value in (
            ("session_signal_digest", self.session_signal_digest),
            ("goal_ids_signal_digest", self.goal_ids_signal_digest),
            ("participant_ids_signal_digest", self.participant_ids_signal_digest),
            ("tool_signal_digest", self.tool_signal_digest),
            ("topic_signal_digest", self.topic_signal_digest),
        ):
            _validate_digest(value, field_name)


@dataclass(frozen=True, kw_only=True, slots=True)
class CanonicalObservationV1:
    request: ObservationRequestV1
    request_digest: str
    content_digest: str
    boundary_decision: EpisodeBoundaryDecisionV1
    pre_core_state_digest: str
    post_core_state: SensoriumCoreStateV1
    post_core_state_digest: str
    pre_append_head_sequence: int
    pre_append_head_hash: str
    boundary_profile_id: str

    def __post_init__(self) -> None:
        if type(self.request) is not ObservationRequestV1:
            raise InputBoundaryError("request must be ObservationRequestV1")
        if type(self.boundary_decision) is not EpisodeBoundaryDecisionV1:
            raise InputBoundaryError(
                "boundary_decision must be EpisodeBoundaryDecisionV1"
            )
        if type(self.post_core_state) is not SensoriumCoreStateV1:
            raise InputBoundaryError("post_core_state must be SensoriumCoreStateV1")
        for field_name, value in (
            ("request_digest", self.request_digest),
            ("content_digest", self.content_digest),
            ("pre_core_state_digest", self.pre_core_state_digest),
            ("post_core_state_digest", self.post_core_state_digest),
            ("pre_append_head_hash", self.pre_append_head_hash),
        ):
            _validate_digest(value, field_name)
        _validate_i63(self.pre_append_head_sequence, "pre_append_head_sequence")
        _validate_boundary_profile_id(self.boundary_profile_id)

        if self.request_digest != derive_request_digest(self.request):
            raise InputBoundaryError("request_digest does not match request")
        if self.content_digest != derive_content_digest(self.request.content):
            raise InputBoundaryError("content_digest does not match content")
        if self.post_core_state_digest != derive_sensorium_core_state_digest(
            self.post_core_state
        ):
            raise InputBoundaryError("post_core_state_digest does not match core")
        if self.post_core_state.boundary_profile_id != self.boundary_profile_id:
            raise InputBoundaryError("post core uses a different boundary profile")
        if self.post_core_state.current_episode_id != self.boundary_decision.episode_id:
            raise InputBoundaryError(
                "boundary decision does not match post core episode"
            )

        encoded = canonical_json_bytes(
            cast(JsonValue, _canonical_observation_wire(self))
        )
        if len(encoded) > OBSERVATION_ENVELOPE_MAX_BYTES:
            raise InputBoundaryError("canonical observation exceeds 262144 bytes")


def encode_provenance(provenance: ProvenanceV1) -> bytes:
    if type(provenance) is not ProvenanceV1:
        raise InputBoundaryError("provenance must be ProvenanceV1")
    return canonical_json_bytes(cast(JsonValue, _provenance_to_json_value(provenance)))


def decode_provenance(data: bytes) -> ProvenanceV1:
    return _provenance_from_json_value(_decode_canonical_json(data))


def observation_request_to_json_value(request: ObservationRequestV1) -> _JsonObject:
    if type(request) is not ObservationRequestV1:
        raise InputBoundaryError("request must be ObservationRequestV1")
    return _observation_request_wire(request)


def observation_request_from_json_value(value: JsonValue) -> ObservationRequestV1:
    wire = _require_object(
        value, keys=_REQUEST_KEYS, schema=_OBSERVATION_REQUEST_SCHEMA
    )
    return ObservationRequestV1(
        observation_id=_required_str(wire, "observation_id"),
        session_id=_required_str(wire, "session_id"),
        turn_id=_required_str(wire, "turn_id"),
        provenance=_provenance_from_json_value(wire["provenance"]),
        content=CanonicalJsonValue.from_value(wire["content"]),
        retrieval_text=_optional_str(wire, "retrieval_text"),
        topic_key=_optional_str(wire, "topic_key"),
        goal_ids=_string_tuple(wire, "goal_ids"),
        participant_ids=_string_tuple(wire, "participant_ids"),
        tool_invocation_id=_optional_str(wire, "tool_invocation_id"),
        tool_phase=_optional_str(wire, "tool_phase"),
        force_boundary=_required_bool(wire, "force_boundary"),
    )


def encode_observation_request(request: ObservationRequestV1) -> bytes:
    return canonical_json_bytes(
        cast(JsonValue, observation_request_to_json_value(request))
    )


def decode_observation_request(data: bytes) -> ObservationRequestV1:
    return observation_request_from_json_value(_decode_canonical_json(data))


def derive_request_digest(request: ObservationRequestV1) -> str:
    return _domain_digest(_REQUEST_DOMAIN, encode_observation_request(request))


def derive_content_digest(content: CanonicalJsonValue) -> str:
    if type(content) is not CanonicalJsonValue:
        raise InputBoundaryError("content must be CanonicalJsonValue")
    return _domain_digest(_CONTENT_DOMAIN, content.canonical_bytes)


def derive_episode_id(
    *,
    boundary_profile_id: str,
    first_observation_id: str,
    session_id: str,
) -> str:
    _validate_boundary_profile_id(boundary_profile_id)
    _validate_observation_id(first_observation_id)
    _validate_event_id_field(session_id, "session_id")
    payload = canonical_json_bytes(
        cast(
            JsonValue,
            {
                "boundary_profile_id": boundary_profile_id,
                "first_observation_id": first_observation_id,
                "session_id": session_id,
            },
        )
    )
    return f"episode:{_domain_digest(_EPISODE_DOMAIN, payload)}"


def sensorium_core_state_to_json_value(core: SensoriumCoreStateV1) -> _JsonObject:
    if type(core) is not SensoriumCoreStateV1:
        raise InputBoundaryError("core must be SensoriumCoreStateV1")
    return _sensorium_core_wire(core)


def sensorium_core_state_from_json_value(value: JsonValue) -> SensoriumCoreStateV1:
    wire = _require_object(value, keys=_CORE_KEYS, schema=_SENSORIUM_CORE_SCHEMA)
    return SensoriumCoreStateV1(
        boundary_profile_id=_required_str(wire, "boundary_profile_id"),
        session_signal_digest=_optional_str(wire, "session_signal_digest"),
        current_episode_id=_optional_str(wire, "current_episode_id"),
        episode_observation_count=_required_int(wire, "episode_observation_count"),
        episode_canonical_request_bytes=_required_int(
            wire, "episode_canonical_request_bytes"
        ),
        goal_ids_signal_digest=_optional_str(wire, "goal_ids_signal_digest"),
        participant_ids_signal_digest=_optional_str(
            wire, "participant_ids_signal_digest"
        ),
        tool_signal_digest=_optional_str(wire, "tool_signal_digest"),
        topic_signal_digest=_optional_str(wire, "topic_signal_digest"),
        last_observation_id=_optional_str(wire, "last_observation_id"),
        last_observation_sequence=_required_int(wire, "last_observation_sequence"),
        last_observed_at_ns=_optional_int(wire, "last_observed_at_ns"),
    )


def encode_sensorium_core_state(core: SensoriumCoreStateV1) -> bytes:
    encoded = canonical_json_bytes(
        cast(JsonValue, sensorium_core_state_to_json_value(core))
    )
    if len(encoded) > SENSORIUM_CORE_MAX_BYTES:
        raise InputBoundaryError("sensorium core exceeds 3072 bytes")
    return encoded


def decode_sensorium_core_state(data: bytes) -> SensoriumCoreStateV1:
    value = _decode_canonical_json(data, max_bytes=SENSORIUM_CORE_MAX_BYTES)
    return sensorium_core_state_from_json_value(value)


def derive_sensorium_core_state_digest(core: SensoriumCoreStateV1) -> str:
    return _domain_digest(_CORE_DOMAIN, encode_sensorium_core_state(core))


def derive_boundary_signal_digests(
    request: ObservationRequestV1,
) -> BoundarySignalDigestsV1:
    if type(request) is not ObservationRequestV1:
        raise InputBoundaryError("request must be ObservationRequestV1")
    return BoundarySignalDigestsV1(
        session_signal_digest=_domain_json_digest(
            _SESSION_SIGNAL_DOMAIN, request.session_id
        ),
        goal_ids_signal_digest=_domain_json_digest(
            _GOAL_SIGNAL_DOMAIN, list(request.goal_ids)
        ),
        participant_ids_signal_digest=_domain_json_digest(
            _PARTICIPANT_SIGNAL_DOMAIN, list(request.participant_ids)
        ),
        tool_signal_digest=_domain_json_digest(
            _TOOL_SIGNAL_DOMAIN,
            {
                "tool_invocation_id": request.tool_invocation_id,
                "tool_phase": request.tool_phase,
            },
        ),
        topic_signal_digest=_domain_json_digest(
            _TOPIC_SIGNAL_DOMAIN, request.topic_key
        ),
    )


def build_canonical_observation(
    *,
    request: ObservationRequestV1,
    boundary_decision: EpisodeBoundaryDecisionV1,
    pre_core_state_digest: str,
    post_core_state: SensoriumCoreStateV1,
    pre_append_head_sequence: int,
    pre_append_head_hash: str,
    boundary_profile_id: str,
) -> CanonicalObservationV1:
    return CanonicalObservationV1(
        request=request,
        request_digest=derive_request_digest(request),
        content_digest=derive_content_digest(request.content),
        boundary_decision=boundary_decision,
        pre_core_state_digest=pre_core_state_digest,
        post_core_state=post_core_state,
        post_core_state_digest=derive_sensorium_core_state_digest(post_core_state),
        pre_append_head_sequence=pre_append_head_sequence,
        pre_append_head_hash=pre_append_head_hash,
        boundary_profile_id=boundary_profile_id,
    )


def canonical_observation_to_json_value(
    observation: CanonicalObservationV1,
) -> _JsonObject:
    if type(observation) is not CanonicalObservationV1:
        raise InputBoundaryError("observation must be CanonicalObservationV1")
    return _canonical_observation_wire(observation)


def canonical_observation_from_json_value(value: JsonValue) -> CanonicalObservationV1:
    wire = _require_object(value, keys=_OBSERVATION_KEYS, schema=_OBSERVATION_SCHEMA)
    return CanonicalObservationV1(
        request=observation_request_from_json_value(wire["request"]),
        request_digest=_required_str(wire, "request_digest"),
        content_digest=_required_str(wire, "content_digest"),
        boundary_decision=_boundary_decision_from_json_value(wire["boundary_decision"]),
        pre_core_state_digest=_required_str(wire, "pre_core_state_digest"),
        post_core_state=sensorium_core_state_from_json_value(wire["post_core_state"]),
        post_core_state_digest=_required_str(wire, "post_core_state_digest"),
        pre_append_head_sequence=_required_int(wire, "pre_append_head_sequence"),
        pre_append_head_hash=_required_str(wire, "pre_append_head_hash"),
        boundary_profile_id=_required_str(wire, "boundary_profile_id"),
    )


def canonical_observation_matches_position(
    observation: CanonicalObservationV1,
    event_id: str,
    sequence: int,
) -> bool:
    """Bind a canonical observation to the ledger slot that authenticates it."""

    return (
        observation.request.observation_id == event_id
        and observation.pre_append_head_sequence + 1 == sequence
        and observation.post_core_state.last_observation_id == event_id
        and observation.post_core_state.last_observation_sequence == sequence
    )


def encode_canonical_observation(observation: CanonicalObservationV1) -> bytes:
    encoded = canonical_json_bytes(
        cast(JsonValue, canonical_observation_to_json_value(observation))
    )
    if len(encoded) > OBSERVATION_ENVELOPE_MAX_BYTES:
        raise InputBoundaryError("canonical observation exceeds 262144 bytes")
    return encoded


def decode_canonical_observation(data: bytes) -> CanonicalObservationV1:
    value = _decode_canonical_json(data, max_bytes=OBSERVATION_ENVELOPE_MAX_BYTES)
    return canonical_observation_from_json_value(value)


def _provenance_to_json_value(provenance: ProvenanceV1) -> _JsonObject:
    return {
        "schema": _PROVENANCE_SCHEMA,
        "source_kind": provenance.source_kind.value,
        "source_instance_id": provenance.source_instance_id,
        "origin_id": provenance.origin_id,
        "observed_at_ns": provenance.observed_at_ns,
        "parent_observation_ids": list(provenance.parent_observation_ids),
        "capture_method": provenance.capture_method,
        "capture_version": provenance.capture_version,
    }


def _provenance_from_json_value(value: JsonValue) -> ProvenanceV1:
    wire = _require_object(value, keys=_PROVENANCE_KEYS, schema=_PROVENANCE_SCHEMA)
    raw_source_kind = _required_str(wire, "source_kind")
    try:
        source_kind = SourceKind(raw_source_kind)
    except ValueError as exc:
        raise InputBoundaryError("unknown source_kind") from exc
    return ProvenanceV1(
        source_kind=source_kind,
        source_instance_id=_required_str(wire, "source_instance_id"),
        origin_id=_required_str(wire, "origin_id"),
        observed_at_ns=_required_int(wire, "observed_at_ns"),
        parent_observation_ids=_string_tuple(wire, "parent_observation_ids"),
        capture_method=_required_str(wire, "capture_method"),
        capture_version=_required_str(wire, "capture_version"),
    )


def _observation_request_wire(request: ObservationRequestV1) -> _JsonObject:
    return {
        "schema": _OBSERVATION_REQUEST_SCHEMA,
        "observation_id": request.observation_id,
        "session_id": request.session_id,
        "turn_id": request.turn_id,
        "provenance": _provenance_to_json_value(request.provenance),
        "content": request.content.to_value(),
        "retrieval_text": request.retrieval_text,
        "topic_key": request.topic_key,
        "goal_ids": list(request.goal_ids),
        "participant_ids": list(request.participant_ids),
        "tool_invocation_id": request.tool_invocation_id,
        "tool_phase": request.tool_phase,
        "force_boundary": request.force_boundary,
    }


def _boundary_decision_to_json_value(
    decision: EpisodeBoundaryDecisionV1,
) -> _JsonObject:
    return {
        "schema": _BOUNDARY_DECISION_SCHEMA,
        "episode_id": decision.episode_id,
        "reasons": [reason.value for reason in decision.reasons],
    }


def _boundary_decision_from_json_value(value: JsonValue) -> EpisodeBoundaryDecisionV1:
    wire = _require_object(
        value, keys=_BOUNDARY_DECISION_KEYS, schema=_BOUNDARY_DECISION_SCHEMA
    )
    raw_reasons = wire["reasons"]
    if type(raw_reasons) is not list:
        raise InputBoundaryError("reasons must be an array")
    reasons: list[EpisodeBoundaryReason] = []
    for raw_reason in raw_reasons:
        if type(raw_reason) is not str:
            raise InputBoundaryError("boundary reason must be a string")
        try:
            reasons.append(EpisodeBoundaryReason(raw_reason))
        except ValueError as exc:
            raise InputBoundaryError("unknown boundary reason") from exc
    return EpisodeBoundaryDecisionV1(
        episode_id=_required_str(wire, "episode_id"),
        reasons=tuple(reasons),
    )


def _sensorium_core_wire(core: SensoriumCoreStateV1) -> _JsonObject:
    return {
        "schema": _SENSORIUM_CORE_SCHEMA,
        "boundary_profile_id": core.boundary_profile_id,
        "session_signal_digest": core.session_signal_digest,
        "current_episode_id": core.current_episode_id,
        "episode_observation_count": core.episode_observation_count,
        "episode_canonical_request_bytes": core.episode_canonical_request_bytes,
        "goal_ids_signal_digest": core.goal_ids_signal_digest,
        "participant_ids_signal_digest": core.participant_ids_signal_digest,
        "tool_signal_digest": core.tool_signal_digest,
        "topic_signal_digest": core.topic_signal_digest,
        "last_observation_id": core.last_observation_id,
        "last_observation_sequence": core.last_observation_sequence,
        "last_observed_at_ns": core.last_observed_at_ns,
    }


def _canonical_observation_wire(observation: CanonicalObservationV1) -> _JsonObject:
    return {
        "schema": _OBSERVATION_SCHEMA,
        "request": _observation_request_wire(observation.request),
        "request_digest": observation.request_digest,
        "content_digest": observation.content_digest,
        "boundary_decision": _boundary_decision_to_json_value(
            observation.boundary_decision
        ),
        "pre_core_state_digest": observation.pre_core_state_digest,
        "post_core_state": _sensorium_core_wire(observation.post_core_state),
        "post_core_state_digest": observation.post_core_state_digest,
        "pre_append_head_sequence": observation.pre_append_head_sequence,
        "pre_append_head_hash": observation.pre_append_head_hash,
        "boundary_profile_id": observation.boundary_profile_id,
    }


def _decode_canonical_json(data: bytes, *, max_bytes: int | None = None) -> JsonValue:
    if type(data) is not bytes:
        raise InputBoundaryError("JSON input must be bytes")
    if max_bytes is not None and len(data) > max_bytes:
        raise InputBoundaryError("canonical input exceeds its byte boundary")
    value = strict_json_loads(data)
    if canonical_json_bytes(value) != data:
        raise InputBoundaryError("JSON bytes are not canonical")
    return value


def _require_object(
    value: JsonValue,
    *,
    keys: frozenset[str],
    schema: str,
) -> _JsonObject:
    if type(value) is not dict:
        raise InputBoundaryError("wire value must be an object")
    wire = cast(_JsonObject, value)
    if set(wire) != keys:
        raise InputBoundaryError("wire object has an invalid key set")
    if wire.get("schema") != schema:
        raise InputBoundaryError("wire object has an invalid schema")
    return wire


def _required_str(wire: _JsonObject, field_name: str) -> str:
    value = wire[field_name]
    if type(value) is not str:
        raise InputBoundaryError(f"{field_name} must be a string")
    return value


def _optional_str(wire: _JsonObject, field_name: str) -> str | None:
    value = wire[field_name]
    if value is not None and type(value) is not str:
        raise InputBoundaryError(f"{field_name} must be a string or null")
    return cast(str | None, value)


def _required_int(wire: _JsonObject, field_name: str) -> int:
    value = wire[field_name]
    if type(value) is not int:
        raise InputBoundaryError(f"{field_name} must be an integer")
    return value


def _optional_int(wire: _JsonObject, field_name: str) -> int | None:
    value = wire[field_name]
    if value is not None and type(value) is not int:
        raise InputBoundaryError(f"{field_name} must be an integer or null")
    return cast(int | None, value)


def _required_bool(wire: _JsonObject, field_name: str) -> bool:
    value = wire[field_name]
    if type(value) is not bool:
        raise InputBoundaryError(f"{field_name} must be a bool")
    return value


def _string_tuple(wire: _JsonObject, field_name: str) -> tuple[str, ...]:
    value = wire[field_name]
    if type(value) is not list or any(type(item) is not str for item in value):
        raise InputBoundaryError(f"{field_name} must be an array of strings")
    return tuple(cast(list[str], value))


def _validate_i63(value: int, field_name: str) -> int:
    if type(value) is not int or not 0 <= value <= MAX_I63:
        raise InputBoundaryError(f"{field_name} is outside the uint63 boundary")
    return value


def _validate_ascii_token(
    value: str,
    *,
    pattern: re.Pattern[str],
    field_name: str,
) -> str:
    if type(value) is not str:
        raise InputBoundaryError(f"{field_name} must be a string")
    try:
        value.encode("ascii")
    except UnicodeEncodeError as exc:
        raise InputBoundaryError(f"{field_name} must be ASCII") from exc
    if pattern.fullmatch(value) is None:
        raise InputBoundaryError(f"{field_name} is outside its canonical boundary")
    return value


def _validate_optional_ascii_token(
    value: str | None,
    *,
    pattern: re.Pattern[str],
    field_name: str,
) -> str | None:
    if value is not None:
        _validate_ascii_token(value, pattern=pattern, field_name=field_name)
    return value


def _validate_observation_id(value: str) -> str:
    return _validate_ascii_token(
        value,
        pattern=_OBSERVATION_ID_PATTERN,
        field_name="observation_id",
    )


def _validate_event_id_field(value: str, field_name: str) -> str:
    try:
        return validate_event_id(value)
    except InputBoundaryError as exc:
        raise InputBoundaryError(
            f"{field_name} is outside its canonical boundary"
        ) from exc


def _validate_boundary_profile_id(value: str) -> str:
    return _validate_ascii_token(
        value,
        pattern=_BOUNDARY_PROFILE_ID_PATTERN,
        field_name="boundary_profile_id",
    )


def _validate_episode_id(value: str) -> str:
    return _validate_ascii_token(
        value,
        pattern=_EPISODE_ID_PATTERN,
        field_name="episode_id",
    )


def _validate_digest(value: str, field_name: str) -> str:
    return _validate_ascii_token(value, pattern=_DIGEST_PATTERN, field_name=field_name)


def _validate_sorted_id_tuple(
    values: tuple[str, ...],
    *,
    field_name: str,
    validator: Any,
) -> tuple[str, ...]:
    if type(values) is not tuple:
        raise InputBoundaryError(f"{field_name} must be a tuple")
    if len(values) > MAX_COLLECTION_ITEMS:
        raise InputBoundaryError(f"{field_name} exceeds 32 items")
    for value in values:
        if type(value) is not str:
            raise InputBoundaryError(f"{field_name} must contain strings")
        validator(value)
    if tuple(sorted(values)) != values or len(set(values)) != len(values):
        raise InputBoundaryError(f"{field_name} must be sorted and unique")
    return values


def _validate_retrieval_text(value: str | None) -> str | None:
    if value is None:
        return None
    if type(value) is not str:
        raise InputBoundaryError("retrieval_text must be a string or null")
    try:
        raw = value.encode("utf-8")
    except UnicodeEncodeError as exc:
        raise InputBoundaryError("retrieval_text contains invalid Unicode") from exc
    if len(raw) > MAX_RETRIEVAL_TEXT_BYTES:
        raise InputBoundaryError("retrieval_text raw UTF-8 exceeds 4096 bytes")
    normalized = search_view_utf8(value, normalizer_id=active_normalizer_id())
    if len(normalized) > MAX_RETRIEVAL_TEXT_BYTES:
        raise InputBoundaryError("retrieval_text normalized UTF-8 exceeds 4096 bytes")
    return value


def _domain_digest(domain: bytes, payload: bytes) -> str:
    framed = (
        struct.pack(">Q", len(domain))
        + domain
        + struct.pack(">Q", len(payload))
        + payload
    )
    return hashlib.sha256(framed).hexdigest()


def _domain_json_digest(domain: bytes, value: JsonValue) -> str:
    return _domain_digest(domain, canonical_json_bytes(value))


__all__ = [
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
    "canonical_observation_matches_position",
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
]
