"""Dormant body boundaries and pure diagnostics, not scientific execution."""
import ast
import importlib
from dataclasses import dataclass
from pathlib import Path
import time

import pytest
from aluclu.alc_r0.canonical import canonical_json_bytes, parse_canonical_json
from aluclu.alc_r0.fixed_d_wire import decode_d_request, DRequest
from test_alc_r0_fixed_d_wire import request


def worker():
    return importlib.import_module('aluclu.alc_r0.fixed_d_worker')


class Trap:
    def __getattribute__(self, name):
        raise AssertionError('request hook called before denial')


@pytest.mark.parametrize('case', ['none', 'dict', 'text', 'trap'])
def test_body_denies_before_request_hooks(case):
    value = {'none': None, 'dict': {}, 'text': 'approved', 'trap': Trap()}[case]
    with pytest.raises(worker().WorkerHandoffUnavailable):
        worker()._execute_request(value)


@dataclass
class Failure:
    stage: str


class QualificationError(RuntimeError):
    def __init__(self, failure):
        self.failure = failure


class QualificationInterrupted(KeyboardInterrupt):
    def __init__(self, failure):
        self.failure = failure


class OOM(RuntimeError):
    pass


TYPES = (QualificationError, QualificationInterrupted, Failure, OOM)


@pytest.mark.parametrize('error,category', [(ValueError(), 'validation'),
                                         (RuntimeError(), 'runtime'),
                                         (MemoryError(), 'oom'), (OOM(), 'oom'),
                                         (KeyboardInterrupt(), 'interrupted')])
def test_diagnostic_category(error, category):
    assert worker()._diagnostic(error, 'worker_context', TYPES) == ('worker_context', category)


@pytest.mark.parametrize('stage', ['tokenizer', 'host', 'official', 'matrix', 'terminal-assets'])
def test_exact_qualifier_stage(stage):
    error = QualificationError(Failure(stage))
    assert worker()._diagnostic(error, 'tokenizer', TYPES) == (stage, 'runtime')


@pytest.mark.parametrize('case', ['none', 'trap', 'unexpected', 'stage_trap'])
def test_unknown_failure_never_supplies_stage(case):
    failure = {'none': None, 'trap': Trap(), 'unexpected': Failure('unexpected'),
               'stage_trap': Failure(Trap())}[case]
    assert worker()._diagnostic(QualificationError(failure), 'tokenizer', TYPES) == (
        'tokenizer', 'runtime')


def test_typed_interruption_preserved():
    assert worker()._diagnostic(QualificationInterrupted(Failure('matrix')),
                                'tokenizer', TYPES) == ('matrix', 'interrupted')


@pytest.mark.parametrize('distance,category', [(1, 'oom'), (7, 'oom'), (8, 'runtime')])
def test_exception_chain_bound(distance, category):
    error = OOM()
    for _ in range(distance):
        outer = RuntimeError()
        outer.__cause__ = error
        error = outer
    assert worker()._diagnostic(error, 'tokenizer', TYPES) == ('tokenizer', category)


def test_cycle_and_causal_precedence():
    first, second = RuntimeError(), RuntimeError()
    first.__cause__, second.__cause__ = second, first
    first.__context__ = OOM()
    assert worker()._diagnostic(first, 'tokenizer', TYPES) == ('tokenizer', 'runtime')


def test_exception_attribute_hooks_not_called():
    class Hook(RuntimeError):
        def __getattribute__(self, name):
            raise AssertionError('exception hook called')
    error = Hook()
    error.__cause__ = OOM()
    assert worker()._diagnostic(error, 'tokenizer', TYPES) == ('tokenizer', 'oom')


@pytest.mark.parametrize('missing', ['failure', 'stage'])
def test_missing_typed_fields_fall_back(missing):
    error = QualificationError.__new__(QualificationError)
    if missing == 'stage':
        error.failure = Failure.__new__(Failure)
    assert worker()._diagnostic(error, 'tokenizer', TYPES) == ('tokenizer', 'runtime')


@pytest.mark.parametrize('expired,category,stage,code', [
    (False, 'runtime', 'worker_context', 2),
    (True, 'oom', 'bootstrap_deadline', 2),
    (True, 'interrupted', 'worker_context', 130),
])
def test_terminal_failure_real_codec(expired, category, stage, code):
    req = decode_d_request(canonical_json_bytes(request()))
    deadline = 1 if expired else time.monotonic_ns() + 10**9
    actual_code, result = worker()._terminal_failure(req, 'worker_context', category, deadline)
    value = parse_canonical_json(result.data)
    assert actual_code == code
    assert value['qualification'] is None
    assert value['failure']['stage'] == stage
    assert value['failure']['category'] == ('validation' if stage == 'bootstrap_deadline' else category)


def test_terminal_failure_invalid_request_not_fabricated():
    req = DRequest(canonical_json_bytes(request()), 'b' * 64)
    with pytest.raises(ValueError):
        worker()._terminal_failure(req, 'worker_context', 'runtime', 1)


def test_terminal_failure_static_max_two_encodes_no_recursion():
    tree = ast.parse(Path(worker().__file__).read_text(encoding='utf-8'))
    body = next(node for node in tree.body if isinstance(node, ast.FunctionDef)
                and node.name == '_terminal_failure')
    calls = [node.func.id for node in ast.walk(body) if isinstance(node, ast.Call)
             and isinstance(node.func, ast.Name)]
    assert calls.count('encode_d_failure') == 2
    assert '_terminal_failure' not in calls
    assert not any(isinstance(node, (ast.For, ast.While)) for node in ast.walk(body))


def test_body_static_fixed_call_is_not_dynamic_execution_proof():
    tree = ast.parse(Path(worker().__file__).read_text(encoding='utf-8'))
    body = next(node for node in tree.body if isinstance(node, ast.FunctionDef)
                and node.name == '_execute_request')
    first = body.body[1] if isinstance(body.body[0], ast.Expr) and isinstance(
        body.body[0].value, ast.Constant) else body.body[0]
    assert isinstance(first, ast.Expr) and isinstance(first.value, ast.Call)
    assert first.value.func.id == '_require_operator_handoff'
    calls = [node for node in ast.walk(body) if isinstance(node, ast.Call)
             and isinstance(node.func, ast.Name) and node.func.id == 'run_parity_qualification']
    assert len(calls) == 1
    parent = next(node for node in ast.walk(body) if isinstance(node, ast.Try))
    call_statement = next(i for i, node in enumerate(parent.body)
                          if isinstance(node, ast.Assign) and node.value is calls[0])
    preceding = parent.body[call_statement - 1]
    assert isinstance(preceding, ast.Expr) and preceding.value.func.id == '_check_original_deadline'
    assert not any(isinstance(node, (ast.For, ast.While)) for node in ast.walk(body))
    assert [arg.arg for arg in body.args.args] == ['request']
