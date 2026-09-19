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
            if (node.level > 0 and node.module is None) or (
                node.level == 0 and node.module == "aluclu.cognition"
            ):
                if node.level > 1:
                    imports.append(("<parent relative import>", frozenset()))
                    continue
                imports.extend(
                    (alias.name.split(".", 1)[0], frozenset()) for alias in node.names
                )
                continue
            if node.level == 2 and node.module == "cognition":
                imports.extend(
                    (alias.name.split(".", 1)[0], frozenset()) for alias in node.names
                )
                continue
            if node.level == 2 and (node.module or "").startswith("cognition."):
                module = (node.module or "").split(".")[1]
            elif node.level > 1:
                module = "<parent relative import>"
            elif node.level == 1:
                module = (node.module or "").split(".", 1)[0]
            elif node.module == "aluclu":
                if any(alias.name == "cognition" for alias in node.names):
                    imports.append(("<cognition package>", frozenset()))
                continue
            elif (node.module or "").startswith("aluclu.cognition."):
                module = (node.module or "").split(".")[2]
            else:
                continue
            imports.append((module, frozenset(alias.name for alias in node.names)))
        elif isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name == "aluclu.cognition":
                    imports.append(("<cognition package>", frozenset()))
                elif alias.name.startswith("aluclu.cognition."):
                    imports.append((alias.name.split(".")[2], frozenset()))
    return imports


_LEXICAL_SCOPES = (
    ast.Module,
    ast.FunctionDef,
    ast.AsyncFunctionDef,
    ast.ClassDef,
    ast.Lambda,
)


def _bound_names(target: ast.AST) -> set[str]:
    if isinstance(target, ast.Name):
        return {target.id}
    if isinstance(target, (ast.Tuple, ast.List)):
        return {name for item in target.elts for name in _bound_names(item)}
    return set()


def _scope_parameters(scope: ast.AST) -> set[str]:
    if not isinstance(scope, (ast.FunctionDef, ast.AsyncFunctionDef, ast.Lambda)):
        return set()
    arguments = scope.args
    return (
        {
            argument.arg
            for argument in (
                *arguments.posonlyargs,
                *arguments.args,
                *arguments.kwonlyargs,
            )
        }
        | ({arguments.vararg.arg} if arguments.vararg is not None else set())
        | ({arguments.kwarg.arg} if arguments.kwarg is not None else set())
    )


def _direct_scope_nodes(scope: ast.AST) -> list[ast.AST]:
    nodes = [scope]
    for child in ast.iter_child_nodes(scope):
        if isinstance(child, _LEXICAL_SCOPES):
            continue
        nodes.extend(_direct_scope_nodes(child))
    return nodes


def _nested_scopes(scope: ast.AST) -> list[ast.AST]:
    nested: list[ast.AST] = []
    for child in ast.iter_child_nodes(scope):
        if isinstance(child, _LEXICAL_SCOPES):
            nested.append(child)
        else:
            nested.extend(_nested_scopes(child))
    return nested


def _expression_references_session_constructor(
    expression: ast.AST,
    aliases: set[str],
) -> bool:
    for node in ast.walk(expression):
        if isinstance(node, ast.Name) and node.id in aliases:
            return True
        if isinstance(node, ast.Attribute) and node.attr == "VerifiedLedgerSession":
            return True
        if (
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Name)
            and node.func.id == "getattr"
            and len(node.args) >= 2
            and isinstance(node.args[1], ast.Constant)
            and node.args[1].value == "VerifiedLedgerSession"
        ):
            return True
    return False


def _session_constructor_calls(tree: ast.Module) -> set[ast.Call]:
    calls: set[ast.Call] = set()

    def inspect_scope(scope: ast.AST, inherited: set[str]) -> None:
        direct_nodes = _direct_scope_nodes(scope)
        local_bindings = _scope_parameters(scope)
        assignments: list[tuple[set[str], ast.AST]] = []
        imported_session_aliases: set[str] = set()

        for node in direct_nodes:
            if isinstance(node, ast.Assign):
                targets = {
                    name for target in node.targets for name in _bound_names(target)
                }
                local_bindings.update(targets)
                assignments.append((targets, node.value))
            elif isinstance(node, ast.AnnAssign) and node.value is not None:
                targets = _bound_names(node.target)
                local_bindings.update(targets)
                assignments.append((targets, node.value))
            elif isinstance(node, ast.NamedExpr):
                targets = _bound_names(node.target)
                local_bindings.update(targets)
                assignments.append((targets, node.value))
            elif isinstance(node, (ast.Import, ast.ImportFrom)):
                for alias in node.names:
                    local_bindings.add(alias.asname or alias.name.split(".", 1)[0])
                if isinstance(node, ast.ImportFrom) and (node.level, node.module) in {
                    (1, "ledger"),
                    (2, "cognition.ledger"),
                    (0, "aluclu.cognition.ledger"),
                }:
                    imported_session_aliases.update(
                        alias.asname or alias.name
                        for alias in node.names
                        if alias.name == "VerifiedLedgerSession"
                    )

        local_bindings.update(
            nested.name
            for nested in _nested_scopes(scope)
            if isinstance(nested, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))
        )
        aliases = (inherited - local_bindings) | imported_session_aliases
        while True:
            additions = {
                target
                for targets, value in assignments
                if _expression_references_session_constructor(value, aliases)
                for target in targets
            }
            if additions <= aliases:
                break
            aliases.update(additions)

        calls.update(
            node
            for node in direct_nodes
            if isinstance(node, ast.Call)
            and _expression_references_session_constructor(node.func, aliases)
        )
        for nested in _nested_scopes(scope):
            inspect_scope(nested, aliases)

    inspect_scope(tree, set())
    return calls


def _scope_nodes(root: ast.AST) -> list[ast.AST]:
    nodes = [root]
    for child in ast.iter_child_nodes(root):
        if isinstance(
            child, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef, ast.Lambda)
        ):
            continue
        nodes.extend(_scope_nodes(child))
    return nodes


def _approved_cursor_close(tree: ast.Module, attribute: ast.Attribute) -> bool:
    receiver = attribute.value
    if not isinstance(receiver, ast.Name) or receiver.id != "cursor":
        return False
    enclosing_scopes = [
        node
        for node in ast.walk(tree)
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.Lambda))
        and any(inner is attribute for inner in ast.walk(node))
    ]
    if not enclosing_scopes:
        return False
    scope = enclosing_scopes[-1]
    args = scope.args
    parameters = (*args.posonlyargs, *args.args, *args.kwonlyargs)
    if any(arg.arg == "cursor" for arg in parameters):
        return False
    if args.vararg and args.vararg.arg == "cursor":
        return False
    if args.kwarg and args.kwarg.arg == "cursor":
        return False
    nodes = _scope_nodes(scope)
    if any(
        isinstance(node, (ast.Global, ast.Nonlocal)) and "cursor" in node.names
        for node in nodes
    ):
        return False
    stores = [
        node
        for node in nodes
        if isinstance(node, ast.Name)
        and node.id == "cursor"
        and isinstance(node.ctx, ast.Store)
    ]
    approved_assignments = [
        node
        for node in nodes
        if isinstance(node, ast.Assign)
        and len(node.targets) == 1
        and isinstance(node.targets[0], ast.Name)
        and node.targets[0].id == "cursor"
        and isinstance(node.value, ast.Call)
        and isinstance(node.value.func, ast.Attribute)
        and node.value.func.attr in {"cursor", "resume_verified"}
        and isinstance(node.value.func.value, ast.Name)
        and node.value.func.value.id in {"session", "active"}
    ]
    return bool(stores) and len(stores) == len(approved_assignments)


def _task1_violations(module_name: str, tree: ast.Module) -> tuple[str, ...]:
    imports = _local_imports(tree)
    violations = [
        f"Task 1 module {module_name} imports Task 2 module {imported_module}"
        for imported_module, _ in imports
        if imported_module in TASK2_MODULES
    ]
    if any(
        imported_module in {"<cognition package>", "<parent relative import>"}
        for imported_module, _ in imports
    ):
        violations.append(f"Task 1 module {module_name} imports cognition package")
    return tuple(violations)


def _task2_violations(module_name: str, tree: ast.Module) -> tuple[str, ...]:
    violations: list[str] = []
    allowed = TASK2_IMPORT_GRAPH[module_name]
    ledger_names: set[str] = set()
    session_constructor_calls = _session_constructor_calls(tree)

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
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Name)
            and node.func.id == "getattr"
            and len(node.args) >= 2
            and isinstance(node.args[1], ast.Constant)
            and isinstance(node.args[1].value, str)
        ):
            attribute_name = node.args[1].value
            if attribute_name in {"close", "__enter__", "__exit__"}:
                violations.append(f"{module_name} takes ownership of caller session")
            if attribute_name in FORBIDDEN_LEDGER_LIFECYCLE_CALLS:
                violations.append(
                    f"{module_name} accesses ledger lifecycle {attribute_name}"
                )
        elif isinstance(node, ast.Call) and node in session_constructor_calls:
            violations.append(f"{module_name} constructs VerifiedLedgerSession")
        elif (
            isinstance(node, (ast.With, ast.AsyncWith))
            and module_name in LEDGER_DEPENDENT_TASK2_MODULES
        ):
            violations.append(f"{module_name} takes ownership of caller session")
        elif (
            isinstance(node, ast.Attribute)
            and node.attr in {"close", "__enter__", "__exit__"}
            and not (node.attr == "close" and _approved_cursor_close(tree, node))
        ):
            violations.append(f"{module_name} takes ownership of caller session")
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
        violations.extend(_task1_violations(module_name, _tree(module_name)))

    assert violations == []


def test_architecture_guard_rejects_forbidden_edges_and_nested_session() -> None:
    synthetic = ast.parse(
        "from .ledger import EncryptedLedger, VerifiedLedgerSession\n"
        "from .sensorium import SensoriumStateV1\n"
        "def violate(ledger):\n"
        "    EncryptedLedger(None, None)\n"
        '    getattr(ledger, "verified_session")()\n'
        "    return ledger.verified_session()\n"
    )

    violations = _task2_violations("observation", synthetic)

    assert "observation imports forbidden cognition module ledger" in violations
    assert "observation imports forbidden cognition module sensorium" in violations
    assert "observation imports EncryptedLedger" in violations
    assert "observation references EncryptedLedger" in violations
    assert "observation accesses ledger lifecycle verified_session" in violations
    assert "observation must not import ledger code" in violations


def test_architecture_guard_rejects_package_form_imports() -> None:
    for source, forbidden_module in (
        ("from . import ledger", "ledger"),
        ("from aluclu.cognition import ledger", "ledger"),
        ("from aluclu.cognition import ledger as storage", "ledger"),
        ("from aluclu.cognition import EncryptedLedger as Ledger", "EncryptedLedger"),
        ("import aluclu.cognition", "<cognition package>"),
    ):
        violations = _task2_violations("observation", ast.parse(source))
        assert (
            f"observation imports forbidden cognition module {forbidden_module}"
            in violations
        )

    for source in (
        "from . import observation",
        "from aluclu.cognition import observation",
        "from aluclu.cognition import observation as obs",
        "from ..cognition import observation",
        "from ..cognition.observation import Observation",
    ):
        violations = _task1_violations("ledger", ast.parse(source))
        assert "Task 1 module ledger imports Task 2 module observation" in violations

    for source in ("import aluclu.cognition", "from aluclu import cognition"):
        violations = _task1_violations("ledger", ast.parse(source))
        assert "Task 1 module ledger imports cognition package" in violations


def test_architecture_guard_rejects_session_ownership_mutations() -> None:
    for source in (
        "from .ledger import VerifiedLedgerSession\nVerifiedLedgerSession(None)",
        "from .ledger import VerifiedLedgerSession as VLS\nVLS(None)",
        "from ..cognition.ledger import VerifiedLedgerSession\nVerifiedLedgerSession(None)",
        "from ..cognition.ledger import VerifiedLedgerSession as VLS\nVLS(None)",
        "from .ledger import VerifiedLedgerSession\nmake = VerifiedLedgerSession\nmake(None)",
        "from .ledger import VerifiedLedgerSession as VLS\nmake = VLS\nmake(None)",
        "from .ledger import VerifiedLedgerSession\nmake: object = VerifiedLedgerSession\nmake(None)",
        "from .ledger import VerifiedLedgerSession\nmake = (VerifiedLedgerSession,)[0]\nmake(None)",
        "from .ledger import VerifiedLedgerSession\n(make := VerifiedLedgerSession)(None)",
    ):
        violations = _task2_violations("sensorium", ast.parse(source))
        assert "sensorium constructs VerifiedLedgerSession" in violations

    shadowed_constructor_name = ast.parse(
        "from .ledger import VerifiedLedgerSession\n"
        "def allowed(VerifiedLedgerSession):\n"
        "    VerifiedLedgerSession(None)\n"
    )
    assert "sensorium constructs VerifiedLedgerSession" not in _task2_violations(
        "sensorium", shadowed_constructor_name
    )

    for operation in (
        "session.close()",
        "active = session\n    active.close()",
        "cursor = session\n    cursor.close()",
        "session.__exit__(None, None, None)",
        'getattr(session, "close")()',
        'getattr(session, "__exit__")(None, None, None)',
        "with session:\n        pass",
    ):
        source = (
            "from .ledger import VerifiedLedgerSession\n"
            "def violate(session: VerifiedLedgerSession):\n"
            f"    {operation}\n"
        )
        violations = _task2_violations("sensorium", ast.parse(source))
        assert "sensorium takes ownership of caller session" in violations

    cross_scope = ast.parse(
        "from .ledger import VerifiedLedgerSession\n"
        "def allowed(session: VerifiedLedgerSession):\n"
        "    cursor = session.cursor()\n"
        "    cursor.close()\n"
        "def violate(cursor):\n"
        "    cursor.close()\n"
    )
    assert "sensorium takes ownership of caller session" in _task2_violations(
        "sensorium", cross_scope
    )
