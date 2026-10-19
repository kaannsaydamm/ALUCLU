# Checkpoint162 independent durable storage review

Initial reviewed source996981c0062268086483aeecc0baf7d63593559236d123651e9025b7294653fb
testsbcfdb37549cf02123eff7dd80b28184a87866ca3b1cb7c887fffc108f6682469.
Both independent GPT6.1Sol lanes inspected exact bytes, no tests or model/process
launches and no edits. Scope is generic storage, not attempt or launch authority.

## Code/spec/security: REQUEST CHANGES

P2 source179-182 opens rb/r+b before nonregular fstat check at138-141. On POSIX
a FIFO can block during rb open under the lock. Need lstat regular/single-link
precheck under the lock before open, retaining descriptor fstat checks. Trusted
root scope excludes malicious path replacement, not accidental storage types.
Native POSIX reproduction was not performed by reviewer; platform fixture needed.
Root verified the relevant blocking-open semantics against
[Linux man-pages fifo(7)](https://man7.org/linux/man-pages/man7/fifo.7.html).
OpenGroup pages returned403; no source download or POSIX launch occurred.

P3 tests134-182 and275-289 lack forced interleaving; sequential scheduling can
let a lock-removal mutant pass. Add controlled competing writer scan visibility
coverage and prove a no-lock mutant is caught. Current lock reuse appears sound.

## Architecture: scoped CLEAR, integration WATCH/BLOCK

External monotone head publication/reconciliation remains mandatory. Crash after
log fsync before publishing head is uncertain, not permission to adopt latest,
relaunch or erase an attempt. Close/unlock exceptions can also follow durable
write. Cooperating writers must preserve journal and lock identities.

Every append fully scans/materializes history; cumulative quadratic cost must
be measured for actual workload before latency claims. Raw32MiB limit is not a
32MiB Python heap bound. Generic events do not enforce attempt transitions,
resumes, repairs, candidate cardinality or exclusive resource reservations.
Reuse of cognition persistence imports a broader package; not stdlib-only.
No universal native portability, powerloss or hostile-root guarantee inferred.

## Initial synthesis

REQUEST CHANGES from code lane blocks acceptance notwithstanding scoped
architecture CLEAR. Repair/rereview/regression pending. Prior native runtime
checkpoint160 stays OPEN. No actual model/tokenizer/dataset/GPU execution.

## Repaired independent rereview

Source2629b8494977f6e22e216bd56e28110b5fb407a6e515b0df3400def566775543;
tests9980e212911079e68aebf6cf349b204128379513935d6b2fa71552991ae83eda.
Both lanes independently rehashed/read repaired bytes: code APPROVE, architecture
scoped CLEAR. P2 closed by lstat before open and retained descriptor validation;
P3 closed by controlled scan interleaving and lock-removal mutant. Windows
directory REDv6 actual1 then focusedv7 actual0,46cases/1explicitPOSIXskip.
Review was static, execution evidence belongs to root and cannot establish
native POSIX FIFO behavior. WATCH/BLOCK caller/launch obligations above remain.
Root personally consumed original92288 terminal actualpytest0 and parsed final
XML1550tests/0failures/0errors/1skip,123.383s (1549passed). Only skipped case is
nativePOSIXFIFO. SHA5d8f3d780e6f09e969610f0686160f44558bebe695e02fe004b348fed661666d.
Confirmed46journal/33ownedprocess/70resource/12persistence cases and unchanged
final source/test SHA256. Ruff check/formatcheck passed; negative evidence kept.
Scoped storage acceptance satisfied on this Windows runtime with explicit POSIX
residual coverage. This neither repairs checkpoint160 native crash nor supplies
external-head owner, typed attempt/reservation semantics or launch readiness.
