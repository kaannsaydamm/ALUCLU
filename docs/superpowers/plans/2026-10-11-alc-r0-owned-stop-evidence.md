# Owned-stop native evidence

Status: repaired implementation and retained final relevant regression independently
closed code APPROVE / architecture CLEAR. Scoped owned-stop checkpoint only.
Scope: harmless Windows processes and synthetic CPU reservations, not a model,
GPU workload, actual authority observer, qualification or learning experiment.

The admitted design is 2026-10-11-alc-r0-owned-stop-integration.md. Independent
GPT6.1Sol code APPROVE and architecture CLEAR admitted TDD, correcting the durable
journal list to include CREATED. Existing cleanup and resource thresholds were
not changed.

## Retained original evidence

Artifacts share `results/alc_r0_owned_stop_<mode>_20261011` and suffixes
`.stdout.log`, `.stderr.log`, `.xml`, `.exit.json`. The runner exclusively creates
files and uses the existing owned-job primitive, original300s diagnostic deadline
and ten-second cleanup. Wrapper exit0 is not pytest success; native receipt and
JUnit below decide it. No assets installed/downloaded.

| Mode | Tests/failures/errors/skips | JUnit seconds | Native exit | Root/total/active |
| --- | --- | --- | --- | --- |
| red | 1/1/0/0 | 0.290 | 1 | 25928/3/0 |
| green | 22/0/0/0 | 8.722 | 0 | 13716/28/0 |
| regression (before repair) | 264/0/0/0 | 70.880 | 0 | 5452/200/0 |
| red_v2 | 2/2/0/0 | 0.545 | 1 | 9464/4/0 |
| green_v2 | 24/0/0/0 | 13.535 | 0 | 28964/29/0 |
| regression_v2 | 266/0/0/0 | 66.362 | 0 | 25200/201/0 |

All six retained runs have timed_out=false and zero-byte stderr. RED is specifically missing
OwnedStopSignal, not a collection error. GREEN tests duplicate exact retained
root/private-job handles and query native terminal/zero-active accounting after
cleanup; the running case observes root+descendant and an unrelated survivor.
Journal remains pending, its last durable state unchanged; store lock can be read
from another thread. No PID discovery/kill or fabricated terminal receipts.

Initial source SHA256866a027a9c00eda696c7944f0a7baa26c9c8b7e10a1ecb1a89b9347d093b29ff;
tests3b881bfbecec083059b51bb580516c8e0f5abe591195f013adb0ba0258c5ccfc;
runnerbcd4d9dfb23cc44bca79038245ea5ac5536b67e53b6c6b3421d3eae685c09292.

RED hashes:
- exit ccb953318465764224c5097761a51d1f7b34757a1d2dacb2b049934d4d91536a
- stdout 87392853df947b0534b030821341ac9aef51a02b008f7e6d3f66f10da47a4953
- stderr e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855
- XML b07ce0b6f99b77c4b0d50ff217d2074946e22c1a68a072a8a42f8f63e98813d2

Initial GREEN hashes:
- exit f7efe559881eae74ce484b71770f965c18dfea9519f055c2107293678e5ab94a
- stdout 005660608b2669367e8019f3f36a0242baa6203f014ce6bff8ce1fa75bdb4ab1
- stderr e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855
- XML fc0733a4c984d33e17bab062256848620d0be6f9b50e83acf19596d8c08636ec

Pre-repair regression hashes:
- exit 59574e9af616945eccd0f8ed4515aec01e6faa572f03283cd4c98b59b2ceda48
- stdout f0d9799079a83c3e2708a41ab604a3a5a2623b24ed38efba743f357e17f837a4
- stderr e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855
- XML 83d76c9e9e94f037467e8a9b9cabf01f33e7677ac17900d88cc8ea62eacbda44

RED-v2 hashes:
- exit 66ef9aa07d86928588fbf624e7a0408d9efba7f37cc020969ffeec81ab149a54
- stdout b39c0b2849805950bdf67e0677fee1e9ef75c3bd9976ad8d79ecfcb5365b98ff
- stderr e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855
- XML 8266342a4cb0fc90a4cb3f45b7782d6f08551a73c5fa93e15b3333eeb1a918a0

GREEN-v2 hashes:
- exit 4259178d80159b7c5a7a0394a11be258e8867c89f5ceb44f4af549caa1f97d6e
- stdout 0e0bbc3cac0934d95d7baa3a804366277eddadd14bc132d353ff5eeb6414003d
- stderr e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855
- XML 26b37fee30d21ac110ccc336a8e2c5b1ca7c717450b9abf846bb42a62df38142

## Independent review, repair and remaining work

Architecture CLEAR for implementation; code REQUEST CHANGES: exact Event with
missing private _flag raises AttributeError rather than fixed OwnedStopRequested,
so the new absorbing denial latch is not set. Existing BaseException cleanup still
closes owned resources, but the promised error contract was incomplete. RED-v2
reproduced both missing-flag failures before/after acquisition on the old source.
Narrow repair catches only AttributeError from exact Event.is_set, converts to
fixed denial and uses the existing latch. No broad catch, extra callback or
cleanup modification. GREEN-v2 passed24; both independent lanes accepted the
repair, architecture also verified focused final artifacts. Every retained run
has empty stderr and no timeout. Original regression remains pre-repair evidence,
not final acceptance.

Final source SHA256 d0e519671a1ce20c42364b5d4445b596ee334ced31f5756ae4dc142149f6f61a;
tests ed53f9c5b300ac5270107e413172962fbff54ae08893a7cc6886b8383face23c;
runner f0535eda05aa6ea0331444b2b9e5f7d4f21a4ec7b31f9541e6cce60e2af9d601.

Final regression selects exactly stop tests plus existing reserved lease, bounded
output, reservation state/store, owned process, authority-watch policy and denied
worker tests. Final regression-v2 original session2157 terminal, native0/no timeout,
all201 owned processes terminal. Author personally parsed JUnit266/0/0/0 and empty
stderr, checked exact selection and unchanged three final pins. Exact counts:
stop24, reserved lease34, bounded output40, reservation state47/store33, owned
process33, authority-watch25, denied worker30 =266. This is relevant regression,
not a full repository suite, all-platform evidence or a scientific workload.

Final regression-v2 hashes:
- exit a83057bc852c7f02c8ec907b19070a64b9aba44a6695accca11111c5e93a0d9d
- stdout 7b20858d4bd9def7c58f9375df846c640db6168a711e4af8a0b3ead83db9c2c2
- stderr e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855
- XML 03d5ff0bfaa171e873bcf57cd5f46f58dbaee603d266f63c5df03c918bf4b81e

Checks remain linearized observations, not atomic revocation or measured20/520ms
enforcement. Trusted producer/observer/admission, final authority revalidation,
factual history/calendar/resource gates and actual scientific worker remain open.

Both independent GPT6.1Sol closing lanes hash-checked all24 retained files and
current final source/test/runner pins, reconciled the exact266 selection, and
accepted repaired native evidence. Their review uses retained artifacts, not the
author's original process-session handles. Only documentation status/wording
changed after closing review; no source/test/runner change or scientific launch.
