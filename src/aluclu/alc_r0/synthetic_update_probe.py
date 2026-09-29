"""Synthetic-only optimizer and capsule-remount execution diagnostic.

This neither authorizes task training nor establishes ALC-0 capability.
"""

from __future__ import annotations

import argparse
import hashlib
import math
import shutil
import stat
import sys
import time
from dataclasses import asdict
from importlib.metadata import version
from pathlib import Path
from typing import Any

import torch
from safetensors.torch import save as save_safetensors
from torch import nn
from torch.nn import functional as F

from .acquisition import verify_model_snapshot
from .base_digest import encode_base_state
from .canonical import canonical_json_bytes
from .capsule_artifact import deserialize_capsule, serialize_capsule
from .context_gradient_probe import (
    _PORTS,
    _RANK,
    _SEED,
    _TARGET_ID,
    _prepare_gpu_math,
    make_synthetic_ids,
)
from .host import load_verified_host
from .host_wrapper import PinnedLlamaCapsuleWrapper
from .matched_lora import MatchedQProjLoRA, PinnedLlamaLoRAWrapper
from .research_capsule import ResearchCapsuleV0
from .source_checkout import inspect_clean_source_checkout

_ARMS = ("capsule", "q_lora")
_UPDATES = 16
_DEFAULT_LENGTH = 512
_LENGTHS = (512, 2048)
_MIN_FREE_BYTES = 20 * 1024**3
_REPRO_TOLERANCE = 1e-4


class SyntheticUpdateProbeError(ValueError):
    """A synthetic update or remount violated the fixed diagnostic contract."""


def validate_update_request(
    arm: str, updates: int, *, length: int = _DEFAULT_LENGTH
) -> tuple[str, int, int]:
    if arm not in _ARMS or type(updates) is not int or updates != _UPDATES:
        raise SyntheticUpdateProbeError("arm or update count is outside declared cells")
    if type(length) is not int or length not in _LENGTHS:
        raise SyntheticUpdateProbeError("length is outside declared cells")
    return arm, updates, length


def _base_parameters(wrapper: nn.Module) -> tuple[nn.Parameter, ...]:
    base = getattr(wrapper, "base", None)
    if isinstance(base, nn.Parameter):
        return (base,)
    if isinstance(base, nn.Module):
        return tuple(base.parameters())
    raise SyntheticUpdateProbeError("wrapper has no frozen base")


def target_log_probability(
    wrapper: nn.Module, input_ids: torch.Tensor, target_token_id: int
) -> float:
    wrapper.eval()
    with torch.no_grad():
        logits = wrapper(input_ids=input_ids, use_cache=False, logits_to_keep=1).logits[
            :, -1, :
        ]
        if (
            logits.ndim != 2
            or logits.shape[0] != 1
            or not 0 <= target_token_id < logits.shape[-1]
        ):
            raise SyntheticUpdateProbeError("invalid next-token logits")
        value = float(F.log_softmax(logits.float(), dim=-1)[0, target_token_id])
    if not math.isfinite(value):
        raise SyntheticUpdateProbeError("nonfinite target log probability")
    return value


def optimizer_update_loop(
    wrapper: nn.Module,
    factors: nn.Module,
    input_ids: torch.Tensor,
    *,
    target_token_id: int,
    updates: int = _UPDATES,
) -> dict[str, Any]:
    """Apply exactly the declared number of FP32-factor AdamW updates."""

    validate_update_request("capsule", updates)
    if not isinstance(wrapper, nn.Module) or not isinstance(factors, nn.Module):
        raise SyntheticUpdateProbeError("module wrapper and factors required")
    if (
        not isinstance(input_ids, torch.Tensor)
        or input_ids.dtype != torch.long
        or input_ids.ndim != 2
        or input_ids.shape[0] != 1
        or input_ids.shape[1] < 1
    ):
        raise SyntheticUpdateProbeError("one nonempty token sequence required")
    base_parameters = _base_parameters(wrapper)
    if not base_parameters or any(
        p.requires_grad or p.grad is not None for p in base_parameters
    ):
        raise SyntheticUpdateProbeError("base is not frozen or has gradients")
    trainable = tuple(factors.parameters())
    if not trainable or any(
        p.dtype != torch.float32 or not p.requires_grad for p in trainable
    ):
        raise SyntheticUpdateProbeError("FP32 trainable factors required")
    before = target_log_probability(wrapper, input_ids, target_token_id)
    optimizer = torch.optim.AdamW(
        trainable,
        lr=3e-4,
        betas=(0.9, 0.999),
        eps=1e-8,
        weight_decay=0.0,
    )
    wrapper.train()
    if any(p.requires_grad or p.grad is not None for p in base_parameters):
        raise SyntheticUpdateProbeError("base changed training authority")
    if isinstance(wrapper.base, nn.Module) and wrapper.base.training:
        raise SyntheticUpdateProbeError("base entered training mode")
    losses: list[float] = []
    gradient_norms: list[float] = []
    for _ in range(updates):
        optimizer.zero_grad(set_to_none=True)
        logits = wrapper(input_ids=input_ids, use_cache=False, logits_to_keep=1).logits[
            :, -1, :
        ]
        loss = F.cross_entropy(
            logits.float(),
            torch.tensor([target_token_id], device=logits.device, dtype=torch.long),
        )
        if not torch.isfinite(loss).item():
            raise SyntheticUpdateProbeError("nonfinite loss before update")
        loss.backward()
        if any(
            p.grad is None or not torch.isfinite(p.grad).all().item() for p in trainable
        ):
            raise SyntheticUpdateProbeError("nonfinite or missing factor gradient")
        if any(p.grad is not None for p in base_parameters):
            raise SyntheticUpdateProbeError("frozen base received a gradient")
        gradient_norm = float(nn.utils.clip_grad_norm_(trainable, max_norm=1.0))
        if not math.isfinite(gradient_norm) or gradient_norm <= 0:
            raise SyntheticUpdateProbeError("nonfinite or zero gradient norm")
        optimizer.step()
        if any(not torch.isfinite(p).all().item() for p in trainable):
            raise SyntheticUpdateProbeError("nonfinite factor after update")
        losses.append(float(loss.detach()))
        gradient_norms.append(gradient_norm)
    after = target_log_probability(wrapper, input_ids, target_token_id)
    return {
        "optimizer_updates": len(losses),
        "pre_target_log_probability": before,
        "post_target_log_probability": after,
        "target_log_probability_improved": after > before,
        "losses": losses,
        "gradient_norms_before_clip": gradient_norms,
    }


def _factor_digest(factors: nn.Module) -> str:
    tensors = {
        name: tensor.detach().to(device="cpu", dtype=torch.float32).contiguous()
        for name, tensor in sorted(factors.state_dict().items())
    }
    return hashlib.sha256(save_safetensors(tensors)).hexdigest()


def _load_host(snapshot: Path):
    _prepare_gpu_math()
    host = load_verified_host(snapshot, device="cuda", dtype=torch.bfloat16)
    host.model.config._attn_implementation = "eager"
    if any(
        layer.self_attn.config._attn_implementation != "eager"
        for layer in host.model.model.layers
    ):
        raise SyntheticUpdateProbeError("host attention is not eager")
    return host


def _boundary(snapshot: Path):
    checkout = inspect_clean_source_checkout(Path.cwd().resolve(strict=True))
    free_bytes = shutil.disk_usage(Path.cwd().anchor).free
    if free_bytes < _MIN_FREE_BYTES:
        raise SyntheticUpdateProbeError("less than 20 GiB free on source drive")
    return checkout, verify_model_snapshot(snapshot), free_bytes


def _verify_boundary(snapshot: Path, checkout, before_snapshot) -> None:
    if (
        verify_model_snapshot(snapshot)["inventory_sha256"]
        != before_snapshot["inventory_sha256"]
    ):
        raise SyntheticUpdateProbeError("model snapshot changed during probe")
    if inspect_clean_source_checkout(Path.cwd().resolve(strict=True)) != checkout:
        raise SyntheticUpdateProbeError("source checkout changed during probe")


def run_update_probe(
    snapshot: Path, *, arm: str, length: int = _DEFAULT_LENGTH
) -> tuple[dict[str, Any], tuple[bytes, bytes] | None]:
    validate_update_request(arm, _UPDATES, length=length)
    checkout, snapshot_receipt, free_bytes = _boundary(snapshot)
    host = _load_host(snapshot)
    if arm == "capsule":
        factors: nn.Module = ResearchCapsuleV0(ports=_PORTS, rank=_RANK, seed=_SEED).to(
            "cuda"
        )
        wrapper: nn.Module = PinnedLlamaCapsuleWrapper(host)
        wrapper.mount(factors)
    else:
        factors = MatchedQProjLoRA(ports=_PORTS, rank=_RANK, seed=_SEED).to("cuda")
        wrapper = PinnedLlamaLoRAWrapper(host)
        wrapper.mount_lora(factors)
    input_ids = make_synthetic_ids(
        length, vocab_size=host.config_identity["vocab_size"]
    ).to("cuda")
    base_before = encode_base_state(host.model.state_dict()).sha256
    factors_before = _factor_digest(factors)
    torch.cuda.synchronize()
    torch.cuda.empty_cache()
    torch.cuda.reset_peak_memory_stats()
    start_ns = time.perf_counter_ns()
    update = optimizer_update_loop(
        wrapper,
        factors,
        input_ids,
        target_token_id=_TARGET_ID,
    )
    torch.cuda.synchronize()
    elapsed_ns = time.perf_counter_ns() - start_ns
    peak_allocated = torch.cuda.max_memory_allocated()
    peak_reserved = torch.cuda.max_memory_reserved()
    factors_after = _factor_digest(factors)
    wrapper.detach()
    detached = target_log_probability(wrapper, input_ids, _TARGET_ID)
    base_after = encode_base_state(host.model.state_dict()).sha256
    _verify_boundary(snapshot, checkout, snapshot_receipt)
    if base_before != base_after or any(
        p.grad is not None for p in host.model.parameters()
    ):
        raise SyntheticUpdateProbeError("frozen base changed during updates")
    if factors_before == factors_after:
        raise SyntheticUpdateProbeError("factor state did not change")
    if abs(detached - update["pre_target_log_probability"]) > _REPRO_TOLERANCE:
        raise SyntheticUpdateProbeError("detached base score differs from baseline")
    artifact = serialize_capsule(factors) if arm == "capsule" else None
    receipt = {
        "receipt_version": 1,
        "status": "synthetic-updates-complete-non-authorizing",
        "training_authority": False,
        "held_out_data_present": False,
        "synthetic_only": True,
        "retrieval_enabled": False,
        "source_checkout": asdict(checkout),
        "model_inventory_sha256": snapshot_receipt["inventory_sha256"],
        "snapshot_root": str(snapshot.resolve(strict=True)),
        "arm": arm,
        "sequence_length": length,
        "batch_size": 1,
        "factor_initialization_seed": _SEED,
        "synthetic_id_rule": "arange_mod_vocab_minus_one_plus_one",
        "ports": list(_PORTS),
        "rank": _RANK,
        "host_dtype": "bfloat16",
        "factor_dtype": "float32",
        "attention_implementation": "eager",
        "use_cache": False,
        "target_token_id": _TARGET_ID,
        "optimizer": "AdamW",
        "learning_rate": 3e-4,
        "betas": [0.9, 0.999],
        "epsilon": 1e-8,
        "weight_decay": 0.0,
        "gradient_clip_norm": 1.0,
        **update,
        "detached_target_log_probability": detached,
        "base_state_sha256_before": base_before,
        "base_state_sha256_after": base_after,
        "factor_state_sha256_before": factors_before,
        "factor_state_sha256_after": factors_after,
        "artifact_manifest_sha256": hashlib.sha256(artifact[0]).hexdigest()
        if artifact
        else None,
        "artifact_tensor_sha256": hashlib.sha256(artifact[1]).hexdigest()
        if artifact
        else None,
        "peak_allocated_bytes": peak_allocated,
        "peak_reserved_bytes": peak_reserved,
        "elapsed_updates_ns": elapsed_ns,
        "disk_free_bytes_before": free_bytes,
        "gpu_name": torch.cuda.get_device_name(0),
        "gpu_total_bytes": torch.cuda.get_device_properties(0).total_memory,
        "torch_version": torch.__version__,
        "torch_cuda_version": torch.version.cuda,
        "transformers_version": version("transformers"),
        "python_version": sys.version.split()[0],
        "python_executable": str(Path(sys.executable).resolve(strict=True)),
    }
    return receipt, artifact


def run_remount_probe(
    snapshot: Path,
    *,
    manifest_path: Path,
    tensor_path: Path,
    length: int = _DEFAULT_LENGTH,
) -> dict[str, Any]:
    validate_update_request("capsule", _UPDATES, length=length)
    checkout, snapshot_receipt, free_bytes = _boundary(snapshot)
    for path in (manifest_path, tensor_path):
        if (
            path.is_symlink()
            or not path.is_file()
            or not stat.S_ISREG(path.stat().st_mode)
        ):
            raise SyntheticUpdateProbeError("artifact path must be a regular file")
    manifest_bytes = manifest_path.read_bytes()
    tensor_bytes = tensor_path.read_bytes()
    _prepare_gpu_math()
    factors = deserialize_capsule(manifest_bytes, tensor_bytes).to("cuda")
    host = _load_host(snapshot)
    wrapper = PinnedLlamaCapsuleWrapper(host)
    input_ids = make_synthetic_ids(
        length, vocab_size=host.config_identity["vocab_size"]
    ).to("cuda")
    base_before = encode_base_state(host.model.state_dict()).sha256
    start_ns = time.perf_counter_ns()
    detached = target_log_probability(wrapper, input_ids, _TARGET_ID)
    wrapper.mount(factors)
    mounted = target_log_probability(wrapper, input_ids, _TARGET_ID)
    wrapper.detach()
    detached_again = target_log_probability(wrapper, input_ids, _TARGET_ID)
    elapsed_ns = time.perf_counter_ns() - start_ns
    base_after = encode_base_state(host.model.state_dict()).sha256
    _verify_boundary(snapshot, checkout, snapshot_receipt)
    if base_before != base_after or abs(detached_again - detached) > _REPRO_TOLERANCE:
        raise SyntheticUpdateProbeError("base changed across fresh-process mount")
    return {
        "receipt_version": 1,
        "status": "synthetic-capsule-fresh-remount-complete-non-authorizing",
        "training_authority": False,
        "held_out_data_present": False,
        "synthetic_only": True,
        "retrieval_enabled": False,
        "source_checkout": asdict(checkout),
        "model_inventory_sha256": snapshot_receipt["inventory_sha256"],
        "arm": "capsule",
        "sequence_length": length,
        "target_token_id": _TARGET_ID,
        "optimizer_updates": 0,
        "detached_target_log_probability": detached,
        "mounted_target_log_probability": mounted,
        "detached_again_target_log_probability": detached_again,
        "base_state_sha256_before": base_before,
        "base_state_sha256_after": base_after,
        "artifact_manifest_sha256": hashlib.sha256(manifest_bytes).hexdigest(),
        "artifact_tensor_sha256": hashlib.sha256(tensor_bytes).hexdigest(),
        "disk_free_bytes_before": free_bytes,
        "elapsed_remount_ns": elapsed_ns,
        "gpu_name": torch.cuda.get_device_name(0),
        "gpu_total_bytes": torch.cuda.get_device_properties(0).total_memory,
        "torch_version": torch.__version__,
        "torch_cuda_version": torch.version.cuda,
        "transformers_version": version("transformers"),
        "python_version": sys.version.split()[0],
        "python_executable": str(Path(sys.executable).resolve(strict=True)),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="mode", required=True)
    train = sub.add_parser("train")
    train.add_argument("snapshot", type=Path)
    train.add_argument("--arm", choices=_ARMS, required=True)
    train.add_argument("--length", type=int, choices=_LENGTHS, default=_DEFAULT_LENGTH)
    train.add_argument("--artifact-dir", type=Path)
    remount = sub.add_parser("remount")
    remount.add_argument("snapshot", type=Path)
    remount.add_argument("manifest_path", type=Path)
    remount.add_argument("tensor_path", type=Path)
    remount.add_argument(
        "--length", type=int, choices=_LENGTHS, default=_DEFAULT_LENGTH
    )
    args = parser.parse_args()
    if args.mode == "train":
        if (args.arm == "capsule") != (args.artifact_dir is not None):
            raise SyntheticUpdateProbeError("capsule only requires an artifact dir")
        if args.artifact_dir is not None:
            artifact_dir = args.artifact_dir.resolve(strict=False)
            if (
                not args.artifact_dir.is_absolute()
                or artifact_dir.is_relative_to(Path.cwd().resolve(strict=True))
                or artifact_dir.exists()
                or not artifact_dir.parent.is_dir()
            ):
                raise SyntheticUpdateProbeError(
                    "artifact dir must be new and outside checkout"
                )
        receipt, artifact = run_update_probe(
            args.snapshot, arm=args.arm, length=args.length
        )
        if artifact is not None:
            artifact_dir.mkdir()
            (artifact_dir / "manifest.json").write_bytes(artifact[0])
            (artifact_dir / "factors.safetensors").write_bytes(artifact[1])
            receipt["artifact_dir"] = str(artifact_dir)
    else:
        receipt = run_remount_probe(
            args.snapshot,
            manifest_path=args.manifest_path,
            tensor_path=args.tensor_path,
            length=args.length,
        )
    sys.stdout.buffer.write(canonical_json_bytes(receipt) + b"\n")


if __name__ == "__main__":
    main()
