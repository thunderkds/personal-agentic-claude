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
| **New test(s) cover Acceptance Criteria (file paths pasted)** | ☑ pass | `tests/test_auto_verify.py` — 43 new tests for AC 1–8 (`test_ac1_*` ×4, `test_ac2_*` ×6, `test_ac3_*` ×7, `test_ac4_*` ×2, `test_ac5_*` ×9, `test_ac6_*` ×3, `test_ac7_*` ×10, `test_ac8_*` ×2); `.claude/hooks/tests/test_stop_auto_mode_check.py` unchanged and green (46 passed), which is AC 1's "stays green unchanged" clause |
| Verification command run | ☑ pass | `python3 -m pytest -q tests/test_auto_verify.py .claude/hooks/tests` → `1010 passed, 25 subtests passed in 65.59s`; `python3 -m pytest -q tests` → `889 passed in 59.45s`; `bash scripts/validate.sh` → `validate.sh: PASS` (the guide writes `./validate.sh`; the script lives at `scripts/validate.sh`). Combined `pytest -q tests .claude/hooks/tests` → `1806 passed, 25 subtests passed` against a pre-task baseline of `1763 passed, 25 subtests passed` (2026-10-28T05:41:15Z) |
| Negative cases hold | ☑ pass | Each block is its own test and each one failed before the change or passes only because of it: no run record (`test_ac5_a_minimal_line_with_no_record_blocks`), a record for another commit (`..._for_another_commit_blocks`), a fail record edited to pass (`..._fail_record_blocks_even_if_the_line_is_edited_to_pass`), three hand-typed line shapes (`test_ac5_a_hand_typed_minimal_line_blocks`, parametrized), a forged record written where an agent can write (`..._a_record_the_agent_could_write_is_not_trusted_on_the_minimal_track`); no marker on either track (`test_ac6_*`, `test_ac4_*` incl. both template copies); a user-filled `verify:` line is never run over (`test_ac3_a_verify_line_the_user_filled_is_never_run_over`); a user-written `Not done:` slot is left alone (`test_ac7_a_slot_the_user_wrote_is_left_alone_and_the_reason_goes_in_the_log`) |
| verify | ☑ pass | `/verify T188` run by the Supervisor at the user's request, 2026-10-28. Runtime observation, not tests: an isolated clone of this branch, a real board row, a real Decision record and a stubbed `claude` binary. BEFORE (main's hook, same fixture): nothing started, no `.claude/verify-runs/`, the slot still read `auto verify: running (T182)`. AFTER (this branch): `T900: auto verify started for commit c57acb014bef`; the record gained `- verify: ☑ pass — auto-run-by-hook [tag hyphenated on purpose: the gate reads the literal tag as a claim that the hook wrote this row], session sess-abc123, commit c57acb01…, log .claude/verify-runs/T900-c57acb014bef.log` **inside** its `Checked:` field, before `**Files:**`; the `Not done:` slot became `auto verify: ☑ pass (…)` with the merge clause intact; the run record landed outside the repo. Merge gate at its own surface: with the record → `T900 (evidence row present but no verified tool call…)`; record removed → `T900 (no evidence row)`; the same line hand-typed as a user `/verify` pass → `no evidence row`. Probes: a marker inside an HTML comment started nothing; malformed run output → `☐ blocked`, no "pass" anywhere; two `Not done:` lines → the line written, the slot refused with the reason logged. Extended track re-driven: row and slot both written, no regression. **Not covered: AC 9** — every drive stubbed `claude`, so a real paid `/verify` session has still never run. | **The user's (`/verify T188`).** An auto verify cannot vouch for the code that starts it (guide, Evidence note). Not filled by this agent, and never by an auto run for this task |
| Review scope bounded to the change's blast radius (affected set, not whole repo) | ☑ pass | Reviewed: the 5 changed hook/lib files and their 3 callers. `pre_bash_block_unsafe_merge.py` is the hub: its other two callers (`.claude/hooks/tests/test_merge_gate_t095.py`, `test_merge_gate_my_tasks.py`) and both "T182 alone may change the gate" guard tests were run and are green, unchanged. Skipped: everything not importing `verify_record`, `auto_mode` or the two Stop hooks |
| Full smoke suite still green (no regression) | ☑ pass | `1806 passed` (above). The one guard that could have regressed, `test_merge_gate_is_untouched`, is green **unchanged** — see "Decisions worth the reviewer's eye" below |
| **UI: Visual regression (diff or verdict pasted)** | ☐ N/A | pure-hook task: no UI component |
| **UI: Design-system compliance (tokens/colors/typography verified)** | ☐ N/A | pure-hook task: no UI component |
| **UI: Responsiveness at target viewports** | ☐ N/A | pure-hook task: no UI component |

### Decisions worth the reviewer's eye

1. **The merge-gate tripwire is now an explicit allowlist, and it is tested (Stage 4 P2, fixed).**
   Two tests assert that only an authorised task has changed
   `.claude/hooks/pre_bash_block_unsafe_merge.py`:
   `.claude/hooks/tests/test_stop_auto_mode_check.py::test_merge_gate_is_untouched` and
   `tests/test_auto_mode.py::test_ac4_merge_gate_file_is_unchanged`. Both read
   `all("T182" in subject ...)` — one ID, as a bare substring. T188 had to change that file (AC 5),
   its commit subject names both T188 and T182, and the check passed; but it would then equally pass
   for any later commit that merely *mentioned* T182 while changing the gate, which is the one thing
   the check exists to catch. Fixed as the reviewer directed, with the commit subject left as it is:
   - `.claude/hooks/tests/merge_gate_guard.py` (**new**) holds the rule **once**, as
     `AUTHORISED_TASKS = ("T182", "T188")` with the rule each task owns in the gate recorded beside
     its ID, matched whole (`\bT182\b`), plus the unchanged pending-change check. Both suites call
     it; the duplicated helper is gone from both. A task that must touch the gate adds its ID with
     the Supervisor's sign-off — that edit is the audit trail.
   - `.claude/hooks/tests/test_merge_gate_guard.py` (**new**, 10 tests) is the part that was missing
     all along: proof that the tripwire **rejects** something. An unauthorised commit is reported;
     so is one unauthorised commit among authorised ones, an uncommitted change, and a `base_ref`
     that does not resolve (fails closed). Before this, the guard had never rejected anything —
     T044 defect C's lesson, in a second place.
   - AC 1's "stays green unchanged" held where it was aimed: the 45 behaviour tests of
     `test_stop_auto_mode_check.py` are untouched and green, and only its guard test moved onto the
     shared helper.
   - **Residual, stated plainly:** matching is still on the commit subject's text, so a commit
     belonging to task T999 whose subject says "extends T182" would pass. Closing that needs the
     subject's own `type(Txxx):` scope to be the authorised one. Not done — the reviewer specified
     "every subject names at least one of them", and a stricter prefix rule could reject an
     unconventional but honest subject. Say the word and it is a two-line change in one place now.

   Both test names still read "untouched" / "is_unchanged" although the gate *was* changed by an
   authorised task. They were left as they are (they are cited in T180's and T182's evidence); each
   one's docstring and failure message now states the real rule.
2. **A hand-typed `verify:` line in a Decision record counts for nothing** — including one claiming
   the user ran `/verify`. Before T188 a minimal-track task at Ready for Review always blocked the
   merge (no guide, no review file, so no Evidence section). Accepting only a hook-written line with
   its run record makes the new path a strict widening; accepting a hand-typed line would have been
   the one way this change could make the gate weaker.
3. **One stderr line when a `Track: minimal` row at Ready for Review has no Decision record.** The
   guide's edge case asks for it, and it fires for non-auto minimal rows too, because auto mode
   cannot be read from a record that is not there. It is one line on a Stop hook's stderr (the debug
   log), and a minimal-track task always ends with a record (T178 D5), so the line is information,
   not noise.

### Residual limits (not defects, stated plainly)

- **Two minimal-track auto tasks finishing at the same instant** both write `tasks/MINIMAL_LOG.md`.
  Each re-reads the file immediately before its write, which is the measure the guide prescribes, but
  that shrinks the window rather than closing it: the later write could drop the earlier line. The
  extended track cannot hit this (one file per task). No locking was added — the cut list rules out
  anything beyond the prescribed re-read.
- The gate still **trusts that a recorded test command ran** (T044's own stated limit, unchanged).

### Lane check (Stage 4 P3, recorded)

```
$ python3 scripts/lane_check.py tasks/TASK_GUIDE_T188.md main...HEAD
lane: C2, 10 files, 1741 lines, EXCEEDS (lines 1741 > 500); unpredicted:
  .claude/hooks/lib/verify_record.py, tasks/TASK_GUIDE_T188.md, tasks/TASK_GUIDE_T189.md
```

- **`.claude/hooks/lib/verify_record.py` was a real prediction miss** in the guide's
  `## Files to Change (Predicted)` table, now added there with what changed in it. It is where the
  change belonged: the D3 `verify:` line shape and the `Checked:` field are the record's shape, and
  that module already owned the row's shape and the run record, so the writer hook and the merge
  gate could keep reading one definition instead of two.
- `tasks/TASK_GUIDE_T188.md` is this task's own guide (the Fidelity Gate tick, the Completion
  Checklist, and the P3 table row) and `tasks/TASK_GUIDE_T189.md` arrived with the same planning
  commit as this branch's base — neither is implementation surface.
- **EXCEEDS is warn-only and the Supervisor is not relabelling the task.** Of the 1741 lines, 540 are
  `tests/test_auto_verify.py` and 355 are the two task guides; the implementation itself is the new
  reader plus edits to four files, and `stop_auto_mode_check.py` got *shorter* (428 → 322 lines)
  because its discovery logic moved into the shared reader.

-------|--------|------------------------|
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

**AFTER** (2026-10-28T06:19:35Z, branch `feat/t188-auto-verify-both-tracks`): a scratch project
whose board has one `Track: minimal` row at Ready for Review and whose `tasks/MINIMAL_LOG.md` record
carries `Mode: auto`. `claude` is a stub on `PATH` that prints `**Verdict:** PASS` — no paid call.
The Stop hook is run exactly as `.claude/settings.json` runs it:

```
Wed Oct 28 06:19:35 AM UTC 2026
=== AFTER: the Stop hook fires for a Track: minimal, Mode: auto task at Ready for Review ===
[hook:stop_auto_verify] T777: auto verify started for commit e825370c3e2b — log .claude/verify-runs/T777-e825370c3e2b.log

=== the Decision record after the run ===
## T777 — Sort the names · minimal
Mode: auto
**Asked:** "sort the names [auto]"
**Decisions:**
1. sort A–Z — RULE: `docs/claude-md/tracks.md` `### Minimal-track flow`
**Checked:**
- New test `test_sort_is_alphabetical` — failed before the change, passes after
- Suite: `pytest -q` — 12 passed
- verify: ☑ pass — auto-run by hook, session d3f0a1b2-1111-4c0d-9e8f-abcdef012345, commit e825370c3e2b8dde600e4e05fefb9920cc6fc1b5, log .claude/verify-runs/T777-e825370c3e2b.log
**Files:** `src/app.py`
**Not done:** merge (yours); auto verify: ☑ pass (session d3f0a1b2-1111-4c0d-9e8f-abcdef012345, commit e825370c3e2b8dde600e4e05fefb9920cc6fc1b5, log .claude/verify-runs/T777-e825370c3e2b.log)

=== the run record, outside the repo (agents are denied writes there) ===
{"task": "T777", "commit": "e825370c3e2b8dde600e4e05fefb9920cc6fc1b5", "verdict": "pass", "session": "d3f0a1b2-1111-4c0d-9e8f-abcdef012345", "log": ".claude/verify-runs/T777-e825370c3e2b.log"}

=== the merge gate on this task: allow, then block once the record is gone ===
with the run record: exit 0 and no block printed above = allow
{"decision": "block", "reason": "[hook:pre_bash] Pipeline gate failed — cannot push/merge:
  • Tasks in Ready for Review missing Stage 5 verify evidence: T777 (no evidence row) …"}
```

The user's three BEFORE symptoms are gone: the run starts for a minimal row, the record carries the
`verify:` line inside its `Checked:` field, and the `Not done:` slot names the result instead of
`auto verify: running (T182)`.

**This run found a defect the tests had missed** and is why it was worth doing: the first AFTER
capture (06:17:40Z) put the `verify:` line *after* `**Not done:**`, because the `Checked:` field's
bullet pattern `[-*]` also matched the record's own `**Files:**` and `**Not done:**` lines. The
bullet is now `(?:[-+]|\*(?!\*))` and `test_ac3_the_checked_lines_the_user_wrote_are_left_exactly_as_they_were`
now pins the order `verify: < **Files:** < **Not done:**`.

**DELTA**: A task started with `[auto]` on the **minimal track** now gets the same real `/verify` run
the extended track has had since T182 — the hook writes its result into the Decision record and the
merge gate reads it there under T182's record rule — and on both tracks the report the user reads
stops saying `auto verify: running (T182)` once the run has ended.

**WITNESS**: `common-infrastructure` agent ran every command above on 2026-10-28 (05:41:15Z baseline,
05:51:12Z BEFORE, 06:19:35Z AFTER, 06:19:47Z final suite), attributed in
`memory/event-trace/T188.jsonl` via `.claude/hooks/.state/active_task`. **Not the implementing agent
alone**: AC 9, the one paid live `/verify` run, is the user's and has not been run — the Supervisor
must ask for the go first. `/verify T188` itself is the user's.
