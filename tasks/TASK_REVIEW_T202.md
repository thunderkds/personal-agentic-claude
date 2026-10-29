# TASK_REVIEW — T202: `main` is green again — budget and corpus test fixes

> Sibling of `tasks/TASK_GUIDE_T202.md`. Everything here is **filled by the reviewer at Stage
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

**BEFORE** (captured 2026-10-29T05:12:10Z at `2335e90`, before any implementation commit; Verification Command with the pytest tail widened to the FAILED lines; the two stray lines at the top are pytest source-context noise matched by the `failed` grep):

```
            f"control failed: the mutation must push past the old 200-line cap "
        assert task_files, "corpus is empty — sanity check failed"
FAILED .claude/hooks/tests/test_agent_guide_dedup.py::test_ac7_per_role_loaded_size_is_strictly_lower_than_baseline[backend]
FAILED .claude/hooks/tests/test_agent_guide_dedup.py::test_ac7_per_role_loaded_size_is_strictly_lower_than_baseline[c-infra]
FAILED .claude/hooks/tests/test_agent_guide_dedup.py::test_ac7_per_role_loaded_size_is_strictly_lower_than_baseline[frontend]
FAILED .claude/hooks/tests/test_agent_guide_dedup.py::test_ac7_per_role_loaded_size_is_strictly_lower_than_baseline[qa]
FAILED .claude/hooks/tests/test_agent_guide_dedup.py::test_t069_ac9_report_per_role_pair_size
FAILED .claude/hooks/tests/test_memory_channel_and_budget.py::test_live_memory_md_is_within_budget_today
FAILED .claude/hooks/tests/test_memory_channel_and_budget.py::test_ac10_growth_in_chars_without_growth_in_lines_turns_the_gate_red
FAILED .claude/hooks/tests/test_memory_channel_and_budget.py::test_ac11_many_short_lines_past_200_stay_green_while_under_budget
FAILED .claude/hooks/tests/test_memory_channel_and_budget.py::test_ac3_per_entry_report_is_advisory_and_never_fails
FAILED .claude/hooks/tests/test_token_audit_format.py::test_memory_md_hot_tier_stays_within_char_budget
FAILED .claude/hooks/tests/test_verify_row_fill_detection.py::test_ac6_old_vs_new_pattern_over_real_corpus_differs_only_on_placeholders
FAILED .claude/hooks/tests/test_vital_slice.py::test_ac11_line_cap[agents/backend.md]
FAILED .claude/hooks/tests/test_vital_slice.py::test_ac11_line_cap[agents/common-infrastructure.md]
FAILED .claude/hooks/tests/test_vital_slice.py::test_ac11_line_cap[agents/frontend.md]
FAILED .claude/hooks/tests/test_vital_slice.py::test_ac11_line_cap[agents/qa.md]
15 failed, 2026 passed, 25 subtests passed in 101.32s (0:01:41)
43019
  150 agents/backend.md
  143 agents/common-infrastructure.md
  146 agents/frontend.md
  135 agents/qa.md
  574 total
- [T199: site `#mcps` lists easy-memory-mcp as a third OPTIONAL companion card](decisions.md) — README facts only, 28% tied to scripted tests; PR #114 (merged on GitHub 2026-10-28) also fixes the 768-899 px `#hooks` overflow; T194 + T199 both edit the `#mcps` lead and the one-entry-per-server test (merge by hand)
- [T198: `wake` prints the Decisions + Learning Records entries with `memory_sections.py`, never reads all of MEMORY.md](decisions.md) — ~9k tokens less per session; **add new index lines at the TOP of a section (newest first) or the script misses them**; `wake/SKILL.md` is 8,152 of 8,192 bytes
- [T195: easy-memory installed; base sub-agents get memory_search/read and use the spawn slice, not all of MEMORY.md](decisions.md) — OPTIONAL: kit works the same without it, agents skip it if absent; `memory/` NOT replaced; decide after ~2 weeks of `easy_memory.py report`
0
```

**AFTER**: [same command, post-change] OR [verbatim excerpt of the new content]

**DELTA**: [one sentence — what a user can now do that they could not before]

**WITNESS**: [who ran it and when — derived from `memory/event-trace/Txxx.jsonl`, never the
implementing agent alone]
