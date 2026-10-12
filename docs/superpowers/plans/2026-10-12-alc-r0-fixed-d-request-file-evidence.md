# Fixed-D request transport: terminal evidence

Baseline c5e40700b8c8017d552a1597ad373acfe21f4b46, authoritative Desktop
unified-lifelong-cognition-local checkout. Dedicated Windows research CPython
3.12.13; CUDA hidden. No model/tokenizer/data access or training was launched.

## Personally verified terminal results

| Closed runner mode | JUnit tests/failures/errors/skips | Seconds | Native exit |
| --- | --- | --- | --- |
| red | 2/2/0/0 | 0.276 | 1 |
| green | 51/0/0/0 | 0.712 | 0 |
| continuity_red | 4/4/0/0 | 0.316 | 1 |
| green_v2 | 55/0/0/0 | 0.364 | 0 |
| regression (diagnostic predecessor only) | 257/0/0/0 | 77.069 | 0 |
| regression_v2 (final source) | 261/0/0/0 | 54.898 | 0 |

RED is missing module; continuity_RED is missing private helper. Negative evidence
is retained, not reclassified. First regression was already live when the tests
were expanded: its 257 passing cases do NOT establish final-byte acceptance.
Final v2 source remained unchanged during its focused and regression runs.
All six receipts: active_processes=0, timed_out=false, original parent bound120s.
Final regression original exec94967 terminal d2c14f: root33516, total51 processes,
native0. Controller exit0 alone is not the pytest verdict. All stderr files empty.
Final scope: request-file55 + wire111 + canonical48 + worker30 + import-isolation17.

Commands from repo root with src PYTHONPATH, no bytecode:
`<research-python> -B tests/alc_r0_fixed_d_request_file_runner.py <mode>`.
Runner permits only listed closed modes and refuses existing evidence files.
It uses the existing owned Windows job with original deadline/cleanup behavior.
Legacy outer capture is NOT runtime-stream-capped, and its receipt has no
output.valid field. Log sizes/hashes are post-run observations, not stream caps.

## Exact final source pins

```
6edf395dbcc34578e743157a28f475464aed9dd1673340d03412025d97a96d0d src/aluclu/alc_r0/fixed_d_request_file.py
f82816249046d2b33e9fd235e3ab4db770d575d810c2c1d9ffbf5ba89ee655fe tests/test_alc_r0_fixed_d_request_file.py
2e24950ebe552094689e3ed5fa49ece81801271de071d8f257cd5ca04897df5c tests/alc_r0_fixed_d_request_file_runner.py
35ba89c1196e933e34885fac4b01aa0ac3440c5914844bd988b97d6315ad7ea2 src/aluclu/alc_r0/fixed_d_worker.py (unchanged)
```

## Raw evidence manifest

Every entry below is under results/, SHA-256 followed by exact basename.

```
fd7a35b8fd91b15f2003ba6807f8979e8e9b2d25ba9fbf344d94931f9b98b355 alc_r0_fixed_d_request_file_continuity_red_20261012.exit.json
e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855 alc_r0_fixed_d_request_file_continuity_red_20261012.stderr.log
11cf77e5109bca9dd15be258c245f3b0a4a70e0d9d0e084a150603c48d889f6c alc_r0_fixed_d_request_file_continuity_red_20261012.stdout.log
33d41a252cc586f7dcee631a1979b248dc82783d8fe6f324ee6c96a20a01a7d5 alc_r0_fixed_d_request_file_continuity_red_20261012.xml
bfae0912de7693262affbc11e7ad1375d8daa972d447c3191ca39089e65713e7 alc_r0_fixed_d_request_file_green_20261012.exit.json
e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855 alc_r0_fixed_d_request_file_green_20261012.stderr.log
1ec33c09745553cad5dc075eda85a7fb1813c84be157e02b8060555661b9fdfc alc_r0_fixed_d_request_file_green_20261012.stdout.log
10fda82a61f3fff1670fa6d37c14e788831b37f588e6897c7de15e34e562e2e7 alc_r0_fixed_d_request_file_green_20261012.xml
efc02ef7748bbee8481e3fa6fd0af80d22f8fe4f4d6484df23061ed7823f00e4 alc_r0_fixed_d_request_file_green_v2_20261012.exit.json
e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855 alc_r0_fixed_d_request_file_green_v2_20261012.stderr.log
cb18da0b6f22f66dcc3b91519f2731f34b02c843e4e4517d002e65d87a1ecdaf alc_r0_fixed_d_request_file_green_v2_20261012.stdout.log
846bd7ccfa5baeafa70128812dcee5423edb3dd4c0f5d919586450e3e2f54870 alc_r0_fixed_d_request_file_green_v2_20261012.xml
2e905d1a8119dff87fed62eb8b8cc0b92296be42a85f899b880a0c4d68e6018b alc_r0_fixed_d_request_file_red_20261012.exit.json
e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855 alc_r0_fixed_d_request_file_red_20261012.stderr.log
8e07a69141c1699efe3b71c52a0d1fef1df5821e1da2fa86e2e50faea365fd2e alc_r0_fixed_d_request_file_red_20261012.stdout.log
9a6d0383004bcac39c056e87e4cdeeb8e0dc532fcebade863bf59e00fdefb66e alc_r0_fixed_d_request_file_red_20261012.xml
b72c841eb4d8c9a4c70d99cc8dd076e21edd5260835eae213613e7d7ef6a5333 alc_r0_fixed_d_request_file_regression_20261012.exit.json
e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855 alc_r0_fixed_d_request_file_regression_20261012.stderr.log
63d4156f2d448b918b13cf73b34821bd7f7b41d235539181a9162826fb8a1672 alc_r0_fixed_d_request_file_regression_20261012.stdout.log
5012830c4baa32c375a5004c495d316eea73e1c66453ce37428eccd9cf7245dc alc_r0_fixed_d_request_file_regression_20261012.xml
f49da7e3b9036c2cc7dda883c535e9fa0ebd317b9f99de8a560975b9c4bba46b alc_r0_fixed_d_request_file_regression_v2_20261012.exit.json
e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855 alc_r0_fixed_d_request_file_regression_v2_20261012.stderr.log
f247b90611985c88f6cf33236513024ec1dce71c868af38e49cb932199c97143 alc_r0_fixed_d_request_file_regression_v2_20261012.stdout.log
0773563ba55479cad673b9a463ad611341e8c9bf74e50dfc7101a3273124bcc1 alc_r0_fixed_d_request_file_regression_v2_20261012.xml
```

## Scope, review and remaining work

55 focused cases prove ordinary temporary-file transport/negative syntax/size/hash
and codec behavior, actual host symlink negatives (no skips here), single-link
refusal and private short-read bounds. Explicit private test doubles wrap real
OS handles to verify mtime mutation, late hardlink refusal, post-acquisition
expiry closes the handle, and success opens once/closes. These are not full
hostile-filesystem experiments. Ancestor/leaf replacement and post-decode expiry
fault injection remain unexecuted; no adversarial ABA/no-follow claim follows.
Deadline20ms +40ms delay expiry fixture is a timing-based local test, not a formal
scheduler guarantee. OS blocking still requires the outer original owned lease.

Two independent GPT6.1 source reviews: code APPROVE, architecture CLEAR at final
pins; both explicitly require final terminal evidence closure before checkpoint.
Terminal independent code APPROVE / architecture CLEAR: both personally verified
all24 raw artifacts +4 sourcepins, six receipts/JUnit pairs and exact261 selection.
Main independently rechecked all28 manifest hashes (3ba1f2). Checkpoint accepted
for transport only. Raw RED traceback stdout/XML contain original trailing
whitespace; retain their exact bytes instead of formatting evidence. Source/docs
diff whitespace checks are separate from those preserved raw artifacts.

Transport reader returns the existing immutable DRequest; caller root is not
authenticated. Existing worker denial remains before any accepted request/heavy
runtime. Trusted operator producer, real worker body, lease admission/monitor,
historical accounting/clock/resource decisions, GPU2 bounded fieldwise comparison,
D/E qualification and actual neural learning experiment remain OPEN. No ALC-0 or
learning PASS, no new platform claim, no experiment clock/budget reset.
