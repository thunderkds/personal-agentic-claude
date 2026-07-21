# TASK_GUIDE — T040: Derive the Token Audit Log from event-trace instead of manual entry; restart the DDR-0001 window
**Date**: 2026-07-21
**Complexity Level**: C1
**Risk Level**: Medium
**Priority**: P1
**Assigned agent**: Common-Infrastructure-Agent
**Agent guide**: `.claude/agents/common-infrastructure.md`

---

## Mandatory Startup (Do Not Skip)

1. Read `PROJECT_SPEC.md`
2. Read `memory/MEMORY.md` (pasted into your spawn prompt — do not re-read if present)
3. Read this file completely
4. Read `.claude/agents/common-infrastructure.md`
5. Read `docs/ddr/0001-measure-first-token-refactor.md`, `reports/token-audit_2026-07-17.md`, and `.claude/hooks/post_tool_trace.py` in full

---

## Requirement (Pillar 1 — Adapt the requirement)

DDR-0001 opened a baseline Token Audit Log on 2026-07-17, logged by a **manual per-session
convention** (deliberately no hook — Simplicity First). DDR-0001 explicitly accepted the risk:
*"forgotten entries degrade the data."* That risk materialised within two days.

Measured state on 2026-07-21 (day 4 of a 14-day window):

| DDR-0001 requires | Actual |
|---|---|
| 7 logged sessions, or 14 days | 1 session logged |
| Entry at every cold-start / stage transition / spawn | last entry dated 2026-07-17 |
| `/cost` at session end as ground truth | never logged, not once |

Meanwhile T029, T034, T035, T036, T037 and T038 were all merged on 2026-07-19 across multiple
sessions, producing **zero** audit entries. The instrument cannot yield the baseline it was built
for, so T030 is blocked on data that will never arrive.

**Restated intent**:
> Replace the manual logging convention with one that does not depend on anyone remembering, and
> reopen the measurement window from a date where the data will actually be complete.

**Hard constraint — read before designing anything.** Claude Code hooks do **not** receive token
counts, and `/cost` is a slash command no hook can capture. Full automation of the *token numbers*
is therefore impossible. What is automatable is the **event stream** — cold-start, stage transition,
spawn — each with its task tag and model tier. The `/cost` ground-truth line stays a manual paste at
session end. Do not attempt to synthesise or estimate token counts; a fabricated number is worse
than a missing one.

**Out of scope**:
- Estimating, inferring, or computing token counts from anything
- Adding a new always-on hook (see Approach — explicitly rejected)
- Analysing the data or choosing a refactor — that is T030
- Editing `CLAUDE.md`, `general-agent-template.md`, or `post_write_register_task.py` (T039/T041/T042)

**Requirement Refs**: no `PRD.md`. Traceability:
- **DDR-0001** — defines Token Audit Log, Measurement Window, entry format, window-close condition
- **User directive 2026-07-21** — chose "Automate logging, restart window" over superseding DDR-0001

### Requirement Fidelity Gate (sign off BEFORE implementation)

- [x] Window failure verified by Supervisor against `reports/token-audit_2026-07-17.md` (1 session, no `/cost`)
- [x] User chose to amend DDR-0001, not supersede it — the measure-first decision stands
- [x] Every Acceptance Criterion traces to the Requirement

---

## Dependencies & Reachability

**Depends on**: **T043 — trace task-attribution must be trustworthy before entries are derived from it.**
> Verified 2026-07-21: this session's records were filed under T001, T012, T017, T028, T029, T030 and
> T038 — all Done or untouched. `post_tool_trace.py:find_task_id` returns the first `T\d{3}` found in
> the combined tool input + response, so *reading* `PROJECT_KANBAN.md` or `memory/MEMORY.md` files the
> record under whichever task ID appears earliest in that file's text. DDR-0001's cost mapping is
> "session `/cost` split proportionally across that session's tagged entries" — with wrong tags, the
> derived log is confidently wrong, which is worse than the manual log that merely stopped.
> Do not implement T040 against the current tagging. If T043 is not done, STOP and tell the Supervisor.

**Entry point**: `scripts/token-audit.sh`
> The generator invoked to refresh the audit log from trace data.

---

## Acceptance Criteria

| # | Criterion (testable) | Traces to |
|---|----------------------|-----------|
| 1 | `scripts/token-audit.sh` reads `memory/event-trace/*.jsonl` and emits entries in DDR-0001's exact format: `<date> \| <event> \| <task-tag> \| <cache> \| <model-tier> \| <notes>` | "replace the manual convention" |
| 2 | `Agent` tool calls in the trace emit `spawn` events; `Skill` calls for `wake` emit `cold-start`; `Skill` calls mapping to a pipeline stage emit `stage-N` | DDR-0001 event vocabulary |
| 3 | Records in `_untagged.jsonl` (no discoverable Task ID) emit with tag `overhead`, not dropped | DDR-0001: task-tag is mandatory |
| 4 | `reports/token-audit_2026-07-21.md` exists, carries the DDR-0001 header (window-close condition, entry format), and opens the new window at 2026-07-21 | "reopen the window" |
| 5 | The generator is **idempotent** — running it twice produces no duplicate entries | correctness |
| 6 | **Negative**: no token count is ever emitted, estimated, or inferred; only the `/cost` manual line carries spend | hard constraint |
| 7 | **Negative**: `reports/token-audit_2026-07-17.md` is left intact and marked closed-inconclusive, not deleted or rewritten | historical record |
| 8 | **Negative**: `.gitignore` still tracks `reports/token-audit_*` as the existing exception — the new file must be committable | see Edge Cases |

---

## Evaluation & Acceptance

### Success Criteria (observable, pass/fail)

| # | Given (input/state) | Expect (output/behavior) | How it's checked |
|---|---------------------|--------------------------|------------------|
| 1 | Fixture trace with 1 Agent + 1 wake Skill + 1 untagged record | 3 entries: one `spawn`, one `cold-start`, one tagged `overhead` | automated test |
| 2 | Generator run twice on the same fixture | byte-identical output; no duplicates | automated test (AC5) |
| 3 | Empty / absent `memory/event-trace/` | exits 0 with a clear "no trace data" message, does not crash or write a malformed file | automated test (negative) |
| 4 | Malformed JSONL line mid-file | line skipped with a warning; remaining entries still emitted | automated test (negative) |
| 5 | `git check-ignore reports/token-audit_2026-07-21.md` | not ignored (AC8) | automated test |

### Verification Command (exact, runnable)

```bash
bash scripts/token-audit.sh && \
  git check-ignore -q reports/token-audit_2026-07-21.md && echo "IGNORED (AC8 FAIL)" || echo "tracked (AC8 pass)"
```

### Evidence (filled by reviewer at Stage 4/5)

| Check | Result | Notes / output snippet |
|-------|--------|------------------------|
| **New test(s) cover Acceptance Criteria (file paths pasted)** | ☐ pass / ☐ fail | [required before Done] |
| Verification command run | ☐ pass / ☐ fail | [paste actual output] |
| Negative cases hold | ☐ pass / ☐ fail | [AC5 idempotency, AC6 no synthetic counts, AC7 old file intact, AC8 not gitignored] |
| verify | ☐ pass / ☐ fail / ☐ N/A | [must literally state "pass" or "fail" in this Notes column] |
| Review scope bounded to the change's blast radius | ☐ pass / ☐ fail | |
| Full smoke suite still green (no regression) | ☐ pass / ☐ fail | [`scripts/smoke-install.sh`] |
| **UI: Visual regression** | ☐ N/A | Script + markdown, no UI component |
| **UI: Design-system compliance** | ☐ N/A | Script + markdown, no UI component |
| **UI: Responsiveness** | ☐ N/A | Script + markdown, no UI component |

---

## Approach

**Derive, do not re-log.** `.claude/hooks/post_tool_trace.py` already fires on every tool call and
already writes task-tagged JSONL to `memory/event-trace/<task>.jsonl`, with untagged records going
to `_untagged.jsonl` rather than being dropped. Every event DDR-0001 wants — spawns, skill
invocations, cold-start — is already being captured.

So the fix is a **generator that reads existing trace data**, not a second always-on logger. This
was chosen over adding a new hook because a new PostToolUse hook fires on every tool call in the
repo and adds a failure surface to every operation, for data that is already being written. Reusing
the existing trace costs one script and no runtime risk.

Run it on demand and at session end alongside the `/cost` paste. Do not wire it into a hook.

**On the `cache` field**: DDR-0001 already documents this as a heuristic — first occurrence in a
session is `miss`, repeats are `hit` — and explicitly warns it is *"not a real cache-hit
measurement — do not over-trust it."* Reproduce that heuristic and carry the same caveat into the
generated file's header. Do not attempt to improve it.

**Model tier** is derivable from the `Agent` tool input where present; where it is not, emit `?`
rather than guessing (same principle as T042 — a visibly missing value beats a plausible wrong one).

**Closing the old window**: prepend a short status block to `reports/token-audit_2026-07-17.md`
recording that it closed inconclusive at 1 of 7 sessions, with the reason. Do not delete it — the
failure is itself the finding that justified this task.

---

## Edge Case Checklist

- [ ] `reports/` is gitignored **except** `reports/token-audit_*` (amended 2026-07-19, `memory/decisions.md`).
      A worktree-isolated spawn's gitignored output silently dies at merge — this file must stay tracked (AC8).
- [ ] Trace files can be large; stream them, do not read all JSONL into memory at once.
- [ ] A trace record may contain no model-tier information at all — emit `?`, never a default tier.
- [ ] Timestamps in the trace are UTC ISO; DDR-0001's format wants `YYYY-MM-DD`. Convert explicitly,
      and be consistent about which timezone the date boundary uses.
- [ ] DDR-0001 says a line missing the task-tag field "is malformed and must not be treated as a
      valid entry" — the generator must never emit such a line.
- [ ] Do not rewrite DDR-0001 itself; the Supervisor amends it separately.
- [ ] No shellcheck in this environment (`memory/learnings.md`) — substitute `sh -n` plus a real
      bash run and state the substitution rather than silently skipping it.

---

## Files to Change (Predicted)

| File | Change |
|------|--------|
| `scripts/token-audit.sh` | **New** — generate DDR-0001-format entries from `memory/event-trace/*.jsonl` |
| `reports/token-audit_2026-07-21.md` | **New** — new window, DDR-0001 header, opens 2026-07-21 |
| `reports/token-audit_2026-07-17.md` | Prepend closed-inconclusive status block; entries left intact |
| `scripts/tests/` or `.claude/hooks/tests/` | **New** test file (follow whichever convention already exists) |

## Files Must NOT Touch

| File | Reason |
|------|--------|
| `.claude/hooks/post_tool_trace.py` | Reused as-is; changing it risks the trace this task depends on |
| `docs/ddr/0001-measure-first-token-refactor.md` | Supervisor amends it — an agent must not edit a decision record |
| `.gitignore` | The `reports/token-audit_*` exception is already correct; AC8 only verifies it |
| `CLAUDE.md`, `.claude/agents/general-agent-template.md`, `.claude/hooks/post_write_register_task.py` | Owned by T039 / T041 / T042 this cycle |

---

## Test Plan

1. **Red**: write tests against a small committed fixture trace directory; they fail (no generator).
2. **Green**: implement the generator; AC1–AC4 pass.
3. **Negative controls**, each with pasted output: run twice (idempotent); empty trace dir; malformed
   JSONL line; `git check-ignore` on the new report.
4. **Regression**: `bash scripts/smoke-install.sh` still green.
5. Paste real command output into every Evidence row — never a claim of output.

---

## Completion Checklist

- [ ] Implementation done
- [ ] Self-review: `Skill({ skill: "code-review" })` run
- [ ] Security review: `Skill({ skill: "security-review" })` run — **mandatory, Risk=Medium**
- [ ] `sh -n` + real bash run (no shellcheck in this env — state the substitution)
- [ ] Tests written AND pass — output pasted into Evidence table (Hard-Stop Gate 5)
- [ ] `Skill({ skill: "verify" })` run
- [ ] Report to the Supervisor for `memory/`: whether the derived-from-trace approach actually
      captures every DDR-0001 event type, or whether gaps remain (do not write memory yourself)
- [ ] Supervisor notified: task ready for Stage 4 review
