# Owned source inspection: native evidence

Status: final focused/regression verified; independent artifact closing code
APPROVE / architecture CLEAR.
Parent a4a63e7; Windows CPython 3.12 existing research venv. No model, GPU, asset
qualification, held-out access or training. This is a source inventory checkpoint,
not source provenance, producer admission or scientific launch readiness.

## Final exact pins

- src/aluclu/alc_r0/owned_source_inspection.py: `45e28961db8bc53646a2ebac3237720605eae3800f8a54f80135a286d22b4fd3`
- tests/test_alc_r0_owned_source_inspection.py: `4343afabc282f390863c674338709bfac0859aca275e9d14d33c910299321b31`
- tests/alc_r0_owned_source_test_runner.py: `59f5a2425bf3cead83ddf44119afa7d78748f8fa4e1df62b45c3e375bcb95d59`
- Frozen original scientific plan unchanged: `0493eeed795dbf089babe54bc14204e30d82c7381c4b819afdf986c0baff6c9b`.

Commands: the existing absolute research Python runs
`tests/alc_r0_owned_source_test_runner.py MODE`. Closed modes exclusively create
`results/alc_r0_owned_source_MODE_20261011.{stdout.log,stderr.log,exit.json,xml}`.
Each native pytest job has original entry +300s useful deadline and the existing
owned cleanup tail. No retries overwrite retained evidence. Wrapper exit0 alone
is not test success; pytest_exit_code and JUnit are inspected separately.

## Personally verified terminal runs

| Mode | tests/failures/errors/skips | JUnit seconds | native exit | root/total/active |
| --- | --- | --- | --- | --- |
| red | 1/1/0/0 | 1.378 | 1 | 22868/34/0 |
| green | 23/0/0/0 | 34.761 | 0 | 22608/446/0 |
| green_v2 | 27/1/0/0 | 40.433 | 1 | 23992/672/0 |
| green_v3 | 27/0/0/0 | 47.096 | 0 | 27624/687/0 |
| regression_v3 | 213/0/0/0 | 107.892 | 0 | 27352/1229/0 |

All five native receipts report timed_out=false and active_processes=0; every
stderr is empty. Process totals include real temporary-repository Git commands
and CPython redirectors, not model calls or test counts. Inside the successful
suite, the deliberate blocked-Git fixture separately requires timeout=true,
root124, zero job members and the fsmonitor-start marker.

RED failed for the intended absent module. Original GREEN predates strengthened
fixtures and is not final. GREEN-v2 failed BEFORE inspector invocation in the
new missing-object test: Windows Git loose objects are read-only, so unlink raised
PermissionError. This unsuccessful test is retained, not product rejection
coverage. After its original session was terminal, only the exact disposable blob
was made writable before removal. Assertions and production source unchanged.
Final GREEN-v3/regression-v3 include that repaired nonzero-Git test.

Final selection is exactly seven files: owned source27 + source checkout11 +
canonical48 + reserved owned lease34 + bounded output40 + owned stop24 + live
watch29 =213. This is a relevant regression, not the whole project suite.
Author inspected original sessions to terminal (GREEN-v3 15188/8b55c4;
regression-v3 71569/295aa7); personal 61e9bf parsed all five receipts/JUnit,
grouped exact selection, checked empty stderr and hashed all20 artifacts.

## Coverage and limits

Real owned temporary Git repositories show oracle digest equality, same tree
across commits, changed binary bytes, chunk/exact/one-over/zero-byte limits,
metadata/count/aggregate refusal, dirty/staged/untracked and hidden index flags,
wrong root, gitlink, nonzero Git exit and expired original deadline. Native lease
tests retain duplicate root/job handles and require terminal/zero members and
valid capped output before reading source evidence. The reservation remains
RUNNING/pending; observing terminal never silently releases accounting.

The real Git fsmonitor helper deliberately blocks the NEW inspector's status
read. Ordinary descendants stay in the private owned job and are drained by the
original outer lease deadline. Python timestamp checks alone do not interrupt
blocking pipe reads. No standalone time guarantee, native Git RSS cap, malicious
Git/configuration sandbox, authenticated source provenance, historical/resource
admission or installed production handoff is asserted. Concurrent HEAD mutation,
malformed tree-path encodings and direct handle-close failures are source-reviewed
but not directly fault-injected. Fixed scientific worker still denies execution.

Independent design/implementation/fixture-repair reviews returned GPT6.1Sol code
APPROVE and architecture CLEAR. Both closing lanes independently verified all20
artifacts, final pins, exact213 selection and honest failed-v2 preservation;
they inspected retained evidence rather than witnessing original native sessions.
Next dependency remains concrete trusted producer/inside-lease admission
and factual history/calendar/resource coverage before actual D/E/pilot execution.

## SHA-256 of retained evidence

Prefix `results/alc_r0_owned_source_`; each row names MODE_20261011.SUFFIX.

| Artifact | SHA-256 |
| --- | --- |
| red_20261011.stdout.log | 622fd4ffea386653ef3ee2b3dd4fef5e867acaa1996dd2d3b7b667348df3fde6 |
| red_20261011.stderr.log | e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855 |
| red_20261011.exit.json | bd85e3e4dfcceab36f58fdbc562ce310afbb4d3cde917bc222eadcc6e3e1cde8 |
| red_20261011.xml | 21b4826337cc29acc6d540c92a87e3773cb535c9f7a49745d4fbce1bfbeea2be |
| green_20261011.stdout.log | 99afb92fd1dc34b5f443be3336cef93d8411e74063dde213264485b100e2a9c8 |
| green_20261011.stderr.log | e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855 |
| green_20261011.exit.json | 3267c56466314bfcf835d6cb31fe3b1503fa0bf417ef4c76fe32e15070705a6a |
| green_20261011.xml | e754f14d3e639a6886d6e92b6c79468914998d0ad6b2e2f244f30abdd4b0e8de |
| green_v2_20261011.stdout.log | 61c55696f7d59c9eb952b42f6657a2ac975da041a6e90706611e0bedf362ac70 |
| green_v2_20261011.stderr.log | e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855 |
| green_v2_20261011.exit.json | 5c6e4f4db187ff7291999df1efa59c00a91af1bd6931d9dd5e827a1d94474501 |
| green_v2_20261011.xml | 4cf7acc897fcfac9174f83a64b5edde700709528e95ceec936fa00657c60ed69 |
| green_v3_20261011.stdout.log | 18395083f2cb1e70edeb9bfc9b39da059cb217359d0fe9eaea01cc89e8d751d4 |
| green_v3_20261011.stderr.log | e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855 |
| green_v3_20261011.exit.json | 168fc6f757e0b18b8e647f52c4917b81efbc50b318b4ea77b415290ec9611222 |
| green_v3_20261011.xml | 261bd847ed03052530c6feabd1f18a41b1245b694473c0588fcbc4120a0dddde |
| regression_v3_20261011.stdout.log | 57af5208e10d95a3356febddadbb2b2d31f02630b755fbb15e029e97d72d4d5e |
| regression_v3_20261011.stderr.log | e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855 |
| regression_v3_20261011.exit.json | 9e1dbf8eeed143315d896db4dcde996b1e67abd20db558835ec2f62d8e806ee7 |
| regression_v3_20261011.xml | 469b34b6e5a3f0e58201f4a8a0d1ea0279c7a1473a52fc3e9a3f2cd6b43dc59e |
