# Canonical AdamW adapter contract — pure comparison only

Implements section B of the reviewed checkpoint detail, not the session/wrapper
or real-host parity runner. No optimizer.step, model loading, task assets or
training occurs in the component or its synthetic fixtures.

`compare_adamw_states(reference, actual, reference_factors, actual_factors, *,
reference_base_parameters, actual_base_parameters, expected_step, exact=False)`
requires runner-owned COMPLETE canonical factor maps and nonempty frozen-base
parameter sequences. The adapter cannot discover an omitted model binding;
construction and completeness need independent runner/wrapper checks later.
Calls require quiescent state, not concurrent mutation or step execution.

- Exact torch.optim.AdamW, one parameter group, full group-key set and the pinned
  Torch2.14 schema (including decoupled_weight_decay=True). LR3e-4, betas(.9,.999),
  eps1e-8, weight_decay0, amsgrad/maximize/foreach/capturable/differentiable/fused
  all False. Unknown/missing flags fail closed, not broad version portability.
- FP32 trainable leaf factors, dense materialized CPU/CUDA storage; canonical
  NFC/UTF8 names reused from the tensor checker. No duplicate factor identity
  or storage, base overlap, omitted/extra/duplicate optimizer membership.
- Exact populated state-key set {step, exp_avg, exp_avg_sq} for EVERY factor.
  Required step is explicit integer1 or2; actual scalar CPU FP32 step has that
  exact value (the pinned noncapturable/nonfused optimizer representation).
  Moments match factor shape/dtype/device, have no autograd and are finite;
  second moments are nonnegative. All moments, steps and factors have independent
  storage, conservatively rejecting even disjoint views of one allocation.
- Both arms must be independently stored; comparison state must be disjoint from
  the UNION of both arms' frozen-base storage, including the opposite arm's base.
  Frozen-base storage may be shared between bases only.
  Validate and clone factor/moment tensors before comparisons so result metrics
  expose no live writable aliases. Cloning is not a concurrent snapshot lock.
- Identical complete names and metadata, every resulting factor and moment is
  compared using existing scale-sensitive checks, UTF8 sorted. CPU parity callers
  must explicitly use exact=True; default False supports later GPU tolerances.
  Numerical equality cannot establish that a real update actually executed.

State order/group parameter order is not semantically relevant after binding;
serialized integer IDs and Python object addresses never become result names.
The use of identities internally only checks live membership/aliasing. Results
are frozen scalar metrics and canonical names, not optimizer state artifacts.

Synthetic fixtures manually create states at required steps and perform no
update. Their success means only adapter validation/comparison correctness.
Session leases, captured replay guards, wrapper integration, pinned-host parity,
synthetic resource qualification and real-task learning remain separate gates.
