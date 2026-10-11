# Directory access-right intervention protocol v1

Preregistered 2026-10-11 before implementation/results. Baseline92ab202.
Research diagnostic only; no production, model/data/GPU/training invocation.

## Question and prior counterevidence

Previous finite diagnostic reproduced installed asyncio directory size/allocation
0->8192 on both by-name and retained-handle routes, with identity and other12
comparison fields unchanged. Enumeration interval association is not causality.
Scratch16 control stayed4096. Same-handle-only substitution is not a repair.

Hypothesis: opening a handle with FILE_LIST_DIRECTORY access, even without
enumerating through it, is sufficient for the transition in this tested scope.
Alternative: a second read-attributes-only open suffices; enumeration remains
necessary in this sequence; or no transition recurs. None is assumed in advance.

## Frozen finite intervention

Extend diagnostic-only NativeAPI.open with closed exact-int access choices
0x80 (existing default FILE_READ_ATTRIBUTES) and0x81 (plus FILE_LIST_DIRECTORY).
All other flags/share/disposition/cleanup/ABI remain unchanged. Preserve v1
inspection/modes/evidence. New exclusive modes red-access, green-access,
regression-access, native-access; private owned-native-access.

Fixed installed target resolved sys.base_prefix/Lib/asyncio, then new scratch
control16files*512bytes. No installed payload reads/writes, tree scan, reboot,
cache flush, lease, paid compute or unrelated environment mutation. No new
native APIs, no substitute device fields. Owned parent60s useful/10s cleanup,
65536stdout/4096stderr, existing synthetic4MiB/8MiB bounds, -I -B child.

Validate bounded resolved absolute local directory/no reparse before querying.
Retain one0x80 baseline handle through all interventions. Fixed stages:

1. By-name before baseline open.
2. Baseline open0x80; full sample + by-name (baseline).
3. Open second0x80, no enumeration; full baseline and second samples + by-name
   (attributes-open).
4. Close second; full baseline sample + by-name (attributes-closed).
5. Open second0x81, no enumeration; full baseline and second samples + by-name
   (list-access-open).
6. Close second; full baseline sample + by-name (list-access-closed).
7. Existing bounded enumeration max256names/32768UTF8bytes; full baseline sample
   + by-name (enumerated).
8. Close baseline; by-name after close.

Keep full raw bytes, all14 decoded fields, NT return/status/length and stat
bookends for every sample; retain enumeration digest/count. Record adjacent
baseline and named field differences, not only size/alloc. Report observations
even if unstable; native exit0 means completed, never continuity PASS.

## Interpretation fixed before results

Transition first at attributes-open/closed undermines list-access specificity.
Transition first at list-access-open/closed supports sufficiency of that access
intervention in this sequence, not unique causality or an NTFS internal proof.
Transition only at enumerated undermines open-only sufficiency in this run.
No recurrence is inconclusive; already-warm targets cannot falsify a cold-state
hypothesis. Opening/querying is itself an observer. Fixed sequential order is
confounded by elapsed time/query count; outside writers and ABA are not excluded.
Each open-stage also samples both handles. An observed transition cannot
separate opening alone from the queries on the second handle. Closing-stage
observations associate with that interval, not exclusively the close operation.
No outcome authorizes prewarming full trees or dropping/zeroing any metadata.

## Alternatives and tradeoffs

| Alternative | Value | Cost/limit | Decision |
| --- | --- | --- | --- |
| Existing same-handle replacement | No new API | Reproduced same instability; device mismatch | Reject as sole repair |
| Access-right intervention | Separates open access from enumeration, exact existing fields | Finite CPU-only; order/outside-actor confounding | Selected next diagnostic |
| New StandardInformation/class5 query | Independent size source | New ABI and observer could initialize state | Defer until access result |
| Class77 full-stat query | Potential same-record device provenance | Support/documentation ambiguity; not a size repair | Defer |
| Mask size/allocation/device differences | Easy to pass | Weakens existing continuity contract | Reject |
| Broad scan warmup or repeated retry until stable | May appear stable | Erases first observation, no cause proof | Reject |

## Primary-source research boundaries

- [CreateFileW](https://learn.microsoft.com/en-us/windows/win32/api/fileapi/nf-fileapi-createfilew)
  defines desired access/backup directory handles; no claimed initialization
  guarantee. FILE_LIST_DIRECTORY is a separate access intervention, not proof
  that enumeration occurred.
- [FILE_FS_DEVICE_INFORMATION](https://learn.microsoft.com/en-us/windows-hardware/drivers/ddi/wdm/ns-wdm-_file_fs_device_information)
  describes device-object information associated with a file object.
- [FileFsDeviceInformation](https://learn.microsoft.com/en-us/openspecs/windows_protocols/ms-fscc/616b66d5-b335-4e1c-8f87-b4a55e8d3e4a)
  supplies bit meanings:0x20 mounted,0x20000 appcontainer traversal,0x100 secure
  open. This decodes the observed0x20020 versus0x100; it does not establish which
  local stack object each query selected or justify replacement/masking.
- [FILE_STAT_BASIC_INFORMATION](https://learn.microsoft.com/en-us/windows-hardware/drivers/ddi/ntifs/ns-ntifs-file_stat_basic_information)
  defines device fields but has internally suspicious directory-control remarks
  and a128-byte description for FILE_ID_128; do not derive a new ABI solely from
  those remarks. Existing tested104-byte mapping is unchanged.
- [FILE_STANDARD_INFORMATION](https://learn.microsoft.com/en-us/windows-hardware/drivers/ddi/wdm/ns-wdm-_file_standard_information)
  defines allocation/EOF/directory facts, not a local lazy-initialization proof.
- [CPython3.12.13 fileutils.c](https://github.com/python/cpython/blob/v3.12.13/Python/fileutils.c)
  maps basic-info EOF to st_size; this is implementation evidence, not a native
  stability guarantee. No authoritative source found proving the local cause.

## Required gates

Intended RED for new access whitelist/sequence/mode behavior; GREEN and full
existing diagnostic+metadata+inventory regression on final bytes. Include exact
stage ordering, second/baseline handles, no early enumeration, failure closure,
full-field difference retention, invalid access before CreateFile. Independent
code and architecture review before one native invocation. Preserve all logs,
terminal receipts/JUnit and SHA256; re-review actual evidence. Production pins
and scientific thresholds remain frozen. This is a research checkpoint, not
ALC-R0 completion or training authority.
