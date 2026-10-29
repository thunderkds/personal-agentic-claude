# TASK_REVIEW — T209: Auto verify refuses a verdict line that lists choices (`**Verdict:** PASS - FAIL - …`) and

> Sibling of `tasks/TASK_GUIDE_T209.md`. Everything here is **filled by the reviewer at Stage
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
| **New test(s) cover Acceptance Criteria (file paths pasted)** | ☑ pass | `tests/test_auto_verify.py` (T209 block: `test_t209_ac1_a_line_that_lists_choices_is_blocked` x9, `test_t209_ac2_...` x2, `test_t209_ac3_...` x3, `test_t209_sc1_...`, `test_t209_ac4_...`). Red before the change: `12 failed, 2 passed` for `-k t209` on the unchanged hook. AC 5 mutation (the choice filter `if not CHOICES.match(rest)` replaced by `if True`): `11 failed, 5 passed` for `-k t209`, AC 1 cases all RED; restored, green. Round 2 (verify run found two fail-open shapes): second verdict word now case-insensitive and `-`, `–`, `—` count as separators before a verdict word; first word stays upper-case. New cases: ac1 x8 more (`PASS or fail`, `PASS / Fail`, `PASS - FAIL`, `PASS - fail`, `PASS – FAIL`, `PASS — FAIL`, `PASS—FAIL`, `PASS | fail`), ac3 x3 more (`PASS — all six hold`, `PASS - nothing broke`, `PASS – nothing broke`). RED on 329e0a7: `7 failed, 20 passed` for `-k t209`. Mutation rerun (`if True`): `19 failed, 8 passed`, restored. After: `tests/test_auto_verify.py` 253 passed; `.claude/hooks/tests` 1158 passed, 25 subtests passed. |
| Verification command run | ☑ pass | `python3 -m pytest tests/test_auto_verify.py -q` -> `242 passed in 91.74s`; `python3 -m pytest .claude/hooks/tests -q` -> `1158 passed, 25 subtests passed in 23.29s`; `python3 -m pytest tests -q` -> `1198 passed in 108.10s` |
| Negative cases hold | ☑ pass | the 12 T208 fail-closed cases (`test_t208_ac3_still_blocked`) still blocked; the blank template alone is `blocked (no single verdict line)`; a verdict word later in a sentence (`PASS. ... FAIL or BLOCKED`) or a clause comma (`PASS, all six hold`) stays a pass (`test_t209_ac3_...`) |
| verify | ☑ pass | auto-run by hook, session 37292b55-ebef-43d5-b2b9-11b17e88421f, commit b38c7a53e8b92421e73999ac35c9eec18066b5c0, log .claude/verify-runs/T209-b38c7a53e8b9.log — pass |
| Review scope bounded to the change's blast radius (affected set, not whole repo) | ☑ pass | Supervisor Stage 4 2026-10-29: round 1 — VERDICT captures the line's rest; CHOICES drops a line whose first word is followed by a choice; round 2 (after the auto verify run 1 finding) — second verdict word case-insensitive, `-`/`–`/`—` separators, prose after a dash still a pass (tests for both). lane_check C1 FITS. Accepted: a plain-space second word (`PASS fail-safe`) now reads as a choice — fail-closed. P3: `**Verdict: PASS**/FAIL` still counts as PASS. security-review (Risk Medium): the change only removes lines from the verdict set; it cannot create a pass. |`, or `/ , or and`/space + another verdict word; docstring; tests; tracks.md sentence). lane_check `C1, 3 files, 76 lines, FITS`. Accepted design: choice detected only right after the first word, so prose like `PASS. Nothing left to FAIL` stays a pass. P3 (not fixed): `**Verdict: PASS**/FAIL` (bold closed before the slash) still counts as PASS — contrived. security-review (Risk Medium): the change only removes lines from the verdict set; it cannot create a pass, and the PASS+FAIL rule is unchanged. |
| Full smoke suite still green (no regression) | ☑ pass | `tests` 1198 passed; `.claude/hooks/tests` 1158 passed, 25 subtests passed (output above) |
| **Companion score (easy-verifier)** | ☐ pass / ☐ fail / ☐ N/A | [`overall` and `change_risk` as the tool returned them, the scope, the ref, and the absolute path of the verifier report after a literal `report:` label — e.g. "overall 86 (>= 80), change_risk pass, scope changes, ref `main...HEAD`, report: `/home/me/.easy-verifier-reports/kit/score_changes_20261028T0530Z.html`". The gate reads the path that follows `report:` and nothing else, so with no label, or a path that is absent, the row is unscored — write ☑ N/A instead. ☑ N/A with a reason when neither companion tool was run: the merge gate blocks on ☑ fail only, never on an absent or N/A row] |
| **UI: Visual regression (diff or verdict pasted)** | ☐ N/A | no UI component: hook-only change |
| **UI: Design-system compliance (tokens/colors/typography verified)** | ☐ N/A | no UI component: hook-only change |
| **UI: Responsiveness at target viewports** | ☐ N/A | no UI component: hook-only change |

---

## Demonstration

> Anchors what this task delivered to an observable before/after pair. BEFORE has no `N/A` path:
> if the task changes executable code, BEFORE is a pasted, timestamped terminal capture taken
> **before any implementation commit exists**; if it does not (docs, templates, skill-instruction
> text), BEFORE is the **verbatim prior content** of what changed — a quoted excerpt, not a command.

**BEFORE**: captured before any implementation commit, on the unchanged hook (`.claude/hooks/stop_auto_verify.py`, blob `1a28232`, HEAD `cd98cec`). Throwaway project with the kit's hooks, stub `claude` on PATH printing a report whose only verdict line is `**Verdict:** PASS | FAIL | BLOCKED | SKIP`; real `--start` path. The blank template line is recorded as a pass:

```
date: 2026-10-29T20:07:04+07:00
hook sha1 source: 1a282329df95b706ef72bc0676341f3c82765757
$ python3 .claude/hooks/stop_auto_verify.py --start T951
T951: auto verify started for commit cea035562a03 — log .claude/verify-runs/T951-cea035562a03.log exit 0
--- log T951-cea035562a03.log
$ claude -p '/verify T951' --max-budget-usd 2 --output-format json
verdict: pass
verify row: ☑ pass | auto-run by hook, session bb6500c2-6ee9-4ce9-bc0e-ea2f246f2fd4, commit cea035562a03785c2356e1c9112338f9809287f2, log .claude/verify-runs/T951-cea035562a03.log — pass
```

**AFTER**: same script (`--start` on a throwaway project, stub `claude`, same blank-template report), run on the changed working-tree hook, 2026-10-29T20:10:24+07:00:

```
date: 2026-10-29T20:10:24+07:00
hook sha1 source: 1a282329df95b706ef72bc0676341f3c82765757
$ python3 .claude/hooks/stop_auto_verify.py --start T951
T951: auto verify started for commit 837e65c32570 — log .claude/verify-runs/T951-837e65c32570.log exit 0
--- log T951-837e65c32570.log
$ claude -p '/verify T951' --max-budget-usd 2 --output-format json
verdict: blocked (no single verdict line)
verify row: ☐ blocked | auto-run by hook, session bb6500c2-6ee9-4ce9-bc0e-ea2f246f2fd4, commit 837e65c3257019d15bf72f844aeb39fa8656aa43, log .claude/verify-runs/T951-837e65c32570.log — blocked (no single verdict line)
```

**DELTA**: A session that copies the report template's `**Verdict:** PASS | FAIL | BLOCKED | SKIP` line without choosing is now recorded as `blocked`, not as a pass.

**WITNESS**: [who ran it and when — derived from `memory/event-trace/Txxx.jsonl`, never the
implementing agent alone]
