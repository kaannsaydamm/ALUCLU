from __future__ import annotations

import hashlib
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
    "RetrievalFeatureVectorV1",
    "active_feature_spec_id",
    "active_normalizer_id",
    "encode_retrieval_text",
    "feature_vector_digest",
    "search_view_utf8",
]
