# Random CPU q/v parity v3: terminal evidence

Source commit: `417ecc4f6a67cbe039d99671e9a16823153bac48`.
Scope: real random CPU FP32 integration, not pretrained-host qualification,
ALC-R0 capability acquisition, research accounting, portability, or learning PASS.

## Personally observed terminal result

Same unified exec session83733 returned actual exit0 on the final poll; no restart.
The persisted exit record agrees: pytest_exit_code=0, child_pid=24716,
observed_at=2026-10-06T16:32:40.6639864+03:00. Owned wrapper12800,
launcher24716 and worker19184 were absent at terminal process inspection.

Start receipt records 2026-10-06T16:16:41.6721450+03:00, authoritative Desktop
worktree, existing research Python runtime, tiny optimizer preflight first,
`-x -q`, and process-start `CUDA_VISIBLE_DEVICES=-1`. No source/test/runner
changes were made during this attempt; only trajectory and prospective design
documentation changed. Source hashes below still match the admitted bytes.

Command:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File scripts/alc_r0_full_factor_cpu_tests.ps1 -Suite ParityIntegration -ArtifactStem alc_r0_reference_parity_integration_v3_20261006
```

Artifact stem: `results/alc_r0_reference_parity_integration_v3_20261006`.
Retain `.start.json`, `.stdout.log`, `.stderr.log`, `.exit.log` and `.xml` together.
The start receipt's generic FAKE_PURE_CPU scope label identifies non-host-
acceptance admission, not replacement of the integration's numerical execution.

JUnit: tests2 / failures0 / errors0 / skipped0, total957.294 seconds.
Tiny optimizer isolation case0.022s; full random q/v case949.818s.
Stdout81bytes contains two successful dots and100%; stderr0bytes.
XML SHA256:
`b5d923ddae8e4f3c5cf6243a68712fb03d73dc0260e5893d65d662c2e3450451`.

Admitted bytes reverified after terminal:

| File | SHA256 |
| --- | --- |
| scripts/alc_r0_full_factor_cpu_tests.ps1 | 84e8edc87ab1e81ffbf536c668484b2b2b7af44c1aa8db73127f193afed8e298 |
| tests/test_alc_r0_cpu_optimizer_isolation.py | 93a79d29e7c8f252c01d17462bb0081f84f8d6c57d072a6803486bb1ed410597 |
| tests/test_alc_r0_reference_parity_integration.py | 6014c7695726c459aa77a8c165a1383b0e4b25167db6bf3a0bfdf8767abc7dcd |

## What this execution proves within its test scope

The full integration directly invokes `run_reference_parity_suite`, without
factory/cell/observation/comparator substitution. It verifies the complete
18-case original single schedule, full120 canonical q/v factor names and460800
trainable values, step1 full factor/exp_avg/exp_avg_sq comparison maps, validated
receipt, unchanged frozen base digest/no base gradients, restored CPU RNG and
thread count, and no CUDA init or seeding.

The suite performs actual forward/backward, two pending graphs, both16-microbatch
accumulations, both pre-clip comparisons before either step, clipping and fixed
AdamW updates through the original runtime. This is numerical CPU development
integration PASS on this source commit, not a receipt-only framing test.

The random test host preserves30 attention blocks and width576/q576/v192 but
deliberately uses embedding1024, MLP64 and a rank16 factorized49152-output head;
its31280448 base parameters and fabricated VerifiedHost metadata do not
authenticate SmolLM2 pretrained assets. It loads no pretrained weights,
tokenizer or corpus and evaluates no held-out capability or restart durability.
One successful random seed/attempt is not a resource/portability guarantee.

Earlier v1 HF dispatch rejection and v2 optimizer CUDA-init failure remain
preserved negative results. Neither was numerical hypothesis falsification.
CPU isolation changed environment access, not AdamW, clipping, fixtures,
gradients, comparisons, original matched search grid, or scientific thresholds.

## Separate prospective work and remaining gates

The failure-journal design was prepared during the attempt but is not runtime
code. Final revision3 SHA256
`e19ae5f6f72301aa94ff8a86a908343de39803c5cfb99d2b49eaefd9afd70a4c`
received independent code APPROVE and architecture CLEAR, closing initial draft
BLOCK and later schema WATCH. This is design readiness only. Implementation
requires RED/GREEN/regression and independent final byte review; any modified
real-model integration needs a fresh admitted source-bound attempt.

Actual pinned-host/assets qualification, scientific freeze/evaluator controls,
historical compute-budget accounting/adoption, GPU or actual-host invocation
admission, D/E1/E2/E3 capability evidence, retrieval-off fresh-process durability,
and ALC-R0 learning acceptance remain OPEN. Do not proceed to dependent ALC
product infrastructure or substitute random integration for these gates.
