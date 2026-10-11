# Checkpoint167 durable local manifest publication

Parent6591de9; extend research execution bookkeeping, not final ALC container.
External current monotone record root remains mandatory: local file plus local
root rollback cannot be detected. No auto-discovery/adoption or launch permission.

Store bounded canonical v1 envelope outside dedicated page directory, containing
generation, declaration root, previous envelope digest, manifest object and review
root. Genesis generation0 contains only empty manifest and null previous/review.
prepare constructs exact next envelope from independently expected previous bytes,
candidate manifest/root and explicit review root, without filesystem access.
PreparedPublication retains exact previous and candidate bytes; no mutable token.
Generation limit262144 is operational, not scientific attempt/work relaxation.

create explicitly verifies empty page directory and refuses existing owner.
read(expected root) returns only exact current envelope plus fully verified page
view under owner lock. publish(prepared) compares exact old bytes/root under same
owner lock, runs166 full strict extension verification and atomically replaces
envelope before acknowledgement. Concurrent cooperating same-parent candidates:
one acknowledgement, one conflict; never latest-wins. Any write error returns no
receipt and requires explicit resolution; external root not silently advanced.

reconcile(prepared) accepts ONLY already-visible exact candidate envelope,
revalidates166 old-to-candidate extension from retained old bytes, and atomically
re-writes IDENTICAL candidate bytes to complete durability acknowledgement.
It does not generate another envelope, repeat model work, or adopt arbitrary
newer state. If old bytes remain visible, reconcile rejects: caller separately
checks old owner and makes an explicitly reviewed retry decision. Absent,
malformed, different or rolled-back bytes never repaired/reset.

Reuse existing path safety/cooperating locks/atomic replacement. Owner and lock
must be single-link regular files before open; bounded reads and descriptor
checks. Trusted closed namespace and all page mutations under same owner lock
are REQUIRED. Existing low-level page API alone does not enforce that contract.
No hostile TOCTOU/privileged attacker or guaranteed power-loss durability claim.
Underlying Windows write-through/POSIX directory-sync semantics need qualification;
full subprocess crash-boundary and actual writer integration gates remain open
until executed, not inferred from unit tests or atomic primitive naming.

TDD: genesis/restart, exact candidate publish/reconcile/no extra generation,
conflicting/stale candidates, fully valid rewritten prefix, review/schema/bounds,
missing/truncated/corrupt/unsafe owner, page failure retains old record, and
concurrent cooperating publication. Actual process-kill boundaries and failure
injection must precede crash-qualified readiness; do not use real model/assets.
Relevant regressions and independent code/architecture review before scoped
acceptance. Rotation/reservations/original resource history/global completeness,
source/runtime/asset/review authentication, native160 and neural experiment OPEN.
