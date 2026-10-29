# TASK_REVIEW — T203: Auto verify for every task, started by the Supervisor

> Sibling of `tasks/TASK_GUIDE_T203.md`. Everything here is **filled by the reviewer at Stage
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
| **New test(s) cover Acceptance Criteria (file paths pasted)** | ☑ pass | `tests/test_auto_verify.py` — 32 new `test_t203_*` functions (39 cases): AC 1 `test_t203_ac1_*` (unmarked extended row, unmarked minimal line, no review file = one stderr line); AC 2 `test_t203_ac2_*` (`--start` returns at once with the log path, twice = one run + `already started`, Stop hook and `--start` share one lock both orders, not at Ready for Review, user-filled row, new commit = new run, no `claude` = blocked, no review file = one line); AC 3 `test_t203_ac3_*` (off/OFF/` off ` hook, off `--start`, off minimal, off still runs a marked task both entries); AC 4 `test_t203_ac4_*` (user row/line never run over, child guard both entries, unmarked pass does not move to Done, marked pass still closes out); AC 5 `test_t203_ac5_*` (unmarked: hook row + record allows; hand-typed, other commit, fail record, `auto-checked` block); AC 6 `test_t203_ac6_*` (5 doctrine tests); AC 7 `test_t203_ac7_*` (merge-settings adds the Stop entry, keeps user Stop entry, `permissions.allow`, `model`; MANIFEST ships the hook files). Mutation check: against the pre-T203 hook (`git show HEAD:.claude/hooks/stop_auto_verify.py`), `-k t203` → `20 failed, 13 passed, 139 deselected in 195.61s` (the 13 are negatives and AC 7, true before too). `python3 -m pytest -q tests/test_auto_verify.py -p no:cacheprovider -k t203` → `39 passed, 139 deselected in 32.33s` — pass |
| Verification command run | ☑ pass | `python3 -m pytest -q tests .claude/hooks/tests -p no:cacheprovider` at `0eeb35f` (2026-10-29T11:04:06Z) → `2197 passed, 25 subtests passed in 148.74s (0:02:28)` (baseline before T203 at `ae719eb`: `2158 passed, 25 subtests passed in 115.07s`). `sh scripts/validate.sh` → `validate.sh: PASS` (the guide's `./validate.sh` lives at `scripts/validate.sh`) — pass |
| Negative cases hold | ☑ pass | Off switch: unmarked task untouched by hook and `--start` (`CLAUDE_AUTO_VERIFY=off`, also `OFF`, ` off `). Not at Ready for Review / user-filled row / already started / already filled / inside the child run (`CLAUDE_AUTO_VERIFY_RUN=1`) → nothing started, one line. Merge gate for an unmarked task: hand-typed `auto-run by hook` row with no record, record for another commit, fail record edited to pass, `auto-checked, not /verify` → all `block`. D6: an unmarked pass leaves the board byte-identical and writes no `Closed:`/`Paused:` line. The 7 T182/T188 tests that pinned "no marker, no run" now run under `CLAUDE_AUTO_VERIFY=off` and pass — pass |
| verify | ☐ pass / ☐ fail / ☐ N/A | [what was observed — must literally state "pass" or "fail" here too, e.g. "skill run, feature confirmed working — pass": the merge gate scans this Notes column for the word "pass", not just the Result column] |
| Review scope bounded to the change's blast radius (affected set, not whole repo) | ☑ pass | Implementer self-check only (Stage 4 `code-review` + `security-review` still due): changed set = `.claude/hooks/stop_auto_verify.py` (trigger, `--start`, off switch, D6 close-out guard), doctrine (`AGENTS.md`, `docs/claude-md/tracks.md`, `docs/claude-md/pipeline-stages.md`, `PROJECT_SPEC.md`), tests. Unchanged and re-run: `pre_bash_block_unsafe_merge.py` (trust rule, no edit), `lib/verify_record.py`, `lib/auto_mode.py`, `lib/auto_closeout.py`, `lib/merge-settings.py`, `setup.sh` — pass |
| Full smoke suite still green (no regression) | ☑ pass | same run as above: `2197 passed, 25 subtests passed in 148.74s (0:02:28)`; one pin repointed, not weakened: `.claude/hooks/tests/test_agent_guide_dedup.py` `T070_BASELINE_REF` `65fe3a8` → `2616322` (T203's AGENTS.md edit commit, D4) — pass |
| **Companion score (easy-verifier)** | ☑ N/A | neither companion tool was run by the implementer; the Stage 4 reviewer may score it |
| **UI: Visual regression (diff or verdict pasted)** | ☐ N/A | no UI: a Python hook, doctrine Markdown and tests; no page or component changed |
| **UI: Design-system compliance (tokens/colors/typography verified)** | ☐ N/A | no UI: a Python hook, doctrine Markdown and tests; no page or component changed |
| **UI: Responsiveness at target viewports** | ☐ N/A | no UI: a Python hook, doctrine Markdown and tests; no page or component changed |

---

## Demonstration

> Anchors what this task delivered to an observable before/after pair. BEFORE has no `N/A` path:
> if the task changes executable code, BEFORE is a pasted, timestamped terminal capture taken
> **before any implementation commit exists**; if it does not (docs, templates, skill-instruction
> text), BEFORE is the **verbatim prior content** of what changed — a quoted excerpt, not a command.

**BEFORE**: captured on branch `feat/t203-auto-verify-all` at `ae719eb` (T189's code, no T203 change),
by the scratch script `demo.sh <kit-checkout>`: it copies the kit's `.claude/hooks` into a throwaway git
project whose board has one **unmarked** task (`T951`, no `Mode: auto`) at Ready for Review with an
empty `verify` row, puts a stub `claude` first on `PATH` (it only logs its argv; no real run, no money),
then fires the Stop hook and tries `--start T951`:

```
2026-10-29T10:46:54Z
$ grep -c "Mode: auto" tasks/TASK_REVIEW_T951.md
0
$ echo {"hook_event_name":"Stop"} | python3 .claude/hooks/stop_auto_verify.py
exit 0
$ python3 .claude/hooks/stop_auto_verify.py --start T951 </dev/null
exit 0
$ ls .claude/verify-runs
ls: cannot access '.claude/verify-runs': No such file or directory
$ cat claude_calls.txt
cat: /tmp/t203-demo.pLHCdA/claude_calls.txt: No such file or directory
$ grep "^| verify" tasks/TASK_REVIEW_T951.md
| verify | ☐ pass / ☐ fail / ☐ N/A | [what was observed] |
```

An unmarked task at Ready for Review gets no run: the Stop hook is silent, `--start` is not an entry
(it falls through to the Stop hook and does nothing), `claude` is never called, and the `verify` row
stays empty — the merge waits on the user's `/verify`.

**AFTER**: [same command, post-change] OR [verbatim excerpt of the new content]

**DELTA**: [one sentence — what a user can now do that they could not before]

**WITNESS**: [who ran it and when — derived from `memory/event-trace/T203.jsonl`, never the
implementing agent alone]
