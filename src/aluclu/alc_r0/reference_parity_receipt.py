"""Bounded separate q/v cell receipts; no execution or authentication authority.

These summaries retain the generic engine's comparison results, not raw tensors.
The caller must bind live120 factor geometry, authenticated fixtures/source/base
and complete execution separately. A fabricated well-formed receipt proves none
of those. No original matched-grid receipt or scientific threshold is changed.
"""

import math
import re
from dataclasses import dataclass

from .checkpoint_fidelity import TensorComparison
from .checkpoint_optimizer import AdamWComparison
from .checkpoint_parity_cell import CaseComparison, ParityCell
from .checkpoint_parity_factory import PARITY_SEED
from .reference_qv_artifact import _SHAPES

REFERENCE_NAMES = tuple(sorted(_SHAPES, key=lambda name: name.encode("utf-8")))


@dataclass(frozen=True)
class ReferenceParityIdentity:
    source_device: str
    source_dtype: str
    base_digest: str
    configuration_digest: str
    host_identity_digest: str
    fixture_digest: str


@dataclass(frozen=True)
class ReferenceParityReceipt:
    identity: ReferenceParityIdentity
    seed: int
    cell: ParityCell


def _sha(value):
    if type(value) is not str or re.fullmatch(r"[0-9a-f]{64}", value) is None:
        raise ValueError("canonical SHA256 required")


def _identity(value):
    if type(value) is not ReferenceParityIdentity or (
        value.source_device,
        value.source_dtype,
    ) not in (("cpu", "torch.float32"), ("cuda:0", "torch.bfloat16")):
        raise ValueError("typed CPU FP32/GPU0 BF16 identity required")
    for digest in (
        value.base_digest,
        value.configuration_digest,
        value.host_identity_digest,
        value.fixture_digest,
    ):
        _sha(digest)


def _finite(value):
    return type(value) is float and math.isfinite(value)


def _pair(value, *, exact):
    if (
        type(value) is not tuple
        or len(value) != 2
        or not all(_finite(item) for item in value)
        or (exact and value[0] != value[1])
    ):
        raise ValueError("finite scalar pair and CPU equality required")


def _metric(value, *, exact):
    if type(value) is not TensorComparison or type(value.exact_zero) is not bool:
        raise ValueError("typed tensor comparison required")
    norms = (value.reference_l2, value.actual_l2, value.difference_l2)
    if not all(_finite(item) and item >= 0 for item in norms):
        raise ValueError("finite nonnegative comparison norms required")
    if value.exact_zero:
        if (
            norms != (0.0, 0.0, 0.0)
            or value.relative_l2 is not None
            or value.cosine is not None
        ):
            raise ValueError("exact-zero comparison metadata differs")
        return
    if (
        value.reference_l2 <= 0
        or value.actual_l2 <= 0
        or not _finite(value.relative_l2)
        or not 0 <= value.relative_l2 <= 1e-5
        or not _finite(value.cosine)
        or not 1 - 1e-6 <= value.cosine <= 1
        or ((value.difference_l2 == 0) != (value.relative_l2 == 0))
        or (
            exact
            and (value.difference_l2 != 0 or value.reference_l2 != value.actual_l2)
        )
    ):
        raise ValueError("fixed fidelity summary/CPU equality required")


def _optimizer(value, *, exact):
    if (
        type(value) is not AdamWComparison
        or type(value.step) is not int
        or value.step != 1
    ):
        raise ValueError("complete fixed AdamW step1 comparison required")
    for mapping in (value.factors, value.exp_avg, value.exp_avg_sq):
        if type(mapping) is not tuple or len(mapping) != 120:
            raise ValueError("complete120-factor comparison mapping required")
        for expected, entry in zip(REFERENCE_NAMES, mapping, strict=True):
            if (
                type(entry) is not tuple
                or len(entry) != 2
                or type(entry[0]) is not str
                or entry[0] != expected
            ):
                raise ValueError("exact canonical120-name order required")
            _metric(entry[1], exact=exact)


def validate_reference_parity_receipt(result, *, expected_identity):
    """Validate bounded completeness against caller-supplied expected identity.

    CPU scalar/norm equality and retained fidelity bounds are checked; original
    runtime comparators still own raw logits, gradients, ordering, repeat parity,
    elementwise tolerance, preclip ordering, geometry and independent storage.
    Digest equality is not asset/source authentication or proof of execution.
    """
    _identity(expected_identity)
    if type(result) is not ReferenceParityReceipt:
        raise ValueError("typed separate q/v receipt required")
    _identity(result.identity)
    if (
        result.identity != expected_identity
        or type(result.seed) is not int
        or result.seed != PARITY_SEED
    ):
        raise ValueError(
            "expected source/base/fixture identity and fixed seed required"
        )
    cell = result.cell
    if (
        type(cell) is not ParityCell
        or cell.base_digest != result.identity.base_digest
        or type(cell.parameter_names) is not tuple
        or cell.parameter_names != REFERENCE_NAMES
        or type(cell.parameter_count) is not int
        or cell.parameter_count != 460800
        or type(cell.cases) is not tuple
        or len(cell.cases) != 18
    ):
        raise ValueError("complete separate q/v cell receipt required")
    exact = result.identity.source_device == "cpu"
    states = {}
    for position, case in enumerate(cell.cases):
        state, repeat = (("zero", 0), ("nonzero", 0), ("nonzero", 1))[position // 6]
        if (
            type(case) is not CaseComparison
            or type(case.state) is not str
            or case.state != state
            or type(case.repeat) is not int
            or case.repeat != repeat
            or type(case.fixture_index) is not int
            or case.fixture_index != position % 6
            or case.base_digest != result.identity.base_digest
        ):
            raise ValueError("fixed18-case schedule/base required")
        _pair(case.losses, exact=exact)
        _pair(case.scores, exact=exact)
        _sha(case.factor_digest)
        if state in states and states[state] != case.factor_digest:
            raise ValueError("same factor state required across fixtures/repeats")
        states[state] = case.factor_digest
    if states["zero"] == states["nonzero"]:
        raise ValueError("zero/nonzero factor state digests must differ")
    _pair(cell.pending_losses, exact=exact)
    _optimizer(cell.accumulation, exact=exact)
