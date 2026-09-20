# ALC-R0 Same-Base Neural Capability Proof

Status: **PREREGISTRATION DESIGN APPROVED — R0.0 freeze/acquisition
implementation is open. Development training and held-out scoring remain
unauthorized until the R0.0 machine validator passes on a committed,
tracked-clean state.**

Experiment ID: `alc-r0-smollm2-135m-v1`

This plan is the blocking ALC-0 experiment inserted between the completed Task 2
gate and ALUCLU Task 3. It is a scientific claim gate, not a product prototype.
Its only possible positive claim is:

> On the frozen, pinned SmolLM2-135M host, a small detachable neural capsule can
> carry a reproducible retrieval-off capability after a fresh process restart,
> while the base model remains byte/hash-identical.

The experiment may instead finish with reproducible negative evidence. A clean
failure is a valid outcome; threshold changes after observing confirmatory data
are forbidden.

## 1. Binding scope and non-goals

### 1.1 Required proof

The experiment must demonstrate all of the following together:

- a real frozen language model, not a mechanistic toy network;
- a bounded neural artifact attached at one or two explicit residual boundaries;
- no RAG, textual profile, tool access, cache reuse, or training-example access in
  the capsule claim arm during evaluation;
- measurable held-out gain on two real-data capability families;
- a parameter-matched native LoRA positive/control arm;
- detach parity, repeated attach/detach, and fresh-process remount;
- identical base-state hashes before training, after training, after cycles, and
  after remount;
- unrelated-capability retention and declared resource bounds;
- raw per-example evidence, fixed seeds, confidence intervals, and all negative
  results retained.

### 1.2 Explicit non-goals

R0 does **not** claim or implement:

- cross-model, cross-width, cross-depth, dense-to-MoE, or future-model portability;
- a public or stable ALC Neural ABI;
- one capsule carrying multiple capabilities (that is ALC-R1/ALC-1);
- product/capsule encryption, end-user artifact signing, marketplace, enterprise
  mounting, serving, paging, routing, dynamic experts, compiler caches, or
  accelerator kernels; the AES-GCM/HMAC below exist only to enforce held-out
  experimental custody and do not constitute an `.alc` security design;
- zero forgetting, lossless transfer, infinite learning, or safety-by-signature;
- conversion of SmolLM2 into the native ALUCLU model (Tasks 10–11).

No later ALC product-infrastructure phase begins unless this gate passes. If the
complete declared development grid is exhausted or a frozen configuration fails
confirmation, the required top-level result is exactly
`ALC-R0 FAILED IN TESTED SCOPE`. A separate machine field preserves the stage as
`failure_stage = DEVELOPMENT_GRID_EXHAUSTED` or
`failure_stage = HELD_OUT_CONFIRMATION`; the stage distinction never renames the
user-required terminal status.

## 2. Frozen host identity

The sole host is:

| Field | Frozen value |
|---|---|
| Repository | `HuggingFaceTB/SmolLM2-135M` |
| Revision | `93efa2f097d58c2a74874c7e644dbc9b0cee75a2` |
| License declared upstream | Apache-2.0 |
| Architecture | `LlamaForCausalLM` |
| Hidden width | 576 |
| Decoder blocks | 30 |
| Attention heads / KV heads | 9 / 3 |
| Intermediate width | 1536 |
| Vocabulary | 49,152 |
| Maximum configured positions | 8,192 |
| Declared weight dtype | BF16 |
| `model.safetensors` expected bytes | 269,060,552 |
| `model.safetensors` expected SHA-256 | `80521b40281d6ce74e35c9282c22539e75aa0ac8578892b2a59955ef78d55da1` |
| `config.json` expected SHA-256 | `1d556eab73b69c7f11f64c557a2f9c6f440bd4c6b89bb2584a6b498c92603843` |
| `tokenizer.json` expected SHA-256 | `9ca9acddb6525a194ec8ac7a87f24fbba7232a9a15ffa1af0c1224fcd888e47c` |
| `tokenizer_config.json` expected SHA-256 | `4bb9af56a342753d39374f4016a16574cab299fe088e896f425ce3c433f61424` |

These are upstream identities, not yet local acquisition evidence. R0.0 must
download the exact revision, verify every snapshot file, record a canonical
manifest, and load with `trust_remote_code=False`, SafeTensors only, and no
revision fallback. After provisioning, all scientific runs use
`local_files_only=True` and a dedicated `HF_HOME`.

The base state digest covers every lexicographically name-sorted entry returned
by the pinned host's `state_dict(keep_vars=False)`, including parameters and
persistent buffers and excluding nonpersistent buffers by PyTorch definition.
The versioned byte grammar is `ALCBASE\0`, `u16le(version=1)`,
`u64le(entry_count)`, then tagged length-delimited entry records. Each entry is
`0x01`, UTF-8 name, one-byte dtype ID, `u64le(rank)`, `u64le(dim)` values,
`u64le(byte_length)`, and raw little-endian bytes; every variable field is
preceded by `u64le(length)`. Dtype IDs are closed and frozen as
`bool=1,u8=2,i8=3,i16=4,i32=5,i64=6,f16=7,bf16=8,f32=9,f64=10,c64=11,c128=12`;
an unlisted dtype is a validator error. Each detached tensor is copied to
contiguous CPU layout without numeric casting before encoding.

Tied/aliased entries are still framed under every published state-dict name.
The separate version-1 alias record is `0x02`, `u64le(group_count)`, then groups
ordered by their lexicographically first member. Each group is exactly `0x10`,
`u64le(stable_group_index)`, `u64le(member_count)`, followed by that many member
records. A member is `0x11`, `u64le(name_utf8_length)`, UTF-8 state-dict name,
`u64le(storage_offset_bytes)`, `u64le(storage_span_bytes)`, `u64le(rank)`, then
exactly `rank` `u64le(dimension)` values and `rank` two's-complement
`i64le(stride)` values. A group is discovered within one load from overlapping
byte intervals in the same untyped storage, but its stable index is its one-based
order, never a pointer or process-local storage ID. Members are name-sorted and
singleton groups are included. The digest stream terminates with
`0xff`; process addresses and allocator identifiers are forbidden. Snapshot-file
hashes remain a separate source check. A hand-built shared-storage/overlap fixture
and two independent model loads must reproduce both the main digest and alias
record byte-for-byte before training.

## 3. ResearchCapsuleV0

R0 uses a research-only same-base NABI profile. It deliberately avoids a learned
bridge so the experiment isolates neural attachment rather than cross-host
translation.

For hidden state `h` with width 576 at selected port `p`:

```text
z       = h / sqrt(mean(h^2, dim=-1, keepdim=True) + 1e-5)
delta_h = (alpha / rank) * B_p(A_p(z))
h_next  = h + delta_h
```

Binding details:

- canonical width `d_c = 576`;
- same-base bridges `E = D = I_576`, represented in the manifest but not stored
  as trainable matrices;
- `A_p` shape `[rank, 576]`, `B_p` shape `[576, rank]`;
- no bias, learned norm scale, gate, router, expert bank, textual payload, or
  durable memory access;
- separate factors per port;
- `A_p` uses the same deterministic Kaiming-uniform initialization rule and
  initialization seed as the matched LoRA arm; `B_p` starts at exact zero;
- scaling uses `alpha = rank`, so the forward multiplier is exactly one;
- capsule master/train tensors, optimizer state, and canonical serialized
  tensors are FP32; capsule math accumulates in FP32 and casts the residual
  delta back to the BF16 host activation dtype;
- only factor tensors plus an immutable canonical JSON manifest are serialized,
  using SafeTensors for tensors;
- all base parameters are frozen, absent from the optimizer, and have no
  gradients or optimizer state.

The host wrapper explicitly iterates pinned decoder blocks and invokes capsule
modules after named block outputs. Monkeypatching and
`register_forward_hook` are forbidden. `detach` removes the capsule execution
path. Conformance compares the wrapper with no capsule against the official
`LlamaForCausalLM.forward`, not merely detach against the same wrapper. The
matrix covers batch sizes 1 and 2; unpadded lengths 1, 8, 127, and 512; left and
right EOS padding; unequal attention masks; explicit and inferred position IDs;
and `use_cache=False` plus one-token incremental `use_cache=True` decoding. CPU
FP32 logits must be bitwise equal. Deterministic GPU BF16 logits must satisfy
`rtol=1e-3`, `atol=1e-3`, preserve argmax tokens, and be stable across two fresh
processes.

The P6 zero control is a separately instantiated, never-trained artifact at the
selected grid whose every FP32 `A_p` and `B_p` element is exact positive zero.
Its manifest identifies control kind `all_factors_zero`, contains no optimizer
state, and uses the same port/rank/host fields as the trained capsule. Its
SafeTensors bytes and SHA-256 are produced by the canonical serializer and
fixture-tested. This is distinct from the ordinary trainable initialization
(Kaiming A, zero B), although both must be forward no-ops before training.

### 3.1 Frozen port/rank development grid

Ports are zero-based decoder-block outputs:

| Grid prefix | Port set | Meaning |
|---|---:|---|
| `M` | `{14}` | midpoint residual boundary |
| `L` | `{29}` | final block output before final norm |
| `ML` | `{14, 29}` | bounded two-port path |

Ranks are `{4, 8, 16}`. The complete search grid is:

```text
M-r4, M-r8, M-r16,
L-r4, L-r8, L-r16,
ML-r4, ML-r8, ML-r16
```

Trainable parameter counts are exact:

| Ports | r=4 | r=8 | r=16 |
|---:|---:|---:|---:|
| 1 | 4,608 | 9,216 | 18,432 |
| 2 | 9,216 | 18,432 | 36,864 |

The maximum is below 0.1% of the host. Its canonical FP32 tensor payload is
147,456 bytes (the BF16 inference copy would be 73,728 bytes). The final
canonical artifact, including manifest, must remain at or below 256 KiB.

### 3.2 Exact parameter-matched LoRA control

The native control applies an explicit low-rank update to `self_attn.q_proj` at
the same block set and rank. Each selected `q_proj` is 576 by 576, giving the
same `1,152 * rank` trainable parameters per block as the capsule.

The comparator is implemented as an explicit non-merged wrapper, not
`merge_and_unload`. Its A/B initialization, scaling, dtype policy, optimizer,
training examples, example order, maximum training budget, and random seeds
match the capsule arm. Each arm selects its checkpoint epoch independently by
the frozen dev rule, so neither arm is intentionally under-tuned. A PEFT
forward-equivalence test may validate semantics, but PEFT serialization or
implicit target discovery is not the scientific source of truth.

Equal parameter count does not make post-residual capsule adaptation identical
to q-only LoRA. A non-blocking best-practice reference therefore trains standard
q+v LoRA at rank 8 across all 30 blocks. It is explicitly larger (460,800
trainable parameters), is reported separately, and is not used for P1 or P5.

## 4. Capability and retention suites

R0 trains a separate capsule per target family. Passing both families establishes
repeatability of the same attachment primitive; it does not claim one
multi-capability capsule.

### 4.1 Target family A: Banking77 intent routing

| Field | Frozen value |
|---|---|
| Dataset source | `PolyAI-LDN/task-specific-datasets`, `banking_data/` |
| Source commit | `9d081458ff52e53cf7e848f414e6e9344e4e6696` |
| Source Git blobs | categories `cdd2a5c77a4079a455f8fb7e751d1ecee0e2a5a4`; train `98e2543cf482d0dca7bfb175ebe35d98efad95be`; test `799687a8367359432985b8b13d85a2baf73f92dd` |
| Dataset-card snapshot | `PolyAI/banking77@90d4e2ee5521c04fc1488f065b8b083658768c57` |
| Upstream license declaration | CC-BY-4.0 |
| Primary metric | macro-F1 over 77 intents |
| Development data | deterministic train/dev partition of official train |
| Confirmatory data | official test, sealed until freeze receipt |

The official training set is first grouped by normalized-utterance SHA-256
across all labels. Normalization is Unicode NFC, CRLF-to-LF, and outer whitespace
stripping. Any digest with conflicting labels fails R0.0. For a same-label
duplicate group, retain only the lexicographically smallest source ID and record
the aggregate removed count/root. Split the resulting unique examples
independently within each label: sort by SHA-256 of `20260916`, a NUL byte,
canonical label, a NUL byte, and normalized utterance UTF-8. The first
`floor(0.20 * label_count)` examples become dev and the remainder train. The
algorithm, ordered IDs, and roots are fixture-tested; no library-specific random
split is used.

Prediction uses frozen candidate-label conditional log likelihood. The common
interface prompt contains the user utterance, the fixed ordered label vocabulary,
and an `Intent:` answer boundary. Loss is computed only on the target label
tokens; prompt and padding tokens use label `-100`. Each candidate is encoded as
exactly one ASCII space followed by its canonical lowercase label, with no BOS,
EOS, or empty candidate. Candidate score is the arithmetic mean of conditional
log probabilities for all candidate tokens; shared prefixes are rescored for
each complete candidate. Exact score ties use UTF-8 byte lexical label order.
The token-ID map and a hand-computed scoring fixture are frozen before training.

### 4.2 Target family B: CodeXGLUE/Devign defect detection

| Field | Frozen value |
|---|---|
| Dataset | `google/code_x_glue_cc_defect_detection` |
| Repository revision | `69bd48c03223c2104342acd9a807caf61ac3efb8` |
| Upstream license declaration | C-UDA |
| Primary metric | macro-F1 |
| Companion metrics | balanced accuracy and Matthews correlation coefficient |
| Development data | official train and validation after frozen clone filtering |
| Confirmatory data | official test after the same frozen filtering |

Before training, code is normalized by the committed preprocessing function.
The development worker computes exact normalized SHA-256 and the frozen MinHash
rule only over train and validation. Any train/validation group overlap is
excluded from validation. Test-spanning duplicate handling is performed later
inside the independent sealing worker described in section 8.1; development
never receives test text, labels, group assignments, or exclusion identities.
Dataset bytes are never committed because their license is research-specific;
only allowed manifests and hashes are committed.

The duplicate rule is fixed: decode UTF-8 strictly, normalize Unicode NFC,
convert CRLF/CR to LF, remove trailing ASCII whitespace per line, and remove
outer blank lines; do not strip comments or rename identifiers. Tokenize with
the committed regex into identifiers, numeric literals, quoted string/character
literals, and individual C operators/punctuation. Form sets of five-token
shingles. Exact normalized SHA-256 equality always joins a group. Candidate
near-clone pairs are generated with 256-permutation MinHash seed `20260916` and
LSH candidate threshold 0.85, then joined only when exact shingle Jaccard is at
least 0.90. Union-find roots choose the lexicographically smallest member ID.
The token regex, hash implementation, MinHash coefficients, package version,
and adversarial duplicate/nonduplicate fixtures are frozen in R0.0.

The union-find root is the data and statistical unit. Within each source split,
retain only the lexicographically smallest member ID of each root. Any root with
conflicting labels fails R0.0. A root present in train is removed from
validation; the sealer removes any test root present in train or validation.
Metrics therefore give one vote to one retained root, and bootstrap vectors
sample root IDs rather than pre-filter examples. The sealed test set must retain
at least 1,500 roots and at least 250 roots per class; otherwise R0.0 fails.
Manifests record aggregate source-member/root counts. Before terminal scoring,
the development side sees only those counts and one ciphertext SHA-256/Merkle
commitment for the complete sealed shard; it receives no per-group root, stable
linkable root, member identity, or test-derived exclusion identity. Plaintext
group roots and the full exclusion ledger remain encrypted under the sealer key
until the terminal transaction commits, then enter the evidence package. A
secret-keyed internal commitment may be used for sealer bookkeeping but is never
released to development. Fixtures cover transitive A-near-B-near-C groups.

The common interface prompt contains the function and the fixed labels
`safe`/`vulnerable`, ending at `Verdict:`. Candidate scoring and label-only loss
follow the Banking77 rule.

All classification statistics use an immutable label universe: the canonical
77-label Banking order or `[safe, vulnerable]`. For each label,
`precision = TP/(TP+FP)` and `recall = TP/(TP+FN)` with a zero denominator
defined as zero; `F1 = 0` when `precision+recall = 0`. Macro-F1 is the unweighted
mean over the full label universe even when a bootstrap replicate contains no
true or predicted example for a label. Balanced accuracy is the same fixed-label
mean recall. Binary MCC uses the standard confusion-matrix formula and is zero
when its denominator is zero. Hand fixtures include absent-class, no-prediction,
all-wrong, and perfect cases.

### 4.3 Unrelated retention suites

| Role | Suite | Frozen repository revision | Metric |
|---|---|---|---|
| unrelated-capability control | `Salesforce/wikitext`, `wikitext-2-raw-v1` | `b08601e04326c79dfdd32d625aee71d232d685c3` | next-token perplexity |
| old-skill/host-capability control | `EleutherAI/lambada_openai` | `900124bf3b8235c6daf21033af9948b3f07346c4` | exact last-word accuracy |

WikiText consumes only the frozen `test` split. Each nonempty source row is an
independent document after Unicode NFC and CRLF-to-LF normalization; rows with
fewer than two tokenizer IDs are excluded and their IDs/root recorded. Add no
BOS/EOS. Score each document independently in windows of 1,024 tokens with
stride 512, masking every target token already scored by an earlier window and
the first token of the document. Perplexity is
`exp(total_negative_log_likelihood / total_scored_tokens)` across all retained
documents. Bootstrap sampling uses document IDs and recomputes both numerator
and denominator. Empty windows and cross-document context are forbidden.

LAMBADA consumes only the frozen `test` split. Normalize each text with Unicode
NFC and strip outer whitespace, then split at the final Unicode-whitespace run
into context and gold last word. Exclude and record examples with an empty side
or a gold word longer than 16 tokenizer IDs. The prompt is context plus exactly
one ASCII space. Greedy decoding produces at most 16 tokens and stops after the
first decoded Unicode-whitespace run following a nonspace character or at EOS;
the text before that boundary is Unicode-NFC normalized and outer-whitespace
stripped. Accuracy is case-sensitive exact Unicode-string equality with the
gold word. No punctuation/case folding or alternate answers are allowed. Both
retention algorithms have hand-calculated masking, likelihood, decoding, and
normalization fixtures frozen in R0.0.

Both retention test splits are confirmatory-only. They enter the same independent
sealing path as the target test sets, are unavailable to development selection,
and open only inside the terminal scoring transaction. Development eligibility
does not inspect WikiText or LAMBADA scores. Their source-row/example IDs,
exclusion counts, ciphertext commitments, minimum retained counts, and scoring
algorithm hashes are frozen before target development begins; plaintext content
and per-example identities remain sealed.

Cross-family swap is also mandatory: mount the Banking capsule on Devign and the
Devign capsule on Banking. A deterministic procedural diagnostic may be added
for debugging but cannot substitute for either blocking real-data family.

### 4.4 Dataset freeze boundary

Repository revisions above are identifiers, not sufficient byte evidence. R0.0
must acquire the revisions, record every consumed file SHA-256 and byte length,
freeze preprocessing code, and produce canonical development split manifests.
The development principal acquires only model/card/license material and target
train/validation bytes. Every target and retention confirmatory test split is
acquired by `ALUCLU_R0_SEALER` inside `ALUCLU-R0-EVAL` and streamed directly into
the same audited normalization/filter/encryption command. Raw or normalized test
bytes never enter a development-readable Windows path, cache, WSL distribution,
environment, descriptor, or artifact. The sealer records exact source URL,
revision/blob identity, response-byte hash/length, code/policy hash, and the
encrypted-shard commitment. No target development training begins until the
allowed development artifacts and sealed-shard receipts are committed. The
held-out scorer refuses to run without the confirmatory freeze receipt.

## 5. Arms and information boundaries

Every arm uses the same tokenizer, label vocabulary, maximum sequence policy,
scoring code, and held-out examples.

1. frozen base;
2. base plus textual task/profile definitions, no examples, using only the
   frozen control budget inside the total sequence limit;
3. base plus BM25 RAG over training examples, using only the frozen control
   budget inside the total sequence limit;
4. exact parameter-matched native `q_proj` LoRA;
5. `ResearchCapsuleV0` with retrieval/profile/tools OFF;
6. exact zero-initialized capsule;
7. label-shuffled capsule trained with the same budget;
8. wrong-family capsule;
9. ten repeated attach/detach cycles;
10. fresh-process remount with retrieval, tools, profile, prior KV cache,
    training-data filesystem access, and network explicitly unavailable.
11. non-blocking standard q+v LoRA reference described in section 3.2.

RAG is a mechanism control and is reported honestly; the capsule is not required
to outperform it. Total target-task sequence length is 1,024 tokens. The common
interface, query, answer boundary, and candidate together may use at most 512;
the textual-profile or RAG insertion may use the remaining at most 512. The
answer boundary and candidate are never truncated. Banking labels precede the
query; Devign code uses deterministic head/tail truncation after reserving fixed
prompt/answer tokens. Exact field priorities and token counts are fixture-tested.
BM25 freezes tokenizer, corpus fields, `k`, score/tie ordering, formatting, and
the no-fitting-example result. The capsule claim arm receives only the common
task interface and evaluation query; it receives no filler for unused tokens.

The textual profile is generated deterministically. Banking emits, in canonical
label order, `The intent label <label> means <label with underscores replaced by
single ASCII spaces>.` Devign emits exactly `The label vulnerable means the
function contains a security-relevant defect. The label safe means no such
defect is identified.` The UTF-8 bytes, tokenizer IDs, and SHA-256 of each
rendered profile are frozen in R0.0.

BM25 uses Unicode-NFC lowercase text and Python-regex `\w+` terms under the
locked runtime, retaining underscores. Banking documents are normalized
utterance plus `\nIntent: <label>`; Devign documents are normalized code plus
`\nVerdict: <label>`. Use Robertson BM25 with `k1=1.5`, `b=0.75`, and
`idf = log(1 + (N - df + 0.5) / (df + 0.5))`; repeated query terms contribute
once. Retrieve `k=8`, sort by descending IEEE-754 score then UTF-8 source-ID
bytes, and render `Example <rank>:\nInput: <input>\nAnswer: <label>\n`. Each
example is head/tail truncated to at most 64 tokenizer IDs after reserving its
fixed framing. Include ranked examples until the next whole rendered example
does not fit the 512-token control budget; then stop. If the first cannot fit,
the result is empty. Corpus rows, index arrays, query terms, scores, selected
IDs, rendered bytes, and hashes are retained. Hand fixtures cover ties, unknown
terms, repeated terms, truncation, and an empty result.

## 6. Determinism, execution environment, and resource contract

Scientific runs use a dedicated, non-OneDrive tree rooted at:

`C:\Users\kaann\AppData\Local\ALUCLU\research\alc-r0-smollm2-135m-v1`

It contains separate environment, HF cache, datasets, run outputs, and immutable
manifests. The repository contains code, small canonical manifests, hashes, and
selected evidence only.

R0.0 provisions fresh Python 3.12 environments with
`system-site-packages = false`, produces separate fully hashed
`windows-training.lock` and `linux-eval.lock` files, and records Python, Torch,
CUDA runtime, driver, GPU, CPU, RAM, pagefile/swap, filesystem, and free-space
details. `linux-eval.lock` is bound to the immutable evaluator rootfs manifest,
kernel identity, distro package manifest, and rootfs digest. The currently
installed global/.venv313 packages are probe evidence only and are not an
acceptable scientific environment.

Binding execution defaults:

- Windows x64 training phases, one process, one RTX 4050 Laptop GPU;
- BF16 host weights and activations; FP32 capsule/LoRA master tensors,
  accumulation, optimizer state, and serialization;
- microbatch 1 and gradient accumulation 16, for an effective batch of 16
  examples; OOM recovery preserves this effective batch;
- maximum total training/evaluation sequence length 1,024 for target tasks;
- `num_workers=0`, guarded main entry point, eager attention;
- `use_cache=False` during training;
- deterministic algorithms enabled, cuDNN benchmark disabled, TF32 disabled,
  and math SDPA used in the reference lane;
- greedy/candidate-scoring evaluation only; no sampling or beam search;
- tokenizer padding side and pad policy frozen in the manifest; because the
  base tokenizer has no independent pad token, EOS is used for padding while
  attention masks and `-100` loss labels prevent pad supervision;
- at least 20 GiB host free space preserved before each run;
- no user processes are terminated automatically to free memory.

The phase/platform contract is immutable: model/card/license and target
train/validation acquisition, development preprocessing, development,
confirmatory retraining, artifact serialization, and the resource harness run
under the hashed Windows x64 training environment. Confirmatory target/retention
test acquisition, test preprocessing and sealing, P9 fresh-process remount, all
held-out scoring, and transaction validation run only inside the service-owned
Linux evaluator environment. P11's full
official-forward conformance matrix must pass independently in both environments
against that environment's unwrapped base reference. Cross-boundary artifacts
are SafeTensors or RFC-8785 JSON/JSONL only, copied through a broker-created
staging directory, hashed before transfer, named in the broker-authenticated
transaction intent, rehashed by the broker and scorer, and mounted read-only. The
intent is RFC-8785 JSON and is authenticated as HMAC-SHA-256 over
`ALC-R0-INTENT-V1\0 || canonical_intent_bytes` with a distinct random 32-byte
intent key held only by `ALUCLU_R0_SEALER`; the broker verifies it before launch
and binds its SHA-256/HMAC to the launch receipt. Pickle, Python
object serialization, mutable cache transfer, and unmanifested files are
forbidden. P9 compares Linux pre-mount, mounted, detached, and fresh-remount
states; P10 compares the canonical version-1 base digest across both independent
Windows and Linux loads.

OOM recovery may only reduce microbatch and increase accumulation so effective
batch, sample order, optimizer updates, and schedule remain identical. If that
still fails, record the minimum measured requirement and request authorization
before any paid external compute.

### 6.1 Enforced fresh-process isolation

Development may exercise the mechanism in the installed WSL2 `kali-linux`
distribution, but confirmatory scoring uses only the service-principal-owned
`ALUCLU-R0-EVAL` distribution described in section 8.1. R0.0 freezes that
distribution's kernel, distro package/root hash, Python environment, and
evaluator-root inventory. Each arm worker is launched with Linux user, mount,
network, and PID namespaces:

```text
unshare --user --map-root-user --mount --net --pid --fork ...
```

The inherited WSL filesystem is not treated as isolated. The launcher makes
mount propagation private, bind-mounts a hash-verified minimal rootfs, performs
`pivot_root`, unmounts and removes the old root, mounts a new `/proc` for the PID
namespace, closes every inherited descriptor above stderr, sets
`no_new_privs`, drops the capability bounding set and supplementary groups, and
executes the scorer as an unprivileged UID/GID. All Windows-drive mounts and WSL
home/cache paths are absent. Required CUDA device/library nodes are individually
allowlisted. Inputs/rootfs are read-only and one empty output mount is writable.

Each logical scoring transaction launches separate clean rootfs policies:

- retrieval-off root for base, capsule, q-only/q+v LoRA, zero, label-shuffled,
  and wrong-family arms: model/tokenizer, selected neural artifact, common
  prompt/evaluator, and sealed shard only;
- profile-control root: the same base assets plus only the exact frozen profile;
- RAG-control root: the same base assets plus only the frozen read-only BM25
  index and allowlisted retrieved-record payload store.

No arm can see another arm's additional assets. A coordinator outside the arm
roots passes the same opaque sealed example IDs to every arm and joins outputs
only by those IDs after each subprocess terminates. Arm policy/rootfs/mount
manifests and hashes are part of the transaction intent.

Before scoring, mandatory negative probes must fail: opening/enumerating the old
root, every Windows drive, WSL home/cache and known training root; opening a
sentinel training record; resolving DNS; TCP connection to a fixed external IP;
and HTTPS to Hugging Face. The complete in-namespace mount/file inventory must
equal the arm allowlist, inherited-descriptor inventory must be only stdin,
stdout, and stderr, and write probes outside the output mount must fail. The
worker inventory, namespace/root transition, mount/link/capability tables,
negative-probe outputs, stdout/stderr/exit, and policy SHA-256 are bound into the
run receipt. A normal same-user child process and a self-authored `offline=true`
JSON field do not satisfy this gate.

## 7. Development search and immutable selection

### 7.1 Development seeds and grid

Development training seeds are `20260917` and `20260918`. Run all nine grid
configurations on both capability families for both seeds for both the capsule
and exact-count q-only LoRA: 72 primary development runs. The non-blocking
standard q+v LoRA reference adds four development runs (two families by two
seeds).

The optimization contract is fixed, not searched:

| Field | Value |
|---|---|
| Optimizer | AdamW |
| Learning rate | `3e-4` |
| Betas / epsilon | `(0.9, 0.999)` / `1e-8` |
| Weight decay | `0.0` |
| Gradient clipping | global norm `1.0` |
| Maximum epochs | 3 |
| Scheduler | cosine decay to zero |
| Warmup | first `ceil(0.05 * total_updates)` updates |
| Effective batch | 16 examples |
| Dropout | 0 |
| Checkpoints | end of epochs 1, 2, and 3 |

For each family/grid/arm, choose one checkpoint epoch by highest two-seed mean
dev macro-F1; ties within `1e-12` prefer the earlier epoch. The capsule and LoRA
select checkpoint epoch independently but share the same maximum data/update
budget. Confirmatory retraining uses the frozen epoch selected for that
arm/family/grid. The label-shuffled arm uses the intended capsule's frozen epoch
and never tunes on held-out labels.

The fixed 200-step fit/throughput pilot uses training data only and exactly the
contract above. It may change nothing. It passes only on finite loss/gradients,
resource fit, a preregistered runtime ceiling, and exactly 200 successfully
journaled optimizer updates per job. Fewer or more updates make that job
`INVALID` or `BLOCKED`, never PASS. It cannot eliminate a grid point or choose
parameters by train/dev performance. Any optimizer or schedule change requires
a new experiment version before held-out access.

The pilot is four jobs: `M-r8` capsule and q-only LoRA on each family with seed
`20260916`, exactly 200 successful optimizer updates and at most two wall-clock
hours per job. The local program budget is 600 total measured GPU-hours across valid,
invalid, failed, and retried attempts, 45 calendar days from the
first development job, and 25 GiB under the isolated research root while always
preserving 20 GiB free on `C:`. A job may receive one exact crash resume and one
rerun after a documented implementation repair; environment-invalid resource
runs may have at most three total attempts. Every attempt consumes the global
budgets and remains in evidence.
The pilot projects the full immutable matrix from measured updates/s and
evaluation throughput. Projection beyond any ceiling records
`LOCAL EXECUTION BLOCKED BY MEASURED RESOURCE ENVELOPE`, measures the minimum
compute/storage requirement, and asks for explicit external-compute authority;
it does not shrink the grid, lower thresholds, or silently extend the budget.

### 7.2 Development eligibility

A configuration is eligible only when, on the two-seed aggregate:

- capsule dev gain is at least +5 absolute macro-F1 points on each family;
- exact-count q-only LoRA dev gain is at least +5 absolute macro-F1 points on
  each family;
- loss and gradients remain finite;
- base mutation, serialization, zero-capsule/zero-LoRA, detach, and restart
  invariants pass for both matched arms;
- capsule and LoRA parameter/artifact bounds pass.

Selection is mechanical:

1. maximize the minimum of the four paired dev gains: capsule Banking, capsule
   Devign, q-only LoRA Banking, and q-only LoRA Devign;
2. treat configurations within 1.0 point as tied;
3. prefer fewer ports;
4. then prefer lower rank;
5. then lexical grid ID.

The selected grid ID is shared by the q-only LoRA, capsule, zero,
label-shuffled, and wrong-family arms. The q-only LoRA uses its independently
selected epoch at that grid. The standard q+v reference uses rank 8 on all 30
blocks and selects only its epoch by the same two-seed rule.

If no grid is eligible because q-only LoRA fails its +5 positive-control floor,
record `ALC-R0 INCONCLUSIVE/EVALUATION_OR_OPTIMIZATION_FAILURE`. If at least one
grid qualifies LoRA but no common grid qualifies the capsule, record
`ALC-R0 FAILED IN TESTED SCOPE` with
`failure_stage = DEVELOPMENT_GRID_EXHAUSTED`. Neither case opens held-out data.

Development results cannot open the ALC-0 claim gate.

## 8. Confirmatory sealing, freeze, and statistics

### 8.1 Two access classes and sealed test material

Test access has two distinct counters:

1. `seal_access_count`: after preprocessing/duplicate code is frozen, the
   dedicated sealing worker performs one audited acquire-and-seal command. Its
   temporary network namespace allowlists only the exact pinned source hosts and
   paths in the acquisition manifest, verifies the expected revision/blob and
   response hash, and streams bytes without a development-readable cache. It
   applies the frozen normalization and duplicate policy, writes an encrypted
   canonical evaluator shard, and releases only dataset ID, input count, label
   count, exclusion count, ciphertext length, Merkle root, ciphertext SHA-256,
   and code/policy hashes. It never releases test text, labels, per-example
   hashes, group identities, or exclusion identities to development.
2. `score_transaction_count`: initialized to zero. Only the post-freeze isolated
   scorer can open the sealed shard. Development code cannot invoke the key
   release path.

The sealer and scorer run through the WSL2 namespace policy in section 6.1 with
separate command, mount, and network allowlists and output schemas. The sealer's
source-only network is destroyed before it commits the shard; the scorer has no
network at all. The key-release command verifies
the committed freeze receipt before releasing plaintext inside the isolated
scorer process. The development worker receives no test path or decryption key.
The raw public nature of the datasets is not treated as evidence of blinding;
only these access receipts define this experiment's hygiene boundary.

The sealer encrypts each canonical shard with AES-256-GCM, a fresh 96-bit OS
CSPRNG nonce, and canonical AAD containing experiment ID, dataset ID,
preprocessing hash, and plaintext Merkle root. The 256-bit key is generated and
held by a dedicated non-interactive local Windows principal
`ALUCLU_R0_SEALER`, not the development account. Its DPAPI/credential store and
broker executable/config are readable only by that principal and SYSTEM.

The same principal owns a dedicated WSL2 distribution
`ALUCLU-R0-EVAL`, registered only for its Windows profile; it does not reuse the
development account's Kali distribution. The development account may submit an
evaluation ID and immutable source/evidence commit to an ACL-restricted request
pipe, but receives only status and output-artifact roots. The broker independently
checks out the commit, re-hashes and validates the complete R0.0/development/
freeze evidence graph, verifies the zero score-transaction counter and replay
state, builds the arm-specific rootfs manifests, and launches/scorers inside its
own WSL distribution. Developer-produced receipt booleans are inputs to be
recomputed, never release authorization. The broker passes the key internally
to the isolated scorer over an inherited anonymous stdin handle; it never sends
the key across the request pipe or to a development-owned WSL process. The key
is never written to repository, command line, environment, stdout, or artifact
files.

R0.0 records broker executable/config/principal/ACL/dedicated-distro hashes and
proves that the
development identity cannot enumerate/read the stored credential or broker
private files, access the evaluator distribution, receive the key from the
request pipe, or substitute its own scorer/rootfs. It tests wrong receipt,
changed hash, incomplete evidence graph, replayed transaction, unauthorized pipe
client, substituted distro/rootfs, and direct key-read denials. If the host
cannot create and isolate this principal and dedicated distribution without
weakening policy, local confirmation is blocked and the minimum external
execution requirement is measured instead.
This controls the automated research process; it is not claimed to resist a
machine administrator deliberately taking ownership or debugging the service.

Devign test-spanning clone groups are resolved inside the sealer. A group also
present in the committed train/validation root is excluded from the sealed test
shard. Before confirmation, only aggregate exclusion counts and the one complete
sealed-shard ciphertext commitment declared in section 4.2 are revealed; no
per-group or stable linkable root leaves the sealer. The Banking77 sealer performs exact normalized-utterance digest
comparison against committed train/dev roots and excludes every cross-split
duplicate without revealing identities. Its sealed test shard must retain at
least 2,000 examples, all 77 labels, and at least 10 examples per label;
otherwise R0.0 fails and no threshold or split is silently changed.

### 8.2 Confirmatory freeze

Before the held-out evaluator can run, commit canonical
`freeze_receipt.json` containing:

- selected grid ID and exact port/rank mapping;
- training steps, checkpoint-selection result, optimizer and schedule;
- all numeric PASS thresholds;
- source commit and clean-status receipt;
- model/tokenizer/snapshot hashes;
- development dataset bytes, preprocessing, duplicate ledger, split, prompt,
  and label hashes plus only the aggregate sealed-test counters and whole-shard
  ciphertext commitment permitted by sections 4.2 and 8.1;
- both platform lock hashes, evaluator-rootfs manifest/digest, artifact-transfer
  manifest, and Windows/Linux hardware/runtime manifest hashes;
- evaluator and bootstrap code hashes;
- confirmatory seeds, `seal_access_count = 1`, and
  `score_transaction_count = 0`.

Confirmatory training seeds are `20260921`, `20260922`, `20260923`,
`20260924`, and `20260925`. The selected capsule and matched LoRA are retrained
for both families for all five seeds: 20 primary confirmatory train runs. The
label-shuffled capsule is also trained for both families and all five seeds,
giving 10 negative-control train runs and 30 confirmatory train runs total.
Zero and wrong-family controls reuse those frozen artifacts and do not add
training runs. The standard q+v reference adds 10 non-blocking confirmatory
train runs.

Every confirmatory artifact is retrained from initialization on the original
frozen training subset only; development/validation examples are never folded
into training. The training manifest commits the ordered retained training IDs
and its SHA-256. For each family, arm, and seed, shuffle that exact list with the
preregistered seed-specific deterministic Fisher-Yates implementation. With
`N` retained examples, `updates_per_epoch = ceil(N/16)`; no example is dropped,
and the final accumulation group divides loss/gradients by its actual example
count. `total_updates = selected_epochs * ceil(N/16)` and warmup is exactly
`ceil(0.05 * total_updates)`. Capsule, q-only, q+v, and label-shuffled training
share this corpus/order/update contract; only the declared labels or trainable
parameterization differ.

Label-shuffle mapping is deterministic per family and confirmatory seed. For
Banking77, seeded Fisher-Yates is repeated until the 77-label permutation is a
derangement; for Devign, the two labels are swapped. The seed is the first 64
bits of SHA-256 over experiment ID, `label-shuffle`, family, and training seed.
Permutation JSON and digest are frozen. Wrong-family pairing uses the other
family's capsule with the same confirmatory seed and selected grid ID.

### 8.3 One logical scoring transaction

Held-out scoring uses one immutable evaluation ID. Before decryption, it writes
an intent record containing every code/model/artifact/policy hash and the shard
list. Each shard writes an append-only completion journal. A crash may resume
only missing shards under the same evaluation ID and exact hashes; any changed
hash rejects resume and forces a new experiment with new untouched held-out
data. Resume is not a new scientific look, and partial outputs remain sealed
until the transaction reaches its terminal commit record.

### 8.4 Exact statistical contract

Best-seed results are never gate statistics. Classification estimands are the
five-seed mean macro-F1 difference, in absolute percentage points, between the
named arms on the same examples. For each of 10,000 replicates, seeded by
`20260926`, sample five training-seed indices with replacement and one example
index vector with replacement per family. Apply that same family vector to all
arms and all sampled seeds, compute each seed/arm macro-F1, average over sampled
seeds, then take paired arm differences. P3 averages the Banking77 and Devign
capsule-minus-base difference within each replicate at equal family weight.

LAMBADA uses the same example-level paired procedure. WikiText-2 uses the frozen
nonempty source-row document IDs defined in section 4.3; each replicate samples
one common document-ID vector for every arm and seed and computes perplexity from total sampled
negative log likelihood divided by total sampled target tokens. Relative
increase is `capsule_ppl / base_ppl - 1`.

Descriptive effect intervals are percentile two-sided 95% intervals using NumPy
`quantile(method="linear")` at 0.025 and 0.975. Gate decisions do not label an
uncentered bootstrap-tail proportion as a p-value. Instead, each preregistered
hypothesis family uses Bonferroni simultaneous one-sided percentile bounds with
family-wise alpha 0.05. For a family of size `k`, a lower gate bound is the
`0.05/k` quantile and an upper gate bound is the `1 - 0.05/k` quantile of the
paired bootstrap estimand. The fixed families and sizes are:

- LoRA-vs-base qualification, `k=2`;
- capsule-vs-base efficacy, `k=2`;
- capsule-vs-profile superiority, `k=2`;
- capsule-vs-LoRA noninferiority, `k=2`;
- capsule-vs-negative controls, `k=6`;
- LAMBADA retention, `k=2`;
- WikiText retention, `k=2`.

P3 is a single preregistered aggregate hypothesis and uses its one-sided 0.05
lower quantile. Boundary comparisons are literal and inclusive unless a P-row
says `strictly`. R0.0 freezes a small synthetic prediction/likelihood test vector
with independently calculated macro-F1, perplexity, descriptive intervals,
Bonferroni gate quantiles, and every boolean, so two evaluator implementations
must agree exactly.

### 8.5 Frozen resource harness

Resource measurements use batch 1 and a fixed 128-token fixture derived from
seed `20260927`. Base (`B`) and mounted-capsule (`A`) arms run in separate clean
processes with identical eager/math-SDPA/cache settings. Five process pairs use
the fixed counterbalanced order `B/A, A/B, B/A, A/B, B/A`. Each process runs 30
unmeasured warmups followed by 200 measured forwards. The harness calls
`torch.cuda.synchronize()` immediately before and after each
`perf_counter_ns()` interval. After warmup it empties the allocator cache,
resets peak stats, and records both peak allocated and peak reserved bytes.

Before each process pair, the run is invalid unless 60 seconds of samples show
no foreign CUDA compute process, GPU utilization at most 5%, and foreign GPU
memory at most 256 MiB. Driver, temperature, clocks, power state, and Windows
power plan are recorded; invalid environmental runs are retained and repeated,
never silently discarded. Latency p50 and p95 use NumPy linear quantiles over
the pooled 1,000 samples per arm. Exact tax formulas are
`p50_tax = capsule_p50 / base_p50 - 1` and
`p95_tax = capsule_p95 / base_p95 - 1`. Peak-VRAM delta is the maximum paired
capsule-minus-base allocated-byte delta across the five pairs. The harness and
an order-sensitive synthetic timing/memory validator fixture are frozen in
R0.0.

The harness is executed for all ten confirmatory capsule artifacts (two families
times five seeds). P13 uses the worst observed valid capsule across all ten for
each resource metric; a missing or invalid artifact cannot be replaced by a
better seed.

### 8.6 Normative confirmatory matrix

The machine preregistration must encode these exact logical cardinalities:

- trainable artifacts: 10 capsule, 10 exact-count q-only LoRA, 10
  label-shuffled capsule, and 10 q+v reference artifacts;
- nontrained zero artifacts: one per family, two total;
- held-out target scoring rows: base 2, profile 2, RAG 2, zero 2, capsule 10,
  q-only 10, shuffled 10, q+v 10, and wrong-family 10, for exactly 58 rows;
- retention scoring rows: one base plus ten capsules for each of WikiText and
  LAMBADA, for exactly 22 rows;
- attach/detach and fresh-process remount: all 10 capsule artifacts in each
  matrix;
- canonical pre/post base digest: all 40 trainable artifacts;
- P12 size/parameter validation: all 10 capsule artifacts;
- P13 resource validation: all 10 capsules, with the worst valid observation
  controlling the gate.

All target arms use the same sealed example IDs for their family; all retention
arms use the same sealed document/example IDs for their suite. Missing, extra,
duplicated, or differently paired rows are validator errors.

## 9. Blocking PASS table

`ALC-R0 = PASS` only when every row below is true:

| ID | Mandatory condition |
|---|---|
| P1 | For matched LoRA minus frozen base, each family's Bonferroni simultaneous lower gate bound is at least +5 absolute macro-F1 points. If not, classify the experiment as evaluation/optimization failure, not capsule falsification. |
| P2 | For capsule minus base, each family's Bonferroni simultaneous lower gate bound is at least +5 points. |
| P3 | The one-sided 95% lower bound of the equal-weight mean capsule-minus-base gain across the two families is at least +10 points. |
| P4 | Capsule minus textual-profile control has a Bonferroni simultaneous lower gate bound strictly above zero on each family. |
| P5 | Capsule is non-inferior to matched LoRA on each family: the Bonferroni simultaneous lower gate bound of capsule-minus-LoRA is strictly greater than -3 points. |
| P6 | For each family, the Bonferroni simultaneous lower gate bound for capsule minus each of zero, label-shuffled, and wrong-family controls is at least +5 points. |
| P7 | For each target-family capsule, LAMBADA point degradation versus base is no worse than 2 points and its Bonferroni simultaneous lower gate bound is strictly greater than -5 points. |
| P8 | For each target-family capsule, the WikiText-2 perplexity relative-increase Bonferroni simultaneous upper gate bound is no more than 2%. |
| P9 | In the Linux evaluator, every one of the ten capsule artifacts fresh-remounts with identical capsule bytes/digest, Linux base digest, and per-example predictions under retrieval/profile/tools/cache/network OFF. |
| P10 | The canonical version-1 base digest is identical before training, after every one of the 40 trainable-artifact runs, after ten attach/detach cycles per capsule, and across independent Windows and Linux fresh-process loads. |
| P11 | In both hashed Windows and Linux environments, each detached cycle and the no-capsule wrapper satisfy the full official-forward conformance matrix against that environment's unwrapped base: CPU FP32 bitwise equality and GPU BF16 `rtol=1e-3`, `atol=1e-3` with identical argmax tokens. |
| P12 | Every one of the ten capsule artifacts has at most 0.1% of host parameters and is at most 256 KiB canonically serialized. |
| P13 | Across all ten capsule artifacts under section 8.5, the worst peak allocated VRAM delta is at most 256 MiB; worst p50 latency tax is at most 15% and worst p95 tax at most 20%. |
| P14 | All source, environment, namespace-denial, data, prompt, split, artifact, raw-output, transaction, statistics, and access receipts validate and their SHA-256 values match the claim ledger. |

P3 intentionally demands a stronger aggregate result than the per-family floor.
It is not redundant with P2 and must not be weakened after observation.

## 10. Failure classification and fallback protocol

- **Implementation/parity failure:** preserve logs, reduce to a conformance
  reproducer, repair only the implementation, and rerun every affected
  development result. Held-out remains sealed.
- **OOM:** use only the semantics-preserving microbatch/accumulation recovery in
  section 6. Otherwise measure requirements and stop for compute authorization.
- **NaN/instability:** reproduce with capsule math in FP32. A new optimizer,
  scaling rule, or architecture requires a preregistration amendment before
  held-out access.
- **LoRA positive-control failure:** record
  `INCONCLUSIVE/EVALUATION_OR_OPTIMIZATION_FAILURE`; it is neither PASS nor a
  capsule-hypothesis falsification.
- **All nine configurations fail development eligibility with a qualified LoRA
  positive control:** record `ALC-R0 FAILED IN TESTED SCOPE` with
  `failure_stage = DEVELOPMENT_GRID_EXHAUSTED`; do not open held-out data and do
  not build dependent ALC infrastructure.
- **Frozen selected configuration fails confirmation:** record
  `ALC-R0 FAILED IN TESTED SCOPE` with
  `failure_stage = HELD_OUT_CONFIRMATION`; do not try a runner-up on the same
  held-out set.
- **Leakage or invalid labels discovered after access:** preserve the invalid
  run, issue a new preregistration version, and use a genuinely untouched
  replacement test set.

Negative runs, discarded variants, resource failures, and invalidated runs are
append-only trajectory/evidence entries.

## 11. Primary-source ledger and version boundary

The preregistration used the following upstream sources. Exact repository
revisions, rather than moving default branches, are the acquisition authority:

- SmolLM2-135M snapshot and model card:
  `https://huggingface.co/HuggingFaceTB/SmolLM2-135M/tree/93efa2f097d58c2a74874c7e644dbc9b0cee75a2`
- SmolLM2-135M frozen configuration:
  `https://huggingface.co/HuggingFaceTB/SmolLM2-135M/blob/93efa2f097d58c2a74874c7e644dbc9b0cee75a2/config.json`
- Banking77 authoritative raw source commit:
  `https://github.com/PolyAI-LDN/task-specific-datasets/tree/9d081458ff52e53cf7e848f414e6e9344e4e6696/banking_data`
- Banking77 dataset-card snapshot:
  `https://huggingface.co/datasets/PolyAI/banking77/tree/90d4e2ee5521c04fc1488f065b8b083658768c57`
- CodeXGLUE defect-detection snapshot:
  `https://huggingface.co/datasets/google/code_x_glue_cc_defect_detection/tree/69bd48c03223c2104342acd9a807caf61ac3efb8`
- CodeXGLUE upstream benchmark repository:
  `https://github.com/microsoft/CodeXGLUE/tree/ac74a62802a0dd159b3258c78a2df8ad36cdf2b9/Code-Code/Defect-detection`
- WikiText snapshot:
  `https://huggingface.co/datasets/Salesforce/wikitext/tree/b08601e04326c79dfdd32d625aee71d232d685c3`
- LAMBADA OpenAI snapshot:
  `https://huggingface.co/datasets/EleutherAI/lambada_openai/tree/900124bf3b8235c6daf21033af9948b3f07346c4`
- PyTorch reproducibility guidance:
  `https://docs.pytorch.org/docs/stable/notes/randomness.html`
- Transformers offline/cache guidance:
  `https://huggingface.co/docs/transformers/installation#offline-mode`

Repository metadata was observed on 2026-09-20. Moving documentation may change;
the local environment lock, acquired bytes, runtime behavior, and committed
manifests remain the experiment authority. Upstream license declarations are
recorded for provenance but are not a legal opinion. Dataset bytes are not
redistributed by this repository.

The pinned Hugging Face Banking77 loader script refers to raw files on a moving
GitHub `master` branch. It is therefore not an acquisition authority. The raw
upstream Git commit and blob identities above are binding; the Hugging Face
revision is retained only for card/schema provenance. The Devign artifact is a
pinned Hugging Face Parquet mirror of the CodeXGLUE task; R0.0 must hash its
actual Parquet bytes and retain both mirror and upstream provenance.

## 12. Evidence package

Every run emits canonical JSON/JSONL and SHA-256 evidence. The final package must
contain:

- preregistration markdown and machine-readable manifest;
- exact Git commit, diff, and tracked-clean receipt;
- model snapshot inventory and hashes;
- environment lock, package inventory, runtime and hardware manifest;
- dataset inventories, preprocessing hash, duplicate ledger, split manifests,
  prompts, labels, and hashes;
- grid and exact trainable-parameter proofs;
- per-run seed/config/hyperparameters and example-order digest;
- train/dev curves, losses, gradients, nonfinite counters, VRAM/RAM and timing;
- base, LoRA, and capsule SafeTensor hashes;
- pre/post base-state digests;
- raw per-example outputs for every evaluation arm;
- textual/RAG token-budget receipts and retrieval result IDs;
- explicit retrieval/profile/tool/cache/network-off receipts;
- attach/detach and fresh-process stdout/stderr/exit artifacts;
- bootstrap inputs/results and the complete threshold boolean table;
- all negative-control and failure artifacts;
- final claim ledger restricted to
  `ALC-0 same-base retrieval-off neural capability` only if P1–P14 all pass.

R0.0 creates versioned JSON Schemas under `schemas/alc_r0/v1/`; changing them
after development starts requires a new experiment version. JSON bytes use RFC
8785 JSON Canonicalization Scheme and UTF-8 with no BOM. JSONL is one RFC-8785
object followed by LF per line, including the final line. Artifact paths match
`results/alc_r0/<phase>/<run-id>/<artifact-type>.<ext>`; run IDs match
`alc-r0-v1-(pilot|dev|confirm|eval)-[a-z0-9-]+-s[0-9]{8}`.

The machine preregistration enumerates the Cartesian expected-run matrix and
expected artifact types/cardinalities. `(experiment_id, run_id)` and
`(run_id, artifact_type, logical_id)` are primary keys; foreign keys bind every
prediction, checkpoint, receipt, statistic, and review to a declared run and
source artifact. Allowed run states are `INTENT`, `RUNNING`, `PREPARED`, and
terminal `PASS|FAIL|INVALID|BLOCKED`; transitions are append-only and only
`PREPARED` may become a scientific terminal result. Duplicate keys, missing
expected rows, unreferenced/orphan files, extra runs, hash mismatch, illegal
transition, and foreign-key failure are validator errors.

The matrix counts logical runs, not process attempts. Each logical run owns
attempt IDs `a001`, `a002`, and, only for environment-invalid resource retries,
`a003`. An exact crash resume appends to the same attempt and can execute only
missing journaled work; an implementation-repair rerun creates the next attempt
and records the superseded source/artifact hashes. Exactly one non-`INVALID`
attempt may become the logical run's `PREPARED` scientific candidate; all prior
attempts remain referenced failure/invalid evidence. Extra logical run IDs are
forbidden, while attempt cardinality and transitions are validated against these
rules. GPU-hour, wall-clock, and disk-budget ledgers include every attempt and
resume, including resource-harness repeats.

For each evidence file other than the claim ledger and completion artifact,
compute SHA-256 over exact bytes. The claim ledger
lists normalized forward-slash relative path, byte length, media/schema type,
and SHA-256, sorted by UTF-8 path bytes. Its root digest is SHA-256 of the RFC
8785 ledger object with `root_digest` omitted; the completion artifact embeds
that digest and is generated strictly after the ledger closes. The ledger does
not list the completion artifact, eliminating a hash cycle; the validator
returns the completion artifact's own SHA-256 out of band in its terminal log.
Valid, missing, duplicate, tampered, orphan, illegal-transition, circular-root,
and wrong-cardinality fixture packages are mandatory before R0.0 passes.

## 13. Validator-gated execution tasks

### R0.0 — Freeze prerequisites and acquisition

- Provision isolated Windows-training and Linux-evaluator Python 3.12
  environments, their separate hashed dependency locks, and the bound evaluator
  rootfs/transfer manifests.
- Acquire and locally verify the exact model snapshot.
- Acquire model and development-only dataset revisions under Windows; separately
  acquire-and-seal every confirmatory test split under the sealer-owned Linux
  environment; hash all consumed bytes and record licenses without exposing test
  paths or caches to development.
- Implement deterministic development preprocessing/split generation, the
  independent test sealer/key broker, and freeze their allowed manifests.
- Freeze prompts, labels, conformance corpus, isolation policy, evaluator, and
  the already-declared optimizer contract in machine-readable preregistration.
- Create a validator that fails closed on any missing/mismatched field.

Gate: no train command accepts `--development` until the R0.0 validator passes
on a committed tracked-clean source state.

### R0.1 — Red conformance tests

Write failing tests for explicit block traversal, port mapping, parameter count,
frozen-base allowlist, optimizer allowlist, state digest, zero/detach parity,
serialization, wrong manifest/host rejection, and fresh-process isolation.

### R0.2 — Capsule and matched-LoRA implementation

Implement the smallest code needed to make R0.1 pass. No generalized public ABI,
router, bridge trainer, or product container is introduced.

### R0.3 — Data/scoring and negative controls

Implement label-only training, deterministic candidate scoring, macro-F1,
retention metrics, textual and BM25 controls, shuffled labels, wrong-family
mounts, and raw-output receipts. Add leakage and budget tests.

### R0.4 — Fixed feasibility pilot

Run the 200-step train-only pilot. Record tokens/s, wall time, VRAM/RAM, disk,
finite gradients, and projected grid runtime. It is feasibility evidence only
and cannot select or eliminate a scientific configuration.

### R0.5 — Full development grid

Run all 72 primary capsule/q-only-LoRA development jobs plus four non-blocking
q+v-LoRA reference jobs and the required conformance jobs. Validate every
artifact and mechanically select at most one common capsule/q-only-LoRA grid
configuration by the arm-neutral rule in section 7.2.

### R0.6 — Confirmatory freeze

Generate, independently review, commit, and validate `freeze_receipt.json`.
Confirm `seal_access_count = 1` and `score_transaction_count = 0` without
exposing test content, labels, group membership, or exclusion identities.

### R0.7 — Five-seed confirmation

Run 30 blocking confirmatory jobs (capsule, q-only LoRA, and label-shuffled), 10
non-blocking q+v-LoRA reference jobs, and one journaled held-out scoring
transaction. Run attach/detach, fresh-process isolation, retention, statistics,
and resource gates.

### R0.8 — Independent verdict

Independent code/security, architecture/scientific-method, and completion
reviewers inspect the immutable evidence package. The machine validator emits
the completion artifact only if every required receipt and P1–P14 boolean is
valid. Record exactly one terminal status:

- `ALC-R0 PASS`;
- `ALC-R0 FAILED IN TESTED SCOPE`;
- `ALC-R0 INCONCLUSIVE/EVALUATION_OR_OPTIMIZATION_FAILURE`.

Only `ALC-R0 PASS` unlocks Task 3 and later dependent ALC claims. Paid external
compute always requires explicit user approval before purchase or launch.
