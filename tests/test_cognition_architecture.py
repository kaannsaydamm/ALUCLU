from __future__ import annotations

import ast
from pathlib import Path

COGNITION_ROOT = Path(__file__).resolve().parents[1] / "src" / "aluclu" / "cognition"

TASK1_MODULES = frozenset({"codec", "contracts", "keys", "ledger", "persistence"})
TASK2_IMPORT_GRAPH = {
    "observation": frozenset({"codec", "contracts", "recall_features"}),
    "recall_features": frozenset({"codec", "contracts"}),
    "calibration": frozenset({"codec", "contracts"}),
    "sensorium": frozenset({"codec", "contracts", "ledger", "observation"}),
    "recollection": frozenset(
        {
            "calibration",
            "codec",
            "contracts",
            "ledger",
            "observation",
            "recall_features",
        }
    ),
    "reconsolidation": frozenset(
        {"codec", "contracts", "ledger", "observation", "recollection"}
    ),
}
LEDGER_DEPENDENT_TASK2_MODULES = frozenset(
    {"sensorium", "recollection", "reconsolidation"}
)
TASK2_MODULES = frozenset(TASK2_IMPORT_GRAPH)
FORBIDDEN_LEDGER_LIFECYCLE_CALLS = frozenset({"unlock", "verified_session"})


def _tree(module_name: str) -> ast.Module:
    path = COGNITION_ROOT / f"{module_name}.py"
    return ast.parse(path.read_text(encoding="utf-8"), filename=str(path))


def _local_imports(tree: ast.Module) -> list[tuple[str, frozenset[str]]]:
    imports: list[tuple[str, frozenset[str]]] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom):
            if node.level > 0:
                module = (node.module or "").split(".", 1)[0]
            elif (node.module or "").startswith("aluclu.cognition."):
                module = (node.module or "").split(".")[2]
            else:
                continue
            imports.append((module, frozenset(alias.name for alias in node.names)))
        elif isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name.startswith("aluclu.cognition."):
                    imports.append((alias.name.split(".")[2], frozenset()))
    return imports


def _task2_violations(module_name: str, tree: ast.Module) -> tuple[str, ...]:
    violations: list[str] = []
    allowed = TASK2_IMPORT_GRAPH[module_name]
    ledger_names: set[str] = set()

    for imported_module, imported_names in _local_imports(tree):
        if imported_module not in allowed:
            violations.append(
                f"{module_name} imports forbidden cognition module {imported_module}"
            )
        if imported_module == "ledger":
            ledger_names.update(imported_names)

    if "EncryptedLedger" in ledger_names:
        violations.append(f"{module_name} imports EncryptedLedger")

    for node in ast.walk(tree):
        if isinstance(node, ast.Name) and node.id == "EncryptedLedger":
            violations.append(f"{module_name} references EncryptedLedger")
        elif (
            isinstance(node, ast.Attribute)
            and node.attr in FORBIDDEN_LEDGER_LIFECYCLE_CALLS
            and isinstance(getattr(node, "ctx", None), ast.Load)
        ):
            violations.append(f"{module_name} accesses ledger lifecycle {node.attr}")

    if module_name in LEDGER_DEPENDENT_TASK2_MODULES:
        if ledger_names != {"VerifiedLedgerSession"}:
            violations.append(
                f"{module_name} must import only VerifiedLedgerSession from ledger"
            )
    elif ledger_names:
        violations.append(f"{module_name} must not import ledger code")

    return tuple(sorted(set(violations)))


def test_task2_dependency_and_session_ownership_contract() -> None:
    violations: list[str] = []
    for module_name in sorted(TASK2_MODULES):
        violations.extend(_task2_violations(module_name, _tree(module_name)))

    for module_name in sorted(TASK1_MODULES):
        for imported_module, _ in _local_imports(_tree(module_name)):
            if imported_module in TASK2_MODULES:
                violations.append(
                    f"Task 1 module {module_name} imports Task 2 module "
                    f"{imported_module}"
                )

    assert violations == []


def test_architecture_guard_rejects_forbidden_edges_and_nested_session() -> None:
    synthetic = ast.parse(
        "from .ledger import EncryptedLedger, VerifiedLedgerSession\n"
        "from .sensorium import SensoriumStateV1\n"
        "def violate(ledger):\n"
        "    EncryptedLedger(None, None)\n"
        "    return ledger.verified_session()\n"
    )

    violations = _task2_violations("observation", synthetic)

    assert "observation imports forbidden cognition module ledger" in violations
    assert "observation imports forbidden cognition module sensorium" in violations
    assert "observation imports EncryptedLedger" in violations
    assert "observation references EncryptedLedger" in violations
    assert "observation accesses ledger lifecycle verified_session" in violations
    assert "observation must not import ledger code" in violations
