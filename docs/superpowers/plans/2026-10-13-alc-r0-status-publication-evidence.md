# Current operator status transaction evidence

Baseline a5ac3b620a441ed1a46c96bd8b22979eb484fd69, authoritative Desktop.
Single-generation current transaction ONLY, not installed operator provenance,
archived history, generation rotation, restart freshness, producer/launcher or
scientific authority. No real operator namespace/model/CUDA/assets/held-out work.

| Mode | Tests | Failures | Errors | Skips | JUnit seconds | Native exit |
| --- | --- | --- | --- | --- | --- | --- |
| red | 1 | 1 | 0 | 0 | 0.256 | 1 |
| green | 19 | 0 | 0 | 0 | 2.815 | 0 |
| red_late | 1 | 1 | 0 | 0 | 1.636 | 1 |
| green_v2 | 26 | 0 | 0 | 0 | 5.869 | 0 |
| regression_v2 | 122 | 0 | 0 | 0 | 10.524 | 0 |
| green_v3 | 47 | 0 | 0 | 0 | 7.342 | 0 |
| regression_v3 | 143 | 0 | 0 | 0 | 15.564 | 0 |

Every native receipt active0/notimeout, original120s parent bound +existing10s
cleanup; stderr empty. Outer legacy runner is not runtime-stream capped.
Final original session71222 terminal5ac272: native0/root6948/total66/active0.
Final selection47publication+47status+32deadline+17consumption=143. Earlier
19-case GREEN predates source return correction;26/122 predates expanded tests.
They are predecessors, not final replacement evidence. Focused47 final identities
must match their final regression counterparts exactly.

RED absentmodule is retained. red_late is a genuine source defect reproducer:
fresh isolated child delays native unlock past original deadline; old code
returned success afterward. Main read the inner diagnostic stderr and verified
the explicit assertion 'publication success returned after original deadline'.
Outer JUnit records the childexit1 assertion, not full inner stderr; that inner
temporary log is not separately promoted as committed raw evidence. Fixed
publish/recover perform originaldeadline check AFTER context cleanup before
return. Both late-publication/recovery child cases pass in final suite; published
candidate may already exist when late API return denies. Preserved evidence is
not necessarily a pending on-disk transaction; no automatic recovery/rollback.

Actual subprocess crash at full-intent/readback-before-status (initial/update)
exits17, ownedactive0; fresh public committed-reader child exits18. Parent uses
its independently constructed exact intent, forward-recovers, idempotently
verifies same candidate; no latest-file discovery or attempt restart. Two native
writers with same predecessor yield one0/one18. No power-loss or all-cut proof.
Public negatives cover wrong store pins, malformed/oversize/hardlink/empty intent
reader/recovery, changed pinned intent, missing update slot, third slot state,
unsafe/missing/file/relative/junction namespaces, forged metadata and bounds.

Mixed-read fixture is a fresh isolated child audit scheduling actual normal
sequence2 publication at the SECOND intent-file open (after pre-open metadata
observation). Outer reader denies, fresh committed reader returns sequence2.
Denial may happen at open/path identity continuity before final intent equality;
do not claim each internal join branch or every race ordering is exercised.
No parent monkeypatch or production callback. Diagnostic private step override
for crash is not authenticated producer implementation.

Initialization claim remains after error; raw status reader intentionally still
exists as diagnostic observation and MUST NOT be installed producer's path.
Next mandatory connection: committed reader -> live watch -> actual owned pending
publication cancellation. Full fixed source installation, generation rotation/
terminal one-use ownership, operator-before-reservation composition, producer
lifetime and create/resume verifier remain open, alongside history/clock/resources
and exact real qualifications. Worker guard unchanged, first learning unstarted.
Limits: cooperating persistent namespace, atomic helper may recreate lostparents;
no hostile ABA/directory rollback/history proof, OS-call interruption or250ms
latency guarantee, all publication/flush/unlink-fault branches, POSIX portability
or scientific readiness. Returned status is a point-in-time committed transport
observation, not continued authority or latestness after operator unlock.

## Exact raw and final source SHA256 (32 entries)

```
923f4a82cd8be9b9cf9ab5f1d5ca029d5f160f91238e10a31b41a583d1f7e9ea src/aluclu/alc_r0/status_publication.py
f74b876ebfb54a1703949808289c45a6cbc93dbb49dc04d75c13dbfa45635556 tests/test_alc_r0_status_publication.py
40a0cd0a7e0fcfd5b4c317d7c9631e1d7838b28206096ac561da89290b6054e1 tests/alc_r0_status_publication_child.py
07a285f084df0aaa37c65767c7d5af0704f25f473529290301a39baab96c6919 tests/alc_r0_status_publication_runner.py
a5434bf705c10d0a46643b654a1f482a8f857c34e222370d602994a64cca7a1e results/alc_r0_status_publication_green_20261013.exit.json
e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855 results/alc_r0_status_publication_green_20261013.stderr.log
dda0df2a5159d1af76b6e0acce4b10db8872d11cd8f72f1ac9177341e2a17886 results/alc_r0_status_publication_green_20261013.stdout.log
bacc09b2c2bf2924a6b69db490ea20d3c5c3eedac45ac75d14ca1e420772b635 results/alc_r0_status_publication_green_20261013.xml
1e9530c7e8fd41c8f255f2a7d615783d14f57905a3f235014e94e9396d46cd04 results/alc_r0_status_publication_green_v2_20261013.exit.json
e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855 results/alc_r0_status_publication_green_v2_20261013.stderr.log
f7e4ad4ed6eadbcec67657213fec22042823489962bbfdfa48122921f037ce8b results/alc_r0_status_publication_green_v2_20261013.stdout.log
87a37a7cb2ecba5b61a9653ecccd7e0b83010d70ec6bb8c38738bcb6c2c122c0 results/alc_r0_status_publication_green_v2_20261013.xml
ac1703da124edf75aca675e75709dcbae3bd25545682b5db42d6a1fab97f05ce results/alc_r0_status_publication_green_v3_20261013.exit.json
e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855 results/alc_r0_status_publication_green_v3_20261013.stderr.log
647689a0c3ea3cace805553d723f6251f68c9740d7ca6a5c1685fae9336ae09d results/alc_r0_status_publication_green_v3_20261013.stdout.log
6083b8eadbdc562848116bf68d5b6fe9ff526c38b76a5e021c27efc6cbc39401 results/alc_r0_status_publication_green_v3_20261013.xml
bdfc86a601c51ac4adcf870936c09f9960c5d99dd5c3bdbe20e4e06cb6c496ea results/alc_r0_status_publication_red_20261013.exit.json
e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855 results/alc_r0_status_publication_red_20261013.stderr.log
cb69ec33d5f864d217673bdf5903e57b054b020966612bb1b8c5fef18a246a61 results/alc_r0_status_publication_red_20261013.stdout.log
36d0325aba37bfc543691e3cc695ab30dc014859f72f070564c784984e793f37 results/alc_r0_status_publication_red_20261013.xml
32948d5065d34dfcfd855502540d797a4acf3a8eef01dd9acdd1942b8d26c15d results/alc_r0_status_publication_red_late_20261013.exit.json
e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855 results/alc_r0_status_publication_red_late_20261013.stderr.log
7a2bdfdf037791c2be5a54c4195d5c2c4af77f870cd88b36fa32ae00863b0e3e results/alc_r0_status_publication_red_late_20261013.stdout.log
899caf208a73571356e4b4e61fdb11bee8d60c953cf083b2ecf84b172bea9c55 results/alc_r0_status_publication_red_late_20261013.xml
86090a9b9b7b2d925ea0e7bfa7a2adbbd8a9e23dcedd926e82a38fe512f42888 results/alc_r0_status_publication_regression_v2_20261013.exit.json
e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855 results/alc_r0_status_publication_regression_v2_20261013.stderr.log
eb3ef57a1d6d1b0c2bc42c3edc0f3fb7dc6ac7a3e826510d35dfb75bd9d2379b results/alc_r0_status_publication_regression_v2_20261013.stdout.log
3a18370654eb0ce89ba0b74688336a0635051dc8e03f8f53571e63c17719c9b6 results/alc_r0_status_publication_regression_v2_20261013.xml
03a1fbbba294479cccc808227cb71ba31a14d860ccd93842fb9f922477d20c69 results/alc_r0_status_publication_regression_v3_20261013.exit.json
e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855 results/alc_r0_status_publication_regression_v3_20261013.stderr.log
f79f82d0b4f39812bc411a8e8ea564008a5180dad891c843f96959828707c5a3 results/alc_r0_status_publication_regression_v3_20261013.stdout.log
2e1515c0920987186755d285cb4f196ac4e7a0064b928da890ec2db249519697 results/alc_r0_status_publication_regression_v3_20261013.xml
```

Independent final code APPROVE and architecture CLEAR each personally verified
all32 hashes, seven actualJUnit/native/log sets, exact143 unique identities and
47focused identity equality. Combined approval preserves this current-transaction
transport checkpoint ONLY. Full objective active; mandatory installed producer/
rotation/lease/resource/history/clock/qualification and actual learning stay open.
