# Checkpoint148: atomic inventory-installation prerequisite

Baseline e9a021021e7791b1b4d97c045d1ea769ca41f40b. New private controller
primitive is an implementation prerequisite for checkpoint145's wrapper bridge,
not that bridge itself. It leaves the original controller and constructor
behavior unchanged. Default callback remains None until explicit installation.

Callability is checked without execution. Active-lease check, identical-binding
handling and first assignment share the original lock with session capture and
publication of _active. Installation during any active lease is denied, even
for an identical binding. Inactive identical reinstallation is idempotent;
different replacement is rejected without changing the old binding.

Installation does NOT qualify arbitrary callbacks. A future integration must
prepare and independently review an observational getter. Capture calls it
while holding a non-reentrant lock: the getter must not enter another session,
install state, call mutation guards or otherwise reacquire that lock. Direct
public-field assignment remains outside this cooperating-process contract;
existing session identity guards remain unchanged, not hostile-host security.

## Evidence and preserved failures

| Receipt | Actual exit | Tests/failures/errors/skips | Time | XML SHA256 |
| --- | --- | --- | --- | --- |
| red_v1 | 1 | 8/8/0/0 | 18.035s | 425177d57c6a9546bc5ca197161ca01c990a475df706da583da3c7ec4db9182b |
| green_v2 (FAILED) | 1 | 114/3/0/0 | 69.055s | 594f4b902e2fa263988bfea1ba635aabf93e16f041a513893813b2fb6f915196 |
| regression_v3 | 0 | 985/0/0/0 | 59.116s | 2a5af88e6c4c7a5a8a112409d69d6bccdbcbbce77a49cbc5a19b8ece18498c94 |

RED lacked the new primitive. Initial v2 fixtures returned noncanonical short
strings, so existing capture validation correctly rejected them before the
intended assertions. Both independent reviewers identified that defect too.
Production validation was preserved; fixtures now use explicit synthetic64hex.
Ruff also identified two lambda-assignment style errors, repaired before final
regression. Initial failure receipts and reviewer REQUEST CHANGES/WATCH remain
recorded rather than being represented as successful checks.

Root consumed original process31814 exit0 and parsed final JUnit, including
all8 new cases. Regression is checkpoint147's31 component targets plus this
test file, not the whole repository. Real CUDA-host and real pinned-tokenizer
cases remain explicitly deselected. Existing tiny optimizer tests are synthetic.

Reviewed final hashes:

- checkpoint_execution.py: 5cfe9b9826f7fcbc918847186145af0eb15873cc239d4bd6bdc62c9123f4694d.
- test_alc_r0_checkpoint_inventory_install.py: 37e15d92dd7b11ed76893eae12122f069978953c8463c3c0b184b82a4942c001.

Final independent GPT-6.1 Sol code lane APPROVE, zero severity findings;
architecture CLEAR. Both verified supplied hashes and source/diff without
executing imports/tests/models or editing files. Root, not reviewers, owns
runtime evidence. Synthesis APPROVE PRIVATE PRIMITIVE ONLY.

Actual wrapper inventory and atomic opt-in integration remain unimplemented;
mask resolver, real-host D parity/E resource and scientific R0 gates remain
open. No launch/training authority, learning, .alc durability or portability
claim follows. Full unified goal remains active.
