from __future__ import annotations

import hashlib
import math
import struct
import unicodedata
from collections.abc import Iterable, Iterator
from dataclasses import dataclass
from typing import cast

from .codec import canonical_json_bytes
from .contracts import InputBoundaryError, JsonValue

MAX_RETRIEVAL_TEXT_BYTES = 4_096
FEATURE_DIMENSIONS = 1_024
FEATURE_VECTOR_BYTES = FEATURE_DIMENSIONS * 2

_NORMALIZER_ID_PREFIX = "aluclu.search-view.nfc-ascii-ws.v1+ucd-"
_FEATURE_SPEC_ID_PREFIX = "aluclu.feature.signed-byte-ngram-1024-int16.v1+ucd-"
_FEATURE_VECTOR_DOMAIN = b"aluclu.task2.feature-vector.v1"
_FEATURE_FRAME_PREFIX = b"\xff\x01"
_FEATURE_FRAME_SUFFIX = b"\xff\x02"
_FEATURE_GRAM_LENGTHS = (3, 4, 5)
_FEATURE_GRAM_DOMAIN = b"\x01"
_BLAKE2S_PERSON = b"al2feat1"
_MIN_FEATURE_BIN = -32_767
_MAX_FEATURE_BIN = 32_767
_Q32_ONE = 1 << 32
_WHITESPACE = frozenset("\t\n\v\f ")


@dataclass(frozen=True, kw_only=True, slots=True)
class RetrievalFeatureVectorV1:
    """Portable, fixed-width signed byte n-gram feature vector."""

    feature_spec_id: str
    bins_i16be: bytes

    def __post_init__(self) -> None:
        _require_active_id(
            self.feature_spec_id,
            expected=active_feature_spec_id(),
            field_name="feature_spec_id",
        )
        if type(self.bins_i16be) is not bytes:
            raise InputBoundaryError("bins_i16be must be bytes")
        if len(self.bins_i16be) != FEATURE_VECTOR_BYTES:
            raise InputBoundaryError("bins_i16be must contain exactly 2048 bytes")


@dataclass(frozen=True, kw_only=True, slots=True)
class FeatureSimilarityV1:
    """Exact integer sufficient statistics plus their conservative Q32 score."""

    dot_product: int
    query_squared_norm: int
    candidate_squared_norm: int
    score_q32: int

    def __post_init__(self) -> None:
        for field_name, value in (
            ("dot_product", self.dot_product),
            ("query_squared_norm", self.query_squared_norm),
            ("candidate_squared_norm", self.candidate_squared_norm),
            ("score_q32", self.score_q32),
        ):
            if type(value) is not int:
                raise InputBoundaryError(f"{field_name} must be an integer")
        if self.query_squared_norm < 0 or self.candidate_squared_norm < 0:
            raise InputBoundaryError("feature squared norms cannot be negative")
        if not 0 <= self.score_q32 <= _Q32_ONE:
            raise InputBoundaryError("score_q32 must be in the inclusive Q32 range")
        if self.dot_product * self.dot_product > (
            self.query_squared_norm * self.candidate_squared_norm
        ):
            raise InputBoundaryError("feature similarity violates the norm bound")
        expected_score = _score_q32(
            self.dot_product,
            self.query_squared_norm,
            self.candidate_squared_norm,
        )
        if self.score_q32 != expected_score:
            raise InputBoundaryError("score_q32 does not match the exact statistics")


def active_normalizer_id() -> str:
    """Return the search-view algorithm ID for the active Unicode database."""

    return f"{_NORMALIZER_ID_PREFIX}{unicodedata.unidata_version}"


def active_feature_spec_id() -> str:
    """Return the feature algorithm ID for the active Unicode database."""

    return f"{_FEATURE_SPEC_ID_PREFIX}{unicodedata.unidata_version}"


def search_view_utf8(text: str, *, normalizer_id: str) -> bytes:
    """Build the bounded, versioned NFC/ASCII-folded retrieval view."""

    _require_active_id(
        normalizer_id,
        expected=active_normalizer_id(),
        field_name="normalizer_id",
    )
    if type(text) is not str:
        raise InputBoundaryError("retrieval text must be a string")

    try:
        raw_utf8 = text.encode("utf-8")
    except UnicodeEncodeError as exc:
        raise InputBoundaryError(
            "retrieval text contains a surrogate code point"
        ) from exc
    if len(raw_utf8) > MAX_RETRIEVAL_TEXT_BYTES:
        raise InputBoundaryError("raw retrieval text exceeds 4096 UTF-8 bytes")

    # Assignment is checked before NFC so a runtime never guesses how a code
    # point absent from its active Unicode database should normalize.
    for character in text:
        if unicodedata.category(character) == "Cn":
            raise InputBoundaryError(
                "retrieval text contains a code point unassigned in the active Unicode database"
            )

    normalized = unicodedata.normalize("NFC", text)
    line_normalized = normalized.replace("\r\n", "\n").replace("\r", "\n")
    search_text = _fold_ascii_and_whitespace(line_normalized)
    search_utf8 = search_text.encode("utf-8")
    if len(search_utf8) > MAX_RETRIEVAL_TEXT_BYTES:
        raise InputBoundaryError("normalized retrieval text exceeds 4096 UTF-8 bytes")
    return search_utf8


def encode_retrieval_text(
    text: str,
    *,
    feature_spec_id: str,
) -> RetrievalFeatureVectorV1:
    """Encode retrieval text into the exact 1,024-bin portable representation."""

    _require_active_id(
        feature_spec_id,
        expected=active_feature_spec_id(),
        field_name="feature_spec_id",
    )
    search_utf8 = search_view_utf8(text, normalizer_id=active_normalizer_id())
    bin_totals = [0] * FEATURE_DIMENSIONS
    for bin_index, sign in _iter_signed_byte_grams(search_utf8):
        bin_totals[bin_index] += sign
    return RetrievalFeatureVectorV1(
        feature_spec_id=feature_spec_id,
        bins_i16be=_bins_to_saturated_i16be(bin_totals),
    )


def feature_vector_digest(vector: RetrievalFeatureVectorV1) -> str:
    """Return the domain-separated digest of a canonical feature vector."""

    if type(vector) is not RetrievalFeatureVectorV1:
        raise InputBoundaryError("vector must be RetrievalFeatureVectorV1")
    payload = cast(
        JsonValue,
        {
            "bins_i16be_hex": vector.bins_i16be.hex(),
            "feature_spec_id": vector.feature_spec_id,
        },
    )
    return _domain_digest(_FEATURE_VECTOR_DOMAIN, canonical_json_bytes(payload))


def measure_feature_similarity(
    query: RetrievalFeatureVectorV1,
    candidate: RetrievalFeatureVectorV1,
) -> FeatureSimilarityV1:
    """Measure platform-stable cosine sufficient statistics and Q32 score."""

    if type(query) is not RetrievalFeatureVectorV1:
        raise InputBoundaryError("query must be RetrievalFeatureVectorV1")
    if type(candidate) is not RetrievalFeatureVectorV1:
        raise InputBoundaryError("candidate must be RetrievalFeatureVectorV1")
    if query.feature_spec_id != candidate.feature_spec_id:
        raise InputBoundaryError("feature vectors use incompatible specifications")

    query_bins = struct.unpack(f">{FEATURE_DIMENSIONS}h", query.bins_i16be)
    candidate_bins = struct.unpack(f">{FEATURE_DIMENSIONS}h", candidate.bins_i16be)
    dot_product = sum(
        left * right for left, right in zip(query_bins, candidate_bins, strict=True)
    )
    query_squared_norm = sum(value * value for value in query_bins)
    candidate_squared_norm = sum(value * value for value in candidate_bins)
    return FeatureSimilarityV1(
        dot_product=dot_product,
        query_squared_norm=query_squared_norm,
        candidate_squared_norm=candidate_squared_norm,
        score_q32=_score_q32(
            dot_product,
            query_squared_norm,
            candidate_squared_norm,
        ),
    )


def compare_feature_similarity_exact(
    left: FeatureSimilarityV1,
    right: FeatureSimilarityV1,
) -> int:
    """Compare cosine magnitudes exactly; return 1, 0, or -1 for left vs right."""

    if type(left) is not FeatureSimilarityV1:
        raise InputBoundaryError("left must be FeatureSimilarityV1")
    if type(right) is not FeatureSimilarityV1:
        raise InputBoundaryError("right must be FeatureSimilarityV1")

    left_denominator = left.query_squared_norm * left.candidate_squared_norm
    right_denominator = right.query_squared_norm * right.candidate_squared_norm
    left_positive = left.dot_product > 0 and left_denominator > 0
    right_positive = right.dot_product > 0 and right_denominator > 0
    if not left_positive or not right_positive:
        if left_positive:
            return 1
        if right_positive:
            return -1
        return 0

    left_cross = left.dot_product * left.dot_product * right_denominator
    right_cross = right.dot_product * right.dot_product * left_denominator
    return (left_cross > right_cross) - (left_cross < right_cross)


def _fold_ascii_and_whitespace(text: str) -> str:
    folded: list[str] = []
    in_whitespace = False
    for character in text:
        if character in _WHITESPACE:
            if not in_whitespace:
                folded.append(" ")
            in_whitespace = True
            continue

        codepoint = ord(character)
        folded.append(chr(codepoint + 32) if 65 <= codepoint <= 90 else character)
        in_whitespace = False
    return "".join(folded)


def _iter_signed_byte_grams(search_utf8: bytes) -> Iterator[tuple[int, int]]:
    """Yield ``(bin, sign)`` pairs in the protocol's exact gram order."""

    if type(search_utf8) is not bytes:
        raise InputBoundaryError("search view must be bytes")
    if len(search_utf8) > MAX_RETRIEVAL_TEXT_BYTES:
        raise InputBoundaryError("search view exceeds 4096 UTF-8 bytes")

    frame = _FEATURE_FRAME_PREFIX + search_utf8 + _FEATURE_FRAME_SUFFIX
    for start in range(len(frame)):
        for gram_length in _FEATURE_GRAM_LENGTHS:
            end = start + gram_length
            if end > len(frame):
                continue
            gram = frame[start:end]
            message = _FEATURE_GRAM_DOMAIN + struct.pack(">H", gram_length) + gram
            digest = hashlib.blake2s(
                message,
                digest_size=8,
                person=_BLAKE2S_PERSON,
            ).digest()
            bin_index = int.from_bytes(digest[:4], "big") % FEATURE_DIMENSIONS
            sign = 1 if (digest[4] & 1) == 0 else -1
            yield bin_index, sign


def _saturate_feature_bin(total: int) -> int:
    if type(total) is not int:
        raise InputBoundaryError("feature bin total must be an integer")
    return max(_MIN_FEATURE_BIN, min(_MAX_FEATURE_BIN, total))


def _score_q32(
    dot_product: int,
    query_squared_norm: int,
    candidate_squared_norm: int,
) -> int:
    denominator = query_squared_norm * candidate_squared_norm
    if dot_product <= 0 or denominator <= 0:
        return 0
    scaled_dot = dot_product * _Q32_ONE
    return min(_Q32_ONE, math.isqrt((scaled_dot * scaled_dot) // denominator))


def _bins_to_saturated_i16be(counts: Iterable[int]) -> bytes:
    if not isinstance(counts, Iterable):
        raise InputBoundaryError("feature bin counts must be iterable")

    saturated: list[int] = []
    for index, total in enumerate(counts):
        if index >= FEATURE_DIMENSIONS:
            raise InputBoundaryError("feature vector must contain exactly 1024 bins")
        saturated.append(_saturate_feature_bin(total))
    if len(saturated) != FEATURE_DIMENSIONS:
        raise InputBoundaryError("feature vector must contain exactly 1024 bins")
    return struct.pack(f">{FEATURE_DIMENSIONS}h", *saturated)


def _require_active_id(value: str, *, expected: str, field_name: str) -> None:
    if type(value) is not str or value != expected:
        raise InputBoundaryError(f"{field_name} does not match the active runtime")


def _domain_digest(domain: bytes, payload: bytes) -> str:
    framed = (
        struct.pack(">Q", len(domain))
        + domain
        + struct.pack(">Q", len(payload))
        + payload
    )
    return hashlib.sha256(framed).hexdigest()


__all__ = [
    "FeatureSimilarityV1",
    "RetrievalFeatureVectorV1",
    "active_feature_spec_id",
    "active_normalizer_id",
    "compare_feature_similarity_exact",
    "encode_retrieval_text",
    "feature_vector_digest",
    "measure_feature_similarity",
    "search_view_utf8",
]
