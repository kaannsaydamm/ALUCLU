# Checkpoint163 prospective attempt-state replay

Original R0 sections7.1/12 remain binding; no frozen schema/matrix changed.
Pure semantic replay over externally authenticated declared RunSpec rows, not
source/review authentication, resource reservation or scientific proof. Existing
280run matrix remains nonauthorizing. Synthetic D/E needs separate declarations.

Each run has exact run_id, resource_run bool and ordered unique work_ids.
Canonical8KiB object events: run_id, attempt_id, kind plus EXACT fields below.
Caps262144events per replay batch,512declaredruns,65536work IDs/run and262144
declaredwork IDs total/batch,128ASCIIchars/ID. Implementation batch bounds, not
scientific update limits. Original3epoch*ceil(N/16) unchanged; former4096work bound
was inadequate for larger cohorts, corrected before any actual invocation.

- intent: source_sha256, invocation_sha256, retry_kind, prior_source_sha256,
  prior_artifact_sha256, review_sha256. a001 INITIAL has null prior/review roots;
  subsequent attempts consecutive, previous INVALID only. REPAIR once/run,
  previous IMPLEMENTATION, changed source, exact superseded source/artifact roots
  and nonnull review. ENVIRONMENT resource only, previous ENVIRONMENT, same source,
  reviewed invocation. At mosta002 otherwise; a003 onlyENVIRONMENT.
- start: receipt_sha256; INTENT->RUNNING only.
- work: work_id, evidence_sha256; RUNNING and exact next missing work only.
- interrupt: checkpoint_sha256, evidence_sha256, gpu_ns, wall_ns,
  storage_growth_bytes. Internal INTERRUPTED keeps logical run RUNNING;
  preserve bindings/work and segment measurements.
- resume: checkpoint_sha256, source_sha256, invocation_sha256, review_sha256;
  INTERRUPTED only, exact checkpoint/bindings, once/logicalrun (not per attempt),
  same attempt, only missing work follows. Never automatic.
- close: state INVALID/BLOCKED/PREPARED, failure_class ENVIRONMENT/
  IMPLEMENTATION/OTHER or null, evidence_sha256 and the three measurements.
  PREPARED onlyRUNNING with all work complete, failure_class null.
  INVALID requires failure_class; BLOCKED requires OTHER, terminal run.
  Other closes allowed from INTENT/RUNNING/INTERRUPTED.
- result: state PASS/FAIL, evidence_sha256; PREPARED only, terminal run.

One prepared candidate, no retries after PREPARED/PASS/FAIL/BLOCKED. Implementation
or environment failures are INVALID attempt evidence, not scientific FAIL. Keep
all prior attempts/roots in immutable output. Metrics caller-supplied integers
0..2^53-1 or explicitNone, incremental per interrupted/closed segment. None stays
unknown through aggregates; open attempts have unknown aggregate consumption.
These are journal-local observations, not historical program budget/current disk.
No resource-fit, authority or completion flag follows from a valid replay.
AttemptView scalars are summaries; its events tuple preserves exact canonical
input bytes, including interrupted/prepared/result/review roots. Original
authenticated journal chain/head/declaration remain necessary to authenticate
these retained references, which do not prove artifact existence.

Never omit scientific work or force the full matrix into one batch/file to fit a
cap. Per-run journal paging/complete-history binding and global accounting/matrix
completeness are mandatory before full R0 training. Current32MiB/65536record
storage page cannot cover arbitrary jobs/retries. A helper batch cap is not
scientific resourceFAIL; paging/efficient semantic continuation remain open.

Mandatory next: exclusive reservations/resource binding, independently durable
monotone-head publication/uncertainty reconciliation, source/runtime/artifact/
review authentication, actual checkpoint restore validation, historical accounting
and owned-process launch binding. No model/data/GPU launches. RED/GREEN, negative
transition/retry/resume/unknown tests, storage replay integration, independent
two-lane review and relevant regression required before scoped acceptance.
