"""Synthetic retained receipts, never real fresh-process/GPU evidence."""
import importlib
import subprocess
import sys
from dataclasses import FrozenInstanceError, replace

import pytest

from aluclu.alc_r0.canonical import canonical_json_bytes
from test_alc_r0_fixed_d_wire import CONTROLS, ROOT, OTHER, full_result, request, wire


def api():
    return importlib.import_module('aluclu.alc_r0.official_repeat_assessment')


def pair():
    r1, r2 = request(CONTROLS[1]), request(CONTROLS[2])
    r1['reservation_id'], r2['reservation_id'] = 'd-gpu-1', 'd-gpu-2'
    for key in ('declaration_root','invocation_root','original_entry_root',
                'authority_generation_root'):
        r2[key] = OTHER
    return r1, full_result(r1), r2, full_result(r2)


def views(values):
    r1, v1, r2, v2 = values
    m = wire()
    a, b = (m.decode_d_request(canonical_json_bytes(r)) for r in (r1,r2))
    return a, m.decode_d_result(canonical_json_bytes(v1),a), b, m.decode_d_result(canonical_json_bytes(v2),b)


def test_equal_complete_official_digests():
    data = views(pair())
    before = tuple(x.data for x in data)
    result = api().assess_official_repeat(*data)
    assert result.kind == 'identical-digests'
    assert (result.compared_slots,result.mismatched_slots) == (3060,0)
    assert result.first_result_root == data[1].root
    assert result.second_result_root == data[3].root
    assert tuple(x.data for x in data) == before
    with pytest.raises(FrozenInstanceError):
        result.kind = 'approved'


@pytest.mark.parametrize('field', ['official_sha256','wrapper_sha256',
                                  'incremental_official_sha256','incremental_wrapper_sha256'])
def test_changed_digest_requires_tensors_not_failure(field):
    values = pair()
    rows = values[3]['qualification']['official']['cases']
    row = next(r for r in rows if r['case']['cached']) if field.startswith('incremental') else rows[0]
    row[field] = 'c'*64
    result = api().assess_official_repeat(*views(values))
    assert (result.kind,result.compared_slots,result.mismatched_slots) == ('tensor-comparison-required',3060,1)


@pytest.mark.parametrize('field',['official_sha256','mounted_sha256'])
def test_witness_mismatch_is_inconclusive(field):
    values = pair()
    values[3]['qualification']['official']['nonzero_witnesses'][0][field] = 'c'*64
    assert api().assess_official_repeat(*views(values)).mismatched_slots == 1


def test_matrix_measurement_not_cross_process_certified():
    values = pair()
    values[3]['qualification']['matrix']['cells'][0]['result']['pending_losses'][0] = 2
    assert api().assess_official_repeat(*views(values)).kind == 'identical-digests'


@pytest.mark.parametrize('field',['source_export_root','runtime_inventory_root',
    'snapshot_inventory_root','fixture_source_root','clock_domain_root','snapshot_path'])
def test_mismatched_request_identity(field):
    values = list(pair())
    values[2][field] = 'C:/other/snapshot' if field == 'snapshot_path' else 'c'*64
    # Snapshot root additionally binds fixtures, so the existing codec may reject first.
    values[3] = full_result(values[2])
    with pytest.raises(ValueError):
        api().assess_official_repeat(*views(values))


@pytest.mark.parametrize('mode',['same','reverse','cpu','reservation'])
def test_invalid_control_pair(mode):
    values = list(pair())
    if mode == 'reverse':
        values = values[2:] + values[:2]
    elif mode == 'same':
        values[2]['control_id'] = CONTROLS[1]
        values[3] = full_result(values[2])
    elif mode == 'cpu':
        values[0]['control_id'] = CONTROLS[0]
        values[1] = full_result(values[0])
    else:
        values[2]['reservation_id'] = values[0]['reservation_id']
        values[3] = full_result(values[2])
    with pytest.raises(ValueError):
        api().assess_official_repeat(*views(values))


@pytest.mark.parametrize('index,field,value', [
    (0,'root',OTHER),(1,'root',OTHER),(2,'root',OTHER),(3,'root',OTHER),
    (1,'outcome','error'),(3,'data',b'{}'),(0,'data',b'{}'),
    (1,'data',b'x'*(4194304+1)),(0,'data',b'x'*(16384+1)),
], ids=['request1-root','result1-root','request2-root','result2-root',
        'forged-outcome','bad-result','bad-request','oversized-result','oversized-request'])
def test_forged_wrappers_and_bad_bytes_rejected(index,field,value):
    data = list(views(pair()))
    data[index] = replace(data[index],**{field:value})
    with pytest.raises(ValueError):
        api().assess_official_repeat(*data)


@pytest.mark.parametrize('change',['base','fixtures','multiple','truncated'])
def test_additional_identity_and_digest_coverage(change):
    values = pair()
    q = values[3]['qualification']
    if change == 'base':
        q['base_digest'] = OTHER
        q['official']['base_digest'] = OTHER
        q['matrix']['base_digest'] = OTHER
        for cell in q['matrix']['cells']:
            cell['result']['base_digest'] = OTHER
            for row in cell['result']['cases']:
                row['base_digest'] = OTHER
    elif change == 'fixtures':
        q['fixtures']['tokenizer_class'] = 'transformers.OtherTokenizerFast'
    elif change == 'multiple':
        q['official']['cases'][0]['official_sha256'] = OTHER
        q['official']['cases'][1]['wrapper_sha256'] = OTHER
        assessment = api().assess_official_repeat(*views(values))
        assert (assessment.kind,assessment.mismatched_slots) == ('tensor-comparison-required',2)
        return
    else:
        data = list(views(values))
        data[3] = replace(data[3],data=data[3].data[:-1])
        with pytest.raises(ValueError):
            api().assess_official_repeat(*data)
        return
    with pytest.raises(ValueError):
        api().assess_official_repeat(*views(values))


def test_error_receipt_and_partial_schedule_reject():
    values = pair()
    values[3].update(outcome='error',qualification=None,
                     failure=dict(stage='host',category='runtime',completed_evidence_root=None))
    with pytest.raises(ValueError):
        api().assess_official_repeat(*views(values))
    values = pair()
    values[3]['qualification']['official']['cases'].pop()
    with pytest.raises(ValueError):
        api().assess_official_repeat(*views(values))


def test_subclass_and_wrong_types_reject():
    data = list(views(pair()))
    class Sub(wire().DRequest):
        pass
    data[0] = Sub(data[0].data,data[0].root)
    with pytest.raises(ValueError):
        api().assess_official_repeat(*data)
    data[0] = object()
    with pytest.raises(ValueError):
        api().assess_official_repeat(*data)


def test_fresh_import_has_no_scientific_runtime():
    code = '''
import importlib.abc, sys
class Deny(importlib.abc.MetaPathFinder):
    def find_spec(self, fullname, path=None, target=None):
        if fullname.split('.')[0] in {'torch','transformers','numpy'}:
            raise AssertionError('scientific import')
sys.meta_path.insert(0,Deny())
import aluclu.alc_r0.official_repeat_assessment
print('pure')
'''
    result = subprocess.run((sys.executable,'-c',code),capture_output=True,text=True,timeout=10)
    assert (result.returncode,result.stdout,result.stderr) == (0,'pure\n','')
