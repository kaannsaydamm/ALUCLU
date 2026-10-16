"""CPU-only factor tests; no real host, tokenizer, corpus, or CUDA access."""

import pytest
import torch
from torch import nn

from aluclu.alc_r0.reference_qv_lora import ReferenceQVLoRA


def frozen_projection(target):
    return nn.Linear(576, 576 if target == "q" else 192, bias=False).requires_grad_(False)


def test_fixed_full_reference_geometry_and_rng():
    before = torch.random.get_rng_state().clone()
    reference = ReferenceQVLoRA(seed=17)
    assert torch.equal(before, torch.random.get_rng_state())
    assert sum(p.numel() for p in reference.parameters()) == 460800
    assert len(reference.state_dict()) == 120
    second = ReferenceQVLoRA(seed=17)
    for key, tensor in reference.state_dict().items():
        assert torch.equal(tensor, second.state_dict()[key])
    for layer in range(30):
        for target, width in (("q", 576), ("v", 192)):
            factors = reference.factors[str(layer)][target]
            assert factors.A.shape == (8, 576)
            assert factors.B.shape == (width, 8)
            assert factors.A.dtype == factors.B.dtype == torch.float32
            assert factors.A.requires_grad and factors.B.requires_grad
            assert torch.count_nonzero(factors.B) == 0


def test_initialization_ignores_ambient_meta_device():
    expected = ReferenceQVLoRA(seed=17)
    with torch.device("meta"):
        actual = ReferenceQVLoRA(seed=17)
    for key, tensor in actual.state_dict().items():
        assert tensor.device.type == "cpu"
        assert torch.equal(tensor, expected.state_dict()[key])


@pytest.mark.parametrize("target", ["q", "v"])
def test_noop_math_gradients_and_frozen_base(target):
    reference = ReferenceQVLoRA(seed=17)
    base = frozen_projection(target)
    original = base.weight.detach().clone()
    project = reference.bind_projection(layer=14, target=target, base=base)
    x = torch.randn(2, 3, 576)
    assert torch.equal(project(x), base(x))
    factors = reference.factors["14"][target]
    project(x).square().sum().backward()
    assert factors.A.grad is not None and torch.count_nonzero(factors.A.grad) == 0
    assert factors.B.grad is not None and torch.count_nonzero(factors.B.grad) > 0
    assert base.weight.grad is None
    with torch.no_grad():
        factors.B.fill_(0.01)
    reference.zero_grad(set_to_none=True)
    expected = base(x) + (x @ factors.A.T) @ factors.B.T
    torch.testing.assert_close(project(x), expected, rtol=0, atol=0)
    project(x).square().sum().backward()
    assert torch.count_nonzero(factors.A.grad) > 0
    assert torch.equal(original, base.weight)
    assert not base.weight.requires_grad


@pytest.mark.parametrize("seed", [True, -1, 2**63, 1.5])
def test_invalid_seed(seed):
    with pytest.raises(ValueError):
        ReferenceQVLoRA(seed=seed)


@pytest.mark.parametrize("layer,target", [(True, "q"), (-1, "q"), (30, "v"), (0, "k")])
def test_invalid_binding_selection(layer, target):
    with pytest.raises(ValueError):
        ReferenceQVLoRA(seed=1).bind_projection(
            layer=layer, target=target, base=frozen_projection("q")
        )


def test_binding_rejects_trainable_or_wrong_geometry():
    reference = ReferenceQVLoRA(seed=1)
    with pytest.raises(ValueError):
        reference.bind_projection(layer=0, target="q", base=nn.Linear(576, 576))
    with pytest.raises(ValueError):
        reference.bind_projection(layer=0, target="v", base=frozen_projection("q"))


def test_binding_captures_factors_and_rechecks_execution_contract():
    reference = ReferenceQVLoRA(seed=1)
    base = frozen_projection("v")
    project = reference.bind_projection(layer=0, target="v", base=base)
    x = torch.randn(1, 576)
    captured = reference.factors["0"]["v"]
    reference.factors["0"]["v"] = ReferenceQVLoRA(seed=2).factors["0"]["v"]
    with torch.no_grad():
        captured.B.fill_(0.1)
    assert not torch.equal(project(x), base(x))
    with pytest.raises(ValueError):
        project(torch.zeros(1, 575))
    captured.to(dtype=torch.float64)
    with pytest.raises(ValueError):
        project(x)
