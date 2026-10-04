# Checkpoint146: actual state/upstream/q attention registry bindings

Baseline:f5938cdd1af9bb80a41ac6ff72e8207ce0347a54. This is a bounded eager/SDPA
dependency repair from checkpoint145, NOT complete wrapper callback coverage.

## Contract and executed-path connection

The computational state helper formerly selected attention using its own
imported registry. Actual q-LoRA resolves matched_lora's module-local registry
and eager fallback. New checkpoint_registry inventories all three state,
upstream Llama and q-local aliases before attention selection, without executing
their resolver. Exact AttentionInterface class/instance schema, static dispatch
function/code/closure references, defaults, effective builtin lookup, bounded
ASCII dictionary tables and admitted selected eager/SDPA functions are checked.
Local map static lookup must match the instance field; a data descriptor is
rejected without executing its getter. Both map identity and bounded key/function
identity rosters are recorded. Selected/fallback function states are frozen;
unselected registry entries are identity-bound only, not recursively audited.

Direct-map selection follows the locked runtime's admitted resolver semantics:
local mapping first, global mapping second, eager default if missing. The final
architecture lane read actual CPython3.12 research runtime Transformers source
modeling_utils.py5089-5101 and utils/generic.py1110-1114. Inventory does not call
an untrusted registry just to check what it returns. Unsupported classes,
instance overrides, mappings, keys, endpoints or dispatch fail closed.

Import-time expected code/closure references are a cooperating-process baseline,
NOT source/runtime authentication. No native-kernel or arbitrary transitive
global proof, wrapper/class/module dispatch, ModuleDict or mask-resolver coverage
is implied. The actual wrapper's opt-in callback remains absent by default.

## RED/intermediate evidence preserved

| Receipt | Actual pytest exit | Tests/failures/errors/skips | Time | XML SHA256 |
| --- | --- | --- | --- | --- |
| red_v1 | 1 | 10/10/0/0 | 20.435s | 20a89e091aad3ea854cf1162eaa7adb946ec4c2f6df35861139e1d236e79c726 |
| green_v2 | 0 | 47/0/0/0 | 53.774s | 33c15b9cbc84ab1639bce9d43ac30fc99e9a347639ff134efdc51ab351530d03 |
| descriptor_red_v3 | 1 | 2/2/0/0 | 43.821s | 50b51be8fc51ccd13962b0747e92082a56f40deecbf15c9c02e9ae8e81c29e45 |
| regression_v4 | 1 | 944/103/0/0 | 53.918s | 9ede11b2d5eb52f9fba8f00f97f45a268295c1b543011b9f404b74f044a3c92e |
| builtins_red_v5 | 1 | 2/2/0/0 | 50.305s | 308ebace60625154553c1ddbf4e98bfcadd5643a94d62d86f242c794bab4f84d |
| regression_v6 | 0 | 949/0/0/0 | 25.790s | 050c931a17d44e2edb1254bc447b6eb9e280092a74dc1c4529164f9842ebae47 |

Initial10 failures show missed registry/fallback drift and foreign-registry
acceptance. GREEN precedes expanded mutation/schema controls. Descriptor RED
showed actual attribute lookup could be redirected while the helper read old
instance data. Its repair validates static lookup identity without invocation.

Intermediate regressionv4 is FAILURE, not waived. The negative instance override
fixture used monkeypatch.setattr on an inherited bound method; teardown restored
it as an instance field on the shared registry. Subsequent failclosed checks
rejected the polluted singleton. Repair uses setitem on the actual instance dict
so teardown removes the newly inserted field, plus a no-override postcondition.
All failing receipts remain preserved rather than overwritten/reinterpreted PASS.

Independent code review REQUEST CHANGES identified a HIGH effective builtin gap:
functions retain function.__builtins__ independently of later globals table
rebinding. Isolated FunctionType own-table REDs reproduced both KeyError/super
cases without processwide builtin mutation. Repair uses actual retained table
and actual global shadow priority, recording table/shadow presence; positive
advertised-table rebound and invalid global-shadow controls also cover the fix.

## Exact final bytes and reviews

- Registry:e6791aa0896a8adf200e27abee1b63ac586a5cea41ca6f9ee640e1daa70e1568.
- State:52d7173a131fcc7f002bc31798fe658f634b595d6dc0d0044520b82ee83c0892.
- New tests:a1bd2032d8d105956fe4eb8846d25622ec46c48f2750d56e13863f1164b70f32.
- Initial code REQUEST CHANGES and limited alternate-runtime architectural
  source inspection are retained above. Final independent GPT6.1Sol code
  APPROVE (zero unresolved severity findings) and architecture CLEAR inspected
  repaired bytes; architecture rereview used the actual locked runtime source.
  Both lanes performed static review only, no edits/imports/tests/models/corpus.
- Root consumed original regression handle96489 actualpytest0, parsed949cases
  including45new, verified zero failures/errors/skips and XML hash. Reviewed
  three source/test hashes unchanged. Ruff/diff checks passed. Synthesis
  APPROVE BOUNDED REGISTRY COMPONENT ONLY, not full callback/host acceptance.

Reproduce by prepending tests/test_alc_r0_q_registry_dependencies.py to the
checkpoint144 exact29-target command, retaining its two actual GPU/tokenizer
case deselections and unique receipt name. New45 cases exercise both routes,
preparation/replay drift, schema/foreign resolver and descriptor no-call checks,
actual builtin resolution and fixture cleanup. This is not a full repository,
host, GPU or portability suite. Test runtime is not latency/resource proof.

Next independent engineering gates remain wrapper/module/ModuleDict/mask
dispatch coverage and atomic opt-in integration, then clean frozen exact-byte
actual-host invocation, full D parity and E resource matrix, scientific R0 and
durable interaction learning. No model weights/config/tokenizer/corpus/held-out
or GPU execution in this turn. Tiny factors are not a learned language model.
Full unified objective ACTIVE; no acceptance threshold or scope changed.
