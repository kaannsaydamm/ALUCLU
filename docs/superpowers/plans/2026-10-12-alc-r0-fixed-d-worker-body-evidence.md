# Dormant fixed-D body: source and terminal boundary evidence

Parent fc3ce6a8c4ea9b0a16e58c126dbfdaaab53c4417. Windows research CPython3.12.13,
same authoritative Desktop checkout. No qualifier, tokenizer, model assets, GPU
or training workload was invoked. The existing worker remains unconditionally
denied, including the new body. This is dormant source composition, NOT evidence
of operational accepted-path execution or qualification readiness.

## Personally verified outcomes

| Mode | tests/failures/errors/skips | seconds | native exit |
| --- | --- | --- | --- |
| red (fixture collection defect) | 1/0/1/0 | 0.346 | 2 |
| red_v2 (missing functions) | 25/25/0/0 | 0.329 | 1 |
| green (initial source) | 25/0/0/0 | 0.142 | 0 |
| regression (initial source) | 287/0/0/0 | 82.616 | 0 |
| repair_red | 8/8/0/0 | 0.318 | 1 |
| green_v2 (final source) | 32/0/0/0 | 0.187 | 0 |
| regression_v2 (final source) | 294/0/0/0 | 79.693 | 0 |

First red is pytest inspecting a hook-bearing parameter during collection, NOT
intended production RED. Fixtures were fixed before red_v2. Original regression
source was stable during that run; it predates the review-driven repair and is
not reused as final-source evidence. Repair RED demonstrates absent finalizer,
typed-field fallback defects and absent immediate-precall deadline guard.
Final source stayed unchanged through green_v2/regression_v2.

All seven receipts: original120s parent bound, active_processes0, timed_outfalse;
all stderr empty. Final regression original43536 terminalf28ff0: native0,
root32196, total53, zero active. XML scope personally checked9c075c:
32body +49projection +55request +111wire +30worker +17import-isolation =294.
Controller exit0 is not a pytest success criterion by itself.

Command from repo root:
`<research-python> -B tests/alc_r0_fixed_d_body_runner.py <closed-mode>`,
src PYTHONPATH, no bytecode, plugins disabled, CUDA hidden. Existing owned job's
original120s deadline and10s cleanup retained. Legacy outer logs are exclusive
files, NOT runtime-stream-capped; no output.valid field. No scientific launcher
guarantee inferred from this diagnostic runner.

## Final source pins

```
7cff93ae086602405227d4435f7c450b0a75df88473e64439c175c98178c0bbc src/aluclu/alc_r0/fixed_d_worker.py
75bccedcd66031fb63a2a2d9239b434412b1b0562520d998a664a634a9b6a56c tests/test_alc_r0_fixed_d_body.py
c416b19ff36ade9afcd279a665ee4ce572de2213c9796e787af7ef90d251004c tests/alc_r0_fixed_d_body_runner.py
```

## Raw manifest

Every basename is under results/. Original bytes preserved with scoped -text
attributes established before staging; raw traceback whitespace is not formatted.

```
85678157d9026260cc7f62870906499f2717fb049b45c66180f87a8b1e7ec83b alc_r0_fixed_d_body_green_20261012.exit.json
e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855 alc_r0_fixed_d_body_green_20261012.stderr.log
0861033bdc2d6203bd8178972703a811b101e61fc065ed32dfd1a4824ab482f0 alc_r0_fixed_d_body_green_20261012.stdout.log
cf91856711b004e1de7727b576e0468c65ddb9d0f77e5efb1edc99faa8d184ce alc_r0_fixed_d_body_green_20261012.xml
865a69d6f86cb949b32d9aebb5eaf01461cb0717eeefdb2ebd4480b125ba96c5 alc_r0_fixed_d_body_green_v2_20261012.exit.json
e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855 alc_r0_fixed_d_body_green_v2_20261012.stderr.log
3833adcbec29e6fc3ba05401d9ffa921159c26e2b47365a157b6aa9c189f0be2 alc_r0_fixed_d_body_green_v2_20261012.stdout.log
c9ef9dcc0557c08f7e8faaca5ff854c2c32c79957f615e997bb036c1192d01d4 alc_r0_fixed_d_body_green_v2_20261012.xml
3ae9c0184a95c7baa1adeae9f6b89d30f1176ab36f239eae846c5ac61e3f930a alc_r0_fixed_d_body_red_20261012.exit.json
e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855 alc_r0_fixed_d_body_red_20261012.stderr.log
76549e256e921e8a96d37c8030301bafcc608b4efb26ab7340655b040bbd7385 alc_r0_fixed_d_body_red_20261012.stdout.log
206ff0dedaee803d7bcf337c58dfd3c23f66d1fb61916406b7100d4157393697 alc_r0_fixed_d_body_red_20261012.xml
74d5f53a61c5221c1f81a5abf6d63f15674f62d2df9aee9891775fa5a20143f6 alc_r0_fixed_d_body_red_v2_20261012.exit.json
e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855 alc_r0_fixed_d_body_red_v2_20261012.stderr.log
774a2ce00463237e3d57717653942c8d84596868c21f53b4747ba5fa27049bfe alc_r0_fixed_d_body_red_v2_20261012.stdout.log
235024411c9f55171da0bbdb437ddb1ad5c332f8fee195145ecccf50a32abba3 alc_r0_fixed_d_body_red_v2_20261012.xml
ffd1e9f35df1a86b4ba4a653949e8ce1d80237807fa0f41585ac7ae687a4167d alc_r0_fixed_d_body_regression_20261012.exit.json
e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855 alc_r0_fixed_d_body_regression_20261012.stderr.log
299ccffd60845340d887a1e64c25dba02f6bf9f8577d6eca495875e4c057ac87 alc_r0_fixed_d_body_regression_20261012.stdout.log
378e7624a8472cbf58337ac55d4e0e06243455180e7f31e731a6f8658e482680 alc_r0_fixed_d_body_regression_20261012.xml
c3a393ac84de82b0f9c3d1f78e1524f3a0b25505722d90b26d76787bc62b16c7 alc_r0_fixed_d_body_regression_v2_20261012.exit.json
e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855 alc_r0_fixed_d_body_regression_v2_20261012.stderr.log
3d80f99ac128d8c2cbde1be8e8b34cfbb3f52fac1f5f39aae641c893ca60875f alc_r0_fixed_d_body_regression_v2_20261012.stdout.log
de733ef7fb616c9e1d4cfece0b2f64cdeada2b3cfecfe58ebd766da084875a20 alc_r0_fixed_d_body_regression_v2_20261012.xml
10240d46697a3a4d59486d45130cad0f31d0743346f8563f3672648913ea53df alc_r0_fixed_d_body_repair_red_20261012.exit.json
e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855 alc_r0_fixed_d_body_repair_red_20261012.stderr.log
fae73dc7b6c6feb78ecb906c0f5b23bde588ce051753d5ecc260b0452dc40aa4 alc_r0_fixed_d_body_repair_red_20261012.stdout.log
fbc10dac30817a615f31e70642325b41153a065404938c6d23a5060536d3f8d6 alc_r0_fixed_d_body_repair_red_20261012.xml
```

## What these tests establish, and what they do not

Dynamic tests establish first-operation denial before request hooks; bounded
cycle-safe diagnostic classification through trusted exception descriptors;
exact closed stage/type checks; absent-field fallback; real synthetic-codec
future/expired/interrupted/invalid-request terminal reporting. Existing worker
regressions retain fresh denied entry/import/settings checks. Pure classifier
class inputs are private classification fixtures, never scientific callbacks.

AST/source checks establish one direct fixed qualifier call, no loop/retry, an
immediate original-deadline guard after imports, and at most two finite terminal
failure encodes without recursion. Mid-encoding deadline crossover is NOT
dynamically fault-tested. The second encode is terminal reporting, not renewed
scientific useful work; blocking calls/cleanup remain outer owner's duty.

The inaccessible accepted path has NOT dynamically demonstrated runtime
preparation followed by qualification, success projection, real model OOM,
deadline interruption during model work, complete scientific partial-receipt
retention, or worker stdout delivery. No fake runtime/qualifier was injected to
pretend otherwise. No CLI, request-file, trusted-producer or output integration
has been installed; main remains denied and unwired.

Initial code REQUEST CHANGES on deadline-reporting ambiguity was resolved by
prospectively admitted finite finalization (max2codec calls), missing typed fields
fallback and immediate precall deadline check. Two independent final source
reviews: GPT6.1 code APPROVE / architecture CLEAR. Terminal independent code
APPROVE / architecture CLEAR: both personally verified28raw+3source hashes,
sevenreceipt/JUnit pairs and exact294selection. Main c25ba6 separately verified
31manifest hashes and31index byte-identities; scoped attributes preserve raw
bytes. Accepted for dormant source/boundary evidence preservation only.

Next requirements remain concrete operator producer, authenticated request/source/
runtime/asset bindings, lease admission and active watch integration, historical
charge/clock/resource bounds, output/terminal ownership, GPU2 fieldwise evidence,
actual CPU/GPU D qualification, E gates and first learning pilot. No ALC-0,
learning PASS, budget reset or broad portability claim follows. Full goal active.
