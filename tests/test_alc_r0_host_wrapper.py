from __future__ import annotations

import os
from importlib.metadata import version
from pathlib import Path

import pytest
import torch

from aluclu.alc_r0.host import VerifiedHost, load_verified_host
from aluclu.alc_r0.host_wrapper import HostWrapperError, PinnedLlamaCapsuleWrapper
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
        pytest.skip("pinned Transformers 5.17.0 and local model snapshot required")
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
        pytest.skip("pinned Transformers 5.17.0 and local model snapshot required")
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


@pytest.mark.parametrize("length", [1, 8, 127, 512])
def test_unmounted_wrapper_matches_official_real_host_logits_bitwise(
    pinned_host: VerifiedHost, length: int
) -> None:
    wrapper = PinnedLlamaCapsuleWrapper(pinned_host)
    input_ids = torch.arange(1, length + 1, dtype=torch.long).unsqueeze(0)

    with torch.inference_mode():
        official = pinned_host.model(input_ids=input_ids, use_cache=False)
        wrapped = wrapper(input_ids=input_ids, use_cache=False)

    assert torch.equal(wrapped.logits, official.logits)
    assert wrapped.past_key_values is None


@pytest.mark.parametrize("padding_side", ["left", "right"])
@pytest.mark.parametrize("explicit_positions", [False, True])
def test_unmounted_wrapper_preserves_unequal_masks_and_positions(
    pinned_host: VerifiedHost, padding_side: str, explicit_positions: bool
) -> None:
    wrapper = PinnedLlamaCapsuleWrapper(pinned_host)
    full = [10, 20, 30, 40]
    short = [50, 60]
    if padding_side == "left":
        rows = [full, [0, 0, *short]]
        masks = [[1, 1, 1, 1], [0, 0, 1, 1]]
    else:
        rows = [full, [*short, 0, 0]]
        masks = [[1, 1, 1, 1], [1, 1, 0, 0]]
    input_ids = torch.tensor(rows, dtype=torch.long)
    attention_mask = torch.tensor(masks, dtype=torch.long)
    position_ids = (
        torch.arange(4, dtype=torch.long).unsqueeze(0).expand(2, -1)
        if explicit_positions
        else None
    )

    with torch.inference_mode():
        official = pinned_host.model(
            input_ids=input_ids,
            attention_mask=attention_mask,
            position_ids=position_ids,
            use_cache=False,
        )
        wrapped = wrapper(
            input_ids=input_ids,
            attention_mask=attention_mask,
            position_ids=position_ids,
            use_cache=False,
        )

    assert torch.equal(wrapped.logits, official.logits)


def test_unmounted_wrapper_preserves_incremental_cache_logits(
    pinned_host: VerifiedHost,
) -> None:
    wrapper = PinnedLlamaCapsuleWrapper(pinned_host)
    initial_ids = torch.tensor([[10, 20, 30]], dtype=torch.long)
    next_id = torch.tensor([[40]], dtype=torch.long)

    with torch.inference_mode():
        official_initial = pinned_host.model(input_ids=initial_ids, use_cache=True)
        wrapped_initial = wrapper(input_ids=initial_ids, use_cache=True)
        official_next = pinned_host.model(
            input_ids=next_id,
            attention_mask=torch.ones((1, 4), dtype=torch.long),
            past_key_values=official_initial.past_key_values,
            use_cache=True,
        )
        wrapped_next = wrapper(
            input_ids=next_id,
            attention_mask=torch.ones((1, 4), dtype=torch.long),
            past_key_values=wrapped_initial.past_key_values,
            use_cache=True,
        )

    assert torch.equal(wrapped_initial.logits, official_initial.logits)
    assert torch.equal(wrapped_next.logits, official_next.logits)
    assert wrapped_next.past_key_values is not None
    assert wrapped_next.past_key_values.get_seq_length() == 4


def test_unmounted_wrapper_matches_real_host_gpu_bf16_logits(
    pinned_gpu_host: VerifiedHost,
) -> None:
    wrapper = PinnedLlamaCapsuleWrapper(pinned_gpu_host)
    input_ids = torch.arange(1, 9, device="cuda", dtype=torch.long).unsqueeze(0)

    with torch.inference_mode():
        official = pinned_gpu_host.model(input_ids=input_ids, use_cache=False)
        wrapped = wrapper(input_ids=input_ids, use_cache=False)

    assert torch.allclose(wrapped.logits, official.logits, rtol=1e-3, atol=1e-3)
    assert torch.equal(wrapped.logits.argmax(-1), official.logits.argmax(-1))


def test_real_host_capsule_mount_changes_logits_and_detach_restores_them(
    pinned_host: VerifiedHost,
) -> None:
    wrapper = PinnedLlamaCapsuleWrapper(pinned_host)
    capsule = ResearchCapsuleV0(ports=(29,), rank=4, seed=1)
    with torch.no_grad():
        for name, parameter in capsule.named_parameters():
            if name.endswith(".B"):
                parameter.fill_(0.125)
    input_ids = torch.tensor([[10, 20, 30]], dtype=torch.long)

    with torch.inference_mode():
        baseline = wrapper(input_ids=input_ids, use_cache=False).logits
        wrapper.mount(capsule)
        mounted = wrapper(input_ids=input_ids, use_cache=False).logits
        wrapper.detach()
        detached = wrapper(input_ids=input_ids, use_cache=False).logits

    assert not torch.equal(mounted, baseline)
    assert torch.equal(detached, baseline)
    assert all(
        not parameter.requires_grad for parameter in pinned_host.model.parameters()
    )
    assert wrapper.capsule is None


def test_wrapper_training_mode_never_changes_frozen_base_mode(
    pinned_host: VerifiedHost,
) -> None:
    wrapper = PinnedLlamaCapsuleWrapper(pinned_host)
    capsule = ResearchCapsuleV0(ports=(14,), rank=4, seed=1)
    wrapper.mount(capsule)

    wrapper.train()

    assert wrapper.training is True
    assert capsule.training is True
    assert pinned_host.model.training is False
    assert all(
        not parameter.requires_grad for parameter in pinned_host.model.parameters()
    )


def test_wrapper_rejects_later_base_mode_or_gradient_drift(
    pinned_host: VerifiedHost,
) -> None:
    wrapper = PinnedLlamaCapsuleWrapper(pinned_host)
    input_ids = torch.tensor([[10]], dtype=torch.long)
    first_parameter = next(pinned_host.model.parameters())
    try:
        pinned_host.model.train()
        with pytest.raises(HostWrapperError):
            wrapper(input_ids=input_ids, use_cache=False)
        pinned_host.model.eval()
        first_parameter.requires_grad_(True)
        with pytest.raises(HostWrapperError):
            wrapper(input_ids=input_ids, use_cache=False)
    finally:
        first_parameter.requires_grad_(False)
        pinned_host.model.eval()


def test_wrapper_rejects_unverified_host_object() -> None:
    with pytest.raises(TypeError):
        PinnedLlamaCapsuleWrapper(object())  # type: ignore[arg-type]
