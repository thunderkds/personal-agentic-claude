# TASK_REVIEW — T189: Auto close-out — after an auto verify pass the hook moves the row to Done, and the auto run does its own memory pass before stopping

> Sibling of `tasks/TASK_GUIDE_T189.md`. Everything here is **filled by the reviewer at Stage
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
| **New test(s) cover Acceptance Criteria (file paths pasted)** | ☑ pass | `tests/test_auto_verify.py` (46 `test_t189_*` cases: AC 1 ×2, AC 2 ×2, AC 3 ×7, AC 4 ×6, AC 6 ×3, AC 7 ×5, AC 8 ×12, AC 9 ×7, edge ×2 — `claude` stubbed, a git spy on PATH for AC 6) and `.claude/hooks/tests/test_stop_auto_mode_check.py` (6 `test_t189_d5_*` cases, AC 5). `python3 -m pytest -q tests/test_auto_verify.py .claude/hooks/tests/test_stop_auto_mode_check.py -k t189` → `52 passed, 139 deselected in 7.74s` (2026-10-29T10:26Z, `5cb4ca4`). RED: the 4 D5 block cases fail on the pre-change hook (`4 failed, 2 passed`); mutations of `auto_closeout.py` — D3 off `5 failed`, D2 off `6 failed`, D9 off `6 failed`, write-once off `1 failed` |
| Verification command run | ☑ pass | 2026-10-29T10:26:17Z at `5cb4ca4`: `python3 -m pytest -q tests/test_auto_verify.py .claude/hooks/tests` → `1287 passed, 25 subtests passed in 79.03s`; `python3 -m pytest -q tests` → `1010 passed in 71.50s`; `./scripts/validate.sh` (the guide's `./validate.sh`; it lives in `scripts/`) → `validate.sh: PASS` |
| Negative cases hold | ☑ pass | fail and blocked verdicts leave the board byte-identical (AC 2); blank tests row, blank / no-reason / `☑ fail` design row, no trace test run, no minimal `New test` line each keep the row (AC 3); no record (run could not write it), another commit, fail record, hand-typed `auto-run by hook` row, another session, a FAIL run whose prose asks for the move each keep the row (AC 4); each of 6 missing D9 fields and 3 placeholders keep the row (AC 8); a deleted report moves and creates nothing |
| verify | ☐ pass / ☐ fail / ☐ N/A | [what was observed — must literally state "pass" or "fail" here too, e.g. "skill run, feature confirmed working — pass": the merge gate scans this Notes column for the word "pass", not just the Result column] |
| Review scope bounded to the change's blast radius (affected set, not whole repo) | ☑ pass | Supervisor Stage 4 2026-10-29: code-review over `main...HEAD` (lib/auto_closeout.py, stop_auto_verify.py, stop_auto_mode_check.py, tracks.md, pipeline-stages.md, both templates, PROJECT_SPEC.md glossary, three test files) plus the readers it loads from `pre_bash_block_unsafe_merge.py` (unchanged: `git diff main...HEAD` empty for the gate and `merge_gate_guard.py`). lane_check: `C2, 12 files, 1077 lines, EXCEEDS (lines 1077 > 500)` — 566 of them are tests; warn-only, kept at C2. Two files outside the Files table (tests/test_auto_mode.py, pipeline-stages.md Stage 5 item 5) are forced by D7 and accepted. Findings, none blocking: P2 surfaced to user — a Done row can now mean "auto-verified, branch not merged" (D4 note text does not say "not merged"); P2 residual, same as T182 — an agent that runs `stop_auto_verify.py --run` with a fake `claude` on PATH gets a record and now a Done move; P3 — `load_gate()` strips the trailing `main()` from the gate source and fails closed with RuntimeError if the shape changes. security-review (Risk High): no writing git command (AC 6 PATH-wrapper test), no memory write, board write under `fcntl` lock + `os.replace`, row matched by ID and exactly-one hit, fail closed on every exception. Full suite: `2158 passed, 25 subtests passed`. AC 11 (paid live check, cap $3) awaits the user. |
| Full smoke suite still green (no regression) | ☑ pass | same run as the verification command: `1287 passed` + `1010 passed` + `validate.sh: PASS`. `git diff 026bc61 -- .claude/hooks/pre_bash_block_unsafe_merge.py` is empty (0 lines): the merge gate is untouched |
| **Companion score (easy-verifier)** | ☑ N/A | neither companion tool was run for this task |
| **UI: Visual regression (diff or verdict pasted)** | ☐ N/A | pure-hook task: no UI component (Stop hooks, a lib module, doctrine text) |
| **UI: Design-system compliance (tokens/colors/typography verified)** | ☐ N/A | pure-hook task: no UI component (Stop hooks, a lib module, doctrine text) |
| **UI: Responsiveness at target viewports** | ☐ N/A | pure-hook task: no UI component (Stop hooks, a lib module, doctrine text) |

---

## Demonstration

> Anchors what this task delivered to an observable before/after pair. BEFORE has no `N/A` path:
> if the task changes executable code, BEFORE is a pasted, timestamped terminal capture taken
> **before any implementation commit exists**; if it does not (docs, templates, skill-instruction
> text), BEFORE is the **verbatim prior content** of what changed — a quoted excerpt, not a command.

**BEFORE**: captured 2026-10-29T10:09:30Z on `feat/t189-auto-closeout` at `026bc61` (the board commit; no T189 implementation commit exists yet). Command — a scripted fixture run of the kit's real Stop hooks in a temp project, `claude` stubbed with the T182 pass fixture, nothing paid, nothing in the repo written:

```
$ python3 <scratchpad>/demo_t189.py /home/hungnguyenhuu/workspace/pets/wt-t189
== (1) after an auto verify pass ==
**Last updated**: 2026-01-01
### Ready for Review
- [ ] **T951** — Move the data | Supervisor | C2 | Risk: Low | P1

### Done
-- report ## Auto decisions --
Mode: auto
1. kept recurring.csv — RULE: `docs/claude-md/tracks.md` `### Stops that stay`
Checks: tests `pytest -q` — 12 passed; reviews code-review — 0 P0/P1
Memory: nothing new
Not done: merge (yours); auto verify: ☑ pass (session bb6500c2-6ee9-4ce9-bc0e-ea2f246f2fd4, commit e0b0cd5c138f931a5c292ef2a462be7d3f4dcf76, log .claude/verify-runs/T951-e0b0cd5c138f.log)
-- verify row --
| verify | ☑ pass | auto-run by hook, session bb6500c2-6ee9-4ce9-bc0e-ea2f246f2fd4, commit e0b0cd5c138f931a5c292ef2a462be7d3f4dcf76, log .claude/verify-runs/T951-e0b0cd5c138f.log — pass |
== (2) auto-mode Stop check, report with no `Memory:` line ==
stdout: (empty — the stop is allowed)
```

(1) The auto verify passed, the record and the evidence are complete, and the row still sits in Ready for Review with `- [ ]`; `### Done` is empty, `**Last updated**` is unchanged and the report has no `Closed:` line. (2) A report with no `Memory:` line ends the auto run unchallenged.

**AFTER**: captured 2026-10-29T10:29:02Z at `5cb4ca4`, the same command:

```
$ python3 <scratchpad>/demo_t189.py /home/hungnguyenhuu/workspace/pets/wt-t189
== (1) after an auto verify pass ==
**Last updated**: 2026-10-29
### Ready for Review

### Done
- [x] **T951** — Move the data | Supervisor | C2 | Risk: Low | P1 | Done 2026-10-29: auto verify pass (session bb6500c2-6ee9-4ce9-bc0e-ea2f246f2fd4, commit 3e4758153e3565a96b32a7f2b505f162bc8d58c8)
-- report ## Auto decisions --
Mode: auto
1. kept recurring.csv — RULE: `docs/claude-md/tracks.md` `### Stops that stay`
Checks: tests `pytest -q` — 12 passed; reviews code-review — 0 P0/P1
Memory: nothing new
Not done: merge (yours); auto verify: ☑ pass (session bb6500c2-6ee9-4ce9-bc0e-ea2f246f2fd4, commit 3e4758153e3565a96b32a7f2b505f162bc8d58c8, log .claude/verify-runs/T951-3e4758153e35.log)
Closed: row moved to Done 2026-10-29 — auto verify pass (session bb6500c2-6ee9-4ce9-bc0e-ea2f246f2fd4, commit 3e4758153e3565a96b32a7f2b505f162bc8d58c8); Gates 5 and 6 checked
-- verify row --
| verify | ☑ pass | auto-run by hook, session bb6500c2-6ee9-4ce9-bc0e-ea2f246f2fd4, commit 3e4758153e3565a96b32a7f2b505f162bc8d58c8, log .claude/verify-runs/T951-3e4758153e35.log — pass |
== (2) auto-mode Stop check, report with no `Memory:` line ==
stdout: {"decision": "block", "reason": "[hook:stop_auto_mode_check] Auto-mode final report check failed \u2014 fix it before you stop (docs/claude-md/tracks.md `## Auto mode`):\n  \u2022 T951: no `Memory:` line in the report \u2014 run the memory pass before you stop and record it there (each entry written, or `Memory: nothing new`)"}
```

Script note: after the first change the script's part (2) gained one line that puts the row back in Ready for Review before the Stop check (part 1 now moves it to Done, and the check skips Done rows). That is the board state the BEFORE run had in part (2). Re-run against the pre-change hooks (`git stash` of the two hook edits), part (2) still printed `stdout: (empty — the stop is allowed)`.

**DELTA**: An `[auto]` task whose auto verify passes, with its run record, Gate 5/6 evidence and a complete final report, now reaches Done on its own, and the report says so on a `Closed:` line. An auto run can no longer stop without recording its memory pass. The merge, the push and `ship` stay the user's.

**WITNESS**: [who ran it and when — derived from `memory/event-trace/Txxx.jsonl`, never the
implementing agent alone]

---

## Implementer notes for Stage 4 (common-infrastructure, 2026-10-29)

**Decisions worth the reviewer's eye**
- **The merge gate is read, never edited.** `auto_closeout.load_gate()` loads `pre_bash_block_unsafe_merge.py` with its bare bottom-of-file `main()` stripped (the technique `test_merge_gate_evidence.py` uses), then calls `has_filled_verify_row`, `trace_shows_verification`, `read_guide_section`, `COMPANION_ROW_PATTERNS`, `CHECKED_PASS/FAIL_PATTERN` and the row builder `_companion_row_pattern` (a private name, used for the tests row so the row shape has one definition). If the gate stops ending in `main()` or its guarded import fails, the load raises, and the run writes `done not moved: close-out failed (...)`: fail closed, never a crash.
- **D2 is stricter than the merge gate today, by the guide's wording.** The gate blocks only on a `☑ fail` design row (T190, fail-open). The close-out also needs each design row filled: `☑ pass` with evidence, or N/A with a reason; a missing row counts as blank. On the minimal track, Gate 5 needs a `New test` line under `Checked:` (the template's Gate 5 line), and Gate 6 does not apply (a UI component puts a task on the extended track).
- **D3** checks the record for (task, head) says pass for the session the run parsed, then the gate's `has_filled_verify_row(task, [that checkout's tasks/])`.
- **D9 order**: the report is read after the slot write (T188), checked, then `Closed:` is written and the report is read again before the move. A row not in Ready for Review is checked first, so a task the user already moved gets no note at all.
- **D2 suffix** goes only on a hook-written result (`auto-run by hook` in the Notes / `verify:` line), once.
- **Lock**: `.claude/hooks/.state/closeout.lock` (gitignored), `flock` around the read-check-write of the report and the board, so two runs that end together cannot lose a board write. A live session's edit is not locked out; the board is re-read just before the write and the row is matched by task ID.
- **D7 split**: `### Never in auto mode` now lists only merge, push, `ship`. The other T180 D6 rules (the Supervisor never runs `/verify` or writes its row, never moves a task to Done, never moves a task down a track) moved unchanged to a new `### The Supervisor never`, so no rule was dropped.

**Files changed outside the guide's predicted table**
- `tests/test_auto_mode.py` — its D6 test pinned the old never-list that D7 rewrites; it now asserts the two subsections and every rule it pinned before.
- `docs/claude-md/pipeline-stages.md` Stage 5 item 5 — said "Never in auto mode: the task stops at Ready for Review", which D7 makes false.
- `.claude/hooks/pre_bash_block_unsafe_merge.py` — predicted as "expose the readers"; **not changed** (Supervisor constraint; they were already module level).

**Residual limits (recorded, not fixed)**
- Same as T182's record: an agent that runs `stop_auto_verify.py --run` itself with a fake `claude` first on its PATH gets a record from the script, and now a Done move as well. The record raises the bar; it is not a proof.
- A placeholder is `<` + a lowercase letter … `>`. A real field whose only text is HTML such as `<details>` reads as a placeholder, so the row stays out of Done (fail closed).
- `Memory:` is checked for presence and not a placeholder; the hook cannot tell whether the pass named every entry it wrote.

**Cut list** (guide's, unchanged): `ship`; a release note; a notification when a row moves; an undo command.
**Not done**: AC 11 (paid live check, cap $3, the user's go); Stage 4 `code-review` and `security-review` (Risk High) — this agent has no `Skill` tool, so both are the Supervisor's; `verify` row is the user's (`/verify T189`).
