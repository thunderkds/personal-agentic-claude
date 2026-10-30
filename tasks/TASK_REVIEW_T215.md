# TASK_REVIEW — T215: [Short Title]

> Sibling of `tasks/TASK_GUIDE_T215.md`. Everything here is **filled by the reviewer at Stage
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
3. <what was decided> — DEBATED: <option> (Advocate 1: <its option>; Advocate 2: <its option>) ⚠ decided for you — please review
4. <what was decided> — SAFER OPTION: <why> ⚠ decided for you — please review
Paused: <only when a stop that stays paused the task: which one, and why>
Checks: tests `<command>` — <result>; reviews <skill — result>; real run `<command>` — printed `<what it printed>` (auto-checked, not /verify)
Memory: <each entry the memory pass wrote, as `file — entry` | nothing new>
Not done: merge (yours); <auto verify: running (T182) | auto verify: <result> | /verify (yours)>

-->

## Evidence

| Check | Result | Notes / output snippet |
|-------|--------|------------------------|
| **New test(s) cover Acceptance Criteria (file paths pasted)** | ☑ pass | `tests/test_repo_layout_t215.py` (7 tests, fixture `tests/fixtures/t215/board_before.json`); red first at `49aadf83` (6 failed, 1 passed), green after: `7 passed in 0.41s` (2026-10-30T03:46Z) |
| Verification command run | ☑ pass | Supervisor re-run in `../wt-t215` 2026-10-30T03:46:40Z: `7 passed in 0.41s` · `2540 passed, 25 subtests passed in 140.67s` · `validate.sh: PASS` · `size ok: 60421` (was 344,246 bytes) |
| Negative cases hold | ☑ pass | Supervisor check: all 180 original Done/Closed/Blocked-scanned rows from `5fd0bd00` — every Done/Closed row found verbatim in `docs/archive/KANBAN_DONE_DETAIL.md` (only T147, a Blocked row with a path edit, differs); no Done/Closed row > 400 chars; all 15 moves are `R100`; per-section IDs equal (Todo 17, In Progress 1, RfR 0, Done 174, Closed 6, Blocked 1) |
| verify | ☑ pass | auto-run by hook, session 6b1ff314-f8fc-4087-8028-e4f2eb2bfdc0, commit b3f50a70a1c6b8b6efea7926de6740daae74fa30, log .claude/verify-runs/T215-b3f50a70a1c6.log — pass |
| Review scope bounded to the change's blast radius (affected set, not whole repo) | ☑ pass | code-review on `5fd0bd00..HEAD` (54 files) + board readers (`auto_mode.board_rows`, `pre_agent_validate_guide` section lookup): 0 P0/P1/P2, 3 P3 (lane EXCEEDS from path-only edits; T180/T094/T113 rows record no close-out, stated as such; path-only memory edits accepted). security-review: no findings (docs/test only; `docs/` not deployed nor in MANIFEST) |
| Full smoke suite still green (no regression) | ☑ pass | `python3 -m pytest -q tests .claude/hooks/tests` → `2540 passed, 25 subtests passed` |
| **Companion score (easy-verifier)** | ☑ N/A | not run — optional companion tool; docs/board-only change |
| **UI: Visual regression (diff or verdict pasted)** | ☑ N/A | no UI component — repo layout and board text only |
| **UI: Design-system compliance (tokens/colors/typography verified)** | ☑ N/A | no UI component — repo layout and board text only |
| **UI: Responsiveness at target viewports** | ☑ N/A | no UI component — repo layout and board text only |

---

## Demonstration

> Anchors what this task delivered to an observable before/after pair. BEFORE has no `N/A` path:
> if the task changes executable code, BEFORE is a pasted, timestamped terminal capture taken
> **before any implementation commit exists**; if it does not (docs, templates, skill-instruction
> text), BEFORE is the **verbatim prior content** of what changed — a quoted excerpt, not a command.

**BEFORE**: captured 2026-10-30T03:22:07Z in `../wt-t215` at `5fd0bd00` (branch base, no implementation commit yet), by common-infrastructure:

```
$ ls BRAINSTORMING_LOG_*.md PRD_*.md
BRAINSTORMING_LOG_companion-scoring.md
BRAINSTORMING_LOG_confusion-resolution.md
BRAINSTORMING_LOG_direct-install.md
BRAINSTORMING_LOG_fidelity-gate.md
BRAINSTORMING_LOG_harness-hardening.md
BRAINSTORMING_LOG_harness-kit-portability.md
BRAINSTORMING_LOG_multi-provider.md
BRAINSTORMING_LOG_online-board.md
BRAINSTORMING_LOG_plain-output.md
BRAINSTORMING_LOG_settings-profiles.md
BRAINSTORMING_LOG_spawn-mode.md
BRAINSTORMING_LOG_token-economy.md
PRD_companion-scoring.md
PRD_online-board.md
PRD_settings-profiles.md
$ wc -c PROJECT_KANBAN.md
344246 PROJECT_KANBAN.md
$ python3 counts.py   # .claude/hooks/lib/auto_mode.py board_rows per ### section; ## Blocked by the find_kanban_section row regex
Todo: 17 rows, 17 unique IDs
In Progress: 1 rows, 1 unique IDs
Ready for Review: 0 rows, 0 unique IDs
Done: 174 rows, 174 unique IDs
Closed (investigated, will not do): 6 rows, 6 unique IDs   # board_rows' ### lookahead runs past `## Blocked`, so T147 is counted here too
Blocked: 1 rows, 1 unique IDs
$ grep -n '^- \[x\] \*\*T155\*\*' PROJECT_KANBAN.md   # sample Done row, 409 chars
142:- [x] **T155** — Init asks the four board questions and writes `.claude/board.json` | common-infrastructure | C2 | Risk: Medium | P1 | Guide: `tasks/TASK_GUIDE_T155.md` | Depends on: T154 | Registered 2026-10-19 from the online-board planning (`PRD_online-board.md`, `BRAINSTORMING_LOG_online-board.md`). Done 2026-10-19: verify PASS (round 2 after /dev/tty fix 9b5c55b); evidence `tasks/TASK_REVIEW_T155.md`.
```

Done/Closed rows: 179 (174 Done + 5 Closed), all one line; 139 of them over 400 characters (longest 12,389, T090).

**AFTER**: captured 2026-10-30T03:31:27Z in `../wt-t215`, after the change (common-infrastructure):

```
$ ls BRAINSTORMING_LOG_*.md PRD_*.md
(eval):1: no matches found: BRAINSTORMING_LOG_*.md
$ ls docs/brainstorming docs/prd
docs/brainstorming: (the 12 BRAINSTORMING_LOG_<topic>.md files above)
docs/prd: PRD_companion-scoring.md PRD_online-board.md PRD_settings-profiles.md
$ wc -c PROJECT_KANBAN.md docs/archive/KANBAN_DONE_DETAIL.md
 60557 PROJECT_KANBAN.md
328044 docs/archive/KANBAN_DONE_DETAIL.md
$ python3 counts.py
Todo: 17 rows, 17 unique IDs
In Progress: 1 rows, 1 unique IDs
Ready for Review: 0 rows, 0 unique IDs
Done: 174 rows, 174 unique IDs
Closed (investigated, will not do): 6 rows, 6 unique IDs
Blocked: 1 rows, 1 unique IDs
(ordered ID list per section identical to tests/fixtures/t215/board_before.json: True for all six)
$ grep -n '^- \[x\] \*\*T155\*\*' PROJECT_KANBAN.md
143:- [x] **T155** — Init asks the four board questions and writes `.claude/board.json` | common-infrastructure | C2 | Risk: Medium | P1 | Guide: `tasks/TASK_GUIDE_T155.md` | Done 2026-10-19: verify PASS (round 2 after /dev/tty fix 9b5c55b); evidence `tasks/TASK_REVIEW_T155.md`
```

Every Done/Closed row is now one line of at most 400 characters (139 rewritten, 40 already short kept verbatim); the 179 original rows are in `docs/archive/KANBAN_DONE_DETAIL.md`, byte-verbatim (sha256 checked against the fixture).

**DELTA**: The repo root holds only live entry files, and the board is 60,557 bytes instead of 344,246, so a reader can open and scan it; every original row is still one lookup away in the archive.

**WITNESS**: [who ran it and when — derived from `memory/event-trace/Txxx.jsonl`, never the
implementing agent alone]
