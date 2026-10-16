# Checkpoint157 — pinned tokenizer fixture binding

Status: independent code APPROVE / architecture CLEAR for exact source/test
bytes below; final broad component regression PASS. Not invocation approval.

`checkpoint_parity_tokenizer.load_parity_fixtures(snapshot)` connects the
previous token-only helper to the original pinned snapshot and unchanged
`DefectPromptTemplate` framing. There is no alternate tokenizer/backend or
caller-provided token-ID argument in this production boundary.

Before any asset/tokenizer access, require an absolute Path and all three
offline flags1. Verify the exact default pinned snapshot, lazily load the
tokenizer with local_files_only=True/trust_remote_code=False/use_fast=True,
and require BOS/EOS0, base vocabulary49152, total vocabulary49152 and fast=True.
Encode unchanged prefix/suffix and BOTH complete leading-space candidates.
Use max_tokens32 to reject infeasible short framing before constructing all
six fixtures: safe/vulnerable32, safe/vulnerable64, safe/vulnerable64+7rightEOS
padding. Preserve full intended candidate labels, masked prompt/padding and
the fixed synthetic code rule, with no corpus input or changed loss semantics.

Repeat the four field encodings and require identical immutable six-fixture
results, recheck tokenizer metadata and reverify the entire snapshot receipt.
No retry, fallback or shortened candidate on failure. Return only a frozen
receipt containing the snapshot inventory/revision, observed tokenizer class,
six immutable fixtures and RFC8785/SHA256 fixture payload digest. Do not retain
the mutable tokenizer. The consumer receives `receipt.fixtures` unchanged.

Asset verification observes the existing verifier's guarantees. It is not
parent-directory/import-origin authentication or security against a malicious
runtime that restores values between observations. Repeated encoding is a
cooperating-process consistency check, not semantic correctness certification.
Source/runtime authentication, clean commit, resource accounting and launch
limits remain mandatory external gates. No command-line launcher is added.

Tests patch snapshot verification and tokenizer loading with stubs; one test
captures the production loader's explicit HF options through a fake module.
Tests neither load the actual tokenizer/model nor access task data. They prove
fixed schedule/complete candidate/padding, immutable output and repeatable
content-bound digest, offline/path denials before access, pinned metadata
denials, malformed/infeasible candidates, encoding/snapshot drift and initial
asset rejection. Existing dependency tests are not transformed into D proof.

Initial RED actualpytest1:22tests/0failures/22setup-errors/0skips,9.249s;
missing module reproduced. XML SHA256
582ff4a794da47ca13c99b104430944d143619903754a8c12cbc1efb22de8f59.
Focusedv2 actualpytest0:65tests/0failures/0errors/1skip,5.195s;
existing actual-tokenizer test skipped because no pinned snapshot path supplied.
XML SHA256817f841b017e885755a54760b21a3e65be616db695bc8809aa3646e685ffccab.
Preserve both raw receipts; not whole-repository or actual-host acceptance.

Ruff check and diff whitespace check passed at initial reviewed bytes:
sourcec1fbd60be5814ca8ced0239e5ec95a127601d93def465404451dbbe027fb57ac,
testsb170c7d71543221e3aaa456ce647c7cbe196738d3d560a280ffb5bd88ab0e194.
## Independent byte reviews

Both established GPT6.1Sol lanes independently read complete source/tests and
unchanged dependencies and verified the supplied exact hashes. Code/spec lane
APPROVE: no actionable finding; fixed snapshot defaults, explicit local loading,
complete candidates/schedule, repeated immutable fixtures, digest binding and
negative controls match the bounded contract. Architecture CLEAR: no unresolved
blocker within offline cooperating-process scope. Strongest counterargument is
the verification/load interval and imported tokenizer runtime: before/after
hashes do not attest against substitute-and-restore behavior. The declared
external source/runtime and exclusive asset-ownership launch gates stay intact.

Reviewers performed static read-only inspection only; neither independently
ran tests nor inspected the focused execution artifact. These are distinct
code/architecture component verdicts, not launch approval or actual D proof.
Neither lane consulted the other. No production/test changes after review.

Final broad component regression uses the existing40-target matrix regression
plus this new tokenizer test and defect-prompt/acquisition dependencies. Three
named existing actual snapshot/GPU cases are explicitly deselected; the focus
run's one absent-snapshot skip is preserved rather than called executed.
Finalv3 original session47336 personally consumed: actualpytest0;
1271tests/0failures/0errors/0skips,103.009s. Root parsed22new tokenizer cases.
XML SHA256d75fecb6a2b6c4c159ca70fd35526469bb9207ae300a3c0a70fa46cf015f74e3.
Ruff/diff checks passed and both final source/test hashes remained unchanged.
Exact command and evidence scope are persisted in
`results/alc_r0_parity_tokenizer_20261005.provenance.txt`.
This completes the component's stub-tested construction/integration boundary,
not actual snapshot execution or real model D. D/E, scientific R0, durable
interaction learning and portable `.alc` remain OPEN; objective stays ACTIVE.
