# Checkpoint151: explicit bounded wrapper inventory opt-in

## Scope and caller contract

`PinnedLlamaCapsuleWrapper.enable_checkpoint_inventory()` is inherited by the
LoRA wrapper. Constructors remain default-off. It warms the current complete
supported wrapper inventory outside the controller lock, then publishes the
owned observational partial through the original atomic one-time installer.
Only the exact owned partial can be reused; arbitrary caller callbacks are not
certified or replaced. Active leases reject installation, including repeats.
The getter follows current mounts rather than caching a prepared fingerprint.

Preparation requires exclusively owned, quiescent wrapper mutation. Racing
first installations may reject; the preparation/publication interval is not
transactional against unrelated mutation. Direct private writes and compromised
runtime are outside this cooperating contract.

## Exact reviewed source bytes

| Artifact | SHA-256 |
| --- | --- |
| checkpoint_inventory.py | 48c895d2567c6a10b9183eb40320b4edf4c25742fe05b6ffbedc31a53bbd151b |
| host_wrapper.py | 242cdcbcc66b561bf1baef67754c098eea4a6e1cf56456118a33f8a6c38e4b4f |
| checkpoint_wrapper.py | 3e202a3a78bc9a0357552dd4ed2378753c33f9c7ec942c75b0ad9759126d40a4 |
| test_alc_r0_wrapper_inventory_enable.py | 4aee5e8fc62574c00236bbc18c3be9acb859f2b98ec5d70debaa3c624e50d31b |

Independent GPT-6.1 Sol code/spec/security lane: APPROVE, no severity findings.
Independent GPT-6.1 Sol architecture lane: CLEAR. Both first reviewed the
12-case test source, then rereviewed the final 18-case source and verified the
unchanged production hashes. Neither lane executed tests or model code. The
authoring/root lane executed and independently parsed the receipts below.

## Executed evidence

Pinned Windows research CPython3.12.13 environment; `PYTHONPATH=src`,
`PYTHONDONTWRITEBYTECODE=1`, `python -B -m pytest -q -p no:cacheprovider --tb=short`.

| Receipt under results/ | Actual pytest exit | Tests/failures/errors/skips | Seconds | XML SHA-256 |
| --- | --- | --- | --- | --- |
| alc_r0_wrapper_inventory_enable_red_20261004.xml | 1 | 12/12/0/0 | 33.597 | f9292ab4e70ac819c939630f5f1f0e793ae901977750fdb4bef2b223e0227641 |
| alc_r0_wrapper_inventory_enable_green_20261004.xml | 0 | 64/0/0/0 | 30.285 | 54a82c2844865402ce701662fc6aa72ef04d0d7afddde9cdd392b2288e293a55 |
| alc_r0_wrapper_inventory_enable_regression_v2_20261004.xml | 0 | 1078/0/0/0 | 62.507 | cc01f57c7ffd351326658e2772641020487df9f7f567604f393cff0c2e844f0f |

RED reproduced the missing API. Focused GREEN ran the new12 cases, existing
wrapper method inventory and atomic installer controls. The final regression
adds all18 cases to the same35-target component regression used at checkpoint150
(1060 prior cases), with the same two GPU/real-tokenizer deselections. It is NOT
a whole-repository, actual-host, GPU or portability suite. Root consumed terminal
session79844, personally parsed1078 cases and18 new cases, and verified all four
source/test hashes unchanged. Ruff and `git diff --check` passed.

Additional boundary tests fill gradients then mutate method defaults or replace
the callback after capture; nonempty begin_forward metadata reaches the intended
guard, denial releases the original lease and clears gradients. Subclasses fail
before publication. A misplaced active-lease assertion introduced while adding
tests was corrected before that expanded source was executed.

## Open gates

This is inventory plumbing, not source authentication or complete effective
execution qualification. Full transitive globals/import resolution,
class/controller/native semantics and mask resolver coverage remain separate.
No actual host, corpus, optimizer training run or GPU launch occurred. Real-host
D parity, E resource fit, scientific R0 freeze/authorization, neural capability,
durable generations, portability and final `.alc` acceptance remain OPEN.
Full unified objective remains ACTIVE.
