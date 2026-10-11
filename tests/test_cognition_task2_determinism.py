from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from subprocess import run
from typing import Any, cast

import pytest

WORKER = Path(__file__).resolve().parent / "helpers" / "task2_determinism_worker.py"
SRC_ROOT = Path(__file__).resolve().parents[1] / "src"

HASH_SEEDS = ("0", "17", "random")
TIMEZONES = ("UTC", "Europe/Istanbul", "America/New_York")

FROZEN_OBSERVATION_VECTOR = {
    "boundary_profile_id": "boundary-profile:" + ("1" * 64),
    "content_digest_nfc": (
        "5b635da1a00b302f071b759714e83226032a1c942e5f9a4c0626c8c5b89fd49d"
    ),
    "content_digest_nfd": (
        "ae77c8a0e742651b754609737c85fa9afc6e9725b9a1e5401aaa0b7748fccb66"
    ),
    "episode_id": (
        "episode:f2dc3cb66b63ccf55e0e923eeb0b9877627ab92b82bb6d943107e671083f5c3e"
    ),
    "post_core_bytes_len": 889,
    "post_core_state_digest": (
        "c478677f2fecd55a3a1c3965930884207c5fb4e8ce0bda547958e3fb5fee6d14"
    ),
    "pre_core_state_digest": (
        "b51eea1117deb34bc5c9b5d4fa20bcb182a5644015183c1bcce31e1a0f00a2c3"
    ),
    "request_bytes_len": 693,
    "request_digest": (
        "acb47b307a12f8436e95debf9fe67965a4473056c400fbc4c07e5001fd8e0810"
    ),
    "search_hex_nfc": "c3a9",
    "search_hex_nfd": "c3a9",
}

FROZEN_FEATURE_DIGEST_BY_UCD = {
    "13.0.0": "c03f3479940712ba1c1c7b60c7a30a8b28498e5889c74f49ebf3214e78a26ebb",
    "14.0.0": "2bfcdc61f7e02c51d8c725120406e63c182f2b556748170b02d51914f82e8eea",
    "15.0.0": "4f128ac04a38c204cf98516d2956f45a33e0ba5ddd21f086b1ccad11d6531fbd",
    "15.1.0": "72d4b6ccfbdf897dcf5209505eca323d62d9a9d2c5c99ca81578507166ba7ede",
}


def _worker_env(*, hash_seed: str, timezone: str) -> dict[str, str]:
    env = os.environ.copy()
    env.update(
        {
            "PYTHONHASHSEED": hash_seed,
            "PYTHONIOENCODING": "utf-8",
            "PYTHONPATH": str(SRC_ROOT),
            "TZ": timezone,
        }
    )
    return env


def _run_worker(*, hash_seed: str, timezone: str) -> dict[str, Any]:
    completed = run(
        [sys.executable, str(WORKER)],
        capture_output=True,
        check=True,
        cwd=Path(__file__).resolve().parents[1],
        env=_worker_env(hash_seed=hash_seed, timezone=timezone),
        text=True,
        timeout=15,
    )
    payload = json.loads(completed.stdout)
    assert type(payload) is dict
    assert completed.stderr == ""
    return cast(dict[str, Any], payload)


def _stable_payload(payload: dict[str, Any]) -> dict[str, Any]:
    return {
        key: value
        for key, value in payload.items()
        if key not in {"python_hash_seed", "python_version", "timezone"}
    }


@pytest.mark.parametrize("hash_seed", HASH_SEEDS)
@pytest.mark.parametrize("timezone", TIMEZONES)
def test_task2_observation_vectors_match_frozen_literals_across_process_env(
    hash_seed: str,
    timezone: str,
) -> None:
    payload = _run_worker(hash_seed=hash_seed, timezone=timezone)

    assert payload["python_hash_seed"] == hash_seed
    assert payload["timezone"] == timezone
    assert {
        key: payload[key] for key in FROZEN_OBSERVATION_VECTOR
    } == FROZEN_OBSERVATION_VECTOR
    assert payload["content_digest_nfd"] != payload["content_digest_nfc"]
    assert payload["search_hex_nfd"] == payload["search_hex_nfc"]


def test_task2_vectors_are_identical_across_hash_seed_and_timezone_matrix() -> None:
    payloads = [
        _stable_payload(_run_worker(hash_seed=hash_seed, timezone=timezone))
        for hash_seed in HASH_SEEDS
        for timezone in TIMEZONES
    ]

    assert payloads == [payloads[0]] * len(payloads)


def test_task2_feature_identity_is_version_scoped_to_active_ucd() -> None:
    payload = _run_worker(hash_seed="0", timezone="UTC")
    ucd_version = payload["ucd_version"]

    assert ucd_version in FROZEN_FEATURE_DIGEST_BY_UCD
    assert payload["normalizer_id"] == (
        f"aluclu.search-view.nfc-ascii-ws.v1+ucd-{ucd_version}"
    )
    assert payload["feature_spec_id"] == (
        f"aluclu.feature.signed-byte-ngram-1024-int16.v1+ucd-{ucd_version}"
    )
    assert payload["feature_vector_digest"] == FROZEN_FEATURE_DIGEST_BY_UCD[ucd_version]
