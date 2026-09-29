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
