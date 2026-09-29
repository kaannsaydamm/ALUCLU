"""Development-only test for PrimeVul pair contrasts lost in the candidate prompt.

Identical vulnerable/patched prompt IDs prove that the pair is not separable
from this input alone. Different prompt IDs do not prove that the vulnerability
signal survived or that a model can learn it. This is never a training gate.
"""

from __future__ import annotations

import argparse
import hashlib
import re
import stat
import sys
from collections.abc import Sequence
from dataclasses import asdict
from pathlib import Path
from typing import Any

from .acquisition import verify_model_snapshot
from .banking_scoring import CandidateTokenizer
from .canonical import canonical_json_bytes, sha256_bytes
from .defect_prompt import DefectPromptError, prepare_defect_prompt
from .primevul_pairs_source import (
    PRIMEVUL_ORIGINAL_PAIRS,
    PrimeVulPairExpectation,
    _decode_row,
    verify_primevul_development_pairs,
)
from .primevul_source import (
    PRIMEVUL_ORIGINAL_DEVELOPMENT,
    PrimeVulDevelopmentExpectation,
)
from .source_checkout import inspect_clean_source_checkout

_MAX_PAIRS = 10_000
_DECLARED_COMMON_BUDGETS = (512, 1024, 2048, 4096, 8192)
_HEX64 = re.compile(r"[0-9a-f]{64}\Z")


class PairedPromptContrastError(ValueError):
    """A pair or pinned development source violates the diagnostic contract."""


def audit_paired_prompt_contrast(
    pairs: Sequence[tuple[str, str]],
    tokenizer: CandidateTokenizer,
    *,
    max_tokens: int = 512,
) -> dict[str, Any]:
    """Count exact prompt collisions, without returning source text or IDs.

    Each tuple is ordered (vulnerable function, patched-safe function).
    """

    if not isinstance(pairs, (tuple, list)) or not 0 < len(pairs) <= _MAX_PAIRS:
        raise PairedPromptContrastError("bounded nonempty pair sequence required")
    try:
        template = prepare_defect_prompt(tokenizer, max_tokens=max_tokens)
    except DefectPromptError as exc:
        raise PairedPromptContrastError("invalid prompt template") from exc
    digest = hashlib.sha256()
    collapsed = both_truncated = one_truncated = neither_truncated = 0
    for pair in pairs:
        if (
            not isinstance(pair, tuple)
            or len(pair) != 2
            or any(not isinstance(code, str) or not code.strip() for code in pair)
        ):
            raise PairedPromptContrastError("invalid ordered pair")
        try:
            vulnerable = template.build(pair[0].encode("utf-8", errors="strict"))
            safe = template.build(pair[1].encode("utf-8", errors="strict"))
        except (UnicodeEncodeError, DefectPromptError) as exc:
            raise PairedPromptContrastError("invalid pair prompt") from exc
        if vulnerable.normalized_code == safe.normalized_code:
            raise PairedPromptContrastError("opposite-label pair has identical code")
        vulnerable_cut = (
            vulnerable.original_code_tokens > vulnerable.retained_code_tokens
        )
        safe_cut = safe.original_code_tokens > safe.retained_code_tokens
        both_truncated += vulnerable_cut and safe_cut
        one_truncated += vulnerable_cut != safe_cut
        neither_truncated += not (vulnerable_cut or safe_cut)
        collapsed += vulnerable.token_ids == safe.token_ids
        digest.update(
            canonical_json_bytes(
                {
                    "vulnerable_prompt_ids": list(vulnerable.token_ids),
                    "safe_prompt_ids": list(safe.token_ids),
                }
            )
            + b"\n"
        )
    return {
        "status": "development-pair-prompt-contrast-non-authorizing",
        "training_authority": False,
        "held_out_data_present": False,
        "pairs": len(pairs),
        "collapsed_pairs": collapsed,
        "both_truncated_pairs": both_truncated,
        "one_truncated_pairs": one_truncated,
        "neither_truncated_pairs": neither_truncated,
        "ordered_pair_prompt_ids_sha256": digest.hexdigest(),
    }


def _read_pinned_pair_functions(
    path: Path, *, expected_sha256: str, expected_pairs: int
) -> tuple[tuple[str, str], ...]:
    if path.is_symlink() or not path.is_file() or not stat.S_ISREG(path.stat().st_mode):
        raise PairedPromptContrastError("paired development file is not regular")
    digest = hashlib.sha256()
    pairs: list[tuple[str, str]] = []
    with path.open("rb") as stream:
        for left_raw in stream:
            right_raw = stream.readline()
            if not right_raw:
                raise PairedPromptContrastError("truncated paired source")
            digest.update(left_raw)
            digest.update(right_raw)
            left = _decode_row(left_raw)
            right = _decode_row(right_raw)
            if left["target"] != 1 or right["target"] != 0:
                raise PairedPromptContrastError("pair labels must be ordered 1,0")
            pairs.append((left["func"], right["func"]))
    if digest.hexdigest() != expected_sha256 or len(pairs) != expected_pairs:
        raise PairedPromptContrastError("pinned pair file changed during read")
    return tuple(pairs)


def run_pinned_paired_prompt_contrast(
    source_dir: Path,
    paired_dir: Path,
    tokenizer: CandidateTokenizer,
    *,
    model_inventory_sha256: str,
    max_common_tokens: int = 512,
    source_expectation: PrimeVulDevelopmentExpectation = PRIMEVUL_ORIGINAL_DEVELOPMENT,
    pair_expectation: PrimeVulPairExpectation = PRIMEVUL_ORIGINAL_PAIRS,
) -> dict[str, Any]:
    """Verify original development bytes, then compare candidate pair prompts."""

    if not isinstance(model_inventory_sha256, str) or not _HEX64.fullmatch(
        model_inventory_sha256
    ):
        raise PairedPromptContrastError("invalid model inventory SHA-256")
    if (
        type(max_common_tokens) is not int
        or max_common_tokens not in _DECLARED_COMMON_BUDGETS
    ):
        raise PairedPromptContrastError("common budget is outside declared grid")
    source_receipt = verify_primevul_development_pairs(
        source_dir,
        paired_dir,
        source_expectation=source_expectation,
        pair_expectation=pair_expectation,
    )
    train = _read_pinned_pair_functions(
        paired_dir / "primevul_train_paired.jsonl",
        expected_sha256=pair_expectation.train_sha256,
        expected_pairs=pair_expectation.train_pairs,
    )
    validation = _read_pinned_pair_functions(
        paired_dir / "primevul_valid_paired.jsonl",
        expected_sha256=pair_expectation.validation_sha256,
        expected_pairs=pair_expectation.validation_pairs,
    )
    return {
        "receipt_version": 1,
        "status": "pinned-development-pair-prompt-contrast-non-authorizing",
        "source_scope": (
            "pinned-original-development"
            if source_expectation == PRIMEVUL_ORIGINAL_DEVELOPMENT
            and pair_expectation == PRIMEVUL_ORIGINAL_PAIRS
            else "fixture"
        ),
        "training_authority": False,
        "held_out_data_present": False,
        "pair_source_receipt_sha256": sha256_bytes(
            canonical_json_bytes(source_receipt)
        ),
        "model_inventory_sha256": model_inventory_sha256,
        "max_common_tokens": max_common_tokens,
        "train": audit_paired_prompt_contrast(
            train, tokenizer, max_tokens=max_common_tokens
        ),
        "validation": audit_paired_prompt_contrast(
            validation, tokenizer, max_tokens=max_common_tokens
        ),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("development_data_dir", type=Path)
    parser.add_argument("paired_development_data_dir", type=Path)
    parser.add_argument("tokenizer_snapshot", type=Path)
    parser.add_argument(
        "--max-common-tokens",
        type=int,
        choices=_DECLARED_COMMON_BUDGETS,
        default=512,
        help="development-only context-budget sensitivity grid value",
    )
    args = parser.parse_args()
    checkout = inspect_clean_source_checkout(Path.cwd().resolve(strict=True))
    snapshot_receipt = verify_model_snapshot(args.tokenizer_snapshot)
    from transformers import AutoTokenizer

    tokenizer = AutoTokenizer.from_pretrained(
        str(args.tokenizer_snapshot), local_files_only=True, trust_remote_code=False
    )
    receipt = run_pinned_paired_prompt_contrast(
        args.development_data_dir,
        args.paired_development_data_dir,
        tokenizer,
        model_inventory_sha256=snapshot_receipt["inventory_sha256"],
        max_common_tokens=args.max_common_tokens,
    )
    if (
        verify_model_snapshot(args.tokenizer_snapshot)["inventory_sha256"]
        != snapshot_receipt["inventory_sha256"]
    ):
        raise PairedPromptContrastError("tokenizer snapshot changed during run")
    if inspect_clean_source_checkout(Path.cwd().resolve(strict=True)) != checkout:
        raise PairedPromptContrastError("source checkout changed during run")
    receipt["source_checkout"] = asdict(checkout)
    receipt["invocation"] = {
        "module": "aluclu.alc_r0.paired_prompt_contrast",
        "source_dir": str(args.development_data_dir.resolve(strict=True)),
        "paired_dir": str(args.paired_development_data_dir.resolve(strict=True)),
        "tokenizer_snapshot": str(args.tokenizer_snapshot.resolve(strict=True)),
        "python_executable": str(Path(sys.executable).resolve(strict=True)),
        "python_version": sys.version.split()[0],
    }
    sys.stdout.buffer.write(canonical_json_bytes(receipt) + b"\n")


if __name__ == "__main__":
    main()
