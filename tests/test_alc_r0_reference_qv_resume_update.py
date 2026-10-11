"""Full30 fake CPU step1 export -> step2 continuation, not learning evidence.

Random fake host/type substitution, one padded forward per update, shared
frozen base and same-process remount only. No real assets, task data, GPU,
stochastic/cursor resume, fresh process, E3 or final .alc acceptance.
"""

import torch
from test_alc_r0_reference_qv_forward import host as host

from aluclu.alc_r0.checkpoint_observation import _base_digest
from aluclu.alc_r0.checkpoint_parity_factory import make_reference_wrapper
from aluclu.alc_r0.reference_qv_artifact import (
    deserialize_reference,
    make_reference_optimizer,
    serialize_reference,
)
from aluclu.alc_r0.reference_qv_optimizer import compare_reference_optimizer_states
from aluclu.alc_r0.reference_qv_resume import (
    restore_reference_optimizer,
    serialize_reference_resume,
)


def test_full_qv_step2_after_moment_restore_matches_uninterrupted(host):
    uninterrupted = make_reference_wrapper(host, False, state="zero")
    optimizer = make_reference_optimizer(uninterrupted)
    base_digest = _base_digest(host.model)
    initial_factors = serialize_reference(uninterrupted.reference)
    first = dict(
        input_ids=torch.tensor([[1, 2, 3, 0]]),
        labels=torch.tensor([[-100, 2, 3, -100]]),
        attention_mask=torch.tensor([[1, 1, 1, 0]]),
        position_ids=torch.tensor([[3, 4, 5, 6]]),
        use_cache=False,
    )
    output = uninterrupted(**first)
    assert torch.isfinite(output.loss)
    output.loss.backward()
    norm = torch.nn.utils.clip_grad_norm_(
        uninterrupted.reference.parameters(),
        1.0,
        error_if_nonfinite=True,
        foreach=False,
    )
    assert torch.isfinite(norm)
    optimizer.step()
    optimizer.zero_grad(set_to_none=True)
    record = serialize_reference_resume(uninterrupted, optimizer)
    assert (record.factor_manifest, record.factor_payload) != initial_factors
    assert any(
        torch.count_nonzero(state["exp_avg"]).item()
        for state in optimizer.state.values()
    )

    resumed = make_reference_wrapper(host, True, state="zero")
    resumed.mount_reference(
        deserialize_reference(
            record.factor_manifest,
            record.factor_payload,
        )
    )
    resumed_optimizer = restore_reference_optimizer(resumed, record)
    step1 = compare_reference_optimizer_states(
        uninterrupted,
        optimizer,
        resumed,
        resumed_optimizer,
        expected_step=1,
        exact=True,
    )
    assert len(step1.factors) == len(step1.exp_avg) == len(step1.exp_avg_sq) == 120
    assert serialize_reference_resume(resumed, resumed_optimizer) == record
    for left, right in zip(
        uninterrupted.reference.parameters(),
        resumed.reference.parameters(),
        strict=True,
    ):
        assert left.data_ptr() != right.data_ptr()
        for role in ("step", "exp_avg", "exp_avg_sq"):
            assert optimizer.state[left][role].data_ptr() != (
                resumed_optimizer.state[right][role].data_ptr()
            )

    second = dict(
        input_ids=torch.tensor([[4, 5, 6, 0]]),
        labels=torch.tensor([[-100, 5, 6, -100]]),
        attention_mask=torch.tensor([[1, 1, 1, 0]]),
        position_ids=torch.tensor([[11, 12, 13, 14]]),
        use_cache=False,
    )
    expected = uninterrupted(**second)
    expected.loss.backward()
    with resumed.checkpoint_session() as session:
        actual = resumed(**second, checkpoint_session=session)
        session.backward(actual.loss)
        assert session.pending_count == 0
    assert torch.equal(actual.logits, expected.logits)
    assert torch.equal(actual.loss, expected.loss)
    assert torch.isfinite(actual.loss)
    for left, right in zip(
        uninterrupted.reference.parameters(),
        resumed.reference.parameters(),
        strict=True,
    ):
        assert torch.equal(left.grad, right.grad)
        assert torch.isfinite(left.grad).all()
    norms = [
        torch.nn.utils.clip_grad_norm_(
            wrapper.reference.parameters(),
            1.0,
            error_if_nonfinite=True,
            foreach=False,
        )
        for wrapper in (uninterrupted, resumed)
    ]
    assert torch.equal(*norms)
    for current in (optimizer, resumed_optimizer):
        current.step()
        current.zero_grad(set_to_none=True)
    step2 = compare_reference_optimizer_states(
        uninterrupted,
        optimizer,
        resumed,
        resumed_optimizer,
        expected_step=2,
        exact=True,
    )
    assert len(step2.factors) == len(step2.exp_avg) == len(step2.exp_avg_sq) == 120
    factors = serialize_reference(uninterrupted.reference)
    assert factors == serialize_reference(resumed.reference)
    assert factors != (record.factor_manifest, record.factor_payload)
    with torch.no_grad():
        expected_after = uninterrupted(**second)
        actual_after = resumed(**second)
    assert torch.equal(actual_after.logits, expected_after.logits)
    assert torch.equal(actual_after.loss, expected_after.loss)
    assert _base_digest(host.model) == base_digest
    assert all(p.grad is None and not p.requires_grad for p in host.model.parameters())
    assert all(p.grad is None for p in resumed.reference.parameters())
    uninterrupted._assert_checkpoint_mutation_allowed()
    resumed._assert_checkpoint_mutation_allowed()
