"""Owned fresh-process fake CPU resume, not actual-host or learning evidence.

Trusted fixture code and disposable local files only; no serialized executable,
real assets, GPU, task data, RNG/cursor replay or final .alc format.
"""

import hashlib
import os
import sys
import time
from dataclasses import fields
from pathlib import Path

import pytest
import torch
from safetensors.torch import save
from test_alc_r0_reference_qv_forward import host as host

from aluclu.alc_r0.canonical import canonical_json_bytes, parse_canonical_json
from aluclu.alc_r0.checkpoint_observation import _base_digest
from aluclu.alc_r0.checkpoint_owned_process import run_owned_process
from aluclu.alc_r0.checkpoint_parity_factory import make_reference_wrapper
from aluclu.alc_r0.reference_qv_artifact import (
    deserialize_reference,
    make_reference_optimizer,
    serialize_reference,
)
from aluclu.alc_r0.reference_qv_resume import (
    ReferenceResumeRecord,
    restore_reference_optimizer,
    serialize_reference_resume,
)

ROOT = Path(__file__).resolve().parents[1]
pytestmark = pytest.mark.skipif(
    os.name != "nt", reason="owned Windows Job Object fixture"
)


def sha(data):
    return hashlib.sha256(data).hexdigest()


def identity(base):
    # Full local source identity, not a signed certificate or general ABI.
    paths = sorted((ROOT / "src/aluclu/alc_r0").glob("*.py")) + sorted(
        (ROOT / "tests").glob("test_alc_r0*.py")
    )
    return {
        "sources": {p.relative_to(ROOT).as_posix(): sha(p.read_bytes()) for p in paths},
        "base": _base_digest(base),
        # Transformers' full JSON normalizes integer label-map keys itself.
        "config": sha(base.config.to_json_string(use_diff=False).encode("utf-8")),
        "torch": str(torch.__version__),
        "seed": 20260916,
        "fixture": "IndependentQVLM/random30/identitynorm/linearMLP/rotary64/vocab8",
    }


def inputs(second):
    return dict(
        input_ids=torch.tensor([[4, 5, 6, 0] if second else [1, 2, 3, 0]]),
        labels=torch.tensor([[-100, 5, 6, -100] if second else [-100, 2, 3, -100]]),
        attention_mask=torch.tensor([[1, 1, 1, 0]]),
        position_ids=torch.tensor([[11, 12, 13, 14] if second else [3, 4, 5, 6]]),
        use_cache=False,
    )


def state_hash(wrapper, optimizer, step):
    values = {}
    assert len(optimizer.state) == 120
    for name, parameter in wrapper.reference.named_parameters():
        state = optimizer.state[parameter]
        assert set(state) == {"step", "exp_avg", "exp_avg_sq"}
        assert state["step"].item() == step
        values[f"factor/{name}"] = parameter.detach().contiguous()
        for role, value in state.items():
            assert torch.isfinite(value).all()
            values[f"{role}/{name}"] = value.detach().contiguous()
    assert len(values) == 480
    return sha(save(values))


def update(wrapper, optimizer, *, second, checkpoint):
    args = inputs(second)
    if checkpoint:
        with wrapper.checkpoint_session() as session:
            output = wrapper(**args, checkpoint_session=session)
            session.backward(output.loss)
            assert session.pending_count == 0
    else:
        output = wrapper(**args)
        output.loss.backward()
    tensors = {"logits": output.logits.detach(), "loss": output.loss.detach()}
    for name, parameter in wrapper.reference.named_parameters():
        assert parameter.grad is not None and torch.isfinite(parameter.grad).all()
        tensors[f"gradient/{name}"] = parameter.grad.detach().clone()
    tensors["clipnorm"] = torch.nn.utils.clip_grad_norm_(
        wrapper.reference.parameters(),
        1.0,
        error_if_nonfinite=True,
        foreach=False,
    ).detach()
    assert torch.isfinite(output.loss)
    before_hash = sha(save(tensors))
    optimizer.step()
    optimizer.zero_grad(set_to_none=True)
    with torch.no_grad():
        after = wrapper(**args)
    wrapper._assert_checkpoint_mutation_allowed()
    assert all(p.grad is None for p in wrapper.reference.parameters())
    assert all(
        p.grad is None and not p.requires_grad for p in wrapper.base.parameters()
    )
    return {
        "preclip": before_hash,
        "state": state_hash(wrapper, optimizer, 2 if second else 1),
        "output": sha(save({"logits": after.logits, "loss": after.loss})),
        "factors": [sha(part) for part in serialize_reference(wrapper.reference)],
        "base": _base_digest(wrapper.base),
    }


def child(directory):
    context = parse_canonical_json((directory / "context.json").read_bytes())
    with pytest.MonkeyPatch.context() as monkeypatch:
        rebuilt = host.__wrapped__(monkeypatch)
        assert identity(rebuilt.model) == context["identity"]
        record = ReferenceResumeRecord(
            **{
                field.name: (directory / field.name).read_bytes()
                for field in fields(ReferenceResumeRecord)
            }
        )
        assert [sha(getattr(record, f.name)) for f in fields(record)] == context[
            "record"
        ]
        wrapper = make_reference_wrapper(rebuilt, True, state="zero")
        wrapper.mount_reference(
            deserialize_reference(record.factor_manifest, record.factor_payload)
        )
        optimizer = restore_reference_optimizer(wrapper, record)
        assert serialize_reference_resume(wrapper, optimizer) == record
        assert state_hash(wrapper, optimizer, 1) == context["step1"]
        result = update(wrapper, optimizer, second=True, checkpoint=True)
        assert result["base"] == context["identity"]["base"]
        (directory / "result.json").write_bytes(
            canonical_json_bytes(
                {
                    "pid": os.getpid(),
                    "parent": os.getppid(),
                    "result": result,
                }
            )
        )


def test_fresh_process_rebuild_and_step2_resume_exact(host, tmp_path):
    wrapper = make_reference_wrapper(host, False, state="zero")
    optimizer = make_reference_optimizer(wrapper)
    initial = serialize_reference(wrapper.reference)
    fingerprint = identity(host.model)
    first = update(wrapper, optimizer, second=False, checkpoint=False)
    record = serialize_reference_resume(wrapper, optimizer)
    assert serialize_reference(wrapper.reference) != initial
    assert first["base"] == fingerprint["base"]
    context = {
        "identity": fingerprint,
        "step1": first["state"],
        "record": [sha(getattr(record, f.name)) for f in fields(record)],
    }
    for field in fields(record):
        (tmp_path / field.name).write_bytes(getattr(record, field.name))
    (tmp_path / "context.json").write_bytes(canonical_json_bytes(context))
    expected = update(wrapper, optimizer, second=True, checkpoint=False)
    environment = os.environ.copy()
    environment.update(
        {
            "PYTHONPATH": str(ROOT / "src"),
            "CUDA_VISIBLE_DEVICES": "",
            "HF_HUB_OFFLINE": "1",
            "TRANSFORMERS_OFFLINE": "1",
            "PYTHONDONTWRITEBYTECODE": "1",
        }
    )
    run = run_owned_process(
        command=(sys.executable, "-B", str(Path(__file__).resolve()), str(tmp_path)),
        cwd=ROOT,
        environment=environment,
        stdout_path=tmp_path / "stdout.log",
        stderr_path=tmp_path / "stderr.log",
        deadline_ns=time.monotonic_ns() + 180_000_000_000,
    )
    assert run.exit_code == 0 and not run.timed_out, (
        (tmp_path / "stdout.log").read_bytes(),
        (tmp_path / "stderr.log").read_bytes(),
    )
    assert run.active_processes == 0 and run.total_processes >= 1
    result = parse_canonical_json((tmp_path / "result.json").read_bytes())
    assert result["pid"] != os.getpid()
    assert (result["pid"] == run.root_pid and result["parent"] == os.getpid()) or (
        result["parent"] == run.root_pid and run.total_processes >= 2
    )
    assert result["result"] == expected
    assert expected["base"] == fingerprint["base"]
    assert identity(host.model) == fingerprint


if __name__ == "__main__":
    child(Path(sys.argv[1]))
