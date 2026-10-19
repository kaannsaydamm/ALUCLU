# Same-handle native diagnostic: transition reproduced, no repair

Baseline4e510320907bfdbc026c91bdbea9e4d229d36303. Implements the previously
preregistered finite protocol, not production integration. No model/data/GPU/
training/full installed scan or installed payload read/write. Source/test frozen
through focused/regression/native invocation and personally rechecked:

```
bf23160f4fbd70d64102ca91b45af64345523722d577bd4ecd71e11834504c4e tests/alc_r0_same_handle_directory.py
f202fafb2229479f75908c4d08cc4c65083f83844c91310531770acbe506f1e8 tests/test_alc_r0_same_handle_directory.py
```

## RED/GREEN/regression before native invocation

| Run | JUnit tests/failures/errors/skips | seconds | native exit/root/total/active | timeout |
| --- | --- | --- | --- | --- |
| red-adapter | 46/15/0/0 | 1.242 | 1/23824/7/0 | false |
| green-adapter | 46/0/0/0 | .805 | 0/33236/7/0 | false |
| regression-adapter | 183/0/0/0 | 39.808 | 0/31988/75/0 | false |

Prior31 core tests passed in RED; new15 failed because adapter/sequence/
enumeration were stubs (one expected bodyfailure regex instead stub error).
Final exact selection46new+22scratch/held+42native metadata+73inventory=183.
Original regression session47903 reached terminal5f343d; main9bc309 parsed
JUnit and exact reviewed pins. Source code APPROVE and architecture CLEAR for
one finite native diagnostic conditional on this terminal success; main verified
conditions before invocation. Neither verdict admitted production or science.
Residual untested areas: comprehensive byte-cap/export/release fault injection,
genuine pending I/O, hostile path replacement, atomicity and ABA protection.

## Native result: same size transition on both routes

21dc99 terminal native0/root30864/total3/active0/notimeout. Started_ns10929031000000,
finished_ns10929890000000 (0.859 seconds). Valid complete capture stdout11776/
65536, stderr0/4096; EOF/resources closed, no excess/failure flags. Synthetic
RUNNING is not release/admission. No XML expected for the non-pytest diagnostic.
Python3.12.13 Windows AMD64. Raw samples retained; maine7b176/76a917 parsed:

Installed target C:\Users\kaann\AppData\Roaming\uv\python\cpython-3.12.13-windows-x86_64-none\Lib\asyncio
has unchanged 128-bit identity:
`ceea3900000001000000000000000000`, volume4343961586895537332.

| Installed route | Before enumeration | After enumeration | Final |
| --- | --- | --- | --- |
| handle size/allocation | 0/0 | 8192/8192 | 8192/8192 |
| by-name size/allocation | 0/0 (both pre-enumeration samples) | 8192/8192 | 8192/8192 |

Only size/allocation change within either route; other12 comparison fields,
including identity/write/change ticks, remain equal. Stat bookends inside each
handle sample agree. Both within-route stable flags are FALSE. Enumeration is
34 names /414 UTF-8 bytes, digest
1d94fbe1058422e6266ee590981b600fd07eee8a8c86da7c2074d4f83a62243a.
This reproduces the previously observed no-write size/allocation transition in
a finite representative diagnostic. It does NOT isolate enumeration as the
unique cause, exclude outside actors, establish disk mutation or prove NTFS
lazy materialization. Query timing/order and observation effects remain relevant.

Owned scratch control has16files512bytes=8192 total, retained at
C:\Users\kaann\AppData\Local\Temp\alc-r0-same-handle-4_0_qm5a\control-16.
All handle and by-name sizes/allocation remain4096/4096. Within-route stable flags
both TRUE. Enumeration16names/224bytes, digest
45c73b0014d7fb47de43ccaf94e143cac48c566e1c04b2ab23ae9d79f7f32df9.

IMPORTANT: all four matched pairs in BOTH cases differ in
device_characteristics: handle volume-query131104 (0x20020), by-name256 (0x100).
Other13 fields agree per matched pair. These may refer to different device-stack
semantics; equivalence is unproved. Do not substitute volume-query device flags
into the production by-name contract or mask/drop the difference.

Main dd4fe1 independently decoded all14 fields of20 observations (6initial
handle+6statbookend+8named) directly from raw offsets, without importing the
diagnostic decoder. Exact raw lengths/statuses/returned72/8 lengths checked;
scratch16files512bytes each verified. All native Nt completions were immediate
success; no actual STATUS_PENDING occurred. Full raw/access-time equality is
not claimed. Native exit0 means diagnostic completed, not continuity PASS.

Conclusion: the same-handle alternative ALONE is not a repair. Original-v5
cause/installed continuity/production/scientific acceptance remain OPEN. Next
investigation must explain observed directory-listing-associated metadata and
device-source semantics using primary sources/controlled protocol; do not warm
full-scan, zero/drop fields or change thresholds to obtain PASS.

## Independent terminal preservation synthesis

Code APPROVE / architecture CLEAR for evidence preservation only. Both existing
GPT-6.1 Sol lanes independently verified all15 hashes, final source/test pins,
JUnit/receipt facts and negative claim bounds; code also rechecked unchanged
production pins and raw/decoded consistency. Main735601 verified all15 documented
hashes and finalpins. Architecture explicitly BLOCKS interpreting the route as
a production repair. This does not block preserving the failed-remedy evidence.
No reviewer executed tests/native queries, edited files or spawned agents.
No independent lane approves production integration or scientific acceptance.

## Artifact SHA256 personally verified

```
56f1521d4f7cd97afb85bd96bf314f87d895b9e7c1c5c6ce59cb011340297afa results/alc_r0_same_handle_green-adapter_20261011.exit.json
e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855 results/alc_r0_same_handle_green-adapter_20261011.stderr.log
2c91283aa8beed85011506e4fae2d7a750df8428affa0bda3d2ab5775e8fe85a results/alc_r0_same_handle_green-adapter_20261011.stdout.log
d33df6ae67c492918bee91d8dd1ba964c62588c616c77c15ce27a5371d74fd72 results/alc_r0_same_handle_green-adapter_20261011.xml
6254fe64c280f1692d961ad9cdf294d10b79ea8cd53697274b154d9c221daa5b results/alc_r0_same_handle_native_20261011.exit.json
e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855 results/alc_r0_same_handle_native_20261011.stderr.log
450d69bd82dc2510f0c0bb81f77682b998f855face05508be6d2d5d231591c7e results/alc_r0_same_handle_native_20261011.stdout.log
292cd800ad7870d02dd941fb51673f87fba1859222526952d38c807cd1957baa results/alc_r0_same_handle_red-adapter_20261011.exit.json
e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855 results/alc_r0_same_handle_red-adapter_20261011.stderr.log
6712a4c610da3a7835d532213195fe8d1e5f0786f01f5baede662f2386223071 results/alc_r0_same_handle_red-adapter_20261011.stdout.log
8d496697f0d2f7057c50e8ef04898e16cbcb790f0c1cde4bf08ed36ac5c3b06f results/alc_r0_same_handle_red-adapter_20261011.xml
12a8538413b8dde27266ec9a660cd2bf516fc416a31f5543a30bb31d958113c8 results/alc_r0_same_handle_regression-adapter_20261011.exit.json
e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855 results/alc_r0_same_handle_regression-adapter_20261011.stderr.log
bcb034febe7b59565468f589b6aaa506f9e62dfdb191e51936184af913d73985 results/alc_r0_same_handle_regression-adapter_20261011.stdout.log
3566505242627a930b6bb4e6d2d5df6d886c0d8816524e3e61cee98a220fd654 results/alc_r0_same_handle_regression-adapter_20261011.xml
```
