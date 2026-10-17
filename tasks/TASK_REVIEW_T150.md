# TASK_REVIEW — T150: Spawns run as background agents, and `wake` flags work a dead agent left behind

> Sibling of `tasks/TASK_GUIDE_T150.md`. Everything here is **filled by the reviewer at Stage
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
| **New test(s) cover Acceptance Criteria (file paths pasted)** | pass | tests/test_dirty_worktrees.py (10 tests, SC1-SC6): `10 passed` |
| Verification command run | pass | `python3 -m pytest tests/test_dirty_worktrees.py -q` -> 10 passed; script on this repo (from wt-t150) -> clean once committed |
| Negative cases hold | ☐ pass / ☐ fail | |
| verify | ☐ pass / ☐ fail / ☐ N/A | [what was observed — must literally state "pass" or "fail" here too, e.g. "skill run, feature confirmed working — pass": the merge gate scans this Notes column for the word "pass", not just the Result column] |
| Review scope bounded to the change's blast radius (affected set, not whole repo) | ☑ pass | Supervisor Stage 4 code-review 2026-10-17, `07172d2...HEAD`: dirty_worktrees.py, test_dirty_worktrees.py, wake/SKILL.md, craft-spawn-prompt/SKILL.md, pipeline-stages.md; lane `C1, 5 files, 196 lines, FITS`. Findings: P1×1 fixed in `6a327fe` (wake line asserted a dead agent; a live concurrent session leaves the same signal); P2×1 suggested (`git --no-optional-locks status`); P3×2 suggested (wake still says "four" sources; `t(\d{3})` breaks at T1000). `10 passed` after fix — pass |
| Full smoke suite still green (no regression) | pass | `python3 -m pytest tests/ .claude/hooks/tests/ -q` -> 1097 passed, 25 subtests passed in 34.11s |
| **UI: Visual regression (diff or verdict pasted)** | ☐ pass / ☐ fail / ☐ N/A | [screenshot path or LLM verdict — required for UI tasks, Hard-Stop Gate 6] |
| **UI: Design-system compliance (tokens/colors/typography verified)** | ☐ pass / ☐ fail / ☐ N/A | [method used + output] |
| **UI: Responsiveness at target viewports** | ☐ pass / ☐ fail / ☐ N/A | [viewports tested, any overflow findings] |

---

## Demonstration

> Anchors what this task delivered to an observable before/after pair. BEFORE has no `N/A` path:
> if the task changes executable code, BEFORE is a pasted, timestamped terminal capture taken
> **before any implementation commit exists**; if it does not (docs, templates, skill-instruction
> text), BEFORE is the **verbatim prior content** of what changed — a quoted excerpt, not a command.

**BEFORE** (captured 2026-10-17T08:56:00Z, before any implementation commit):

```
$ python3 -m pytest tests/test_dirty_worktrees.py -q
no tests ran in 0.00s
$ python3 skills/wake/scripts/dirty_worktrees.py
python3: can't open file '.../skills/wake/scripts/dirty_worktrees.py': [Errno 2] No such file or directory
```

Prior doc text. `skills/craft-spawn-prompt/SKILL.md` Output (#6), item 4 ended: "`Agent()` spawns are **not** sandboxed — they run with the Supervisor's permissions; say so whenever you pick that path." `docs/claude-md/pipeline-stages.md` Stage 3 has no Spawn-mode bullet: the `craft-spawn-prompt` bullet ends "Then issue the `Agent()` call in that worktree using its output." `skills/wake/SKILL.md` Step 1 reads "four live authoritative sources" (git log, KANBAN, MEMORY.md, LRs) and has no worktree check.

**AFTER**: [same command, post-change] OR [verbatim excerpt of the new content]

**DELTA**: [one sentence — what a user can now do that they could not before]

**WITNESS**: [who ran it and when — derived from `memory/event-trace/Txxx.jsonl`, never the
implementing agent alone]
