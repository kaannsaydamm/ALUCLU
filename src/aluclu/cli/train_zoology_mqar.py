from __future__ import annotations

import argparse
import json
import os
import platform
import random
import tempfile
import time
from dataclasses import replace
from pathlib import Path

import torch

from aluclu import (
    ZOOLOGY_ICLR24_RAW_PROTOCOL_ID,
    AlucluLanguageModel,
    ZoologyMQARBatch,
    ZoologyMQARConfig,
    build_research_config,
    generate_zoology_mqar_batch,
    parameter_count,
    tensor_tree_bytes,
    zoology_mqar_accuracy,
    zoology_mqar_loss,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Train ALUCLU with historical Zoology query-aligned MQAR semantics."
        )
    )
    parser.add_argument("--input-seq-len", type=int, default=64)
    parser.add_argument("--num-kv-pairs", type=int, default=4)
    parser.add_argument("--vocab-size", type=int, default=8192)
    parser.add_argument("--train-examples", type=int, default=100_000)
    parser.add_argument("--eval-examples", type=int, default=3_000)
    parser.add_argument("--batch-size", type=int, default=512)
    parser.add_argument("--epochs", type=int, default=64)
    parser.add_argument("--d-model", type=int, default=64)
    parser.add_argument("--n-layers", type=int, default=4)
    parser.add_argument("--learning-rate", type=float, default=1e-4)
    parser.add_argument("--weight-decay", type=float, default=0.1)
    parser.add_argument("--model-seed", type=int, default=123)
    parser.add_argument("--data-seed", type=int, default=0)
    parser.add_argument("--power-a", type=float, default=0.01)
    parser.add_argument("--random-non-queries", action="store_true")
    parser.add_argument(
        "--device",
        default="cuda" if torch.cuda.is_available() else "cpu",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("results/zoology_mqar.json"),
    )
    args = parser.parse_args()
    for name in (
        "input_seq_len",
        "num_kv_pairs",
        "vocab_size",
        "train_examples",
        "eval_examples",
        "batch_size",
        "epochs",
        "d_model",
        "n_layers",
    ):
        if getattr(args, name) < 1:
            parser.error(f"--{name.replace('_', '-')} must be positive")
    if args.learning_rate <= 0:
        parser.error("--learning-rate must be positive")
    if args.weight_decay < 0:
        parser.error("--weight-decay must be non-negative")
    return args


def build_model(args: argparse.Namespace) -> AlucluLanguageModel:
    config = build_research_config(
        d_model=args.d_model,
        n_layers=args.n_layers,
        local_window=min(64, args.input_seq_len),
        segment_size=16,
        live_segments=16,
        archive_slots=4,
        archive_segments_per_slot=4,
        archive_rank=8,
        exact_cache_capacity=64,
    )
    return AlucluLanguageModel(args.vocab_size, config)


def select_batch(
    batch: ZoologyMQARBatch,
    indices: torch.Tensor,
    device: torch.device,
) -> ZoologyMQARBatch:
    return ZoologyMQARBatch(
        input_ids=batch.input_ids[indices].to(device),
        labels=batch.labels[indices].to(device),
        loss_mask=batch.loss_mask[indices].to(device),
        query_positions=batch.query_positions[indices].to(device),
        answer_tokens=batch.answer_tokens[indices].to(device),
        config=replace(batch.config, num_examples=indices.numel()),
    )


@torch.no_grad()
def evaluate(
    model: AlucluLanguageModel,
    dataset: ZoologyMQARBatch,
    *,
    batch_size: int,
    device: torch.device,
) -> tuple[float, float]:
    model.eval()
    weighted_loss = 0.0
    weighted_accuracy = 0.0
    count = 0
    for start in range(0, dataset.input_ids.shape[0], batch_size):
        stop = min(start + batch_size, dataset.input_ids.shape[0])
        indices = torch.arange(start, stop)
        batch = select_batch(dataset, indices, device)
        logits = model(batch.input_ids).logits
        examples = stop - start
        weighted_loss += zoology_mqar_loss(logits, batch).item() * examples
        weighted_accuracy += zoology_mqar_accuracy(logits, batch).item() * examples
        count += examples
    model.train()
    return weighted_loss / count, weighted_accuracy / count


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
    random.seed(args.model_seed)
    torch.manual_seed(args.model_seed)
    device = torch.device(args.device)
    train_config = ZoologyMQARConfig(
        num_examples=args.train_examples,
        input_seq_len=args.input_seq_len,
        num_kv_pairs=args.num_kv_pairs,
        vocab_size=args.vocab_size,
        seed=args.data_seed,
        power_a=args.power_a,
        random_non_queries=args.random_non_queries,
    )
    train_dataset = generate_zoology_mqar_batch(train_config)
    eval_dataset = generate_zoology_mqar_batch(
        replace(
            train_config,
            num_examples=args.eval_examples,
            seed=args.data_seed + 10,
        )
    )
    model = build_model(args).to(device)
    optimizer = torch.optim.AdamW(
        model.parameters(),
        lr=args.learning_rate,
        weight_decay=args.weight_decay,
    )
    scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(
        optimizer,
        T_max=args.epochs,
    )
    shuffle_generator = torch.Generator(device="cpu")
    shuffle_generator.manual_seed(args.model_seed)
    started = time.perf_counter()
    first_train_loss = None
    last_train_loss = None
    eval_loss = float("nan")
    eval_accuracy = float("nan")
    completed_epochs = 0

    for epoch in range(1, args.epochs + 1):
        order = torch.randperm(
            args.train_examples,
            generator=shuffle_generator,
        )
        loss_sum = 0.0
        examples_seen = 0
        for start in range(0, args.train_examples, args.batch_size):
            indices = order[start : start + args.batch_size]
            batch = select_batch(train_dataset, indices, device)
            logits = model(batch.input_ids).logits
            loss = zoology_mqar_loss(logits, batch)
            if first_train_loss is None:
                first_train_loss = loss.item()
            optimizer.zero_grad(set_to_none=True)
            loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), max_norm=1.0)
            optimizer.step()
            loss_sum += loss.item() * indices.numel()
            examples_seen += indices.numel()
        scheduler.step()
        last_train_loss = loss_sum / examples_seen
        eval_loss, eval_accuracy = evaluate(
            model,
            eval_dataset,
            batch_size=args.batch_size,
            device=device,
        )
        completed_epochs = epoch
        print(
            f"epoch={epoch:03d} train_loss={last_train_loss:.5f} "
            f"eval_loss={eval_loss:.5f} eval_accuracy={eval_accuracy:.4f}"
        )
        if eval_accuracy > 0.99:
            break

    elapsed = time.perf_counter() - started
    sample = select_batch(eval_dataset, torch.arange(1), device)
    state = model(sample.input_ids).state
    official_grid = {
        (64, 4, 512),
        (128, 8, 512),
        (256, 16, 256),
        (512, 64, 128),
    }
    payload = {
        "protocol_id": "aluclu_zoology_mqar_training_v1",
        "source_data_protocol_id": ZOOLOGY_ICLR24_RAW_PROTOCOL_ID,
        "result": {
            "first_train_loss": first_train_loss,
            "last_train_loss": last_train_loss,
            "eval_loss": eval_loss,
            "eval_accuracy": eval_accuracy,
            "completed_epochs": completed_epochs,
            "elapsed_seconds": elapsed,
            "state_bytes_batch1": tensor_tree_bytes(state),
        },
        "conformance": {
            "same_position_labels": True,
            "additional_causal_shift": False,
            "default_figure2_grid_point": (
                args.input_seq_len,
                args.num_kv_pairs,
                args.batch_size,
            )
            in official_grid,
            "full_historical_dataset_sizes": (
                args.train_examples == 100_000 and args.eval_examples == 3_000
            ),
            "historical_epoch_count": args.epochs == 64,
            "single_learning_rate_run": True,
        },
        "config": {
            key: str(value) if isinstance(value, Path) else value
            for key, value in vars(args).items()
        },
        "model": {
            "parameters": parameter_count(model),
            "architecture": repr(model.config),
        },
        "environment": {
            "python": platform.python_version(),
            "torch": torch.__version__,
            "device": str(device),
            "cuda": torch.version.cuda,
            "platform": platform.platform(),
        },
        "claim_policy": (
            "This trains ALUCLU on tagged data/loss semantics. It is not an "
            "unmodified historical Zoology model result or a four-LR sweep."
        ),
    }
    atomic_json_dump(args.output, payload)
    print(f"result={args.output}")


if __name__ == "__main__":
    main()
