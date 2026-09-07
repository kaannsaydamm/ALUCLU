from __future__ import annotations

import re
from dataclasses import dataclass
from enum import Enum

from .contracts import InputBoundaryError
from .ledger import VerifiedLedgerSession
from .observation import (
    CanonicalJsonValue,
    ProvenanceV1,
    canonical_observation_from_json_value,
)

_OBSERVATION_ID_PATTERN = re.compile(r"obs:[A-Za-z0-9][A-Za-z0-9._:-]{0,251}\Z")
_DIGEST_PATTERN = re.compile(r"[0-9a-f]{64}\Z")
_EPISODE_ID_PATTERN = re.compile(r"episode:[0-9a-f]{64}\Z")


class RecallBasis(str, Enum):
    DIRECT_ID = "direct_id"
    CONTENT_DIGEST = "content_digest"
    CALIBRATED_TEXT_MATCH = "calibrated_text_match"


@dataclass(frozen=True, kw_only=True, slots=True)
class EventIdRecallQuery:
    observation_id: str

    def __post_init__(self) -> None:
        _require_observation_id(self.observation_id)


@dataclass(frozen=True, kw_only=True, slots=True)
class ExactRecollection:
    content: CanonicalJsonValue
    observation_id: str
    episode_id: str
    sequence: int
    record_hash: str
    content_digest: str
    provenance: ProvenanceV1
    basis: RecallBasis

    def __post_init__(self) -> None:
        if type(self.content) is not CanonicalJsonValue:
            raise InputBoundaryError("recollection content is invalid")
        _require_observation_id(self.observation_id)
        if (
            type(self.episode_id) is not str
            or _EPISODE_ID_PATTERN.fullmatch(self.episode_id) is None
        ):
            raise InputBoundaryError("recollection episode_id is invalid")
        if type(self.sequence) is not int or self.sequence <= 0:
            raise InputBoundaryError("recollection sequence is invalid")
        _require_digest(self.record_hash, "record_hash")
        _require_digest(self.content_digest, "content_digest")
        if type(self.provenance) is not ProvenanceV1:
            raise InputBoundaryError("recollection provenance is invalid")
        if type(self.basis) is not RecallBasis:
            raise InputBoundaryError("recollection basis is invalid")

    @property
    def content_is_observation(self) -> bool:
        return True

    @property
    def content_is_verified_fact(self) -> bool:
        return False


@dataclass(frozen=True, kw_only=True, slots=True)
class NoRecollection:
    observation_id: str

    def __post_init__(self) -> None:
        _require_observation_id(self.observation_id)

    @property
    def content_is_observation(self) -> bool:
        return False

    @property
    def content_is_verified_fact(self) -> bool:
        return False


def recall(
    session: VerifiedLedgerSession,
    query: EventIdRecallQuery,
) -> ExactRecollection | NoRecollection:
    active = _require_session(session)
    if type(query) is not EventIdRecallQuery:
        raise InputBoundaryError("Task 2.2 supports only EventIdRecallQuery")
    record = active.read(query.observation_id)
    if record is None:
        return NoRecollection(observation_id=query.observation_id)
    try:
        observation = canonical_observation_from_json_value(record.payload)
    except InputBoundaryError:
        return NoRecollection(observation_id=query.observation_id)
    if observation.request.observation_id != query.observation_id:
        return NoRecollection(observation_id=query.observation_id)
    if (
        observation.pre_append_head_sequence + 1 != record.sequence
        or observation.post_core_state.last_observation_sequence != record.sequence
    ):
        return NoRecollection(observation_id=query.observation_id)
    return ExactRecollection(
        content=observation.request.content,
        observation_id=query.observation_id,
        episode_id=observation.boundary_decision.episode_id,
        sequence=record.sequence,
        record_hash=record.record_hash,
        content_digest=observation.content_digest,
        provenance=observation.request.provenance,
        basis=RecallBasis.DIRECT_ID,
    )


def _require_session(value: object) -> VerifiedLedgerSession:
    if type(value) is not VerifiedLedgerSession:
        raise InputBoundaryError("an active VerifiedLedgerSession is required")
    return value


def _require_observation_id(value: str) -> None:
    if type(value) is not str or _OBSERVATION_ID_PATTERN.fullmatch(value) is None:
        raise InputBoundaryError("observation_id is invalid")


def _require_digest(value: str, field_name: str) -> None:
    if type(value) is not str or _DIGEST_PATTERN.fullmatch(value) is None:
        raise InputBoundaryError(f"{field_name} must be a lowercase SHA-256 digest")


__all__ = [
    "EventIdRecallQuery",
    "ExactRecollection",
    "NoRecollection",
    "RecallBasis",
    "recall",
]
