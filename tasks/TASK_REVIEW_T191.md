# TASK_REVIEW — T191: `score` skill — one scoring session writes the Companion score row

> Sibling of `tasks/TASK_GUIDE_T191.md`. Everything here is **filled by the reviewer at Stage
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
| **New test(s) cover Acceptance Criteria (file paths pasted)** | ☑ pass | `tests/test_companion_scoring_skills.py` (21 tests, AC 1-13 plus guide edge cases; AC 14 is the file itself). Run 2026-10-29T10:11:56Z in `wt-t191`: `21 passed in 0.28s`. After Stage 4 F1 (22 tests, +`test_f1_payload_is_data_never_instructions`): `python3 -m pytest tests/test_companion_scoring_skills.py tests/test_site_content.py -q` -> `114 passed in 0.47s`; with the F1 sentence's key phrase removed the new test is RED (`1 failed, 21 passed`), restored it is green; SKILL.md 7513 bytes. Mutation proof: deleting each of 7 load-bearing phrases (`waits forever`, `never averaged`, `not a failing rule`, `0.5 × confidence`, `unbacked pass`, `stays abstained`, `report: <absolute path>`) turned exactly 1 test red each time; the 8193-byte cap check is asserted to reject 8193 and accept 8192 bytes |
| Verification command run | ☑ pass | `python3 -m pytest tests/test_companion_scoring_skills.py -q && sh scripts/validate.sh` -> `21 passed in 0.28s` then `validate.sh: PASS`. SKILL.md is 7298 bytes (cap 8192) |
| Negative cases hold | ☑ pass | AC 10 (unanswerable gate stays abstained; `0.5 × confidence` consequence), AC 13 (unbacked pass rewritten as N/A), AC 6 (chore abstention is not `fail`): each sentence pinned by a test that goes red when the sentence is removed (see the first row) |
| verify | ☑ pass | /verify (user) 2026-10-29: pass. Rung 1 driven live: headless `claude -p` (sonnet, $0.37) with only the easy-verifier MCP (`http://127.0.0.1:8766/mcp`, the running container), told to follow skills/score/SKILL.md on a throwaway clone. It handed over the code-review finding (after 3 rejections fixed by the messages: numeric confidence, ref format, ref not in pack), answered `change_kind` with branch/commit/file signals, left `solution-fit` abstained (no kit-held evidence), left `picks` unanswered, called `write_report` (file exists, outside the repo) and wrote `☑ fail` — overall 50 < 80 from 4 of 13 dimensions, change_risk abstained, all abstentions listed, `report:` path last. The merge gate's `failed_companion_rows` reads that row as failed. This row in THIS branch is left for the user. |
| Review scope bounded to the change's blast radius (affected set, not whole repo) | ☑ pass | Supervisor Stage 4 2026-10-29: code-review over `main...HEAD` (skills/score/SKILL.md, tests/test_companion_scoring_skills.py, site/index.html chip + two counts, tests/test_site_content.py stage-4 set) plus the gate reader it targets (`cited_report_path` in `pre_bash_block_unsafe_merge.py`: the example row parses). lane_check: `C2, 4 files, 284 lines, FITS; unpredicted: site/index.html, tests/test_site_content.py` (roster/count tests force both). Findings: F1 P2 security — verifier payload not marked as data → fixed 83b658d (sentence + RED/GREEN test). Accepted deviation from AC 9: the engine accepts only refs listed for that dimension (`gate.py:_evaluation_problems`), so kit-held evidence (code-review finding, guide AC, easy-ui report) backs a listed ref and is named in `rationale`. P3 not fixed: the skill and the verifier MCP tool are both named `score`. security-review (Risk Medium): prompt-only skill; never installs/runs the container, warns that `127.0.0.1:8766` is unauthenticated, never copies a raw secret, stdin closed on every CLI call. Full suite after fix: `2134 passed, 25 subtests passed`. |
| Full smoke suite still green (no regression) | ☑ pass | `python3 -m pytest tests .claude/hooks/tests -q` -> `2133 passed, 25 subtests passed in 120.85s`; `sh tests/test_harness_projection.sh` 41 passed, `test_manifest_exclusions.sh` 8 passed, `test_harness_fetch.sh` 9 passed |
| **Companion score (easy-verifier)** | ☐ pass / ☐ fail / ☐ N/A | [`overall` and `change_risk` as the tool returned them, the scope, the ref, and the absolute path of the verifier report after a literal `report:` label — e.g. "overall 86 (>= 80), change_risk pass, scope changes, ref `main...HEAD`, report: `/home/me/.easy-verifier-reports/kit/score_changes_20261028T0530Z.html`". The gate reads the path that follows `report:` and nothing else, so with no label, or a path that is absent, the row is unscored — write ☑ N/A instead. ☑ N/A with a reason when neither companion tool was run: the merge gate blocks on ☑ fail only, never on an absent or N/A row] |
| **UI: Visual regression (diff or verdict pasted)** | ☑ N/A | N/A justified: copy-only change to site/index.html (one roster chip reusing the existing `.chip` markup, two counts 32→33), covered by the roster and count tests in tests/test_site_content.py; no new styles or layout |
| **UI: Design-system compliance (tokens/colors/typography verified)** | ☑ N/A | N/A justified: copy-only change to site/index.html (one roster chip reusing the existing `.chip` markup, two counts 32→33), covered by the roster and count tests in tests/test_site_content.py; no new styles or layout |
| **UI: Responsiveness at target viewports** | ☑ N/A | N/A justified: copy-only change to site/index.html (one roster chip reusing the existing `.chip` markup, two counts 32→33), covered by the roster and count tests in tests/test_site_content.py; no new styles or layout |

---

## Demonstration

> Anchors what this task delivered to an observable before/after pair. BEFORE has no `N/A` path:
> if the task changes executable code, BEFORE is a pasted, timestamped terminal capture taken
> **before any implementation commit exists**; if it does not (docs, templates, skill-instruction
> text), BEFORE is the **verbatim prior content** of what changed — a quoted excerpt, not a command.

**BEFORE**: The skill is new text, so BEFORE is the prior content: nothing exists. Captured 2026-10-29T10:04:59Z in `/home/hungnguyenhuu/workspace/pets/wt-t191` (branch `feat/t191-score-skill`), before any implementation commit:

```
$ ls skills/score/SKILL.md
ls: cannot access 'skills/score/SKILL.md': No such file or directory
$ ls skills | grep -c "^score$"
0
$ python3 -m pytest tests/test_companion_scoring_skills.py -q
ERROR: file or directory not found: tests/test_companion_scoring_skills.py
no tests ran in 0.00s
$ python3 -c "import easy_verifier"
ModuleNotFoundError: No module named 'easy_verifier'
```

**AFTER**: same commands, 2026-10-29T10:11:56Z, after commit `1e62153` plus the follow-up commit:

```
$ python3 -m pytest tests/test_companion_scoring_skills.py -q && sh scripts/validate.sh | tail -1
.....................                                                    [100%]
21 passed in 0.28s
validate.sh: PASS
$ wc -c skills/score/SKILL.md
7298 skills/score/SKILL.md
```

Real CLI session (rung 2) with the reference package on `PYTHONPATH` (the package is not installed on this machine), scratch repo, `--scope changes --ref main...HEAD < /dev/null`:

- Bugfix branch with no test: `overall` 100 from 2 of 13 dimensions (12 abstentions), `change_risk` rating 0, kind `bugfix`, `bugfix_without_regression_test` `passed: false`. The skill's rule gives `☑ fail`, although `overall` is high.
- Docs-only branch: `change_risk` is `rating_abstention` (kind `chore`, `all_metrics_abstained`), and `overall` itself is an abstention (`no_dimension_rated`). The skill's rule gives `☑ N/A` with that reason, not `fail`. This was found in the run and added to the skill (a tool-fact the guide did not carry).
- `write-report ... --findings <[]> < /dev/null` returned an absolute `path` and the file exists (under `EASY_VERIFIER_REPORTS_DIR`).
- Rung 3: with no `PYTHONPATH`, `python -c "import easy_verifier" < /dev/null` -> `ModuleNotFoundError: No module named 'easy_verifier'`, so the row is `☑ N/A` naming the missing tool and the rung reached.
- Rung 1 (registered MCP, the asking round) was NOT run live: no verifier MCP tools are registered in this agent session. The round-by-round text comes from the verifier's own docs and `gate.py`, not from a live session.

**DELTA**: A reviewer can run `Skill({ skill: "score" })` at Stage 4 and get one scoring session that ends in a filled Companion score row (or an N/A row that names the missing tool), instead of writing that row by hand.

**WITNESS**: [who ran it and when — derived from `memory/event-trace/Txxx.jsonl`, never the
implementing agent alone]
