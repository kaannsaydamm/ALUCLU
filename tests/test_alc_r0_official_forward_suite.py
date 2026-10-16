"""Synthetic CPU/stub controls; never actual pinned-host conformance evidence."""

import importlib
from dataclasses import FrozenInstanceError
from types import SimpleNamespace

import pytest
import torch
from torch import nn

from aluclu.alc_r0.host import VerifiedHost
from aluclu.alc_r0.matched_lora import MatchedQProjLoRA
from aluclu.alc_r0.research_capsule import ResearchCapsuleV0


@pytest.fixture
def module():
    return importlib.import_module("aluclu.alc_r0.checkpoint_official_forward")


class Base(nn.Module):
    def __init__(self):
        super().__init__()
        self.weight = nn.Parameter(torch.ones(1), requires_grad=False)
        self.eval()


class Wrapper(nn.Module):
    def __init__(self, host):
        super().__init__()
        self.base = host.model
        self.capsule = nn.Linear(1, 1, bias=False)
        self.capsule.weight.data.zero_()
        self.eval()

    def detach(self):
        self.capsule = None


@pytest.fixture
def wiring(module, monkeypatch):
    host = VerifiedHost(Base(), {}, {}, 1, 0)
    calls = []

    def make(host, checkpoint, *, arm, ports, rank, state):
        assert checkpoint is False
        calls.append(("make", arm, ports, rank, state))
        wrapper = Wrapper(host)
        factor_type = ResearchCapsuleV0 if arm == "capsule" else MatchedQProjLoRA
        wrapper.capsule = factor_type(ports=ports, rank=rank, seed=20260916)
        if arm == "q_lora":
            wrapper.lora, wrapper.capsule = wrapper.capsule, None
            wrapper.detach = lambda: setattr(wrapper, "lora", None)
        wrapper.eval()
        return wrapper

    def observe(wrapper, key, case, *, exact):
        assert exact is True
        assert not wrapper.training and not torch.is_grad_enabled()
        calls.append((key, case))
        increment = ("a" * 64, "a" * 64) if case.cached else (None, None)
        return module.OfficialCase(key, case, "a" * 64, "a" * 64, *increment)

    monkeypatch.setattr(module, "PinnedLlamaCapsuleWrapper", Wrapper)
    monkeypatch.setattr(module, "PinnedLlamaLoRAWrapper", Wrapper)
    monkeypatch.setattr(module, "make_parity_wrapper", make)
    monkeypatch.setattr(module, "_case", observe)
    monkeypatch.setattr(
        module, "_nonzero_witness", lambda wrapper, device: ("a" * 64, "b" * 64)
    )
    return host, calls


def test_complete_suite_order_grid_phases_and_small_receipts(module, wiring):
    host, calls = wiring
    result = module.run_official_forward_suite(host, exact=True)
    assert len(result.cases) == 1296
    assert len(result.nonzero_witnesses) == 18
    assert result.source_device == "cpu" and result.source_dtype == "torch.float32"
    assert result.cases[0].key.arm == "capsule"
    assert result.cases[0].key.grid_id == "M-r4"
    assert result.cases[0].key.phase == "unmounted"
    assert tuple(result.cases[i].key.phase for i in (0, 24, 48)) == (
        "unmounted",
        "zero",
        "detached",
    )
    assert result.cases[-1].key.arm == "q_lora"
    assert result.cases[-1].key.grid_id == "ML-r16"
    assert result.cases[-1].key.phase == "detached"
    assert len([c for c in calls if c[0] == "make"]) == 54
    with pytest.raises(FrozenInstanceError):
        result.base_digest = "c" * 64


@pytest.mark.parametrize("index", [0, 29, 1295])
def test_failure_keeps_completed_prefix_and_unrun_without_retry(
    module, wiring, monkeypatch, index
):
    host, calls = wiring
    observe = module._case
    executed = []

    def fail(wrapper, key, case, *, exact):
        if len(executed) == index:
            raise RuntimeError("deliberate comparison failure")
        executed.append(key)
        return observe(wrapper, key, case, exact=exact)

    monkeypatch.setattr(module, "_case", fail)
    with pytest.raises(module.OfficialForwardError) as caught:
        module.run_official_forward_suite(host, exact=True)
    assert len(caught.value.failure.completed) == index
    assert len(caught.value.failure.unrun) == 1295 - index
    assert caught.value.__cause__.args == ("deliberate comparison failure",)


def test_keyboard_interrupt_preserves_kind_and_partial_state(
    module, wiring, monkeypatch
):
    host, _ = wiring

    def interrupt(*args, **kwargs):
        raise KeyboardInterrupt("interrupted")

    monkeypatch.setattr(module, "_case", interrupt)
    with pytest.raises(module.OfficialForwardInterrupted) as caught:
        module.run_official_forward_suite(host, exact=True)
    assert caught.value.failure.completed == ()
    assert len(caught.value.failure.unrun) == 1295


def test_changed_base_cannot_join_success_prefix(module, wiring, monkeypatch):
    host, _ = wiring
    observe = module._case

    def mutate(wrapper, key, case, *, exact):
        result = observe(wrapper, key, case, exact=exact)
        wrapper.base.weight.data.add_(1)
        return result

    monkeypatch.setattr(module, "_case", mutate)
    with pytest.raises(module.OfficialForwardError, match="official"):
        module.run_official_forward_suite(host, exact=True)


@pytest.mark.parametrize("mode", [False, 1, None])
def test_cpu_requires_exact_boolean_mode_before_construction(module, wiring, mode):
    host, calls = wiring
    with pytest.raises(ValueError):
        module.run_official_forward_suite(host, exact=mode)
    assert calls == []


def test_fixed_inputs_reproduce_existing_no_mount_matrix(module):
    assert len(module.FORWARD_CASES) == 24
    for case in module.FORWARD_CASES[:20]:
        ids, mask, positions = module._inputs(case, torch.device("cpu"))
        assert ids.shape == (case.batch, case.length)
        if case.batch == 2:
            assert torch.equal(mask, ids.ne(0).long())
            assert int(mask[1].sum()) == case.length // 2
        else:
            assert mask is None
        assert (positions is not None) == case.explicit_positions
    assert tuple(c.length for c in module.FORWARD_CASES[20:]) == (1, 8, 127, 512)


def test_cpu_logit_comparison_is_bitwise_and_finite(module):
    reference = torch.ones((1, 1, 49152))
    assert module._compare_logits(
        reference, reference.clone(), (1, 1), torch.device("cpu"), True
    ) == (module._tensor_digest(reference), module._tensor_digest(reference))
    signed_zero = reference.clone()
    reference[0, 0, 0] = 0.0
    signed_zero[0, 0, 0] = -0.0
    with pytest.raises(ValueError, match="bitwise"):
        module._compare_logits(
            reference, signed_zero, (1, 1), torch.device("cpu"), True
        )


@pytest.mark.parametrize("kind", ["shape", "dtype", "nonfinite", "changed", "grad"])
def test_invalid_or_nonidentical_logits_rejected(module, kind):
    reference = torch.ones((1, 1, 49152))
    actual = reference.clone()
    if kind == "shape":
        actual = actual[..., :1]
    elif kind == "dtype":
        actual = actual.to(torch.float64)
    elif kind == "nonfinite":
        actual[0, 0, 0] = float("nan")
    elif kind == "changed":
        actual[0, 0, 0] += 1
    else:
        actual.requires_grad_(True)
    with pytest.raises(ValueError):
        module._compare_logits(reference, actual, (1, 1), torch.device("cpu"), True)


class Cache:
    def __init__(self, length):
        self.length = length

    def get_seq_length(self):
        return self.length


def test_cache_pair_requires_distinct_correct_length_objects(module):
    official, wrapped = Cache(8), Cache(8)
    module._cache_pair(official, wrapped, 8)
    with pytest.raises(ValueError):
        module._cache_pair(official, official, 8)
    with pytest.raises(ValueError):
        module._cache_pair(None, wrapped, 8)
    with pytest.raises(ValueError):
        module._cache_pair(official, Cache(7), 8)


def test_cached_case_passes_own_cache_to_each_incremental_branch(module):
    calls = []

    def forward(
        tag,
        input_ids,
        attention_mask=None,
        position_ids=None,
        use_cache=False,
        past_key_values=None,
    ):
        assert not torch.is_grad_enabled()
        calls.append((tag, past_key_values, attention_mask))
        length = input_ids.shape[1] + (
            0 if past_key_values is None else past_key_values.length
        )
        cache = Cache(length) if past_key_values is None else past_key_values
        cache.length = length
        return SimpleNamespace(
            logits=torch.ones((*input_ids.shape, 49152)), past_key_values=cache
        )

    class CallableBase:
        def parameters(self):
            return iter([torch.ones(1)])

        def __call__(self, **kw):
            return forward("official", **kw)

    class CallableWrapper:
        base = CallableBase()

        def __call__(self, **kw):
            return forward("wrapped", **kw)

    case = module.FORWARD_CASES[21]
    key = module.OfficialKey("M-r4", "capsule", "unmounted")
    with torch.inference_mode():
        result = module._case(CallableWrapper(), key, case, exact=True)
    assert result.incremental_official_sha256 is not None
    assert calls[2][1] is not calls[3][1]
    assert calls[2][2].shape == (1, 9)


def test_nonzero_witness_must_actually_change_official_logits(module):
    class Noop:
        def base(self, **kw):
            return SimpleNamespace(logits=torch.ones((1, 3, 49152)))

        __call__ = base

    with torch.inference_mode(), pytest.raises(ValueError, match="nonzero"):
        module._nonzero_witness(Noop(), torch.device("cpu"))


@pytest.mark.parametrize(
    "mutation", ["remove", "replace", "A", "B", "metadata", "mode"]
)
@pytest.mark.parametrize("arm,completed", [("capsule", 24), ("q_lora", 96)])
def test_zero_phase_drift_fails_before_receipt_admission(
    module, wiring, monkeypatch, mutation, arm, completed
):
    host, _ = wiring
    observe = module._case

    def drift(wrapper, key, case, *, exact):
        result = observe(wrapper, key, case, exact=exact)
        if key.phase == "zero" and key.arm == arm:
            factor = wrapper.capsule if arm == "capsule" else wrapper.lora
            if mutation == "remove":
                wrapper.detach()
            elif mutation == "replace":
                factor_type = (
                    ResearchCapsuleV0 if arm == "capsule" else MatchedQProjLoRA
                )
                replacement = factor_type(ports=(14,), rank=4, seed=20260916)
                replacement.eval()
                setattr(wrapper, "capsule" if arm == "capsule" else "lora", replacement)
            elif mutation in ("A", "B"):
                dict(factor.named_parameters())[f"factors.14.{mutation}"].data.add_(1)
            elif mutation == "metadata":
                factor.rank = 8
            else:
                wrapper.train()
        return result

    monkeypatch.setattr(module, "_case", drift)
    with pytest.raises(module.OfficialForwardError) as caught:
        module.run_official_forward_suite(host, exact=True)
    assert len(caught.value.failure.completed) == completed
    assert caught.value.failure.current[0].phase == "zero"


@pytest.mark.parametrize("phase,index", [("unmounted", 0), ("detached", 48)])
@pytest.mark.parametrize("arm,offset", [("capsule", 0), ("q_lora", 72)])
def test_absent_phase_remount_fails_before_receipt_admission(
    module, wiring, monkeypatch, phase, index, arm, offset
):
    host, _ = wiring
    observe = module._case

    def remount(wrapper, key, case, *, exact):
        result = observe(wrapper, key, case, exact=exact)
        if key.phase == phase and key.arm == arm:
            factor_type = ResearchCapsuleV0 if arm == "capsule" else MatchedQProjLoRA
            factor = factor_type(ports=(14,), rank=4, seed=20260916)
            factor.eval()
            setattr(wrapper, "capsule" if arm == "capsule" else "lora", factor)
        return result

    monkeypatch.setattr(module, "_case", remount)
    with pytest.raises(module.OfficialForwardError) as caught:
        module.run_official_forward_suite(host, exact=True)
    assert len(caught.value.failure.completed) == index + offset


def test_witness_failure_has_accurate_stage_and_leaves_first_case_unrun(
    module, wiring, monkeypatch
):
    host, _ = wiring

    def fail(*args):
        raise RuntimeError("witness failed")

    monkeypatch.setattr(module, "_nonzero_witness", fail)
    with pytest.raises(module.OfficialForwardError) as caught:
        module.run_official_forward_suite(host, exact=True)
    failure = caught.value.failure
    assert failure.stage == "witness"
    assert len(failure.completed) == 48
    assert failure.unrun[0] == failure.current
    assert len(failure.unrun) == 1248


@pytest.mark.parametrize(
    "kind", ["type", "key", "plain_increment", "digest", "missing_increment"]
)
def test_malformed_or_misattributed_receipt_is_rejected(
    module, wiring, monkeypatch, kind
):
    from dataclasses import replace

    host, _ = wiring
    observe = module._case

    def bad(wrapper, key, case, *, exact):
        result = observe(wrapper, key, case, exact=exact)
        if kind == "type":
            return None
        if kind == "key":
            return replace(result, key=module.OfficialKey("bad", key.arm, key.phase))
        if kind == "plain_increment":
            return replace(result, incremental_official_sha256="a" * 64)
        if kind == "digest":
            return replace(result, official_sha256="not a hash")
        if case.cached:
            return replace(result, incremental_official_sha256=None)
        return result

    monkeypatch.setattr(module, "_case", bad)
    with pytest.raises(module.OfficialForwardError):
        module.run_official_forward_suite(host, exact=True)


def test_factor_construction_has_ordinary_version_counters(module, wiring, monkeypatch):
    host, _ = wiring
    make = module.make_parity_wrapper

    def checked(*args, **kwargs):
        assert not torch.is_inference_mode_enabled(), (
            "factor construction must remain outside inference mode"
        )
        result = make(*args, **kwargs)
        assert all(not p.is_inference() for p in result.parameters())
        return result

    monkeypatch.setattr(module, "make_parity_wrapper", checked)
    module.run_official_forward_suite(host, exact=True)
