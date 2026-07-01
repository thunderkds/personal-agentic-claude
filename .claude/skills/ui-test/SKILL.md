---
name: ui-test
description: Self-degrading UI test orchestration over the local easy-ui-mcp server. Use during Stage 5 (verify) for any task with a UI component, to drive a browser through the 8 easy-ui-mcp tools and format the resulting JSON/screenshot report into TASK_GUIDE Evidence rows — this same run also satisfies Stage 4 Hard-Stop Gate 6's UI Evidence rows. Never invoke for tasks with no UI component. If the local server is down, emits a one-line skip note and exits cleanly — it never blocks or errors out the pipeline.
---

## Role: UI Test Orchestrator (Self-Degrading)

You answer one question: **"Does the local `easy-ui-mcp` server confirm this UI works, and if it can't, does the pipeline still move?"** You orchestrate — you do not reimplement screenshot diffing, assertion logic, or a new report schema. `easy-ui-mcp` already emits JSON + screenshot reports; your job is sequencing its 8 tools and reshaping its output into Evidence-table rows.

This is a **local-machine convenience**, not a CI gate. Mobile testing is out of scope (web only).

### Karpathy Operational Commands (Specific Overrides)
- **Ask vs. Guess**: Never fabricate a screenshot, assertion result, or pass/fail — only report what the MCP tools actually returned.
- **Simplicity First**: No new report schema. Reuse `easy-ui-mcp`'s JSON/screenshot output as-is, just remapped into rows.
- **Goal-Driven Execution**: Success is verifiable — either a full Evidence-ready report, or a clean one-line skip note. There is no third outcome.

### Activation Trigger
Called only for a task whose TASK_GUIDE has a UI/Design Acceptance Criteria section (never invoked for pure-backend tasks — that decision belongs to the caller, e.g. `qa.md`).

### Workflow

#### 1. Health Check (always first)
```bash
curl -sf http://localhost:8765/health
```
- **Fails** (connection refused, timeout, non-2xx, or Docker not running): emit the skip note below and **stop** — this is not a failure, it is infrastructure being unavailable.
  > `ui-test: skipped — easy-ui-mcp not reachable at localhost:8765 (Docker not running?)`
- **Succeeds**: continue to step 2.

#### 2. No-UI-Component Check
If the calling task has no UI/Design Acceptance Criteria section, do not run this skill at all — emit:
> `ui-test: skipped — task has no UI component`

This is a distinct skip path from step 1: server-down is an infra gap, no-UI-component is a scope gap. Never conflate the two in the skip note.

#### 3. Drive the MCP Tool Sequence
Call the 8 tools in this exact order, once per session:

1. `ui_start_session` — open a fresh browser session (avoids stale screenshot/state bleed from a prior run)
2. `ui_navigate` — go to the page/route under test
3. `ui_click` / `ui_fill` — perform the interactions the Acceptance Criteria require (repeat as needed)
4. `ui_assert` — check expected state/text/elements
5. `ui_get_page_state` — capture DOM/state snapshot for the design-system compliance row
6. `ui_take_screenshot` — capture visual evidence for the visual-regression row
7. `ui_end_session` — always close the session, even if an assertion failed above

If a `ui_*` tool call fails **after** the health check passed, that is a **real test failure**, not a skip — report it as a failing Evidence row with the tool's error output, and still call `ui_end_session` to avoid leaking session state into the next run.

#### 4. Map Output into Evidence Rows
Reshape the JSON/screenshot report `easy-ui-mcp` returns directly into these TASK_GUIDE Evidence table rows — no new fields, no reformatting beyond pass/fail + evidence snippet:

| TASK_GUIDE Evidence row | Sourced from |
|---|---|
| UI: Visual regression | `ui_take_screenshot` output (path/diff result) |
| UI: Design-system compliance | `ui_get_page_state` + `ui_assert` results |
| UI: Responsiveness | Repeat steps 2–6 per viewport size exercised by `ui_navigate`/`ui_assert`; one row per breakpoint or a combined pass/fail |
| `verify` (Stage 5 row) | Overall pass/fail across the full tool sequence |

#### 5. Report Naming
If a rendered artifact is produced, save it as `reports/ui-test_<branch>_<YYYYMMDDTHHMMSS>.json` (or `.html` if a visual render is generated) — the same naming convention `html-report`/`thinking-report` already use. Do not invent a new scheme.

### Communication Protocol
- **To Supervisor**: Report the outcome the moment the run ends — one of: skipped (infra), skipped (no UI), or pass/fail with the Evidence rows above.
- **Default Notification**: "ui-test for [Task ID]: SKIPPED (server down) / SKIPPED (no UI component) / PASS / FAIL. Evidence rows: [pasted or N/A]."
