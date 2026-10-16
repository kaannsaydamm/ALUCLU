# Checkpoint130: observed host dependency inventory, NOT acceptance

Baseline `86551f02f50d4a3a6635b35bec7ec1a4e06ea8c2`; authoritative Desktop
worktree `unified-lifelong-cognition-local`. Previous turn was PROGRESS.

Two actual read-only Python diagnostic invocations exited0. They imported installed
runtime/project code, inspected19 callable bodies using inspect.unwrap,
inspect.getclosurevars/getsourcefile/getsourcelines, and SHA256 of complete source
files. A second invocation inspected2 captured factor closures with seeded CPU
research factors and Identity q projection, without executing those closures.
No host model weights, VerifiedHost, snapshot/corpus/held-out data, optimizer,
CUDA workload or network acquisition was used. Output was tool-captured; no
standalone raw JSON/log file was persisted. This is source/dependency evidence,
not model-run performance, complete dynamic inventory or scientific evidence.

## Observed source bindings

Installed source paths below are relative to research `.venv/Lib/site-packages/`.

| Source file | Observed whole-file SHA256 |
|---|---|
| transformers/models/llama/modeling_llama.py | 13e65b752a9c9d8a5c22b83df73009a8940c0eefdc58c101df3eb910e3efc2f9 |
| transformers/modeling_layers.py | 81469b99e3f933ad78eaf5c90d401a95a02a5f569732c6ed2b7020daaed31953 |
| transformers/masking_utils.py | 50a737f63d8c778a5597fa34ac139049af921f44958205e3e1c29fe2bae77254 |
| transformers/integrations/sdpa_attention.py | 53c7229daca9ade4c5df874194448938c1edc925abbc71809f9750dd66381e6f |
| transformers/loss/loss_utils.py | 83db16b24ce5c3a0642097624aa9a0ae7eb72445c41d8b4d5059a129862fdbbe |

Observed project hashes:

- host_wrapper.py:6b15039c8b0f870b032f432b9d13a494b121d58fdb61d60ec9101ab2aadd8adc
- matched_lora.py:17d504653ccf515d4a8c8298670f1dbbcac020ee3fcff800576704caac41ff57
- research_capsule.py:7a1484f2ff2d485475497a0c62ff717d2b4f95f56460fcf15abf613f3fac401e

## Body-level dependencies that affect next implementation

| Inspected callable (source line) | Observed direct dependencies | Required disposition |
|---|---|---|
| LlamaRMSNorm.forward (62) | torch; variance_epsilon; weight | Bind scalar and actual framework callables alongside registered weight |
| LlamaRotaryEmbedding.forward (111) | maybe_autocast, torch, attention_scaling, inv_freq | Bind body AND decorators; registered inv_freq is already engine-covered |
| LlamaDecoderLayer.forward (295) | norm/attention/MLP child references | Bind actual layer roster/index and child inventory |
| LlamaAttention.forward (243) | ALL_ATTENTION_FUNCTIONS, apply_rotary_pos_emb, eager_attention_forward | Bind selected attention backend and rotary function, not registry identity alone |
| LlamaMLP.forward (174) | act_fn and projection children | Inventory actual activation module/class and underlying function |
| apply_rotary_pos_emb (137) | rotate_half | Bind transitive helper and decorator/kernel dispatch |
| eager_attention_forward (191) | repeat_kv, nn, torch | Bind helper and actual softmax/dropout/matmul dependency paths |
| repeat_kv (179) | tensor expand/reshape | Pinned native runtime plus invocation/shape evidence |
| GradientCheckpointingLayer.__call__ (80) | partial, logger, __class__, implicit checkpoint/cache flags | Deny implicit checkpointing; audit superclass and class-default lookup, not just class identity |
| create_causal_mask (865) | ALL_MASK_ATTENTION_FUNCTIONS, _preprocess_mask_arguments, version flag, and_masks/or_masks, causal/packed/overlay/bidirectional helpers | Separate selected mask registry binding, config route and reachable helper closure |
| sdpa_mask (372) | TransformGetItemToIndex, ignore-mask helpers, vmap/non-vmap expansion, version flag, padding helpers, torch | Pin route-affecting booleans and reachable mask functions/classes |
| eager_mask (539) | sdpa_mask, torch | Do not treat eager mask as independent of SDPA-mask helpers |
| sdpa_attention_forward (79) | use_gqa_in_sdpa, repeat_kv, create_position_bias_mask, NPU flag, logger, torch | Pin selected dispatch and runtime/backend route; no eager fallback substitution |
| use_gqa_in_sdpa (27) | XPU availability flag and torch>=2.8 flag | Bind values consulted by GQA selection, plus input-dependent route |
| ForCausalLMLoss (49) | fixed_cross_entropy, nn | Bind selected loss function including model loss-property resolution |
| fixed_cross_entropy (32) | nn, torch | Bind cross_entropy and any reduction/count semantics |
| wrapper._checkpoint_forward (303) | create_causal_mask, torch, engine/output classes | Audit preparation, loss and terminal state too, not only replay blocks |
| _q_attention_with_projection (230) | attention registry, rotary, eager fallback | Same host-global contract must apply to native-LoRA comparison arm |
| ResearchCapsuleV0.bind_port (71) | factory cast/_PortFactors | Factory inspection alone misses nested apply globals |

Captured `apply` (line83) additionally reads CANONICAL_WIDTH,
NORMALIZATION_EPSILON, F and torch, while capturing actual factor_a/factor_b.
Captured q `project` (line85) reads F/torch/error type and captures factor_a,
factor_b, q_proj. **Explicitly bind capsule epsilon/width and actual F.linear
dependency; captured references do not eliminate these globals.**

`inspect.getclosurevars().unbound` contains attribute names such as reshape,
dtype/config/scaling; it is not a reliable list of unresolved global variables.
No transitive completeness claim is made. unwrap omits decorator wrappers; their
closure/state and kernel paths require separate inspection. Source hashes do not
prove live namespace objects match disk bytes or prevent same-function mutation.

## Observed ambient settings, not a freeze

The second process reported grad enabled=True, CPU/CUDA autocast=False,
float32 matmul precision=highest, deterministic algorithms=False and default
dtype=torch.float32. These were observed, not changed. They do not describe an
actual GPU run or establish the required invocation settings. Checkpoint may
restore autocast context internally; qualification must distinguish preserved
context from mutable ambient/backend settings rather than blanket-checking a
phase-dependent flag and creating false replay failures.

## Concrete next acceptance work

1. Explicitly bind selected mask/attention/loss functions, global scalar values,
   nested factor globals, relevant runtime settings and decorated callable paths.
   Unknown/unreviewed routes must fail, not become identity-only success.
2. Pure counterexamples must change each bound selected registry/scalar/runtime
   dependency and demonstrate denial before preparation/replay side effects.
3. Inspect actual pinned host module/config attributes without executing forward
   only under a separately reviewed inventory invocation; unsupported attributes
   remain errors, not repr/identity fallback. No arbitrary callback certificate.
4. Exact-byte review/freeze and budgeted actual CPU/GPU synthetic parity/resource
   runs still follow the existing plan. No model launch authorized by this audit.

Whole host inventory, callback attachment, actual numerical parity/resource fit,
ALC-R0 capability and durable user learning remain OPEN. This turn changes the
next binding work through observed evidence; it does not close those gates.
