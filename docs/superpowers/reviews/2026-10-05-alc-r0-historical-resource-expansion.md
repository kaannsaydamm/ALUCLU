# Historical resource reconstruction: checkpoint174 discovery

Inspected parent8d4f7a23629437b8638704d6e530ce71ffb2bc8f, authoritative Desktop
checkout,2026-10-05. Read-only evidence discovery; no historical jobs rerun, model
import, corpus access, installation, deletion or scientific launch. This is not
a reconciled budget ledger or a launch approval.

## Finding that changes the next action

Checkpoint156's twelve selected synthetic stdout receipts are insufficient to
reconstruct consumption. Searching current results for the exact testcase
`test_real_frozen_host_synthetic_capsule_training_survives_serialization` found
21 distinct XML byte roots, each with one non-skipped, non-failing, non-error
record for that test. The historical and current host-wrapper test Git blob is
identical:539e124803a07192a73166ccd4dbafc0a54830d2 (fcd47a0 vs inspected HEAD).
Local SHA25649b9896e452024d4ae6aaf6f36403e18f180ff6e8a74da86041ce1aa233fe2f3.

That test uses the verified pinned real GPU BF16 host, eight synthetic input
tokens,40 AdamW updates on the capsule, serialization and a child-process
remount. These are additional historical GPU-exercising records, not the six
separate16-update CLI cells. Test names alone do not establish runtime/source
approval; inspected source corroborates device/loop behavior. Distinct XML roots
are distinct records, NOT authenticated proof of21 distinct process invocations.
Do not turn840 expected loop iterations into an authoritative global update count.

Sum of those21 testcase duration fields:828.979seconds. Sum of their full suite
duration fields:5712.584seconds. Neither is measured GPU consumption: tests include
CPU/digest/serialization/process overhead, shared fixture setup, asynchronous CUDA
and other cases. Do not add either sum to the twelve phase timings or subtract
it from600GPU-hours. A conservative reservation cannot retroactively replace the
original measured accounting requirement without a separately approved amendment.

## Exact matching records

All paths below are under `results/`; durations are testcase seconds, not GPU
seconds. Exact SHA256 roots are retained for revalidation, not authenticity.

| XML file | Case seconds | SHA256 |
| --- | ---: | --- |
| alc_r0_banded_edit_visibility_regression-v1_20261002.xml | 17.204 | 43472ed12a6198ceeb314c24d756680364c09ea2ff5cee02fe6f561af5aeb32e |
| alc_r0_banded_native_final-regression-968e92f-other-v2.xml | 72.669 | 82fb3d96fee384b7cb188a2be36ce7940c4db66e824564f6694dccc74edbde32 |
| alc_r0_banded_native_final-regression-bf08b1c-non-native-v1.xml | 30.538 | daecd99e9560e3214967f72c72ebf7b3f2667bc84e391089c1534f51edae2ae4 |
| alc_r0_context_gradient_probe_regression_20260929.xml | 44.869 | 44f58afea177258222718c5865d8cf9d47eb0da1d273051f7e86501ad7d0f36d |
| alc_r0_defect_prompt_receipt_regression_20260929.xml | 24.218 | fc46dc4c04a5250e7f6ec6b745629e6f0e45a04df347a81f75e1d9ef56a7687e |
| alc_r0_defect_prompt_regression_20260929.xml | 30.256 | 8ee52c4848b7c10141da5962e26ee48ce74482e5d5be5a0042096df3109dd2a7 |
| alc_r0_edit_token_visibility_regression_20260930.xml | 62.915 | 786142468199c05286fe5a1cf9247b22988e8d21b1bdd5b67fd378c9707a98a7 |
| alc_r0_near_edge_audit_regression_20260929.xml | 46.993 | 6f2baed09ca947e99a149785990af969c3be8da0d2d0715296df0db6ade65c1c |
| alc_r0_pair_prompt_contrast_postreview_regression_20260929.xml | 80.619 | 7ab9d437220d5215ab92a8bb16cd605e654bc6ea55e076549b2e11a03ee4c58c |
| alc_r0_pair_resource_census_broad_v1_20261002.xml | 19.445 | 87c7abed8a00be6d1b46f9a14946bbf7c5b7765606977a1322af92696555d1d2 |
| alc_r0_pair_prompt_contrast_regression_20260929.xml | 41.280 | 61eda6fcf3af11968bdcc2d614d87348bc1ee4d5206a8ed03b4060241fbe53a5 |
| alc_r0_prompt_budget_grid_regression_20260929.xml | 34.532 | 0bdee327d4c17635c1fa63b7382bd9f0a9e785e5d80bcf54d0c7111600d119b5 |
| alc_r0_retained_pair_regression_20260929.xml | 26.765 | 887298c0dd99d92c30aeaca05600b59f626532afbf8a087399af15a338492cf8 |
| alc_r0_retained_prompt_information_regression_v2_20260930.xml | 36.042 | 22e6230617f93b35bc77528313eccb1dc5b25c6b1f6865e0cbfcc33930b9f30b |
| alc_r0_synthetic_trainability_focused_20260928.xml | 39.176 | 727de856e20d34c395df6e467f6ec26e07a9330228d16e984ba778326a4b2e4b |
| alc_r0_synthetic_trainability_final_regression_20260928.xml | 32.136 | 608c97d6cc6a245f25f95f7ece5ed5e0c74f6141e0bc31457e7520d9e57fefce |
| alc_r0_synthetic_trainability_focused_v2_20260928.xml | 50.872 | 976b05a8bae3de530b7d8c5d8bea0af9866db0b1f961b5d5964c05b91a78194c |
| alc_r0_synthetic_trainability_regression_20260928.xml | 50.650 | aa3e84736c9e2fbcc47fb532472abb556049761d689ad990ffda1dff70bc1521 |
| alc_r0_source_checkout_regression_20260929.xml | 34.490 | 10bda54b817fc767b905cc6f7e64002c657c277b8f7ae272b050ba615e14adc1 |
| alc_r0_synthetic_update_long_regression_20260929.xml | 24.070 | e86e8b5e2650dcd30bab0be27579beac4da39c78114bfa9328b7f51efc601988 |
| alc_r0_synthetic_update_regression_20260929.xml | 29.240 | 0b6320c935a1503da5ee76d2a35aa13621520f5dd64092b105314b6b3245c84d |

Reproduce discovery with `rg -l --fixed-strings <exact testcase name> results -g
'*.xml'`; parse each XML, select that exact name, inspect child skipped/failure/
error fields, sum decimal duration fields with invariant culture, and SHA256 the
original XML bytes. This inspects old results; it does not execute pytest again.

## Further categories and private terminal provenance

- `alc_r0_defect_prompt_model_smoke_20260929.xml`:1/0/0/0,28.508suite seconds,
  case24.557seconds, SHA3b3cf719a6e4af25e5662c92c860aabcd9878bf71989d428ca81feb87624ee6e.
  Actual inspected source loads CPU FP32; do NOT classify it as GPU time based
  on being a real-model test. This is another execution category to reconcile.
- Base-digest receipt SHA3bc973d0003160ab24f2b26c519129d48d7094a025381b41b1ffe152645d1953
  records two observations, no wrapper start/end or measured GPU duration.
- Linux evaluator bootstrap SHAf3eb83630369a7b71f08005ed69648eb0007143cbd911be45b5cb556cab1208a
  contains actual BF16 CUDA probe but no started_utc/ended_utc/elapsed_gpu_ns.
- Gradient execution log SHAbd5b3970f528c252843b1955adff3578240c9a25fa63baee19ff8302993518da
  records six terminal stopwatch wall values totaling465.588seconds, explicitly
  manually transcribed; model loading included but not synchronized GPU measure.
- Prompt-budget log SHA26bae1934a18f2a911d4666ce54aaf6587624f301ba5d93354028e402b5e14a7
  explicitly says model_forward_executed=false. Tokenizer/CPU durations are not
  GPU training consumption.
- TRAJECTORY.md original family-B source checkpoint (around line4542 in parent)
  retains one first-child CUDA OOM in two-fresh-process forward test, followed by
  targeted and full reruns. Successful later receipts must not erase this attempt.
  Failure duration/terminal identity/source/whole-program accounting still needs
  the original terminal evidence, not a guessed zero or success-only ledger.

Bounded Git history filename discovery:55 unique selected names matching
`^results/alc_r0.*(budget|ledger|gpu|pilot|fit|train|host|smoke|synthetic|gradient)`;
none absent from current tracked results. This is a naming-based subset, not proof
of no missing or removed records elsewhere/historical commits/untracked directories.
Commit author dates prove repository metadata only, not first job start time.

Private local session inspected through bounded date/pattern filtering:
`C:\Users\kaann\.codex\sessions\2026\09\18\rollout-2026-09-18T23-11-24-01a029c6-7908-79a3-8b63-2b0998d2bd3e_01a0b625-2aa9-7eb1-be31-088f8b48bf34.jsonl`.
Do not copy/stage/upload that entire history (unrelated user content). Relevant
response items show these512-token invocation call timestamps in UTC:

| Cell | Invocation response item | Timestamp | Returned exec cell |
| --- | --- | --- | --- |
| capsule | call_BSM9pzPjCybx6MOyMfVXKpeC | 2026-09-29T18:48:35.531Z | 348 |
| q_lora | call_XVkHET9H1hxlwOqa0VIyJntQ | 2026-09-29T18:50:21.908Z | 354 |
| remount | call_9Z9qHJzaNLL1nAhT3GG9J50j | 2026-09-29T18:51:57.177Z | 359 |

Commands select actual synthetic_update_probe train/remount, prior recorded local
runtime/snapshot, offline variables and external .research-evidence stdout/stderr.
These are tool request timestamps, NOT actual process-start/terminal measurements.
Calls354/359's final wait outputs at18:50:35.699Z/18:52:09.041Z respectively are
only `System.Management.Automation.OrderedHashtable System.Management.Automation.OrderedHashtable`.
Their serialized visible outputs do not expose a numeric exit code/duration.
Subsequent inspection of the SAME bounded timestamp range's embedded
`event_msg/item_completed/CommandExecution` records recovered all three terminal
results, with exact synthetic_update_probe command/arm/paths and Desktop cwd:

| Arm | CommandExecution id | Tool process handle | Exit | Command duration seconds | started_at_ms | completed_at_ms |
| --- | --- | --- | ---: | ---: | ---: | ---: |
| capsule | exec-16fa462f-8570-4ca1-86c5-c4ca38479cf3 | 16536 | 0 | 69.155747700 | 1790707715736 | 1790707784890 |
| q_lora | exec-017909b3-c305-4027-b995-c3050977647c | 83699 | 0 | 70.201327300 | 1790707822175 | 1790707892375 |
| remount | exec-6879345b-dd6f-44c7-a24e-36b43dafb4fe | 59229 | 0 | 60.941178100 | 1790707917372 | 1790707978312 |

These are recovered terminal tool-command observations, not merely trajectory
assertions. Tool process handle is NOT an OS PID authenticated for termination;
timestamps/duration cover the shell command, not CUDA occupancy or dedicated
GPU measured time. Command duration sum200.298253100seconds is not global budget
consumption. Raw timestamp interval and high-resolution duration differ slightly
because tool timestamp fields are millisecond precision; do not replace fields.
No saved command was executed; no old process was restarted or terminated.

## Remaining reconstruction work and launch boundary

Continue joining other invocation/result identities from original item_completed
embedded tool events (three512-token cells now recovered); include21 matching suite records, all other GPU suites,
CPU-only host/tokenizer controls, original OOM/failed/interrupted jobs, acquisitions
and bootstrap categories. Deduplicate copied artifacts by exact execution identity,
not by equal score, similar filename or shared source. No completion coverage
claim follows from this first exact-name search.

The original first development instant, complete measured GPU consumption and
all-attempt inventory remain UNKNOWN. The600hour/45day/25GiB/20GiB limits and
retry rules remain unchanged. The local intent audit173 can validate a newly
recorded published chain, but cannot reconstruct unmeasured old GPU activity or
authenticate external freshness. No actual launch permit follows from this audit;
native160/checkpointrestore/source-runtime-assets/review/rights/R0 gates remain
OPEN. Safe pure implementation and bounded historical reconstruction continue.
