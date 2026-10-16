# Owned current-interpreter runtime binding

Parent dd3ff45. Scoped implementation/TDD design APPROVE / CLEAR.
Purpose: replace disconnected per-tree hashes with one current-process runtime
identity usable as factual input to the later trusted operator producer. This is
not that producer, immutable/native closure, launch permission or scientific D.
Current labels and current on-disk hashes do not prove the exact image bytes
originally mapped into the already-running process or any loaded native DLL set.
Executable compatibility amendment, reproduced before repair: CPython Windows
path stat synthesizes0111 mode bits for .exe/.bat/.cmd/.com whereas fstat has no
path. Cross-source matching accepts only the directed all0111->0 difference with
every other mode bit identical, Windows only. Full same-source mode continuity,
file type, dev/inode/nlink and read/write bits remain checked. No executable
permission/ACL or native mapped-image claim is inferred. Primary implementation:
https://github.com/python/cpython/blob/v3.12.12/Modules/posixmodule.c#L1777-L1798

Implement inspect_current_python_runtime(deadline_ns, bounds), callable only
inside existing owned original-deadline diagnostic/preflight child. No CLI or
launcher, root selector, callback, arbitrary executable, package/model imports,
installation or new reservation framework. Existing scientific bootstrap denial
remains unchanged. Component roots are the running interpreter's sys.base_prefix
and sys.prefix, not request values; require a distinct venv and resolved absolute
regular directory roots. Windows CPython only for this first local binding.

Observe before/after: sys.executable, sys._base_executable, sys.prefix,
sys.base_prefix, sys.exec_prefix, sys.base_exec_prefix, sys.version,
sys.implementation.name/cache_tag, sys.platform, pointer size, byteorder,
selected sys.flags (isolated, ignore_environment, no_user_site, safe_path,
dont_write_bytecode, optimize), and exact ordered sys.path strings. Capture fixed
environment keys PYTHONPATH/PYTHONHOME/PYTHONNOUSERSITE/PYTHONDONTWRITEBYTECODE,
HF_HUB_OFFLINE/TRANSFORMERS_OFFLINE/HF_DATASETS_OFFLINE/CUDA_VISIBLE_DEVICES/
CUBLAS_WORKSPACE_CONFIG. Missing differs from empty. These are observations, NOT
a finding that import paths, environment or flags are safe/approved. Preserve
nonexistent zip sys.path entries literally; never import or execute them.
Require prefix==exec_prefix and base_prefix==base_exec_prefix; interpreter paths
must be resolved regular non-reparse files within their corresponding roots.
No public injected sys/backend/environment seam in production.

Bound observations before retaining: max256 sys.path entries, max32768 UTF-8
bytes/string, max4MiB aggregate observation-string bytes. Version/name/cachetag
obey same bounds; require exact scalar types, finite closed Windows platform/
CPython/64bit values; no arbitrary object repr. Bounds validation and original
deadline precede tree observation. Reject unknown/missing implementation fields.

Using unchanged runtime_tree_inventory inspect both exact component roots under
the SAME original deadline and explicit RuntimeTreeBounds; bound each component,
logical total <=2 times supplied component cap. Require existing pyvenv.cfg as
regular non-reparse file in venv. Capture its SHA and both executable SHAs via
existing streamed _hash_file continuity primitive and full lstat fingerprint;
each special file <=16MiB, cfg<=64KiB. Recheck all three path fingerprints after
the two component scans and require equal before/after process observations.
Tree fingerprints remain cooperating-filesystem continuity, not immutable/native
DLL closure; two roots cannot be atomically captured against hostile mutation.

Canonical root covers schema, complete observed layout/settings, both component
evidence rows and special file bindings (role, absolute path, byte length, SHA).
Integer counts/lengths encode decimal strings to avoid RFC8785 large-int limits.
Return canonical bytes plus SHA256; no approved/success/permit field or authority
generation inferred. Absolute paths are local identity, not portable semantics.

TDD: Windows owned temporary venv-like trees via isolated child sys state (test
fixtures only), import trap against torch/transformers, exact root oracle,
changed executable/config/path/env binding, malformed/current-layout rejection,
deadline and cap failures, complete terminal root/job evidence. Then run one
read-only actual-current-interpreter inventory INSIDE a bounded owned child if
its explicit caps fit. This is factual runtime observation, not model/CUDA/D
qualification or history/accounting reset. No mutation of installed runtime.
Independent reviews plus relevant runtime/source/canonical/lease/stop/watch
regression and all negative attempts retained. Real scan may fail; do not lower
requirements or claim installed-runtime certification from synthetic fixtures.

## Observed uv base-junction amendment (independently admitted)

Actual read-only scan refused the current uv base-prefix minor-version junction.
Readonly Windows metadata confirms cpython-3.12-windows-x86_64-none targets the
regular cpython-3.12.13-windows-x86_64-none directory. Preserve failed attempt;
do not mutate installed config, silently call raw prefix resolved, or certify it.

Permit only the observed-class base-prefix directory junction (Windows mount
point reparse tag0xA0000003), derived from current sys.base_prefix, with explicit
base_prefix_alias field in canonical payload: null for ordinary root, otherwise
raw absolute path, exact immediate-target string, resolved regular-directory root
and decimal reparse_tag.
Require the raw root itself to be that exact directory junction, not symlink or
other reparse kind. Read os.readlink on the junction; preserve exact immediate
target string. Normalize ONLY Windows extended local-drive prefix (\\?\\C:\...)
for filesystem access, not in retained identity; reject UNC/relative targets.
Require immediate target itself resolved==raw normalized target, regular and
non-reparse, and raw junction parent resolved==parent. Reject chained target or
ancestor aliases rather than resolving past unrecorded links. Final root must
equal that immediate physical target. Add real chained-junction negative fixture.
Final resolved root must be regular/non-reparse. Venv remains
strict resolved/non-reparse. Base executable raw label must lie structurally
inside raw base-prefix path; resolve it through that base alias and require exact
regular resolved executable inside resolved base root. Preserve raw labels.

Capture full raw-junction lstat fingerprint and exact resolved target before any
special hashing; repeat fingerprint, exact immediate target and resolved target
after the component scans. Deny alias identity or
target drift. Hash only resolved base tree, whose internal reparse rejection is
unchanged. Include alias path/target/tag in result; alias is factual, NOT approved
provenance or a safe-resolution claim. One captured junction, no generic resolver
API/allowlinks option and no request roots. Non-junction aliases still reject.
Tests: actual temporary mount-point junction fixture (no fake stat), exact alias
binding, target content participation, nonjunction regular-root null field, and
retained original real denial before separately versioned actual retry. Existing
current labels/on-disk bytes/native-closure limits remain unchanged.
Alias strings must satisfy the same32768UTF8/string cap before retaining them;
all complete payload value strings share4MiB aggregate before canonical encoding.
The actual test is skip-by-default under ordinary collection; closed versioned
actual modes explicitly opt into diagnostic observation, never launch authority.
