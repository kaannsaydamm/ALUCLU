# Fixed D worker bootstrap and process-local settings

Status: scoped denied-bootstrap/settings checkpoint accepted after independent
code APPROVE and architecture CLEAR, with native RED/GREEN/regression evidence.
This does not accept an operational worker or authorize scientific execution.
Parent69a4cfadfd8bc170e94cbba9d74573ba45ea4071. Implements the denied-bootstrap/
settings preparation portion of the accepted fixed-worker design, not a complete
worker/coordinator or first model run. Existing wire/projection stay unchanged.

## Concrete boundary

Add fixed_d_worker module and scripts/run_alc_r0_fixed_d_worker.py. Both import
without Torch/Transformers/NumPy. Production main emits a fixed short ASCII
denial to stderr, empty stdout, exit2 because independently reviewed operator
handoff is not installed. It does not read argv-selected files, stdin, adjacent
JSON, environment approval flags, latest manifests or private sessions; it cannot
acquire approval from transport. No request syntax, file/inventory provenance or
deadline verification is claimed complete by this denied bootstrap.

One private _require_operator_handoff() unconditionally raises a closed error.
main and private _prepare_runtime(request) BOTH invoke it before heavy import,
environment/settings mutation or scientific work. No accepting return, boolean
permit parameter, callback, injectable verifier or public verified constructor.
Opening that seam requires concrete independently reviewed producer/integration;
an always-accept replacement is not a permissible implementation. No qualification
call is enabled by this preparation checkpoint, even by a valid DRequest.

## Fixed runtime preparation

Behind that denial seam, _prepare_runtime reparses DRequest/root through the
existing accepted decoder and derives exactly cpu or cuda:0 from the closed3
controls. Fix HF_HUB_OFFLINE/TRANSFORMERS_OFFLINE/HF_DATASETS_OFFLINE=1 and
CUBLAS_WORKSPACE_CONFIG=:4096:8 before importing Torch. CPU sets
CUDA_VISIBLE_DEVICES=-1. GPU visibility must remain the future independently
pinned coordinator mapping; this helper never discovers/selects a physical GPU
or treats logical0 as proof of physical identity. Source/runtime/asset admission,
entry deadline, history/resource/clock and active monitoring remain prerequisite.
Reject already-imported Torch/Transformers before preparation; fresh process is
required. The denied production path never reaches this dormant preparation.

A private _apply_runtime_settings(backend, device) factors only deterministic
settings for unit testing. Production resolves fixed import torch internally;
no CLI/request/environment field can choose this backend. Recording fakes in
tests are explicit private-helper inputs, not model/host callbacks or attestation.
This helper is not a launch/admission API and has no host/tokenizer/qualifier call.
Do not add generic worker/command infrastructure or scientific module selectors.

Reject an inference-mode context rather than claiming to undo its enclosing
scope. Set ordinary CPU default device, grad enabled and strict deterministic
algorithms (warn_only=False). CPU rejects already-initialized CUDA and makes no
CUDA availability/device/property calls. GPU requires availability, selects
logical0, requires BF16; no fallback. Set TF32 off for matmul and cuDNN, cuDNN
benchmark off/deterministic on; enable math SDP, disable flash/mem-efficient/
cuDNN SDP. Check resulting context with the existing qualification._context
after real settings in the dormant preparation path. Exceptions are terminal,
no retry, dtype/device/grid/tolerance change or silent feature substitution.

The helper deliberately mutates its supplied backend; the production operation
belongs only to a fresh child. CPU unit integration uses a fresh interpreter and
real Torch with CUDA hidden, applies settings once and verifies original _context
without model/assets. Recording GPU tests verify setter order/values and failure
propagation, not real CUDA availability, BF16 numerics, physical identity or
scientific qualification. This scope cannot establish GPU runtime readiness.

## TDD and acceptance

RED3 missing-module bootstrap tests (closed controls). GREEN covers fresh denied
module/direct-script entry, malicious approval-shaped env/argv cannot unlock it,
denied heavy imports, empty stdout/fixed stderr/exit2, main/private preparation
denial before env mutation and no CUDA/scientific execution. Recording settings
cover CPU/GPU route and unsupported device/inference/already-initialized CUDA/
unavailable GPU/unsupported BF16/setter failures without fallback. Fresh real CPU
integration verifies ordinary CPU/grad/strict deterministic context, CUDA not
initialized and no host loaded. No monkeypatch/global replacement or real GPU.
Use existing closed owned-job diagnostic supervision, RED120s, GREEN/reg300s
useful+same10s cleanup, no scientific reservation bypass. Relevant regression
adds this file to accepted projection/wire/canonical/parity-input/import tests.

Independent code/spec and architecture reviews distinguish this preparation
checkpoint from actual worker invocation readiness. Next integration still needs
concrete producer/handoff, bounded provenance/deadline/resource/lease monitoring,
fieldwise fresh-GPU evidence and then original qualification/pilot gates. Owner
method approval is already recorded; no new permission/reset is inferred here.
