from __future__ import annotations

import hashlib
import math
import re
import struct
from collections.abc import Callable
from dataclasses import dataclass
from decimal import (
    ROUND_CEILING,
    ROUND_FLOOR,
    Decimal,
    DivisionByZero,
    InvalidOperation,
    Overflow,
    Underflow,
    localcontext,
)
from enum import Enum
from functools import lru_cache
from typing import TypeAlias, cast

from .codec import canonical_json_bytes, strict_json_loads, validate_event_id
from .contracts import InputBoundaryError, JsonValue

_CALIBRATION_SPEC_SCHEMA = "aluclu.calibration-spec.v1"
_LABEL_PROVENANCE_MANIFEST_SCHEMA = "aluclu.label-provenance-manifest.v1"
_LABELED_RECALL_EXAMPLE_SCHEMA = "aluclu.labeled-recall-example.v1"
_CALIBRATION_SPEC_DOMAIN = b"aluclu.task2.calibration-spec.v1"
_LABEL_PROVENANCE_MANIFEST_DOMAIN = (
    b"aluclu.task2.label-provenance-manifest.v1"
)
_LABELED_RECALL_EXAMPLE_DOMAIN = b"aluclu.task2.labeled-recall-example.v1"
_CALIBRATION_SPEC_MAX_BYTES = 32_768
_LABEL_PROVENANCE_MANIFEST_MAX_BYTES = 2_097_152
_LABELED_RECALL_EXAMPLE_MAX_BYTES = 4_096
_MAX_MANIFEST_EXAMPLE_IDS = 4_096
_MAX_EXTERNAL_REFERENCE_BYTES = 2_048
_Q32_ONE = 1 << 32
_DIGEST_PATTERN = re.compile(r"[0-9a-f]{64}\Z")
_STRATUM_ID_PATTERN = re.compile(r"[A-Za-z0-9][A-Za-z0-9._:+-]{0,127}\Z")
_VERSION_ID_PATTERN = re.compile(r"[A-Za-z0-9][A-Za-z0-9._:+-]{0,255}\Z")
_OBSERVATION_ID_PATTERN = re.compile(r"obs:[A-Za-z0-9][A-Za-z0-9._:-]{0,251}\Z")
_CALIBRATION_SPEC_KEYS = frozenset(
    {
        "schema",
        "purpose",
        "query_stratum_id",
        "scorer_id",
        "normalizer_id",
        "feature_spec_id",
        "boundary_schema_id",
        "dataset_manifest_digest",
        "label_provenance_manifest_digest",
        "threshold_grid_q32",
        "minimum_margin_q32",
        "alpha_decimal",
        "delta_decimal",
        "minimum_selected",
        "minimum_coverage_decimal",
        "selection_rule",
    }
)
_LABEL_PROVENANCE_MANIFEST_KEYS = frozenset(
    {
        "schema",
        "issuer_id",
        "adjudication_method_id",
        "gold_source_digest",
        "dataset_manifest_digest",
        "scorer_input_manifest_digest",
        "gold_label_manifest_digest",
        "fit_example_ids",
        "calibration_example_ids",
        "external_evidence_reference",
        "external_signature_digest",
        "independence_status",
    }
)
_LABELED_RECALL_EXAMPLE_KEYS = frozenset(
    {
        "schema",
        "example_id",
        "calibration_spec_digest",
        "label_provenance_manifest_digest",
        "score_q32",
        "eligible",
        "target_observation_id",
        "predicted_observation_id",
        "error",
    }
)
_JsonObject: TypeAlias = dict[str, JsonValue]


class CalibrationPurpose(str, Enum):
    PERSONAL_MEMORY_TEXT = "personal_memory_text"


class ThresholdSelectionRule(str, Enum):
    MAX_COVERAGE_THEN_HIGHER_THRESHOLD = (
        "max_coverage_then_higher_threshold"
    )


class LabelIndependenceStatus(str, Enum):
    ASSERTED_NOT_PROVEN = "asserted_not_proven"


@dataclass(frozen=True, kw_only=True, slots=True)
class CalibrationSpecV1:
    purpose: CalibrationPurpose
    query_stratum_id: str
    scorer_id: str
    normalizer_id: str
    feature_spec_id: str
    boundary_schema_id: str
    dataset_manifest_digest: str
    label_provenance_manifest_digest: str
    threshold_grid_q32: tuple[int, ...]
    minimum_margin_q32: int
    alpha_decimal: str
    delta_decimal: str
    minimum_selected: int
    minimum_coverage_decimal: str
    selection_rule: ThresholdSelectionRule

    def __post_init__(self) -> None:
        if type(self.purpose) is not CalibrationPurpose:
            raise InputBoundaryError("purpose must be a CalibrationPurpose")
        _require_ascii_token(
            self.query_stratum_id,
            pattern=_STRATUM_ID_PATTERN,
            field_name="query_stratum_id",
        )
        for field_name, value in (
            ("scorer_id", self.scorer_id),
            ("normalizer_id", self.normalizer_id),
            ("feature_spec_id", self.feature_spec_id),
            ("boundary_schema_id", self.boundary_schema_id),
        ):
            _require_ascii_token(
                value,
                pattern=_VERSION_ID_PATTERN,
                field_name=field_name,
            )
        _require_digest(self.dataset_manifest_digest, "dataset_manifest_digest")
        _require_digest(
            self.label_provenance_manifest_digest,
            "label_provenance_manifest_digest",
        )
        _require_threshold_grid(self.threshold_grid_q32)
        _require_int(self.minimum_margin_q32, "minimum_margin_q32", 0, _Q32_ONE)
        _require_closed_probability(self.alpha_decimal, "alpha_decimal")
        _require_open_probability(self.delta_decimal, "delta_decimal")
        _require_int(
            self.minimum_selected,
            "minimum_selected",
            1,
            _MAX_SELECTED_EXAMPLES,
        )
        _require_closed_probability(
            self.minimum_coverage_decimal,
            "minimum_coverage_decimal",
        )
        if type(self.selection_rule) is not ThresholdSelectionRule:
            raise InputBoundaryError(
                "selection_rule must be a ThresholdSelectionRule"
            )


@dataclass(frozen=True, kw_only=True, slots=True)
class LabelProvenanceManifestV1:
    issuer_id: str
    adjudication_method_id: str
    gold_source_digest: str
    dataset_manifest_digest: str
    scorer_input_manifest_digest: str
    gold_label_manifest_digest: str
    fit_example_ids: tuple[str, ...]
    calibration_example_ids: tuple[str, ...]
    external_evidence_reference: str | None
    external_signature_digest: str | None
    independence_status: LabelIndependenceStatus

    def __post_init__(self) -> None:
        _require_event_id(self.issuer_id, "issuer_id")
        _require_ascii_token(
            self.adjudication_method_id,
            pattern=_STRATUM_ID_PATTERN,
            field_name="adjudication_method_id",
        )
        for field_name, value in (
            ("gold_source_digest", self.gold_source_digest),
            ("dataset_manifest_digest", self.dataset_manifest_digest),
            ("scorer_input_manifest_digest", self.scorer_input_manifest_digest),
            ("gold_label_manifest_digest", self.gold_label_manifest_digest),
        ):
            _require_digest(value, field_name)
        _require_sorted_event_ids(self.fit_example_ids, "fit_example_ids")
        _require_sorted_event_ids(
            self.calibration_example_ids,
            "calibration_example_ids",
        )
        if (
            len(self.fit_example_ids) + len(self.calibration_example_ids)
            > _MAX_MANIFEST_EXAMPLE_IDS
        ):
            raise InputBoundaryError(
                "manifest example IDs exceed the canonical payload boundary"
            )
        _require_optional_reference(self.external_evidence_reference)
        if self.external_signature_digest is not None:
            _require_digest(
                self.external_signature_digest,
                "external_signature_digest",
            )
        if type(self.independence_status) is not LabelIndependenceStatus:
            raise InputBoundaryError(
                "independence_status must be a LabelIndependenceStatus"
            )


@dataclass(frozen=True, kw_only=True, slots=True, init=False)
class LabeledRecallExampleV1:
    example_id: str
    calibration_spec_digest: str
    label_provenance_manifest_digest: str
    score_q32: int
    eligible: bool
    target_observation_id: str
    predicted_observation_id: str | None
    error: bool

    def __new__(cls) -> LabeledRecallExampleV1:
        raise TypeError("use labeled_recall_example")

    @classmethod
    def _create(
        cls,
        *,
        example_id: str,
        calibration_spec_digest: str,
        label_provenance_manifest_digest: str,
        score_q32: int,
        eligible: bool,
        target_observation_id: str,
        predicted_observation_id: str | None,
    ) -> LabeledRecallExampleV1:
        _require_event_id(example_id, "example_id")
        _require_digest(calibration_spec_digest, "calibration_spec_digest")
        _require_digest(
            label_provenance_manifest_digest,
            "label_provenance_manifest_digest",
        )
        _require_int(score_q32, "score_q32", 0, _Q32_ONE)
        if type(eligible) is not bool:
            raise InputBoundaryError("eligible must be a bool")
        _require_observation_id(target_observation_id, "target_observation_id")
        if predicted_observation_id is not None:
            _require_observation_id(
                predicted_observation_id,
                "predicted_observation_id",
            )

        instance = object.__new__(cls)
        object.__setattr__(instance, "example_id", example_id)
        object.__setattr__(
            instance,
            "calibration_spec_digest",
            calibration_spec_digest,
        )
        object.__setattr__(
            instance,
            "label_provenance_manifest_digest",
            label_provenance_manifest_digest,
        )
        object.__setattr__(instance, "score_q32", score_q32)
        object.__setattr__(instance, "eligible", eligible)
        object.__setattr__(
            instance,
            "target_observation_id",
            target_observation_id,
        )
        object.__setattr__(
            instance,
            "predicted_observation_id",
            predicted_observation_id,
        )
        object.__setattr__(
            instance,
            "error",
            predicted_observation_id != target_observation_id,
        )
        return instance


_CANONICAL_OPEN_PROBABILITY = re.compile(r"0\.(?:[0-9]*[1-9])\Z")
_CANONICAL_CLOSED_PROBABILITY = re.compile(
    r"(?:0|1|0\.(?:[0-9]*[1-9]))\Z"
)
_MAX_SELECTED_EXAMPLES = 65_536
_MAX_THRESHOLD_FAMILY = 256
_OUTPUT_DECIMAL_PLACES = 24
_SOLVER_DECIMAL_PLACES = 36
_MAX_PROBABILITY_FRACTIONAL_DIGITS = _SOLVER_DECIMAL_PLACES
_SOLVER_SCALE = 10**_SOLVER_DECIMAL_PLACES
_OUTPUT_SCALE = 10**_OUTPUT_DECIMAL_PLACES
_OUTPUT_GUARD_FACTOR = 10 ** (
    _SOLVER_DECIMAL_PLACES - _OUTPUT_DECIMAL_PLACES
)
_CDF_PRECISIONS = (80, 120, 160, 200, 240)
_DECIMAL_EMIN = -999_999_999
_DECIMAL_EMAX = 999_999_999


def clopper_pearson_upper_bound(
    *,
    error_count: int,
    selected_count: int,
    delta_decimal: str,
    family_size: int,
) -> str:
    """Return a Bonferroni-corrected one-sided upper risk bound.

    The result is the smallest canonical 24-place decimal-lattice value proven
    not to be below the continuous Clopper-Pearson root. No binary floating
    point or ambient Decimal context participates in the calculation.
    """

    _require_int(error_count, "error_count", 0, _MAX_SELECTED_EXAMPLES)
    _require_int(selected_count, "selected_count", 0, _MAX_SELECTED_EXAMPLES)
    if error_count > selected_count:
        raise InputBoundaryError("error_count cannot exceed selected_count")
    _require_int(family_size, "family_size", 1, _MAX_THRESHOLD_FAMILY)
    delta = _require_open_probability(delta_decimal, "delta_decimal")
    if selected_count == 0 or error_count == selected_count:
        return "1"
    return _solve_upper_bound(
        error_count,
        selected_count,
        delta.as_integer_ratio(),
        family_size,
    )


@lru_cache(maxsize=256)
def _solve_upper_bound(
    error_count: int,
    selected_count: int,
    delta_ratio: tuple[int, int],
    family_size: int,
) -> str:
    delta_numerator, delta_denominator = delta_ratio
    tail_numerator = delta_numerator
    tail_denominator = delta_denominator * family_size
    common = math.gcd(tail_numerator, tail_denominator)
    tail_numerator //= common
    tail_denominator //= common

    lower = 0
    upper = _SOLVER_SCALE
    while upper - lower > 1:
        midpoint = (lower + upper) // 2
        side = _classify_binomial_cdf(
            error_count=error_count,
            selected_count=selected_count,
            probability_units=midpoint,
            tail_numerator=tail_numerator,
            tail_denominator=tail_denominator,
        )
        if side > 0:
            lower = midpoint
        else:
            upper = midpoint

    output_units = (
        upper + _OUTPUT_GUARD_FACTOR - 1
    ) // _OUTPUT_GUARD_FACTOR
    return _canonical_output_probability(output_units)


def _classify_binomial_cdf(
    *,
    error_count: int,
    selected_count: int,
    probability_units: int,
    tail_numerator: int,
    tail_denominator: int,
) -> int:
    """Return 1 below the root and -1 at-or-above the root."""

    for precision in _CDF_PRECISIONS:
        lower = _binomial_cdf_directed(
            error_count=error_count,
            selected_count=selected_count,
            probability_units=probability_units,
            precision=precision,
            rounding=ROUND_FLOOR,
        )
        upper = _binomial_cdf_directed(
            error_count=error_count,
            selected_count=selected_count,
            probability_units=probability_units,
            precision=precision,
            rounding=ROUND_CEILING,
        )
        if _compare_decimal_to_ratio(lower, tail_numerator, tail_denominator) > 0:
            return 1
        if _compare_decimal_to_ratio(upper, tail_numerator, tail_denominator) <= 0:
            return -1

    return _compare_binomial_cdf_exact(
        error_count=error_count,
        selected_count=selected_count,
        probability_numerator=probability_units,
        probability_denominator=_SOLVER_SCALE,
        tail_numerator=tail_numerator,
        tail_denominator=tail_denominator,
    )


def _binomial_cdf_directed(
    *,
    error_count: int,
    selected_count: int,
    probability_units: int,
    precision: int,
    rounding: str,
) -> Decimal:
    if probability_units == 0:
        return Decimal(1)
    if probability_units == _SOLVER_SCALE:
        return Decimal(0)

    with localcontext() as context:
        context.prec = precision
        context.rounding = rounding
        context.Emin = _DECIMAL_EMIN
        context.Emax = _DECIMAL_EMAX
        for signal in (DivisionByZero, InvalidOperation, Overflow, Underflow):
            context.traps[signal] = True

        probability = context.scaleb(
            Decimal(probability_units),
            -_SOLVER_DECIMAL_PLACES,
        )
        complement = context.subtract(Decimal(1), probability)

        probability_power = _directed_power(
            probability,
            error_count,
            context.multiply,
        )
        complement_power = _directed_power(
            complement,
            selected_count - error_count,
            context.multiply,
        )
        term = context.multiply(
            Decimal(math.comb(selected_count, error_count)),
            context.multiply(probability_power, complement_power),
        )
        cumulative = term
        for index in range(error_count, 0, -1):
            numerator = context.multiply(
                context.multiply(term, Decimal(index)),
                complement,
            )
            denominator = context.multiply(
                Decimal(selected_count - index + 1),
                probability,
            )
            term = context.divide(numerator, denominator)
            cumulative = context.add(cumulative, term)

        if cumulative > 1:
            return Decimal(1)
        return cumulative


def _directed_power(
    base: Decimal,
    exponent: int,
    multiply: Callable[[Decimal, Decimal], Decimal],
) -> Decimal:
    result = Decimal(1)
    factor = base
    remaining = exponent
    while remaining:
        if remaining & 1:
            result = multiply(result, factor)
        remaining >>= 1
        if remaining:
            factor = multiply(factor, factor)
    return result


def _compare_binomial_cdf_exact(
    *,
    error_count: int,
    selected_count: int,
    probability_numerator: int,
    probability_denominator: int,
    tail_numerator: int,
    tail_denominator: int,
) -> int:
    common = math.gcd(probability_numerator, probability_denominator)
    probability_numerator //= common
    probability_denominator //= common
    complement_numerator = probability_denominator - probability_numerator
    if probability_numerator == 0:
        return 1
    if complement_numerator == 0:
        return -1

    term = complement_numerator**selected_count
    cdf_numerator = term
    for index in range(error_count):
        dividend = (
            term
            * (selected_count - index)
            * probability_numerator
        )
        divisor = (index + 1) * complement_numerator
        term, remainder = divmod(dividend, divisor)
        if remainder:
            raise AssertionError("exact binomial recurrence lost integrality")
        cdf_numerator += term

    left = cdf_numerator * tail_denominator
    right = tail_numerator * (probability_denominator**selected_count)
    return 1 if left > right else -1


def _compare_decimal_to_ratio(
    value: Decimal,
    numerator: int,
    denominator: int,
) -> int:
    value_numerator, value_denominator = value.as_integer_ratio()
    left = value_numerator * denominator
    right = numerator * value_denominator
    return (left > right) - (left < right)


def _canonical_output_probability(output_units: int) -> str:
    if output_units >= _OUTPUT_SCALE:
        return "1"
    fraction = f"{output_units:0{_OUTPUT_DECIMAL_PLACES}d}".rstrip("0")
    if not fraction:
        return "0"
    return f"0.{fraction}"


def _require_open_probability(value: object, field_name: str) -> Decimal:
    if (
        type(value) is not str
        or len(value) > 2 + _MAX_PROBABILITY_FRACTIONAL_DIGITS
        or _CANONICAL_OPEN_PROBABILITY.fullmatch(value) is None
    ):
        raise InputBoundaryError(f"{field_name} must be a canonical open probability")
    parsed = Decimal(value)
    if not Decimal(0) < parsed < Decimal(1):
        raise InputBoundaryError(f"{field_name} must be strictly between zero and one")
    return parsed


def _require_int(value: object, field_name: str, lower: int, upper: int) -> None:
    if type(value) is not int or not lower <= value <= upper:
        raise InputBoundaryError(f"{field_name} is outside its integer boundary")


def labeled_recall_example(
    *,
    example_id: str,
    calibration_spec_digest: str,
    label_provenance_manifest_digest: str,
    score_q32: int,
    eligible: bool,
    target_observation_id: str,
    predicted_observation_id: str | None,
) -> LabeledRecallExampleV1:
    return LabeledRecallExampleV1._create(
        example_id=example_id,
        calibration_spec_digest=calibration_spec_digest,
        label_provenance_manifest_digest=label_provenance_manifest_digest,
        score_q32=score_q32,
        eligible=eligible,
        target_observation_id=target_observation_id,
        predicted_observation_id=predicted_observation_id,
    )


def calibration_spec_to_json_value(spec: CalibrationSpecV1) -> _JsonObject:
    if type(spec) is not CalibrationSpecV1:
        raise InputBoundaryError("spec must be CalibrationSpecV1")
    return {
        "schema": _CALIBRATION_SPEC_SCHEMA,
        "purpose": spec.purpose.value,
        "query_stratum_id": spec.query_stratum_id,
        "scorer_id": spec.scorer_id,
        "normalizer_id": spec.normalizer_id,
        "feature_spec_id": spec.feature_spec_id,
        "boundary_schema_id": spec.boundary_schema_id,
        "dataset_manifest_digest": spec.dataset_manifest_digest,
        "label_provenance_manifest_digest": (
            spec.label_provenance_manifest_digest
        ),
        "threshold_grid_q32": list(spec.threshold_grid_q32),
        "minimum_margin_q32": spec.minimum_margin_q32,
        "alpha_decimal": spec.alpha_decimal,
        "delta_decimal": spec.delta_decimal,
        "minimum_selected": spec.minimum_selected,
        "minimum_coverage_decimal": spec.minimum_coverage_decimal,
        "selection_rule": spec.selection_rule.value,
    }


def calibration_spec_from_json_value(value: JsonValue) -> CalibrationSpecV1:
    wire = _require_object(
        value,
        keys=_CALIBRATION_SPEC_KEYS,
        schema=_CALIBRATION_SPEC_SCHEMA,
    )
    try:
        purpose = CalibrationPurpose(_required_str(wire, "purpose"))
    except ValueError as exc:
        raise InputBoundaryError("unknown calibration purpose") from exc
    try:
        selection_rule = ThresholdSelectionRule(
            _required_str(wire, "selection_rule")
        )
    except ValueError as exc:
        raise InputBoundaryError("unknown threshold selection rule") from exc
    return CalibrationSpecV1(
        purpose=purpose,
        query_stratum_id=_required_str(wire, "query_stratum_id"),
        scorer_id=_required_str(wire, "scorer_id"),
        normalizer_id=_required_str(wire, "normalizer_id"),
        feature_spec_id=_required_str(wire, "feature_spec_id"),
        boundary_schema_id=_required_str(wire, "boundary_schema_id"),
        dataset_manifest_digest=_required_str(
            wire,
            "dataset_manifest_digest",
        ),
        label_provenance_manifest_digest=_required_str(
            wire,
            "label_provenance_manifest_digest",
        ),
        threshold_grid_q32=_integer_tuple(wire, "threshold_grid_q32"),
        minimum_margin_q32=_required_int(wire, "minimum_margin_q32"),
        alpha_decimal=_required_str(wire, "alpha_decimal"),
        delta_decimal=_required_str(wire, "delta_decimal"),
        minimum_selected=_required_int(wire, "minimum_selected"),
        minimum_coverage_decimal=_required_str(
            wire,
            "minimum_coverage_decimal",
        ),
        selection_rule=selection_rule,
    )


def encode_calibration_spec(spec: CalibrationSpecV1) -> bytes:
    encoded = canonical_json_bytes(
        cast(JsonValue, calibration_spec_to_json_value(spec))
    )
    if len(encoded) > _CALIBRATION_SPEC_MAX_BYTES:
        raise InputBoundaryError("calibration spec exceeds 32768 bytes")
    return encoded


def decode_calibration_spec(data: bytes) -> CalibrationSpecV1:
    value = _decode_canonical_json(data, max_bytes=_CALIBRATION_SPEC_MAX_BYTES)
    return calibration_spec_from_json_value(value)


def derive_calibration_spec_digest(spec: CalibrationSpecV1) -> str:
    return _domain_digest(_CALIBRATION_SPEC_DOMAIN, encode_calibration_spec(spec))


def label_provenance_manifest_to_json_value(
    manifest: LabelProvenanceManifestV1,
) -> _JsonObject:
    if type(manifest) is not LabelProvenanceManifestV1:
        raise InputBoundaryError(
            "manifest must be LabelProvenanceManifestV1"
        )
    return {
        "schema": _LABEL_PROVENANCE_MANIFEST_SCHEMA,
        "issuer_id": manifest.issuer_id,
        "adjudication_method_id": manifest.adjudication_method_id,
        "gold_source_digest": manifest.gold_source_digest,
        "dataset_manifest_digest": manifest.dataset_manifest_digest,
        "scorer_input_manifest_digest": manifest.scorer_input_manifest_digest,
        "gold_label_manifest_digest": manifest.gold_label_manifest_digest,
        "fit_example_ids": list(manifest.fit_example_ids),
        "calibration_example_ids": list(manifest.calibration_example_ids),
        "external_evidence_reference": manifest.external_evidence_reference,
        "external_signature_digest": manifest.external_signature_digest,
        "independence_status": manifest.independence_status.value,
    }


def label_provenance_manifest_from_json_value(
    value: JsonValue,
) -> LabelProvenanceManifestV1:
    wire = _require_object(
        value,
        keys=_LABEL_PROVENANCE_MANIFEST_KEYS,
        schema=_LABEL_PROVENANCE_MANIFEST_SCHEMA,
    )
    try:
        independence_status = LabelIndependenceStatus(
            _required_str(wire, "independence_status")
        )
    except ValueError as exc:
        raise InputBoundaryError("unknown label independence status") from exc
    return LabelProvenanceManifestV1(
        issuer_id=_required_str(wire, "issuer_id"),
        adjudication_method_id=_required_str(wire, "adjudication_method_id"),
        gold_source_digest=_required_str(wire, "gold_source_digest"),
        dataset_manifest_digest=_required_str(wire, "dataset_manifest_digest"),
        scorer_input_manifest_digest=_required_str(
            wire,
            "scorer_input_manifest_digest",
        ),
        gold_label_manifest_digest=_required_str(
            wire,
            "gold_label_manifest_digest",
        ),
        fit_example_ids=_string_tuple(wire, "fit_example_ids"),
        calibration_example_ids=_string_tuple(
            wire,
            "calibration_example_ids",
        ),
        external_evidence_reference=_optional_str(
            wire,
            "external_evidence_reference",
        ),
        external_signature_digest=_optional_str(
            wire,
            "external_signature_digest",
        ),
        independence_status=independence_status,
    )


def encode_label_provenance_manifest(
    manifest: LabelProvenanceManifestV1,
) -> bytes:
    encoded = canonical_json_bytes(
        cast(JsonValue, label_provenance_manifest_to_json_value(manifest))
    )
    if len(encoded) > _LABEL_PROVENANCE_MANIFEST_MAX_BYTES:
        raise InputBoundaryError("label provenance manifest exceeds 2097152 bytes")
    return encoded


def decode_label_provenance_manifest(
    data: bytes,
) -> LabelProvenanceManifestV1:
    value = _decode_canonical_json(
        data,
        max_bytes=_LABEL_PROVENANCE_MANIFEST_MAX_BYTES,
    )
    return label_provenance_manifest_from_json_value(value)


def derive_label_provenance_manifest_digest(
    manifest: LabelProvenanceManifestV1,
) -> str:
    return _domain_digest(
        _LABEL_PROVENANCE_MANIFEST_DOMAIN,
        encode_label_provenance_manifest(manifest),
    )


def labeled_recall_example_to_json_value(
    example: LabeledRecallExampleV1,
) -> _JsonObject:
    if type(example) is not LabeledRecallExampleV1:
        raise InputBoundaryError("example must be LabeledRecallExampleV1")
    return {
        "schema": _LABELED_RECALL_EXAMPLE_SCHEMA,
        "example_id": example.example_id,
        "calibration_spec_digest": example.calibration_spec_digest,
        "label_provenance_manifest_digest": (
            example.label_provenance_manifest_digest
        ),
        "score_q32": example.score_q32,
        "eligible": example.eligible,
        "target_observation_id": example.target_observation_id,
        "predicted_observation_id": example.predicted_observation_id,
        "error": example.error,
    }


def labeled_recall_example_from_json_value(
    value: JsonValue,
) -> LabeledRecallExampleV1:
    wire = _require_object(
        value,
        keys=_LABELED_RECALL_EXAMPLE_KEYS,
        schema=_LABELED_RECALL_EXAMPLE_SCHEMA,
    )
    serialized_error = _required_bool(wire, "error")
    example = labeled_recall_example(
        example_id=_required_str(wire, "example_id"),
        calibration_spec_digest=_required_str(
            wire,
            "calibration_spec_digest",
        ),
        label_provenance_manifest_digest=_required_str(
            wire,
            "label_provenance_manifest_digest",
        ),
        score_q32=_required_int(wire, "score_q32"),
        eligible=_required_bool(wire, "eligible"),
        target_observation_id=_required_str(wire, "target_observation_id"),
        predicted_observation_id=_optional_str(
            wire,
            "predicted_observation_id",
        ),
    )
    if example.error is not serialized_error:
        raise InputBoundaryError("error does not match target/prediction IDs")
    return example


def encode_labeled_recall_example(example: LabeledRecallExampleV1) -> bytes:
    encoded = canonical_json_bytes(
        cast(JsonValue, labeled_recall_example_to_json_value(example))
    )
    if len(encoded) > _LABELED_RECALL_EXAMPLE_MAX_BYTES:
        raise InputBoundaryError("labeled recall example exceeds 4096 bytes")
    return encoded


def decode_labeled_recall_example(data: bytes) -> LabeledRecallExampleV1:
    value = _decode_canonical_json(
        data,
        max_bytes=_LABELED_RECALL_EXAMPLE_MAX_BYTES,
    )
    return labeled_recall_example_from_json_value(value)


def derive_labeled_recall_example_digest(
    example: LabeledRecallExampleV1,
) -> str:
    return _domain_digest(
        _LABELED_RECALL_EXAMPLE_DOMAIN,
        encode_labeled_recall_example(example),
    )


def _decode_canonical_json(data: bytes, *, max_bytes: int) -> JsonValue:
    if type(data) is not bytes:
        raise InputBoundaryError("JSON input must be bytes")
    if len(data) > max_bytes:
        raise InputBoundaryError("canonical input exceeds its byte boundary")
    value = strict_json_loads(data)
    if canonical_json_bytes(value) != data:
        raise InputBoundaryError("JSON bytes are not canonical")
    return value


def _require_object(
    value: JsonValue,
    *,
    keys: frozenset[str],
    schema: str,
) -> _JsonObject:
    if type(value) is not dict:
        raise InputBoundaryError("wire value must be an object")
    wire = cast(_JsonObject, value)
    if set(wire) != keys:
        raise InputBoundaryError("wire object has an invalid key set")
    if wire.get("schema") != schema:
        raise InputBoundaryError("wire object has an invalid schema")
    return wire


def _required_str(wire: _JsonObject, field_name: str) -> str:
    value = wire[field_name]
    if type(value) is not str:
        raise InputBoundaryError(f"{field_name} must be a string")
    return value


def _optional_str(wire: _JsonObject, field_name: str) -> str | None:
    value = wire[field_name]
    if value is not None and type(value) is not str:
        raise InputBoundaryError(f"{field_name} must be a string or null")
    return cast(str | None, value)


def _required_int(wire: _JsonObject, field_name: str) -> int:
    value = wire[field_name]
    if type(value) is not int:
        raise InputBoundaryError(f"{field_name} must be an integer")
    return value


def _required_bool(wire: _JsonObject, field_name: str) -> bool:
    value = wire[field_name]
    if type(value) is not bool:
        raise InputBoundaryError(f"{field_name} must be a bool")
    return value


def _string_tuple(wire: _JsonObject, field_name: str) -> tuple[str, ...]:
    value = wire[field_name]
    if type(value) is not list or any(type(item) is not str for item in value):
        raise InputBoundaryError(f"{field_name} must be an array of strings")
    return tuple(cast(list[str], value))


def _integer_tuple(wire: _JsonObject, field_name: str) -> tuple[int, ...]:
    value = wire[field_name]
    if type(value) is not list or any(type(item) is not int for item in value):
        raise InputBoundaryError(f"{field_name} must be an array of integers")
    return tuple(cast(list[int], value))


def _require_ascii_token(
    value: object,
    *,
    pattern: re.Pattern[str],
    field_name: str,
) -> str:
    if type(value) is not str:
        raise InputBoundaryError(f"{field_name} must be a string")
    try:
        value.encode("ascii")
    except UnicodeEncodeError as exc:
        raise InputBoundaryError(f"{field_name} must be ASCII") from exc
    if pattern.fullmatch(value) is None:
        raise InputBoundaryError(f"{field_name} is outside its canonical boundary")
    return value


def _require_event_id(value: object, field_name: str) -> str:
    if type(value) is not str:
        raise InputBoundaryError(f"{field_name} must be a string")
    try:
        return validate_event_id(value)
    except InputBoundaryError as exc:
        raise InputBoundaryError(
            f"{field_name} is outside its canonical boundary"
        ) from exc


def _require_observation_id(value: object, field_name: str) -> str:
    return _require_ascii_token(
        value,
        pattern=_OBSERVATION_ID_PATTERN,
        field_name=field_name,
    )


def _require_digest(value: object, field_name: str) -> str:
    if type(value) is not str or _DIGEST_PATTERN.fullmatch(value) is None:
        raise InputBoundaryError(f"{field_name} must be a lowercase SHA-256 digest")
    return value


def _require_threshold_grid(value: object) -> tuple[int, ...]:
    if type(value) is not tuple or not 1 <= len(value) <= _MAX_THRESHOLD_FAMILY:
        raise InputBoundaryError("threshold_grid_q32 must contain 1 to 256 values")
    for item in value:
        _require_int(item, "threshold_grid_q32 item", 0, _Q32_ONE)
    if any(left >= right for left, right in zip(value, value[1:])):
        raise InputBoundaryError("threshold_grid_q32 must be strictly increasing")
    return cast(tuple[int, ...], value)


def _require_sorted_event_ids(value: object, field_name: str) -> tuple[str, ...]:
    if type(value) is not tuple:
        raise InputBoundaryError(f"{field_name} must be a tuple")
    for item in value:
        _require_event_id(item, f"{field_name} item")
    if any(left >= right for left, right in zip(value, value[1:])):
        raise InputBoundaryError(f"{field_name} must be sorted and unique")
    return cast(tuple[str, ...], value)


def _require_optional_reference(value: object) -> str | None:
    if value is None:
        return None
    if type(value) is not str:
        raise InputBoundaryError(
            "external_evidence_reference must be a string or null"
        )
    try:
        encoded = value.encode("utf-8")
    except UnicodeEncodeError as exc:
        raise InputBoundaryError(
            "external_evidence_reference is not canonical UTF-8"
        ) from exc
    if not 1 <= len(encoded) <= _MAX_EXTERNAL_REFERENCE_BYTES:
        raise InputBoundaryError(
            "external_evidence_reference is outside its byte boundary"
        )
    return value


def _require_closed_probability(value: object, field_name: str) -> Decimal:
    if (
        type(value) is not str
        or len(value) > 2 + _MAX_PROBABILITY_FRACTIONAL_DIGITS
        or _CANONICAL_CLOSED_PROBABILITY.fullmatch(value) is None
    ):
        raise InputBoundaryError(f"{field_name} must be a canonical probability")
    return Decimal(value)


def _domain_digest(domain: bytes, payload: bytes) -> str:
    framed = (
        struct.pack(">Q", len(domain))
        + domain
        + struct.pack(">Q", len(payload))
        + payload
    )
    return hashlib.sha256(framed).hexdigest()
