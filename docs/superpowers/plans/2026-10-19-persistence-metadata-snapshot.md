# Single-observation path classification: preregistered implementation change

Baseline diagnostic checkpoint a298171. This is shared cognition persistence,
not a scientific architecture/search-grid or admission change.

Profile2 observed2783 native stat calls and889 helper calls, including867
Path.is_symlink calls. Installed CPython3.12 implements is_symlink via another
lstat. These nested profiler times are not additive or predicted savings.

Chosen narrow change: classify symbolic-link mode and Windows reparse attributes
from ONE lstat result in _is_link_or_reparse. Preserve FileNotFoundError->False,
all other errors, all call-site/parent/pre-replacement validation and fsync.
No path cache, ancestor memoization, deadline extension or boundary removal.

Two independently reviewed alternatives: keep all current queries (no improvement),
or anchored native-handle redesign (substantial scope and new platform semantics).
One internally consistent snapshot is the narrow Pareto candidate within existing
stable/cooperating-path assumptions in durable-reservation contract17-23 and
deadline-lock54-56. It is NOT exact behavior equivalence under concurrent mutation:
regular->symlink between old samples may be caught by old code but not the first
snapshot; symlink->regular may be missed by old POSIX code but caught by snapshot.
Neither proves an atomic binding or hostile ABA protection. No TOCTOU fix claim.

TDD: explicit non-global observation seam covers mode/attributes, missing/error
propagation and deliberate first-snapshot semantics; actual file/directory/missing,
native symlinks and Windows junction exercise real paths. No monkeypatch added.
Run focused RED before product change; GREEN plus existing persistence regression
afterward, then reservation/caller regressions and independent review. Measure
actual operation-count reduction; wall-time benefit and coordinator deadlines
remain unproven until matched measurements, never inferred from helper tests.

Primary references: https://docs.python.org/3.12/library/pathlib.html#pathlib.Path.is_symlink
and https://docs.python.org/3.12/library/stat.html#stat.S_ISLNK .

## Observed validation, not coordinator closure

RED18cases/10fail/0error/0skip. Final LF-source focused GREENv2:30/0/0/0,
JUnit0.353s. Caller regression215cases/0fail/0error/1skip JUnit25.420s:
POSIX FIFO unavailable onWindows. Ledger/keys100/0/0/0 JUnit117.519s.
All native exit0/active0/no timeout for final successful runs, original120s bound.
The earlier GREEN before line-ending normalization is separate historical evidence.

Actual stable regular-file probe:32 helper invocations, reconstructed exact old
helper64 native nt.stat calls, current helper32. This is measured operation-count
reduction for this workload, not walltime gain, application speedup, coordinator
deadline success or hostile namespace protection. Broad316 regression and
responsive acquisition/cleanup remain OPEN.
