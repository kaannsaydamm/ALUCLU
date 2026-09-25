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
TASK2_ALLOWED_DIRECT_EXTERNAL_MODULE_MEMBERS = {
    "sensorium": {
        "hashlib": frozenset({"sha256"}),
        "re": frozenset({"compile"}),
        "struct": frozenset({"pack"}),
    },
    "recollection": {
        "hashlib": frozenset({"sha256"}),
        "hmac": frozenset({"compare_digest", "digest", "new"}),
        "re": frozenset({"compile"}),
        "secrets": frozenset({"token_bytes"}),
        "struct": frozenset({"pack"}),
        "weakref": frozenset({"WeakValueDictionary"}),
    },
    "reconsolidation": {
        "hashlib": frozenset({"sha256"}),
        "re": frozenset({"compile"}),
        "struct": frozenset({"pack"}),
    },
}
TASK2_ALLOWED_FROM_EXTERNAL_IMPORTS = {
    "sensorium": {
        "__future__": frozenset({"annotations"}),
        "dataclasses": frozenset({"dataclass"}),
        "enum": frozenset({"Enum"}),
        "typing": frozenset({"cast"}),
    },
    "recollection": {
        "__future__": frozenset({"annotations"}),
        "dataclasses": frozenset({"dataclass", "field"}),
        "enum": frozenset({"Enum"}),
        "functools": frozenset({"cmp_to_key"}),
        "typing": frozenset({"cast", "overload"}),
    },
    "reconsolidation": {
        "__future__": frozenset({"annotations"}),
        "dataclasses": frozenset({"dataclass"}),
        "enum": frozenset({"Enum"}),
        "typing": frozenset({"cast"}),
    },
}
FORBIDDEN_LEDGER_LIFECYCLE_CALLS = frozenset({"unlock", "verified_session"})
FORBIDDEN_NAMESPACE_INTROSPECTION_CALLS = frozenset(
    {
        "globals",
        "locals",
        "vars",
        "eval",
        "exec",
        "compile",
        "__import__",
        "__builtins__",
        "getattr",
        "setattr",
        "delattr",
        "dir",
    }
)
FORBIDDEN_FRAME_NAMESPACE_ATTRIBUTES = frozenset(
    {
        "f_globals",
        "f_locals",
        "f_builtins",
        "gi_frame",
        "cr_frame",
        "ag_frame",
        "tb_frame",
        "_getframe",
        "sys",
        "modules",
    }
)
ALLOWED_RUNTIME_DUNDER_ATTRIBUTES = frozenset(
    {("object", "__new__"), ("object", "__setattr__")}
)


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


def _annotation_nodes(tree: ast.Module) -> set[ast.AST]:
    postponed = any(
        isinstance(node, ast.ImportFrom)
        and node.module == "__future__"
        and any(alias.name == "annotations" for alias in node.names)
        for node in tree.body
    )
    if not postponed:
        return set()
    annotations: set[ast.AST] = set()
    for node in ast.walk(tree):
        roots: list[ast.AST] = []
        if isinstance(node, ast.arg) and node.annotation is not None:
            roots.append(node.annotation)
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            if node.returns is not None:
                roots.append(node.returns)
        elif isinstance(node, ast.AnnAssign):
            roots.append(node.annotation)
        for root in roots:
            annotations.update(ast.walk(root))
    return annotations


def _scope_rebinding_names(scope: ast.AST) -> set[str]:
    rebound: set[str] = set()

    def visit(node: ast.AST) -> None:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            rebound.add(node.name)
            return
        if isinstance(node, ast.Lambda):
            return
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            rebound.update(
                alias.asname or alias.name.split(".", 1)[0] for alias in node.names
            )
        elif isinstance(node, ast.Name) and isinstance(node.ctx, (ast.Store, ast.Del)):
            rebound.add(node.id)
        elif isinstance(node, ast.ExceptHandler) and node.name is not None:
            rebound.add(node.name)
        elif isinstance(node, (ast.MatchAs, ast.MatchStar)) and node.name is not None:
            rebound.add(node.name)
        elif isinstance(node, ast.MatchMapping) and node.rest is not None:
            rebound.add(node.rest)
        for child in ast.iter_child_nodes(node):
            visit(child)

    if isinstance(scope, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
        for statement in scope.body:
            visit(statement)
    elif isinstance(scope, ast.Lambda):
        visit(scope.body)
    return rebound


def _scope_declaration_names(
    scope: ast.AST,
    declaration_type: type[ast.Global] | type[ast.Nonlocal],
) -> set[str]:
    declared: set[str] = set()

    def visit(node: ast.AST) -> None:
        if isinstance(
            node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef, ast.Lambda)
        ):
            return
        if isinstance(node, declaration_type):
            declared.update(node.names)
        for child in ast.iter_child_nodes(node):
            visit(child)

    if isinstance(scope, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
        for statement in scope.body:
            visit(statement)
    elif isinstance(scope, ast.Lambda):
        visit(scope.body)
    return declared


def _parameter_shadows_reference(
    reference: ast.AST,
    alias: str,
    parents: dict[ast.AST, ast.AST],
) -> bool:
    child = reference
    parent = parents.get(child)
    crossed_non_class_scope = False
    while parent is not None:
        if isinstance(parent, (ast.FunctionDef, ast.AsyncFunctionDef)):
            if child in parent.body:
                if alias in _scope_declaration_names(parent, ast.Global):
                    return False
                if alias not in _scope_declaration_names(parent, ast.Nonlocal):
                    if alias in _scope_rebinding_names(parent):
                        return False
                    if alias in _scope_parameters(parent):
                        return True
                crossed_non_class_scope = True
        elif isinstance(parent, ast.Lambda):
            if child is parent.body:
                if alias in _scope_rebinding_names(parent):
                    return False
                if alias in _scope_parameters(parent):
                    return True
                crossed_non_class_scope = True
        elif isinstance(
            parent, (ast.ListComp, ast.SetComp, ast.DictComp, ast.GeneratorExp)
        ):
            crossed_non_class_scope = True
        elif isinstance(parent, ast.ClassDef) and child in parent.body:
            if not crossed_non_class_scope:
                if alias in _scope_declaration_names(parent, ast.Global):
                    return False
                if alias not in _scope_declaration_names(parent, ast.Nonlocal):
                    if alias in _scope_rebinding_names(parent):
                        return False
            crossed_non_class_scope = True
        child = parent
        parent = parents.get(child)
    return False


def _target_bound_names(target: ast.AST) -> set[str]:
    if isinstance(target, ast.Name):
        return {target.id}
    if isinstance(target, (ast.Tuple, ast.List)):
        return {
            name for element in target.elts for name in _target_bound_names(element)
        }
    if isinstance(target, ast.Starred):
        return _target_bound_names(target.value)
    return set()


def _contains_node(root: ast.AST, candidate: ast.AST) -> bool:
    return any(node is candidate for node in ast.walk(root))


def _comprehension_shadows_reference(
    reference: ast.AST,
    alias: str,
    parents: dict[ast.AST, ast.AST],
) -> bool:
    comprehension_types = (
        ast.ListComp,
        ast.SetComp,
        ast.DictComp,
        ast.GeneratorExp,
    )
    ancestor = parents.get(reference)
    while ancestor is not None:
        if isinstance(ancestor, comprehension_types):
            # CPython evaluates only the first iterable in the enclosing scope.
            # Every other expression runs in the implicit comprehension function,
            # where every generator target is local even before its assignment.
            first_iterable = ancestor.generators[0].iter
            comprehension_locals = {
                name
                for generator in ancestor.generators
                for name in _target_bound_names(generator.target)
            }
            if (
                not _contains_node(first_iterable, reference)
                and alias in comprehension_locals
            ):
                return True
        ancestor = parents.get(ancestor)
    return False


def _is_forbidden_runtime_attribute(node: ast.Attribute) -> bool:
    if node.attr in FORBIDDEN_FRAME_NAMESPACE_ATTRIBUTES:
        return True
    if not (node.attr.startswith("__") and node.attr.endswith("__")):
        return False
    return not (
        isinstance(node.value, ast.Name)
        and (node.value.id, node.attr) in ALLOWED_RUNTIME_DUNDER_ATTRIBUTES
    )


def _is_forbidden_dynamic_attribute(attribute_name: str) -> bool:
    return attribute_name in FORBIDDEN_FRAME_NAMESPACE_ATTRIBUTES or (
        attribute_name.startswith("__") and attribute_name.endswith("__")
    )


def _is_type_call(node: ast.AST) -> bool:
    return (
        isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id == "type"
        and len(node.args) == 1
        and not node.keywords
    )


def _is_explicit_type_check(
    reference: ast.AST,
    parents: dict[ast.AST, ast.AST],
) -> bool:
    parent = parents.get(reference)
    if isinstance(parent, ast.Compare):
        operands = (parent.left, *parent.comparators)
        for index, operand in enumerate(operands):
            if operand is not reference:
                continue
            if (
                index > 0
                and isinstance(parent.ops[index - 1], (ast.Is, ast.IsNot))
                and _is_type_call(operands[index - 1])
            ):
                return True
            if (
                index < len(parent.ops)
                and isinstance(parent.ops[index], (ast.Is, ast.IsNot))
                and _is_type_call(operands[index + 1])
            ):
                return True

    child = reference
    while parent is not None and isinstance(parent, (ast.Tuple, ast.List, ast.Set)):
        child = parent
        parent = parents.get(child)
    return bool(
        isinstance(parent, ast.Call)
        and isinstance(parent.func, ast.Name)
        and parent.func.id in {"isinstance", "issubclass"}
        and len(parent.args) >= 2
        and child is parent.args[1]
    )


def _session_constructor_runtime_uses(tree: ast.Module) -> set[ast.AST]:
    """Reject moving the session constructor into any runtime data flow.

    Task 2 may name the caller-owned session type in annotations and exact type
    checks.  Every other runtime load is forbidden.  This fail-closed rule also
    covers attributes, subscripts, containers, closures, defaults, and helper
    returns without attempting an incomplete whole-Python taint analysis.
    """

    parents = {
        child: parent
        for parent in ast.walk(tree)
        for child in ast.iter_child_nodes(parent)
    }
    annotations = _annotation_nodes(tree)
    aliases = {
        alias.asname or alias.name
        for node in ast.walk(tree)
        if isinstance(node, ast.ImportFrom)
        and (node.level, node.module)
        in {
            (1, "ledger"),
            (2, "cognition.ledger"),
            (0, "aluclu.cognition.ledger"),
        }
        for alias in node.names
        if alias.name == "VerifiedLedgerSession"
    }
    uses: set[ast.AST] = set()
    for node in ast.walk(tree):
        if node in annotations or _is_explicit_type_check(node, parents):
            continue
        if (
            isinstance(node, ast.Name)
            and isinstance(node.ctx, ast.Load)
            and node.id in aliases
            and not _comprehension_shadows_reference(node, node.id, parents)
            and not _parameter_shadows_reference(node, node.id, parents)
        ):
            uses.add(node)
        elif (
            isinstance(node, ast.Attribute)
            and isinstance(node.ctx, ast.Load)
            and node.attr == "VerifiedLedgerSession"
        ):
            uses.add(node)
        elif (
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Name)
            and node.func.id == "getattr"
            and len(node.args) >= 2
            and isinstance(node.args[1], ast.Constant)
            and node.args[1].value == "VerifiedLedgerSession"
        ):
            uses.add(node)
    return uses


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
    session_constructor_runtime_uses = _session_constructor_runtime_uses(tree)
    allowed_direct_modules = TASK2_ALLOWED_DIRECT_EXTERNAL_MODULE_MEMBERS.get(
        module_name
    )
    allowed_from_imports = TASK2_ALLOWED_FROM_EXTERNAL_IMPORTS.get(module_name)
    parents = {
        child: parent
        for parent in ast.walk(tree)
        for child in ast.iter_child_nodes(parent)
    }

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
        elif module_name in LEDGER_DEPENDENT_TASK2_MODULES and (
            (
                isinstance(node, ast.Import)
                and any(imported.name == "builtins" for imported in node.names)
            )
            or (isinstance(node, ast.ImportFrom) and node.module == "builtins")
        ):
            # Task 2 modules do not need the reflective builtins namespace. Banning
            # the import itself keeps this architecture boundary fail-closed for
            # aliases, getattr(), __dict__, and future dynamic attribute forms.
            violations.append(f"{module_name} uses namespace introspection")
        elif isinstance(node, ast.Import) and allowed_direct_modules is not None:
            for imported in node.names:
                root = imported.name.partition(".")[0]
                if (
                    imported.name != root
                    or root not in allowed_direct_modules
                    or imported.asname is not None
                ):
                    violations.append(
                        f"{module_name} imports forbidden external module {root}"
                    )
        elif (
            isinstance(node, ast.ImportFrom)
            and allowed_from_imports is not None
            and node.level == 0
            and node.module is not None
        ):
            allowed_names = allowed_from_imports.get(node.module)
            for imported in node.names:
                if allowed_names is None or imported.name not in allowed_names:
                    violations.append(
                        f"{module_name} imports forbidden external member "
                        f"{node.module}.{imported.name}"
                    )
        elif (
            module_name in LEDGER_DEPENDENT_TASK2_MODULES
            and allowed_direct_modules is not None
            and isinstance(node, ast.Name)
            and isinstance(node.ctx, ast.Load)
            and node.id in allowed_direct_modules
        ):
            parent = parents.get(node)
            if not (
                isinstance(parent, ast.Attribute)
                and parent.value is node
                and parent.attr in allowed_direct_modules[node.id]
            ):
                violations.append(
                    f"{module_name} uses forbidden external member {node.id}"
                )
        elif (
            module_name in LEDGER_DEPENDENT_TASK2_MODULES
            and isinstance(node, ast.Name)
            and isinstance(node.ctx, ast.Load)
            and node.id in FORBIDDEN_NAMESPACE_INTROSPECTION_CALLS
        ):
            violations.append(f"{module_name} uses namespace introspection")
        elif (
            module_name in LEDGER_DEPENDENT_TASK2_MODULES
            and isinstance(node, ast.Constant)
            and node.value == "__builtins__"
        ):
            violations.append(f"{module_name} uses namespace introspection")
        elif (
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Name)
            and node.func.id == "getattr"
            and len(node.args) >= 2
            and isinstance(node.args[1], ast.Constant)
            and isinstance(node.args[1].value, str)
        ):
            attribute_name = node.args[1].value
            if (
                module_name in LEDGER_DEPENDENT_TASK2_MODULES
                and _is_forbidden_dynamic_attribute(attribute_name)
            ):
                violations.append(f"{module_name} uses namespace introspection")
            if attribute_name in {"close", "__enter__", "__exit__"}:
                violations.append(f"{module_name} takes ownership of caller session")
            if attribute_name in FORBIDDEN_LEDGER_LIFECYCLE_CALLS:
                violations.append(
                    f"{module_name} accesses ledger lifecycle {attribute_name}"
                )
        elif node in session_constructor_runtime_uses:
            violations.append(f"{module_name} constructs VerifiedLedgerSession")
        elif (
            isinstance(node, (ast.With, ast.AsyncWith))
            and module_name in LEDGER_DEPENDENT_TASK2_MODULES
        ):
            violations.append(f"{module_name} takes ownership of caller session")
        elif (
            module_name in LEDGER_DEPENDENT_TASK2_MODULES
            and isinstance(node, ast.Attribute)
            and _is_forbidden_runtime_attribute(node)
        ):
            violations.append(f"{module_name} uses namespace introspection")
            if node.attr in {"close", "__enter__", "__exit__"}:
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
        (
            "from .ledger import VerifiedLedgerSession\n"
            "class Box:\n"
            "    pass\n"
            "box = Box()\n"
            "box.make = VerifiedLedgerSession\n"
            "box.make(None)\n"
        ),
        (
            "from .ledger import VerifiedLedgerSession\n"
            "box = {}\n"
            "box['make'] = VerifiedLedgerSession\n"
            "box['make'](None)\n"
        ),
        (
            "from .ledger import VerifiedLedgerSession\n"
            "def factory():\n"
            "    return VerifiedLedgerSession\n"
            "factory()(None)\n"
        ),
        (
            "from .ledger import VerifiedLedgerSession\n"
            "box = []\n"
            "box.append(VerifiedLedgerSession)\n"
            "box[0](None)\n"
        ),
        (
            "from .ledger import VerifiedLedgerSession\n"
            "def violate(factory=VerifiedLedgerSession):\n"
            "    factory(None)\n"
        ),
        (
            "from .ledger import VerifiedLedgerSession\n"
            "def violate():\n"
            "    return lambda: VerifiedLedgerSession(None)\n"
        ),
        (
            "from .ledger import VerifiedLedgerSession\n"
            "def violate(session: VerifiedLedgerSession(None)):\n"
            "    return session\n"
        ),
        (
            "from .ledger import VerifiedLedgerSession as VLS\n"
            "def violate(VLS):\n"
            "    from .ledger import VerifiedLedgerSession as VLS\n"
            "    VLS(None)\n"
        ),
        (
            "from .ledger import VerifiedLedgerSession as VLS\n"
            "def outer(VLS):\n"
            "    def violate():\n"
            "        from .ledger import VerifiedLedgerSession as VLS\n"
            "        VLS(None)\n"
            "    return violate\n"
        ),
        (
            "from .ledger import VerifiedLedgerSession as VLS\n"
            "def outer(VLS):\n"
            "    def violate():\n"
            "        global VLS\n"
            "        VLS(None)\n"
            "    return violate\n"
        ),
        (
            "from .ledger import VerifiedLedgerSession as VLS\n"
            "def outer(VLS):\n"
            "    class Violate:\n"
            "        global VLS\n"
            "        made = VLS(None)\n"
            "    return Violate\n"
        ),
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

    allowed_type_references = ast.parse(
        "from __future__ import annotations\n"
        "from .ledger import VerifiedLedgerSession as VLS\n"
        "def allowed(session: VLS) -> VLS:\n"
        "    if type(session) is not VLS:\n"
        "        raise TypeError\n"
        "    if not isinstance(session, VLS):\n"
        "        raise TypeError\n"
        "    return session\n"
    )
    assert "sensorium constructs VerifiedLedgerSession" not in _task2_violations(
        "sensorium", allowed_type_references
    )

    allowed_lexical_shadows = (
        (
            "from .ledger import VerifiedLedgerSession as VLS\n"
            "def outer(VLS):\n"
            "    def allowed():\n"
            "        nonlocal VLS\n"
            "        return VLS(None)\n"
            "    return allowed\n"
        ),
        (
            "from .ledger import VerifiedLedgerSession as VLS\n"
            "def outer(VLS):\n"
            "    class C:\n"
            "        VLS = int\n"
            "        def allowed(self):\n"
            "            return VLS(None)\n"
            "    return C\n"
        ),
        (
            "from .ledger import VerifiedLedgerSession as VLS\n"
            "def allowed(VLS):\n"
            "    return [VLS(None) for VLS in ()]\n"
        ),
        (
            "from .ledger import VerifiedLedgerSession as VLS\n"
            "def allowed():\n"
            "    return [[x for x in (VLS,)] for VLS in ()]\n"
        ),
        (
            "from .ledger import VerifiedLedgerSession as VLS\n"
            "def allowed():\n"
            "    return [[x for x in VLS(None)] for VLS in ()]\n"
        ),
        (
            "from .ledger import VerifiedLedgerSession as VLS\n"
            "def allowed():\n"
            "    return [[VLS for x in ()] for VLS in ()]\n"
        ),
        (
            "from .ledger import VerifiedLedgerSession as VLS\n"
            "def allowed():\n"
            "    return [{VLS for x in ()} for VLS in ()]\n"
        ),
        (
            "from .ledger import VerifiedLedgerSession as VLS\n"
            "def allowed():\n"
            "    return [{x: VLS for x in ()} for VLS in ()]\n"
        ),
        (
            "from .ledger import VerifiedLedgerSession as VLS\n"
            "def allowed():\n"
            "    return [(VLS for x in ()) for VLS in ()]\n"
        ),
        (
            "from .ledger import VerifiedLedgerSession as VLS\n"
            "def allowed():\n"
            "    return [x for x in (1,) for VLS in VLS(None)]\n"
        ),
        (
            "from .ledger import VerifiedLedgerSession as VLS\n"
            "def allowed():\n"
            "    return {x for x in (1,) for VLS in VLS(None)}\n"
        ),
        (
            "from .ledger import VerifiedLedgerSession as VLS\n"
            "def allowed():\n"
            "    return {x: x for x in (1,) for VLS in VLS(None)}\n"
        ),
        (
            "from .ledger import VerifiedLedgerSession as VLS\n"
            "def allowed():\n"
            "    return (x for x in (1,) for VLS in VLS(None))\n"
        ),
    )
    for source in allowed_lexical_shadows:
        assert "sensorium constructs VerifiedLedgerSession" not in _task2_violations(
            "sensorium", ast.parse(source)
        )

    unsafe_comprehension = ast.parse(
        "from .ledger import VerifiedLedgerSession as VLS\n"
        "def violate():\n"
        "    return [VLS(None) for _ in ()]\n"
    )
    assert "sensorium constructs VerifiedLedgerSession" in _task2_violations(
        "sensorium", unsafe_comprehension
    )

    unsafe_nested_comprehension = ast.parse(
        "from .ledger import VerifiedLedgerSession as VLS\n"
        "def violate():\n"
        "    return [[VLS(None) for x in ()] for y in ()]\n"
    )
    assert "sensorium constructs VerifiedLedgerSession" in _task2_violations(
        "sensorium", unsafe_nested_comprehension
    )

    for source in (
        (
            "from .ledger import VerifiedLedgerSession as VLS\n"
            "def violate():\n"
            "    return [x for x in (1,) for y in VLS(None)]\n"
        ),
        (
            "from .ledger import VerifiedLedgerSession as VLS\n"
            "def violate():\n"
            "    return {x for x in (1,) for y in VLS(None)}\n"
        ),
        (
            "from .ledger import VerifiedLedgerSession as VLS\n"
            "def violate():\n"
            "    return {x: x for x in (1,) for y in VLS(None)}\n"
        ),
        (
            "from .ledger import VerifiedLedgerSession as VLS\n"
            "def violate():\n"
            "    return (x for x in (1,) for y in VLS(None))\n"
        ),
    ):
        assert "sensorium constructs VerifiedLedgerSession" in _task2_violations(
            "sensorium", ast.parse(source)
        )

    for source in (
        (
            "from .ledger import VerifiedLedgerSession as VLS\n"
            "def violate():\n"
            "    return globals()['VLS'](None)\n"
        ),
        (
            "from .ledger import VerifiedLedgerSession as VLS\n"
            "def outer(VLS):\n"
            "    def violate(factory=globals()['VLS']):\n"
            "        return factory(None)\n"
            "    return violate\n"
        ),
        (
            "from .ledger import VerifiedLedgerSession as VLS\n"
            "def violate():\n"
            "    return locals().__getitem__('VLS')(None)\n"
        ),
        (
            "from .ledger import VerifiedLedgerSession as VLS\n"
            "def violate():\n"
            "    namespace = globals\n"
            "    return namespace()['VLS'](None)\n"
        ),
        (
            "from .ledger import VerifiedLedgerSession as VLS\n"
            "import builtins\n"
            "def violate():\n"
            "    return builtins.globals()['VLS'](None)\n"
        ),
        (
            "from .ledger import VerifiedLedgerSession as VLS\n"
            "import builtins\n"
            "def violate():\n"
            "    return builtins.__dict__['globals']()['VLS'](None)\n"
        ),
        (
            "from .ledger import VerifiedLedgerSession as VLS\n"
            "import builtins\n"
            "def violate():\n"
            "    return getattr(builtins, 'globals')()['VLS'](None)\n"
        ),
        (
            "from .ledger import VerifiedLedgerSession as VLS\n"
            "from builtins import globals as namespace\n"
            "def violate():\n"
            "    return namespace()['VLS'](None)\n"
        ),
        (
            "from .ledger import VerifiedLedgerSession as VLS\n"
            "def violate():\n"
            "    return __builtins__['globals']()['VLS'](None)\n"
        ),
        (
            "from .ledger import VerifiedLedgerSession as VLS\n"
            "def violate():\n"
            "    return (lambda: None).__globals__['VLS'](None)\n"
        ),
        (
            "from .ledger import VerifiedLedgerSession as VLS\n"
            "def violate():\n"
            "    return getattr(lambda: None, '__globals__')['VLS'](None)\n"
        ),
        (
            "from .ledger import VerifiedLedgerSession as VLS\n"
            "def violate():\n"
            "    attribute = '__' + 'globals__'\n"
            "    return getattr(lambda: None, attribute)['VLS'](None)\n"
        ),
        (
            "from .ledger import VerifiedLedgerSession as VLS\n"
            "def violate():\n"
            "    namespace = (lambda: None).__globals__\n"
            "    builtins_value = namespace['__builtins__']\n"
            "    globals_fn = (\n"
            "        builtins_value['globals']\n"
            "        if isinstance(builtins_value, dict)\n"
            "        else builtins_value.globals\n"
            "    )\n"
            "    return globals_fn()['VLS'](None)\n"
        ),
    ):
        assert "sensorium uses namespace introspection" in _task2_violations(
            "sensorium", ast.parse(source)
        )

    for source, forbidden_root in (
        (
            "from .ledger import VerifiedLedgerSession as VLS\n"
            "import importlib\n"
            "def violate():\n"
            "    return importlib.import_module('builtins').globals()['VLS'](None)\n",
            "importlib",
        ),
        (
            "from .ledger import VerifiedLedgerSession as VLS\n"
            "import sys\n"
            "def violate():\n"
            "    return sys.modules['builtins'].globals()['VLS'](None)\n",
            "sys",
        ),
        (
            "from .ledger import VerifiedLedgerSession as VLS\n"
            "import sys\n"
            "def violate():\n"
            "    return sys.modules[__name__].VLS(None)\n",
            "sys",
        ),
    ):
        assert (
            f"sensorium imports forbidden external module {forbidden_root}"
            in _task2_violations("sensorium", ast.parse(source))
        )

    for module_name in sorted(LEDGER_DEPENDENT_TASK2_MODULES):
        for external_module in ("typing", "dataclasses", "enum"):
            source = (
                f"from {external_module} import sys as approved\n"
                "from .ledger import VerifiedLedgerSession as VLS\n"
                "def violate():\n"
                "    return approved.modules[__name__].VLS(None)\n"
            )
            assert (
                f"{module_name} imports forbidden external member "
                f"{external_module}.sys"
                in _task2_violations(module_name, ast.parse(source))
            )

        direct_module_gateway = ast.parse(
            "from .ledger import VerifiedLedgerSession as VLS\n"
            "import typing\n"
            "def violate():\n"
            "    return typing.sys.modules[__name__].VLS(None)\n"
        )
        assert (
            f"{module_name} imports forbidden external module typing"
            in _task2_violations(module_name, direct_module_gateway)
        )

    recollection_module_gateway = ast.parse(
        "from .ledger import VerifiedLedgerSession as VLS\n"
        "import weakref\n"
        "def violate():\n"
        "    return weakref.sys.modules[__name__].VLS(None)\n"
    )
    assert "recollection uses forbidden external member weakref" in _task2_violations(
        "recollection", recollection_module_gateway
    )

    frame_builtins_gateway = ast.parse(
        "import dataclasses\n"
        "from .ledger import VerifiedLedgerSession as VLS\n"
        "def violate():\n"
        "    return (\n"
        "        dataclasses.sys._getframe().f_builtins['globals']()['VLS'](None)\n"
        "    )\n"
    )
    assert "sensorium uses namespace introspection" in _task2_violations(
        "sensorium", frame_builtins_gateway
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
