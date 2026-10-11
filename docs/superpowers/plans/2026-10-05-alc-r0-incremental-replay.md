# Checkpoint164 incremental attempt replay qualification

Parent158fd31, original R0 attempt/retry/work/metric contract unchanged. Keep
the whole-history immutable replay as a reference. Add single-owner in-memory
AttemptReplay(specs), append(one canonical event), event_count, snapshot().
Only semantic validation; no authenticated page reader, checkpoint cache import,
durable witness, resource reservation or model execution permit.

Work/history buffers append in place privately; snapshots copy into immutable
views only on request. No caller-supplied cached state: initialize from declarations
and replay every authenticated event in order from genesis. Do not skip earlier
pages. All declaration/event bounds remain unchanged, never scientific thresholds.
Invalid append must leave the accepted prefix and count unchanged. Snapshots must
not mutate buffers or lose partial measurements; old snapshots remain immutable.
Single owner, no concurrent writers; no all-or-nothing multi-event batch promise.

RED/GREEN/reference prefix equality, reject/nonmutation/continued valid event,
interleaved runs, retry/resume/unknown/overflow, bounds and storage restart tests.
Independent code/security + architecture review and relevant regression required.

Prospective synthetic timing: counts8192,16384,33243; three samples each, both
reference full-history replay and incremental append plus one final snapshot;
same canonical fixture events/declarations and exact output equality. Record all
elapsed wall nanoseconds, per-count speed ratios and roots; no target acceptance
threshold or claim about training/model/disk performance. Imports may initialize
existing package CPU dependencies. No actual model/tokenizer/corpus/GPU assets.
Repeated snapshot-per-work still copies history; storage full scans and paging
remain separate OPEN work. Historical budget/runtime160 remain OPEN.
