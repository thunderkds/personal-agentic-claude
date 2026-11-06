# TASK_REVIEW — T267: Native Windows support, step 6 - merge gate detects PowerShell-spelled git writes

> Sibling of `tasks/TASK_GUIDE_T267.md`. Everything here is **filled by the reviewer at Stage
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
3. <what was decided> — DEBATED: <option> (Advocate 1: <its proposal>; Advocate 2: <its proposal>) ⚠ decided for you — please review
4. <what was decided> — SAFER OPTION: <why> ⚠ decided for you — please review
Paused: <only when a stop that stays paused the task: which one, and why>
Checks: tests `<command>` — <result>; reviews <skill — result>; real run `<command>` — printed `<what it printed>` (auto-checked, not /verify)
Memory: <each entry the memory pass wrote, as `file — entry` | nothing new>
Not done: merge (yours); <auto verify: running (T182) | auto verify: <result> | /verify (yours)>

-->

## Auto decisions

Mode: auto
1. No PowerShell lexer; the gate keeps POSIX shlex for narrowing and gains a syntax-blind detection fallback (`git.exe push`, ``git` push``, `& $g push` do not match today) — DEBATED: fallback only, no lexer (Advocate 1: tokenizer plus conservative raw-text fallback; Advocate 2: tokenize both syntaxes plus a block tripwire; Advocate 3: syntax-blind fallback beside BLOCKED_PATTERNS, no PowerShell parser, unresolved goes to the whole-board check) ⚠ decided for you — please review
2. The fallback is active only on win32 or when the text carries a PowerShell marker, so POSIX behaviour does not change — RULE: `AGENTS.md § Karpathy Engineering Principles` (Surgical Changes)
3. Over-matching is accepted (a quoted "git push" may be gated on Windows) — RULE: .claude/hooks/pre_bash_block_unsafe_merge.py:835 "Seeing more text than bash runs can only make this global."
4. `git branch -D` is not added to this hook; T266 ships its Python twin of the guardrail — RULE: `docs/windows-support-plan.md § Tasks` (T-W5 row)
Checks: pending (T267 in progress)
Memory: pending (written before the run ends)
Not done: merge (yours); auto verify: not started


## Evidence

| Check | Result | Notes / output snippet |
|-------|--------|------------------------|
| **New test(s) cover Acceptance Criteria (file paths pasted)** | ☑ pass | `.claude/hooks/tests/test_windows_merge_gate.py` (179 tests, written in this task): AC 4/8 matrix of 18 spellings × 3 boards × tool Bash/PowerShell, each compared with the plain command's verdict; AC 4 `-EncodedCommand`; AC 5 / AC 8 negatives on win32 for both tools; AC 2 Linux baseline (15 commands, verdicts recorded on `eb76a9af`) and marker / PowerShell-tool activation; AC 3 `pushed_task_ids` is None for every flagged spelling, unreadable input still blocks; AC 8 PowerShell trace record counts; AC 9 Read/Write/Edit/Agent/None ignored, Bash plain push unchanged; edge: 10k and 100k inputs under 1 s; two mutation controls. Run on `290612e2`: `python3 -m pytest .claude/hooks/tests/test_windows_merge_gate.py -q` → `179 passed in 0.26s` — pass |
| Verification command run | ☑ pass | On `48f4f0c3` (review fixes): `python3 -m pytest .claude/hooks/tests/test_windows_merge_gate.py -q` → `234 passed in 0.32s`; `python3 -m pytest .claude/hooks/tests tests -q` → `3655 passed, 25 subtests passed in 188.25s (0:03:08)` — pass |
| Negative cases hold | ☑ pass | Red first: test file committed alone at `58240334` against the unchanged hook → `63 failed, 88 passed in 0.47s` (the 88 are the Linux baseline, AC 5 and AC 9, which must hold before and after). Self-review gaps red before `290612e2`: `16 failed, 163 passed`. Mutation 1, fallback branch removed from `main()`: `git diff --stat` → `.claude/hooks/pre_bash_block_unsafe_merge.py \| 3 +--` → `61 failed, 118 passed`, incl. `test_ac4_…[git.exe push origin main-git push origin main-in_progress-Bash]`. Mutation 2, `if tool_name != "Bash":` restored: `git diff --stat` → `… \| 2 +-` → `41 failed, 138 passed`, incl. `test_ac8_powershell_tool_plain_push_blocks_like_bash`. Both restored with `git checkout`; the same two mutations also run inside the suite (`test_mutation_*`) — pass |
| verify | ☐ pass / ☐ fail / ☐ N/A | [what was observed — must literally state "pass" or "fail" here too, e.g. "skill run, feature confirmed working — pass": the merge gate scans this Notes column for the word "pass", not just the Result column] |
| Review scope bounded to the change's blast radius (affected set, not whole repo) | ☐ pass / ☐ fail | [what was reviewed vs. skipped, and why] |
| Full smoke suite still green (no regression) | ☑ pass | `python3 -m pytest .claude/hooks/tests tests -q` on `48f4f0c3` → `3655 passed, 25 subtests passed in 188.25s (0:03:08)`, 0 failed. `ruff check` on the hook: only the existing `E741` (`for l in block.splitlines()`), identical on `eb76a9af` — pass |
| **Companion score (easy-verifier)** | ☐ pass / ☐ fail / ☐ N/A | [`overall` and `change_risk` as the tool returned them, the scope, the ref, and the absolute path of the verifier report after a literal `report:` label — e.g. "overall 86 (>= 80), change_risk pass, scope changes, ref `main...HEAD`, report: `/home/me/.easy-verifier-reports/kit/score_changes_20261028T0530Z.html`". The gate reads the path that follows `report:` and nothing else, so with no label, or a path that is absent, the row is unscored — write ☑ N/A instead. ☑ N/A with a reason when neither companion tool was run: the merge gate blocks on ☑ fail only, never on an absent or N/A row] |
| **UI: Visual regression (diff or verdict pasted)** | ☑ N/A | No UI: a Python hook and its tests |
| **UI: Design-system compliance (tokens/colors/typography verified)** | ☑ N/A | No UI |
| **UI: Responsiveness at target viewports** | ☑ N/A | No UI |

## Review fixes

Stage 4 review (2026-11-06) found 2 P0, 1 P1, 1 P2 and 1 P3 finding; all were fixed in `48f4f0c3`, tests first. Red run of the new tests against `d44284ae`+pin: `40 failed, 194 passed in 0.56s` (P0-1 failed with `assert (None is not None)`, i.e. the PowerShell call was allowed; P3 failed with `TypeError: cannot use 'list' as a set element`).

- **P0-1 (narrowing):** for tool `PowerShell`, `main()` sets `scoped = None`, skips the T250 session filter and uses `([], [])` for branch targets, so the whole board is checked. Bash tool unchanged. Test: `test_review_p0_1_powershell_call_is_never_narrowed` (the reviewer's `--force-with-lease="x\"; …` repro on a real `feat/t900-x` repo: Bash allows as before, PowerShell blocks naming T901).
- **P0-2 (detection):** for tool `PowerShell` one rule: remove backtick, `^`, `+` and ASCII/Unicode quotes, then flag any `push`/`merge` (not `merge-base`)/`rebase`/`pull`/`alias.` word anywhere, plus the `-EncodedCommand` rule. All 15 reviewer repros are in `POWERSHELL_SPELLINGS`, each compared with the plain command on 3 boards. Known limit kept in the hook comment: verbs built at run time (`-join`, `[char]`).
- **P1-1 (POSIX):** the fallback runs only for tool `PowerShell` or on `win32`; the marker activation is gone. Bash on `win32` reads `strip_heredoc_bodies(command)`. `LINUX_BASELINE` gained the 3 reproduced regressions plus `git.exe push origin main` and ``git` push`` (base `eb76a9af` allows all 5 on Linux/Bash).
- **P2:** `test_review_p2_powershell_mention_of_a_verb_over_blocks_known_decision` records the over-block (`git commit -m "merge gate fix"`, `Select-String merge`, `Push-Location`) for tool PowerShell.
- **P3:** `if not isinstance(tool_name, str) or tool_name not in SHELL_TOOLS:`; test with a list, a dict and an int.
- Mutation controls updated and still red on their mutants (`test_mutation_*`, run in the suite). The 10k/100k timing tests also time the Bash-on-win32 path.
- Not touched, as instructed: `GIT_ALIAS_PATTERN` (pre-existing quadratic case, follow-up task).

---

## Demonstration

> Anchors what this task delivered to an observable before/after pair. BEFORE has no `N/A` path:
> if the task changes executable code, BEFORE is a pasted, timestamped terminal capture taken
> **before any implementation commit exists**; if it does not (docs, templates, skill-instruction
> text), BEFORE is the **verbatim prior content** of what changed — a quoted excerpt, not a command.

**BEFORE**: captured on `eb76a9af` (no implementation commit yet). Fixture project: `PROJECT_KANBAN.md`
with T900 In Progress, no evidence; each event piped to the worktree hook with
`CLAUDE_PROJECT_DIR=<fixture>`. The hook signals a block by a `"decision": "block"` JSON on stdout, exit 0;
no stdout = allow. Command: `python3 <scratchpad>/demo.py .claude/hooks/pre_bash_block_unsafe_merge.py`

```
eb76a9af
captured 2026-11-06T12:36:19+00:00
Bash       'git push origin main'         exit=0 BLOCK  • Tasks still In Progress: T900
Bash       'git.exe push origin main'     exit=0 ALLOW  (no output)
Bash       'git` push'                    exit=0 ALLOW  (no output)
PowerShell 'git push origin main'         exit=0 ALLOW  (no output)
```

Three spellings slip past today: `git.exe push`, ``git` push``, and any command from the PowerShell tool.

**AFTER**: same demo on `48f4f0c3` (after the review fixes), with three PowerShell-tool rows added. On this Linux host the Bash tool gets the base verdicts by design (review P1-1); the Bash-tool-on-`win32` path is covered by the tests, which force `sys.platform`:

```
48f4f0c3
captured 2026-11-06T13:06:50+00:00
Bash       'git push origin main'         exit=0 BLOCK  • Tasks still In Progress: T900
Bash       'git.exe push origin main'     exit=0 ALLOW  (no output)
Bash       'git` push'                    exit=0 ALLOW  (no output)
PowerShell 'git push origin main'         exit=0 BLOCK  • Tasks still In Progress: T900
PowerShell 'git.exe push origin main'     exit=0 BLOCK  • Tasks still In Progress: T900
PowerShell 'git` push'                    exit=0 BLOCK  • Tasks still In Progress: T900
PowerShell 'Start-Process -ArgumentList push -FilePath git' exit=0 BLOCK  • Tasks still In Progress: T900
```

**DELTA**: On native Windows, a push, merge, rebase or pull sent through the PowerShell tool or spelled for PowerShell (`git.exe push`, ``git` push``, `& $g push`, `iex "git push"`) now meets the same merge gate as a plain `git push`, and plain POSIX commands on Linux and macOS get the verdicts they got before.

**WITNESS**: [who ran it and when — derived from `memory/event-trace/Txxx.jsonl`, never the
implementing agent alone]
