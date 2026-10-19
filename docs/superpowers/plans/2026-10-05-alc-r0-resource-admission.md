# Checkpoint161 resource admission and subsequent journal — prospective

Scope: the already fixed synthetic checkpoint D/E launch boundary, not adoption,
training permission, a new scientific matrix or the final secure ALC container.
Source requirements: checkpoint implementation detail sections D/E/F and the
original R0 resource budget/attempt rules. Runtime diagnosis checkpoint160 stays
OPEN; pure CPU implementation does not require actual-host launch authority.

## First component: pure arithmetic and explicit unknowns

`checkpoint_resource_admission.py` consumes immutable caller-supplied observations.
It opens no files, starts no processes, imports no model/tokenizer/Torch and grants
no execution authority. Observations are trusted inputs, not authenticated by a
hash string. Caller must verify a reconciled history artifact and bind its root.

Fixed program ceilings:600 measured GPU-hours,25GiB research storage,20GiB C:
free-space floor,45 days from the evidenced first development instant (UTC).
This component uses45*86400 elapsed seconds in UTC; it cannot infer or reset the
first development date. D45min, E1/E330min, E210min invocation ceilings stand.
No caller-custom threshold. D accepts CPU/GPU, E cells GPU only.

For single-GPU reservations conservatively reserve the entire wrapper ceiling;
CPU D reserves0 GPU time and must never perform CUDA work. A future measurement
ledger must distinguish that upper reservation from measured GPU consumption.
Incomplete/unknown historical consumption/start/root returns non-authorizing
failure with unknown remaining budget/deadline, never a fresh600-hour allocation.
Explicit pending GPU/storage reservations are mandatory inputs, not default0.
Current research bytes plus pending/projected growth must fit25GiB; free C:
minus pending/projected growth must preserve20GiB. Boundary equality is allowed
except a launch at/after program deadline; an entire ceiling must fit the window.
Each growth input MUST conservatively bound BOTH incremental research-accounted
bytes and peak incremental physical allocation on C:, taking the larger bound.
Include temporary files, staged/checkpoint copies, journal/log writes and any
asset/cache effects; final output length alone is not an acceptable projection.
Pending growth denotes only still-unmaterialized reservations. Current observed
research usage/free space already include materialized bytes; subtract them from
outstanding reservation growth atomically during later journal reconciliation,
not twice here. If reliable shared upper bounds cannot be obtained, integration
must introduce separately measured research and physical growth projections.
`remaining_gpu_ns` is availability BEFORE this new request's required reservation,
not a post-reservation balance. No reservation is created by this calculation.
Over-budget observations are preserved as denied evidence, not clamped success.
Reject malformed integers/bools/floats/negative/oversized values, invalid phases,
devices and malformed evidence roots. Output frozen decision/reasons only.

Acceptance: RED missing module, GREEN exact arithmetic/unknown/negative/boundary
and immutability tests, focused independent code/security and architecture review,
then relevant regression. None establishes real historical reconciliation.

## Mandatory subsequent components, not replaced by the first helper

Durable append-only intent/reservation/launch/terminal journal with exact source,
runtime/assets/invocation roots; interprocess reservation exclusion; no rollback
or silent truncated-tail acceptance; fsync-before-launch and terminal failure
retention. Resume and retry cardinalities must follow the original run/attempt
contract, not become implicit retries. Measured resource reconciliation must
cover all attempts/resumes, not partial forward/backward timings alone.
Actual resource observations/source authentication/storage revalidation and
owned-process binding are separate launcher integration gates. A passing pure
helper cannot close these, runtime qualification, D/E or scientific learning.
Never launch directly on `resource_fit`; authenticate current accounting, reserve
exclusively/durably, revalidate storage and bind a qualified exact invocation.
The runtime must enforce one GPU for GPU D/E and no CUDA activity for CPU D.
