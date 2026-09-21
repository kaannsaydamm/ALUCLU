"""Reproducible control evidence for the pinned ALC-R0 host."""

from __future__ import annotations

import hashlib
import platform
import re
from collections.abc import Mapping, Sequence
from importlib.metadata import version
from typing import Any

import torch

from aluclu.alc_r0.base_digest import encode_base_state
from aluclu.alc_r0.canonical import canonical_json_bytes
from aluclu.alc_r0.host import SMOLLM2_135M_CONFIG, VerifiedHost

_COMMIT = re.compile(r"^[0-9a-f]{40}$")
_SHA256 = re.compile(r"^[0-9a-f]{64}$")
_OBSERVATION_KEYS = {
    "alias_group_count",
    "alias_record_sha256",
    "base_state_sha256",
    "config_identity",
    "dtype",
    "encoded_byte_length",
    "entry_count",
    "parameter_count",
    "runtime",
    "trainable_parameter_count",
    "training",
}


class HostEvidenceError(ValueError):
    """Raised when host evidence cannot support a reproducibility receipt."""


def observe_verified_host(host: VerifiedHost) -> dict[str, Any]:
    """Encode one loaded host and return a path-free deterministic observation."""

    parameters = tuple(host.model.parameters())
    if not parameters:
        raise HostEvidenceError("verified host has no parameters")
    dtypes = {str(parameter.dtype) for parameter in parameters}
    if dtypes != {"torch.bfloat16"}:
        raise HostEvidenceError(f"host parameter dtype drift: {sorted(dtypes)}")
    encoded = encode_base_state(host.model.state_dict(keep_vars=False))
    return {
        "alias_group_count": encoded.alias_group_count,
        "alias_record_sha256": encoded.alias_record_sha256,
        "base_state_sha256": encoded.sha256,
        "config_identity": dict(host.config_identity),
        "dtype": "torch.bfloat16",
        "encoded_byte_length": len(encoded.data),
        "entry_count": encoded.entry_count,
        "parameter_count": host.parameter_count,
        "runtime": {
            "python": platform.python_version(),
            "torch": str(torch.__version__),
            "transformers": version("transformers"),
        },
        "trainable_parameter_count": host.trainable_parameter_count,
        "training": host.training,
    }


def _validate_observation(observation: Mapping[str, Any]) -> None:
    if set(observation) != _OBSERVATION_KEYS:
        raise HostEvidenceError(
            "host observation fields do not match the frozen contract"
        )
    if observation.get("parameter_count") != 134_515_008:
        raise HostEvidenceError("host parameter count drift")
    if observation.get("trainable_parameter_count") != 0:
        raise HostEvidenceError("host has trainable base parameters")
    if observation.get("training") is not False:
        raise HostEvidenceError("host is not in eval mode")
    if observation.get("dtype") != "torch.bfloat16":
        raise HostEvidenceError("host dtype drift")
    if observation.get("config_identity") != SMOLLM2_135M_CONFIG.as_dict():
        raise HostEvidenceError("host config identity drift")
    for name in ("alias_record_sha256", "base_state_sha256"):
        value = observation.get(name)
        if not isinstance(value, str) or _SHA256.fullmatch(value) is None:
            raise HostEvidenceError(f"invalid observation digest: {name}")
    for name in ("alias_group_count", "encoded_byte_length", "entry_count"):
        value = observation.get(name)
        if type(value) is not int or value <= 0:
            raise HostEvidenceError(f"invalid observation count: {name}")
    runtime = observation.get("runtime")
    if not isinstance(runtime, Mapping) or set(runtime) != {
        "python",
        "torch",
        "transformers",
    }:
        raise HostEvidenceError("invalid host runtime identity")
    if not all(isinstance(value, str) and value for value in runtime.values()):
        raise HostEvidenceError("empty host runtime identity")


def build_host_evidence_receipt(
    observations: Sequence[Mapping[str, Any]],
    *,
    source_commit: str,
    acquisition_receipt_bytes: bytes,
    windows_lock_bytes: bytes,
    lock_manifest_bytes: bytes,
) -> dict[str, Any]:
    """Bind two equal fresh-process observations to source and dependency bytes."""

    if _COMMIT.fullmatch(source_commit) is None:
        raise HostEvidenceError("source commit must be lowercase 40-hex")
    if len(observations) != 2:
        raise HostEvidenceError("host evidence requires exactly two fresh processes")
    for observation in observations:
        _validate_observation(observation)
    first = canonical_json_bytes(dict(observations[0]))
    second = canonical_json_bytes(dict(observations[1]))
    if first != second:
        raise HostEvidenceError("fresh-process host observations differ")
    stable_observation = dict(observations[0])
    return {
        "acquisition_receipt_sha256": hashlib.sha256(
            acquisition_receipt_bytes
        ).hexdigest(),
        "experiment_id": "alc-r0-smollm2-135m-v1",
        "fresh_process_reproducible": True,
        "lock_manifest_sha256": hashlib.sha256(lock_manifest_bytes).hexdigest(),
        "observations": [stable_observation, dict(stable_observation)],
        "process_count": 2,
        "schema_id": (
            "https://aluclu.org/schemas/alc_r0/v1/base-digest-receipt.schema.json"
        ),
        "schema_version": 1,
        "source_commit": source_commit,
        "training_authority": False,
        "windows_lock_sha256": hashlib.sha256(windows_lock_bytes).hexdigest(),
    }
