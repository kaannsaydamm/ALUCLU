"""All120 q/v factors through a synthetic scalar block, not host attention/E3.

Actual CPU AdamW steps are disposable fixture updates. One scalar fixture block
uses every fixed-shape factor; it is NOT thirty real decoder blocks or learning.
"""

import pytest
import torch
from test_alc_r0_accumulation_observation import fixtures
from test_alc_r0_checkpoint_observation import TinyWrapper

from aluclu.alc_r0.checkpoint_accumulation_pair import run_accumulation_pair
from aluclu.alc_r0.checkpoint_accumulation_step import step_accumulation
from aluclu.alc_r0.checkpoint_observation import observe_accumulation
from aluclu.alc_r0.reference_qv_lora import ReferenceQVLoRA


class ScalarQVWrapper(TinyWrapper):
    def __init__(self, base=None):
        super().__init__(True)
        if base is not None:
            self.base = base
        self.factors = ReferenceQVLoRA(seed=17)
        with torch.no_grad():
            for layer in self.factors.factors.values():
                for factor in layer.values():
                    factor.B.fill_(0.01)
        self.train()
        self.base.eval()

    def forward(self, **kwargs):
        from types import SimpleNamespace

        assert kwargs["use_cache"] is False
        input_ids, labels = kwargs["input_ids"], kwargs["labels"]
        hidden = torch.ones((*input_ids.shape, 2))

        def scalar_block(value, metadata):
            contribution = None
            for layer in self.factors.factors.values():
                for factor in layer.values():
                    delta = factor.A.mean() * factor.B.mean()
                    contribution = (
                        delta if contribution is None else contribution + delta
                    )
            return value * (1 + contribution)

        session = kwargs.get("checkpoint_session")
        if session is None:
            hidden = scalar_block(hidden, None)
        else:
            ticket = session.begin_forward(self, {"labels": labels})
            hidden = ticket.run(0, scalar_block, hidden)
        logits = hidden.sum(-1, keepdim=True).expand(*input_ids.shape, 128)
        if session is not None:
            ticket.bind_output(logits)
        return SimpleNamespace(loss=logits[labels != -100].sum(), logits=logits)


def test_all_qv_factors_accumulate_and_step_exact_off_on():
    base = ScalarQVWrapper().base
    created, initial = [], []

    def factory(checkpoint):
        wrapper = ScalarQVWrapper(base)
        created.append(wrapper)
        initial.append(
            {name: p.detach().clone() for name, p in wrapper.factors.named_parameters()}
        )
        return wrapper

    result = run_accumulation_pair(factory, fixtures(), exact=True)
    assert len(result.comparison.factors) == 120
    assert len(result.comparison.exp_avg) == len(result.comparison.exp_avg_sq) == 120
    for wrapper, before, step in zip(
        created, initial, (result.reference, result.actual), strict=True
    ):
        assert len(step.observation.forwards) == 16
        for name, parameter in wrapper.factors.named_parameters():
            assert not torch.equal(parameter, before[name])
            assert float(step.optimizer.state[parameter]["step"]) == 1
        assert (
            step.observation.forwards[0].base_digest
            == result.reference.observation.forwards[0].base_digest
        )
    assert all(p.grad is None for p in base.parameters())


@pytest.mark.parametrize("bad", ["late_gradient", "active_lease"])
def test_qv_step_preconditions_preserve_all_factors(bad):
    wrapper = ScalarQVWrapper()
    observation = observe_accumulation(wrapper, fixtures(), checkpoint=False)
    before = {
        name: p.detach().clone() for name, p in wrapper.factors.named_parameters()
    }
    if bad == "late_gradient":
        wrapper.factors.factors["29"]["v"].B.grad.add_(1)
        with pytest.raises(ValueError):
            step_accumulation(wrapper, observation)
    else:
        with wrapper.checkpoint_session():
            with pytest.raises(ValueError):
                step_accumulation(wrapper, observation)
    assert all(
        torch.equal(p, before[name]) for name, p in wrapper.factors.named_parameters()
    )
