"""Tiny real CPU AdamW accelerator isolation, not model training/evaluation."""

import os

import torch


def test_cpu_adamw_step_never_initializes_cuda(monkeypatch):
    assert os.environ.get("CUDA_VISIBLE_DEVICES") == "-1"
    def forbidden(*args, **kwargs):
        raise RuntimeError("CPU optimizer must not initialize or seed CUDA")

    def forbidden_seed(*args, **kwargs):
        raise RuntimeError("CPU optimizer must not seed CUDA")

    monkeypatch.setattr(torch.cuda, "_lazy_init", forbidden)
    monkeypatch.setattr(torch.cuda, "manual_seed_all", forbidden_seed)
    parameter = torch.nn.Parameter(torch.tensor([1.0, -1.0], device="cpu"))
    before = parameter.detach().clone()
    parameter.grad = torch.tensor([0.25, -0.5], device="cpu")
    optimizer = torch.optim.AdamW(
        [parameter],
        lr=3e-4,
        betas=(0.9, 0.999),
        eps=1e-8,
        weight_decay=0,
        foreach=False,
        fused=False,
    )
    torch.nn.utils.clip_grad_norm_(
        [parameter], 1.0, error_if_nonfinite=True, foreach=False
    )
    optimizer.step()
    assert not torch.equal(parameter, before)
    assert not torch.cuda.is_initialized()
    assert torch.accelerator.current_accelerator(check_available=True) is None
    assert parameter.device.type == "cpu"
    state = optimizer.state[parameter]
    assert state["step"].item() == 1
    assert all(
        value.device.type == "cpu" and torch.isfinite(value).all()
        for value in state.values()
    )
