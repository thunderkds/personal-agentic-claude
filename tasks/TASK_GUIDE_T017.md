# TASK_GUIDE — T017: Task dependency declaration & entry-point reachability check
**Date**: 2026-07-07
**Complexity Level**: C1
**Risk Level**: Low
**Priority**: P1
**Assigned agent**: common-infrastructure
**Agent guide**: `.claude/agents/common-infrastructure.md`

---

## Mandatory Startup (Do Not Skip)

Before writing any code:
1. Read `PROJECT_SPEC.md` (Glossary already updated with `Depends on` / `Entry point` definitions)
2. Read `memory/MEMORY.md`
3. Read this file completely
4. Read `.claude/agents/common-infrastructure.md`
5. C1 — single agent, no worktree brainstorm needed; design already resolved in `BRAINSTORMING_LOG.md` (Option C) and `grill-with-docs` terminology session
6. Skip `memory/codebase-map.md` — single-file-family, known-pattern change

This is a framework meta-task (this repo *is* the Supervisor framework) — there is no `PRD.md`/`docs/legacy/` to consult.

---

## Requirement (Pillar 1 — Adapt the requirement)

User reported that the pipeline has no way to catch two failure modes: (1) Task B silently assumes Task A's output exists as a precondition, with nothing checking this before/during execution, and (2) a feature is implemented with no reachable entry point (no button/route/caller), so it passes its own tests but is functionally dead code. Resolved via `Skill({ skill: "brainstorming" })` → Option C (Declarative + Verified Hybrid), then sharpened via `Skill({ skill: "grill-with-docs" })`.

**Restated intent** (Supervisor's interpretation, in the project's domain language):
> Every `TASK_GUIDE_Txxx.md` gains two structured, checkable fields — `Depends on:` and `Entry point:`. `Depends on` is verified automatically at Agent-spawn time (warn if the referenced task isn't Done). `Entry point` is verified at Stage 4 `code-review` time (warn if the declared literal identifier isn't found in the diff/repo). Both fail toward an advisory warning, never a hard block — this is a new advisory layer, not an addition to the six existing Hard-Stop Gates.

**Out of scope** (what this task explicitly does NOT do):
- Does not build a real dependency graph or static-analysis tool (explicitly rejected in `BRAINSTORMING_LOG.md` Option B)
- Does not touch or merge with `PROJECT_KANBAN.md`'s existing `## Blocked` table — confirmed via `AskUserQuestion` to stay a separate, manual mechanism for non-task blockers
- Does not add a new Hard-Stop Gate (7th gate) — this is advisory, per the brainstorming log's Surgical Scope

**Requirement Refs**: N/A — this repo has no `PRD.md` (it *is* the Supervisor framework, not a target project). Traces instead to `BRAINSTORMING_LOG.md` → "Recommended Path: Option C" (approved 2026-07-07) and `PROJECT_SPEC.md` Glossary entries for `Depends on` / `Entry point`.

### Requirement Fidelity Gate (sign off BEFORE implementation)

- [x] Restated intent confirmed to match the user's request (brainstorming + grilling sessions, both approved by user)
- [x] Domain terms align with `PROJECT_SPEC.md` glossary (`Depends on`, `Entry point` — canonical terms locked via `grill-with-docs`, "Reachable via" rejected as synonym)
- [x] Every Acceptance Criterion below traces to a line in the Requirement
- [x] N/A — no `PRD.md` in this repo; Requirement Refs point to `BRAINSTORMING_LOG.md` instead (see above)

---

## Acceptance Criteria

| # | Criterion (testable) | Traces to requirement |
|---|----------------------|-----------------------|
| 1 | `templates/TASK_GUIDE_template.md` has a `## Dependencies & Reachability` section with `Depends on:` and `Entry point:` fields, each documented with an example and the N/A case | Restated intent |
| 2 | `.claude/hooks/pre_agent_validate_guide.py` parses `Depends on: Txxx` from the target task's guide and warns (does not block) if Txxx is not `Done` on `PROJECT_KANBAN.md` | Restated intent |
| 3 | A task guide with `Depends on: None` or no such field spawns with no warning (no false positive on the common case) | Edge case: most tasks have no dependency |
| 4 | A task guide with `Depends on: T999` (nonexistent task) produces a distinct "unknown dependency" warning, not silently treated as satisfied | Edge case checklist item 1 |
| 5 | `.claude/skills/code-review/SKILL.md` gains a reachability check step: if a task's guide declares `Entry point: [identifier]` (not `Standalone — N/A`), the reviewer greps the diff/repo for that literal string and adds a finding if not found | Restated intent |
| 6 | `CLAUDE.md` documents the new TASK_GUIDE section and states explicitly this is advisory, not a 7th Hard-Stop Gate | Out of scope constraint |

---

## Evaluation & Acceptance (How we know the agent worked correctly)

### Success Criteria (observable, pass/fail)

| # | Given (input/state) | Expect (output/behavior) | How it's checked |
|---|---------------------|--------------------------|------------------|
| 1 | A task guide with `Depends on: T999` (T999 not in KANBAN) spawned via the Agent tool | Hook prints a warning naming T999 as unknown; spawn still proceeds (advisory) | Manual: pipe a synthetic event through `pre_agent_validate_guide.py` and inspect stdout/decision field |
| 2 | A task guide with `Depends on: T001` where T001 is in the `Done` section | Hook allows spawn with no warning | Manual: same harness, synthetic event with `Depends on: T001` |
| 3 | A task guide with `Depends on: T005` where T005 is in `Todo`/`In Progress` | Hook warns "T005 not yet Done" but does not set `decision: block` | Manual: synthetic event, assert JSON output has no `"decision": "block"` |
| 4 | A guide with no `Depends on` field at all | No warning printed, hook exits silently (matches current behavior) | Manual: synthetic event without the field |

### Verification Command (exact, runnable)

```bash
# 1. Unit-style manual checks against the hook via stdin (no test framework in this repo for hooks)
echo '{"tool_name":"Agent","tool_input":{"prompt":"Spawn for T020. Depends on: T999"}}' | python3 .claude/hooks/pre_agent_validate_guide.py
echo '{"tool_name":"Agent","tool_input":{"prompt":"Spawn for T020. Depends on: T001"}}' | python3 .claude/hooks/pre_agent_validate_guide.py
echo '{"tool_name":"Agent","tool_input":{"prompt":"Spawn for T020"}}' | python3 .claude/hooks/pre_agent_validate_guide.py

# 2. Syntax/compile check
python3 -m py_compile .claude/hooks/pre_agent_validate_guide.py

# 3. Settings/template sanity
python3 -m json.tool .claude/settings.json > /dev/null
grep -q "Dependencies & Reachability" templates/TASK_GUIDE_template.md
grep -q "Entry point" .claude/skills/code-review/SKILL.md
```

### Evidence (filled by reviewer at Stage 4/5)

| Check | Result | Notes / output snippet |
|-------|--------|------------------------|
| **New test(s) cover Acceptance Criteria (file paths pasted)** | ☑ pass | `.claude/hooks/pre_agent_validate_guide.py` — 4 synthetic-stdin transcripts covering all 4 Success Criteria rows, run and pasted below |
| Verification command run | ☑ pass | See transcripts below; `python3 -m py_compile .claude/hooks/pre_agent_validate_guide.py` → clean; `python3 -m json.tool .claude/settings.json` → valid; `grep -q "Dependencies & Reachability" templates/TASK_GUIDE_template.md` → match; `grep -q "Entry point" .claude/skills/code-review/SKILL.md` → match |
| Negative cases hold | ☑ pass | T999-unknown case (below) warns without blocking; no-field case (below) produces zero output |
| `verify` skill — works in running app | N/A | No running app — this is tooling/process infra, not a UI/app feature. Manual hook-transcript evidence above/below (4 synthetic stdin cases) is the substitute evidence for this row. |
| Review scope bounded to the change's blast radius (affected set, not whole repo) | ☑ pass | Reviewed only the 4 touched files: `templates/TASK_GUIDE_template.md`, `templates/PROJECT_KANBAN_template.md`, `.claude/hooks/pre_agent_validate_guide.py`, `.claude/skills/code-review/SKILL.md`, `CLAUDE.md` |
| Full smoke suite still green (no regression) | ☑ pass | No existing test suite in this repo; confirmed `pre_bash_block_unsafe_merge.py` and `post_agent_move_to_review.py` still `py_compile` clean and untouched by this change |
| **UI: Visual regression** | N/A | Pure backend/tooling task |
| **UI: Design-system compliance** | N/A | Pure backend/tooling task |
| **UI: Responsiveness** | N/A | Pure backend/tooling task |

**Verification transcripts (2026-07-07)**:

```
-- case1: Depends on T999 (unknown) --
$ echo '{"tool_name":"Agent","tool_input":{"prompt":"Spawn for T900"}}' | python3 .claude/hooks/pre_agent_validate_guide.py
{"hookSpecificOutput": {"hookEventName": "PreToolUse", "additionalContext": "[hook:pre_agent] Dependency warning (advisory, not blocking):\n  • T900 declares 'Depends on: T999' but T999 was not found anywhere on PROJECT_KANBAN.md — unknown dependency, check for a typo."}}

-- case2: Depends on T001 (Done) --
$ echo '{"tool_name":"Agent","tool_input":{"prompt":"Spawn for T901"}}' | python3 .claude/hooks/pre_agent_validate_guide.py
(no output — allowed silently, as expected)

-- case3: Depends on T014 (Todo, not Done) --
$ echo '{"tool_name":"Agent","tool_input":{"prompt":"Spawn for T902"}}' | python3 .claude/hooks/pre_agent_validate_guide.py
{"hookSpecificOutput": {"hookEventName": "PreToolUse", "additionalContext": "[hook:pre_agent] Dependency warning (advisory, not blocking):\n  • T902 declares 'Depends on: T014', which is currently 'Todo' (not Done). Confirm this is intentional (e.g. parallel stub work) before proceeding."}}

-- case4: no Depends on field --
$ echo '{"tool_name":"Agent","tool_input":{"prompt":"Spawn for T903"}}' | python3 .claude/hooks/pre_agent_validate_guide.py
(no output — allowed silently, as expected)
```

All 4 cases match Success Criteria exactly: warnings are advisory-only (no `"decision": "block"` in any output), the common case (no field / satisfied dependency) is silent, and the two failure cases (unknown / not-Done) are distinguishable.

---

## UI / Design Acceptance Criteria

N/A — pure-backend/tooling task, section deleted per template instructions. All three UI Evidence rows above marked N/A.

---

## Approach

Extend the existing, already-proven pattern from the `feat/deterministic-guardrails-hooks` branch (declare a claim, verify it cheaply at an existing gate — not a new heavyweight system):

1. **Template**: add `## Dependencies & Reachability` to `TASK_GUIDE_template.md` directly after the `## Requirement` section (so it's filled at the same planning step as the rest of Pillar 1), with two fields and inline examples for both the populated and N/A cases.
2. **Hook**: extend `pre_agent_validate_guide.py` — it already parses the spawn prompt for a Task ID and reads `tasks/TASK_GUIDE_Txxx.md`. Add: read the target guide's `Depends on:` line (regex), and if it names a task ID, read `PROJECT_KANBAN.md` and check which section (`Todo`/`In Progress`/`Ready for Review`/`Done`) contains it. Emit a **non-blocking** stderr/context message (do not set `"decision": "block"`) for "not yet Done" or "unknown task ID" cases — this hook's existing block behavior (missing TASK_GUIDE entirely) is unaffected.
3. **code-review skill**: add a step that reads the target task's `Entry point:` field; if present and not `Standalone — N/A`, grep the diff (or repo, since diffs may not always be scoped) for the literal string; report a finding if absent.
4. **CLAUDE.md**: document the section under Stage 2 planning instructions and add one sentence to Stage 4 review responsibilities; explicitly note in the Hard-Stop Gates section (or just above it) that this is advisory and not gate #7.

---

## Edge Case Checklist

- [ ] `Depends on: Txxx` where Txxx doesn't exist anywhere in `PROJECT_KANBAN.md` — must warn "unknown dependency," not silently pass
- [ ] Circular dependency (A depends on B, B depends on A) — out of scope for this task's hook logic (single-hop lookup only); note as a known limitation in the CLAUDE.md doc rather than solving it now (avoids scope creep into graph traversal)
- [ ] Task intentionally starts before its dependency finishes (parallel stub work) — confirmed as a **warning**, not a block, so this pattern stays possible
- [ ] `Entry point:` written as vague prose instead of a literal identifier — code-review step will simply grep-miss and report a finding; the CLAUDE.md doc should instruct Stage 2 authors to use literal, grep-able strings
- [ ] Backend task with an external caller (webhook/cron/consumer outside repo) — `Entry point: Standalone — N/A` with a reason must be accepted without a finding

---

## Files to Change (Predicted)

| File | Change |
|------|--------|
| `templates/TASK_GUIDE_template.md` | Add `## Dependencies & Reachability` section with `Depends on:` / `Entry point:` fields + examples |
| `templates/PROJECT_KANBAN_template.md` | Optional: note in the board legend that `Depends on` lives in the TASK_GUIDE, not the KANBAN line itself (keep KANBAN line format unchanged to avoid churn) |
| `.claude/hooks/pre_agent_validate_guide.py` | Add `Depends on:` parsing + non-blocking KANBAN status check |
| `.claude/skills/code-review/SKILL.md` | Add entry-point reachability check step |
| `CLAUDE.md` | Document new TASK_GUIDE section; clarify advisory (not Hard-Stop) status |

## Files Must NOT Touch

| File | Reason |
|------|--------|
| `.claude/hooks/pre_bash_block_unsafe_merge.py` | Verify-evidence gate is a separate concern from dependency ordering — confirmed in `BRAINSTORMING_LOG.md` Surgical Scope |
| `PROJECT_KANBAN.md`'s `## Blocked` table (template or live file) | Stays a separate manual mechanism per `AskUserQuestion` answer ("Keep separate") |
| Hard-Stop Gates 1–6 numbering in `CLAUDE.md` | This is a new advisory layer, not a 7th hard-stop gate |

---

## Test Plan

No automated test framework exists for the Python hooks in this repo (prior hook changes were verified the same way — manual JSON-over-stdin transcripts + `py_compile`). Follow that established pattern: pipe synthetic `PreToolUse` events through `pre_agent_validate_guide.py` covering the 4 Success Criteria cases above, and paste the transcripts into the Evidence table.

---

## Completion Checklist

- [x] Implementation done
- [x] Self-review: `Skill({ skill: "code-review" })` run — 0 P0/P1/P2, 2 P3 (documentation polish, not applied per Phase 4 advisory-only rule)
- [x] Security review: N/A (Low risk)
- [x] Lint passes (`py_compile` on the touched hook)
- [x] Tests written AND pass — manual transcripts pasted into Evidence table (Hard-Stop Gate 5)
- [x] `Skill({ skill: "verify" })` run — N/A, no running app; manual hook transcripts serve as the verify evidence instead
- [ ] `memory/MEMORY.md` updated (new decision + one-liner)
- [x] Supervisor notified: task ready for Stage 4 review
