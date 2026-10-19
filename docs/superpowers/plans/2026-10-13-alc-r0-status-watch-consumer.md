# Stateful status-to-watch consumption

Baseline e1e20dad6c4121ca3dfc1aeb432ecc1ef4c4ad5c. Previous turn made a
documentation-only factual update: owner scope testimony narrows machine scope,
not measured historical charge. No actual learning has started.

Connect the existing bounded status reader to LiveAuthorityWatch without changing
scientific worker denial or introducing an accepting launcher. This consumer is
denial transport; its path, installation pin and UTC bound are inputs supplied by
a future independently reviewed installed producer. They do not authenticate
themselves. No model, Torch, CUDA, dataset or held-out work in this checkpoint.

## Exact operational contract

StatusWatchConsumer is single creating-thread-owned, retaining installation and
generation roots, highest observed sequence/root, and minimum observed expiry.
Each consume reparses exact OperatorStatus.data and compares every typed field;
constructing a dataclass is not valid observation. First observed installation
and generation must match the original pins. Subsequent sequence must not regress;
equal sequence permits ONLY byte-identical status. Increased sequence permits
expiry tightening, never extension, and cannot clear revocation. Any invalidity
latches consumer denial permanently, before raising. No reset/new generation API.

The same exact OwnedStopSignal is held by consumer and watch, checked at binding.
Binding requires exact LiveAuthorityWatch with matching generation and clock
roots; no subclass or alternate stop signal. consume(status, observed_monotonic_ns,
utc_upper_ns) returns an exact Observation only after successful checks; supplied
clock evidence is transport, not authenticated measurement. Numeric inputs must
be exact positive signed64 ints. Revoked status causes immediate owned stop;
it is not returned as an accepting observation. Consumer errors request owned
stop, including ordinary reader/submit failures and interruption in service.

serve_once(watch, path, utc_upper_ns, utc_anchor_monotonic_ns=...) waits at most20ms for one observation
request. If none, returns False without creating a new deadline. Otherwise read
the existing bounded reader using min(original useful deadline,
request.started_monotonic_ns+250ms). Capture monotonic time AFTER read and supply
the consumer Observation to the exact outstanding request. Recheck deadline
before/after consumption and submission; no retries, source discovery, new
thread or time renewal. A blocked OS read cannot be interrupted by Python; the
independent existing watch must stop the owned child at its original observation
timeout while the reader is blocked. Shutdown of a blocked producer remains a
future owned-producer requirement, not solved here. No wallclock sampling via
time.time_ns pretending a justified UTC upper bound.

Creating-thread state must not be mutated by concurrent callers. Wrong-thread
calls request stop and raise without resetting/rebinding state. A stopped watch
or stop signal never returns a usable observation. Read/consume/submit exception
paths remain sticky. Watch lifecycle closure remains with its original owner;
consumer does not create/start/close watches or release/reconcile reservations.

## Acceptance

RED before implementation; tests for first/equal/increased sequence, regression,
same-sequence changed bytes, changed installation/generation, expiry extension
and tightening, revocation then restoration, forged dataclass metadata, invalid
types/clock inputs, thread ownership, wrong watch/signal, and sticky failure.
Temporary real files + real LiveAuthorityWatch for valid observations then
revocation, missing/corrupt files, and generation change. Existing real watch
owned-child cancellation tests must regress; this checkpoint does not substitute
thread Event state for fresh actual-child proof. No 250ms latency benchmark or
hostile-writer/ABA detection guarantee.

Before completion independently review exact final source/test and native test
exit, JUnit counts, output logs, cleanup receipt and artifact hashes. Frozen
science, original limits and guard remain unchanged; installed origin/updater,
mandatory lease verifier, history/clock/resources and qualifications remain open.

Independent design code APPROVE / architecture CLEAR both required explicit UTC
anchoring. Service advances supplied UTC upper bound by post-read monotonic time
minus the supplied anchor, checked signed64. This assumes independently justified
clock evidence whose UTC upper envelope grows no faster than elapsed monotonic
nanoseconds in the pinned domain; this component DOES NOT establish that mapping.
Without such evidence an installed caller must remain denied. Future anchors,
overflow and monotonic regression deny. No ad hoc wallclock sampling in production.
Bind the exact watch instance once and retain its complete immutable policy;
switching to another watch with equal roots is denial, not a reset. Consume checks
known expiry, and when bound checks original useful deadline and full cleanup
envelope coverage. A successful submission reports queuing only, not synchronous
watch acceptance. Wrong-thread calls latch only the shared signal, leaving owner
sequence state untouched; the owner sees that signal as permanent denial.
