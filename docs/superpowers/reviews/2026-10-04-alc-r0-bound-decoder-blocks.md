# Checkpoint127: captured decoder blocks

Baseline `c2ddf9c13f06c5112e31390c1217da305aec355b`; checkout
`C:\Users\kaann\Desktop\03_Projeler_Arge\ALUCLU\.worktrees\unified-lifelong-cognition-local`.

`_bind_checkpoint_block(index, decoder)` creates a callable for an existing
guarded ticket, not a new execution authority. Capsule blocks capture the actual
decoder module and selected post-block factor operation. LoRA-selected blocks
capture input/post norms, attention, MLP, q factor operation and attention helper.
Nonselected blocks delegate to the capsule builder with no capsule mounted.
Index must be an exact integer0..29; decoder must be a module. Cache is absent
and disabled. Private ticket metadata supplies mask/positions/cos/sin; the builder
itself neither clones nor certifies arbitrary caller metadata.

The existing q-attention computation is extracted into one function shared by
default and captured paths. Mathematical operation order is retained. Closures
do not look up the current wrapper mount during initial compute or replay.
This is reference capture, not immutable state: session guards and the later
complete host dependency inventory remain mandatory.

## Evidence

All files below are under `results/` with prefix `alc_r0_bound_decoder_`.
Parent observed real exit codes and parsed JUnit counters and SHA256.

| Artifact | Exit | Tests | Fail/error/skip | Seconds | SHA256 |
|---|---:|---:|---|---:|---|
| red_v1_20261004.xml | 1 | 16 | 16/0/0 | 7.691 | 3b21c32857542785b27aad3bcc49906eece739d0bfb87c34ac05ccfbad7a7c0d |
| green_v2_20261004.xml | 0 | 16 | 0/0/0 | 6.076 | aa0e565458e2e8c289fc9175ddbd885a9dbb8d60e9fa7eafb88d4396cac46064 |
| engine_v3_20261004.xml | 1 | 22 | 1/0/0 | 6.384 | 256792a06fb9e79693f3375c44f706a9dccd1bed6a05e59393523f23caafd9c2 |
| regression_v4_20261004.xml | 0 | 485 | 0/0/0 | 9.265 | 9e4b39eef57c3ab529a6501d0808a001f5d07984772de7859469260bc5a3470a |

RED is missing binding API. Enginev3's one failure arose in two-pending LoRA
gradient equality: reference incorrectly multiplied a single graph loss by2,
while checkpoint arm summed two separate graphs. The reference was repaired to
two separate forwards with the same summation order; the exact CPU comparison
was not relaxed. Preserved all four attempts. Final Ruff check passes.

The 22 new cases test first/last and each of30 layer captures, correct capsule
placement, captured q/factor gradients with frozen inputs, mount replacement
without current-mount reads, invalid indices, complete owned engine traversal,
one/two outstanding graphs, private metadata isolation, no base gradients, factor
drift abort/gradient cleanup and successful lease reacquisition.

Final regression reproduces checkpoint126's documented 463-case command plus
`tests/test_alc_r0_bound_decoder_blocks.py`, with a new unique JUnit path. Same
research Python, `PYTHONPATH=src`, `PYTHONDONTWRITEBYTECODE=1`, `-B`, pytest
`-q -p no:cacheprovider --tb=short`. Its two asset-dependent deselections remain
explicitly required and were absent in the parsed final case list. No model
asset, corpus, held-out evaluation or optimizer step executed. Standard logs were
tool-captured, not saved as separate log files.

## Candidate exact bytes and independent review

- host_wrapper.py: 396ba312e78fe47302d2077092f44c23fe06ccb673954fe61122fba8bf2566b1
- matched_lora.py: 17d504653ccf515d4a8c8298670f1dbbcac020ee3fcff800576704caac41ff57
- test_alc_r0_bound_decoder_blocks.py: 8ecfe9330fdbd8ae320a25a6b4c53796917906491b1de52347ab93af53c8c037

Independent final code APPROVE, architecture CLEAR; synthesis APPROVE BOUND
CALLABLE COMPONENT ONLY. Both verified the three exact hashes and inspected
without execution. Architecture notes that live/bound LoRA comparisons share the
extracted helper and therefore verify capture/placement, not independent full
attention parity. Both require later complete host-state guards and actual
index-to-layer binding. No real-model or learning authority follows.

## OPEN integration gates

No opt-in forward argument/path or computational-state callback is attached by
this component. Installed Transformers source inspection identifies mutable
dependencies beyond registered tensors: RMS epsilon, attention dimensions/scaling,
configuration/selected attention backend, activation modules, rotary/global
functions, masking/loss helpers and framework execution settings. Identity-only
or function-global-blind fingerprints do not discharge this audit.

Real-wrapper inventory, full input/cache validation, forward/ticket orchestration,
actual-host CPU/GPU parity, resource qualification, synthetic invocation review,
scientific rights/freeze/evaluation and neural learning remain OPEN. This record
does not approve training or claim ALC-0 or user-driven durable `.alc` learning.
