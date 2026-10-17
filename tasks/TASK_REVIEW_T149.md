# TASK_REVIEW — T149: `ship` won't recommend GO for production until a human has approved that exact version

> Sibling of `tasks/TASK_GUIDE_T149.md`. Everything here is **filled by the reviewer at Stage
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
| **New test(s) cover Acceptance Criteria (file paths pasted)** | pass | tests/test_ship_approval_gate.py (6 tests) |
| Verification command run | pass | `python3 -m pytest tests/test_ship_approval_gate.py -q` -> `6 passed in 0.02s`. Mutation (approval line deleted) -> `1 failed, 5 passed` (test_gate_has_approval_line) |
| Negative cases hold | ☐ pass / ☐ fail | |
| verify | ☐ pass / ☐ fail / ☐ N/A | [what was observed — must literally state "pass" or "fail" here too, e.g. "skill run, feature confirmed working — pass": the merge gate scans this Notes column for the word "pass", not just the Result column] |
| Review scope bounded to the change's blast radius (affected set, not whole repo) | ☐ pass / ☐ fail | [what was reviewed vs. skipped, and why] |
| Full smoke suite still green (no regression) | ☐ pass / ☐ fail | |
| **UI: Visual regression (diff or verdict pasted)** | ☐ pass / ☐ fail / ☐ N/A | [screenshot path or LLM verdict — required for UI tasks, Hard-Stop Gate 6] |
| **UI: Design-system compliance (tokens/colors/typography verified)** | ☐ pass / ☐ fail / ☐ N/A | [method used + output] |
| **UI: Responsiveness at target viewports** | ☐ pass / ☐ fail / ☐ N/A | [viewports tested, any overflow findings] |

---

## Demonstration

> Anchors what this task delivered to an observable before/after pair. BEFORE has no `N/A` path:
> if the task changes executable code, BEFORE is a pasted, timestamped terminal capture taken
> **before any implementation commit exists**; if it does not (docs, templates, skill-instruction
> text), BEFORE is the **verbatim prior content** of what changed — a quoted excerpt, not a command.

**BEFORE** (verbatim prior content, 2026-10-17; non-executable change):

`skills/ship/SKILL.md` § 7:
```
- [ ] Stage 5 evidence green for every in-scope task
- [ ] Rollback plan exists with trigger conditions + exact reverse steps
- [ ] Post-deploy health check is defined with a concrete pass condition
- [ ] Deploy command is known (sourced from PROJECT_SPEC.md) — not a TODO
```
`skills/ship/SKILL.md` § 3 post-deploy bullet: "**Post-deploy health check**: an exact command or URL probe with a concrete pass condition ..."
`templates/RUNBOOK_template.md`:
```
| Version / Tag | Date | Scope (Task IDs) | Deployer | Outcome |
```

**AFTER**: `skills/ship/SKILL.md` § 7 now adds `- [ ] Production approval recorded for <version> @ <commit>` plus a "Production approval" paragraph (AskUserQuestion naming version+commit, verbatim answer into Release Log, mismatched version/commit does not satisfy, Supervisor-written record); § 3 adds "Smoke test, defined before the deploy"; RUNBOOK Release Log header gains `Approved (by / when / answer)`. SKILL.md 5.5 KB (<8 KB).

**DELTA**: `ship` cannot recommend GO until the human approved that exact version and commit, and the smoke-test pass condition is fixed before deploying.

**WITNESS**: [who ran it and when — derived from `memory/event-trace/Txxx.jsonl`, never the
implementing agent alone]
