from __future__ import annotations

import math

import pytest
import torch

from aluclu.alc_r0.checkpoint_fidelity import (
    CheckpointFidelityError,
    compare_named_tensors,
    compare_tensor,
)


def test_identical_nonzero_metrics_and_inputs_unchanged() -> None:
    ref = torch.tensor([1.0, -2.0], requires_grad=True)
    before = ref.detach().clone()
    result = compare_tensor(ref, ref.clone(), exact=True)
    assert result.relative_l2 == 0.0
    assert result.cosine == pytest.approx(1.0)
    assert result.reference_l2 == pytest.approx(math.sqrt(5))
    assert result.difference_l2 == 0.0
    assert not result.exact_zero
    assert torch.equal(before, ref)
    assert ref.grad is None


def test_zero_metrics_are_explicit_without_fake_ratios() -> None:
    result = compare_tensor(torch.zeros(2), torch.tensor([-0.0, 0.0]))
    assert result.exact_zero
    assert result.reference_l2 == result.actual_l2 == result.difference_l2 == 0
    assert result.relative_l2 is None and result.cosine is None


def test_exact_comparison_preserves_original_signed_zero_bytes() -> None:
    with pytest.raises(CheckpointFidelityError):
        compare_tensor(torch.tensor([0.0]), torch.tensor([-0.0]), exact=True)


def test_exact_comparison_uses_logical_values_not_backing_storage() -> None:
    backing = torch.tensor([123.0, 1.0, 999.0, -2.0])
    compare_tensor(backing[1::2], torch.tensor([1.0, -2.0]), exact=True)


@pytest.mark.parametrize("actual", [torch.zeros(2), torch.tensor([-1e-6, 2e-6])])
def test_small_gradient_mutation_defeats_loose_allclose(actual: torch.Tensor) -> None:
    reference = torch.tensor([1e-6, -2e-6])
    assert torch.allclose(reference, actual, rtol=1e-3, atol=1e-3)
    with pytest.raises(CheckpointFidelityError):
        compare_tensor(reference, actual)


def test_scale_mutation_is_not_hidden_by_absolute_tolerance() -> None:
    reference = torch.tensor([1e-6, 2e-6])
    actual = reference * 1.01
    assert torch.allclose(reference, actual, rtol=1e-3, atol=1e-3)
    with pytest.raises(CheckpointFidelityError):
        compare_tensor(reference, actual)


def test_small_acceptable_perturbation_uses_relative_scale() -> None:
    ref = torch.tensor([1e-8, -2e-8], dtype=torch.float64)
    result = compare_tensor(ref, ref * (1 + 1e-6))
    assert result.relative_l2 == pytest.approx(1e-6, rel=1e-6)
    assert result.cosine == pytest.approx(1)


def test_subnormal_nonzero_identity_does_not_become_zero() -> None:
    tiny = float.fromhex("0x0.0000000000001p-1022")
    ref = torch.tensor([tiny, tiny], dtype=torch.float64)
    result = compare_tensor(ref, ref.clone())
    assert not result.exact_zero
    assert result.reference_l2 > 0
    assert result.relative_l2 == 0
    assert result.cosine == pytest.approx(1)


def test_independently_scaled_subnormal_perturbation_is_rejected() -> None:
    tiny = float.fromhex("0x0.0000000000001p-1022")
    ref = torch.tensor([2 * tiny, 4 * tiny], dtype=torch.float64)
    actual = torch.tensor([3 * tiny, 4 * tiny], dtype=torch.float64)
    assert torch.allclose(ref, actual, rtol=1e-3, atol=1e-3)
    with pytest.raises(CheckpointFidelityError):
        compare_tensor(ref, actual)


def test_unrepresentable_absolute_norm_is_rejected() -> None:
    ref = torch.full((4,), 1e308, dtype=torch.float64)
    with pytest.raises(CheckpointFidelityError):
        compare_tensor(ref, ref.clone())


@pytest.mark.parametrize(
    "actual",
    [
        None,
        [1.0],
        torch.tensor([1]),
        torch.tensor([True]),
        torch.tensor([1j]),
        torch.tensor([]),
        torch.tensor([math.nan]),
        torch.tensor([math.inf]),
        torch.tensor([1.0], dtype=torch.float64),
        torch.tensor([[1.0]]),
        torch.sparse_coo_tensor([[0]], [1.0], (1,), check_invariants=True),
        torch.ones(1, device="meta"),
    ],
)
def test_invalid_actual_tensor_fails_closed(actual: object) -> None:
    with pytest.raises(CheckpointFidelityError):
        compare_tensor(torch.ones(1), actual)


@pytest.mark.parametrize("exact", [None, 1, "yes"])
def test_exact_flag_must_be_actual_boolean(exact: object) -> None:
    with pytest.raises(CheckpointFidelityError):
        compare_tensor(torch.ones(1), torch.ones(1), exact=exact)


def test_nonzero_actual_against_zero_reference_fails() -> None:
    with pytest.raises(CheckpointFidelityError):
        compare_tensor(torch.zeros(1), torch.tensor([1e-12]))


def test_named_comparison_is_complete_and_canonically_ordered() -> None:
    tensors = {"z.B": torch.ones(1), "a.A": torch.zeros(2)}
    result = compare_named_tensors(tensors, dict(reversed(list(tensors.items()))))
    assert tuple(name for name, _ in result) == ("a.A", "z.B")


@pytest.mark.parametrize(
    "actual", [{}, {"a": torch.ones(1)}, {"z": None}, {"z": torch.zeros(1)}]
)
def test_missing_wrong_or_mutated_named_gradient_fails(actual: object) -> None:
    with pytest.raises(CheckpointFidelityError):
        compare_named_tensors({"z": torch.ones(1)}, actual)


@pytest.mark.parametrize("name", ["", " x", "x\n", "e\u0301", "\ud800"])
def test_noncanonical_tensor_name_is_rejected(name: str) -> None:
    with pytest.raises(CheckpointFidelityError):
        compare_named_tensors({name: torch.ones(1)}, {name: torch.ones(1)})


def test_accumulated_gradient_mutation_is_checked_per_factor() -> None:
    tensors = {"a.A": torch.tensor([1e-6]), "a.B": torch.ones(1)}
    changed = {"a.A": torch.tensor([-1e-6]), "a.B": torch.ones(1)}
    with pytest.raises(CheckpointFidelityError):
        compare_named_tensors(tensors, changed)


@pytest.mark.parametrize(
    "reference",
    [None, torch.tensor([]), torch.tensor([math.nan]), torch.tensor([math.inf])],
)
def test_reference_validation_is_not_assumed(reference: object) -> None:
    with pytest.raises(CheckpointFidelityError):
        compare_tensor(reference, torch.ones(1))


@pytest.mark.parametrize(
    "dtype", [torch.float16, torch.bfloat16, torch.float32, torch.float64]
)
def test_exact_supported_floating_dtype_identity(dtype: torch.dtype) -> None:
    values = torch.tensor([0.0, 1.0, -2.0], dtype=dtype)
    compare_tensor(values, values.clone(), exact=True)


def test_nonfinite_difference_of_finite_values_fails() -> None:
    reference = torch.tensor([1e308], dtype=torch.float64)
    with pytest.raises(CheckpointFidelityError):
        compare_tensor(reference, -reference)


@pytest.mark.parametrize(
    "reference,actual",
    [
        ({}, {}),
        ([], {}),
        ({"x": torch.ones(1)}, []),
        ({1: torch.ones(1)}, {1: torch.ones(1)}),
    ],
)
def test_invalid_named_containers_fail(reference: object, actual: object) -> None:
    with pytest.raises(CheckpointFidelityError):
        compare_named_tensors(reference, actual)
