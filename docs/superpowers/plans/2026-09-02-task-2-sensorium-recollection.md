# Task 2 Sensorium, Recollection, Calibration, and Reconsolidation Plan

> **Status:** implementation-ready architecture; no Task 2 production code is
> authorized until this document receives an independent requirements review
> and an independent architecture review.

**Goal:** turn the Task 1 encrypted lifetime ledger into the first complete
cognition vertical slice: a typed observation enters through the sensorium,
receives a deterministic episode boundary, can be recalled exactly without
being confused with approximate familiarity, is governed by a versioned
selective-risk profile, and can be explicitly reconsolidated as a new immutable
lineage record. The same result must survive process restart while active
working state remains bounded.

**Architecture:** Task 2 is a model-independent domain layer over one
caller-owned `VerifiedLedgerSession`. It never opens, unlocks, closes, or nests a
ledger session. Observation ingestion first performs a storage-pure direct
lookup classification; only a genuinely new observation is appended. Exact
recollection is an authenticated record property, whereas query-to-record
confidence is a separate calibrated decision. Approximate retrieval uses a
deterministic, bounded, streaming baseline and can never promote itself to
exact recollection. Reconsolidation appends an explicit child record and never
overwrites or silently averages an earlier memory.

**Tech stack:** Python 3.10+, immutable dataclasses/enums/protocols, existing
Task 1 canonical JSON and ledger APIs, stdlib SHA-256/BLAKE2s, `unicodedata`,
integer arithmetic, `math.isqrt`, `decimal`, `heapq`, `array`, pytest, Ruff,
and scoped Pyright. Task 2 adds no runtime dependency and does not import
PyTorch or NumPy.

**Roadmap dependency:** Task 1 is frozen at commit
`f5a30e0d7c9e0e95a8d8a5533517a852c77e0d3c`, whose scale gate is CLEAN. Any
new persistence defect discovered while implementing this plan is repaired as
a separate Task 1 regression with its own review; Task 2 must not opportunistically
rewrite `ledger.py`, `keys.py`, `persistence.py`, or `codec.py`.

## 1. Scope and non-goals

Task 2 owns:

- typed observations and physically distinct provenance source kinds;
- storage-pure duplicate/conflict/tombstone receipt classification;
- deterministic, versioned episode segmentation and bounded replay state;
- direct exact recall, exact-content recall, bounded approximate candidate
  retrieval, deterministic inhibition, and explicit abstention;
- versioned calibration artifacts and simultaneous selective-risk bounds;
- explicit immutable reconsolidation lineage;
- restart determinism, scale/resource accounting, and platform-stable test
  vectors.

Task 2 does **not** own:

- truth, belief, source trust, external verification, contradiction of world
  claims, or supersession semantics; those belong to Task 4;
- host hidden states, logits, routing, or gradients; those belong to Task 3;
- planning, tool dispatch, side effects, or prospective tasks; those belong to
  Task 5;
- weight updates, plastic experts, eligibility for training, or sleep
  transactions; those belong to Tasks 6 and 7;
- resource-lease authority; Task 2 exposes bounded work and usage to Task 8;
- the global phase journal and single-session orchestration; Task 9 owns them;
- learned semantic encoders or learned event segmenters. They remain disabled
  until a predeclared Task 12 comparison beats this deterministic baseline;
- a claim that remembering an observation makes its contents true;
- a claim that a natural-language match is exact merely because its similarity
  score is high.

This boundary is deliberate: Task 2 makes memory usable, not omniscient, and it
does not pretend that retrieval is weight learning. The later plasticity and
native-model tasks remain necessary for the full lifelong-learning objective.

## 2. Binding invariants

1. **Memory is not belief.** A user, model, file, or tool observation proves
   only that the observation was recorded. Task 2 never marks a world claim
   verified.
2. **Inference is not evidence.** Approximate similarity and model-produced
   text carry no evidence authority.
3. **Familiarity is not recollection.** Exact and approximate results are
   different closed types, record kinds, metrics, and public states. There is
   no `exactness: float` that can drift from approximate to exact.
4. **Exact means authenticated bytes.** An exact result must name a live Task 1
   record, its sequence, record hash, canonical content digest, and the
   retrieval basis that established identity.
5. **Natural-query authorization is selective.** A natural-language query may
   authorize personal recollection only through a compatible, enabled,
   held-out calibration profile and a non-conflicted candidate. Missing,
   stale, incompatible, or underpowered profiles fail closed.
6. **Model output cannot certify itself.** Calibration labels must come from
   frozen gold query-target pairs or independently adjudicated outcomes. A
   model's own answer is never a correctness label.
7. **Duplicate classification is storage-pure.** Classifying a retry performs
   no append, receipt-journal write, tombstone write, pointer write, or state
   codec write. A duplicate retry leaves ledger head and event count unchanged.
   State convergence is explicit: the stored record carries the bounded post
   core state plus pre/post core-state digests, and a retry may apply it only
   when the caller is exactly one ledger sequence behind. The Task 1 checkpoint
   wrapper is deliberately outside that digest basis, avoiding a self-hash with
   the record that creates the post-append head. A farther-behind caller must
   replay; an equal/ahead caller must never apply the transition again or roll
   state backward.
8. **No resurrection.** A tombstoned observation cannot be re-ingested,
   recalled, used as a reconsolidation parent, or reconstructed through a
   child payload.
9. **Reconsolidation never overwrites.** Retrieval alone is read-only. An
   explicit reconsolidation creates a new append-only child whose parents stay
   separate. Conflicting memories are not averaged.
10. **One verified session.** Every ledger-dependent Task 2 API consumes the
    already active caller-owned `VerifiedLedgerSession`. Task 2 contains no
    `EncryptedLedger` constructor, `unlock`, `close`, or nested
    `verified_session()` call.
11. **Cursor-before-mutation discipline.** A recall/replay cursor is closed or
    suspended before any append. This follows the Task 1 prohibition on
    mutation with an active cursor.
12. **Bounded active state.** Sensorium state, feature vectors, candidate heap,
    query buffers, and returned payload bytes have explicit caps independent
    of lifetime record count. Lifetime encrypted storage and scan time may
    grow and are reported separately.
13. **No plaintext persistent index.** Task 2 creates no disk index, cache, or
    sidecar containing observation text or retrieval features. Restart rebuilds
    bounded state by streaming the encrypted ledger. Later optimization must
    preserve this privacy boundary.
14. **Determinism precedes learning.** Event boundaries, baseline features,
    ranking, conflict handling, replay, and production thresholds are
    versioned and reproducible. A learned replacement is a later ablation, not
    a hidden fallback.
15. **Pre-recall causality.** The execution policy, compatible profile, work
    page, output budget, and any tightening are frozen before scanning. A
    post-recall signal may schedule later work but cannot retroactively change
    the recall result.
16. **Tightening is one-way.** A process-local Task 2 policy handle may raise a
    minimum score, lower `top_k`, lower work/output budgets, or force abstention.
    It cannot lower the calibrated threshold or expand authority. Serialized
    data is not a policy handle.
17. **Incomplete is not absent.** Exhausting a scan page, deadline, or caller
    budget produces `INCOMPLETE` plus a Task 1 checkpoint; it never produces
    `NOT_FOUND`.
18. **The published v0.1 four-lane implementation remains an immutable
    baseline.** Task 2 may consume its ideas in later host integration but does
    not rewrite its core files or tests.

## 3. Technology decisions

| Concern | Decision | Reason |
|---|---|---|
| Persistence | Existing `VerifiedLedgerSession` only | Preserves the independently reviewed lock, verification, rollback, and crypto-shred boundary. |
| Serialization | Existing strict canonical JSON | One byte representation, bounded depth/nodes/payload, and existing audit coverage. |
| Identity/content digest | SHA-256 with domain-separated canonical bytes | Guaranteed by Python across supported platforms and already used by Task 1. |
| Baseline feature hashing | BLAKE2s with fixed personalization | Guaranteed stdlib availability on Python 3.10+; explicit personalization prevents cross-domain collisions. |
| Text normalization | NFC search view, fixed ASCII case/whitespace folding, explicit normalizer version | Leaves canonical content bytes untouched, makes the search view deterministic, and avoids locale-dependent tokenization. Unassigned code points fail closed for the active Unicode database. |
| Similarity/ranking | Signed hashed byte n-grams, fixed-width integer bins, inclusive Q32 unit score, integer comparisons | Cross-platform behavior does not depend on BLAS, GPU kernels, Python hash seed, or floating tie behavior. It is a baseline, not a semantic-understanding claim. |
| Approximate search | Streaming top-k heap | Memory is `O(KD)` rather than `O(ND)`; the ledger may grow without growing active candidate state. |
| Selective calibration | Predeclared finite threshold grid; one-sided Clopper-Pearson upper bounds; Bonferroni familywise correction | Selecting a threshold on the same held-out set remains covered simultaneously. The result is conservative and auditable. |
| Numerical calibration artifact | Counts plus conservatively rounded decimal upper bounds | Runtime decisions use the frozen integer threshold; numerical root finding never sits in the hot path. |
| Reconsolidation | Immutable lineage append | Mirrors the useful engineering property of reactivation/update without biological overclaim or destructive overwrite. |
| Dependencies | No new runtime package | Task 2 needs none; avoiding SciPy/vector DB/tokenizer dependencies keeps installation and portability narrow. |

Rejected alternatives:

- a single `RecallResult` with scalar `exactness`, because it permits an
  approximate score to masquerade as exact memory;
- an embedding/vector database in Task 2, because it creates a plaintext or
  separately encrypted mutable index and adds a second persistence authority;
- storing all lifetime feature vectors in RAM, because it violates bounded
  active state;
- calibrating and choosing an arbitrary threshold on the same examples without
  simultaneous correction;
- treating `0.85`, `0.90`, or any other confidence number as a natural
  constant. Such values may appear in a predeclared grid, but only a versioned
  calibration artifact can select one;
- automatic reconsolidation on every read, because a read must be idempotent
  and cannot silently rewrite memory;
- learned segmentation or embeddings before the deterministic baseline has
  measured Task 12 evidence.

## 4. Complete annotated file structure

The following is the complete Task 2 implementation surface. Files marked
`modify` receive exports or metadata only; Task 1 implementation files stay
unchanged.

```text
ALUCLU/
├── TRAJECTORY.md
│   # modify on every logical change/test/review/commit: durable context ledger
├── docs/superpowers/plans/
│   └── 2026-09-02-task-2-sensorium-recollection.md
│       # This reviewed, decision-complete Task 2 architecture and execution plan.
├── src/aluclu/cognition/
│   ├── __init__.py                         # modify: preserve every Task 1 export and add approved Task 2 types
│   ├── observation.py                      # create: provenance, observation schemas, strict codecs, receipt types
│   ├── sensorium.py                        # create: deterministic boundary transition, replay, storage-pure ingestion
│   ├── recall_features.py                  # create: NFC/byte-ngram baseline and platform-stable score primitives
│   ├── recollection.py                     # create: query/result unions, streaming top-k, conflict and abstain policy
│   ├── calibration.py                      # create: immutable profile schema and simultaneous risk-bound builder
│   └── reconsolidation.py                  # create: proposal validation and immutable lineage append
├── src/aluclu/protocols/
│   └── task2_determinism_v1.json            # create: non-secret cross-platform hash/feature/ranking vectors
├── tests/
│   ├── test_cognition_observation.py        # create: strict types, canonical schemas, source separation, ID bounds
│   ├── test_cognition_sensorium.py          # create: pure classification, segmentation, replay, crash retry
│   ├── test_cognition_recall_features.py    # create: NFC/byte vectors, fixed hashes, Q32/ranking determinism
│   ├── test_cognition_recollection.py       # create: exact/approx separation, top-k, conflicts, paging, abstention
│   ├── test_cognition_calibration.py        # create: exact-binomial fixtures, familywise selection, profile failures
│   ├── test_cognition_reconsolidation.py    # create: explicit lineage, idempotency, no overwrite/no resurrection
│   ├── test_cognition_task2_e2e.py          # create: ingest -> recall -> revise -> restart vertical slice
│   └── test_cognition_task2_scale.py        # create: 2,048/4,096/8,192 record resource and complexity gate
└── pyproject.toml                           # modify: package protocol JSON if existing rule is insufficient; no dependency
```

No production Task 2 file may write outside the caller's Task 1 ledger. The
determinism JSON contains only public synthetic strings and expected numbers;
it contains no user data, key material, or calibration claim.

## 5. Module architecture and dependency direction

Dependency direction is acyclic:

```text
Task 1 contracts/codec/ledger
               │
               ▼
         observation.py
          │           │
          ▼           ▼
    sensorium.py  recall_features.py
          │           │
          └─────┬─────┘
                ▼
         recollection.py ◄──── calibration.py
                │
                ▼
       reconsolidation.py
```

- `observation.py` owns only immutable schemas, validation, canonical
  conversion, and source-kind separation. It performs no I/O.
- `sensorium.py` owns receipt classification, episode segmentation, ingestion,
  and replay. It depends only on Task 1's session interface and observation
  schemas.
- `recall_features.py` is a pure platform-stable baseline. It knows nothing
  about the ledger or policies.
- `calibration.py` is a pure/offline statistics module. It consumes frozen
  labeled score examples and produces an immutable artifact. It does not train
  a scorer and does not read personal memory.
- `recollection.py` owns direct and streaming retrieval plus the selective
  decision state machine. It consumes, but never modifies, a calibration
  artifact.
- `reconsolidation.py` consumes an exact recollection and a new observation to
  validate and append a separate lineage record. It does not assign truth or
  training eligibility.

Forbidden edges are tested: `observation`, `recall_features`, and
`calibration` cannot import ledger code; no Task 2 module imports Task 3–9; no
Task 2 module imports `EncryptedLedger`; and Task 1 modules do not import Task
2.

## 6. Data models

All public records are immutable, keyword-only, versioned, strict about unknown
fields, and round-trip through canonical JSON. Booleans are not accepted as
integers; non-finite numbers are rejected; IDs use Task 1's ASCII event-ID
boundary or a stricter field-specific subset.

Unless a narrower rule is stated below, every integer field is an exact Python
`int` (never `bool`) in `[0, 2^63 - 1]`. Every byte decoder requires exact
`bytes`, checks its task-specific byte ceiling before parsing, calls Task 1
`strict_json_loads`, requires `canonical_json_bytes(decoded) == input`, and then
checks the exact schema, key set, field types, ranges, and relationships. Caller
boundary violations raise `InputBoundaryError`; no decoder repairs, reorders,
normalizes, truncates, or supplies a missing field.

The wire rules for Task 2.1 are frozen as follows:

| Field family | Exact boundary |
|---|---|
| Observation ID | `obs:[A-Za-z0-9][A-Za-z0-9._:-]{0,251}\Z`; 5–256 ASCII bytes, so bare `obs:` is invalid |
| Session, turn, goal, participant, tool-invocation ID | Task 1 `validate_event_id`; 1–256 ASCII bytes |
| Source instance and origin ID | `[A-Za-z0-9][A-Za-z0-9._:@+-]{0,127}\Z`; 1–128 ASCII bytes |
| Capture method and capture version | `[A-Za-z0-9][A-Za-z0-9._+-]{0,63}\Z`; two separate required fields, each 1–64 ASCII bytes |
| Topic key | source/origin alphabet above; 1–128 ASCII bytes when present |
| Tool phase | capture-token alphabet above; 1–64 ASCII bytes when present |
| Parent, goal, participant collections | immutable tuple; each independently capped at 32; ASCII-lexicographically sorted and unique; unsorted or duplicate wire input is invalid |

All optional fields still occur in every wire object: absence is encoded as
JSON `null`, and an empty collection as `[]`. Missing keys and unknown keys are
invalid. `observed_at_ns`, ledger sequences, and state counters use the integer
boundary above. A timestamp earlier than the preceding accepted observation is
a stateful Task 2.3 `TIME_REVERSED_INVALID` rejection; it is not a Task 2.1
field-shape error and is never persisted as a boundary reason.

### 6.1 Observation and provenance

`SourceKind` is a closed string enum with physically distinct names and wire
values:

```text
USER="user" | TOOL="tool" | WEB="web" | DATABASE="database" |
FILE="file" | ENVIRONMENT="environment" | MODEL="model"
```

There is no `OTHER` value. A new source kind requires a schema version and
tests. In particular, `MODEL` cannot be serialized as `USER`, `TOOL`, or
external evidence.

`CanonicalJsonValue` is the deep-immutability boundary for observation content:

```python
@dataclass(frozen=True, slots=True, init=False)
class CanonicalJsonValue:
    canonical_bytes: bytes
```

Only `from_value`, `from_canonical_bytes`, and `to_value` are public creation or
access paths. `from_value` validates and canonical-encodes a JSON tree;
`from_canonical_bytes` parses, re-encodes, and requires byte-for-byte canonical
equality; `to_value()` parses afresh on every call. No caller-owned mutable
`dict` or `list` is retained or returned, and the disabled public constructor
prevents unvalidated bytes from masquerading as canonical content.

`ProvenanceV1` is `@dataclass(frozen=True, kw_only=True, slots=True)` and
contains:

- `source_kind`;
- bounded ASCII `source_instance_id` and `origin_id`;
- `observed_at_ns` as a UTC Unix integer supplied by the adapter;
- bounded parent observation IDs (the tuple may be empty);
- separate required `capture_method` and `capture_version`;
- no trust, confidence, truth, or verification status.

Its exact wire keys are:

```text
schema source_kind source_instance_id origin_id observed_at_ns
parent_observation_ids capture_method capture_version
```

and `schema` is exactly `aluclu.provenance.v1`.

`ObservationRequestV1` is also frozen, keyword-only, and slotted. It contains:

- caller-supplied canonical `observation_id` with `obs:` namespace;
- canonical `session_id` and `turn_id`;
- `ProvenanceV1`;
- immutable `CanonicalJsonValue` `content`;
- optional `retrieval_text` whose raw UTF-8 and normalized search-view UTF-8
  forms are each at most 4,096 bytes; omission means “not eligible for
  approximate text retrieval” rather than implicit stringification;
- bounded explicit boundary signals: `topic_key`, goal IDs, participant IDs,
  tool invocation/phase, and `force_boundary`;
- no derived episode decision and no ingestion wall-clock value.

The request rejects its own observation ID in `parent_observation_ids`. Its
wire object has exact schema `aluclu.observation-request.v1` and exact keys:

```text
schema observation_id session_id turn_id provenance content retrieval_text
topic_key goal_ids participant_ids tool_invocation_id tool_phase force_boundary
```

`content` is the JSON value itself, not a string containing JSON. Every other
optional key is present with `null`; tuple fields are present as arrays.

The final stored `CanonicalObservationV1`, including content, metadata, and
envelope fields, is capped at 262,144 canonical bytes. This Task 2 ceiling is
deliberately smaller than Task 1's 2,097,152-byte generic ledger ceiling, so
one direct exact recollection always fits the Task 2 return budget. A request
whose content fits alone but whose complete stored envelope does not fit is
rejected before classification/append; it is never implicitly truncated.

`CanonicalObservationV1`, the stored payload, adds:

- schema discriminator `aluclu.observation.v1`;
- `request_digest`, SHA-256 over a domain tag plus canonical request bytes;
- `content_digest`, separately domain-separated from the request digest;
- immutable `EpisodeBoundaryDecisionV1`;
- `pre_core_state_digest` over the bounded Task 2 core before transition;
- the complete bounded `post_core_state` and its independently recomputed
  `post_core_state_digest`;
- the exact pre-append Task 1 snapshot head sequence/hash from the exhaustive
  checkpoint that authorized segmentation;
- the exact boundary-profile ID that produced the decision.

It is a frozen, keyword-only, slotted record with fields, and only fields,
`request`, `request_digest`, `content_digest`, `boundary_decision`,
`pre_core_state_digest`, `post_core_state`, `post_core_state_digest`,
`pre_append_head_sequence`, `pre_append_head_hash`, and
`boundary_profile_id`. The exact wire keys are `schema` plus those field names;
`request` and `post_core_state` are complete nested wire objects and `schema` is
exactly `aluclu.observation.v1`. Every digest/head hash is 64 lowercase
hexadecimal characters. A decoder recomputes and compares the request, content,
and post-core digests. The complete canonical wire envelope is accepted through
262,144 bytes inclusive and rejected at 262,145 bytes before parsing or ledger
access.

The core/wrapper split is mandatory, not an optimization. A Task 1 record hash
depends on randomized authenticated-encryption material plus the stored
observation payload, so the post-append checkpoint head hash cannot be an input
to a digest inside that same payload. `post_core_state` contains no Task 1
checkpoint field. Keeping its bounded value, rather than only its digest, also
lets replay resume from surviving authenticated observations after an unrelated
record or an earlier observation has been shredded without reconstructing the
shredded content.

The canonical content bytes preserve the caller's original JSON value and
Unicode code-point sequence, including an NFC/NFD distinction. They do not and
cannot preserve irrelevant lexical JSON spellings or object-key order because
the API accepts a JSON value, not raw JSON source bytes. NFC and search
normalization apply only to `retrieval_text`, never to stored content or its
exact digest.

`EpisodeBoundaryDecisionV1` is a frozen, keyword-only, slotted record with exact
wire schema `aluclu.episode-boundary-decision.v1` and keys `schema`,
`episode_id`, and `reasons`. `episode_id` matches
`episode:[0-9a-f]{64}\Z`. Reasons are unique and already ordered by the fixed
precedence in section 6.3; `continue` may appear only as the sole reason.

### 6.2 Receipt classification

`ReceiptClass` is a closed string enum:

```text
NEW="new" | DUPLICATE="duplicate" | CONFLICT="conflict" |
TOMBSTONED="tombstoned"
```

`ObservationReceiptV1` is frozen, keyword-only, slotted, and has exact schema
`aluclu.observation-receipt.v1` plus exact keys `schema`, `receipt_class`,
`observation_id`, `incoming_request_digest`, `existing_request_digest`,
`existing_sequence`, and `existing_record_hash`. It is a returned value, never
a ledger record. All three `existing_*` fields are null for `NEW` and
`TOMBSTONED`; sequence/hash are present for every live conflict; the existing
request digest is present only when that live record decodes as a Task 2
observation. For `DUPLICATE`, both request digests are equal and all existing
fields are present.

Ingestion returns a closed union rather than a nullable option bag:

- `ObservationAcceptedV1`, schema `aluclu.observation-ingest-accepted.v1`, exact
  keys `schema`, `status`, `receipt`, `stored_observation`, `next_state`; status
  is `applied` for a `NEW` append or `duplicate` for a converged retry;
- `ObservationRejectedV1`, schema `aluclu.observation-ingest-rejected.v1`, exact
  keys `schema`, `receipt`, `rejection_code`, `replay_from_sequence`;
  `rejection_code` is one of `observation_conflict`,
  `observation_tombstoned`, `state_conflict`, `replay_required`, or
  `time_reversed_invalid`, and `replay_from_sequence` is non-null only for
  `replay_required`.

A rejection has no `next_state` and never returns caller data as if it had been
validated. The caller retains its state and either corrects the input or runs
replay. These typed domain rejections may be mapped to exceptions only at a
higher adapter boundary; the core API does not communicate them by parsing
error strings.

Classification rules under the already-held Task 1 session lock:

| Ledger state | Incoming request | Class | Mutation |
|---|---|---|---|
| tombstoned ID | any | `TOMBSTONED` | none |
| no live ID | valid request | `NEW` | none during classification |
| live Task 2 observation | same `request_digest` | `DUPLICATE` | none |
| live Task 2 observation | different digest | `CONFLICT` | none |
| live non-observation record | any | `CONFLICT` | none |

Only the subsequent ingest operation for `NEW` performs one
`session.append_once`. `CONFLICT` and `TOMBSTONED` fail closed. A `DUPLICATE`
uses the stored pre/post core-state digests and existing ledger sequence as follows:

| Caller `last_applied_sequence` | Required behavior |
|---|---|
| exactly `existing.sequence - 1` | active head must equal `existing.sequence`; checkpoint sequence/hash and core digest must equal the stored pre-append/core values; use the stored post core once, verify its digest, then bind it to the current head |
| exactly `existing.sequence` | caller checkpoint must match the active head and caller core digest must equal the stored post-core digest; return state unchanged |
| greater than `existing.sequence` | caller checkpoint must match the active head; treat it as a historical retry, return current state unchanged, and never roll back |
| less than `existing.sequence - 1` | return `REPLAY_REQUIRED`; do not guess or append |

An ahead state must still belong to the same session/profile lineage. Any
digest/session mismatch is `STATE_CONFLICT`, not an invitation to repair state
from untrusted caller data.

### 6.3 Episode boundary profile and bounded state

`BoundaryProfileV1` is immutable and content-addressed. The initial engineering
profile is named `task2-baseline-v1`; its limits are not biological claims:

- maximum inter-observation gap: 1,800,000,000,000 ns (30 minutes);
- maximum observations in one episode: 64;
- maximum cumulative canonical request bytes in one episode: 8 MiB;
- maximum goal and participant IDs per observation: 32 each;
- topic change is an explicit `topic_key` change; when no key is supplied,
  Task 2 does not invent semantic topic certainty;
- a profile change always starts a new episode.

The byte counter is explicitly the sum of canonical
`ObservationRequestV1` wire sizes, not complete stored-envelope sizes. This
quantity is known before transition; counting an envelope that itself contains
the resulting counter would create a size fixed-point. A new observation starts
a new episode when adding its request would exceed either profile limit; the
new episode begins at count one and the current request's byte length.

`SensoriumCoreStateV1` is the only state digest basis. It is frozen,
keyword-only, slotted, and has exact schema `aluclu.sensorium-core-state.v1`
plus the following exact keys:

```text
schema boundary_profile_id session_signal_digest current_episode_id
episode_observation_count episode_canonical_request_bytes
goal_ids_signal_digest participant_ids_signal_digest tool_signal_digest
topic_signal_digest last_observation_id last_observation_sequence
last_observed_at_ns
```

It stores no raw observation text, content, provenance, goal/participant array,
or growing history. Signal digests are 64-character lowercase SHA-256 values
over the current request's canonical signal values; this is required because 32
maximum-size goal IDs plus 32 maximum-size participant IDs alone cannot satisfy
a 4 KiB state ceiling. The initial core has the selected
`boundary_profile_id`, null session/episode/signal/last-observation fields, zero
episode counters and last sequence, and null last timestamp. After the first
observation those nullable fields are all populated except that the canonical
tool/topic signal values inside their digests may themselves contain null. The
core canonical form is capped at 3,072 bytes.

Signal digest payloads and domains are exact:

| Signal | Domain bytes | Canonical payload |
|---|---|---|
| session | `aluclu.task2.signal.session.v1` | session ID JSON string |
| goals | `aluclu.task2.signal.goals.v1` | sorted goal-ID JSON array |
| participants | `aluclu.task2.signal.participants.v1` | sorted participant-ID JSON array |
| tool | `aluclu.task2.signal.tool.v1` | exact object keys `tool_invocation_id`, `tool_phase`, including nulls |
| topic | `aluclu.task2.signal.topic.v1` | topic-key JSON string or null |

`SensoriumStateV1` is the checkpoint wrapper, never a digest input. Its exact
wire schema is `aluclu.sensorium-state.v1` and its only other keys are `core`
and `task1_checkpoint`. The checkpoint is the existing Task 1
`LedgerCursorCheckpoint` encoded with exact keys `ledger_id`,
`snapshot_head_sequence`, `snapshot_head_hash`, and `next_sequence`; its shape
and bounds remain Task 1's authority. A completed state requires an exhaustive
tail checkpoint whose `next_sequence == snapshot_head_sequence + 1`. The
state's `last_applied_sequence` property is exactly that snapshot-head sequence,
including intervening non-Task-2 ledger records. Its complete canonical form is
capped at 4,096 bytes.

Before segmenting/appending a new observation, `ingest_observation` validates
that state checkpoint against the active session using Task 1's
`resume_verified`, then closes the zero-work cursor. A mismatch requires replay.
After append it creates and immediately suspends an empty tail cursor to bind
the returned core to the new head. This adds no full verification and leaves no
cursor live. The post core and its digest are computed before append; the
checkpoint wrapper is created only after Task 1 returns the unpredictable
record hash.

The duplicate exactly-one-behind case is the sole exception to validating the
caller's checkpoint against the already-advanced current head: the active head
must equal the existing observation sequence, the caller checkpoint must equal
the stored pre-append sequence/hash, and its core digest must equal the stored
pre-core digest. Ingest then uses the stored post core, verifies its digest, and
binds it to the current head. If the active head has advanced beyond the
duplicate record, that stale one-behind caller requires replay. Equal and ahead
states must validate against the active head before being returned unchanged.
This prevents a stale but well-formed state from segmenting against unseen
observations and prevents a retry from applying its transition twice.

Boundary reasons are accumulated in a fixed precedence order:

```text
FIRST_OBSERVATION="first_observation"
PROFILE_CHANGED="profile_changed"
FORCED="forced"
SESSION_CHANGED="session_changed"
TIME_GAP="time_gap"
GOAL_CHANGED="goal_changed"
TOOL_PHASE_CHANGED="tool_phase_changed"
PARTICIPANTS_CHANGED="participants_changed"
TOPIC_KEY_CHANGED="topic_key_changed"
EPISODE_COUNT_LIMIT="episode_count_limit"
EPISODE_BYTE_LIMIT="episode_byte_limit"
CONTINUE="continue"
```

`TIME_REVERSED_INVALID` is a closed ingestion rejection code, not a member of
`EpisodeBoundaryReason`, not a boundary, and never stored in a decision.
Multiple applicable reasons are stored in precedence order. `CONTINUE` is used
only when no boundary reason applies. Episode IDs are deterministic hashes of
the profile ID, session ID, and first observation ID; they are never random.

The profile identity object excludes its derived ID and has exact keys
`schema`, `name`, `max_inter_observation_gap_ns`, `max_observations`,
`max_canonical_request_bytes`, `max_goal_ids`, and `max_participant_ids`, with
schema `aluclu.boundary-profile.v1`. Its ID is
`boundary-profile:` followed by `H_boundary_profile` of that canonical object,
and matches `boundary-profile:[0-9a-f]{64}\Z`. The baseline values are exactly
those listed above. An episode ID is `episode:` followed by `H_episode` of the
canonical object whose exact keys are `boundary_profile_id`,
`first_observation_id`, and `session_id`.

Historical boundary decisions are immutable. Replay consumes the recorded
decision and, when the referenced profile is available, recomputes it as an
integrity oracle. A newer profile does not resegment old history.

Paged replay keeps incomplete work physically distinct from a completed active
state:

- `SensoriumReplayContinuationV1` has exact schema
  `aluclu.sensorium-replay-continuation.v1` and keys `schema`, `core`,
  `task1_checkpoint`, `records_examined`, `observations_applied`, and
  `canonical_payload_bytes_examined`. Its checkpoint may be mid-snapshot and is
  used only with Task 1 `resume_verified`; it is not a `SensoriumStateV1`.
- `SensoriumReplayIncompleteV1` has exact schema
  `aluclu.sensorium-replay-incomplete.v1` and keys `schema`, `continuation`, and
  `page_work`.
- `SensoriumReplayCompleteV1` has exact schema
  `aluclu.sensorium-replay-complete.v1` and keys `schema`, `state`, and
  `page_work`; its state carries the exhausted checkpoint at the same frozen
  snapshot head.

The continuation's canonical form is capped at 5,120 bytes. Page-work counters
are exact nonnegative integers and include records examined, decrypted canonical
bytes, and observations applied. Replay streams only live authenticated records.
For each surviving Task 2 observation it validates the stored post core and may
adopt that bounded core even when an earlier record was shredded; it never
guesses or reconstructs missing content. When an unbroken compatible predecessor
is available it also recomputes the transition and both core digests as an
integrity oracle.

### 6.4 Recollection query and result types

Queries are a closed tagged union:

- `EventIdRecallQuery`: explicit observation ID;
- `ContentDigestRecallQuery`: exact SHA-256 digest;
- `TextRecallQuery`: bounded retrieval text plus optional session/time/source
  filters and a frozen work policy.

Results are a closed tagged union, not one permissive bag of optionals:

- `ExactRecollection`: authenticated content, observation/episode IDs,
  sequence, record hash, content digest, provenance, and basis
  `DIRECT_ID`, `CONTENT_DIGEST`, or `CALIBRATED_TEXT_MATCH`;
- `AmbiguousExactRecollection`: two or more individually preserved live
  records have the same exact content digest after all explicit filters; it
  returns total match count plus at most 32 IDs/provenance summaries in the
  deterministic ranking order, but no content, arbitrarily selected personal
  occurrence, or answer authority;
- `ApproximateCandidates`: one or more individually preserved candidates with
  integer score, margin, provenance, and content-omission marker;
- `ConflictedRecollection`: competing candidate metadata, never a blended
  content value;
- `NoRecollection`: only after an exhaustive stable snapshot scan;
- `IncompleteRecollection`: checkpoint, bounded process-local
  `RecallContinuationV1`, and exact work consumed;
- `ProfileUnavailable`: reason code for missing/stale/incompatible/disabled
  calibration;
- `AbstainedRecollection`: explicit policy or risk abstention.

All results also report whether their content is an observation, never a
verified fact. Task 4 may wrap these records with evidence semantics later; it
must not mutate their exact/approximate tag.

### 6.5 Calibration records

`CalibrationSpecV1` contains:

- profile purpose and query stratum;
- exact scorer/normalizer/boundary schema IDs;
- frozen dataset manifest hash and label provenance;
- predeclared sorted unique inclusive Q32 threshold grid;
- target selective risk `alpha` and familywise failure probability `delta` as
  canonical decimal strings;
- minimum selected examples and minimum empirical coverage;
- the rule used to choose among passing thresholds.

`LabelProvenanceManifestV1` records the asserted issuer, adjudication method,
gold source/dataset hashes, fit-example IDs, calibration-example IDs, and any
external signature/reference. Task 2 can mechanically verify schema, hashes,
unique IDs, and disjoint fit/calibration sets. It cannot infer that a human was
actually independent or that a purported gold label is true. Those facts are
explicit audit assertions; Task 12 must independently review their evidence
before a production profile may be accepted.

`LabeledRecallExampleV1` contains only a frozen score, eligibility bit, target
ID from the declared gold manifest, predicted ID, and binary error derived from
those IDs. It cannot contain a model's self-assigned correctness label. The
builder rejects mechanically detectable leakage or overlap; it reports
unverifiable independence as `ASSERTED_NOT_PROVEN` rather than laundering
metadata into proof.

`CalibrationArtifactV1` contains the spec hash, counts for every threshold,
one-sided risk upper bounds, empirical coverage, chosen threshold or
`DISABLED`, generator version, artifact digest, statistical status, and
deployment status. Task 2's builder may prove `STATISTICAL_PASS` for a declared
dataset but emits `TEST_ONLY` deployment status; it cannot mint
`PRODUCTION_ACCEPTED`. Task 12 may produce the latter only after the separate
dataset/label-independence audit and real held-out experiment gate. The
artifact does not contain a callable and grants no authority by itself.
`recollection.py` accepts it only after strict compatibility validation and,
outside explicit test harnesses, requires `PRODUCTION_ACCEPTED`.

### 6.6 Reconsolidation lineage

`ReconsolidationProposalV1` is pure data derived from:

- exactly one `ExactRecollection` parent;
- exactly one live new observation trigger;
- explicit reason enum (`CORRECTION`, `CONTEXT_ADDED`, `USER_LINK`, or
  `OUTCOME_LINK`);
- parent and trigger sequence/record hashes;
- the recall/profile evidence that motivated the proposal;
- no claim that either payload is true.

`ReconsolidationRecordV1` has schema discriminator
`aluclu.reconsolidation.v1`, deterministic `recon:` ID, parent/trigger IDs and
hashes, reason, and schema/profile IDs only. It is content-free with respect to
both parent and trigger. Any new context must already exist as its own typed
observation and is referenced only by ID/hash. The
creation sequence comes from the enclosing Task 1 `LedgerRecord`; it is not
predicted inside the payload before append. The record never copies parent
or trigger content. This prevents a lineage edge from resurrecting either
shredded endpoint.

`RecallContinuationV1` carries the query/policy/profile digests, exact Task 1
snapshot checkpoint, bounded top-k candidate metadata accumulated so far, and
work totals. It is a process-local continuation, not a serialized authority.
Task 9 may later journal an encrypted continuation under its own phase
protocol. If a process dies before that exists, recall restarts from sequence
zero; it must not resume with a checkpoint while discarding earlier top-k
candidates.

## 7. API contracts

The following are interface contracts, not implementation pseudocode.

| API | Input | Output | Side effects |
|---|---|---|---|
| `initialize_empty_sensorium_state` | active `VerifiedLedgerSession`, `BoundaryProfileV1` | initial `SensoriumStateV1` or `SensoriumBootstrapReplayRequiredV1` | reads/captures the current head; returns replay-required unless head sequence is zero |
| `canonicalize_observation` | `ObservationRequestV1`, `BoundaryProfileV1`, current `SensoriumCoreStateV1` | canonical request, pure boundary decision, next core | none |
| `classify_observation_receipt` | active `VerifiedLedgerSession`, canonical request | `ObservationReceiptV1` | none |
| `ingest_observation` | active session, request, boundary profile, current `SensoriumStateV1` | closed `ObservationAcceptedV1 | ObservationRejectedV1` | exactly one `append_once` only when classification is `NEW` and validation succeeds |
| `replay_sensorium_page` | active session, frozen page policy, start profile or `SensoriumReplayContinuationV1` | `SensoriumReplayCompleteV1 | SensoriumReplayIncompleteV1` | reads one stable snapshot page |
| `encode_retrieval_text` | bounded text, feature-spec ID | fixed-width integer feature vector | none |
| `recall` | active session, closed query union, frozen execution policy, compatible profile if required | closed recollection result union plus usage | reads only; direct read or one cursor page |
| `build_calibration_artifact` | immutable spec and held-out labeled examples | enabled or disabled immutable artifact | none; offline computation |
| `tighten_recall_policy` | compatible policy and process-local Task 2 handle | policy no less conservative than input | none |
| `propose_reconsolidation` | exact recollection, live trigger, explicit reason | deterministic proposal | none |
| `commit_reconsolidation` | active session, validated proposal | created/duplicate reconsolidation outcome | at most one `append_once`; no cursor may be active |

All ledger-dependent APIs reject a bare `EncryptedLedger`. Session ownership,
thread ownership, and poisoning semantics remain Task 1's responsibility.
`initialize_empty_sensorium_state` captures an exhaustive tail checkpoint using
the existing session cursor API; it never fabricates a ledger ID/hash. It is
only the Task 2.2 new-ledger bootstrap. A nonzero head fails closed with replay
required, and Task 2.3 `replay_sensorium_page` is the only restart/bootstrap path
for a nonempty ledger.
`SensoriumBootstrapReplayRequiredV1` has exact schema
`aluclu.sensorium-bootstrap-replay-required.v1` and keys `schema`,
`snapshot_head_sequence`, `snapshot_head_hash`, and `replay_from_sequence`; the
last value is always zero in v1.

### 7.1 Frozen Task 2.1 pure API surface

`observation.py` owns exactly these Task 2.1 public operations:

```text
CanonicalJsonValue.from_value
CanonicalJsonValue.from_canonical_bytes
CanonicalJsonValue.to_value
encode_provenance / decode_provenance
encode_observation_request / decode_observation_request
observation_request_to_json_value / observation_request_from_json_value
derive_request_digest / derive_content_digest / derive_episode_id
encode_sensorium_core_state / decode_sensorium_core_state
sensorium_core_state_to_json_value / sensorium_core_state_from_json_value
derive_sensorium_core_state_digest / derive_boundary_signal_digests
build_canonical_observation
encode_canonical_observation / decode_canonical_observation
canonical_observation_to_json_value / canonical_observation_from_json_value
```

`recall_features.py` owns exactly these Task 2.1 baseline operations:

```text
active_normalizer_id() -> str
active_feature_spec_id() -> str
search_view_utf8(text: str, *, normalizer_id: str) -> bytes
encode_retrieval_text(text: str, *, feature_spec_id: str)
    -> RetrievalFeatureVectorV1
feature_vector_digest(vector: RetrievalFeatureVectorV1) -> str
```

The two compatibility IDs are exact:

```text
aluclu.search-view.nfc-ascii-ws.v1+ucd-<unicodedata.unidata_version>
aluclu.feature.signed-byte-ngram-1024-int16.v1+ucd-<unicodedata.unidata_version>
```

Any caller-supplied ID that differs from the active runtime's exact ID fails
closed. `RetrievalFeatureVectorV1` is a frozen, keyword-only, slotted record
with `feature_spec_id` plus exactly 2,048 `bins_i16be` bytes: 1,024 signed int16
big-endian bins. A tuple of unbounded Python integers is not the stored public
representation. `feature_vector_digest` hashes the canonical object with exact
keys `bins_i16be_hex` and `feature_spec_id` under the feature-vector domain.

Task 2 additions to `aluclu.cognition` are strictly additive. Every existing
Task 1 import and every current `aluclu.cognition.__all__` member remains present
and behavior-compatible.

## 8. Data flow

### 8.1 Ingestion and crash-retry flow

```text
ObservationRequestV1
        │ strict validation + canonical request digest
        ▼
classify_observation_receipt(active Task 1 session)
        │
        ├── TOMBSTONED ──> fail closed, no write
        ├── CONFLICT ────> fail closed, no write
        ├── DUPLICATE ───> return stored decision/next state, no write
        └── NEW
             │ pure episode transition
             ▼
      CanonicalObservationV1
             │ one session.append_once
             ▼
      stored record + bounded next state
```

If the process dies after the append commits but before returning, retry sees
the same request digest as `DUPLICATE`, reads the stored boundary decision, and
returns the same next state. No Task 2 sidecar needs crash reconciliation.

### 8.2 Recall flow

```text
Frozen query + policy + profile
        │
        ├── explicit observation ID ──> direct authenticated read
        │                                 └── ExactRecollection(DIRECT_ID)
        │
        └── content/text query
             │ stable verified cursor, bounded page
             │ stream records; keep only top K metadata
             │ close/suspend cursor
             │ direct-read selected payloads within output byte budget
             ▼
      exact digest? ── yes ──> ExactRecollection(CONTENT_DIGEST)
             │
             ├── multiple live occurrences after filters
             │      └──> AmbiguousExactRecollection (no arbitrary occurrence)
             │ no unique exact match
             ▼
      near-tie/different digest? ── yes ──> ConflictedRecollection
             │ no
             ▼
      compatible profile passes? ── yes ──> ExactRecollection(CALIBRATED_TEXT_MATCH)
             │ no
             ├── approximate allowed ──> ApproximateCandidates
             └── personal answer path ─> Abstained/ProfileUnavailable
```

A calibrated text match is exact about the bytes of the selected record, not
about the truth of its content. The profile controls whether the query-to-record
selection is reliable enough to call it recollection.

### 8.3 Reconsolidation flow

```text
ExactRecollection + new live observation + explicit reason
        │ pure deterministic proposal
        ▼
validate parent/trigger IDs and hashes with active session
        │ reject approximate, missing, tombstoned, stale, cyclic, oversized
        ▼
close all cursors
        │ append_once deterministic recon: ID
        ▼
new immutable lineage record; both observations remain separate
```

## 9. Deterministic baseline mathematics

### 9.1 Canonical identity

For domain tag `d` and canonical bytes `b`, every Task 2 digest is:

```text
H_d(b) = SHA256(u64be(len(d)) || d || u64be(len(b)) || b)
```

`u64be` is unsigned eight-byte big-endian and the output is exactly 64 lowercase
hexadecimal characters. These Task 2.1 domain tags are literal ASCII bytes:

| Identity | Exact domain bytes | Exact payload |
|---|---|---|
| Request | `aluclu.task2.observation-request.v1` | complete canonical `ObservationRequestV1` wire bytes |
| Content | `aluclu.task2.observation-content.v1` | `CanonicalJsonValue.canonical_bytes` |
| Episode | `aluclu.task2.episode-id.v1` | canonical object with `boundary_profile_id`, `first_observation_id`, `session_id` |
| Sensorium core state | `aluclu.task2.sensorium-core-state.v1` | complete canonical `SensoriumCoreStateV1` wire bytes; never the Task 1 checkpoint wrapper |
| Boundary profile | `aluclu.task2.boundary-profile.v1` | canonical profile identity object defined in section 6.3 |
| Feature vector | `aluclu.task2.feature-vector.v1` | canonical object with `bins_i16be_hex`, `feature_spec_id` |

Later Task 2 records receive distinct literal domains when their schemas are
frozen; no domain above may be reused. No Python object hash or unordered
iteration participates in identity.

### 9.2 Search view and fixed features

The baseline search view:

1. rejects surrogate code points and every code point whose active Unicode
   database category is `Cn`;
2. applies NFC;
3. maps ASCII `A-Z` to `a-z`, first maps CRLF and lone CR to LF, then maps every
   maximal consecutive run drawn from the exact set
   `{U+0009,U+000A,U+000B,U+000C,U+0020}` to one U+0020 without trimming a
   leading or trailing run;
4. encodes UTF-8;
5. forms the byte frame `ff 01 || normalized_utf8 || ff 02` (`ff` is not valid
   inside UTF-8), then emits every fully contained gram in increasing start
   offset and, at the same offset, length 3, 4, then 5;
6. for each gram `g`, computes an eight-byte BLAKE2s digest with exact
   personalization bytes `61 6c 32 66 65 61 74 31` (`al2feat1`) over the
   framed message `01 || u16be(len(g)) || g`, exactly equivalent to
   `hashlib.blake2s(message, digest_size=8, person=b"al2feat1")`;
7. maps `u32be(digest[0:4]) mod 1024` to the bin and maps an even low bit of
   `digest[4]` to `+1`, odd to `-1`;
8. sums signed occurrences in gram-emission order and, after summation,
   saturates each bin symmetrically to `[-32767, 32767]` for int16 storage.

The original observation content is not normalized or truncated. For every
`retrieval_text` and query, the raw UTF-8 byte length and the final normalized
UTF-8 byte length are each independently capped at 4,096 bytes. Either excess
is rejected rather than silently cut; this prevents a whitespace bomb from
bypassing the active-input bound merely because normalization compresses it.

Let fixed vectors be `x,y in Z^1024`, `S=2^32`,
`d=x·y`, and `n=(x·x)(y·y)`. For `d>0` and `n>0`, the reported similarity is
the following exact integer definition:

```text
score_q32 = isqrt(((d * S) * (d * S)) // n)
```

Integer floor division occurs before `isqrt`, making this a conservative floor
of the nonnegative cosine magnitude at Q32 scale. Ranking compares candidates
without the quantized score when needed: for positive dots it compares
`d_a^2 * n_b` against `d_b^2 * n_a`, then applies the fixed tie order. It does
not use binary floating point. Nonpositive dot product or a zero vector scores
zero. Scores are clipped to the inclusive integer range `[0, 2^32]`, so
`2^32` represents exactly one while the serialized value is not falsely
described as a 32-bit storage type. Literal vector/digest/score fixtures cover
empty, ASCII, Turkish, composed/decomposed, Arabic, CJK, emoji, newline, and
maximum-length inputs.

Ranking is the total order:

1. higher exact integer similarity;
2. higher temporal-filter match;
3. newer observed timestamp;
4. higher ledger sequence;
5. lexicographically smaller ASCII observation ID.

The retrieval margin is the nonnegative difference between the top two Q32
scores. A policy-defined minimum margin is itself calibrated/versioned. If the
top candidates have different content digests and the margin does not pass,
the result is `CONFLICTED`; content is never averaged.

### 9.3 Streaming and state bound

For lifetime record count `N`, feature width `D=1024`, returned candidate cap
`K<=32`, page cap `P<=8192`, and one ledger payload cap `L<=2 MiB`:

```text
search time          = O(P * (feature_cost + log K)) per page
candidate state      = O(KD)
sensorium state      = O(1)
lifetime scan pages  = ceil(N / P)
persistent storage   = O(N), accounted separately
```

The logical Task 2 hot-state budget is:

- sensorium canonical state: at most 4 KiB;
- query/search bytes: at most 4 KiB each;
- one current fixed feature vector: 2 KiB;
- 32 retained vectors: at most 64 KiB raw bins;
- bounded metadata/heap: at most 128 KiB canonical equivalent;
- returned decrypted content: at most 256 KiB cumulative;
- one Task 1 record payload: at most 2 MiB transient.

Python object overhead is measured empirically but cannot change the
algorithmic bound. A caller requesting more work receives paging/incomplete
state, not an expanded allocation.

### 9.4 Selective-risk calibration

For a predeclared threshold grid `T={t_1,...,t_m}` and held-out labeled
examples, define for each threshold:

```text
I_t = {i : eligible_i = 1 and score_i >= t}
n_t = |I_t|
k_t = sum_{i in I_t} error_i
coverage_hat(t) = n_t / n_total
risk_hat(t) = k_t / n_t                    when n_t > 0
```

Let target familywise failure probability be `delta`. For each threshold use a
one-sided Clopper-Pearson binomial upper confidence limit at tail probability
`delta/m`:

```text
U_t = 1                                      when n_t = 0 or k_t = n_t
U_t solves P[Binomial(n_t, U_t) <= k_t]
           = delta/m                         otherwise
```

The numerical solver must return an upper-rounded value, so approximation
cannot make a failing threshold pass. By the union bound, all `m` upper limits
hold simultaneously with probability at least `1-delta`; selecting one of the
predeclared thresholds on this calibration set therefore does not silently
discard the confidence level.

A threshold passes only if:

- `n_t >= min_selected`;
- `coverage_hat(t) >= min_coverage`;
- `U_t <= alpha`.

The chosen threshold is the passing threshold with maximum empirical coverage;
ties choose the higher threshold, then the lexicographically earlier canonical
grid entry. If no threshold passes, the artifact is `DISABLED`. Zero examples,
missing strata, a changed scorer, mechanically detected fit/calibration
overlap, or a changed threshold grid also disable the profile. Independence
that metadata alone cannot establish remains an explicit external audit
precondition for `PRODUCTION_ACCEPTED`, not a fact inferred by this builder.

`risk_hat`, ECE, Brier score, and raw accuracy may be reported as diagnostics,
but none replaces the simultaneous upper-bound gate. The guarantee is scoped
to the declared calibration distribution and assumptions; distribution shift
invalidates the profile rather than being hidden.

## 10. Resource and platform contract

### 10.1 Frozen execution policy

`RecallExecutionPolicyV1` is constructed before recall and includes:

- snapshot/page checkpoint;
- `max_records <= 8192` per call;
- `top_k <= 32`;
- `max_returned_payload_bytes <= 262,144`;
- allowed source/session/time filters;
- profile and scorer IDs;
- minimum score and minimum margin no lower than the compatible calibration
  artifact;
- whether approximate candidates may be returned;
- whether a non-exhaustive page is acceptable to the caller.

When a text scan spans pages, the next call must receive the exact
`RecallContinuationV1` from the prior page as well as its Task 1 checkpoint.
The continuation remains bounded by the same `top_k`, output, and metadata
caps. A bare checkpoint without the accumulator is rejected, because otherwise
an earlier better candidate could disappear and change the final answer.

Task 2 reports records scanned, bytes decoded, candidates scored/returned,
output bytes, and exhaustive/incomplete status. Task 8 will later wrap this
work in issuer-bound leases. Until then, hard caps still apply.

### 10.2 Cross-platform determinism

- IDs and protocol discriminators are ASCII; payload text is canonical UTF-8.
- Timestamps are UTC integer nanoseconds. No locale, local timezone, DST, or
  filesystem timestamp participates in a decision.
- Newlines in the search view follow a fixed rule; original content remains
  unchanged.
- Hash constructors are named guaranteed stdlib algorithms, never
  OpenSSL-provider aliases.
- Integer score comparisons and explicit total ordering avoid BLAS/GPU/float
  nondeterminism.
- The normalizer/scorer ID includes the algorithm version and Unicode database
  version. Surrogate or active-database-unassigned input fails closed rather
  than producing a platform-specific guess; an unprofiled newer database gets a
  distinct compatibility ID and no inherited production authorization.
- Sets and dictionaries are sorted before canonicalization; Python's randomized
  `hash()` is forbidden.
- No Task 2 code branches on `os.name`, path separator, shell, credential
  manager, or platform keyring.

Unicode compatibility is keyed by the exact algorithm ID, never merely by the
Python minor version. The initial protocol manifest recognizes UCD `13.0.0`,
`14.0.0`, `15.0.0`, and `15.1.0` as distinct profiles. Vectors shared across
all profiles use only code points whose assignment and NFC result are stable in
all four databases; assignment-boundary cases carry an
`expected_by_unidata_version` result. A runtime with a newer UCD may create a
new versioned search view and feature vector, but it is not compatible with an
already accepted production/calibration profile until explicit vectors and a
gate add that exact ID. The current local evidence covers CPython 3.12.13/UCD
15.0.0 and CPython 3.13.5/UCD 15.1.0 only.

`src/aluclu/protocols/task2_determinism_v1.json` is canonical JSON with the
exact top-level keys `schema`, `algorithm`, `supported_unidata_versions`,
`domain_vectors`, `search_vectors`, and
`assignment_vectors_by_unidata_version`; unknown or missing keys are invalid.
`schema` is `aluclu.task2-determinism.v1`. `algorithm` has the exact string keys
`identity`, `search_view`, and `feature_vector`, with respective literal values
`aluclu.identity.sha256-u64be-domain.v1`,
`aluclu.search-view.nfc-ascii-ws.v1`, and
`aluclu.feature.signed-byte-ngram-1024-int16.v1`.
`supported_unidata_versions` is the ordered array
`["13.0.0","14.0.0","15.0.0","15.1.0"]`.

Every `domain_vector` has exact keys `case_id`, `domain_ascii`,
`canonical_payload_utf8_hex`, and `expected_sha256_hex`. Every stable
`search_vector` has exact keys `case_id`, `input`, `raw_utf8_hex`,
`search_utf8_hex`, `gram_count`, `gram_fixtures`, `nonzero_bins`, and
`feature_vector_digest_by_unidata_version`. Each selected `gram_fixture` has
exact keys `start`, `length`, `gram_hex`, `message_hex`, `blake2s_hex`, `bin`,
and `sign`. Short cases include enough literal gram fixtures to verify framing
and emission order; `nonzero_bins` is an increasing array of
`[index,signed_count]`.
`feature_vector_digest_by_unidata_version` is an object with exactly the four
ordered keys in `supported_unidata_versions`, each mapped to its 64-character
lowercase digest. The bin bytes are stable for a stable search vector, but the
feature-vector digest also binds the UCD-suffixed `feature_spec_id`, so one
unversioned digest would be mathematically contradictory.
`assignment_vectors_by_unidata_version` is an object whose exact UCD-version
keys map to ordered boundary-case arrays. Each boundary case has exact keys
`case_id`, `input`, `outcome`, `search_utf8_hex`, and `feature_vector_digest`;
`outcome` is `accept` or `reject_unassigned`, and both result fields are `null`
for rejection. The complete 2,048-byte feature vector is bound by the
feature-vector domain digest rather than copied as 1,024 JSON integers.

The same protocol vectors must pass under Python 3.10, 3.11, 3.12, and 3.13 on
Windows, Linux, and macOS, with x86-64 plus an arm64 lane where available.
Local Task 2 completion proves the current Windows host only. A broad
“cross-platform verified” claim remains blocked until the full CI matrix or
equivalent clean hosts run; source inspection alone is not that proof.

## 11. Development phases and TDD execution plan

Every numbered implementation task follows this loop:

1. freeze a task brief with owned files and acceptance oracles;
2. write a real-code failing test and observe the intended RED failure;
3. implement only the task's contract;
4. run focused tests, the entire suite, Ruff, scoped Pyright, compileall, and
   `git diff --check`;
5. append the exact change, verification result, open risk, and next gate to
   root `TRAJECTORY.md`;
6. commit only the task-owned tracked files plus the required trajectory entry;
7. give the complete base-to-head diff and evidence to a fresh independent
   reviewer;
8. convert every valid finding into a failing regression before fixing it;
9. record the review and controller-owned rerun in `TRAJECTORY.md`, then mark
   the task CLEAN only when both are clean.

No later task starts from a non-CLEAN row. The first useful E2E slice is Task
2.2, before calibration/reconsolidation hardening, so progress is continuously
toward a working brain path rather than persistence-only work.

### Task 2.0 — plan freeze and evidence workspace

**Tracked ownership:** this plan, the roadmap continuity invariant, root
`TRAJECTORY.md`, and `.gitignore` entries that keep local workflow state out of
the repository.

Acceptance:

- independent requirements reviewer maps every authoritative Task 2 trajectory
  clause to a section and identifies no missing load-bearing decision;
- independent architect finds no circular dependency, session nesting, truth
  escalation, unbounded active state, or cross-task ownership leak;
- plan hash, branch SHA, current host profile, and review verdicts are recorded
  in the ignored plan-scoped SDD progress ledger;
- the root trajectory records the Task 1 handoff, this plan freeze, review
  verdicts, verification evidence, open risks, and the exact next action;
- Task 1 remains CLEAN and its tracked files are unchanged.

### Task 2.1 — strict observation contracts and determinism vectors

**Files:** `observation.py`, `recall_features.py`, protocol vector JSON,
observation/feature tests, `cognition/__init__.py` exports, and the required
same-change `TRAJECTORY.md` entry.

RED oracles:

- every source kind round-trips distinctly; model origin cannot decode as user
  or tool;
- every pre-existing Task 1 import and `aluclu.cognition.__all__` member remains
  present and behavior-compatible; Task 2 exports are strictly additive;
- unknown fields/schema/source kinds, booleans-as-integers, invalid IDs,
  out-of-range timestamp integers, oversized arrays/raw text/normalized text,
  invalid Unicode, and noncanonical JSON fail;
- literal observation/request/content/episode digest fixtures match on repeated
  processes, hash seeds, timezones, and supported Python versions;
- exact content digest preserves the canonical content's original Unicode
  code-point sequence while the search view has its separately versioned NFC
  representation.
- a complete canonical observation envelope at 262,144 bytes is accepted and
  one byte beyond the ceiling is rejected before any ledger access.
- the canonical protocol manifest validates its exact top-level and case
  schemas; every literal domain, gram, feature-vector, UCD-version, and digest
  oracle matches independently computed fixed expected bytes;
- `CanonicalJsonValue` neither retains nor returns caller-owned mutable nested
  containers, and direct construction with unvalidated bytes is impossible.
- core-state bytes/digests exclude every Task 1 checkpoint field; a regression
  attempting to include the new record's post-append head hash fails before any
  ledger integration can create a self-referential contract;
- maximum-size goal and participant sets keep the digest-only core at or below
  3,072 bytes, and an exhaustive checkpoint wrapper at or below 4,096 bytes.

Exit evidence: focused contracts/vectors, full suite, static checks, and fresh
review are CLEAN.

### Task 2.2 — first vertical slice: storage-pure ingestion and direct exact recall

**Files:** `sensorium.py`, initial `recollection.py`, sensorium/recollection/E2E
tests.

RED oracles:

- classification of `NEW`, `DUPLICATE`, `CONFLICT`, and `TOMBSTONED` matches
  the table and changes neither event count nor head;
- a genuinely new observation produces exactly one append;
- a same-request retry after simulated post-commit process loss produces no
  second record and returns the stored boundary/next state;
- duplicate retry tests cover state exactly one sequence behind, equal, ahead,
  and more than one behind; only the exactly-behind case applies a transition,
  the farther-behind case requires replay, and no case rolls state backward;
- pre/post core-state digest mismatch is `STATE_CONFLICT`, never silent repair;
- same ID/different payload conflicts; deleted ID never resurrects;
- direct ID recall returns the authenticated canonical content bytes and Task 1
  record hash; missing ID returns `NoRecollection` only for that direct lookup;
- approximate result construction cannot satisfy the exact-result type or
  direct-answer authorization;
- integration begins with one active verified session and adds no full
  verification/nested session.

E2E checkpoint: create ledger -> ingest one observation -> recall exact by ID ->
close -> reopen -> recall identical bytes/hash. This is the first working
observation-to-memory path.

### Task 2.3 — deterministic segmentation and bounded replay

**Files:** `sensorium.py`, sensorium/E2E tests, plus the narrowly reopened
Task 1 `ledger.py`/ledger-session tests described below.

Security amendment after RED review:

- Task 1 schema v2 cannot prove the Task 2 pre/post-core lineage of an append
  after crypto-shred destroys its payload key. Task 2.3 therefore reopens Task
  1 for one additive schema-v3 `append_witnesses` projection; no other Task 1
  behavior is redesigned.
- Existing schema-v2 ledgers fail with explicit `LedgerMigrationRequired` and
  are not mutated. A separately reviewed crash-safe migrator is outside this
  task. History record hash/AAD framing remains version 2, so the storage schema
  bump does not silently redefine existing record cryptography.
- Only the private append path reached after `ingest_observation` validation
  atomically mints a witness. Generic `append`/`append_once`, including a raw
  canonical-looking Task 2 payload, never mints one. The underscore method is a
  library trust boundary, not a defense against hostile code executing inside
  the same Python process.
- Each witness is HMAC-authenticated with a ledger-internal key and bound to
  ledger ID, event ID, append sequence, append record hash, exact witness
  schema, post-core link digest, and a canonical body of IDs/digests/profile and
  append/core counters. It stores no observation content, retrieval text,
  provenance text, or record key.
- When a predecessor core is missing, replay must walk an exact ordered chain
  of tombstoned Task 2 witnesses back to the currently adopted core. It must
  also verify an exact live ingest witness for the first surviving observation;
  otherwise a generic raw successor could borrow a valid missing witness while
  presenting an unvalidated post core. Unrelated live/shredded records and
  unwitnessed Task 2-shaped records never bridge the chain.
- When the predecessor core is present but the exact boundary profile object is
  unavailable, replay likewise requires the live ingest witness instead of
  accepting a transition it cannot recompute. A raw record never turns a
  missing profile into implicit trust; an ingested profile change remains
  replayable because its exact append binding survives.
- Witness reads use the same frozen verified-session certificate and remain
  valid across continuation pages without changing the frozen continuation
  wire. Lookup and chain traversal are bounded by the 8,192-record replay cap.
- Deleting a witness without its HMAC is intentionally an availability attack:
  replay fails closed because the bridge disappears. The history chain does
  not commit to witness presence, so this task makes no rollback-detection claim
  for isolated witness deletion; preventing that denial of service requires a
  later history-format/migration design rather than resurrecting shredded data.

RED oracles:

- every boundary reason and precedence combination has a literal expected
  decision/episode ID;
- duplicate retries do not increment episode counters;
- time reversal rejects; time gap uses integer UTC nanoseconds;
- explicit topic/goal/tool/participant/profile changes are separated and never
  averaged;
- 8,192 replayed observations leave `SensoriumStateV1` at or below 4 KiB;
- one-shot replay and every tested page partition produce identical final
  state bytes, core digest, and recorded boundary decisions;
- an incomplete replay returns only `SensoriumReplayContinuationV1`, never a
  completed `SensoriumStateV1`; its checkpoint resumes the exact frozen head;
- replay across a shredded earlier observation adopts only a surviving record's
  authenticated bounded post core and never recreates missing content;
- restart replay at the same ledger head is byte-identical;
- changed-head checkpoint raises Task 1 `LedgerSnapshotChanged`; it does not
  resume against a different snapshot;
- missing work budget returns `INCOMPLETE`, never `NOT_FOUND`.

### Task 2.4 — bounded streaming approximate recollection

**Files:** `recall_features.py`, `recollection.py`, feature/recollection/scale
tests.

#### Task 2.4 binding implementation freeze

This subsection resolves ambiguities found at Task 2.4 entry and is binding for
the RED/GREEN work below. It does not change Task 2.1 feature bytes or Task 2.2
direct-ID behavior.

- Task 2.1's canonical `task2_determinism_v1.json` manifest and its exact key
  set remain frozen. Task 2.4 adds the separately canonical
  `task2_recollection_v1.json` companion with exact top-level keys
  `algorithm`, `ranking_vectors`, `schema`, and `similarity_vectors`; its schema
  is `aluclu.task2-recollection-determinism.v1`. The companion contains sparse
  signed-bin inputs plus literal dot, squared-norm, norm-product, pre-`isqrt`
  quotient, Q32 score, and cross-product ordering values. Neither manifest is
  derived from the implementation under test.
- `FeatureSimilarityV1` is a frozen/slotted runtime value containing exact
  `dot_product`, `query_squared_norm`, `candidate_squared_norm`, and
  `score_q32`. `measure_feature_similarity` and
  `compare_feature_similarity_exact` are pure public operations. The comparator
  returns `1`, `0`, or `-1` for its left operand and treats every nonpositive
  dot or zero norm as the same zero-similarity class; positive values compare
  `d_left^2 * n_right` with `d_right^2 * n_left` before any tie breaker.
- The accepted Task 2.2 call `recall(session, EventIdRecallQuery(...))` and its
  exact `ExactRecollection | NoRecollection` shapes remain behavior-compatible.
  Scan queries require the keyword-only `policy`; a resumed call additionally
  requires the exact opaque continuation returned by the preceding call.
- `RecallFiltersV1` contains sorted-unique session IDs (at most 32),
  sorted-unique `SourceKind` values, inclusive optional provenance
  `observed_at_ns_min`/`observed_at_ns_max` hard bounds, and an independent
  inclusive optional `preferred_observed_at_ns_min`/
  `preferred_observed_at_ns_max` window. Empty ID/source tuples mean no hard
  constraint. A preference window contributes the boolean temporal-preference
  tie breaker but never admits a record excluded by a hard filter. Range ends
  must be supplied together and lower must not exceed upper.
- `ContentDigestRecallQuery` is the exact lowercase content digest plus frozen
  filters. `TextRecallQuery` is bounded text plus frozen filters. The policy is
  separate from both query types: `RecallExecutionPolicyV1` has exact
  `max_records` in `[0,8192]`, `top_k` in `[1,32]`,
  `max_returned_payload_bytes` in `[0,262144]`, active normalizer/feature IDs,
  `minimum_score_q32` and `minimum_margin_q32` in `[0,2^32]`, exact booleans
  `allow_approximate` and `allow_incomplete`, and no checkpoint. Fresh recall
  always captures a Task 1 cursor from sequence zero; only the continuation
  owns a resume checkpoint.
- Score eligibility is inclusive (`score_q32 >= minimum_score_q32`). A
  distinct-content top pair is conflicted when
  `margin_q32 <= minimum_margin_q32`; promotion would require a strictly larger
  margin. Task 2.4 never emits `CALIBRATED_TEXT_MATCH`, even for Q32 score
  `2^32`; Task 2.5 alone may add that transition after compatible calibration.
- The exact total order is unquantized positive cosine by cross-product,
  preferred-window match (`1` before `0`), newer provenance timestamp, higher
  ledger sequence, then lexicographically smaller ASCII observation ID. The
  query's feature vector is common, but implementations still use the general
  exact comparator. Content-digest summaries use the same order with the
  similarity term equal for every exact match.
- `RecallContinuationV1` is a public-name, non-publicly-constructible,
  process-local capability. It contains a Task 1 checkpoint, query/policy
  digests, the literal no-calibration profile digest, bounded top-candidate
  metadata, scalar exact-match count, at most 32 exact-match summaries, and
  cumulative work. A module-private process token authenticates all those
  fields. There is no byte decoder or persistence format in Task 2.4. A
  lookalike, field mutation, different process, changed query/policy/profile,
  different ledger/head, or bare checkpoint fails closed. As elsewhere in
  Task 2, private module state is not a hostile same-process isolation boundary.
- The broad canonical-wire rule in Section 6 applies to a public record only
  when this plan names a wire codec for it. Task 2.2/2.4 runtime query, result,
  usage, candidate, and process-local continuation values are immutable strict
  Python contracts but are deliberately not persistence authorities and have
  no JSON decoders. Task 9 may introduce a distinct encrypted continuation
  record and schema.
- A non-exhaustive page never returns absence, uniqueness, ambiguity, conflict,
  or final candidates. With `allow_incomplete=True` it returns only
  `IncompleteRecollection` and its full accumulator. With
  `allow_incomplete=False` it returns `AbstainedRecollection` with reason
  `WORK_BUDGET_EXHAUSTED`, no absence claim, and no resumable authority. A legal
  zero-record page follows the same rule. Changed snapshot on resume raises
  Task 1 `LedgerSnapshotChanged`.
- Direct-ID absence keeps the existing `NoRecollection`. Exhaustive scan
  absence uses the new closed `NoScanRecollection`, avoiding optional-field
  retrofits. Exact digest uniqueness yields `ExactRecollection` with basis
  `CONTENT_DIGEST`; multiple live filtered occurrences yield
  `AmbiguousExactRecollection` with an exact scalar count, at most 32 ordered
  summaries, and no content. An exact or approximate payload that alone exceeds
  remaining output budget is never attached; exact selection abstains with
  `PAYLOAD_BUDGET_EXCEEDED`, while approximate candidate metadata records
  `content_omitted=True` and `content=None`.
- Output-byte accounting is the sum of attached
  `CanonicalJsonValue.canonical_bytes` lengths. Work totals are cumulative
  across continuation pages and separately report records scanned, canonical
  payload bytes decoded, candidates scored, candidates returned, output bytes,
  and exhaustive status. The candidate accumulator never exceeds `top_k`,
  exact summaries never exceed 32, and no all-record list is permitted.
- During a cursor scan, unrelated schemas are skipped. A payload claiming the
  canonical Task 2 observation schema but failing strict decode or Task 2
  position invariants raises `LedgerIntegrityError`; it is not converted into
  false absence. Selected payloads are direct-read and revalidated by
  ID/sequence/hash/content digest only after the cursor is closed or suspended.
  All exception paths close the cursor.
- The no-calibration profile digest is a frozen literal fixture derived from a
  separately domain-framed canonical null payload. Query and policy digests use
  distinct new literal Task 2 domains. These digests bind continuations but do
  not grant evidence or calibration authority.

RED oracles:

- feature vectors and Q32 scores match protocol fixtures on all local Python
  interpreters;
- literal fixtures verify the exact BLAKE2s message frame, personalization,
  digest bytes, bin, sign, saturation, dot/norm products, integer square-root
  score, and exact ranking cross-products;
- ranking is invariant to input iteration batching and Python hash seed;
- exact digest match is exact; maximum similarity without digest equality remains
  approximate;
- one content-digest match returns one exact occurrence; two or more live
  occurrences after filters return `AmbiguousExactRecollection`, and no latest/
  earliest occurrence is silently selected;
- digest-duplicate accumulation remains bounded and survives paged continuation;
- similar-but-different observations stay separate;
- close top candidates with distinct content digests produce `CONFLICTED`;
- top-k never exceeds 32, cumulative returned content never exceeds 256 KiB,
  and an oversized result is omitted/abstained rather than overallocated;
- streaming pages and a reference exhaustive implementation select identical
  top-k on bounded fixtures;
- an incomplete page cannot claim absence;
- all cursors close/suspend before selected payload direct reads or later
  mutation;
- 2,048 vs 8,192 records demonstrate bounded candidate state and approximately
  linear work, not materialization of all records.

### Task 2.5 — calibrated selective recall

**Files:** `calibration.py`, `recollection.py`, calibration/recollection tests.

RED oracles:

- Clopper-Pearson one-sided upper bounds match independently generated
  high-precision fixtures for zero errors, interior counts, all errors, and
  edge sample sizes; implementation results are never below the fixture after
  allowed rounding;
- the Bonferroni tail is `delta/m`, not `delta` per threshold;
- threshold grid mutation after seeing labels is rejected by hash mismatch;
- choosing among passing thresholds follows maximum coverage then conservative
  tie-break exactly;
- zero examples, too few selected examples, missing stratum, scorer/normalizer
  mismatch, stale dataset, reused fitting/calibration IDs, and mechanically
  detectable label-manifest leakage produce `DISABLED`/`ProfileUnavailable`;
- a manifest's independence/adjudication declaration remains explicitly
  `ASSERTED_NOT_PROVEN` until separate Task 12 audit evidence accepts it;
- a process-local tightening can only be more conservative; serialized lookalike
  input cannot loosen a policy;
- a natural personal-memory query without an enabled compatible profile
  abstains even when its raw similarity is high;
- fixed-seed simulation is diagnostic, while exact fixture/proof checks remain
  the blocking gate;
- calibration artifact construction is deterministic under input permutation
  after canonical example ordering.

No production accuracy/risk claim is made from synthetic fixtures. Task 12 must
generate held-out real artifacts before enabling a release profile.

### Task 2.6 — explicit immutable reconsolidation

**Files:** `reconsolidation.py`, reconsolidation/E2E tests.

RED oracles:

- proposal from approximate/conflicted/missing/tombstoned/stale-hash memory is
  rejected;
- proposal is pure and repeatable; same inputs have the same `recon:` ID;
- commit appends one lineage record and does not mutate parent or trigger;
- reconsolidation payload contains no parent content, trigger content, snippet,
  summary, feature vector, or derived contextual copy;
- process loss after append followed by retry returns duplicate, not a second
  lineage node;
- self-parent, cycles, excessive parents, any unexpected content field,
  mismatched record hashes, and cross-session misuse fail closed;
- later shredding a parent makes it unavailable and the child cannot recreate
  its content;
- conflicting child observations remain distinct;
- read-only recall alone never appends a reconsolidation record;
- a cursor must be closed before commit and the same passed verified session is
  used throughout.

### Task 2.7 — full vertical slice, restart, scale, and portability evidence

**Files:** E2E/scale tests and, only if required, deterministic protocol
fixtures. Production changes require their own RED regression.

Full E2E scenario:

1. ingest typed user/model/tool observations with explicit boundaries;
2. prove storage-pure duplicate behavior;
3. recall one observation directly and one through calibrated synthetic query
   selection while preserving observation-not-fact status;
4. force a near-tie conflict and abstention;
5. append an explicit correction/reconsolidation child;
6. close and reopen the ledger;
7. replay bounded state and reproduce episode IDs, exact record hashes, recall
   ordering, conflict state, and lineage;
8. shred a selected parent and prove no resurrection;
9. run the same scenario with page splits and process restarts.

Scale gate on the current host:

- normal suite uses a smaller deterministic fixture; final evidence runs a real
  8,192-observation, 512-byte-class encrypted ledger;
- compare 2,048, 4,096, and 8,192 streaming recall pages;
- Task 2 incremental RSS at 8,192 is no more than 64 MiB over an empty-session
  baseline and no more than the 2,048 case plus 16 MiB;
- logical caps from Section 9.3 all hold and peak returned bytes stay within
  policy;
- 8,192/4,096 scan-time ratio is at most 2.75 on the same host/run; if host
  noise invalidates the ratio, rerun and retain raw samples rather than
  weakening the target;
- direct-ID recall p95 is at most 2x a Task 1 `session.read` baseline measured
  in the same process;
- one-shot and paged/restarted result digests are identical;
- no hidden full-ledger materialization, plaintext index, duplicate record, or
  additional full verification occurs;
- raw JSON results include host/software profile, seeds, counts, RSS, timings,
  persistent bytes, and exact git SHA.

Portability gate:

- protocol vectors plus the 256-observation E2E smoke pass on Windows/Linux/
  macOS and Python 3.10–3.13 before any broad portability claim;
- at least one arm64 lane runs where available;
- OS-keyring E2E remains Task 1's responsibility; Task 2 smoke may use each
  platform's already accepted Task 1 profile;
- absence of a host does not become a fake pass: evidence states the verified
  host scope and Task 14 blocks the broad release claim until the matrix exists.

### Task 2.8 — final independent gate

Freeze the complete Task 1..2 branch diff and evidence. Run in parallel:

- a fresh code reviewer for correctness, security boundaries, concurrency,
  strict parsing, and test adequacy;
- a fresh architect for module ownership, boundedness proof, no nested session,
  cross-task compatibility, and non-escalation of memory into truth;
- a completion verifier mapping every requirement and acceptance oracle in this
  plan to current evidence.

Any Critical, Important, architectural blocker, missing oracle, sub-target
metric, or portability contradiction reopens the owning implementation task.
The loop continues with a failing regression or stronger experiment; targets
are not lowered to obtain a green label.

Task 2 is CLEAN only when all three final verdicts are clear, the tracked tree
is clean, and the controller records:

```text
Task 2 sensorium/recollection gate: CLEAN
```

Only then may Task 3 implementation begin.

## 12. Verification command families

The controller resolves the active virtual environment explicitly. On the
current Windows worktree the expected interpreter is `.venv313`; equivalent
POSIX commands use the same interpreter/version and test arguments.

Blocking families:

- focused pytest for the files owned by the current subtask;
- complete pytest suite with persistent JUnit evidence;
- Ruff over source, tests, and scripts;
- scoped Pyright over all Task 2 production and test files with zero errors and
  warnings;
- compileall for `src/aluclu/cognition` and Task 2 tests;
- `git diff --check` and exact changed-file ownership check;
- deterministic vector subprocesses under at least three `PYTHONHASHSEED`
  values and two timezones/locales;
- Task 2 E2E and scale commands producing machine-readable raw JSON;
- independent review package hash and verdicts.

No command's exit code is accepted without inspecting the result counts,
skips, warnings, and produced artifact. A skipped platform or calibration case
is missing evidence, not a pass.

## 13. Risks and mitigations

| Risk | Consequence | Mitigation / blocking evidence |
|---|---|---|
| Query similarity is mistaken for exact memory | Confident false personal history | Closed result union; digest/record evidence; compatible selective profile; conflict abstention. |
| Calibration threshold or labels are not genuinely held out | Invalid risk claim | Frozen scorer/grid; simultaneous Bonferroni-corrected exact-binomial bounds; mechanically disjoint IDs; explicit `ASSERTED_NOT_PROVEN` provenance; separate Task 12 evidence audit before production acceptance. |
| Distribution shift makes a once-valid profile unsafe | Silent risk increase | Profile declares stratum/dataset/scorer; mismatch or stale monitor disables rather than extrapolates. Task 12 owns renewal. |
| Full encrypted scan is slow | Poor startup/query latency | Direct-ID path for exact references; bounded paging and honest `INCOMPLETE`; measure linear cost. Later encrypted projections require their own reviewed task, never a plaintext shortcut. |
| Persistent index leaks user text | Privacy regression | Task 2 writes only encrypted ledger records; static/dynamic tests reject new sidecars and plaintext n-grams. |
| Replay materializes lifetime history | RAM grows with use | Streaming cursor, fixed `K/D/P`, bounded state-size and RSS gates at multiple `N`. |
| Duplicate retry advances state twice | Changed episode boundaries after crash | Storage-pure digest classification; duplicate returns stored decision/derived next state; crash-after-commit E2E. |
| Post-state digest includes its own Task 1 record hash | Cryptographic self-reference; observation cannot be constructed | Persist/digest only `SensoriumCoreStateV1`; create the `SensoriumStateV1` checkpoint wrapper after append and never include it in the record digest basis. |
| Maximum goal/participant IDs overflow the 4 KiB state cap | Supposedly bounded state fails valid inputs | Store domain-separated fixed-size signal digests in core state; keep full arrays only in the encrypted observation request. |
| Episode byte counter counts its own stored envelope | Size fixed-point and platform-dependent boundary | Count canonical request bytes only; complete observation envelope has its separate 262,144-byte cap. |
| Reconsolidation becomes destructive overwrite | Lost/confounded history | Explicit new lineage record, parent hash validation, no content copy, no mutation on recall. |
| Deleted endpoint is reconstructed from lineage | Crypto-shred defeated semantically | Lineage stores IDs/hashes/reason/profile only; both parent and trigger payloads stay in their own independently shreddable observations. |
| Task 2 opens another ledger session | Deadlock, second verification, fake `O(1)` claim | Session-only API types, forbidden-import test, integration verification counters, cursor-before-mutation rule. |
| Unicode/locale/platform drift changes results | Restart/host mismatch | NFC search view, explicit normalizer/scorer IDs, ASCII protocol fields, integer ranking, public cross-platform vectors, fail-closed unsupported input. |
| Deterministic byte n-gram baseline has weak semantics | Low recall coverage | Honest approximate label and abstention; Task 12 compares learned alternatives. Weak quality never justifies type escalation. |
| More persistence hardening delays the brain path | “Fort Knox without a brain” | Task 2.2 delivers E2E ingestion/direct recall early; Task 1 stays frozen unless a concrete regression is proved. |
| Passing unit tests hides unusable behavior | Green but non-functional system | Restarted E2E, real 8,192 scale run, selective-risk fixtures, raw metrics, and independent completion audit. |

## 14. Research sources

- ALUCLU global roadmap and binding invariants:
  `docs/superpowers/plans/2026-08-12-unified-lifelong-cognition.md`.
- Current Task 1 persistence/session contract:
  `docs/superpowers/plans/2026-08-22-task-1-persistence-reconstruction.md`
  and the production code at commit `f5a30e0`.
- Angelopoulos et al., *Conformal Risk Control* (finite-sample risk-control
  framing and held-out calibration): https://arxiv.org/abs/2208.02814
- Lee et al., *Fair Selective Classification Via Sufficiency* (risk/coverage
  tradeoff for abstaining classifiers):
  https://proceedings.mlr.press/v139/lee21b.html
- Clopper and Pearson, exact binomial confidence limits; modern discussion of
  conservatism: https://doi.org/10.1093/biomet/26.4.404 and
  https://doi.org/10.1191/0962280203sm311ra
- Unicode Standard Annex #15, normalization, versioning, and stabilized-string
  constraints: https://www.unicode.org/reports/tr15/
- Python `hashlib` guaranteed algorithms and BLAKE2 interface:
  https://docs.python.org/3/library/hashlib.html
- RFC 7693, BLAKE2: https://www.rfc-editor.org/rfc/rfc7693
- Nader, Schafe, and LeDoux, *Fear memories require protein synthesis in the
  amygdala for reconsolidation after retrieval*; used only as biological
  inspiration for explicit reactivation/update, not as proof of software
  behavior: https://doi.org/10.1038/35021052

## 15. Architecture quality checklist

- [x] Every planned directory/file has one owner and purpose.
- [x] Dependency direction is acyclic and Task 1 does not depend on Task 2.
- [x] Data flow is unidirectional and the single-session boundary is explicit.
- [x] Exact, approximate, confidence, and truth are separate modalities.
- [x] Active-state and output bounds have formulas and measurable caps.
- [x] Calibration selection has a simultaneous finite-sample bound and a
      fail-closed empty/underpowered outcome.
- [x] Restart, duplicate, crash, deletion, and reconsolidation semantics are
      explicit.
- [x] Cross-platform determinism constraints and the honest proof scope are
      explicit.
- [x] No new external library is required; existing library choices were
      checked against their maintained primary documentation.
- [x] Development phases produce an early functional vertical slice and then
      add calibrated/lineage rigor without changing the end state.
- [x] Final completion requires requirement-by-requirement evidence, not absence
      of known failures.
