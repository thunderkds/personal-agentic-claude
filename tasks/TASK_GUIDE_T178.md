# TASK_GUIDE — T178: Two tracks — small tasks run on the minimal track without process stops and end with a Decision record; big or risky tasks run on the extended track
**Date**: 2026-10-26
**Complexity Level**: C3
**Risk Level**: High
**Priority**: P1
**Assigned agent**: common-infrastructure
**Agent guide**: `agents/common-infrastructure.md`

> Risk High: changes the doctrine (`AGENTS.md`) every Supervisor session loads, including Hard-Stop Gate 1.
> C3, not split further: the track rule, the minimal track and the Decision record only work together.

---

## Mandatory Startup (Do Not Skip)

1. Read `PROJECT_SPEC.md`
2. Read the memory slice in your spawn prompt; `memory/MEMORY.md` in full only if needed
3. Read this file completely
4. Read `agents/common-infrastructure.md`
5. Read `memory/codebase-map.md` (C3)
6. Read the evidence: `experiments/kit-arms/results/REPORT.md` (round 1) and, on branch `feat/t177-kit-arms-followup`, `experiments/kit-arms/results/round2/REPORT-2.md` and `experiments/kit-arms/arms/minimal-AGENTS.md` (`git show feat/t177-kit-arms-followup:<path>`)

---

## Requirement (Pillar 1 — Adapt the requirement)

Kit-arms experiment (T175–T177): on 6 small tasks, a 26-line `AGENTS.md` scored 12/12 with 3 stops; the full kit scored 12/12 only after 7 stops (5 about its own process) at 2.3× the cost. User, 2026-10-26: "first, for the small task, should automate the flow, and save the decision in the report final. for the big task or implementing or high risk, let create the flow for that, so I image that, we will have 2 ways, 1 is minimal, 2 is the extend for the future, right?" Then: "so when the track 2 is run, supervisor will decide to run, right?" (answer: yes, by fixed rules, announced in one line, the user can override).

**Restated intent**:
> The Supervisor sorts every implementation request into one of two tracks by fixed rules and says which
> in one line. The **minimal track** (small, low-risk work) runs straight through — test first, change,
> real run — with no process stop, and ends with a **Decision record** of what was decided and checked.
> The **extended track** (big, risky, multi-session work) is today's full 5-stage pipeline, unchanged.

Supervisor design decisions (defaults the user can overrule before the build):
- D1 — **Track rule.** Extended track if **any** of: Complexity C2 or above; Risk Medium or High; a Gate-2 word (*refactor*, *restructure*, *migrate to pattern*, *clean architecture*, *QA suite*, *test coverage*) or *migrate*; the work clearly spans more than one session or more than one agent; a UI component (Gate 6 evidence does not fit a Decision record). Otherwise minimal track.
- D2 — **Announcement.** Before any work: `Track: minimal — <reasons>` or `Track: extended — <reasons>`. The user can reply `full` or `minimal` to switch. The Supervisor may move a task **up** (minimal → extended) mid-task when it finds a D1 condition, and says so; it never moves a task **down** on its own.
- D3 — **Who writes the code on the minimal track.** The Supervisor itself, in one context, as the experiment's minimal arm did. Hard-Stop Gate 1 ("no TASK_GUIDE = no work", "never write implementation code directly") is amended to apply to the extended track only. This is the largest doctrine change in the task.
- D4 — **Minimal-track flow.** Register a task ID and set the active-task state; work on a new branch, never on `main`; test first (Gate 5 still holds: a new test plus its passing output); change; run the program the way a user would; append the Decision record; add one board row. The only stop: when the request itself is unclear (one question, then stop — the line that won the experiment). No task guide, no sub-agent, no Stage 4 skills. Merge is never automatic.
- D5 — **Decision record.** Appended, newest first, to `tasks/MINIMAL_LOG.md`. Fields: ID, title, track; `Asked:` (the request, verbatim); `Decisions:` (each decision with its reason; an assumption starts with `Assumed:`); `Checked:` (the new test's name and result, the suite result, the real-run command and what it printed); `Files:`; `Not done:` (always includes merge). The same block is the Supervisor's final chat message.
- D6 — **`AGENTS.md` stays ≤200 lines** (`tests/test_agents_md_primary.py`). The full rule and the minimal-track flow go in a new `docs/claude-md/tracks.md`; `AGENTS.md` gets the short rule and a pointer.

**Out of scope**: auto mode, i.e. removing the remaining stops on either track (T180); the Debate (T179); any change to the extended track's stages.

**Requirement Refs**: none in `PRD.md` (framework doctrine change; the evidence is the kit-arms reports).

### Requirement Fidelity Gate

- [x] Restated intent confirmed (Supervisor, 2026-10-26, from the user's two messages above)
- [x] Domain terms: add **Minimal track**, **Extended track**, **Decision record** to the `PROJECT_SPEC.md` glossary (agent; done in AC 5, block after the `Lane` row)
- [x] Every AC traces to the Requirement
- [x] Refs covered (none)

---

## Dependencies & Reachability

**Depends on**: None
**Entry point**: `docs/claude-md/tracks.md`

---

## Acceptance Criteria

| # | Criterion (testable) | Traces to requirement |
|---|----------------------|-----------------------|
| 1 | `docs/claude-md/tracks.md` states the D1 rule as a table (each condition → extended), the D2 announcement shape with both literal examples, the up-only switch, and the D4 minimal-track flow as numbered steps. | D1, D2, D4 |
| 2 | `AGENTS.md` has a `## Tracks` section (≤12 lines) with the D1 rule in short form and a pointer to `docs/claude-md/tracks.md`; Hard-Stop Gate 1 says it applies to the extended track; `AGENTS.md` stays ≤200 lines and ≤32,768 bytes. | D3, D6 |
| 3 | `templates/MINIMAL_LOG_template.md` holds the D5 record with every field; `tasks/MINIMAL_LOG.md` is created on first use from it, newest record first. | D5 |
| 4 | The pipeline doc (`docs/claude-md/pipeline-stages.md`) says the 5 stages are the extended track, and Gates 2–6 still apply to it unchanged. Gate 5 (a new test with pasted output) also applies to the minimal track, through the record's `Checked:` field. | D3, D4 |
| 5 | The glossary in `PROJECT_SPEC.md` defines Minimal track, Extended track and Decision record, each with a "Not …" line where a near-synonym exists (e.g. Decision record is not the Decision Log of board mode `online`). | terms |
| 6 | Hooks: a minimal-track task has no guide, so the agent reads `pre_bash_block_unsafe_merge.py`, `pre_agent_step_limit.py`, `post_write_register_task.py` and `stop_review_reminder.py` and states, with a test for each, how each behaves for a task with no guide. The merge gate must not get weaker: a merge of a minimal-track branch still needs the user. | D4, Risk |
| 7 | Tests (`tests/test_tracks.py`) pin AC 1–6: the rule's conditions, both announcement examples, the record's fields, the amended Gate 1, the line/byte caps, and the merge-gate behaviour. The full suite stays green. | Gate 5 |
| 8 | Live check, **after the user's go, paid, cap $3**: 2 headless runs of the updated kit in the T175 Docker sandbox (`experiments/kit-arms/`): fixture task 2 (comma bug) → announces minimal, makes no process stop, passes the task-2 oracle, and writes a Decision record with every field; fixture task 5 (CSV→JSON) → announces extended. | user request |

---

## Evaluation & Acceptance

### Success Criteria

| # | Given | Expect | How |
|---|-------|--------|-----|
| 1 | doctrine after the change | `## Tracks` present, Gate 1 scoped to extended, ≤200 lines | test |
| 2 | `templates/MINIMAL_LOG_template.md` | fields ID/title/track, Asked, Decisions, Assumed, Checked, Files, Not done | test |
| 3 | merge of a branch whose task has only a Decision record | still blocked without the user | test (stubbed hook input) |
| 4 | task 2 "comma bug" run (paid) | `Track: minimal`, 1 turn, oracle pass, record written | run |
| 5 | task 5 "CSV→JSON" run (paid) | `Track: extended` | run |

### Verification Command

```bash
python3 -m pytest -q tests/test_tracks.py tests/test_agents_md_primary.py tests/test_claude_md_slim.py && python3 -m pytest -q tests
```

### Evidence

> **Moved.** Filled in `tasks/TASK_REVIEW_T178.md`.

---

## Demonstration

> **Moved.** See `tasks/TASK_REVIEW_T178.md`.

---

## Approach

**Pattern reference**: `docs/claude-md/pipeline-stages.md` + its pointer in `AGENTS.md` (how detail moves out of the doctrine under the 200-line cap); `experiments/kit-arms/arms/minimal-AGENTS.md` (the minimal rules that worked — reuse its wording for the minimal-track steps).
**Vital slice**: the track rule + announcement (AC 1–2), the record template (AC 3), the Gate-1 amendment (AC 2, 4).
**Cut list**: a hook that enforces the track choice (the choice is the Supervisor's judgment; the record makes it auditable); auto mode (T180); a site page.

---

## Edge Case Checklist

- [ ] A request that matches the minimal track but names a risky file (a migration, auth, a delete) → extended (D1 risk).
- [ ] The user says `minimal` for a High-risk task → the Supervisor complies, says the risk in one line, and the record notes "track set by the user".
- [ ] A minimal-track task grows past one file or one session → move up, say so, write the task guide from what was learned.
- [ ] A question about a fact in the code, not about what the user wants, is not a stop: the Supervisor reads the code (the stop is only for an unclear request).
- [ ] `tasks/MINIMAL_LOG.md` does not exist yet → create it from the template.
- [ ] Board mode `online`: the record still goes to `tasks/MINIMAL_LOG.md`; the board row goes through `board_sync.py` as today.

---

## Files to Change (Predicted)

| File | Change |
|------|--------|
| `AGENTS.md` | `## Tracks` section; Gate 1 scoped to the extended track |
| `docs/claude-md/tracks.md` | new: rule, announcement, minimal-track flow |
| `docs/claude-md/pipeline-stages.md` | the 5 stages = extended track |
| `templates/MINIMAL_LOG_template.md` | new: Decision record |
| `PROJECT_SPEC.md` | glossary terms |
| `.claude/hooks/*.py` | only if AC 6 finds a hook that blocks or nags a minimal-track task wrongly |
| `tests/test_tracks.py` | new |

## Files Must NOT Touch

| File | Reason |
|------|--------|
| `experiments/kit-arms/` | frozen experiment |
| `skills/resolve-question/` | T179 |
| the extended track's stage content | out of scope |

---

## Completion Checklist

- [ ] Build + tests (agent)
- [ ] Stage 4: code-review, security-review (High risk)
- [ ] User go → AC 8 paid live check (Supervisor)
- [ ] `verify` (user-only)
- [ ] Merge only when the user asks

---

## Questions Log
