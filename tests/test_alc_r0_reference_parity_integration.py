"""Real random CPU q/v forward/backward/step, NOT pretrained learning evidence.

No factory/cell/observation/comparator substitution. Random thin-MLP host keeps
30 attention blocks, all120 rank8 q/v factors and full49152-output logits.
Test-only host deviations are declared in alc_r0_random_qv_host.py.
"""

from dataclasses import asdict

import pytest
import torch
from alc_r0_random_qv_host import random_cpu_host
from test_alc_r0_parity_cell import fixtures

from aluclu.alc_r0.checkpoint_parity_cell import SINGLE_SCHEDULE
from aluclu.alc_r0.reference_official_suite import _base_digest, _json_digest
from aluclu.alc_r0.reference_parity_receipt import (
    REFERENCE_NAMES,
    validate_reference_parity_receipt,
)
from aluclu.alc_r0.reference_parity_suite import run_reference_parity_suite


def test_full_random_qv_cell_real_backward_pending_and_adamw():
    def forbidden(*args, **kwargs):
        pytest.fail("random CPU integration must not initialize or seed CUDA")

    def forbidden_seed(*args, **kwargs):
        pytest.fail("random CPU integration must not seed CUDA")

    rng, threads = torch.get_rng_state().clone(), torch.get_num_threads()
    with pytest.MonkeyPatch.context() as gpu_guard:
        gpu_guard.setattr(torch.cuda, "manual_seed_all", forbidden_seed)
        gpu_guard.setattr(torch.cuda, "_lazy_init", forbidden)
        with random_cpu_host() as host:
            before = _base_digest(host.model)
            inputs = fixtures()
            result = run_reference_parity_suite(
                host,
                inputs,
                exact=True,
                expected_fixture_digest=_json_digest([asdict(f) for f in inputs]),
            )
            validate_reference_parity_receipt(result, expected_identity=result.identity)
            assert (
                tuple(
                    (row.state, row.repeat, row.fixture_index)
                    for row in result.cell.cases
                )
                == SINGLE_SCHEDULE
            )
            assert result.cell.parameter_names == REFERENCE_NAMES
            assert result.cell.parameter_count == 460800
            assert result.cell.accumulation.step == 1
            for field in ("factors", "exp_avg", "exp_avg_sq"):
                assert (
                    tuple(name for name, _ in getattr(result.cell.accumulation, field))
                    == REFERENCE_NAMES
                )
            assert result.identity.base_digest == result.cell.base_digest == before
            assert _base_digest(host.model) == before
            assert all(
                p.grad is None and not p.requires_grad for p in host.model.parameters()
            )
    assert torch.equal(rng, torch.get_rng_state())
    assert torch.get_num_threads() == threads
