# GPU official-forward repeat assessment: sufficient exact-byte route

Status: bounded pure assessment implemented and accepted after independent code
APPROVE/architecture CLEAR and native TDD/relevant-regression evidence.
Parent02a27ec166977e454b2b41243a465691952925c2. Original scientific plan frozen.
This addresses part of the open fresh-process evidence contract, NOT operational
GPU2 qualification, full fieldwise D stability, a launch permit or a new threshold.

## Scientific scope and storage constraint

Frozen plan section3 requires CPU bitwise parity, GPU BF16 rtol=atol=1e-3,
identical argmax, stable across two fresh processes. Current _compare_logits
enforces finite logits, exact scheduled shape/device/dtype and within-process
official/wrapper parity. Receipts retain SHA256 of contiguous raw tensor bytes,
not tensors. Root binding is not observation provenance or physical GPU identity.

Recomputed24-case schedule:7124 output token positions including four incremental
positions,49152 vocabulary,2bytes/BF16 =>700317696bytes per side per24cases.
18cells*3phases*2sides =>75634311168bytes=70.43994140625GiB for GPU1's
official+wrapper logits alone, excluding witness tensors and metadata. This
uncompressed full-trace strategy exceeds original25GiB research budget. No
storage allocated, model executed, compression/deduplication ratio assumed or
worst-case bound replaced with a hoped-for measurement.

Equal SHA256 values for the SAME fixed shape/dtype and reviewed tensor digest
encoding are sufficient evidence of identical raw bytes under the existing
cryptographic collision assumption. Finite identical tensors necessarily meet
original allclose and argmax requirements. This exact-byte route is sufficient,
NOT necessary. Unequal digests reveal nothing about tolerance or argmax; they
must return tensor-comparison-required, NEVER numerical failure or falsification.
No tolerance tightening. Missing general bounded numerical evidence route stays
explicitly open; do not retry original controls to manufacture missing tensors.

## Exact pure API

New official_repeat_assessment.py imports dataclasses, canonical and fixed_d_wire
only. assess_official_repeat(first_request, first_result, second_request,
second_result) accepts exact DRequest/DResult objects, revalidates request bytes
and roots and result bytes/roots/outcome using existing bounded codecs. Reject
subclasses, forged roots/outcomes, invalid/incomplete receipts or error outcomes.
Bounded parse before any interpretation; no Torch/files/process/observer/callback.

Controls must be exactly GPUfresh1 then GPUfresh2, with distinct reservation IDs
and request roots. CPU, reverse pair, same control and same reservation reject.
Require equal source_export_root, runtime_inventory_root, snapshot_inventory_root,
fixture_source_root, clock_domain_root, snapshot_path. Require equal qualification
source_device/dtype/base_digest and FULL tokenized fixture projection. Original
entry, declaration, invocation and authority-generation roots may differ between
separate legitimate controls; they are not compared as scientific observations.
Coordinator must authenticate each independently, including same physical GPU,
original source/runtime/asset pins, successful terminal owned tree, fresh process
identity and each control's sole a001/initial execution. Pure transport cannot
verify these facts; two fabricated receipts cannot establish real evidence.

Each complete official schedule is already checked by wire codec. Compare all
1296 rows in order, keys/cases identical, both official/wrapper SHA256 slots,
and both incremental slots for216cached rows. Compare both digest slots of all18
ordered nonzero witnesses as a sufficient stronger witness check. Total3060
nonnull digest slots. Count mismatched slots, not rows; null slots are validated
but not counted. No field may silently disappear or be skipped.

Return immutable OfficialRepeatAssessment with kind identical-digests when all
3060 match; otherwise tensor-comparison-required. Fields first_request_root,
first_result_root, second_request_root, second_result_root, compared_slots3060,
mismatched_slots0..3060 bind exact inputs and measurements. No PASS/approved/
fresh-process-proven or threshold boolean. This assesses ONLY retained official
digests; matrix losses/gradients/AdamW values are validated individually by codecs
but are NOT cross-process numerically certified. No final GPU2 qualification
claim until broader fieldwise evidence and operational prerequisites are met.

## Required validation

TDD: intended missing-module RED, equal complete synthetic GPU receipts GREEN;
single changed official/wrapper/incremental/witness digest returns numerical
comparison required, never failed. Same/reverse/CPU controls, same reservation,
changed compared identity/root/fixtures, malformed/truncated/oversized/forged
request/result and partial/error receipt reject. Per-run roots may legitimately
differ. Changed matrix measurement must not be claimed cross-process certified.
Test immutable output,3060slot accounting, no scientific imports through a fresh
child import trap and original input bytes unchanged. Relevant regressions:
wire, projection and denied worker. No model, assets, GPU or held-out invocation.

Independent scientific/code and architecture review before implementation and
after retained runtime evidence. Preserve missing numerical route, real GPU2,
producer/handoff/monitor/lease/resource/history/calendar gates as open. This
component cannot convert a wire success flag into scientific acceptance.
