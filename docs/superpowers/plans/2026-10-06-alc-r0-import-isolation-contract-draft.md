# Import-isolation prerequisite — prospective implementation contract

Status: DRAFT_PENDING_REVIEW; no source/test modification or invocation admission.
Parent3b9fe764e5a87937aaaf58a08dad363346068073. This is a prerequisite of real-host
preflight, not a launcher, reservation, accounting amendment or learning gate.

## Decision and exact first-stage scope

Propose compatible lazy public exports in `src/aluclu/__init__.py` and
`src/aluclu/alc_r0/__init__.py`. Normal package imports must remain normal imports;
no importlib file-location loader, sys.modules substitution, environment switch,
duplicate resource-arithmetic implementation or caller-chosen module is permitted.

An independent stdlib bootstrap would avoid eager imports but require either
duplicating policy arithmetic or reorganizing shared modules/public paths. Lazy
export resolution preserves the existing actual object definitions and module
paths with a smaller change. Cost: missing optional dependencies become errors
when their exports are requested, rather than on unrelated package import. Record
this deliberate timing change; do not hide dependency errors or provide stubs.

First-stage acceptance is LIMITED to package initialization and normal import/use
of `checkpoint_resource_admission`. It does not promise that journal/canonical
modules are stdlib-only: canonical requires rfc8785, and cognition initialization
loads cryptography-backed ledger/key modules. Full launcher dependency isolation
remains a separate OPEN prerequisite, not waived by this stage.

## Export compatibility contract

Pin every current `__all__` name and `__version__` value from parent source before
edits. Build a static allowlisted export-to-original-module/symbol map, with no
dynamic filesystem discovery. Preserve exact class/function objects, defining
`__module__`, exception inheritance and object identity with direct imports.
Use package `__getattr__` only for missing allowlisted public names; cache ONLY
successful resolutions. Unknown names raise AttributeError; failed dependencies
propagate their original exception without caching a fake/partial value.

Keep `__all__` content/order and public from-import/star-import behavior unchanged.
Star import intentionally requests all exports and therefore may import heavy
dependencies. `dir(package)` advertises existing public exports without resolving
them. Import machinery must keep ordinary submodule semantics intact; document
incidental eagerly imported module attributes separately from the public symbol
contract. Do not accidentally shadow a real submodule with an export mapping.

Use only stdlib import machinery at package initialization; no probing Torch,
Transformers, CUDA availability, hardware, model paths or optional dependency
installation. Do not import model/cognition/host merely to populate annotations.
No resource_admission logic, scientific thresholds or workers change.

## RED / GREEN / regression evidence

Before source edits, add an isolated fresh-process test with a blocking import
finder installed BEFORE importing either package. Reject torch/transformers and
their submodules; record attempted imports. Normal import of both packages plus
the pure admission helper must succeed, leave these absent from sys.modules and
produce existing non-authorizing `history-unreconciled` denial on unknown inputs.
Current initializers must reproduce RED for eager dependency import, not a bad
PYTHONPATH or test-runner dependency. Use explicit source/runtime identity.

Do not instantiate models, load assets or initialize CUDA for compatibility tests.
With the existing pinned runtime available, resolve all public names and compare
identity to original direct-module symbols. Cover exact export roster, from-import,
star-import, repeated access, dir-without-resolution, unknown name, dependency
failure and failure-not-cached. Tests also cover direct submodule imports before
and after public export access and packages accessed from two cooperating threads.
Isolation must be assessed in subprocesses, not a pre-populated pytest process.

Run focused import tests, the unchanged resource-admission tests and relevant
existing public/API regression selections on final source bytes. Full-suite and
architecture guard scope must be evaluated explicitly: changing package entry
points affects more than this helper. Independent code/security and architecture
review precede approval; exact invocation/resource admission precedes test launches
under the existing workflow. This document itself admits no command.

## Residual gates

No pure-helper PASS authenticates caller observations, reserves resources or
permits a scientific child. Accounting policy/history/clock, trusted authority,
q/v ceilings, durable reservation/process-publication protocol, peak bounds and
real-host qualification remain OPEN. First-stage isolation may be implemented
only after independent review of this contract; full launcher remains BLOCK.
