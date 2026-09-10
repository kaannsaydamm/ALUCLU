from __future__ import annotations

import hashlib
import hmac
import re
import secrets
import struct
from dataclasses import dataclass, field
from enum import Enum
from functools import cmp_to_key
from typing import cast, overload

from .codec import canonical_json_bytes, validate_event_id
from .contracts import (
    InputBoundaryError,
    JsonValue,
    LedgerCursorCheckpoint,
    LedgerIntegrityError,
    LedgerRecord,
)
from .ledger import VerifiedLedgerSession
from .observation import (
    CanonicalJsonValue,
    CanonicalObservationV1,
    ProvenanceV1,
    SourceKind,
    canonical_observation_from_json_value,
)
from .recall_features import (
    FeatureSimilarityV1,
    RetrievalFeatureVectorV1,
    compare_feature_similarity_exact,
    encode_retrieval_text,
    feature_vector_digest,
    measure_feature_similarity,
)
from .recall_features import (
    active_feature_spec_id as runtime_feature_spec_id,
)
from .recall_features import (
    active_normalizer_id as runtime_normalizer_id,
)

_OBSERVATION_ID_PATTERN = re.compile(r"obs:[A-Za-z0-9][A-Za-z0-9._:-]{0,251}\Z")
_DIGEST_PATTERN = re.compile(r"[0-9a-f]{64}\Z")
_EPISODE_ID_PATTERN = re.compile(r"episode:[0-9a-f]{64}\Z")
_CANONICAL_OBSERVATION_SCHEMA = "aluclu.observation.v1"
_QUERY_DIGEST_DOMAIN = b"aluclu.task2.recall-query.v1"
_POLICY_DIGEST_DOMAIN = b"aluclu.task2.recall-policy.v1"
_NO_PROFILE_DOMAIN = b"aluclu.task2.no-calibration-profile.v1"
_NO_CALIBRATION_PROFILE_DIGEST = ""
_MAX_I63 = (1 << 63) - 1
_MAX_Q32 = 1 << 32
_MAX_RECORDS = 8_192
_MAX_TOP_K = 32
_MAX_RETURNED_PAYLOAD_BYTES = 262_144
_CONTINUATION_KEY = secrets.token_bytes(32)


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
class RecallFiltersV1:
    session_ids: tuple[str, ...] = ()
    source_kinds: tuple[SourceKind, ...] = ()
    observed_at_ns_min: int | None = None
    observed_at_ns_max: int | None = None
    preferred_observed_at_ns_min: int | None = None
    preferred_observed_at_ns_max: int | None = None

    def __post_init__(self) -> None:
        if type(self.session_ids) is not tuple or len(self.session_ids) > 32:
            raise InputBoundaryError("session_ids must be a tuple with at most 32 IDs")
        for session_id in self.session_ids:
            validate_event_id(session_id)
        if tuple(sorted(set(self.session_ids))) != self.session_ids:
            raise InputBoundaryError("session_ids must be sorted and unique")

        if type(self.source_kinds) is not tuple:
            raise InputBoundaryError("source_kinds must be a tuple")
        if any(type(source) is not SourceKind for source in self.source_kinds):
            raise InputBoundaryError("source_kinds must contain SourceKind values")
        if tuple(sorted(set(self.source_kinds), key=lambda item: item.value)) != (
            self.source_kinds
        ):
            raise InputBoundaryError("source_kinds must be sorted and unique")

        _validate_optional_range(
            self.observed_at_ns_min,
            self.observed_at_ns_max,
            "observed_at_ns",
        )
        _validate_optional_range(
            self.preferred_observed_at_ns_min,
            self.preferred_observed_at_ns_max,
            "preferred_observed_at_ns",
        )


@dataclass(frozen=True, kw_only=True, slots=True)
class ContentDigestRecallQuery:
    content_digest: str
    filters: RecallFiltersV1 = field(default_factory=RecallFiltersV1)

    def __post_init__(self) -> None:
        _require_digest(self.content_digest, "content_digest")
        if type(self.filters) is not RecallFiltersV1:
            raise InputBoundaryError("filters must be RecallFiltersV1")


@dataclass(frozen=True, kw_only=True, slots=True)
class TextRecallQuery:
    text: str
    filters: RecallFiltersV1 = field(default_factory=RecallFiltersV1)

    def __post_init__(self) -> None:
        encode_retrieval_text(self.text, feature_spec_id=runtime_feature_spec_id())
        if type(self.filters) is not RecallFiltersV1:
            raise InputBoundaryError("filters must be RecallFiltersV1")


@dataclass(frozen=True, kw_only=True, slots=True)
class RecallExecutionPolicyV1:
    max_records: int
    top_k: int
    max_returned_payload_bytes: int
    active_normalizer_id: str
    active_feature_spec_id: str
    minimum_score_q32: int
    minimum_margin_q32: int
    allow_approximate: bool
    allow_incomplete: bool

    def __post_init__(self) -> None:
        _require_bounded_int(self.max_records, "max_records", 0, _MAX_RECORDS)
        _require_bounded_int(self.top_k, "top_k", 1, _MAX_TOP_K)
        _require_bounded_int(
            self.max_returned_payload_bytes,
            "max_returned_payload_bytes",
            0,
            _MAX_RETURNED_PAYLOAD_BYTES,
        )
        if self.active_normalizer_id != runtime_normalizer_id():
            raise InputBoundaryError("active_normalizer_id is incompatible")
        if self.active_feature_spec_id != runtime_feature_spec_id():
            raise InputBoundaryError("active_feature_spec_id is incompatible")
        _require_bounded_int(
            self.minimum_score_q32, "minimum_score_q32", 0, _MAX_Q32
        )
        _require_bounded_int(
            self.minimum_margin_q32, "minimum_margin_q32", 0, _MAX_Q32
        )
        if type(self.allow_approximate) is not bool:
            raise InputBoundaryError("allow_approximate must be bool")
        if type(self.allow_incomplete) is not bool:
            raise InputBoundaryError("allow_incomplete must be bool")


@dataclass(frozen=True, kw_only=True, slots=True)
class RecollectionWorkV1:
    records_scanned: int
    canonical_payload_bytes_decoded: int
    candidates_scored: int
    candidates_returned: int
    output_bytes: int
    exhaustive: bool

    def __post_init__(self) -> None:
        for field_name, value in (
            ("records_scanned", self.records_scanned),
            ("canonical_payload_bytes_decoded", self.canonical_payload_bytes_decoded),
            ("candidates_scored", self.candidates_scored),
            ("candidates_returned", self.candidates_returned),
            ("output_bytes", self.output_bytes),
        ):
            _require_bounded_int(value, field_name, 0, _MAX_I63)
        if self.candidates_returned > _MAX_TOP_K:
            raise InputBoundaryError("candidates_returned exceeds 32")
        if self.output_bytes > _MAX_RETURNED_PAYLOAD_BYTES:
            raise InputBoundaryError("output_bytes exceeds 262144")
        if type(self.exhaustive) is not bool:
            raise InputBoundaryError("exhaustive must be bool")


@dataclass(frozen=True, kw_only=True, slots=True)
class ExactOccurrenceSummaryV1:
    observation_id: str
    episode_id: str
    sequence: int
    record_hash: str
    content_digest: str
    provenance: ProvenanceV1
    temporal_preference_match: bool

    def __post_init__(self) -> None:
        _require_observation_id(self.observation_id)
        if (
            type(self.episode_id) is not str
            or _EPISODE_ID_PATTERN.fullmatch(self.episode_id) is None
        ):
            raise InputBoundaryError("episode_id is invalid")
        _require_bounded_int(self.sequence, "sequence", 1, _MAX_I63)
        _require_digest(self.record_hash, "record_hash")
        _require_digest(self.content_digest, "content_digest")
        if type(self.provenance) is not ProvenanceV1:
            raise InputBoundaryError("provenance is invalid")
        if type(self.temporal_preference_match) is not bool:
            raise InputBoundaryError("temporal_preference_match must be bool")


@dataclass(frozen=True, kw_only=True, slots=True)
class _TextCandidateStateV1:
    observation_id: str
    episode_id: str
    sequence: int
    record_hash: str
    content_digest: str
    observed_at_ns: int
    temporal_preference_match: bool
    similarity: FeatureSimilarityV1
    feature_digest: str

    def __post_init__(self) -> None:
        _require_observation_id(self.observation_id)
        _require_episode_id(self.episode_id)
        _require_bounded_int(self.sequence, "sequence", 1, _MAX_I63)
        _require_digest(self.record_hash, "record_hash")
        _require_digest(self.content_digest, "content_digest")
        _require_bounded_int(self.observed_at_ns, "observed_at_ns", 0, _MAX_I63)
        if type(self.temporal_preference_match) is not bool:
            raise InputBoundaryError("temporal_preference_match must be bool")
        if type(self.similarity) is not FeatureSimilarityV1:
            raise InputBoundaryError("similarity must be FeatureSimilarityV1")
        _require_digest(self.feature_digest, "feature_digest")


class AbstainReason(str, Enum):
    WORK_BUDGET_EXHAUSTED = "work_budget_exhausted"
    PAYLOAD_BUDGET_EXCEEDED = "payload_budget_exceeded"
    APPROXIMATE_DISABLED = "approximate_disabled"


@dataclass(frozen=True, kw_only=True, slots=True)
class AmbiguousExactRecollection:
    content_digest: str
    exact_match_count: int
    summaries: tuple[ExactOccurrenceSummaryV1, ...]
    work: RecollectionWorkV1

    def __post_init__(self) -> None:
        _require_digest(self.content_digest, "content_digest")
        _require_bounded_int(self.exact_match_count, "exact_match_count", 2, _MAX_I63)
        if (
            type(self.summaries) is not tuple
            or not 2 <= len(self.summaries) <= _MAX_TOP_K
            or any(type(item) is not ExactOccurrenceSummaryV1 for item in self.summaries)
            or len(self.summaries) > self.exact_match_count
        ):
            raise InputBoundaryError("ambiguous exact summaries are invalid")
        if any(item.content_digest != self.content_digest for item in self.summaries):
            raise InputBoundaryError("ambiguous exact summaries use a different digest")
        if type(self.work) is not RecollectionWorkV1 or not self.work.exhaustive:
            raise InputBoundaryError("ambiguous exact work must be exhaustive")

    @property
    def content_is_observation(self) -> bool:
        return True

    @property
    def content_is_verified_fact(self) -> bool:
        return False


@dataclass(frozen=True, kw_only=True, slots=True)
class NoScanRecollection:
    content_digest: str
    work: RecollectionWorkV1

    def __post_init__(self) -> None:
        _require_digest(self.content_digest, "content_digest")
        if type(self.work) is not RecollectionWorkV1 or not self.work.exhaustive:
            raise InputBoundaryError("scan absence work must be exhaustive")

    @property
    def content_is_observation(self) -> bool:
        return False

    @property
    def content_is_verified_fact(self) -> bool:
        return False


@dataclass(frozen=True, kw_only=True, slots=True)
class ApproximateCandidateV1:
    content: CanonicalJsonValue | None
    observation_id: str
    episode_id: str
    sequence: int
    record_hash: str
    content_digest: str
    provenance: ProvenanceV1
    score_q32: int
    content_omitted: bool

    def __post_init__(self) -> None:
        if self.content is not None and type(self.content) is not CanonicalJsonValue:
            raise InputBoundaryError("candidate content is invalid")
        _require_observation_id(self.observation_id)
        _require_episode_id(self.episode_id)
        _require_bounded_int(self.sequence, "sequence", 1, _MAX_I63)
        _require_digest(self.record_hash, "record_hash")
        _require_digest(self.content_digest, "content_digest")
        if type(self.provenance) is not ProvenanceV1:
            raise InputBoundaryError("candidate provenance is invalid")
        _require_bounded_int(self.score_q32, "score_q32", 0, _MAX_Q32)
        if type(self.content_omitted) is not bool:
            raise InputBoundaryError("content_omitted must be bool")
        if self.content_omitted != (self.content is None):
            raise InputBoundaryError("content_omitted disagrees with content")

    @property
    def content_is_observation(self) -> bool:
        return self.content is not None

    @property
    def content_is_verified_fact(self) -> bool:
        return False


@dataclass(frozen=True, kw_only=True, slots=True)
class ApproximateCandidates:
    candidates: tuple[ApproximateCandidateV1, ...]
    margin_q32: int
    work: RecollectionWorkV1

    def __post_init__(self) -> None:
        if (
            type(self.candidates) is not tuple
            or not 1 <= len(self.candidates) <= _MAX_TOP_K
            or any(type(item) is not ApproximateCandidateV1 for item in self.candidates)
        ):
            raise InputBoundaryError("approximate candidates are invalid")
        _require_bounded_int(self.margin_q32, "margin_q32", 0, _MAX_Q32)
        if (
            type(self.work) is not RecollectionWorkV1
            or not self.work.exhaustive
            or self.work.candidates_returned != len(self.candidates)
        ):
            raise InputBoundaryError("approximate work is invalid")

    @property
    def content_is_observation(self) -> bool:
        return True

    @property
    def content_is_verified_fact(self) -> bool:
        return False


@dataclass(frozen=True, kw_only=True, slots=True)
class ConflictedRecollection:
    candidates: tuple[ApproximateCandidateV1, ApproximateCandidateV1]
    margin_q32: int
    work: RecollectionWorkV1

    def __post_init__(self) -> None:
        if (
            type(self.candidates) is not tuple
            or len(self.candidates) != 2
            or any(type(item) is not ApproximateCandidateV1 for item in self.candidates)
            or any(not item.content_omitted for item in self.candidates)
            or self.candidates[0].content_digest == self.candidates[1].content_digest
        ):
            raise InputBoundaryError("conflict candidates are invalid")
        _require_bounded_int(self.margin_q32, "margin_q32", 0, _MAX_Q32)
        if (
            type(self.work) is not RecollectionWorkV1
            or not self.work.exhaustive
            or self.work.candidates_returned != 2
            or self.work.output_bytes != 0
        ):
            raise InputBoundaryError("conflict work is invalid")

    @property
    def content_is_observation(self) -> bool:
        return True

    @property
    def content_is_verified_fact(self) -> bool:
        return False


@dataclass(frozen=True, kw_only=True, slots=True)
class NoTextRecollection:
    query_digest: str
    work: RecollectionWorkV1

    def __post_init__(self) -> None:
        _require_digest(self.query_digest, "query_digest")
        if type(self.work) is not RecollectionWorkV1 or not self.work.exhaustive:
            raise InputBoundaryError("text absence work must be exhaustive")

    @property
    def content_is_observation(self) -> bool:
        return False

    @property
    def content_is_verified_fact(self) -> bool:
        return False


@dataclass(frozen=True, slots=True, init=False)
class RecallContinuationV1:
    checkpoint: LedgerCursorCheckpoint
    query_digest: str
    policy_digest: str
    profile_digest: str
    exact_match_count: int
    exact_summaries: tuple[ExactOccurrenceSummaryV1, ...]
    text_candidates: tuple[_TextCandidateStateV1, ...]
    conflict_candidates: tuple[_TextCandidateStateV1, ...]
    work: RecollectionWorkV1
    _authenticator: bytes = field(repr=False, compare=False)


@dataclass(frozen=True, kw_only=True, slots=True)
class IncompleteRecollection:
    continuation: RecallContinuationV1
    work: RecollectionWorkV1
    exact_match_count: int

    def __post_init__(self) -> None:
        if type(self.continuation) is not RecallContinuationV1:
            raise InputBoundaryError("continuation is invalid")
        if type(self.work) is not RecollectionWorkV1 or self.work.exhaustive:
            raise InputBoundaryError("incomplete work cannot be exhaustive")
        _require_bounded_int(self.exact_match_count, "exact_match_count", 0, _MAX_I63)
        if (
            self.work != self.continuation.work
            or self.exact_match_count != self.continuation.exact_match_count
        ):
            raise InputBoundaryError("incomplete result disagrees with continuation")

    @property
    def content_is_observation(self) -> bool:
        return False

    @property
    def content_is_verified_fact(self) -> bool:
        return False


@dataclass(frozen=True, kw_only=True, slots=True)
class AbstainedRecollection:
    reason: AbstainReason
    work: RecollectionWorkV1
    continuation: None = None

    def __post_init__(self) -> None:
        if type(self.reason) is not AbstainReason:
            raise InputBoundaryError("abstention reason is invalid")
        if type(self.work) is not RecollectionWorkV1:
            raise InputBoundaryError("abstention work is invalid")
        if self.continuation is not None:
            raise InputBoundaryError("abstention cannot carry a continuation")

    @property
    def content_is_observation(self) -> bool:
        return False

    @property
    def content_is_verified_fact(self) -> bool:
        return False


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
    work: RecollectionWorkV1 | None = None

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
        if self.work is not None and type(self.work) is not RecollectionWorkV1:
            raise InputBoundaryError("recollection work is invalid")

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


@overload
def recall(
    session: VerifiedLedgerSession,
    query: EventIdRecallQuery,
) -> ExactRecollection | NoRecollection:
    ...


@overload
def recall(
    session: VerifiedLedgerSession,
    query: ContentDigestRecallQuery,
    *,
    policy: RecallExecutionPolicyV1,
    continuation: RecallContinuationV1 | None = None,
) -> (
    ExactRecollection
    | AmbiguousExactRecollection
    | NoScanRecollection
    | IncompleteRecollection
    | AbstainedRecollection
):
    ...


@overload
def recall(
    session: VerifiedLedgerSession,
    query: TextRecallQuery,
    *,
    policy: RecallExecutionPolicyV1,
    continuation: RecallContinuationV1 | None = None,
) -> (
    ApproximateCandidates
    | ConflictedRecollection
    | NoTextRecollection
    | IncompleteRecollection
    | AbstainedRecollection
):
    ...


def recall(
    session: VerifiedLedgerSession,
    query: EventIdRecallQuery | ContentDigestRecallQuery | TextRecallQuery,
    *,
    policy: RecallExecutionPolicyV1 | None = None,
    continuation: RecallContinuationV1 | None = None,
) -> (
    ExactRecollection
    | NoRecollection
    | AmbiguousExactRecollection
    | NoScanRecollection
    | ApproximateCandidates
    | ConflictedRecollection
    | NoTextRecollection
    | IncompleteRecollection
    | AbstainedRecollection
):
    active = _require_session(session)
    if type(query) is ContentDigestRecallQuery:
        if type(policy) is not RecallExecutionPolicyV1:
            raise InputBoundaryError("scan recall requires RecallExecutionPolicyV1")
        return _recall_content_digest(active, query, policy, continuation)
    if type(query) is TextRecallQuery:
        if type(policy) is not RecallExecutionPolicyV1:
            raise InputBoundaryError("scan recall requires RecallExecutionPolicyV1")
        if policy.top_k < 2:
            raise InputBoundaryError("text recall policy top_k must be at least 2")
        return _recall_text(active, query, policy, continuation)
    if type(query) is not EventIdRecallQuery:
        raise InputBoundaryError("query is not a supported recall query")
    if policy is not None or continuation is not None:
        raise InputBoundaryError("direct-ID recall does not accept scan state")
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


def _recall_content_digest(
    session: VerifiedLedgerSession,
    query: ContentDigestRecallQuery,
    policy: RecallExecutionPolicyV1,
    continuation: RecallContinuationV1 | None,
) -> (
    ExactRecollection
    | AmbiguousExactRecollection
    | NoScanRecollection
    | IncompleteRecollection
    | AbstainedRecollection
):
    query_digest = _query_digest(query)
    policy_digest = _policy_digest(policy)
    if continuation is None:
        cursor = session.cursor(
            after_sequence=0,
            batch_size=max(1, min(policy.max_records, 64)),
        )
        exact_match_count = 0
        summaries: tuple[ExactOccurrenceSummaryV1, ...] = ()
        prior_work = _empty_work(exhaustive=False)
    else:
        _validate_continuation(
            continuation,
            query_digest=query_digest,
            policy_digest=policy_digest,
        )
        cursor = session.resume_verified(
            continuation.checkpoint,
            batch_size=max(1, min(policy.max_records, 64)),
        )
        exact_match_count = continuation.exact_match_count
        summaries = continuation.exact_summaries
        prior_work = continuation.work

    page_records = 0
    page_bytes = 0
    try:
        while page_records < policy.max_records:
            try:
                record = next(cursor)
            except StopIteration:
                break
            page_records += 1
            page_bytes += len(canonical_json_bytes(record.payload))
            observation = _scan_observation(record.payload, record.event_id, record.sequence)
            if observation is None or not _matches_filters(observation, query.filters):
                continue
            if observation.content_digest != query.content_digest:
                continue
            exact_match_count += 1
            summaries = _retain_exact_summary(
                summaries,
                _summary_from_observation(record, observation, query.filters),
            )
    except BaseException as primary:
        try:
            cursor.close()
        except BaseException as cleanup_failure:
            raise primary from cleanup_failure
        raise

    checkpoint = cursor.suspend()
    exhaustive = checkpoint.next_sequence == checkpoint.snapshot_head_sequence + 1
    work = RecollectionWorkV1(
        records_scanned=prior_work.records_scanned + page_records,
        canonical_payload_bytes_decoded=(
            prior_work.canonical_payload_bytes_decoded + page_bytes
        ),
        candidates_scored=prior_work.candidates_scored,
        candidates_returned=0,
        output_bytes=0,
        exhaustive=exhaustive,
    )
    if not exhaustive:
        if not policy.allow_incomplete:
            return AbstainedRecollection(
                reason=AbstainReason.WORK_BUDGET_EXHAUSTED,
                work=work,
            )
        next_continuation = _make_continuation(
            checkpoint=checkpoint,
            query_digest=query_digest,
            policy_digest=policy_digest,
            exact_match_count=exact_match_count,
            exact_summaries=summaries,
            work=work,
        )
        return IncompleteRecollection(
            continuation=next_continuation,
            work=work,
            exact_match_count=exact_match_count,
        )
    if exact_match_count == 0:
        return NoScanRecollection(content_digest=query.content_digest, work=work)
    if exact_match_count > 1:
        return AmbiguousExactRecollection(
            content_digest=query.content_digest,
            exact_match_count=exact_match_count,
            summaries=summaries,
            work=work,
        )

    if len(summaries) != 1:
        raise LedgerIntegrityError("exact-match accumulator is inconsistent")
    summary = summaries[0]
    record = session.read(summary.observation_id)
    observation = None
    if record is not None:
        observation = _scan_observation(record.payload, record.event_id, record.sequence)
    if (
        record is None
        or observation is None
        or record.sequence != summary.sequence
        or record.record_hash != summary.record_hash
        or observation.content_digest != query.content_digest
    ):
        raise LedgerIntegrityError("selected exact occurrence changed after scan")
    returned_bytes = len(observation.request.content.canonical_bytes)
    if returned_bytes > policy.max_returned_payload_bytes:
        return AbstainedRecollection(
            reason=AbstainReason.PAYLOAD_BUDGET_EXCEEDED,
            work=work,
        )
    completed_work = RecollectionWorkV1(
        records_scanned=work.records_scanned,
        canonical_payload_bytes_decoded=work.canonical_payload_bytes_decoded,
        candidates_scored=work.candidates_scored,
        candidates_returned=1,
        output_bytes=returned_bytes,
        exhaustive=True,
    )
    return ExactRecollection(
        content=observation.request.content,
        observation_id=observation.request.observation_id,
        episode_id=observation.boundary_decision.episode_id,
        sequence=record.sequence,
        record_hash=record.record_hash,
        content_digest=observation.content_digest,
        provenance=observation.request.provenance,
        basis=RecallBasis.CONTENT_DIGEST,
        work=completed_work,
    )


def _recall_text(
    session: VerifiedLedgerSession,
    query: TextRecallQuery,
    policy: RecallExecutionPolicyV1,
    continuation: RecallContinuationV1 | None,
) -> (
    ApproximateCandidates
    | ConflictedRecollection
    | NoTextRecollection
    | IncompleteRecollection
    | AbstainedRecollection
):
    query_digest = _query_digest(query)
    policy_digest = _policy_digest(policy)
    query_vector = encode_retrieval_text(
        query.text,
        feature_spec_id=policy.active_feature_spec_id,
    )
    if continuation is None:
        cursor = session.cursor(
            after_sequence=0,
            batch_size=max(1, min(policy.max_records, 64)),
        )
        candidates: tuple[_TextCandidateStateV1, ...] = ()
        conflict_candidates: tuple[_TextCandidateStateV1, ...] = ()
        prior_work = _empty_work(exhaustive=False)
    else:
        _validate_continuation(
            continuation,
            query_digest=query_digest,
            policy_digest=policy_digest,
        )
        if continuation.exact_match_count != 0 or continuation.exact_summaries:
            raise InputBoundaryError("text continuation carries exact-digest state")
        cursor = session.resume_verified(
            continuation.checkpoint,
            batch_size=max(1, min(policy.max_records, 64)),
        )
        candidates = continuation.text_candidates
        conflict_candidates = continuation.conflict_candidates
        prior_work = continuation.work

    page_records = 0
    page_bytes = 0
    page_candidates_scored = 0
    try:
        while page_records < policy.max_records:
            try:
                record = next(cursor)
            except StopIteration:
                break
            page_records += 1
            page_bytes += len(canonical_json_bytes(record.payload))
            observation = _scan_observation(record.payload, record.event_id, record.sequence)
            if observation is None or not _matches_filters(observation, query.filters):
                continue
            retrieval_text = observation.request.retrieval_text
            if retrieval_text is None:
                continue
            candidate_vector = encode_retrieval_text(
                retrieval_text,
                feature_spec_id=policy.active_feature_spec_id,
            )
            similarity = measure_feature_similarity(query_vector, candidate_vector)
            page_candidates_scored += 1
            if similarity.score_q32 < policy.minimum_score_q32:
                continue
            candidate_state = _text_candidate_state(
                record,
                observation,
                query.filters,
                similarity,
                candidate_vector,
            )
            candidates = _retain_text_candidate(
                candidates,
                candidate_state,
                top_k=policy.top_k,
            )
            conflict_candidates = _retain_conflict_candidate(
                conflict_candidates,
                candidate_state,
            )
    except BaseException as primary:
        try:
            cursor.close()
        except BaseException as cleanup_failure:
            raise primary from cleanup_failure
        raise

    checkpoint = cursor.suspend()
    exhaustive = checkpoint.next_sequence == checkpoint.snapshot_head_sequence + 1
    work = RecollectionWorkV1(
        records_scanned=prior_work.records_scanned + page_records,
        canonical_payload_bytes_decoded=(
            prior_work.canonical_payload_bytes_decoded + page_bytes
        ),
        candidates_scored=prior_work.candidates_scored + page_candidates_scored,
        candidates_returned=0,
        output_bytes=0,
        exhaustive=exhaustive,
    )
    if not exhaustive:
        if not policy.allow_incomplete:
            return AbstainedRecollection(
                reason=AbstainReason.WORK_BUDGET_EXHAUSTED,
                work=work,
            )
        next_continuation = _make_continuation(
            checkpoint=checkpoint,
            query_digest=query_digest,
            policy_digest=policy_digest,
            exact_match_count=0,
            exact_summaries=(),
            text_candidates=candidates,
            conflict_candidates=conflict_candidates,
            work=work,
        )
        return IncompleteRecollection(
            continuation=next_continuation,
            work=work,
            exact_match_count=0,
        )
    if not candidates:
        return NoTextRecollection(query_digest=query_digest, work=work)
    if not conflict_candidates:
        raise LedgerIntegrityError("text conflict accumulator is inconsistent")

    margin_q32 = _top_two_margin_q32(conflict_candidates)
    if len(conflict_candidates) >= 2 and margin_q32 <= policy.minimum_margin_q32:
        competing = tuple(
            _hydrate_text_candidate(
                session,
                state,
                query_vector=query_vector,
                filters=query.filters,
                remaining_output_bytes=None,
            )[0]
            for state in conflict_candidates
        )
        if len(competing) != 2:
            raise LedgerIntegrityError("conflict accumulator is inconsistent")
        conflict_work = _completed_text_work(work, returned=2, output_bytes=0)
        return ConflictedRecollection(
            candidates=(competing[0], competing[1]),
            margin_q32=margin_q32,
            work=conflict_work,
        )

    if not policy.allow_approximate:
        return AbstainedRecollection(
            reason=AbstainReason.APPROXIMATE_DISABLED,
            work=work,
        )

    remaining_output_bytes = policy.max_returned_payload_bytes
    output_bytes = 0
    hydrated: list[ApproximateCandidateV1] = []
    for state in candidates:
        candidate, attached_bytes = _hydrate_text_candidate(
            session,
            state,
            query_vector=query_vector,
            filters=query.filters,
            remaining_output_bytes=remaining_output_bytes,
        )
        remaining_output_bytes -= attached_bytes
        output_bytes += attached_bytes
        hydrated.append(candidate)
    completed_work = _completed_text_work(
        work,
        returned=len(hydrated),
        output_bytes=output_bytes,
    )
    return ApproximateCandidates(
        candidates=tuple(hydrated),
        margin_q32=margin_q32,
        work=completed_work,
    )


def _text_candidate_state(
    record: LedgerRecord,
    observation: CanonicalObservationV1,
    filters: RecallFiltersV1,
    similarity: FeatureSimilarityV1,
    feature_vector: RetrievalFeatureVectorV1,
) -> _TextCandidateStateV1:
    return _TextCandidateStateV1(
        observation_id=observation.request.observation_id,
        episode_id=observation.boundary_decision.episode_id,
        sequence=record.sequence,
        record_hash=record.record_hash,
        content_digest=observation.content_digest,
        observed_at_ns=observation.request.provenance.observed_at_ns,
        temporal_preference_match=_temporal_preference_match(observation, filters),
        similarity=similarity,
        feature_digest=feature_vector_digest(feature_vector),
    )


def _retain_text_candidate(
    candidates: tuple[_TextCandidateStateV1, ...],
    candidate: _TextCandidateStateV1,
    *,
    top_k: int,
) -> tuple[_TextCandidateStateV1, ...]:
    retained = [*candidates, candidate]
    retained.sort(key=cmp_to_key(_compare_text_candidates))
    return tuple(retained[:top_k])


def _retain_conflict_candidate(
    candidates: tuple[_TextCandidateStateV1, ...],
    candidate: _TextCandidateStateV1,
) -> tuple[_TextCandidateStateV1, ...]:
    retained = list(candidates)
    same_digest_index = next(
        (
            index
            for index, current in enumerate(retained)
            if current.content_digest == candidate.content_digest
        ),
        None,
    )
    if same_digest_index is None:
        retained.append(candidate)
    elif _compare_text_candidates(candidate, retained[same_digest_index]) < 0:
        retained[same_digest_index] = candidate
    retained.sort(key=cmp_to_key(_compare_text_candidates))
    return tuple(retained[:2])


def _compare_text_candidates(
    left: _TextCandidateStateV1,
    right: _TextCandidateStateV1,
) -> int:
    similarity_order = compare_feature_similarity_exact(
        left.similarity,
        right.similarity,
    )
    if similarity_order:
        return -similarity_order
    if left.temporal_preference_match != right.temporal_preference_match:
        return -1 if left.temporal_preference_match else 1
    if left.observed_at_ns != right.observed_at_ns:
        return -1 if left.observed_at_ns > right.observed_at_ns else 1
    if left.sequence != right.sequence:
        return -1 if left.sequence > right.sequence else 1
    return (left.observation_id > right.observation_id) - (
        left.observation_id < right.observation_id
    )


def _top_two_margin_q32(candidates: tuple[_TextCandidateStateV1, ...]) -> int:
    top_score = candidates[0].similarity.score_q32
    second_score = candidates[1].similarity.score_q32 if len(candidates) >= 2 else 0
    if second_score > top_score:
        raise LedgerIntegrityError("candidate score order is inconsistent")
    return top_score - second_score


def _hydrate_text_candidate(
    session: VerifiedLedgerSession,
    state: _TextCandidateStateV1,
    *,
    query_vector: RetrievalFeatureVectorV1,
    filters: RecallFiltersV1,
    remaining_output_bytes: int | None,
) -> tuple[ApproximateCandidateV1, int]:
    record, observation = _read_and_revalidate_text_candidate(session, state)
    retrieval_text = observation.request.retrieval_text
    if retrieval_text is None or not _matches_filters(observation, filters):
        raise LedgerIntegrityError("selected text candidate is no longer eligible")
    candidate_vector = encode_retrieval_text(
        retrieval_text,
        feature_spec_id=query_vector.feature_spec_id,
    )
    similarity = measure_feature_similarity(query_vector, candidate_vector)
    if (
        feature_vector_digest(candidate_vector) != state.feature_digest
        or similarity != state.similarity
        or observation.request.provenance.observed_at_ns != state.observed_at_ns
        or _temporal_preference_match(observation, filters)
        != state.temporal_preference_match
    ):
        raise LedgerIntegrityError("selected text candidate ranking changed after scan")
    content_bytes = len(observation.request.content.canonical_bytes)
    attach_content = (
        remaining_output_bytes is not None
        and content_bytes <= remaining_output_bytes
    )
    candidate = ApproximateCandidateV1(
        content=observation.request.content if attach_content else None,
        observation_id=state.observation_id,
        episode_id=state.episode_id,
        sequence=record.sequence,
        record_hash=record.record_hash,
        content_digest=state.content_digest,
        provenance=observation.request.provenance,
        score_q32=state.similarity.score_q32,
        content_omitted=not attach_content,
    )
    return candidate, content_bytes if attach_content else 0


def _read_and_revalidate_text_candidate(
    session: VerifiedLedgerSession,
    state: _TextCandidateStateV1,
) -> tuple[LedgerRecord, CanonicalObservationV1]:
    record = session.read(state.observation_id)
    observation = None
    if record is not None:
        observation = _scan_observation(record.payload, record.event_id, record.sequence)
    if (
        record is None
        or observation is None
        or record.sequence != state.sequence
        or record.record_hash != state.record_hash
        or observation.content_digest != state.content_digest
        or observation.boundary_decision.episode_id != state.episode_id
    ):
        raise LedgerIntegrityError("selected text candidate changed after scan")
    return record, observation


def _completed_text_work(
    work: RecollectionWorkV1,
    *,
    returned: int,
    output_bytes: int,
) -> RecollectionWorkV1:
    return RecollectionWorkV1(
        records_scanned=work.records_scanned,
        canonical_payload_bytes_decoded=work.canonical_payload_bytes_decoded,
        candidates_scored=work.candidates_scored,
        candidates_returned=returned,
        output_bytes=output_bytes,
        exhaustive=True,
    )


def _scan_observation(
    payload: JsonValue,
    event_id: str,
    sequence: int,
) -> CanonicalObservationV1 | None:
    claims_observation = (
        type(payload) is dict
        and cast(dict[str, JsonValue], payload).get("schema")
        == _CANONICAL_OBSERVATION_SCHEMA
    )
    try:
        observation = canonical_observation_from_json_value(payload)
    except InputBoundaryError as exc:
        if claims_observation:
            raise LedgerIntegrityError(
                "malformed Task 2 observation encountered during recall"
            ) from exc
        return None
    if (
        observation.request.observation_id != event_id
        or observation.pre_append_head_sequence + 1 != sequence
        or observation.post_core_state.last_observation_id != event_id
        or observation.post_core_state.last_observation_sequence != sequence
    ):
        raise LedgerIntegrityError("Task 2 observation position is invalid during recall")
    return observation


def _matches_filters(
    observation: CanonicalObservationV1,
    filters: RecallFiltersV1,
) -> bool:
    request = observation.request
    observed_at_ns = request.provenance.observed_at_ns
    return (
        (not filters.session_ids or request.session_id in filters.session_ids)
        and (
            not filters.source_kinds
            or request.provenance.source_kind in filters.source_kinds
        )
        and (
            filters.observed_at_ns_min is None
            or cast(int, filters.observed_at_ns_min) <= observed_at_ns
        )
        and (
            filters.observed_at_ns_max is None
            or observed_at_ns <= cast(int, filters.observed_at_ns_max)
        )
    )


def _summary_from_observation(
    record: LedgerRecord,
    observation: CanonicalObservationV1,
    filters: RecallFiltersV1,
) -> ExactOccurrenceSummaryV1:
    return ExactOccurrenceSummaryV1(
        observation_id=observation.request.observation_id,
        episode_id=observation.boundary_decision.episode_id,
        sequence=record.sequence,
        record_hash=record.record_hash,
        content_digest=observation.content_digest,
        provenance=observation.request.provenance,
        temporal_preference_match=_temporal_preference_match(observation, filters),
    )


def _temporal_preference_match(
    observation: CanonicalObservationV1,
    filters: RecallFiltersV1,
) -> bool:
    observed_at_ns = observation.request.provenance.observed_at_ns
    return (
        filters.preferred_observed_at_ns_min is not None
        and cast(int, filters.preferred_observed_at_ns_min) <= observed_at_ns
        and observed_at_ns <= cast(int, filters.preferred_observed_at_ns_max)
    )


def _retain_exact_summary(
    summaries: tuple[ExactOccurrenceSummaryV1, ...],
    candidate: ExactOccurrenceSummaryV1,
) -> tuple[ExactOccurrenceSummaryV1, ...]:
    retained = [*summaries, candidate]
    retained.sort(
        key=lambda item: (
            -int(item.temporal_preference_match),
            -item.provenance.observed_at_ns,
            -item.sequence,
            item.observation_id,
        )
    )
    return tuple(retained[:_MAX_TOP_K])


def _make_continuation(
    *,
    checkpoint: LedgerCursorCheckpoint,
    query_digest: str,
    policy_digest: str,
    exact_match_count: int,
    exact_summaries: tuple[ExactOccurrenceSummaryV1, ...],
    work: RecollectionWorkV1,
    text_candidates: tuple[_TextCandidateStateV1, ...] = (),
    conflict_candidates: tuple[_TextCandidateStateV1, ...] = (),
) -> RecallContinuationV1:
    continuation = object.__new__(RecallContinuationV1)
    object.__setattr__(continuation, "checkpoint", checkpoint)
    object.__setattr__(continuation, "query_digest", query_digest)
    object.__setattr__(continuation, "policy_digest", policy_digest)
    object.__setattr__(
        continuation, "profile_digest", _no_calibration_profile_digest()
    )
    object.__setattr__(continuation, "exact_match_count", exact_match_count)
    object.__setattr__(continuation, "exact_summaries", exact_summaries)
    object.__setattr__(continuation, "text_candidates", text_candidates)
    object.__setattr__(continuation, "conflict_candidates", conflict_candidates)
    object.__setattr__(continuation, "work", work)
    authenticator = hmac.new(
        _CONTINUATION_KEY,
        canonical_json_bytes(_continuation_payload(continuation)),
        hashlib.sha256,
    ).digest()
    object.__setattr__(continuation, "_authenticator", authenticator)
    return continuation


def _validate_continuation(
    continuation: RecallContinuationV1,
    *,
    query_digest: str,
    policy_digest: str,
) -> None:
    if type(continuation) is not RecallContinuationV1:
        raise InputBoundaryError("continuation must be RecallContinuationV1")
    try:
        if (
            type(continuation.text_candidates) is not tuple
            or len(continuation.text_candidates) > _MAX_TOP_K
            or any(
                type(candidate) is not _TextCandidateStateV1
                for candidate in continuation.text_candidates
            )
            or type(continuation.conflict_candidates) is not tuple
            or len(continuation.conflict_candidates) > 2
            or any(
                type(candidate) is not _TextCandidateStateV1
                for candidate in continuation.conflict_candidates
            )
            or len(
                {
                    candidate.content_digest
                    for candidate in continuation.conflict_candidates
                }
            )
            != len(continuation.conflict_candidates)
        ):
            raise InputBoundaryError("recall continuation candidates are malformed")
        expected = hmac.new(
            _CONTINUATION_KEY,
            canonical_json_bytes(_continuation_payload(continuation)),
            hashlib.sha256,
        ).digest()
        authentic = hmac.compare_digest(continuation._authenticator, expected)
    except (AttributeError, InputBoundaryError, TypeError, ValueError) as exc:
        raise InputBoundaryError("recall continuation is malformed") from exc
    if not authentic:
        raise InputBoundaryError("recall continuation authentication failed")
    if continuation.query_digest != query_digest:
        raise InputBoundaryError("recall continuation query changed")
    if continuation.policy_digest != policy_digest:
        raise InputBoundaryError("recall continuation policy changed")
    if continuation.profile_digest != _no_calibration_profile_digest():
        raise InputBoundaryError("recall continuation profile changed")


def _continuation_payload(continuation: RecallContinuationV1) -> JsonValue:
    return cast(
        JsonValue,
        {
            "checkpoint": {
                "ledger_id": continuation.checkpoint.ledger_id,
                "next_sequence": continuation.checkpoint.next_sequence,
                "snapshot_head_hash": continuation.checkpoint.snapshot_head_hash,
                "snapshot_head_sequence": continuation.checkpoint.snapshot_head_sequence,
            },
            "conflict_candidates": [
                _text_candidate_state_payload(item)
                for item in continuation.conflict_candidates
            ],
            "exact_match_count": continuation.exact_match_count,
            "exact_summaries": [_summary_payload(item) for item in continuation.exact_summaries],
            "policy_digest": continuation.policy_digest,
            "profile_digest": continuation.profile_digest,
            "query_digest": continuation.query_digest,
            "text_candidates": [
                _text_candidate_state_payload(item)
                for item in continuation.text_candidates
            ],
            "work": _work_payload(continuation.work),
        },
    )


def _summary_payload(summary: ExactOccurrenceSummaryV1) -> dict[str, JsonValue]:
    return {
        "capture_method": summary.provenance.capture_method,
        "capture_version": summary.provenance.capture_version,
        "content_digest": summary.content_digest,
        "episode_id": summary.episode_id,
        "observation_id": summary.observation_id,
        "observed_at_ns": summary.provenance.observed_at_ns,
        "origin_id": summary.provenance.origin_id,
        "parent_observation_ids": list(summary.provenance.parent_observation_ids),
        "record_hash": summary.record_hash,
        "sequence": summary.sequence,
        "source_instance_id": summary.provenance.source_instance_id,
        "source_kind": summary.provenance.source_kind.value,
        "temporal_preference_match": summary.temporal_preference_match,
    }


def _text_candidate_state_payload(
    candidate: _TextCandidateStateV1,
) -> dict[str, JsonValue]:
    similarity = candidate.similarity
    return {
        "candidate_squared_norm": similarity.candidate_squared_norm,
        "content_digest": candidate.content_digest,
        "dot_product": similarity.dot_product,
        "episode_id": candidate.episode_id,
        "feature_digest": candidate.feature_digest,
        "observation_id": candidate.observation_id,
        "observed_at_ns": candidate.observed_at_ns,
        "query_squared_norm": similarity.query_squared_norm,
        "record_hash": candidate.record_hash,
        "score_q32": similarity.score_q32,
        "sequence": candidate.sequence,
        "temporal_preference_match": candidate.temporal_preference_match,
    }


def _work_payload(work: RecollectionWorkV1) -> dict[str, JsonValue]:
    return {
        "candidates_returned": work.candidates_returned,
        "candidates_scored": work.candidates_scored,
        "canonical_payload_bytes_decoded": work.canonical_payload_bytes_decoded,
        "exhaustive": work.exhaustive,
        "output_bytes": work.output_bytes,
        "records_scanned": work.records_scanned,
    }


def _query_digest(query: ContentDigestRecallQuery | TextRecallQuery) -> str:
    filters = query.filters
    common: dict[str, JsonValue] = {
        "filters": {
            "observed_at_ns_max": filters.observed_at_ns_max,
            "observed_at_ns_min": filters.observed_at_ns_min,
            "preferred_observed_at_ns_max": filters.preferred_observed_at_ns_max,
            "preferred_observed_at_ns_min": filters.preferred_observed_at_ns_min,
            "session_ids": list(filters.session_ids),
            "source_kinds": [item.value for item in filters.source_kinds],
        },
    }
    if type(query) is ContentDigestRecallQuery:
        common["content_digest"] = query.content_digest
        common["query_kind"] = "content_digest"
    elif type(query) is TextRecallQuery:
        common["query_kind"] = "text"
        common["text"] = query.text
    else:
        raise InputBoundaryError("scan query is unsupported")
    payload = cast(JsonValue, common)
    return _domain_digest(_QUERY_DIGEST_DOMAIN, canonical_json_bytes(payload))


def _policy_digest(policy: RecallExecutionPolicyV1) -> str:
    payload = cast(
        JsonValue,
        {
            "active_feature_spec_id": policy.active_feature_spec_id,
            "active_normalizer_id": policy.active_normalizer_id,
            "allow_approximate": policy.allow_approximate,
            "allow_incomplete": policy.allow_incomplete,
            "max_records": policy.max_records,
            "max_returned_payload_bytes": policy.max_returned_payload_bytes,
            "minimum_margin_q32": policy.minimum_margin_q32,
            "minimum_score_q32": policy.minimum_score_q32,
            "top_k": policy.top_k,
        },
    )
    return _domain_digest(_POLICY_DIGEST_DOMAIN, canonical_json_bytes(payload))


def _no_calibration_profile_digest() -> str:
    global _NO_CALIBRATION_PROFILE_DIGEST
    if not _NO_CALIBRATION_PROFILE_DIGEST:
        _NO_CALIBRATION_PROFILE_DIGEST = _domain_digest(_NO_PROFILE_DOMAIN, b"null")
    return _NO_CALIBRATION_PROFILE_DIGEST


def _domain_digest(domain: bytes, payload: bytes) -> str:
    framed = (
        struct.pack(">Q", len(domain))
        + domain
        + struct.pack(">Q", len(payload))
        + payload
    )
    return hashlib.sha256(framed).hexdigest()


def _empty_work(*, exhaustive: bool) -> RecollectionWorkV1:
    return RecollectionWorkV1(
        records_scanned=0,
        canonical_payload_bytes_decoded=0,
        candidates_scored=0,
        candidates_returned=0,
        output_bytes=0,
        exhaustive=exhaustive,
    )


def _validate_optional_range(
    lower: int | None,
    upper: int | None,
    field_name: str,
) -> None:
    if (lower is None) != (upper is None):
        raise InputBoundaryError(f"{field_name} bounds must be supplied together")
    if lower is None:
        return
    _require_bounded_int(lower, f"{field_name}_min", 0, _MAX_I63)
    _require_bounded_int(cast(int, upper), f"{field_name}_max", 0, _MAX_I63)
    if lower > cast(int, upper):
        raise InputBoundaryError(f"{field_name} lower bound exceeds upper bound")


def _require_bounded_int(
    value: int,
    field_name: str,
    lower: int,
    upper: int,
) -> None:
    if type(value) is not int or not lower <= value <= upper:
        raise InputBoundaryError(f"{field_name} is outside its allowed range")


def _require_session(value: object) -> VerifiedLedgerSession:
    if type(value) is not VerifiedLedgerSession:
        raise InputBoundaryError("an active VerifiedLedgerSession is required")
    return value


def _require_observation_id(value: str) -> None:
    if type(value) is not str or _OBSERVATION_ID_PATTERN.fullmatch(value) is None:
        raise InputBoundaryError("observation_id is invalid")


def _require_episode_id(value: str) -> None:
    if type(value) is not str or _EPISODE_ID_PATTERN.fullmatch(value) is None:
        raise InputBoundaryError("episode_id is invalid")


def _require_digest(value: str, field_name: str) -> None:
    if type(value) is not str or _DIGEST_PATTERN.fullmatch(value) is None:
        raise InputBoundaryError(f"{field_name} must be a lowercase SHA-256 digest")


__all__ = [
    "AbstainReason",
    "AbstainedRecollection",
    "AmbiguousExactRecollection",
    "ApproximateCandidateV1",
    "ApproximateCandidates",
    "ConflictedRecollection",
    "ContentDigestRecallQuery",
    "EventIdRecallQuery",
    "ExactOccurrenceSummaryV1",
    "ExactRecollection",
    "IncompleteRecollection",
    "NoRecollection",
    "NoScanRecollection",
    "NoTextRecollection",
    "RecallBasis",
    "RecallContinuationV1",
    "RecallExecutionPolicyV1",
    "RecallFiltersV1",
    "RecollectionWorkV1",
    "TextRecallQuery",
    "recall",
]
