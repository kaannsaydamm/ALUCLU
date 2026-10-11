# Checkpoint145: actual-wrapper computational inventory integration candidate

Status: PROSPECTIVE, independent source audit completed; NOT implementation or
actual-host qualification. Baseline61e27750dfbd7073176a614621b1bf2f43d74fee.
Parent: checkpoint-implementation-detail sections C/D. No new scientific
variant, prompt change, fixture change, threshold change or launch authority.

## Observed integration gap

PinnedLlamaCapsuleWrapper initializes one controller with no computational
callback. Its checkpoint forward explicitly refuses that absence. Existing
forward harness uses a constant fake-only callback; it is not a host
certificate. Checkpoint144 enforces pair phase ordering but does not fill this
gap. Prior397-module meta rows show structural compatibility only, not complete
weight-bearing wrapper coverage or forward/backward correctness.

Session engine already guards module/parameter/buffer identities, tensor
metadata, modes, frozen flags, callback identity and parameter/buffer bytes at
boundaries. The computational helper separately covers live base/factor
attributes/configuration and enumerated factor/loss/runtime/attention/mask
dependencies. In particular the mask helper already resolves the wrapper's
create_causal_mask alias, and attention inventory resolves the q-only helper
and rotary dependencies. Do not duplicate those as supposedly missing globals.

Base/factor roots alone do NOT include the owner wrapper's own dispatch/method
selection or extra instance attributes. Passing the whole wrapper naively
also inventories its controller object, which the bounded helper does not
support. Silently ignoring every private attribute would create a bypass.

## Proposed bounded integration, subject to independent audit

1. Add a host-wrapper-specific computational inventory, not generic recursive
   global traversal. Enumerate the two exact wrapper classes and all forward,
   checkpoint-forward, block-builder, factor-getter and q-attention methods
   that affect the admitted cache-free path. Resolve actual class/instance
   dispatch and reject unsupported instance overrides, subclasses, hooks,
   compiled paths and unknown computational attributes before computation.
2. Bind method functions, code/default/closure state and explicitly selected
   namespace aliases using the existing bounded fingerprint conventions.
   Superclass closure cells require explicit known-class support, not arbitrary
   type acceptance. Preserve current enumerated base/factor dependency coverage
   and its native-kernel/transitive-global limitations; no full hostile-host
   security claim. Identity-only callable checks cannot detect same-object code
   or defaults changes, so those need negative tests and structural capture.
3. Expose an explicit owner method (candidate enable_checkpoint_inventory),
   usable only while no lease exists. Keep the single original controller;
   do not rebuild it, implicitly activate checkpointing or change ordinary
   forward behavior. Default callback remains None. Do not accept an arbitrary
   caller callback and call it qualified. Failures leave installation unchanged.
4. Installed getter resolves CURRENT admitted base/factor bindings for each
   session, so legitimate mounting/mode changes between independent disposable
   attempts are not mistaken for within-lease drift. Session-captured fingerprint
   must still reject any drift during an active lease. Installation itself is
   not a receipt authenticating source/runtime/model assets or training access.
5. Do not relax unknown-type/resource limits to make a host pass. Produce an
   exact reject and repair enumerated coverage only after reviewed evidence.

## Independent source-audit findings and mandatory refinements

Both GPT6.1Sol lanes returned BLOCK for qualifying base/factor-only coverage
or treating the proposed integration as implementation-ready. This is a
repairable engineering gap, NOT a falsified learning hypothesis or external
goal blocker. No actual callback is installed by this candidate document.

- Wrapper routing: inventory forward, _checkpoint_forward, factor getter,
  block builder, ordinary decoder path and LoRA q-attention route. Class
  replacement, instance overrides and same-function __code__ mutation must
  fail before execution/replay. Base/factor roots do not include these methods.
- Q registry separation: matched_lora.py:252 resolves its OWN
  ALL_ATTENTION_FUNCTIONS.get_interface and local eager fallback. Existing
  checkpoint_attention.py binds q-helper code and rotary helpers, but NOT that
  registry alias/resolver/fallback. Resolve and bind the actually used alias,
  resolver dispatch/state and route-sensitive selection for eager and SDPA.
  A replacement registry returning a different implementation must fail even
  when checkpoint_state.py's independently imported registry is unchanged.
- Module dispatch/container lookup: existing __call__/_call_impl/
  _wrapped_call_impl/__getattribute__ records capture identities only. Same
  Python function object with altered code/defaults is not covered there.
  ModuleDict.__getitem__ redirects factor capture without necessarily changing
  module registration. Include actual executed dispatch/lookup operations and
  factory cast alias; bind code/defaults or reject unsupported replacements.
- Wrapper namespaces: enumerate actual torch, nn, CheckpointSession,
  CausalLMOutputWithPast and relevant builder aliases. Existing mask alias
  coverage is retained. Binding one helper's code is not binding its globals.
- Atomic installation: install under the ORIGINAL controller lock with
  _active is None verified inside the same critical section. Calling mutation
  guard then assigning outside the lock leaves a lease-entry race. Do not
  invoke an inventory callback under that lock if it can reacquire the lock.
  The callback must be observational; prepare lazy imports before acquisition
  so first-call import side effects cannot be mistaken for live state drift.

Residual mask/attention registry dispatch, vmap classes, tensor methods,
transitive globals and native semantics require named coverage or explicit
rejection before broad actual-host qualification. Scope each component claim
honestly; do not silently convert remaining limits into coverage claims.

Code/spec lane: four HIGH coverage gaps and one MEDIUM residual-coverage
finding, disposition BLOCK. Architecture lane: BLOCK on missing wrapper/LoRA
inventory and atomic installation, WATCH on bounded namespaces/observational
callback. Both lanes inspected sources without executing code. They reviewed
the source architecture/proposal, NOT this subsequently written document's
final bytes. Source hashes below identify their inspected implementation.

Implementation sequence: q registry/dispatch closure repair with RED tests;
module/container callable-state controls; bounded wrapper inventory; atomic
explicit opt-in bridge; exact-byte code/architecture review; clean freeze and
separately reviewed actual-host launch. Keep all existing C/D/E gates intact.

## Required implementation evidence before model invocation

RED/GREEN and the complete current904-case component regression, plus new
tests: default denial; both arms explicit installation; active-lease installation
denial before mutation; repeated installation/controller preservation; missing
or wrong arm; subclass/instance callable override; same-function code/default
mutation; wrapper namespace or route changes not already covered; unknown
attributes; getter replacement; failure cleanup; mount/detach between versus
inside leases; no arbitrary callback certification. Use fake modules only in
these tests and label them accordingly. Preserve all failed receipts.

Independently review exact implementation/source and negative controls before
commit/freeze. A separate reviewed config-only meta invocation can diagnose
wrapper inventory shape without weights/forward, but cannot pass actual D.
Then review exact offline actual-host invocation, one-base cell factory,
verified tokenizer fixtures, resource journal/ceilings/source/runtime/snapshot
hashes. Only then run complete D CPU/GPU matrix, official-forward regression,
then E resources and scientific freeze/R0 evaluation as already ordered.

## Current inspected source hashes

- host_wrapper.py:6b15039c8b0f870b032f432b9d13a494b121d58fdb61d60ec9101ab2aadd8adc
- matched_lora.py:17d504653ccf515d4a8c8298670f1dbbcac020ee3fcff800576704caac41ff57
- checkpoint_state.py:ce992ba6c0ffab0f203d24b8b61a2719b07b0da6bfc2798dfd3d636d489597d0
- checkpoint_execution.py:8f2fb6363e146612cee78bb618c7beef249d84a936e9b457debdd141efbb8be5
- checkpoint_attention.py:c1a893c5bc327e99f14ba3631fdd105d7d5db459804ebf90ddcde82fc1b00801
- checkpoint_mask.py:aec719586209e64fc69679e16d4c34e906e8fcbef9e96a9670777438f64d4c58

No imports/tests/model/config/tokenizer/corpus/GPU/optimizer execution in this
audit turn. No inference of durable learning, resource fit or broad portability.
Full unified objective remains ACTIVE; this candidate cannot replace that goal.
