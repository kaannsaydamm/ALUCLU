# Acyclic generation/request/child binding

Parent98e7c5b7f4248c79cd1b5f46c928abbdeeacaf8d. Previous turn PROGRESS,
operatorstatus codec/read accepted47focused/286regression, worker stilldenied.
No installed operator, durable one-use consumer or launch is added by this step.

Concrete structural issue: request includes authority_generation_root. A generation
which includes full request_root while that field equals generation byte root
requires a cryptographic fixed point. A generation containing its future child
identity also cannot exist before child creation. Resolve prospectively with two
explicit records; do NOT alter the existing request wire schema or acceptance.

1. `request_binding_root(request)` validates exact DRequest bytes/root and hashes
   canonical {schema:alc-r0-generation-request-binding-v1, request:<exact decoded
   request minus authority_generation_root>}. Domain-separated projection includes
   ALL other fields. Exclusion is ONLY that self-referential field.
2. Generation record, <=4096 canonical bytes, exact fields: schema,
   installation_root, control_id, reservation_id, attempt_id, segment,
   request_binding_root. Schema alc-r0-operator-generation-v1; roots64lowerhex,
   control one of existingthreeD, reservationexisting128grammar, attempta001,
   segmentinitial. Frozen GenerationRecord(data,root). No child/request fullroot,
   PID or future READYownerroot. It is made before creation and rooted; request
   authority_generation_root is THEN assigned that generation.root and redecoded.
3. Child-binding record AFTER actual suspend/publication, <=4096 canonical bytes,
   exact fields: schema, generation_root, request_root, ready_owner_root,
   reservation_id, pid, creation_filetime_100ns, owner_nonce, identity_receipt_root.
   Schema alc-r0-operator-child-binding-v1. PID1..2^32-1, FILETIME1..2^64-1,
   canonicaldecimal strings, nonce32lowerhex, roots64lowerhex. Recompute original
   alc-r0-owned-child-v1 identityroot using reservation/PID/FILETIME/nonce.
   This separate binding does NOT change generation.root or request root.

`validate_generation_binding(generation, request, installation_root)` reparses
generation and request bytes/root, exacttypes, compares installation/control/ID/
projected binding and requestauthorityroot. `validate_child_binding(data,
generation,request,installation_root,identity,ready_owner_root)` first validates
generation then exact OwnedChildIdentity type/field bounds/recomputedroot, and
compares all record fields with separately supplied pinned inputs. Returns frozen
ChildBinding(data,root), observations only, not VerifiedLaunchContext/permit.
Pure validation, no IO/subprocess/scientificimports/callback or statusupdate.
Supplied immutable identities/roots are not authenticated process provenance;
actual producer must obtain them from ownedhandles/currentstore/installorigin.

Reuse status4096 lexical bounds (depth2/tokens64/rawstring256) and canonical parser;
identifiers fit these caps. Before numeric conversion enforce a common20-character
positive canonical decimal cap, then exact uint32 PID/uint64 FILETIME range. This
module has no signed64 record numeric field; a later addition needs its own range.
All unknown/missing/extra keys reject, malformed
dataclass bytes/root or type subclasses deny. No generic recursive serialization.

Future operator-owned one-use publication must pin childbinding root in its
durable control consumption record AFTER READY, BEFOREresume; workercorroborates
that record from fixedorigin. A valid binding alone cannot consume or prevent
replay. Future lock/recovery mechanism stillneedsconcreteTDD: operator->reservation
->journal, uncertainpublicationkeepsconsumed, statusgenerationunchanged, no retry
or generation rollover of alreadyconsumedcontrol. This step does NOT implement
that mechanism or claim child createdbeforedurablecontrolconsumption.

TDD synthetic bindings: create pre-root then request then separatechildbinding,
all3controls, every request field drift, modifiedauthorityroot, forgedrecordroots,
wrong installation/control/reservation/attempt/segment, every childfield drift,
PID/FILETIMEboundaries, identityrootmismatch, malformed canonicalcontent/types.
No actual child/model/GPU; pure fixtures cannot establish realhandoff. Relevant
status/wire/request/canonical/reservationidentity regressions. Existing worker
denial unchanged; independently reviewed source/evidence required for preservation.
