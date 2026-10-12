# Standard-first production-library candidate: source and regression evidence

Date: 2026-10-12. Baseline: c025b36b4c5eacb38abb577d641c379d6fb4d8bb.
Protocol: 2026-10-12-alc-r0-standard-first-integration-protocol.md.

## Scope and implementation

The candidate changes only Windows directory acquisition. The immutable
DirectoryObservation full14 continuity domain, canonical inventory, file hashing,
bounds and non-Windows route are retained. Standard class1/24 corroborates three
size/link fields; retained-handle identity class18/24 corroborates volume/full128ID.
Three named class3/104 observations must agree exactly, including after handle close.
This differs from the earlier diagnostic's native full13 cross-source comparison:
that diagnostic's installed-target success is NOT evidence for this composition.
Device characteristics are retained exactly from named observations, not replaced
by volume-device values or normalized away.

Explicit adapter owns System32 DLL loads, reverse releases and handle cleanup,
including deadline expiry and partial acquisition failures. No NT pending buffers,
process-fatal exit, retry, warmup, relaxed bounds or field waiver were introduced.
Sequential calls are not atomic, hostile-host ABA protection or cold-state proof.
Blocking OS calls still require the outer owned process deadline.

## TDD and terminal results

Each mode below uses results/alc_r0_same_handle_{mode}_20261011 with stdout.log,
stderr.log and exit.json; xml exists only for complete pytest reports. The filename
date is a retained launcher label, not asserted execution UTC.

| Mode | JUnit tests/failures/errors/skipped | JUnit seconds | Native exit |
| --- | --- | ---: | ---: |
| red-library | 52/52/0/0 | 3.958 | 1 |
| red-library-v2 | 62/62/0/0 | 6.018 | 1 |
| green-library-v2 | 62/0/0/0 | 0.358 | 0 |
| red-library-v3 | 65/1/0/0 | 0.613 | 1 |
| green-library-v3 | 65/0/0/0 | 0.433 | 0 |
| regression-library-a | 107/0/0/0 | 2.213 | 0 |
| regression-library-b | NO XML; incomplete timeout | not available | 124 |
| regression-library-b1 | 36/0/0/0 | 2.600 | 0 |
| regression-library-b2 | NO XML; incomplete timeout | not available | 124 |
| regression-library-b21 | 10/0/0/0 | 27.969 | 0 |
| regression-library-b22 | 11/0/0/0 | 52.589 | 0 |
| regression-library-b23 | 16/0/0/0 | 7.346 | 0 |

Initial REDs expose missing implementation; v3 exposes explicit False release
failure being ignored. The fix rejects False while preserving normal None return
from _ctypes.FreeLibrary; ExitStack still attempts remaining releases.

All12 terminal receipts report active_processes=0 and output.valid=true.
Only original B and B2 report timed_out=true. All stderr logs are empty.
Main personally checked terminal receipts, JUnit fields and every receipt's
stdout/stderr file_sha256 against current disk bytes on 2026-10-12.

Final relevant regression evidence is A107+B1 36+B21 10+B22 11+B23 16 =
180 distinct passing test cases, zero failures/errors/skips. A contains65 new
contract/adapter cases and42 retained native metadata cases. The remaining73
inventory node IDs match the old retained initialized-b report exactly, with
closed prospectively recorded slices [0:36],[36:46],[46:57],[57:73].
No test was dropped. This does NOT establish ordering equivalence or turn either
original timed-out whole-file attempt into PASS. Fixed60s useful/10s cleanup,
65536 stdout/4096 stderr caps are unchanged.

Duration reports show several process-heavy fixture calls taking roughly3-8s.
They support aggregate time pressure as a possibility, not a uniquely proven
timeout cause or production performance claim.

## Frozen review pins (SHA-256)

```text
175787d217e1a45b49a0154ca395fd4191a0c3e249abba62bf613a54f3ab399b  src/aluclu/alc_r0/windows_directory_metadata.py
68aa3d7dce649d74e4926f62c072ff333e0f4ea9a1f1e503b45ae475a7a0fd79  tests/test_alc_r0_standard_first_observer.py
28a2f0440d895f0f4891a7569b025b4c73fb26471cf129722985fe908e900f23  tests/alc_r0_same_handle_directory.py
86a96a908076ab830e2a3719cc9bdd87fab5440c61f63221e68ad64839db271f  src/aluclu/alc_r0/python_runtime_binding.py
283be69ba005c108b2eaaae34b0574e7a27dd19b38aa31f026bb0cee93c6a667  src/aluclu/alc_r0/runtime_tree_inventory.py
```

Prior independent code APPROVE and architecture CLEAR concern source preservation,
conditional on final180 union and exact pins. They are not installed-runtime or
fullscan acceptance. Terminal evidence-document review is pending when this
document is first written; record actual later verdicts in TRAJECTORY.md.

## Remaining blocking work

No installed-target run of this new production composition or full installed
base/venv scan has been performed in this checkpoint. Required next step is a
separate closed, owned finite installed asyncio +16*512 scratch-control driver,
source/negative-test review and retained evidence before the real full scan.
No model, tokenizer, dataset, held-out, CUDA or training run is authorized or
claimed by these fixture/regression results. Trusted producer, historical
clock/resource reconciliation, D qualification, E gates and actual ALC-R0 neural
capability evaluation remain open. No Task2 re-opening or ALC-R0 PASS claim.

## Raw artifact manifest

All46 retained files, including RED and both incomplete timeouts, are first-class
evidence. SHA-256 was calculated from original current disk bytes, not rewritten
logs. Empty stderr files are intentionally included.

```text
0ba42e4eca1d6156afe88afb9c57b1688827b9d66b0523048a4e8ee385cda0ea  results/alc_r0_same_handle_green-library-v2_20261011.exit.json
e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855  results/alc_r0_same_handle_green-library-v2_20261011.stderr.log
80b733e3344a79564a96035746af9abc6a6667df35774e19c9cd0711760d70a1  results/alc_r0_same_handle_green-library-v2_20261011.stdout.log
d1d8bc00436032a037dd9b1a116a16e6b19aba87880915c292d93de7aab58d08  results/alc_r0_same_handle_green-library-v2_20261011.xml
64da93593d35ab6a444b9f73fc52c6917fa09f1a38850eba8b5af25a6995c202  results/alc_r0_same_handle_green-library-v3_20261011.exit.json
e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855  results/alc_r0_same_handle_green-library-v3_20261011.stderr.log
f7050369ca0ab035f64d38e10820bf42d148318d8b2c1f07ca16ad55a03cd0a4  results/alc_r0_same_handle_green-library-v3_20261011.stdout.log
74e0b913ba2790de76bc08f76851400a70bd606b8dca6bcebeae075b28ccf492  results/alc_r0_same_handle_green-library-v3_20261011.xml
fea635d784a6b07ff023ac978264f9d1cc95e83d32dc8212de38f4956f2895e8  results/alc_r0_same_handle_red-library_20261011.exit.json
e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855  results/alc_r0_same_handle_red-library_20261011.stderr.log
625db91e11db256d92380c6040066ecb32e012e45f812000a50537479f4ab999  results/alc_r0_same_handle_red-library_20261011.stdout.log
dbca7b22c2c6f80a3c178b9b94394d7f4e100010f5088bb572c837ab0f29b29e  results/alc_r0_same_handle_red-library_20261011.xml
4751cebf6422547cd31a2dcb5ebdc7ba5b671aecb0a52d89c2047d24e3bddd45  results/alc_r0_same_handle_red-library-v2_20261011.exit.json
e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855  results/alc_r0_same_handle_red-library-v2_20261011.stderr.log
796bfcb4c8d92cb46ed928fa14cb0ac4fb81dcc363dc264935c6f95a8bf4c387  results/alc_r0_same_handle_red-library-v2_20261011.stdout.log
354b5ff7604216f241935a31f6e1d4a3990692f6f885c485e88806cac81f2cb5  results/alc_r0_same_handle_red-library-v2_20261011.xml
9dffbbb60ea194d07dddc721b6eb9d96698311c9b70deeff73ede37b269f6ae1  results/alc_r0_same_handle_red-library-v3_20261011.exit.json
e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855  results/alc_r0_same_handle_red-library-v3_20261011.stderr.log
c4d736d0c88039c46ae55b4c563ee346b36cd3233d9f72eae033c352795a4967  results/alc_r0_same_handle_red-library-v3_20261011.stdout.log
bf1e77cdb629c2aa27f9d139181ee2fb0e53832e9572ea5af26329475d7ff303  results/alc_r0_same_handle_red-library-v3_20261011.xml
bfe65df6e30444c60b2f76cb3415f6de8f26347b1d453764080226538aeef5a1  results/alc_r0_same_handle_regression-library-a_20261011.exit.json
e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855  results/alc_r0_same_handle_regression-library-a_20261011.stderr.log
cbb3706472bc99cdb39412f0a4283dedb3c58b5b08466bb086b244352367a02e  results/alc_r0_same_handle_regression-library-a_20261011.stdout.log
79f004dd498ca099aa2d5ba537a29eac9386d41ed91feef090bd6b0ab2cba556  results/alc_r0_same_handle_regression-library-a_20261011.xml
16dac022c79c856401e620a6adf1714b4e482af3a1a0b9972fbfb3afe1ac05ce  results/alc_r0_same_handle_regression-library-b_20261011.exit.json
e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855  results/alc_r0_same_handle_regression-library-b_20261011.stderr.log
dd89800342a2addec342ca19569ffac89df7946b38145f98f63937b588fc1727  results/alc_r0_same_handle_regression-library-b_20261011.stdout.log
d51618fd8dcd4b5d68e6f05ee63fb199a1712339f7d77259fcf2dcc3f1beb98a  results/alc_r0_same_handle_regression-library-b1_20261011.exit.json
e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855  results/alc_r0_same_handle_regression-library-b1_20261011.stderr.log
369c47fbf4e04af873402a8568be38208bebabff8b6f81e2c7207438907bd4e4  results/alc_r0_same_handle_regression-library-b1_20261011.stdout.log
017e7344d723733f4d137b682b7c020458ad7fb4a4593d853d37abb779c64af4  results/alc_r0_same_handle_regression-library-b1_20261011.xml
432a1cfc2b53a5d190468556bc017ee44ea4d10b4026b5fad98e69db96590022  results/alc_r0_same_handle_regression-library-b2_20261011.exit.json
e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855  results/alc_r0_same_handle_regression-library-b2_20261011.stderr.log
1daed90b5518b44bf5d8add9b231fef90f7083e36bf6f679f988b5b00403e308  results/alc_r0_same_handle_regression-library-b2_20261011.stdout.log
22442fe152dced929091c4eb86dbc445830a53e1c2ddf1e27f35370cd351827c  results/alc_r0_same_handle_regression-library-b21_20261011.exit.json
e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855  results/alc_r0_same_handle_regression-library-b21_20261011.stderr.log
254b34ef7eb687b6bee9fd012858cc3174926b1f3dc7328cd5cb6c2c353f7472  results/alc_r0_same_handle_regression-library-b21_20261011.stdout.log
59ee5f2dbe8859d06a091835ff2bca48ef4f7eb4b23045a6d94bc0aab8e022a9  results/alc_r0_same_handle_regression-library-b21_20261011.xml
a3e19f98fcae1995ed395b64fe5982e531661de0b0e927feea2717e0bb5fead8  results/alc_r0_same_handle_regression-library-b22_20261011.exit.json
e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855  results/alc_r0_same_handle_regression-library-b22_20261011.stderr.log
e6d51f8cae8ca2bc52ac46e46932bafa17b6f30808d6699d4ce0098d28f9b4c4  results/alc_r0_same_handle_regression-library-b22_20261011.stdout.log
1aa649ae57f59602f894d0bf866e29e01fce84cbe42bfbec7c5b70d7b32712b7  results/alc_r0_same_handle_regression-library-b22_20261011.xml
6fd764a299103d970cb1309ff5f683e56344141b16c501bc9dbfabf111d105c2  results/alc_r0_same_handle_regression-library-b23_20261011.exit.json
e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855  results/alc_r0_same_handle_regression-library-b23_20261011.stderr.log
8e7ac12181ee3e8dcc418f44406d85277125e5e7927080b56e266c6294b33f3c  results/alc_r0_same_handle_regression-library-b23_20261011.stdout.log
446f3f300681e38b0a96e0cc4e76f9cb8e72603d4eae903ea7e779a56df9d235  results/alc_r0_same_handle_regression-library-b23_20261011.xml
```
