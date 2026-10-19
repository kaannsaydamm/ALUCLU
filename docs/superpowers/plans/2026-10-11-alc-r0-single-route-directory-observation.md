# Preregistered single-route Windows directory observation

Parent eaa124c92578b72c4c0d4130485a912374a13cc8. Development-only prerequisite
to runtime continuity repair; no scientific execution, accepting worker or
installed-binding PASS. Previous diagnostic checkpoint is progress, not a wait:
35 terminal artifacts, independently reviewed and pushed. No process is live.

## Evidence and alternatives

Actual_v4 retained a directory size4096->0 refusal. Both small probes saw4096
through every API and did not reproduce it. Causal origin remains unknown.
[CPython3.12.13](https://github.com/python/cpython/blob/v3.12.13/Modules/posixmodule.c#L1977-L2018)
selects by-name metadata or a slow handle fallback; its legacy ctime is creation
time. [Conversions](https://github.com/python/cpython/blob/v3.12.13/Python/fileutils.c#L1071-L1132)
and the [exact ABI](https://github.com/python/cpython/blob/v3.12.13/Include/internal/pycore_fileutils_windows.h#L12-L43)
support explicit native observation. This is not evidence that a branch switch
caused actual_v4. No prior failed attempt is reinterpreted as success.

Alternatives: (A) drop/normalize directory size; cheapest, but weakens the
existing comparison and does not establish cause, rejected here. (B) explicit
by-name query without fallback; one fixed104-byte result, retains size and all
previous identity/time/attribute semantics, selected as a candidate primitive.
(C) handle query with multiple information classes; explicit route but more
calls/cleanup/identity assembly and larger implementation cost. Keep available
if B is unavailable or fails, not automatic fallback. (D) repeat unchanged full
scan; additional opaque failures would not discriminate routes, not selected.
No alternative changes neural thresholds/grid/seeds/data or budget accounting.

## Bounded candidate contract

New standalone windows_directory_metadata.py; production inventory remains
unchanged in this checkpoint. Observe only explicit absolute resolved directory
paths, Windows64 little-endian. Reject UNC/device/relative/NUL/oversize labels,
reparse points/non-directories and missing native API. Load the fixed system API
set through LOAD_LIBRARY_SEARCH_SYSTEM32, never a caller-supplied DLL/function.
One GetFileInformationByName(path,FileStatBasicByNameInfo=3,104-byte buffer).
Failure denies; no retry or fallback. Original deadline checks before/after
validation/library load/native call/decoding; outer owned job still bounds
blocking OS calls. No handles, file-content reads, writes, heavy imports or GPU.

Retain exact immutable native fields: derived directory mode (readonly flag),
unsigned volume serial, full128-bit identity, size/EOF, last-write, creation,
link count, attributes, change time, allocation size, legacy64-bit file ID,
device type/characteristics and reparse tag. Native timestamps remain100ns ticks,
not lossy floats or purported Python nanoseconds. Exclude access time only,
which the old fingerprint never compared; Reserved is ABI padding, not identity.
Decoder accepts exact bytes length104, not an injected record/callable. Mode is
S_IFDIR|0555 when readonly, S_IFDIR|0777 otherwise; directory extension irrelevant.
Signed ABI serial and legacy ID reinterpret modulo2**64; identity stores the
complete16 native bytes as lowercase32-digit hex in native little-endian order.
The explicit WinDLL load's owned module reference is released with Windows
_ctypes.FreeLibrary in finally, including failure/deadline paths; no file handles.
Resolution and native observation are separate, non-atomic operations; native
directory/reparse checks are mandatory even after successful path validation.
Reject negative sizes/timestamps, zero links/128-bit identity, non-directory or
reparse attributes/tag. All retained fields compare exactly; size stays checked.
No path/open tuple mixing and no silent field truncation. Valid native observation
does not certify mapped images, provenance, immutable FS or launch permission.

## Validation and later integration boundary

TDD RED before implementation: pure fixed-record decoder negatives for every
retained value's conversion/validation and exact equality discrimination;
Windows owned synthetic-directory success/repeats, regular-file/junction denial,
original expired deadline, relative/UNC/device/NUL/oversize rejection. No mocks or
monkeypatch API/global state. Isolated fixture subprocesses keep bounded original
leases and receipts; test failures retained, no model/dataset/heldout access.
Focused and relevant runtime regression must terminate/drain and be inspected.
Review source before execution and artifacts before commit/push; record trajectory.

This primitive alone cannot resolve the fullscan refusal. Integration needs a
separate reviewed decision for using the SAME exact directory observation in
both walks, preserving membership/count/identity/reparse/file bytes checks,
structured diagnosis, bounded resources and original deadline. No production
comparison change or actual fullscan is authorized by this primitive checkpoint.
