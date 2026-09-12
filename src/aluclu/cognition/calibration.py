from __future__ import annotations

import hashlib
import hmac
import math
import re
import secrets
import struct
import weakref
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
_THRESHOLD_CALIBRATION_SCHEMA = "aluclu.threshold-calibration.v1"
_CALIBRATION_ARTIFACT_SCHEMA = "aluclu.calibration-artifact.v1"
_CALIBRATION_SPEC_DOMAIN = b"aluclu.task2.calibration-spec.v1"
_LABEL_PROVENANCE_MANIFEST_DOMAIN = (
    b"aluclu.task2.label-provenance-manifest.v1"
)
_LABELED_RECALL_EXAMPLE_DOMAIN = b"aluclu.task2.labeled-recall-example.v1"
_CALIBRATION_EXAMPLE_SET_DOMAIN = b"aluclu.task2.calibration-example-set.v1"
_CALIBRATION_ARTIFACT_DOMAIN = b"aluclu.task2.calibration-artifact.v1"
_CALIBRATION_PROFILE_DOMAIN = b"aluclu.task2.calibration-profile.v1"
_TEST_HARNESS_AUTH_DOMAIN = b"aluclu.task2.calibration-test-harness.v1"
_ACTIVE_PROFILE_AUTH_DOMAIN = b"aluclu.task2.active-calibration-profile.v1"
_CALIBRATION_SPEC_MAX_BYTES = 32_768
_LABEL_PROVENANCE_MANIFEST_MAX_BYTES = 2_097_152
_LABELED_RECALL_EXAMPLE_MAX_BYTES = 4_096
_CALIBRATION_ARTIFACT_MAX_BYTES = 262_144
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
_THRESHOLD_CALIBRATION_KEYS = frozenset(
    {
        "schema",
        "threshold_q32",
        "selected_count",
        "error_count",
        "total_example_count",
        "coverage_decimal",
        "risk_upper_bound_decimal",
        "passed",
    }
)
_CALIBRATION_ARTIFACT_KEYS = frozenset(
    {
        "schema",
        "spec_digest",
        "label_provenance_manifest_digest",
        "example_set_digest",
        "threshold_results",
        "chosen_threshold_q32",
        "statistical_status",
        "deployment_status",
        "disabled_reasons",
        "generator_version",
        "independence_status",
        "production_acceptance_digest",
        "artifact_digest",
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


class CalibrationStatisticalStatus(str, Enum):
    STATISTICAL_PASS = "statistical_pass"
    DISABLED = "disabled"


class CalibrationDeploymentStatus(str, Enum):
    TEST_ONLY = "test_only"
    PRODUCTION_ACCEPTED = "production_accepted"


class CalibrationDisabledReason(str, Enum):
    DATASET_MANIFEST_MISMATCH = "dataset_manifest_mismatch"
    EXAMPLE_SET_MISMATCH = "example_set_mismatch"
    FIT_CALIBRATION_OVERLAP = "fit_calibration_overlap"
    INSUFFICIENT_SELECTED = "insufficient_selected"
    LABEL_MANIFEST_DIGEST_MISMATCH = "label_manifest_digest_mismatch"
    LABEL_MANIFEST_LEAKAGE = "label_manifest_leakage"
    NO_PASSING_THRESHOLD = "no_passing_threshold"
    SPEC_DIGEST_MISMATCH = "spec_digest_mismatch"
    ZERO_EXAMPLES = "zero_examples"


class CalibrationActivationScope(str, Enum):
    PRODUCTION = "production"
    TEST_HARNESS = "test_harness"


class CalibrationProfileUnavailableReason(str, Enum):
    ARTIFACT_GATE_MISMATCH = "artifact_gate_mismatch"
    ARTIFACT_GRID_MISMATCH = "artifact_grid_mismatch"
    ARTIFACT_SELECTION_MISMATCH = "artifact_selection_mismatch"
    BOUNDARY_SCHEMA_MISMATCH = "boundary_schema_mismatch"
    DATASET_MANIFEST_MISMATCH = "dataset_manifest_mismatch"
    FEATURE_SPEC_MISMATCH = "feature_spec_mismatch"
    LABEL_MANIFEST_DIGEST_MISMATCH = "label_manifest_digest_mismatch"
    MISSING = "missing"
    NORMALIZER_MISMATCH = "normalizer_mismatch"
    PRODUCTION_ACCEPTANCE_UNTRUSTED = "production_acceptance_untrusted"
    PURPOSE_MISMATCH = "purpose_mismatch"
    QUERY_STRATUM_MISMATCH = "query_stratum_mismatch"
    SCORER_MISMATCH = "scorer_mismatch"
    SPEC_DIGEST_MISMATCH = "spec_digest_mismatch"
    STATISTICALLY_DISABLED = "statistically_disabled"
    TEST_ONLY_REQUIRES_EXPLICIT_HARNESS = (
        "test_only_requires_explicit_harness"
    )


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


@dataclass(frozen=True, kw_only=True, slots=True)
class ThresholdCalibrationV1:
    threshold_q32: int
    selected_count: int
    error_count: int
    total_example_count: int
    coverage_decimal: str
    risk_upper_bound_decimal: str
    passed: bool

    def __post_init__(self) -> None:
        _require_int(self.threshold_q32, "threshold_q32", 0, _Q32_ONE)
        _require_int(
            self.total_example_count,
            "total_example_count",
            0,
            _MAX_MANIFEST_EXAMPLE_IDS,
        )
        _require_int(
            self.selected_count,
            "selected_count",
            0,
            self.total_example_count,
        )
        _require_int(
            self.error_count,
            "error_count",
            0,
            self.selected_count,
        )
        _require_closed_probability(self.coverage_decimal, "coverage_decimal")
        if self.coverage_decimal != _coverage_decimal(
            self.selected_count,
            self.total_example_count,
        ):
            raise InputBoundaryError("coverage_decimal does not match counts")
        _require_closed_probability(
            self.risk_upper_bound_decimal,
            "risk_upper_bound_decimal",
        )
        if type(self.passed) is not bool:
            raise InputBoundaryError("passed must be a bool")


@dataclass(frozen=True, kw_only=True, slots=True, init=False)
class CalibrationArtifactV1:
    spec_digest: str
    label_provenance_manifest_digest: str
    example_set_digest: str
    threshold_results: tuple[ThresholdCalibrationV1, ...]
    chosen_threshold_q32: int | None
    statistical_status: CalibrationStatisticalStatus
    deployment_status: CalibrationDeploymentStatus
    disabled_reasons: tuple[CalibrationDisabledReason, ...]
    generator_version: str
    independence_status: LabelIndependenceStatus
    production_acceptance_digest: str | None
    artifact_digest: str

    def __new__(cls) -> CalibrationArtifactV1:
        raise TypeError("use build_calibration_artifact or decode_calibration_artifact")

    @classmethod
    def _create(
        cls,
        *,
        spec_digest: str,
        label_provenance_manifest_digest: str,
        example_set_digest: str,
        threshold_results: tuple[ThresholdCalibrationV1, ...],
        chosen_threshold_q32: int | None,
        statistical_status: CalibrationStatisticalStatus,
        deployment_status: CalibrationDeploymentStatus,
        disabled_reasons: tuple[CalibrationDisabledReason, ...],
        generator_version: str,
        independence_status: LabelIndependenceStatus,
        production_acceptance_digest: str | None,
        artifact_digest: str,
    ) -> CalibrationArtifactV1:
        _require_digest(spec_digest, "spec_digest")
        _require_digest(
            label_provenance_manifest_digest,
            "label_provenance_manifest_digest",
        )
        _require_digest(example_set_digest, "example_set_digest")
        _require_threshold_results(threshold_results)
        _require_optional_q32(chosen_threshold_q32, "chosen_threshold_q32")
        if type(statistical_status) is not CalibrationStatisticalStatus:
            raise InputBoundaryError(
                "statistical_status must be a CalibrationStatisticalStatus"
            )
        if type(deployment_status) is not CalibrationDeploymentStatus:
            raise InputBoundaryError(
                "deployment_status must be a CalibrationDeploymentStatus"
            )
        _require_disabled_reasons(disabled_reasons)
        _require_ascii_token(
            generator_version,
            pattern=_VERSION_ID_PATTERN,
            field_name="generator_version",
        )
        if generator_version != _CALIBRATION_GENERATOR_VERSION:
            raise InputBoundaryError("generator_version is not supported")
        if type(independence_status) is not LabelIndependenceStatus:
            raise InputBoundaryError(
                "independence_status must be a LabelIndependenceStatus"
            )
        if production_acceptance_digest is not None:
            _require_digest(
                production_acceptance_digest,
                "production_acceptance_digest",
            )
        _require_digest(artifact_digest, "artifact_digest")
        _validate_artifact_relations(
            threshold_results=threshold_results,
            chosen_threshold_q32=chosen_threshold_q32,
            statistical_status=statistical_status,
            deployment_status=deployment_status,
            disabled_reasons=disabled_reasons,
            production_acceptance_digest=production_acceptance_digest,
        )

        instance = object.__new__(cls)
        for field_name, value in (
            ("spec_digest", spec_digest),
            (
                "label_provenance_manifest_digest",
                label_provenance_manifest_digest,
            ),
            ("example_set_digest", example_set_digest),
            ("threshold_results", threshold_results),
            ("chosen_threshold_q32", chosen_threshold_q32),
            ("statistical_status", statistical_status),
            ("deployment_status", deployment_status),
            ("disabled_reasons", disabled_reasons),
            ("generator_version", generator_version),
            ("independence_status", independence_status),
            ("production_acceptance_digest", production_acceptance_digest),
            ("artifact_digest", artifact_digest),
        ):
            object.__setattr__(instance, field_name, value)
        return instance


@dataclass(frozen=True, kw_only=True, slots=True)
class CalibrationProfileV1:
    spec: CalibrationSpecV1
    artifact: CalibrationArtifactV1

    def __post_init__(self) -> None:
        if type(self.spec) is not CalibrationSpecV1:
            raise InputBoundaryError("spec must be CalibrationSpecV1")
        if type(self.artifact) is not CalibrationArtifactV1:
            raise InputBoundaryError("artifact must be CalibrationArtifactV1")


@dataclass(frozen=True, kw_only=True, slots=True)
class CalibrationCompatibilityRequirementsV1:
    purpose: CalibrationPurpose
    query_stratum_id: str
    scorer_id: str
    normalizer_id: str
    feature_spec_id: str
    boundary_schema_id: str
    dataset_manifest_digest: str

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


@dataclass(frozen=True, init=False)
class ExplicitCalibrationTestHarnessV1:
    __slots__ = ("_authenticator", "__weakref__")

    _authenticator: bytes

    def __new__(cls) -> ExplicitCalibrationTestHarnessV1:
        raise TypeError("use explicit_calibration_test_harness")

    @classmethod
    def _create(cls, *, authenticator: bytes) -> ExplicitCalibrationTestHarnessV1:
        instance = object.__new__(cls)
        object.__setattr__(instance, "_authenticator", authenticator)
        return instance


@dataclass(frozen=True, init=False)
class ActiveCalibrationProfileV1:
    __slots__ = (
        "profile_digest",
        "spec_digest",
        "artifact_digest",
        "purpose",
        "query_stratum_id",
        "scorer_id",
        "normalizer_id",
        "feature_spec_id",
        "boundary_schema_id",
        "dataset_manifest_digest",
        "minimum_score_q32",
        "minimum_margin_q32",
        "deployment_status",
        "activation_scope",
        "production_acceptance_digest",
        "_authenticator",
        "__weakref__",
    )

    profile_digest: str
    spec_digest: str
    artifact_digest: str
    purpose: CalibrationPurpose
    query_stratum_id: str
    scorer_id: str
    normalizer_id: str
    feature_spec_id: str
    boundary_schema_id: str
    dataset_manifest_digest: str
    minimum_score_q32: int
    minimum_margin_q32: int
    deployment_status: CalibrationDeploymentStatus
    activation_scope: CalibrationActivationScope
    production_acceptance_digest: str | None
    _authenticator: bytes

    def __new__(cls) -> ActiveCalibrationProfileV1:
        raise TypeError("use activate_calibration_profile")

    @classmethod
    def _create(
        cls,
        *,
        profile_digest: str,
        spec_digest: str,
        artifact_digest: str,
        purpose: CalibrationPurpose,
        query_stratum_id: str,
        scorer_id: str,
        normalizer_id: str,
        feature_spec_id: str,
        boundary_schema_id: str,
        dataset_manifest_digest: str,
        minimum_score_q32: int,
        minimum_margin_q32: int,
        deployment_status: CalibrationDeploymentStatus,
        activation_scope: CalibrationActivationScope,
        production_acceptance_digest: str | None,
        authenticator: bytes,
    ) -> ActiveCalibrationProfileV1:
        instance = object.__new__(cls)
        for field_name, value in (
            ("profile_digest", profile_digest),
            ("spec_digest", spec_digest),
            ("artifact_digest", artifact_digest),
            ("purpose", purpose),
            ("query_stratum_id", query_stratum_id),
            ("scorer_id", scorer_id),
            ("normalizer_id", normalizer_id),
            ("feature_spec_id", feature_spec_id),
            ("boundary_schema_id", boundary_schema_id),
            ("dataset_manifest_digest", dataset_manifest_digest),
            ("minimum_score_q32", minimum_score_q32),
            ("minimum_margin_q32", minimum_margin_q32),
            ("deployment_status", deployment_status),
            ("activation_scope", activation_scope),
            ("production_acceptance_digest", production_acceptance_digest),
            ("_authenticator", authenticator),
        ):
            object.__setattr__(instance, field_name, value)
        return instance


@dataclass(frozen=True, kw_only=True, slots=True)
class CalibrationProfileUnavailableV1:
    reason: CalibrationProfileUnavailableReason
    spec_digest: str | None
    artifact_digest: str | None

    def __post_init__(self) -> None:
        if type(self.reason) is not CalibrationProfileUnavailableReason:
            raise InputBoundaryError(
                "reason must be a CalibrationProfileUnavailableReason"
            )
        if self.spec_digest is not None:
            _require_digest(self.spec_digest, "spec_digest")
        if self.artifact_digest is not None:
            _require_digest(self.artifact_digest, "artifact_digest")


_TEST_HARNESS_SECRET = secrets.token_bytes(32)
_ACTIVE_PROFILE_SECRET = secrets.token_bytes(32)
_LIVE_TEST_HARNESSES: weakref.WeakValueDictionary[
    int, ExplicitCalibrationTestHarnessV1
] = weakref.WeakValueDictionary()
_LIVE_ACTIVE_PROFILES: weakref.WeakValueDictionary[
    int, ActiveCalibrationProfileV1
] = weakref.WeakValueDictionary()


_CANONICAL_OPEN_PROBABILITY = re.compile(r"0\.(?:[0-9]*[1-9])\Z")
_CANONICAL_CLOSED_PROBABILITY = re.compile(
    r"(?:0|1|0\.(?:[0-9]*[1-9]))\Z"
)
_MAX_SELECTED_EXAMPLES = 65_536
_MAX_THRESHOLD_FAMILY = 256
_OUTPUT_DECIMAL_PLACES = 24
_SOLVER_DECIMAL_PLACES = 36
_MAX_PROBABILITY_FRACTIONAL_DIGITS = _SOLVER_DECIMAL_PLACES
_CALIBRATION_GENERATOR_VERSION = (
    "aluclu.task2.calibration.clopper-pearson-q24.v1"
)
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


def build_calibration_artifact(
    spec: CalibrationSpecV1,
    manifest: LabelProvenanceManifestV1,
    examples: tuple[LabeledRecallExampleV1, ...],
) -> CalibrationArtifactV1:
    if type(spec) is not CalibrationSpecV1:
        raise InputBoundaryError("spec must be CalibrationSpecV1")
    if type(manifest) is not LabelProvenanceManifestV1:
        raise InputBoundaryError("manifest must be LabelProvenanceManifestV1")
    if type(examples) is not tuple or any(
        type(example) is not LabeledRecallExampleV1 for example in examples
    ):
        raise InputBoundaryError(
            "examples must be a tuple of LabeledRecallExampleV1"
        )
    if len(examples) > _MAX_MANIFEST_EXAMPLE_IDS:
        raise InputBoundaryError("examples exceed the calibration set boundary")

    ordered_examples = tuple(
        sorted(
            examples,
            key=lambda example: (
                example.example_id,
                encode_labeled_recall_example(example),
            ),
        )
    )
    spec_digest = derive_calibration_spec_digest(spec)
    manifest_digest = derive_label_provenance_manifest_digest(manifest)
    reasons: set[CalibrationDisabledReason] = set()

    if not ordered_examples or not manifest.calibration_example_ids:
        reasons.add(CalibrationDisabledReason.ZERO_EXAMPLES)
    if spec.dataset_manifest_digest != manifest.dataset_manifest_digest:
        reasons.add(CalibrationDisabledReason.DATASET_MANIFEST_MISMATCH)
    if spec.label_provenance_manifest_digest != manifest_digest:
        reasons.add(CalibrationDisabledReason.LABEL_MANIFEST_DIGEST_MISMATCH)
    if set(manifest.fit_example_ids).intersection(
        manifest.calibration_example_ids
    ):
        reasons.add(CalibrationDisabledReason.FIT_CALIBRATION_OVERLAP)
    if manifest.scorer_input_manifest_digest == manifest.gold_label_manifest_digest:
        reasons.add(CalibrationDisabledReason.LABEL_MANIFEST_LEAKAGE)

    actual_example_ids = tuple(example.example_id for example in ordered_examples)
    if actual_example_ids != manifest.calibration_example_ids:
        reasons.add(CalibrationDisabledReason.EXAMPLE_SET_MISMATCH)
    if any(
        example.calibration_spec_digest != spec_digest
        for example in ordered_examples
    ):
        reasons.add(CalibrationDisabledReason.SPEC_DIGEST_MISMATCH)
    if any(
        example.label_provenance_manifest_digest != manifest_digest
        for example in ordered_examples
    ):
        reasons.add(CalibrationDisabledReason.LABEL_MANIFEST_DIGEST_MISMATCH)

    threshold_results = tuple(
        _calibrate_threshold(
            threshold_q32=threshold_q32,
            examples=ordered_examples,
            spec=spec,
        )
        for threshold_q32 in spec.threshold_grid_q32
    )
    passing = tuple(result for result in threshold_results if result.passed)
    if not any(
        result.selected_count >= spec.minimum_selected
        for result in threshold_results
    ):
        reasons.add(CalibrationDisabledReason.INSUFFICIENT_SELECTED)
    if not passing:
        reasons.add(CalibrationDisabledReason.NO_PASSING_THRESHOLD)

    disabled_reasons = tuple(sorted(reasons, key=lambda reason: reason.value))
    if disabled_reasons:
        chosen_threshold_q32 = None
        statistical_status = CalibrationStatisticalStatus.DISABLED
    else:
        chosen = max(
            passing,
            key=lambda result: (result.selected_count, result.threshold_q32),
        )
        chosen_threshold_q32 = chosen.threshold_q32
        statistical_status = CalibrationStatisticalStatus.STATISTICAL_PASS

    example_set_digest = _derive_example_set_digest(ordered_examples)
    deployment_status = CalibrationDeploymentStatus.TEST_ONLY
    production_acceptance_digest = None
    artifact_digest = _derive_artifact_fields_digest(
        spec_digest=spec_digest,
        label_provenance_manifest_digest=manifest_digest,
        example_set_digest=example_set_digest,
        threshold_results=threshold_results,
        chosen_threshold_q32=chosen_threshold_q32,
        statistical_status=statistical_status,
        deployment_status=deployment_status,
        disabled_reasons=disabled_reasons,
        generator_version=_CALIBRATION_GENERATOR_VERSION,
        independence_status=manifest.independence_status,
        production_acceptance_digest=production_acceptance_digest,
    )
    return CalibrationArtifactV1._create(
        spec_digest=spec_digest,
        label_provenance_manifest_digest=manifest_digest,
        example_set_digest=example_set_digest,
        threshold_results=threshold_results,
        chosen_threshold_q32=chosen_threshold_q32,
        statistical_status=statistical_status,
        deployment_status=deployment_status,
        disabled_reasons=disabled_reasons,
        generator_version=_CALIBRATION_GENERATOR_VERSION,
        independence_status=manifest.independence_status,
        production_acceptance_digest=production_acceptance_digest,
        artifact_digest=artifact_digest,
    )


def threshold_calibration_to_json_value(
    result: ThresholdCalibrationV1,
) -> _JsonObject:
    if type(result) is not ThresholdCalibrationV1:
        raise InputBoundaryError("result must be ThresholdCalibrationV1")
    return {
        "schema": _THRESHOLD_CALIBRATION_SCHEMA,
        "threshold_q32": result.threshold_q32,
        "selected_count": result.selected_count,
        "error_count": result.error_count,
        "total_example_count": result.total_example_count,
        "coverage_decimal": result.coverage_decimal,
        "risk_upper_bound_decimal": result.risk_upper_bound_decimal,
        "passed": result.passed,
    }


def threshold_calibration_from_json_value(
    value: JsonValue,
) -> ThresholdCalibrationV1:
    wire = _require_object(
        value,
        keys=_THRESHOLD_CALIBRATION_KEYS,
        schema=_THRESHOLD_CALIBRATION_SCHEMA,
    )
    return ThresholdCalibrationV1(
        threshold_q32=_required_int(wire, "threshold_q32"),
        selected_count=_required_int(wire, "selected_count"),
        error_count=_required_int(wire, "error_count"),
        total_example_count=_required_int(wire, "total_example_count"),
        coverage_decimal=_required_str(wire, "coverage_decimal"),
        risk_upper_bound_decimal=_required_str(
            wire,
            "risk_upper_bound_decimal",
        ),
        passed=_required_bool(wire, "passed"),
    )


def calibration_artifact_to_json_value(
    artifact: CalibrationArtifactV1,
) -> _JsonObject:
    if type(artifact) is not CalibrationArtifactV1:
        raise InputBoundaryError("artifact must be CalibrationArtifactV1")
    wire = _artifact_body_wire(
        spec_digest=artifact.spec_digest,
        label_provenance_manifest_digest=(
            artifact.label_provenance_manifest_digest
        ),
        example_set_digest=artifact.example_set_digest,
        threshold_results=artifact.threshold_results,
        chosen_threshold_q32=artifact.chosen_threshold_q32,
        statistical_status=artifact.statistical_status,
        deployment_status=artifact.deployment_status,
        disabled_reasons=artifact.disabled_reasons,
        generator_version=artifact.generator_version,
        independence_status=artifact.independence_status,
        production_acceptance_digest=artifact.production_acceptance_digest,
    )
    wire["artifact_digest"] = artifact.artifact_digest
    return wire


def calibration_artifact_from_json_value(
    value: JsonValue,
) -> CalibrationArtifactV1:
    wire = _require_object(
        value,
        keys=_CALIBRATION_ARTIFACT_KEYS,
        schema=_CALIBRATION_ARTIFACT_SCHEMA,
    )
    raw_results = wire["threshold_results"]
    if type(raw_results) is not list:
        raise InputBoundaryError("threshold_results must be an array")
    threshold_results = tuple(
        threshold_calibration_from_json_value(item) for item in raw_results
    )
    try:
        statistical_status = CalibrationStatisticalStatus(
            _required_str(wire, "statistical_status")
        )
    except ValueError as exc:
        raise InputBoundaryError("unknown calibration statistical status") from exc
    try:
        deployment_status = CalibrationDeploymentStatus(
            _required_str(wire, "deployment_status")
        )
    except ValueError as exc:
        raise InputBoundaryError("unknown calibration deployment status") from exc
    disabled_reasons = _disabled_reason_tuple(wire, "disabled_reasons")
    try:
        independence_status = LabelIndependenceStatus(
            _required_str(wire, "independence_status")
        )
    except ValueError as exc:
        raise InputBoundaryError("unknown label independence status") from exc

    artifact = CalibrationArtifactV1._create(
        spec_digest=_required_str(wire, "spec_digest"),
        label_provenance_manifest_digest=_required_str(
            wire,
            "label_provenance_manifest_digest",
        ),
        example_set_digest=_required_str(wire, "example_set_digest"),
        threshold_results=threshold_results,
        chosen_threshold_q32=_optional_int(wire, "chosen_threshold_q32"),
        statistical_status=statistical_status,
        deployment_status=deployment_status,
        disabled_reasons=disabled_reasons,
        generator_version=_required_str(wire, "generator_version"),
        independence_status=independence_status,
        production_acceptance_digest=_optional_str(
            wire,
            "production_acceptance_digest",
        ),
        artifact_digest=_required_str(wire, "artifact_digest"),
    )
    if derive_calibration_artifact_digest(artifact) != artifact.artifact_digest:
        raise InputBoundaryError("calibration artifact digest does not verify")
    return artifact


def encode_calibration_artifact(artifact: CalibrationArtifactV1) -> bytes:
    if derive_calibration_artifact_digest(artifact) != artifact.artifact_digest:
        raise InputBoundaryError("calibration artifact digest does not verify")
    encoded = canonical_json_bytes(
        cast(JsonValue, calibration_artifact_to_json_value(artifact))
    )
    if len(encoded) > _CALIBRATION_ARTIFACT_MAX_BYTES:
        raise InputBoundaryError("calibration artifact exceeds 262144 bytes")
    return encoded


def decode_calibration_artifact(data: bytes) -> CalibrationArtifactV1:
    value = _decode_canonical_json(
        data,
        max_bytes=_CALIBRATION_ARTIFACT_MAX_BYTES,
    )
    return calibration_artifact_from_json_value(value)


def derive_calibration_artifact_digest(
    artifact: CalibrationArtifactV1,
) -> str:
    if type(artifact) is not CalibrationArtifactV1:
        raise InputBoundaryError("artifact must be CalibrationArtifactV1")
    return _derive_artifact_fields_digest(
        spec_digest=artifact.spec_digest,
        label_provenance_manifest_digest=(
            artifact.label_provenance_manifest_digest
        ),
        example_set_digest=artifact.example_set_digest,
        threshold_results=artifact.threshold_results,
        chosen_threshold_q32=artifact.chosen_threshold_q32,
        statistical_status=artifact.statistical_status,
        deployment_status=artifact.deployment_status,
        disabled_reasons=artifact.disabled_reasons,
        generator_version=artifact.generator_version,
        independence_status=artifact.independence_status,
        production_acceptance_digest=artifact.production_acceptance_digest,
    )


def explicit_calibration_test_harness() -> ExplicitCalibrationTestHarnessV1:
    authenticator = hmac.digest(
        _TEST_HARNESS_SECRET,
        _TEST_HARNESS_AUTH_DOMAIN,
        "sha256",
    )
    harness = ExplicitCalibrationTestHarnessV1._create(
        authenticator=authenticator,
    )
    _LIVE_TEST_HARNESSES[id(harness)] = harness
    return harness


def activate_calibration_profile(
    profile: CalibrationProfileV1 | None,
    requirements: CalibrationCompatibilityRequirementsV1,
    *,
    test_harness: ExplicitCalibrationTestHarnessV1 | None = None,
) -> ActiveCalibrationProfileV1 | CalibrationProfileUnavailableV1:
    _validate_compatibility_requirements_instance(requirements)
    if test_harness is not None:
        _validate_test_harness(test_harness)
    if profile is None:
        return CalibrationProfileUnavailableV1(
            reason=CalibrationProfileUnavailableReason.MISSING,
            spec_digest=None,
            artifact_digest=None,
        )
    _validate_profile_instance(profile)

    spec = profile.spec
    artifact = profile.artifact
    _validate_spec_instance(spec)
    _validate_artifact_instance(artifact)
    spec_digest = derive_calibration_spec_digest(spec)
    if artifact.deployment_status is CalibrationDeploymentStatus.TEST_ONLY:
        if test_harness is None:
            return _profile_unavailable(
                CalibrationProfileUnavailableReason.TEST_ONLY_REQUIRES_EXPLICIT_HARNESS,
                spec_digest=spec_digest,
                artifact=artifact,
            )
    else:
        return _profile_unavailable(
            CalibrationProfileUnavailableReason.PRODUCTION_ACCEPTANCE_UNTRUSTED,
            spec_digest=spec_digest,
            artifact=artifact,
        )

    unavailable = _profile_semantic_unavailability(
        spec=spec,
        artifact=artifact,
        spec_digest=spec_digest,
    )
    if unavailable is not None:
        return unavailable
    if artifact.statistical_status is CalibrationStatisticalStatus.DISABLED:
        return _profile_unavailable(
            CalibrationProfileUnavailableReason.STATISTICALLY_DISABLED,
            spec_digest=spec_digest,
            artifact=artifact,
        )

    compatibility_reason = _compatibility_unavailability(spec, requirements)
    if compatibility_reason is not None:
        return _profile_unavailable(
            compatibility_reason,
            spec_digest=spec_digest,
            artifact=artifact,
        )

    activation_scope = CalibrationActivationScope.TEST_HARNESS

    chosen_threshold = artifact.chosen_threshold_q32
    if chosen_threshold is None:
        raise InputBoundaryError(
            "statistically enabled artifact has no chosen threshold"
        )
    profile_digest = _derive_profile_digest(
        activation_scope=activation_scope,
        artifact_digest=artifact.artifact_digest,
        spec_digest=spec_digest,
    )
    fields = _active_profile_authentication_fields(
        profile_digest=profile_digest,
        spec_digest=spec_digest,
        artifact_digest=artifact.artifact_digest,
        purpose=spec.purpose,
        query_stratum_id=spec.query_stratum_id,
        scorer_id=spec.scorer_id,
        normalizer_id=spec.normalizer_id,
        feature_spec_id=spec.feature_spec_id,
        boundary_schema_id=spec.boundary_schema_id,
        dataset_manifest_digest=spec.dataset_manifest_digest,
        minimum_score_q32=chosen_threshold,
        minimum_margin_q32=spec.minimum_margin_q32,
        deployment_status=artifact.deployment_status,
        activation_scope=activation_scope,
        production_acceptance_digest=artifact.production_acceptance_digest,
    )
    authenticator = _authenticate_active_profile_fields(fields)
    active = ActiveCalibrationProfileV1._create(
        profile_digest=profile_digest,
        spec_digest=spec_digest,
        artifact_digest=artifact.artifact_digest,
        purpose=spec.purpose,
        query_stratum_id=spec.query_stratum_id,
        scorer_id=spec.scorer_id,
        normalizer_id=spec.normalizer_id,
        feature_spec_id=spec.feature_spec_id,
        boundary_schema_id=spec.boundary_schema_id,
        dataset_manifest_digest=spec.dataset_manifest_digest,
        minimum_score_q32=chosen_threshold,
        minimum_margin_q32=spec.minimum_margin_q32,
        deployment_status=artifact.deployment_status,
        activation_scope=activation_scope,
        production_acceptance_digest=artifact.production_acceptance_digest,
        authenticator=authenticator,
    )
    _LIVE_ACTIVE_PROFILES[id(active)] = active
    return active


def _validate_test_harness(harness: object) -> None:
    if type(harness) is not ExplicitCalibrationTestHarnessV1:
        raise InputBoundaryError("test harness capability is invalid")
    typed = cast(ExplicitCalibrationTestHarnessV1, harness)
    if _LIVE_TEST_HARNESSES.get(id(typed)) is not typed:
        raise InputBoundaryError("test harness capability is invalid")
    expected = hmac.digest(
        _TEST_HARNESS_SECRET,
        _TEST_HARNESS_AUTH_DOMAIN,
        "sha256",
    )
    try:
        authenticator = typed._authenticator
    except AttributeError as exc:
        raise InputBoundaryError("test harness capability is invalid") from exc
    if type(authenticator) is not bytes or not hmac.compare_digest(
        authenticator,
        expected,
    ):
        raise InputBoundaryError("test harness capability is invalid")


def _validate_active_calibration_profile(profile: object) -> None:
    if type(profile) is not ActiveCalibrationProfileV1:
        raise InputBoundaryError("active calibration profile is invalid")
    typed = cast(ActiveCalibrationProfileV1, profile)
    if _LIVE_ACTIVE_PROFILES.get(id(typed)) is not typed:
        raise InputBoundaryError("active calibration profile is invalid")
    try:
        _validate_active_profile_fields(typed)
        expected_profile_digest = _derive_profile_digest(
            activation_scope=typed.activation_scope,
            artifact_digest=typed.artifact_digest,
            spec_digest=typed.spec_digest,
        )
        fields = _active_profile_authentication_fields(
            profile_digest=typed.profile_digest,
            spec_digest=typed.spec_digest,
            artifact_digest=typed.artifact_digest,
            purpose=typed.purpose,
            query_stratum_id=typed.query_stratum_id,
            scorer_id=typed.scorer_id,
            normalizer_id=typed.normalizer_id,
            feature_spec_id=typed.feature_spec_id,
            boundary_schema_id=typed.boundary_schema_id,
            dataset_manifest_digest=typed.dataset_manifest_digest,
            minimum_score_q32=typed.minimum_score_q32,
            minimum_margin_q32=typed.minimum_margin_q32,
            deployment_status=typed.deployment_status,
            activation_scope=typed.activation_scope,
            production_acceptance_digest=typed.production_acceptance_digest,
        )
        expected = _authenticate_active_profile_fields(fields)
        authenticator = typed._authenticator
    except (AttributeError, InputBoundaryError, TypeError, ValueError) as exc:
        raise InputBoundaryError("active calibration profile is invalid") from exc
    if (
        typed.profile_digest != expected_profile_digest
        or not hmac.compare_digest(authenticator, expected)
    ):
        raise InputBoundaryError("active calibration profile is invalid")


def _validate_active_profile_fields(profile: ActiveCalibrationProfileV1) -> None:
    for field_name, value in (
        ("profile_digest", profile.profile_digest),
        ("spec_digest", profile.spec_digest),
        ("artifact_digest", profile.artifact_digest),
        ("dataset_manifest_digest", profile.dataset_manifest_digest),
    ):
        _require_digest(value, field_name)
    if type(profile.purpose) is not CalibrationPurpose:
        raise InputBoundaryError("purpose must be a CalibrationPurpose")
    for field_name, value, pattern in (
        ("query_stratum_id", profile.query_stratum_id, _STRATUM_ID_PATTERN),
        ("scorer_id", profile.scorer_id, _VERSION_ID_PATTERN),
        ("normalizer_id", profile.normalizer_id, _VERSION_ID_PATTERN),
        ("feature_spec_id", profile.feature_spec_id, _VERSION_ID_PATTERN),
        ("boundary_schema_id", profile.boundary_schema_id, _VERSION_ID_PATTERN),
    ):
        _require_ascii_token(value, pattern=pattern, field_name=field_name)
    _require_int(profile.minimum_score_q32, "minimum_score_q32", 0, _Q32_ONE)
    _require_int(profile.minimum_margin_q32, "minimum_margin_q32", 0, _Q32_ONE)
    if type(profile.deployment_status) is not CalibrationDeploymentStatus:
        raise InputBoundaryError(
            "deployment_status must be a CalibrationDeploymentStatus"
        )
    if type(profile.activation_scope) is not CalibrationActivationScope:
        raise InputBoundaryError(
            "activation_scope must be a CalibrationActivationScope"
        )
    if profile.production_acceptance_digest is not None:
        _require_digest(
            profile.production_acceptance_digest,
            "production_acceptance_digest",
        )
    if (
        profile.activation_scope is CalibrationActivationScope.TEST_HARNESS
        and (
            profile.deployment_status is not CalibrationDeploymentStatus.TEST_ONLY
            or profile.production_acceptance_digest is not None
        )
    ):
        raise InputBoundaryError("test profile has invalid deployment binding")
    if (
        profile.activation_scope is CalibrationActivationScope.PRODUCTION
        and (
            profile.deployment_status
            is not CalibrationDeploymentStatus.PRODUCTION_ACCEPTED
            or profile.production_acceptance_digest is None
        )
    ):
        raise InputBoundaryError("production profile has invalid deployment binding")
    if type(profile._authenticator) is not bytes:
        raise InputBoundaryError("authenticator must be bytes")


def _validate_spec_instance(spec: CalibrationSpecV1) -> None:
    if type(spec) is not CalibrationSpecV1:
        raise InputBoundaryError("spec must be CalibrationSpecV1")
    try:
        if decode_calibration_spec(encode_calibration_spec(spec)) != spec:
            raise InputBoundaryError("calibration spec does not round trip")
    except InputBoundaryError:
        raise
    except (AttributeError, KeyError, OverflowError, TypeError, ValueError) as exc:
        raise InputBoundaryError("calibration spec is invalid") from exc


def _validate_artifact_instance(artifact: CalibrationArtifactV1) -> None:
    if type(artifact) is not CalibrationArtifactV1:
        raise InputBoundaryError("artifact must be CalibrationArtifactV1")
    try:
        if (
            decode_calibration_artifact(encode_calibration_artifact(artifact))
            != artifact
        ):
            raise InputBoundaryError("calibration artifact does not round trip")
    except InputBoundaryError:
        raise
    except (AttributeError, KeyError, OverflowError, TypeError, ValueError) as exc:
        raise InputBoundaryError("calibration artifact is invalid") from exc


def _validate_profile_instance(profile: object) -> None:
    if type(profile) is not CalibrationProfileV1:
        raise InputBoundaryError("profile must be CalibrationProfileV1 or None")
    typed = cast(CalibrationProfileV1, profile)
    try:
        typed.__post_init__()
    except InputBoundaryError:
        raise
    except (AttributeError, TypeError) as exc:
        raise InputBoundaryError("calibration profile is invalid") from exc


def _validate_compatibility_requirements_instance(requirements: object) -> None:
    if type(requirements) is not CalibrationCompatibilityRequirementsV1:
        raise InputBoundaryError(
            "requirements must be CalibrationCompatibilityRequirementsV1"
        )
    typed = cast(CalibrationCompatibilityRequirementsV1, requirements)
    try:
        typed.__post_init__()
    except InputBoundaryError:
        raise
    except (AttributeError, TypeError) as exc:
        raise InputBoundaryError("calibration requirements are invalid") from exc


def _profile_semantic_unavailability(
    *,
    spec: CalibrationSpecV1,
    artifact: CalibrationArtifactV1,
    spec_digest: str,
) -> CalibrationProfileUnavailableV1 | None:
    if artifact.spec_digest != spec_digest:
        return _profile_unavailable(
            CalibrationProfileUnavailableReason.SPEC_DIGEST_MISMATCH,
            spec_digest=spec_digest,
            artifact=artifact,
        )
    if (
        artifact.label_provenance_manifest_digest
        != spec.label_provenance_manifest_digest
    ):
        return _profile_unavailable(
            CalibrationProfileUnavailableReason.LABEL_MANIFEST_DIGEST_MISMATCH,
            spec_digest=spec_digest,
            artifact=artifact,
        )
    if (
        tuple(row.threshold_q32 for row in artifact.threshold_results)
        != spec.threshold_grid_q32
    ):
        return _profile_unavailable(
            CalibrationProfileUnavailableReason.ARTIFACT_GRID_MISMATCH,
            spec_digest=spec_digest,
            artifact=artifact,
        )

    expected_passes: list[bool] = []
    for row in artifact.threshold_results:
        expected_coverage = _coverage_decimal(
            row.selected_count,
            row.total_example_count,
        )
        expected_risk = clopper_pearson_upper_bound(
            error_count=row.error_count,
            selected_count=row.selected_count,
            delta_decimal=spec.delta_decimal,
            family_size=len(spec.threshold_grid_q32),
        )
        expected_passed = (
            row.selected_count >= spec.minimum_selected
            and Decimal(expected_coverage)
            >= Decimal(spec.minimum_coverage_decimal)
            and Decimal(expected_risk) <= Decimal(spec.alpha_decimal)
        )
        expected_passes.append(expected_passed)
        if (
            row.coverage_decimal != expected_coverage
            or row.risk_upper_bound_decimal != expected_risk
            or row.passed is not expected_passed
        ):
            return _profile_unavailable(
                CalibrationProfileUnavailableReason.ARTIFACT_GATE_MISMATCH,
                spec_digest=spec_digest,
                artifact=artifact,
            )

    if artifact.statistical_status is CalibrationStatisticalStatus.STATISTICAL_PASS:
        passing = tuple(
            row
            for row, passed in zip(artifact.threshold_results, expected_passes)
            if passed
        )
        expected_choice = max(
            passing,
            key=lambda row: (row.selected_count, row.threshold_q32),
        ).threshold_q32
        if artifact.chosen_threshold_q32 != expected_choice:
            return _profile_unavailable(
                CalibrationProfileUnavailableReason.ARTIFACT_SELECTION_MISMATCH,
                spec_digest=spec_digest,
                artifact=artifact,
            )
    return None


def _compatibility_unavailability(
    spec: CalibrationSpecV1,
    requirements: CalibrationCompatibilityRequirementsV1,
) -> CalibrationProfileUnavailableReason | None:
    comparisons = (
        (
            spec.purpose,
            requirements.purpose,
            CalibrationProfileUnavailableReason.PURPOSE_MISMATCH,
        ),
        (
            spec.query_stratum_id,
            requirements.query_stratum_id,
            CalibrationProfileUnavailableReason.QUERY_STRATUM_MISMATCH,
        ),
        (
            spec.scorer_id,
            requirements.scorer_id,
            CalibrationProfileUnavailableReason.SCORER_MISMATCH,
        ),
        (
            spec.normalizer_id,
            requirements.normalizer_id,
            CalibrationProfileUnavailableReason.NORMALIZER_MISMATCH,
        ),
        (
            spec.feature_spec_id,
            requirements.feature_spec_id,
            CalibrationProfileUnavailableReason.FEATURE_SPEC_MISMATCH,
        ),
        (
            spec.boundary_schema_id,
            requirements.boundary_schema_id,
            CalibrationProfileUnavailableReason.BOUNDARY_SCHEMA_MISMATCH,
        ),
        (
            spec.dataset_manifest_digest,
            requirements.dataset_manifest_digest,
            CalibrationProfileUnavailableReason.DATASET_MANIFEST_MISMATCH,
        ),
    )
    for actual, expected, reason in comparisons:
        if actual != expected:
            return reason
    return None


def _profile_unavailable(
    reason: CalibrationProfileUnavailableReason,
    *,
    spec_digest: str,
    artifact: CalibrationArtifactV1,
) -> CalibrationProfileUnavailableV1:
    return CalibrationProfileUnavailableV1(
        reason=reason,
        spec_digest=spec_digest,
        artifact_digest=artifact.artifact_digest,
    )


def _derive_profile_digest(
    *,
    activation_scope: CalibrationActivationScope,
    artifact_digest: str,
    spec_digest: str,
) -> str:
    body: _JsonObject = {
        "activation_scope": activation_scope.value,
        "artifact_digest": artifact_digest,
        "spec_digest": spec_digest,
    }
    return _domain_digest(
        _CALIBRATION_PROFILE_DOMAIN,
        canonical_json_bytes(cast(JsonValue, body)),
    )


def _active_profile_authentication_fields(
    *,
    profile_digest: str,
    spec_digest: str,
    artifact_digest: str,
    purpose: CalibrationPurpose,
    query_stratum_id: str,
    scorer_id: str,
    normalizer_id: str,
    feature_spec_id: str,
    boundary_schema_id: str,
    dataset_manifest_digest: str,
    minimum_score_q32: int,
    minimum_margin_q32: int,
    deployment_status: CalibrationDeploymentStatus,
    activation_scope: CalibrationActivationScope,
    production_acceptance_digest: str | None,
) -> dict[str, object]:
    return {
        "profile_digest": profile_digest,
        "spec_digest": spec_digest,
        "artifact_digest": artifact_digest,
        "purpose": purpose,
        "query_stratum_id": query_stratum_id,
        "scorer_id": scorer_id,
        "normalizer_id": normalizer_id,
        "feature_spec_id": feature_spec_id,
        "boundary_schema_id": boundary_schema_id,
        "dataset_manifest_digest": dataset_manifest_digest,
        "minimum_score_q32": minimum_score_q32,
        "minimum_margin_q32": minimum_margin_q32,
        "deployment_status": deployment_status,
        "activation_scope": activation_scope,
        "production_acceptance_digest": production_acceptance_digest,
    }


def _authenticate_active_profile_fields(fields: dict[str, object]) -> bytes:
    wire: _JsonObject = {
        "activation_scope": cast(CalibrationActivationScope, fields["activation_scope"]).value,
        "artifact_digest": cast(str, fields["artifact_digest"]),
        "boundary_schema_id": cast(str, fields["boundary_schema_id"]),
        "dataset_manifest_digest": cast(str, fields["dataset_manifest_digest"]),
        "deployment_status": cast(CalibrationDeploymentStatus, fields["deployment_status"]).value,
        "feature_spec_id": cast(str, fields["feature_spec_id"]),
        "minimum_margin_q32": cast(int, fields["minimum_margin_q32"]),
        "minimum_score_q32": cast(int, fields["minimum_score_q32"]),
        "normalizer_id": cast(str, fields["normalizer_id"]),
        "production_acceptance_digest": cast(
            str | None,
            fields["production_acceptance_digest"],
        ),
        "profile_digest": cast(str, fields["profile_digest"]),
        "purpose": cast(CalibrationPurpose, fields["purpose"]).value,
        "query_stratum_id": cast(str, fields["query_stratum_id"]),
        "scorer_id": cast(str, fields["scorer_id"]),
        "spec_digest": cast(str, fields["spec_digest"]),
    }
    return hmac.digest(
        _ACTIVE_PROFILE_SECRET,
        _ACTIVE_PROFILE_AUTH_DOMAIN + canonical_json_bytes(cast(JsonValue, wire)),
        "sha256",
    )


def _calibrate_threshold(
    *,
    threshold_q32: int,
    examples: tuple[LabeledRecallExampleV1, ...],
    spec: CalibrationSpecV1,
) -> ThresholdCalibrationV1:
    selected = tuple(
        example
        for example in examples
        if example.eligible and example.score_q32 >= threshold_q32
    )
    selected_count = len(selected)
    error_count = sum(1 for example in selected if example.error)
    coverage_decimal = _coverage_decimal(selected_count, len(examples))
    risk_upper_bound_decimal = clopper_pearson_upper_bound(
        error_count=error_count,
        selected_count=selected_count,
        delta_decimal=spec.delta_decimal,
        family_size=len(spec.threshold_grid_q32),
    )
    passed = (
        selected_count >= spec.minimum_selected
        and Decimal(coverage_decimal) >= Decimal(spec.minimum_coverage_decimal)
        and Decimal(risk_upper_bound_decimal) <= Decimal(spec.alpha_decimal)
    )
    return ThresholdCalibrationV1(
        threshold_q32=threshold_q32,
        selected_count=selected_count,
        error_count=error_count,
        total_example_count=len(examples),
        coverage_decimal=coverage_decimal,
        risk_upper_bound_decimal=risk_upper_bound_decimal,
        passed=passed,
    )


def _coverage_decimal(selected_count: int, total_count: int) -> str:
    if total_count == 0 or selected_count == 0:
        return "0"
    units = (selected_count * _OUTPUT_SCALE) // total_count
    return _canonical_output_probability(units)


def _derive_example_set_digest(
    examples: tuple[LabeledRecallExampleV1, ...],
) -> str:
    hasher = hashlib.sha256()
    hasher.update(struct.pack(">Q", len(_CALIBRATION_EXAMPLE_SET_DOMAIN)))
    hasher.update(_CALIBRATION_EXAMPLE_SET_DOMAIN)
    hasher.update(struct.pack(">Q", len(examples)))
    for example in examples:
        encoded = encode_labeled_recall_example(example)
        hasher.update(struct.pack(">Q", len(encoded)))
        hasher.update(encoded)
    return hasher.hexdigest()


def _derive_artifact_fields_digest(
    *,
    spec_digest: str,
    label_provenance_manifest_digest: str,
    example_set_digest: str,
    threshold_results: tuple[ThresholdCalibrationV1, ...],
    chosen_threshold_q32: int | None,
    statistical_status: CalibrationStatisticalStatus,
    deployment_status: CalibrationDeploymentStatus,
    disabled_reasons: tuple[CalibrationDisabledReason, ...],
    generator_version: str,
    independence_status: LabelIndependenceStatus,
    production_acceptance_digest: str | None,
) -> str:
    body = _artifact_body_wire(
        spec_digest=spec_digest,
        label_provenance_manifest_digest=label_provenance_manifest_digest,
        example_set_digest=example_set_digest,
        threshold_results=threshold_results,
        chosen_threshold_q32=chosen_threshold_q32,
        statistical_status=statistical_status,
        deployment_status=deployment_status,
        disabled_reasons=disabled_reasons,
        generator_version=generator_version,
        independence_status=independence_status,
        production_acceptance_digest=production_acceptance_digest,
    )
    return _domain_digest(
        _CALIBRATION_ARTIFACT_DOMAIN,
        canonical_json_bytes(cast(JsonValue, body)),
    )


def _artifact_body_wire(
    *,
    spec_digest: str,
    label_provenance_manifest_digest: str,
    example_set_digest: str,
    threshold_results: tuple[ThresholdCalibrationV1, ...],
    chosen_threshold_q32: int | None,
    statistical_status: CalibrationStatisticalStatus,
    deployment_status: CalibrationDeploymentStatus,
    disabled_reasons: tuple[CalibrationDisabledReason, ...],
    generator_version: str,
    independence_status: LabelIndependenceStatus,
    production_acceptance_digest: str | None,
) -> _JsonObject:
    return {
        "schema": _CALIBRATION_ARTIFACT_SCHEMA,
        "spec_digest": spec_digest,
        "label_provenance_manifest_digest": label_provenance_manifest_digest,
        "example_set_digest": example_set_digest,
        "threshold_results": [
            threshold_calibration_to_json_value(result)
            for result in threshold_results
        ],
        "chosen_threshold_q32": chosen_threshold_q32,
        "statistical_status": statistical_status.value,
        "deployment_status": deployment_status.value,
        "disabled_reasons": [reason.value for reason in disabled_reasons],
        "generator_version": generator_version,
        "independence_status": independence_status.value,
        "production_acceptance_digest": production_acceptance_digest,
    }


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


def _optional_int(wire: _JsonObject, field_name: str) -> int | None:
    value = wire[field_name]
    if value is not None and type(value) is not int:
        raise InputBoundaryError(f"{field_name} must be an integer or null")
    return cast(int | None, value)


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


def _disabled_reason_tuple(
    wire: _JsonObject,
    field_name: str,
) -> tuple[CalibrationDisabledReason, ...]:
    value = wire[field_name]
    if type(value) is not list or any(type(item) is not str for item in value):
        raise InputBoundaryError(f"{field_name} must be an array of strings")
    reasons: list[CalibrationDisabledReason] = []
    for item in cast(list[str], value):
        try:
            reasons.append(CalibrationDisabledReason(item))
        except ValueError as exc:
            raise InputBoundaryError("unknown calibration disabled reason") from exc
    return tuple(reasons)


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


def _require_optional_q32(value: object, field_name: str) -> int | None:
    if value is None:
        return None
    _require_int(value, field_name, 0, _Q32_ONE)
    return cast(int, value)


def _require_threshold_results(value: object) -> tuple[ThresholdCalibrationV1, ...]:
    if (
        type(value) is not tuple
        or not 1 <= len(value) <= _MAX_THRESHOLD_FAMILY
        or any(type(result) is not ThresholdCalibrationV1 for result in value)
    ):
        raise InputBoundaryError(
            "threshold_results must contain 1 to 256 ThresholdCalibrationV1 values"
        )
    results = cast(tuple[ThresholdCalibrationV1, ...], value)
    if any(
        left.threshold_q32 >= right.threshold_q32
        for left, right in zip(results, results[1:])
    ):
        raise InputBoundaryError(
            "threshold_results must be strictly ordered by threshold"
        )
    totals = {result.total_example_count for result in results}
    if len(totals) != 1:
        raise InputBoundaryError(
            "threshold_results must share one total example count"
        )
    return results


def _require_disabled_reasons(
    value: object,
) -> tuple[CalibrationDisabledReason, ...]:
    if type(value) is not tuple or any(
        type(reason) is not CalibrationDisabledReason for reason in value
    ):
        raise InputBoundaryError(
            "disabled_reasons must be a tuple of CalibrationDisabledReason"
        )
    reasons = cast(tuple[CalibrationDisabledReason, ...], value)
    if tuple(sorted(reasons, key=lambda reason: reason.value)) != reasons:
        raise InputBoundaryError("disabled_reasons must be sorted and unique")
    if len(set(reasons)) != len(reasons):
        raise InputBoundaryError("disabled_reasons must be sorted and unique")
    return reasons


def _validate_artifact_relations(
    *,
    threshold_results: tuple[ThresholdCalibrationV1, ...],
    chosen_threshold_q32: int | None,
    statistical_status: CalibrationStatisticalStatus,
    deployment_status: CalibrationDeploymentStatus,
    disabled_reasons: tuple[CalibrationDisabledReason, ...],
    production_acceptance_digest: str | None,
) -> None:
    if statistical_status is CalibrationStatisticalStatus.STATISTICAL_PASS:
        if disabled_reasons or chosen_threshold_q32 is None:
            raise InputBoundaryError(
                "statistical pass requires one chosen threshold and no disabled reasons"
            )
        if not any(
            result.threshold_q32 == chosen_threshold_q32 and result.passed
            for result in threshold_results
        ):
            raise InputBoundaryError(
                "chosen threshold must identify a passing threshold result"
            )
    elif chosen_threshold_q32 is not None or not disabled_reasons:
        raise InputBoundaryError(
            "disabled artifact requires reasons and no chosen threshold"
        )

    if deployment_status is CalibrationDeploymentStatus.TEST_ONLY:
        if production_acceptance_digest is not None:
            raise InputBoundaryError(
                "test-only artifact cannot contain production acceptance"
            )
    else:
        if statistical_status is not CalibrationStatisticalStatus.STATISTICAL_PASS:
            raise InputBoundaryError(
                "production artifact requires statistical pass"
            )
        if production_acceptance_digest is None:
            raise InputBoundaryError(
                "production artifact requires an acceptance evidence digest"
            )


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
