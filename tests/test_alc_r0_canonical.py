from __future__ import annotations

import pytest

from aluclu.alc_r0.canonical import (
    CanonicalEvidenceError,
    canonical_json_bytes,
    canonical_jsonl_bytes,
    normalize_evidence_path,
    parse_canonical_json,
    parse_canonical_jsonl,
    sha256_bytes,
    validate_evidence_paths,
)


def test_canonical_json_matches_rfc8785_number_and_key_rules() -> None:
    value = {"z": -0.0, "a": 1.0, "\u20ac": "currency", "\r": "control"}

    encoded = canonical_json_bytes(value)

    assert encoded == b'{"\\r":"control","a":1,"z":0,"\xe2\x82\xac":"currency"}'
    assert parse_canonical_json(encoded) == {"\r": "control", "a": 1, "z": 0, "\u20ac": "currency"}


@pytest.mark.parametrize(
    "data",
    [
        b"\xef\xbb\xbf{}",
        b'{"a":1,"a":2}',
        b'{"x":NaN}',
        b'{"x":Infinity}',
        b'{"a":1.0}',
        b'{ "a":1}',
        b"\xff",
    ],
)
def test_parse_canonical_json_rejects_invalid_or_noncanonical_bytes(data: bytes) -> None:
    with pytest.raises(CanonicalEvidenceError):
        parse_canonical_json(data)


@pytest.mark.parametrize("value", [float("nan"), float("inf"), 2**60])
def test_canonical_json_rejects_values_outside_jcs_domain(value: float | int) -> None:
    with pytest.raises(CanonicalEvidenceError):
        canonical_json_bytes({"value": value})


def test_canonical_jsonl_round_trip_requires_objects_and_final_lf() -> None:
    encoded = canonical_jsonl_bytes([{"b": 2, "a": 1}, {"ok": True}])

    assert encoded == b'{"a":1,"b":2}\n{"ok":true}\n'
    assert parse_canonical_jsonl(encoded) == ({"a": 1, "b": 2}, {"ok": True})


@pytest.mark.parametrize(
    "data",
    [
        b"",
        b"{}",
        b"{}\r\n",
        b"{}\n\n",
        b"[]\n",
        b"{}\ntrailing",
        b'{"b":2,"a":1}\n',
    ],
)
def test_parse_canonical_jsonl_rejects_boundary_violations(data: bytes) -> None:
    with pytest.raises(CanonicalEvidenceError):
        parse_canonical_jsonl(data)


def test_sha256_bytes_hashes_exact_payload() -> None:
    assert sha256_bytes(b"abc") == "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad"


@pytest.mark.parametrize(
    "path",
    [
        "",
        "/absolute.json",
        "C:/drive.json",
        "a\\b.json",
        "a//b.json",
        "./a.json",
        "a/../b.json",
        "a/./b.json",
        "a/\x00b.json",
        "a/file.json:stream",
        "a/NUL.json",
        "a/trailing. ",
        "a/control\x1fb.json",
    ],
)
def test_normalize_evidence_path_rejects_unsafe_or_noncanonical_paths(path: str) -> None:
    with pytest.raises(CanonicalEvidenceError):
        normalize_evidence_path(path)


def test_evidence_paths_reject_exact_and_windows_casefold_collisions() -> None:
    assert validate_evidence_paths(["results/a.json", "results/b.json"]) == (
        "results/a.json",
        "results/b.json",
    )
    with pytest.raises(CanonicalEvidenceError, match="duplicate"):
        validate_evidence_paths(["results/a.json", "results/a.json"])
    with pytest.raises(CanonicalEvidenceError, match="casefold"):
        validate_evidence_paths(["results/A.json", "results/a.json"])
