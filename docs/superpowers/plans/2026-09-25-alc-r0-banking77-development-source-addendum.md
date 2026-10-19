# ALC-R0 Banking77 development-source parser addendum

Status: development-only parser clarification; **not** R0.0 authorization.

This note accompanies, but does not alter, the byte-frozen ALC-R0 source plan
(`SHA-256 0493eeed795dbf089babe54bc14204e30d82c7381c4b819afdf986c0baff6c9b`).
It was recorded after inspecting only the pinned `categories.json` and
`train.csv` from `PolyAI-LDN/task-specific-datasets` commit
`9d081458ff52e53cf7e848f414e6e9344e4e6696` and before accessing any
confirmatory split or training a model.

The source categories contain `Refund_not_showing_up` and
`reverted_card_payment?`. Every official-train CSV category must first match
one upstream category string exactly. Its canonical label is the ASCII
lowercase of that complete string. The terminal `?` is retained, not stripped
or replaced. Reject malformed category strings and any collision after
lowercasing. The category-file order is the canonical cross-label order.

Assign stable IDs by zero-based CSV data-row ordinal:
`train:<zero-padded eight-digit row ordinal>`. This is a source-row ID, not a
split-local rank, and remains unchanged when rows are deduplicated.

These rules make the section-4.1 normalized-utterance duplicate and hash split
unambiguous on the actual pinned development source. The earlier exploratory
raw-label roots in TRAJECTORY checkpoint 22 are superseded by the
canonical-label roots in the machine-readable development receipt. No source
bytes, acceptance threshold, seed, or held-out test content was changed. The
official test split remains outside the development directory and is not
acquired by this command.
