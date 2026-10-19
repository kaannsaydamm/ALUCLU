"""One fresh-process, non-authorizing GPU forward-conformance observation."""

from __future__ import annotations

import argparse
import hashlib
import os
import sys
from pathlib import Path

import torch
from transformers.modeling_outputs import CausalLMOutputWithPast

from aluclu.alc_r0.canonical import canonical_json_bytes
from aluclu.alc_r0.host import load_verified_host
from aluclu.alc_r0.host_wrapper import PinnedLlamaCapsuleWrapper


def _digest(tensor: torch.Tensor) -> str:
    raw = tensor.detach().contiguous().cpu().view(torch.uint8).numpy().tobytes()
    return hashlib.sha256(raw).hexdigest()


def _cases() -> list[tuple[int, int, str, bool]]:
    return [
        (1, length, "none", explicit)
        for length in (1, 8, 127, 512)
        for explicit in (False, True)
    ] + [
        (2, length, side, explicit)
        for length in (8, 127, 512)
        for side in ("left", "right")
        for explicit in (False, True)
    ]


def _inputs(
    batch: int, length: int, side: str, explicit: bool
) -> tuple[torch.Tensor, torch.Tensor | None, torch.Tensor | None]:
    full = torch.arange(1, length + 1, device="cuda", dtype=torch.long)
    if batch == 1:
        ids = full.unsqueeze(0)
        mask = None
    else:
        shorter = torch.arange(100, 100 + length // 2, device="cuda")
        padding = torch.zeros(length - len(shorter), device="cuda", dtype=torch.long)
        padded = (
            torch.cat((padding, shorter))
            if side == "left"
            else torch.cat((shorter, padding))
        )
        ids = torch.stack((full, padded))
        mask = ids.ne(0).long()
    positions = (
        torch.arange(length, device="cuda", dtype=torch.long)
        .unsqueeze(0)
        .expand(batch, -1)
        if explicit
        else None
    )
    return ids, mask, positions


def _check(
    wrapper: PinnedLlamaCapsuleWrapper,
    ids: torch.Tensor,
    mask: torch.Tensor | None,
    positions: torch.Tensor | None,
    *,
    use_cache: bool,
) -> tuple[dict[str, object], CausalLMOutputWithPast, CausalLMOutputWithPast]:
    official = wrapper.base(
        input_ids=ids,
        attention_mask=mask,
        position_ids=positions,
        use_cache=use_cache,
    )
    wrapped = wrapper(
        input_ids=ids,
        attention_mask=mask,
        position_ids=positions,
        use_cache=use_cache,
    )
    if not torch.allclose(wrapped.logits, official.logits, rtol=1e-3, atol=1e-3):
        raise RuntimeError("official/wrapper GPU BF16 logit tolerance failed")
    if not torch.equal(wrapped.logits.argmax(-1), official.logits.argmax(-1)):
        raise RuntimeError("official/wrapper GPU BF16 argmax mismatch")
    return (
        {
            "official_logits_sha256": _digest(official.logits),
            "wrapper_logits_sha256": _digest(wrapped.logits),
        },
        official,
        wrapped,
    )


def observe(snapshot: Path) -> dict[str, object]:
    if os.environ.get("CUBLAS_WORKSPACE_CONFIG") != ":4096:8":
        raise RuntimeError(
            "CUBLAS_WORKSPACE_CONFIG must be :4096:8 before CUDA initialization"
        )
    if not torch.cuda.is_available() or not torch.cuda.is_bf16_supported():
        raise RuntimeError("CUDA BF16 is unavailable")
    torch.use_deterministic_algorithms(True)
    torch.backends.cuda.matmul.allow_tf32 = False
    torch.backends.cudnn.allow_tf32 = False
    torch.backends.cudnn.benchmark = False
    torch.backends.cudnn.deterministic = True

    host = load_verified_host(
        snapshot,
        environment={
            "HF_HUB_OFFLINE": "1",
            "TRANSFORMERS_OFFLINE": "1",
            "HF_DATASETS_OFFLINE": "1",
        },
        device="cuda",
        dtype=torch.bfloat16,
    )
    wrapper = PinnedLlamaCapsuleWrapper(host)
    results: dict[str, dict[str, object]] = {}
    with torch.inference_mode():
        for batch, length, side, explicit in _cases():
            ids, mask, positions = _inputs(batch, length, side, explicit)
            name = f"b{batch}-n{length}-{side}-p{int(explicit)}"
            results[name], _, _ = _check(wrapper, ids, mask, positions, use_cache=False)
        for length in (1, 8, 127, 512):
            ids, _, _ = _inputs(1, length, "none", False)
            initial, official, wrapped = _check(
                wrapper, ids, None, None, use_cache=True
            )
            next_id = torch.tensor([[42]], device="cuda", dtype=torch.long)
            next_mask = torch.ones((1, length + 1), device="cuda", dtype=torch.long)
            official_next = wrapper.base(
                input_ids=next_id,
                attention_mask=next_mask,
                past_key_values=official.past_key_values,
                use_cache=True,
            )
            wrapped_next = wrapper(
                input_ids=next_id,
                attention_mask=next_mask,
                past_key_values=wrapped.past_key_values,
                use_cache=True,
            )
            if not torch.allclose(
                wrapped_next.logits, official_next.logits, rtol=1e-3, atol=1e-3
            ):
                raise RuntimeError("incremental GPU BF16 logit tolerance failed")
            if not torch.equal(
                wrapped_next.logits.argmax(-1), official_next.logits.argmax(-1)
            ):
                raise RuntimeError("incremental GPU BF16 argmax mismatch")
            results[f"cache-n{length}"] = {
                "initial": initial,
                "official_logits_sha256": _digest(official_next.logits),
                "wrapper_logits_sha256": _digest(wrapped_next.logits),
            }
    return {
        "case_count": len(results),
        "cases": results,
        "cublas_workspace_config": os.environ["CUBLAS_WORKSPACE_CONFIG"],
        "experiment_id": "alc-r0-smollm2-135m-v1",
        "gpu": torch.cuda.get_device_name(0),
        "schema_version": 1,
        "torch": str(torch.__version__),
        "training_authority": False,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--snapshot", type=Path, required=True)
    args = parser.parse_args()
    sys.stdout.buffer.write(canonical_json_bytes(observe(args.snapshot)))


if __name__ == "__main__":
    main()
