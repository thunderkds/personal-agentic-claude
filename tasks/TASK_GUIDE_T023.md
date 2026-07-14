# TASK_GUIDE — T023: craft-spawn-prompt skill + wire Stage 3 / bugfix to it
**Date**: 2026-07-14
**Complexity Level**: C2
**Risk Level**: Low
**Priority**: P1
**Assigned agent**: backend-developer
**Agent guide**: `.claude/agents/backend.md`

---

## Dependencies & Reachability
- Depends on: T022 (the hook's task-ID extraction must be hardened first — this skill's own pre-flight check, and its generated prompts, should reflect the final/hardened hook behavior, not the pre-fix one)
- Entry point: `Skill({ skill: "craft-spawn-prompt" })` — invoked from `CLAUDE.md` Stage 3 and `.claude/skills/bugfix/SKILL.md` Step 4

---

## Mandatory Startup (Do Not Skip)
1. Read `PROJECT_SPEC.md`
2. Read `memory/MEMORY.md`
3. Read this file completely
4. Read `.claude/agents/backend.md`
5. Read `.claude/skills/bugfix/SKILL.md` Step 4, `.claude/agents/general-agent-template.md`, and `CLAUDE.md` Stage 3 in full before drafting — the new skill's output contract must satisfy both existing consumers.

---

## Requirement (Pillar 1 — Adapt the requirement)

Brainstorming (`BRAINSTORMING_LOG.md`, 2026-07-14) selected Option B. This task is the second half: build the `craft-spawn-prompt` skill and wire the two existing spawn-prompt call sites to it, so they can't drift apart again.

**Restated intent**: a new skill that, given a `tasks/TASK_GUIDE_Txxx.md` path (and implicitly `memory/MEMORY.md` + the relevant `.claude/agents/*.md`), assembles a complete, well-formed sub-agent spawn prompt — detecting whether the guide is a standard Stage 3 task or a bugfix-flavored task (has a "Mental Model" section) and assembling the right shape for each. Even though T022 hardens the hook to stop false-positive-blocking on prose mentions, this skill should still include a lightweight pre-flight sanity check (mirroring the hook's *final* structural-reference pattern) so the Supervisor gets a clear warning if an assembled prompt would still be rejected, rather than discovering it only after the `Agent()` call fails.

**Out of scope**:
- Does not call the `Agent` tool itself — skills run inline in the Supervisor's context; the skill returns the assembled prompt text, and the Supervisor still issues the `Agent()` call.
- Does not change `general-agent-template.md`'s expected-input contract — the assembled prompt must satisfy it as-is (MEMORY.md pasted, TASK_GUIDE + agent-guide pointers present).
- Does not change the `Depends on:` advisory-warning behavior from T017 — this skill assembles the prompt; the hook still independently checks dependencies and issues its own advisory warning at spawn time, unchanged.

**Requirement Refs**: none (internal tooling).

### Requirement Fidelity Gate (sign off BEFORE implementation)
- [x] Restated intent confirmed to match the request (Supervisor, informed by approved brainstorming Option B)

---

## Complexity & Risk
- Complexity: C2 (new skill + two call-site edits, real design decision on prompt-shape detection)
- Risk: Low (no hard-block/guardrail logic changes here — that's T022; this task only produces text and edits doc/skill files)

## Task

1. **Draft the skill** at `.claude/skills/craft-spawn-prompt/SKILL.md` (use `templates/SKILL_template.md` shape; consult `.claude/skills/write-better-skill/SKILL.md` for craft conventions). It must:
   - Accept a TASK_GUIDE path (and optionally an explicit "bugfix mode" flag, though auto-detection via a "Mental Model" section heading is preferred).
   - Read the guide, the relevant `.claude/agents/*.md` (from the guide's `**Assigned agent**`/`**Agent guide**` field), and `memory/MEMORY.md`.
   - Assemble the prompt per the 5-element checklist already proven in `bugfix` Step 4 (guide pointer, mental-model-or-restated-intent, first-action skill invocation if the task type requires one e.g. `diagnose` for bugfixes, `MEMORY.md` verbatim, agent-guide pointer) — for non-bugfix tasks, the "mental model" element becomes the guide's Restated Intent / Requirement section instead.
   - Run the pre-flight structural-reference check (mirroring T022's hardened hook pattern) over the assembled text and flag — not silently fix — any token that would still trip the hook.
   - Set the spawn model recommendation per Complexity (C0→haiku, C1→sonnet, C2→sonnet/opus, C3→opus), matching the table already in `CLAUDE.md` Stage 3 / `.claude/agents/general-agent-template.md`.
   - Output the assembled prompt as a fenced block the Supervisor pastes into `Agent()` — this skill does not call `Agent` itself.

2. **Wire `CLAUDE.md` Stage 3**: replace the current ad hoc "Tell the user the exact command to spawn..." bullet with an instruction to invoke `Skill({ skill: "craft-spawn-prompt" })` first, then issue the `Agent()` call with its output.

3. **Wire `.claude/skills/bugfix/SKILL.md` Step 4**: replace the inline 5-element checklist restatement with a pointer to `craft-spawn-prompt`, keeping the bugfix-specific instruction ("must invoke `diagnose` as first action") as an input to the skill rather than a duplicated rule.

4. Update the skills table in `CLAUDE.md`'s "Skills vs Agents" section to register the new skill (name, definition path, when to use).

## Diagnosis / Fix Gates
- [x] Manually dry-run the skill against `tasks/TASK_GUIDE_T021.md` (a plain Stage-3-style task, no Mental Model section) and confirm it assembles a correct, non-bugfix-shaped prompt.
- [x] Manually dry-run the skill against `tasks/TASK_GUIDE_T018.md` (a bugfix-shaped task, has a Mental Model section) and confirm it detects bugfix mode and includes the mental model + `diagnose` first-action instruction.
- [x] Confirm the pre-flight check correctly flags a synthetic prompt containing a prose-only mention of a missing-guide task ID (using T022's final hardened pattern definition) as "would still be rejected" vs. a clean prompt as "safe."
- [x] Confirm `CLAUDE.md` Stage 3 and `bugfix` Step 4 both now point to the skill and no longer contain divergent restatements of the same checklist.

## Cleanup Checklist
- [x] No scratch files left behind
- [x] Commit message references T022's final hook pattern (must match, not guess) — N/A, no commit made per instructions; Supervisor to reference T022's `extract_structural_task_ids` when committing.

## Evidence
| Check | Command / observation | Result |
|---|---|---|
| Dry-run: Stage-3-style guide | `grep -n "Mental Model" tasks/TASK_GUIDE_T021.md` → no match; manually walked skill logic against `tasks/TASK_GUIDE_T021.md` | Correctly detected "standard" flavor (no Mental Model heading). Assembled prompt uses T021's Restated Intent block ("reword the two prose mentions so they no longer contain a bare T013/T014 token...") as element 2, omits the first-action skill invocation (no schema/migration work declared), pastes `memory/MEMORY.md` verbatim as element 4, and points to `.claude/agents/backend.md` as element 5. Model recommendation: haiku (Complexity C0). |
| Dry-run: bugfix-style guide | `grep -n "Mental Model" tasks/TASK_GUIDE_T018.md` → matched line 9 | Correctly detected "bugfix" flavor. Assembled prompt uses T018's confirmed Mental Model block verbatim (Observed/Expected/Likely divergence/Recent context) as element 2, includes `Skill({ skill: "diagnose" })` as first action (element 3, always present for bugfix flavor), pastes `memory/MEMORY.md` verbatim as element 4, points to `.claude/agents/backend.md` as element 5. Model recommendation: sonnet (Complexity C1). |
| Pre-flight check: clean vs. flagged case | `python3` run importing `extract_structural_task_ids` logic verbatim from `.claude/hooks/pre_agent_validate_guide.py` against two synthetic strings: prose-only `"Note: earlier we confirmed T099 has no guide and was descoped in review."` vs structural `"See tasks/TASK_GUIDE_T099.md for full scope."` (T099 has no guide on disk) | `prose_only ids: []` (not flagged — correctly ignored, matches T022's hardened intent) vs `structural ids: ['099']` with `os.path.exists('tasks/TASK_GUIDE_T099.md') == False` → flagged as "would be rejected by the spawn hook." |
| Smoke suite | No repo-wide automated test suite exists for this doc/skill-framework repo (no `tests/` root, confirmed same as T018's precedent). Verified via manual dry-run walkthroughs above plus a real Python execution of the hook's own `extract_structural_task_ids` pattern (not a re-derived approximation) against representative prompt fragments. | Both dry-runs produced the expected prompt shape; pre-flight check produced the expected safe/flagged split. `CLAUDE.md` Stage 3 and `bugfix` Step 4 both now delegate to `craft-spawn-prompt` with no duplicated checklist prose remaining. |
