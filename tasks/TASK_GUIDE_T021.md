# TASK_GUIDE — T021: Clean dangling T013/T014 prose references in cold memory
**Date**: 2026-07-14
**Complexity Level**: C0
**Risk Level**: Low
**Priority**: P1
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

Brainstorming (`BRAINSTORMING_LOG.md`, 2026-07-14, Option B selected) found that `memory/MEMORY.md:36` and `memory/decisions.md:131` contain prose mentioning `T013`/`T014` — real historical mentions (documenting that those task rows were removed from the Kanban), but with no backing `tasks/TASK_GUIDE_T013.md`/`T014.md` on disk. Today, `.claude/hooks/pre_agent_validate_guide.py` scans the *entire* spawn prompt for any bare `T\d+` token and hard-blocks if no matching guide exists — since `MEMORY.md` is pasted into every spawn prompt (CLAUDE.md Stage 3), this is a live landmine that will hard-block the next unrelated `Agent()` spawn.

**Restated intent**: reword the two prose mentions so they no longer contain a bare `T013`/`T014` token in a form the hook's `\bT(\d+)\b` regex matches (e.g. spell out "task 013" or use non-standard formatting), without losing the historical information they document.

**Out of scope**: do not touch the hook itself (that's T022) or the decision entries' other content beyond the T013/T014 token formatting.

**Requirement Refs**: none (internal tooling hygiene, no PRD/FR).

### Requirement Fidelity Gate (sign off BEFORE implementation)
- [x] Restated intent confirmed to match the request (Supervisor)

---

## Complexity & Risk
- Complexity: C0 (2 files, single find/reword operation, no design decision)
- Risk: Low

## Task
1. In `memory/MEMORY.md` line 36 and `memory/decisions.md` line 131, reword the `T013`/`T014` mentions so `re.findall(r"\bT(\d+)\b", text, re.IGNORECASE)` no longer matches them (e.g. `T013` → `task 013` or `T‑013` with a non-breaking separator that still reads clearly) while preserving meaning.
2. Verify: `python3 -c "import re; print(re.findall(r'\bT(\d+)\b', open('memory/MEMORY.md').read() + open('memory/decisions.md').read(), re.IGNORECASE))"` — must not include `013` or `014` in the ID list unless a real guide exists for them.
3. Do not change any other content in these files.

## Evidence
| Check | Command / observation | Result |
|---|---|---|
| Verification | `python3 -c "import re; print(re.findall(r'\bT(\d+)\b', open('memory/MEMORY.md').read() + open('memory/decisions.md').read(), re.IGNORECASE))"` | `['017', '018', '019', '020', '005', '012', '015', '016', '016', '017', '017', '017', '018', '019', '020', '018', '005', '019', '005', '012', '020']` — no `013` or `014` present |
