"""Ambient-setting guard fixtures; CPU only, no model/assets/optimizer."""

from contextlib import contextmanager

import pytest
import torch
from torch import nn

from aluclu.alc_r0.checkpoint_execution import (
    CheckpointController,
    CheckpointExecutionError,
)
from aluclu.alc_r0.checkpoint_state import computational_state_fingerprint


def make_owner():
    owner = nn.Module()
    owner.base = nn.Linear(2, 2).requires_grad_(False).eval()
    owner.factors = nn.Linear(2, 2, bias=False)

    def getter():
        return computational_state_fingerprint(
            {"base": owner.base, "factors": owner.factors}
        )

    controller = CheckpointController(
        owner,
        base_getter=lambda: owner.base,
        factor_getter=lambda: owner.factors,
        layer_count=1,
        state_fingerprint_getter=getter,
    )
    return owner, controller, getter


SDP = {
    "flash": ("flash_sdp_enabled", "enable_flash_sdp"),
    "math": ("math_sdp_enabled", "enable_math_sdp"),
    "memory": ("mem_efficient_sdp_enabled", "enable_mem_efficient_sdp"),
    "cudnn": ("cudnn_sdp_enabled", "enable_cudnn_sdp"),
    "reduction": (
        "fp16_bf16_reduction_math_sdp_allowed",
        "allow_fp16_bf16_reduction_math_sdp",
    ),
}
MATMUL = (
    "allow_tf32",
    "allow_fp16_reduced_precision_reduction",
    "allow_bf16_reduced_precision_reduction",
)
CUDNN = ("enabled", "benchmark", "deterministic", "allow_tf32")
CASES = ["dtype", "precision", "deterministic", "threads"]
CASES += [f"sdp:{key}" for key in SDP]
CASES += [f"matmul:{key}" for key in MATMUL]
CASES += [f"cudnn:{key}" for key in CUDNN]


@contextmanager
def changed_setting(kind):
    if kind == "dtype":
        original = torch.get_default_dtype()
        setter, changed = (
            torch.set_default_dtype,
            (torch.float64 if original != torch.float64 else torch.float32),
        )
    elif kind == "precision":
        original = torch.get_float32_matmul_precision()
        setter, changed = (
            torch.set_float32_matmul_precision,
            ("high" if original == "highest" else "highest"),
        )
    elif kind == "deterministic":
        original = torch.are_deterministic_algorithms_enabled()
        warn_only = torch.is_deterministic_algorithms_warn_only_enabled()

        def setter(value):
            torch.use_deterministic_algorithms(value, warn_only=warn_only)

        changed = not original
    elif kind == "threads":
        original = torch.get_num_threads()
        setter, changed = torch.set_num_threads, (1 if original != 1 else 2)
    else:
        group, name = kind.split(":")
        if group == "sdp":
            getter_name, setter_name = SDP[name]
            original = getattr(torch.backends.cuda, getter_name)()
            setter = getattr(torch.backends.cuda, setter_name)
        else:
            target = (
                torch.backends.cuda.matmul
                if group == "matmul"
                else torch.backends.cudnn
            )
            original = getattr(target, name)

            def setter(value):
                setattr(target, name, value)

        changed = not original
    try:
        setter(changed)
        yield
    finally:
        setter(original)


@pytest.mark.parametrize("kind", CASES)
@pytest.mark.parametrize("phase", ["preparation", "replay"])
def test_runtime_drift_denied_before_side_effect(kind, phase):
    owner, controller, getter = make_owner()
    before = getter()
    calls = []
    with pytest.raises(CheckpointExecutionError):
        with controller.session() as session:
            if phase == "replay":
                ticket = session.begin_forward(owner, {"position_ids": torch.zeros(1)})

                def block(hidden, metadata):
                    calls.append(1)
                    return owner.factors(hidden).square()

                output = ticket.run(0, block, torch.ones(1, 2))
                ticket.bind_output(output)
            with changed_setting(kind):
                for parameter in owner.factors.parameters():
                    parameter.grad = torch.ones_like(parameter)
                if phase == "preparation":
                    session.begin_forward(owner, {"position_ids": torch.zeros(1)})
                    calls.append(1)
                else:
                    session.backward(output.sum())
    assert calls == ([] if phase == "preparation" else [1])
    assert controller._active is None
    assert all(parameter.grad is None for parameter in owner.factors.parameters())
    assert getter() == before


@pytest.mark.parametrize("autocast", [False, True])
def test_preserved_autocast_context_allows_complete_session(autocast):
    owner, controller, getter = make_owner()
    before = getter()
    with controller.session() as session:
        ticket = session.begin_forward(owner, {"position_ids": torch.zeros(1)})
        with torch.autocast("cpu", dtype=torch.bfloat16, enabled=autocast):
            output = ticket.run(
                0,
                lambda hidden, metadata: owner.factors(hidden).square(),
                torch.ones(1, 2),
            )
            ticket.bind_output(output)
            assert getter() == before
            loss = output.float().sum()
        session.backward(loss)
    assert getter() == before
    assert all(parameter.grad is None for parameter in owner.base.parameters())
    assert all(
        parameter.grad is not None and torch.isfinite(parameter.grad).all()
        for parameter in owner.factors.parameters()
    )


def test_phase_grad_and_rng_are_not_ambient_drift_fields():
    _, _, getter = make_owner()
    before = getter()
    with torch.random.fork_rng(devices=[]):
        torch.rand(3)
        with torch.no_grad():
            assert getter() == before
    assert getter() == before


@pytest.mark.parametrize("phase", ["preparation", "replay"])
def test_runtime_getter_replacement_denied_even_with_equal_value(phase, monkeypatch):
    owner, controller, _ = make_owner()
    value = torch.get_float32_matmul_precision()
    calls = []
    with pytest.raises(CheckpointExecutionError):
        with controller.session() as session:
            if phase == "replay":
                ticket = session.begin_forward(owner, {"position_ids": torch.zeros(1)})

                def block(hidden, metadata):
                    calls.append(1)
                    return owner.factors(hidden).square()

                output = ticket.run(0, block, torch.ones(1, 2))
                ticket.bind_output(output)
            monkeypatch.setattr(torch, "get_float32_matmul_precision", lambda: value)
            if phase == "preparation":
                session.begin_forward(owner, {"position_ids": torch.zeros(1)})
                calls.append(1)
            else:
                session.backward(output.sum())
    assert calls == ([] if phase == "preparation" else [1])
    assert controller._active is None
    assert all(parameter.grad is None for parameter in owner.factors.parameters())


@pytest.mark.parametrize(
    "name,value",
    [
        ("get_default_dtype", "float32"),
        ("get_default_device", "cpu"),
        ("get_float32_matmul_precision", "unknown"),
        ("are_deterministic_algorithms_enabled", 1),
        ("get_num_threads", True),
        ("get_num_threads", 0),
        ("get_num_interop_threads", 65537),
        ("is_deterministic_algorithms_warn_only_enabled", None),
        ("get_default_dtype", object()),
    ],
)
def test_unsupported_runtime_values_rejected(name, value, monkeypatch):
    _, _, getter = make_owner()
    monkeypatch.setattr(torch, name, lambda: value)
    with pytest.raises(CheckpointExecutionError, match="runtime setting"):
        getter()
