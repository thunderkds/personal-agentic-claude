# TASK_REVIEW — T250: Gates tell this session's work from a parallel session's; a blocked verify falls back to the user's `/verify`

> Sibling of `tasks/TASK_GUIDE_T250.md`. Everything here is **filled by the reviewer at Stage
> 4/5** — it is deliberately NOT in the guide, because the implementing agent re-reads the guide on
> every turn and never fills these two sections.
>
> Consumers resolve each section **guide first, this file second** (`.claude/hooks/lib/guide_sections.py`):
> a legacy guide that still carries these sections inline keeps working unchanged, and a stray
> review file can never override an inline section.

---

<!-- Optional: the final report, only for a task run in auto mode (the user's `[auto]` tag,
`docs/claude-md/tracks.md` `## Auto mode`). To use it, copy the block below out of this comment, to this
place, and replace every <...>. Keep `Mode: auto` as its first line, exactly as written: T182's hook reads
it. Write it to this file before the run ends; the chat message is a copy, not the report. The same
block is the Supervisor's final chat message. It is not the `delivery-report` page and not
Evidence. A taste decision (what the user wants) also ends with the flag. Write `DEBATED` only when ≥2
Advocate `Agent` calls ran for that question, naming each Advocate's option. A decision with no Advocates is
labelled `RULE`, `FACT` or `SAFER OPTION`, never `DEBATED`. A decision flagged `⚠ decided for you` is a choice, and is never labelled `FACT`. A
safety action a rule requires (for example the backup before a delete) is `RULE` without the flag.
At Risk Medium or High, a `RULE:` counts only when it names a written rule (`path:line`,
`path § <heading>`, or `docs/claude-md/tracks.md` `### <section>`), and a `FACT:` needs a Citation
(`path:line "quoted text"`); without one it is a choice and must be `DEBATED`. Good: `2. backed up the CSV
— RULE: `docs/claude-md/tracks.md` `### Stops that stay``. Bad: `1. kept recurring.csv — RULE: Surgical Changes`.
`Memory:` records the diff-driven memory pass you run before you stop: each entry written, or `nothing new`.
After an auto verify pass the hook, never you, adds `Closed: row moved to Done <date> — …` and moves the row,
or adds `Paused: done not moved — <reason>`. It moves the row only when this block holds `Mode: auto`, a
numbered decision, `Checks:`, `Memory:`, the `Not done:` auto verify slot with its result, and `Not done:`
naming the merge — no `<...>` left (`docs/claude-md/tracks.md` `### Auto close-out`).

## Auto decisions

Mode: auto
1. <what was decided> — RULE: <the rule>
2. <what was decided> — FACT: <path>:<line> "<quoted text>"
3. <what was decided> — DEBATED: <option> (Advocate 1: <its proposal>; Advocate 2: <its proposal>) ⚠ decided for you — please review
4. <what was decided> — SAFER OPTION: <why> ⚠ decided for you — please review
Paused: <only when a stop that stays paused the task: which one, and why>
Checks: tests `<command>` — <result>; reviews <skill — result>; real run `<command>` — printed `<what it printed>` (auto-checked, not /verify)
Memory: <each entry the memory pass wrote, as `file — entry` | nothing new>
Not done: merge (yours); <auto verify: running (T182) | auto verify: <result> | /verify (yours)>

-->

## Evidence

| Check | Result | Notes / output snippet |
|-------|--------|------------------------|
| **New test(s) cover Acceptance Criteria (file paths pasted)** | ☑ pass | `.claude/hooks/tests/test_t250_session_ownership.py` — 102 tests for AC 1–8, `102 passed in 8.70s` (2026-11-04, `3c01a43b`). Written test-first; red before each change: `ModuleNotFoundError: No module named 'session_work'` (tracer); G2 `2 failed, 51 passed`; G1 `4 failed, 66 passed`; G3 `1 failed, 77 passed` (exactly the T249 case); real-transcript false positives `3 failed` then pass. Stage 4 fix pass (+17): paths with a space / symlinked worktree, 10:40:35Z `7 failed, 2 passed, 85 deselected` then `94 passed`; stacked branch cut from an In Progress task's branch, 10:41:15Z `5 failed, 13 passed, 83 deselected` then `101 passed`; Stop hook with a `load_work` that raises still checks the task (`2 passed`; mutated to treat the error as not-owned: `1 failed`). `.claude/hooks/tests/test_stop_auto_mode_check.py`: the session's own `Write` added to `test_a_non_auto_task_is_ignored`, `test_check1_ignores_a_guide_older_than_the_auto_request`, `test_t229_a_task_touched_after_a_later_plain_request_is_not_auto` — each passes; each window-rule mutation (code-span strip removed / window start ignored / plain request no longer closes the window) makes the new test `1 failed` and the old test `1 passed` (mutations reverted). Four other T229 window fixtures show the session's own `Write` (AC 7 changes their outcome by design) |
| Verification command run | ☑ pass | Guide line as written, wt-t250 at `365379ce`, 2026-11-04T09:15:28Z: `[hook:pre_bash] T249 is In Progress, but this session did not work on it and this merge does not bring in its branch — not blocking (T250)` then block with only `Tasks still In Progress: T250` and Ready for Review `T248, T246, T230 (no evidence row)` (T246's real record has no user line; not edited). Board-state copy (scratch clone of wt-t246 with T250 hooks, main's board, user line for `5244fce5…`), 09:16:46Z — A, session f5ea81bb's transcript: T249 not blocking, blockers `T250` + `T248, T230 (no evidence row)`: T246 accepted. B, a folder without f5ea81bb.jsonl: `cannot read this session's transcript — every In Progress task blocks this merge`, blockers `T250, T249` + `T248, T246, T230 (no evidence row)`: pass |
| Negative cases hold | ☐ pass / ☐ fail | |
| verify | ☐ pass / ☐ fail / ☐ N/A | [what was observed — must literally state "pass" or "fail" here too, e.g. "skill run, feature confirmed working — pass": the merge gate scans this Notes column for the word "pass", not just the Result column] |
| Review scope bounded to the change's blast radius (affected set, not whole repo) | ☐ pass / ☐ fail | [what was reviewed vs. skipped, and why] |
| Full smoke suite still green (no regression) | ☑ pass | `python3 -m pytest .claude/hooks/tests/ tests/ -q` on the branch at `3c01a43b` (the fix commit before it was amended to add only this review file — same code), 2026-11-04T10:57:38Z–11:02:14Z: `3266 passed, 25 subtests passed in 275.36s (0:04:35)`; `main` at `f3f24ac7`: `3163 passed, 25 subtests passed in 182.95s (0:03:02)` — +103 = 102 new T250 tests + 1 net elsewhere, 0 failed. One earlier run at 10:49:00Z had `1 failed, 3265 passed` (`tests/test_auto_verify.py::test_ac5_fail_record_blocks_even_if_the_row_is_edited_to_pass`, a `WAIT_S` wait on a detached run under host load); it passed 3/3 alone and `tests/test_auto_verify.py` gave `254 passed` |
| **Companion score (easy-verifier)** | ☐ pass / ☐ fail / ☐ N/A | [`overall` and `change_risk` as the tool returned them, the scope, the ref, and the absolute path of the verifier report after a literal `report:` label — e.g. "overall 86 (>= 80), change_risk pass, scope changes, ref `main...HEAD`, report: `/home/me/.easy-verifier-reports/kit/score_changes_20261028T0530Z.html`". The gate reads the path that follows `report:` and nothing else, so with no label, or a path that is absent, the row is unscored — write ☑ N/A instead. ☑ N/A with a reason when neither companion tool was run: the merge gate blocks on ☑ fail only, never on an absent or N/A row] |
| **UI: Visual regression (diff or verdict pasted)** | ☐ pass / ☐ fail / ☐ N/A | [screenshot path or LLM verdict — required for UI tasks, Hard-Stop Gate 6] |
| **UI: Design-system compliance (tokens/colors/typography verified)** | ☐ pass / ☐ fail / ☐ N/A | [method used + output] |
| **UI: Responsiveness at target viewports** | ☐ pass / ☐ fail / ☐ N/A | [viewports tested, any overflow findings] |

---

## Demonstration

> Anchors what this task delivered to an observable before/after pair. BEFORE has no `N/A` path:
> if the task changes executable code, BEFORE is a pasted, timestamped terminal capture taken
> **before any implementation commit exists**; if it does not (docs, templates, skill-instruction
> text), BEFORE is the **verbatim prior content** of what changed — a quoted excerpt, not a command.

**BEFORE** (captured 2026-11-04T08:56:33Z in `../wt-t250` at `f3f24ac7`, before any implementation commit; session f5ea81bb has never edited T249's files, and its transcript holds the user's `/verify T246`):
```
$ echo '{"tool_name":"Bash","tool_input":{"command":"git merge --no-ff fix/t246-x"},"transcript_path":"…/f5ea81bb-c349-4953-9f6b-0307a641966a.jsonl","session_id":"f5ea81bb-…","cwd":"…/personal-agentic-claude"}' | python3 .claude/hooks/pre_bash_block_unsafe_merge.py
{"decision": "block", "reason": "[hook:pre_bash] Pipeline gate failed — cannot push/merge:\n  • Tasks still In Progress: T250, T249\n  • Tasks in Ready for Review missing Stage 5 verify evidence: T246 (no evidence row)\n…"}
```
G3, from this session's Stop hook (every stop since 2026-11-04 ~08:31Z):
```
[hook:stop_auto_mode_check] Auto-mode final report check failed — fix it before you stop (docs/claude-md/tracks.md `## Auto mode`):
  • T249: tasks/TASK_REVIEW_T249.md has no `## Auto decisions` section starting with `Mode: auto`
  • T249: no `Memory:` line in the report — run the memory pass before you stop and record it there (each entry written, or `Memory: nothing new`)
```

**AFTER** (2026-11-04T09:15:28Z, wt-t250 at `365379ce`, the guide's real-run line as written):
```
[hook:pre_bash] T249 is In Progress, but this session did not work on it and this merge does not bring in its branch — not blocking (T250)
{"decision": "block", "reason": "[hook:pre_bash] Pipeline gate failed — cannot push/merge:\n  • Tasks still In Progress: T250\n  • Tasks in Ready for Review missing Stage 5 verify evidence: T248 (no evidence row), T246 (no evidence row), T230 (no evidence row)\n…"}
exit=0
```
With T246's user line (`- verify: ☑ pass — /verify by the user, session f5ea81bb-c349-4953-9f6b-0307a641966a, commit 5244fce5adeb30cce9e11293d7bd3441af289516`) in a scratch copy of the board state, 09:16:46Z:
```
== A: session f5ea81bb's own transcript
[hook:pre_bash] T249 is In Progress, but this session did not work on it and this merge does not bring in its branch — not blocking (T250)
BLOCK: … • Tasks still In Progress: T250
  • Tasks in Ready for Review missing Stage 5 verify evidence: T248 (no evidence row), T230 (no evidence row)
== B: a transcripts folder without f5ea81bb.jsonl
[hook:pre_bash] cannot read this session's transcript — every In Progress task blocks this merge
BLOCK: … • Tasks still In Progress: T250, T249
  • Tasks in Ready for Review missing Stage 5 verify evidence: T248 (no evidence row), T246 (no evidence row), T230 (no evidence row)
```

**DELTA**: A merge no longer waits on another session's In Progress task, and the user's own `/verify` now opens the gate after a blocked auto run.

**WITNESS**: [who ran it and when — derived from `memory/event-trace/T250.jsonl`, never the
implementing agent alone]
