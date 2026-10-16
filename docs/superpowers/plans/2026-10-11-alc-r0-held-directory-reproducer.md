# Held directory handle diagnostic v1, preregistered

Accepted prior scratch evidence44c080d709ce3eb72ef06b2d6c2b6762f3950bfc; no
transition on freshdirectories0/16/48files with creationhandlesclosed. Actualv5
installedLib/asyncio size/allocation0->8192 stillunexplained, not accepting.

Primary motivation, historical not currentAPI causalproof:
https://devblogs.microsoft.com/oldnewthing/20111226-00/?p=8813/
Discusses NTFS file directoryentry replicas/handleclosure; does not prove class3
directory semantics or causehere. Newvariant tests ONLY helddirectoryhandle
population/close, not every NTFSmechanism or installedstate.

## Fixed procedure before native observation

Reuse existing scratch diagnostic and boundedlease, no production/previousprobe
edits. Newclosed --red-held/--green-held/--regression-held/--held modes and unique
permode artifacts; internal --owned-held has no callerpath. Priorresultbytes
never overwritten, oldmode limits unchanged. Currentcode/testpins necessarily
change; old128resultnotclaimedcoverageofnewbytes. New9contractcases plus old13;
regression selects all22+42native+73tree=137 if currentcollection agrees.

One parentexclusive tempdir resolves before child; childCWD exactthatroot.
Three exclusive case-0/16/48 dirs. Open each emptydirectory readattributes/share7/
backup+openreparse; query empty_open. Write exactly0/16/48exclusive sample-NNN.bin
files each512xbytes (total32768logicalbytes), closing eachfilehandle. Keep original
directoryhandle OPEN throughoutpopulation. Query populated_open; same heldhandle
FILE_STANDARD_INFO class1/24bytes -> query after_held_standard. Close original
handle in finally -> query after_close. No newwrites afterpopulated_open. Then
reuse existing boundedinspect_case toverifyexactmembership/content and capture
fiveadditionalphases. Preserveall104byterawrecords/14decodedfields. Changes
empty_open->populated_open are expected consequencesof deliberatewrites, NOT a
continuity defect. The relevant comparison is populated_open->afterstandard->
afterclose (identity/metadata), then stable verificationphases. Do not label any
0->nonzero fromintentionalpopulation a reproductionof actualv5!

NativeAPI hold method is privatecontextmanager; exacthandleclosesfinally onquery/
writeerror. Existing standard(path) behaviorunchanged. Newtests injectfakehold
and assert ordering/rawretention/failurecleanup/noinvalidcountwrites; notnative
proof. TestRED first, GREEN then137regression under sameoriginal60s/10cleanup,
stdout65536/stderr4096. Native--held once ONLY after successfulterminalregression
and independent exactsource code/architecture review. No retry/deadlinerenewal.

Syntheticjournal4MiBresearch/8MiBphysical declarationsnotmeasuredbounds/admission,
RUNNINGstate notautomaticrelease. Actualscratchlogicalpayload32768B plus small
journal/evidence; retainedno deletion. No installedtree/fullscan/cacheflush,
model/tokenizer/dataset/importtorch/transformers/GPU/training or externalcompute.
No fieldequalitynormalization/tolerance/threshold/clock/budget/searchgrid changes.

Personally verifyprocess/outputterminal/hash/JUnitcounts, perphase/rawfields and
payload. Regardlessofoutcome cannotclaim actualv5cause/fix/runtimebindingPASS,
scientificcapability, launchpermission, nativeprovenance or trainingreadiness.
If transition observed, reproduce under another separatelyreviewedfinitevariant
before choosingproductionremedy. If absent, narrowthishypothesis only; do not
cycleblindfullscans. FullALUCLU/ALCroadmap remainsactive.

## Actual test evidence before native run

RED56eaec originalsession19816 terminalffe4e4: native1/root16224/total3/active0/
notimeout, validstdout10758/stderr0. JUnit22/9/0/0,3.449s: old13pass,new9fail,
8stubNotImplemented plus1expectedqueryerrorregexvsstub. All missinghelper, not
collection/dependencyerrors. REDsourceceea8223679e514519185d0beb59e8227e359ff7dfe2adffe8185d25dc3c5c6e.
GREENb6f748 originalsession88608 terminal1fbfa6 native0/root28428/total3/active0/
notimeout,validstdout81/stderr0; JUnit22/0/0/0,0.741s.
REGRESSION471d59 originalsession29674 terminal572e98 native0/root34252/total71/
active0/notimeout,validstdout162/stderr0; JUnit137/0/0/0,42.232s.
Main5141bd parsed exact22new+42native+73tree and verified unchangedfinalpins:
source dae91a80f33e69724ec70ebd05e15044ba2c538fd47ed6da8fc85fc043158c62,
tests932ee985e6619b62768f2ea2c9a837ff1fb951d700e0665a85c7cd7ea2d86a5f.
Source/testsfrozen throughoutregression; no nativeheldrun yet. All12hashes:

```
5c9c34a665e2ab841c1a71729e012819b3a31723473de65d2d3072f9b7db4ad4 results/alc_r0_directory_reproducer_red-held_20261011.exit.json
e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855 results/alc_r0_directory_reproducer_red-held_20261011.stderr.log
ed8618d9af2b750b6687a921c0d5636341eb0c5e072e53d2e0d2da0eb284849d results/alc_r0_directory_reproducer_red-held_20261011.stdout.log
83d900169d035f0eb9781a623429f53953c6d5a6399d961cfbb44bff5790aca5 results/alc_r0_directory_reproducer_red-held_20261011.xml
371d66a6fd0a2c4db5e9508c608adfa9abe21ff6be4fdab9f1ec0cef647f2c6e results/alc_r0_directory_reproducer_green-held_20261011.exit.json
e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855 results/alc_r0_directory_reproducer_green-held_20261011.stderr.log
005660608b2669367e8019f3f36a0242baa6203f014ce6bff8ce1fa75bdb4ab1 results/alc_r0_directory_reproducer_green-held_20261011.stdout.log
3e93481dfadc35132481509adf69664dd6fc3bd59b920d16c7c22245b7f2fa42 results/alc_r0_directory_reproducer_green-held_20261011.xml
11322778c382ea55043b27f866d9831eb8002542cb3ef74f3f4f3f80f4c90591 results/alc_r0_directory_reproducer_regression-held_20261011.exit.json
e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855 results/alc_r0_directory_reproducer_regression-held_20261011.stderr.log
509b05a96cc94338d19ec537e0f3bce707e0aee476f5fb4e51fae336c04346c8 results/alc_r0_directory_reproducer_regression-held_20261011.stdout.log
85270e3751a845f3d8f8f50e7b3859b5b4087b206542b69af325ff590b7fbfe9 results/alc_r0_directory_reproducer_regression-held_20261011.xml
```

## Independent exact-source readiness

Both GPT-6.1 Sol lanes codeAPPROVE/architectureCLEAR for onefinite--held
conditional on successfulterminalregression/exactpins. Main5141bd verified137
pass and exactsource/testpins afterterminal; no livejob before invocation. Native
cleanup/writefailure paths not comprehensivelyfaultinjected; fakefailurechecks
are notnativeproof. Only scratch mechanism observation, no installedcause/fix
or scientific/execution authority. Source/testsfrozen duringinvocation.

## Native held-handle terminal: no postpopulation transition

4e6441 terminalnative0/root23400/total3/active0/notimeout, started_ns9480171000000/
finished_ns9481187000000 (1.016s). Validcompletecapture stdout19050/65536,
stderr0/4096, EOF/resourcesclosed/noexcess/failure. Synthetic RUNNINGnotrelease.
Retainedscratchroot C:\Users\kaann\AppData\Local\Temp\alc-r0-directory-reproducer-1b6m076u.
Mainc6ce71 parsedcounts[0,16,48],512payload/32768logicalwritten/read0+8192+24576.
All27native104byterecords retained (4held+5verification percase).

Emptybaseline allsize/allocation0; afterintentionalpopulation case16=4096 and
case48=16384 (case0=0). Nonemptybaseline->population differs in size/allocation/
write/change ticks as expected deliberatewrites. NOT no-write reproduction.
From populated_open through afterheldstandard/afterclose and allfiveverification
phases, eachcase's14decodedfields equal exactly. Standard heldhandle matches
size/allocation0/4096/16384, directorytrue/links1/deletefalse. No claim whole104
bytes/accessTime equal. No postpopulationtransition in thisfinitevariant; no
proof of actualv5cause/fix, nativebindingPASS, trainingreadiness, production
waiver or scienceclaim. This narrows only the testedheldhandlehypothesis.

```
749d9e9cc60e900e42d6c8f9addded32e5f1210edb4f0003b339f945ec3b922b results/alc_r0_directory_reproducer_held_20261011.exit.json
e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855 results/alc_r0_directory_reproducer_held_20261011.stderr.log
4897b63448c491e476557c27a81a660421d5d54b2914cb37e830a4cfacc79691 results/alc_r0_directory_reproducer_held_20261011.stdout.log
```

Next investigation must improve representativeness/information gain rather
than arbitrary scratchcounts/repetitions or warmfullscan acceptance. Candidate:
explicit per-directory same-handle native observation contract retaining all
identity/timestamps/size/allocation/reparse/device facts, independently compared
with by-name on realinstalledtree under an owned read-only deadline. No candidate
implemented/accepted or invocation authorized here; inspect official ABI/source,
compare correctness/cost/complexity and preregister before changing production.

## Independent terminal preservation verdicts

Both existing GPT-6.1 Sol reviewers completed read-only terminal review:
`worker_close_code61`: APPROVE preservation only; `worker_close_arch61`: CLEAR
for evidence preservation only. Each independently verified all 15 artifact
hashes, both source/test pins, the exact 20-file delta, unchanged production and
prior-probe pins, JUnit counts, receipt/capture bounds, and native result claims.
They confirmed 27 retained 104-byte records and equality of the 14 decoded
fields after population, not equality of every raw byte or access time.

Neither found a blocking preservation defect. Neither verdict establishes
actual-v5 causality, installed-runtime continuity, a production repair, training
readiness, scientific acceptance, or authority for the next candidate. Synthetic
RUNNING remains neither resource release nor real admission. No reviewer ran
tests, probes, models, training, or spawned agents during terminal review.
