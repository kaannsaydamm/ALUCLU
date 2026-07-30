from __future__ import annotations

import argparse
import json
import os
import platform
import random
import tempfile
import time
from pathlib import Path

import torch

from aluclu import (
    AlucluLanguageModel,
    build_research_config,
    generate_mqar_batch,
    mqar_accuracy,
    parameter_count,
    tensor_tree_bytes,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Train the bounded hybrid model on diagnostic next-token MQAR."
    )
    parser.add_argument("--steps", type=int, default=200)
    parser.add_argument("--batch-size", type=int, default=32)
    parser.add_argument("--n-pairs", type=int, default=8)
    parser.add_argument("--n-queries", type=int, default=4)
    parser.add_argument("--key-vocab-size", type=int, default=128)
    parser.add_argument("--value-vocab-size", type=int, default=128)
    parser.add_argument("--d-model", type=int, default=64)
    parser.add_argument("--n-layers", type=int, default=4)
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--learning-rate", type=float, default=3e-4)
    parser.add_argument("--weight-decay", type=float, default=0.01)
    parser.add_argument("--eval-batches", type=int, default=8)
    parser.add_argument(
        "--device",
        default="cuda" if torch.cuda.is_available() else "cpu",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("results/diagnostic_mqar.json"),
    )
    args = parser.parse_args()
    for name in (
        "steps",
        "batch_size",
        "n_pairs",
        "n_queries",
        "key_vocab_size",
        "value_vocab_size",
        "d_model",
        "n_layers",
        "eval_batches",
    ):
        if getattr(args, name) < 1:
            parser.error(f"--{name.replace('_', '-')} must be positive")
    return args


def build_model(args: argparse.Namespace, vocab_size: int) -> AlucluLanguageModel:
    config = build_research_config(
        d_model=args.d_model,
        n_layers=args.n_layers,
        local_window=32,
        segment_size=8,
        live_segments=8,
        archive_slots=4,
        archive_segments_per_slot=4,
        archive_rank=8,
        exact_cache_capacity=32,
        sketch_dim=64,
    )
    return AlucluLanguageModel(vocab_size, config)


@torch.no_grad()
def evaluate(
    model: AlucluLanguageModel,
    args: argparse.Namespace,
    *,
    device: torch.device,
) -> tuple[float, float]:
    model.eval()
    generator = torch.Generator(device=device)
    generator.manual_seed(args.seed + 10_000)
    losses = []
    accuracies = []
    for _ in range(args.eval_batches):
        batch = generate_mqar_batch(
            args.batch_size,
            args.n_pairs,
            args.n_queries,
            key_vocab_size=args.key_vocab_size,
            value_vocab_size=args.value_vocab_size,
            device=device,
            generator=generator,
        )
        output = model(
            batch.input_ids,
            labels=batch.labels,
            loss_mask=batch.loss_mask,
        )
        if output.loss is None:
            raise RuntimeError("evaluation loss was not produced")
        losses.append(output.loss.item())
        accuracies.append(mqar_accuracy(output.logits, batch).item())
    model.train()
    return sum(losses) / len(losses), sum(accuracies) / len(accuracies)


def atomic_json_dump(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=path.name,
        suffix=".tmp",
        dir=path.parent,
    )
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            json.dump(payload, handle, indent=2, sort_keys=True)
            handle.write("\n")
        os.replace(temporary_name, path)
    except BaseException:
        if os.path.exists(temporary_name):
            os.unlink(temporary_name)
        raise


def main() -> None:
    args = parse_args()
    random.seed(args.seed)
    torch.manual_seed(args.seed)
    device = torch.device(args.device)

    example = generate_mqar_batch(
        1,
        args.n_pairs,
        args.n_queries,
        key_vocab_size=args.key_vocab_size,
        value_vocab_size=args.value_vocab_size,
    )
    model = build_model(args, example.vocab_size).to(device)
    optimizer = torch.optim.AdamW(
        model.parameters(),
        lr=args.learning_rate,
        weight_decay=args.weight_decay,
    )
    generator = torch.Generator(device=device)
    generator.manual_seed(args.seed)
    started = time.perf_counter()
    first_loss = None

    for step in range(1, args.steps + 1):
        batch = generate_mqar_batch(
            args.batch_size,
            args.n_pairs,
            args.n_queries,
            key_vocab_size=args.key_vocab_size,
            value_vocab_size=args.value_vocab_size,
            device=device,
            generator=generator,
        )
        output = model(
            batch.input_ids,
            labels=batch.labels,
            loss_mask=batch.loss_mask,
        )
        if output.loss is None:
            raise RuntimeError("training loss was not produced")
        if first_loss is None:
            first_loss = output.loss.item()
        optimizer.zero_grad(set_to_none=True)
        output.loss.backward()
        torch.nn.utils.clip_grad_norm_(model.parameters(), max_norm=1.0)
        optimizer.step()
        if step == 1 or step % max(1, args.steps // 10) == 0:
            accuracy = mqar_accuracy(output.logits.detach(), batch).item()
            print(
                f"step={step:05d} loss={output.loss.item():.5f} "
                f"answer_accuracy={accuracy:.4f}"
            )

    elapsed = time.perf_counter() - started
    eval_loss, eval_accuracy = evaluate(model, args, device=device)
    sample = generate_mqar_batch(
        1,
        args.n_pairs,
        args.n_queries,
        key_vocab_size=args.key_vocab_size,
        value_vocab_size=args.value_vocab_size,
        device=device,
    )
    final_state = model(sample.input_ids).state
    payload = {
        "protocol_id": "aluclu_diagnostic_next_token_mqar_v1",
        "result": {
            "first_train_loss": first_loss,
            "eval_loss": eval_loss,
            "eval_answer_accuracy": eval_accuracy,
            "elapsed_seconds": elapsed,
            "train_tokens_per_second": (
                args.steps * args.batch_size * sample.input_ids.shape[1] / elapsed
            ),
            "state_bytes_batch1": tensor_tree_bytes(final_state),
        },
        "config": vars(args) | {"output": str(args.output)},
        "model": {
            "parameters": parameter_count(model),
            "trainable_parameters": parameter_count(model, trainable_only=True),
            "architecture": repr(model.config),
        },
        "environment": {
            "python": platform.python_version(),
            "torch": torch.__version__,
            "device": str(device),
            "cuda": torch.version.cuda,
            "platform": platform.platform(),
        },
    }
    atomic_json_dump(args.output, payload)
    print(
        f"eval_loss={eval_loss:.5f} eval_answer_accuracy={eval_accuracy:.4f} "
        f"result={args.output}"
    )


if __name__ == "__main__":
    main()
