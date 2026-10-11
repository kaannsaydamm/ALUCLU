"""Separate fixed q/v official-forward composition over one supplied host.

No loader, callback injection, optimizer or launch authority. Caller authenticates
assets/source/runtime and admits inclusive resources before invoking. Mutable
base/factors require exclusive cooperative ownership; receipts are observations,
not authentication, scientific adoption or completion of the matched D suite.
"""

import hashlib
import json
import re
from dataclasses import dataclass

import torch

from .checkpoint_execution import _digest
from .checkpoint_observation import _base_digest, _roster_stamp
from .checkpoint_official_forward import (
    FORWARD_CASES,
    ForwardCase,
    OfficialCase,
    OfficialKey,
    _case,
    _nonzero_witness,
    _receipt,
)
from .checkpoint_parity_factory import _base_device, make_reference_wrapper
from .reference_official_guard import ReferencePhaseGuard
from .reference_qv_artifact import _SHAPES, _live_factors

REFERENCE_SCHEDULE = tuple(
    (OfficialKey("qv-reference-r8", "qv_reference", phase), case)
    for phase in ("unmounted", "zero", "detached")
    for case in FORWARD_CASES
)
_NAMES = tuple(sorted(_SHAPES))


@dataclass(frozen=True)
class ReferenceWitness:
    official_sha256: str
    mounted_sha256: str
    factor_sha256: str


@dataclass(frozen=True)
class ReferenceOfficialSuite:
    source_device: str
    source_dtype: str
    base_digest: str
    configuration_digest: str
    host_identity_digest: str
    parameter_names: tuple[str, ...]
    parameter_count: int
    phase_factors: tuple[tuple[str, str, str], ...]
    cases: tuple[OfficialCase, ...]
    witness: ReferenceWitness


@dataclass(frozen=True)
class ReferenceOfficialFailure:
    completed: tuple[OfficialCase, ...]
    current: tuple[OfficialKey, ForwardCase]
    unrun: tuple[tuple[OfficialKey, ForwardCase], ...]
    witness: ReferenceWitness | None
    stage: str


class ReferenceOfficialError(RuntimeError):
    def __init__(self, failure):
        super().__init__(f"terminal q/v official error at {failure.current}")
        self.failure = failure


class ReferenceOfficialInterrupted(KeyboardInterrupt):
    def __init__(self, failure):
        super().__init__(f"q/v official interrupted at {failure.current}")
        self.failure = failure


def _json_digest(value):
    raw = json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def _signature(host):
    device = _base_device(host)
    base, config = host.model, host.model.config
    if (
        device not in (torch.device("cpu"), torch.device("cuda:0"))
        or type(config.vocab_size) is not int
        or config.vocab_size != 49152
        or type(config.max_position_embeddings) is not int
        or config.max_position_embeddings != 8192
        or config._attn_implementation != "eager"
        or any(buffer.grad is not None for buffer in base.buffers())
    ):
        raise ValueError("pinned vocabulary/capacity/eager and clean base required")
    return (
        device,
        _base_digest(base),
        _roster_stamp(base.named_parameters()),
        _roster_stamp(base.named_buffers()),
        id(config),
        _json_digest(config.to_dict()),
        _json_digest((dict(host.acquisition_receipt), dict(host.config_identity))),
        id(base),
    )


def _sha(value):
    if type(value) is not str or re.fullmatch(r"[0-9a-f]{64}", value) is None:
        raise ValueError("canonical SHA256 required")


def _row_receipt(row, key, case, *, exact):
    _receipt(row, key, case)
    if exact and (
        row.official_sha256 != row.wrapper_sha256
        or row.incremental_official_sha256 != row.incremental_wrapper_sha256
    ):
        raise ValueError("CPU receipt must retain bitwise equal logit digests")


def validate_reference_official_suite(result):
    """Strict bounded structure validation, never a signature/host certificate."""
    if (
        type(result) is not ReferenceOfficialSuite
        or (result.source_device, result.source_dtype)
        not in (("cpu", "torch.float32"), ("cuda:0", "torch.bfloat16"))
        or type(result.parameter_count) is not int
        or result.parameter_count != 460800
        or type(result.parameter_names) is not tuple
        or result.parameter_names != _NAMES
        or type(result.cases) is not tuple
        or len(result.cases) != 72
        or type(result.phase_factors) is not tuple
        or len(result.phase_factors) != 3
        or type(result.witness) is not ReferenceWitness
    ):
        raise ValueError("complete separately typed q/v official receipt required")
    for digest in (
        result.base_digest,
        result.configuration_digest,
        result.host_identity_digest,
    ):
        _sha(digest)
    for phase, entry in zip(
        ("unmounted", "zero", "detached"), result.phase_factors, strict=True
    ):
        if type(entry) is not tuple or len(entry) != 3 or entry[0] != phase:
            raise ValueError("exact three ordered phase factor records required")
        _sha(entry[1])
        _sha(entry[2])
    if len({entry[1:] for entry in result.phase_factors}) != 1:
        raise ValueError("identical original seeded factors across phases required")
    witness = result.witness
    for digest in (
        witness.official_sha256,
        witness.mounted_sha256,
        witness.factor_sha256,
    ):
        _sha(digest)
    if (
        witness.official_sha256 == witness.mounted_sha256
        or witness.factor_sha256 == result.phase_factors[0][2]
    ):
        raise ValueError("changed logits and witness factor bytes required")
    for row, (key, case) in zip(result.cases, REFERENCE_SCHEDULE, strict=True):
        _row_receipt(row, key, case, exact=result.source_device == "cpu")


def run_reference_official_suite(host, *, exact):
    """Execute all 72 rows once; on error preserve bounded prefix/unrun schedule.

    Parent owns durable attempt logs, timeout/process-kill handling, source and
    asset authentication, deterministic CUDA context and fresh-process repeats.
    No catch/retry/OOM fallback, optimizer or tolerance change occurs here.
    """
    if type(exact) is not bool:
        raise ValueError("exact boolean required")
    completed, phases, witness = [], [], None
    wrapper, guard, current_phase, signature = None, None, None, None
    base = getattr(host, "model", None)
    for index, (key, case) in enumerate(REFERENCE_SCHEDULE):
        stage, attempted = "base-preflight", False
        try:
            current = _signature(host)
            if signature is None:
                signature = current
                if exact != (signature[0].type == "cpu"):
                    raise ValueError("CPU exact/GPU fixed tolerance mode required")
            if host.model is not base or current != signature:
                raise ValueError(
                    "one unchanged base/configuration/host identity required"
                )
            if current_phase != key.phase:
                stage = "preparation"
                guard, wrapper = None, None
                with torch.inference_mode(False):
                    wrapper = make_reference_wrapper(host, False, state="zero")
                    wrapper.eval()
                    ReferencePhaseGuard(wrapper, base, mounted=True).check()
                    named = tuple(_live_factors(wrapper.reference).items())
                    a_digest = _digest(
                        tuple((n, p) for n, p in named if n.endswith(".A"))
                    )
                    factor_digest = _digest(named)
                    del named
                    phases.append((key.phase, a_digest, factor_digest))
                    if any(entry[1:] != phases[0][1:] for entry in phases):
                        raise ValueError("same seeded factors across phases required")
                    if key.phase == "unmounted":
                        wrapper.detach()
                    elif key.phase == "detached":
                        with torch.no_grad():
                            for name, parameter in wrapper.reference.named_parameters():
                                if name.endswith(".B"):
                                    parameter.fill_(0.01)
                        guard = ReferencePhaseGuard(
                            wrapper, base, mounted=True, expected_b=0.01
                        )
                        stage = "witness"
                        with torch.inference_mode():
                            logits = _nonzero_witness(wrapper, signature[0])
                        guard.check()
                        if _signature(host) != signature:
                            raise ValueError("base changed during witness")
                        candidate = ReferenceWitness(
                            *logits,
                            _digest(tuple(_live_factors(wrapper.reference).items())),
                        )
                        for digest in (
                            candidate.official_sha256,
                            candidate.mounted_sha256,
                            candidate.factor_sha256,
                        ):
                            _sha(digest)
                        if candidate.official_sha256 == candidate.mounted_sha256:
                            raise ValueError("nonzero witness must change logits")
                        witness = candidate
                        stage = "detach"
                        guard = None
                        wrapper.detach()
                    guard = ReferencePhaseGuard(
                        wrapper, base, mounted=key.phase == "zero"
                    )
                    current_phase = key.phase
            stage = "case-preflight"
            if _signature(host) != signature:
                raise ValueError("base changed during preparation")
            guard.check()
            stage, attempted = "case", True
            with torch.inference_mode():
                row = _case(wrapper, key, case, exact=exact)
            stage = "case-validation"
            if _signature(host) != signature:
                raise ValueError("base changed during case")
            guard.check()
            _row_receipt(row, key, case, exact=exact)
            completed.append(row)
            if index == 71:
                stage = "suite-validation"
                result = ReferenceOfficialSuite(
                    str(signature[0]),
                    str(next(base.parameters()).dtype),
                    signature[1],
                    signature[5],
                    signature[6],
                    _NAMES,
                    460800,
                    tuple(phases),
                    tuple(completed),
                    witness,
                )
                validate_reference_official_suite(result)
                return result
        except (Exception, KeyboardInterrupt) as exc:
            failure = ReferenceOfficialFailure(
                tuple(completed),
                (key, case),
                REFERENCE_SCHEDULE[index + int(attempted) :],
                witness,
                stage,
            )
            error = (
                ReferenceOfficialInterrupted
                if isinstance(exc, KeyboardInterrupt)
                else ReferenceOfficialError
            )
            raise error(failure) from exc
