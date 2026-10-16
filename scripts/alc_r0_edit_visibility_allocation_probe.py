"""Supplementary helper allocation probe; no package/model/data imports."""

import importlib.util
import json
import sys
import tracemalloc

module_path = sys.argv[1]
spec = importlib.util.spec_from_file_location(
    "edit_visibility_probe_module", module_path
)
module = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = module
spec.loader.exec_module(module)

# Caller-owned inputs and enormous budget are constructed before tracing.
giant_budget = 1 << 2_000_000
cases = (
    ("giant-budget", (1, 2), (2, 1), (giant_budget,)),
    (
        "maximum-row-width",
        (),
        (1,) * module.MAX_ENDPOINT_TOKENS,
        (1, 2, 4, 8192, giant_budget),
    ),
)
measurements = []
for name, first, second, budgets in cases:
    tracemalloc.start()
    result = module.audit_edit_token_visibility(first, second, code_budgets=budgets)
    _, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    assert result.status == "exact-non-authorizing"
    assert peak <= result.estimated_scratch_bytes
    if name == "giant-budget":
        assert result.edit_distance == 2
        assert result.budgets[0].total_min == result.budgets[0].total_max == 2
    else:
        assert result.edit_distance == module.MAX_ENDPOINT_TOKENS
        assert (
            result.budgets[-1].total_min
            == result.budgets[-1].total_max
            == module.MAX_ENDPOINT_TOKENS
        )
    measurements.append(
        {
            "case": name,
            "first_tokens": len(first),
            "second_tokens": len(second),
            "budget_count": len(budgets),
            "peak_traced_bytes": peak,
            "estimated_scratch_bytes": result.estimated_scratch_bytes,
            "peak_within_estimate": True,
        }
    )
print(
    json.dumps(
        {
            "status": "supplementary-helper-allocation-probe",
            "training_authority": False,
            "held_out_data_present": False,
            "package_integration_test": False,
            "python_version": sys.version.split()[0],
            "measurements": measurements,
        },
        sort_keys=True,
        separators=(",", ":"),
    )
)
