# TASK_REVIEW — T211: Merge gate sees git -C/-c forms and resolves merges with any option

> Sibling of `tasks/TASK_GUIDE_T211.md`. Everything here is **filled by the reviewer at Stage
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
| **New test(s) cover Acceptance Criteria (file paths pasted)** | ☑ pass | `.claude/hooks/tests/test_merge_gate_t211.py` (new, 99 tests: AC 1-7 + guide edge cases) and `.claude/hooks/tests/test_merge_gate_guard.py` (allowlist pin). Red first on the unchanged gate: `75 failed, 24 passed in 1.54s`. After the change: `python3 -m pytest .claude/hooks/tests/test_merge_gate_t211.py -q` → `99 passed in 1.27s` (2026-10-29T15:28Z). AC 8 mutations by hand, gate restored after each (2026-10-29T15:27:38Z): M1 drop the global-option prefix → `32 failed, 67 passed`; M2 unknown merge option → unresolved → `9 failed, 90 passed`; M3 octopus → first branch only → `5 failed, 94 passed`; M4 drop the alias rule → `14 failed, 85 passed` |
| Verification command run | ☑ pass | `python3 -m pytest .claude/hooks/tests -q && python3 -m pytest tests -q` at `720b2ae` (2026-10-29T15:28:08Z): `1307 passed, 25 subtests passed in 26.63s` then `1209 passed in 110.22s (0:01:50)` |
| Negative cases hold | ☑ pass | Allowed with an In Progress row: `git -C x merge-base A B`, `git -C x log`, `git --no-pager log --oneline`, `git -c core.x=y status`; mentions (`grep "git -C x push"`, heredoc body, `echo git -c alias.p=push p`, `printf` of a pull). Clean board allows every gated form. One unresolvable branch keeps the T210 working-tree read (`git merge main`). A push carrying `-c`, `--git-dir`, `--namespace` or `-Cdir` is not narrowed (whole board). Classification of 600 global options stays linear (< 5 s test bound) |
| verify | ☑ pass | auto-run by hook, session 3fddf8e5-d609-43c9-a356-2d2c003d8b83, commit 7f9e95e25bc90d6d5240555dd0b87a2b05f04207, log .claude/verify-runs/T211-7f9e95e25bc9.log — pass |
| Review scope bounded to the change's blast radius (affected set, not whole repo) | ☑ pass | Supervisor Stage 4 2026-10-29: code-review + security-review (Risk High) over `main...HEAD`: shared `GIT_VERB_PREFIX` (global options) in BLOCKED_PATTERNS, option-agnostic `_merge_source` (MERGE_FLAGS removed), `branch_targets` with octopus handling, `-c alias.`/`--config-env alias.` gated as a merge, 99 new tests. lane_check `C2, 5 files, 544 lines, EXCEEDS (lines 544 > 500)` — warn-only, test-heavy. Departures accepted: (1) two T210 parameters that asserted the replaced behaviour removed, with the reason in the commit; (2) the alias rule skips a T099 data-command head (echo/printf/grep…), same class as today's quoted `echo "git push" | sh`; (3) `--config-env alias.` included; (4) narrowing resolves only `-C`, `--no-pager`, `-P` (and `-c` before merge) — every other global option gives the whole-board check, which is stricter; (5) octopus doubts block only while a task is open; the committed-row rule applies to named Ready-for-Review tasks; (6) `branch_target` kept as a wrapper. Security: classification only widens what is gated; the single-pass option regex has a 600-option timing test. P2 (pre-existing class, not fixed): `echo git -c alias.p=push p | sh` and quoted `echo "git push" | sh` are allowed. |
| Full smoke suite still green (no regression) | ☑ pass | Both suites green (row above). Oracle files `t190_pre_change_gate_output.txt`, `t197_pre_change_gate_output.txt` unchanged and their tests pass. Two T210 AC 5 params (`--strategy=ours`, octopus) retired: T211 D2 changes exactly that behaviour; replaced by T211 AC 3/4 tests |
| **Companion score (easy-verifier)** | ☐ pass / ☐ fail / ☐ N/A | [`overall` and `change_risk` as the tool returned them, the scope, the ref, and the absolute path of the verifier report after a literal `report:` label — e.g. "overall 86 (>= 80), change_risk pass, scope changes, ref `main...HEAD`, report: `/home/me/.easy-verifier-reports/kit/score_changes_20261028T0530Z.html`". The gate reads the path that follows `report:` and nothing else, so with no label, or a path that is absent, the row is unscored — write ☑ N/A instead. ☑ N/A with a reason when neither companion tool was run: the merge gate blocks on ☑ fail only, never on an absent or N/A row] |
| **UI: Visual regression (diff or verdict pasted)** | ☑ N/A | no UI component (hook-only change) |
| **UI: Design-system compliance (tokens/colors/typography verified)** | ☑ N/A | no UI component (hook-only change) |
| **UI: Responsiveness at target viewports** | ☑ N/A | no UI component (hook-only change) |

---

## Demonstration

> Anchors what this task delivered to an observable before/after pair. BEFORE has no `N/A` path:
> if the task changes executable code, BEFORE is a pasted, timestamped terminal capture taken
> **before any implementation commit exists**; if it does not (docs, templates, skill-instruction
> text), BEFORE is the **verbatim prior content** of what changed — a quoted excerpt, not a command.

**BEFORE**: captured 2026-10-29T15:15:55Z, before any implementation commit, against the UNCHANGED
gate at `1f0603c`. Real PreToolUse JSON events fed to `.claude/hooks/pre_bash_block_unsafe_merge.py`
of a throwaway `git clone` of this branch (driver: scratchpad `demo.py <repo> <dir>`; it rewrites the
clone's `PROJECT_KANBAN.md`, adds worktree `wt-t900` on `feat/t900-x` and a T900 trace record):

```
clone of /home/hungnguyenhuu/workspace/pets/wt-t211 at 1f0603c
-- board: T900 In Progress
2026-10-29T15:15:56Z  ALLOW  git -C . merge feat/x
2026-10-29T15:15:56Z  ALLOW  git -c alias.p=push p
2026-10-29T15:15:56Z  ALLOW  git -C . log
-- board: T900 Ready for Review; verify row only in wt-t900's working tree
2026-10-29T15:15:56Z  ALLOW  git merge -X ours feat/t900-x
-- verify row committed on feat/t900-x
2026-10-29T15:15:56Z  ALLOW  git merge -X ours feat/t900-x
```

All three gaps are live: a `-C` merge and a `-c alias` push pass an In Progress board unchecked (G5,
G7), and `-X ours` leaves the branch unresolved, so the working-tree row is accepted (G6).

**AFTER**: same driver, same events, against the changed gate at `720b2ae` (2026-10-29T15:27:58Z):

```
clone of /home/hungnguyenhuu/workspace/pets/wt-t211 at 720b2ae
-- board: T900 In Progress
2026-10-29T15:27:58Z  BLOCK  git -C . merge feat/x   -> • Tasks still In Progress: T900
2026-10-29T15:27:58Z  BLOCK  git -c alias.p=push p   -> • Tasks still In Progress: T900
2026-10-29T15:27:58Z  ALLOW  git -C . log
-- board: T900 Ready for Review; verify row only in wt-t900's working tree
2026-10-29T15:27:58Z  BLOCK  git merge -X ours feat/t900-x   -> • verify row for T900 is not committed on feat/t900-x — commit it, then merge
-- verify row committed on feat/t900-x
2026-10-29T15:27:59Z  ALLOW  git merge -X ours feat/t900-x
```

This is Success Criterion 1 (`-C` merge and `-c alias` push blocked, `-C . log` allowed) and
Success Criterion 2 (`-X ours` blocked with the D4 message, allowed once committed).

**DELTA**: A merge, push, pull or rebase written with git global options (`-C`, `-c`, `--git-dir`, …) or as an inline `-c alias`, and a merge with any option or several branches, can no longer pass the gate unchecked or without each task's verify row committed on its branch.

**WITNESS**: [who ran it and when — derived from `memory/event-trace/Txxx.jsonl`, never the
implementing agent alone]
