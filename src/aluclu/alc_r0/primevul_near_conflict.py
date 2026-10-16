"""Verify a development-only PrimeVul near-clone label-conflict witness.

A single confirmed opposite-label pair violates the frozen clone-root rule.
This is a negative source-qualification witness, not a full-corpus LSH audit,
training permit, held-out evaluation, or neural-capability result.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import struct
import sys
from pathlib import Path
from typing import Any

import numpy as np

from .canonical import canonical_json_bytes, sha256_bytes
from .devign_clone import (
    _MULTIPLIERS,
    _OFFSETS,
    EXACT_JACCARD_THRESHOLD,
    LSH_BANDS,
    LSH_CANDIDATE_THRESHOLD,
    LSH_ROWS,
    MINHASH_PERMUTATIONS,
    MINHASH_SEED,
    _band_keys,
    minhash_signature,
)
from .devign_preprocess import (
    DEVIGN_TOKEN_REGEX,
    code_five_shingles,
    normalize_devign_code,
    tokenize_devign_code,
)
from .primevul_source import (
    PRIMEVUL_ORIGINAL_DEVELOPMENT,
    PrimeVulDevelopmentExpectation,
    verify_primevul_development,
)


class PrimeVulNearConflictError(ValueError):
    """A proposed pair is not a valid conflicting near-clone witness."""


def _read_witnesses(
    source_dir: Path,
    *,
    left_id: int,
    right_id: int,
    expectation: PrimeVulDevelopmentExpectation,
) -> dict[int, tuple[str, str, int]]:
    witnesses: dict[int, tuple[str, str, int]] = {}
    for split, filename, expected_sha256 in (
        ("train", "primevul_train.jsonl", expectation.train_sha256),
        ("validation", "primevul_valid.jsonl", expectation.validation_sha256),
    ):
        digest = hashlib.sha256()
        with (source_dir / filename).open("rb") as stream:
            for raw in stream:
                digest.update(raw)
                row = json.loads(raw)
                source_id = row["idx"]
                if source_id in (left_id, right_id):
                    if source_id in witnesses:
                        raise PrimeVulNearConflictError("duplicate witness source ID")
                    witnesses[source_id] = (split, row["func"], row["target"])
        if digest.hexdigest() != expected_sha256:
            raise PrimeVulNearConflictError(
                "source SHA-256 changed during witness read"
            )
    if set(witnesses) != {left_id, right_id}:
        raise PrimeVulNearConflictError("missing witness source ID")
    return witnesses


def build_primevul_near_conflict_receipt(
    source_dir: Path,
    *,
    left_id: int,
    right_id: int,
    expectation: PrimeVulDevelopmentExpectation = PRIMEVUL_ORIGINAL_DEVELOPMENT,
) -> dict[str, Any]:
    """Bind one LSH-confirmed, opposite-label pair to verified development bytes."""

    if (
        type(left_id) is not int
        or type(right_id) is not int
        or left_id < 0
        or left_id >= right_id
    ):
        raise PrimeVulNearConflictError(
            "ordered distinct nonnegative source IDs required"
        )
    source_receipt = verify_primevul_development(source_dir, expectation=expectation)
    if source_receipt["status"] != "candidate-non-authorizing":
        raise PrimeVulNearConflictError("exact preflight must be clear")
    rows = _read_witnesses(
        source_dir, left_id=left_id, right_id=right_id, expectation=expectation
    )
    left_split, left_code, left_label = rows[left_id]
    right_split, right_code, right_label = rows[right_id]
    if left_label == right_label:
        raise PrimeVulNearConflictError("opposite labels required")
    left_normalized = normalize_devign_code(left_code.encode("utf-8"))
    right_normalized = normalize_devign_code(right_code.encode("utf-8"))
    if left_normalized == right_normalized:
        raise PrimeVulNearConflictError("witness is exact, not near, clone")
    left_shingles = code_five_shingles(tokenize_devign_code(left_normalized))
    right_shingles = code_five_shingles(tokenize_devign_code(right_normalized))
    intersection = len(left_shingles & right_shingles)
    union = len(left_shingles | right_shingles)
    if not union or 10 * intersection < 9 * union:
        raise PrimeVulNearConflictError("exact Jaccard is below 0.90")
    left_bands = set(_band_keys(minhash_signature(left_shingles)))
    right_bands = set(_band_keys(minhash_signature(right_shingles)))
    common_bands = len(left_bands & right_bands)
    if not common_bands:
        raise PrimeVulNearConflictError("pair is not an LSH candidate")
    coefficients = b"".join(
        struct.pack("!II", int(multiplier), int(offset))
        for multiplier, offset in zip(_MULTIPLIERS, _OFFSETS, strict=True)
    )
    return {
        "receipt_version": 1,
        "status": "failed-near-clone-label-conflict",
        "candidate_qualified": False,
        "training_authority": False,
        "held_out_data_present": False,
        "full_development_lsh_executed": False,
        "source_receipt_sha256": sha256_bytes(canonical_json_bytes(source_receipt)),
        "train_sha256": expectation.train_sha256,
        "validation_sha256": expectation.validation_sha256,
        "exact_conflict_groups": source_receipt["exact_conflict_groups"],
        "normalization_policy": source_receipt["normalization_policy"],
        "token_regex_sha256": sha256_bytes(DEVIGN_TOKEN_REGEX.encode("utf-8")),
        "five_shingle_width": 5,
        "minhash_seed": MINHASH_SEED,
        "minhash_permutations": MINHASH_PERMUTATIONS,
        "minhash_coefficient_sha256": sha256_bytes(coefficients),
        "minhash_shingle_hash": "sha256-first32-big-endian",
        "minhash_affine_rule": "odd-a-h-plus-b-mod-2**32",
        "numpy_version": np.__version__,
        "lsh_candidate_threshold": LSH_CANDIDATE_THRESHOLD,
        "lsh_bands": LSH_BANDS,
        "lsh_rows_per_band": LSH_ROWS,
        "near_clone_exact_jaccard_threshold": EXACT_JACCARD_THRESHOLD,
        "witness": {
            "left": {
                "source_id": f"primevul:{left_id}",
                "split": left_split,
                "label": left_label,
                "normalized_sha256": sha256_bytes(left_normalized.encode("utf-8")),
                "five_shingles": len(left_shingles),
            },
            "right": {
                "source_id": f"primevul:{right_id}",
                "split": right_split,
                "label": right_label,
                "normalized_sha256": sha256_bytes(right_normalized.encode("utf-8")),
                "five_shingles": len(right_shingles),
            },
            "jaccard_intersection": intersection,
            "jaccard_union": union,
            "common_lsh_bands": common_bands,
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("development_data_dir", type=Path)
    parser.add_argument("--left-id", type=int, required=True)
    parser.add_argument("--right-id", type=int, required=True)
    args = parser.parse_args()
    receipt = build_primevul_near_conflict_receipt(
        args.development_data_dir, left_id=args.left_id, right_id=args.right_id
    )
    sys.stdout.buffer.write(canonical_json_bytes(receipt) + b"\n")


if __name__ == "__main__":
    main()
