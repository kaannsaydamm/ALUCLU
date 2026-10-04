"""Non-authorizing, synthetic-only long-context gradient resource probe.

This is not the frozen R0.4 200-update pilot, a dataset run, or a capability
evaluation. Each invocation measures one declared length and one matched arm.
"""

from __future__ import annotations

import argparse
import math
import os
import shutil
import sys
import time
from dataclasses import asdict
from importlib.metadata import version
from pathlib import Path
from typing import Any

import torch
from torch.nn import functional as F

from .acquisition import verify_model_snapshot
from .base_digest import encode_base_state
from .canonical import canonical_json_bytes
from .host import load_verified_host
from .host_wrapper import PinnedLlamaCapsuleWrapper
from .matched_lora import MatchedQProjLoRA, PinnedLlamaLoRAWrapper
from .research_capsule import ResearchCapsuleV0
from .source_checkout import inspect_clean_source_checkout

_DECLARED_LENGTHS = (512, 1024, 2048)
_DECLARED_ARMS = ("capsule", "q_lora")
_MIN_FREE_BYTES = 20 * 1024**3
_SEED = 20260916
_PORTS = (14, 29)
_RANK = 8
_TARGET_ID = 23


class ContextGradientProbeError(ValueError):
    """The synthetic probe request or local execution boundary is invalid."""


def validate_probe_request(length: int, arm: str) -> tuple[int, str]:
    if type(length) is not int or length not in _DECLARED_LENGTHS:
        raise ContextGradientProbeError("length is outside declared probe grid")
    if arm not in _DECLARED_ARMS:
        raise ContextGradientProbeError("arm is outside declared probe grid")
    return length, arm


def make_synthetic_ids(length: int, *, vocab_size: int) -> torch.Tensor:
    if type(length) is not int or length not in _DECLARED_LENGTHS:
        raise ContextGradientProbeError("length is outside declared probe grid")
    if type(vocab_size) is not int or vocab_size <= _TARGET_ID:
        raise ContextGradientProbeError("vocabulary is invalid for synthetic probe")
    return (torch.arange(length, dtype=torch.long) % (vocab_size - 1) + 1).unsqueeze(0)


def _prepare_gpu_math() -> None:
    if os.environ.get("CUBLAS_WORKSPACE_CONFIG") != ":4096:8":
        raise ContextGradientProbeError("deterministic CUBLAS workspace is required")
    if not torch.cuda.is_available() or not torch.cuda.is_bf16_supported():
        raise ContextGradientProbeError("CUDA BF16 GPU is unavailable")
    torch.use_deterministic_algorithms(True)
    torch.backends.cuda.matmul.allow_tf32 = False
    torch.backends.cudnn.allow_tf32 = False
    torch.backends.cudnn.benchmark = False
    torch.backends.cudnn.deterministic = True


def run_probe(snapshot: Path, *, length: int, arm: str) -> dict[str, Any]:
    """Run exactly one synthetic backward without an optimizer update."""

    validate_probe_request(length, arm)
    checkout = inspect_clean_source_checkout(Path.cwd().resolve(strict=True))
    disk_free_bytes_before = shutil.disk_usage(Path.cwd().anchor).free
    if disk_free_bytes_before < _MIN_FREE_BYTES:
        raise ContextGradientProbeError("less than 20 GiB free on source drive")
    before_snapshot = verify_model_snapshot(snapshot)
    _prepare_gpu_math()
    host = load_verified_host(snapshot, device="cuda", dtype=torch.bfloat16)
    host.model.config._attn_implementation = "eager"
    if any(
        layer.self_attn.config._attn_implementation != "eager"
        for layer in host.model.model.layers
    ):
        raise ContextGradientProbeError("host attention is not eager")

    if arm == "capsule":
        factors = ResearchCapsuleV0(ports=_PORTS, rank=_RANK, seed=_SEED).to("cuda")
        wrapper = PinnedLlamaCapsuleWrapper(host)
        wrapper.mount(factors)
    else:
        factors = MatchedQProjLoRA(ports=_PORTS, rank=_RANK, seed=_SEED).to("cuda")
        wrapper = PinnedLlamaLoRAWrapper(host)
        wrapper.mount_lora(factors)
    wrapper.train()
    if host.model.training or any(p.requires_grad for p in host.model.parameters()):
        raise ContextGradientProbeError("frozen base mode drifted")
    before_base_sha256 = encode_base_state(host.model.state_dict()).sha256
    input_ids = make_synthetic_ids(
        length, vocab_size=host.config_identity["vocab_size"]
    ).to("cuda")
    target = torch.tensor([_TARGET_ID], device="cuda", dtype=torch.long)

    torch.cuda.synchronize()
    torch.cuda.empty_cache()
    torch.cuda.reset_peak_memory_stats()
    baseline_allocated = torch.cuda.memory_allocated()
    baseline_reserved = torch.cuda.memory_reserved()
    cuda_free_before = torch.cuda.mem_get_info()[0]
    start_ns = time.perf_counter_ns()
    status = "synthetic-backward-complete-non-authorizing"
    loss_value: float | None = None
    gradient_norm: float | None = None
    try:
        logits = wrapper(input_ids=input_ids, use_cache=False, logits_to_keep=1).logits[
            :, -1, :
        ]
        loss = F.cross_entropy(logits.float(), target)
        if not torch.isfinite(loss).item():
            status = "nonfinite-loss"
        else:
            loss_value = float(loss.detach().item())
            loss.backward()
            gradients = [p.grad for p in factors.parameters()]
            if any(g is None or not torch.isfinite(g).all().item() for g in gradients):
                status = "nonfinite-or-missing-gradient"
            else:
                gradient_norm = float(
                    torch.linalg.vector_norm(
                        torch.stack(
                            [torch.linalg.vector_norm(g.float()) for g in gradients]
                        )
                    ).item()
                )
                if not math.isfinite(gradient_norm):
                    gradient_norm = None
                    status = "nonfinite-gradient-norm"
                elif gradient_norm <= 0:
                    status = "zero-gradient"
    except torch.cuda.OutOfMemoryError:
        status = "cuda-out-of-memory"
    torch.cuda.synchronize()
    elapsed_ns = time.perf_counter_ns() - start_ns
    peak_allocated = torch.cuda.max_memory_allocated()
    peak_reserved = torch.cuda.max_memory_reserved()
    cuda_free_after = torch.cuda.mem_get_info()[0]
    after_base_sha256 = encode_base_state(host.model.state_dict()).sha256
    after_snapshot = verify_model_snapshot(snapshot)
    if after_snapshot["inventory_sha256"] != before_snapshot["inventory_sha256"]:
        raise ContextGradientProbeError("model snapshot changed during probe")
    if inspect_clean_source_checkout(Path.cwd().resolve(strict=True)) != checkout:
        raise ContextGradientProbeError("source checkout changed during probe")
    if after_base_sha256 != before_base_sha256:
        raise ContextGradientProbeError("frozen base state changed during probe")
    if any(p.grad is not None for p in host.model.parameters()):
        raise ContextGradientProbeError("frozen base received gradients")

    return {
        "receipt_version": 1,
        "status": status,
        "success": status == "synthetic-backward-complete-non-authorizing",
        "training_authority": False,
        "held_out_data_present": False,
        "synthetic_only": True,
        "optimizer_updates": 0,
        "source_checkout": asdict(checkout),
        "model_inventory_sha256": before_snapshot["inventory_sha256"],
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
        "loss": loss_value,
        "gradient_norm": gradient_norm,
        "base_state_sha256_before": before_base_sha256,
        "base_state_sha256_after": after_base_sha256,
        "baseline_allocated_bytes": baseline_allocated,
        "baseline_reserved_bytes": baseline_reserved,
        "peak_allocated_bytes": peak_allocated,
        "peak_reserved_bytes": peak_reserved,
        "cuda_free_bytes_before": cuda_free_before,
        "cuda_free_bytes_after": cuda_free_after,
        "disk_free_bytes_before": disk_free_bytes_before,
        "elapsed_forward_backward_ns": elapsed_ns,
        "gpu_name": torch.cuda.get_device_name(0),
        "gpu_total_bytes": torch.cuda.get_device_properties(0).total_memory,
        "torch_version": torch.__version__,
        "torch_cuda_version": torch.version.cuda,
        "transformers_version": version("transformers"),
        "python_version": sys.version.split()[0],
        "python_executable": str(Path(sys.executable).resolve(strict=True)),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("snapshot", type=Path)
    parser.add_argument("--length", type=int, choices=_DECLARED_LENGTHS, required=True)
    parser.add_argument("--arm", choices=_DECLARED_ARMS, required=True)
    args = parser.parse_args()
    receipt = run_probe(args.snapshot, length=args.length, arm=args.arm)
    sys.stdout.buffer.write(canonical_json_bytes(receipt) + b"\n")
    return 0 if receipt["success"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
