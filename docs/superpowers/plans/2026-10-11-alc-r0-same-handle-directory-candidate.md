# Same-handle directory observation: research candidate

Status: ABI research and design draft, not implemented or execution-ready.
Baseline: reviewed held-directory checkpoint
`76f848e87a412ee32924cd7a183afdaedd53034c` (remote equality verified).
This is a diagnostic precursor to installed-runtime continuity, not a change
to ALC-R0 model, scientific thresholds, accounting, or training authority.

## Why this candidate

Actual-v5 recorded size/allocation 0 -> 8192 for installed `Lib/asyncio`.
Closed-handle scratch and held-handle population variants did not reproduce
the no-write discrepancy. Neither negative result explains or repairs v5.
Another arbitrary scratch count or warm full scan has low information gain.
A handle-bound observation can instead compare independently acquired complete
facts about the same open object with the current by-name route. This remains
a hypothesis about observation semantics, not a claim that either API is wrong.

## Alternatives and decision

| Alternative | Information/correctness | Cost and limitation | Decision |
| --- | --- | --- | --- |
| Drop or zero size/allocation | Hides the observed contradiction | Cheap but weakens the invariant | Reject |
| Prewarm/repeat full scan | May remove a transient without explanation | Whole-tree cost, no cold proof | Reject as acceptance |
| Repeat synthetic counts | Same already-tested mechanism | Cheap, low representativeness | Do not repeat blindly |
| Same-handle complete observation | Preserves all 14 facts; separates routes | More calls, compound non-atomic observation, ABI work | Investigate |

No measured latency/CPU/memory advantage is claimed. No production alternative
is selected until native feasibility, negative tests, parity and original-budget
installed-tree evidence exist. No cross-platform claim follows.

## Complete field mapping proposal

| Existing comparison fields | Candidate source on one retained handle |
| --- | --- |
| legacy_file_id, creation_ticks, write_ticks, change_ticks, allocation_size, size, attributes, reparse_tag, link_count | NtQueryInformationFile FileStatInformation (68), FILE_STAT_INFORMATION |
| volume_serial, file_id128 | GetFileInformationByHandleEx FileIdInfo (18), FILE_ID_INFO |
| device_type, device_characteristics | NtQueryVolumeInformationFile FileFsDeviceInformation, FILE_FS_DEVICE_INFORMATION |
| mode | Existing exact directory/read-only attribute derivation |

Expected Windows64 layouts from these declarations: stat 72 bytes, ID 24,
device 8, IO_STATUS_BLOCK 16. These are proposed ABI assertions, not measured
native support. Never substitute stat's 64-bit FileId for the 128-bit identity.
Preserve unsigned serial/legacy-ID interpretation and exact native timestamp
ticks. No access-time comparison is newly removed; it was already excluded.

## Failure semantics learned from primary documentation

Nt return status is authoritative when not STATUS_PENDING; IO_STATUS_BLOCK
status is not a second unconditional success predicate. In particular, do not
turn an uninitialized/stale IOSB status into a false failure on a synchronous
successful return. Record both for diagnosis. Pending completion cannot be
treated as completed or decoded; a minimal candidate should reject it and keep
all native buffers alive through safe close/owned-process cleanup. Whether that
cleanup is sufficient must be settled before native invocation.

Require successful completed query and exact reported byte length for fixed
Nt records. Reject truncation, unsupported classes, malformed directory facts,
zero identity/links, reparses, negative sizes/timestamps and ABI mismatch. APIs
can return zeros for unsupported members: zero must not be assumed to prove
support, although legitimate zero sizes cannot simply be forbidden. Unsupported
field semantics and volume/device parity therefore need explicit evidence.

Multiple calls on one handle are not an atomic snapshot. A future candidate
must define bookend validation and path-rebinding checks, preserve the original
owned deadline and finally-close behavior, and document residual cooperating-
host races. Holding a handle alone does not authenticate the installed producer
or prevent concurrent modification. No fallback to a partial record is allowed.

## Required next work before invocation

1. Verify FileFsDeviceInformation numeric enum and user-mode ntdll ABI/export
   contract from primary headers; do not guess the number or load kernel code.
2. Define pending/error cleanup and buffer lifetime; no asynchronous buffer UAF.
3. Freeze a standalone, read-only, single-directory diagnostic protocol on the
   existing installed `Lib/asyncio` and owned scratch control. Set explicit query
   ordering, finite count, output caps, original deadline and resource receipt.
   This will not establish cold-state behavior on the already-observed directory.
4. TDD exact decoder/ABI/sequence/failure/close/deadline tests, then relevant
   regression and independent source/design review before native invocation.
5. Preserve raw records and fieldwise within-route and cross-route comparisons.
   Any cross-route difference is evidence to explain, not permission to normalize.
6. Only after diagnostic evidence, separately propose production integration,
   affected full regression, budgeted installed scan and performance measurement.

No invocation is scheduled by this draft. No model/tokenizer/data/GPU/training
operation is introduced. Fixed-D and later scientific prerequisites remain open.

## Primary sources inspected 2026-10-11

- [FILE_STAT_INFORMATION](https://learn.microsoft.com/en-us/windows-hardware/drivers/ddi/ntifs/ns-ntifs-_file_stat_information)
- [NtQueryInformationFile](https://learn.microsoft.com/en-us/windows-hardware/drivers/ddi/ntifs/nf-ntifs-ntqueryinformationfile)
- [FILE_ID_INFO](https://learn.microsoft.com/en-us/windows/win32/api/winbase/ns-winbase-file_id_info)
- [FILE_INFO_BY_HANDLE_CLASS](https://learn.microsoft.com/en-us/windows/win32/api/minwinbase/ne-minwinbase-file_info_by_handle_class)
- [NtQueryVolumeInformationFile](https://learn.microsoft.com/en-us/windows-hardware/drivers/ddi/ntifs/nf-ntifs-ntqueryvolumeinformationfile)
- [FILE_FS_DEVICE_INFORMATION](https://learn.microsoft.com/en-us/windows-hardware/drivers/ddi/wdm/ns-wdm-_file_fs_device_information)
- [IO_STATUS_BLOCK](https://learn.microsoft.com/en-us/windows-hardware/drivers/ddi/wdm/ns-wdm-_io_status_block)

Driver documentation's platform minimum is not proof that every class is
supported by the local user-mode runtime. Local support remains to be tested.
