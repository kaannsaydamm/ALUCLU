# Accumulation journal runtime evidence

Status: implemented development checkpoint; focused and relevant CPU regressions
verified. Final source-commit-bound random-CPU numerical integration verified PASS;
independent terminal synthesis APPROVE for this bounded development checkpoint. This is
not pretrained-host qualification, training authorization, or ALC-R0 acceptance.

The prospective failure-journal design document is preserved as historical design
evidence. Its original DRAFT header describes its preparation time, not current
implementation status. This record and TRAJECTORY.md describe the later runtime.

## Scope and invariant

A private attempt owner transports fixed primitive entry/return metadata from
reference suite through cell and accumulation pair into observation and step.
Snapshots distinguish actual returned inner operations from enclosing returns.
The existing 16-microbatch loss/16 calculation, serial backward/capture order,
both full pre-clip comparisons before either optimizer step, norm-1 clipping,
fixed AdamW configuration and step-1 full-state comparison remain unchanged.
Successful pair, cell and reference receipt schemas are unchanged.

Errors and interruptions preserve the original cause, independently bounded
journal/cleanup fault indicators, and independently valid completed/pending
evidence. Cleanup excludes caller-base parameter identities, including rejected
factor aliases. Shared exact-field sanitization occurs before caching a returned
cell prefix and again during late failure emission. Final recapture after the
last outer state check rejects detected malformed framing before success return.

This is cooperative instrumentation, not authenticated proof of execution.
Cleanup is best-effort, not optimizer rollback. Payload bounds do not bound
Python traceback retention; callers must discard live exceptions/wrappers after
extracting bounded diagnostics. No durable process-kill journal is claimed.

## Verified terminal evidence

All attempts were serial, admitted independently, launched in the existing pinned
CPU research runtime, and personally observed terminal on their original tool
handles. No relevant source/test edits occurred while a worker was live. Launch
records retain immediate physical/virtual headroom and process-start CUDA mask.
Each stem has start JSON, stdout, stderr, exit receipt and JUnit XML.

| Final attempt stem in `results/` | Tests/failures/errors/skips | Time seconds | Exit | XML SHA-256 |
|---|---|---:|---:|---|
| `alc_r0_accumulation_journal_late_green_20261006` | 124/0/0/0 | 40.950 | 0 | `f25e5c62412f7db1c2db78fdc630f8c87c9569affdcfdd428fc9888f2894ecb1` |
| `alc_r0_accumulation_journal_regression_v2_20261006` | 495/0/0/0 | 69.240 | 0 | `5124d0627688034f05cf55a2f61331e3f27d76aec114bf9f6ffff3faff24067c` |
| `alc_r0_accumulation_journal_existing_regression_20261006` | 325/0/0/0 | 37.390 | 0 | `c3ecc813ab9d089fb6007283427eb3b27837ba9be71a13d0ee4e01d58a62eb21` |

These selections overlap. Their counts must not be added as unique-test coverage.
All final stdout logs reached 100%; all final stderr logs were empty.

## Negative results preserved

Initial broad regression: 483/16/0/0, exit 1, 59.343 seconds. Fifteen failures
were an existing stub-cell private-keyword incompatibility; one expected a raw
RuntimeError rather than the new typed wrapper. Test adaptation retained all
existing behavioral checks and added exact primary-cause and progress assertions.
The adapted 483-case run passed before further independent findings.

Independent whole review found two concrete defects, reproduced before repair:

1. Late failure payload could retain an extra tensor/object field attached to an
   exact non-slotted comparison row. RED: 120/8/0/0, exit 1, 34.971 seconds.
2. Detected malformed returned framing could still return a success receipt.
   RED: 122/2/0/0, exit 1, 45.843 seconds. Prior 120 cases passed, including the
   repaired late failure cases.

Final 124 cases cover both before-cache and after-cache contamination windows for
ordinary/interruption late failures and normal-path fail-closed rejection. The
reference framing tests deliberately stub cell computation; actual tiny CPU pair
and cell execution is covered separately. Neither is pretrained-host evidence.
All RED artifacts and prior attempts remain first-class records in the trajectory.

## Reviewed source identities

| File | SHA-256 |
|---|---|
| `checkpoint_accumulation_progress.py` | `812e891fea7fa5c0dcb32550988364dd9e5d0b27889d0548603f77cf283d75a9` |
| `checkpoint_accumulation_pair.py` | `a968fff30f033382deaf151f6de97e57b6fd7e8aec45f91f97697898fded2c4b` |
| `checkpoint_observation.py` | `448a43a05604748c2067fc73b6da51727e52ba0546f255ee2b13add080756afd` |
| `checkpoint_accumulation_step.py` | `d153352c2c38023d164cede16f03ab54c4c355fe0a8aa05d68cf05eb0ead517d` |
| `checkpoint_parity_cell.py` | `d42abe347fc5255a1ce5de7cecc16f9cfcd9ac3e9457556ec7e82635e79f591a` |
| `reference_parity_suite.py` | `9c750045abecd22915a0edfac152975941c353288ab46159de2141eb1636bce5` |
| `test_alc_r0_accumulation_journal_integration.py` | `8af90a5e47d12c48a5cb7c047124ac8b29f1e88f8b13d331790d70bf5e735cf5` |
| `test_alc_r0_accumulation_pair.py` | `3a166b8d31535f3ca86598dc3d6f3c26d6d39401c0387e5f86a481f0a58a938f` |
| `test_alc_r0_reference_parity_suite.py` | `179731e13660ca0a6ad28c00bfc9b14575b76e543747a92260b61d5069f30017` |
| `alc_r0_full_factor_cpu_tests.ps1` | `acd2cb6a583478ad36a759f14210868d1206da6709b6aa330cd6bff7ae388095` |

## Open gates

Independent GPT-6.1 Sol code/spec/security terminal synthesis returned APPROVE;
the separate architecture terminal synthesis returned CLEAR for this scoped
development checkpoint, with residual provenance and operational cautions below.
Both independently checked persisted terminal artifacts and source identities;
the parent separately observed the original launcher exit. Deterministic combined
verdict: APPROVE for this bounded checkpoint, not whole-branch/program acceptance.
Both reproduced framing blockers were resolved; no unresolved scoped BLOCK remains.

Source checkpoint c683f4e71348e38a718070ab3fb68369c2672062 was preserved and pushed.
Both independent lanes admitted one fresh random-CPU numerical integration bound
to that source. Its original launcher session8889 personally returned exit0
(3198f7); persisted exit0 and child26716 observed at2026-10-06T19:03:33.8062920+03.
Stem `alc_r0_reference_parity_journal_v4_c683f4e_20261006`: JUnit2/0/0/0,
1400.911seconds; tiny CPU isolation0.639s, full random q/v integration1386.458s.
Stdout100%, stderr empty, no remaining matching Python worker. XML SHA-256
`86695c84dc644520842ce3910e06ee1f426e9757b8605802f3b5814c5b3454c7`.
This supplies current-source numerical regression evidence, not a speed claim.
Earlier v3 evidence belongs only to its prior source, not this instrumentation.
No test thresholds, seeds, schedule, fixtures or runner were changed during LIVE.
Residual limits: cooperative in-memory instrumentation is not authenticated
execution proof, process-kill durability or bounded traceback retention. Cleanup
is best-effort, not optimizer rollback. Launch headroom is not a reservation.
One random fixture seed does not qualify all accelerator/backend configurations.
Next: preserve terminal artifacts and synthesis, then resume the still-open
pretrained-host and scientific readiness gates without promoting this fixture.
Actual pinned pretrained-host execution, scientific freeze/accounting, capability
controls, retrieval-off fresh-process durability and R0 learning acceptance remain
separate OPEN gates. Dependent ALC product infrastructure must not leapfrog them.
