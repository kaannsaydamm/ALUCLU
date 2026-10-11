# Owner-approved allocation policy arithmetic adapter

Status: revised design readiness code APPROVE / architecture CLEAR; implementation
and execution evidence pending. Not actual resource or launch admission.
Parentaf3ddb1174e38b5f2abf7b68cb91794fe391f623.
This is a required accounting composition input to the real launcher, not a
substitute for training, a historical reconciliation or authorization producer.

## Existing decision and compatibility

Owner-approved October7 decision permits GPU allocation wall time and separately
justified conservative historical upper bounds. Existing ProgramAccounting has
observed-claim semantics; do not insert estimates into it or change its current
callers/tests. Add allocation_policy.py separately, stdlib-only, with immutable
exact typed observations. A policy/coverage root is an evidence link, not proof
of origin, completeness, user approval or a signature. Actual trusted coordinator
must independently verify policy, complete coverage and pinned clock before use.
The pure helper cannot launch, reserve, release, write evidence, open assets,
authenticate history, initialize CUDA or produce VerifiedLaunchContext.

## Exact interface

assess_allocation(request: AllocationRequest) returns AllocationAssessment.

AllocationAccounting(policy_root, coverage_root, charge_kind, effective_gpu_ns,
clock_kind, clock_utc_ns), frozen slots dataclass. Optional roots are None or
exact64lowercasehex. charge_kind is observed/allocation_upper_bound/unknown;
clock_kind is observed/conservative_boundary/prospective_pending/unknown.
Numeric fields are None or exact integers0..2^63-1 excludingbool. unknown charge
requires None effective value; known charge requires an exact value (including0).
observed/conservative clock requires exact clock value; pending/unknown requires
None. Keep the kind in the input, never silently relabel an upper bound observed.
Known facts may still lack coverage or policy; those cases deny, not infer proof.

AllocationRequest(accounting, phase, device, now_utc_ns, entry_monotonic_ns,
now_monotonic_ns, research_bytes, free_c_bytes, projected_research_growth_bytes,
projected_physical_growth_bytes, pending_research_growth_bytes,
pending_physical_growth_bytes, pending_gpu_ns), frozen slots dataclass.
Each numeric observation is exact0..2^63-1, excluding bool/float. Trusted caller
must use one independently verified monotonic domain for entry/current time;
pure numbers cannot establish boot identity. These are independently verified
inputs at the later producer, not arbitrary worker JSON launch permits.

AllocationAssessment(resource_fit, reasons, useful_deadline_monotonic_ns,
cleanup_deadline_monotonic_ns, required_gpu_reservation_ns, remaining_gpu_ns,
program_deadline_utc_ns), immutable. resource_fit is arithmetic consistency ONLY;
no launch/training/authority flag. Reasons are bounded fixed strings in stable
order. Derived deadlines and reservation become None on their own overflow;
Unknown charge or missing charge policy/coverage leaves remainingGPU None;
unknown/pending clock leaves programdeadline None. Derive these independently:
a known clock still exposes an expired window when charge is unknown, and known
exhausted charge still exposes budget failure when clock is unknown. Missing
policy/coverage remains an independent denial, never origin authentication.
Do not clamp ordinary representable negative remaining.

## Frozen numerical rules

Keep600GPUhours,45days,25GiBresearch cap,20GiBCfree floor and existing10second
cleanup tail. Fixed useful ceilings D45minutes, E1/E3 30minutes, E2 10minutes,
pilot2hours. D admits separately declaredCPU/noCUDA or singleGPU; E1/E2/E3/pilot
require the original singleGPU scope. pilot describes ONE original200-update job,
not an altered four-job pilot schedule. This helper never checks updates or
scientific job IDs: the fixed declaration/RunSpec coordinator must do that.
Separate q/v has no approved ceiling; unsupported phase fails structurally.

Required singleGPU reservation = useful ceiling + existing10secondtail; CPU0.
Derive useful deadline from ORIGINAL entry_monotonic_ns, not current time.
Derive cleanup upper bound from that same useful deadline + tail; no renewal.
Backwards now or now>=usefuldeadline denies. Checked addition overflow denies,
never wrapped arithmetic. Full preflight consumes the original useful allowance.

Effective remainingGPU = original600h - effective historical charge - pendingGPU.
The supplied effective charge covers all prior charged work, including released
reservations, without double-counting historical and instrumented periods; the
trusted coordinator must establish that coverage, not this arithmetic helper.
Check charge+pending against signed64 MAX BEFORE returning a remaining value.
Overflow returns remaining_gpu_ns=None and resource-arithmetic-overflow, while
retaining the independently provable gpu-budget-insufficient denial. Intermediate
bounded exact Python arithmetic may establish the comparison but must not emit
an out-of-range value. Returned remaining is signed64; no clamp or refund.
Coverage/policy/known charge required even for CPU. None does not mean zero.
Clock observed/conservative_boundary required; pending does not start a new clock.
Programdeadline = clock + original45days. Deny UTCbackwards, overflow, now>=end,
or projected completion past end. UTC projected duration uses REMAINING useful
monotonic allowance + cleanup tail, not a fresh full useful interval at every
preflight recheck. Clock root/provenance verification remains external.
If the monotonic useful allowance is already exhausted, use zero remaining
useful time only for the independent calendar diagnostic; monotonic-window-invalid
still denies. If its deadline overflowed, calendar completion cannot be established
and denies too. Check every derived deadline, UTC completion and storage sum
against signed64 MAX, accumulating one resource-arithmetic-overflow reason.

Physical and research growth are distinct: research_bytes + pending_research +
projected_research <=25GiB; freeC - pending_physical - projected_physical >=20GiB.
Check derived signed64 sums before interpreting. Materialization subtraction is
allowed only by the coordinator on a matched verified growth observation root;
this pure request receives already verified pending values, never discovers or
guesses them. No retrospective refunds, reset or hidden CPU/GPU fallback.

Fixed denial order: history-unreconciled, clock-unreconciled,
gpu-budget-insufficient, monotonic-window-invalid, program-window-invalid,
resource-arithmetic-overflow, research-storage-insufficient,
c-free-space-insufficient. Include independent known failures even when history
is unknown. Malformed exact types/kind/value combinations raise ValueError.

## Evidence and subsequent connection

TDD missing-module RED then focused synthetic arithmetic GREEN: observed and
bounded charges retain their kinds; unknown/pending denies; exact limits; cleanup
tail budget/calendar boundary; elapsed preflight; backwards/overflow; independent
research/physical growth; no mutability, authority flags or heavy imports.
Existing resource arithmetic and import-boundary regressions remain unchanged.
Exact source/test invocations independently reviewed before execution; original
native test process personally observed terminal, raw artifacts preserved.

Acceptance proves arithmetic policy implementation, NOT complete historical
coverage or actual launch admission. Next compose authenticated operator/source/
runtime/declaration/history inputs with durable reservations and reviewed owned
lease, then qualify the pinned real host and execute the original pilots. Numeric
history/calendar, resource observations and authority producer remain mandatory.
