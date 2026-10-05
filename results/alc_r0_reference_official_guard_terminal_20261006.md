# Checkpoint199 parent-observed terminal evidence

Scope: fake/pure CPU mount-guard substrate only. No host/assets/GPU/training.
Parent source bcd84e78cf0971c2ecad8aa704d2d30db180e2a9 plus reviewed new files.
PYTHONPATH=src; existing locked Windows research venv Python. No installations.

Commands were direct tool-owned foreground executions, not detached launcher
runs. The following are observed tool terminal exits, not inferred from XML.
Tool stdout snippets below are transcriptions, not independent raw log files.

| Tool session | pytest selection | Observed exit | JUnit tests/failures/errors/skipped | seconds |
| --- | --- | --- | --- | --- |
| 88748 | new guard before implementation | 1 | no XML; collection missing-module error | not measured |
| 55543 | guard initial implementation | 0 | 21/0/0/0 | 18.297 |
| 7513 | guard -k 'exact_declared_arguments or negative_zero_argument' before repair | 1 | 6/1/0/0 | 15.126 |
| 16307 | guard + reference_qv_artifact + parity_factory after repair | 0 | 117/0/0/0 | 19.383 |

All selections used `python -m pytest`, explicit test paths, `-q`; XML runs
used one `--junitxml=results/<stem>.xml` argument. Final paths:
`tests/test_alc_r0_reference_official_guard.py`,
`tests/test_alc_r0_reference_qv_artifact.py`,
`tests/test_alc_r0_parity_factory.py`.

Final stdout reached `[100%]`; JUnit testcase grouping independently inspected:
24 new guard,29 artifact,64 factory. Final Python processes matching the new
test command absent after terminal return. Ruff check and git diff check passed.

Negative-zero RED reproduced `Failed: DID NOT RAISE ValueError` with all B=-0.0
and expected_b=-0.0. Explicit sign rejection repairs the phase declaration;
no acceptance threshold relaxed. First missing-module RED is expected TDD.

XML SHA-256:

- initial focused: b35de77f4655efab71b24e44d76806fb1f93252957dafa451bd359fb52a67892
- signedzero RED: 5678b9c0b445553b87d2061fda2883a25502803ed8738842e6d62ec3e78775f8
- final regression: d86c9e7fec79ea5f4d7d2679a41a7234c8b7504f94ba014cfc18146a34f14038

Independent exact-byte GPT6.1Sol code APPROVE and architecture CLEAR:

- source: 3f6ae0e8bd76be19f687b5a0fecb54ff769600da1d617ff17529f1d8d4db3007
- tests: d989d568d783cdbe34d5de7f6e75aa8f8f778f042728905c8d5e8deff9df271e

Limits: complete base/source/configuration checks are outer obligations; this
is cooperative quiescent observation, not locking. Validation overhead belongs
to inclusive accounting. Fake fixture explicitly bypasses verified-host
construction. No model execution,72-row suite,cache/witness behavior,actual
host parity,resource qualification,scientific adoption or learned capability
is proved by these results. Original matched grid/scientific gates unchanged.
