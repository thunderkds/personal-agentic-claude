# TASK_REVIEW — T264: [Short Title]

> Sibling of `tasks/TASK_GUIDE_T264.md`. Everything here is **filled by the reviewer at Stage
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
| **New test(s) cover Acceptance Criteria (file paths pasted)** | ☑ pass | `.claude/hooks/tests/test_filelock.py` (12 tests): AC1/3 two-process 400 whole lines; AC4 fake-msvcrt LK_LOCK then LK_UNLCK, 1 byte at offset 0, position restored, no fcntl import; AC5 trace hook still appends with `lock: failed`, close-out raises (fails closed); no direct `fcntl` in the three files. AC6: chain code untouched; `test_trace_chain.py` (chain/anchor/INTACT tests) still passes. |
| Verification command run | ☑ pass | `python3 -m pytest .claude/hooks/tests/test_filelock.py -q` -> `12 passed in 0.59s`; `python3 -m pytest .claude/hooks/tests/ tests/ -q` -> `3432 passed, 25 subtests passed in 213.22s` (2026-11-06T12:03Z; before: 3420, +12 new). |
| Negative cases hold | ☑ pass | Red against prior content: before the helper existed `test_filelock.py` failed at collection (`ModuleNotFoundError: No module named 'filelock'`); with the helper but old call sites, 4 caller tests failed (`4 failed, 8 passed`). Mutation: `test_mutation_control_no_op_lock_goes_red` replaces `fcntl.flock` with a no-op in the worker; the 400-line sequence check then fails (test asserts `not numbers_intact`, and passes). The mutation lives in the test worker, so `git diff --stat` of the source is empty by design. |
| verify | ☐ pass / ☐ fail / ☐ N/A | [what was observed — must literally state "pass" or "fail" here too, e.g. "skill run, feature confirmed working — pass": the merge gate scans this Notes column for the word "pass", not just the Result column] |
| Review scope bounded to the change's blast radius (affected set, not whole repo) | ☐ pass / ☐ fail | [what was reviewed vs. skipped, and why] |
| Full smoke suite still green (no regression) | ☐ pass / ☐ fail | |
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

**BEFORE** (captured 2026-11-06T11:54Z-11:58Z, branch feat/t264-portable-filelock at 0aafdf84, no implementation commit yet):

```
$ python3 -m pytest .claude/hooks/tests/ tests/ -q
3420 passed, 25 subtests passed in 214.04s (0:03:34)

$ grep -rn fcntl scripts/verify_trace.py .claude/hooks/post_tool_trace.py .claude/hooks/lib/auto_closeout.py
scripts/verify_trace.py:40:    import fcntl
scripts/verify_trace.py:42:    fcntl = None
scripts/verify_trace.py:50:            fcntl.flock(f.fileno(), fcntl.LOCK_SH)
.claude/hooks/post_tool_trace.py:54:    import fcntl
.claude/hooks/post_tool_trace.py:56:    fcntl = None
.claude/hooks/post_tool_trace.py:183:        fcntl.flock(f.fileno(), fcntl.LOCK_EX)
.claude/hooks/lib/auto_closeout.py:36:import fcntl
.claude/hooks/lib/auto_closeout.py:192:        fcntl.flock(handle, fcntl.LOCK_EX)
.claude/hooks/lib/auto_closeout.py:196:            fcntl.flock(handle, fcntl.LOCK_UN)
```

Note: `auto_closeout.py:36` is a bare top-level `import fcntl`, so on Windows that module raises ImportError. `.claude/hooks/lib/filelock.py` does not exist.

**AFTER** (2026-11-06T12:03Z):

```
$ python3 -m pytest .claude/hooks/tests/ tests/ -q
3432 passed, 25 subtests passed in 213.22s (0:03:33)

$ grep -rn fcntl scripts/verify_trace.py .claude/hooks/post_tool_trace.py .claude/hooks/lib/auto_closeout.py
(no output)

$ grep -n "file_lock" scripts/verify_trace.py .claude/hooks/post_tool_trace.py .claude/hooks/lib/auto_closeout.py
(each file imports and uses file_lock from .claude/hooks/lib/filelock.py)
```

**DELTA**: The trace hook, the auto close-out and the trace verifier no longer import `fcntl`; they lock through one helper that uses `msvcrt.locking` on Windows, so none of them crashes on `import fcntl`.

**WITNESS**: [who ran it and when — derived from `memory/event-trace/Txxx.jsonl`, never the
implementing agent alone]
