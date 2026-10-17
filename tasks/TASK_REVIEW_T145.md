# TASK_REVIEW — T145: A spawned agent inherits past decisions about its files, and compound leads with the general lesson

> Sibling of `tasks/TASK_GUIDE_T145.md`. Everything here is **filled by the reviewer at Stage
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
| **New test(s) cover Acceptance Criteria (file paths pasted)** | ☑ pass | `tests/test_memory_slice.py` (8 `test_t145_*` tests appended; the 21 existing untouched): `29 passed in 0.62s`
| Verification command run | ☑ pass | `python3 -m pytest tests/test_memory_slice.py -q` -> `29 passed`; live T137 run (2026-10-17T05:10:22Z) ends with `- **T137 merged (2026-10-08): a backup is named after the kit version it replaces; Update's `[o]verwrite` backs up too.** → memory/decisions.md`; **fix round 1** (P2: hot at cap hid matched cold entries): `python3 -m pytest tests/test_memory_slice.py -q` -> `30 passed in 0.71s` (new `test_t145_fix1_hot_at_cap_still_reports_dropped_cold_entries`) -- pass
| Negative cases hold | ☑ pass | prose-only mention and no-Files-line entries not selected; missing decisions.md silent. Mutation (cold pass disabled): `5 failed, 24 passed`, SC1 RED |
| verify | ☐ pass / ☐ fail / ☐ N/A | [what was observed — must literally state "pass" or "fail" here too, e.g. "skill run, feature confirmed working — pass": the merge gate scans this Notes column for the word "pass", not just the Result column] |
| Review scope bounded to the change's blast radius (affected set, not whole repo) | ☐ pass / ☐ fail | [what was reviewed vs. skipped, and why] |
| Full smoke suite still green (no regression) | ☐ fail (pre-existing) | `.claude/hooks/tests/ tests/`: 5 failed / 1044 passed; same 5 MEMORY.md hot-tier budget tests fail on the untouched base (5 failed / 1036 passed) -- not caused by T145 |
| **UI: Visual regression (diff or verdict pasted)** | ☐ pass / ☐ fail / ☐ N/A | [screenshot path or LLM verdict — required for UI tasks, Hard-Stop Gate 6] |
| **UI: Design-system compliance (tokens/colors/typography verified)** | ☐ pass / ☐ fail / ☐ N/A | [method used + output] |
| **UI: Responsiveness at target viewports** | ☐ pass / ☐ fail / ☐ N/A | [viewports tested, any overflow findings] |

---

## Demonstration

> Anchors what this task delivered to an observable before/after pair. BEFORE has no `N/A` path:
> if the task changes executable code, BEFORE is a pasted, timestamped terminal capture taken
> **before any implementation commit exists**; if it does not (docs, templates, skill-instruction
> text), BEFORE is the **verbatim prior content** of what changed — a quoted excerpt, not a command.

**BEFORE** (captured before any implementation commit; `python3 -m pytest tests/test_memory_slice.py -q; python3 skills/craft-spawn-prompt/scripts/memory_slice.py tasks/TASK_GUIDE_T137.md`, lines truncated to 160 chars; note: no `### From decisions.md` section, the T137 cold entry title "**T137 merged (2026-10-08): a backup is named after the kit version it replaces...**" is absent):

```
2026-10-17T05:09:19Z
.....................                                                    [100%]
21 passed in 0.40s
<!-- memory-slice:T137 -->
memory/MEMORY.md — 12 of 249 index lines matched on: lib/harness-fetch.sh, setup.sh, PROJECT_KANBAN.md, memory/, .claude/hooks/, T137
### Decisions
- [The push gate reads the board and the trace](learnings.md) — set `.claude/hooks/.state/active_task` before a task's verification work, or its Bash calls are 
- [Codebase Map](codebase-map.md) — structural snapshot (tree, entry points, hotspots) in memory/codebase-map.md; C2/C3 agents read it
- [learn skill: Learning Record System](decisions.md) — LR files in memory/learning-records/
- [T031/T032/T033 merged: the direct-install trio](decisions.md) — shared lib/harness-fetch.sh + per-file harness-lock.json + hash-lock update
- [setup.sh clones the remote, so unmerged work is unverifiable](learnings.md) — an install can run green and build a tree without your change
- [T137 merged: backups named `<file>.bak-<prev kit_commit>`, Update `o` backs up](decisions.md) — lock gains `kit_commit`; date fallback; hex-only from the loc
### Patterns & Gotchas
- [A short SHA is hex — lock pair regex would read `kit_commit` as a file](learnings.md) — scope lock readers to the `"files"` block (T137)
- [The merge gate reads one board by name](learnings.md) — `pre_bash_block_unsafe_merge.py` checks `PROJECT_KANBAN.md` only, so T083's site board was ungated at
- [`pytest tests/ -q` runs 8 tests, not 688](learnings.md) — the suite lives in `.claude/hooks/tests/` and bare pytest skips hidden dirs; Always `python3 -m pyt
- [CLAUDE.md gains Supervisor Communication Style section, 2026-08-03](decisions.md) — lives in the harness's master CLAUDE.md so setup.sh propagates to other r
- [Kanban merge hygiene when both sides edit the board](learnings.md) — restore Supervisor-side PROJECT_KANBAN.md to the merge base BEFORE merging (only branch 
- [A memory pass is uncommitted work like any other, and stashes hide it](learnings.md) — T046 shipped with a merged commit, passing tests and a closed row, yet
<!-- /memory-slice -->
```

**AFTER** (2026-10-17T05:10:22Z, same T137 command, tail): the slice now ends with `### From decisions.md`, a header line, and `- **T137 merged (2026-10-08): a backup is named after the kit version it replaces; Update's `[o]verwrite` backs up too.** → memory/decisions.md`. `skills/compound/SKILL.md` template now opens `## The General Lesson`, `## Applies When`, then `## Problem`.

**DELTA**: A spawned agent now sees the titles of past decisions that named its files, and new compound docs lead with the reusable lesson.

**WITNESS**: [who ran it and when — derived from `memory/event-trace/Txxx.jsonl`, never the
implementing agent alone]
