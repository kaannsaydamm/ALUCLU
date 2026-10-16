# Bounded native CPU fixture backend: revised declaration before implementation

Declared 2026-10-02 before native code/tests/build/execution. Supersedes the
standalone draft eaf55dd06e82a4e51108b3f42051ba034d28c59b96e5ddda64f17cc8e6233a8f,
preserved byte-for-byte in 2026-10-02-alc-r0-banded-native-standalone-draft-superseded.md.
Root and independent reviewer challenged thousands of per-fixture process
launches and unnecessary wire protocol. Revision selects one locally authored
trusted DLL with fixed C ABI and ctypes. No new experimental outcome prompted
this revision; no native implementation existed. This is structural cost
reduction, not a measured speedup.

Reference source dff2a30af16daa97dd0acd1ab39fe89403b35b6a4b181c95f7bf5db21f707f8d
and fixture declaration3cfe062e9cdcfdd0a4b46e8c106e6462d110f4feebdc3a2b9375a01b03dec611
remain fixed. Root reports broad reference regression complete, checkpoint81,
commit85862ebc9ba409fb3a78187b9f87e006bafcd33a.

Scope: synthetic fixtures only. No corpus/model/tokenizer/training/held-out,
GPU/accelerator/product kernel, adaptive K, ceiling increase, installation or
paid compute. Independent design review precedes implementation; final native
code/build review precedes acceptance. Root verified compiler19.44.35228,
linker14.44.35228 and SDK10.0.26100.0. Build uses explicit local cl.exe:
C:/Program Files (x86)/Microsoft Visual Studio/2022/BuildTools/VC/Tools/MSVC/14.44.35207/bin/Hostx64/x64/cl.exe
with /O2 /std:c++17 /EHsc /MT /LD; record actual paths/versions/flags.

## Smallest implementation and artifact identity

One C++ translation unit, fixed exported C ABI, one fixture-only Python adapter.
No automatic package import/build/load, arbitrary binary path API, foreign
artifact, CPython extension packaging or IPC protocol. Normal oracle parity
reuses loaded DLL; malformed-pointer/crash probes are child-isolated. Standalone
process framing/startup is unnecessary for the trusted locally built kernel;
a persistent executable would add another state protocol. DLL is not a sandbox.

Canonical build receipt binds clean commit/tree, source/adapter/reference/design
hashes, compiler/linker paths/hashes/versions/flags, SDK/architecture/dependencies,
actual DLL bytes/size/hash and build stdout/stderr/exit. Binary reproducibility
is not presumed. Artifacts/evidence stay outside tracked checkout.

Adapter opens receipt's canonical absolute DLL with deny-write/delete Windows
handle, hashes same file through handle and holds it throughout DLL lifetime.
Reject reparse relocation/mismatched identity; load that path with restricted
DLL-load-directory plus System32 flags; verify loaded module path/file identity
and recheck hash before evidence acceptance. If identity cannot be established,
fail before execution. Compiled identifier binds ABI/source, not self-referential
complete DLL hash. Dependencies are separately inventoried. No PATH/CWD lookup.
This is local fixture provenance, not protection from an administrator.

Official facts only:
- https://docs.python.org/3/library/ctypes.html
- https://learn.microsoft.com/en-us/windows/win32/api/libloaderapi/nf-libloaderapi-loadlibraryexw
- https://learn.microsoft.com/en-us/windows/win32/dlls/dynamic-link-library-search-order

## Concrete version1 ABI

Export cdecl aluclu_banded_abi_v1 returning uint32 ABI version1, and
aluclu_banded_audit_v1 returning uint32 transport status. Audit parameters in
order: pointers const uint32* first, uint32 n, const uint32* second, uint32 m,
const uint32* effective_budgets, uint32 B, uint32 K, const uint32* policy8,
uint8* workspace, uint64 workspace_capacity, uint32* output64,
uint32 output_words. ctypes argtypes/restype explicit. No native structs/padding,
C++ exceptions, strings or allocator-owned pointers cross ABI.

policy8 slots: endpoint_limit, cell_limit, scratch_limit, threshold_limit,
reference_uint32_header, reference_byte_header, rank_count, reserved_zero.
Output64 is fixed uint32 words, initialized only after pointer/capacity/ABI
validation. slots0..19: ABI1, method_status, reason, n,m,B,K,presence_bits,
signed lower encoded two's complement, signed upper similarly, C_low,C_high,
visited_low,visited_high,W,scratch_low,scratch_high,payload_low,payload_high,D.
Slots20..54: five consecutive seven-state budget slots in reference order.
Slots55,56: training_authority=0, held_out=0; slots57..63 reserved zero.
Presence bits0..5 designate lower,upper,C,W,scratch,D respectively. Absent slots
zero and adapter reconstructs None. Payload/visited always present. Exact result
uses B states; unused slots zero. Original Python budgets are restored by adapter.
Export cdecl uint32 aluclu_banded_build_id_v1(uint8* output, uint32 capacity):
status0 success,1 invalid pointer/capacity; capacity>=32 required. It writes
exactly32 bytes only on success: SHA-256 of native translation-unit source bytes,
supplied as build-time constant via generated external include. Source does not
contain that constant, avoiding self-reference. Receipt binds source/include
hashes and expected32 bytes. No returned pointer; ctypes
argtypes=(POINTER(c_uint8),c_uint32),restype=c_uint32.

Transport status1/2 rejection leaves output/workspace byte-for-byte unchanged;
status3 leaves output unchanged but may have mutated workspace before discovering
the invariant failure. Publish output only on transport success.
Transport status0 success,1 invalid ABI/input,2 insufficient workspace,
3 internal invariant failure. Method_status0 exact,1 unresolved; reason0 none,
1 endpoint,2 threshold,3 cells,4 scratch. Unknown status/enums/reserved values
fail closed. No infrastructure failure is a mathematical unresolved result.
No automatic fallback/retry.

Validate n,m/counts/limits before array scans, pointers and capacities before
reads/writes; ranks<rank_count<=65536 (rank_count0 only when n=m=0);
B1..5; positive nondecreasing effective
budgets<=max(n,m,1); policy ceilings and headers1..4096. Checked uint64/size_t
offset/product arithmetic. Empty input pointers may be null only for count0.
Output pointer nonnull/capacity>=64 words. Workspace null allowed only required
capacity0. Native cannot validate arbitrary address accessibility: trusted adapter
owns all buffers; unsafe pointer probes exclusively child-isolated and crashes
are failures, not PASS.

Caller retains all buffers across ctypes calls, uses private invocation buffers
and no concurrent mutation. Kernel is reentrant with no mutable global state,
no exceptions escaping and no vectors/dynamic per-cell or kernel heap allocation.

## Equality, budgets and mathematics

Adapter validates exact nonnegative Python integer tuples (never bool) before
deterministic first-occurrence bijection across first then second to ranks0..r-1.
r<=n+m<=65536. Test equality iff ranks equal including integers above uint64;
never byte-narrow/truncate or use hash-only identity. Rank map/input arrays are
adapter overhead outside kernel scratch.

Validate original positive strictly increasing Python budgets. Send
min(budget,max(n,m,1)); saturated duplicate native budgets are legal and preserve
distinct original output slots. This preserves both endpoint masks and supports
giant integers without native narrowing.

Port fixed parity-safe band, original-position masks, all tied optimal
predecessors including equal-ID indels, independent extrema/direct total and
joint signature union. No trimming, greedy snake, substitution, marginal-total/
joint inference, adaptive threshold, pruning or fallback. Exact iff terminal
D<=K; unresolved no distance/states. Completed DP visited=C. Null geometry and
reason precedence match reference. Prior declaration's proof remains required.

Endpoint32768/B5/K512/C4194304/scratch64MiB ceilings unchanged; only tighten.
INF=n+m+1 and exposure fit uint32; offset/products/cell totals checked uint64.
Range-gated relative row indexes prevent stale/out-of-band predecessors.

## Workspace and reference metadata

Adapter preflights geometry/reference estimate before allocation; native
independently recomputes it. Header values from empty-array getsizeof bound to
receipt, do not control independent native workspace. Mathematical result retains
Python reference estimate/payload fields; not a native RSS estimate.

Artifact receipt verification and data-only Python validation/preflight precede
every C audit call. Endpoint rejection must happen before rank-map/input-buffer
allocation. Null workspace is accepted for a preflight-only resource/threshold
rejection (required capacity0); an admitted computation never treats null as a
workspace query and instead returns insufficient-workspace. No callback or native
owned-buffer lifetime is introduced. Native recomputation remains mandatory.

Required workspace bytes equal exactly packed payload
2*(1+7B)*4*W+B*(n+m); pointer must be4-byte aligned, otherwise transport invalid
before writes. Caller allocates uint32 backing storage of ceil(payload/4) words,
passes logical capacity=payload and retains it. Row region precedes byte masks
so every uint32 offset is aligned; no padding inside payload. Bookkeeping is
stack-only, fixed <=65536 bytes, separately bounded, never workspace heap.
Both reference scratch admission and independent native workspace fit64MiB.
No matrix/path history/input duplication. Required native bytes and allocated
capacity recorded separately; too-small workspace rejects before writes.
Adapter allocation failure is infrastructure failure. Preflight rejection
needs no workspace allocation. Tuples/rank map/input/output/loader/CRT/RSS are
excluded and documented separately; canary checks verify actual boundaries.

## RED, oracle, resources and declared timing

Freeze independent-reviewed design before absent-backend RED tests, native
implementation/build and final code/build review. Full mathematical metadata/
states parity with reference and independent recursive oracle: binary lengths0..4,
all five budgets/threshold/parities; ternary/swap/nested/crossed/repeated/empty,
giant IDs/budgets and saturation, K0/512, endpoint fit/overflow and exact-fit/
one-over cells/scratch. Preserve all nine semantic mutation checks and add ABI
offset/capacity/overflow/null/output-corruption mutations.

Test absent/changed artifact, wrong ABI/build identifier, invalid counts/ranks/
limits, null/capacity mismatch, too-small workspace/output, impossible metadata,
isolated crashes and state leakage. Canary no-write-on-reject and guard-region
checks; preflight visited0, threshold-complete visited=C, exact payload and
empty/giant/max-width allocation corners. Unsafe pointers never run in main
interpreter.

Only after correctness/resources pass, benchmark serial fixed fixtures:
identity range(10000),K0; unique token10000 inserted at5000,K1; repeated7
length10000/10001,K1; identity range(600),K512. Budgets1,2,3,4,5 for all.
Warmup2 and measured5 repetitions per method/case. Measure Python call,
native kernel call, mapping, buffer marshalling, load and native end-to-end
separately with monotonic high-resolution clock. End-to-end excludes one-time
load but reports it separately, includes all per-call mapping/buffer/output cost.
Report mean/median/min/max, CPU/OS/compilerflags and order. Actually measured
native end-to-end median versus Python decides optimization benefit for these
fixtures; no invented speedup, corpus coverage or cross-platform claim.
No benchmarking before parity; broad regression final-source evidence required.

All receipts/results remain non-authorizing. No corpus proposal, learning PASS,
family-B freeze satisfaction, training authority or old-policy change follows.
