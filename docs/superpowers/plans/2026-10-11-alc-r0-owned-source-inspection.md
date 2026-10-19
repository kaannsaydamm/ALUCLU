# Owned source inspection before fixed D

Status: implemented; independent scoped code APPROVE / architecture CLEAR.
Final focused27/relevant regression213 verified; independent artifact closing
code APPROVE / architecture CLEAR. Parent a4a63e7.

The fixed D design forbids calling the existing unbounded source_checkout loop
in the unowned coordinator. Implement a concrete source-inspection callable for
execution INSIDE an already owned, deadline-enforced child, not a new scientific
launcher or accepting handoff. Preserve source_checkout's exact committed-blob,
mode, UTF-8 path and canonical inventory digest, clean-before/after and stable
HEAD checks. Existing freeze callers remain unchanged.

Inputs are an absolute resolved repository root, an absolute existing Git binary,
an explicit string environment, the original absolute monotonic deadline and
exact integer bounds: metadata bytes, file count, per-blob bytes, total blob
bytes. No callbacks or arbitrary command templates. Hard implementation ceilings
are 4 MiB metadata per Git command, 65,536 files, 512 MiB per blob, 8 GiB total
blob bytes; these are refusal limits, not scientific thresholds or evidence the
actual repository fits. Zero blob bytes is valid; metadata/count must be positive.

Use only the fixed read-only Git commands already used by source_checkout.
Capture bounded metadata before parsing; stream blob SHA-256 in at most 64 KiB
chunks, rejecting one byte beyond per-blob/aggregate allowance. Never retain a
whole blob. Stderr goes to the null device, not an uncapped pipe/file. Check the
same original deadline before spawn/read/parse and before returning evidence.
Fixed Git subprocesses are ordinary descendants of the owned inspector child.

Blocking OS pipe reads cannot be interrupted by a Python timestamp check. The
outer ReservedOwnedLease is therefore REQUIRED for time/descendant enforcement;
the callable alone is not a bounded launcher or authority. Native tests must
execute it in that real lease and verify timeout cleanup/zero owned members. No
public CLI, environment switch, self-asserted JSON permit or accepting scientific
worker is added. Cooperating trusted Git/repository assumptions remain; this is
not a malicious-Git sandbox or native-process RSS limit. Git's own memory peaks
and coordinator reservation/history/resource/producer admission remain open.

RED/GREEN: real tiny temporary Git repositories, oracle digest equality with the
existing inspector, changed commits/bytes, exact limits and one-byte overflow,
zero-length blobs, malformed bounds, dirty/index-hiding/root/submodule failures,
expired deadline. Owned native integration proves ordinary Git descendants are
in the job and terminal, and enforces the original timeout for a deliberately
blocking diagnostic child. No model/GPU/assets/training. Relevant regression
includes source_checkout, canonical, owned lease/output/stop/watch. Retain logs,
native receipt, JUnit and hashes; independent final code/design review required.

Implementation preserves the existing freeze inspector unchanged. Direct focused
tests exercise real Git's configured fsmonitor helper blocking during the new
inspector's status read: the outer lease terminates the entire private job. The
27-case GREEN-v3 passes after a retained failed-v2 Windows fixture permission
repair; final relevant regression and artifact verification are recorded in the
companion evidence. Concurrent HEAD mutation, malformed tree-path encodings and
explicit Git-handle close failures remain source-inspected, not directly injected
native tests. There is no measured native RSS bound or installed producer.
