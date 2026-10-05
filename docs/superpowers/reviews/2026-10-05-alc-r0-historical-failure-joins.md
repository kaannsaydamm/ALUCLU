# Checkpoint175: original failed GPU suite and subsequent terminal joins

Parent 7b8116c5087e39fc231e91071c44acfbe1e7e2e6. Read-only reconstruction on
2026-10-05 in authoritative Desktop checkout; no historical command executed.
This extends checkpoint174's discovery, not measured GPU accounting or approval.

## Primary observations

Bounded private-session record search recovered four original terminal
event_msg/item_completed/CommandExecution records from 2026-09-25. The same
private session path is recorded in checkpoint174's discovery report. Search
the exact four execution IDs below, parse the original JSON and emit only the
selected metadata or relevant failure/summary lines. Never export the session.

| CommandExecution id | Completion event UTC | Tool handle | Exit | Command seconds | Pytest terminal summary |
| --- | --- | --- | ---: | ---: | --- |
| exec-b68ee095-e91e-451a-97f5-37be5dfcdd25 | 2026-09-25T18:34:16.710Z | 71949 | 1 | 468.864998300 | 2 failed, 259 passed in 451.41s |
| exec-0f8b4b2a-9186-452e-9a76-2c0c508f3fa7 | 2026-09-25T18:37:14.263Z | 51732 | 0 | 102.971501800 | 2 passed in 99.25s |
| exec-d08b7597-ac30-4d8e-b868-511dd7f0b004 | 2026-09-25T18:40:10.003Z | 24754 | 0 | 140.400253800 | 261 passed in 137.28s |
| exec-2a735fd9-dd34-4ce9-925b-6a15f197e51b | 2026-09-25T18:53:30.151Z | 64473 | 0 | 580.916381200 | 261 passed in 576.24s |

The first record has status failed; subsequent records have status completed.
All four commands use the historical Windows research venv python.exe with
PYTHONPATH resolved to src. Historical cwd is
C:\Users\kaann\OneDrive\Desktop\03_Projeler_Arge\ALUCLU\.worktrees\unified-lifelong-cognition.
That is historical provenance, NOT the current working directory or permission
to mutate the old checkout. Current work remains in the Desktop local worktree.
The three full suites enumerate test_alc_r0_*.py and invoke pytest -o addopts='' -q.
The targeted rerun selects exactly these two failed test names:

- tests/test_alc_r0_host_wrapper.py::test_two_fresh_gpu_processes_reproduce_full_forward_matrix
- tests/test_alc_r0_run_matrix.py::test_tracked_matrix_is_reproducible_from_exact_plan_bytes

Original failed output asserts first.returncode == 0, then reports first child
returncode 1 and torch.AcceleratorError: CUDA error: out of memory. It also
reports run_matrix.py ValueError while reproducing the matrix from exact plan
bytes. This corroborates the two failures recorded in historical trajectory23;
the later clean suites do not erase the failed invocation or its resource cost.
No new claim about the cause of the intermittent CUDA OOM is established.

## Bounded output roots and interpretation

These are SHA256 of UTF-8 encoding of the decoded aggregated_output string,
without newline normalization, NOT the entire session file or raw JSON line.
They identify retained tool output content, not authenticated measurements.

| CommandExecution id | Output UTF-8 bytes | Output SHA256 |
| --- | ---: | --- |
| exec-b68ee095-e91e-451a-97f5-37be5dfcdd25 | 7486 | 648b2de8903178b064505d1f658d4fda5764f865e7f18348f68f00c042bc20e4 |
| exec-0f8b4b2a-9186-452e-9a76-2c0c508f3fa7 | 111 | 7d06d2189e8c0ad75a7cb94f5294567be33e19775bdebb6703a84292192c6b29 |
| exec-d08b7597-ac30-4d8e-b868-511dd7f0b004 | 357 | e1f56c92506a8a0a9a44be6c25f9e20d20c7769444e39f107e1d0a78a0bd3da3 |
| exec-2a735fd9-dd34-4ce9-925b-6a15f197e51b | 357 | 0f5986a439396c3fba6dd4b29365feb919dc380f78fd619b5d87c914ebffb260 |

Command duration sum is 1293.153135100 seconds. This is shell/tool wall time,
not measured GPU consumption. Pytest durations differ and must stay separate.
The nested CommandExecution items do not contain started_at_ms/completed_at_ms;
the original enclosing event payloads DO contain both numeric fields:

| CommandExecution id | Payload started_at_ms | Payload completed_at_ms |
| --- | ---: | ---: |
| exec-b68ee095-e91e-451a-97f5-37be5dfcdd25 | 1790360787791 | 1790361256709 |
| exec-0f8b4b2a-9186-452e-9a76-2c0c508f3fa7 | 1790361331291 | 1790361434263 |
| exec-d08b7597-ac30-4d8e-b868-511dd7f0b004 | 1790361469596 | 1790361609996 |
| exec-2a735fd9-dd34-4ce9-925b-6a15f197e51b | 1790361829230 | 1790362410149 |

Preserve original envelope timestamps; do not reconstruct them by subtraction.
These tool-envelope values and completion event timestamps are not authenticated
OS process start/end receipts or measured GPU occupancy. The initial draft's
record-wide absence claim was wrong because it inspected only the nested item;
independent review caught this and the original envelope fields were revalidated.
Tool handles are not operating-system PIDs authorized for termination.
Commands do not select --junitxml; no new XML or skip/error breakdown is inferred
from their textual summaries. Historical current-source/runtime compatibility
and the exact tree contents at each execution require separate joins.

This closes terminal identity/output gaps for one failed full suite, its targeted
rerun and two successful full suites. It does not prove complete attempt coverage,
first development instant, measured cumulative GPU hours or resource admission.
All original limits, frozen scientific grid and remaining launch gates stand.
No training, learning PASS, R0 PASS, budget reset or program completion follows.
