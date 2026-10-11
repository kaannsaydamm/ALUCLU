# Checkpoint161 independent resource arithmetic review

Scope: pure arithmetic helper, tests and prospective plan. This is neither a
launcher nor authenticated accounting nor a durable reservation journal.

## Code/spec/security lane

Independent GPT6.1Sol `/root/resource_code_61` inspected all three files, verified
source SHA302a8d58c6d08d04e2304e0500e8e4961f60e750067c4fc57c1d7debe540e82e
and tests SHAfe3c1eb6147898529461e64e736ee48e1883810916f0ed7105e4274dc46108c3.
APPROVE, no actionable correctness/security defect. Review was read-only, no
imports or test/model/tokenizer/GPU execution.

LOW optional coverage improvement at tests195-210: explicitly exercise nested
ProgramAccounting mutation and dataclass subclass rejection. Existing frozen
dataclasses and exact-type checks enforce these properties. This observation
is retained rather than represented as executed additional test coverage.

## Architecture lane and synthesis

Independent GPT6.1Sol `/root/resource_arch_61` verified the same source/test hashes.
WATCH for pure arithmetic, BLOCK for interpreting it as launch readiness. No
arithmetic defect found under disclosed fixed elapsed-UTC/single-GPU assumptions.

Main interface concern: source43-45 and131-135 apply the same projected/pending
growth to logical research quota and physical C: free space. Plan now requires
each input to upper-bound BOTH measures, including peak temporary/staged/cache/
journal allocation; materialized pending bytes must be reconciled atomically,
not double-counted in observations and outstanding growth. Independent recheck
of the clarified contract remains pending; current executing source unchanged.

Other WATCH items retained: remaining GPU value is before new reservation;
CPU/no-CUDA and single-GPU bounds require runtime enforcement; hash formatting
does not authenticate history; elapsed45UTC days does not certify alternate
civil-calendar interpretations; pending-value arithmetic tests do not prove
concurrent exclusion. Future launcher must not launch directly on resource_fit.

After the plan amendment, the same independent architecture lane rechecked the
contract: CLEAR for pure arithmetic architecture, source/test hashes unchanged.
The shared conservative growth bound resolves the storage objection at the
specification level. WATCH for later caller obligations and BLOCK for actual
launch readiness remain: no reconciled historical budget/start, durable journal,
reservation exclusion or runtime qualification has been established here.

Synthesis: code APPROVE + scoped architecture CLEAR = scoped review APPROVE.
Root personally consumed original regression session57160 terminal actualpytest0:
1492tests/0failures/0errors/0skipped,154.198s. XML SHA256
ecfb52c6b3506232e72ff43c42f87ed54b2db8529d0a2361ea1bb5712aa59056;
70 resource cases and33 owned-process cases included,49 selected targets total,
same three actual-asset/GPU exclusions. Source/tests rehashed unchanged.
This closes only pure arithmetic component acceptance, not the journal/launcher.
Checkpoint160 native crash diagnosis remains OPEN regardless of helper results.
