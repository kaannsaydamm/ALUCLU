# Fixed-control sticky consumption publication

Parentcf7976356da99f4523956168fdddc300e8b1a660. Previous turnPROGRESS: acyclic
structural bindings47/319 accepted. This next component persists one-use exclusion
for the three fixed D controls in one pinned namespace, not operator authenticity,
reservation/admission, worker handoff or experiment execution.

`consume_control(directory, generation, request, installation_root, deadline_ns)`:
validate exact generation/request link and original deadline before filesystem
mutation. Directory must exist, absolute ordinary path/ancestors, no aliases,
symlinks/reparse. No directory initialization/latestdiscovery or installation from
request/CLI. Future concreteoperator pins same namespace across all installations;
moving/deleting it can defeat exclusion, excluded under cooperatinghost threatmodel.

Closed filenames `d-cpu-fresh1.consumed.json`, `d-gpu-fresh1.consumed.json`,
`d-gpu-fresh2.consumed.json`, selected ONLY by existingexactcontrol. Never generation,
requestroot or installationroot in filename: rotating any of those cannot restore
the same control's availability. No a002/resume or automatic rerun path.

Exact canonical consumed record <=4096bytes: schema, control_id, installation_root,
generation_root, request_root, reservation_id. Schema alc-r0-control-consumed-v1;
roots64lowerhex/closedcontrol/128charID. Return frozen ConsumptionRecord(data,root).
No accepting boolean/context. Read/validate bytes separately later, not inferred
from object construction. This records supplied structural evidence only; real
producer must authenticate all inputs and reserve before creating any child.

Publication order: exclusive-create fixed target with xb, creating a sticky claim
that blocks every competing writer immediately. Flush/fsync claim and close it;
then existing atomic_write_bytes replaces ONLY this caller-owned claim with full
validated record, fsync/write-through behavior reused unchanged. Same original
deadline and boundedrecord. Reobserve ordinary singlelink path and bytes after
publication before returning. Any existing path (complete/empty/truncated/corrupt,
directory/link) blocks; no parsing it into availability, no idempotent-success
replay. No cleanup unlinks consumption after error. If expiry/writefailure/crash
occurs after claim creation, claim remains consumed/uncertain forever until an
explicit separately reviewed owner recovery decision, never auto-retry.

The exclusive-create primitive serializes competing consumption; no new blocking
filelock introduced. Atomic replacement is by winner only under cooperatingwriters
assumption. Future operator->reservation->journal lockorder stillmandatory around
actualadmission/childcreate. This component introduces no different lockorder.
Atomic helper creates siblingtemporaryfiles; abrupt crash may retain them. Do not
purge uncertain outputs, scan unbounded directory or treat temps as release.
Powerloss/mediarollback protection is NOT newly established by process-crash tests.
Existing atomic helper may mkdir a disappearing parent: namespace-loss race is
explicitly excluded under this cooperating-host contract, not unconditionally
prevented. Consumption must prevalidate and reobserve the existing namespace;
no claim is ever deleted, helper cleanup of its OWN sibling temporary unchanged.
Independent design code APPROVE / architecture CLEAR requires actual separate-
process one-winner and fresh-process refusal after abrupt claim diagnostic.
Existing persistence guarantees remain platform/filesystem scoped.

`read_consumption(directory, control_id, deadline_ns)` single-read boundedfile
observation with own4096cap/4097sentinel, full path/open fingerprint and ancestors,
same reviewed Windowscross-sourceexception. Empty/partial/corrupt denies. Decode
exactstatuslexicalcaps/canonicalrecord andrequire pathcontrol matches. Reads do
not release/reopen/reset or establish installationorigin/durable oneuseperhuman.

TDD actualtempfiles: firstpublication/reopenbytes, duplicate and changedgeneration
or installationcannotreuse, threeindependentcontrols, empty/truncated/corrupt
preexistingclaimblocks, invalidrequest/deadline deniespremutation, wrongcontrol,
concurrentwriters exactlyonewinner. No global monkeypatch; explicitprivate writer
boundary may simulate failure after stickyclaim for testing, unavailable via public
API. Actual abruptchild test should leaveclaim andfreshprocessrefuse before
claimingprocess-crash exclusion; do not call ordinaryexception powerlossproof.
Exact originaltestprocess/output containment required. No model/GPU/science.

First accept persistence component with independentdesign/source/evidence review;
then publish actualownedchild binding under existingREADY lifetime before resume
and couple consumption to concretetrustedproducer. Those integrations and original
historyclock/resources/GPU2/qualification/learning gates remainOPEN. No guardchange.
