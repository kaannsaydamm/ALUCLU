# Fixed D scientific receipt projection

Status: scoped exporter accepted after independent code APPROVE / architecture
CLEAR, real synthetic RED/GREEN and relevant regression; no launch acceptance.
Parent 07052c41402369921bf205a06014c3b046def282; preserves original scientific
dataclasses and the accepted fixed_d_wire contract. No actual host execution.

## Interface and boundary

fixed_d_projection.encode_d_success(qualification, request) returns the existing
immutable DResult. Only exact existing ParityQualification and nested scientific
receipt types are supported; no recursive asdict, duck typing, callback, object
repr, tensor/optimizer serialization or generic exporter. encode_d_failure takes
only request plus closed stage/category; outcome derives from category. Failure
always has qualification=null and completed_evidence_root=null. Partial scientific
receipts and raw/chained exceptions are not exported or claimed complete here.

Importing the projection module is Torch/Transformers-free. Success first fully
revalidates DRequest bytes/root, then lazily imports existing receipt types. That
call is a post-heavy-runtime operation, not a bootstrap authentication step.
Neither import nor projection invokes qualification, model loading, tokenizer,
GPU initialization, training, filesystem or process APIs. No worker entrypoint
or accepting launch path is added. Producer/admission/resource/history/GPU2
gates remain unresolved and deny actual scientific launch.

Before building arrays or serializing, exact built-in scalar and tuple types and
fixed sequence bounds are enforced at each node: 1296 official rows, 18 witnesses,
18 matrix cells, 18 cases/cell, 6 fixtures, fixture sequences at most71 tokens,
candidate at most64, 2/4 factor names and comparison pairs. Exact dataclass types
exclude user-defined field access/iteration/conversion hooks. Strings are exact
str, capped at schema-specific ASCII-sized limits (metadata256, hashes64,
schedule/names64), before serialization. Integers are exact int, bounded signed64,
converted to decimal strings; -100 is labels-only. Booleans stay genuine bool;
finite measurements require exact Python float values without narrowing, and nullable values
stay null. Unsupported/malformed inputs raise DWireError, no partial DResult.

Every retained field is explicitly projected, including original numeric fixture
root, all cached/incremental hashes, witnesses, case scalar pairs/digests, pending
losses and AdamW factor/moment comparisons. The existing decoder is the final
semantic validator over canonical bytes; it independently enforces original
schedule, request roots, numeric fixture hash, identities and retained comparisons.
No GPU hash equality or invented scientific threshold is introduced. Projection
does not reconstruct tensor allclose/argmax or two-fresh-GPU stability evidence.

The fixed projection shape plus scalar bounds limit encoding before the decoder's
4MiB cap. Existing conservative full-success wire-size argument applies; this
does not claim a benchmarked RSS upper bound or authorize host memory admission.
Caller owns quiescent immutable observations; concurrent mutation is unsupported.

## Verification

RED missing module on synthetic exact scientific dataclass fixtures; then all
three controls complete roundtrip against independent expected wire fixtures,
zero/null/finite and nonzero GPU comparison preservation, malformed exact/nested
types, bool/integer/float confusion, oversized tuples/strings/ints, schedule/hash
drift, forged request, input unchanged, closed errors/interruption and fresh
import isolation. Fixtures instantiate dataclasses only, no real host/assets or
CUDA. Relevant wire/canonical/parity-input/import regressions run in the existing
owned test job with retained exit/tree/log/JUnit evidence. Test launcher remains
closed diagnostic code, never a scientific reservation bypass. Independent code
and architecture closing reviews precede accepted checkpoint commit/push.

Initial owned RED completed in89.276s (3 intended missing-module failures),
dominated by scientific-type/Torch import on this host. RED retains120s useful;
GREEN/regression prospective diagnostic bound is300s plus existing10s cleanup,
not the fixed scientific D allowance or any resource/admission threshold change.
All scientific metadata scalar strings are ASCII in the closed schema; reject
non-ASCII/surrogates before serialization. No original scientific input changed.
