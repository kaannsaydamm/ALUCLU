"""Fresh-process cognition bootstrap checks, not journal or launch authority."""

import os
import subprocess
import sys
import textwrap
from pathlib import Path

import pytest
from alc_r0_public_export_contract import ROOT_EXPORT_MODULES
from cognition_public_export_contract import (
    COGNITION_ALL,
    COGNITION_EXPORT_MODULES,
    COGNITION_SUBMODULES,
)
from test_alc_r0_import_isolation import _fresh


def test_cognition_roster_dir_unknown_and_submodule_collisions():
    _fresh(
        f"""
        import importlib
        import sys
        package = importlib.import_module("aluclu.cognition")
        assert package.__all__ == {COGNITION_ALL!r}
        assert set(package.__all__) <= set(dir(package))
        assert not set(package.__all__).intersection({COGNITION_SUBMODULES!r})
        assert not set(package.__all__).intersection(vars(package))
        before = set(sys.modules)
        try:
            getattr(package, "not_a_cognition_export")
        except AttributeError:
            pass
        else:
            raise AssertionError("unknown export accepted")
        assert set(sys.modules) == before
        assert not {{"cryptography", "torch", "transformers", "keyring"}}.intersection(sys.modules)
        print("export-contract-ok")
    """,
        no_site=True,
    )


def test_complete_cognition_identity_from_star_and_root_reexports():
    root_cognition = {
        name: module
        for name, module in ROOT_EXPORT_MODULES.items()
        if module == "aluclu.cognition"
    }
    _fresh(f"""
        import importlib
        import aluclu
        package = importlib.import_module("aluclu.cognition")
        assert package.__all__ == {COGNITION_ALL!r}
        for name, module in {COGNITION_EXPORT_MODULES!r}.items():
            direct = getattr(importlib.import_module(module), name)
            assert getattr(package, name) is direct
            assert getattr(package, name) is direct
            assert vars(package)[name] is direct
            namespace = {{}}
            exec("from aluclu.cognition import " + name, namespace)
            assert namespace[name] is direct
        namespace = {{}}
        exec("from aluclu.cognition import *", namespace)
        assert set(namespace) - {{"__builtins__"}} == set(package.__all__)
        for name in package.__all__:
            assert namespace[name] is getattr(package, name)
        for name in {list(root_cognition)!r}:
            assert getattr(aluclu, name) is getattr(package, name)
        print("export-contract-ok")
    """)


def test_crypto_dependency_failure_not_cached_then_retry():
    _fresh("""
        import importlib
        import importlib.abc
        import sys
        package = importlib.import_module("aluclu.cognition")
        assert "cryptography" not in sys.modules
        attempts = []
        class DenyCrypto(importlib.abc.MetaPathFinder):
            def find_spec(self, fullname, path=None, target=None):
                if fullname == "cryptography" or fullname.startswith("cryptography."):
                    attempts.append(fullname)
                    raise ModuleNotFoundError("intentional crypto denial", name=fullname)
                return None
        blocker = DenyCrypto()
        sys.meta_path.insert(0, blocker)
        for _ in range(2):
            try:
                package.EncryptedLedger
            except ModuleNotFoundError as error:
                assert str(error) == "intentional crypto denial"
                assert error.name == "cryptography"
            else:
                raise AssertionError("dependency failure suppressed")
            assert "EncryptedLedger" not in vars(package)
        assert attempts == ["cryptography", "cryptography"]
        sys.meta_path.remove(blocker)
        from aluclu.cognition.ledger import EncryptedLedger
        assert package.EncryptedLedger is EncryptedLedger
        assert vars(package)["EncryptedLedger"] is EncryptedLedger
        print("export-contract-ok")
    """)


@pytest.mark.parametrize(
    "submodule,symbol",
    (
        ("persistence", "exclusive_file_lock"),
        ("keys", "StaticKeyProvider"),
        ("recollection", "recall"),
    ),
)
@pytest.mark.parametrize("submodule_first", (False, True))
def test_cognition_submodule_import_orders(submodule, symbol, submodule_first):
    _fresh(f"""
        import importlib
        import types
        package = importlib.import_module("aluclu.cognition")
        if {submodule_first!r}:
            module = importlib.import_module({"aluclu.cognition." + submodule!r})
            exported = getattr(package, {symbol!r})
        else:
            exported = getattr(package, {symbol!r})
            module = importlib.import_module({"aluclu.cognition." + submodule!r})
        assert exported is getattr(module, {symbol!r})
        assert getattr(package, {submodule!r}) is module
        assert isinstance(module, types.ModuleType)
        namespace = {{}}
        exec("from aluclu.cognition import " + {submodule!r}, namespace)
        assert namespace[{submodule!r}] is module
        print("export-contract-ok")
    """)


def test_concurrent_cognition_exports_and_direct_ledger_import():
    _fresh("""
        import importlib
        from concurrent.futures import ThreadPoolExecutor
        from threading import Barrier
        package = importlib.import_module("aluclu.cognition")
        barrier = Barrier(4)
        def resolve(index):
            barrier.wait(timeout=10)
            if index == 3:
                return importlib.import_module("aluclu.cognition.ledger")
            return getattr(package, "PersistenceError" if index % 2 == 0 else "EncryptedLedger")
        with ThreadPoolExecutor(max_workers=4) as pool:
            results = list(pool.map(resolve, range(4)))
        assert results[0] is results[2] is package.PersistenceError
        assert results[1] is results[3].EncryptedLedger is package.EncryptedLedger
        print("export-contract-ok")
    """)


def test_shared_registry_competing_locks_and_atomic_write(tmp_path):
    _fresh(f"""
        import importlib
        import time
        from concurrent.futures import ThreadPoolExecutor
        from pathlib import Path
        from threading import Barrier, Lock
        package = importlib.import_module("aluclu.cognition")
        direct = importlib.import_module("aluclu.cognition.persistence")
        root = Path({str(tmp_path)!r})
        lock_path = root / "shared.lock"
        assert package.exclusive_file_lock is direct.exclusive_file_lock
        assert package.PersistenceError is direct.PersistenceError
        key_a, registry_a = direct._process_path_lock(direct.resolve_ledger_path(lock_path))
        key_b, registry_b = direct._process_path_lock(package.resolve_ledger_path(lock_path))
        assert key_a == key_b and registry_a is registry_b
        barrier = Barrier(2)
        guard = Lock()
        active = 0
        max_active = 0
        completed = 0
        def contend(lock_api):
            global active, max_active, completed
            barrier.wait(timeout=10)
            for _ in range(16):
                with lock_api(lock_path):
                    with guard:
                        active += 1
                        max_active = max(max_active, active)
                    time.sleep(0.001)
                    with guard:
                        active -= 1
                        completed += 1
        with ThreadPoolExecutor(max_workers=2) as pool:
            futures = [pool.submit(contend, api) for api in
                       (package.exclusive_file_lock, direct.exclusive_file_lock)]
            for future in futures:
                future.result(timeout=10)
        assert max_active == 1 and active == 0 and completed == 32
        target = root / "state.bin"
        package.atomic_write_bytes(target, b"old")
        assert target.read_bytes() == b"old"
        direct.atomic_write_bytes(target, b"new")
        assert target.read_bytes() == b"new"
        assert package.resolve_ledger_path(target) == direct.resolve_ledger_path(target)
        print("export-contract-ok")
    """)


def test_persistence_imports_without_third_party_dependencies():
    source = Path(__file__).resolve().parents[1] / "src"
    script = textwrap.dedent(
        """
        import importlib.abc
        import sys

        blocked = {"torch", "transformers", "numpy", "cryptography",
                   "rfc8785", "jsonschema", "safetensors", "pyarrow", "keyring"}
        attempts = []
        class DenyThirdParty(importlib.abc.MetaPathFinder):
            def find_spec(self, fullname, path=None, target=None):
                if fullname.split(".")[0] in blocked:
                    attempts.append(fullname)
                    raise ModuleNotFoundError("forbidden dependency: " + fullname)
                return None

        assert not blocked.intersection(sys.modules), "contaminated subprocess"
        sys.meta_path.insert(0, DenyThirdParty())
        import aluclu
        import aluclu.cognition as cognition
        import aluclu.cognition.contracts as contracts
        import aluclu.cognition.persistence as persistence

        for name in ("atomic_write_bytes", "exclusive_file_lock", "resolve_ledger_path"):
            assert getattr(cognition, name) is getattr(persistence, name)
        assert cognition.PersistenceError is contracts.PersistenceError
        assert cognition.UnsafePathError is contracts.UnsafePathError
        assert aluclu.CognitionError is cognition.CognitionError is contracts.CognitionError
        assert not attempts, attempts
        assert not blocked.intersection(sys.modules)
        print("cognition-persistence-isolated")
        """
    )
    environment = os.environ.copy()
    environment.update(
        PYTHONPATH=str(source), PYTHONNOUSERSITE="1", CUDA_VISIBLE_DEVICES="-1"
    )
    completed = subprocess.run(
        [sys.executable, "-S", "-c", script],
        env=environment,
        cwd=source.parent,
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
    )
    assert completed.returncode == 0, completed.stdout + completed.stderr
    assert completed.stdout.strip() == "cognition-persistence-isolated"
    assert completed.stderr == ""
