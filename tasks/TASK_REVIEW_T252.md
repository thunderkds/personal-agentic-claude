# TASK_REVIEW — T252: Stop check skips a marked auto task this session did not work on

> Sibling of `tasks/TASK_GUIDE_T252.md`. Everything here is **filled by the reviewer at Stage
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
| **New test(s) cover Acceptance Criteria (file paths pasted)** | ☑ pass | `.claude/hooks/tests/test_t252_marked_ownership.py` (AC 1, 2, 3, 5 + minimal-track edge case); `python3 -m pytest .claude/hooks/tests/test_t252_marked_ownership.py -q` -> `9 passed` (BEFORE: 4 failed, 5 passed). AC 4: `python3 -m pytest .claude/hooks/tests/test_stop_auto_mode_check.py .claude/hooks/tests/test_t250_session_ownership.py -q` -> `189 passed in 14.95s`. AC 6: `docs/claude-md/tracks.md` (Stop-check text, `### Known limits`) |
| Verification command run | ☑ pass | The guide's Verification Command: targeted files `198 passed in 14.77s`; full suite `3293 passed, 25 subtests passed in 191.40s` (implementing agent, after `ce406d9d`). End-to-end through the hook's `main()` with stdin JSON is in `.claude/hooks/tests/test_t252_marked_ownership.py` (AC 5). The live run is the auto verify — pass |
| Negative cases hold | ☑ pass | Fail closed kept: a reader that raises, a missing transcript and an unreadable sub-agent transcript all still block (AC 3 tests); a session's own `Write` of the report, and a sub-agent's, still block (AC 2); a marked minimal-track record with no work by this session is still checked (Stage 4 P1 test `test_edge_a_marked_minimal_track_task_is_still_checked_without_work_by_this_session`) — pass |
| verify | ☐ pass / ☐ fail / ☐ N/A | [what was observed — must literally state "pass" or "fail" here too, e.g. "skill run, feature confirmed working — pass": the merge gate scans this Notes column for the word "pass", not just the Result column] |
| Review scope bounded to the change's blast radius (affected set, not whole repo) | ☑ pass | code-review read `git diff main...HEAD` (5 files) and the one caller, `main()` at `stop_auto_mode_check.py:517`; `lane: C1, 4 files, 187 lines, FITS; unpredicted: .claude/hooks/tests/test_stop_auto_mode_check.py` (the AC 4 fixture change). code-review: one P1 (a marked minimal-track task in the main checkout went unchecked — fixed in `ce406d9d`), one P3 (two tests keep an unneeded `_wrote_report` entry — left). Startup reads: all 3. security-review (scoped to the hook diff): one finding, confidence 8 — work hidden from `session_work.worked_on` (e.g. `python3 -c`) makes a marked extended report unchecked; same blind spot as T250's file-time path; accepted as a known limit, docs bullet `d131b3ad` — pass |
| Full smoke suite still green (no regression) | ☑ pass | `python3 -m pytest .claude/hooks/tests/ tests/ -q` -> `3293 passed, 25 subtests passed in 203.50s (0:03:23)`; after the Stage 4 fix pass: `3293 passed, 25 subtests passed in 191.40s (0:03:11)` |
| **Companion score (easy-verifier)** | ☑ N/A | Not run; `score` is optional at Stage 4 |
| **UI: Visual regression (diff or verdict pasted)** | ☑ N/A | No UI: a hook and docs only |
| **UI: Design-system compliance (tokens/colors/typography verified)** | ☑ N/A | No UI |
| **UI: Responsiveness at target viewports** | ☑ N/A | No UI |

### Stage 4 fix pass (P1: marked minimal-track tasks stay checked)

Finding: a minimal-track `[auto]` task done in the main checkout leaves no `tasks/*_<ID>*` write and no worktree, so `owned(task)` is False and the first T252 change skipped it (fail open; on main it was always checked). Fix: the marked-path ownership question is asked only for an extended-track task; `task.marked and task.minimal` is always checked. The file-time path (T250 G3) is unchanged for both tracks.

RED (2026-11-04T15:03:14Z, hook still asking ownership for minimal): the edge-case test flipped to "is checked" -> `FAILED .claude/hooks/tests/test_t252_marked_ownership.py::test_edge_a_marked_minimal_track_task_is_still_checked_without_work_by_this_session`, `1 failed, 8 passed`.

GREEN: `python3 -m pytest .claude/hooks/tests/test_t252_marked_ownership.py -q` -> `9 passed`; `python3 -m pytest .claude/hooks/tests/test_stop_auto_mode_check.py .claude/hooks/tests/test_t250_session_ownership.py .claude/hooks/tests/test_t252_marked_ownership.py -q` -> `198 passed in 14.77s`; full suite `python3 -m pytest .claude/hooks/tests/ tests/ -q` -> `3293 passed, 25 subtests passed in 191.40s (0:03:11)`.

Docs: `docs/claude-md/tracks.md` T252 sentence now says extended-track only; new Known-limits bullet "A parallel session's marked minimal-track record can block your stop".

security-review: one finding (confidence 8) — accepted as a known limit, docs bullet added (`### Known limits`: "The Stop check cannot see every kind of work.")

---

## Demonstration

> Anchors what this task delivered to an observable before/after pair. BEFORE has no `N/A` path:
> if the task changes executable code, BEFORE is a pasted, timestamped terminal capture taken
> **before any implementation commit exists**; if it does not (docs, templates, skill-instruction
> text), BEFORE is the **verbatim prior content** of what changed — a quoted excerpt, not a command.

**BEFORE**: captured 2026-11-04T14:55:48Z in `/home/hungnguyenhuu/workspace/pets/wt-t252`, against the unchanged `.claude/hooks/stop_auto_mode_check.py` (HEAD `0dbdcdc4`), command `python3 -m pytest .claude/hooks/tests/test_t252_marked_ownership.py -q`:

```
FAILED .claude/hooks/tests/test_t252_marked_ownership.py::test_ac1_ac5_a_marked_task_this_session_did_not_work_on_is_not_checked
FAILED .claude/hooks/tests/test_t252_marked_ownership.py::test_ac1_a_marked_task_is_not_checked_without_an_auto_request_too
FAILED .claude/hooks/tests/test_t252_marked_ownership.py::test_ac3_an_ownership_reader_that_raises_keeps_the_check
FAILED .claude/hooks/tests/test_t252_marked_ownership.py::test_edge_a_minimal_track_task_marked_auto_and_not_worked_on_is_not_checked
4 failed, 5 passed in 1.08s
```

The AC 1 / AC 5 no-work test fails because the hook blocks a marked task this session did not work on: `assert '[hook:stop_auto_mode_check] Auto-mode final report check failed ... • T900: no `Memory:` line in the report ...' is None`. The AC 3 test fails with `assert 'session ownership unknown (RuntimeError)' in ''` (ownership is never asked for a marked task). The 5 passing tests are the block cases (AC 2, rest of AC 3) that must stay unchanged.

**AFTER**: same command post-change, `python3 -m pytest .claude/hooks/tests/test_t252_marked_ownership.py -q` -> `9 passed`. New `docs/claude-md/tracks.md` text: "Since T252 the same rule also applies to a task whose report is already marked auto mode ... if this session did not work on it, the check skips it and writes one stderr note."

**DELTA**: [one sentence — what a user can now do that they could not before]

**WITNESS**: [who ran it and when — derived from `memory/event-trace/T252.jsonl`, never the
implementing agent alone]
