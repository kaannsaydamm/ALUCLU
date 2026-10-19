# Same-handle diagnostic core evidence

Scope: decoder, fake-query contracts, stat bookends, isolated fatal control flow
and bounded test runner only. Native adapter and native target protocol are NOT
implemented. No installed continuity, v5 cause/repair, training readiness or
scientific acceptance follows. Protocol outlines future work, not a completed
capability. All results below were personally parsed; no test rerun on timeout.

## Test sequence

| Run | tests/failures/errors/skips | JUnit seconds | Native exit/root/total/active | timeout |
| --- | --- | --- | --- | --- |
| red | 30/29/0/0 | .932 | 1/34336/5/0 | false |
| green | 30/0/0/0 | .507 | 0/26572/5/0 | false |
| regression | 167/0/0/0 | 28.350 | 0/27316/73/0 | false |
| red-v2 | 31/1/0/0 | 1.303 | 1/33364/7/0 | false |
| green-v2 | 31/0/0/0 | .447 | 0/30236/7/0 | false |
| regression-v2 | 168/0/0/0 | 24.711 | 0/13068/75/0 | false |

Initial29 failures were missing decoder/query/bookend stubs; isolated normal
exit helper already passed. Both independent GPT-6.1 Sol reviewers found that
the initial marker os.write could fail before os._exit and unwind pending
buffers. Added isolated closed-stderr/fake-pending test reproduced the defect:
child exit3221226505, stdout UNWOUND, empty stderr; pytest exited1. This is not
an actual pending OS I/O reproduction. Repair: unconditional os._exit(71) in
finally around best-effort marker. Final31 focused and168 regression include
this negative; no UNWOUND output, child exit71. Older167 is not final coverage.

Final exact selection: 31 new +22 scratch/held +42 native metadata +73 inventory.
Original regression-v2 session99118 reached terminal fc5744; mainf4a083 parsed
counts and pins. All six captures valid/complete/EOF/resources closed, no excess
or failure flags, stderr empty. Stdout bytes:37267/81/243/1390/81/243 in table
order. Synthetic RUNNING remains not release or real admission.

Final source SHA256223726a48e8c24736f59d4db291896695b6638334862f1ec0feb987c80f67fcf
for tests/alc_r0_same_handle_directory.py; tests SHA256
aa0ae0fb2ac188ea9d98fe0c8eab46fe6c80428691e1b6fdb5a9f81ee1a51a5b.
Source frozen through final regression. Production pins personally rechecked:
python_runtime_binding86a96a908076ab830e2a3719cc9bdd87fab5440c61f63221e68ad64839db271f;
runtime_tree_inventory283be69ba005c108b2eaaae34b0574e7a27dd19b38aa31f026bb0cee93c6a667;
windows_directory_metadata63d02c6ea57bb76a0d2bdd31bbf3f169cdc27dc07de4342afa8c8b6617efc622.

## Independent review synthesis

Code lane initially REQUEST CHANGES, architecture identified same HIGH lifecycle
defect. After repair, code APPROVE and architecture CLEAR for core preservation
conditional on final-byte regression/artifact closure. Main verified terminal168
and final pins afterwards. Reviewers performed no execution/edits/spawns.
No native/production approval. Compound observation remains non-atomic; no path-
binding/ABA protection; fake query is not genuine pending I/O evidence. Next
work is native adapter plus sequence/cleanup/ABI tests, not another model run.

Terminal artifact rereview: code APPROVE / architecture CLEAR for repaired core
preservation only. Both independently verified all24 hashes, allsix JUnit/receipt
pairs, finalpins, exact168 selection and unchanged production. No discrepancies.
Main11fe65 also cross-checked allsix capture filehashes/terminal flags/counts.
These final verdicts do not expand scope to native readiness or genuine pending
I/O safety. No reviewer executed tests/probes or changed any file.

## Personally verified artifact SHA256

```
0214c0234fc6d5b9de5b7c337544be7a4f3e915cb09178af018e6f47465e3a3f results/alc_r0_same_handle_green_20261011.exit.json
e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855 results/alc_r0_same_handle_green_20261011.stderr.log
19932ebea0a183b7da572b238fb5973469697826509e41c17ad341f8d17bc318 results/alc_r0_same_handle_green_20261011.stdout.log
9b481192bb58be93ab2784e5bebb6266dc7859052a742b0ef06c24ffafaaa5a5 results/alc_r0_same_handle_green_20261011.xml
dfb9a4b68c419feb931a99712266521f5fd8408ce4e6cd1d97dca0da80ba147a results/alc_r0_same_handle_green-v2_20261011.exit.json
e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855 results/alc_r0_same_handle_green-v2_20261011.stderr.log
97d69e0dc34dc36495ba3305f1354db37988e9db84619c94a3d189c1aaf90e99 results/alc_r0_same_handle_green-v2_20261011.stdout.log
92c90a850310ea3811cd7abd5ccffd7012d352e9226cc85e844a233ee076f514 results/alc_r0_same_handle_green-v2_20261011.xml
5be721157f5fc0baeed675fa3550dbf8df1fea0f751ebf4de19c37c345c566b4 results/alc_r0_same_handle_red_20261011.exit.json
e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855 results/alc_r0_same_handle_red_20261011.stderr.log
9f4750dcc920cd35783c8781d3a74d05998193dad3383727d2787ae971e04007 results/alc_r0_same_handle_red_20261011.stdout.log
959ec89f3b348471f5c8c8b2036f1251c75498476fb9795887f72439efd8bcf3 results/alc_r0_same_handle_red_20261011.xml
ade1faa73e49360ac79d277b9a9c92e655d1eafd107600b3e4f636f239017e10 results/alc_r0_same_handle_red-v2_20261011.exit.json
e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855 results/alc_r0_same_handle_red-v2_20261011.stderr.log
017e2f1b595e4d5bcafe2c553598a223af023877e5f261cbdb53c306d43d1e5e results/alc_r0_same_handle_red-v2_20261011.stdout.log
e89e09988396225979de70f593f049f81e0f00b574f1d964e474467d04d1b321 results/alc_r0_same_handle_red-v2_20261011.xml
73a6a35947080dec18caf8922628aed5e853506d41deee351d29923986df63c8 results/alc_r0_same_handle_regression_20261011.exit.json
e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855 results/alc_r0_same_handle_regression_20261011.stderr.log
17f8626278ba7deb28d42492256554499a5f0426b1c70afe7a994d547a4455f2 results/alc_r0_same_handle_regression_20261011.stdout.log
f02883f41b15b56e3f0afb60075aea0c57de6a5b148846ff5b9ea2ba9d816a0e results/alc_r0_same_handle_regression_20261011.xml
46c09156c948f85ec0867cb66545ff95795222193cbd578c64c79d2189e76bfc results/alc_r0_same_handle_regression-v2_20261011.exit.json
e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855 results/alc_r0_same_handle_regression-v2_20261011.stderr.log
82dc709afe62bcda9ed39939c9f2c44a616ff1fd5d82655c712e809db11c072c results/alc_r0_same_handle_regression-v2_20261011.stdout.log
074145656a6612036159acfda7eace107d86829dfa0e9e66ca05895538542ebb results/alc_r0_same_handle_regression-v2_20261011.xml
```
