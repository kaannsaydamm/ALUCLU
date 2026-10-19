# StandardInformation observer intervention v1

Preregistered before implementation/native results, baselinef6ad53d,2026-10-11.
Previous access intervention was progress: final197tests and actual sequence
showed opening/querying second0x80/0x81 handles insufficient in that run; only
enumeration interval showed0->8192. Preserve all prior negative evidence.

## Question, selected alternative and boundaries

Does a FileStandardInformation query on the retained attributes-only handle
report a different size than class68/by-name before enumeration, or initialize
the observation without enumeration? This is a diagnostic question, not a repair.
Existing14fields/fullraw contract remains intact. No normalization, support
inference from zero, tree warmup, retry-to-PASS, model/data/GPU/training/fullscan.

Alternatives: repeating old access run adds little discrimination; class77 adds
new support/device-provenance ambiguity; class5 provides separate documented
size/allocation facts through an existing native export for small CPU/ABI cost.
Choose class5 now, keeping portability/security/scientific claims unchanged.
No new compiled dependency, installed writes, cacheflush, reboot or paid compute.

## Native ABI and fixed sequence

Only new allowed NtQueryInformationFile pair(size24,class5). Existing72/68 and
8/4 remain. Windows64/little-endian, IOStatus16/infooffset8, exact native status0
and Information24 required. Preserve IOSB status diagnostically. Pending uses
existing immediate process-only fatal71, no unwind/retry. Other status/length
errors fail closed and remain terminal error evidence; no fallback.

FILE_STANDARD_INFORMATION layout24: signed64 allocation@0, signed64 EOF@8,
unsigned32 links@16, BOOLEAN delete_pending@20, directory@21, padding@22..23.
Preserve all24rawbytes including padding (not requiredzero). Decode validated
directory record: nonnegative sizes, nonzero links, delete_pending0/directory1.
Reject invalid type/length/flags, no equality-support claim from successfulzeros.
This diagnostic strictness is not a portable production parser contract.

Fixed target resolved sys.base_prefix/Lib/asyncio, then new owned control16*512.
Same path/no-reparse/localdrive validation as previous finite diagnostics.

1. By-name before open.
2. Retain baseline handle0x80; sample full existing stat/ID/device/statbookend,
   then by-name (baseline).
3. Query class5 once (standard-before-enumeration), retain raw/status/length.
4. Full baseline sample and by-name (after-standard).
5. Bounded enumeration max256names/32768UTF8bytes.
6. Query class5 once (standard-after-enumeration), retain raw/status/length.
7. Full baseline sample and by-name (after-enumeration).
8. Close retained handle; by-name after-close.

Record all3 full samples, all5 by-name observations, both standard records,
adjacent full14field differences, class5-vs-correspondingclass68 differences in
allocation_size/size/link_count, and enumeration count/digest. No discarding
fields or differences to obtain parity. Class5 comparison is sequential/nonatom.
Closing/error paths retain original context cleanup. Native exit0 = completion.

## Interpretation frozen before results

If postclass5 stage changes before enumeration, class5/query interval supports
an observer initialization association; opening/queries/time remain confounded.
If class5 sizes disagree with class68, preserve that counterevidence, not a
substitution. If all remainzero until enumeration, class5-alone sufficiency is
unsupported in this run. If first sample already8192, no-recurrence is inconclusive.
Enumeration order/time/outside actors/ABA remain; no unique mechanism or ondisk
mutation proof. No result permits a warmed fullscan, fieldwaiver, bindingPASS,
scientificPASS, training readiness or production integration.

## Execution and gates

Existingowned60suseful/10scleanup/65536stdout/4096stderr,synthetic4MiB/8MiB.
Newclosedexclusive red-standard/green-standard/regression-standard/native-standard,
privateowned-native-standard. Nativechild-I-B stdlibonly, no realrelease/admission.
Preserve prior modes/sourcebehavior; test and rerun finalbytes exactregression.
TDD intendedRED thenGREEN andrelevantregression. Newtests:24ABIdecode/layout,
negative/truncated/flags/padding, class5/signedstatus/exactlength/pending behavior,
adapterclass/prototype, fixedsequence/queryobserver/rawretention, failureclose.
TwoindependentGPT6.1Sol source/designreviews beforeonefinite nativeinvocation;
terminalreceipt/JUnit/loghash verification and actualevidence rereview afterward.

## Primary references inspected before implementation

- [NtQueryInformationFile](https://learn.microsoft.com/en-us/windows-hardware/drivers/ddi/ntifs/nf-ntifs-ntqueryinformationfile):
  class5 queries open file object without special DesiredAccess; Information is
  byteswritten; unsupportedmembersmayzero. Not a stability or supportedzero proof.
- [FILE_STANDARD_INFORMATION](https://learn.microsoft.com/en-us/windows-hardware/drivers/ddi/wdm/ns-wdm-_file_standard_information):
  fields and meanings; no guaranteed stable directory EOF around enumeration.
- [FILE_INFORMATION_CLASS](https://learn.microsoft.com/en-us/windows-hardware/drivers/ddi/wdm/ne-wdm-_file_information_class):
  FileStandardInformation5, not Win32 FILE_INFO_BY_HANDLE_CLASS values.
- [FILE_STANDARD_INFO](https://learn.microsoft.com/en-us/windows/win32/api/winbase/ns-winbase-file_standard_info):
  separate Win32 API contract; its two fields ALSO use BOOLEAN, not BOOL.
  Post-result reference clarification172: same24-byte field layout does not
  equate Win32 FileStandardInfo1 with native FileStandardInformation5. A future
  Win32 observer needs its own experiment; no native result is reused as proof.

No authoritative source found proving the observed local NTFS mechanism.
