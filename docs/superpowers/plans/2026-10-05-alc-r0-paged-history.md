# Checkpoint165 manifest-bound per-run paged history

Parenteeaa037; original R0 rules and full matrix unchanged. Implement page reader
over existing journal162 and incremental replay164; not the final .alc container.
One immutable RunSpec per stream. Declaration root is domain-separated SHA256
of RFC8785 run_id/resource_run/ordered full work_ids. Page identity binds that
root, zero-based index and exact previous page head (null only for first page).

Canonical manifest <=8KiB, exact fields version1/spec_sha256/pages. pages is an
ordered list of exact count/byte_length/digest heads, nonempty pages only; empty
list is an UNSTARTED stream. Expected manifest SHA256 must come independently
from a trusted current monotone owner. Validate exact bytes/hash/schema/declaration
and all page/head/aggregate bounds before filesystem access. No read-latest,
automatic tail adoption, checkpoint cache import, truncation or orphan ignoring.

Trusted dedicated directory, fixed page-0000.jsonl... names; only those pages and
optional existing storage lock companions allowed. Validate inventory before/after
read, reject missing/extra pages and nonregular/hardlinked/link paths. Existing
journal read locks may create their normal lock companions. Feed ALL pages from
genesis into one private replay and return immutable snapshot only after every
head/chain/semantic check succeeds. Error yields no partial snapshot.

Caps8pages,32MiB/65536records per existing page,256MiB declared bytes and262144
events per stream; original65536work/run unchanged. Operational helper bounds,
not scientific thresholds: never omit work/retries or label cap denial scientific
FAIL. Full run inventory must fit/qualify before invocation; no all-matrix claim.

Threat boundary unchanged: trusted closed namespace, cooperating writers, no
concurrent page rotation or hostile TOCTOU. Matching a caller-supplied hash is
integrity relative to that hash, not freshness/authentication by itself. If both
manifest and external witness roll back, this reader cannot discover omitted
history. Durable owner publication/uncertain writes, writer rotation/reservations,
historical accounting, full matrix completeness, exact launch authority and
runtime160 remain OPEN. Source/review hashes are not artifact existence proofs.

RED/GREEN, cross-page restart/reference equality, wrong manifest/declaration,
missing/reordered/substituted/extra page, old/new head, corrupt framing, malformed
heads/bounds/JSON, invalid semantic tail/no partial result, empty stream, path
controls; independent two-lane review and relevant regression. No actual model,
tokenizer, task corpus, held-out data or GPU. No throughput/learning PASS claim.
