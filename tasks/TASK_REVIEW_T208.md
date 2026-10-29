# TASK_REVIEW — T208: Auto verify reads a PASS written as **Verdict: PASS …**

> Sibling of `tasks/TASK_GUIDE_T208.md`. Everything here is **filled by the reviewer at Stage
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
| **New test(s) cover Acceptance Criteria (file paths pasted)** | ☑ pass | `tests/test_auto_verify.py` (`test_t208_ac1_…` 12 cases, `test_t208_ac2_…` 2, `test_t208_ac3_still_blocked` 12 cases); fixture `tests/fixtures/auto_verify/verify_pass_bold_sentence.json`. Red first on the unchanged hook: `11 failed, 15 passed, 200 deselected` (`-k t208`); after the change: `26 passed, 200 deselected in 0.29s`. AC 4 mutation A (old regex restored): `11 failed, 15 passed` — ac1 `**Verdict: {w}**`, `**Verdict: {w}. All six things hold.**`, `**Verdict**: {w}`, indented `**Verdict: {w}**` (PASS and FAIL), ac2 parse + ac2 stub row, ac3 `pass-and-fail`. Mutation B (`^` anchor dropped): `2 failed, 24 passed` — ac3 `mid-sentence`, `mid-sentence-label-only`. Regex restored, `26 passed`. |
| Verification command run | ☑ pass | `python3 -m pytest tests/test_auto_verify.py -q` → `226 passed in 91.74s (0:01:31)`; `python3 -m pytest .claude/hooks/tests -q` → `1158 passed, 25 subtests passed in 23.51s` |
| Negative cases hold | ☑ pass | `test_t208_ac3_still_blocked` (12 cases, all `blocked`): no verdict line, one PASS and one FAIL (label-bold and sentence-bold), `BLOCKED`, `SKIP`, `PASSED`, lower-case `pass`, `Verdict: PASS` mid-sentence (bold sentence and bold label), plain prose `My Verdict: PASS`, non-success subtype, `is_error` run |
| verify | ☑ pass | auto-run by hook, session 4309931e-8059-4a1e-bd63-4ded12923d8d, commit 8ec94d5fbeeb1c273c2d0cfbca77b8ad335d4f22, log .claude/verify-runs/T208-8ec94d5fbeeb.log — pass |
| Review scope bounded to the change's blast radius (affected set, not whole repo) | ☑ pass | Supervisor Stage 4 2026-10-29: code-review over `main...HEAD` (VERDICT regex + comment + docstring, T208 test block, fixture). lane_check `C1, 3 files, 68 lines, FITS`. Regex `^\s*\*\*Verdict(?::\*\*|\*\*:|:)\s*([A-Z]+)\b`: line-start anchor kept, upper-case word only, PASS/FAIL set logic unchanged, so two different verdicts and any other word stay blocked. No findings at P0-P2. P3 (not fixed, pre-existing): a verdict line inside a fenced block still counts; docs/claude-md/tracks.md still names only the `**Verdict:**` shape. security-review (Risk Medium): the widening only admits bold variants of the same anchored label; it cannot turn a FAIL report into a pass, because a PASS+FAIL pair stays blocked. |
| Full smoke suite still green (no regression) | ☑ pass | the two suites above: 226 passed and 1158 passed, 25 subtests passed |
| **Companion score (easy-verifier)** | ☐ pass / ☐ fail / ☐ N/A | [`overall` and `change_risk` as the tool returned them, the scope, the ref, and the absolute path of the verifier report after a literal `report:` label — e.g. "overall 86 (>= 80), change_risk pass, scope changes, ref `main...HEAD`, report: `/home/me/.easy-verifier-reports/kit/score_changes_20261028T0530Z.html`". The gate reads the path that follows `report:` and nothing else, so with no label, or a path that is absent, the row is unscored — write ☑ N/A instead. ☑ N/A with a reason when neither companion tool was run: the merge gate blocks on ☑ fail only, never on an absent or N/A row] |
| **UI: Visual regression (diff or verdict pasted)** | ☑ N/A | no UI component: hook-only change |
| **UI: Design-system compliance (tokens/colors/typography verified)** | ☑ N/A | no UI component: hook-only change |
| **UI: Responsiveness at target viewports** | ☑ N/A | no UI component: hook-only change |

---

## Demonstration

> Anchors what this task delivered to an observable before/after pair. BEFORE has no `N/A` path:
> if the task changes executable code, BEFORE is a pasted, timestamped terminal capture taken
> **before any implementation commit exists**; if it does not (docs, templates, skill-instruction
> text), BEFORE is the **verbatim prior content** of what changed — a quoted excerpt, not a command.

**BEFORE** (captured 2026-10-29T19:26:48+0700, before any implementation commit; unchanged hook at `f2bc739`, real `--start` path, stub `claude` on PATH printing the saved T207 output, throwaway project via the `tests/test_auto_verify.py` helpers):

```
$ python3 <throwaway>/.claude/hooks/stop_auto_verify.py --start T951
T951: auto verify started for commit cfb069405fab — log .claude/verify-runs/T951-cfb069405fab.log
verify row: ☐ blocked | auto-run by hook, session 4af6b987-45a0-4709-9b67-2ffb823aa29d, commit cfb069405faba5a779ac1505b8f3885f6ff4bf7c, log .claude/verify-runs/T951-cfb069405fab.log — blocked (no single verdict line)
== log T951-cfb069405fab.log
$ claude -p '/verify T951' --max-budget-usd 2 --output-format json
verdict: blocked (no single verdict line)
```

**AFTER** (captured 2026-10-29T19:27:50+0700, same command and stub, hook with the new `VERDICT`):

```
$ python3 <throwaway>/.claude/hooks/stop_auto_verify.py --start T951
T951: auto verify started for commit f4515f11c6fc — log .claude/verify-runs/T951-f4515f11c6fc.log
verify row: ☑ pass | auto-run by hook, session 4af6b987-45a0-4709-9b67-2ffb823aa29d, commit f4515f11c6fcf7f665b30817ce0f7c95575bca24, log .claude/verify-runs/T951-f4515f11c6fc.log — pass
== log T951-f4515f11c6fc.log
$ claude -p '/verify T951' --max-budget-usd 2 --output-format json
verdict: pass
```

Regex: before `^\s*\*\*Verdict:\*\*\s*([A-Z]+)\b`; after `^\s*\*\*Verdict(?::\*\*|\*\*:|:)\s*([A-Z]+)\b` (both `re.M`).

**DELTA**: A real `/verify` PASS written as `**Verdict: PASS. …**` is now recorded as `☑ pass` instead of `☐ blocked`, and the hook still blocks a missing, doubled, non-PASS/FAIL or mid-sentence verdict.

**WITNESS**: [who ran it and when — derived from `memory/event-trace/Txxx.jsonl`, never the
implementing agent alone]
