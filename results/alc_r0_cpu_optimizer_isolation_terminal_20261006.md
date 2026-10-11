# Checkpoint207 CPU accelerator isolation and fail-closed preflight

Actual random CPU model v2 remains FAIL, never retroactive PASS:
session26579 actualexit1, persistedexit1 child20816, observed2026-10-06T15:53:54+03:00.
JUnit1test/1failure/0errors/0skipped,1040.458seconds;
XML8b2f1ee9b6838e2e191324e3f4211c22de84be10e3cff46c5f3fe8a06d26627a.
stderr0bytes. Trace reaches first AdamW step after unchanged cell comparisons;
torch2.14 optimizer health-check requests available accelerator current_stream,
which hits forbidden CUDA initialization despite all factor parameters onCPU.
No completed-cell receipt, moment comparison or learning success exists.

Installed optimizer.py475-485 and official primary documentation reviewed:
https://docs.pytorch.org/docs/stable/cuda_environment_variables.html
Process-start CUDA_VISIBLE_DEVICES=-1 hides GPUs; no optimizer/health-check,
gradient/fixture/comparator/threshold mutation. Fixed CPU launcher records the
setting and restores its prior process environment in finally. Not machine/user
environment changes, CPU build installation or GPU/backend fallback.

Tiny single2element parameter CPU AdamW uses prescribed3e-4/.9,.999/1e-8/wd0/foreachFalse/
fusedFalse with actual norm1 clip, step1 CPU finite state and parameter change.
CUDA seed/init guards remain; exact-1 inherited environment and no available
accelerator/no initializedCUDA are asserted in final test.

First tiny REDtool823f95exit1 was a test harness duplicate guard callable issue
in lazyTorchDynamo rules, not the optimizer reproducer. Preserve that XML.
Corrected REDtoolf50689exit1 reaches exact accelerator initialization defect.
Fresh masked focusedtool47d9e6exit0 then fixedrunner smoke05a942exit0.
Strengthened runner-v2 smoke594ec3exit0;1/0/0/0,3.435s,
XMLebff8a7e0950b44d387e95310eb21997e61c9aeaf0595f448b103dc9415e0938.

Independent codeREQUESTCHANGES/architectureBLOCK initially rejected order-only
preflight. Repaired suite-specific-x prevents entering expensive integration on
isolation failure. Deliberately invalid visibility-2, exact tiny+full test order,
pytest-x control d2ee9aexit1:JUnit1test/1failure/0errors/0skipped,6.921s, only tiny
case present; captured stdout explicitly stopping after1failure. This is expected
negative stop-control evidence, NOT a passing model run. No full model executes.

Final runner-v3 smoke5921f9exit0;1/0/0/0,3.851s,
XMLfb76016c0e7ffaccc196f5493477c4986a5518976d653ca56c926fd114068670.
Final fixed Regression session78290 personallyactualexit0 and persistedexit0,
child23520 at2026-10-06T16:14:58+03:00;325/0/0/0,24.166s,
XML1b4ebca75606ccb56a34997cbfb6060f97cbcf79658bbaf2bb146572f6c76edb.
Ruff checks and PowerShell AST parser passed. Final fixed-runner smoke/regression
have persisted start/stdout/stderr/exit/XML artifacts; foreground tiny RED/focused/
stop controls have tool transcript and XML only, no invented process logs.

Exact reviewed runner SHA84e8edc87ab1e81ffbf536c668484b2b2b7af44c1aa8db73127f193afed8e298.
Tiny test SHA93a79d29e7c8f252c01d17462bb0081f84f8d6c57d072a6803486bb1ed410597.
Full integration test SHA6014c7695726c459aa77a8c165a1383b0e4b25167db6bf3a0bfdf8767abc7dcd.
Final independent GPT6.1Sol codeAPPROVE/architectureCLEAR for isolation/preflight;
operationalWATCH no reservation/lock/timeout. ConditionalADMIT one fresh v3 CPU
integration after final committed hashes/currentheadroom/process/freshstem checks.
Actual pretrained assets/tokenizer/corpus/GPU/research-accounting/E3/learning
authorization and acceptance are NOT provided by this checkpoint.
