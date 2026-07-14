# TASK_GUIDE — T015: `ui-test` skill (easy-ui-mcp orchestration)
**Date**: 2026-07-01
**Complexity Level**: C1
**Risk Level**: Low
**Priority**: P1
**Assigned agent**: qa-expert
**Agent guide**: `.claude/agents/qa.md`

---

## Mandatory Startup (Do Not Skip)

Before writing any code:
1. Read `PROJECT_SPEC.md`
2. Read `memory/MEMORY.md`
3. Read this file completely
4. Read `.claude/agents/qa.md`
5. Complexity Level is C1 — light smoke-test rigor, no brainstorm/decompose step required per the Complexity matrix in `.claude/agents/general-agent-template.md`
6. Single new file, single known location — skip `memory/codebase-map.md`

---

## Requirement (Pillar 1 — Adapt the requirement)

User: "I implemented the MCP for web UI testing (github.com/thunderkds/easy-ui-mcp) and want to integrate it with our harness to make UI testing steps more possible for web (mobile deferred)." Brainstorming (`BRAINSTORMING_LOG.md`, approved 2026-07-01) locked **Option B — Self-Degrading Optional Skill**.

**Restated intent**:
> Create `.claude/skills/ui-test/SKILL.md`: a skill that, when invoked, health-checks the local `easy-ui-mcp` Docker server (`http://localhost:8765/health`), and — if healthy and the task has a UI component — drives the 8 MCP tools (`ui_start_session`, `ui_navigate`, `ui_click`, `ui_fill`, `ui_assert`, `ui_get_page_state`, `ui_take_screenshot`, `ui_end_session`) in sequence, then formats the resulting JSON/screenshot report into rows pasteable directly into a TASK_GUIDE's Evidence table. If the server is down or the task has no UI component, the skill must emit a one-line skip note and exit cleanly — it never blocks or errors out the pipeline.

**Out of scope**:
- Any mobile testing (deferred per user's original request)
- Wiring the skill into `qa.md` / `CLAUDE.md` (that's T016 — this task only builds the skill itself)
- CI/remote execution — this is a local-machine convenience only
- Reimplementing screenshot diffing, assertion logic, or a new report schema — delegate to what `easy-ui-mcp` already emits

**Requirement Refs**: None (`PRD.md` does not cover this framework's own skill catalogue — this is an internal tooling task, not a product FR/NFR). Traceability is instead to `BRAINSTORMING_LOG.md` → Option B → Surgical Scope.

### Requirement Fidelity Gate (sign off BEFORE implementation)

- [x] Restated intent confirmed to match the user's request (Supervisor, via approved brainstorming session)
- [x] Domain terms align — "MCP UI Evidence", "health-check", "skip note" all defined in `BRAINSTORMING_LOG.md`
- [x] Every Acceptance Criterion below traces to a line in the Requirement
- [x] No `PRD.md` Requirement Refs apply (internal tooling task) — Supervisor waives this row explicitly

---

## Acceptance Criteria

| # | Criterion (testable) | Traces to requirement |
|---|----------------------|-----------------------|
| 1 | Skill file exists at `.claude/skills/ui-test/SKILL.md`, follows the structure of other skills in this repo (frontmatter-free Markdown, Role/Workflow/Communication sections per `write-better-skill` conventions) | Restated intent |
| 2 | Skill's first documented step is a health-check against `http://localhost:8765/health`; on failure it documents emitting a skip note and stopping, not erroring | Self-degrading requirement |
| 3 | Skill documents the exact MCP tool call sequence (`ui_start_session` → navigate/click/fill → `ui_assert`/`ui_get_page_state` → `ui_take_screenshot` → `ui_end_session`) | Orchestration requirement |
| 4 | Skill documents how it maps `easy-ui-mcp`'s JSON+screenshot report output into the three UI Evidence rows (visual regression, design-system compliance, responsiveness) plus the `verify` row, ready to paste into a TASK_GUIDE | Gate 6 reuse requirement |
| 5 | Skill documents the "task has no UI component" skip path (distinct from the "server down" skip path) | Non-blocking requirement |
| 6 | Report file naming follows the existing `reports/<skill>_<branch>_<timestamp>.html` (or `.json` if no HTML render applies) convention already used by `html-report`/`thinking-report` | Edge case checklist |

---

## Evaluation & Acceptance (How we know the agent worked correctly)

### Success Criteria (observable, pass/fail)

| # | Given (input/state) | Expect (output/behavior) | How it's checked |
|---|---------------------|--------------------------|------------------|
| 1 | `easy-ui-mcp` Docker container running locally, task has a UI component | Skill's documented workflow runs the full MCP tool sequence and produces Evidence-table-ready output | Manual dry run against a real local `easy-ui-mcp` instance (or documented trace if Docker unavailable in this environment) |
| 2 | `easy-ui-mcp` server NOT running | Skill documents emitting a one-line skip note; no error, no block | Manual dry run with server stopped |
| 3 | Task has no UI component | Skill is simply never invoked by `qa.md` (verified in T016, not here) — this task only needs to document that the skill assumes it's called conditionally | Read-through of SKILL.md logic |

### Verification Command (exact, runnable)

```bash
# Health-check path (server down case — always runnable in this environment)
curl -sf http://localhost:8765/health || echo "expected: skip path triggers here"
```

### Evidence (filled by reviewer at Stage 4/5)

| Check | Result | Notes / output snippet |
|-------|--------|------------------------|
| **New test(s) cover Acceptance Criteria (file paths pasted)** | ☐ pass / ☐ fail | |
| Verification command run | ☐ pass / ☐ fail | |
| Negative cases hold | ☐ pass / ☐ fail | |
| `verify` skill — works in running app | ☐ pass / ☐ fail | |
| Review scope bounded to the change's blast radius | ☐ pass / ☐ fail | |
| Full smoke suite still green (no regression) | ☐ pass / ☐ fail | |
| **UI: Visual regression** | ☐ N/A | This task authors a skill file, not a UI — N/A justified |
| **UI: Design-system compliance** | ☐ N/A | Same as above |
| **UI: Responsiveness** | ☐ N/A | Same as above |

---

## Approach

Follow `write-better-skill` conventions (this repo's authoritative reference for SKILL.md structure). Model the file on existing lean skills like `migration-safety` or `blast-radius` — self-contained, reads the repo/tests state, no external CLI assumed beyond the documented `curl` health-check. Keep it under ~90 lines per the brainstorming session's 50%-rule check: orchestration only, no reimplemented test logic.

---

## Edge Case Checklist

From `BRAINSTORMING_LOG.md`:
- [ ] MCP server not running / Docker not installed → skip note, no block
- [ ] Task has no UI component → never invoked (enforced by caller in T016, but document the assumption here)
- [ ] Health check passes but a `ui_*` tool call fails mid-sequence → report as a real failure, not a skip (infra-available vs test-failed distinction)
- [ ] Each run must call `ui_start_session` / `ui_end_session` to avoid stale screenshot/state bleed across runs
- [ ] Document explicitly: local-machine convenience, not a CI gate
- [ ] Reuse `reports/<skill>_<branch>_<timestamp>` naming — no new scheme

---

## Files to Change (Predicted)

| File | Change |
|------|--------|
| `.claude/skills/ui-test/SKILL.md` | New file — full skill definition |

## Files Must NOT Touch

| File | Reason |
|------|--------|
| `.claude/agents/qa.md` | Wiring happens in T016, after this skill exists to reference concretely |
| `CLAUDE.md` | Same — T016 |
| `.claude/agents/frontend.md`, `.claude/agents/backend.md`, `.claude/agents/common-infrastructure.md` | No UI-testing responsibility belongs here (Surgical Scope) |
| `packs/mobile/*` | Mobile explicitly out of scope |

---

## Test Plan

Manual dry run: (1) confirm the skip path triggers when `curl http://localhost:8765/health` fails (true in this environment — no Docker container exists yet), (2) read-through validation that the documented MCP tool sequence and Evidence-mapping are internally consistent and match `easy-ui-mcp`'s documented tool names exactly.

---

## Completion Checklist

- [ ] Implementation done
- [ ] Self-review: `Skill({ skill: "code-review" })` run
- [ ] Security review: N/A (Low risk)
- [ ] Lint passes (Markdown only — no code)
- [ ] Tests written AND pass — output pasted into Evidence table
- [ ] `Skill({ skill: "verify" })` run — feature confirmed working (skip-path only, since no local MCP server in this environment)
- [ ] `memory/MEMORY.md` updated (new skill entry)
- [ ] Supervisor notified: task ready for Stage 4 review
