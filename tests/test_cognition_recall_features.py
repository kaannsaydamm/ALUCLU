from __future__ import annotations

import hashlib
import json
import struct
import unicodedata
from collections.abc import Iterable
from dataclasses import FrozenInstanceError, fields
from pathlib import Path
from typing import Any, cast

import pytest

from aluclu.cognition import InputBoundaryError
from aluclu.cognition.recall_features import (
    FeatureSimilarityV1,
    RetrievalFeatureVectorV1,
    _bins_to_saturated_i16be,
    _iter_signed_byte_grams,
    active_feature_spec_id,
    active_normalizer_id,
    compare_feature_similarity_exact,
    encode_retrieval_text,
    feature_vector_digest,
    measure_feature_similarity,
    search_view_utf8,
)

SUPPORTED_UNIDATA_VERSIONS = ("13.0.0", "14.0.0", "15.0.0", "15.1.0")
FEATURE_DOMAIN = b"aluclu.task2.feature-vector.v1"
BLAKE2S_PERSON = b"al2feat1"
PROTOCOL_PATH = (
    Path(__file__).resolve().parents[1]
    / "src"
    / "aluclu"
    / "protocols"
    / "task2_determinism_v1.json"
)
RECOLLECTION_PROTOCOL_PATH = PROTOCOL_PATH.with_name("task2_recollection_v1.json")


def _canonical_json_bytes(value: object) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


def _domain_digest(domain: bytes, payload: bytes) -> str:
    framed = (
        struct.pack(">Q", len(domain))
        + domain
        + struct.pack(">Q", len(payload))
        + payload
    )
    return hashlib.sha256(framed).hexdigest()


def _independent_search_view(text: str) -> bytes:
    raw_utf8 = text.encode("utf-8")
    if len(raw_utf8) > 4096:
        raise InputBoundaryError("raw retrieval text is too large")
    for character in text:
        codepoint = ord(character)
        if 0xD800 <= codepoint <= 0xDFFF:
            raise InputBoundaryError("surrogate code point is invalid")
        if unicodedata.category(character) == "Cn":
            raise InputBoundaryError("unassigned code point is invalid")

    normalized = unicodedata.normalize("NFC", text)
    normalized = normalized.replace("\r\n", "\n").replace("\r", "\n")
    folded: list[str] = []
    in_whitespace = False
    for character in normalized:
        codepoint = ord(character)
        if character in "\t\n\v\f ":
            if not in_whitespace:
                folded.append(" ")
            in_whitespace = True
            continue
        folded.append(chr(codepoint + 32) if 65 <= codepoint <= 90 else character)
        in_whitespace = False

    search_utf8 = "".join(folded).encode("utf-8")
    if len(search_utf8) > 4096:
        raise InputBoundaryError("normalized retrieval text is too large")
    return search_utf8


def _independent_grams(search_utf8: bytes) -> list[dict[str, object]]:
    frame = b"\xff\x01" + search_utf8 + b"\xff\x02"
    grams: list[dict[str, object]] = []
    for start in range(len(frame)):
        for length in (3, 4, 5):
            if start + length > len(frame):
                continue
            gram = frame[start : start + length]
            message = b"\x01" + struct.pack(">H", len(gram)) + gram
            digest = hashlib.blake2s(
                message,
                digest_size=8,
                person=BLAKE2S_PERSON,
            ).digest()
            grams.append(
                {
                    "start": start,
                    "length": length,
                    "gram_hex": gram.hex(),
                    "message_hex": message.hex(),
                    "blake2s_hex": digest.hex(),
                    "bin": int.from_bytes(digest[:4], "big") % 1024,
                    "sign": 1 if (digest[4] & 1) == 0 else -1,
                }
            )
    return grams


def _independent_bins(search_utf8: bytes) -> list[int]:
    bins = [0] * 1024
    for gram in _independent_grams(search_utf8):
        bins[cast(int, gram["bin"])] += cast(int, gram["sign"])
    return [max(-32767, min(32767, value)) for value in bins]


def _bins_to_i16be(bins: Iterable[int]) -> bytes:
    return b"".join(struct.pack(">h", value) for value in bins)


def _independent_vector_digest(search_utf8: bytes, unidata_version: str) -> str:
    payload = {
        "bins_i16be_hex": _bins_to_i16be(_independent_bins(search_utf8)).hex(),
        "feature_spec_id": (
            f"aluclu.feature.signed-byte-ngram-1024-int16.v1+ucd-{unidata_version}"
        ),
    }
    return _domain_digest(FEATURE_DOMAIN, _canonical_json_bytes(payload))


def _load_manifest() -> dict[str, Any]:
    wire = PROTOCOL_PATH.read_bytes()
    value = json.loads(wire)
    assert type(value) is dict
    assert wire == _canonical_json_bytes(value), (
        "protocol fixture must be canonical UTF-8 JSON"
    )
    return cast(dict[str, Any], value)


def test_protocol_manifest_has_exact_task2_1_shape() -> None:
    manifest = _load_manifest()

    assert tuple(manifest) == (
        "algorithm",
        "assignment_vectors_by_unidata_version",
        "domain_vectors",
        "schema",
        "search_vectors",
        "supported_unidata_versions",
    )
    assert manifest["schema"] == "aluclu.task2-determinism.v1"
    assert tuple(manifest["supported_unidata_versions"]) == SUPPORTED_UNIDATA_VERSIONS
    assert tuple(manifest["assignment_vectors_by_unidata_version"]) == (
        SUPPORTED_UNIDATA_VERSIONS
    )
    assert manifest["algorithm"] == {
        "identity": "aluclu.identity.sha256-u64be-domain.v1",
        "search_view": "aluclu.search-view.nfc-ascii-ws.v1",
        "feature_vector": "aluclu.feature.signed-byte-ngram-1024-int16.v1",
    }


def test_domain_vectors_use_exact_framed_sha256_domains() -> None:
    registered_domains = {
        "aluclu.task2.observation-request.v1",
        "aluclu.task2.observation-content.v1",
        "aluclu.task2.episode-id.v1",
        "aluclu.task2.sensorium-core-state.v1",
        "aluclu.task2.boundary-profile.v1",
        "aluclu.task2.feature-vector.v1",
    }
    for vector in _load_manifest()["domain_vectors"]:
        assert tuple(vector) == (
            "canonical_payload_utf8_hex",
            "case_id",
            "domain_ascii",
            "expected_sha256_hex",
        )
        assert vector["domain_ascii"] in registered_domains
        assert vector["expected_sha256_hex"] == _domain_digest(
            vector["domain_ascii"].encode("ascii"),
            bytes.fromhex(vector["canonical_payload_utf8_hex"]),
        )


def test_literal_search_vectors_cover_required_script_and_length_cases() -> None:
    assert {
        "empty",
        "ascii_case_ws",
        "turkish",
        "arabic",
        "cjk",
        "emoji",
        "decomposed_e_acute",
        "composed_e_acute",
        "newline_ws",
        "leading_trailing_ws",
        "maximum_ascii",
    } <= {case["case_id"] for case in _load_manifest()["search_vectors"]}


def test_active_compatibility_ids_bind_the_runtime_unidata_version() -> None:
    assert active_normalizer_id() == (
        f"aluclu.search-view.nfc-ascii-ws.v1+ucd-{unicodedata.unidata_version}"
    )
    assert active_feature_spec_id() == (
        "aluclu.feature.signed-byte-ngram-1024-int16.v1"
        f"+ucd-{unicodedata.unidata_version}"
    )


@pytest.mark.parametrize("case", _load_manifest()["search_vectors"])
def test_search_view_matches_literal_protocol_vectors(case: dict[str, Any]) -> None:
    assert tuple(case) == (
        "case_id",
        "feature_vector_digest_by_unidata_version",
        "gram_count",
        "gram_fixtures",
        "input",
        "nonzero_bins",
        "raw_utf8_hex",
        "search_utf8_hex",
    )

    assert case["input"].encode("utf-8").hex() == case["raw_utf8_hex"]
    assert search_view_utf8(case["input"], normalizer_id=active_normalizer_id()) == (
        bytes.fromhex(case["search_utf8_hex"])
    )
    assert _independent_search_view(case["input"]).hex() == case["search_utf8_hex"]


@pytest.mark.parametrize("case", _load_manifest()["search_vectors"])
def test_signed_gram_fixtures_match_independent_blake2s_frames(
    case: dict[str, Any],
) -> None:
    grams = _independent_grams(bytes.fromhex(case["search_utf8_hex"]))

    assert len(grams) == case["gram_count"]
    for fixture in case["gram_fixtures"]:
        matches = [
            gram
            for gram in grams
            if gram["start"] == fixture["start"] and gram["length"] == fixture["length"]
        ]
        assert matches == [fixture]


@pytest.mark.parametrize("case", _load_manifest()["search_vectors"])
def test_feature_vectors_match_bins_and_ucd_scoped_digests(
    case: dict[str, Any],
) -> None:
    search_utf8 = bytes.fromhex(case["search_utf8_hex"])
    vector = encode_retrieval_text(
        case["input"], feature_spec_id=active_feature_spec_id()
    )

    assert isinstance(vector, RetrievalFeatureVectorV1)
    assert tuple(field.name for field in fields(vector)) == (
        "feature_spec_id",
        "bins_i16be",
    )
    assert not hasattr(vector, "__dict__")
    with pytest.raises((FrozenInstanceError, AttributeError)):
        vector.feature_spec_id = vector.feature_spec_id  # type: ignore[misc]

    expected_bins = _independent_bins(search_utf8)
    assert vector.bins_i16be == _bins_to_i16be(expected_bins)
    assert case["nonzero_bins"] == [
        [index, value] for index, value in enumerate(expected_bins) if value
    ]
    digest_by_ucd = case["feature_vector_digest_by_unidata_version"]
    assert tuple(digest_by_ucd) == SUPPORTED_UNIDATA_VERSIONS
    assert feature_vector_digest(vector) == digest_by_ucd[unicodedata.unidata_version]
    for version in SUPPORTED_UNIDATA_VERSIONS:
        assert digest_by_ucd[version] == _independent_vector_digest(
            search_utf8,
            version,
        )


def test_feature_digest_changes_when_only_the_ucd_suffix_changes() -> None:
    vector = encode_retrieval_text(
        "same bytes", feature_spec_id=active_feature_spec_id()
    )
    search_utf8 = _independent_search_view("same bytes")
    digests = {
        version: _independent_vector_digest(search_utf8, version)
        for version in SUPPORTED_UNIDATA_VERSIONS
    }

    assert len(set(digests.values())) == len(SUPPORTED_UNIDATA_VERSIONS)
    assert feature_vector_digest(vector) == digests[unicodedata.unidata_version]


def test_assignment_vectors_use_singular_feature_digest_per_ucd_case() -> None:
    manifest = _load_manifest()
    for version, cases in manifest["assignment_vectors_by_unidata_version"].items():
        for case in cases:
            assert tuple(case) == (
                "case_id",
                "feature_vector_digest",
                "input",
                "outcome",
                "search_utf8_hex",
            )
            assert "feature_vector_digest_by_unidata_version" not in case
            if case["outcome"] == "reject_unassigned":
                assert case["search_utf8_hex"] is None
                assert case["feature_vector_digest"] is None
                if version == unicodedata.unidata_version:
                    with pytest.raises(InputBoundaryError):
                        encode_retrieval_text(
                            case["input"], feature_spec_id=active_feature_spec_id()
                        )
                continue
            assert case["outcome"] == "accept"
            search_utf8 = bytes.fromhex(case["search_utf8_hex"])
            if version == unicodedata.unidata_version:
                assert _independent_search_view(case["input"]) == search_utf8
                assert (
                    search_view_utf8(
                        case["input"], normalizer_id=active_normalizer_id()
                    )
                    == search_utf8
                )
                actual = encode_retrieval_text(
                    case["input"], feature_spec_id=active_feature_spec_id()
                )
                assert feature_vector_digest(actual) == case["feature_vector_digest"]
            assert case["feature_vector_digest"] == _independent_vector_digest(
                search_utf8,
                version,
            )


def test_raw_and_normalized_utf8_caps_are_independent() -> None:
    accepted = "\u0958" * 682
    rejected_by_normalized = "\u0958" * 683
    rejected_by_raw = " " * 4097

    assert len(accepted.encode("utf-8")) == 2046
    assert len(unicodedata.normalize("NFC", accepted).encode("utf-8")) == 4092
    assert search_view_utf8(accepted, normalizer_id=active_normalizer_id()) == (
        unicodedata.normalize("NFC", accepted).encode("utf-8")
    )

    assert len(rejected_by_normalized.encode("utf-8")) == 2049
    assert len(
        unicodedata.normalize("NFC", rejected_by_normalized).encode("utf-8")
    ) == (4098)
    with pytest.raises(InputBoundaryError):
        search_view_utf8(rejected_by_normalized, normalizer_id=active_normalizer_id())

    assert len(rejected_by_raw.encode("utf-8")) == 4097
    assert len(_independent_search_view(" " * 4096)) == 1
    with pytest.raises(InputBoundaryError):
        search_view_utf8(rejected_by_raw, normalizer_id=active_normalizer_id())


def test_public_maximum_4096_ascii_input_emits_12291_grams() -> None:
    search_utf8 = search_view_utf8("A" * 4096, normalizer_id=active_normalizer_id())

    assert search_utf8 == b"a" * 4096
    assert len(list(_iter_signed_byte_grams(search_utf8))) == 12291
    assert len(_independent_grams(search_utf8)) == 12291


def test_private_saturation_helper_clips_each_bin_to_int16_storage() -> None:
    counts = [0] * 1024
    counts[7] = 40000
    counts[8] = -40000
    counts[9] = 32767
    counts[10] = -32767

    encoded = _bins_to_saturated_i16be(counts)

    assert len(encoded) == 2048
    assert encoded[14:22].hex() == "7fff80017fff8001"


def _literal_vector(*bins: int) -> RetrievalFeatureVectorV1:
    padded = (*bins, *((0,) * (1024 - len(bins))))
    return RetrievalFeatureVectorV1(
        feature_spec_id=active_feature_spec_id(),
        bins_i16be=_bins_to_i16be(padded),
    )


def _sparse_literal_vector(entries: list[list[int]]) -> RetrievalFeatureVectorV1:
    bins = [0] * 1024
    for index, value in entries:
        bins[index] = value
    return _literal_vector(*bins)


def test_recollection_protocol_fixture_is_canonical_and_exactly_shaped() -> None:
    wire = RECOLLECTION_PROTOCOL_PATH.read_bytes()
    manifest = json.loads(wire)

    assert wire == _canonical_json_bytes(manifest)
    assert tuple(manifest) == (
        "algorithm",
        "ranking_vectors",
        "schema",
        "similarity_vectors",
    )
    assert manifest["schema"] == "aluclu.task2-recollection-determinism.v1"
    assert manifest["algorithm"] == {
        "comparator": "positive-cosine-cross-product.v1",
        "score": "cosine-q32-floor-isqrt.v1",
    }


@pytest.mark.parametrize(
    "case",
    json.loads(RECOLLECTION_PROTOCOL_PATH.read_bytes())["similarity_vectors"],
)
def test_similarity_matches_companion_protocol_fixture(case: dict[str, Any]) -> None:
    assert tuple(case) == (
        "candidate_nonzero_bins",
        "candidate_squared_norm",
        "case_id",
        "dot_product",
        "norm_product",
        "pre_isqrt_quotient",
        "query_nonzero_bins",
        "query_squared_norm",
        "score_q32",
    )
    measured = measure_feature_similarity(
        _sparse_literal_vector(case["query_nonzero_bins"]),
        _sparse_literal_vector(case["candidate_nonzero_bins"]),
    )

    assert measured.dot_product == case["dot_product"]
    assert measured.query_squared_norm == case["query_squared_norm"]
    assert measured.candidate_squared_norm == case["candidate_squared_norm"]
    assert (
        measured.query_squared_norm * measured.candidate_squared_norm
        == case["norm_product"]
    )
    if measured.dot_product > 0 and case["norm_product"] > 0:
        scale = 1 << 32
        assert (
            ((measured.dot_product * scale) ** 2) // case["norm_product"]
            == case["pre_isqrt_quotient"]
        )
    else:
        assert case["pre_isqrt_quotient"] == 0
    assert measured.score_q32 == case["score_q32"]


def test_exact_comparator_matches_companion_protocol_fixture() -> None:
    [case] = json.loads(RECOLLECTION_PROTOCOL_PATH.read_bytes())["ranking_vectors"]
    query_bins = [case["query_default_bin"]] * 1024
    left_bins = [case["left_candidate_default_bin"]] * 1024
    right_bins = [case["right_candidate_default_bin"]] * 1024
    for index, value in case["left_candidate_overrides"]:
        left_bins[index] = value
    for index, value in case["right_candidate_overrides"]:
        right_bins[index] = value

    left = measure_feature_similarity(
        _literal_vector(*query_bins), _literal_vector(*left_bins)
    )
    right = measure_feature_similarity(
        _literal_vector(*query_bins), _literal_vector(*right_bins)
    )
    left_cross = (
        left.dot_product
        * left.dot_product
        * right.query_squared_norm
        * right.candidate_squared_norm
    )
    right_cross = (
        right.dot_product
        * right.dot_product
        * left.query_squared_norm
        * left.candidate_squared_norm
    )

    assert left.score_q32 == case["left_score_q32"]
    assert right.score_q32 == case["right_score_q32"]
    assert left_cross == case["left_cross_product"]
    assert right_cross == case["right_cross_product"]
    assert compare_feature_similarity_exact(left, right) == case["expected_comparison"]


@pytest.mark.parametrize(
    ("query", "candidate", "expected_dot", "expected_query_norm", "expected_candidate_norm", "expected_score"),
    (
        ((1,), (1,), 1, 1, 1, 1 << 32),
        ((1,), (-1,), -1, 1, 1, 0),
        ((1, 0), (0, 1), 0, 1, 1, 0),
        ((1, 1), (1, 0), 1, 2, 1, 3_037_000_499),
        ((3, 4), (6, 8), 50, 25, 100, 1 << 32),
    ),
)
def test_literal_q32_similarity_fixtures(
    query: tuple[int, ...],
    candidate: tuple[int, ...],
    expected_dot: int,
    expected_query_norm: int,
    expected_candidate_norm: int,
    expected_score: int,
) -> None:
    measured = measure_feature_similarity(
        _literal_vector(*query),
        _literal_vector(*candidate),
    )

    assert type(measured) is FeatureSimilarityV1
    assert measured.dot_product == expected_dot
    assert measured.query_squared_norm == expected_query_norm
    assert measured.candidate_squared_norm == expected_candidate_norm
    assert measured.score_q32 == expected_score
    assert 0 <= measured.score_q32 <= 1 << 32


def test_q32_similarity_is_symmetric_and_floors_before_integer_square_root() -> None:
    left = _literal_vector(1, 1)
    right = _literal_vector(1, 0)

    forward = measure_feature_similarity(left, right)
    reverse = measure_feature_similarity(right, left)

    assert forward.score_q32 == reverse.score_q32 == 3_037_000_499
    assert forward.dot_product == reverse.dot_product == 1
    assert forward.query_squared_norm == reverse.candidate_squared_norm == 2
    assert forward.candidate_squared_norm == reverse.query_squared_norm == 1


def test_exact_cross_product_breaks_a_quantized_q32_score_tie() -> None:
    query_bins = [32_767] * 1024
    closer_bins = query_bins.copy()
    farther_bins = query_bins.copy()
    closer_bins[0] -= 1
    farther_bins[0] -= 19
    query = _literal_vector(*query_bins)
    closer = measure_feature_similarity(query, _literal_vector(*closer_bins))
    farther = measure_feature_similarity(query, _literal_vector(*farther_bins))

    assert closer.score_q32 == farther.score_q32 == (1 << 32) - 1
    assert compare_feature_similarity_exact(closer, farther) == 1
    assert compare_feature_similarity_exact(farther, closer) == -1
    assert compare_feature_similarity_exact(closer, closer) == 0


def test_similarity_primitives_reject_non_vectors_and_incompatible_specs() -> None:
    vector = _literal_vector(1)
    with pytest.raises(InputBoundaryError):
        measure_feature_similarity(vector, object())  # type: ignore[arg-type]
    with pytest.raises(InputBoundaryError):
        compare_feature_similarity_exact(vector, vector)  # type: ignore[arg-type]
