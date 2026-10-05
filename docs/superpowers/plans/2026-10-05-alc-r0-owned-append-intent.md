# Checkpoint169 owner-locked append integration contract

Parent49873d3. Existing publication CAS alone cannot recover intent lost between
page append and owner replacement. Before any page mutation, persist the complete
exact planned transition: previous owner bytes/root, candidate owner bytes/root,
canonical event, declaration, target page/index/identity, exact prior and next
journal heads, creation/rotation choice and review root. Caller independently
pins intent root; local discovery is not current-root authentication.

First prerequisite: journal162 must expose exact bounded append planning using
THE SAME record encoding and resource checks as actual append. Pure planner
accepts exact journal identity/head/canonical event; returns immutable exact line
and next head, no I/O/approval/receipt. Actual append validates disk predecessor,
writes/fsyncs this exact planned line and returns the SAME planned head. Never
duplicate a guessed record format in the transaction coordinator. Tests must
prove byte-for-byte parity and invalid inputs/boundaries before filesystem.

Integrated coordinator then holds owner lock BEFORE page lock through predecessor
check, all-page semantic preflight, durable intent, page create/append/rotation,
full166extension validation and167publication. No page mutation before durable
intent, no invalid semantic event appended, no scientific work launched by it.
Only bounded fixed-layout pages and intent records; original limits unchanged.
Rotating page must bind exact frozen predecessor head and preserve all events.

Explicit resume requires exact independently expected intent bytes/root, not
latest file search. Exact old owner + exact old target page: append intended
record once. Exact old owner + exact intended new target page: publish only,
never repeat append. New page absent/empty exact genesis can complete creation
under same owner lock. Exact candidate owner: identical167reconciliation only,
no additional event/generation/model work. Divergent/truncated/partial/extra/
malformed records reject without truncation, repair, adoption or retry loop.
Inventory and prior page heads must be checked before every recovery mutation.
An uncertain journal fsync needs explicit renewed durable acknowledgement, not
infer durability solely from visible bytes. Retain completed-intent evidence
within declared bounded growth; never silently delete failed research history.

Tests: exact planned byte/head parity, stale concurrent append, first-page/
same-page/rotation, invalid semantic event leaves all storage unchanged, same
owner lock blocks page writer during publication, competing one-event writers,
restart at durable intent/page create/append/fsync/owner-write boundaries, exact
completed idempotence, orphan/divergent intents and partial page failure. Actual
65536-record rotation boundary must preserve full work schedule, not shrink it.

Planner alone is NOT integrated coordinator or recovery. Implementation/review/
regression/crash controls required before integrated writer qualification. No
model/tokenizer/corpus/GPU/heldout/launch; original resource history/global matrix,
external monotone authority, native160 and neural experiment remain OPEN.
