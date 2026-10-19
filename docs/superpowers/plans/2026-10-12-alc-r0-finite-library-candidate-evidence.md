# Finite public directory observer: candidate evidence

Date2026-10-12; baseline d0cda1a77a1b644477fee7675b7237817ee4a0f1.
Protocol: 2026-10-12-alc-r0-finite-library-candidate-protocol.md.
This is new evidence from the public production observer, not a reused result
from the preceding NativeAPI diagnostic. All earlier negative results remain.

## TDD / regression

Closed retained modes red-library-driver, green-library-driver and
regression-library-driver use the retained launcher basename date20261011,
which is not an execution-UTC assertion.

| Mode | tests/failures/errors/skipped | JUnit seconds | Native exit |
| --- | --- | ---: | ---: |
| red-library-driver | 43/43/0/0 | 0.610 | 1 |
| green-library-driver | 43/0/0/0 | 0.257 | 0 |
| regression-library-driver | 226/0/0/0 | 1.207 | 0 |

RED personally inspected before implementation: missing inspect_library.
Regression is43 new driver +65 library +118 retained diagnostic cases.
All receipts report active0/no timeout/valid capture, stderr empty.
Main d13079 verified JUnit, receipts and log hashes; source-review lanes each
returned code APPROVE / architecture CLEAR before one native invocation.

## Reviewed pins

```text
f4d9595758fc49edaa087914be36e816efbc389a47bd50bfc0618a169374ee31  tests/alc_r0_same_handle_directory.py
7ad9d46d8057b919ca73c64286c8973827b551b40e0e11e0146c88443034bd8a  tests/test_alc_r0_library_candidate_driver.py
175787d217e1a45b49a0154ca395fd4191a0c3e249abba62bf613a54f3ab399b  src/aluclu/alc_r0/windows_directory_metadata.py
```

## One real finite candidate invocation

Main a2e44b launched exactly one native-library invocation after both independent
source lanes cleared those pins and main revalidated them. Receipt: native exit0,
rootPID28872,totalprocesses3,active0,notimedout, valid3285stdout/0stderr.
Owned elapsed .610s. No native XML expected: this is a JSON diagnostic, not pytest.
Synthetic reservation records provide test containment only, not training authority.

The -I -B child explicitly imports this checkout src and invokes public
observe_directory exactly three times per target: before bounded enumeration,
after enumeration and once again. One shared45s inner deadline; unchanged60s
outer useful/10s cleanup,65536stdout/4096stderr. No separate metadata preflight,
warmup, retry or threshold waiver.

Target1: C:\Users\kaann\AppData\Roaming\uv\python\cpython-3.12.13-windows-x86_64-none\Lib\asyncio
- All3 full14 observations exactly identical.
- Size/allocation8192/8192, named device_characteristics256.
- Volume4343961586895537332, IDceea3900000001000000000000000000.
- Enumeration34names/414UTF8bytes.
- NamesSHA256 1d94fbe1058422e6266ee590981b600fd07eee8a8c86da7c2074d4f83a62243a.

Target2: C:\Users\kaann\AppData\Local\Temp\alc-r0-same-handle-r7b2tzev\control-16
- All3 full14 observations exactly identical.
- Size/allocation4096/4096, named device_characteristics256.
- Volume4343961586895537332, ID2edd0600000009000000000000000000.
- Enumeration16names/224UTF8bytes.
- NamesSHA256 45c73b0014d7fb47de43ccaf94e143cac48c566e1c04b2ab23ae9d79f7f32df9.

Main personally parsed native receipt/output, compared all14 fields in all3
samples per target, checked stdout/stderr receipt hashes, and read all16 owned
files to verify exactly512 bytes of x each (8192 total), not just the declared
logical count. Retained stdout carries every full14 value, not only these highlights.

## Claim limits / next gate

This supports finite continuity under this exact new public-observer procedure
on these two targets. Installed target was already observed in earlier experiments:
no cold-state proof, unique initialization cause, atomicity, hostile ABA resistance
or full-runtime PASS. Pure Win32 standard3 + handleidentity2 corroboration remains
different from previous native full13 comparison; no raw-ABI/parity claim is added
beyond the reviewed adapter/unit tests.

Real installed base/venv continuity scan, runtime binding, producer/history/clock/
resource reconciliation, D qualifications, E gates and neural pilot remain open.
No torch, transformers, model/tokenizer/dataset/heldout, CUDA or training execution.
Terminal evidence preservation review is pending at initial document creation;
record actual later verdicts in trajectory. Fullscan requires separate protocol
review and invocation, not authority inherited from this finite result.

## Raw SHA-256 manifest

All15 current original artifacts, including RED, are retained without rewriting.

```text
dff0d0e0791f57f2f616a297e998b4288e0ed487179337fb8decd27bd0d3cc27  results/alc_r0_same_handle_green-library-driver_20261011.exit.json
e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855  results/alc_r0_same_handle_green-library-driver_20261011.stderr.log
dd030096a7f9022af7d39cc5b0cee24bd30f0c0946575dc6169ffb144f64e010  results/alc_r0_same_handle_green-library-driver_20261011.stdout.log
a64b52abc483f0557a461f2776346737b1a135fd6570b76a50ab82dcd06432c9  results/alc_r0_same_handle_green-library-driver_20261011.xml
9797920a321a8f08d7b36dbd424cba3e783c5c1ac7c684c2e07bac207bd67049  results/alc_r0_same_handle_native-library_20261011.exit.json
e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855  results/alc_r0_same_handle_native-library_20261011.stderr.log
e64bfb321f779bb0e17cbbf7c61147ea4a8700015beeeed337662b65b474b70d  results/alc_r0_same_handle_native-library_20261011.stdout.log
eefed185de57f1835968410a3ef81394d7e7eb048c48e7cc65cc57998406309c  results/alc_r0_same_handle_red-library-driver_20261011.exit.json
e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855  results/alc_r0_same_handle_red-library-driver_20261011.stderr.log
957c95003242a60bc378a04facc465ac7a6ec9ace7a427ba60a956af0e09e505  results/alc_r0_same_handle_red-library-driver_20261011.stdout.log
16992271c4c0e03f5bd0f6a0f97c4975733a3f2495a7f07444bcc2956d4f3e1c  results/alc_r0_same_handle_red-library-driver_20261011.xml
7a8f3be8a176114209eef62d5d76f463061ed996294004b8fbfb558aef7ef294  results/alc_r0_same_handle_regression-library-driver_20261011.exit.json
e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855  results/alc_r0_same_handle_regression-library-driver_20261011.stderr.log
d9a6eb4461ee65c689e523e8c772d6f2e0b12b45040a8f960107216d1463a984  results/alc_r0_same_handle_regression-library-driver_20261011.stdout.log
339da01fca80c7014c6cb6292e8c40aef936beb7b464d79b4a32ba9218a92437  results/alc_r0_same_handle_regression-library-driver_20261011.xml
```
