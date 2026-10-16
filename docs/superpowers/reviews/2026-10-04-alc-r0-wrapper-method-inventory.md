# Checkpoint149: exact-wrapper method/schema/controller bindings

Baseline e4e11ec3a3713455ae058a2991302cfba45f143a. This repairs the method/schema
part of checkpoint145's candidate, NOT complete computational callback coverage.

## Contract

The two exact wrapper types receive explicit schema checks and method records.
Subclasses, instance overrides, unknown instance/registered fields, wrong or
missing exact factor arms and foreign controllers are rejected. Static class
shadows of base/capsule/lora/controller are rejected without invoking getters.
The missing sentinel is unique, so a present class field=None is rejected too.

Enumerated functions: forward, _checkpoint_forward, _checkpoint_factors,
_bind_checkpoint_block, _run_decoder_layer, checkpoint_session,
_assert_checkpoint_mutation_allowed, __getattr__, and LoRA _q_lora_attention.
Their function/code/default/keyword-default/closure state is frozen, along with
globals-dictionary identity, not all effective contents of that dictionary.

Only after dedicated controller validation may generic attribute inventory
skip _checkpoint_controller. Its exact type/owner, lock identity, depth and
base/factor/computational getter bindings are recorded. Active lease/ticket/
thread bookkeeping is intentionally excluded. Inventory takes no controller
lock and invokes no getter or wrapper method. Explicit owner references and
the two known super-class closure cells are supported; arbitrary classes or
module-object references are not generally admitted by this extension.

These are cooperating-process bindings, not source authentication. Complete
controller implementation semantics, effective wrapper namespaces/builtins,
mask resolver, tensor/native behavior and actual wrapper activation remain open.
Default callback stays None. Installing an arbitrary callback is not qualified.

## Executed evidence and failures

| Receipt | Actual pytest exit | Tests/failures/errors/skips | Time | XML SHA256 |
| --- | --- | --- | --- | --- |
| red_v1 | 1 | 30/22/0/0 | 22.728s | 7ead8b7984da4db97ee48daf1ce8912c2357fdf45c68ca4f0a3bb4a130603b51 |
| green_v2 | 0 | 76/0/0/0 | 17.751s | e5aa17eae42b8aa22712b0e77a844fce050ad9ff315e832c63401b949e86a39b |
| regression_v3 (intermediate) | 0 | 1029/0/0/0 | 71.723s | 22d6b93a67c70f74e118440816803a54875aae78af6b0a1449c9de7662fd47a3 |
| shadow_red_v4 | 1 | 4/4/0/0 | 14.050s | 129c4bae4f699e3206bcac3ee337f92bbd8a04fa8c4b06270e37343650c371df |
| regression_v5 (final) | 0 | 1033/0/0/0 | 25.173s | dddb108b6b87682448714e3edda0b12d0c769e3d39c21d9756535beeafdc7051 |

Initial RED rejected every controller object; eight rejection cases passing
there were not proof of specific schema coverage. Initial GREEN preceded
expanded controls. Independent reviewers found present-None class shadows
treated as absent. Four RED controls demonstrated effective lookup changed
while the registered base/mount remained unchanged. Unique-sentinel repair
preserved every previous check. Initial code REQUEST CHANGES and architecture
BLOCK are retained; intermediate1029 PASS is not final repaired-byte evidence.

Root consumed original final process25534 terminal exit0, parsed JUnit and
confirmed all48 new cases. Regression covers checkpoint148's32 component targets
plus the two new files, not all repository/host/platform tests. Real CUDA-host
and real pinned-tokenizer cases remain explicitly deselected. Existing small
optimizer checks are synthetic, not actual language-model learning.

## Exact-byte independent review

- checkpoint_wrapper.py: a0bd493ea9330ef4f9c4ce2f58187253b0ac253a64a68a66cd8eb1e0d7df0df8.
- checkpoint_state.py: dcb5ab55b7aafdd85d72acf60db3ece281a1ed2fbea9a2719fa72edbe2bffa9c.
- test_alc_r0_wrapper_method_inventory.py: d5d71414450571a9ba6e6571055bd0b7968ccecb6b205ab250cd0c2ff3ff6982.
- test_alc_r0_wrapper_field_shadow.py: c214d045dc4a75c727acab963fba534e008f9d762be3de93284d90dee15cba92.

Final independent GPT-6.1 Sol code APPROVE with no remaining severity findings;
architecture CLEAR. Both inspected supplied hashes, complete relevant sources
and state diff read-only; no imports/tests/model/corpus/optimizer or writes.
Root owns execution evidence; reviewers did not infer pending regression PASS.

Strongest residual counterargument: method state and namespace identity do not
bind effective globals/builtins or controller code semantics. This component
cannot alone qualify actual-host execution. Synthesis APPROVE BOUNDED COMPONENT
ONLY. Next steps remain wrapper namespace dependencies, explicit atomic wrapper
opt-in and remaining coverage/invocation review before real D/E experiments.
No neural capability, durable generations, .alc portability or release claim;
the full unified objective stays active.
