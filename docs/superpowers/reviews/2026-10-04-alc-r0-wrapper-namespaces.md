# Checkpoint150: enumerated actual wrapper namespaces and parent fallbacks

Baseline 3b7b11aa23799e6045f5684acab91d25d04cba20. Extension of checkpoint149,
not a complete actual-host computational certificate or callback activation.

## Contract

Per-method binding reads the actual function.__globals__, not an independently
imported namespace used as a stand-in. Named Torch/nn/session/error/output/cache/
cast/mask/q-helper aliases must match cooperating import-time references.
Function aliases use bounded code/default/keyword-default/closure freezing;
module and class aliases are identity-bound only, not all their methods.

Thirteen selected builtin names bind actual effective resolution: an actual
global shadow takes precedence, otherwise function.__builtins__ is read. That
retained table must be exact dict, at most512 entries with bounded string keys.
Advertised globals['__builtins__'] does not stand in for the actual table.
Table identity, shadow presence and selected binding identities are recorded.

Torch Tensor/int64/strided and nn.Module are explicit identity checks; arange
is a schema-checked native/Python endpoint frozen without invocation. No resolver,
getter, inspected alias or native operation is called by this inventory.

LoRA additionally records parent _bind_checkpoint_block/_run_decoder_layer code
and their actual parent namespaces: those bodies are reached via super() on
unselected ports. Selected override/class identity alone did not cover them.

Import-time baselines are NOT source/runtime authentication. Complete class/
controller semantics, native code, all builtins and transitive globals remain
outside the extension. Existing mask/attention inventory remains in place but
does not imply closure of remaining mask resolver coverage. Default wrapper
callback remains None; no actual-host launch/training authority is issued.

## Executed evidence

| Receipt | Actual pytest exit | Tests/failures/errors/skips | Time | XML SHA256 |
| --- | --- | --- | --- | --- |
| red_v1 | 1 | 23/20/0/0 | 9.909s | 8750927eef58fa330674ed4e640ec9cf684333385a9094f4c9396b0aac5af3c1 |
| boundary_red_v2 | 1 | 2/2/0/0 | 10.167s | 223656b677cd08d4e01712570f39d84eeaf55695076f6281a4b1585b32cb4abd |
| green_v3 (FAILED) | 1 | 71/1/0/0 | 10.229s | d2a307d478f8c1794a371ce3a6e6c5c7d39914b48d0d17cf7fcba59cb53ec15b |
| fallback_red_v4 | 1 | 4/4/0/0 | 8.603s | 2d50dd51f23fe6ecd737cba6e94b9c75c965b1a5ecd7dfdde77705c32f63cfee |
| regression_v5 | 0 | 1060/0/0/0 | 29.423s | c6736ed693d99fc3c774e3d12736dc37b48b4eebd8ee9e7f3a7977fd4819cbee |

Initial RED's two boundary passes were false positives from empty metadata.
Fixtures were repaired before implementation to use nonempty metadata and
match namespace/fingerprint drift explicitly. Boundary RED then failed twice
for unconsumed graphs, proving preparation had not rejected the changed alias.
Matched Torch rebinding was already caught by existing factor coverage.

Initial implementation's remaining failure exposed missing parent fallback
namespace coverage. Four additional RED controls reproduced parent code/default
drift. Parent bodies/namespaces were added without calling super. All prior
failed artifacts remain preserved; the green filename alone is not evidence.

Root consumed original final process82962 terminal exit0, parsed JUnit and all
27 new cases. Scope is checkpoint149's34 selected component targets plus this
test file, not whole repository or real model/platform tests. Real CUDA-host and
real pinned-tokenizer cases remain explicitly deselected; tiny optimizer tests
are synthetic. No actual language-model learning result follows.

## Exact-byte independent review

- checkpoint_wrapper_namespaces.py: 45fc28afeecfc7674133bc8d7c99dd8cda6d2b13947f84464a85b9f4c50887d8.
- checkpoint_wrapper.py: 976d9a57a7c4e3f77fff160ebb53e648759b6875f03c0f30d4c88f2da91527b3.
- test_alc_r0_wrapper_namespaces.py: b70d292737bf9cbddd23d2df67df066288a7ab73656fe415e6c50c026c57500b.

Independent GPT-6.1 Sol code APPROVE, no severity findings; architecture CLEAR.
Both verified hashes and read complete sources/diff without imports, tests,
models/corpus/optimizer or writes. Root owns runtime evidence; reviewers did
not infer pending regression PASS. Ruff and diff checks passed.

Strongest counterargument: the same class/module can retain identity while its
methods or transitive dependencies change. This remains explicitly outside
the enumerated extension. Synthesis APPROVE BOUNDED COMPONENT ONLY. Atomic
wrapper opt-in, remaining class/controller/mask resolver qualification, actual
D/E and scientific R0 remain open; full unified objective stays active.
