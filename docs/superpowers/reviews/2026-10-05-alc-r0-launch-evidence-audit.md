# Actual-host launch evidence audit — checkpoint156

Observation date: 2026-10-05, local Europe/Istanbul. Directory-size observation
completed at 01:04:50+03:00; hashes and receipt checks followed in the same turn.
Inspected clean source HEAD: `bf2acc94ae52a85e3e14cab104c512996ace2014`.
This is a read-only evidence audit, NOT an invocation approval, D/E result,
resource-budget reservation, scientific learning result or independent review.

## Authoritative locations and present processes

Worktree:
`C:\Users\kaann\Desktop\03_Projeler_Arge\ALUCLU\.worktrees\unified-lifelong-cognition-local`.

Research root actually inspected:
`C:\Users\kaann\AppData\Local\Packages\OpenAI.Codex_2p2nqsd0c76g0\LocalCache\Local\ALUCLU\research\alc-r0-smollm2-135m-v1`.
Do not substitute the nominal LocalAppData path without resolving it again.

`Get-CimInstance Win32_Process` found only two Windows Python processes:
PIDs32616/33256, Python313 `http.server`, localhost8090/8092, directories
`build/web`/`build/web_profile`. Neither is an ALUCLU model worker. No process
was stopped. This observation excludes only the enumerated Windows Python
processes; it is not an exclusive worker reservation or WSL/GPU inventory.

## Current storage, not a projected qualification result

`Get-ChildItem -LiteralPath <root-child> -Recurse -File -Force -ErrorAction Stop`
and `Measure-Object Length -Sum` produced:

| Root child | File count | Logical file bytes |
| --- | ---: | ---: |
| acquisition-staging | 23 | 272447888 |
| datasets | 12 | 474521139 |
| evidence | 4 | 7312 |
| hf-home | 4 | 6007 |
| model | 10 | 272445324 |
| windows-training | 23449 | 3369976388 |
| Total inspected child directories | 23502 | 4389404058 |

Research limit: 26843545600 bytes (25GiB). `Get-PSDrive C` reported
55541108736 free bytes, above the 21474836480-byte floor (20GiB).
These are point-in-time logical directory sizes and drive free space, not
physical allocation, a recursive reparse-point safety certification, or a
future peak-storage guarantee. Dataset file metadata only was enumerated;
no dataset contents were read. No files were deleted or acquired.

## Model/tokenizer bytes revalidated without importing the model

Snapshot: research root + `model\SmolLM2-135M-93efa2f`.
Expected inventory: `results/alc_r0/control/model-acquisition-receipt.json`,
revision `93efa2f097d58c2a74874c7e644dbc9b0cee75a2`, inventory digest
`d9db0058a63990399f26b53ff7480f2e67bd5ef9a0398797fecfeb4ed9732b0e`.

Each of the ten local files matched BOTH expected byte length and SHA256.
Each file's ReparsePoint attribute was false. Snapshot contains ten direct
files including hidden files. Parent-directory identity, imported runtime
origins and source authentication remain separate launch checks.

| File | Bytes | Verified SHA256 |
| --- | ---: | --- |
| .gitattributes | 1519 | 11ad7efa24975ee4b0c3c3a38ed18737f0658a5f75a0a96787b576a78a023361 |
| README.md | 6340 | d1ba68cae64a89b6b434b11526e6e2271ee5ffd2c914ec35ed515f9d84c6085c |
| config.json | 704 | 1d556eab73b69c7f11f64c557a2f9c6f440bd4c6b89bb2584a6b498c92603843 |
| generation_config.json | 111 | 2056c988e990b0d13670f63f2f3b87b3b6d07edaf7a3416998ba27dab2d8a059 |
| merges.txt | 466391 | 0b54e8aa4e53d5383e2e4bc635a56b43f9647f7b13832d5d9ecd8f82dac4f510 |
| model.safetensors | 269060552 | 80521b40281d6ce74e35c9282c22539e75aa0ac8578892b2a59955ef78d55da1 |
| special_tokens_map.json | 831 | e786b595b9a23148bf1630df78d9037a048ea671e48bfd3549a1e3c233742bb3 |
| tokenizer.json | 2104556 | 9ca9acddb6525a194ec8ac7a87f24fbba7232a9a15ffa1af0c1224fcd888e47c |
| tokenizer_config.json | 3658 | 4bb9af56a342753d39374f4016a16574cab299fe088e896f425ce3c433f61424 |
| vocab.json | 800662 | 82b84012e3add4d01d12ba14442026e49b8cbbaead1f79ecf3d919784f82dc79 |

## Historical attempt-accounting evidence and gaps

Parsed twelve existing stdout JSON receipts, rehashed their actual files and
checked `synthetic_only=true`, `training_authority=false`,
`held_out_data_present=false`, and equal before/after base digests in each.
This is receipt consistency, NOT a fresh execution of those old experiments.

In `results/alc_r0_context_gradient_probe_d4fb2d1_20260929.execution.log`, all
six stdout hashes match the actual stdout files. The recorded wrapper wall
seconds are explicitly manually transcribed terminal stopwatch values.
They are not an automatic launch/terminal journal.

| Historical stdout prefix/cell | Recorded phase nanoseconds | Actual stdout SHA256 |
| --- | ---: | --- |
| context_gradient_probe_d4fb2d1_20260929_512-capsule | 1633938500 | 511776e09f0dfcd96fd786f2f39da7fc01078d3ba7d908c03184fb77a80fcca2 |
| context_gradient_probe_d4fb2d1_20260929_512-q_lora | 764937200 | 6a5a9b419b777bbae7d1aa931bfaf98cabe481b582a86d684c51ff2ed2824bb7 |
| context_gradient_probe_d4fb2d1_20260929_1024-capsule | 1288677100 | 8d09a6cab782f9e38ac482bddd062dd559854134cad247495702324da6a03850 |
| context_gradient_probe_d4fb2d1_20260929_1024-q_lora | 708949900 | c180702fdccbe2a8792de96ef13585873a87463440f546a5b383599e024c1f29 |
| context_gradient_probe_d4fb2d1_20260929_2048-capsule | 1477696100 | 92ecbc5a361a90818049a363cc6aa7ae159b32153327cb4aaf6ac3c908ef5723 |
| context_gradient_probe_d4fb2d1_20260929_2048-q_lora | 3034961500 | f47171b93297b85221d74577032db0444ecb41c2334af459fc688b9242f813d9 |
| synthetic_update_c4f147c_capsule | 3826416300 | dca7d0bf198fa4d3f771078023ae14f2c9e7f20936ecd795d68f8e665577a082 |
| synthetic_update_c4f147c_q_lora | 3664747400 | 4418f92e703a257de8b84290b2bacd5fe322db7ac60a1980aded8559fbf3bcc0 |
| synthetic_update_c4f147c_remount | 722105200 | f68e10aae6702cf5c983d76c0917f5ac1fd98604284e0c662576dd708638cc1f |
| synthetic_update_2048_3966c90_capsule | 9748722800 | 03083a385dddf625af3c7acb5e724f94f43d03edfa1f12d40644bee18473e00d |
| synthetic_update_2048_3966c90_q_lora | 10017682300 | e0cae21caab3a0d6925bfa9a1709d70c5b16130de9add7db82f8e7a51c82ecc8 |
| synthetic_update_2048_3966c90_remount | 1406949500 | 6ff92634fa1fd56daed0e1213a840e2f9dc0e16fc34455e09c6cdcf220317b7c |

Prefix means `results/alc_r0_` + table entry + `.stdout.log`.
Phase field is `elapsed_forward_backward_ns`, `elapsed_updates_ns` or
`elapsed_remount_ns` respectively. Sum: 38295783800ns. **Do not subtract this
sum from600GPU-hours**: it covers partial phases of twelve selected receipts,
not every attempt, loading/verification, failed/interrupted runs, synchronized
GPU activity or wrapper-inclusive elapsed times. Four update receipts each
record16 updates; other eight record0. None proves the new D schedule.

Prompt-budget execution log explicitly records `model_forward_executed=false`;
its five CPU/tokenizer wall timings are not GPU-training consumption.

Filename discovery across tracked results/docs/scripts/src found no named
program budget/attempt ledger. `results/alc_r0/control` has acquisition,
bootstrap and base-digest receipts only. The inspected research `evidence`
directory contains four acquisition/base-digest receipts under526786f/6ad9965,
not a budget ledger. This bounded search does NOT prove no ledger exists in
other directories or historical commits.

Consequently, **remaining measured GPU budget and the first development-job
date are unknown**, not zero consumption or a fresh600-hour allocation.
The original600-hour limit includes invalid/failed/retried/resumed attempts;
45calendar days begin at the first development job, not this audit or the
earliest synthetic diagnostic by inference.

## Next implementation / launch boundary

Continue implementing the exact D worker/launcher; absence of accounting does
not prohibit pure CPU development. Before executing that launcher, reconcile
historical attempt records (including interrupted/failed attempts) into a
verifiable program ledger. Preserve unknown consumption explicitly; do not
invent timestamps, terminal exit codes or full resource measurements from
stdout success fields. Reconstruct missing provenance from the bounded relevant
trajectory/terminal records and Git history before treating it as authority.

Launcher additionally needs: exact frozen source and runtime-origin hashes,
tokenizer-authenticated six fixtures, official no-mount/zero/detach/cache
regressions, CPU/GPU separate18-cell invocations,45min wrapper-inclusive
timeout, exact owned-child handling, append-only reservation/terminal evidence,
worker RSS/private and synchronized CUDA/resource measurements. Independent
exact-byte code/architecture and invocation reviews precede actual execution.

No real host import/forward/backward, optimizer, task training, held-out
evaluation, dependency installation, cleanup or new model launch occurred in
this audit. D/E, scientific R0, durable interaction learning and portable `.alc`
remain OPEN; the full unified objective is unchanged.
