# TASK_REVIEW — T169: Writing Principles (ASD-STE100) for text a human reads only

> Sibling of `tasks/TASK_GUIDE_T169.md`. Everything here is **filled by the reviewer at Stage
> 4/5** — it is deliberately NOT in the guide, because the implementing agent re-reads the guide on
> every turn and never fills these two sections.
>
> Consumers resolve each section **guide first, this file second** (`.claude/hooks/lib/guide_sections.py`):
> a legacy guide that still carries these sections inline keeps working unchanged, and a stray
> review file can never override an inline section.

---

## Evidence

| Check | Result | Notes / output snippet |
|-------|--------|------------------------|
| **New test(s) cover Acceptance Criteria (file paths pasted)** | ☑ pass | `tests/test_writing_principles.py` (7 tests: AC1–AC8, AC10; written first, RED 6 failed / 1 passed at 19e2d5d's parent per agent). Supervisor re-run 2026-10-20 at d653337: `24 passed in 0.03s` (with test_provider_adapters.py, test_response_standard.py). AC9 is a measurement, not a test: BEFORE `attachment:instructions` 5,273 tokens (Supervisor session, `token_meter --current`); AFTER pending a new session post-merge |
| Verification command run | ☑ pass | `python3 -m pytest -q tests/test_writing_principles.py tests/test_provider_adapters.py tests/test_response_standard.py` → `24 passed in 0.03s` |
| Negative cases hold | ☑ pass | Supervisor mutants on d653337, each reverted: M1 drop keep-the-term sentence → `1 failed, 6 passed`; M2 scope "only to text a human reads"→"to all text" → `1 failed, 6 passed`; M3 append table row to `agents/qa.md` → `1 failed, 6 passed` |
| verify | ☐ pass / ☐ fail / ☐ N/A | [what was observed — must literally state "pass" or "fail" here too, e.g. "skill run, feature confirmed working — pass": the merge gate scans this Notes column for the word "pass", not just the Result column] |
| Review scope bounded to the change's blast radius (affected set, not whole repo) | ☑ pass | Reviewed the 8 changed files + pin tests that read CLAUDE.md. lane_check: `EXCEEDS (files 7 > 6); unpredicted: test_agent_guide_dedup.py, test_vital_slice.py` — pin edits, cap 202→218 user-approved 2026-10-20. code-review: 0 P0, 1 P1 (template pointer dangled for sub-agents — fixed 19c139f), 1 P3 (duplicate scope sentence — fixed 19c139f). Startup reads line complete |
| Full smoke suite still green (no regression) | ☑ pass | `python3 -m pytest -q tests .claude/hooks/tests` → `1382 passed, 25 subtests passed in 30.32s` (exit 0); `bash tests/test_update_claude_md.sh` → `35 passed, 0 failed` |
| **UI: Visual regression (diff or verdict pasted)** | ☑ N/A | Docs/rules task — no UI component |
| **UI: Design-system compliance (tokens/colors/typography verified)** | ☑ N/A | Docs/rules task — no UI component |
| **UI: Responsiveness at target viewports** | ☑ N/A | Docs/rules task — no UI component |

---

## Demonstration

> Anchors what this task delivered to an observable before/after pair. BEFORE has no `N/A` path:
> if the task changes executable code, BEFORE is a pasted, timestamped terminal capture taken
> **before any implementation commit exists**; if it does not (docs, templates, skill-instruction
> text), BEFORE is the **verbatim prior content** of what changed — a quoted excerpt, not a command.

**BEFORE**: Captured 2026-10-20T05:00:52Z, before any implementation commit. Docs change, so BEFORE is the prior state.

Command: `grep -n "Writing Principles" CLAUDE.md agents/*.md AGENTS.md .cursor/rules/agent-base.mdc` -> no output, exit 1.

Prior `CLAUDE.md` Response Standard bullet (line 35, verbatim):
> - Write for a reader who hasn't followed the project, above all when asking them to decide: plain words; a task ID or internal term gets a few words saying what it is; technical depth only when asked.

Prior `CLAUDE.md` section order: `## Karpathy Engineering Principles` (line 109) is followed directly by `## Code Naming Conventions` (line 127). `AGENTS.md` and `.cursor/rules/agent-base.mdc` list only the 4 Karpathy names.

AC 9 token_meter BEFORE (`python3 scripts/token_meter.py --current --json`, main checkout, this implementer session, not a baseline of a Supervisor session): calls 44, spend_usd 3.853, context_now 127710, calls_over_150k 0. The AFTER row is left for the Supervisor.

**AFTER**: [same command, post-change] OR [verbatim excerpt of the new content]

**DELTA**: [one sentence — what a user can now do that they could not before]

**WITNESS**: [who ran it and when — derived from `memory/event-trace/Txxx.jsonl`, never the
implementing agent alone]
