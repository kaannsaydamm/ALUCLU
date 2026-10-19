# Initial output-allocation RED-v2 preservation review

Both existing GPT-6.1 Sol lanes inspected current tests/plan/runner and actual
artifacts read-only. Code: APPROVE preservation of tightened INITIAL RED-v2 only.
Architecture: CLEAR for the same bounded preservation scope. No implementation
or scientific/resource admission approval follows.

Manifest SHA-256:
b354e52a81200fc138bb1cd26ea93a2aca61980c7bc20e883b21001009cee5bd.
Both independently verified all8raw artifact hashes/lengths,3current source pins,
both native receipts and JUnit summaries. Pins apply only RED-v2; first RED used
earlier test/runner bytes. Product coordinator remains pushed89d9d9d source.

InitialRED:3fail/0error/0skip,4.383s/native1/root2816/total10/active0/no timeout.
TightenedREDv2:3fail/0error/0skip,5.898s/native1/root19256/total10/active0/no timeout.
Original120s controller bound unchanged. Missing capacity record and missing
private implementation are the actual failures, not an OS/model falsification.

Review-driven refinements now require observation time before the corresponding
native action bracket; role/action/request/PID/creationFILETIME bindings; and
device/inode continuity across create/resume/final plus direct pipe initial/final.
These deeper assertions remain unexecuted because current failures occur before
them. They are prospective acceptance requirements, not proof of preallocation,
native action order or continuous retained ownership.

API refusal, second-output partial acquisition, unsupported attributes and
before-resume allocation/identity-loss negatives are still required. Generic
output/lease regressions and the full relevant integrated selection follow actual
implementation. The old249case pass belongs to the previous pushed checkpoint;
it does not cover these additions. Complete physical footprint, metadata/cache,
scientific origin/resource admission and learning gates stay OPEN/BLOCK.
