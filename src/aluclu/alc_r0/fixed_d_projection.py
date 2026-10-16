"""Explicit bounded scientific-receipt projection; never launch or provenance.

Module import and failure encoding are lightweight. Success type resolution is
post-runtime and lazy; no model, tokenizer, qualification or GPU call is made.
Caller owns quiescent observations. Constructed receipts are not execution proof.
"""

import math

from .canonical import canonical_json_bytes, parse_canonical_json
from .fixed_d_wire import (
    DRequest, DWireError, _ROOT_FIELDS, decode_d_request, decode_d_result,
)


def _require(condition):
    if not condition:
        raise DWireError("invalid fixed D scientific projection input")


def _typed(value, expected):
    _require(type(value) is expected)
    return value


def _tuple(value, low, high=None):
    _typed(value, tuple)
    _require(low <= len(value) <= (low if high is None else high))
    return value


def _text(value, limit=64):
    _typed(value, str)
    _require(0 < len(value) <= limit and value.isascii())
    return value


def _integer(value, low=0, high=(1 << 63) - 1):
    _typed(value, int)
    _require(low <= value <= high)
    return str(value)


def _boolean(value):
    return _typed(value, bool)


def _number(value):
    _typed(value, float)
    _require(math.isfinite(value))
    return value


def _nullable_number(value):
    return None if value is None else _number(value)


def _nullable_hash(value):
    return None if value is None else _text(value)


def _request(request):
    _typed(request, DRequest)
    checked = decode_d_request(request.data)
    _typed(request.root, str)
    _require(request.root == checked.root)
    return parse_canonical_json(checked.data)


def _envelope(request, req, outcome, qualification, failure):
    value = dict(schema="alc-r0-fixed-d-result-v1", request_root=request.root,
                 control_id=req["control_id"], reservation_id=req["reservation_id"],
                 **{key: req[key] for key in _ROOT_FIELDS}, outcome=outcome,
                 qualification=qualification, failure=failure)
    return decode_d_result(canonical_json_bytes(value), request)


def _scientific_types():
    # Import only after request denial checks, never on bootstrap/failure paths.
    from .checkpoint_fidelity import TensorComparison
    from .checkpoint_official_forward import (
        ForwardCase, OfficialKey, OfficialCase, NonzeroWitness, OfficialSuite,
    )
    from .checkpoint_optimizer import AdamWComparison
    from .checkpoint_parity_cell import CaseComparison, ParityCell
    from .checkpoint_parity_inputs import ParityInput
    from .checkpoint_parity_matrix import CellKey, MatrixCell, ParityMatrix
    from .checkpoint_parity_qualification import ParityQualification
    from .checkpoint_parity_tokenizer import TokenizedParityFixtures
    return dict(TensorComparison=TensorComparison, ForwardCase=ForwardCase,
                OfficialKey=OfficialKey, OfficialCase=OfficialCase,
                NonzeroWitness=NonzeroWitness, OfficialSuite=OfficialSuite,
                AdamWComparison=AdamWComparison, CaseComparison=CaseComparison,
                ParityCell=ParityCell, ParityInput=ParityInput, CellKey=CellKey,
                MatrixCell=MatrixCell, ParityMatrix=ParityMatrix,
                ParityQualification=ParityQualification,
                TokenizedParityFixtures=TokenizedParityFixtures)


def _identity(value):
    return dict(source_device=_text(value.source_device),
                source_dtype=_text(value.source_dtype), base_digest=_text(value.base_digest))


def _fixture(value, types):
    _typed(value, types["ParityInput"])
    size = len(_tuple(value.input_ids, 3, 71))
    labels = _tuple(value.labels, size)
    result = dict(
        input_ids=[_integer(v, 0, 49151) for v in value.input_ids],
        attention_mask=[_integer(v, 0, 1) for v in _tuple(value.attention_mask, size)],
        labels=[_integer(v, -100, 49151) for v in labels],
        position_ids=[_integer(v, 0, 70) for v in _tuple(value.position_ids, size)],
        prompt_length=_integer(value.prompt_length, 1, 64),
        candidate_ids=[_integer(v, 1, 49151) for v in _tuple(value.candidate_ids, 1, 64)])
    # The decoder rejects every signed label spelling other than -100.
    return result


def _fixtures(value, types):
    _typed(value, types["TokenizedParityFixtures"])
    return dict(snapshot_inventory_sha256=_text(value.snapshot_inventory_sha256),
                model_revision=_text(value.model_revision),
                tokenizer_class=_text(value.tokenizer_class, 256),
                fixture_sha256=_text(value.fixture_sha256),
                fixtures=[_fixture(row, types) for row in _tuple(value.fixtures, 6)])


def _official_case(value, types):
    _typed(value, types["OfficialCase"])
    key = _typed(value.key, types["OfficialKey"])
    case = _typed(value.case, types["ForwardCase"])
    return dict(key=dict(grid_id=_text(key.grid_id), arm=_text(key.arm), phase=_text(key.phase)),
                case=dict(batch=_integer(case.batch), length=_integer(case.length),
                          padding_side=_text(case.padding_side),
                          explicit_positions=_boolean(case.explicit_positions),
                          cached=_boolean(case.cached)),
                official_sha256=_text(value.official_sha256),
                wrapper_sha256=_text(value.wrapper_sha256),
                incremental_official_sha256=_nullable_hash(value.incremental_official_sha256),
                incremental_wrapper_sha256=_nullable_hash(value.incremental_wrapper_sha256))


def _witness(value, types):
    _typed(value, types["NonzeroWitness"])
    return dict(grid_id=_text(value.grid_id), arm=_text(value.arm),
                official_sha256=_text(value.official_sha256),
                mounted_sha256=_text(value.mounted_sha256))


def _official(value, types):
    _typed(value, types["OfficialSuite"])
    return dict(**_identity(value),
                cases=[_official_case(row, types) for row in _tuple(value.cases, 1296)],
                nonzero_witnesses=[_witness(row, types)
                                  for row in _tuple(value.nonzero_witnesses, 18)])


def _comparison(value, types):
    _typed(value, types["TensorComparison"])
    return dict(reference_l2=_number(value.reference_l2), actual_l2=_number(value.actual_l2),
                difference_l2=_number(value.difference_l2),
                relative_l2=_nullable_number(value.relative_l2),
                cosine=_nullable_number(value.cosine), exact_zero=_boolean(value.exact_zero))


def _named(value, count, types):
    result = []
    for pair in _tuple(value, count):
        name, comparison = _tuple(pair, 2)
        result.append([_text(name), _comparison(comparison, types)])
    return result


def _pair(value):
    return [_number(v) for v in _tuple(value, 2)]


def _case(value, types):
    _typed(value, types["CaseComparison"])
    return dict(state=_text(value.state), repeat=_integer(value.repeat),
                fixture_index=_integer(value.fixture_index), losses=_pair(value.losses),
                scores=_pair(value.scores), base_digest=_text(value.base_digest),
                factor_digest=_text(value.factor_digest))


def _matrix_cell(value, types):
    _typed(value, types["MatrixCell"])
    key = _typed(value.key, types["CellKey"])
    result = _typed(value.result, types["ParityCell"])
    ports = _tuple(key.ports, 1, 2)
    count = 2 * len(ports)
    accumulation = _typed(result.accumulation, types["AdamWComparison"])
    return dict(key=dict(grid_id=_text(key.grid_id), ports=[_integer(p) for p in ports],
                         rank=_integer(key.rank), arm=_text(key.arm)),
                result=dict(cases=[_case(row, types) for row in _tuple(result.cases, 18)],
                            pending_losses=_pair(result.pending_losses),
                            accumulation=dict(step=_integer(accumulation.step),
                                              factors=_named(accumulation.factors, count, types),
                                              exp_avg=_named(accumulation.exp_avg, count, types),
                                              exp_avg_sq=_named(accumulation.exp_avg_sq, count, types)),
                            parameter_names=[_text(v) for v in _tuple(result.parameter_names, count)],
                            parameter_count=_integer(result.parameter_count),
                            base_digest=_text(result.base_digest)))


def _matrix(value, types):
    _typed(value, types["ParityMatrix"])
    return dict(**_identity(value), seed=_integer(value.seed),
                cells=[_matrix_cell(row, types) for row in _tuple(value.cells, 18)])


def encode_d_success(qualification, request: DRequest):
    """Retain complete typed observations, not tensor evidence or execution proof."""
    req = _request(request)
    types = _scientific_types()
    _typed(qualification, types["ParityQualification"])
    value = dict(**_identity(qualification), fixtures=_fixtures(qualification.fixtures, types),
                 official=_official(qualification.official, types),
                 matrix=_matrix(qualification.matrix, types))
    return _envelope(request, req, "success", value, None)


def encode_d_failure(request: DRequest, *, stage: str, category: str):
    """Closed terminal diagnostic; no raw exception or partial success export."""
    req = _request(request)
    stage, category = _text(stage), _text(category, 32)
    outcome = "interrupted" if category == "interrupted" else "error"
    return _envelope(request, req, outcome, None,
                     dict(stage=stage, category=category, completed_evidence_root=None))
