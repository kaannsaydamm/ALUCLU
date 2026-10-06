"""Random thin-MLP CPU Llama wiring, NOT pretrained SmolLM2 qualification.

All 30 q/v dimensions, full 49152 logits and the original 72-row schedule are
retained. Smaller random embedding/MLP/factorized head are explicitly test-only;
no assets, tokenizer, data, CUDA, checkpoint backward or optimizer are accessed.
"""

from types import SimpleNamespace

import pytest
import torch
from alc_r0_random_qv_host import random_cpu_host

from aluclu.alc_r0.checkpoint_observation import _base_digest
from aluclu.alc_r0.checkpoint_official_forward import _case, _nonzero_witness
from aluclu.alc_r0.checkpoint_parity_factory import make_reference_wrapper
from aluclu.alc_r0.reference_official_suite import (
    REFERENCE_SCHEDULE,
    run_reference_official_suite,
    validate_reference_official_suite,
)


@pytest.fixture(scope="module")
def host():
    rng, threads = torch.get_rng_state().clone(), torch.get_num_threads()

    def forbidden(*args, **kwargs):
        pytest.fail("CPU fixture must not initialize or seed CUDA")

    with pytest.MonkeyPatch.context() as gpu_guard:
        gpu_guard.setattr(torch.cuda, "manual_seed_all", forbidden)
        gpu_guard.setattr(torch.cuda, "_lazy_init", forbidden)
        with random_cpu_host() as result:
            yield result
    assert torch.equal(rng, torch.get_rng_state())
    assert torch.get_num_threads() == threads


def test_all72_real_forward_rows_witness_and_detach(host):
    base_digest = _base_digest(host.model)
    result = run_reference_official_suite(host, exact=True)
    validate_reference_official_suite(result)
    assert tuple((row.key, row.case) for row in result.cases) == REFERENCE_SCHEDULE
    assert len(result.cases) == 72
    assert sum(row.case.cached for row in result.cases) == 12
    assert sum(row.case.batch == 2 for row in result.cases) == 36
    assert sum(row.case.explicit_positions for row in result.cases) == 30
    assert result.witness.official_sha256 != result.witness.mounted_sha256
    assert result.base_digest == _base_digest(host.model) == base_digest
    assert all(p.grad is None and not p.requires_grad for p in host.model.parameters())


def test_actual_noop_mount_cannot_pass_witness(host):
    wrapper = make_reference_wrapper(host, False, state="zero").eval()
    with torch.inference_mode(), pytest.raises(ValueError, match="nonzero"):
        _nonzero_witness(wrapper, torch.device("cpu"))


def test_actual_cache_forward_then_corrupt_receipt_is_rejected(host, monkeypatch):
    wrapper = make_reference_wrapper(host, False, state="zero").eval()
    original = wrapper.forward

    def corrupt(**kwargs):
        result = original(**kwargs)
        if result.past_key_values is not None:
            result.past_key_values = SimpleNamespace(get_seq_length=lambda: 0)
        return result

    monkeypatch.setattr(wrapper, "forward", corrupt)
    key, case = REFERENCE_SCHEDULE[21]
    with torch.inference_mode(), pytest.raises(ValueError, match="sequence length"):
        _case(wrapper, key, case, exact=True)


def test_random_fixture_restores_rng_and_threads_on_exception():
    rng, threads = torch.get_rng_state().clone(), torch.get_num_threads()
    with pytest.raises(RuntimeError, match="deliberate fixture exit"):
        with random_cpu_host():
            raise RuntimeError("deliberate fixture exit")
    assert torch.equal(rng, torch.get_rng_state())
    assert torch.get_num_threads() == threads
