# Self-review spike — results (2026-11-05)

Branch `spike/self-review-experiment`. No kit file changed. Raw run outputs: session scratchpad
(`runA.json`, `runB.json`, `runC.json`, `open_proposals.md`); scorer `check_runs.py`; prompt `MINER_PROMPT.md`.

## E0 — data audit (deterministic)
- `memory/event-trace/`: 223 files, 19,257 records, 0 malformed. `is_error` is false on all 19,257.
- Probe: a Bash call that exits 3 leaves NO trace line. PostToolUse does not fire on a failed tool call.
  => traces hold successful calls only; they cannot show failures. The merge gate's
  `is_error` skip (`pre_bash_block_unsafe_merge.py` `trace_shows_verification`) is dead code but
  harmless: a failed test run never reaches the trace, so the gate still fails closed.
- Hook blocks (pre_* hooks) are not logged anywhere.
- Self-feeding: this session's own analysis calls (grep TASK_REVIEW, P0...) were appended to
  `memory/event-trace/_untagged.jsonl` (6,869 lines). A trace miner would mine itself.

## E1 — two independent miners, same prompt, sonnet, 33 reviews (T200-T252)
| | A | B |
|---|---|---|
| patterns (cap 5) | 5 | 5 |
| citations valid (quote at file:line +-3) | 26/26 | 27/27 |
| tokens / time | 109k / 115 s | 102k / 92 s |

Agreement (task-set Jaccard, best match): 4 of 5 patterns match (0.57-0.75):
memory budget red on main; sibling/stale text left after a change; auto verify finds what
code-review passed; startup reads incomplete. Unmatched: A `guide-files-table-misses-pinned-files`,
B `hook-classifier-evasion-left-open`.
Spot check: memory-budget pattern is live — 5 budget-fix commits to `memory/MEMORY.md`
2026-10-27..2026-11-04.

## E2 — dedupe run C (told the 10 A+B patterns are open)
- Re-proposed: 0 of 10 (all recognised as open).
- New: 3, all citations valid (12/12): lane EXCEEDS noise (14 tasks — larger than any A/B
  pattern), security-review scoped to the wrong diff (3), frozen SHA pin forces merge commit (4).
- => model-judged dedupe stops re-proposals, but a model run on the SAME data always finds
  more. "Second run proposes nothing" only holds if the second run does not call the model:
  termination must come from a deterministic watermark (no review file newer than the last run
  => stop, 0 tokens).
- => one run is a sample of a larger pool (13 distinct patterns over 3 runs); the cap decides
  how much of the pool a run shows.

## Effect on the 5 assumptions
1. Threshold 3 tasks: keep; the pool at >=3 is large (13), so ranking by task count matters more.
2. Cap 3 per run: keep; needed, since every run finds more.
3. Cost: ~100k tokens, ~2 min per sonnet run; budget cap still advised.
4. Input: v1 reads TASK_REVIEW files only. Traces (no failures) and hook blocks (not logged) are
   dropped from v1. This removes loop 1 (self-feeding traces) for v1; the env guard stays for later.
5. Loop guard: deterministic watermark + fingerprint list of open proposals; the model never
   decides whether to run.
