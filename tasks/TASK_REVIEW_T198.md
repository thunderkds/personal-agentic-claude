# TASK_REVIEW — T198: wake reads two sections of memory/MEMORY.md, not the whole file

> Sibling of `tasks/TASK_GUIDE_T198.md`. Everything here is **filled by the reviewer at Stage
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

## Auto decisions

Mode: auto
1. <what was decided> — RULE: <the rule>
2. <what was decided> — FACT: <path>:<line> "<quoted text>"
3. <what was decided> — DEBATED: <option> (Advocate 1: <its option>; Advocate 2: <its option>) ⚠ decided for you — please review
4. <what was decided> — SAFER OPTION: <why> ⚠ decided for you — please review
Paused: <only when a stop that stays paused the task: which one, and why>
Checks: tests `<command>` — <result>; reviews <skill — result>; real run `<command>` — printed `<what it printed>` (auto-checked, not /verify)
Not done: merge (yours); <auto verify: running (T182) | auto verify: <result> | /verify (yours)>

-->

## Evidence

| Check | Result | Notes / output snippet |
|-------|--------|------------------------|
| **New test(s) cover Acceptance Criteria (file paths pasted)** | ☑ pass | `tests/test_wake_memory_sections.py` (11 tests, AC 1 to 4, 6, 7; red first: 11 failed with the script missing, 2026-10-28T08:00:00Z) |
| Verification command run | ☑ pass | Supervisor re-ran `python3 -m pytest tests/test_wake_memory_sections.py tests/test_dirty_worktrees.py tests/test_board_triage.py -q` -> `42 passed in 1.52s`; `python3 skills/wake/scripts/memory_sections.py \| wc -c` -> `1778` (cap 4,000) |
| Negative cases hold | ☑ pass | Missing file, no sections, CRLF, wrapped lines and no-write/no-nonzero-exit cases are in the new test file and pass |
| verify | ☐ pass / ☐ fail / ☐ N/A | [what was observed — must literally state "pass" or "fail" here too, e.g. "skill run, feature confirmed working — pass": the merge gate scans this Notes column for the word "pass", not just the Result column] |
| Review scope bounded to the change's blast radius (affected set, not whole repo) | ☑ pass | Supervisor inline review of `memory_sections.py`, the `skills/wake/SKILL.md` diff (Step 1 row, Step 4 text) and the new test. `SKILL.md` is 8,152 bytes against the 8,192 cap in `tests/test_board_triage.py`: only 40 bytes of room. Multi-reviewer `code-review` skill not run (one script, one skill text edit) |
| Full smoke suite still green (no regression) | ☑ pass | agent run: `python3 -m pytest tests -q -x` -> `873 passed in 41.61s` |
| **UI: Visual regression (diff or verdict pasted)** | ☐ pass / ☐ fail / ☐ N/A | [screenshot path or LLM verdict — required for UI tasks, Hard-Stop Gate 6] |
| **UI: Design-system compliance (tokens/colors/typography verified)** | ☐ pass / ☐ fail / ☐ N/A | [method used + output] |
| **UI: Responsiveness at target viewports** | ☐ pass / ☐ fail / ☐ N/A | [viewports tested, any overflow findings] |

---

## Demonstration

> Anchors what this task delivered to an observable before/after pair. BEFORE has no `N/A` path:
> if the task changes executable code, BEFORE is a pasted, timestamped terminal capture taken
> **before any implementation commit exists**; if it does not (docs, templates, skill-instruction
> text), BEFORE is the **verbatim prior content** of what changed — a quoted excerpt, not a command.

**BEFORE** (captured 2026-10-28T08:00:00Z, before any implementation commit; non-executable skill text quoted verbatim, executable part is a real red run):

(a) Prior `skills/wake/SKILL.md` Step 1 table row:

```
| `memory/MEMORY.md` | Read full file | `"No MEMORY.md found."` |
```

Prior Step 4 first paragraph:

```
From `memory/MEMORY.md`, emit the `### Decisions` section and `### Learning Records` section one-liners verbatim. Do not include other sections (Patterns, Glossary index lines, etc.) unless the Decisions and LR sections are absent, in which case emit the raw `## Index` block as-is.
```

(b) New test red, script missing (`python3 -m pytest tests/test_wake_memory_sections.py -q`, 2026-10-28T08:00:00Z):

```
E       assert 2 == 0
E        +  where 2 = CompletedProcess(args=['/usr/bin/python3', '/home/hungnguyenhuu/workspace/pets/wt-t198/skills/wake/scripts/memory_sections.py'], ... stderr="python3: can't open file '.../skills/wake/scripts/memory_sections.py': [Errno 2] No such file or directory\n").returncode
tests/test_wake_memory_sections.py:12: AssertionError
FAILED tests/test_wake_memory_sections.py::test_few_entries_all_printed_and_nothing_else
FAILED tests/test_wake_memory_sections.py::test_exactly_twenty_prints_all
FAILED tests/test_wake_memory_sections.py::test_over_twenty_prints_first_five_of_each
FAILED tests/test_wake_memory_sections.py::test_missing_memory_file
FAILED tests/test_wake_memory_sections.py::test_neither_section_prints_index_block
FAILED tests/test_wake_memory_sections.py::test_neither_section_and_no_index_prints_nothing
FAILED tests/test_wake_memory_sections.py::test_only_one_section_present
FAILED tests/test_wake_memory_sections.py::test_windows_line_endings_and_trailing_space_heading
FAILED tests/test_wake_memory_sections.py::test_wrapped_continuation_line_is_ignored
FAILED tests/test_wake_memory_sections.py::test_script_writes_nothing
FAILED tests/test_wake_memory_sections.py::test_real_memory_file_is_small
11 failed in 0.18s
```

(c) `wc -c memory/MEMORY.md` before the change: `42665 memory/MEMORY.md` (the whole file `wake` read each session).

**AFTER** (Supervisor, 2026-10-28): `python3 skills/wake/scripts/memory_sections.py` prints 10 lines (the 5 newest Decisions, then the 5 newest Learning Records) in 1,778 characters; `wc -c memory/MEMORY.md` is 42,665. `skills/wake/SKILL.md` Step 1 row now runs the script and says never to read the whole file.

**DELTA**: A session starts with the same Key Memory lines but loads about 1,800 characters (about 450 tokens) of `MEMORY.md` instead of about 42,000 (about 10,400 tokens), with or without easy-memory installed.

**WITNESS**: [who ran it and when — derived from `memory/event-trace/Txxx.jsonl`, never the
implementing agent alone]
