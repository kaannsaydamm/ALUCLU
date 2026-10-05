"""Full120-factor CPU integration on30 substituted fake decoder blocks.

The executor's4096 schedule/preflight remain real. ONLY microbatch input is
explicitly mapped to4/5tokens before calling the real helper; all32 forwards,
owned replay/backwards, clipping, optimizer and state checks execute. Random
fake base,8-token embedding,49152-output head and RMS-normalized fake blocks
are NOT SmolLM2/official-forward parity or4096 attention/resource/E3 evidence.
"""

from dataclasses import replace

import pytest
import torch
from test_alc_r0_reference_qv_forward import host as host
from torch import nn

from aluclu.alc_r0 import reference_stress_execution as execution
from aluclu.alc_r0.checkpoint_observation import _base_digest
from aluclu.alc_r0.checkpoint_parity_factory import make_reference_wrapper
from aluclu.alc_r0.reference_qv_artifact import serialize_reference
from aluclu.alc_r0.reference_stress_inputs import StressInput, build_stress_schedule


@pytest.mark.parametrize("corrupt_second_step", [False, True])
def test_full_factors_real_preflight_replay_two_updates(
    host, monkeypatch, corrupt_second_step
):
    for layer in host.model.model.layers:
        layer.input_layernorm = nn.RMSNorm(576, eps=1e-5, elementwise_affine=False)
        layer.post_attention_layernorm = nn.RMSNorm(
            576, eps=1e-5, elementwise_affine=False
        )
    with torch.random.fork_rng(devices=[]):
        torch.manual_seed(20261005)
        host.model.lm_head = nn.Linear(576, 49152, bias=False)
    host.model.config.vocab_size = 49152
    host.model.config.max_position_embeddings = 8192
    host.model.requires_grad_(False).eval()
    host = replace(
        host, parameter_count=sum(p.numel() for p in host.model.parameters())
    )
    wrapper = make_reference_wrapper(host, True, state="zero")
    schedule = build_stress_schedule(
        prefix_ids=(1,), suffix_ids=(4,), safe_ids=(5,), vulnerable_ids=(6, 7)
    )
    initial = serialize_reference(wrapper.reference)
    base_digest = _base_digest(wrapper.base)
    created, observed = [], []
    original_factory = execution.make_reference_optimizer
    original_microbatch = execution._microbatch

    def factory(owner):
        optimizer = original_factory(owner)
        created.append(optimizer)
        if corrupt_second_step:
            original_step = optimizer.step
            calls = 0

            def step():
                nonlocal calls
                calls += 1
                original_step()
                if calls == 2:
                    next(iter(optimizer.state.values()))["step"].fill_(1)

            optimizer.step = step
        return optimizer

    def short_microbatch(owner, item, device):
        assert item is schedule.inputs[len(observed) % 16]
        assert len(item.input_ids) in (4095, 4096)
        prompt, candidate = (1, 2, 4), item.candidate_ids
        short = StressInput(
            label=item.label,
            input_ids=prompt + candidate,
            attention_mask=(1,) * (len(prompt) + len(candidate)),
            labels=(-100,) * len(prompt) + candidate,
            position_ids=tuple(range(len(prompt) + len(candidate))),
            prompt_length=len(prompt),
            candidate_ids=candidate,
        )
        value = original_microbatch(owner, short, device)
        assert owner._checkpoint_controller._active is None
        gradients = tuple(owner.reference.named_parameters())
        assert len(gradients) == 120
        assert all(
            p.grad is not None and torch.isfinite(p.grad).all() for _, p in gradients
        )
        if not observed:
            assert all(
                torch.count_nonzero(p.grad).item() == 0
                for n, p in gradients
                if n.endswith(".A")
            )
            assert any(
                torch.count_nonzero(p.grad).item()
                for n, p in gradients
                if n.endswith(".B")
            )
        observed.append(item.label)
        return value

    monkeypatch.setattr(execution, "make_reference_optimizer", factory)
    monkeypatch.setattr(execution, "_microbatch", short_microbatch)
    if corrupt_second_step:
        with pytest.raises(execution.StressExecutionError) as caught:
            execution.execute_reference_stress(wrapper, schedule)
        progress = caught.value.progress
        assert progress.stage == "optimizer_state"
        assert progress.completed_updates == 1
        assert progress.attempted_steps == progress.returned_steps == 2
    else:
        result = execution.execute_reference_stress(wrapper, schedule)
        progress = result.progress
        assert progress.stage == "complete" and progress.completed_updates == 2
        assert (
            result.start.factor_count == 120 and result.start.parameter_count == 460800
        )
        assert result.start.sequence_lengths == (4095, 4096) * 8
        assert [update.step for update in result.updates] == [1, 2]
        assert result.updates[0].factor_digest != result.updates[1].factor_digest
        assert result.updates[0].moment_digest != result.updates[1].moment_digest
        assert all(
            float(state["step"].item()) == 2 for state in created[0].state.values()
        )
        assert all(p.grad is None for p in wrapper.reference.parameters())
    assert len(created) == 1 and len(created[0].state) == 120
    assert progress.attempted_microbatches == progress.completed_microbatches == 32
    assert observed == ["safe", "vulnerable"] * 16
    assert serialize_reference(wrapper.reference) != initial
    assert _base_digest(wrapper.base) == base_digest
    assert all(
        p.grad is None and not p.requires_grad for p in wrapper.base.parameters()
    )
    wrapper._assert_checkpoint_mutation_allowed()
