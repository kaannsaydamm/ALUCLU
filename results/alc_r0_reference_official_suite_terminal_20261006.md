# Checkpoint200 observed terminal evidence

Scope: separate q/v composition/receipt substrate with real factors/guards,
tiny substituted base and stubbed forward/witness. Not actual-host evidence.
Parent9d0f28bbbcbae84dba78d301b10c85dcb70225d4 plus reviewed implementation.
PYTHONPATH=src. Existing Windows research venv Python; no installation/asset load.

Foreground tool-owned `python -m pytest` commands used explicit paths, `-q`
and single `--junitxml=results/<stem>.xml` arguments. No detached exit inferred.

| Session | Selection | Personally observed exit | JUnit tests/failures/errors/skips | seconds |
| --- | --- | --- | --- | --- |
|87091|new suite before source, -x|1|1/0/1/0|11.000|
|30967|new suite initial|0|24/0/0/0|17.916|
|35108|suite -k 'bad_case_receipts or byte_identical_base' before repairs|1|6/2/0/0|19.145|
|5288|four-file regression before import-spacing correction|0|153/0/0/0|29.733|
|98606|same four files final bytes|0|153/0/0/0|29.034|

Four final paths:

- tests/test_alc_r0_reference_official_suite.py (36)
- tests/test_alc_r0_reference_official_guard.py (24)
- tests/test_alc_r0_reference_qv_artifact.py (29)
- tests/test_alc_r0_parity_factory.py (64)

Counts/grouping/time and XML hashes personally inspected after final terminal.
Tool stdout reached100percent; this is an output transcription, not a separate
raw stdout/stderr log. OS inventory after terminal found no relevant Python.
Ruff check/format check passed final bytes; no source/test edits while live.

RED35108 demonstrated delayed per-row CPU digest validation (72 bad rows entered
completed before final rejection) and undetected final base-object replacement
sharing parameter/config objects. Repaired by per-row equality before append
and base object identity in every signature. No threshold/fixture/grid changes.
Import-spacing correction was nonbehavioral, but final evidence rerun anyway.

XML SHA-256:

- missing-module RED:25c42771775fb480ff93dcd60030eea81ec8bc087649f54456c06bb9292d7b6f
- initial focused:e934f528596e870fbc5e24231ec8515e68875ac34ac0129fac9c1622d039408d
- identity RED:e1d4538163daeeb85c4095a057a67fa17c158069914c24f580f4032f55bb1214
- regressionv2:513974261b1f6044620d306b8aef8879cfd3110249acaa3891ff32c7359a0efd
- finalv3:9d290b0d8552649a5ff5819b47b414a56aea2f4085460a57e3af49e054d9a257

Independent GPT6.1Sol codeAPPROVE/architectureCLEAR verified final exact hashes:

- source:ae79719edcd10bfe61c10cf131cb5e09c9ba07506c0f4028b42573e0aaad49cd
- tests:4ec911dad227c48561e866174d394f74c57b3d3f8e3f17a4d770b67612e79bd9

Residual limits: full72observations/witness are stubbed; real cached primitive
test exercises shared checks using synthetic logits/cache, not actual decoder.
Fakefullwrapper real_case/witness/detach/padding/positions/cache integration is
required next before actual-host invocation. Separate q/v checkpoint parity
composition is also incomplete. Source/assets/tokenizer/runtime authentication,
deterministic GPU context, exclusive cooperating ownership, inclusive time/peak
accounting, admitted resources and durable outer journal remain external.
Receipts are consistency observations, not authentication or launch authority.
No actual model/GPU/E3/capability-learning/portability claim is made here.
