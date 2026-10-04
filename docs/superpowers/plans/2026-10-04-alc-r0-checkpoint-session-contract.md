# Explicit checkpoint session engine — prospective implementation contract

Implements the reusable engine portion of checkpoint detail section C. The real
host wrappers remain unchanged in this component; their opt-in integration and
actual-host parity/resource invocations are later separately reviewed gates.
No model/assets/corpus, optimizer updates or dataset training in these fixtures.

An owner keeps exactly one explicit CheckpointController, constructed with
owner nn.Module, live base/factor getters and declared layer_count (1..30).
`with controller.session() as session:` obtains a nonnested, owner-thread lease.
Declared layer_count is validated/captured at entry and cannot change during the
lease; ticket completion uses the captured count, not mutable controller state.
Wrapper integration later calls controller.assert_mutation_allowed BEFORE
mount/detach/train/eval/_apply/mutation. The engine cannot intercept arbitrary
Python or .data writes; replay version/mode/identity guards and entry/exit byte
fingerprints detect cooperating-process drift, not a compromised host.

On entry validate training owner/factors, eval frozen base, dense materialized
parameters, one base/factor device, FP32 factors; capture complete registered
module/parameter identities, modes, shapes/dtypes/devices/requires_grad/versions
and storage layout. Capture every named registered buffer identity/stamp too;
buffers may not be trainable. Guard their roster/versions at each entry, and
include their bytes with parameter bytes in namespace-separated fingerprints.
Factor parameter storage must be distinct from frozen-base parameters AND buffers;
storage identity includes device as well as the allocation pointer.
The owner's parameter roster must be exactly base plus factors. Live getters
must continue returning the same modules. Record streamed parameter byte
fingerprints at entry and normal exit. Plain unregistered tensor/state attributes
remain a later host-specific binding-audit obligation. Completeness requires wrapper
inspection: arbitrary user getters cannot establish the real host inventory.

`session.begin_forward(owner, metadata)` allocates a ticket; at most32 pending
forward graphs. It clones a nonempty canonical mapping of detached tensor/None
metadata once per forward. A mapping proxy passed only to bound block callables
prevents structural edits; metadata tensor versions are guarded at entry and
after block return. Caller mutation of original masks/positions is isolated.

`ticket.run(index, bound_block, hidden)` requires ascending indices0..layer_count-1
and invokes torch checkpoint with use_reentrant=False, preserve_rng_state=True.
The block callable receives hidden and the private metadata mapping; its layer/
factor operation must be captured by the caller, inside this callable. Entry
guards run before any block operation, initial execution AND recomputation;
recomputation requires session-owned backward. Engine order does not prove actual
port placement; later wrapper inspection/integration tests must establish that.

`ticket.bind_output(logits)` after every layer installs the output traversal hook.
Layer-output hooks also reject raw/foreign/closed backward and record traversed
gradient-bearing blocks, with at least ONE such block required for binding an
output. An unrelated output cannot make zero gradient-bearing blocks a valid
neural-factor graph. This denies backward on exposed intermediate tensors
and prevents an unrelated output hook alone from consuming a real graph. Final
hook traversal plus every gradient-bearing layer traversal is required to consume
a ticket, only AFTER backward returns successfully. Non-gradient early frozen
blocks are explicitly not invented as gradient-bearing. No input-grad workaround.

`session.backward(loss, retain_graph=False)` accepts only finite real scalar
differentiable loss, explicit False and owner thread. Supports summed losses from
multiple tickets; an unvisited ticket stays pending and normal exit fails. Any
invalid/lifecycle/backward exception in the owner operation invalidates/releases
the lease, clears all factor gradients (including earlier accumulation), and
propagates. Failed or consumed graphs cannot be reused. Foreign-thread/foreign-
owner precondition rejection cannot release another owner's lease. On complete
normal exit check bindings/bytes, invalidate closures and release. Retained
output hooks intentionally remain so old graphs fail closed after scope exit.

Session does not step, clip, schedule or authorize training. Accumulation16 later
performs16 complete forward/backward calls without parameter changes, then steps
only outside the closed lease. Wrapper cache/input/batch/dtype checks remain
integration requirements, not claimed by this engine alone.

TDD: sequential fake blocks and FP32 factors, frozen input requires_grad=False,
checkpoint-off exact output/gradient reference, first/last capture, two pending
summed losses, omission, graph reuse, retain_graph, nested/foreign/thread, mutation
denials, mode/parameter/data drift, metadata isolation, entry-before-recompute
side effect, partial backward failure cleanup and lease reacquisition. Relevant
pure regressions and independent code/security+architecture exact-byte review.
