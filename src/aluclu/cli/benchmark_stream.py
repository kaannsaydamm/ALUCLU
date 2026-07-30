from __future__ import annotations

import argparse
import json
import os
import platform
import tempfile
import time
from pathlib import Path

import torch

from aluclu import (
    AlucluLanguageModel,
    build_research_config,
    parameter_count,
    tensor_tree_bytes,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Measure recurrent decode/prefill latency and bounded state."
    )
    parser.add_argument("--d-model", type=int, default=64)
    parser.add_argument("--n-layers", type=int, default=4)
    parser.add_argument("--vocab-size", type=int, default=8192)
    parser.add_argument("--warmup-tokens", type=int, default=640)
    parser.add_argument("--measure-tokens", type=int, default=128)
    parser.add_argument("--prefill-tokens", type=int, default=512)
    parser.add_argument("--repeats", type=int, default=3)
    parser.add_argument(
        "--torch-threads",
        type=int,
        default=0,
        help="0 keeps the PyTorch default; a positive value pins CPU threads.",
    )
    parser.add_argument(
        "--device",
        default="cuda" if torch.cuda.is_available() else "cpu",
    )
    parser.add_argument("--output", type=Path)
    return parser.parse_args()


def build_model(args: argparse.Namespace) -> AlucluLanguageModel:
    config = build_research_config(
        d_model=args.d_model,
        n_layers=args.n_layers,
        local_window=64,
        segment_size=16,
        live_segments=16,
        archive_slots=4,
        archive_segments_per_slot=4,
        archive_rank=8,
        exact_cache_capacity=64,
    )
    return AlucluLanguageModel(
        args.vocab_size,
        config,
    )


def synchronize(device: torch.device) -> None:
    if device.type == "cuda":
        torch.cuda.synchronize(device)


def state_saturation_tokens(model: AlucluLanguageModel) -> int:
    requirements = [1]
    for block in model.blocks:
        if block.local_attention is not None:
            requirements.append(block.local_attention.window_size)
        if block.exact_cache is not None:
            requirements.append(block.exact_cache.config.capacity)
        if block.episodic is not None:
            requirements.append(block.episodic.maximum_retained_tokens())
    return max(requirements)


@torch.inference_mode()
def run_once(
    model: AlucluLanguageModel,
    args: argparse.Namespace,
    device: torch.device,
    tokens: torch.Tensor,
) -> tuple[float, int]:
    state = None
    for index in range(args.warmup_tokens):
        _, state = model.step(tokens[index : index + 1], state)
    synchronize(device)
    started = time.perf_counter()
    for index in range(args.warmup_tokens, tokens.shape[0]):
        _, state = model.step(tokens[index : index + 1], state)
    synchronize(device)
    elapsed = time.perf_counter() - started
    if state is None:
        raise RuntimeError("benchmark state was not created")
    return args.measure_tokens / elapsed, tensor_tree_bytes(state)


@torch.inference_mode()
def run_prefill_once(
    model: AlucluLanguageModel,
    args: argparse.Namespace,
    device: torch.device,
    tokens: torch.Tensor,
) -> float:
    model(tokens[: min(16, args.prefill_tokens)].view(1, -1))
    synchronize(device)
    started = time.perf_counter()
    model(tokens.view(1, -1))
    synchronize(device)
    return args.prefill_tokens / (time.perf_counter() - started)


def metric_summary(samples: list[float]) -> dict[str, float | list[float]]:
    ordered = sorted(samples)
    return {
        "min": ordered[0],
        "median": ordered[len(ordered) // 2],
        "max": ordered[-1],
        "samples": ordered,
    }


def atomic_write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=path.name,
        suffix=".tmp",
        dir=path.parent,
    )
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            handle.write(content)
        os.replace(temporary_name, path)
    except BaseException:
        if os.path.exists(temporary_name):
            os.unlink(temporary_name)
        raise


def main() -> None:
    args = parse_args()
    if (
        min(
            args.d_model,
            args.n_layers,
            args.vocab_size,
            args.warmup_tokens,
            args.measure_tokens,
            args.prefill_tokens,
            args.repeats,
        )
        < 1
    ):
        raise ValueError("numeric arguments must be positive")
    if args.torch_threads < 0:
        raise ValueError("torch-threads must be non-negative")
    if args.torch_threads:
        torch.set_num_threads(args.torch_threads)
    torch.manual_seed(0)
    device = torch.device(args.device)
    model = build_model(args).to(device).eval()
    saturation_tokens = state_saturation_tokens(model)
    generator = torch.Generator(device=device)
    generator.manual_seed(1)
    decode_tokens = [
        torch.randint(
            0,
            args.vocab_size,
            (args.warmup_tokens + args.measure_tokens,),
            device=device,
            generator=generator,
        )
        for _ in range(args.repeats)
    ]
    prefill_tokens = [
        torch.randint(
            0,
            args.vocab_size,
            (args.prefill_tokens,),
            device=device,
            generator=generator,
        )
        for _ in range(args.repeats)
    ]
    measurements = [run_once(model, args, device, tokens) for tokens in decode_tokens]
    decode_throughputs = [item[0] for item in measurements]
    prefill_throughputs = [
        run_prefill_once(model, args, device, tokens) for tokens in prefill_tokens
    ]
    state_bytes = {item[1] for item in measurements}
    if len(state_bytes) != 1:
        raise RuntimeError("state size changed between saturated repetitions")
    decode_summary = metric_summary(decode_throughputs)
    median_decode = float(decode_summary["median"])
    payload = {
        "protocol_id": "aluclu_reference_performance_v2",
        "decode": {
            "tokens_per_second": decode_summary,
            "median_milliseconds_per_token": 1000.0 / median_decode,
        },
        "prefill_tokens_per_second": metric_summary(prefill_throughputs),
        "state_bytes_batch1_after_stream": state_bytes.pop(),
        "state_saturation": {
            "required_warmup_tokens": saturation_tokens,
            "decode_started_saturated": args.warmup_tokens >= saturation_tokens,
        },
        "parameters": parameter_count(model),
        "config": {
            key: str(value) if isinstance(value, Path) else value
            for key, value in vars(args).items()
        },
        "environment": {
            "python": platform.python_version(),
            "torch": torch.__version__,
            "device": str(device),
            "cuda": torch.version.cuda,
            "torch_threads": torch.get_num_threads(),
            "platform": platform.platform(),
        },
        "note": (
            "Random token generation is outside timed regions. State is fully "
            "allocated before decode only when decode_started_saturated is true. "
            "This measures the portable recurrent correctness backend, not "
            "fused GPU kernels."
        ),
    }
    rendered = json.dumps(payload, indent=2, sort_keys=True)
    print(rendered)
    if args.output is not None:
        atomic_write(args.output, rendered + "\n")


if __name__ == "__main__":
    main()
