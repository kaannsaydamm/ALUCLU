# Status/watch consumer evidence

Baseline e1e20dad6c4121ca3dfc1aeb432ecc1ef4c4ad5c; authoritative Desktop checkout.
Denial-only transport, NOT installed producer/launch readiness or learning PASS.
No model/Torch/CUDA/assets/held-out work was executed by these closed runners.

| Mode | Tests | Failures | Errors | Skips | JUnit seconds | Native exit |
| --- | --- | --- | --- | --- | --- | --- |
| red | 1 | 1 | 0 | 0 | .370 | 1 |
| green | 33 | 0 | 0 | 0 | 1.281 | 0 |
| green_v2 | 42 | 1 | 0 | 0 | 5.348 | 1 |
| green_v3 | 42 | 0 | 0 | 0 | 4.488 | 0 |
| regression_v3 | 143 | 0 | 0 | 0 | 9.702 | 0 |

All receipts active_processes=0, timed_out=false, original120s parent limit with
existing10s owned cleanup; all stderr empty. Outer legacy runner is not a capped
runtime capture claim. Final original session29593 terminal native0/root26948,
total_processes34, active0 confirmed personally. Selection42consumer+29livewatch+
25purewatch+47status=143. Earlier33 tests precede expansion, not final evidence.

RED demonstrates absent implementation. GREEN-v2 failure is retained verbatim:
generation native fixture was stopped before resume by shared watch timeout while
its synchronous producer could not service observations during store audit.
Correction uses a consumer-owning producer thread, same250ms observation bound,
original lease/watch deadlines and bounded producer join. No threshold relaxation
or production source change. Final two actual native trees (root+descendant) are
stopped by file revocation/generation changes; retained handles verify drain,
lease outputs close, reservation remains RUNNING/pending, unrelated child remains
alive until diagnostic cleanup. These are fake-pin temporary diagnostics, not
scientific admission. Existing timeout/revocation owned-watch tests also regress.

UTC values from time.time_ns in tests are synthetic transport, not validated
UTC uncertainty/clock mapping. Production advances supplied bound by monotonic
elapsed time under explicitly external at-most1:1 envelope prerequisite; actual
clock-domain evidence still absent. Path/pins/metadata do not authenticate origin.
Consumer success means queued response, not synchronous watch acceptance.

Residual uncovered deterministic branches: same-watch policy mutation, service
read ending before deadline but consume/submit crossing deadline, interruption/
submit failure, deliberately blocked read with eventual producer cleanup. Pure
input/sequence/expiry/anchor/overflow/rebinding and actual temporary file failures
are covered; no250ms latency/interruption guarantee, hostile-host/ABA or producer
shutdown proof. Standalone consume supplies typed denial transport only; actual
installed producer, operator updater/recovery, mandatory create/resume verifier,
history/clock/resources and real host qualification remain OPEN. Worker guard
unchanged and first actual learning unstarted. Full goal remains active.

## Exact raw and final source SHA256 (23 entries)

```
4a8d7a45e33494f44c7a24901a67d78e5e8bf4e27a7d1de93b6c659c1d6147bf src/aluclu/alc_r0/status_watch_consumer.py
52352810f14f3469e42c24237a183c149e74804dd607d3a58ebcd80a347dfe57 tests/test_alc_r0_status_watch_consumer.py
bf094d9cead1f05e63c8560e701215b667b7e15edf313fd0fd66ba938afb5a28 tests/alc_r0_status_watch_runner.py
ed119a7808261b0d30950b1f63f8d75f3ca7b58cd47ef3f87f33a533a5f2c209 results/alc_r0_status_watch_green_20261013.exit.json
e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855 results/alc_r0_status_watch_green_20261013.stderr.log
99a915c99a66698475c39c40568f595a870cd5a2051ba7dc42d749efa4e349f0 results/alc_r0_status_watch_green_20261013.stdout.log
114b243a3ddc7e300a7606942a9c6f0523ea2731ad66bff2667ed960607af017 results/alc_r0_status_watch_green_20261013.xml
6519cc343441f4cb6f2824fc6b7ad6acda22ba199072d1c8f43dc523eba7607b results/alc_r0_status_watch_green_v2_20261013.exit.json
e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855 results/alc_r0_status_watch_green_v2_20261013.stderr.log
bd2b59b8e8bb6ca296a928b2bc5047ca3252491de2800c31e487efaaf8e0e263 results/alc_r0_status_watch_green_v2_20261013.stdout.log
5610a3f79a34b39813a9c4a63b47d7c7405d80e95256d04d789eebcd4f51eafe results/alc_r0_status_watch_green_v2_20261013.xml
41abac7074f56f3299cba87729ac54a64fe3cf3a35bd585a4b496625d153ba1e results/alc_r0_status_watch_green_v3_20261013.exit.json
e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855 results/alc_r0_status_watch_green_v3_20261013.stderr.log
27d9c0eace019be83deacbd63a1387d7d9efd16b700968abfe1197325a35e654 results/alc_r0_status_watch_green_v3_20261013.stdout.log
a17ef182acd89332b5110421f94979a013bc495dfebeff4268431cd0e3476024 results/alc_r0_status_watch_green_v3_20261013.xml
69afd84f05035388b25b3ad3e93753b42333d4e6ff08278695c2ee2ac775bafa results/alc_r0_status_watch_red_20261013.exit.json
e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855 results/alc_r0_status_watch_red_20261013.stderr.log
cd8134d9e6f58067aec2e954cd72b4d4158c72d64dd007beed9ab9e350997892 results/alc_r0_status_watch_red_20261013.stdout.log
ece26e4948714bb1ecce2caf31f13e2a3e23c4be04ff5c1717e169290fffe757 results/alc_r0_status_watch_red_20261013.xml
ff5fe7b44fb97c9d5dd097e02f0575e997e73ab02a28734afcabebefb38809ad results/alc_r0_status_watch_regression_v3_20261013.exit.json
e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855 results/alc_r0_status_watch_regression_v3_20261013.stderr.log
f79f82d0b4f39812bc411a8e8ea564008a5180dad891c843f96959828707c5a3 results/alc_r0_status_watch_regression_v3_20261013.stdout.log
08e3e798f3cf946ea3308d5e2db5c9803ac98b76d3f6cc345a781f9d3e72a0c5 results/alc_r0_status_watch_regression_v3_20261013.xml
```

Independent architecture terminal CLEAR and separate code/security terminal
APPROVE each personally verified all23 hashes, fiveJUnit/native/log sets and
exact143 selection. Code lane also confirmed42final consumer identities match
GREEN-v3 and the unchanged worker-denial test is present in status regressions.
Combined approval is preservation of this denial-transport checkpoint ONLY.
Original code lane stuck pending_init was interrupted; clean-context GPT6.1 Sol
replacement performed the actual final review. No author fallback or scientific
gate closure. All documented timing/provenance/producer-lifetime limits remain.
