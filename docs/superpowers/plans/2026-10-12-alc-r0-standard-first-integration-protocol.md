# Standard-first Windows directory observer integration protocol

Preregistered before implementation/results, baselinec025b36. The previous
two-target diagnostic is positive finite evidence, NOT whole-runtime acceptance.
Earlier0->8192negative records remain preserved. ALC-R0 science remains OPEN.

## Interface, acquisition and ownership

Keep DirectoryObservation and its exact14field continuity domain unchanged.
Keep runtime_tree_inventory canonical format, file hashing, all bounds and the
non-Windows route unchanged. Change only Windows observe_directory acquisition.
No dropped/zeroed sizes, allocation, device or timestamps; no retry/fallback,
fulltreewarmup, new model/data/GPU execution or threshold/grid/accounting change.

Use only documented synchronous Win32 calls in this production-library candidate;
do NOT copy native Nt query buffers or process-only fatal71 into the library.
Load existing by-name API DLL and kernel32 from System32 with exact prototypes,
use_last_error and reverse-order FreeLibrary. Explicit injectable adapter for
unit tests, never implicit process-global mutation or accepting launch verifier.
Open existing directory readattributes0x80/share7/flags0x02200000, noinheritance.
Always CloseHandle and release DLLs after failures, including original deadline
expiry. Cleanup is not skipped by pre-cleanup deadline checks. Failure to close
or release is an error, not silently swallowed. Partial load unwinds resources.

One public observation validates the same resolved/local/nonreparse bounded path,
then performs exactly this compound acquisition, without retry:

1. Open retained handle.
2. GetFileInformationByHandleEx class1 standard24 (BOOLsuccess, no returnedcount).
3. GetFileInformationByName class3 raw104, decoded full14 first record.
4. GetFileInformationByHandleEx class18 identity24 on retained handle.
5. Second class3 named104; require full14 equality with first.
6. Close retained handle.
7. Third class3 named104; require full14 equality with first, then return first.

Require standard allocation/EOF/link agreement with first named record, valid
directory1/deletepending0 and nonnegative sizes/nonzero links. Require handle
volume_serial/full128fileID agreement with firstnamed, reject zeroID. Exact
buffers24/104 and fixed ABI; do not invent bytes-written receipt. Failclosed
for malformed records, API failure, identity mismatch, named mutation or expiry.
Original deadline checks surround acquisition calls/decode; blocking calls still
require outer ReservedOwnedLease original useful deadline/cleanup boundary.

This is explicitly a DIFFERENT composition from the diagnostic: it corroborates
named metadata using Win32standard3+handleidentity2, not native68/device4/full13
cross-source parity. The existing production by-name14continuity domain is NOT
weakened; bookends and handle identity corroboration are added. No assertion of
Win32/native fullmetadata parity or underlyingdevice semantics. Device flags are
returned and compared exactly from named records, never volume substitutions.
No diagnosticresult is reused as proof of this candidate's native behavior.

## Threat model and evidence boundary

Compound sequential calls are not atomic, cold-state observation, authenticated
provenance or pathABA protection. Existing cooperating-host assumption remains.
Sharing flags do not enforce immutability. resolve/lstat already observes paths.
Identity correspondence catches observed mismatches, not hostile unobserved ABA.
No observing an unstable directory until it eventually passes: any mismatch in
one observation fails. No call to os._exit, pending NT query or fallback route.

## Verification order

TDD before implementation: standard24decoder/BOOL flaglayout/error, exact adapter
classes/prototypes/openflags, all14field mutations duringbothnamedbookends,
all3standard mismatches, volume/128ID mismatches, validzero facts, failclosed API
errors, deadlineexpiry/handleclose/libraryunwind and exactsequence tests.
Keep existing42native tests and73inventory tests. Use separately named bounded
owned test artifacts, stdout/stderr/exit/JUnit, no overwrites. Partition fixed
file sets prospectively if needed within existing60s/10s limits; missingXML or
timedout remains incomplete. Record final sourcepins and actualJUnit counts.

Independent GPT6.1Sol code/security and architecture source/design reviews are
required before real candidate installed-runtime testing. First finite installed
asyncio +owned16*512control observation/enum/reobservation, with full14 reporting
and raw adapter/unit proof; no old diagnostic result counted as new candidate.
Then real installed-base/venv continuity scan and negative-race regressions in
the existing original owned bounds. Read exact fullscan protocol before launch;
no fullscan authorization from this document alone. A failure is preserved and
diagnosed, not threshold-normalized. Fullenvironment acceptance, trustedproducer,
history/clock/resource reconciliation, D controls and science remain separate.

Before candidate native result, fix regression selection to two bounded modes:
regression-library-a = new65 + oldnative42 =107;
regression-library-b = runtimeinventory73. Disjoint union180, no deselection.
Architecture designreview requires releasefailure/remainingrelease and postopen
expiry ownership tests. Addthose before correcting code, retainnew REDv3 result.

## Regression execution amendment before native result

regression-library-b terminatedexit124 at its original60s deadline, noXML;
retain and do not treat50partialdots as complete cases. Fixed b1/b2 split uses
the original73 exact inventory node IDs retained in the previous initialized-b
JUnit, encoded as closed runner constants before new execution: first36 and
remaining37. Require complete107+36+37=180results with exactdisjointnodeunion;
no deselection/order-equivalence/whole-suitePASS claim. Same60s/10s/caps remain.

b2 also terminatedexit124/NOXML after13partialdots. Its37 exact nodes are fixed
into b21/b22/b23 slices of the same immutable73list: [36:46],[46:57],[57:73],
counts10/11/16. Keep36completedb1 and107completedA; require exact107+36+10+11+16
union180. Add pytest duration reporting for these fixed slices to distinguish
expensive process-heavy tests from a test failure; do not infer cause from dots.
Preserveboth timedout attempts; no wider deadline, hidden retry or field waiver.

## Primary references inspected before implementation

- https://learn.microsoft.com/en-us/windows/win32/api/fileapi/nf-fileapi-createfilew
  Directory handles require backup semantics; OPEN_EXISTING, sharing and reparse
  behavior are not snapshot or path-continuity guarantees.
- https://learn.microsoft.com/en-us/windows/win32/api/winbase/nf-winbase-getfileinformationbyhandleex
  Standardclass1/identityclass18, BOOLsuccess and no returnedbytecount; OS/driver
  behavior varies. Standard-first stability is an experimental claim, not API guarantee.
- https://learn.microsoft.com/en-us/windows/win32/api/winbase/ns-winbase-file_standard_info
  Signed64 sizes, DWORDlinks, one-byte BOOLEAN flags,24byte layout.
- https://learn.microsoft.com/en-us/windows/win32/api/winbase/ns-winbase-file_id_info
  VolumeSerialNumber/full128fileID identity pair,24byte layout.
