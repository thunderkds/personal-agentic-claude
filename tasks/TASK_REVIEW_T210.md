# TASK_REVIEW — T210: Merge gate closes four gaps — `git pull` is gated, `timeout`-wrapped test runs count, `git

> Sibling of `tasks/TASK_GUIDE_T210.md`. Everything here is **filled by the reviewer at Stage
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
| **New test(s) cover Acceptance Criteria (file paths pasted)** | ☑ pass | `.claude/hooks/tests/test_merge_gate_t210.py` (50 tests: AC 1 pull forms blocked / clean board allowed / quoted mention is data; AC 2 merge-base allowed, merge/merge-file/merge-tree blocked; AC 3 timeout-wrapped runs count, `timeout 900 echo pytest` does not; AC 4 merge + narrowed push blocked with the D4 message then allowed after commit, auto-verify row committed after the verified commit passes, code after it does not, guide-first precedence, minimal-track line read from the branch; AC 5 unresolved branch / detached HEAD / git failure keep the working-tree read). `python3 -m pytest .claude/hooks/tests/test_merge_gate_t210.py -q` → `50 passed in 0.60s` (red first on `73a6f89`: `30 failed, 20 passed in 0.71s`). AC 6: `.claude/hooks/tests/test_merge_gate_guard.py` → `14 passed in 0.20s`. |
| Verification command run | ☑ pass | `python3 -m pytest .claude/hooks/tests -q && python3 -m pytest tests -q` on `e162191`, 2026-10-29T20:30+07:00: `1209 passed, 25 subtests passed in 24.43s` then `1 failed, 1181 passed` — the one was `tests/test_auto_verify.py::test_t203_ac2_start_twice_on_one_commit_runs_once` (timing stub `sleep=2`, auto verify lock, does not touch the gate); alone `tests/test_auto_verify.py` → `226 passed in 91.63s`; full `tests` rerun → `1182 passed in 107.20s`. |
| Negative cases hold | ☑ pass | AC 7 mutations, each applied to the gate and the T210 tests run, file restored after: M1 drop pull from the patterns: exit 1 → 6 failed, 44 passed in 0.64s; M2 drop the merge-base lookahead: exit 1 → 3 failed, 47 passed in 0.62s; M3 drop the timeout prefix: exit 1 → 6 failed, 44 passed in 0.64s; M4 read the verify row from the working tree again: exit 1 → 5 failed, 45 passed in 0.57s. Negatives in the suite: `timeout 900 echo pytest`, `timeout pytest`, `grep "git pull"`, merge-file/merge-tree, unknown merge option, octopus merge, no-such-branch, detached HEAD, git failure on the tip. |
| verify | ☑ pass | auto-run by hook, session b503c47d-514b-48ff-9412-fb275de29034, commit 7ea033bef3f53d97745a0c58913ba2b326cec6bb, log .claude/verify-runs/T210-7ea033bef3f5.log — pass |
| Review scope bounded to the change's blast radius (affected set, not whole repo) | ☑ pass | Supervisor Stage 4 2026-10-29: code-review + security-review (Risk High) over `main...HEAD`: BLOCKED_PATTERNS (+`git pull`; `merge(?!-base\b)`), BENIGN prefix (+`timeout` with `-k/-s` args, one `(` peel), D4 `branch_target`/`committed_verify_row`/`_auto_row_confirmed_at`, the `has_filled_verify_row` split, `_git_actions` extraction, 50 new tests, guard allowlist += T210. Deviations from the guide accepted: D3 `(?!-base\b)` (the guide's `(?!-)` would have freed merge-file/merge-tree, contrary to D3's own text); D2 option args (AC 3's own case needed them); D4 also reads the minimal-track `verify:` line from the branch. Confirmed: committing the hook-written row does not break D4 — `same_code` allows the tip to differ from the verified commit only in the result file. Security: every change narrows or keeps what is allowed except the merge-base exemption, which is anchored to `-base\b`; D4 falls back to today's working-tree read only when the branch cannot be resolved. Findings: P2 follow-up (pre-existing, outside scope) — `git -C <dir> pull|merge|push` and `git -c k=v merge` match no BLOCKED_PATTERNS and are ungated; P3 — `_auto_row_confirmed_at` repeats ~8 lines of `verify_record.auto_row_confirmed`, and the gate imports the private `guide_sections._candidate_paths`; note — `test_t203_ac2_start_twice_on_one_commit_runs_once` (timing, `sleep=2` stub) failed once in a full run and passed on rerun. |
| Full smoke suite still green (no regression) | ☑ pass | Both suites green (see Verification row). Oracles `t190_pre_change_gate_output.txt`, `t197_pre_change_gate_output.txt` NOT regenerated: no existing message text changed, and their byte-identical tests pass. |
| **Companion score (easy-verifier)** | ☐ pass / ☐ fail / ☐ N/A | [`overall` and `change_risk` as the tool returned them, the scope, the ref, and the absolute path of the verifier report after a literal `report:` label — e.g. "overall 86 (>= 80), change_risk pass, scope changes, ref `main...HEAD`, report: `/home/me/.easy-verifier-reports/kit/score_changes_20261028T0530Z.html`". The gate reads the path that follows `report:` and nothing else, so with no label, or a path that is absent, the row is unscored — write ☑ N/A instead. ☑ N/A with a reason when neither companion tool was run: the merge gate blocks on ☑ fail only, never on an absent or N/A row] |
| **UI: Visual regression (diff or verdict pasted)** | ☐ N/A | no UI component (hook-only change) |
| **UI: Design-system compliance (tokens/colors/typography verified)** | ☐ N/A | no UI component (hook-only change) |
| **UI: Responsiveness at target viewports** | ☐ N/A | no UI component (hook-only change) |

---

## Demonstration

> Anchors what this task delivered to an observable before/after pair. BEFORE has no `N/A` path:
> if the task changes executable code, BEFORE is a pasted, timestamped terminal capture taken
> **before any implementation commit exists**; if it does not (docs, templates, skill-instruction
> text), BEFORE is the **verbatim prior content** of what changed — a quoted excerpt, not a command.

**BEFORE**: captured 2026-10-29T20:21+07:00 on the UNCHANGED gate (`5c17cf5`, before any T210 implementation commit), by feeding real PreToolUse JSON events to `python3 <clone>/.claude/hooks/pre_bash_block_unsafe_merge.py` in a throwaway clone. Driver: `python3 $S/demo_gate.py /home/hungnguyenhuu/workspace/pets/wt-t210 $S/before` (`$S` = this session's scratchpad, `/tmp/claude-1000/-home-hungnguyenhuu-workspace-pets-personal-agentic-claude/24c52e71-3f68-4a99-b4fe-2b45d25d5e60/scratchpad`).

```text
gate under test: $S/before/clone/.claude/hooks/pre_bash_block_unsafe_merge.py (source /home/hungnguyenhuu/workspace/pets/wt-t210 @ 5c17cf5)
[2026-10-29T20:21:23+07:00] G1 pull, In Progress row
  event command: 'git pull'  cwd: $S/before/clone
  exit 0 -> ALLOWED: (no output)
[2026-10-29T20:21:23+07:00] G1 pull --ff-only, In Progress row
  event command: 'git pull --ff-only'  cwd: $S/before/clone
  exit 0 -> ALLOWED: (no output)
[2026-10-29T20:21:23+07:00] G3 merge-base --is-ancestor, In Progress row
  event command: 'git merge-base --is-ancestor HEAD main'  cwd: $S/before/clone
  exit 0 -> BLOCKED: [hook:pre_bash] Pipeline gate failed — cannot push/merge:
  • Tasks still In Progress: T900
[2026-10-29T20:21:23+07:00] G3 control: merge feat/x, In Progress row
  event command: 'git merge feat/x'  cwd: $S/before/clone
  exit 0 -> BLOCKED: [hook:pre_bash] Pipeline gate failed — cannot push/merge:
  • Tasks still In Progress: T900
[2026-10-29T20:21:23+07:00] G2 trace = only `timeout 900 python3 -m pytest -q`
  event command: 'git merge feat/x'  cwd: $S/before/clone
  exit 0 -> BLOCKED: [hook:pre_bash] Pipeline gate failed — cannot push/merge:
  • Tasks in Ready for Review missing Stage 5 verify evidence: T900 (evidence row present but no verified tool call in memory/event-trace/T900.jsonl)
  worktree status: ?? tasks/TASK_REVIEW_T900.md
[2026-10-29T20:21:24+07:00] G4 merge feat/t900-x, verify row uncommitted in worktree
  event command: 'git merge feat/t900-x'  cwd: $S/before/clone
  exit 0 -> ALLOWED: (no output)
  worktree status after commit: (clean)
[2026-10-29T20:21:24+07:00] G4 merge feat/t900-x, verify row committed on the branch
  event command: 'git merge feat/t900-x'  cwd: $S/before/clone
  exit 0 -> ALLOWED: (no output)
```

Read: G1 `git pull` ALLOWED with an In Progress row; G3 `git merge-base` BLOCKED as a merge; G2 a trace whose only test run is `timeout 900 python3 -m pytest -q` reads "no verified tool call"; G4 the merge is ALLOWED while the verify row is only an untracked file in the worktree.

**AFTER**: same driver, same events, on the changed gate (`e162191`): `python3 $S/demo_gate.py /home/hungnguyenhuu/workspace/pets/wt-t210 $S/after`.

```text
gate under test: $S/after/clone/.claude/hooks/pre_bash_block_unsafe_merge.py (source /home/hungnguyenhuu/workspace/pets/wt-t210 @ e162191)
[2026-10-29T20:30:19+07:00] G1 pull, In Progress row
  event command: 'git pull'  cwd: $S/after/clone
  exit 0 -> BLOCKED: [hook:pre_bash] Pipeline gate failed — cannot push/merge:
  • Tasks still In Progress: T900
[2026-10-29T20:30:19+07:00] G1 pull --ff-only, In Progress row
  event command: 'git pull --ff-only'  cwd: $S/after/clone
  exit 0 -> BLOCKED: [hook:pre_bash] Pipeline gate failed — cannot push/merge:
  • Tasks still In Progress: T900
[2026-10-29T20:30:19+07:00] G3 merge-base --is-ancestor, In Progress row
  event command: 'git merge-base --is-ancestor HEAD main'  cwd: $S/after/clone
  exit 0 -> ALLOWED: (no output)
[2026-10-29T20:30:19+07:00] G3 control: merge feat/x, In Progress row
  event command: 'git merge feat/x'  cwd: $S/after/clone
  exit 0 -> BLOCKED: [hook:pre_bash] Pipeline gate failed — cannot push/merge:
  • Tasks still In Progress: T900
[2026-10-29T20:30:19+07:00] G2 trace = only `timeout 900 python3 -m pytest -q`
  event command: 'git merge feat/x'  cwd: $S/after/clone
  exit 0 -> ALLOWED: (no output)
  worktree status: ?? tasks/TASK_REVIEW_T900.md
[2026-10-29T20:30:19+07:00] G4 merge feat/t900-x, verify row uncommitted in worktree
  event command: 'git merge feat/t900-x'  cwd: $S/after/clone
  exit 0 -> BLOCKED: [hook:pre_bash] Pipeline gate failed — cannot push/merge:
  • verify row for T900 is not committed on feat/t900-x — commit it, then merge
  worktree status after commit: (clean)
[2026-10-29T20:30:19+07:00] G4 merge feat/t900-x, verify row committed on the branch
  event command: 'git merge feat/t900-x'  cwd: $S/after/clone
  exit 0 -> ALLOWED: (no output)
```

Success Criterion 1: `git pull` BLOCKED and `git merge-base --is-ancestor HEAD main` ALLOWED with an In Progress row. Success Criterion 2: the merge is BLOCKED with the D4 message while the row is uncommitted, and ALLOWED after the commit.

**DELTA**: The gate now refuses a `git pull` and a merge whose verify row is not committed on the merged branch, while it lets a read-only `git merge-base` through and counts a `timeout`-wrapped test run.

**WITNESS**: [who ran it and when — derived from `memory/event-trace/Txxx.jsonl`, never the
implementing agent alone]
