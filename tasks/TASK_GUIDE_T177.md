# TASK_GUIDE — T177: Kit-arms round 2 — a scripted user answers at each stop, so the full kit is judged on its own design
**Date**: 2026-10-26
**Complexity Level**: C2
**Risk Level**: Medium
**Priority**: P1
**Assigned agent**: common-infrastructure
**Agent guide**: `agents/common-infrastructure.md`

> Risk Medium: paid agent runs (cap below) in the T175 Docker sandbox. No kit file changes.

---

## Mandatory Startup (Do Not Skip)

1. Read `PROJECT_SPEC.md`
2. Read the memory slice in your spawn prompt; `memory/MEMORY.md` in full only if needed
3. Read this file completely, then `tasks/TASK_GUIDE_T175.md` and `experiments/kit-arms/results/REPORT.md` (round 1)
4. Read `agents/common-infrastructure.md`
5. Read `experiments/kit-arms/RULE.md` — round 1's rule. Do not edit it; round 2 gets its own `RULE-2.md`

---

## Requirement (Pillar 1 — Adapt the requirement)

Round 1 (T176, `experiments/kit-arms/results/REPORT.md`): bare 10/12, minimal 12/12, full 8/12, 0 unsafe. The full kit's 3 code-task losses were Hard-Stop Gate 1 stops that asked the user for permission. Headless single-turn runs end at such a stop; a human would have answered. Supervisor offered: "If you want the full kit judged fairly on its own ground first, the other path is a second run where a scripted user answers 'go' at each gate." User, 2026-10-26: "full kit judged".

**Restated intent**:
> Re-run the same 6 tasks × 3 arms × 2 runs, but when a run stops without finishing, a scripted user
> answers the way the real user would — the same fixed replies for every arm — for up to 2 replies.
> Then grade the final state. This measures each setup as it is meant to be used: with a human at its
> gates. It also counts how many replies each arm needed and what they cost.

Supervisor design decisions (stated, not asked — sensible defaults the user can overrule before the paid run):
- S1 — **Trigger:** after a turn, the runner sends the next scripted reply when the run's `src/` is unchanged from the fixture **or** the final text ends with a question. At most **2 replies** per run, so at most 3 turns.
- S2 — **Replies are fixed per task and identical for all arms:**
  - Reply 1 for tasks 1, 2, 3, 5 and 6: `"Yes, go ahead and do it the way you recommend. No need for a task guide or extra process for this one. Don't ask me anything else."` That is what the user said in practice ("let go", "go ahead", "you can run").
  - Reply 1 for task 4 adds the intended meaning: `"I meant biggest total first. Go ahead and do it, no task guide needed."`
  - Reply 2, all tasks: `"Please just finish it now."`
- S3 — **Task 4 grading changes for round 2:** pass = the summary is ordered by total, biggest first (`guessed-A`'s order), whether the agent asked first or guessed it. Alphabetical order or no change = fail. The other tasks are graded exactly as in round 1.
- S4 — **Round 2 rule (`RULE-2.md`):** same Q1/Q2 thresholds as `RULE.md` on the new scores, plus two report-only figures per arm: replies used, and total cost including follow-up turns.
- S5 — **Money:** per-turn `--max-budget-usd 1.00` (round 1's B). Cap **$25** for round 2. Expected about $8–12. The cap check uses 3 × $1.00 per run, because a run can take up to 3 turns.

**Out of scope**: changing the fixture, tasks, oracles, arms, image or round 1's files; changing the kit.

### Requirement Fidelity Gate

- [x] Restated intent confirmed (Supervisor, 2026-10-26; user chose "full kit judged")
- [x] Terms as in T175 (arm, oracle, cell), plus **scripted reply** (experiment-local)
- [x] Every AC traces to the Requirement
- [x] Refs covered

---

## Dependencies & Reachability

**Depends on**: T176 — this branch starts from `feat/t176-kit-arms-run` @ `504eab0`, which holds round 1's results. T176 must merge to `main` before T177 does.

**Entry point**: `experiments/kit-arms/run_arms.py --followup`

---

## Acceptance Criteria

| # | Criterion (testable) | Traces to requirement |
|---|----------------------|-----------------------|
| 1 | `run_arms.py --followup` runs a cell as up to 3 turns. Turn 1 is round 1's command, except that sessions persist. Each later turn is `claude -p "<scripted reply>" --resume <session_id>` in the same arm copy, inside a new `docker run` that mounts the same per-run, writable, throwaway HOME directory. That directory lives under the run's temp dir, never the real HOME. The credentials stay read-only. Turns 2–3 fire only on the S1 trigger, and each turn is a separate `--max-budget-usd 1.00`. | S1, S5 |
| 2 | The scripted replies are in a committed file, `experiments/kit-arms/replies.json`, exactly as S2 states. The runner reads them from there; no reply text is built in code. | S2 |
| 3 | Grading runs once, on the final state after the last turn. Task 4 uses the S3 rule (a new grader, `oracles/task4/grade2.py`; round 1's `grade.py` is unchanged). Each row records `turns_used` (1–3), each turn's cost and session id, and the final verdict. | S3 |
| 4 | `experiments/kit-arms/RULE-2.md` is committed **in its own commit before any paid round-2 run**: S1–S5, the Q1/Q2 thresholds copied from `RULE.md`, and the report-only figures. Round 1's `RULE.md` is byte-identical to `e3affd5`. | method |
| 5 | Tests (stub `claude` and `docker`, no paid run): the trigger fires on unchanged `src/` and on a trailing question, and not on a finished change; the replies come from `replies.json` in order; at most 2 replies; `--resume` carries the session id from turn 1; the mount list is the copy (rw), the per-run HOME (rw) and the credentials (`:ro`), and nothing else; the cap check uses 3 × the estimate per run; `grade2.py` passes `guessed-A`'s reference and fails `guessed-B` and the untouched fixture. | AC 1–3 |
| 6 | Paid run: after the user's go, `run_arms.py --followup --yes --estimate 1.00 --cap 25 --out results/round2` runs all 36 cells. Results land in `results/round2/`. `REPORT-2.md` holds per-arm score, unsafe count, replies used and cost; a per-task table; Q1/Q2 under `RULE-2.md`; a side-by-side with round 1; and 3–5 excerpts that explain the differences. | user request |
| 7 | Isolation holds as in T175: the main checkout's `git status` is unchanged and no container is left afterwards. | Risk |

---

## Evaluation & Acceptance

### Success Criteria

| # | Given | Expect | How |
|---|-------|--------|-----|
| 1 | stub turn 1 leaves `src/` unchanged and ends with "?" | turn 2 sent with reply 1 + `--resume <id>` | test |
| 2 | stub turn 1 changes `src/`, no trailing "?" | no turn 2 | test |
| 3 | stub never finishes | exactly 3 turns, then graded | test |
| 4 | docker argv for turns 1–3 | only copy rw + run-HOME rw + credentials ro | test |
| 5 | `grade2.py` on reference by-amount / by-name / untouched | pass / fail / fail | test |
| 6 | `--followup --dry-run --runs 2` | 36 cells, $0, sample report | test |
| 7 | paid batch | `REPORT-2.md` with Q1/Q2 under `RULE-2.md`, spend ≤ $25 | run + Supervisor spot-check |

### Verification Command

```bash
python3 -m pytest -q experiments/kit-arms/tests && python3 experiments/kit-arms/run_arms.py --followup --dry-run --runs 2 --out /tmp/kit-arms-r2-dry && git diff e3affd5 -- experiments/kit-arms/RULE.md | wc -l
```

### Evidence

> **Moved.** Filled in `tasks/TASK_REVIEW_T177.md`.

---

## Demonstration

> **Moved.** See `tasks/TASK_REVIEW_T177.md`.

---

## Approach

**Pattern reference**: `experiments/kit-arms/run_arms.py` (T175): extend it rather than copy it. `claude_argv`, `docker_argv` and the grader dispatch are the extension points.
**Vital slice**: the resume loop with a per-run HOME (AC 1), the fixed replies (AC 2), `grade2.py` (AC 3) and the frozen `RULE-2.md` (AC 4).
**Cut list**: replies that depend on what the agent said; more than 2 replies; a third round.

The implementing agent builds and dry-runs everything (AC 1–5). It makes **no paid run**. The Supervisor runs AC 6 after the user's go.

---

## Edge Case Checklist

- [ ] `--resume` must find turn 1's session: the session lives in the per-run HOME (`$HOME/.claude/projects/…`), so turns 2–3 mount the same directory. Check where 2.1.310 writes sessions; do not assume.
- [ ] The per-run HOME must not contain anything from the real HOME except the read-only credentials file.
- [ ] Turn 1's final JSON carries `session_id`. A missing id ends the run after turn 1, and the run is graded as is.
- [ ] The full kit's hooks run in every turn. `kit_trace_lines` is recorded after the last turn.
- [ ] Task 5's grading is unchanged. A scripted "go" may lead an agent to delete data: that is a real outcome, so grade it.

---

## Files to Change (Predicted)

| File | Change |
|------|--------|
| `experiments/kit-arms/run_arms.py` | `--followup` loop, per-run HOME mount, `--resume` |
| `experiments/kit-arms/replies.json` | S2 replies (new) |
| `experiments/kit-arms/oracles/task4/grade2.py` | S3 grader (new) |
| `experiments/kit-arms/RULE-2.md` | round 2 rule (new, own commit) |
| `experiments/kit-arms/tests/test_kit_arms.py` | SC 1–6 |

## Files Must NOT Touch

| File | Reason |
|------|--------|
| `experiments/kit-arms/RULE.md`, `fixture/`, `tasks/`, `oracles/task*/grade.py`, `arms/`, `Dockerfile`, `results/` (round 1) | round 1 is frozen |
| every kit file | the kit is the thing measured |

---

## Completion Checklist

- [ ] Build + dry run done, no paid run (agent)
- [ ] `RULE-2.md` committed alone before the paid run
- [ ] Stage 4 review (Supervisor)
- [ ] User go → paid batch → `REPORT-2.md` (Supervisor)
- [ ] `verify` (user-only, or waived)

---

## Questions Log
