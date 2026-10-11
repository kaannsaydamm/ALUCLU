# Fixed D wire codec runtime evidence

Status: scoped codec accepted; closing independent code APPROVE / architecture
CLEAR verified all final source/test/runner/contract/runtime bytes and artifacts.
Parentc363bd4e412e17f41632399e451d658f2719c549. Pure transport checkpoint only.

## Exact final bytes and observed environment

- fixed_d_wire.py SHA2564d55e8bdcc0943e3c9dab289a3f35eb2046bc2de9283746fa18f45c47e72d8df.
- test_alc_r0_fixed_d_wire.py SHA256580d4cbf39f2f2d519d74b730705624da3020a1154146a5392149dbc3a44bd01.
- alc_r0_fixed_d_wire_test_runner.py SHA256dd8251af8410e2d4bf61c6b4b155e458010d768fdcf601a6d64643cc554fc92a.
- Wire contract at admission SHA256bdc2746d6afd1d464d67069bd71108f221e981c18e1609a0001819925a68a986.

Windows CPython3.12 through the previously pinned existing research interpreter:
C:/Users/kaann/AppData/Local/Packages/OpenAI.Codex_2p2nqsd0c76g0/LocalCache/Local/ALUCLU/research/alc-r0-smollm2-135m-v1/windows-training/.venv/Scripts/python.exe.
All runs use authoritative Desktop worktree src on PYTHONPATH, disabled user site,
bytecode/plugin autoload and CUDA_VISIBLE_DEVICES=-1. No installation/download.
Plain codec imports no Torch/Transformers/NumPy. Import-isolation regression
deliberately imports Torch/CLI exports without invoking main, initializing CUDA,
instantiating host/model or accessing model assets. Not a no-Torch regression claim.

## Personally observed terminal evidence

All groups under results/alc_r0_fixed_d_wire_{phase}_20261008 with .stdout.log,
.stderr.log, .exit.json and .xml. stderr is0bytes in all4groups; no timeout.
Counts below are tests/failures/errors/skipped, not the runner's own exit status.

| Phase | Retained native root | pytest exit | JUnit counts | Seconds | XML SHA256 |
| --- | --- | --- | --- | --- | --- |
| red | 8256 | 1 | 3/3/0/0 | 0.772 | 5ba9d2328c7e89f89299966777886176bac9180b7f2a4b46be2f50e1b6ad523c |
| c1_red | 14548 | 1 | 2/2/0/0 | 0.391 | 8044a5a0abe30677e7dffa3e7b20bf19c20bb9f4cb0634a67f460d8f3b507b2b |
| green | 21824 | 0 | 111/0/0/0 | 27.052 | c46b822ef8062555e6e83e2bca9e8df054830b60fe23eebb998374a75f31da12 |
| regression | 7744 | 0 | 199/0/0/0 | 72.258 | 6028323e53e5afd61490fd50cb51a2382ffaf6b2c3b773a2b7d9a605f1c53916 |

Initial RED had exactly3missing-module failures before production module existed,
not dependency/collection failure. It used native parent60s supervision; selected
tests launched no subprocess and no terminal-tree fact beyond that root is claimed.
Initial test file SHA75bceaef6a2cb4c186626a9223131f599bcfc205ea98ae2093cd6749a67c966c.

Initial implementation SHA5dcac79f32f3660d6b4d70d62e65a9465097584699fe4ecb61fdc8efe69cdb9a
had a real C1 control-path defect discovered independently. c1_red reproduced
both DIDNOTRAISE before repair. Then path predicate was changed to Unicodecategory
Cc (C0/DEL/C1), without scientific/data comparison change. Closed test runner
uses the existing private-job primitive, not a scientific admission path.

Owned receipts for c1_red/green/regression show respectively3/5/39total processes
and0active members at terminal, original root handle exit observed. Bounds are
60/120/120useful seconds plus the primitive's existing10second cleanup tail.
Runner's own exit0 is not pytest0: actual receipt+JUnit were personally checked.
GREEN observed original session2783/b47f68; conditional regression continued only
after exit0, zero issues/timeout/active members and unchanged pins, same retained
session2783 terminal65a153. All final pins and every XML/log/exit were rechecked
b90ba8. No source/test edits occurred during either live execution.

Regression selection is exactly codec+canonical+checkpoint_parity_inputs+
alc_r0_import_isolation. This is not the entire repository suite or portability
matrix. No attempt to reinterpret earlier narrower suite evidence as this result.

## Size-bound scope

Tests exercise the full1296official rows,18witnesses,18matrix cells and18case rows
per cell, largest tokenizer-class/path metadata, long finite measurement spellings,
closed failures, schedule/field mutations and preparse byte/depth/UTF8/token bounds.
The larger fixture is a synthetic stress example, not an exhaustive numerical
supremum or observed host/RSS projection. An additional conservative encoding bound
follows directly from the admitted fixed shapes and scalar grammars:

| Component | Conservative canonical byte allowance |
| --- | --- |
| 1296official rows at<=1024bytes | 1327104 |
| 18witnesses at<=512bytes | 9216 |
| 18*18matrix case rows at<=1024bytes | 331776 |
| 18*3*4named comparisons at<=512bytes | 110592 |
| 18cell metadata blocks at<=1024bytes | 18432 |
| 6fixture rows at<=8192bytes | 49152 |
| remaining fixed envelopes/identities/fixture metadata | 16384 |
| Total upper allowance | 1862656 |

This deliberately overcounts all cells as4named factors. An official row retains
4fixed64hex digests at most, bounded keys and fixed schedule values, comfortably
below1024. Witness has2digests/fixed grid/arm below512. Case row retains2digests,
4measurement numbers and fixed integer/state fields below1024. Comparison pair
has a fixed short name,6keys,5measurements/nullable fields and oneboolean below512.
Fixture row has at most4*71+64bounded integer/string entries, one prompt and6keys;
even allowing21bytes per integer entry, plus punctuation/keys, stays below8192.
The16KiB envelope allowance covers all remaining fixed metadata and256byte class;
snapshot path is request-only and separately capped at16KiB total request bytes.

Finite measurement canonical spellings are conservatively<=32bytes: ordinary
binary64 short decimal, optional sign and3digit exponent, or RFC8785 expansion
only in the -6..20 exponent window. The existing pinned rfc8785/_impl.py float
serializer was read (bf4d86) to check that expansion rule; this is an encoding
argument, NOT complete runtime-binary provenance. Numeric JSON integer measurements
also have RFC8785 safe-integer bound; decimal-string fields are bounded separately.
Thus full admitted success receipts fit below4MiB without tensor/optimizer payloads.
Decoder still enforces that cap BEFORE parsing any untrusted bytes; hostile input
allocation protection is independent of a valid-success size argument.

## Honest acceptance boundary

Synthetic codec behavior does not authenticate a worker, source/runtime/assets,
history numbers or clock. Reduced receipts cannot reconstruct absent tensor
comparisons. No real model/GPU qualification, pilot, retrieval-off neural learning,
durability, platform PASS or full-goal completion follows. Original frozen plan
SHA2560493eeed795dbf089babe54bc14204e30d82c7381c4b819afdf986c0baff6c9b unchanged.
Next integrate a bounded projection from the existing qualification return value
into the fixed worker, preserving denial until reviewed operator handoff and
accounting/resource admission. GPU2 fieldwise stability evidence remains blocking.
