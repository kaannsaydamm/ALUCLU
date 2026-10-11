"""Bind the fixed six D fixtures to the pinned offline snapshot tokenizer.

No dataset, host load, forward, optimizer, process launcher or launch authority.
Asset hashes are checked before loading and after encoding. Cooperating-process
runtime/source authentication and resource reservations remain caller duties;
these observations cannot attest against a compromised tokenizer/runtime.
"""

import hashlib
import os
from dataclasses import asdict, dataclass
from pathlib import Path

from .acquisition import verify_model_snapshot
from .canonical import canonical_json_bytes
from .checkpoint_parity_inputs import ParityInput, parity_input
from .defect_prompt import prepare_defect_prompt


class ParityTokenizerError(ValueError):
    """Pinned assets, tokenizer metadata or fixed D encoding is invalid."""


@dataclass(frozen=True)
class TokenizedParityFixtures:
    snapshot_inventory_sha256: str
    model_revision: str
    tokenizer_class: str
    fixture_sha256: str
    fixtures: tuple[ParityInput, ...]


def _load_tokenizer(snapshot):
    from transformers import AutoTokenizer

    return AutoTokenizer.from_pretrained(
        str(snapshot), local_files_only=True, trust_remote_code=False, use_fast=True
    )


def _metadata(tokenizer):
    for field, expected in (
        ("bos_token_id", 0),
        ("eos_token_id", 0),
        ("vocab_size", 49152),
    ):
        value = getattr(tokenizer, field, None)
        if type(value) is not int or value != expected:
            raise ParityTokenizerError(f"pinned tokenizer {field} required")
    if getattr(tokenizer, "is_fast", None) is not True or len(tokenizer) != 49152:
        raise ParityTokenizerError("pinned fast tokenizer vocabulary required")


def _fixtures(template):
    return tuple(
        parity_input(
            prefix_ids=template.prefix_ids,
            suffix_ids=template.suffix_ids,
            safe_ids=template.safe_candidate_ids,
            vulnerable_ids=template.vulnerable_candidate_ids,
            eos_token_id=0,
            common_length=length,
            label=label,
            padded=padded,
        )
        for length, padded in ((32, False), (64, False), (64, True))
        for label in ("safe", "vulnerable")
    )


def load_parity_fixtures(snapshot: Path) -> TokenizedParityFixtures:
    """Verify local assets and freeze complete tokenizer-derived D fixtures.

    Uses the unchanged defect framing and leading-space candidate encoding.
    No custom tokenizer/backend or caller-supplied token IDs in this production
    boundary. Repeat encoding must agree; no retry or alternate fixture on error.
    This API is not an executable invocation or permission to run an experiment.
    """
    if not isinstance(snapshot, Path) or not snapshot.is_absolute():
        raise ParityTokenizerError("absolute snapshot path required")
    flags = ("HF_HUB_OFFLINE", "TRANSFORMERS_OFFLINE", "HF_DATASETS_OFFLINE")
    if any(os.environ.get(flag) != "1" for flag in flags):
        raise ParityTokenizerError("offline flags must all equal1 before access")
    try:
        before = verify_model_snapshot(snapshot)
    except Exception as exc:
        raise ParityTokenizerError("pinned snapshot verification failed") from exc
    try:
        tokenizer = _load_tokenizer(snapshot)
        _metadata(tokenizer)
        template = prepare_defect_prompt(tokenizer, max_tokens=32)
        fixtures = _fixtures(template)
        repeated = _fixtures(prepare_defect_prompt(tokenizer, max_tokens=32))
        _metadata(tokenizer)
        if repeated != fixtures:
            raise ParityTokenizerError("tokenizer encoding changed during construction")
    except ParityTokenizerError:
        raise
    except Exception as exc:
        raise ParityTokenizerError(
            "pinned tokenizer fixture construction failed"
        ) from exc
    try:
        after = verify_model_snapshot(snapshot)
        if before != after:
            raise ParityTokenizerError("snapshot changed during tokenization")
    except ParityTokenizerError:
        raise
    except Exception as exc:
        raise ParityTokenizerError("terminal snapshot verification failed") from exc
    payload = {
        "fixtures": [asdict(fixture) for fixture in fixtures],
        "revision": before["revision"],
        "snapshot_inventory_sha256": before["inventory_sha256"],
    }
    return TokenizedParityFixtures(
        snapshot_inventory_sha256=before["inventory_sha256"],
        model_revision=before["revision"],
        tokenizer_class=f"{type(tokenizer).__module__}.{type(tokenizer).__qualname__}",
        fixture_sha256=hashlib.sha256(canonical_json_bytes(payload)).hexdigest(),
        fixtures=fixtures,
    )
