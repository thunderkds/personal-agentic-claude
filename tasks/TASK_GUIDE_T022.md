# TASK_GUIDE — T022: Harden pre_agent_validate_guide.py task-ID extraction
**Date**: 2026-07-14
**Complexity Level**: C2
**Risk Level**: Medium
**Priority**: P1
**Assigned agent**: backend-developer
**Agent guide**: `.claude/agents/backend.md`

---

## Mandatory Startup (Do Not Skip)
1. Read `PROJECT_SPEC.md`
2. Read `memory/MEMORY.md`
3. Read this file completely
4. Read `.claude/agents/backend.md`
5. This is a C2 task touching a guardrail hook — read `memory/codebase-map.md` if it exists, and read `.claude/hooks/pre_agent_validate_guide.py` and `.claude/hooks/pre_agent_step_limit.py` in full before editing (the latter for a second example of the project's existing hook-parsing conventions).

---

## Requirement (Pillar 1 — Adapt the requirement)

Brainstorming (`BRAINSTORMING_LOG.md`, 2026-07-14) selected **Option B**: harden `.claude/hooks/pre_agent_validate_guide.py`'s task-ID extraction so it only recognizes **structural** references to a task ID — not any bare `T\d+` appearing anywhere in free prose (which currently causes false-positive hard-blocks, e.g. a `MEMORY.md` decision entry mentioning a since-removed task ID blocks the *next*, unrelated spawn).

**Current behavior** (confirmed via code read): `pre_agent_validate_guide.py` line ~93 runs `task_ids = re.findall(r"\bT(\d+)\b", prompt, re.IGNORECASE)` over the **entire** spawn prompt string (including any pasted `MEMORY.md` content), then hard-blocks the spawn if any matched ID has no `tasks/TASK_GUIDE_Txxx.md`.

**Restated intent**: change the extraction so it only treats an ID as "this spawn is about task Txxx" when it appears in a genuinely structural marker — e.g. a literal `tasks/TASK_GUIDE_Txxx.md` file-path reference, or an explicit `**Task ID**: Txxx` / `Task ID: Txxx` declaration line — not when `Txxx` merely appears inside a sentence, a decision-log entry, or other prose. The `Depends on:` field parsing (used for the separate, already-advisory dependency warning) is a different code path (`check_dependency_warnings`) and must keep working exactly as today — this task only changes the **blocking** extraction (`task_ids` used for the "missing TASK_GUIDE" hard block), not the dependency-warning logic.

**Out of scope**:
- Do not change `check_dependency_warnings()`'s own regex or behavior (it already only fires on `**Depends on**:` lines — that's correct and unaffected).
- Do not change the hard-block decision logic itself (still blocks if a *genuinely referenced* guide is missing) — only which substrings count as "genuinely referenced."
- Do not touch `post_write_register_task.py` (separate hook, separate bug — noted as a follow-up, not this task: its `agent` field regex matches "Agent guide" instead of "Assigned agent" due to a similar boundary issue, confirmed live during T021 registration).

**Requirement Refs**: none (internal tooling hygiene).

### Requirement Fidelity Gate (sign off BEFORE implementation)
- [x] Restated intent confirmed to match the request (Supervisor, informed by approved brainstorming Option B)

---

## Complexity & Risk
- Complexity: C2 (design decision: what counts as "structural," touches a hard-block guardrail hook, needs real-data verification per the T018 lesson)
- Risk: Medium (floors here because a wrong fix could either (a) silently defeat the guardrail — an actual missing-guide spawn slips through, or (b) still false-positive-block legitimate spawns; both are worse than the status quo if unverified)

## Diagnosis Gates (must pass before any fix)
- [ ] Reproduce the false positive: confirm `re.findall(r"\bT(\d+)\b", open('memory/MEMORY.md').read(), re.IGNORECASE)` currently returns IDs with no backing guide (T013/T014, before T021 lands — if T021 already landed, construct a synthetic prompt string containing a decision-log-style sentence mentioning an ID with no guide, to prove the false-positive class still exists for *future* entries).
- [ ] Confirm the fix's new pattern correctly extracts the task ID from every real historical spawn-prompt shape used in this session (structural: `tasks/TASK_GUIDE_T005.md`, `TASK_GUIDE_T018.md` style references) — these must still resolve and hard-block correctly if genuinely missing.
- [ ] Confirm the fix's new pattern does NOT extract an ID from prose mentions like "T019: reconciled PROJECT_KANBAN.md..." or "confirmed T013/T014 have no guide" (both real sentences already present in `memory/decisions.md`).

## Fix Gates
- [ ] Regression test (new, `.claude/hooks/tests/test_pre_agent_validate_guide.py`) covering: (a) structural reference to an existing guide → not blocked; (b) structural reference to a missing guide → blocked; (c) prose mention of an ID with no guide, NOT in a structural marker → not blocked (this is the false-positive case being fixed); (d) prose mention of an ID that DOES have a guide → not blocked (should never have been an issue, but confirm no regression).
- [ ] Verify against real files: run the updated hook's extraction logic against an actual multi-line prompt string built from `memory/MEMORY.md` + `memory/decisions.md` content (as they exist at fix time) and confirm no false-positive block occurs, and against a synthetic prompt containing `tasks/TASK_GUIDE_T999_DOES_NOT_EXIST.md` and confirm it DOES block.
- [ ] Fix matches "correct behaviour": genuinely-spawned tasks with missing guides still hard-block (guardrail intact); prose mentions of unrelated task IDs never block.

## Cleanup Checklist
- [ ] No scratch files left behind
- [ ] Commit message states the old vs. new extraction pattern and why
- [ ] Post-mortem note: this is the second time in one session a "looks right in isolation, fails on real multi-line/markdown content" regex bug was found (see T018) — consider whether `.claude/hooks/tests/` should get a standing convention requiring every hook regex to be tested against real repo file content, not just synthetic strings, as a follow-up recommendation to the Supervisor (do not implement that convention here — flag it only).

## Evidence
| Check | Command / observation | Result |
|---|---|---|
| Repro loop (old regex, synthetic prose) | `python3 -c "import re; prompt='Task pointer: spawn backend-developer for T022.\n\nmemory/MEMORY.md (hot-tier context):\n- Decision log: confirmed T013/T014 have no guide and were superseded before Stage 2 re-planning; see decisions.md for T019: reconciled PROJECT_KANBAN.md drift.\n'; print(re.findall(r'\\bT(\\d+)\\b', prompt, re.IGNORECASE))"` → `['022', '013', '014', '019']` — confirms the old `\bT(\d+)\b` extraction over the whole prompt picks up prose-only mentions (013/014, which have no backing guide) alongside the genuine spawn target (022). This is the false-positive class being fixed (T013/T014 already had no guide per the T019 decision-log cleanup, so this was reproducible directly against real repo state, no synthetic guide-removal needed). | Confirmed reproducible |
| Fix applied | Added `extract_structural_task_ids()` to `.claude/hooks/pre_agent_validate_guide.py`, used for the hard-block `task_ids` (only): matches `TASK_GUIDE_T(\d+)(?:_[A-Z0-9_]+)?\.md` (literal file-path reference) or `(?:\*\*Task ID\*\*\|Task ID)\s*:\s*T(\d+)\b` (explicit declaration line). `check_dependency_warnings()` and its `\bT(\d{3})\b` regex on `**Depends on**:` lines left untouched. Also changed the file's bare `main()` call at module scope to `if __name__ == "__main__": main()` so the hook remains importable/unit-testable without consuming stdin (behavior when invoked as a script by Claude Code is unchanged). | Diff applied, see summary below |
| Regression test | `python3 .claude/hooks/tests/test_pre_agent_validate_guide.py` → `PASS` x7 (`test_structural_reference_to_existing_guide`, `test_structural_reference_to_missing_guide`, `test_prose_mention_of_missing_id_not_extracted`, `test_prose_mention_of_id_with_existing_guide_not_extracted`, `test_task_id_declaration_line_extracted`, `test_real_memory_and_decisions_content_no_false_positive`, `test_synthetic_missing_guide_reference_still_blocks`) → "All 7 tests passed". Also verified via `python3 -m pytest .claude/hooks/tests/test_pre_agent_validate_guide.py -v` → "7 passed in 0.02s". | PASS |
| Real-file verification (`test_real_memory_and_decisions_content_no_false_positive`) | Built a real multi-line prompt from the actual `memory/MEMORY.md` + `memory/decisions.md` content read at fix time, ran `extract_structural_task_ids()` against it. Note: `decisions.md` legitimately contains literal `tasks/TASK_GUIDE_Txxx.md` mentions in its own historical "**Files**:" lines (e.g. T001, T015–T020) — these DO get extracted as structural (correct, since the pattern is a genuine file-path), but every one of them has a real backing guide on disk, so no false-positive block fires. Asserted: no extracted ID lacks a backing guide, and T022 (the genuine spawn target) is present in the extracted set. | PASS — no false-positive block |
| Guardrail-intact check | `echo '{"tool_name":"Agent","tool_input":{"prompt":"Spawn context.\nRead tasks/TASK_GUIDE_T999_DOES_NOT_EXIST.md before starting."}}' \| python3 .claude/hooks/pre_agent_validate_guide.py` (via `subprocess.run` to get real stdin) → `{"decision": "block", "reason": "[hook:pre_agent] Cannot spawn agent — missing TASK_GUIDE for: T999. Run Stage 2 planning first to generate the guide(s) in tasks/."}` | PASS — still blocks on a genuinely missing structural reference |
| `check_dependency_warnings()` unaffected | Read-diff confirms no lines in `check_dependency_warnings()` or its `\bT(\d{3})\b` regex on `**Depends on**:` lines were touched. | Unaffected, confirmed by diff |
