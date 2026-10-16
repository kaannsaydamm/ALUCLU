# Same-handle diagnostic protocol v1

Preregistered before implementation and native results, 2026-10-11.
Baseline 0e5a920313df06fbde390a86882ecc5125fd6ed5. Development diagnostic only;
not installed binding, activation authority or ALC-R0 scientific acceptance.

## Scope and bounds

Standalone tests/alc_r0_same_handle_directory.py. Parent uses the existing
run_diagnostic owned Windows job contract: original 60-second useful deadline,
10-second cleanup, 65536-byte stdout, 4096-byte stderr, synthetic reservations
4 MiB research / 8 MiB physical, no release/admission claim. Preserve exclusive
result files and retained temporary directories. No native invocation before
focused GREEN, relevant regression and two independent source/design verdicts.

Closed parent modes --red/--green/--regression/--native; private --owned-native.
Test runs are CPU-only; no model, tokenizer, dataset, training, GPU, external
compute, installed-tree writes, full scan, cache flush or threshold change.
Native child uses -I -B and stdlib only. Only fixed installed target is resolved
sys.base_prefix/Lib/asyncio; one owned scratch control has 16 exclusive files
of 512 bytes. These targets are already-warm/created observations, not cold proof.

For each target: by-name before open; open read-attributes, share7, existing3,
backup/open-reparse flags0x02200000 (no overlapped); same retained handle sample;
by-name while open; enumerate at most256 names /32768 UTF-8 bytes; second same-
handle sample; by-name while open; third same-handle sample; finally close;
by-name after close. Each sample includes stat72, ID24, device8 raw bytes and
all14 existing decoded fields. Within each sample: stat then ID then device
then stat bookend; reject if compared stat facts differ. Preserve both raw stat
records. Compare three handle samples and four by-name samples fieldwise, plus
cross-route differences; differences are reported, not normalized or hidden.
Lstat/resolve validation precedes probing; no claim of an observer-free baseline.
No file contents are read in installed target. Scratch writes total8192 bytes.

## Native failures and cleanup

Load only system32 named API, kernel32 and ntdll with winmode0x800. Exact64-bit
little-endian ABI assertions. Nt queries use classes68 and4; Win32 ID uses18.
Return NTSTATUS must be exactly STATUS_SUCCESS, and Information exactly expected
record size. IOSB status retained for diagnosis, not an unconditional second
success predicate. Normal errors close handles and release DLL references.
If STATUS_PENDING occurs, immediate os._exit(71) in the isolated native child,
before stack unwinding: local buffer/IOSB/handle/DLL references stay alive until
process teardown. Fixed stderr marker identifies pending; no result decoding,
no retry, fallback, lease renewal or resumed training. Parent records nonzero
terminal status and owns draining. This is diagnostic-only, not reusable in-
process library behavior. Tests inject a raising fatal function only with fake
queries; real native fatal path must be child-process tested before invocation.

Reject wrong byte types/lengths, negative size/times, zero identity/links,
non-directory/reparse facts and invalid handles. Zero allocation/EOF is valid
and preserved; unsupported-zero fields cannot be inferred supported from zeros.
Multiple queries/path validation are non-atomic on a cooperating host. Same-
handle bookends do not prove path binding or protect against an ABA modification.
Production integration needs a separate path-identity/race design and scan proof.

## Test and evidence requirements

RED missing implementation must fail intended new tests, not collection.
GREEN verifies full14 mapping, signed/unsigned IDs, exact raw retention,
negative/malformed metadata, NT success/error/pending and exact-length rules,
bookend mutation rejection, query ordering and cleanup using explicit fakes.
Regression includes old22 scratch/held, native42 and inventory73 cases.
Native fatal path must be tested in an isolated subprocess, not pytest itself.
Record JUnit counts, original process terminal receipt, stdout/stderr and SHA256.
Do not reuse earlier137 evidence as coverage of new source. Native evidence is
only local finite feasibility/parity, never a scientific PASS or v5 cause proof.

## Primary ABI provenance

Use candidate document's Microsoft Learn sources for stat/ID/device/IOSB.
Additional sources inspected before implementation:
- [Microsoft terminal header, FS enum starts at1; device is4](https://github.com/microsoft/terminal/blob/main/src/host/conddkrefs.h)
- [FS_INFORMATION_CLASS](https://learn.microsoft.com/en-us/windows-hardware/drivers/ddi/wdm/ne-wdm-_fsinfoclass)
- [CreateFileW synchronous/no-overlapped and directory flags](https://learn.microsoft.com/en-us/windows/win32/api/fileapi/nf-fileapi-createfilew)

Microsoft terminal's declaration is primary implementation evidence, not a
local export availability guarantee. Missing native exports fail closed.
