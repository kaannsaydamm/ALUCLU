"""Fresh-process package isolation; no host/model/assets are instantiated."""

import os
import subprocess
import sys
import textwrap
from pathlib import Path

import pytest
from alc_r0_public_export_contract import (
    R0_ALL,
    R0_EXPORT_MODULES,
    ROOT_ALL,
    ROOT_EXPORT_MODULES,
)

PACKAGES = (
    ("aluclu", ROOT_ALL, ROOT_EXPORT_MODULES),
    ("aluclu.alc_r0", R0_ALL, R0_EXPORT_MODULES),
)


def _fresh(script, *, no_site=False):
    source = Path(__file__).resolve().parents[1] / "src"
    environment = os.environ.copy()
    environment.update(
        PYTHONPATH=str(source), PYTHONNOUSERSITE="1", CUDA_VISIBLE_DEVICES="-1"
    )
    command = [sys.executable]
    if no_site:
        command.append("-S")
    completed = subprocess.run(
        command + ["-c", textwrap.dedent(script)],
        env=environment,
        cwd=source.parent,
        capture_output=True,
        text=True,
        timeout=90,
        check=False,
    )
    assert completed.returncode == 0, completed.stdout + completed.stderr
    assert completed.stdout.strip() == "export-contract-ok"
    assert completed.stderr == ""


@pytest.mark.parametrize("package,names,modules", PACKAGES)
def test_roster_dir_unknown_do_not_resolve_exports(package, names, modules):
    _fresh(
        f"""
        import importlib
        import sys
        package = importlib.import_module({package!r})
        expected = {names!r}
        assert package.__all__ == expected
        assert set(expected) <= set(dir(package))
        if package.__name__ == "aluclu":
            assert package.__version__ == "0.1.0"
        assert not set({list(modules)!r}).intersection(vars(package))
        before = set(sys.modules)
        try:
            getattr(package, "not_a_public_export")
        except AttributeError:
            pass
        else:
            raise AssertionError("unknown export accepted")
        assert set(sys.modules) == before
        assert not {{"torch", "transformers", "cryptography", "rfc8785",
                    "jsonschema", "numpy"}}.intersection(sys.modules)
        print("export-contract-ok")
    """,
        no_site=True,
    )


@pytest.mark.parametrize("package,names,modules", PACKAGES)
def test_all_exports_keep_direct_identity_from_and_star(package, names, modules):
    _fresh(f"""
        import importlib
        import sys
        package = importlib.import_module({package!r})
        modules = {modules!r}
        assert package.__all__ == {names!r}
        for name, module in modules.items():
            original = getattr(importlib.import_module(module), name)
            assert getattr(package, name) is original
            assert getattr(package, name) is original
            assert vars(package)[name] is original
            namespace = {{}}
            exec("from " + package.__name__ + " import " + name, namespace)
            assert namespace[name] is original
        namespace = {{}}
        exec("from " + package.__name__ + " import *", namespace)
        assert set(namespace) - {{"__builtins__"}} == set(package.__all__)
        for name in package.__all__:
            assert namespace[name] is getattr(package, name)
        assert not sys.modules["torch"].cuda.is_initialized()
        print("export-contract-ok")
    """)


@pytest.mark.parametrize(
    "package,symbol,direct",
    (
        ("aluclu", "GatedDeltaRule2", "aluclu.gated_delta"),
        ("aluclu.alc_r0", "HostLoadError", "aluclu.alc_r0.host"),
    ),
)
def test_dependency_failure_is_not_cached_and_retry_keeps_identity(
    package, symbol, direct
):
    _fresh(f"""
        import importlib
        import importlib.abc
        import sys
        package = importlib.import_module({package!r})
        assert "torch" not in sys.modules
        attempts = []
        class DenyTorch(importlib.abc.MetaPathFinder):
            def find_spec(self, fullname, path=None, target=None):
                if fullname == "torch" or fullname.startswith("torch."):
                    attempts.append(fullname)
                    raise ModuleNotFoundError("intentional torch denial", name=fullname)
                return None
        blocker = DenyTorch()
        sys.meta_path.insert(0, blocker)
        for _ in range(2):
            try:
                getattr(package, {symbol!r})
            except ModuleNotFoundError as error:
                assert str(error) == "intentional torch denial"
                assert error.name == "torch"
            else:
                raise AssertionError("dependency failure suppressed")
            assert {symbol!r} not in vars(package)
        assert attempts == ["torch", "torch"]
        sys.meta_path.remove(blocker)
        original = getattr(importlib.import_module({direct!r}), {symbol!r})
        assert getattr(package, {symbol!r}) is original
        assert vars(package)[{symbol!r}] is original
        assert not sys.modules["torch"].cuda.is_initialized()
        print("export-contract-ok")
    """)


@pytest.mark.parametrize(
    "package,submodule,symbol",
    (
        ("aluclu", "config", "AlucluConfig"),
        ("aluclu.alc_r0", "host", "PinnedHostConfig"),
    ),
)
@pytest.mark.parametrize("submodule_first", (False, True))
def test_submodule_and_export_import_orders(
    package, submodule, symbol, submodule_first
):
    _fresh(f"""
        import importlib
        import types
        package = importlib.import_module({package!r})
        if {submodule_first!r}:
            direct = importlib.import_module({package + "." + submodule!r})
            exported = getattr(package, {symbol!r})
        else:
            exported = getattr(package, {symbol!r})
            direct = importlib.import_module({package + "." + submodule!r})
        assert exported is getattr(direct, {symbol!r})
        assert getattr(package, {submodule!r}) is direct
        assert isinstance(direct, types.ModuleType)
        namespace = {{}}
        exec("from " + package.__name__ + " import " + {submodule!r}, namespace)
        assert namespace[{submodule!r}] is direct
        print("export-contract-ok")
    """)


@pytest.mark.parametrize(
    "package,symbols",
    (
        ("aluclu", ("AlucluConfig", "GatedDeltaRule2")),
        ("aluclu.alc_r0", ("HostLoadError", "PinnedHostConfig")),
    ),
)
def test_concurrent_exports_and_direct_imports_keep_identity(package, symbols):
    _fresh(f"""
        import importlib
        from concurrent.futures import ThreadPoolExecutor
        from threading import Barrier
        package = importlib.import_module({package!r})
        symbols = {symbols!r}
        barrier = Barrier(4)
        def resolve(index):
            barrier.wait(timeout=10)
            if index == 3:
                return importlib.import_module(
                    "aluclu.gated_delta" if package.__name__ == "aluclu"
                    else "aluclu.alc_r0.host"
                )
            return getattr(package, symbols[index % 2])
        with ThreadPoolExecutor(max_workers=4) as pool:
            results = list(pool.map(resolve, range(4)))
        assert results[0] is results[2] is getattr(package, symbols[0])
        assert results[1] is getattr(package, symbols[1])
        assert getattr(results[3], symbols[1]) is results[1]
        print("export-contract-ok")
    """)


@pytest.mark.parametrize(
    "module",
    (
        "aluclu.cli.train_mqar",
        "aluclu.cli.train_zoology_mqar",
        "aluclu.cli.benchmark_stream",
        "aluclu.cli.benchmark_cognition_ledger",
    ),
)
def test_cli_entrypoint_import_without_running_main(module):
    _fresh(f"""
        import importlib
        import sys
        module = importlib.import_module({module!r})
        assert callable(module.main)
        if "torch" in sys.modules:
            assert not sys.modules["torch"].cuda.is_initialized()
        print("export-contract-ok")
    """)


def test_pure_resource_admission_without_third_party_imports():
    source = Path(__file__).resolve().parents[1] / "src"
    script = textwrap.dedent(
        """
        import importlib.abc
        import sys

        blocked = {"torch", "transformers", "numpy", "cryptography",
                   "rfc8785", "jsonschema", "safetensors", "pyarrow"}
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
        import aluclu.alc_r0
        from aluclu.alc_r0.checkpoint_resource_admission import (
            ProgramAccounting, ResourceRequest, assess_resources,
        )

        result = assess_resources(ResourceRequest(
            accounting=ProgramAccounting(False, None, None, None),
            phase="D", device="cpu", now_utc_ns=0, research_bytes=0,
            free_c_bytes=25 * (1 << 30), projected_growth_bytes=0,
            pending_gpu_ns=0, pending_growth_bytes=0,
        ))
        assert result.resource_fit is False
        assert result.reasons == ("history-unreconciled",)
        assert result.remaining_gpu_ns is None
        assert result.program_deadline_utc_ns is None
        assert not attempts, attempts
        assert not blocked.intersection(sys.modules)
        print("pure-admission-isolated")
        """
    )
    environment = os.environ.copy()
    environment["PYTHONPATH"] = str(source)
    environment["PYTHONNOUSERSITE"] = "1"
    environment["CUDA_VISIBLE_DEVICES"] = "-1"
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
    assert completed.stdout.strip() == "pure-admission-isolated"
    assert completed.stderr == ""
