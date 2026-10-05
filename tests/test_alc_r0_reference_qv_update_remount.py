"""Disposable full fake CPU q/v updates and same-process factor remount.

No real host, task data, 16-microbatch E3, optimizer resume, fresh-process
restart, learned capability or final .alc container is demonstrated here.
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


def test_full_qv_two_updates_and_factor_remount_exact(host):
    off = make_reference_wrapper(host, False, state="zero")
    on = make_reference_wrapper(host, True, state="zero")
    optimizers = [make_reference_optimizer(wrapper) for wrapper in (off, on)]
    initial_record = serialize_reference(off.reference)
    base_digest = _base_digest(host.model)
    args = dict(
        input_ids=torch.tensor([[1, 2, 3, 0]]),
        labels=torch.tensor([[-100, 2, 3, -100]]),
        attention_mask=torch.tensor([[1, 1, 1, 0]]),
        position_ids=torch.tensor([[3, 4, 5, 6]]),
        use_cache=False,
    )
    for step in (1, 2):
        for optimizer in optimizers:
            optimizer.zero_grad(set_to_none=True)
        expected = off(**args)
        expected.loss.backward()
        with on.checkpoint_session() as session:
            actual = on(**args, checkpoint_session=session)
            session.backward(actual.loss)
            assert session.pending_count == 0
        assert torch.equal(actual.logits, expected.logits)
        assert torch.equal(actual.loss, expected.loss)
        assert torch.isfinite(actual.loss)
        for left, right in zip(
            off.reference.parameters(), on.reference.parameters(), strict=True
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
            for wrapper in (off, on)
        ]
        assert torch.equal(*norms)
        for optimizer in optimizers:
            optimizer.step()
        comparison = compare_reference_optimizer_states(
            off, optimizers[0], on, optimizers[1], expected_step=step, exact=True
        )
        assert len(comparison.factors) == 120
        assert len(comparison.exp_avg) == len(comparison.exp_avg_sq) == 120
        assert _base_digest(host.model) == base_digest
        assert all(
            p.grad is None and not p.requires_grad for p in host.model.parameters()
        )
    record = serialize_reference(on.reference)
    assert record == serialize_reference(off.reference)
    assert record != initial_record
    restored = deserialize_reference(*record)
    remounted = make_reference_wrapper(host, False, state="zero")
    remounted.mount_reference(restored)
    assert serialize_reference(remounted.reference) == record
    for original, loaded in zip(
        on.reference.parameters(), restored.parameters(), strict=True
    ):
        assert torch.equal(original, loaded)
        assert original.data_ptr() != loaded.data_ptr()
    with torch.no_grad():
        updated = off(**args)
        reloaded = remounted(**args)
    assert torch.equal(updated.logits, reloaded.logits)
    assert torch.equal(updated.loss, reloaded.loss)
    assert _base_digest(host.model) == base_digest
