# Fixed D bounded transport wire contract

Status: pure codec accepted after independent code APPROVE / architecture CLEAR,
real synthetic RED/GREEN and relevant regression; no exporter/launch acceptance.
Parentc363bd4e412e17f41632399e451d658f2719c549. Supplements fixed-worker design,
not scientific dataclasses, source comparisons, run permissions or frozen plan.

## Scope/API and limits

Proposed fixed_d_wire module is Torch/Transformers/OS-process/filesystem-free.
decode_d_request(data: bytes) and decode_d_result(data: bytes, request: DRequest)
return immutable transport views of validated canonical bytes and SHA256, NOT
VerifiedLaunchContext, scientific PASS or provenance. DRequest is itself only
transport. Result decoder reparses/revalidates its request bytes; constructing
a lookalike/frozen dataclass cannot skip request checks. No callbacks, configurable
limits/tolerances, generic object exporter, file read, launcher or authority API.

Before JSON decoding: exact bytes type, nonempty, <=16384 request /4194304 result
bytes, lexical JSON nesting depth <=12, <=100000 string/scalar/container tokens
(including object-key strings and every object/array opening), and decoded-string token length <=4096
UTF8 bytes. Reject malformed escapes/unterminated strings in bounded decoder.
Depth/string bound scan must respect quoted/escaped braces; it is not a JSON
parser substitute. Use existing RFC8785 canonical parser with duplicate rejection,
strict UTF8/BOM/no-NaN rules and exact byte recanonicalization, no stdlib fallback.
Reject recursion/overflow/encoding errors through DWireError. Fixed shape/count
validation follows; unknown/missing keys and bool-as-number reject at every node.
No successful partial/truncated document. These are implementation transport caps.

API views retain canonical data bytes plus computed root; public construction is
not trusted origin. Never expose a mutable parsed mapping as authority. Decoder
may use private temporary dicts; subsequent consumer always checks those bytes.
An encoder/exporter from real scientific objects is NOT implemented in this scope.

## Scalar spelling

H is exactly64lowercasehex. I is decimal string matching0|[1-9][0-9]*,
length<=19, value0..2^63-1; per-field bounds below also apply. Numeric JSON is
for measurements only. Measurements accept finite JSON int/float excluding bool,
convert to Python float; canonical0 is allowed because RFC8785 spells0.0 as0.
No scientific dtype/norm/tolerance change follows from that JSON spelling.
Genuine booleans remain JSON booleans. Labels allow the additional exact string
"-100" only; other negatives and negative zero reject. Arrays are JSON lists,
never objects or null except explicitly nullable fields. All object keys exact.

## Request

Schema alc-r0-fixed-d-request-v1, EXACT fields:
schema, control_id, reservation_id, declaration_root, source_export_root,
runtime_inventory_root, snapshot_inventory_root, fixture_source_root,
invocation_root, authority_generation_root, original_entry_root,
clock_domain_root, useful_deadline_monotonic_ns, snapshot_path.
Nine *_root fields are H. reservation_id matches[A-Za-z0-9_-]{1,128}.
useful_deadline_monotonic_ns is positive I. Exact closed control IDs and their
derived device/dtype are those in the fixed-worker design (CPU1/GPU1/GPU2 only).
snapshot_path is NFC strictUTF8<=4096bytes, lexical absolute normalized POSIX
(/a/b) or drive-qualified Windows(C:/a/b), forward slash only, no NUL/control,
empty/dot segments, trailing slash, UNC/device prefix or relative drive path.
Windows segments additionally reject reserved device names, forbidden characters
and trailing dot/space. This is lexical transport validation, never existence,
symlink, inventory or local-origin verification. Operational Windows invocation
must separately bind the exact actual pinned local path and assets.

## Result envelope and failures

Schema alc-r0-fixed-d-result-v1, EXACT fields:
schema, request_root, control_id, reservation_id, declaration_root,
source_export_root, runtime_inventory_root, snapshot_inventory_root,
fixture_source_root, invocation_root, authority_generation_root,
original_entry_root, clock_domain_root, outcome, qualification, failure.
All common binding fields equal decoded request. request_root equals SHA256 of
original canonical request bytes. outcome success/error/interrupted only.
Success has failure=null and complete qualification below. Other outcomes have
qualification=null and EXACT failure keys stage, category, completed_evidence_root.
stage is bootstrap_request/bootstrap_binding/bootstrap_inventory/bootstrap_deadline/
worker_context/tokenizer/host/official/matrix/terminal-assets/worker_projection.
category is validation/runtime/oom/interrupted; outcome interrupted requires
category interrupted, error prohibits it. oom is allowed only for worker_context/
tokenizer/host/official/matrix/terminal-assets/worker_projection, not bootstrap.
completed_evidence_root=null or H; a digest is diagnostic, not proof of completion.
Malformed request cannot be bound into a result; its bootstrap diagnostic uses
bounded stderr/nonzero exit instead. Decoder does not inspect OS exit/tree facts.

## Qualification and original schedule

EXACT qualification keys source_device, source_dtype, base_digest, fixtures,
official, matrix. Device/dtype equal closed request-derived cpu/torch.float32 or
cuda:0/torch.bfloat16. base_digest=H; official/matrix repeat all three bindings.

Cell order: prefixes M(ports14), L(ports29), ML(ports14,29); within each ranks4,8,16;
within rank arms capsule,q_lora.18cells. CellKey has EXACT grid_id,ports,rank,arm;
ports/rank use I, strings/grid exactly match original ordered schedule.
ForwardCase has EXACT batch,length,padding_side,explicit_positions,cached;
batch/length use I, booleans remain boolean.24forward cases in original order:
batch1 lengths1,8,127,512, paddingnone, explicitFalse/True; then batch2 lengths8,
127,512, paddingleft/right, explicitFalse/True; then cached batch1 lengths1,8,127,
512, paddingnone, explicitFalse. cachedFalse for first20, True for last4.

## Fixtures

EXACT keys snapshot_inventory_sha256,model_revision,tokenizer_class,fixture_sha256,
fixtures. Inventory equals request snapshot_inventory_root. Model revision is
93efa2f097d58c2a74874c7e644dbc9b0cee75a2. tokenizer_class is dotted ASCII identifier
syntax [A-Za-z_][A-Za-z0-9_]*(\.[A-Za-z_][A-Za-z0-9_]*)+, <=256bytes; it is retained
metadata, not runtime provenance. fixture_sha256=H; fixtures has exactly6rows.

ParityInput EXACT keys input_ids,attention_mask,labels,position_ids,prompt_length,
candidate_ids. Four sequence arrays have equal length3..71; candidate_ids1..64.
input_ids/candidate_ids are I0..49151, maskI0/1, positionsI0..70, labelsI0..49151
or"-100"; prompt_lengthI1..64. Candidate IDs contain noEOS0. Active sequence is
prompt+candidate; labels are -100 for prompt then exactcandidate; mask active1;
positions0..n-1; padding is exactly7EOS0/mask0/label-100 only for last2rows, zero
padding otherwise. Candidate exactly follows prompt and precedes padding.

Pair order corresponds to original (length32,unpadded),(64,unpadded),(64,padded),
each safe/vulnerable. In each pair prompt prefix and prompt_length match, distinct
two candidates repeat identically across pairs; max pair sequence length equals
32,64,71 respectively. Lastpair unpadded sequences equal middlepair plus7EOS0.
Apply original six-fixture schedule validation with lightweight integer values,
without importing heavy checkpoint_observation/parity modules.

For fixture hash reconstruct ORIGINAL payload with numeric Python ints, including
-100, with EXACT keys fixtures (original ParityInput dictionaries), revision and
snapshot_inventory_sha256. SHA256(RFC8785(original payload)) equals fixture_sha256.
Do NOT hash decimal-string wire projection or substitute request fixture_source_root.
Transport cannot prove IDs came from the real tokenizer; verified worker does that.

## Official projection

EXACT official keys source_device,source_dtype,base_digest,cases,nonzero_witnesses.
cases EXACTLY1296 rows in cell order, phaseunmounted/zero/detached, ForwardCase order.
Each row EXACT keys key,case,official_sha256,wrapper_sha256,
incremental_official_sha256,incremental_wrapper_sha256. OfficialKey EXACT keys
grid_id,arm,phase. Key/case matches its position; hashes H. Incremental hashes
both H iff cached, otherwise bothnull. For CPU require official/wrapper hashes
equal, including cached incremental pair (necessary receipt consequence of original
bitwise rule, not a new comparison). GPU digests need not equal: tensors were
allclose/argmax-compared in the reviewed callable, not recoverable from digests.
nonzero_witnesses EXACTLY18 in cell order; EXACT keys grid_id,arm,official_sha256,
mounted_sha256; both H and unequal. Witness proves only a retained changed-digest
assertion unless independently bound to trusted executed worker.

## Matrix projection

EXACT matrix keys source_device,source_dtype,seed,base_digest,cells. Seed is
I20260916.18cells in exact CellKey order; each EXACT keys key,result.
Result EXACT keys cases,pending_losses,accumulation,parameter_names,
parameter_count,base_digest. CountI=1152*rank*len(ports); base equal qualification.
Names exactly factors.{port}.A,factors.{port}.B in port order (2or4strings).
cases EXACTLY18 ordered (zero,repeat0),(nonzero,repeat0),(nonzero,repeat1), each
fixture_index0..5. Each EXACT keys state,repeat,fixture_index,losses,scores,
base_digest,factor_digest. Integers I; digest H, base equal; losses/scores each
2finite measurements. pending_losses2finite measurements. Do not invent a loss
threshold or compare those scalar pairs as a substitute for original tensors.

Accumulation EXACT keys step,factors,exp_avg,exp_avg_sq. StepI1. Each mapping is
ordered list of2-element arrays [exactparameter_name,TensorComparison], with all
names present once/in exact name order. TensorComparison EXACT keys reference_l2,
actual_l2,difference_l2,relative_l2,cosine,exact_zero. Norms finite>=0. exact_zero
is genuineboolean. True requires all3norms0 and both nullable measurementsnull.
False requires reference/actual norms>0, difference>=0, finite relative0..1e-5,
finite cosine[1-1e-6,1], none nullable. Difference0 iff relative0. CPU additionally
requires difference0/relative0 and equal reference/actual norms, as a retained
consequence of original bitwise comparison. Do not require cosine exactly1: the
original float64 normalized dot product can round slightly below1. This checks
retained measurements, not allclose on absent tensors or original-byte proof.

## Acceptance and remaining gates

Design admission concerns only this exact bounded codec. Tests first RED missing
module, then full CPU/GPU success fixtures and errors; schema drift/duplicates/
noncanonical/UTF8/depth/string/byte caps; numeric/string/bool/null cases; each
schedule/candidate/name/root/failure mutation; immutable canonical roundtrip;
synthetic full1296-row worst-size encoding remains below4MiB; no heavy imports.
Boundary/cap tests are transport/resource diagnostics, not peak host-memory proof.
Relevant canonical/parity-input/import-boundary regressions; no model assets/GPU.

Operational producer, actual execution, receipt projection from scientific objects,
source/runtime provenance, lease admission/monitor, factual history and fieldwise
GPU2 stability contract remain OPEN. No actual qualification, pilot/training,
scientific PASS, changed allowance or full-goal completion follows from this codec.
