# Access-right intervention: open/query alone insufficient in this run

Baseline92ab202; preregistration directory-access-protocol.md preceded source and
results. Diagnostic-only; no production/model/data/GPU/training/full scan.
Frozen final source/test SHA256:
```
aad9e1d20aa024eb5179e88f9ae71a92be852d2353d68aaf5a80d36e4000e0f1 tests/alc_r0_same_handle_directory.py
2fd7aacb1fa6f654f48173e5b46a8166f27846f8929aade585d49bc557049e5f tests/test_alc_r0_same_handle_directory.py
```

## TDD and regression

| Run | JUnit tests/failures/errors/skips | seconds | native exit/root/total/active |
| --- | --- | --- | --- |
| red-access | 60/14/0/0 | 1.413 | 1/34108/7/0 |
| first green-access | 60/1/0/0 | .904 | 1/34220/7/0 |
| green-access-v2 | 60/0/0/0 | 1.050 | 0/33164/7/0 |
| regression-access-v2 | 197/0/0/0 | 31.158 | 0/24776/75/0 |

RED existing46pass; new14 failed missingaccess/stub, not collection. First
GREEN failure was an incorrect fake expectation: FakeAccess.changed also
activates inherited FakeSample.stat size4096->1. Implementation correctly
retained that difference. Corrected test asserts size difference AND final1;
production/acceptance unchanged. Failed GREEN retained, never overwritten.
Final exact regression60+22+42+73. Original70593 terminal922a7b.
Main4401e8 personally checked all four JUnit counts and all five receipt/log
hash pairs, valid capture/EOF/closed resources/no excess/failure/no timeout.
Source code APPROVE / architecture CLEAR for one finite invocation conditional
terminal197 and frozenpins, personally met before invocation. Architectural
confounds added before native result: open-stage also queries both handles,
so not pure opening-only evidence; fixed order/time/outside actors remain.

## Native observations

65a012 terminal exit0/root19068/total3/active0/no timeout. Start11716640000000,
finish11717281000000 =.641seconds. Valid complete26848stdout/65536, empty
stderr/4096; EOF/resourcesclosed, no excess/failure. SyntheticRUNNING remains
neither release nor admission. Main373f20 parsed full sequence:

Installed target:
C:\Users\kaann\AppData\Roaming\uv\python\cpython-3.12.13-windows-x86_64-none\Lib\asyncio
Identityceea3900000001000000000000000000; volume4343961586895537332.

| Stage | retained baseline size/allocation | second handle size/allocation | by-name size/allocation |
| --- | --- | --- | --- |
| before baseline open | n/a | n/a | 0/0 |
| baseline | 0/0 | n/a | 0/0 |
| attributes-open | 0/0 | 0/0 | 0/0 |
| attributes-closed | 0/0 | n/a | 0/0 |
| list-access-open | 0/0 | 0/0 | 0/0 |
| list-access-closed | 0/0 | n/a | 0/0 |
| enumerated | 8192/8192 | n/a | 8192/8192 |
| after baseline close | n/a | n/a | 8192/8192 |

All other12 fields remain equal within each route, including identity and
creation/write/change ticks. Baseline and named adjacent-difference lists only
change size/allocation at enumerated. NT returns immediate0/length72stat/8device;
stat bookends agree in compared fields. No genuine pending I/O occurred.

Scratch16files*512bytes root:
C:\Users\kaann\AppData\Local\Temp\alc-r0-same-handle-c0f5g55d\control-16
All stage/second/named size/allocation4096/4096, no adjacent differences.
Installed enumeration34names/414UTF8bytes, SHA256
1d94fbe1058422e6266ee590981b600fd07eee8a8c86da7c2074d4f83a62243a.
Scratch enumeration16names/224bytes, SHA256
45c73b0014d7fb47de43ccaf94e143cac48c566e1c04b2ab23ae9d79f7f32df9.

Device-characteristics mismatch remains throughout both targets:
retained/second handle volume-query131104 (0x20020), by-name256 (0x100).
No substitution, parity or mask. Main8a91f5 independently checked raw size/
allocation for all handle records AND bookends, raw identity/volume/device and
NT completion lengths, and named104-byte size/allocation/ID/device for all32
observations. Full decoded14 field differences personally compared; this is
not a claim of an independent raw reconstruction of every field this turn.

## Fixed interpretation

Opening and sampling another attributes-only handle did not trigger transition.
Opening and sampling a list-directory-access handle also did not trigger it.
Thus the list-access open/query sufficiency hypothesis is unsupported in this
tested sequence. Actual enumeration interval again contains the transition.
This is stronger discrimination than original order but NOT proof enumeration
is the unique cause, NTFS lazy initialization, disk mutation or absence of
outside writers/ABA. No observer-free/cold baseline. No repair/binding/science
PASS or training readiness. Production pins unchanged.

Next candidate: separately preregister a StandardInformation class5 query
intervention, or investigate enumeration initialization with primary evidence.
Do not infer a class5 result from class68 observations. A new query is itself
an observer and must preserve its failure/unsupported state. Existing output
and full14 continuity contract remain unchanged; no warmup/retry-to-PASS.

## Artifact SHA256

Independent terminal codeAPPROVE / architectureCLEAR for preservation ONLY.
Both existing GPT-6.1 Sol lanes verified19hashes/finalpins/fourJUnitreceiptpairs/
native sequence and conservative interpretation; no reviewer executed probes,
tests, edits or spawns. Mainf73af8 verified all19 documented hashes, scratch
count16/8192bytes/all512 and diffcheck. No production/training/science approval.

```
541cbc780017670ef1797cfa5a37e8d02f4670842b5ac132cecd008399f3a4f5 results/alc_r0_same_handle_green-access_20261011.exit.json
e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855 results/alc_r0_same_handle_green-access_20261011.stderr.log
f100adb74f7c0a0eea84d28399a12fcbd27079c474954cf467c037c978ab89a0 results/alc_r0_same_handle_green-access_20261011.stdout.log
f769211cfae73ed77d752654ad0fa1128a33fc6a8336276ae6e53bbb67e31fc3 results/alc_r0_same_handle_green-access_20261011.xml
98ad5976eac74e17c2f53db875a2e1bbb0ee912234245b88f9bb5d411ff9b4fd results/alc_r0_same_handle_green-access-v2_20261011.exit.json
e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855 results/alc_r0_same_handle_green-access-v2_20261011.stderr.log
199f701955786ef1c8109689487bcb6a74ebc4384a76e1ec71a64fa81edbebfe results/alc_r0_same_handle_green-access-v2_20261011.stdout.log
f85abfbf3c30771248dbd716306d8fb4564130747291db5282465924bed4b71f results/alc_r0_same_handle_green-access-v2_20261011.xml
2bbac0d9957a97d5597498f256699dcf77e353694caac84adb49a7a26161b597 results/alc_r0_same_handle_native-access_20261011.exit.json
e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855 results/alc_r0_same_handle_native-access_20261011.stderr.log
49c00223a1108f565ab03c009ab6e858349c0a715e15f4e4d59862e3c9024c8a results/alc_r0_same_handle_native-access_20261011.stdout.log
b448a0e2bef9f34bb48227bd3b588cc240c7b06c547159d7cccd42083eab155d results/alc_r0_same_handle_red-access_20261011.exit.json
e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855 results/alc_r0_same_handle_red-access_20261011.stderr.log
9cb76732f0e253059b3f8c65361d721a45c2bc4d9f8dfe80f140d164080a3b93 results/alc_r0_same_handle_red-access_20261011.stdout.log
c7009e2e254af4b40bf9adb8130aedc9f0cf86a04bbb2abb6bc0b993b826aabc results/alc_r0_same_handle_red-access_20261011.xml
9019b1f3806735f6380fc667f597e3e31992c9486285e7b26cf402ef566c2a7d results/alc_r0_same_handle_regression-access-v2_20261011.exit.json
e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855 results/alc_r0_same_handle_regression-access-v2_20261011.stderr.log
426e469a2611a3fb423bed334e18f1c8908e32773ebf0c886fa061e34e047983 results/alc_r0_same_handle_regression-access-v2_20261011.stdout.log
908bda854cc833602632478adf743320704df923934542c9935b9f421d836cbc results/alc_r0_same_handle_regression-access-v2_20261011.xml
```

