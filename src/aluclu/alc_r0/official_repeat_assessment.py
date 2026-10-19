"""Assess retained official digests only; no tensor/provenance/launch acceptance.

Matching digests are a sufficient exact-byte route under independently verified
execution. Mismatches require numerical evidence, never imply numerical failure.
Matrix stability, actual fresh processes and physical GPU identity stay external.
"""
from dataclasses import dataclass

from .canonical import parse_canonical_json
from .fixed_d_wire import DRequest, DResult, decode_d_request, decode_d_result

_FIRST = 'alc-r0-qualification-v1-d-gpu-fresh1-s20260916'
_SECOND = 'alc-r0-qualification-v1-d-gpu-fresh2-s20260916'
_SAME = ('source_export_root','runtime_inventory_root','snapshot_inventory_root',
         'fixture_source_root','clock_domain_root','snapshot_path')
_DIGESTS = ('official_sha256','wrapper_sha256',
            'incremental_official_sha256','incremental_wrapper_sha256')


@dataclass(frozen=True, slots=True)
class OfficialRepeatAssessment:
    kind: str
    first_request_root: str
    first_result_root: str
    second_request_root: str
    second_result_root: str
    compared_slots: int
    mismatched_slots: int


def _require(condition):
    if not condition:
        raise ValueError('invalid official repeat inputs; not a numerical failure')


def _validated(request, result):
    _require(type(request) is DRequest and type(result) is DResult)
    _require(type(request.data) is bytes and type(request.root) is str
             and type(result.data) is bytes and type(result.root) is str
             and type(result.outcome) is str)
    actual_request = decode_d_request(request.data)
    _require(actual_request == request)
    actual_result = decode_d_result(result.data, actual_request)
    _require(actual_result == result and actual_result.outcome == 'success')
    return parse_canonical_json(request.data), parse_canonical_json(result.data)


def assess_official_repeat(first_request, first_result, second_request, second_result):
    """Bounded transport assessment, never real-GPU2 or scientific PASS."""
    req1, result1 = _validated(first_request, first_result)
    req2, result2 = _validated(second_request, second_result)
    _require(req1['control_id'] == _FIRST and req2['control_id'] == _SECOND)
    _require(req1['reservation_id'] != req2['reservation_id']
             and first_request.root != second_request.root)
    _require(all(req1[key] == req2[key] for key in _SAME))
    q1, q2 = result1['qualification'], result2['qualification']
    _require(all(q1[key] == q2[key] for key in
                 ('source_device','source_dtype','base_digest','fixtures')))
    official1, official2 = q1['official'], q2['official']
    compared, mismatched = 0, 0
    for row1, row2 in zip(official1['cases'], official2['cases'], strict=True):
        _require(row1['key'] == row2['key'] and row1['case'] == row2['case'])
        for field in _DIGESTS:
            if row1[field] is None:
                _require(row2[field] is None)
                continue
            _require(row2[field] is not None)
            compared += 1
            mismatched += row1[field] != row2[field]
    for row1, row2 in zip(official1['nonzero_witnesses'],
                          official2['nonzero_witnesses'], strict=True):
        _require(row1['grid_id'] == row2['grid_id'] and row1['arm'] == row2['arm'])
        for field in ('official_sha256','mounted_sha256'):
            compared += 1
            mismatched += row1[field] != row2[field]
    _require(compared == 3060)
    return OfficialRepeatAssessment(
        'tensor-comparison-required' if mismatched else 'identical-digests',
        first_request.root, first_result.root, second_request.root,
        second_result.root, compared, mismatched)
