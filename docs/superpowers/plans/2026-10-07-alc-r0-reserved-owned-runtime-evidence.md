# Reserved Windows owned lease: execution evidence

Parent eac26df671d3f95c7dbde5c049a3cc018eb80c8b.
Status: scoped Windows component accepted, code APPROVE / architecture CLEAR;
no scientific launch or whole-program completion.
The first-checkpoint document remains historical, not rewritten as final proof.

## Exact reviewed final inputs

- Contract: 14cdc65cbd36d4e38939171e3669e95850b84ef8d320c6ad7ed7f8c10a790bdc.
- Source: 7c2661c4b67c07506a7c47e8aff903ffbd06f340fb2b61f25c46fb1a4862a066.
- Final tests: 5ab7bc7a9a38b64dc72746bc1531d6dcb2ecd2db737d54b5d909c4eb07021383.
- Diagnostic worker: e1a38895395b943f61807b3fc3a67177887660b723789c3377eed2b5611382f2.
- Initial expanded test bytes: db917930d81cd8c5575d049617d49defd81b993596b543762f2da620fef82572.

Source changes add a protected default owned-handle creation-time observation,
not an arbitrary launch callback or module-global mutation. Resource-free cleanup
does not import _winapi and mask unsupported-host validation. That last property
is source-inspected; Windows tests do not establish native non-Windows execution.

## Native terminal observations and artifacts

Every invocation used the existing pinned Windows training venv, authoritative
Desktop cwd, no pytest plugin autoload, CUDA hidden, no user site/bytecode, and
explicit src path. No model/tokenizer/corpus/GPU/assets or paid compute accessed.
Author retained original hidden native process handles, observed terminal/exit,
then parsed JUnit/hashes. No edits occurred while those tests were live. Review
lanes independently admitted each exact invocation; their artifact review does
not replace author's original native observation.

| Stage / results stem | Native PID / exit | JUnit tests/failures/errors/skips | Time | Native evidence |
| --- | --- | --- | --- | --- |
| alc_r0_reserved_owned_entry_red_20261007 | 2600 / 1 | 2/2/0/0 | 0.794s | tool9ec2e6 |
| alc_r0_reserved_owned_extended_green_20261007 | 30944 / 0 | 22/0/0/0 | 18.290s | session71576, tool78f4f4 |
| alc_r0_reserved_owned_final_regression_20261007 | 27760 / 0 | 135/0/0/0 | 44.217s | session24144, toolab983e |
| alc_r0_reserved_owned_final_regression_v2_20261007 | 28848 / 0 | 138/0/0/0 | 59.789s | session54439, tool59252f |

XML SHA-256 in the same order:

1. 78bb74d8b57845d0c3e86952183895b6f85e52f537dec0488fa4b5dc61788945
2. 8adbe4e2e1b212a29b49dde0239381c0df76ce47312cf38e0f44e86d72aa95a6
3. 4bab26afabbe37e6ed2f10338035e5436b40eb583226aee29e27d8f8bc72242a
4. f784d9f39015f7efb8ee04e93fe739dab3be3cbc1b8657c806f53c46cfb336c7

Each stem has separate stdout.log,stderr.log,exit.json,xml. All stderr files empty.
RED specifically reports both DID NOT RAISE failures before the observation seam;
ordinary context cleanup still drains the suspended fixture. GREEN/stdout contains
22 passing dots; final v2 contains 138 passing dots/100%. Exit JSON binds PID,
exit code and original_handle_terminal=true. A wrapper timeout is never PASS.

The first three stages bind expanded tests db917930..., not the final three new
cases. Only v2 supports final test SHA5ab7bc7a...; previous135-case evidence is not
reused for those additions. Regressions include lease, legacy owned process,
reservation store and pure state; no full-suite or capacity benchmark claim.

## Contract coverage and claim boundary

The final lease file contains25 focused cases; relevant regression includes them.
These establish suspended creation/no execution before durable identity, exact
handle-derived identity/receipt, durable CREATED->READY->single resume->RUNNING,
global lock release before terminal wait, nonzero/timeout descendant handling,
held reservation after close and lost durable responses, exact owner/state/
clock/deadline checks, forged caller receipt denial, lifecycle/thread checks,
exclusive output preservation and failure after actual creation before identity.
The postcreation OSError/KeyboardInterrupt fixtures directly observe duplicated
owned process handles terminal with exit124, closed local handles, no sentinel,
available global lock and still-held RESERVED state.

Three real abrupt-parent phases (postcreation,READY,RUNNING) execute os._exit(73)
inside the new lease coordinator. An outer legacy private job is a containment
safety net. Each outer receipt must be exit73,not timed out,active_processes0
before its original12second deadline; RUNNING also observes the child's execution
sentinel and a live-descendant process count. Fresh explicit-root store reads
retain RESERVED/READY/RUNNING plus4096 pending bytes. An outer timeout/termination
would not prove inner orphan prevention. These are ordinary contained Windows
process-crash tests, not powerloss, privileged escape or hostile-host proof.

The outer-child membership/last-handle behavior was checked against Microsoft's
[Job Objects](https://learn.microsoft.com/en-us/windows/win32/procthread/job-objects)
and [Nested Jobs](https://learn.microsoft.com/en-us/windows/win32/procthread/nested-jobs)
documentation; actual receipts remain the runtime proof for this tested scope.

## Still not implemented or admitted by this component

The lease is trusted execution plumbing, not a sandbox, authority verifier,
numeric historical/calendar reconciliation, bounded output sink, fixed scientific
declaration/work-ceiling producer or resource-admission system. READY/hash roots
are not permission. CPU process times are not measured GPU allocation. A terminal
receipt does not automatically reconcile/release charge. No model training,
host qualification, capability gain, .alc durability or portability PASS follows.

Next scientific execution dependencies: enforce reviewed log byte caps; bind
trusted operator authority/clock and explicit declarations/resource observations;
reconcile historical charges/calendar under the existing owner-approved method;
qualify pinned host/runtime; run original four200-update pilots. No method re-ask,
new600GPUh/45day allowance, altered grid/threshold or paid external compute.

Both existing GPT-6.1 Sol lanes independently reviewed final component coverage,
source/test/worker identities, all four XML/counts/hashes, empty stderr and stored
exit consistency. They explicitly found no remaining blocker within the declared
Windows lease scope. Their acceptance does not extend to those scientific
dependencies or substitute for the author's original native terminal observation.
