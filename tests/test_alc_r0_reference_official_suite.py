"""Real guards/factors with stubbed forwards; no host conformance evidence."""

import importlib
from dataclasses import replace

import pytest
import torch
from torch import nn
from transformers import LlamaConfig

from aluclu.alc_r0.checkpoint_official_forward import OfficialCase
from aluclu.alc_r0.checkpoint_parity_factory import PARITY_SEED
from aluclu.alc_r0.host import VerifiedHost
from aluclu.alc_r0.reference_qv_lora import ReferenceQVLoRA
from aluclu.alc_r0.reference_qv_wrapper import PinnedLlamaQVReferenceWrapper


@pytest.fixture
def wiring(monkeypatch):
    module = importlib.import_module("aluclu.alc_r0.reference_official_suite")
    base = nn.Linear(576, 8, bias=False).requires_grad_(False).eval()
    base.config = LlamaConfig(vocab_size=49152, max_position_embeddings=8192)
    base.config._attn_implementation = "eager"
    host = VerifiedHost(base, {"fixture": True}, {"fixture": True}, 4608, 0)
    calls = []

    def make(host, checkpoint, *, state):
        assert checkpoint is False and state == "zero"
        assert not torch.is_inference_mode_enabled()
        result = PinnedLlamaQVReferenceWrapper.__new__(PinnedLlamaQVReferenceWrapper)
        nn.Module.__init__(result)
        result.base, result.capsule = host.model, None
        result.reference = ReferenceQVLoRA(seed=PARITY_SEED)
        calls.append("make")
        return result.eval()

    def observe(wrapper, key, case, *, exact):
        assert exact is True and torch.is_inference_mode_enabled()
        assert not wrapper.training
        calls.append((key, case))
        increment = ("a" * 64, "a" * 64) if case.cached else (None, None)
        return OfficialCase(key, case, "a" * 64, "a" * 64, *increment)

    def witness(wrapper, device):
        assert torch.is_inference_mode_enabled()
        assert all(not p.is_inference() for p in wrapper.reference.parameters())
        assert all(
            torch.equal(p, torch.full_like(p, 0.01))
            for n, p in wrapper.reference.named_parameters()
            if n.endswith(".B")
        )
        calls.append("witness")
        return "a" * 64, "b" * 64

    monkeypatch.setattr(module, "make_reference_wrapper", make)
    monkeypatch.setattr(module, "_case", observe)
    monkeypatch.setattr(module, "_nonzero_witness", witness)
    return module, host, calls


def test_complete_separate_schedule_and_receipt(wiring):
    module, host, calls = wiring
    result = module.run_reference_official_suite(host, exact=True)
    module.validate_reference_official_suite(result)
    assert len(result.cases) == 72
    assert tuple((r.key, r.case) for r in result.cases) == module.REFERENCE_SCHEDULE
    assert calls.count("make") == 3 and calls.count("witness") == 1
    assert result.parameter_count == 460800 and len(result.parameter_names) == 120
    assert result.parameter_names.index(
        "factors.10.q.A"
    ) < result.parameter_names.index("factors.2.q.A")
    assert len(result.phase_factors) == 3
    assert len({r[1] for r in result.phase_factors}) == 1
    assert len({r[2] for r in result.phase_factors}) == 1


@pytest.mark.parametrize("index", [0, 24, 48, 71])
@pytest.mark.parametrize("interrupt", [False, True])
def test_failure_preserves_prefix_and_unrun(wiring, monkeypatch, index, interrupt):
    module, host, calls = wiring
    observe, attempted = module._case, []

    def fail(wrapper, key, case, *, exact):
        attempted.append((key, case))
        if len(attempted) == index + 1:
            raise KeyboardInterrupt() if interrupt else RuntimeError("deliberate")
        return observe(wrapper, key, case, exact=exact)

    monkeypatch.setattr(module, "_case", fail)
    error = (
        module.ReferenceOfficialInterrupted
        if interrupt
        else module.ReferenceOfficialError
    )
    with pytest.raises(error) as caught:
        module.run_reference_official_suite(host, exact=True)
    failure = caught.value.failure
    assert len(failure.completed) == index
    assert failure.current == module.REFERENCE_SCHEDULE[index]
    assert failure.unrun == module.REFERENCE_SCHEDULE[index + 1 :]
    assert failure.stage == "case"
    assert len(attempted) == index + 1


@pytest.mark.parametrize(
    "mutation", ["bytes", "buffer", "config", "metadata", "mode", "gradient", "factor"]
)
def test_mutated_state_not_admitted_as_completed(wiring, monkeypatch, mutation):
    module, host, _ = wiring
    observe = module._case

    def drift(wrapper, key, case, *, exact):
        result = observe(wrapper, key, case, exact=exact)
        if mutation == "bytes":
            wrapper.base.weight.data.add_(1)
        elif mutation == "buffer":
            wrapper.base.register_buffer("extra", torch.ones(1))
        elif mutation == "config":
            wrapper.base.config.vocab_size += 1
        elif mutation == "metadata":
            host.acquisition_receipt["fixture"] = False
        elif mutation == "mode":
            wrapper.base.train()
        elif mutation == "gradient":
            wrapper.base.weight.grad = torch.zeros_like(wrapper.base.weight)
        elif key.phase == "zero":
            wrapper.reference.factors["29"]["v"].B.data.add_(1)
        return result

    monkeypatch.setattr(module, "_case", drift)
    with pytest.raises(module.ReferenceOfficialError) as caught:
        module.run_reference_official_suite(host, exact=True)
    assert len(caught.value.failure.completed) == (24 if mutation == "factor" else 0)
    assert caught.value.failure.stage == "case-validation"


def test_witness_failure_keeps_detached_phase_unrun(wiring, monkeypatch):
    module, host, _ = wiring

    def fail(*args):
        raise RuntimeError("witness failed")

    monkeypatch.setattr(module, "_nonzero_witness", fail)
    with pytest.raises(module.ReferenceOfficialError) as caught:
        module.run_reference_official_suite(host, exact=True)
    assert len(caught.value.failure.completed) == 48
    assert caught.value.failure.unrun == module.REFERENCE_SCHEDULE[48:]
    assert caught.value.failure.stage == "witness"


@pytest.mark.parametrize(
    "field,value",
    [
        ("cases", ()),
        ("parameter_names", ()),
        ("parameter_count", True),
        ("source_device", "cuda:1"),
        ("base_digest", "x"),
        ("phase_factors", ()),
    ],
)
def test_partial_or_foreign_receipts_rejected(wiring, field, value):
    module, host, _ = wiring
    result = module.run_reference_official_suite(host, exact=True)
    with pytest.raises(ValueError):
        module.validate_reference_official_suite(replace(result, **{field: value}))


def test_reordered_rows_rejected(wiring):
    module, host, _ = wiring
    result = module.run_reference_official_suite(host, exact=True)
    with pytest.raises(ValueError):
        module.validate_reference_official_suite(
            replace(result, cases=tuple(reversed(result.cases)))
        )


@pytest.mark.parametrize("stage", ["preparation", "detach"])
def test_pre_case_failure_keeps_current_row_unrun(wiring, monkeypatch, stage):
    module, host, _ = wiring
    if stage == "preparation":

        def fail(*args, **kwargs):
            raise RuntimeError("construction failed")

        monkeypatch.setattr(module, "make_reference_wrapper", fail)
    else:
        monkeypatch.setattr(PinnedLlamaQVReferenceWrapper, "detach", lambda self: None)
    with pytest.raises(module.ReferenceOfficialError) as caught:
        module.run_reference_official_suite(host, exact=True)
    assert caught.value.failure.completed == ()
    assert caught.value.failure.unrun == module.REFERENCE_SCHEDULE


@pytest.mark.parametrize("mode", [False, 1, None])
def test_wrong_exact_mode_rejected_before_construction(wiring, mode):
    module, host, calls = wiring
    with pytest.raises((ValueError, module.ReferenceOfficialError)):
        module.run_reference_official_suite(host, exact=mode)
    assert calls == []


@pytest.mark.parametrize(
    "mutation", ["duplicate", "foreign", "bad_digest", "cache", "cpu_unequal"]
)
def test_bad_case_receipts_rejected(wiring, monkeypatch, mutation):
    module, host, _ = wiring
    observe = module._case

    def bad(wrapper, key, case, *, exact):
        row = observe(wrapper, key, case, exact=exact)
        if mutation in ("duplicate", "foreign"):
            return replace(row, key=replace(key, phase="elsewhere"))
        if mutation == "bad_digest":
            return replace(row, official_sha256="nan")
        if mutation == "cache":
            return replace(row, incremental_official_sha256="a" * 64)
        return replace(row, wrapper_sha256="b" * 64)

    monkeypatch.setattr(module, "_case", bad)
    with pytest.raises(module.ReferenceOfficialError) as caught:
        module.run_reference_official_suite(host, exact=True)
    assert caught.value.failure.completed == ()
    assert caught.value.failure.stage == "case-validation"


def test_byte_identical_base_replacement_at_last_row_rejected(wiring, monkeypatch):
    module, host, _ = wiring
    observe, count = module._case, 0

    def swap(wrapper, key, case, *, exact):
        nonlocal count
        row = observe(wrapper, key, case, exact=exact)
        count += 1
        if count == 72:
            replacement = nn.Linear(576, 8, bias=False).requires_grad_(False).eval()
            replacement.weight = host.model.weight
            replacement.config = host.model.config
            object.__setattr__(host, "model", replacement)
        return row

    monkeypatch.setattr(module, "_case", swap)
    with pytest.raises(module.ReferenceOfficialError) as caught:
        module.run_reference_official_suite(host, exact=True)
    assert len(caught.value.failure.completed) == 71


def test_actual_cached_primitive_with_separate_qv_key(wiring):
    from types import SimpleNamespace

    from aluclu.alc_r0 import checkpoint_official_forward as official

    module, _, _ = wiring
    seen = []

    class Cache:
        def __init__(self, length):
            self.length = length

        def get_seq_length(self):
            return self.length

    def forward(
        tag,
        input_ids,
        attention_mask=None,
        position_ids=None,
        use_cache=False,
        past_key_values=None,
    ):
        assert torch.is_inference_mode_enabled()
        seen.append((tag, past_key_values))
        length = input_ids.shape[1] + (past_key_values.length if past_key_values else 0)
        cache = Cache(length) if past_key_values is None else past_key_values
        cache.length = length
        return SimpleNamespace(
            logits=torch.ones((*input_ids.shape, 49152)), past_key_values=cache
        )

    class Base:
        def parameters(self):
            return iter((torch.ones(1),))

        def __call__(self, **kwargs):
            return forward("base", **kwargs)

    class Wrapper:
        base = Base()

        def __call__(self, **kwargs):
            return forward("qv", **kwargs)

    key, case = module.REFERENCE_SCHEDULE[21]
    with torch.inference_mode():
        row = official._case(Wrapper(), key, case, exact=True)
    assert row.key.arm == "qv_reference"
    assert row.incremental_official_sha256 == row.incremental_wrapper_sha256
    assert seen[2][1] is not seen[3][1]
