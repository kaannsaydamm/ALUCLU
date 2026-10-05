# Checkpoint177: early CPU observations and historical measurement coverage

Parent801a6dc2d14cd6c2c4279d3fa47e38c78988f2df,2026-10-05. Bounded read-only
reconstruction; no old command, model, tokenizer, corpus or GPU job executed.
Private primary-session path/privacy boundary is recorded in checkpoint174.
No scientific thresholds, grid, original plan or accounting policy changed.

## Earlier bare CPU observations

Exact original event_msg/item_completed records corroborate these three commands:

| CommandExecution id | Completion event UTC | Tool handle | Exit | Command seconds | Payload started_at_ms | Payload completed_at_ms |
| --- | --- | --- | ---: | ---: | ---: | ---: |
| exec-9533e824-6ccb-4a49-ab12-a3981d2e32ba | 2026-09-20T17:44:45.189Z | 94342 | 0 | 34.355830900 | 1789926250831 | 1789926285186 |
| exec-8c5f0d26-a3c0-424d-b346-56463bed5946 | 2026-09-20T17:45:20.547Z | 36088 | 0 | 17.521254000 | 1789926303013 | 1789926320547 |
| exec-3b7d0cbe-9926-460d-9d2d-29240815bf46 | 2026-09-20T17:45:46.817Z | 35611 | 0 | 15.778131500 | 1789926331038 | 1789926346816 |

All statuses completed. The first command's output reports LlamaForCausalLM,
134515008 parameters, trainable0, trainingFalse, torch.bfloat16 and devicecpu.
The two other commands independently load the same pinned local snapshot and
encode its state:273 entries/272 alias groups/325706271 encoded bytes, base root
ce7e8dd6a97ac4cc56bf4f1e38625817386e27af58f1ed63377741f7f2aab1ba,
alias root8efcc3120c19a1a0784811d4ae95d327849ad8e7bd9176d45c3a6b9b7f067a84.
The inline commands use mutable src through PYTHONPATH, not an immutable export
or a source/runtime attestation. Earlier than Sep21 controls is not proof of the
first development job, exhaustive coverage or the original45day-clock authority.

SHA256 identifies UTF-8 bytes of decoded aggregated_output, preserving CR/LF:

| CommandExecution id | Output UTF-8 bytes | Output SHA256 |
| --- | ---: | --- |
| exec-9533e824-6ccb-4a49-ab12-a3981d2e32ba | 728 | 2019a030eaca5b94462bfbcbc3f9de67f2e793d1ac9b4b4cde1003c357fd8a83 |
| exec-8c5f0d26-a3c0-424d-b346-56463bed5946 | 412 | a7eca93c89504efebbb033046d0d60569be70411e823f7168cbc44f46f90aec9 |
| exec-3b7d0cbe-9926-460d-9d2d-29240815bf46 | 412 | 0d956a6405b7e98b60e8a557ff31c5a0067baabc1c76425f076b78ec907a8865 |

Tool handles/timestamps are not authenticated OS PIDs/process clocks. Command
duration sum67.655216400seconds is wall time, not GPU consumption. No private
session export or retrospective command execution is required for these joins.

## Partial CUDA phase measurements exist

The twelve selected stdout receipts are not devoid of measurements. Historical
context_gradient_probe atd4fb2d1 and currentHEAD share Git blob
962aa552c142bf4e686a8777835838da7e7a869c; its forward/backward timer is explicitly
bracketed by CUDA synchronize calls. Synthetic update source atc4f147c has blob
d88c16be43590e18fdf49fc6f4116d1074cb3b16 and at3966c90/currentHEAD has blob
772f9468f042e9249e59fe4caa2a825c3b3a7f1a. Both bracket optimizer_update_loop
with explicit CUDA synchronization and perf_counter_ns. These measure phase wall
intervals covering GPU work plus CPU/Python overhead, not GPU-active occupancy.
Remount timers lack that explicit bracketing; scalar score conversion must not
be silently upgraded to a full job-resource measurement.

| Receipt under results/ | Timing field | Nanoseconds |
| --- | --- | ---: |
| alc_r0_context_gradient_probe_d4fb2d1_20260929_512-capsule.stdout.log | elapsed_forward_backward_ns | 1633938500 |
| alc_r0_context_gradient_probe_d4fb2d1_20260929_512-q_lora.stdout.log | elapsed_forward_backward_ns | 764937200 |
| alc_r0_context_gradient_probe_d4fb2d1_20260929_1024-capsule.stdout.log | elapsed_forward_backward_ns | 1288677100 |
| alc_r0_context_gradient_probe_d4fb2d1_20260929_1024-q_lora.stdout.log | elapsed_forward_backward_ns | 708949900 |
| alc_r0_context_gradient_probe_d4fb2d1_20260929_2048-capsule.stdout.log | elapsed_forward_backward_ns | 1477696100 |
| alc_r0_context_gradient_probe_d4fb2d1_20260929_2048-q_lora.stdout.log | elapsed_forward_backward_ns | 3034961500 |
| alc_r0_synthetic_update_c4f147c_capsule.stdout.log | elapsed_updates_ns | 3826416300 |
| alc_r0_synthetic_update_c4f147c_q_lora.stdout.log | elapsed_updates_ns | 3664747400 |
| alc_r0_synthetic_update_2048_3966c90_capsule.stdout.log | elapsed_updates_ns | 9748722800 |
| alc_r0_synthetic_update_2048_3966c90_q_lora.stdout.log | elapsed_updates_ns | 10017682300 |
| alc_r0_synthetic_update_c4f147c_remount.stdout.log | elapsed_remount_ns | 722105200 |
| alc_r0_synthetic_update_2048_3966c90_remount.stdout.log | elapsed_remount_ns | 1406949500 |

Integer sums: gradient8909160300ns; updates27257568800ns;
explicitly bracketed phases36166729100ns; remount2129054700ns;
all twelve timing fields38295783800ns. No union of authenticated jobs or complete
consumption follows from these field sums. All selected receipts remain
synthetic_only=true/training_authority=false/held_out_data_present=false.
Source identity is source_checkout.source_commit, not a top-level source_commit.
Do not merge these inner intervals with outer command durations and double count.

## What further log reconstruction can and cannot establish

Checkpoint174's21 GPU-exercising test records have pytest duration fields but no
full historical resource journal. The inspected unchanged host-wrapper test file
SHA25649b9896e452024d4ae6aaf6f36403e18f180ff6e8a74da86041ce1aa233fe2f3 has no
explicit synchronize/perf_counter/elapsed timing instrumentation. Checkpoint175
recovers failed and successful terminal commands, not missing full GPU timing.
Control bootstrap includes CUDA work without a complete started/ended/GPU-time
receipt. More logs may recover further timing and identity; missing measurements
are not established as recoverable or globally impossible from these checks.

The frozen original plan requires600total measured GPU-hours, all attempts,
45days fromfirst development job,25GiBresearchgrowth and20GiBCfree floor.
Current resource arithmetic file SHA256
302a8d58c6d08d04e2304e0500e8e4961f60e750067c4fc57c1d7debe540e82e
returns history-unreconciled for incomplete/unknown firststart or consumption.
It is not permission, reservation or an authenticated completeness detector.
The Oct3 detail expressly says missing accounting prevents launch.

To avoid endless selected-history audits without crossing the real learning
gate, the remaining admission decision must be explicit: either recover a
reconciled complete original accounting, or obtain authority for a separately
reviewed, conservative historical accounting amendment. The latter is NOT
adopted here. It must define covered attempts, justified upper-bound charges,
clock anchor and evidence gaps; preserve the original600hour allowance without
reset, all failures, scientific grid/thresholds, disk ceilings and other launch
gates. It must not relabel estimates as observed GPU consumption or approve
training automatically. Missing evidence remains visible. If no defensible
bound is possible, remain blocked instead of inventing one.

This report establishes selected timing coverage and gaps, not global resource
PASS, first-job certainty, irrecoverability, scientific falsification, training
authority or durable-learning PASS. Whole program remains ACTIVE.
