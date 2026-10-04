# Checkpoint155: fixed one-base matrix composition

Scope: fixed synchronous section-D matrix binding, no loader or actual-host
invocation. Original v1 plan section3.1 order: M/L/ML each rank4/8/16, capsule
then q-only LoRA. One supplied frozen base, exact reviewed factory/cell functions,
no injectable production execution callbacks, retries or dropped cells.

Factory checks BEFORE observations: exact wrapper/factor classes, base identity,
ports/rank/seed, names/counts/shapes, matching original A across both arms. Base
bytes/rosters are checked across construction and complete cells. Structurally
complete cell receipts join the completed prefix; terminal errors preserve
completed/current/unrun and original cause. KeyboardInterrupt remains its own
exception kind. Launcher still owns durable journaling, resource/45min ceiling,
runtime/source/host/tokenizer authentication and official-forward regressions.

## Independent review

Source SHA256 c7aa8a70eb5aa6bdbd3106debd1515f2ff11dfc01692db84ea9179646c052552.
Initial tests SHA256 5e262ad13dd14fda1592f0a5ed85f01977c0fce824b67e468589e59f92d38270.
Initial GPT6.1Sol code APPROVE and architecture CLEAR. Code lane recommended
direct negative tests of matrix-local guards; architecture initially could not
locate originalv1 ordering but later verified the exact plan lines180-203.

Final tests SHA256 7c060322d59d5761279640c49ec91b1883108f3b9eade8316d8bbdfe08ccf04f.
Nine added guard/receipt controls; source unchanged. Final architecture CLEAR.
Final code test-only rereview first errored with usage limit; one retry returned
APPROVE at exact final hashes. Final synthesis APPROVE/CLEAR, no author-lane
approval fallback. Reviews read exact bytes without imports,
tests/host/corpus/optimizer/network/writes or consulting the other lane.

## Execution evidence

Tests use actual factor/wrapper construction over FakeBase, but STUB cell
execution. They verify binding/order/error-prefix/shape/metadata guards, NOT
actual-host full-D parity. No dataset, model weights or task learning run.

| Receipt | actual pytest | tests/failures/errors/skipped | seconds | XML SHA256 |
| --- | --- | --- | --- | --- |
| red_v1 | 1 | 14/14/0/0 | 90.195 | bdebf59f7ed008dbab46b15a3ff5fc0d9dfbc7bbd26924987bacbff80c2d34b1 |
| focused_v2 | 0 | 102/0/0/0 | 130.505 | a749d225a3f67d4ea459c39f5b3c4a259d4d5d1c0f5594171eefded1c7381fc6 |
| regression_v3 | 0 | 1230/0/0/0 | 109.356 | 668278b8f769dd16bd0abe437554642cf2cea223db9e98f981a9f9eaca09a66c |

Focusedv2 predates nine final tests and is intermediate evidence only. Wider
final40-target component regression terminal actualpytest0 personally consumed
on original15643; root parsed counts,23new cases and XML SHA256. Both reviewed
source/test hashes unchanged; Ruff/diff clean. Two real-CUDA/tokenizer tests
explicitly deselected as in prior component suite; not whole-repo/host or
portability evidence. Full unified goal ACTIVE. Actual D,
resource E1/E2/E3, scientific capability, durable learning and ALC gates OPEN.
