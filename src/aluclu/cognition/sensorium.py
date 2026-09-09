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
    LedgerIntegrityError,
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
SENSORIUM_REPLAY_CONTINUATION_MAX_BYTES = 5_120
SENSORIUM_REPLAY_MAX_RECORDS = 8_192

_PROFILE_SCHEMA = "aluclu.boundary-profile.v1"
_STATE_SCHEMA = "aluclu.sensorium-state.v1"
_BOOTSTRAP_REPLAY_SCHEMA = "aluclu.sensorium-bootstrap-replay-required.v1"
_RECEIPT_SCHEMA = "aluclu.observation-receipt.v1"
_INGEST_ACCEPTED_SCHEMA = "aluclu.observation-ingest-accepted.v1"
_INGEST_REJECTED_SCHEMA = "aluclu.observation-ingest-rejected.v1"
_CANONICAL_OBSERVATION_SCHEMA = "aluclu.observation.v1"
_REPLAY_PAGE_POLICY_SCHEMA = "aluclu.sensorium-replay-page-policy.v1"
_REPLAY_PAGE_WORK_SCHEMA = "aluclu.sensorium-replay-page-work.v1"
_REPLAY_CONTINUATION_SCHEMA = "aluclu.sensorium-replay-continuation.v1"
_REPLAY_INCOMPLETE_SCHEMA = "aluclu.sensorium-replay-incomplete.v1"
_REPLAY_COMPLETE_SCHEMA = "aluclu.sensorium-replay-complete.v1"
_TASK2_LINEAGE_WITNESS_SCHEMA = "aluclu.task2-observation-lineage-witness.v1"
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
class SensoriumReplayPagePolicyV1:
    max_records: int

    def __post_init__(self) -> None:
        if (
            type(self.max_records) is not int
            or not 0 <= self.max_records <= SENSORIUM_REPLAY_MAX_RECORDS
        ):
            raise InputBoundaryError("replay max_records must be an integer in 0..8192")


@dataclass(frozen=True, kw_only=True, slots=True)
class SensoriumReplayPageWorkV1:
    records_examined: int
    observations_applied: int
    canonical_payload_bytes_examined: int

    def __post_init__(self) -> None:
        _require_nonnegative_i63(self.records_examined, "records_examined")
        _require_nonnegative_i63(self.observations_applied, "observations_applied")
        _require_nonnegative_i63(
            self.canonical_payload_bytes_examined,
            "canonical_payload_bytes_examined",
        )
        if self.observations_applied > self.records_examined:
            raise InputBoundaryError("replay observations exceed examined records")


@dataclass(frozen=True, kw_only=True, slots=True)
class SensoriumReplayContinuationV1:
    core: SensoriumCoreStateV1
    task1_checkpoint: LedgerCursorCheckpoint
    records_examined: int
    observations_applied: int
    canonical_payload_bytes_examined: int

    def __post_init__(self) -> None:
        if type(self.core) is not SensoriumCoreStateV1:
            raise InputBoundaryError("replay continuation core is invalid")
        _validate_checkpoint(self.task1_checkpoint)
        checkpoint = self.task1_checkpoint
        if checkpoint.next_sequence > checkpoint.snapshot_head_sequence:
            raise InputBoundaryError("replay continuation checkpoint is exhaustive")
        if self.core.last_observation_sequence >= checkpoint.next_sequence:
            raise InputBoundaryError("replay continuation core is ahead of checkpoint")
        SensoriumReplayPageWorkV1(
            records_examined=self.records_examined,
            observations_applied=self.observations_applied,
            canonical_payload_bytes_examined=self.canonical_payload_bytes_examined,
        )
        if (
            len(_encode_replay_continuation_unchecked(self))
            > SENSORIUM_REPLAY_CONTINUATION_MAX_BYTES
        ):
            raise InputBoundaryError(
                "sensorium replay continuation exceeds 5120 canonical bytes"
            )


@dataclass(frozen=True, kw_only=True, slots=True)
class SensoriumReplayIncompleteV1:
    continuation: SensoriumReplayContinuationV1
    page_work: SensoriumReplayPageWorkV1

    def __post_init__(self) -> None:
        if type(self.continuation) is not SensoriumReplayContinuationV1:
            raise InputBoundaryError("replay continuation is invalid")
        if type(self.page_work) is not SensoriumReplayPageWorkV1:
            raise InputBoundaryError("replay page work is invalid")


@dataclass(frozen=True, kw_only=True, slots=True)
class SensoriumReplayCompleteV1:
    state: SensoriumStateV1
    page_work: SensoriumReplayPageWorkV1

    def __post_init__(self) -> None:
        if type(self.state) is not SensoriumStateV1:
            raise InputBoundaryError("completed replay state is invalid")
        if type(self.page_work) is not SensoriumReplayPageWorkV1:
            raise InputBoundaryError("replay page work is invalid")


@dataclass(frozen=True, kw_only=True, slots=True)
class CanonicalizedObservationV1:
    request: ObservationRequestV1
    pre_core_state: SensoriumCoreStateV1
    boundary_decision: EpisodeBoundaryDecisionV1
    post_core_state: SensoriumCoreStateV1


@dataclass(frozen=True, kw_only=True, slots=True)
class _Task2LineageWitnessV1:
    event_id: str
    append_sequence: int
    append_record_hash: str
    boundary_profile_id: str
    content_digest: str
    pre_append_head_hash: str
    pre_append_head_sequence: int
    pre_core_state_digest: str
    post_core_state_digest: str
    request_digest: str


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


def replay_page_policy_to_json_value(
    policy: SensoriumReplayPagePolicyV1,
) -> dict[str, JsonValue]:
    if type(policy) is not SensoriumReplayPagePolicyV1:
        raise InputBoundaryError("policy must be SensoriumReplayPagePolicyV1")
    return {"schema": _REPLAY_PAGE_POLICY_SCHEMA, "max_records": policy.max_records}


def replay_page_work_to_json_value(
    work: SensoriumReplayPageWorkV1,
) -> dict[str, JsonValue]:
    if type(work) is not SensoriumReplayPageWorkV1:
        raise InputBoundaryError("work must be SensoriumReplayPageWorkV1")
    return {
        "schema": _REPLAY_PAGE_WORK_SCHEMA,
        "records_examined": work.records_examined,
        "observations_applied": work.observations_applied,
        "canonical_payload_bytes_examined": (work.canonical_payload_bytes_examined),
    }


def replay_continuation_to_json_value(
    continuation: SensoriumReplayContinuationV1,
) -> dict[str, JsonValue]:
    if type(continuation) is not SensoriumReplayContinuationV1:
        raise InputBoundaryError("continuation must be SensoriumReplayContinuationV1")
    return {
        "schema": _REPLAY_CONTINUATION_SCHEMA,
        "core": sensorium_core_state_to_json_value(continuation.core),
        "task1_checkpoint": _checkpoint_to_json_value(continuation.task1_checkpoint),
        "records_examined": continuation.records_examined,
        "observations_applied": continuation.observations_applied,
        "canonical_payload_bytes_examined": (
            continuation.canonical_payload_bytes_examined
        ),
    }


def replay_incomplete_to_json_value(
    incomplete: SensoriumReplayIncompleteV1,
) -> dict[str, JsonValue]:
    if type(incomplete) is not SensoriumReplayIncompleteV1:
        raise InputBoundaryError("incomplete must be SensoriumReplayIncompleteV1")
    return {
        "schema": _REPLAY_INCOMPLETE_SCHEMA,
        "continuation": replay_continuation_to_json_value(incomplete.continuation),
        "page_work": replay_page_work_to_json_value(incomplete.page_work),
    }


def replay_complete_to_json_value(
    complete: SensoriumReplayCompleteV1,
) -> dict[str, JsonValue]:
    if type(complete) is not SensoriumReplayCompleteV1:
        raise InputBoundaryError("complete must be SensoriumReplayCompleteV1")
    return {
        "schema": _REPLAY_COMPLETE_SCHEMA,
        "state": sensorium_state_to_json_value(complete.state),
        "page_work": replay_page_work_to_json_value(complete.page_work),
    }


def replay_page_policy_from_json_value(
    value: JsonValue,
) -> SensoriumReplayPagePolicyV1:
    wire = _require_object(
        value,
        {_REPLAY_PAGE_POLICY_SCHEMA: {"schema", "max_records"}},
    )
    return SensoriumReplayPagePolicyV1(max_records=_required_int(wire, "max_records"))


def replay_page_work_from_json_value(value: JsonValue) -> SensoriumReplayPageWorkV1:
    wire = _require_object(
        value,
        {
            _REPLAY_PAGE_WORK_SCHEMA: {
                "schema",
                "records_examined",
                "observations_applied",
                "canonical_payload_bytes_examined",
            }
        },
    )
    return SensoriumReplayPageWorkV1(
        records_examined=_required_int(wire, "records_examined"),
        observations_applied=_required_int(wire, "observations_applied"),
        canonical_payload_bytes_examined=_required_int(
            wire, "canonical_payload_bytes_examined"
        ),
    )


def replay_continuation_from_json_value(
    value: JsonValue,
) -> SensoriumReplayContinuationV1:
    wire = _require_object(
        value,
        {
            _REPLAY_CONTINUATION_SCHEMA: {
                "schema",
                "core",
                "task1_checkpoint",
                "records_examined",
                "observations_applied",
                "canonical_payload_bytes_examined",
            }
        },
    )
    return SensoriumReplayContinuationV1(
        core=sensorium_core_state_from_json_value(wire["core"]),
        task1_checkpoint=_checkpoint_from_json_value(wire["task1_checkpoint"]),
        records_examined=_required_int(wire, "records_examined"),
        observations_applied=_required_int(wire, "observations_applied"),
        canonical_payload_bytes_examined=_required_int(
            wire, "canonical_payload_bytes_examined"
        ),
    )


def replay_incomplete_from_json_value(
    value: JsonValue,
) -> SensoriumReplayIncompleteV1:
    wire = _require_object(
        value,
        {_REPLAY_INCOMPLETE_SCHEMA: {"schema", "continuation", "page_work"}},
    )
    return SensoriumReplayIncompleteV1(
        continuation=replay_continuation_from_json_value(wire["continuation"]),
        page_work=replay_page_work_from_json_value(wire["page_work"]),
    )


def replay_complete_from_json_value(value: JsonValue) -> SensoriumReplayCompleteV1:
    wire = _require_object(
        value,
        {_REPLAY_COMPLETE_SCHEMA: {"schema", "state", "page_work"}},
    )
    return SensoriumReplayCompleteV1(
        state=sensorium_state_from_json_value(wire["state"]),
        page_work=replay_page_work_from_json_value(wire["page_work"]),
    )


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


def replay_sensorium_page(
    session: VerifiedLedgerSession,
    policy: SensoriumReplayPagePolicyV1,
    start: BoundaryProfileV1 | SensoriumReplayContinuationV1,
) -> SensoriumReplayCompleteV1 | SensoriumReplayIncompleteV1:
    active = _require_session(session)
    if type(policy) is not SensoriumReplayPagePolicyV1:
        raise InputBoundaryError("policy must be SensoriumReplayPagePolicyV1")

    batch_size = max(1, min(policy.max_records, 64))
    available_profile: BoundaryProfileV1 | None = None
    if type(start) is BoundaryProfileV1:
        available_profile = start
        core = _initial_core(start)
        cursor = active.cursor(after_sequence=0, batch_size=batch_size)
        total_records = 0
        total_observations = 0
        total_payload_bytes = 0
    elif type(start) is SensoriumReplayContinuationV1:
        core = start.core
        cursor = active.resume_verified(
            start.task1_checkpoint,
            batch_size=batch_size,
        )
        total_records = start.records_examined
        total_observations = start.observations_applied
        total_payload_bytes = start.canonical_payload_bytes_examined
        baseline = baseline_boundary_profile()
        if baseline.profile_id == core.boundary_profile_id:
            available_profile = baseline
    else:
        raise InputBoundaryError("replay start must be a profile or continuation")

    page_records = 0
    page_observations = 0
    page_payload_bytes = 0
    exhausted = False
    try:
        while page_records < policy.max_records:
            try:
                record = next(cursor)
            except StopIteration:
                exhausted = True
                break
            page_records += 1
            payload_bytes = len(canonical_json_bytes(record.payload))
            page_payload_bytes += payload_bytes
            total_records += 1
            total_payload_bytes += payload_bytes

            observation = _observation_from_record_payload(
                record.payload,
                record.event_id,
                record.sequence,
            )
            claims_observation = (
                type(record.payload) is dict
                and cast(dict[str, JsonValue], record.payload).get("schema")
                == _CANONICAL_OBSERVATION_SCHEMA
            )
            if observation is None:
                if claims_observation:
                    raise LedgerIntegrityError(
                        "malformed Task 2 observation encountered during replay"
                    )
                continue

            pre_core_matches = _core_digest_matches(
                core, observation.pre_core_state_digest
            )
            if not pre_core_matches:
                if not _has_authenticated_lineage_bridge(
                    active,
                    core,
                    target_digest=observation.pre_core_state_digest,
                    before_sequence=record.sequence,
                ):
                    raise LedgerIntegrityError(
                        "Task 2 replay predecessor core digest does not match"
                    )
                if not _live_observation_has_authenticated_witness(
                    active,
                    event_id=record.event_id,
                    sequence=record.sequence,
                    record_hash=record.record_hash,
                    observation=observation,
                ):
                    raise LedgerIntegrityError(
                        "Task 2 replay gap successor lacks authenticated ingest witness"
                    )
            profile = _available_replay_profile(
                observation.boundary_profile_id,
                available_profile,
            )
            if pre_core_matches and profile is not None:
                try:
                    recomputed = canonicalize_observation(
                        observation.request,
                        profile,
                        core,
                        record.sequence,
                    )
                except InputBoundaryError as exc:
                    raise LedgerIntegrityError(
                        "Task 2 replay transition cannot be recomputed"
                    ) from exc
                if (
                    recomputed.boundary_decision != observation.boundary_decision
                    or recomputed.post_core_state != observation.post_core_state
                ):
                    raise LedgerIntegrityError(
                        "Task 2 replay transition disagrees with stored observation"
                    )
            elif pre_core_matches and not _live_observation_has_authenticated_witness(
                active,
                event_id=record.event_id,
                sequence=record.sequence,
                record_hash=record.record_hash,
                observation=observation,
            ):
                raise LedgerIntegrityError(
                    "Task 2 replay unavailable profile lacks authenticated ingest witness"
                )
            core = observation.post_core_state
            available_profile = profile
            page_observations += 1
            total_observations += 1
    except BaseException as primary:
        try:
            cursor.close()
        except BaseException as cleanup_failure:
            raise primary from cleanup_failure
        raise

    checkpoint = cursor.suspend()
    page_work = SensoriumReplayPageWorkV1(
        records_examined=page_records,
        observations_applied=page_observations,
        canonical_payload_bytes_examined=page_payload_bytes,
    )
    if exhausted or checkpoint.next_sequence == checkpoint.snapshot_head_sequence + 1:
        return SensoriumReplayCompleteV1(
            state=SensoriumStateV1(core=core, task1_checkpoint=checkpoint),
            page_work=page_work,
        )
    return SensoriumReplayIncompleteV1(
        continuation=SensoriumReplayContinuationV1(
            core=core,
            task1_checkpoint=checkpoint,
            records_examined=total_records,
            observations_applied=total_observations,
            canonical_payload_bytes_examined=total_payload_bytes,
        ),
        page_work=page_work,
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
    outcome = active._append_once_with_authenticated_witness(
        request.observation_id,
        cast(JsonValue, canonical_observation_to_json_value(observation)),
        witness_schema=_TASK2_LINEAGE_WITNESS_SCHEMA,
        link_digest=observation.post_core_state_digest,
        witness_body=_task2_lineage_witness_body(observation),
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
            or observation.boundary_profile_id != profile.profile_id
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
        if observation.boundary_profile_id != profile.profile_id:
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
        or observation.post_core_state.last_observation_id != expected_id
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
    _validate_checkpoint(value)
    checkpoint = cast(LedgerCursorCheckpoint, value)
    if checkpoint.next_sequence != checkpoint.snapshot_head_sequence + 1:
        raise InputBoundaryError("sensorium state checkpoint is not exhaustive")


def _validate_checkpoint(value: object) -> None:
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
        or not 1 <= checkpoint.next_sequence <= checkpoint.snapshot_head_sequence + 1
    ):
        raise InputBoundaryError("checkpoint next_sequence is invalid")


def _encode_sensorium_state_unchecked(state: SensoriumStateV1) -> bytes:
    return canonical_json_bytes(sensorium_state_to_json_value(state))


def _encode_replay_continuation_unchecked(
    continuation: SensoriumReplayContinuationV1,
) -> bytes:
    return canonical_json_bytes(replay_continuation_to_json_value(continuation))


def _checkpoint_to_json_value(
    checkpoint: LedgerCursorCheckpoint,
) -> dict[str, JsonValue]:
    _validate_checkpoint(checkpoint)
    return {
        "ledger_id": checkpoint.ledger_id,
        "snapshot_head_sequence": checkpoint.snapshot_head_sequence,
        "snapshot_head_hash": checkpoint.snapshot_head_hash,
        "next_sequence": checkpoint.next_sequence,
    }


def _checkpoint_from_json_value(value: JsonValue) -> LedgerCursorCheckpoint:
    wire = _require_exact_object(
        value,
        {"ledger_id", "snapshot_head_sequence", "snapshot_head_hash", "next_sequence"},
        "task1_checkpoint",
    )
    return LedgerCursorCheckpoint(
        ledger_id=_required_str(wire, "ledger_id"),
        snapshot_head_sequence=_required_int(wire, "snapshot_head_sequence"),
        snapshot_head_hash=_required_str(wire, "snapshot_head_hash"),
        next_sequence=_required_int(wire, "next_sequence"),
    )


def _core_digest_matches(core: SensoriumCoreStateV1, expected: str) -> bool:
    return derive_sensorium_core_state_digest(core) == expected


def _task2_lineage_witness_body(
    observation: CanonicalObservationV1,
) -> dict[str, JsonValue]:
    post_core = observation.post_core_state
    return {
        "boundary_profile_id": observation.boundary_profile_id,
        "content_digest": observation.content_digest,
        "observation_id": observation.request.observation_id,
        "observation_schema": _CANONICAL_OBSERVATION_SCHEMA,
        "post_core_state_digest": observation.post_core_state_digest,
        "post_last_observation_id": post_core.last_observation_id,
        "post_last_observation_sequence": post_core.last_observation_sequence,
        "pre_append_head_hash": observation.pre_append_head_hash,
        "pre_append_head_sequence": observation.pre_append_head_sequence,
        "pre_core_state_digest": observation.pre_core_state_digest,
        "request_digest": observation.request_digest,
        "schema": _TASK2_LINEAGE_WITNESS_SCHEMA,
    }


def _has_authenticated_lineage_bridge(
    session: VerifiedLedgerSession,
    core: SensoriumCoreStateV1,
    *,
    target_digest: str,
    before_sequence: int,
) -> bool:
    anchored_digest = derive_sensorium_core_state_digest(core)
    next_digest = target_digest
    upper_bound = before_sequence
    traversed = 0
    while next_digest != anchored_digest:
        proof = session.authenticated_tombstoned_append_witness(
            witness_schema=_TASK2_LINEAGE_WITNESS_SCHEMA,
            link_digest=next_digest,
            after_sequence=core.last_observation_sequence,
            before_sequence=upper_bound,
        )
        if proof is None:
            return False
        try:
            witness = _task2_lineage_witness_from_proof(proof)
        except InputBoundaryError as exc:
            raise LedgerIntegrityError(
                "authenticated Task 2 lineage witness is malformed"
            ) from exc
        if (
            witness.post_core_state_digest != next_digest
            or witness.append_sequence >= upper_bound
            or witness.append_sequence <= core.last_observation_sequence
        ):
            raise LedgerIntegrityError(
                "authenticated Task 2 lineage witness binding is invalid"
            )
        next_digest = witness.pre_core_state_digest
        upper_bound = witness.append_sequence
        traversed += 1
        if traversed > SENSORIUM_REPLAY_MAX_RECORDS:
            raise LedgerIntegrityError("Task 2 lineage witness chain exceeds bound")
    return True


def _live_observation_has_authenticated_witness(
    session: VerifiedLedgerSession,
    *,
    event_id: str,
    sequence: int,
    record_hash: str,
    observation: CanonicalObservationV1,
) -> bool:
    proof = session.authenticated_live_append_witness(
        event_id=event_id,
        append_sequence=sequence,
        append_record_hash=record_hash,
        witness_schema=_TASK2_LINEAGE_WITNESS_SCHEMA,
        link_digest=observation.post_core_state_digest,
    )
    if proof is None:
        return False
    try:
        witness = _task2_lineage_witness_from_proof(proof)
    except InputBoundaryError as exc:
        raise LedgerIntegrityError(
            "authenticated Task 2 successor witness is malformed"
        ) from exc
    return witness == _Task2LineageWitnessV1(
        event_id=event_id,
        append_sequence=sequence,
        append_record_hash=record_hash,
        boundary_profile_id=observation.boundary_profile_id,
        content_digest=observation.content_digest,
        pre_append_head_hash=observation.pre_append_head_hash,
        pre_append_head_sequence=observation.pre_append_head_sequence,
        pre_core_state_digest=observation.pre_core_state_digest,
        post_core_state_digest=observation.post_core_state_digest,
        request_digest=observation.request_digest,
    )


def _task2_lineage_witness_from_proof(
    value: JsonValue,
) -> _Task2LineageWitnessV1:
    proof = _require_exact_object(
        value,
        {
            "append_record_hash",
            "append_sequence",
            "event_id",
            "link_digest",
            "witness_body",
            "witness_schema",
        },
        "authenticated append witness",
    )
    witness_schema = _required_str(proof, "witness_schema")
    if witness_schema != _TASK2_LINEAGE_WITNESS_SCHEMA:
        raise InputBoundaryError("Task 2 lineage witness schema is invalid")
    event_id = _required_str(proof, "event_id")
    _require_observation_id(event_id)
    append_sequence = _required_int(proof, "append_sequence")
    _require_positive_i63(append_sequence, "append_sequence")
    append_record_hash = _required_str(proof, "append_record_hash")
    _require_digest(append_record_hash, "append_record_hash")
    link_digest = _required_str(proof, "link_digest")
    _require_digest(link_digest, "link_digest")

    body = _require_exact_object(
        proof["witness_body"],
        {
            "boundary_profile_id",
            "content_digest",
            "observation_id",
            "observation_schema",
            "post_core_state_digest",
            "post_last_observation_id",
            "post_last_observation_sequence",
            "pre_append_head_hash",
            "pre_append_head_sequence",
            "pre_core_state_digest",
            "request_digest",
            "schema",
        },
        "Task 2 lineage witness body",
    )
    if (
        _required_str(body, "schema") != _TASK2_LINEAGE_WITNESS_SCHEMA
        or _required_str(body, "observation_schema")
        != _CANONICAL_OBSERVATION_SCHEMA
    ):
        raise InputBoundaryError("Task 2 lineage witness body schema is invalid")
    observation_id = _required_str(body, "observation_id")
    post_last_observation_id = _required_str(body, "post_last_observation_id")
    _require_observation_id(observation_id)
    _require_observation_id(post_last_observation_id)
    pre_head_sequence = _required_int(body, "pre_append_head_sequence")
    _require_nonnegative_i63(pre_head_sequence, "pre_append_head_sequence")
    post_last_sequence = _required_int(body, "post_last_observation_sequence")
    _require_positive_i63(post_last_sequence, "post_last_observation_sequence")
    pre_head_hash = _required_str(body, "pre_append_head_hash")
    request_digest = _required_str(body, "request_digest")
    content_digest = _required_str(body, "content_digest")
    pre_core_digest = _required_str(body, "pre_core_state_digest")
    post_core_digest = _required_str(body, "post_core_state_digest")
    for field_name, digest in (
        ("pre_append_head_hash", pre_head_hash),
        ("request_digest", request_digest),
        ("content_digest", content_digest),
        ("pre_core_state_digest", pre_core_digest),
        ("post_core_state_digest", post_core_digest),
    ):
        _require_digest(digest, field_name)
    profile_id = _required_str(body, "boundary_profile_id")
    if _PROFILE_ID_PATTERN.fullmatch(profile_id) is None:
        raise InputBoundaryError("boundary_profile_id is invalid")
    if (
        event_id != observation_id
        or observation_id != post_last_observation_id
        or append_sequence != pre_head_sequence + 1
        or append_sequence != post_last_sequence
        or link_digest != post_core_digest
    ):
        raise InputBoundaryError("Task 2 lineage witness binding is invalid")
    return _Task2LineageWitnessV1(
        event_id=event_id,
        append_sequence=append_sequence,
        append_record_hash=append_record_hash,
        boundary_profile_id=profile_id,
        content_digest=content_digest,
        pre_append_head_hash=pre_head_hash,
        pre_append_head_sequence=pre_head_sequence,
        pre_core_state_digest=pre_core_digest,
        post_core_state_digest=post_core_digest,
        request_digest=request_digest,
    )


def _available_replay_profile(
    profile_id: str,
    current: BoundaryProfileV1 | None,
) -> BoundaryProfileV1 | None:
    if current is not None and current.profile_id == profile_id:
        return current
    baseline = baseline_boundary_profile()
    if baseline.profile_id == profile_id:
        return baseline
    return None


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
    "SENSORIUM_REPLAY_CONTINUATION_MAX_BYTES",
    "SENSORIUM_REPLAY_MAX_RECORDS",
    "BoundaryProfileV1",
    "CanonicalizedObservationV1",
    "IngestRejectionCode",
    "IngestStatus",
    "ObservationAcceptedV1",
    "ObservationReceiptV1",
    "ObservationRejectedV1",
    "ReceiptClass",
    "SensoriumBootstrapReplayRequiredV1",
    "SensoriumReplayCompleteV1",
    "SensoriumReplayContinuationV1",
    "SensoriumReplayIncompleteV1",
    "SensoriumReplayPagePolicyV1",
    "SensoriumReplayPageWorkV1",
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
    "replay_complete_from_json_value",
    "replay_complete_to_json_value",
    "replay_continuation_from_json_value",
    "replay_continuation_to_json_value",
    "replay_incomplete_from_json_value",
    "replay_incomplete_to_json_value",
    "replay_page_policy_from_json_value",
    "replay_page_policy_to_json_value",
    "replay_page_work_from_json_value",
    "replay_page_work_to_json_value",
    "replay_sensorium_page",
    "sensorium_state_from_json_value",
    "sensorium_state_to_json_value",
]
