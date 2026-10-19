from __future__ import annotations

import os
from importlib.metadata import version
from pathlib import Path

import pytest
import torch

from aluclu.alc_r0.host import VerifiedHost, load_verified_host
from aluclu.alc_r0.host_wrapper import HostWrapperError
from aluclu.alc_r0.matched_lora import MatchedQProjLoRA, PinnedLlamaLoRAWrapper
from aluclu.alc_r0.research_capsule import ResearchCapsuleV0

SNAPSHOT = Path(
    os.environ.get(
        "ALUCLU_R0_SNAPSHOT",
        "C:/Users/kaann/AppData/Local/ALUCLU/research/alc-r0-smollm2-135m-v1/"
        "model/SmolLM2-135M-93efa2f",
    )
)


@pytest.fixture(scope="module")
def pinned_host() -> VerifiedHost:
    if version("transformers") != "5.17.0" or not SNAPSHOT.is_dir():
        pytest.skip("pinned Transformers 5.17.0 and model snapshot required")
    return load_verified_host(
        SNAPSHOT,
        environment={
            "HF_HUB_OFFLINE": "1",
            "TRANSFORMERS_OFFLINE": "1",
            "HF_DATASETS_OFFLINE": "1",
        },
        dtype=torch.float32,
    )


@pytest.fixture(scope="module")
def pinned_gpu_host() -> VerifiedHost:
    if version("transformers") != "5.17.0" or not SNAPSHOT.is_dir():
        pytest.skip("pinned Transformers 5.17.0 and model snapshot required")
    if not torch.cuda.is_available() or not torch.cuda.is_bf16_supported():
        pytest.skip("CUDA BF16 host is unavailable")
    return load_verified_host(
        SNAPSHOT,
        environment={
            "HF_HUB_OFFLINE": "1",
            "TRANSFORMERS_OFFLINE": "1",
            "HF_DATASETS_OFFLINE": "1",
        },
        device="cuda",
        dtype=torch.bfloat16,
    )


@pytest.mark.parametrize("ports,rank", [((14,), 4), ((29,), 8), ((14, 29), 16)])
def test_matched_lora_has_exact_count_and_capsule_initial_A(
    ports: tuple[int, ...], rank: int
) -> None:
    seed = 20260921
    lora = MatchedQProjLoRA(ports=ports, rank=rank, seed=seed)
    capsule = ResearchCapsuleV0(ports=ports, rank=rank, seed=seed)

    assert sum(p.numel() for p in lora.parameters()) == 1152 * rank * len(ports)
    assert set(lora.state_dict()) == {
        f"factors.{port}.{factor}" for port in ports for factor in ("A", "B")
    }
    for port in ports:
        assert torch.equal(
            lora.state_dict()[f"factors.{port}.A"],
            capsule.state_dict()[f"factors.{port}.A"],
        )
        assert torch.count_nonzero(lora.state_dict()[f"factors.{port}.B"]) == 0


def test_lora_initialization_preserves_global_rng() -> None:
    before = torch.random.get_rng_state().clone()

    MatchedQProjLoRA(ports=(14, 29), rank=8, seed=42)

    assert torch.equal(before, torch.random.get_rng_state())


@pytest.mark.parametrize("ports,rank", [((14,), 4), ((14, 29), 16)])
def test_unmounted_and_zero_initialized_lora_match_official_real_host(
    pinned_host: VerifiedHost, ports: tuple[int, ...], rank: int
) -> None:
    wrapper = PinnedLlamaLoRAWrapper(pinned_host)
    lora = MatchedQProjLoRA(ports=ports, rank=rank, seed=7)
    ids = torch.tensor([[10, 20, 30, 40]], dtype=torch.long)

    with torch.inference_mode():
        official = pinned_host.model(input_ids=ids, use_cache=False).logits
        unmounted = wrapper(input_ids=ids, use_cache=False).logits
        wrapper.mount_lora(lora)
        initial = wrapper(input_ids=ids, use_cache=False).logits
        wrapper.detach_lora()
        detached = wrapper(input_ids=ids, use_cache=False).logits

    assert torch.equal(unmounted, official)
    assert torch.equal(initial, official)
    assert torch.equal(detached, official)
    assert all(not p.requires_grad for p in pinned_host.model.parameters())


def test_nonzero_lora_changes_logits_and_detach_restores_base(
    pinned_host: VerifiedHost,
) -> None:
    wrapper = PinnedLlamaLoRAWrapper(pinned_host)
    lora = MatchedQProjLoRA(ports=(14,), rank=4, seed=7)
    with torch.no_grad():
        dict(lora.named_parameters())["factors.14.B"].fill_(0.125)
    ids = torch.tensor([[10, 20, 30, 40]], dtype=torch.long)

    with torch.inference_mode():
        baseline = wrapper(input_ids=ids, use_cache=False).logits
        wrapper.mount_lora(lora)
        mounted = wrapper(input_ids=ids, use_cache=False).logits
        wrapper.detach_lora()
        detached = wrapper(input_ids=ids, use_cache=False).logits

    assert not torch.equal(mounted, baseline)
    assert torch.equal(detached, baseline)


def test_lora_train_mode_keeps_base_frozen_and_eval(pinned_host: VerifiedHost) -> None:
    wrapper = PinnedLlamaLoRAWrapper(pinned_host)
    lora = MatchedQProjLoRA(ports=(29,), rank=4, seed=1)
    wrapper.mount_lora(lora)

    wrapper.train()

    assert wrapper.training
    assert lora.training
    assert not pinned_host.model.training
    assert all(not p.requires_grad for p in pinned_host.model.parameters())


def test_lora_arm_rejects_capsule_co_mount(pinned_host: VerifiedHost) -> None:
    wrapper = PinnedLlamaLoRAWrapper(pinned_host)

    with pytest.raises(HostWrapperError):
        wrapper.mount(ResearchCapsuleV0(ports=(14,), rank=4, seed=7))

    assert wrapper.capsule is None


def test_q_lora_path_preserves_masked_incremental_cache_and_base_identity(
    pinned_host: VerifiedHost,
) -> None:
    wrapper = PinnedLlamaLoRAWrapper(pinned_host)
    before_q = dict(pinned_host.model.named_modules())[
        "model.layers.14.self_attn.q_proj"
    ]
    lora = MatchedQProjLoRA(ports=(14,), rank=4, seed=7)
    ids = torch.tensor([[10, 20, 30, 40], [0, 0, 50, 60]], dtype=torch.long)
    mask = ids.ne(0).long()
    next_ids = torch.tensor([[42], [43]], dtype=torch.long)
    next_mask = torch.cat((mask, torch.ones((2, 1), dtype=torch.long)), dim=1)

    with torch.inference_mode():
        official_initial = pinned_host.model(
            input_ids=ids, attention_mask=mask, use_cache=True
        )
        wrapper.mount_lora(lora)
        wrapped_initial = wrapper(input_ids=ids, attention_mask=mask, use_cache=True)
        official_next = pinned_host.model(
            input_ids=next_ids,
            attention_mask=next_mask,
            past_key_values=official_initial.past_key_values,
            use_cache=True,
        )
        wrapped_next = wrapper(
            input_ids=next_ids,
            attention_mask=next_mask,
            past_key_values=wrapped_initial.past_key_values,
            use_cache=True,
        )

    assert torch.equal(wrapped_initial.logits, official_initial.logits)
    assert torch.equal(wrapped_next.logits, official_next.logits)
    assert (
        dict(pinned_host.model.named_modules())["model.layers.14.self_attn.q_proj"]
        is before_q
    )
    assert wrapped_next.past_key_values is not None
    assert wrapped_next.past_key_values.get_seq_length() == 5


def test_q_lora_backward_updates_only_factors(pinned_host: VerifiedHost) -> None:
    wrapper = PinnedLlamaLoRAWrapper(pinned_host)
    lora = MatchedQProjLoRA(ports=(14,), rank=4, seed=7)
    wrapper.mount_lora(lora)
    wrapper.train()
    ids = torch.tensor([[10, 20, 30, 40]], dtype=torch.long)

    loss = wrapper(input_ids=ids, use_cache=False).logits.float().square().mean()
    loss.backward()

    factors = dict(lora.named_parameters())
    assert factors["factors.14.B"].grad is not None
    assert torch.isfinite(factors["factors.14.B"].grad).all()
    assert torch.count_nonzero(factors["factors.14.B"].grad) > 0
    assert all(parameter.grad is None for parameter in pinned_host.model.parameters())
    wrapper.detach_lora()
    wrapper.eval()


def test_zero_initialized_q_lora_matches_real_gpu_bf16_host(
    pinned_gpu_host: VerifiedHost,
) -> None:
    wrapper = PinnedLlamaLoRAWrapper(pinned_gpu_host)
    lora = MatchedQProjLoRA(ports=(14, 29), rank=8, seed=7).to("cuda")
    ids = torch.tensor([[10, 20, 30, 40]], device="cuda", dtype=torch.long)

    with torch.inference_mode():
        official = pinned_gpu_host.model(input_ids=ids, use_cache=False).logits
        wrapper.mount_lora(lora)
        wrapped = wrapper(input_ids=ids, use_cache=False).logits

    assert torch.allclose(wrapped, official, rtol=1e-3, atol=1e-3)
    assert torch.equal(wrapped.argmax(-1), official.argmax(-1))
    assert all(parameter.dtype == torch.float32 for parameter in lora.parameters())
