# ALC-R0 synthetic optimizer-update diagnostic — NON-AUTHORIZING

This is a local execution diagnostic, not R0.4, development eligibility, or
ALC-0 capability evidence. It uses no Banking77, PrimeVul, or held-out rows.
The existing R0.0 validator and family-B v2 freeze remain required before
task training. No acceptance threshold or frozen experiment contract changes.

Before running the real host, fix these cells: pinned SmolLM2-135M snapshot,
Windows CUDA/BF16, eager attention, frozen/eval base, FP32 factors, ports
`(14, 29)`, rank 8, initialization seed `20260916`, deterministic 512-token
synthetic IDs from the existing gradient probe, target token ID 23, batch 1,
and `use_cache=False`. Run separate fresh processes for `ResearchCapsuleV0`
and exactly parameter-matched q-only LoRA, in that order. Each arm gets exactly
16 successful AdamW updates with the existing frozen optimizer values:
learning rate `3e-4`, betas `(0.9, 0.999)`, epsilon `1e-8`, weight decay 0,
global gradient norm clip 1.0. This is *not* a replacement for R0.4's
200-update, real-data, effective-batch-16 pilot or its schedule.

Measure target-token log probability before and after the 16 updates, loss
trajectory, finite gradients, factor-state change, base-state digest equality,
GPU peak allocated/reserved bytes, runtime, exact source/model/environment
identity, and every failure/OOM. Record either improvement or non-improvement
without changing the target, step count, or learning rate. A post-update
increase on one fixed synthetic next-token example would demonstrate only
that the trainable factors can store a local neural update; it says nothing
about generalization, durable skill, code vulnerability detection, or
Banking77 intent routing.

For the capsule arm, serialize learned factors through the existing canonical
SafeTensors artifact, detach, and launch a separate process that remounts the
artifact on a fresh pinned host. Require its target log probability to match
the training process post-update score within `1e-4` and its detached score
to match the training process pre-update base score within `1e-4`. The
remount process may not see training examples (only the deterministic
synthetic-ID rule) or use retrieval. If any check fails, report it as a
negative result; do not call this ALC-0 PASS.

## Observed local result, 2026-09-29

Clean source commit `c4f147c` produced terminal exit zero for both separate
16-update cells and the fresh-process capsule remount. Capsule target-token
log probability moved from `-6.6672158241272` to `-6.34233427047729`
(`+0.324881553649902`); matched q-only LoRA moved from the same baseline to
`-6.5954794883728` (`+0.0717363357543945`). Both factor states changed,
both base-state digests stayed identical, and both detached scores returned
to the baseline. In a third fresh process, the canonical capsule artifact
produced exactly the training post-update mounted score and the baseline
detached score (both absolute differences `0`, below `1e-4`). No held-out
data or task examples were used. The differences are not arm rankings or
task-skill gains; one synthetic example and 16 updates cannot establish
generalization. Exact receipts, SafeTensors artifact, hashes, and measured
resources are in `results/alc_r0_synthetic_update_c4f147c_*` and
`TRAJECTORY.md` checkpoint 68. R0.0/R0.4 and ALC-0 remain OPEN.

## Predeclared long-context follow-up — NON-AUTHORIZING

The completed 512-token diagnostic says nothing about whether the candidate
2,048-token family-B context can sustain optimizer updates locally. Before
running a longer cell, extend only the synthetic sequence length to **2,048**
with the same deterministic ID rule and all other values above unchanged:
capsule then matched q-only LoRA in fresh processes, exactly 16 successful
updates per arm, and a third fresh-process capsule remount at 2,048. Require
at least 20 GiB free C: and the unchanged frozen-base/model/source checks.
Record all exits/OOMs, loss and gradient trajectories, target log probability,
factor/base hashes, CUDA peak allocated/reserved bytes, and elapsed time.
Do not retry at a shorter length, lower the step count, change dtype/rank,
or treat a failed arm as feasible. A success shows only 16-update synthetic
resource fit; it does not establish the full label-sequence, effective-batch-16,
200-step R0.4 envelope or select a v2 prompt budget.

The complete follow-up ran from clean source commit `3966c90` with terminal
exit zero for all three fresh processes. The capsule's target-token log
probability changed `-6.94224405288696 → -6.530837059021`
(`+0.411406993865967`); matched q-only LoRA changed from the same baseline
to `-6.83657646179199` (`+0.105667591094971`). All 16 losses/gradient
norms per arm were finite; both factors changed and both base digests stayed
identical. CUDA peaks allocated/reserved were **4,424.6/4,522 MiB** for
capsule and **4,603.1/4,810 MiB** for q-only LoRA. The third fresh process
reproduced the capsule's mounted post-update score and detached baseline
score with zero measured difference. Receipts, artifact, hashes, and limits
are in `results/alc_r0_synthetic_update_2048_3966c90_*` and trajectory
checkpoint 70. This observed 16-update fit does not authorize a 2,048-token
prompt freeze or imply 200-step/full-label feasibility.
