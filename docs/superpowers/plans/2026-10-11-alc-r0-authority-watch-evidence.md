# Pure authority-watch policy runtime evidence

Status: terminal results independently accepted, code APPROVE/architecture CLEAR.
Parent b9ddb511b2cdcc31ed76b68fe4fae70a4794f5b1; Desktop authoritative checkout
`.worktrees/unified-lifelong-cognition-local`. This is deterministic synthetic
timing-policy validation, NOT a live monitor or model/training experiment.

## Executed byte pins and invocation

- src/aluclu/alc_r0/authority_watch_policy.py SHA256
  bfeea17a15537ebe9bee0e041bf2a23b3fd2e47fe2c8a83af8e10dd7179db97f
- tests/test_alc_r0_authority_watch_policy.py SHA256
  90268d3cb605683717e63ba180023ada98128b7a832ab70d5ff8e4463a6986f2
- tests/alc_r0_authority_watch_test_runner.py SHA256
  463c839dabc09dac90ba6349d834cfb87efbf6594cf15aba425f12282ed73918
- Admitted design before status updates SHA256
  503d2e2734e8075746e60eb441935cf7202f138c8a9c4f34159726c23673be81

Existing Windows CPython3.12 research interpreter, no dependency changes:
`C:\Users\kaann\AppData\Local\Packages\OpenAI.Codex_2p2nqsd0c76g0\LocalCache\Local\ALUCLU\research\alc-r0-smollm2-135m-v1\windows-training\.venv\Scripts\python.exe`
invokes `tests/alc_r0_authority_watch_test_runner.py` with closed red, green,
regression modes. Runner invokes pytest under existing owned-process supervision,
300second original entry deadline and existing cleanup tail; refuses overwriting
retained artifacts. Environment selects Desktop src, no user site/bytecode,
pytest plugin autoload disabled and CUDA_VISIBLE_DEVICES=-1. Diagnostic primitive
does not substitute for ReservedOwnedLease scientific admission.

## Personally observed terminal evidence

Artifacts stem `results/alc_r0_authority_watch_{mode}_20261011` has stdout.log,
stderr.log, exit.json and XML for each mode. Native receipts and XML, not wrapper
success, determine the following results:

| Mode | tests/failures/errors/skips | JUnit seconds | pytest exit | root/total/active |
| --- | --- | --- | --- | --- |
| red | 1/1/0/0 | 0.268 | 1 | 25576/3/0 |
| green | 25/0/0/0 | 0.198 | 0 | 23388/3/0 |
| regression | 215/0/0/0 | 74.274 | 0 | 472/19/0 |

Every receipt timed_out=false; all stderr0bytes. RED is precisely the intended
missing authority_watch_policy module, not a collection/dependency failure.
GREEN follows source implementation. Relevant regression contains watch25,
fixed-worker30, wire111, projection49; unchanged final source/test/runner pins
were checked after original session12800 terminal d5b2f1. No full-suite claim.
Original native handles were personally observed by the author; independent
reviewers corroborate retained artifacts rather than claiming that observation.

XML SHA256:
- RED d87e93ebeb8cd9224d595309a0d3a59e8a3b45af1bb9faac55634dc40bc0cef4
- GREEN 2062a800e0197b8b79d5a6818726f5c11f2e8e19f08249e1637133166506fd80
- Regression ed0da263345dce781f7c96010e194f26703c9c6c9b3b04ca0e213923408ca673

## Review findings and limits

Initial design review correctly rejected delivery-time polling: an early sample
delivered249ms later could compound with250ms idle and249ms acquisition to exceed
the proposed520ms bound. Fixed cadence anchors to sampling time. Added exact
policy binding and persisted stop reason with absorbing stop before new expiry.
Independent design code APPROVE and architecture CLEAR preceded TDD; actual
implementation reviews likewise APPROVE/CLEAR. Both closing lanes independently
read and hash-checked all12 retained artifacts and final source/test/runner pins;
closing code APPROVE and architecture CLEAR cover this pure checkpoint only.

Tests cover representative malformed inputs, not every dataclass combination;
policy/observation frozen behavior and complete stop_reason combinations are
correct on review but not directly exhaustively tested. Import purity is checked
by source review (only re/dataclasses), not an explicit fresh import trap here.
Immediate repoll is defensive/unreachable for a valid timely observation under
the current equal poll/acquisition constants; no invalid fixture manufactures it.

This code never reads a real clock or observer, never launches/stops children,
and never grants authority. It does NOT establish actual520ms enforcement,
trusted observation/UTC uncertainty, worker handoff, lease admission/monitoring,
history/calendar accounting, current resource admission, GPU2 stability or
qualification/training PASS. Worker denial unchanged. Next integration needs
reviewed concrete trusted producer and bounded acquisition/owned termination;
unknown factual history still denies actual launch. Full unified goal active.
