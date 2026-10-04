"""Reviewed config-only meta skeleton diagnostic; never a model-run acceptance."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
from pathlib import Path

CONFIG_SHA256 = "1d556eab73b69c7f11f64c557a2f9c6f440bd4c6b89bb2584a6b498c92603843"
PROJECT_ROOT = Path(__file__).resolve().parents[1]


def read_pinned_config(path: Path) -> dict:
    if not path.is_absolute() or path.is_symlink() or not path.is_file():
        raise ValueError("absolute regular config file required")
    if path.stat().st_size != 704:
        raise ValueError("pinned config length mismatch")
    data = path.read_bytes()
    if len(data) != 704 or hashlib.sha256(data).hexdigest() != CONFIG_SHA256:
        raise ValueError("pinned config digest mismatch")
    return json.loads(data)


def clean_commit() -> str:
    status = subprocess.check_output(
        ["git", "status", "--porcelain"], cwd=PROJECT_ROOT, text=True
    )
    if status:
        raise ValueError("inventory requires clean source checkout")
    return subprocess.check_output(
        ["git", "rev-parse", "HEAD"], cwd=PROJECT_ROOT, text=True
    ).strip()


def run(config_path: Path) -> dict:
    config_data = read_pinned_config(config_path)
    commit = clean_commit()
    for variable in ("HF_HUB_OFFLINE", "TRANSFORMERS_OFFLINE"):
        if os.environ.get(variable) != "1":
            raise ValueError("offline environment required")
    if os.environ.get("CUDA_VISIBLE_DEVICES") != "":
        raise ValueError("CUDA devices must be hidden for meta inventory")
    # Import/construction is reached only by the separately reviewed invocation.
    import torch
    import transformers
    from transformers import LlamaConfig, LlamaForCausalLM

    from aluclu.alc_r0.checkpoint_execution import CheckpointExecutionError
    from aluclu.alc_r0.checkpoint_state import computational_state_fingerprint

    if torch.get_default_dtype() is not torch.float32:
        raise ValueError("default FP32 required")
    routes = []
    for route in ("eager", "sdpa"):
        config = LlamaConfig(**config_data)
        config._attn_implementation = route
        with torch.device("meta"):
            model = LlamaForCausalLM(config)
        model.requires_grad_(False).eval()
        modules = tuple(model.named_modules())
        tensors = (*model.parameters(), *model.buffers())
        if len(modules) > 512 or any(t.device.type != "meta" for t in tensors):
            raise ValueError("meta-only bounded skeleton required")
        rows = []
        for name, module in modules:
            row = {
                "name": name,
                "type": type(module).__module__ + "." + type(module).__qualname__,
                "attribute_types": {
                    key: type(value).__module__ + "." + type(value).__qualname__
                    for key, value in sorted(vars(module).items())
                },
            }
            try:
                first = computational_state_fingerprint({"inventory": module})
                second = computational_state_fingerprint({"inventory": module})
                row.update(status="stable" if first == second else "unstable")
            except CheckpointExecutionError as error:
                row.update(status="rejected", reason=str(error))
            rows.append(row)
        routes.append(
            {
                "route": route,
                "module_count": len(modules),
                "parameter_numel": sum(p.numel() for p in model.parameters()),
                "all_tensors_meta": True,
                "modules": rows,
            }
        )
        del model, modules, tensors
    if hashlib.sha256(config_path.read_bytes()).hexdigest() != CONFIG_SHA256:
        raise ValueError("config changed during inventory")
    return {
        "kind": "config_only_meta_host_inventory",
        "source_commit": commit,
        "config_sha256": CONFIG_SHA256,
        "torch_version": torch.__version__,
        "transformers_version": transformers.__version__,
        "weights_loaded": False,
        "forward_executed": False,
        "optimizer_executed": False,
        "training_authority": False,
        "model_run_acceptance": False,
        "routes": routes,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(run(args.config), sort_keys=True, allow_nan=False))


if __name__ == "__main__":
    main()
