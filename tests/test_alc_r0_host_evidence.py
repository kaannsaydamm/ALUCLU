from __future__ import annotations

import hashlib
from pathlib import Path

import pytest

from aluclu.alc_r0.canonical import canonical_json_bytes
from aluclu.alc_r0.host_evidence import (
    HostEvidenceError,
    build_host_evidence_receipt,
)
from aluclu.alc_r0.schema_validation import validate_r0_document

SCHEMA_ROOT = Path(__file__).parents[1] / "schemas" / "alc_r0" / "v1"


def _observation() -> dict[str, object]:
    return {
        "alias_group_count": 272,
        "alias_record_sha256": "8efcc3120c19a1a0784811d4ae95d327849ad8e7bd9176d45c3a6b9b7f067a84",
        "base_state_sha256": "ce7e8dd6a97ac4cc56bf4f1e38625817386e27af58f1ed63377741f7f2aab1ba",
        "config_identity": {
            "architectures": ["LlamaForCausalLM"],
            "bos_token_id": 0,
            "eos_token_id": 0,
            "hidden_size": 576,
            "intermediate_size": 1536,
            "max_position_embeddings": 8192,
            "model_type": "llama",
            "num_attention_heads": 9,
            "num_hidden_layers": 30,
            "num_key_value_heads": 3,
            "tie_word_embeddings": True,
            "vocab_size": 49152,
        },
        "dtype": "torch.bfloat16",
        "encoded_byte_length": 325706271,
        "entry_count": 273,
        "parameter_count": 134515008,
        "runtime": {
            "python": "3.12.13",
            "torch": "2.14.0+cu130",
            "transformers": "5.17.0",
        },
        "trainable_parameter_count": 0,
        "training": False,
    }


def test_build_host_evidence_receipt_binds_two_identical_processes() -> None:
    observation = _observation()
    acquisition = canonical_json_bytes({"receipt": "acquisition"})
    lock = b"windows-lock\n"
    lock_manifest = canonical_json_bytes({"locks": []})

    receipt = build_host_evidence_receipt(
        [observation, dict(observation)],
        source_commit="a" * 40,
        acquisition_receipt_bytes=acquisition,
        windows_lock_bytes=lock,
        lock_manifest_bytes=lock_manifest,
    )

    assert receipt["process_count"] == 2
    assert receipt["fresh_process_reproducible"] is True
    assert receipt["training_authority"] is False
    assert receipt["observations"] == [observation, observation]
    assert (
        receipt["acquisition_receipt_sha256"] == hashlib.sha256(acquisition).hexdigest()
    )
    assert receipt["windows_lock_sha256"] == hashlib.sha256(lock).hexdigest()
    assert receipt["lock_manifest_sha256"] == hashlib.sha256(lock_manifest).hexdigest()


def test_build_host_evidence_receipt_rejects_wrong_count_or_drift() -> None:
    observation = _observation()
    arguments = {
        "source_commit": "a" * 40,
        "acquisition_receipt_bytes": b"acquisition",
        "windows_lock_bytes": b"lock",
        "lock_manifest_bytes": b"manifest",
    }
    with pytest.raises(HostEvidenceError, match="exactly two"):
        build_host_evidence_receipt([observation], **arguments)

    changed = dict(observation)
    changed["base_state_sha256"] = "3" * 64
    with pytest.raises(HostEvidenceError, match="differ"):
        build_host_evidence_receipt([observation, changed], **arguments)


@pytest.mark.parametrize("source_commit", ["main", "A" * 40, "0" * 39])
def test_build_host_evidence_receipt_rejects_unpinned_source(
    source_commit: str,
) -> None:
    observation = _observation()
    with pytest.raises(HostEvidenceError, match="source commit"):
        build_host_evidence_receipt(
            [observation, dict(observation)],
            source_commit=source_commit,
            acquisition_receipt_bytes=b"acquisition",
            windows_lock_bytes=b"lock",
            lock_manifest_bytes=b"manifest",
        )


def test_frozen_base_digest_schema_accepts_the_observed_host_identity() -> None:
    observation = _observation()
    receipt = {
        "acquisition_receipt_sha256": "2a4baddc2bb8451811e199e7dd6f91512fad73d367083c833e117c3e4d09984a",
        "experiment_id": "alc-r0-smollm2-135m-v1",
        "fresh_process_reproducible": True,
        "lock_manifest_sha256": "1756f42033d4de2f5d2944fc7a95a4e324665a26f54c0679bb757658fc91abaf",
        "observations": [observation, dict(observation)],
        "process_count": 2,
        "schema_id": "https://aluclu.org/schemas/alc_r0/v1/base-digest-receipt.schema.json",
        "schema_version": 1,
        "source_commit": "a" * 40,
        "training_authority": False,
        "windows_lock_sha256": "a7a921f7b095b0329fbb7df6a25612c6e8a1f160122f853a6a159d8478946615",
    }

    assert (
        validate_r0_document(
            canonical_json_bytes(receipt),
            schema_name="base-digest-receipt",
            schema_root=SCHEMA_ROOT,
        )
        == receipt
    )
