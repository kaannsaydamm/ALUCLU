# Checkpoint147: enumerated module dispatch and factor lookup state

Baseline: ce4719076f9f2bde85abd243861143226e6bb982.

Static class lookup inventories __call__, _call_impl, _wrapped_call_impl and
__getattribute__; ModuleDict adds getitem/len/iter/contains, ModuleList adds
getitem/len/iter/_get_abs_string_index. Python function identity, code, defaults,
keyword defaults and closures use the existing bounded fingerprint. Unsupported
descriptors fail closed without invoking their getters. Native descriptors,
including originals captured in a Python closure, bind identity and owner-class
identity only. Both factor factories require the import-time typing.cast alias
and fingerprint that function's state. Import-time identity is NOT source
authentication or a complete computational integrity guarantee.

## Executed evidence

Root consumed the original regression process terminal: pytest_exit_code=0.
JUnit was independently parsed; all 28 new cases were found. Reviewed bytes:

- checkpoint_state.py SHA256: 3143311f6b240005cf8d99b3ea3f664a40e9a9c80c3c1af11400d39e6a921527.
- New test SHA256: 9ab6240ec16b71d9378efe0a459ff002200d56fd835dea1554bd14a905396411.

| Receipt | Exit | Tests/failures/errors/skips | Time | XML SHA256 |
| --- | --- | --- | --- | --- |
| red_v1 | 1 | 12/12/0/0 | 17.221s | 9909050729536066028e0e840f36a00e83175c1222b022a0cfed96982b516291 |
| green_v2 (FAILED) | 1 | 87/1/0/0 | 11.480s | 410454572ae51bac4e88b8635a9d50ed9e4ff7a52518d28c72cc66c2892592c7 |
| regression_v3 | 0 | 977/0/0/0 | 28.817s | 22e1100f4ebe0467a12c46458f656513dfa4e1883384d8da0e2fb3ad63c2c9ce |

RED reproduced same-object code/cast drift, including preparation/replay denial
failures. Intermediate v2 exposed an existing closure retaining its native
descriptor; explicit bounded descriptor records repaired it without weakening
that test. Sixteen further controls expanded the new test set to 28 cases.
Coverage includes all enumerated code mutations, dispatch defaults, both factor
arms, cast alias/code drift, and property rejection without getter execution.

Regression scope is the 31 checkpoint/capsule/LoRA/observation/accumulation/schema
test targets from checkpoint146 plus this new file, not the entire repository.
The real CUDA host and pinned real-tokenizer tests remain explicitly deselected.
Tiny optimizer controls in this suite are synthetic, not model training.

## Independent review and synthesis

GPT-6.1 Sol code lane: APPROVE, no severity-rated findings; inspected complete
state/test sources and diff, verified hashes, executed no tests or models.
GPT-6.1 Sol architecture lane: CLEAR for the enumerated extension; inspected the
same complete sources/diff and verified hashes without executing code.

Strongest counterargument: Python functions can change behavior via effective
globals/builtins without code/default/closure changes. This extension explicitly
does not inventory those dependencies for all dispatch methods. It is not all
module methods, native semantics, full wrapper callback coverage or actual-host
qualification. Native endpoints are identity-only; import-time baselines are
cooperating-process references. These remain explicit open requirements.

Synthesis: APPROVE BOUNDED COMPONENT ONLY. No host parity/resource/portability,
neural acquisition, .alc durability or scientific ALC-R0 acceptance claim.
Wrapper inventory, atomic opt-in, mask resolver, actual D/E and scientific R0
gates remain open; the full unified goal remains active.
