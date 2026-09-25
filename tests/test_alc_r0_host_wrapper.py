from __future__ import annotations

import os
import subprocess
import sys
from collections.abc import Iterator
from importlib.metadata import version
from pathlib import Path

import pytest
import torch

from aluclu.alc_r0.canonical import parse_canonical_json
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
PROJECT_ROOT = Path(__file__).parents[1]


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


@pytest.fixture(scope="module")
def deterministic_gpu_math() -> Iterator[None]:
    previous_workspace = os.environ.get("CUBLAS_WORKSPACE_CONFIG")
    previous = (
        torch.are_deterministic_algorithms_enabled(),
        torch.backends.cuda.matmul.allow_tf32,
        torch.backends.cudnn.allow_tf32,
        torch.backends.cudnn.benchmark,
        torch.backends.cudnn.deterministic,
    )
    try:
        os.environ["CUBLAS_WORKSPACE_CONFIG"] = ":4096:8"
        torch.use_deterministic_algorithms(True)
        torch.backends.cuda.matmul.allow_tf32 = False
        torch.backends.cudnn.allow_tf32 = False
        torch.backends.cudnn.benchmark = False
        torch.backends.cudnn.deterministic = True
        yield
    finally:
        if previous_workspace is None:
            os.environ.pop("CUBLAS_WORKSPACE_CONFIG", None)
        else:
            os.environ["CUBLAS_WORKSPACE_CONFIG"] = previous_workspace
        torch.use_deterministic_algorithms(previous[0])
        torch.backends.cuda.matmul.allow_tf32 = previous[1]
        torch.backends.cudnn.allow_tf32 = previous[2]
        torch.backends.cudnn.benchmark = previous[3]
        torch.backends.cudnn.deterministic = previous[4]


@pytest.mark.parametrize("length", [1, 8, 127, 512])
@pytest.mark.parametrize("explicit_positions", [False, True])
def test_unmounted_wrapper_matches_official_real_host_logits_bitwise(
    pinned_host: VerifiedHost, length: int, explicit_positions: bool
) -> None:
    wrapper = PinnedLlamaCapsuleWrapper(pinned_host)
    input_ids = torch.arange(1, length + 1, dtype=torch.long).unsqueeze(0)
    position_ids = (
        torch.arange(length, dtype=torch.long).unsqueeze(0)
        if explicit_positions
        else None
    )

    with torch.inference_mode():
        official = pinned_host.model(
            input_ids=input_ids, position_ids=position_ids, use_cache=False
        )
        wrapped = wrapper(
            input_ids=input_ids, position_ids=position_ids, use_cache=False
        )

    assert torch.equal(wrapped.logits, official.logits)
    assert wrapped.past_key_values is None


@pytest.mark.parametrize("padding_side", ["left", "right"])
@pytest.mark.parametrize("explicit_positions", [False, True])
@pytest.mark.parametrize("length", [8, 127, 512])
def test_unmounted_wrapper_preserves_unequal_masks_and_positions(
    pinned_host: VerifiedHost,
    padding_side: str,
    explicit_positions: bool,
    length: int,
) -> None:
    wrapper = PinnedLlamaCapsuleWrapper(pinned_host)
    full = list(range(1, length + 1))
    short = list(range(100, 100 + length // 2))
    padding = [0] * (length - len(short))
    if padding_side == "left":
        rows = [full, padding + short]
        masks = [[1] * length, [0] * len(padding) + [1] * len(short)]
    else:
        rows = [full, short + padding]
        masks = [[1] * length, [1] * len(short) + [0] * len(padding)]
    input_ids = torch.tensor(rows, dtype=torch.long)
    attention_mask = torch.tensor(masks, dtype=torch.long)
    position_ids = (
        torch.arange(length, dtype=torch.long).unsqueeze(0).expand(2, -1)
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


@pytest.mark.parametrize("initial_length", [1, 8, 127, 512])
def test_unmounted_wrapper_preserves_incremental_cache_logits(
    pinned_host: VerifiedHost, initial_length: int
) -> None:
    wrapper = PinnedLlamaCapsuleWrapper(pinned_host)
    initial_ids = torch.arange(1, initial_length + 1, dtype=torch.long).unsqueeze(0)
    next_id = torch.tensor([[42]], dtype=torch.long)
    attention_mask = torch.ones((1, initial_length + 1), dtype=torch.long)

    with torch.inference_mode():
        official_initial = pinned_host.model(input_ids=initial_ids, use_cache=True)
        wrapped_initial = wrapper(input_ids=initial_ids, use_cache=True)
        official_next = pinned_host.model(
            input_ids=next_id,
            attention_mask=attention_mask,
            past_key_values=official_initial.past_key_values,
            use_cache=True,
        )
        wrapped_next = wrapper(
            input_ids=next_id,
            attention_mask=attention_mask,
            past_key_values=wrapped_initial.past_key_values,
            use_cache=True,
        )

    assert torch.equal(wrapped_initial.logits, official_initial.logits)
    assert torch.equal(wrapped_next.logits, official_next.logits)
    assert wrapped_next.past_key_values is not None
    assert wrapped_next.past_key_values.get_seq_length() == initial_length + 1


_GPU_CASES = [
    (1, length, "none", explicit_positions)
    for length in (1, 8, 127, 512)
    for explicit_positions in (False, True)
] + [
    (2, length, padding_side, explicit_positions)
    for length in (8, 127, 512)
    for padding_side in ("left", "right")
    for explicit_positions in (False, True)
]


@pytest.mark.parametrize(
    "batch_size,length,padding_side,explicit_positions", _GPU_CASES
)
def test_unmounted_wrapper_matches_real_host_gpu_bf16_logits(
    pinned_gpu_host: VerifiedHost,
    deterministic_gpu_math: None,
    batch_size: int,
    length: int,
    padding_side: str,
    explicit_positions: bool,
) -> None:
    wrapper = PinnedLlamaCapsuleWrapper(pinned_gpu_host)
    full = torch.arange(1, length + 1, device="cuda", dtype=torch.long)
    if batch_size == 1:
        input_ids = full.unsqueeze(0)
        attention_mask = None
    else:
        shorter = torch.arange(100, 100 + length // 2, device="cuda")
        padding = torch.zeros(length - len(shorter), device="cuda", dtype=torch.long)
        padded = (
            torch.cat((padding, shorter))
            if padding_side == "left"
            else torch.cat((shorter, padding))
        )
        input_ids = torch.stack((full, padded))
        attention_mask = input_ids.ne(0).long()
    position_ids = (
        torch.arange(length, device="cuda", dtype=torch.long)
        .unsqueeze(0)
        .expand(batch_size, -1)
        if explicit_positions
        else None
    )

    with torch.inference_mode():
        official = pinned_gpu_host.model(
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

    assert torch.allclose(wrapped.logits, official.logits, rtol=1e-3, atol=1e-3)
    assert torch.equal(wrapped.logits.argmax(-1), official.logits.argmax(-1))


@pytest.mark.parametrize("initial_length", [1, 8, 127, 512])
def test_unmounted_wrapper_matches_real_host_gpu_incremental_cache(
    pinned_gpu_host: VerifiedHost,
    deterministic_gpu_math: None,
    initial_length: int,
) -> None:
    wrapper = PinnedLlamaCapsuleWrapper(pinned_gpu_host)
    initial_ids = torch.arange(
        1, initial_length + 1, device="cuda", dtype=torch.long
    ).unsqueeze(0)
    next_id = torch.tensor([[42]], device="cuda", dtype=torch.long)
    attention_mask = torch.ones(
        (1, initial_length + 1), device="cuda", dtype=torch.long
    )

    with torch.inference_mode():
        official_initial = pinned_gpu_host.model(input_ids=initial_ids, use_cache=True)
        wrapped_initial = wrapper(input_ids=initial_ids, use_cache=True)
        official_next = pinned_gpu_host.model(
            input_ids=next_id,
            attention_mask=attention_mask,
            past_key_values=official_initial.past_key_values,
            use_cache=True,
        )
        wrapped_next = wrapper(
            input_ids=next_id,
            attention_mask=attention_mask,
            past_key_values=wrapped_initial.past_key_values,
            use_cache=True,
        )

    assert torch.allclose(
        wrapped_initial.logits, official_initial.logits, rtol=1e-3, atol=1e-3
    )
    assert torch.allclose(
        wrapped_next.logits, official_next.logits, rtol=1e-3, atol=1e-3
    )
    assert torch.equal(wrapped_next.logits.argmax(-1), official_next.logits.argmax(-1))
    assert wrapped_next.past_key_values is not None
    assert wrapped_next.past_key_values.get_seq_length() == initial_length + 1


def test_two_fresh_gpu_processes_reproduce_full_forward_matrix() -> None:
    if version("transformers") != "5.17.0" or not SNAPSHOT.is_dir():
        pytest.skip("pinned Transformers 5.17.0 and local model snapshot required")
    if not torch.cuda.is_available() or not torch.cuda.is_bf16_supported():
        pytest.skip("CUDA BF16 host is unavailable")
    environment = os.environ.copy()
    environment.update(
        {
            "CUBLAS_WORKSPACE_CONFIG": ":4096:8",
            "HF_HUB_OFFLINE": "1",
            "TRANSFORMERS_OFFLINE": "1",
            "HF_DATASETS_OFFLINE": "1",
            "PYTHONPATH": str(PROJECT_ROOT / "src"),
        }
    )
    command = [
        sys.executable,
        str(PROJECT_ROOT / "scripts" / "verify_alc_r0_forward_worker.py"),
        "--snapshot",
        str(SNAPSHOT),
    ]

    first = subprocess.run(
        command,
        cwd=PROJECT_ROOT,
        env=environment,
        capture_output=True,
        check=True,
        timeout=300,
    )
    second = subprocess.run(
        command,
        cwd=PROJECT_ROOT,
        env=environment,
        capture_output=True,
        check=True,
        timeout=300,
    )

    assert first.stdout == second.stdout
    result = parse_canonical_json(first.stdout)
    assert result["case_count"] == 24
    assert len(result["cases"]) == 24
    assert result["training_authority"] is False


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
