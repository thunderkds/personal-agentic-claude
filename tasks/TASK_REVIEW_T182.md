# TASK_REVIEW — T182: Auto verify — for an `[auto]` task, a hook runs the real `/verify` in a fresh headless session

> Sibling of `tasks/TASK_GUIDE_T182.md`. Everything here is **filled by the reviewer at Stage
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
| AC 1 spike (paid, cap $1, user go 2026-10-27: "182 and 181") | ☑ pass | Supervisor 2026-10-27T14:34:46Z–14:35:39Z, cwd `../wt-t180-auto` (branch `feat/t180-auto-mode`, clean), command: `timeout 900 claude -p "/verify T180" --max-budget-usd 1 --model sonnet --output-format json` (user's normal settings, no `--dangerously-skip-permissions`). Result JSON: `subtype: success`, `is_error: false`, `total_cost_usd: 0.2565`, `num_turns: 7`, `duration_ms: 49612`, `session_id: bb6500c2-6ee9-4ce9-bc0e-ea2f246f2fd4`, `permission_denials: []`. The built-in skill ran: the result is the skill's own report shape, `## Verification: T180 auto-mode Stop hook (D8–D10) …` / `**Verdict:** PASS` / `**Method:** … There is no verifier-* or run-* skill …` / 9 Steps (4 🔍 probes, temp projects via `mktemp`) / Findings. The worktree stayed clean (`git status --short` empty). Raw output kept in `.spawn/t182-spike/run1.json`. Notes for the build: the verdict is the line `**Verdict:** PASS|FAIL|BLOCKED|SKIP` in `result`; a run with no diff vs the base still ran (it measured the branch against `main`). D1 holds: no hand-written equivalent is needed. |
| **New test(s) cover Acceptance Criteria (file paths pasted)** | ☐ pass / ☐ fail | [test file path(s) — required before Done] |
| Verification command run | ☐ pass / ☐ fail | [paste actual output] |
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

**BEFORE**: captured by common-infrastructure at 2026-10-27T14:42:24Z on `7e73811` (before any T182
implementation commit), command `python3 /tmp/claude-1000/-home-hungnguyenhuu-workspace-pets-personal-agentic-claude/55ed681c-3b51-48e8-a01f-66698e543862/scratchpad/t182_demo.py /home/hungnguyenhuu/workspace/pets/wt-t182-auto-verify`
(a temp git project with the kit's hooks and `settings.json`; T951 is `Mode: auto`, Ready for Review, `verify`
row unfilled; `claude` on `PATH` is a stub that logs its argv and prints `**Verdict:** PASS`):

```
$ date -u  -> 2026-10-27T14:42:24Z
kit: /home/hungnguyenhuu/workspace/pets/wt-t182-auto-verify @ 7e73811
temp project head: 46e2d0f591c4; stub claude: /tmp/t182_demo_4pne2y_n/bin/claude

== 1. Stop hooks fire for the [auto] task T951 at Ready for Review ==
  stop_review_reminder.py: exit 0 in 0.02s
  stop_auto_mode_check.py: exit 0 in 0.03s
  stub claude calls: (none)
  verify row: | verify | ☐ pass / ☐ fail / ☐ N/A | [what was observed] |
  .claude/verify-runs/: (absent)

== 2. hand-typed row, no D5 record, no test run in the trace ==
  git merge feat/t951: BLOCK — • Tasks in Ready for Review missing Stage 5 verify evidence: T951 (evidence row present but no verified tool call in memory/event-trace/T951.jsonl)

== 3. same hand-typed row, a test run in the trace ==
  git merge feat/t951: ALLOW
```

Today no Stop hook starts a `/verify` run (the stub is never called, the row stays unfilled). A hand-typed
`☑ pass | auto-run by hook, session forged-1, commit <sha>, … — pass` row is blocked only for the reason any
unverified row is (no test run in the trace); once the trace has a test run, the forged row is accepted.

**AFTER**: [same command, post-change] OR [verbatim excerpt of the new content]

**DELTA**: [one sentence — what a user can now do that they could not before]

**WITNESS**: [who ran it and when — derived from `memory/event-trace/Txxx.jsonl`, never the
implementing agent alone]
