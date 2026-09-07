from __future__ import annotations

import hashlib
import re
import struct
from dataclasses import dataclass
from enum import Enum
from typing import cast

from .codec import canonical_json_bytes, strict_json_loads
from .contracts import (
    InputBoundaryError,
    JsonValue,
    LedgerConflictError,
    LedgerCursorCheckpoint,
    LedgerSnapshotChanged,
)
from .ledger import VerifiedLedgerSession
from .observation import (
    CanonicalObservationV1,
    EpisodeBoundaryDecisionV1,
    EpisodeBoundaryReason,
    ObservationRequestV1,
    SensoriumCoreStateV1,
    build_canonical_observation,
    canonical_observation_from_json_value,
    canonical_observation_to_json_value,
    derive_boundary_signal_digests,
    derive_episode_id,
    derive_request_digest,
    derive_sensorium_core_state_digest,
    encode_observation_request,
    sensorium_core_state_from_json_value,
    sensorium_core_state_to_json_value,
)

MAX_I63 = (1 << 63) - 1
SENSORIUM_STATE_MAX_BYTES = 4_096

_PROFILE_SCHEMA = "aluclu.boundary-profile.v1"
_STATE_SCHEMA = "aluclu.sensorium-state.v1"
_BOOTSTRAP_REPLAY_SCHEMA = "aluclu.sensorium-bootstrap-replay-required.v1"
_RECEIPT_SCHEMA = "aluclu.observation-receipt.v1"
_INGEST_ACCEPTED_SCHEMA = "aluclu.observation-ingest-accepted.v1"
_INGEST_REJECTED_SCHEMA = "aluclu.observation-ingest-rejected.v1"
_PROFILE_DOMAIN = b"aluclu.task2.boundary-profile.v1"
_PROFILE_NAME_PATTERN = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]{0,63}\Z")
_OBSERVATION_ID_PATTERN = re.compile(r"obs:[A-Za-z0-9][A-Za-z0-9._:-]{0,251}\Z")
_DIGEST_PATTERN = re.compile(r"[0-9a-f]{64}\Z")
_PROFILE_ID_PATTERN = re.compile(r"boundary-profile:[0-9a-f]{64}\Z")


class ReceiptClass(str, Enum):
    NEW = "new"
    DUPLICATE = "duplicate"
    CONFLICT = "conflict"
    TOMBSTONED = "tombstoned"


class IngestStatus(str, Enum):
    APPLIED = "applied"
    DUPLICATE = "duplicate"


class IngestRejectionCode(str, Enum):
    OBSERVATION_CONFLICT = "observation_conflict"
    OBSERVATION_TOMBSTONED = "observation_tombstoned"
    STATE_CONFLICT = "state_conflict"
    REPLAY_REQUIRED = "replay_required"
    TIME_REVERSED_INVALID = "time_reversed_invalid"


@dataclass(frozen=True, kw_only=True, slots=True)
class BoundaryProfileV1:
    name: str
    max_inter_observation_gap_ns: int
    max_observations: int
    max_canonical_request_bytes: int
    max_goal_ids: int
    max_participant_ids: int

    def __post_init__(self) -> None:
        if (
            type(self.name) is not str
            or _PROFILE_NAME_PATTERN.fullmatch(self.name) is None
        ):
            raise InputBoundaryError("boundary profile name is invalid")
        _require_positive_i63(
            self.max_inter_observation_gap_ns, "max_inter_observation_gap_ns"
        )
        _require_positive_i63(self.max_observations, "max_observations")
        _require_positive_i63(
            self.max_canonical_request_bytes, "max_canonical_request_bytes"
        )
        _require_positive_i63(self.max_goal_ids, "max_goal_ids")
        _require_positive_i63(self.max_participant_ids, "max_participant_ids")
        if self.max_goal_ids > 32 or self.max_participant_ids > 32:
            raise InputBoundaryError(
                "boundary profile collection limits exceed protocol cap"
            )

    @property
    def profile_id(self) -> str:
        return "boundary-profile:" + _domain_digest(
            _PROFILE_DOMAIN,
            canonical_json_bytes(boundary_profile_to_json_value(self)),
        )


@dataclass(frozen=True, kw_only=True, slots=True)
class SensoriumStateV1:
    core: SensoriumCoreStateV1
    task1_checkpoint: LedgerCursorCheckpoint

    def __post_init__(self) -> None:
        if type(self.core) is not SensoriumCoreStateV1:
            raise InputBoundaryError("sensorium state core is invalid")
        _validate_exhaustive_checkpoint(self.task1_checkpoint)
        if (
            self.core.last_observation_sequence
            > self.task1_checkpoint.snapshot_head_sequence
        ):
            raise InputBoundaryError("sensorium core is ahead of its Task 1 checkpoint")
        if len(_encode_sensorium_state_unchecked(self)) > SENSORIUM_STATE_MAX_BYTES:
            raise InputBoundaryError("sensorium state exceeds 4096 canonical bytes")

    @property
    def last_applied_sequence(self) -> int:
        return self.task1_checkpoint.snapshot_head_sequence


@dataclass(frozen=True, kw_only=True, slots=True)
class SensoriumBootstrapReplayRequiredV1:
    snapshot_head_sequence: int
    snapshot_head_hash: str
    replay_from_sequence: int = 0

    def __post_init__(self) -> None:
        _require_nonnegative_i63(self.snapshot_head_sequence, "snapshot_head_sequence")
        _require_digest(self.snapshot_head_hash, "snapshot_head_hash")
        if type(self.replay_from_sequence) is not int or self.replay_from_sequence != 0:
            raise InputBoundaryError("bootstrap replay must begin at sequence zero")


@dataclass(frozen=True, kw_only=True, slots=True)
class CanonicalizedObservationV1:
    request: ObservationRequestV1
    pre_core_state: SensoriumCoreStateV1
    boundary_decision: EpisodeBoundaryDecisionV1
    post_core_state: SensoriumCoreStateV1


@dataclass(frozen=True, kw_only=True, slots=True)
class ObservationReceiptV1:
    receipt_class: ReceiptClass
    observation_id: str
    incoming_request_digest: str
    existing_request_digest: str | None
    existing_sequence: int | None
    existing_record_hash: str | None

    def __post_init__(self) -> None:
        if type(self.receipt_class) is not ReceiptClass:
            raise InputBoundaryError("receipt class is invalid")
        _require_observation_id(self.observation_id)
        _require_digest(self.incoming_request_digest, "incoming_request_digest")
        if self.existing_request_digest is not None:
            _require_digest(self.existing_request_digest, "existing_request_digest")
        if self.existing_sequence is not None:
            _require_positive_i63(self.existing_sequence, "existing_sequence")
        if self.existing_record_hash is not None:
            _require_digest(self.existing_record_hash, "existing_record_hash")

        if self.receipt_class in {ReceiptClass.NEW, ReceiptClass.TOMBSTONED}:
            if any(
                value is not None
                for value in (
                    self.existing_request_digest,
                    self.existing_sequence,
                    self.existing_record_hash,
                )
            ):
                raise InputBoundaryError(
                    "new/tombstoned receipt cannot expose existing data"
                )
        elif self.receipt_class is ReceiptClass.DUPLICATE:
            if (
                self.existing_request_digest != self.incoming_request_digest
                or self.existing_sequence is None
                or self.existing_record_hash is None
            ):
                raise InputBoundaryError("duplicate receipt is incomplete")
        elif self.existing_sequence is None or self.existing_record_hash is None:
            raise InputBoundaryError("conflict receipt is incomplete")


@dataclass(frozen=True, kw_only=True, slots=True)
class ObservationAcceptedV1:
    status: IngestStatus
    receipt: ObservationReceiptV1
    stored_observation: CanonicalObservationV1
    next_state: SensoriumStateV1

    def __post_init__(self) -> None:
        if type(self.status) is not IngestStatus:
            raise InputBoundaryError("ingest status is invalid")
        if type(self.receipt) is not ObservationReceiptV1:
            raise InputBoundaryError("accepted receipt is invalid")
        if type(self.stored_observation) is not CanonicalObservationV1:
            raise InputBoundaryError("stored observation is invalid")
        if type(self.next_state) is not SensoriumStateV1:
            raise InputBoundaryError("next sensorium state is invalid")
        expected_class = (
            ReceiptClass.NEW
            if self.status is IngestStatus.APPLIED
            else ReceiptClass.DUPLICATE
        )
        if self.receipt.receipt_class is not expected_class:
            raise InputBoundaryError("accepted status and receipt disagree")
        if (
            self.receipt.observation_id
            != self.stored_observation.request.observation_id
        ):
            raise InputBoundaryError("accepted receipt and observation disagree")


@dataclass(frozen=True, kw_only=True, slots=True)
class ObservationRejectedV1:
    receipt: ObservationReceiptV1
    rejection_code: IngestRejectionCode
    replay_from_sequence: int | None

    def __post_init__(self) -> None:
        if type(self.receipt) is not ObservationReceiptV1:
            raise InputBoundaryError("rejected receipt is invalid")
        if type(self.rejection_code) is not IngestRejectionCode:
            raise InputBoundaryError("ingest rejection code is invalid")
        if self.rejection_code is IngestRejectionCode.REPLAY_REQUIRED:
            if self.replay_from_sequence is None:
                raise InputBoundaryError(
                    "replay rejection requires a starting sequence"
                )
            _require_nonnegative_i63(self.replay_from_sequence, "replay_from_sequence")
        elif self.replay_from_sequence is not None:
            raise InputBoundaryError(
                "only replay rejection carries a starting sequence"
            )


class _TimeReversed(InputBoundaryError):
    pass


def baseline_boundary_profile() -> BoundaryProfileV1:
    return BoundaryProfileV1(
        name="task2-baseline-v1",
        max_inter_observation_gap_ns=1_800_000_000_000,
        max_observations=64,
        max_canonical_request_bytes=8 * 1024 * 1024,
        max_goal_ids=32,
        max_participant_ids=32,
    )


def boundary_profile_to_json_value(profile: BoundaryProfileV1) -> dict[str, JsonValue]:
    if type(profile) is not BoundaryProfileV1:
        raise InputBoundaryError("profile must be BoundaryProfileV1")
    return {
        "schema": _PROFILE_SCHEMA,
        "name": profile.name,
        "max_inter_observation_gap_ns": profile.max_inter_observation_gap_ns,
        "max_observations": profile.max_observations,
        "max_canonical_request_bytes": profile.max_canonical_request_bytes,
        "max_goal_ids": profile.max_goal_ids,
        "max_participant_ids": profile.max_participant_ids,
    }


def sensorium_state_to_json_value(state: SensoriumStateV1) -> dict[str, JsonValue]:
    if type(state) is not SensoriumStateV1:
        raise InputBoundaryError("state must be SensoriumStateV1")
    checkpoint = state.task1_checkpoint
    return {
        "schema": _STATE_SCHEMA,
        "core": sensorium_core_state_to_json_value(state.core),
        "task1_checkpoint": {
            "ledger_id": checkpoint.ledger_id,
            "snapshot_head_sequence": checkpoint.snapshot_head_sequence,
            "snapshot_head_hash": checkpoint.snapshot_head_hash,
            "next_sequence": checkpoint.next_sequence,
        },
    }


def bootstrap_replay_to_json_value(
    replay: SensoriumBootstrapReplayRequiredV1,
) -> dict[str, JsonValue]:
    if type(replay) is not SensoriumBootstrapReplayRequiredV1:
        raise InputBoundaryError("replay must be SensoriumBootstrapReplayRequiredV1")
    return {
        "schema": _BOOTSTRAP_REPLAY_SCHEMA,
        "snapshot_head_sequence": replay.snapshot_head_sequence,
        "snapshot_head_hash": replay.snapshot_head_hash,
        "replay_from_sequence": replay.replay_from_sequence,
    }


def observation_receipt_to_json_value(
    receipt: ObservationReceiptV1,
) -> dict[str, JsonValue]:
    if type(receipt) is not ObservationReceiptV1:
        raise InputBoundaryError("receipt must be ObservationReceiptV1")
    return {
        "schema": _RECEIPT_SCHEMA,
        "receipt_class": receipt.receipt_class.value,
        "observation_id": receipt.observation_id,
        "incoming_request_digest": receipt.incoming_request_digest,
        "existing_request_digest": receipt.existing_request_digest,
        "existing_sequence": receipt.existing_sequence,
        "existing_record_hash": receipt.existing_record_hash,
    }


def observation_accepted_to_json_value(
    accepted: ObservationAcceptedV1,
) -> dict[str, JsonValue]:
    if type(accepted) is not ObservationAcceptedV1:
        raise InputBoundaryError("accepted must be ObservationAcceptedV1")
    return {
        "schema": _INGEST_ACCEPTED_SCHEMA,
        "status": accepted.status.value,
        "receipt": observation_receipt_to_json_value(accepted.receipt),
        "stored_observation": canonical_observation_to_json_value(
            accepted.stored_observation
        ),
        "next_state": sensorium_state_to_json_value(accepted.next_state),
    }


def observation_rejected_to_json_value(
    rejected: ObservationRejectedV1,
) -> dict[str, JsonValue]:
    if type(rejected) is not ObservationRejectedV1:
        raise InputBoundaryError("rejected must be ObservationRejectedV1")
    return {
        "schema": _INGEST_REJECTED_SCHEMA,
        "receipt": observation_receipt_to_json_value(rejected.receipt),
        "rejection_code": rejected.rejection_code.value,
        "replay_from_sequence": rejected.replay_from_sequence,
    }


def encode_sensorium_state(state: SensoriumStateV1) -> bytes:
    encoded = _encode_sensorium_state_unchecked(state)
    if len(encoded) > SENSORIUM_STATE_MAX_BYTES:
        raise InputBoundaryError("sensorium state exceeds 4096 canonical bytes")
    return encoded


def decode_sensorium_state(data: bytes) -> SensoriumStateV1:
    if type(data) is not bytes:
        raise InputBoundaryError("sensorium state encoding must be bytes")
    if len(data) > SENSORIUM_STATE_MAX_BYTES:
        raise InputBoundaryError("sensorium state exceeds 4096 canonical bytes")
    value = strict_json_loads(data)
    if canonical_json_bytes(value) != data:
        raise InputBoundaryError("sensorium state bytes are not canonical")
    return sensorium_state_from_json_value(value)


def sensorium_state_from_json_value(value: JsonValue) -> SensoriumStateV1:
    wire = _require_object(
        value, {_STATE_SCHEMA: {"schema", "core", "task1_checkpoint"}}
    )
    checkpoint_wire = _require_exact_object(
        wire["task1_checkpoint"],
        {"ledger_id", "snapshot_head_sequence", "snapshot_head_hash", "next_sequence"},
        "task1_checkpoint",
    )
    return SensoriumStateV1(
        core=sensorium_core_state_from_json_value(wire["core"]),
        task1_checkpoint=LedgerCursorCheckpoint(
            ledger_id=_required_str(checkpoint_wire, "ledger_id"),
            snapshot_head_sequence=_required_int(
                checkpoint_wire, "snapshot_head_sequence"
            ),
            snapshot_head_hash=_required_str(checkpoint_wire, "snapshot_head_hash"),
            next_sequence=_required_int(checkpoint_wire, "next_sequence"),
        ),
    )


def initialize_empty_sensorium_state(
    session: VerifiedLedgerSession,
    profile: BoundaryProfileV1,
) -> SensoriumStateV1 | SensoriumBootstrapReplayRequiredV1:
    active = _require_session(session)
    _require_profile(profile)
    checkpoint = _tail_checkpoint(active)
    if checkpoint.snapshot_head_sequence != 0:
        return SensoriumBootstrapReplayRequiredV1(
            snapshot_head_sequence=checkpoint.snapshot_head_sequence,
            snapshot_head_hash=checkpoint.snapshot_head_hash,
            replay_from_sequence=0,
        )
    return SensoriumStateV1(
        core=_initial_core(profile),
        task1_checkpoint=checkpoint,
    )


def canonicalize_observation(
    request: ObservationRequestV1,
    profile: BoundaryProfileV1,
    current_core: SensoriumCoreStateV1,
    observation_sequence: int | None = None,
) -> CanonicalizedObservationV1:
    if type(request) is not ObservationRequestV1:
        raise InputBoundaryError("request must be ObservationRequestV1")
    _require_profile(profile)
    if type(current_core) is not SensoriumCoreStateV1:
        raise InputBoundaryError("current_core must be SensoriumCoreStateV1")
    if len(request.goal_ids) > profile.max_goal_ids:
        raise InputBoundaryError("request exceeds profile goal limit")
    if len(request.participant_ids) > profile.max_participant_ids:
        raise InputBoundaryError("request exceeds profile participant limit")

    sequence = (
        current_core.last_observation_sequence + 1
        if observation_sequence is None
        else observation_sequence
    )
    _require_positive_i63(sequence, "observation_sequence")
    request_bytes = len(encode_observation_request(request))
    if request_bytes > profile.max_canonical_request_bytes:
        raise InputBoundaryError("one request exceeds the profile episode byte limit")
    signals = derive_boundary_signal_digests(request)
    reasons: list[EpisodeBoundaryReason] = []
    first = current_core.current_episode_id is None
    if first:
        reasons.append(EpisodeBoundaryReason.FIRST_OBSERVATION)
    else:
        if current_core.boundary_profile_id != profile.profile_id:
            reasons.append(EpisodeBoundaryReason.PROFILE_CHANGED)
        if request.force_boundary:
            reasons.append(EpisodeBoundaryReason.FORCED)
        if current_core.session_signal_digest != signals.session_signal_digest:
            reasons.append(EpisodeBoundaryReason.SESSION_CHANGED)
        assert current_core.last_observed_at_ns is not None
        if request.provenance.observed_at_ns < current_core.last_observed_at_ns:
            raise _TimeReversed("observation timestamp moves backward")
        if (
            request.provenance.observed_at_ns - current_core.last_observed_at_ns
            > profile.max_inter_observation_gap_ns
        ):
            reasons.append(EpisodeBoundaryReason.TIME_GAP)
        if current_core.goal_ids_signal_digest != signals.goal_ids_signal_digest:
            reasons.append(EpisodeBoundaryReason.GOAL_CHANGED)
        if current_core.tool_signal_digest != signals.tool_signal_digest:
            reasons.append(EpisodeBoundaryReason.TOOL_PHASE_CHANGED)
        if (
            current_core.participant_ids_signal_digest
            != signals.participant_ids_signal_digest
        ):
            reasons.append(EpisodeBoundaryReason.PARTICIPANTS_CHANGED)
        if current_core.topic_signal_digest != signals.topic_signal_digest:
            reasons.append(EpisodeBoundaryReason.TOPIC_KEY_CHANGED)
        if current_core.episode_observation_count + 1 > profile.max_observations:
            reasons.append(EpisodeBoundaryReason.EPISODE_COUNT_LIMIT)
        if (
            current_core.episode_canonical_request_bytes + request_bytes
            > profile.max_canonical_request_bytes
        ):
            reasons.append(EpisodeBoundaryReason.EPISODE_BYTE_LIMIT)
    if not reasons:
        reasons.append(EpisodeBoundaryReason.CONTINUE)

    starts_episode = reasons != [EpisodeBoundaryReason.CONTINUE]
    episode_id = (
        derive_episode_id(
            boundary_profile_id=profile.profile_id,
            first_observation_id=request.observation_id,
            session_id=request.session_id,
        )
        if starts_episode
        else cast(str, current_core.current_episode_id)
    )
    post_core = SensoriumCoreStateV1(
        boundary_profile_id=profile.profile_id,
        session_signal_digest=signals.session_signal_digest,
        current_episode_id=episode_id,
        episode_observation_count=(
            1 if starts_episode else current_core.episode_observation_count + 1
        ),
        episode_canonical_request_bytes=(
            request_bytes
            if starts_episode
            else current_core.episode_canonical_request_bytes + request_bytes
        ),
        goal_ids_signal_digest=signals.goal_ids_signal_digest,
        participant_ids_signal_digest=signals.participant_ids_signal_digest,
        tool_signal_digest=signals.tool_signal_digest,
        topic_signal_digest=signals.topic_signal_digest,
        last_observation_id=request.observation_id,
        last_observation_sequence=sequence,
        last_observed_at_ns=request.provenance.observed_at_ns,
    )
    return CanonicalizedObservationV1(
        request=request,
        pre_core_state=current_core,
        boundary_decision=EpisodeBoundaryDecisionV1(
            episode_id=episode_id,
            reasons=tuple(reasons),
        ),
        post_core_state=post_core,
    )


def classify_observation_receipt(
    session: VerifiedLedgerSession,
    request: ObservationRequestV1,
) -> ObservationReceiptV1:
    active = _require_session(session)
    if type(request) is not ObservationRequestV1:
        raise InputBoundaryError("request must be ObservationRequestV1")
    incoming_digest = derive_request_digest(request)
    if active.is_tombstoned(request.observation_id):
        return ObservationReceiptV1(
            receipt_class=ReceiptClass.TOMBSTONED,
            observation_id=request.observation_id,
            incoming_request_digest=incoming_digest,
            existing_request_digest=None,
            existing_sequence=None,
            existing_record_hash=None,
        )
    record = active.read(request.observation_id)
    if record is None:
        return ObservationReceiptV1(
            receipt_class=ReceiptClass.NEW,
            observation_id=request.observation_id,
            incoming_request_digest=incoming_digest,
            existing_request_digest=None,
            existing_sequence=None,
            existing_record_hash=None,
        )
    existing = _observation_from_record_payload(
        record.payload,
        request.observation_id,
        record.sequence,
    )
    existing_digest = None if existing is None else existing.request_digest
    duplicate = existing_digest == incoming_digest
    return ObservationReceiptV1(
        receipt_class=(ReceiptClass.DUPLICATE if duplicate else ReceiptClass.CONFLICT),
        observation_id=request.observation_id,
        incoming_request_digest=incoming_digest,
        existing_request_digest=existing_digest,
        existing_sequence=record.sequence,
        existing_record_hash=record.record_hash,
    )


def ingest_observation(
    session: VerifiedLedgerSession,
    request: ObservationRequestV1,
    profile: BoundaryProfileV1,
    state: SensoriumStateV1,
) -> ObservationAcceptedV1 | ObservationRejectedV1:
    active = _require_session(session)
    _require_profile(profile)
    if type(state) is not SensoriumStateV1:
        raise InputBoundaryError("state must be SensoriumStateV1")
    receipt = classify_observation_receipt(active, request)
    if receipt.receipt_class is ReceiptClass.TOMBSTONED:
        return _rejected(receipt, IngestRejectionCode.OBSERVATION_TOMBSTONED)
    if receipt.receipt_class is ReceiptClass.CONFLICT:
        return _rejected(receipt, IngestRejectionCode.OBSERVATION_CONFLICT)
    if receipt.receipt_class is ReceiptClass.DUPLICATE:
        return _resolve_duplicate(active, request, profile, state, receipt)

    if not _state_matches_active_head(active, state):
        return _rejected(receipt, IngestRejectionCode.STATE_CONFLICT)
    if state.core.boundary_profile_id != profile.profile_id:
        return _rejected(receipt, IngestRejectionCode.STATE_CONFLICT)
    if not _state_lineage_is_valid(active, state):
        return _rejected(receipt, IngestRejectionCode.STATE_CONFLICT)
    try:
        canonical = canonicalize_observation(
            request,
            profile,
            state.core,
            state.task1_checkpoint.snapshot_head_sequence + 1,
        )
    except _TimeReversed:
        return _rejected(receipt, IngestRejectionCode.TIME_REVERSED_INVALID)
    observation = build_canonical_observation(
        request=request,
        boundary_decision=canonical.boundary_decision,
        pre_core_state_digest=derive_sensorium_core_state_digest(state.core),
        post_core_state=canonical.post_core_state,
        pre_append_head_sequence=state.task1_checkpoint.snapshot_head_sequence,
        pre_append_head_hash=state.task1_checkpoint.snapshot_head_hash,
        boundary_profile_id=profile.profile_id,
    )
    outcome = active.append_once(
        request.observation_id,
        cast(JsonValue, canonical_observation_to_json_value(observation)),
    )
    if not outcome.created:
        raise LedgerConflictError("NEW observation unexpectedly already exists")
    checkpoint = _tail_checkpoint(active)
    if (
        checkpoint.snapshot_head_sequence != outcome.record.sequence
        or checkpoint.snapshot_head_hash != outcome.record.record_hash
    ):
        raise LedgerConflictError("Task 1 append outcome and tail checkpoint disagree")
    return ObservationAcceptedV1(
        status=IngestStatus.APPLIED,
        receipt=receipt,
        stored_observation=observation,
        next_state=SensoriumStateV1(
            core=canonical.post_core_state,
            task1_checkpoint=checkpoint,
        ),
    )


def _resolve_duplicate(
    session: VerifiedLedgerSession,
    request: ObservationRequestV1,
    profile: BoundaryProfileV1,
    state: SensoriumStateV1,
    receipt: ObservationReceiptV1,
) -> ObservationAcceptedV1 | ObservationRejectedV1:
    record = session.read(request.observation_id)
    if record is None:
        return _rejected(receipt, IngestRejectionCode.STATE_CONFLICT)
    observation = _observation_from_record_payload(
        record.payload,
        request.observation_id,
        record.sequence,
    )
    if observation is None:
        return _rejected(receipt, IngestRejectionCode.OBSERVATION_CONFLICT)
    existing_sequence = cast(int, receipt.existing_sequence)
    caller_sequence = state.last_applied_sequence
    active_tail = _tail_checkpoint(session)

    if caller_sequence < existing_sequence - 1:
        return _replay_required(receipt, caller_sequence)
    if caller_sequence == existing_sequence - 1:
        if active_tail.snapshot_head_sequence != existing_sequence:
            return _replay_required(receipt, caller_sequence)
        checkpoint = state.task1_checkpoint
        if (
            checkpoint.ledger_id != active_tail.ledger_id
            or checkpoint.snapshot_head_sequence != observation.pre_append_head_sequence
            or checkpoint.snapshot_head_hash != observation.pre_append_head_hash
            or checkpoint.next_sequence != checkpoint.snapshot_head_sequence + 1
            or derive_sensorium_core_state_digest(state.core)
            != observation.pre_core_state_digest
            or state.core.boundary_profile_id != profile.profile_id
            or active_tail.snapshot_head_hash != record.record_hash
        ):
            return _rejected(receipt, IngestRejectionCode.STATE_CONFLICT)
        next_state = SensoriumStateV1(
            core=observation.post_core_state,
            task1_checkpoint=active_tail,
        )
    else:
        if not _state_matches_checkpoint(active_tail, state.task1_checkpoint):
            return _rejected(receipt, IngestRejectionCode.STATE_CONFLICT)
        if state.core.boundary_profile_id != profile.profile_id:
            return _rejected(receipt, IngestRejectionCode.STATE_CONFLICT)
        if caller_sequence > existing_sequence and not _state_lineage_is_valid(
            session, state
        ):
            return _rejected(receipt, IngestRejectionCode.STATE_CONFLICT)
        if (
            caller_sequence == existing_sequence
            and derive_sensorium_core_state_digest(state.core)
            != observation.post_core_state_digest
        ):
            return _rejected(receipt, IngestRejectionCode.STATE_CONFLICT)
        next_state = state
    return ObservationAcceptedV1(
        status=IngestStatus.DUPLICATE,
        receipt=receipt,
        stored_observation=observation,
        next_state=next_state,
    )


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


def _tail_checkpoint(session: VerifiedLedgerSession) -> LedgerCursorCheckpoint:
    cursor = session.cursor(after_sequence=MAX_I63, batch_size=1)
    return cursor.suspend()


def _state_matches_active_head(
    session: VerifiedLedgerSession, state: SensoriumStateV1
) -> bool:
    try:
        cursor = session.resume_verified(state.task1_checkpoint, batch_size=1)
    except LedgerSnapshotChanged:
        return False
    cursor.close()
    return True


def _state_matches_checkpoint(
    active: LedgerCursorCheckpoint, candidate: LedgerCursorCheckpoint
) -> bool:
    return (
        active.ledger_id == candidate.ledger_id
        and active.snapshot_head_sequence == candidate.snapshot_head_sequence
        and active.snapshot_head_hash == candidate.snapshot_head_hash
        and active.next_sequence == candidate.next_sequence
    )


def _state_lineage_is_valid(
    session: VerifiedLedgerSession,
    state: SensoriumStateV1,
) -> bool:
    observation_id = state.core.last_observation_id
    if observation_id is None:
        return state.core.last_observation_sequence == 0
    record = session.read(observation_id)
    if record is None or record.sequence != state.core.last_observation_sequence:
        return False
    observation = _observation_from_record_payload(
        record.payload,
        observation_id,
        record.sequence,
    )
    return observation is not None and observation.post_core_state == state.core


def _observation_from_record_payload(
    payload: JsonValue,
    expected_id: str,
    record_sequence: int,
) -> CanonicalObservationV1 | None:
    try:
        observation = canonical_observation_from_json_value(payload)
    except InputBoundaryError:
        return None
    if observation.request.observation_id != expected_id:
        return None
    if (
        observation.pre_append_head_sequence + 1 != record_sequence
        or observation.post_core_state.last_observation_sequence != record_sequence
    ):
        return None
    return observation


def _rejected(
    receipt: ObservationReceiptV1, code: IngestRejectionCode
) -> ObservationRejectedV1:
    return ObservationRejectedV1(
        receipt=receipt,
        rejection_code=code,
        replay_from_sequence=None,
    )


def _replay_required(
    receipt: ObservationReceiptV1, from_sequence: int
) -> ObservationRejectedV1:
    return ObservationRejectedV1(
        receipt=receipt,
        rejection_code=IngestRejectionCode.REPLAY_REQUIRED,
        replay_from_sequence=from_sequence,
    )


def _require_session(value: object) -> VerifiedLedgerSession:
    if type(value) is not VerifiedLedgerSession:
        raise InputBoundaryError("an active VerifiedLedgerSession is required")
    return value


def _require_profile(value: object) -> BoundaryProfileV1:
    if type(value) is not BoundaryProfileV1:
        raise InputBoundaryError("profile must be BoundaryProfileV1")
    return value


def _validate_exhaustive_checkpoint(value: object) -> None:
    if type(value) is not LedgerCursorCheckpoint:
        raise InputBoundaryError("Task 1 checkpoint is invalid")
    checkpoint = cast(LedgerCursorCheckpoint, value)
    if (
        type(checkpoint.ledger_id) is not str
        or not checkpoint.ledger_id
        or len(checkpoint.ledger_id.encode("utf-8")) > 256
    ):
        raise InputBoundaryError("checkpoint ledger_id is invalid")
    _require_nonnegative_i63(
        checkpoint.snapshot_head_sequence, "snapshot_head_sequence"
    )
    _require_digest(checkpoint.snapshot_head_hash, "snapshot_head_hash")
    if (
        type(checkpoint.next_sequence) is not int
        or checkpoint.next_sequence != checkpoint.snapshot_head_sequence + 1
    ):
        raise InputBoundaryError("sensorium state checkpoint is not exhaustive")


def _encode_sensorium_state_unchecked(state: SensoriumStateV1) -> bytes:
    return canonical_json_bytes(sensorium_state_to_json_value(state))


def _require_object(
    value: JsonValue, schemas: dict[str, set[str]]
) -> dict[str, JsonValue]:
    wire = _require_exact_object(value, next(iter(schemas.values())), "object")
    schema = wire.get("schema")
    if type(schema) is not str or schema not in schemas:
        raise InputBoundaryError("object schema is invalid")
    return wire


def _require_exact_object(
    value: JsonValue, keys: set[str], field_name: str
) -> dict[str, JsonValue]:
    if type(value) is not dict:
        raise InputBoundaryError(f"{field_name} must be an object")
    wire = cast(dict[str, JsonValue], value)
    if set(wire) != keys:
        raise InputBoundaryError(f"{field_name} keys are invalid")
    return wire


def _required_str(wire: dict[str, JsonValue], key: str) -> str:
    value = wire[key]
    if type(value) is not str:
        raise InputBoundaryError(f"{key} must be a string")
    return value


def _required_int(wire: dict[str, JsonValue], key: str) -> int:
    value = wire[key]
    if type(value) is not int:
        raise InputBoundaryError(f"{key} must be an integer")
    return value


def _require_observation_id(value: str) -> None:
    if type(value) is not str or _OBSERVATION_ID_PATTERN.fullmatch(value) is None:
        raise InputBoundaryError("observation_id is invalid")


def _require_digest(value: str, field_name: str) -> None:
    if type(value) is not str or _DIGEST_PATTERN.fullmatch(value) is None:
        raise InputBoundaryError(f"{field_name} must be a lowercase SHA-256 digest")


def _require_positive_i63(value: int, field_name: str) -> None:
    if type(value) is not int or not 1 <= value <= MAX_I63:
        raise InputBoundaryError(f"{field_name} must be a positive i63 integer")


def _require_nonnegative_i63(value: int, field_name: str) -> None:
    if type(value) is not int or not 0 <= value <= MAX_I63:
        raise InputBoundaryError(f"{field_name} must be a nonnegative i63 integer")


def _domain_digest(domain: bytes, payload: bytes) -> str:
    framed = (
        struct.pack(">Q", len(domain))
        + domain
        + struct.pack(">Q", len(payload))
        + payload
    )
    return hashlib.sha256(framed).hexdigest()


__all__ = [
    "BoundaryProfileV1",
    "CanonicalizedObservationV1",
    "IngestRejectionCode",
    "IngestStatus",
    "ObservationAcceptedV1",
    "ObservationReceiptV1",
    "ObservationRejectedV1",
    "ReceiptClass",
    "SensoriumBootstrapReplayRequiredV1",
    "SensoriumStateV1",
    "baseline_boundary_profile",
    "bootstrap_replay_to_json_value",
    "boundary_profile_to_json_value",
    "canonicalize_observation",
    "classify_observation_receipt",
    "decode_sensorium_state",
    "encode_sensorium_state",
    "ingest_observation",
    "initialize_empty_sensorium_state",
    "observation_accepted_to_json_value",
    "observation_receipt_to_json_value",
    "observation_rejected_to_json_value",
    "sensorium_state_from_json_value",
    "sensorium_state_to_json_value",
]
