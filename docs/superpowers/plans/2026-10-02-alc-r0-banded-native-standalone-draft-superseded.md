# Bounded native CPU fixture backend: design before implementation

Declared 2026-10-02 before native source, tests, compilation or execution.
Python reference source SHA-256 is
`dff2a30af16daa97dd0acd1ab39fe89403b35b6a4b181c95f7bf5db21f707f8d`;
its fixture declaration is
`3cfe062e9cdcfdd0a4b46e8c106e6462d110f4feebdc3a2b9375a01b03dec611`.
Root reports reference checkpoint cce8cbf; final broad regression is still
pending at declaration time. This design is not completion evidence.

Only synthetic fixtures are authorized by this proposed implementation slice.
No corpus adapter, tokenizer/model, native corpus run, training, held-out data,
GPU, custom accelerator, product kernel, adaptive distance threshold or ceiling
increase is proposed. No installation or paid compute is needed. Root verified
local MSVC cl.exe 19.44.35228 at
`C:/Program Files (x86)/Microsoft Visual Studio/2022/BuildTools/VC/Tools/MSVC/14.44.35207/bin/Hostx64/x64/cl.exe`.
That reported availability must be recorded again at any eventual build.
Independent design/code review is required before implementation.

## Selected smallest backend

Use one standalone x64 CPU executable, a small C++ translation unit using only
standard library and Windows file/process facilities, and a Python fixture
adapter. Build locally with explicitly recorded MSVC/linker flags and static CRT
where available; record actual executable dependencies. No package-wide import,
automatic build, PATH executable lookup, DLL loading, or model-library linkage.
Launch one bounded fixture request per process with an absolute executable path,
shell disabled and an explicit timeout. Crash, timeout, malformed response or
identity mismatch is an infrastructure failure, never a mathematical unresolved
result or an implicit Python fallback.

The executable is preferred first because it isolates native faults and makes
one bounded wire request observable. Process startup/marshalling may dominate
tiny cases; this is an explicit benchmark cost, not a reason to invent speedup.
A ctypes DLL avoids startup and offers a small C ABI but exposes the Python
process to pointer/ABI faults and requires verified atomic load identity and
dependency search. A CPython extension additionally introduces Python ABI/build
coupling without improving this first correctness proof. Both are deferred.

For a later DLL proposal, absolute-path loading and restricted dependency search
are necessary but are not alone hash-to-load atomicity. Python documents ctypes
winmode/full-path loading; Microsoft documents LoadLibraryEx search flags and
dependency search. Any DLL variant must separately prove same-file load identity
under a deny-write/delete handle, bind GetModuleFileName identity and dependencies,
declare argtypes/restype/ABI version and ownership, and test malformed pointers
in a child process. This document authorizes none of that implementation.

- Python official ctypes documentation:
  https://docs.python.org/3/library/ctypes.html
- Microsoft LoadLibraryExW:
  https://learn.microsoft.com/en-us/windows/win32/api/libloaderapi/nf-libloaderapi-loadlibraryexw
- Microsoft DLL search order:
  https://learn.microsoft.com/en-us/windows/win32/dlls/dynamic-link-library-search-order

## Identity and bounded wire contract

Publish a canonical build receipt containing protocol/kernel version, clean
source commit/tree, native and adapter source hashes, reference/declaration
hashes, exact compiler/linker absolute paths, versions and binary hashes, flags,
architecture, SDK/runtime identity, dependency inventory, executable size/hash
and stdout/stderr/exit evidence. Reproducible binary bytes are not presumed:
source equivalence never substitutes for the actual binary hash.

The adapter must open the executable with a Windows handle denying write/delete,
hash bytes through that handle, verify expected absolute canonical path/file
identity and hold the handle through process exit. Launch that same path while
the handle remains held; recheck identity/hash before accepting output. Reject
symlink/reparse relocation or mismatch. If these semantics cannot be established
on the local filesystem, fail the provenance gate rather than launch. A build
identifier returned by the executable binds its compiled algorithm/protocol,
not its own complete binary hash (which would be self-referential). System
dependency provenance is recorded separately; the receipt is not a sandbox or
claim of resistance to an administrator changing the host.

Use one fixed little-endian binary frame on stdin/stdout, with versioned magic,
exact lengths and no native struct padding. Request fields: protocol version,
n,m,B,K, all four per-call limits, reference uint32/byte array-header byte sizes,
B canonical effective budgets, and n+m token
ranks. Length fields/counts are uint32; byte offsets, products and cell sums use
checked uint64/size_t arithmetic. Frame length is deterministically derived
from validated counts before allocation. Reject truncated frames, excess/trailing
bytes, invalid magic/version, length mismatch, bool/noninteger adapter inputs,
invalid budgets/limits, out-of-range ranks and arithmetic overflow. Hard input
frame ceiling 1 MiB includes every field; do not read unbounded stdin into memory.
EOF completes the single frame; no multi-request loop or batch endpoint is added.

Response frame has fixed versioned schema: method status/reason codes, dimensions,
K, nullable geometry/scratch fields with explicit presence tags, scheduled and
visited cells, maximum width, exact allocated packed payload, distance presence,
original budget count and seven states per budget only when exact. Add a fixed
compiled build identifier. No token ranks, alignment paths or internal row state
are returned. Adapter rejects unknown enums, invalid null tags, wrong counts,
trailing bytes, impossible signatures (>15), distance>K in an exact response,
nonempty metrics in unresolved responses, authority fields other than false,
or mismatch of recomputed geometry/policy. Bound stdout and stderr capture
(response <=4 KiB, diagnostics <=4 KiB); do not let a malformed child grow
unbounded buffers. Record raw fixture receipts separately from scientific data.

## Equality, budgets and exact recurrence

Validate original tuples using the Python reference's exact-integer rules before
mapping. Make a deterministic first-occurrence bijection from arbitrary Python
integer token IDs across first then second to ranks 0..r-1. At most n+m<=65536
ranks exist. Prove and test equality iff ranks equal, including IDs above uint64;
no byte narrowing, hash collision equivalence or truncation is allowed. Mapping
and frame allocations belong to adapter overhead, not native DP scratch. Empty
endpoints remain mathematical fixtures.

Preserve original increasing Python budgets in returned BudgetExposure records.
For native masks transmit effective budget min(original_budget,max(n,m,1));
equal effective budgets are legal after saturation and must not merge output
slots. This saturation preserves both endpoint masks, including giant integers,
without converting arbitrary original integers to native widths. Validate original
strict ordering before saturation; native validates positive nondecreasing
effective budgets <=max(n,m,1). Native recurrence uses each budget slot separately.

Use precisely the reference's parity-safe threshold band and original-position
masks, all minimum-distance predecessor ties, six independent extrema and joint
signature union. No equal-prefix/suffix stripping, greedy snake, replacement
edge, marginal-total arithmetic, inferred joint bits or chosen traceback.
Reuse the proof in the prior fixture declaration; changing language does not
change the estimand. No dynamic widening, retry, distance-discovery backend or
automatic full-grid fallback. Preserve reason precedence, null conventions and
exact scheduled/visited counts. No pruning: completed DP visits exactly C.

## Independent native storage policy

Endpoint <=32768, B<=5, K<=512, C<=4194304, scratch<=64 MiB remain unchanged;
limits may only tighten. Counts/exposures/INF=n+m+1 fit uint32; large IDs never
enter these counters. Preflight checked arithmetic computes the clipped region
and width without storing a row-width vector. Range-gated relative row indexes
and explicit unreachable states prevent newly entered/out-of-band stale slots
from becoming predecessors. Origin/boundaries and all-ties signature transforms
match Python exactly.

To preserve exact result metadata, return the Python reference scratch estimate
and payload as reference-policy fields, recomputed independently by adapter and
native using explicitly supplied platform header constants. Adapter derives
these constants from empty-array getsizeof probes, binds them to the invocation
receipt, and requires response metadata parity; native rejects header values
outside 1..4096 and checked arithmetic overflow. The native kernel's independent
workspace bound must not rely on those supplied header values. This is
not native measured memory. Separately record native_workspace_bytes and
native_workspace_peak in a fixture execution receipt outside the mathematical
result. The native kernel allocates one checked contiguous block for
2*(1+7B)*4*W+B*(n+m) bytes, matching prescribed packed payload, plus <=65536
bytes declared bookkeeping allowance. Masks and row layout use no padding beyond
explicit checked offsets; state pointer tables are bounded. No full matrix,
path history, dynamic per-cell allocation or input duplication inside the kernel.

The reference 64 MiB estimate remains an admission condition; the native
workspace including allowance must also fit 64 MiB. Allocation failure is a
distinct infrastructure error, not a successful unresolved response. Caller-owned
tuples, rank map, request/response buffers, process loader/CRT and RSS are excluded
from kernel scratch and measured separately if reported. Document exact frame
and native input storage bounds so exclusion is explicit. Do not advertise the
Python reference estimate as a native allocator/process bound.

## RED, parsing, oracle, allocation and timing evidence

Freeze/review this design first. Write fixture adapter/native interface tests
against the absent executable to record RED before implementation. Build only
after independent design approval; final native source and build receipt receive
independent review before any timing acceptance. Keep temporary build/binaries
and receipts outside the tracked checkout; no executable downloaded or installed.

Compare complete mathematical results field-for-field against the fixed Python
reference and independent recursive all-path oracle: exhaustive tiny binary
lengths 0..4 and all five budgets across all thresholds/parities; ternary/swap/
nested cases; crossed joint fixture; repeated equal-ID ties; empty endpoints;
giant integer IDs and budgets; saturation producing duplicate effective budgets;
K0/512, hard endpoint fit/overflow, exact-fit/one-over C and scratch policies.
Retain both original input commitments and mapped equality proof in fixture
receipts. Large known-distance fixtures are synthetic, declared before execution
and bounded exactly as the Python design. Include all nine existing semantic
mutations and native-specific index/overflow/null-schema mutations.

Protocol fixtures independently construct malformed binary requests/responses:
every truncation boundary, trailing bytes, absurd counts, invalid ranks/versions/
tags, inconsistent metrics, missing executable, changed binary identity, wrong
compiled identifier, timeout/crash and oversized output. All fail closed; none
silently falls back to Python or becomes visibility evidence. Assert no kernel
workspace allocation on preflight rejection, exact C on terminal-threshold
failure, fixed payload, canary/guard checks around row/mask regions, and no
state leakage between separate requests/processes.

Only after parity and resource checks pass, run serial isolated synthetic timing
fixtures with declared sizes/budgets/K and repeats. Report Python and native
kernel time separately from rank-map, serialization, process startup and total
end-to-end time; report warmup, compiler flags, CPU/OS and measurement dispersion.
Do not subtract costs to claim an unmeasured product speedup. No speedup, corpus
coverage, native portability or learning claim exists before actual evidence.
Broader regression must complete on final source before completion reporting.

This design alone cannot authorize corpus DP, change old policy, select a common
budget, waive unresolved diagnostics, satisfy family-B freeze gates or grant
training authority. Every result/receipt remains non-authorizing.
