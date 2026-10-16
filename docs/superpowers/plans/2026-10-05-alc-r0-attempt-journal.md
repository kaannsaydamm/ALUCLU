# Checkpoint162 prospective durable attempt journal

Original R0 sections7.1 and12, checkpoint implementation D/E/F and checkpoint161
remain binding. This implements the journal's storage boundary first, not a new
experiment or the final ALC container. No actual model/data/GPU launch allowed.

Reuse existing cognition persistence path validation, process/thread file lock
and durable atomic creation; reuse R0 RFC8785 canonical JSON. Do not reset or
silently repair prior files. Constructor opens nothing. Explicit creation must
refuse an existing journal, including empty files.

Journal identity is a caller-bound canonical SHA256 root for its approved matrix/
contract. Empty journal has a domain-separated genesis digest. Each LF-terminated
canonical JSON record carries version1, journal identity, sequence, predecessor
digest and canonical object event. Returned frozen head includes count, byte size
and domain-separated SHA256 of last record (or genesis). Inputs/outputs use exact
canonical bytes; events remain generic at this layer, no state permission inferred.

Read/append requires an explicit expected head from an independent trusted owner;
verify the complete chain and exact expected head under an exclusive file lock.
Append compares then writes, flushes and fsyncs before returning its new head.
Concurrent writers with the same head: only one can succeed, other conflicts.
No automatic read-latest/retry, rewind, tail truncation or fsync-error success.
Cap event8KiB, record16KiB, journal32MiB/65536records before allocation/append.
Reject malformed/noncanonical/duplicate keys, blank or truncated lines, wrong
sequence/identity/hash, unsafe paths and nonregular/hardlinked files.

Threat boundary: trusted local root/cooperating writers. Existing path and sidecar
lock safety do not defend hostile directory replacement or privileged alteration.
Hash chain alone cannot detect whole-file rollback when its expected head is also
rolled back. Caller must durably bind a separately trusted monotone head; a crash
after record fsync but before head publication is an explicit uncertain outcome,
not permission to launch or rewrite. This component will not invent such a witness.
File fsync is required; platform durability is limited by the already implemented
atomic creation primitive/storage OS guarantees, not a universal hardware promise.

Subsequent journal semantics MUST implement declaration FK/unique matrix IDs,
INTENT->RUNNING->PREPARED->PASS/FAIL and INVALID/BLOCKED failure transitions,
one exact crash resume within the same attempt and only missing journaled work,
one reviewed implementation-repair rerun, a003 only for environment-invalid
resource retries, exactly one nonINVALID prepared candidate, prior failures kept,
all measured GPU/wall/storage consumption and outstanding exclusive reservations.
No launch readiness until those semantics, external head, historical accounting,
current source/runtime/asset authority and owned-process integration are verified.

Acceptance for storage: missing-module RED, restart readback, compare-and-append,
malformed/truncated/rollback negatives, explicit fsync-failure/no-return evidence,
two owned subprocess writers, independent code/security and architecture review,
relevant R0/persistence regressions. Storage PASS is not whole journal or learning.
