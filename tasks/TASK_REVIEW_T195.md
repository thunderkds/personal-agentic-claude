# TASK_REVIEW — T195: Sub-agents can use easy-memory, and read less of memory/MEMORY.md

> Sibling of `tasks/TASK_GUIDE_T195.md`. Everything here is **filled by the reviewer at Stage
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
| **New test(s) cover Acceptance Criteria (file paths pasted)** | ☑ pass | `tests/test_agent_memory_tools.py` (AC 1-3 and 5; red first: 12 failed, 4 passed at 2026-10-28T07:26:49Z; after the edit all pass) |
| Verification command run | ☑ pass | `python3 -m pytest tests/test_agent_frontmatter.py tests/test_agent_memory_tools.py -q` -> `47 passed in 0.10s` |
| Negative cases hold | ☑ pass | `test_other_startup_steps_kept` (4 cases) and the `tools:` retention assert pass: no existing Startup step or tool removed |
| verify | ☐ pass / ☐ fail / ☐ N/A | [what was observed — must literally state "pass" or "fail" here too, e.g. "skill run, feature confirmed working — pass": the merge gate scans this Notes column for the word "pass", not just the Result column] |
| Review scope bounded to the change's blast radius (affected set, not whole repo) | ☐ pass / ☐ fail | [what was reviewed vs. skipped, and why] |
| Full smoke suite still green (no regression) | ☑ pass | `python3 -m pytest tests -q -x` -> `862 passed in 77.28s` |
| **UI: Visual regression (diff or verdict pasted)** | ☐ pass / ☐ fail / ☐ N/A | [screenshot path or LLM verdict — required for UI tasks, Hard-Stop Gate 6] |
| **UI: Design-system compliance (tokens/colors/typography verified)** | ☐ pass / ☐ fail / ☐ N/A | [method used + output] |
| **UI: Responsiveness at target viewports** | ☐ pass / ☐ fail / ☐ N/A | [viewports tested, any overflow findings] |

---

## Demonstration

> Anchors what this task delivered to an observable before/after pair. BEFORE has no `N/A` path:
> if the task changes executable code, BEFORE is a pasted, timestamped terminal capture taken
> **before any implementation commit exists**; if it does not (docs, templates, skill-instruction
> text), BEFORE is the **verbatim prior content** of what changed — a quoted excerpt, not a command.

**BEFORE** (captured 2026-10-28T07:26:49Z, before any implementation commit; non-executable change, so the prior content is quoted verbatim from `agents/*.md` at the base commit):

Prior `tools:` lines:

```
agents/common-infrastructure.md:4:tools: Read, Write, Edit, Bash, Glob, Grep
agents/backend.md:4:tools: Read, Write, Edit, Bash, Glob, Grep
agents/frontend.md:4:tools: Read, Write, Edit, Bash, Glob, Grep
agents/qa.md:4:tools: Read, Write, Edit, Grep, Glob, Bash
```

Prior MEMORY.md Startup step (identical text in all four guides, step 2 of Mandatory Startup Sequence):

```
2. Read `memory/MEMORY.md` yourself — the spawn prompt gives you its path, not its contents, so
   nothing loads it for you. Follow its links into cold files only when relevant to your task
```

Prior state, new test run on the unchanged files (`python3 -m pytest tests/test_agent_memory_tools.py -q`, 2026-10-28T07:26:49Z), tail of the real output:

```
FAILED tests/test_agent_memory_tools.py::test_tools_line_lists_both_memory_tools[common-infrastructure]
FAILED tests/test_agent_memory_tools.py::test_tools_line_lists_both_memory_tools[backend]
FAILED tests/test_agent_memory_tools.py::test_tools_line_lists_both_memory_tools[frontend]
FAILED tests/test_agent_memory_tools.py::test_tools_line_lists_both_memory_tools[qa]
FAILED tests/test_agent_memory_tools.py::test_memory_rule_present[common-infrastructure]
FAILED tests/test_agent_memory_tools.py::test_memory_rule_present[backend]
FAILED tests/test_agent_memory_tools.py::test_memory_rule_present[frontend]
FAILED tests/test_agent_memory_tools.py::test_memory_rule_present[qa]
FAILED tests/test_agent_memory_tools.py::test_memory_md_step_uses_the_slice[common-infrastructure]
FAILED tests/test_agent_memory_tools.py::test_memory_md_step_uses_the_slice[backend]
FAILED tests/test_agent_memory_tools.py::test_memory_md_step_uses_the_slice[frontend]
FAILED tests/test_agent_memory_tools.py::test_memory_md_step_uses_the_slice[qa]
12 failed, 4 passed in 0.25s
```

(The 4 passing are the negative `test_other_startup_steps_kept` cases, which must hold before and after.)

**AFTER**: [same command, post-change] OR [verbatim excerpt of the new content]

**DELTA**: [one sentence — what a user can now do that they could not before]

**WITNESS**: [who ran it and when — derived from `memory/event-trace/Txxx.jsonl`, never the
implementing agent alone]
