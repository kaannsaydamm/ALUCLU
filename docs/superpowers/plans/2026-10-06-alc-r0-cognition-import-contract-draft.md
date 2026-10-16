# Cognition import isolation — second bootstrap prerequisite

Status: DRAFT_PENDING_REVIEW. No command, source edit, model access or scientific
launch is admitted by this document. Parent source is
9d245071f4585665e1f7d3a43e6289e23e84afb5. The preceding root/R0 import checkpoint
is preserved; this proposal does not extend its test coverage retrospectively.

## Observed boundary and alternatives

The ordinary `aluclu.cognition.persistence` route executes cognition/__init__.py,
which eagerly imports keys/ledger and therefore cryptography. The persistence
module and its contracts imports themselves use only stdlib. This eager coupling
prevents dependency-minimal preflight reuse of already-tested path/lock primitives.

Propose static lazy exports in cognition/__init__.py only, following the root/R0
resolver contract. Do not move persistence code, create a duplicate lock registry,
rename modules, load arbitrary files, replace sys.modules, add optional stubs, or
alter path/lock/ledger semantics. Relocating primitives would enlarge compatibility
and shared-lock-identity risk; retaining eager imports would preserve needless
coupling. Lazy exports preserve the original defining modules and singleton state.

This does NOT make the full journal stdlib-only. attempt_journal and attempt_state
use alc_r0.canonical, which intentionally requires rfc8785. RFC 8785 must remain
unchanged; do not substitute cognition JSON or stdlib json.dumps, suppress missing
dependencies or interpret import errors as an empty history. After minimal initial
denial, journal composition needs a separately reviewed dependency/provenance
boundary. The latter is OPEN, not implicitly approved by this initializer change.

## Exact technical scope

- Runtime edits limited to src/aluclu/cognition/__init__.py. Root/R0 initializers,
  persistence/contracts/keys/ledger and canonical implementations stay unchanged.
- Static module/symbol pairs preserve every current public export, __all__ content
  and order, original object identity and defining-module behavior. Pin the
  pre-edit roster/mapping in a test fixture independently of the implementation.
- Ordinary importlib resolution, success-only cache, original dependency errors,
  unknown AttributeError, no custom lock across imports, non-resolving dir.
- Preserve direct and from-submodule semantics, including imported submodules
  being installed as module-valued package attributes. Assess name collisions.
- Incidental eager module attributes and import-time timing are deliberately not
  the public-symbol promise; inspect their actual consumers and record limits.
- Root re-exported cognition symbols must resolve to exactly the same original
  objects; lazy delegation must not produce wrapper classes/functions.
- Persistence module imports must retain the same process-path lock registry and
  exception classes through direct and package export access. No new registry.

## Test-first acceptance and regression scope

First add a fresh-process test with third-party blockers installed before all
project imports. Exercise normal cognition package, contracts, persistence and
root stdlib error exports; require zero prohibited attempts/modules and original
identity. Reproduce current eager cryptography import as RED before source edits.
An initial contaminated child, wrong source path or collection failure is not RED.

Then verify complete pinned public roster and object identity, repeated/from/star
access, non-resolving dir and unknown names, dependency error twice with no failed
binding then successful retry, both direct-submodule access orders and concurrent
same/different exports plus direct imports. Heavy explicit exports remain heavy.

Add temporary-directory persistence integration using the original APIs: lock
sharing, normal path resolution and atomic replacement. This is synthetic local
storage, not actual research accounting, resource reservation or model access.
Assess existing persistence, key/ledger, session, sensorium, recollection,
calibration, reconsolidation and architecture regressions before admission. Do not
silently include hours-long scale workloads or real OS-keyring mutation. Existing
Task 2 behavior/acceptance cannot be certified by a pure import test alone.

Exact commands and bounded resource scope require independent review before runs;
final-byte test results, native terminal exit, artifacts/hashes, lint and both
independent implementation/terminal verdicts are required for this checkpoint.

## Still-open real-host gates

Trusted history/authority, original program clock, separate q/v ceilings,
reservation/process publication/crash reconciliation, resource upper bounds,
RFC 8785 dependency bootstrap, actual pinned host qualification, rights/evaluator/
sealer/scientific freeze and retrieval-off durable neural learning remain OPEN.
No accounting convention, threshold, grid, scientific meaning or launch authority
is changed. This is a prerequisite on the same path, not a substitute end state.
