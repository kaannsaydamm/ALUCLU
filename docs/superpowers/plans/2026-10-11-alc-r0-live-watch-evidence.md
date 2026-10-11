# Live denial-watch runtime evidence

Status: implementation and retained final relevant regression independently closed
code APPROVE / architecture CLEAR. Scoped live denial-watch integration only.
Parent4548421110857c05164662988087531acfed9e00. Scope is real monitor threads and
harmless Windows children with synthetic reservations/observations, not a trusted
authority producer, installed handoff, actual qualification or learning experiment.

## Source and execution

The fixed loop composes existing advance_watch with the exact OwnedStopSignal.
It does not execute a producer, accept a callback, authenticate Observation values
or grant launch authority. Scientific worker remains unconditionally denied.
Constructor capture starts the original acquisition allowance. Real consumption
time preserves timeout precedence. Condition ownership serializes the one-request/
one-response slot; stale/duplicate inputs permanently deny. Closure retains the
earliest caller-supplied absolute cleanup deadline and signals before joining
outside Condition ownership. Signaling errors and late/unobserved termination do
not become successful closure. First terminal reason is absorbing.

Final source SHA25643c00718c773627ee2d5649b0e9a85cde3dc413c20938074edf75b1524316b16;
final tests b7f856d072739258611793298f48f6118ce86ff5a502049ebba5a74fedc3b97a;
final runner878bcb3bb7aef0179b701181f77db419a9c94a49e8db35e8c3eee22ddab734be.
Original27-test/runner pins were8021a25203b88af0d5c76bd7cdffb88150a8b388cb912c801cf324496e6b5bc7
and f35be3514660d9e93f2aa19e8ec7c347609f789fafc2d392a8075cb4ded7b7af.
Production source unchanged between both GREENs; no running-code/test edits before
original regression session75244 became terminal.

Existing research Windows CPython3.12 venv ran the closed owned runner with fixed
pytest selections, original300s diagnostic deadline and existing ten-second tail.
No installs/downloads or model/GPU execution. Exclusive file creation preserves
every run; wrapper exit0 never substitutes for native pytest exit/JUnit.

## Retained native results

Stems are results/alc_r0_live_watch_<mode>_20261011; each retains stdout.log,
stderr.log, exit.json and xml. All terminal rows below have no timeout and empty
stderr. RED is the intended missing module, not collection/error failure.

| Mode | Tests/failures/errors/skips | JUnit seconds | Native exit | Root/total/active |
| --- | --- | --- | --- | --- |
| red | 1/1/0/0 | 0.295 | 1 | 13160/3/0 |
| green | 27/0/0/0 | 2.932 | 0 | 20464/17/0 |
| regression (original tests) | 293/0/0/0 | 74.081 | 0 | 26704/215/0 |
| green_v2 | 29/0/0/0 | 3.582 | 0 | 13716/20/0 |
| regression_v2 | 295/0/0/0 | 72.313 | 0 | 7120/218/0 |

Focused fixtures exercise actual observation timeout, delayed start without
renewal, next request sequence, generation/clock/revocation/expiry/capture failures,
stale/duplicate/malformed responses, exact wait bounds, owner-thread lifecycle,
absorbing reason, signaling failure and deliberately delayed response consumption.
Added final fixtures demonstrate actual join timeout, eventual observed joined
thread with original deadline still expired on repeated close, and a fresh owned
Torch/Transformers import trap. Actual thread-start failure is handled in source
but NOT runtime-exercised; no claim otherwise. Transport is one-slot item-count
bounded, not a byte cap for arbitrarily malformed Python field objects.

Native timeout/revocation tests first observe actual root+descendant membership,
then run the real watch and lease wait. Duplicate exact retained root/private-job
handles prove terminal root/zero members; no PID discovery. Unrelated child stays
alive and reservation remains pending RUNNING. Monitor and producer thread join
use the lease's same pinned cleanup deadline, no new tail. This proves cooperating
fixture termination, not authenticated producer or scheduler worst-case latency.

## Artifact SHA256

Empty stderr in each run: e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855.

| Mode | Artifact | SHA256 |
| --- | --- | --- |
| red | exit | 15ce061011f648736e31226b03294eb58327f64b440ced0ea181f2f0af1394e1 |
| red | stdout | 8e4058b603f6e439929b1d8d0f7647680ac0af6bc6ef06a574b3d5b41dc8d8bb |
| red | XML | 30fc5a8a360c44b2f940992b29cd84080b8d7ea15fe3a89d6a3d68b6d8d05156 |
| green | exit | ca0a694371460234518507e7111f625cca37a0ec17dbd9f14bcbdebae27c73f0 |
| green | stdout | 18395083f2cb1e70edeb9bfc9b39da059cb217359d0fe9eaea01cc89e8d751d4 |
| green | XML | fc41db6636fd14d45964421cb92e4cf1200d97d4018de6e238c5a59ea3cd7485 |
| original regression | exit | a74c6ee374abc48be35c906e09790bb44d4fa99bdc4c6c4c40e167b13b42cdd4 |
| original regression | stdout | 81758c2cf1764103d4ad09b3176ff7f6c42d526c2549371bc13f66ab28e08e4f |
| original regression | XML | c955492b152b569b58f27e8c46fe8072f1285c319edccee480420a22cbc7c04d |
| green_v2 | exit | e190b73da7c4466ce92e9a6664fcf0ea1e8880a3c22a08e716753e503806ba6d |
| green_v2 | stdout | c2d871562b2fa0c02e95fde1458fcfd7ee7f58c9b51d93bfda0cbce141d2c2a5 |
| green_v2 | XML | 0b850f3318834ad971f44627b409da3d5248391c2449f624728d724068cf397c |
| regression_v2 | exit | 9a0239bad273a3d2ba4a0fef4cf1a050fa7902738a68f8c12bb6ac09106de4d2 |
| regression_v2 | stdout | 826ee42e8478ec08417e69209a6bfc0514a29e04c0f58d477f4021f5e14496fe |
| regression_v2 | XML | e2bcfa0f7c2220e55dbd3e9ecc04ea1c1dd594266e6fba7ea3caef64371d719e |

Final relevant regression-v2 original session71028 is terminal on unchanged final
pins. Author personally verified native exit0/root7120/job218total0active/no timeout,
JUnit295/0/0/0 72.313s and stderr0. Exact nine-file selection: live watch29 + stop24
+ reserved lease34 + bounded output40 + reservation state47/store33 + owned process33
+ authority-watch25 + denied worker30 =295. Original293-case evidence does not
substitute for this final strengthened-test regression. This is relevant regression,
not a full repository suite or broad portability evidence.

No trusted producer/provenance, precreation/preresume admission, measured520ms
guarantee, final authority verification, history/calendar/resource adoption,
GPU2/full fieldwise stability or scientific acceptance follows. Those remain
actual execution prerequisites, not silently waived by successful fixture tests.

Both independent GPT6.1Sol closing lanes hash-checked all20 retained artifacts,
parsed final native/JUnit evidence and exact295 selection, and checked unchanged
final source/test/runner pins. Their evidence is retained artifacts, not the
author's original process-session handles. Only status/trajectory documentation
changed after closing review; no code or test changes after final verified run.
