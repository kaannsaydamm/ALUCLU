"""Data-only timer contracts; no timing clock, DLL load, or native call."""

import importlib.util
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "banded_native_fixture_timing",
    ROOT / "scripts/alc_r0_banded_native_fixture_timing.py",
)
TIMER = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(TIMER)


def test_fixed_four_cases_and_serial_schedule():
    cases = TIMER.fixed_cases()
    assert [c["K"] for c in cases] == [0, 1, 1, 512]
    assert [(len(c["first"]), len(c["second"])) for c in cases] == [
        (10000, 10000),
        (10000, 10001),
        (10000, 10001),
        (600, 600),
    ]
    assert cases[1]["second"][5000] == 10000
    assert cases[2]["first"] == (7,) * 10000
    order = TIMER.measurement_schedule()
    assert len(order) == 4 * 5 * 7
    assert order[:7] == [
        (0, "python_reference", "warmup", 0),
        (0, "python_reference", "warmup", 1),
        *[(0, "python_reference", "measured", i) for i in range(5)],
    ]


def test_every_integer_sample_and_losing_comparison_reported():
    stats = TIMER.sample_statistics([5, 1, 3, 4, 2])
    assert stats == dict(
        samples_ns=[5, 1, 3, 4, 2], mean_ns=3.0, median_ns=3, min_ns=1, max_ns=5
    )
    assert TIMER.compare_medians(
        stats, TIMER.sample_statistics([9, 7, 8, 6, 10])
    ) == dict(
        native_end_to_end_over_python_reference=8 / 3, native_end_to_end_faster=False
    )


@pytest.mark.parametrize(
    "samples", [[], [1] * 4, [1] * 6, [True] * 5, [-1] * 5, [1.0] * 5]
)
def test_malformed_samples_fail_closed(samples):
    with pytest.raises(ValueError):
        TIMER.sample_statistics(samples)


def test_complete_encoder_crossed_geometry_and_all_five_slots():
    from array import array
    from sys import getsizeof

    from aluclu.alc_r0.banded_edit_token_visibility_reference import (
        audit_banded_edit_token_visibility,
    )

    result = audit_banded_edit_token_visibility(
        (1, 2), (2, 1), code_budgets=(1, 2, 3, 4, 5), distance_threshold=2
    )
    expected = [0] * 64
    scratch = 884 + 72 * getsizeof(array("I")) + 10 * getsizeof(array("B")) + 65536
    expected[:20] = [
        1,
        0,
        0,
        2,
        2,
        5,
        2,
        63,
        0xFFFFFFFF,
        1,
        7,
        0,
        7,
        0,
        3,
        scratch,
        0,
        884,
        0,
        2,
    ]
    expected[20:27] = [0, 1, 0, 1, 1, 1, 6]
    for index in range(1, 5):
        expected[20 + 7 * index : 27 + 7 * index] = [1, 1, 1, 1, 2, 2, 8]
    assert TIMER.encode_reference_words(result) == expected


def test_unresolved_encoder_absent_fields_and_authority_flags():
    from dataclasses import replace

    from aluclu.alc_r0.banded_edit_token_visibility_reference import (
        audit_banded_edit_token_visibility,
    )

    result = audit_banded_edit_token_visibility(
        (), (1,), code_budgets=(1, 2, 3, 4, 5), distance_threshold=0
    )
    expected = [0] * 64
    expected[:8] = [1, 1, 2, 0, 1, 5, 0, 12]
    assert TIMER.encode_reference_words(result) == expected
    with pytest.raises(ValueError):
        TIMER.encode_reference_words(replace(result, training_authority=True))


def test_private_guarded_marshalling_owns_every_buffer_without_native_call():
    import ctypes as ct

    from aluclu.alc_r0.banded_edit_token_visibility_reference import (
        audit_banded_edit_token_visibility,
    )

    result = audit_banded_edit_token_visibility(
        (7,), (7,), code_budgets=(1, 2, 3, 4, 5), distance_threshold=0
    )
    buffers = TIMER.marshal_private(((0,), (0,), 1), result)
    assert buffers["payload"] == buffers["logical_capacity"] == 298
    assert buffers["allocated_backing_bytes"] == 308
    assert ct.addressof(buffers["workspace"]) + 4 & 3 == 0
    assert tuple(buffers["budgets"]) == (1, 1, 1, 1, 1)
    assert bytes(buffers["workspace"]) == b"\xa5" * 308
    assert (
        buffers["args"][0] is buffers["first"]
        and buffers["args"][2] is buffers["second"]
    )
    assert (
        buffers["args"][4] is buffers["budgets"]
        and buffers["args"][7] is buffers["policy"]
    )


@pytest.mark.parametrize(
    "mapped", [((1,), (0,), 1), ((True,), (0,), 1), ((0,), (), 1), ((0,), (0,), 0)]
)
def test_invalid_mapped_buffers_rejected_data_only(mapped):
    from aluclu.alc_r0.banded_edit_token_visibility_reference import (
        audit_banded_edit_token_visibility,
    )

    result = audit_banded_edit_token_visibility(
        (7,), (7,), code_budgets=(1, 2, 3, 4, 5), distance_threshold=0
    )
    with pytest.raises(ValueError):
        TIMER.marshal_private(mapped, result)


def test_actual_original_receipt_and_all_timing_pins_data_only():
    receipt = TIMER.verify_pins_and_receipt()
    assert receipt["commit"] == TIMER.BASELINE_COMMIT
    assert len(receipt["source_hashes"]) == 6


def test_zero_python_median_is_failure_not_invented_speedup():
    with pytest.raises(ValueError):
        TIMER.compare_medians(
            TIMER.sample_statistics([0] * 5), TIMER.sample_statistics([1] * 5)
        )


def test_output_must_be_fresh_and_external(tmp_path):
    path = tmp_path / "timing.json"
    assert TIMER.fresh_output(path) == path
    path.write_bytes(b"preserved")
    with pytest.raises(ValueError):
        TIMER.fresh_output(path)
    assert path.read_bytes() == b"preserved"
    with pytest.raises(ValueError):
        TIMER.fresh_output(ROOT / "timing.json")


def test_final_verification_failure_cannot_publish_success(tmp_path):
    output = tmp_path / "timing.json"

    def verification_failure():
        assert not output.exists()
        raise RuntimeError("held artifact verification failed")

    with pytest.raises(RuntimeError, match="held artifact"):
        TIMER.publish_completed_report(
            output, {"status": "success"}, verification_failure
        )
    assert not output.exists()
    assert list(tmp_path.iterdir()) == []


def test_serialization_failure_cannot_leave_final_report(tmp_path):
    output = tmp_path / "timing.json"
    with pytest.raises(TypeError):
        TIMER.publish_completed_report(output, {"invalid": object()}, lambda: None)
    assert not output.exists()
    assert list(tmp_path.iterdir()) == []


def test_complete_publication_is_exclusive_and_checked_first(tmp_path):
    import json

    output = tmp_path / "timing.json"
    checks = []

    def verify():
        assert not output.exists()
        checks.append("verified")

    report = {"status": "unit-only", "samples": [1, 2, 3]}
    assert TIMER.publish_completed_report(output, report, verify) == report
    assert checks == ["verified"]
    assert json.loads(output.read_bytes()) == report
    assert list(tmp_path.iterdir()) == [output]
    original = output.read_bytes()
    with pytest.raises(FileExistsError):
        TIMER.publish_completed_report(output, {"replacement": True}, lambda: None)
    assert output.read_bytes() == original
    assert list(tmp_path.iterdir()) == [output]


def test_execute_publishes_only_after_fallible_finally_checks():
    import ast
    import inspect

    function = ast.parse(inspect.getsource(TIMER.execute)).body[0]
    guarded = next(node for node in function.body if isinstance(node, ast.Try))
    assert guarded.finalbody
    # Publication in the try body would precede its mandatory finally checks.
    assert not any(
        isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and node.func.attr == "open"
        for statement in guarded.body
        for node in ast.walk(statement)
    )
    final_return = function.body[-1]
    assert isinstance(final_return, ast.Return)
    assert isinstance(final_return.value, ast.Call)
    assert final_return.value.func.id == "publish_completed_report"
