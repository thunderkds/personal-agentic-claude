# TASK_GUIDE — T024: Fix post_write_register_task.py agent-field regex
**Date**: 2026-07-14
**Complexity Level**: C0
**Risk Level**: Low
**Priority**: P2
**Assigned agent**: backend-developer
**Agent guide**: `.claude/agents/backend.md`

---

## Mandatory Startup (Do Not Skip)
1. Read `PROJECT_SPEC.md`
2. Read `memory/MEMORY.md`
3. Read this file completely
4. Read `.claude/agents/backend.md`

---

## Requirement (Pillar 1 — Adapt the requirement)

Confirmed live twice during T021/T022's Kanban auto-registration (2026-07-14): `.claude/hooks/post_write_register_task.py`'s `agent` extraction regex `(?:Assigned Agent|Agent)[:\s]+([a-z\-]+)` matches the substring `"Agent guide"` (from the `**Agent guide**: ...` line) instead of `"Assigned agent"` when the guide's markdown bold markers (`**`) sit between the word "Agent" and its intended colon — same boundary-matching bug class as the T018 title regex.

**Restated intent**: fix the `agent` field extraction so it reliably captures the value after `**Assigned agent**:`, not `guide` from `**Agent guide**:`.

**Out of scope**: does not touch the `title`/`cx`/`risk`/`priority` extractions (already fixed/working) or `pre_agent_validate_guide.py` (separate hook, separate task T022, already done).

### Requirement Fidelity Gate (sign off BEFORE implementation)
- [x] Restated intent confirmed to match the observed live bug (Supervisor)

---

## Complexity & Risk
- Complexity: C0 (one regex, one file)
- Risk: Low

## Task
1. Reproduce: run the current `agent` extraction regex against a real guide file containing both `**Assigned agent**: backend-developer` and `**Agent guide**: ...` lines (e.g. `tasks/TASK_GUIDE_T021.md`) and confirm it returns `"guide"`.
2. Fix the regex (e.g. anchor on the literal `**Assigned agent**` bold-wrapped label specifically, or require the captured value not be the literal word `guide`, or reorder so `Assigned Agent` is tried with a pattern that tolerates `**` between the label and colon).
3. Add a regression test to `.claude/hooks/tests/test_post_write_register_task.py` covering: real guide with both lines present → extracts the real agent name, not "guide".
4. Verify against `tasks/TASK_GUIDE_T021.md`, `T022.md`, `T023.md` — all three currently show the wrong agent value on the Kanban (already manually corrected by the Supervisor as a workaround); confirm the fixed regex now extracts them correctly.

## Evidence
| Check | Command / observation | Result |
|---|---|---|
| Repro loop | | |
| Regression test | | |
| Smoke suite | | |
