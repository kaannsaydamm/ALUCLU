from __future__ import annotations

import hashlib
import os
import subprocess
import sys
from collections.abc import Iterator
from importlib.metadata import version
from pathlib import Path

import pytest
import torch

from aluclu.alc_r0.base_digest import encode_base_state
from aluclu.alc_r0.canonical import canonical_json_bytes, parse_canonical_json
from aluclu.alc_r0.capsule_artifact import deserialize_capsule, serialize_capsule
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
    safe_child_keys = (
        "PATH",
        "SYSTEMROOT",
        "WINDIR",
        "TEMP",
        "TMP",
        "USERPROFILE",
        "APPDATA",
        "LOCALAPPDATA",
        "CUDA_PATH",
        "CUDA_VISIBLE_DEVICES",
    )
    environment = {key: os.environ[key] for key in safe_child_keys if key in os.environ}
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
        check=False,
        timeout=300,
    )
    assert first.returncode == 0, first.stderr.decode("utf-8", "replace")[-3000:]
    second = subprocess.run(
        command,
        cwd=PROJECT_ROOT,
        env=environment,
        capture_output=True,
        check=False,
        timeout=300,
    )
    assert second.returncode == 0, second.stderr.decode("utf-8", "replace")[-3000:]

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


def test_real_frozen_host_synthetic_capsule_training_survives_serialization(
    pinned_gpu_host: VerifiedHost,
    deterministic_gpu_math: None,
    tmp_path: Path,
) -> None:
    """Non-authorizing mechanism check, not an R0 capability evaluation."""

    from torch.nn import functional as F

    wrapper = PinnedLlamaCapsuleWrapper(pinned_gpu_host)
    capsule = ResearchCapsuleV0(ports=(14, 29), rank=8, seed=20260916).to(device="cuda")
    input_ids = torch.tensor([[2, 3, 5, 7, 11, 13, 17, 19]], device="cuda")
    target = torch.tensor([23], device="cuda")
    base_digest_before = encode_base_state(pinned_gpu_host.model.state_dict()).sha256

    with torch.inference_mode():
        baseline = wrapper(input_ids=input_ids, use_cache=False).logits[:, -1, :]
    wrapper.mount(capsule)
    wrapper.train()
    optimizer = torch.optim.AdamW(
        capsule.parameters(), lr=3e-4, betas=(0.9, 0.999), eps=1e-8, weight_decay=0.0
    )
    initial_loss = float(F.cross_entropy(baseline.float(), target).item())
    for _ in range(40):
        optimizer.zero_grad(set_to_none=True)
        logits = wrapper(input_ids=input_ids, use_cache=False).logits[:, -1, :]
        loss = F.cross_entropy(logits.float(), target)
        assert torch.isfinite(loss).item()
        loss.backward()
        assert all(parameter.grad is not None for parameter in capsule.parameters())
        grad_norm = torch.nn.utils.clip_grad_norm_(capsule.parameters(), max_norm=1.0)
        assert torch.isfinite(grad_norm).item()
        optimizer.step()

    wrapper.eval()
    with torch.inference_mode():
        trained = wrapper(input_ids=input_ids, use_cache=False).logits[:, -1, :]
    final_loss = float(F.cross_entropy(trained.float(), target).item())
    assert final_loss < initial_loss - 0.1
    assert not torch.equal(trained, baseline)

    manifest_bytes, tensor_bytes = serialize_capsule(capsule)
    wrapper.detach()
    restored = deserialize_capsule(manifest_bytes, tensor_bytes).to(device="cuda")
    wrapper.mount(restored)
    with torch.inference_mode():
        remounted = wrapper(input_ids=input_ids, use_cache=False).logits[:, -1, :]
    assert torch.equal(remounted, trained)
    wrapper.detach()
    with torch.inference_mode():
        detached = wrapper(input_ids=input_ids, use_cache=False).logits[:, -1, :]
    assert torch.equal(detached, baseline)
    assert (
        encode_base_state(pinned_gpu_host.model.state_dict()).sha256
        == base_digest_before
    )
    assert all(
        not parameter.requires_grad for parameter in pinned_gpu_host.model.parameters()
    )

    manifest_path = tmp_path / "synthetic-capsule-manifest.json"
    tensor_path = tmp_path / "synthetic-capsule.safetensors"
    manifest_path.write_bytes(manifest_bytes)
    tensor_path.write_bytes(tensor_bytes)
    safe_child_keys = (
        "PATH",
        "SYSTEMROOT",
        "WINDIR",
        "TEMP",
        "TMP",
        "USERPROFILE",
        "APPDATA",
        "LOCALAPPDATA",
        "CUDA_PATH",
        "CUDA_VISIBLE_DEVICES",
    )
    environment = {key: os.environ[key] for key in safe_child_keys if key in os.environ}
    environment.update(
        {
            "CUBLAS_WORKSPACE_CONFIG": ":4096:8",
            "HF_HUB_OFFLINE": "1",
            "TRANSFORMERS_OFFLINE": "1",
            "HF_DATASETS_OFFLINE": "1",
            "PYTHONPATH": str(PROJECT_ROOT / "src"),
        }
    )
    child = subprocess.run(
        [
            sys.executable,
            str(PROJECT_ROOT / "scripts" / "verify_alc_r0_synthetic_remount_worker.py"),
            "--snapshot",
            str(SNAPSHOT),
            "--manifest",
            str(manifest_path),
            "--tensors",
            str(tensor_path),
        ],
        cwd=PROJECT_ROOT,
        env=environment,
        capture_output=True,
        check=False,
        timeout=300,
    )
    assert child.returncode == 0, child.stderr.decode("utf-8", "replace")[-3000:]
    observation = parse_canonical_json(child.stdout)
    assert observation["status"] == "synthetic-remount-verified-non-authorizing"
    assert observation["training_authority"] is False
    assert observation["held_out_data_present"] is False
    assert observation["base_state_sha256"] == base_digest_before
    assert (
        observation["baseline_logits_sha256"]
        == hashlib.sha256(
            baseline.contiguous().cpu().view(torch.uint8).numpy().tobytes()
        ).hexdigest()
    )
    assert (
        observation["remounted_logits_sha256"]
        == hashlib.sha256(
            trained.contiguous().cpu().view(torch.uint8).numpy().tobytes()
        ).hexdigest()
    )
    print(
        canonical_json_bytes(
            {
                "status": "synthetic-trainability-verified-non-authorizing",
                "training_authority": False,
                "initial_loss": initial_loss,
                "final_loss": final_loss,
                "base_state_sha256": base_digest_before,
                "fresh_process_remount": True,
            }
        ).decode("utf-8")
    )


def test_serialized_zero_control_is_real_host_forward_noop(
    pinned_host: VerifiedHost,
) -> None:
    wrapper = PinnedLlamaCapsuleWrapper(pinned_host)
    manifest_bytes, tensor_bytes = serialize_capsule(
        ResearchCapsuleV0.zero_control(ports=(14, 29), rank=16)
    )
    restored = deserialize_capsule(manifest_bytes, tensor_bytes)
    input_ids = torch.tensor([[10, 20, 30, 40]], dtype=torch.long)

    with torch.inference_mode():
        official = pinned_host.model(input_ids=input_ids, use_cache=False).logits
        wrapper.mount(restored)
        mounted = wrapper(input_ids=input_ids, use_cache=False).logits
        wrapper.detach()
        detached = wrapper(input_ids=input_ids, use_cache=False).logits

    assert torch.equal(mounted, official)
    assert torch.equal(detached, official)
    assert all(not parameter.requires_grad for parameter in restored.parameters())


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
