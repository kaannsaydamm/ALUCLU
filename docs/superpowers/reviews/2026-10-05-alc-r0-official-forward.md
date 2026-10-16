# Checkpoint158 — official-forward regression composition

Status: repaired component code APPROVE / architecture CLEAR at the exact
hashes below, final broad component regression1313 passed. Initial REQUEST
CHANGES / WATCH retained below. Not launch-approved or actual-host evidence.

Original v1 requires comparison against the environment's official unwrapped
base, not only detach against the same wrapper. Retain the original20 cache-free
cases (batch1 lengths1/8/127/512 with inferred/explicit positions; batch2
lengths8/127/512 with unequal left/right EOS padding and inferred/explicit
positions) and4 initial+one-token cache cases at1/8/127/512.

The new fixed one-base schedule runs those24 cases for every declared grid/arm
in original order, with unmounted, seeded-A/B0, and detached phases. There are
1296 ordinary case rows (18grid/arms x3phases x24cases). Cached rows compare
both initial and incremental logits;1512 official/wrapper comparisons total.
Each detached phase first witnesses changed logits with the existing fixed
B=.125, length3 synthetic mount fixture:18 additional witnesses. That regression
fixture is distinct from D's B=((i%17)-8)*1e-4; neither is a learned artifact.
No new scientific optimization grid or acceptance tolerance is introduced.

CPU logits must be byte-equal including signed zeros; GPU uses original
rtol1e-3/atol1e-3 and matching argmax. Shape/vocabulary/device/dtype/finiteness
and inference-only outputs are checked. Cache objects must be distinct and each
branch receives its own initial cache; exact initial/incremental lengths are
observed. Base parameters/buffers, identities/metadata, frozen flags and bytes
must stay unchanged. Only small immutable digest receipts are retained; the
full logits and base-hash work remains real bounded cost, not a resource-fit
claim. No model loader, executable CLI, checkpoint session, optimizer or data
reader is added. Preserve existing old workers/tests and historical evidence.

First19 tests were added before source: RED actualpytest1,19/0/19/0,18.278s;
XML SHA256fded73dba4678649d8f166b06df4c2ecea6789c94d61e2d3fc5a0f367138a383.
Initial focusedv2 actualpytest0,19/0/0/0,96.394s;
XML SHA2562d4414862c6f73c75248ec8385465817cf5c6f21a6a4634d5cc6cdfee5ada3bf.
Wiring tests stub factory/case computation; logits/cache controls use synthetic
CPU tensors. They are not a pinned-host forward execution or D/P11 PASS.

## Initial independent reviews, preserved findings

Both established GPT6.1Sol lanes inspected complete source/tests/dependencies
read-only and verified initial source SHA256
e9949548ab7c76334d1260ea4b7e531f6db32d1031247e96151381e1fa1a776e
and tests SHA25669e24d3c0d61c41fab268412ac2c9dfbc6d6a0e22b477edd3392383fade9ecc8.
Neither executed code/tests/models or consulted the other lane.

Code REQUEST CHANGES, HIGH: shared-base checks do not preserve zero-mounted
factor bindings. Clearing/replacing a zero mount can leave logits identical
while generating mislabeled zero-phase receipts. Require before/after row
checks of effective mount, factor identities/roster/grid/seed/shapes/device/
dtype/bytes/eval/no-grad; unmounted/detached mounts must remain absent. COMMENT:
validate typed per-case receipt key/case/digests/cache fields before publication.

Architecture WATCH: same phase integrity gap; stage attribution must distinguish
preparation/nonzero witness/detach from an actually attempted ordinary forward.
Before/after logits do not independently authenticate declared execution phase.
Factor construction inside inference_mode also needs repair before ordinary
version-counter metadata can be captured. Full logits allocation and repeated
base hashing remain cost concerns to measure in the separate launch envelope.

Added explicit negative controls before repair: zero mount removal/equal-value
replacement, A/B/metadata/mode drift, unmounted/detached remount, witness failure
attribution, malformed/misattributed digest/cache receipts, ordinary factor
construction outside inference context. Preserve initial source/test findings
and all intermediate test receipts. Final exact-byte rereviews and wide
component regression are required after repairs; no author self-approval.

## Repair evidence and final independent reviews

Phase REDv3 personally re-parsed:15 tests/14 failures/0 errors/0 skips,153.150s,
actualpytest1; SHA256
645542ca2515d798556743eab7e7ea540816fc912849d1a54a8d9a44ec06fb2c.
The mode-drift control already passed; A/B drift was rejected only later at
the q-arm rather than at the required first zero row. Other controls exposed
phase/receipt/stage/construction gaps. Do not reinterpret this as15 failing
controls or erase the partial reproducer limitations.

Repaired focusedv4 personally re-parsed:34/0/0/0,47.946s,actualpytest0; SHA256
00f2c794f5ae8e773fecd7a2a8d483019c59f6c1d8041a1146260b615699bc94.
This precedes final mechanical import/buffer checks and eight additional q-arm
mutation/remount controls; it is NOT proof for the final42-case version.

Final source SHA256:
ae997430bb9e9e29acf090234b4df508ae719aeec1b8b16373ebc5639bfd90fe.
Final tests SHA256:
0bd547f8ec87fb14075e65341fb570ce156f0bca0518c6ec0b502b48bf0df52e.
Both existing GPT6.1Sol lanes independently read the complete final files,
verified these hashes, and inspected relevant contracts read-only. Neither
ran imports/tests/models/tokenizers/optimizers/corpora or consulted the other.
Code APPROVE: no remaining actionable bounded-component finding. Architecture
CLEAR: repaired mount integrity and stage/receipt attribution close earlier
findings. Neither verdict assumes pending regression PASS or approves launch.

`_PhaseGuard` validates same base/eval modes, effective/opposite-arm mounts,
exact factor identity, grid/rank/seed, canonical roster/shapes, ordinary finite
FP32 tensors without gradients, fixed B values and identity/version/storage/
byte state before and after each row and the nonzero witness. Across phases
and arms, original seeded A digests must match. Construction disables inference
mode only while creating ordinary factors. Stage and attempted-case tracking
retain accurate completed/current/unrun observations; malformed digest/cache/
schedule receipts cannot enter the completed prefix.

Residual limits: row guards do not authenticate malicious method/global/native
semantics or state restored during a call. Cooperating authenticated source and
runtime remain mandatory external boundaries. Full logits are materialized and
base/factors repeatedly hashed; small retained receipts do not prove peak memory
or wall-clock fit. Actual-host, deterministic/two-process GPU, Linux and resource
evidence are not supplied by the stub tests or these independent verdicts.

Actual D host loading, authenticated runtime/source/tokenizer, resource budget
reconciliation, exact invocation review, two fresh GPU-process reproducibility,
Linux P11, E resource qualification and scientific R0 remain OPEN. Durable
interaction learning/portable `.alc` are not inferred. Unified goal ACTIVE.

## Final regression and reproduction

Root consumed the original86085 terminal handle:actualpytest0. JUnit personally
parsed1313 tests/0 failures/0 errors/0 skips,107.503s, including42 new controls.
Final XML SHA256:
a7f7b09fe62ee96a8ad42866d15d086944529a87b4bddc5f8ebd4544d22179b9.
Source/test hashes stayed identical to the independent rereview bytes. Ruff
check and format --check passed; git diff --check clean. Prior19/34 focused
and both RED artifacts remain first-class history, not final-byte evidence.

Exact invocation/environment, selected files, three explicit real-host/GPU
deselections, original handle, counts and hashes are retained in
`results/alc_r0_official_forward_20261005.provenance.txt`. XMLs retain original
raw bytes via -text attributes. This is selected component regression, not
whole-repository qualification. Full schedule wiring stubs official/wrapper
forward and witness calls over a tiny fake base; actual factor construction
and numeric/cache helper controls are exercised, not pinned-model inference.
