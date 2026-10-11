# Checkpoint139: mask subroutes and direct endpoint binding

Baseline003c1522ba9ca5f5e1b9d681a6b41bcf4330d1b4, clean authoritative Desktop
checkout verified. Full objective reread; previous goal turn was PROGRESS.
No model/corpus/held-out/GPU/training acquisition or optimizer update authorized
by these component fixtures. Unified neural learning/portability goal stays OPEN.

## Gap, fixture repairs and implementation

Nine additional helpers: find_packed_sequence_indices,
packed_sequence_mask_function, or_masks, blockwise_overlay,
maybe_pad_block_sequence_ids, _can_skip_bidirectional_mask_xpu,
bidirectional_mask_function, create_bidirectional_mask, _vmap_expansion_sdpa.
Four direct callable endpoints: Torch arange/diff/where and functional.pad.
The masking F namespace must match the actual imported functional module.
Existing function code/default/closure freezer and exact namespace bindings used.
No masking computation is invoked by the fingerprint helper.

REDv1 had52 proper drift failures plus THREE fixture argument mistakes: absent
required past_key_values argument, and a pad-substitute input named value that
collided with the value keyword. These three are NOT numeric gap evidence.
Receipt retained. Fixed fixtures BEFORE implementation and reran REDv2: all55
now fail for actual drift/missed denial or unchanged fingerprint after changed
numeric output. Two examples execute actual create_causal_mask on tiny packed
positions; one executes block-ID padding. No full language model is loaded.

Final61 cases:52 eager/SDPA preparation/replay denials, three numeric examples,
six unsupported helper/endpoint/namespace schema cases. Denials verify no added
block side effect, lease release and factor-gradient cleanup. Substitutions are
pytest-monkeypatch restored. Tiny fixture owner/shared factory comes from137;
positive unchanged eager/SDPA factor-gradient leases remain in regression scope.
Factor gradients are not actual-host attention parity or neural acquisition.

## Receipts

Existing research CPython, PYTHONPATH=src, PYTHONDONTWRITEBYTECODE=1,
Python-B -m pytest-q -p no:cacheprovider --tb=short, unique JUnit paths.

| Attempt | Actual pytest exit | Tests/failures/errors/skipped | Time | XML SHA256 |
|---|---|---|---|---|
| red_v1 | 1 | 55/55/0/0 | 11.757s | 3bb92f143d800dd23e18459e680f7a8cede3235dcd1eb4900a81fe45946d60c8 |
| red_v2 | 1 | 55/55/0/0 | 6.862s | c6461a15f6503b0aca3111539a61258e7227053caaae0e9edde8aab706ed1fd7 |
| green_v3 | 0 | 211/0/0/0 | 7.976s | 4521e5901916af23cdacbc350d32cb8e8604f4be5efd2679305bb4a68fbe7d38 |
| full_pure_v4 | unobserved | 808/0/0/0 | 12.175s | 3040af18842ca7daf480a8ffa0db65996e07046c2dd9ebdd221d16640e9e3283 |
| full_pure_v5 | 0 | 808/0/0/0 | 116.143s | 4aa7f3ae03f8a61cd207e3dbf6ef3469f656e236a0fb096b2e401443141fc5fb |

green_v3 precedes a Ruff blank-line correction. v4 XML includes61 new cases;
final source hashes matched. Terminal tool session86828 was missing on poll;
matching Python command lines were absent, so v4 actual exit is NOT inferred.
A new distinct v5 receipt run was launched only after that terminal-state check;
session66643 and matching Python28720/21208 subsequently confirmed live.
v5 later terminated with root-witnessed actualpytest0; root parsed all counts,
61 new cases and XML hash. Final reviewed source/test hashes unchanged. Original
receipts preserved. Variable suite durations are NOT latency/resource evidence.

## Reproduction and review

Use checkpoint138's exact23-target pure regression command, prepend
tests/test_alc_r0_mask_subdependencies.py. Total24 explicit targets; keep both
asset-case deselections and existing research environment from134. Always NEW
JUnit filename. Not the full repo/model/GPU suite or a resource benchmark.

- Helper SHA256:aec719586209e64fc69679e16d4c34e906e8fcbef9e96a9670777438f64d4c58.
- Tests SHA256:18cdf0eec812a47f229452ff5dc8ae1ffcf67946895afe51feef8e368cd84ed0.
- Original reused review handles disappeared after continuation; new isolated
  GPT6.1Sol lanes reviewed exact source/test bytes. Code APPROVE, architecture
  CLEAR; synthesis APPROVE ENUMERATED MASK SUBROUTES/ENDPOINTS ONLY.
  Reviewers performed read-only file/hash inspection, no imports/tests/models,
  and did not infer then-pending v5 outcome. Root independently observed terminal
  exit and parsed final receipt. No approval inferred from checkpoint138 review.

## Open boundaries

Enumerated function and endpoint binding only. Same callable identity is not
native implementation proof. Tensor methods, finfo/class behavior, remaining
Torch endpoints, vmap context classes, registry/class dispatch, transitive
globals and actual-host route qualification remain OPEN. Binding unused branch
helpers does not certify all active branches. No callback certificate, actual
model parity/resource acceptance, real neural learning or final .alc acceptance.
