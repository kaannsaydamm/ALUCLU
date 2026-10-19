# Fixed-D request-file reader

Prospective scope: implement the missing bounded request-file read from the
fixed-D worker design. This is transport integrity, never activation authority.
Existing wire validation, projection, runtime settings and unconditional worker
handoff denial remain unchanged. No scientific assets or heavy imports.

API: `read_d_request_file(path, *, expected_root, deadline_ns) -> DRequest`.
Accept only an exact str or concrete pathlib Path, absolute local path, at most
4096 UTF-8 bytes and 256 components. Reject UNC/device namespaces, dot/dot-dot
components (for str input), links/reparse points at every ancestor and leaf,
nonregular leaf and leaf link count other than one. Reject unresolved aliases:
strict resolve must equal the provided absolute path under platform Path equality.
Use existing canonical ordinary-component rules (including no alternate streams,
reserved Windows devices or trailing space/dot) on both platforms. Include the
drive/root directory in ancestor observations. Total retained/read bytes cannot
exceed announced size plus one sentinel, at most REQUEST_LIMIT + 1 (16385).
Directory observations preserve mode/device/inode/attributes, not mutable size or
timestamps (unrelated directory writes are allowed). Reobserve every ancestor
after reading; compare those identities. This is cooperating-host continuity,
not adversarial ABA-proof traversal or mapped-native provenance.

Validate expected SHA-256 (exact lowercase hex str) and original monotonic signed
64-bit positive deadline before filesystem access. Check the same deadline before
and after I/O and decoding, with no retry or renewal. Outer owned-process lease
must interrupt blocking OS calls; Python deadline checks alone cannot do that.

Leaf lstat/fstat continuity reuses the independently reviewed runtime inventory
identity semantics, including the narrow Windows cross-source ctime/execute-bit
exception. Keep full same-source fingerprints. Stat size must be 1..16384 bytes
before opening. Open once, read at most announced size plus one sentinel byte,
reject growth/truncation or changed open/path identity, and compare hash before
calling the existing bounded canonical decoder. Result is its existing immutable
DRequest, not a new trust/permit object. Caller-supplied root is not authenticated
by this reader. No external callback or public I/O injection interface.

TDD: harmless temporary canonical request, wrong root, malformed bounded content,
empty/oversize, missing/directory, relative/UNC/device/dot paths, invalid argument
types/deadlines, symlink/hardlink and ancestor symlink; explicit private helper
tests may use a recording fake stream for short reads/growth/truncation without
monkeypatch. Focused and codec/canonical/worker regressions use an owned test job,
fresh exclusive evidence files, original 120-second deadline and cleanup tail.
Legacy outer capture is not runtime-capped and is not a scientific launcher.
Design review: independent GPT6.1 code APPROVE / architecture CLEAR, with above
component, sentinel, root observation, handle-close and post-decode deadline
requirements incorporated. These are design verdicts only, not code acceptance.

Previous goal turn: NO_PROGRESS (status-only answer). Current action: this design
and RED tests; no test outcome or launch permission inferred yet. Independent
code/security and architectural review required before accepting this component.
Full worker, trusted operator producer, lease admission/watch, historical charge,
clock/resource admission, GPU2 bounded comparison and D/E/science gates stay open.

After initial source review, extract the unchanged single-open operation into a
private `_read_file` helper to exercise real OS handles through explicit owned
test doubles. No substitution seam on public reader. Add real mtime mutation,
late hardlink and post-acquisition expiry/close cases; RED before extraction.
Fresh green_v2/regression_v2 artifacts required for final source. Initial
regression was live when the test file changed; retain it as diagnostic only,
not immutable final-source proof. Ancestor replacement/ABA and post-decode
expiry injection remain untested; do not imply those are experimentally defeated.
