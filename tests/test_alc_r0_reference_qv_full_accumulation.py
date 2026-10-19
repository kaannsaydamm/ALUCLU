"""Fake 30-block CPU q/v integration with the fixed16-microbatch runner.

Parameter-free RMS normalizers bound the synthetic full-depth activations.
This is not the official SmolLM2 architecture/assets, actual-host parity,
4096-token E3, a learned capability, optimizer resume or fresh-process proof.
"""

import torch
from test_alc_r0_reference_qv_forward import host as host
from torch import nn

from aluclu.alc_r0.checkpoint_accumulation_pair import run_accumulation_pair
from aluclu.alc_r0.checkpoint_observation import _base_digest
from aluclu.alc_r0.checkpoint_parity_factory import make_reference_wrapper
from aluclu.alc_r0.checkpoint_parity_inputs import ParityInput
from aluclu.alc_r0.reference_qv_artifact import serialize_reference


def test_thirty_qv_blocks_fixed_accumulation_pipeline(host):
    # Keep all thirty distinct projections and the frozen base. Stabilize this
    # fake fixture before any observation, not by weakening gradient rules.
    for layer in host.model.model.layers:
        layer.input_layernorm = nn.RMSNorm(576, eps=1e-5, elementwise_affine=False)
        layer.post_attention_layernorm = nn.RMSNorm(
            576, eps=1e-5, elementwise_affine=False
        )
    host.model.eval()
    prompt = (1,) + (2, 3) * 30 + (4,)
    pair = tuple(
        ParityInput(
            input_ids=prompt + candidate,
            attention_mask=(1,) * (len(prompt) + len(candidate)),
            labels=(-100,) * len(prompt) + candidate,
            position_ids=tuple(range(len(prompt) + len(candidate))),
            prompt_length=len(prompt),
            candidate_ids=candidate,
        )
        for candidate in ((5,), (6, 7))
    )
    fixtures = pair * 8
    before_base = _base_digest(host.model)
    created, initial_records = [], []

    def factory(checkpoint):
        wrapper = make_reference_wrapper(host, checkpoint, state="nonzero")
        created.append(wrapper)
        initial_records.append(serialize_reference(wrapper.reference))
        return wrapper

    result = run_accumulation_pair(factory, fixtures, exact=True)
    assert len(created) == 2
    assert result.comparison.step == 1
    assert len(result.comparison.factors) == 120
    assert len(result.comparison.exp_avg) == len(result.comparison.exp_avg_sq) == 120
    for wrapper, initial, step in zip(
        created, initial_records, (result.reference, result.actual), strict=True
    ):
        assert len(step.observation.forwards) == 16
        assert tuple(item.fixture for item in step.observation.forwards) == fixtures
        assert step.observation.forwards[0].base_digest == before_base
        assert torch.isfinite(step.observation.averaged_loss)
        assert serialize_reference(wrapper.reference) != initial
        assert len(step.optimizer.state) == 120
        assert all(float(state["step"]) == 1 for state in step.optimizer.state.values())
    assert serialize_reference(created[0].reference) == serialize_reference(
        created[1].reference
    )
    assert created[1]._checkpoint_controller._active is None
    assert _base_digest(host.model) == before_base
    assert all(p.grad is None and not p.requires_grad for p in host.model.parameters())
