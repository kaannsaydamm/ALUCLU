# Scratch directory metadata diagnosis, preregistered v1

Base checkpoint8b36a533e1738918ba21e0f153c1dcfcbc3f3cfe. Actual_v5 refused
same-native size/allocation0->8192 at Lib/asyncio; warmprobev3 did not reproduce.
Original scientific model/grid/thresholds,300s oldtest/900s actual limits,
production14field exactequality and Task2acceptance stay unchanged.

Previous goal turn ended on a status question without executing a new test.
Current checkout clean; C: NTFS confirmed d2a173. Inspection suggests observer
ordering is worth isolating, not proven cache/OS cause. Primary API references:
https://learn.microsoft.com/en-us/windows/win32/api/winbase/nf-winbase-getfileinformationbyname
https://learn.microsoft.com/en-us/windows/win32/api/winbase/ns-winbase-file_standard_info
By-name returns metadata without returning a file handle; no source says the
observed fields can be dropped. New scratch tree may not model installed cold
state; a reproduction is mechanism evidence only, not proof of actual_v5 cause.

## Finite experiment before observation

Independent new tests-only diagnostic, no edits to previously pinned probe or
production. One parent-created exclusive resolved tempdir; child CWD only that
dir; child takes no caller path. Three exclusive children case-0/case-16/case-48,
with respectively0/16/48 fixed sample-NNN.bin files, each512bytes of x, total
32768logicalpayload bytes. No unlink, recursive cleanup, installedtree writes,
cache flush, external compute, model/tokenizer/dataset/GPU import or training.
Keep the bounded scratch directory and report absolute path as evidence.

After creating/filling each directory, no further application writes in that
case. Before any lstat/resolve/open/enum on the created directory itself, query
by-name104byte basic metadata first. Then lstat -> by-name; readattributes-only
handle standard24byte query class1 -> close -> by-name; boundedscandir ->
by-name; read each exactly512byte fixture -> close -> by-name. Raw named104byte
records plus decoded size/allocation/identity/times retained. Standard handle
opened backup+openreparse/share7 and closedfinally. Query functions fixed ABI,
system32 DLL loading; no fallback. Names must exactlymatch preregisteredfiles,
bounded48entries/4096namebytes, unexpected membership/content denied.

Closed --red/--green/--regression test modes and --scratch factual mode; internal
--owned-scratch takes no paths. One original60s ownedjobdeadline per invocation,
stdout65536/stderr4096 plus original10s cleanup; artifactcollision refusal,
fresh per-mode stems. Reuse the bounded ReservedOwnedLease with test-only owner
roots and synthetic journal (4MiB research/8MiB physical declaration envelopes,
not measured usage or scientific resource admission). Keep RUNNING state in
receipt; terminal is not automatic release. No training reservation/authority,
automatic rerun/deadline extension. Pytest modes select new13case contract suite;
regression additionally selects full existing native-directory and inventory
modules; record authoritative collected counts. RED expected unimplemented helpers,
GREEN implements isolated contract, REGRESSION verifies compatible prior scope.
Injected FakeAPI checks order/rawretention only, NOT native behavior evidence.
Actual native run only after focused/regression success and independent source
code/architecture review. Personally inspect ownedterminal/output/artifacthashes,
threecasephase records and any changedfields. Regardlessoftransition, no runtime
bindingPASS, modelreadiness, fixedDauthority or neuralcapabilityclaim follows.

The next remedy must address factual evidence with separate preregistration and
review; never normalize/ignore fields or count a warmed fullscan as causal fix.

## RED, GREEN and regression evidence

RED0e205e terminalnative1/root18056/total3/active0/notimeout, validcapture,
stdout13608/stderr0; JUnit13/13/0/0,0.764s, every failure NotImplementedError
scratchcreation (not collection/error/timeout). REDsource
24d9df26672751bc8fdb05928df00f7c824bae9cdc6110c6ec7c1c6997f5e12a.
Final diagnostic source43d4a211f35a2a3d20dc74c2bfccb8a99e483039759ea1f08a471f3a842e7e09;
testsaedabb280b489a36335d2d0062582a56244926b979eb288c4b1e05a8ec2010d9 unchanged.
GREEN6669fb native0/root29408/total3/active0/notimeout, validcapture81bytes/
stderr0; JUnit13/0/0/0,0.399s.
REGRESSION e88a97 originalsession84361 terminal6c4e34, native0/root25440/total71/
active0/notimeout, validcapture162bytes/stderr0; JUnit128/0/0/0,31.430s.
Mainff0e2c confirmed exactmodulecounts13new+42native+73tree. Sourcepins retained;
three productionmodules and previouscomparativeprobe unchanged. No old full345
claim is carried to changedtestbytes; this is fresh relevant128case evidence.
All synthetic receipts remain RUNNING, no automatic resource reconciliation.

```
5d508e090f0d4ee43401c8861897efd848f5a68c736720338ffce60f975221ff results/alc_r0_directory_reproducer_red_20261011.exit.json
e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855 results/alc_r0_directory_reproducer_red_20261011.stderr.log
0f093d42cce7ce69de33b882c370b07bf878e0c33612fc6b9a27194893d10c3a results/alc_r0_directory_reproducer_red_20261011.stdout.log
7c0082227376500d3c7c582d336f702685c8c0c1f8b1b73d9212f6944cf20094 results/alc_r0_directory_reproducer_red_20261011.xml
19a6ee682f62ec3f16b598e8473482797661156f140e5691b6486a6073a05710 results/alc_r0_directory_reproducer_green_20261011.exit.json
e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855 results/alc_r0_directory_reproducer_green_20261011.stderr.log
7fbe072bd6c74a7b0b55ddd2583fc288534b9dfe428b8a0f002c2ecdfb8dc490 results/alc_r0_directory_reproducer_green_20261011.stdout.log
3988b8fbc86e2abf1acdd09671c377d67a73ab06b137846797c0d7a05312812a results/alc_r0_directory_reproducer_green_20261011.xml
6931a91036e77057c4481cdc9cc431977b5d8bcecdd3f0ef8c012a153f98c772 results/alc_r0_directory_reproducer_regression_20261011.exit.json
e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855 results/alc_r0_directory_reproducer_regression_20261011.stderr.log
9b9da80ac596bcdd1b3bc2938847243be96fbbc0827798529c1e0e927d901bff results/alc_r0_directory_reproducer_regression_20261011.stdout.log
65fd1de6c83b560fea30534759ff55758e91c385f2033b3906d43fb70becf386 results/alc_r0_directory_reproducer_regression_20261011.xml
```

## Independent source readiness before factual invocation

GPT-6.1 Sol code APPROVE and architecture CLEAR for one --scratch conditional on
terminalregression/exactpins. Mainff0e2c personally verified terminal128casepass
and sourceunchanged before invoking. Both reviewed nativeABI/closedpath/caps/
claimlimits; neither ran tests/edited/spawned. Creation itself performs OS
operations, so first means firstdiagnosticobservation NOT untouched/cold state.
Primary ByName/HandleEx/Standard docs rechecked this turn; no fieldwaiver.
Proceed once serial; source/tests frozen until terminal, no installed/model/GPU.

## Scratch factual terminal: no transition in tested sequence

df5fb5 terminalnative0/root9296/total3/active0/notimeout, started_ns7736515000000/
finished_ns7737812000000 (1.297s). Validcompletecapture stdout11019bytes within
65536, stderr0 within4096, EOF/resourcesclosed and no failure/excess. Synthetic
reservation RUNNING asobserved, not release/admission. No XML expected for this
non-pytest mode. Retained exclusive scratchroot:
C:\Users\kaann\AppData\Local\Temp\alc-r0-directory-reproducer-82hm_bit

Main61add2 parsed exactcounts[0,16,48], payload512, logicalwritten32768; readbytes
respectively0/8192/24576. Across all five namedphases eachcase's14decodedfields
match firstquery exactly. All15rawrecords104bytes/208hexcharacters retained.
Case0size/allocation0; case16size/allocation4096; case48size/allocation16384;
eachlstat andstandardhandle sizes agree; standard directorytrue/links1 and
delete_pendingfalse. Native size/allocation0->8192 was NOT reproduced.

This excludes neither a cache/installedstate/OS mechanism nor an external actor.
It only shows that this finite sequence on freshlycreated small directories did
not produce a transition. Simple queryorder alone is not a sufficient explanation
from these testedcases. No actual_v5 cause/fix, directoryfieldundefined/irrelevant,
runtime bindingPASS, sciencePASS or trainingreadiness claim. No blind fullscan.
The diagnostic source/prod/probe pins remained unchanged throughout invocation;
C:48.96GiBfree afterterminal. New native evidence requires independent final
artifact review before preservation, not acceptance of installedcontinuity.

```
33192942f6c80d13f167a661e452807240cb05496c26ad1e12dc2af39e9c8af5 results/alc_r0_directory_reproducer_scratch_20261011.exit.json
e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855 results/alc_r0_directory_reproducer_scratch_20261011.stderr.log
f11258b9b1c65d02d91ac3db971285cce39a108efcaa998e849c98e65a5134e5 results/alc_r0_directory_reproducer_scratch_20261011.stdout.log
```

## Next candidate, not implemented or authorized by this result

Further primary-source investigation found Microsoft's historical explanation:
https://devblogs.microsoft.com/oldnewthing/20111226-00/?p=8813/
It describes NTFS directory-entry replicas for files and handle-close updates;
it is not specific documentation of current GetFileInformationByName class3
directory behavior. Hence it motivates, but does NOT establish, a held-handle
creation/population/close comparison on a fresh owned scratch directory. The
current experiment closes creation handles before the firstquery and tests
neither that variant nor earlier installedstate. Preregister finite held-handle
variant separately before observation; do not turn the old article into a cause
claim or permission to alter production equality. No held-handle experiment,
warmfullscan retry, production modification or training was performed here.

## Final independent evidence closure

GPT-6.1 Sol code APPROVE and architecture CLEAR for preserving this20file
checkpoint only. Both independently verified15artifacthashes, source/testpins,
128case exactcoverage, nativeprocess/outputfacts and claimlimits. No reviewlane
edits/tests/spawns. Production and priorprobe unchanged; continuity/cause OPEN.
Main2f43fd additionally decoded all15raw104byte records independently and checked
numeric fields/IDs against output. Code reviewer noted fullrawbytes need not be
identical despite14field equality. Main1bb668 confirmed only byteoffsets16/17
(LastAccessTime) differ for case0/48 afterenumeration and afterfilereads, not
size/allocation/otherretainedfields. Case0 access134362128810090490->
134362128810100490; case48 access134362128810657498->134362128810667505.
Case16fullraw unchanged. AccessTime was already outside production14field
comparison before this experiment; no new exclusion or waiver. Do not claim
whole104byte stability. Preserve evidence, then separately preregister heldhandle
variant; full scientific roadmap goal staysactive.
