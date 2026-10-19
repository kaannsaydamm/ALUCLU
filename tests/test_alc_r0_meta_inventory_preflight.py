"""Pure config rejection tests; never invoke meta-host construction."""

import importlib.util
from pathlib import Path

import pytest

_SCRIPT = Path(__file__).resolve().parents[1] / "scripts/inventory_alc_r0_meta_host.py"
_SPEC = importlib.util.spec_from_file_location("meta_inventory_preflight", _SCRIPT)
inventory = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(inventory)


def test_relative_config_rejected():
    with pytest.raises(ValueError, match="absolute regular"):
        inventory.read_pinned_config(Path("config.json"))


def test_wrong_config_length_rejected(tmp_path):
    config = tmp_path / "config.json"
    config.write_bytes(b"{}")
    with pytest.raises(ValueError, match="length mismatch"):
        inventory.read_pinned_config(config)


def test_same_length_wrong_config_digest_rejected(tmp_path):
    config = tmp_path / "config.json"
    config.write_bytes(b" " * 704)
    with pytest.raises(ValueError, match="digest mismatch"):
        inventory.read_pinned_config(config)
