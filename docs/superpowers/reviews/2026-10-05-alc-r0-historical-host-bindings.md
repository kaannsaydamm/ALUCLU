# Checkpoint176: historical host controls joined to source and runtime receipts

Parent 2b6ac0e2598428e24d1f8df8f99612b46aa800eb. Read-only reconstruction,
2026-10-05. No old command executed, model loaded, corpus read or GPU job run.
Private session path and privacy boundary are recorded in checkpoint174's report.
Filter original 2026-09-21 records and exact four execution IDs below; do not
export whole private history. Current work remains in the Desktop local checkout.

## Terminal observations

| CommandExecution id | Completion event UTC | Tool handle | Exit | Command seconds | Payload started_at_ms | Payload completed_at_ms |
| --- | --- | --- | ---: | ---: | ---: | ---: |
| exec-e35be2f7-1e98-40a4-aef7-3db20c6a1643 | 2026-09-21T19:18:00.662Z | 16813 | 0 | 33.790638500 | 1790018246871 | 1790018280662 |
| exec-f24da8f4-aec8-4724-8c94-d1894e3ec957 | 2026-09-21T19:45:23.063Z | 31821 | 1 | 3.983815500 | 1790019919079 | 1790019923062 |
| exec-91d70551-fb07-4481-a5fa-19782d06693a | 2026-09-21T19:46:20.003Z | 31325 | 0 | 34.805039900 | 1790019945196 | 1790019980002 |
| exec-2891513f-947e-494b-b6cb-391d43ef8d9d | 2026-09-21T20:26:15.671Z | 47725 | 0 | 28.420985200 | 1790022347250 | 1790022375671 |

All invoke scripts/verify_alc_r0_host.py in the historical OneDrive cognition
worktree, using the Windows research venv and pinned local SmolLM2 snapshot.
The failed second command supplies expected source
6ad9965381e0602de5af8fd556be3cb1774fb76f; terminal traceback says
current HEAD does not match expected source commit. Historical script6ad9965
checks this before entering the immutable export and spawning model workers.
This is a pre-worker source-identity rejection, not a failed GPU training step.
Keep it in attempted-invocation history; no global budget exemption is inferred.

## Exact source/receipt/runtime joins

Successful terminal JSON summaries provide these source/receipt pairs. Raw Git
receipt bytes were read without checkout EOL conversion through redirected Git
stdout, UTF-8 encoded without normalization, hashed and parsed. Each receipt is
2040 bytes. These hashes agree with terminal summaries and original trajectory.

| Source commit | Receipt stored at commit | Base receipt SHA256 |
| --- | --- | --- |
| 4efd7d5a1958abacea93a4bac664c0674cd678b8 | 177ab33090fdbfbfd3a3b82dea267d0152757280 | 6d260faac2e527e34fe21a112e338be034e0b32894cf6e15c1c84f08fa6ff4e1 |
| 6ad99656be57771515335cd6dfdccdef0eeadc9c | 8810e0e0239a1be1eb282dc375d5a45631633f24 | d963fd85b5a3defd90391646323d6a3878e4f0dcb4c068e3e77a057990d4aa09 |
| 526786fea7c4a4a9ed459a18b99eee2c646ea24f | addd213a673139eaa2d08639d4a82d43bd64faff | 3bc973d0003160ab24f2b26c519129d48d7094a025381b41b1ffe152645d1953 |

All three bind acquisition receipt
2a4baddc2bb8451811e199e7dd6f91512fad73d367083c833e117c3e4d09984a,
Windows lock a7a921f7b095b0329fbb7df6a25612c6e8a1f160122f853a6a159d8478946615,
lock manifest 1756f42033d4de2f5d2944fc7a95a4e324665a26f54c0679bb757658fc91abaf.
Two equal observations report Python3.12.13/Torch2.14.0+cu130/Transformers5.17.0,
torch.bfloat16,134515008 parameters,zero trainable parameters and training=false.
training_authority=false remains explicit. Version strings and lock roots are
runtime receipt claims, not authenticated runtime-binary attestation.

All three source commits share host.py Git blob
10e8287773c198ca52051420d0333031aebd342a: default device=cpu and dtype=bfloat16.
Historical script workers call load_verified_host(snapshot) without overriding
that device. These are CPU/BF16 base-identity controls, not CUDA training merely
because the installed Torch build includes CUDA. The initial4efd7d5 script blob
868b8d1251d6e69bc39567af90b5fb3d858cf245 uses mutable-worktree source after an
initial cleanliness check; do not retroactively grant it immutable-export proof.
The6ad9965 script blob9bc36e5539d8e6ce61f3e3f3731bdea118beeee4 introduces the
immutable source export;526786f script blob0d64e7e8cd41612887faa17db1649da212a653f2
continues commit-bound worker execution. These are separate historical strengths.

## Decoded output roots and remaining limits

SHA256 below identifies UTF-8 bytes of decoded aggregated_output strings,
including original carriage returns/newlines, not whole-session authentication.

| CommandExecution id | Output UTF-8 bytes | Output SHA256 |
| --- | ---: | --- |
| exec-e35be2f7-1e98-40a4-aef7-3db20c6a1643 | 643 | 730c44d6954300d8a9025808fb38ce1395648afbb42794d4858895524e054f6c |
| exec-f24da8f4-aec8-4724-8c94-d1894e3ec957 | 677 | a75b0831d69696d232cfd8d8fcda7882de358586a90f4183abc61d3bdb1039de |
| exec-91d70551-fb07-4481-a5fa-19782d06693a | 690 | 0c6212fda914ff86cb838512e84aa94faee33e12208df630ddb93aabb61cb3a7 |
| exec-2891513f-947e-494b-b6cb-391d43ef8d9d | 647 | cc5a89c92c4cf84e72fcf19ea188ca706a0789414c3dd7d9496ac7fe96f16806 |

Sum101.000479100seconds is tool-command wall duration, not GPU consumption.
Tool handles are not authenticated OS PIDs; payload envelope timestamps are not
OS/GPU timing. Early CPU controls precede later synthetic training records but
do not determine the original first development job or complete attempt coverage.
The date/name-filtered discovery excluded static tools and source-view commands;
it is not exhaustive proof of no earlier/different invocation. Initial broader
formatted output was truncated; exact-ID compact reinspection supplied the
selected complete metadata. No first-job clock or600hour allowance is reset.
Remaining GPU/bootstrap/failed/interrupted history, measurement gaps, original
resource admission, current invocation authority and scientific gates stay OPEN.
