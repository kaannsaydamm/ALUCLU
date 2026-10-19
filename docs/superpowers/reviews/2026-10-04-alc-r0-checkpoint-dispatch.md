# Checkpoint129: module class dispatch identities

Baseline65023935a0d96fa2a70ca3a367187db9551221ab. Installed Transformers
GradientCheckpointingLayer defines a class __call__ wrapper; nn.Module also
dispatches through _wrapped_call_impl/_call_impl and attribute lookup. Forward
identity alone therefore does not bind all class dispatch identities.

Local class counterexample changed __call__, preserved forward, changed output,
and left the prior fingerprint unchanged. The repaired module record includes
__call__, _call_impl, _wrapped_call_impl and __getattribute__ identities. Four
parameterized local fixtures verify drift and restoration. Only test-local
classes are mutated; no production class or framework global is patched.

This is identity binding, NOT callable-global/code-state/class-property closure
or total computational inventory. Excluded dependencies remain explicit. No
real-host callback attachment, assets, corpus, optimizer update or learning run.

## Parent-observed attempts

Artifacts under results/, prefix alc_r0_checkpoint_dispatch_:

| Artifact | Exit | Tests | Fail/error/skip | Seconds | SHA256 |
|---|---:|---:|---|---:|---|
| red_v1_20261004.xml | 1 | 1 | 1/0/0 | 10.411 | 96ffb645d046c7f09801baf4dca48eada3682c131d05f03b3e391c964e05cef6 |
| regression_v2_20261004.xml | 0 | 197 | 0/0/0 | 11.415 | b9355564813f6435fdab7c13895e3c9dd74347df1a152866b9d459827ad87065 |
| regression_v3_20261004.xml | 0 | 200 | 0/0/0 | 7.897 | 0806ccfc1076b53565dc0805ce9f9cf1ad729e3b1a5ae9cf459ad454cd8ab699 |

Final focused scope: test_alc_r0_checkpoint_state.py, checkpoint_forward.py,
bound_decoder_blocks.py, checkpoint_execution.py, wrapper_checkpoint_lifecycle.py
(each filename starts test_alc_r0_). Use pinned Windows research Python documented
in checkpoint128, PYTHONPATH=src, PYTHONDONTWRITEBYTECODE=1, Python -B, pytest
-q -p no:cacheprovider --tb=short --junitxml=<new unique path>. Parent verified
real shell exits/JUnit/hash and final Ruff clean. Standard logs tool-captured.
This scope does not reuse the old517-case receipt as new full regression proof.

## Review

Candidate checkpoint_state.py SHA25666bc1d53d520cd83e52ede354a818e150a34178a9243faa843d103ec30dae8e5.
Candidate state tests SHA25657b339f09f248b97ac9379c21af279d0655ec4cd8b117b18c1d0d54b6bf5bc3d.
Independent code APPROVE and architecture CLEAR, exact hashes verified by both
without execution; synthesis APPROVE DISPATCH IDENTITY REPAIR ONLY. Strongest
residual: same-function code/default/global mutation is not identity replacement.
Full pinned host inventory,
actual-host parity/resource qualification and scientific gates remain OPEN.
