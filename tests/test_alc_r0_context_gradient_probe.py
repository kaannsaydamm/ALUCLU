from __future__ import annotations

import pytest
import torch

from aluclu.alc_r0.context_gradient_probe import (
    ContextGradientProbeError,
    make_synthetic_ids,
    validate_probe_request,
)


@pytest.mark.parametrize("length", [512, 1024, 2048])
@pytest.mark.parametrize("arm", ["capsule", "q_lora"])
def test_declared_synthetic_probe_request(length: int, arm: str) -> None:
    assert validate_probe_request(length, arm) == (length, arm)


@pytest.mark.parametrize(
    ("length", "arm"),
    [(511, "capsule"), (4096, "capsule"), (True, "capsule"), (512, "base")],
)
def test_undeclared_probe_request_fails_closed(length, arm) -> None:
    with pytest.raises(ContextGradientProbeError):
        validate_probe_request(length, arm)


def test_synthetic_ids_are_reproducible_bounded_and_not_source_text() -> None:
    first = make_synthetic_ids(512, vocab_size=49_152)
    second = make_synthetic_ids(512, vocab_size=49_152)

    assert torch.equal(first, second)
    assert first.shape == (1, 512)
    assert first.dtype == torch.long
    assert int(first.min()) > 0
    assert int(first.max()) < 49_152


@pytest.mark.parametrize("vocab_size", [0, 1, True, "49152"])
def test_synthetic_ids_reject_invalid_vocabulary(vocab_size) -> None:
    with pytest.raises(ContextGradientProbeError):
        make_synthetic_ids(512, vocab_size=vocab_size)
