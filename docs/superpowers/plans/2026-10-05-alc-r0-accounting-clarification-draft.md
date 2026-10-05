# Historical resource accounting clarification: DRAFT, NOT ADOPTED

Parent d1e027da42d6cf12348b752a0df9e7650f62811a.
Status: DRAFT_PENDING_USER_DECISION; no launch or training authority.
Prepared2026-10-05. Automatic goal continuations are not approval of this draft.
Original scientific plan remains byte-frozen and authoritative. Checkpoint177
documents partial historical measurements and unresolved accounting convention.

## Decision requested, not a completed requirement

Clarify the resource charge as GPU allocation wall time rather than requiring
GPU-active occupancy telemetry. For unmeasured historical intervals, allow only
separately justified conservative upper-bound charges. This changes the evidence
standard for resource accounting, not learned-capability acceptance. It requires
explicit user approval and independent review before any adoption.

Approval of the method alone is insufficient for launch. A concrete reconciled
coverage record, numeric charge and clock anchor must be reviewed separately;
no numeric historical consumption, first-job fact or resource PASS is supplied
by this draft. Until then current history-unreconciled denial remains unchanged.

## Preserve distinctions in the proposed record

Keep observed phase times, observed full-command wall times, justified upper
bounds and unexplained gaps as separate typed categories. A hash authenticates
none of their factual claims by itself. Exact artifact roots are evidence links,
not substitutes for origin, coverage or authority. Never write an estimate into
an observed measurement field or mark incomplete measured history complete.
If adopted, any effective conservative charge needs its own explicit policy
identity and provenance; existing ProgramAccounting.consumed_gpu_ns semantics
must not be silently repurposed. No production code changes are made here.

## Required historical coverage before a finite bound can be accepted

1. Enumerate valid, invalid, failed, retried, resumed and interrupted attempts,
   including GPU-exercising tests, bootstrap/control work and possible surviving
   children. Selected successful receipts do not establish whole-program coverage.
2. Join execution identity, source/runtime evidence, hardware/device count,
   allocation interval, terminal state, outputs and uncertainty. Runtime version
   strings and current hardware are not proof of historical binary/device facts.
3. Deduplicate copied records only through justified execution identity. Preserve
   ambiguous duplicates; score equality, filenames and shared source are not IDs.
4. Prove a start/end envelope for each uncertain charged period and a justified
   maximum participating device count. Full-command wall time can upper-bound
   a contained device allocation only when containment is supported. Missing
   terminal coverage or surviving child tails cannot be assigned zero duration.
5. A whole historical-window bound is another candidate only if its earliest
   boundary, latest cutoff and maximum device scope are justified. Do not assume
   one GPU, exclude prior machines/external runs or invent an earliest start.
6. If scope/device/time bounds are absent, the bound stays UNKNOWN; no arbitrary
   padding or round-number charge is acceptable. Retain the evidence gap and
   deny launch. A conservative estimate does not prove the actual original time.

## Charging arithmetic if the method is approved

For justified covered allocation intervals, charge duration times device count
using checked integer nanoseconds. Inner update/gradient/remount intervals are
not added to their outer allocation charge. For overlapping observations of one
physical device, an interval union needs justified device/execution coverage;
otherwise an explicitly conservative sum may overcharge, never hide uncertainty
as observed utilization. Both sources and overlap treatment remain auditable.
Count all failed/resumed/repaired/resource-invalid attempts under original rules.
An unknown gap blocks admission; it does not become a zero-valued row.

Keep effective historical charges plus pending reservations plus the requested
worst-case reservation within the ORIGINAL600GPU-hour total. No new600hour
allowance, subtract-and-forget rewrite, retrospective refund or implicit extension.
If the conservative total exceeds the ceiling, report resource admission blocked.

## Calendar, storage and scientific gates remain separate

Preserve ORIGINAL45days from the first development job. Keep actual first-start
evidence distinct from a separately approved conservative clock boundary; the
latter must not extend the deadline or be represented as an observed first job.
If the original or defensible no-later-than-first boundary cannot be established,
calendar admission stays blocked. No new clock starts upon approval or reboot.
Preserve25GiB isolated research ceiling and20GiB C:free floor, pending/peak growth,
exact source/runtime/assets/invocation review, owned-process qualification,
durable exclusion/reservation, rights/sealer/evaluator/freeze and all R0 gates.
No paid compute, installations, cleanup, unowned process termination or OOM
fallback is authorized. Scientific grid/seeds/splits/thresholds remain unchanged.

## Prospective accounting, conditional future implementation

After explicit method/record approval and tested implementation, persist exact
attempt identity and full conservative reservation before launch under exclusive
ownership. Measure full owned wrapper/allocation lifetime with monotonic time;
retain UTC observations separately. Preserve synchronized phase timers as
diagnostics, not substitute total consumption. On timeout/crash/reboot, keep
reservation until owned-tree terminal state and charge are reconciled; do not
release on an observation timeout. TDD, regression, independent byte reviews
and evidence/trajectory precede adoption; no such implementation is claimed here.

## Current unresolved values and authority

User method approval: absent. Historical complete coverage: unproven.
Effective historical charge: UNKNOWN. Original first development instant: UNKNOWN.
Clock boundary and historical maximum device scope: not approved/proven here.
No allocation charge or remaining-budget number is calculated from these gaps.
Current admission and scientific launch: BLOCKED, not a falsified neural hypothesis.
This draft can be reviewed/preserved without implementing or adopting its policy.
