# Checkpoint203: bounded generic parity failure journal

Parent7a855a4c974177ac4859fa25ae3ff63197bdf3e4. Small synthetic cooperating wrappers
and failure injection, no actual pinned-host/model/tokenizer/corpus/GPU acceptance.
Original numerical comparisons, seed, fixtures, schedule, accumulation16 and
optimizer ordering remain unchanged. No retry, rollback or learning claim.

## Personally observed terminal evidence

Pinned existing CPython, PYTHONPATH=<Desktop worktree>/src; pytest -q and one
--junitxml=results/<stem>.xml argument. Foreground tool output was observed; no
separate raw stdout/stderr/exit files generated. This note is a transcription.

- RED tool46b99c exit1,16 tests:15failed missing new journal API,1passed original
  success path. XML815e48958fdbb294ba1bd5888766d8204bb97a716ec50d8457ee20b345ac1b61.
- Regressionv1 tool64627 exit0,127/0/0/0 tests/failures/errors/skipped,12.805s.
  XMLf46685402702592bd2268f29a3964c733314b9b6759d64887e99f9d93e39a49b.
- Expandedv2 tool57499 exit0,377/0/0/0,33.910s; stdout100pct.
  XML92b298d42979686a4cb10dfce9883aefa8e416c1fb6bd24bf9b9ba889e6f4a93.
  Includes new failure, parity_cell, parity_matrix, parity_qualification,
  reference_parity_receipt, checkpoint_observation, pending_observation,
  accumulation_pair and checkpoint_optimizer test modules. Relevant processes
  absent afterward. These are separate runs, not summed suite evidence.

## Exact-byte independent GPT6.1Sol review

- Source checkpoint_parity_cell.py:
  39625fc9e642918154a4e87004493f5403662134aa2739f5938312620b5ba732
- Tests test_alc_r0_parity_cell_failure.py:
  830beee39ded291359ab7f18f58a752bb2cda76b702eac6eadf07d896d92e1c4

Code/spec APPROVE, architecture WATCH; combined COMMENT, not merge-ready APPROVE.
Reviews were read-only; no independent execution inferred. Ruff checks passed,
final hashes unchanged and git diff checks passed. Admission remains outside
execution wrapping. Ordinary errors are ObservationError subclasses, interruption
is a KeyboardInterrupt subclass; message/original cause and gradient cleanup remain.

## WATCH boundaries and required continuation

The bounded failure payload contains single-row scalar/digest receipts, current
single key, remaining SINGLE keys, stage and validated pending losses. It is not
a success receipt. A first candidate can be recorded before pair-ranking succeeds.
After18 singles, current=None and unrun=() can coexist with pending/accumulation/
final-base failure. Always preserve stage; only successful ParityCell return proves
that this complete synthetic pipeline finished.

Chained traceback frames can retain wrappers/logits/optimizer/autograd objects.
Clearing gradients is not rollback or bounded exception retention. The outer
owner must persist .failure plus textual error then discard exception/traceback
and wrappers, or terminate the owned attempt process; never cache live exceptions.

Accumulation remains one delegated stage, without internal microbatch/clipping/
step/state-comparison progress. A failed attempt may have stepped one or both
disposable optimizers. Internal-stage journaling, fixed q/v factory/geometry/
source/fixture binding, separate success-receipt composition and real numerical
integration remain required before actual qualification. Durable process-kill/
timeout evidence is an outer-launcher responsibility. No accounting/rights/
evaluation/actual-host/learning gate is closed by this checkpoint.
