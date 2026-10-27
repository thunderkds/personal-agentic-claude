# TASK_REVIEW — T178: Two tracks — small tasks run on the minimal track without process stops and end with a Decision record; big or risky tasks run on the extended track

> Sibling of `tasks/TASK_GUIDE_T178.md`. Everything here is **filled by the reviewer at Stage
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

**BEFORE**: captured on `feat/t178-tracks` at `8386b17`, before the first implementation commit.

(a) Executable — the real hooks, run by `scratchpad/demo_t178.sh` against a temp project whose board has one
minimal-track row (no guide, only a Decision record) in Ready for Review:

```
captured 2026-10-27T02:35:23Z
$ ls /tmp/tmp.MevxuIg2lo/proj/tasks/ ; ls /home/hungnguyenhuu/workspace/pets/wt-t178-tracks/docs/claude-md/tracks.md /home/hungnguyenhuu/workspace/pets/wt-t178-tracks/templates/MINIMAL_LOG_template.md
MINIMAL_LOG.md
ls: cannot access '/home/hungnguyenhuu/workspace/pets/wt-t178-tracks/docs/claude-md/tracks.md': No such file or directory
ls: cannot access '/home/hungnguyenhuu/workspace/pets/wt-t178-tracks/templates/MINIMAL_LOG_template.md': No such file or directory
$ python3 .claude/hooks/stop_review_reminder.py   (stderr)

============================================================
⚠️  SUPERVISOR: Tasks awaiting Stage 4 Review:
   - [ ] **T901** — Fix the comma bug in amounts | Supervisor | C0 | Risk: Low | P2 | Track: minimal | Record: `tasks/MINIMAL_LOG.md`

Run: Skill({ skill: 'code-review' })
For Medium/High risk: Skill({ skill: 'security-review' })
============================================================

$ echo '{"tool_name":"Bash","tool_input":{"command":"git merge feat/t901"}}' | python3 .claude/hooks/pre_bash_block_unsafe_merge.py
block
[hook:pre_bash] Pipeline gate failed — cannot push/merge:
  • Tasks in Ready for Review missing Stage 5 verify evidence: T901 (no evidence row)
Complete Stage 4 review and Stage 5 verify first.
```

The stop hook asks for `code-review` on a task that has no Stage 4 (wrong for the minimal track); the merge gate
blocks (right, and must stay).

(b) Non-executable — verbatim prior doctrine, `AGENTS.md` at `8386b17`:

```
## 5-Stage Agentic Pipeline
See [`docs/claude-md/pipeline-stages.md`](docs/claude-md/pipeline-stages.md) for full Stage 0.5–5 detail. Strictly follow this order. Never skip or reorder stages.
```
```
- Stage 4 (code-review) is mandatory for every task. Stage 4 security-review is mandatory for Medium/High risk tasks.
```
```
1. **No TASK_GUIDE = no work.** If the user requests any implementation and no `tasks/TASK_GUIDE_Txxx.md` exists for it, the Supervisor must create one through Stage 2 before any code is written — by the Supervisor *or* any agent. The Supervisor must never write implementation code directly.
```

`docs/claude-md/pipeline-stages.md` at `8386b17`, the head before Stage 0.5:

```
# 5-Stage Agentic Pipeline

> Extracted from `AGENTS.md` — full detail for Stage 0.5 through Stage 5. See `AGENTS.md` for the pointer back to this file and the Mandatory Session Startup / Hard-Stop Gates, which remain inline there.

Strictly follow this order. Never skip or reorder stages.
```

`PROJECT_SPEC.md` glossary: no `Minimal track`, `Extended track` or `Decision record` row (only `Decision Log`,
line 74). `templates/MINIMAL_LOG_template.md` and `docs/claude-md/tracks.md`: absent (see (a)).

**AFTER**: [same command, post-change] OR [verbatim excerpt of the new content]

**DELTA**: [one sentence — what a user can now do that they could not before]

**WITNESS**: [who ran it and when — derived from `memory/event-trace/Txxx.jsonl`, never the
implementing agent alone]
