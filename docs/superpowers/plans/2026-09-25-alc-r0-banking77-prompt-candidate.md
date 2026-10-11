# ALC-R0 Banking77 common-prompt candidate

Status: development-only, non-authorizing R0.0 candidate. No held-out data or
model-training result was inspected to select this rule. The byte-frozen source
plan (`0493eeed795dbf089babe54bc14204e30d82c7381c4b819afdf986c0baff6c9b`)
is unchanged. R0.0 must still freeze this candidate (or transparently replace it
before confirmatory data access) in a machine-readable preregistration.

## Exact reference rule

Use the source category-file order of 77 canonical lowercase labels. Encode
three fields *separately*, each with `add_special_tokens=False`, then
concatenate token IDs:

```text
prefix = "Labels: " + " ".join(labels) + "\nInput: "
query  = NFC(CRLF-to-LF(utterance)).strip()
suffix = "\nIntent:"
prompt_ids = encode(prefix) + kept_encode(query) + encode(suffix)
```

The query must be nonempty valid UTF-8. Reject any explicit BOS/EOS token in
the three encoded spans. Candidate IDs are still exactly
`encode(" " + canonical_label, add_special_tokens=False)` from the scoring
contract; they are appended to `prompt_ids`, never re-tokenized together with
the prompt string. Do not prepend BOS or append EOS. The answer boundary and
all 77 labels are never truncated.

Compute `max_candidate_tokens` once over the ordered label list. Reserve it
for *every* example, so every candidate sees identical prompt IDs. With total
common budget 512, `query_budget = 512 - len(prefix_ids) - len(suffix_ids) -
max_candidate_tokens`. Fail if fewer than one query token fits. If the query
has more token IDs than this budget, retain its first `ceil(query_budget/2)`
and last `floor(query_budget/2)` IDs in that order. A one-token budget keeps
only the first token. The same transformation must be used in training and
every comparison/evaluation arm; it is not an adaptive per-arm truncation.

On the pinned local SmolLM2-135M tokenizer and verified official-train-derived
9,999 unique development rows: prefix 472 IDs, suffix 4, longest candidate
17, leaving 19 query IDs. Query lengths were min 3, median 11, p95 34, p99
49, max 96. **1,483/9,999 (14.83%)** queries require head/tail truncation;
the longest resulting prompt-plus-candidate is exactly 512 IDs. This is a
capability-quality risk, not a PASS result. The earlier tentative full-string
space-delimited measurement in TRAJECTORY checkpoint 24 used a different
tokenization boundary and found 1,575 over-budget rows; it is superseded for
this *candidate* rule, not silently erased.

The reference and fixtures are `src/aluclu/alc_r0/banking_prompt.py` and
`tests/test_alc_r0_banking_prompt.py`. A later R0.0 freeze must bind their
source hashes, tokenizer bytes, exact prompt token IDs/roots and field order,
the 512-token limit, all three split roots, and evaluator enforcement before
training or held-out access is authorized. This document alone grants no
training or confirmatory-evaluation authority.

The development-only candidate receipt is
`results/alc_r0_banking77_prompt_candidate_20260925.json` (exact LF bytes,
SHA-256 `0a2c08ef5dee37e9a75e8fe088a05be36392a696c1bf63bc82c5341256874661`).
It binds the source receipt, ordered labels and candidate IDs, prefix/suffix
IDs, and ordered train/dev prompt-token streams by SHA-256 without storing raw
utterances. It records 1,207 truncated train rows and 276 truncated dev rows.
`banking_prompt_receipt.py` regenerates it from the verified development
source and local tokenizer, and the pinned-asset test checks byte-for-byte
equality. This receipt intentionally does **not** claim it has verified the
model/tokenizer acquisition inventory or the evaluator environment; those
checks belong to the later R0.0 validator.
