# Checkpoint166 append-only manifest extension prerequisite

Parent9ab3889. Current cognition key receipts bind encrypted-record lifecycle,
not R0 page manifests; do not silently reuse their anchor/recovery semantics.
Before a durable owner may publish/reconcile a candidate manifest, prove it
strictly extends its trusted prior manifest and preserves every earlier event.

verify_paged_extension(directory,spec,previous_manifest,previous_sha256,
candidate_manifest,candidate_sha256) validates BOTH canonical manifests and all
bounds before filesystem. Candidate has no fewer pages, strictly more events,
and every previously non-last page head unchanged. Previous last page may remain
unchanged or grow, never shrink in count/bytes. Its complete old count/byte/digest
head MUST equal the recomputed prefix head of the actual validated candidate
page. Page identity uses original journal162 domains/record format, declaration,
index/predecessor; no independent guessed hash format.

Reuse165 exact inventory/full locked candidate reads and164 private full semantic
replay. Recompute the prior-last prefix from canonical bytes validated by the
existing journal; all earlier frozen heads already match. Return only the final
immutable candidate view after every prefix/semantic/inventory check. No partial
state, file reset, repair or auto adoption. Both expected roots are caller claims
until bound by independent current owner/source/review authority.

No-op is not a strict extension. Future publisher must separately handle already
committed idempotent operations without inventing another generation. Initial
trusted empty manifest may extend to first nonempty candidate; it cannot prove
absence of earlier unrecorded jobs. Operational bounds/scientific matrix unchanged.

TDD same-page growth, append then rotate, frozen-prefix retention, fully valid
rewritten-prefix rejection, shrink/no-op/missing/extra/pre-I/O root failures,
semantic invalid tail and empty genesis. Two independent review lanes via
code-review skill and relevant regressions. No model/tokenizer/corpus/GPU.

This is a mandatory publication/reconciliation precondition, NOT the durable
publisher, fresh witness, rotating writer, reservation, historical accountant,
checkpoint restore or launch permit. Those remain OPEN; native160 also OPEN.
No dependency investment in final ALC container/serving and no learning PASS.
