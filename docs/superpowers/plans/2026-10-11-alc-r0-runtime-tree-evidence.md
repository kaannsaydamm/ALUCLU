# Installed component inventory: diagnostic evidence

Parent d3a63ba. Scope: harmless temporary runtime-like file trees, inside owned
Windows jobs. No real installed runtime scan, model load, CUDA work or training.
This is not effective native closure, authenticated provenance or launch consent.

## Preserved attempts

Modes use results/alc_r0_runtime_tree_MODE_20261011 with stdout.log, stderr.log,
exit.json and XML. Native receipt is authoritative; wrapper status is not pytest.

| Mode | Tests/failures/errors/skips | JUnit seconds | pytest | Root/total/active |
| --- | --- | --- | --- | --- |
| red | 1/1/0/0 | 0.431 | 1 | 27128/3/0 |
| green | 28/7/0/0 | 16.203 | 1 | 30364/61/0 |
| red_v2 | 1/1/0/0 | 0.298 | 1 | 25632/3/0 |
| green_v2 | 29/1/0/0 | 25.122 | 1 | 25800/64/0 |
| green_v3 | 29/0/0/0 | 18.473 | 0 | 7916/67/0 |
| regression_v3 | 231/0/0/0 | 107.393 | 0 | 18272/867/0 |
| regression_v4 | 240/1/0/0 | 107.665 | 1 | 24200/867/0 |
| regression_v5 | 240/0/0/0 | 105.004 | 0 | 26404/867/0 |

RED was absent implementation. Initial GREEN found Windows DirEntry.stat lacks
full identity fields; RED-v2 directly reproduced that identity mismatch. Full
path lstat repaired it without dropping device/inode/link identity. GREEN-v2
then found renamed-file path/open-handle legacy ctime semantics differ on this
Python 3.12 host. Full path and full open-handle timestamps are now retained and
compared within their own observation source. Cross-source exception was
restricted to Windows after independent code review; v3 is not final evidence.
All above jobs drained to zero active owned processes and did not time out.

Final code-review APPROVE on platform-specific exception and8negative-field
fixtures plus simulated posix full-ctime equality. Simulated branch coverage is
not non-Windows portability evidence. Terminal v4 failed the existing live-watch
repeated-close test: after one close reported TimeoutError, later completion could
allow a successful repeated close. Retained as a lifecycle defect, not a passing
flaky test. The narrow repair latches observed closure failure while still joining
under the original minimum deadline. The reproducer asserts absorbing failure.
Runtime tests38/38 passed in v4. V5 personally verified terminal0, zero active
owned processes, no timeout, empty stderr and complete stdout. Exact7-file
selection: runtime38/source27/canonical48/lease34/output40/stop24/watch29=240.
Independent final GPT-6.1 Sol code/security APPROVE and architecture CLEAR verified
the exact final pins and v5 artifacts recorded here. No scientific admission follows.

Blocking filesystem calls depend on the outer original-deadline job. Metadata
continuity assumes a cooperating host; concurrent change-and-restore, blocked-FS
faults and effective import/DLL resolution are not established by these tests.
Hardlinks count per logical path, not physical bytes. All earlier failures stay.

## Personally verified XML SHA-256

- red: 2e6ab41e1f1e37f552a7c9d325071a810d6efa548ed2f2ff04fed3274b8964e7
- green: e732e1abff159a68b5db1eb7fd6463b8c4df5c9394b5f986e390dbb32c6a00d7
- red_v2: 5b14e8a81962d40f4839959e41920f5390d1fa7e9c9c9ec85deefbae1887b42d
- green_v2: b28d92300bf14477c0575eec06187b90231e25aa1c7de4762224f201b08c10d0
- green_v3: 6fab090393b9425ce95af3206eeed6a31c19682b9fa098b003e39c585000878c
- regression_v3: 22d31834e49546db4aee9951ed6ac73e9880d2350a5abc49507ea1592fc894cd
- regression_v4: f029ce58631bc06152ae9542704047b0e54b1d5e24c74bc27ca771b9e17ad461
- regression_v5: 109a4159f63f724884d493f4c79edeafdfbeb872b0768aa01a92d596a9a94679

Runtime implementation pins (unchanged in v5; runner v4 historical):

- source: da7d5e3367a855dc2d0bebce7043123d93e605fb73f6ed2786752adc524b33c7
- tests: 380a622e361a531af77f306bfc26e51d5630db854485c3fc21acb13ff696a9e9
- v4 runner: 3f038e0ea3a48ecd81f7999d638c768f08e178e7ee2079a51410e40e09d5db15
- final runner: 89ba2cb04992a63e25a1ddba36cc1edba241c32c176c751ae06dec3f73058fd5
- final watch: 9509c0a9378131f546e6c07574fc5b3945dacd75679d5f4f5cd60dd2da9bbc31
- final watch tests: 796279bcded0029502d69514ca1510e38440a9484d2611c8ef7fd3486914166b

All32 native artifacts have byte sizes and SHA-256 in
2026-10-11-alc-r0-runtime-tree-artifact-hashes.md. Every stderr is zero bytes.
