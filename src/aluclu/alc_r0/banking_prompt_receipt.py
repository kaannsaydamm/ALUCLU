"""Development-only cryptographic roots for the Banking77 prompt candidate."""

from __future__ import annotations

import argparse
import hashlib
import sys
from collections.abc import Sequence
from pathlib import Path
from typing import Any

from .banking_preprocess import BankingPreparedRecord
from .banking_prompt import BankingPromptTemplate, prepare_banking_prompt
from .banking_scoring import CandidateTokenizer, candidate_token_map_root
from .banking_source import (
    VerifiedBankingDevelopment,
    load_verified_banking77_development,
)
from .canonical import canonical_json_bytes, sha256_bytes


class BankingPromptReceiptError(ValueError):
    """The development prompt receipt cannot be produced safely."""


def _ordered_prompt_root(
    rows: Sequence[BankingPreparedRecord], template: BankingPromptTemplate
) -> tuple[str, int]:
    if not rows:
        raise BankingPromptReceiptError("train and dev must be nonempty")
    digest = hashlib.sha256()
    truncated = 0
    for row in rows:
        prompt = template.build(row.utterance)
        truncated += prompt.retained_query_tokens < prompt.original_query_tokens
        digest.update(
            canonical_json_bytes(
                {
                    "source_id": row.source_id,
                    "label": row.label,
                    "normalized_sha256": row.normalized_sha256,
                    "prompt_ids": list(prompt.token_ids),
                }
            )
            + b"\n"
        )
    return digest.hexdigest(), truncated


def build_banking_prompt_candidate_receipt(
    development: VerifiedBankingDevelopment,
    tokenizer: CandidateTokenizer,
    *,
    max_tokens: int = 512,
) -> dict[str, Any]:
    """Bind verified-development order to exact prompt IDs without raw text.

    This is a candidate artifact only. It does not inspect or authorize a
    held-out split, and the R0.0 validator must independently bind model and
    tokenizer inventory, source code, and the other target families.
    """

    if not isinstance(development, VerifiedBankingDevelopment):
        raise BankingPromptReceiptError("verified development input required")
    if development.receipt.get("training_authority") is not False:
        raise BankingPromptReceiptError("source receipt must not authorize training")
    if not development.split.train or not development.split.dev:
        raise BankingPromptReceiptError("train and dev must be nonempty")
    template = prepare_banking_prompt(
        tokenizer, development.labels, max_tokens=max_tokens
    )
    train_root, train_truncated = _ordered_prompt_root(
        development.split.train, template
    )
    dev_root, dev_truncated = _ordered_prompt_root(development.split.dev, template)
    return {
        "receipt_version": 1,
        "status": "candidate-non-authorizing",
        "training_authority": False,
        "held_out_data_present": False,
        "source_receipt_sha256": sha256_bytes(
            canonical_json_bytes(development.receipt)
        ),
        "ordered_labels_sha256": sha256_bytes(canonical_json_bytes(development.labels)),
        "candidate_token_map_sha256": candidate_token_map_root(
            tokenizer, development.labels
        ),
        "prefix_token_ids_sha256": sha256_bytes(
            canonical_json_bytes(template.prefix_ids)
        ),
        "suffix_token_ids_sha256": sha256_bytes(
            canonical_json_bytes(template.suffix_ids)
        ),
        "prefix_tokens": len(template.prefix_ids),
        "suffix_tokens": len(template.suffix_ids),
        "max_candidate_tokens": template.max_candidate_tokens,
        "query_budget": template.query_budget,
        "max_common_tokens": template.max_tokens,
        "tokenization_policy": "separate-prefix-query-suffix-no-specials",
        "truncation_policy": "query-head-ceil-tail-floor-token-ids",
        "train_rows": len(development.split.train),
        "dev_rows": len(development.split.dev),
        "train_truncated_rows": train_truncated,
        "dev_truncated_rows": dev_truncated,
        "ordered_train_prompt_ids_sha256": train_root,
        "ordered_dev_prompt_ids_sha256": dev_root,
    }


def main() -> None:
    """Print only canonical candidate metadata from local development assets."""

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("development_source_dir", type=Path)
    parser.add_argument("local_tokenizer_snapshot_dir", type=Path)
    args = parser.parse_args()
    from transformers import AutoTokenizer

    development = load_verified_banking77_development(args.development_source_dir)
    tokenizer = AutoTokenizer.from_pretrained(
        str(args.local_tokenizer_snapshot_dir),
        local_files_only=True,
        trust_remote_code=False,
    )
    receipt = build_banking_prompt_candidate_receipt(development, tokenizer)
    sys.stdout.buffer.write(canonical_json_bytes(receipt) + b"\n")


if __name__ == "__main__":
    main()
