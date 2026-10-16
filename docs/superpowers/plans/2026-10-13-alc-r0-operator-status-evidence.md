# Operator status: terminal observation evidence

Baseline878c7b5d95130ee150522a8bd7e75ff31f62b928, authoritative Desktop checkout,
dedicated Windows CPython3.12.13. No real installation, updater, model, tokenizer,
GPU, heldout access or training was performed. This completes bounded status
observation only, not trusted producer or accepting launch integration.

## Verified results

| Mode | tests/failures/errors/skips | seconds | native exit |
| --- | --- | --- | --- |
| red | 2/2/0/0 | 0.337 | 1 |
| green | 40/0/0/0 | 0.234 | 0 |
| regression | 279/0/0/0 | 14.824 | 0 |
| green_v2 | 47/0/0/0 | 0.221 | 0 |
| regression_v2 | 286/0/0/0 | 14.875 | 0 |

RED: two valid decode/read cases fail missing module, retained. First regression
was terminal before tests expanded, so it is initial-test coverage only. Production
bytes unchanged; final test/runner bytes stable for v2 runs. Main82f893 personally
parsed five JUnit reports and current pins. Final selection47status+55request+
111wire+48canonical+25watch=286. Original76324 terminalbcfdb8 native0/root3552/
total5/active0/notimeout. All five receipts active0/notimeout, parentbound120s;
stderr empty. Wrapper exit0 alone is not a test verdict.

Run from root: `<research-python> -B tests/alc_r0_operator_status_runner.py <mode>`,
src PYTHONPATH/no bytecode/no user site/plugins disabled/CUDA hidden. Exclusive
fresh output files and original120s owned job+10s cleanup. Legacy outer capture
is not runtime-stream-capped and supplies no output.valid field. Post-run hashes
are not an enforced log-cap claim.

## Final source pins

```
69134bf486f695dd0c23fd5f9b0aefd00f04b3d1f40580db42bf64f36e34a6e8 src/aluclu/alc_r0/operator_status.py
a23c9eb72e55b10424f9a6fc438eed7cf442b7a65e45b6a7602724223faa7d18 tests/test_alc_r0_operator_status.py
e95408194e82a624b38afdabea0eff6f83f7099ab5840f8e7f191404be587397 tests/alc_r0_operator_status_runner.py
```

## Raw artifact manifest

Under results/, original bytes preserved via scoped -text rules, including RED
traceback whitespace. No rerun overwrites or normalized output.

```
6d69c7bfde1fe357cc51dfabe55d621d18e2536ba120267f7464a1f7cc1ada86 alc_r0_operator_status_green_20261013.exit.json
e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855 alc_r0_operator_status_green_20261013.stderr.log
6ebed2952a4b894cf41fe3f033912ab2809f8670a405e433039e960465e4f5b8 alc_r0_operator_status_green_20261013.stdout.log
365a8bea2870a3b9e940832bcdbd32febba6e88ba543fab3c920578f6f4152e6 alc_r0_operator_status_green_20261013.xml
0cc18b597bb3e535d83213f9ae323021509857cc1c92686b3ab78f44a0d1996c alc_r0_operator_status_green_v2_20261013.exit.json
e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855 alc_r0_operator_status_green_v2_20261013.stderr.log
647689a0c3ea3cace805553d723f6251f68c9740d7ca6a5c1685fae9336ae09d alc_r0_operator_status_green_v2_20261013.stdout.log
67412888eb4dc2df01adc1b87c8da8e79e3e5b31f704327e3b1cbf8319489a3a alc_r0_operator_status_green_v2_20261013.xml
77e1564a10b84c2dc1ef1b7612614d182d14612e396b5c4579241ae7a2b16bd3 alc_r0_operator_status_red_20261013.exit.json
e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855 alc_r0_operator_status_red_20261013.stderr.log
c2216575958950d0223426b0770fbf8f43577382f948380ddeab80c3324d5d46 alc_r0_operator_status_red_20261013.stdout.log
32b8dd5dba076b65adce7d81a4507a19eca0074444f549307092ffb317844f95 alc_r0_operator_status_red_20261013.xml
4899a4e375353d01d3af4eaca1e864b9e242dddf37d348edd2c00586599803be alc_r0_operator_status_regression_20261013.exit.json
e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855 alc_r0_operator_status_regression_20261013.stderr.log
6967eed7f8964b586fdb3b1fe8b1c13787b2b0c9a56345333f01a04c5b6ab63b alc_r0_operator_status_regression_20261013.stdout.log
5da0af0cbaa5ae012e74cc9bd6f130b8a5b093f1f31ae77f590df82dc7bea508 alc_r0_operator_status_regression_20261013.xml
54c2aa136d160501c57988f2c2f08bad3741799eef676ce751e0faf9eb407ac7 alc_r0_operator_status_regression_v2_20261013.exit.json
e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855 alc_r0_operator_status_regression_v2_20261013.stderr.log
4a936487f34b71b32b415a7ed58628a26945470ea64b187454809b80981b1a7e alc_r0_operator_status_regression_v2_20261013.stdout.log
f4bb7a0da65b48346b029890836797d64e75fa97a09bc40f333706f95299b142 alc_r0_operator_status_regression_v2_20261013.xml
```

## Coverage and authority boundaries

Actual temporary-file tests establish valid/frozen exact-byte observations, strict
schema/numeric/bool/hash parsing, malformed content and size refusal, directory/
missing/hardlink refusal, original expired/malformed deadline refusal, ordinary
path/ADS/device/symlink refusal (zero skips here), and observation of sequential
atomic replacement between two reads. Independent depth1 token fixture isolates
64 allowed vs65 refused lexical tokens. Updated tests address source-review
token/path coverage concerns without altering production code or scientificrules.

Observed replacement during reading, post-open expiry, leaf/ancestor mutation,
hostile ABA and all overlapping atomic replacements are NOT directly fault-tested
in this status suite. Reviewed source retains cooperating-host continuity only.
Path string/decoded roots do not authenticate installation, time, revocation or
writer provenance. No monotonic sequence enforcement, durable consumption, updater
recovery or restart anti-replay is claimed by this stateless reader.

Codec applies4096bytes/depth2/tokens64/rawUTF8string256 before canonical parser;
file reader checks own4096 size pre-open/open and4097sentinel maximum, not reused
16KiB request cap. Decoded sequence/expiry are integers, while raw canonical bytes
remain exact. Blocking OS I/O must be contained by outer ownership, not Python
deadline checks. No 250ms operational observation-latency guarantee measured.

Two independent final GPT6.1 reviews returned code APPROVE / architecture CLEAR.
Both personally verified20raw+3sourceSHA, fiveJUnit/receipt pairs and exact286
selection; mainfbaa8b separately verified23manifestSHA+23index byte-identities
and clean staged whitespace check. Scoped observation checkpoint accepted;
no launch/installation readiness follows.
Next: exact generation-record and durable one-use publication/updater contract,
then trustedinstallation/leasecreate-resume/workerhandoff/watch composition;
history/clock/resource/GPU2 and real D/E/learning gates remain OPEN. No worker
guard removal, budget reset, learning PASS or full-roadmap completion.
