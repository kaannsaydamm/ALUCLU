# Original D qualification resource identity

Status: proposed mechanical adapter; implementation readiness review pending.
Parent68fc3a79ddf0c489d5192faf88e97c322a587a76. No host or launch admission.

## Gap and boundary

ReservationReplay currently accepts only the frozen scientific run-ID grammar
pilot/dev/confirm/eval. A fixed D qualification is a prerequisite control, not
an extra scientific development or pilot run. Do not give it a fictitious dev
ID or change attempt_state.RunSpec / the frozen Cartesian matrix/schema/paths.
Original plan section12 separately names non-run R0.0/freeze controls; this
mechanical resource identity does not create a new scientific artifact namespace.
Actual control artifact types/paths still require declared freeze validation.

Extend ONLY reservation_state declaration validation with these three exact
resource-control identities (not a general regex wildcard or a scientific ID):

- alc-r0-qualification-v1-d-cpu-fresh1-s20260916
- alc-r0-qualification-v1-d-gpu-fresh1-s20260916
- alc-r0-qualification-v1-d-gpu-fresh2-s20260916

They bind original matched D, not the separate all-layer q/v computation or E
stress/pilot. CPU maps to cpu, GPU maps to gpu in the existing declaration.
Each useful_wall_ceiling_ns is exactly2700000000000 (45minutes); existing
cleanup_ceiling_ns is10000000000. charge_envelope_ns is exactly2710000000000;
GPU gpu_reservation_ns equals that full one-device envelope, CPU equals0.
All other IDs retain their exact existing validation and resource semantics.
No added kind/phase field, wire record mutation or rewritten historical genesis.
Any new declaration produces a separately pinned new genesis; existing histories
are never reinterpreted or extended by silently replacing their declarations.

This pure replay remains integrity/arithmetic, not authentication, attempt
eligibility, process control or permission. The future trusted coordinator must
bind each identity to the fixed D invocation and original official/matched-D
schedule, independently review retry/resume eligibility, and account all attempts.
Existing a001/a002/a003 and segment checks are not an automatic qualification
retry/resume permit. No new attempt allowance is created by accepting a resource ID.
The pending numeric-history/calendar and authority checks still deny real work.

## TDD and acceptance

Add tests against current source: the three exact declarations must replay
without an event/process; presently they fail invalid declaration identity.
Expected rejection matrix: seed/name/fresh-count/lane drift, q/v/E/pilot aliases,
device mismatch, changed useful/cleanup/charge/GPU envelope; malformed types.
Scientific RunSpec must reject these non-scientific resource-control IDs, while
original scientific IDs keep old behavior. Prove new-ID reserve/terminal/no-child/
reconcile/release arithmetic with synthetic facts only; complete replay hash
bindings and pure/durable regressions must retain legacy behavior.

Exact source/test invocation review precedes actual RED/GREEN/regression.
No model, Torch execution, dataset/held-out access, actual reservation namespace
initialization, source export or historical-accounting adoption follows. The new
tests may create harmless temporary reservation stores to exercise canonical
publication, but none launches a child. This narrow adapter removes a concrete
composition gap; fixed D worker/coordinator and actual-host evidence remain next.
