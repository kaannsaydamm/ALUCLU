"""Non-authorizing Devign normalized-code and tokenization roots."""

from __future__ import annotations

import argparse
import hashlib
import sys
from collections.abc import Sequence
from pathlib import Path
from typing import Any

from .canonical import canonical_json_bytes, sha256_bytes
from .devign_preprocess import (
    DEVIGN_TOKEN_REGEX,
    code_five_shingles,
    normalize_devign_code,
    tokenize_devign_code,
)
from .devign_source import (
    DevignSourceRecord,
    VerifiedDevignDevelopment,
    load_verified_devign_development,
)


class DevignPreprocessReceiptError(ValueError):
    """The normalized development-source receipt cannot be produced safely."""


def _ordered_root(rows: Sequence[DevignSourceRecord]) -> dict[str, int | str]:
    if not rows:
        raise DevignPreprocessReceiptError("train and validation must be nonempty")
    root = hashlib.sha256()
    changed = 0
    empty_shingles = 0
    min_tokens: int | None = None
    max_tokens = 0
    for row in rows:
        normalized = normalize_devign_code(
            row.function.encode("utf-8", errors="strict")
        )
        tokens = tokenize_devign_code(normalized)
        shingle_count = len(code_five_shingles(tokens))
        token_count = len(tokens)
        changed += normalized != row.function
        empty_shingles += shingle_count == 0
        min_tokens = token_count if min_tokens is None else min(min_tokens, token_count)
        max_tokens = max(max_tokens, token_count)
        root.update(
            canonical_json_bytes(
                {
                    "source_id": row.source_id,
                    "target": row.target,
                    "normalized_sha256": sha256_bytes(normalized.encode("utf-8")),
                    "token_count": token_count,
                    "five_shingle_count": shingle_count,
                }
            )
            + b"\n"
        )
    assert min_tokens is not None
    return {
        "rows": len(rows),
        "normalization_changed_rows": changed,
        "empty_shingle_rows": empty_shingles,
        "min_tokens": min_tokens,
        "max_tokens": max_tokens,
        "ordered_normalized_sha256": root.hexdigest(),
    }


def build_devign_preprocess_candidate_receipt(
    source: VerifiedDevignDevelopment,
) -> dict[str, Any]:
    """Bind ordered normalized train/validation rows without exposing code."""

    if not isinstance(source, VerifiedDevignDevelopment):
        raise DevignPreprocessReceiptError("verified development source required")
    if source.receipt.get("training_authority") is not False:
        raise DevignPreprocessReceiptError("source receipt must not authorize training")
    train = _ordered_root(source.train)
    validation = _ordered_root(source.validation)
    return {
        "receipt_version": 1,
        "status": "candidate-non-authorizing",
        "training_authority": False,
        "held_out_data_present": False,
        "source_receipt_sha256": sha256_bytes(canonical_json_bytes(source.receipt)),
        "normalization_policy": "strict-utf8-nfc-lf-trailing-ascii-outer-blank",
        "token_regex_sha256": sha256_bytes(DEVIGN_TOKEN_REGEX.encode("utf-8")),
        "five_shingle_width": 5,
        "ordered_train_normalized_sha256": train["ordered_normalized_sha256"],
        "ordered_validation_normalized_sha256": validation["ordered_normalized_sha256"],
        **{
            f"train_{key}": value
            for key, value in train.items()
            if key != "ordered_normalized_sha256"
        },
        **{
            f"validation_{key}": value
            for key, value in validation.items()
            if key != "ordered_normalized_sha256"
        },
    }


def main() -> None:
    """Print only canonical development preprocessing metadata."""

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("development_data_dir", type=Path)
    args = parser.parse_args()
    source = load_verified_devign_development(args.development_data_dir)
    receipt = build_devign_preprocess_candidate_receipt(source)
    sys.stdout.buffer.write(canonical_json_bytes(receipt) + b"\n")


if __name__ == "__main__":
    main()
