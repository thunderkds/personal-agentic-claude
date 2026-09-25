# TASK_GUIDE — T126: The Supervisor can see its own context size — compact-advisor decides on a measurement, not a feeling
**Date**: 2026-09-25
**Complexity Level**: C1
**Risk Level**: Low — read-only measurement fed into an advisory skill; nothing compacts automatically
**Priority**: P1
**Assigned agent**: Common-Infrastructure-Agent
**Agent guide**: `agents/common-infrastructure.md`

---

## Mandatory Startup (Do Not Skip)

Before writing any code:
1. Read `PROJECT_SPEC.md`
2. Read `memory/MEMORY.md` (or the memory slice in your spawn prompt, once T125 has shipped)
3. Read this file completely
4. Read `agents/common-infrastructure.md`
5. Note the **Complexity Level** above and apply the matching process from the Complexity matrix in your role guide
6. Read `docs/token-focus-finding-2026-09-25.md` § 1–2 and `skills/compact-advisor/SKILL.md`

---

## Requirement (Pillar 1 — Adapt the requirement)

User, 2026-09-25: keep each agent *"focus on the request, no overwhelm of content"*; *"yes, let do the best"*.

**Measured** (finding doc; Supervisor sessions only): Supervisor sessions are **92%** of spend. Their
median API call carries **120k tokens** of context, and **34%** of their calls carry more than 150k.
`compact-advisor` today says *"no tool exposes your own context size… never claim a precise number"* —
true when written, and the reason its verdict is a feeling. The transcript of the running session
records every call's size, so the number exists.

**Restated intent:**
> When the Supervisor (or the user via `/compact-advisor`) asks whether to compact, the answer starts
> from the live session's measured context size and what fills it — "180k tokens, 40% Bash output" —
> and the existing judgment signals decide the verdict. Nothing compacts on its own.

**Out of scope:**
- Automatic compaction or any hook that triggers it (both remain user-invoked).
- A token threshold that forces a verdict — the number informs; `CLAUDE.md`'s self-monitoring rule stays a judgment call.
- Changing what the Supervisor reads at session start (`wake`, `CLAUDE.md`).
- Spawned agents (T125).

**Requirement Refs**: no `PRD.md` — N/A. Traces to the user's messages and DDR-0009 § Decision 2.

### Requirement Fidelity Gate (sign off BEFORE implementation)

- [x] Restated intent confirmed to match the user's request (2026-09-25)
- [x] Domain terms align: *live session*, *context size*, *composition*, `/compact` vs `compact-memory`
- [x] Every Acceptance Criterion below traces to a line in the Requirement
- [x] Requirement Refs: N/A (no PRD) — recorded, not skipped

> An agent must NOT start implementing until this gate is checked. If anything here is unclear,
> STOP and ask the Supervisor (Karpathy: Think Before Coding).

---

## Dependencies & Reachability

**Depends on**: T124 — `scripts/token_meter.py --session` and `--json` must exist

**Entry point**: `skills/compact-advisor/SKILL.md` (step 2a) → `python3 scripts/token_meter.py --current --json`

---

## Acceptance Criteria

| # | Criterion (testable) | Traces to |
|---|----------------------|-----------|
| 1 | `token_meter.py --current` resolves the running session's transcript: the most recently modified top-level `*.jsonl` in `<projects-dir>/<slug>/`, where `<slug>` is the absolute working directory with every `/` and `.` replaced by `-` (verify the rule against real directory names before relying on it). Not found → exit 2 naming the directory it looked in | "the number exists" |
| 2 | `--current` accepts `--cwd DIR` for tests and for a worktree; it never scans other projects | scoped |
| 3 | `--session`/`--current` output adds `context_now` (last call), `context_peak`, `calls_over_150k`, and the top three content kinds by carry share — aggregates only (T124 AC8 holds) | "what fills it" |
| 4 | `compact-advisor` step 2a starts by running `python3 scripts/token_meter.py --current --json` and quoting `context_now` and the top content kind; if the command fails, it says so in one line and falls back to the judgment signals. The "no tool exposes your own context size" sentence is replaced with the truthful statement | measurement, not feeling |
| 5 | The verdict remains judgment: the skill names 150k as a **reference point** ("a third of past Supervisor calls ran above it"), not a trigger; one verdict, one reason, one action (its Simplicity rule) is kept | CLAUDE.md self-monitoring rule |
| 6 | `CLAUDE.md`'s self-monitoring paragraph is edited only if it states the number is unknowable; otherwise untouched | Surgical |

**Evaluation window (after Done, recorded in DDR-0009 follow-up — not a Done blocker):** the next ≥ 5
Supervisor sessions. **Target:** share of Supervisor calls above 150k context falls from **34%** to
≤ 25%. **Quality guard:** no increase in "lost an earlier decision" corrections noted by the user.

---

## Evaluation & Acceptance (How we know the agent worked correctly)

### Success Criteria (observable, pass/fail)

| # | Given | Expect | How checked |
|---|-------|--------|-------------|
| 1 | tmp projects dir with `<slug>/a.jsonl` (older) and `<slug>/b.jsonl` (newer), `--cwd` mapping to `<slug>` | `--current` reports `b` | pytest via subprocess |
| 2 | A `subagents/` file newer than both | still reports `b` (top-level only) | pytest |
| 3 | No matching slug dir | exit 2, message names the path looked in | pytest |
| 4 | Fixture with calls of 100k, 160k, 170k context | `context_now` 170k, `context_peak` 170k, `calls_over_150k` 2 | pytest |
| 5 | Sentinel content in fixture | absent from output | pytest (extends T124 SC5) |
| 6 | `skills/compact-advisor/SKILL.md` | names the command, keeps the fallback, no longer claims the size is unknowable, calls 150k a reference not a trigger | structural pytest |

**Mutation controls:** **M1** — pick the oldest file → SC1 RED. **M2** — include `subagents/` → SC2 RED. **M3** — restore the "no tool exposes" sentence → SC6 RED.

### Verification Command (exact, runnable)

```bash
python3 -m pytest tests/test_token_meter.py tests/test_compact_advisor_measures.py -q
python3 -m pytest .claude/hooks/tests tests -q | tail -3
python3 scripts/token_meter.py --current        # in a live session: prints this session's size
```

### Evidence (filled by reviewer at Stage 4/5)

> **Moved.** Filled by the reviewer at Stage 4/5 in `tasks/TASK_REVIEW_T126.md`.

---

## Demonstration

> **Moved.** See `tasks/TASK_REVIEW_T126.md`. BEFORE: compact-advisor's step 2a verbatim. AFTER:
> `/compact-advisor` in a live session quoting a measured `context_now`.

---

## Approach

**Pattern reference**: T124's `scripts/token_meter.py` (extend, don't fork); `skills/compact-advisor/SKILL.md` (keep its shape and length).

**Vital slice**: AC1, AC3, AC4.

**Cut list**: statusline integration; a hook that warns at a threshold; per-turn trend output; `wake` reporting the last session's size.

---

## Edge Case Checklist

- [ ] Slug rule for paths containing `.` or `_` — confirm against the real `~/.claude-personal/projects/` names
- [ ] Two sessions open in the same project — newest-modified is a heuristic; say so in the output
- [ ] Transcript written mid-call (last line partial) — skipped as malformed, counted (T124 AC10)
- [ ] `CLAUDE_CONFIG_DIR` unset → `~/.claude/projects`

---

## Files to Change (Predicted)

| File | Change |
|------|--------|
| `scripts/token_meter.py` | `--current`, `--cwd`, extra session fields |
| `tests/test_token_meter.py` | SC1–5 |
| `tests/test_compact_advisor_measures.py` | **New.** SC6 |
| `skills/compact-advisor/SKILL.md` | Step 2a + the Ask-vs-Guess sentence |

## Files Must NOT Touch

| File | Reason |
|------|--------|
| `.claude/hooks/**`, `.claude/settings.json` | No hooks — nothing triggers compaction |
| `skills/compact-memory/**` | Different mechanism |
| `memory/*` | Supervisor-only writes |

---

## Test Plan

1. `tdd`: SC1–6 first. 2. Implement. 3. M1–M3 RED/GREEN pasted. 4. User-run `/verify`: `/compact-advisor` in a live session.

---

## Completion Checklist

- [ ] Implementation done
- [ ] Self-review: `Skill({ skill: "code-review" })` run
- [ ] Security review: not required (Risk Low)
- [ ] Tests written AND pass — output pasted into `tasks/TASK_REVIEW_T126.md` Evidence (Hard-Stop Gate 5)
- [ ] M1–M3 pasted
- [ ] `/verify` — user-run
- [ ] UI Evidence rows: ☐ N/A — no UI component
- [ ] Supervisor notified: task ready for Stage 4 review
