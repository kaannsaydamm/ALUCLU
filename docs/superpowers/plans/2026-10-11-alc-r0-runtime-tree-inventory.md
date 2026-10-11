# Bounded installed-runtime tree inventory

Status: scoped design, implementation and final-v5 artifacts APPROVE / CLEAR.
Parent d3a63ba.

Fixed D needs exact runtime bytes, not package version labels. No installed-file
inventory exists yet. Implement a read-only callable for use INSIDE the already
owned deadline-enforced child; do not add a launcher, accepting handoff or model
import. This is inventory evidence, NOT effective native-module closure,
provenance authentication, immutable runtime, resource admission or permission.

API: inspect_runtime_tree(root, component, deadline_ns, bounds). Component is
exactly python-base or python-venv, selected by the trusted later coordinator,
not a worker request. Root is an absolute resolved existing regular directory.
RuntimeTreeBounds has exact integer entry_count, path_bytes, file_bytes,
total_file_bytes. Hard refusal ceilings:65,536 nodes INCLUDING root/directories,
4MiB total relative UTF-8 path bytes,4GiB/file,16GiB logical file bytes. These
are implementation refusal bounds, not scientific thresholds, native RSS bounds,
physical storage observations or evidence the real runtime fits. Empty files
are valid; require at least one regular file in a runtime component.
Count/path budgets are positive; file/total byte budgets are nonnegative, all
exact integers excluding bool. Root counts as one node and has a separate retained
fingerprint; it is excluded from canonical relative-path rows and path-byte charge.
No empty or dot root sentinel is passed through the evidence-path validator.

Enumerate with scandir incrementally, refusing each count/path/size bound before
retaining another node or opening its content. Reject symlinks, Windows reparse
points/junctions and nonregular entries; validate normalized relative evidence
paths/casefold collisions. Bound directories as well as files, including empty
directories. Root identity is captured separately; directory nodes participate
in the canonical inventory. Do not materialize an unbounded list before checks.

Fingerprint each node using lstat mode/device/inode/size/mtime_ns/ctime_ns/nlink
and Windows attributes. Stream regular files in at most64KiB and at most remaining
allowance+1; hash exact bytes. Check retained path fingerprint against open-file
fstat before/after reading and lstat afterward; require read length==pinned size.
Windows-only timestamp amendment: compare all cross-source fingerprint fields except
legacy ctime, whose path/open-handle meanings differ on this CPython 3.12 host.
Retain full path ctime for path-before/after and both traversal comparisons;
retain full open-handle ctime for fstat-before/after continuity. Do not remove
device/inode/link-count identity or either source's timestamp continuity check.
Non-Windows cross-source comparisons retain full fingerprint equality.
Re-enumerate the complete bounded tree after hashing and require equal node/
root fingerprints. Use the same original deadline before every traversal/open/
read and before/after canonicalization and return. Every open file/scandir handle
must close on success and error. Blocking filesystem calls still require the
outer owned job; no timestamp check is called a standalone interruption bound.

Allow existing regular-file hardlinks (uv may use them); charge each logical path
against limits, never infer physical-byte ownership or immutability from these
counts. File/link metadata is diagnostic continuity, not adversarial race proof.
Cooperating local filesystem/runtime ownership is assumed; this is NOT a sandbox
against a hostile tree mutating between path validation and open, or an attacker
restoring metadata. No network filesystem, import path or DLL resolution safety
claim follows from a successful digest.

Sort rows by UTF-8 relative path. Hash RFC8785 rows with exact keys path/kind/
byte_length/sha256; kind is directory/file, directories have0/null. Result binds
component, absolute root, inventory SHA256, entry_count (root included), file_count
and logical_file_bytes. Paths and bytes both participate; node metadata is not
silently substituted for content hashing. The actual future runtime root must
also bind exact Python image/redirector, import paths/settings, Git executable,
OS/driver/native DLL identities and independent reviewed pins; these are NOT
claimed by this per-component inventory. No current installed runtime is certified.

TDD with harmless owned temporary trees: independent canonical byte oracle,
stable inventory, changed bytes/path/empty directory, multi-chunk/zero files,
count/path/per-file/aggregate exact and overflow bounds, invalid bounds/component/
root/deadline, hardlink semantics, symlink/junction rejection, no heavy imports.
Use actual ReservedOwnedLease root/job handles and capped outputs; retain pending
reservation and zero-member terminal proof. Concurrent mutation and blocked-FS
fault coverage must be honest (source inspection is not runtime injection).
Relevant regression includes canonical, owned source, lease/output/stop/watch.
No model/GPU/assets/install/real runtime scan or scientific execution in tests.
