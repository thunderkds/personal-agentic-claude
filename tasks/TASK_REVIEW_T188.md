# TASK_REVIEW — T188: Auto verify fires for every `[auto]` task — the minimal track gets a run too, and both Stop hooks find auto tasks the same way

> Sibling of `tasks/TASK_GUIDE_T188.md`. Everything here is **filled by the reviewer at Stage
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

**BEFORE** (captured 2026-10-28T05:51:12Z / 05:58:43Z, before any implementation commit; branch
`feat/t188-auto-verify-both-tracks` @ 1bf34ef — no implementation code existed yet):

1. The new tests for AC 1–8 fail against the unchanged hooks —
   `python3 -m pytest -q tests/test_auto_verify.py`:

```
Wed Oct 28 05:51:12 AM UTC 2026
FAILED tests/test_auto_verify.py::test_ac1_the_reader_returns_each_task_with_its_track_and_report_file
FAILED tests/test_auto_verify.py::test_ac1_neither_stop_hook_holds_a_second_copy_of_the_reader
FAILED tests/test_auto_verify.py::test_ac2_a_minimal_track_row_starts_one_detached_run
FAILED tests/test_auto_verify.py::test_ac3_the_record_gets_the_d3_line_for_pass_fail_and_blocked[pass]
FAILED tests/test_auto_verify.py::test_ac5_a_minimal_line_with_its_record_is_accepted
FAILED tests/test_auto_verify.py::test_ac7_the_extended_report_slot_names_the_result[pass]
FAILED tests/test_auto_verify.py::test_ac7_the_minimal_record_slot_names_the_result[pass]
FAILED tests/test_auto_verify.py::test_ac8_tracks_md_says_both_tracks_and_where_each_result_lands
32 failed, 61 passed in 440.43s (0:07:20)
```

   `test_ac2_a_minimal_track_row_starts_one_detached_run` fails with
   `AssertionError: the hook never wrote the record's verify line: ''` — a `Track: minimal` `[auto]`
   task at Ready for Review gets no run at all.

2. Gap 1, the code that drops it — `sed -n '76,81p' .claude/hooks/stop_auto_verify.py`:

```
Wed Oct 28 05:58:43 AM UTC 2026
def ready_for_review(kanban):
    m = re.search(r"^### Ready for Review\n(.*?)(?=^###|\Z)", kanban, re.S | re.M)
    rows = m.group(1).splitlines() if m else []
    return [ROW_ID.search(l).group(1) for l in rows
            if l.strip().startswith("- ") and ROW_ID.search(l) and not MINIMAL.search(l)]
```

3. Gap 2, nothing writes the result back into the report —
   `grep -rn "running (T182)" --include='*.py' --include='*.md' .` names only templates, docs and
   task guides; no hook reads or replaces the slot:

```
docs/claude-md/tracks.md:250:- `Not done: merge (yours)`, plus the `/verify` state: `auto verify: running (T182)`, its result, or
templates/MINIMAL_LOG_template.md:50:**Not done:** merge (yours); <auto verify: running (T182) | auto verify: <result> | /verify (yours)>
templates/TASK_REVIEW_template.md:36:Not done: merge (yours); <auto verify: running (T182) | auto verify: <result> | /verify (yours)>
```

**AFTER**: [same command, post-change] OR [verbatim excerpt of the new content]

**DELTA**: [one sentence — what a user can now do that they could not before]

**WITNESS**: [who ran it and when — derived from `memory/event-trace/Txxx.jsonl`, never the
implementing agent alone]
