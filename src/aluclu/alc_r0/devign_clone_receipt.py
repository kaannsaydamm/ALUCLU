"""Canonical, non-authorizing Devign exact-label-conflict preflight receipt."""

from __future__ import annotations

import argparse
import hashlib
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
    audit_devign_exact_conflicts,
)
from .devign_preprocess import DEVIGN_TOKEN_REGEX
from .devign_source import VerifiedDevignDevelopment, load_verified_devign_development


def build_devign_exact_conflict_receipt(
    source: VerifiedDevignDevelopment,
) -> dict[str, Any]:
    """Bind the negative preflight to code policy without claiming an LSH run."""

    coefficients = b"".join(
        struct.pack("!II", int(multiplier), int(offset))
        for multiplier, offset in zip(_MULTIPLIERS, _OFFSETS, strict=True)
    )
    return {
        "receipt_version": 1,
        "audit": audit_devign_exact_conflicts(source),
        "normalization_policy": "strict-utf8-nfc-lf-trailing-ascii-outer-blank",
        "token_regex_sha256": sha256_bytes(DEVIGN_TOKEN_REGEX.encode("utf-8")),
        "five_shingle_width": 5,
        "minhash_seed": MINHASH_SEED,
        "minhash_permutations": MINHASH_PERMUTATIONS,
        "minhash_coefficient_sha256": hashlib.sha256(coefficients).hexdigest(),
        "minhash_shingle_hash": "sha256-first32-big-endian",
        "minhash_affine_rule": "odd-a-h-plus-b-mod-2**32",
        "numpy_version": np.__version__,
        "lsh_candidate_threshold": LSH_CANDIDATE_THRESHOLD,
        "lsh_bands": LSH_BANDS,
        "lsh_rows_per_band": LSH_ROWS,
        "near_clone_exact_jaccard_threshold": EXACT_JACCARD_THRESHOLD,
        "lsh_executed": False,
        "held_out_data_present": False,
        "training_authority": False,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("development_data_dir", type=Path)
    args = parser.parse_args()
    source = load_verified_devign_development(args.development_data_dir)
    sys.stdout.buffer.write(
        canonical_json_bytes(build_devign_exact_conflict_receipt(source)) + b"\n"
    )


if __name__ == "__main__":
    main()
