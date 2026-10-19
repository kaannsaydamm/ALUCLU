"""Fresh-process, non-authorizing remount check for a synthetic R0 diagnostic."""

from __future__ import annotations

import argparse
import hashlib
import os
import sys
from pathlib import Path

import torch

from aluclu.alc_r0.base_digest import encode_base_state
from aluclu.alc_r0.canonical import canonical_json_bytes
from aluclu.alc_r0.capsule_artifact import deserialize_capsule
from aluclu.alc_r0.host import load_verified_host
from aluclu.alc_r0.host_wrapper import PinnedLlamaCapsuleWrapper


def _logits_sha256(logits: torch.Tensor) -> str:
    raw = logits.detach().contiguous().cpu().view(torch.uint8).numpy().tobytes()
    return hashlib.sha256(raw).hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--snapshot", type=Path, required=True)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--tensors", type=Path, required=True)
    args = parser.parse_args()

    if not torch.cuda.is_available() or not torch.cuda.is_bf16_supported():
        raise RuntimeError("synthetic remount diagnostic requires CUDA BF16")
    torch.use_deterministic_algorithms(True)
    torch.backends.cuda.matmul.allow_tf32 = False
    torch.backends.cudnn.allow_tf32 = False
    torch.backends.cudnn.benchmark = False
    torch.backends.cudnn.deterministic = True

    host = load_verified_host(
        args.snapshot,
        environment={
            "HF_HUB_OFFLINE": os.environ.get("HF_HUB_OFFLINE", ""),
            "TRANSFORMERS_OFFLINE": os.environ.get("TRANSFORMERS_OFFLINE", ""),
            "HF_DATASETS_OFFLINE": os.environ.get("HF_DATASETS_OFFLINE", ""),
        },
        device="cuda",
        dtype=torch.bfloat16,
    )
    wrapper = PinnedLlamaCapsuleWrapper(host)
    input_ids = torch.tensor([[2, 3, 5, 7, 11, 13, 17, 19]], device="cuda")
    with torch.inference_mode():
        baseline = wrapper(input_ids=input_ids, use_cache=False).logits[:, -1, :]
    capsule = deserialize_capsule(
        args.manifest.read_bytes(), args.tensors.read_bytes()
    ).to(device="cuda")
    wrapper.mount(capsule)
    with torch.inference_mode():
        remounted = wrapper(input_ids=input_ids, use_cache=False).logits[:, -1, :]
    wrapper.detach()

    observation = {
        "status": "synthetic-remount-verified-non-authorizing",
        "training_authority": False,
        "held_out_data_present": False,
        "base_state_sha256": encode_base_state(host.model.state_dict()).sha256,
        "baseline_logits_sha256": _logits_sha256(baseline),
        "remounted_logits_sha256": _logits_sha256(remounted),
    }
    sys.stdout.buffer.write(canonical_json_bytes(observation))


if __name__ == "__main__":
    main()
