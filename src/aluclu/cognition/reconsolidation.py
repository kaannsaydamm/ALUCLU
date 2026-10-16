"""Content-free lineage; recall annotations are not calibration authority."""

from __future__ import annotations

import hashlib
import re
import struct
from dataclasses import dataclass
from enum import Enum
from typing import cast

from .codec import canonical_json_bytes
from .contracts import (
    AppendOutcome,
    InputBoundaryError,
    JsonValue,
    LedgerIntegrityError,
)
from .ledger import VerifiedLedgerSession
from .observation import (
    canonical_observation_from_json_value,
    canonical_observation_matches_position,
    derive_content_digest,
)
from .recollection import (
    CalibratedTextMatchEvidenceV1,
    ExactRecollection,
    RecallBasis,
    RecollectionWorkV1,
)

RECONSOLIDATION_SCHEMA = "aluclu.reconsolidation.v1"
_ID_DOMAIN = b"aluclu.task2.reconsolidation-id.v1"
_OBSERVATION_ID = re.compile(r"obs:[A-Za-z0-9][A-Za-z0-9._:-]{0,251}\Z")
_RECONSOLIDATION_ID = re.compile(r"recon:[0-9a-f]{64}\Z")
_DIGEST = re.compile(r"[0-9a-f]{64}\Z")
_MAX_I63 = (1 << 63) - 1


class ReconsolidationReason(str, Enum):
    CORRECTION = "correction"
    CONTEXT_ADDED = "context_added"
    USER_LINK = "user_link"
    OUTCOME_LINK = "outcome_link"


@dataclass(frozen=True, kw_only=True, slots=True)
class ReconsolidationRecordV1:
    """Endpoint-bound lineage with caller-declared, non-authoritative recall tags."""

    reconsolidation_id: str
    parent_observation_id: str
    parent_sequence: int
    parent_record_hash: str
    trigger_observation_id: str
    trigger_sequence: int
    trigger_record_hash: str
    reason: ReconsolidationReason
    recall_basis: RecallBasis
    calibration_profile_digest: str | None
    effective_policy_digest: str | None

    def __post_init__(self) -> None:
        _require_observation_id(self.parent_observation_id)
        _require_observation_id(self.trigger_observation_id)
        if self.parent_observation_id == self.trigger_observation_id:
            raise InputBoundaryError("reconsolidation cannot self-link")
        _require_sequence(self.parent_sequence, "parent_sequence")
        _require_sequence(self.trigger_sequence, "trigger_sequence")
        if self.trigger_sequence <= self.parent_sequence:
            raise InputBoundaryError("trigger must be a later observation")
        _require_digest(self.parent_record_hash, "parent_record_hash")
        _require_digest(self.trigger_record_hash, "trigger_record_hash")
        if type(self.reason) is not ReconsolidationReason:
            raise InputBoundaryError("reconsolidation reason is invalid")
        if type(self.recall_basis) is not RecallBasis:
            raise InputBoundaryError("recall basis is invalid")
        if self.recall_basis is RecallBasis.CALIBRATED_TEXT_MATCH:
            _require_digest(self.calibration_profile_digest, "calibration_profile_digest")
            _require_digest(self.effective_policy_digest, "effective_policy_digest")
        elif (
            self.calibration_profile_digest is not None
            or self.effective_policy_digest is not None
        ):
            raise InputBoundaryError("noncalibrated lineage cannot carry profile evidence")
        if (
            type(self.reconsolidation_id) is not str
            or _RECONSOLIDATION_ID.fullmatch(self.reconsolidation_id) is None
            or self.reconsolidation_id != _derive_reconsolidation_id(self)
        ):
            raise InputBoundaryError("reconsolidation ID is invalid")


@dataclass(frozen=True, kw_only=True, slots=True)
class ReconsolidationProposalV1:
    record: ReconsolidationRecordV1
    parent_content_digest: str
    parent_episode_id: str
    trigger_content_digest: str
    trigger_episode_id: str
    calibrated_evidence: CalibratedTextMatchEvidenceV1 | None

    def __post_init__(self) -> None:
        if type(self.record) is not ReconsolidationRecordV1:
            raise InputBoundaryError("reconsolidation record is invalid")
        _require_digest(self.parent_content_digest, "parent_content_digest")
        _require_digest(self.trigger_content_digest, "trigger_content_digest")
        for field_name, value in (
            ("parent_episode_id", self.parent_episode_id),
            ("trigger_episode_id", self.trigger_episode_id),
        ):
            if (
                type(value) is not str
                or not value.startswith("episode:")
                or _DIGEST.fullmatch(value[8:]) is None
            ):
                raise InputBoundaryError(f"{field_name} is invalid")
        if self.record.recall_basis is RecallBasis.CALIBRATED_TEXT_MATCH:
            if type(self.calibrated_evidence) is not CalibratedTextMatchEvidenceV1:
                raise InputBoundaryError("calibrated lineage evidence is missing")
            if (
                self.record.calibration_profile_digest
                != self.calibrated_evidence.profile_digest
                or self.record.effective_policy_digest
                != self.calibrated_evidence.effective_policy_digest
            ):
                raise InputBoundaryError("calibrated lineage evidence disagrees")
        elif self.calibrated_evidence is not None:
            raise InputBoundaryError("noncalibrated lineage has calibrated evidence")

    @property
    def reconsolidation_id(self) -> str:
        return self.record.reconsolidation_id


def propose_reconsolidation(
    parent: ExactRecollection,
    trigger: ExactRecollection,
    *,
    reason: ReconsolidationReason,
) -> ReconsolidationProposalV1:
    """Build a deterministic proposal without a ledger read or mutation."""

    _validate_exact_recollection(parent)
    _validate_exact_recollection(trigger)
    if type(reason) is not ReconsolidationReason:
        raise InputBoundaryError("reconsolidation reason is invalid")
    if parent.observation_id == trigger.observation_id:
        raise InputBoundaryError("reconsolidation cannot self-link")
    if trigger.sequence <= parent.sequence:
        raise InputBoundaryError("trigger must be a later observation")
    evidence = parent.calibrated_evidence
    profile_digest = evidence.profile_digest if evidence is not None else None
    policy_digest = evidence.effective_policy_digest if evidence is not None else None
    identity_body: dict[str, JsonValue] = {
        "parent_observation_id": parent.observation_id,
        "parent_sequence": parent.sequence,
        "parent_record_hash": parent.record_hash,
        "trigger_observation_id": trigger.observation_id,
        "trigger_sequence": trigger.sequence,
        "trigger_record_hash": trigger.record_hash,
        "reason": reason.value,
        "recall_basis": parent.basis.value,
        "calibration_profile_digest": profile_digest,
        "effective_policy_digest": policy_digest,
    }
    reconsolidation_id = _derive_reconsolidation_id_from_body(identity_body)
    record = ReconsolidationRecordV1(
        reconsolidation_id=reconsolidation_id,
        parent_observation_id=parent.observation_id,
        parent_sequence=parent.sequence,
        parent_record_hash=parent.record_hash,
        trigger_observation_id=trigger.observation_id,
        trigger_sequence=trigger.sequence,
        trigger_record_hash=trigger.record_hash,
        reason=reason,
        recall_basis=parent.basis,
        calibration_profile_digest=profile_digest,
        effective_policy_digest=policy_digest,
    )
    return ReconsolidationProposalV1(
        record=record,
        parent_content_digest=parent.content_digest,
        parent_episode_id=parent.episode_id,
        trigger_content_digest=trigger.content_digest,
        trigger_episode_id=trigger.episode_id,
        calibrated_evidence=evidence,
    )


def commit_reconsolidation(
    session: VerifiedLedgerSession,
    proposal: ReconsolidationProposalV1,
) -> AppendOutcome:
    """Verify both live endpoints, then append one content-free lineage edge."""

    if type(session) is not VerifiedLedgerSession:
        raise InputBoundaryError("an active VerifiedLedgerSession is required")
    session._ensure_active()
    session._ensure_no_active_cursors()
    _validate_proposal(proposal)
    _validate_live_endpoint(
        session,
        proposal.record.parent_observation_id,
        proposal.record.parent_sequence,
        proposal.record.parent_record_hash,
        proposal.parent_content_digest,
        proposal.parent_episode_id,
    )
    _validate_live_endpoint(
        session,
        proposal.record.trigger_observation_id,
        proposal.record.trigger_sequence,
        proposal.record.trigger_record_hash,
        proposal.trigger_content_digest,
        proposal.trigger_episode_id,
    )
    return session.append_once(
        proposal.reconsolidation_id,
        reconsolidation_record_to_json_value(proposal.record),
    )


def reconsolidation_record_to_json_value(
    record: ReconsolidationRecordV1,
) -> dict[str, JsonValue]:
    _validate_record(record)
    return {
        "schema": RECONSOLIDATION_SCHEMA,
        "reconsolidation_id": record.reconsolidation_id,
        **_record_identity_body(record),
    }


def reconsolidation_record_from_json_value(value: JsonValue) -> ReconsolidationRecordV1:
    """Decode only the exact content-free V1 wire shape and its derived identity."""

    expected = {
        "schema",
        "reconsolidation_id",
        "parent_observation_id",
        "parent_sequence",
        "parent_record_hash",
        "trigger_observation_id",
        "trigger_sequence",
        "trigger_record_hash",
        "reason",
        "recall_basis",
        "calibration_profile_digest",
        "effective_policy_digest",
    }
    if type(value) is not dict or set(value) != expected:
        raise InputBoundaryError("reconsolidation wire shape is invalid")
    wire = cast(dict[str, JsonValue], value)
    if type(wire["schema"]) is not str or wire["schema"] != RECONSOLIDATION_SCHEMA:
        raise InputBoundaryError("reconsolidation schema is invalid")
    if type(wire["reason"]) is not str or type(wire["recall_basis"]) is not str:
        raise InputBoundaryError("reconsolidation enum value is invalid")
    try:
        reason = ReconsolidationReason(wire["reason"])
        basis = RecallBasis(wire["recall_basis"])
    except (TypeError, ValueError) as exc:
        raise InputBoundaryError("reconsolidation enum value is invalid") from exc
    return ReconsolidationRecordV1(
        reconsolidation_id=cast(str, wire["reconsolidation_id"]),
        parent_observation_id=cast(str, wire["parent_observation_id"]),
        parent_sequence=cast(int, wire["parent_sequence"]),
        parent_record_hash=cast(str, wire["parent_record_hash"]),
        trigger_observation_id=cast(str, wire["trigger_observation_id"]),
        trigger_sequence=cast(int, wire["trigger_sequence"]),
        trigger_record_hash=cast(str, wire["trigger_record_hash"]),
        reason=reason,
        recall_basis=basis,
        calibration_profile_digest=cast(str | None, wire["calibration_profile_digest"]),
        effective_policy_digest=cast(str | None, wire["effective_policy_digest"]),
    )


def _validate_live_endpoint(
    session: VerifiedLedgerSession,
    observation_id: str,
    sequence: int,
    record_hash: str,
    content_digest: str,
    episode_id: str,
) -> None:
    record = session.read(observation_id)
    if record is None:
        raise InputBoundaryError("reconsolidation endpoint is no longer live")
    try:
        observation = canonical_observation_from_json_value(record.payload)
    except InputBoundaryError as exc:
        raise LedgerIntegrityError("reconsolidation endpoint is not an observation") from exc
    if (
        record.event_id != observation_id
        or record.sequence != sequence
        or record.record_hash != record_hash
        or observation.request.observation_id != observation_id
        or observation.content_digest != content_digest
        or observation.boundary_decision.episode_id != episode_id
        or not canonical_observation_matches_position(
            observation,
            observation_id,
            sequence,
        )
    ):
        raise InputBoundaryError("reconsolidation endpoint changed")


def _validate_exact_recollection(value: object) -> None:
    if type(value) is not ExactRecollection:
        raise InputBoundaryError("reconsolidation requires exact recollection")
    exact = cast(ExactRecollection, value)
    try:
        work = exact.work
        if work is not None:
            RecollectionWorkV1(
                records_scanned=work.records_scanned,
                canonical_payload_bytes_decoded=work.canonical_payload_bytes_decoded,
                candidates_scored=work.candidates_scored,
                candidates_returned=work.candidates_returned,
                output_bytes=work.output_bytes,
                exhaustive=work.exhaustive,
            )
        evidence = exact.calibrated_evidence
        if evidence is not None:
            CalibratedTextMatchEvidenceV1(
                profile_digest=evidence.profile_digest,
                effective_policy_digest=evidence.effective_policy_digest,
                score_q32=evidence.score_q32,
                margin_q32=evidence.margin_q32,
            )
        ExactRecollection(
            content=exact.content,
            observation_id=exact.observation_id,
            episode_id=exact.episode_id,
            sequence=exact.sequence,
            record_hash=exact.record_hash,
            content_digest=exact.content_digest,
            provenance=exact.provenance,
            basis=exact.basis,
            work=exact.work,
            calibrated_evidence=exact.calibrated_evidence,
        )
        if derive_content_digest(exact.content) != exact.content_digest:
            raise InputBoundaryError("exact recollection content digest changed")
    except (AttributeError, InputBoundaryError, TypeError, ValueError) as exc:
        raise InputBoundaryError("exact recollection is malformed") from exc


def _validate_record(value: object) -> None:
    if type(value) is not ReconsolidationRecordV1:
        raise InputBoundaryError("reconsolidation record is invalid")
    record = cast(ReconsolidationRecordV1, value)
    try:
        ReconsolidationRecordV1(
            reconsolidation_id=record.reconsolidation_id,
            parent_observation_id=record.parent_observation_id,
            parent_sequence=record.parent_sequence,
            parent_record_hash=record.parent_record_hash,
            trigger_observation_id=record.trigger_observation_id,
            trigger_sequence=record.trigger_sequence,
            trigger_record_hash=record.trigger_record_hash,
            reason=record.reason,
            recall_basis=record.recall_basis,
            calibration_profile_digest=record.calibration_profile_digest,
            effective_policy_digest=record.effective_policy_digest,
        )
    except (AttributeError, InputBoundaryError, TypeError, ValueError) as exc:
        raise InputBoundaryError("reconsolidation record is invalid") from exc


def _validate_proposal(value: object) -> None:
    if type(value) is not ReconsolidationProposalV1:
        raise InputBoundaryError("reconsolidation proposal is invalid")
    proposal = cast(ReconsolidationProposalV1, value)
    try:
        _validate_record(proposal.record)
        evidence = proposal.calibrated_evidence
        if evidence is not None:
            CalibratedTextMatchEvidenceV1(
                profile_digest=evidence.profile_digest,
                effective_policy_digest=evidence.effective_policy_digest,
                score_q32=evidence.score_q32,
                margin_q32=evidence.margin_q32,
            )
        ReconsolidationProposalV1(
            record=proposal.record,
            parent_content_digest=proposal.parent_content_digest,
            parent_episode_id=proposal.parent_episode_id,
            trigger_content_digest=proposal.trigger_content_digest,
            trigger_episode_id=proposal.trigger_episode_id,
            calibrated_evidence=proposal.calibrated_evidence,
        )
    except (AttributeError, InputBoundaryError, TypeError, ValueError) as exc:
        raise InputBoundaryError("reconsolidation proposal is invalid") from exc


def _record_identity_body(record: ReconsolidationRecordV1) -> dict[str, JsonValue]:
    return {
        "parent_observation_id": record.parent_observation_id,
        "parent_sequence": record.parent_sequence,
        "parent_record_hash": record.parent_record_hash,
        "trigger_observation_id": record.trigger_observation_id,
        "trigger_sequence": record.trigger_sequence,
        "trigger_record_hash": record.trigger_record_hash,
        "reason": record.reason.value,
        "recall_basis": record.recall_basis.value,
        "calibration_profile_digest": record.calibration_profile_digest,
        "effective_policy_digest": record.effective_policy_digest,
    }


def _derive_reconsolidation_id(record: ReconsolidationRecordV1) -> str:
    return _derive_reconsolidation_id_from_body(_record_identity_body(record))


def _derive_reconsolidation_id_from_body(identity_body: dict[str, JsonValue]) -> str:
    body = canonical_json_bytes(cast(JsonValue, identity_body))
    frame = (
        struct.pack(">Q", len(_ID_DOMAIN))
        + _ID_DOMAIN
        + struct.pack(">Q", len(body))
        + body
    )
    return "recon:" + hashlib.sha256(frame).hexdigest()


def _require_observation_id(value: object) -> None:
    if type(value) is not str or _OBSERVATION_ID.fullmatch(value) is None:
        raise InputBoundaryError("observation ID is invalid")


def _require_sequence(value: object, field_name: str) -> None:
    if type(value) is not int or not 1 <= value <= _MAX_I63:
        raise InputBoundaryError(f"{field_name} is invalid")


def _require_digest(value: object, field_name: str) -> None:
    if type(value) is not str or _DIGEST.fullmatch(value) is None:
        raise InputBoundaryError(f"{field_name} is invalid")


__all__ = [
    "RECONSOLIDATION_SCHEMA",
    "ReconsolidationProposalV1",
    "ReconsolidationReason",
    "ReconsolidationRecordV1",
    "commit_reconsolidation",
    "propose_reconsolidation",
    "reconsolidation_record_from_json_value",
    "reconsolidation_record_to_json_value",
]
