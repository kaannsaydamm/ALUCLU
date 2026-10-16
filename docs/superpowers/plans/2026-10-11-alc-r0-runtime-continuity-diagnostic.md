# Runtime continuity first-difference diagnostic

Parent 9c39299. Previous goal turn PROGRESS: factual binding implementation,
274-case regression and separately retained actual_v2 continuity refusal.
Installed runtime acceptance remains OPEN; no scientific execution is enabled.

Add diagnostic detail only to the existing final tree-comparison failure. The
same complete before/after trees and counts still decide refusal. Retain the
lexically first differing relative path (Python string order, independent of
scandir order), component, membership/kind/metadata fields and both original
fingerprints. Show at most128 path characters, plus exact full UTF8 byte length,
SHA256 and truncation flag. Root path is the empty string. No file contents or
additional filesystem observations are performed to explain the difference.
Every selection iteration and final encoding checks the same original deadline.
The already bounded tree/path data are the only inputs; no public injectable
backend, extra allowance or metadata tolerance is introduced.

RED covers all8 fingerprint fields, added/removed/kind changes, bounded Unicode
preview with deterministic path selection and expired original deadline. GREEN
includes full binding/tree tests, then relevant eight-file regression. An actual
read-only attempt uses a fresh closed actual_v3 artifact stem only after code
review/focused evidence; preserve earlier failures. Use result detail to decide
the cause and next fix, not an identical blind rerun or scientific gate bypass.

## Retained failures and next diagnostic envelope

GREEN-diff85 passed; regression-diff287 had exactly one failure: old fixture
compared path lstat ctime to open-file fstat ctime,1791725079935187600 versus
1791725079935693200. That contradicts the already accepted Windows cross-API
ctime distinction. Correct the fixture to use the existing cross-source identity
predicate and preserve full path-to-path and fstat-to-fstat continuity. Production
comparison fields/tolerance are unchanged. Do not infer this is actual_v2's cause.

Actual_v3 hit its ORIGINAL240s inner owned deadline, root exited124, stdout0;
outer pytest failed1case240.640s and completed without outer timeout. No binding
JSON was produced because the old fixture asserted zero child exit before result
retention. Preserve logs/XML and no invented completed inventory. Improve actual
diagnostic retention: drain using observed native exit, persist nonzero/timeout
as ok=false with full native process receipt. Success still requires non-timeout
zero exit, complete output and valid binding; assertions do not accept timeout.

Preregister actual_v4 only: NEW900s CPU-only diagnostic reservation and960s outer
test bound, never renew prior240s attempt. It uses the same paths/file/byte caps
and original deadline through all work. Run serialized after revised focused and
regression evidence/review, not alongside process-heavy validation. This is a
diagnostic allowance, not a scientific D threshold change, retry permit, budget
reset or model/GPU run. The observed240s truncation justifies gathering full
evidence in one larger finite attempt; cause of actual_v2 remains unknown.
