# Checkpoint135: actual rotary decorator incompatibility, preserved RED

Baseline de885aaf3efa6ade4b1eb01e38811fac8b024a96, clean authoritative Desktop
worktree verified before changes. Full objective reread. Prior goal turn PROGRESS.
This checkpoint records a real compatibility failure, not a completed repair.

## Observed installed decorator chain

Read-only inventory imported installed Llama class definitions, used static
forward lookup and traversed __wrapped__/closure cells without invoking forward
or constructing any host. Five classes inspected: rotary, RMSNorm, MLP, attention,
decoder. Diagnostic actual exit0; tool output retained, no standalone JSON log.
Only rotary had wrappers in this inspected scope:

1. torch/utils/_contextlib.py:120 decorate_context wrapper captures ctx_factory,
   a bound _DecoratorContextManager.clone owned by torch.autograd.grad_mode.no_grad,
   with owner field prev of exact bool type, and the wrapped function.
2. transformers/modeling_rope_utils.py:120 wrapper captures
   dynamic_frequency_update, longrope_frequency_update and rope_forward functions.
3. transformers/models/llama/modeling_llama.py:111 original rotary forward.

Observed whole-file SHA256, relative to research .venv/Lib/site-packages:

- torch/utils/_contextlib.py:69e88fddbfb4c222cfc6f50f5b4c9d2acb3f30711233589c79b2e9632c47da18.
- transformers/modeling_rope_utils.py:fd7407b2dc3e16de2507e8619906ff9f84fdda65d49c67a41db4974fd6982a47.
- transformers/models/llama/modeling_llama.py:13e65b752a9c9d8a5c22b83df73009a8940c0eefdc58c101df3eb910e3efc2f9.
- torch/autograd/grad_mode.py:b31662fe50c49c075b9ee00245cfe4fa8230b855b867816ad373dac6c38a2d6b.

Installed no_grad enter saves current thread grad mode into prev and disables
grad; exit restores it. decorate_context calls ctx_factory() on each invocation.
These body observations do not establish complete native/context/helper binding.
Unwrapping to the body for fingerprinting would discard real execution semantics.

## Minimal reproduced failure

A plain empty nn.Module receives only
types.MethodType(LlamaRotaryEmbedding.forward, root) as its forward attribute.
No model/rotary construction, dimensions, weights, configuration or forward call.
computational_state_fingerprint rejects the outer closure's foreign bound clone
method at checkpoint_state.py:292. Minimal diagnostic exited0 because it asserted
that exact current error, not because compatibility passed.

New executable requirement test expects the actual callable to be fingerprintable
and stable without execution. REDv1 actual pytest exit1;2tests,1failure,0errors,
0skips,10.954s. Arbitrary foreign bound-method negative control passes; do not
remove its rejection to make the positive green. Ruff and git diff checks passed.

- XML:results/alc_r0_decorated_dependencies_red_v1_20261004.xml.
- XML SHA256:a40e8e33cc8288dc8435815a54b1d951319b42bb546ef1034a4772d2b66d35da.
- Test SHA256:1817c97b8a859673c5c8033d129e02dada5738b552dda60a8b4e9d939536bbbb.

Reproduce from the authoritative worktree, existing researchPython executable
as recorded in checkpoint134. Set newArtifactPath to a fresh result path:

```powershell
$env:PYTHONPATH='src'
$env:PYTHONDONTWRITEBYTECODE='1'
& $researchPython -B -m pytest -q -p no:cacheprovider tests/test_alc_r0_decorated_dependencies.py --tb=short --junitxml=$newArtifactPath
$LASTEXITCODE
```

## Disposition and next acceptance

Implementation compatibility gap, NOT falsified neural hypothesis or unavailable
hardware. Production source unchanged. No full suite was rerun or claimed green
after introducing this intentional RED requirement. No independent approval or
merge-ready verdict is claimed for an unrepaired component.

Next repair must explicitly schema-bind the reviewed no_grad context factory,
class/method/getter operations and supported state rather than permit arbitrary
foreign methods, repr, unwrap-only or identity-only success. Tests must preserve
phase-context restoration, reject unknown contexts/method/state and deny bound
operation mutations before side effects. Nested RoPE decorator/global helpers
still need disposition; fixing the first rejection cannot certify the whole host.
Then focused/broad regression and independent exact-byte code/architecture review.

No host/assets/corpus/held-out/GPU/optimizer acquisition or model training occurred.
Actual-host attribute inventory remains separately launch-reviewed; synthetic
parity/resource and scientific fresh-process/retrieval-off gates remain OPEN.
Full unified ALUCLU+ALC goal ACTIVE; no thresholds or scientific claims changed.
