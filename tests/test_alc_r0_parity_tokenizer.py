"""Tokenizer-bound fixture wiring, using stubs; no local snapshot/model run."""

import importlib
import sys
from dataclasses import FrozenInstanceError
from pathlib import Path
from types import SimpleNamespace

import pytest

from aluclu.alc_r0.acquisition import SMOLLM2_135M
from aluclu.alc_r0.checkpoint_parity_cell import _schedule


class StubTokenizer:
    bos_token_id = eos_token_id = 0
    vocab_size = 49152
    is_fast = True

    def __init__(self):
        self.calls = []
        self.ids = {
            "Labels: safe vulnerable\nInput: ": [10, 11, 12],
            "\nVerdict:": [13],
            " safe": [14],
            " vulnerable": [15, 16],
        }

    def __len__(self):
        return self.vocab_size

    def encode(self, text, *, add_special_tokens):
        assert add_special_tokens is False
        self.calls.append(text)
        return self.ids[text].copy()


@pytest.fixture
def setup(monkeypatch):
    module = importlib.import_module("aluclu.alc_r0.checkpoint_parity_tokenizer")
    tokenizer, calls = StubTokenizer(), []
    tokenizer.production_loader = module._load_tokenizer
    receipt = {
        "repository": SMOLLM2_135M.repository,
        "revision": SMOLLM2_135M.revision,
        "inventory_sha256": "d9db0058a63990399f26b53ff7480f2e67bd5ef9a0398797fecfeb4ed9732b0e",
    }

    def verify(path):
        calls.append(("verify", path))
        return receipt.copy()

    def load(path):
        calls.append(("load", path))
        return tokenizer

    monkeypatch.setattr(module, "verify_model_snapshot", verify)
    monkeypatch.setattr(module, "_load_tokenizer", load)
    for flag in ("HF_HUB_OFFLINE", "TRANSFORMERS_OFFLINE", "HF_DATASETS_OFFLINE"):
        monkeypatch.setenv(flag, "1")
    return module, tokenizer, calls, receipt


def test_six_fixture_schedule_and_complete_candidates(setup, tmp_path):
    module, tokenizer, calls, receipt = setup
    result = module.load_parity_fixtures(tmp_path)
    assert calls == [("verify", tmp_path), ("load", tmp_path), ("verify", tmp_path)]
    _schedule(result.fixtures)
    assert result.snapshot_inventory_sha256 == receipt["inventory_sha256"]
    assert result.model_revision == SMOLLM2_135M.revision
    assert result.tokenizer_class.endswith(".StubTokenizer")
    assert len(result.fixture_sha256) == 64
    assert result.fixtures[0].candidate_ids == (14,)
    assert result.fixtures[1].candidate_ids == (15, 16)
    for index, length in ((0, 32), (2, 64)):
        code = tuple((i + 1) % 49151 + 1 for i in range(length - 6))
        prompt = (10, 11, 12) + code + (13,)
        assert result.fixtures[index].input_ids == prompt + (14,)
        assert result.fixtures[index + 1].input_ids == prompt + (15, 16)
    for original, padded in zip(result.fixtures[2:4], result.fixtures[4:6]):
        assert padded.input_ids == original.input_ids + (0,) * 7
        assert padded.labels == original.labels + (-100,) * 7
    assert len(tokenizer.calls) == 8  # two identical four-field encodings
    with pytest.raises(FrozenInstanceError):
        result.fixture_sha256 = "a" * 64


def test_fixture_digest_is_repeatable_and_binds_actual_ids(setup, tmp_path):
    module, tokenizer, _, _ = setup
    first = module.load_parity_fixtures(tmp_path)
    assert first == module.load_parity_fixtures(tmp_path)
    tokenizer.ids[" safe"] = [17]
    changed = module.load_parity_fixtures(tmp_path)
    assert first.fixture_sha256 != changed.fixture_sha256
    assert first.fixtures[0].candidate_ids == (14,)


@pytest.mark.parametrize(
    "flag", ["HF_HUB_OFFLINE", "TRANSFORMERS_OFFLINE", "HF_DATASETS_OFFLINE"]
)
def test_offline_denial_precedes_asset_or_tokenizer_access(
    setup, monkeypatch, tmp_path, flag
):
    module, _, calls, _ = setup
    monkeypatch.setenv(flag, "0")
    with pytest.raises(module.ParityTokenizerError, match="offline"):
        module.load_parity_fixtures(tmp_path)
    assert calls == []


@pytest.mark.parametrize(
    "field,value",
    [
        ("bos_token_id", 1),
        ("eos_token_id", None),
        ("eos_token_id", False),
        ("vocab_size", 49153),
        ("vocab_size", True),
        ("is_fast", False),
        ("is_fast", 1),
    ],
)
def test_pinned_tokenizer_metadata_denied_before_encoding(
    setup, tmp_path, field, value
):
    module, tokenizer, _, _ = setup
    setattr(tokenizer, field, value)
    with pytest.raises(module.ParityTokenizerError, match="tokenizer"):
        module.load_parity_fixtures(tmp_path)
    assert tokenizer.calls == []


@pytest.mark.parametrize("tokens", [[], [0], [49152], [True], list(range(1, 65))])
def test_invalid_or_infeasible_complete_candidate_fails(setup, tmp_path, tokens):
    module, tokenizer, _, _ = setup
    tokenizer.ids[" vulnerable"] = tokens
    with pytest.raises(module.ParityTokenizerError):
        module.load_parity_fixtures(tmp_path)


def test_encoding_drift_rejected(setup, monkeypatch, tmp_path):
    module, tokenizer, _, _ = setup
    encode = tokenizer.encode

    def changed(text, *, add_special_tokens):
        result = encode(text, add_special_tokens=add_special_tokens)
        return [17] if len(tokenizer.calls) > 4 and text == " safe" else result

    monkeypatch.setattr(tokenizer, "encode", changed)
    with pytest.raises(module.ParityTokenizerError, match="changed"):
        module.load_parity_fixtures(tmp_path)


def test_snapshot_drift_rejected_after_encoding(setup, monkeypatch, tmp_path):
    module, _, calls, receipt = setup

    def changed(path):
        calls.append(("verify", path))
        return receipt | {
            "inventory_sha256": "a" * 64
            if len(calls) > 1
            else receipt["inventory_sha256"]
        }

    monkeypatch.setattr(module, "verify_model_snapshot", changed)
    with pytest.raises(module.ParityTokenizerError, match="snapshot"):
        module.load_parity_fixtures(tmp_path)


def test_snapshot_denial_precedes_tokenizer_load(setup, monkeypatch, tmp_path):
    module, _, calls, _ = setup

    def denied(path):
        raise ValueError("corrupt snapshot")

    monkeypatch.setattr(module, "verify_model_snapshot", denied)
    with pytest.raises(module.ParityTokenizerError, match="snapshot"):
        module.load_parity_fixtures(tmp_path)
    assert calls == []


def test_production_loader_explicit_local_only_without_remote_code(
    setup, monkeypatch, tmp_path
):
    module, tokenizer, _, _ = setup
    calls = []

    def from_pretrained(*args, **kwargs):
        calls.append((args, kwargs))
        return tokenizer

    monkeypatch.setitem(
        sys.modules,
        "transformers",
        SimpleNamespace(AutoTokenizer=SimpleNamespace(from_pretrained=from_pretrained)),
    )
    actual_loader = tokenizer.production_loader
    assert actual_loader(tmp_path) is tokenizer
    assert calls == [
        (
            (str(tmp_path),),
            {"local_files_only": True, "trust_remote_code": False, "use_fast": True},
        )
    ]


def test_relative_snapshot_rejected_before_access(setup):
    module, _, calls, _ = setup
    with pytest.raises(module.ParityTokenizerError, match="absolute"):
        module.load_parity_fixtures(Path("relative"))
    assert calls == []
