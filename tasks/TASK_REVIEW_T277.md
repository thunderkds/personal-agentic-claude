# TASK_REVIEW — T[NNN]: [Short Title]

> Sibling of `tasks/TASK_GUIDE_T[NNN].md`. Everything here is **filled by the reviewer at Stage
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

## Evidence

| Check | Result | Notes / output snippet |
|-------|--------|------------------------|
| **New test(s) cover Acceptance Criteria (file paths pasted)** | ☐ pass / ☐ fail | [test file path(s) — required before Done] |
| Verification command run | ☐ pass / ☐ fail | [paste actual output] |
| Negative cases hold | ☐ pass / ☐ fail | [paste the red run against the prior content, or the mutation diff (`git diff --stat`, non-empty) before each verdict] |
| verify | ☐ pass / ☐ fail / ☐ N/A | [what was observed — must literally state "pass" or "fail" here too, e.g. "skill run, feature confirmed working — pass": the merge gate scans this Notes column for the word "pass", not just the Result column] |
| Review scope bounded to the change's blast radius (affected set, not whole repo) | ☐ pass / ☐ fail | [what was reviewed vs. skipped, and why] |
| Full smoke suite still green (no regression) | ☐ pass / ☐ fail | |
| **Companion score (easy-verifier)** | ☐ pass / ☐ fail / ☐ N/A | [`overall` and `change_risk` as the tool returned them, the scope, the ref, and the absolute path of the verifier report after a literal `report:` label — e.g. "overall 86 (>= 80), change_risk pass, scope changes, ref `main...HEAD`, report: `/home/me/.easy-verifier-reports/kit/score_changes_20261028T0530Z.html`". The gate reads the path that follows `report:` and nothing else, so with no label, or a path that is absent, the row is unscored — write ☑ N/A instead. ☑ N/A with a reason when neither companion tool was run: the merge gate blocks on ☑ fail only, never on an absent or N/A row] |
| **UI: Visual regression (diff or verdict pasted)** | ☐ pass / ☐ fail / ☐ N/A | [screenshot path or LLM verdict — required for UI tasks, Hard-Stop Gate 6] |
| **UI: Design-system compliance (tokens/colors/typography verified)** | ☐ pass / ☐ fail / ☐ N/A | [method used + output] |
| **UI: Responsiveness at target viewports** | ☐ pass / ☐ fail / ☐ N/A | [viewports tested, any overflow findings] |

---

## Demonstration

> Anchors what this task delivered to an observable before/after pair. BEFORE has no `N/A` path:
> if the task changes executable code, BEFORE is a pasted, timestamped terminal capture taken
> **before any implementation commit exists**; if it does not (docs, templates, skill-instruction
> text), BEFORE is the **verbatim prior content** of what changed — a quoted excerpt, not a command.

**BEFORE**: captured 2026-11-07T06:29:05Z on Linux, before any T277 implementation commit (HEAD `c38d10f1`). The existing `.sh` hook, fed `{"tool_input":{"command":...}}` as in SKILL.md step 5 (`jq -n --arg c ... | bash skills/git-guardrails-claude-code/scripts/block-dangerous-git.sh`); the `.py` twin does not exist:

```
cmd: git push origin main     -> BLOCKED: 'git push origin main' matches dangerous pattern 'git push'. The user has prevented you from doing this.   exit=2
cmd: git reset --hard HEAD~1  -> BLOCKED: ... matches dangerous pattern 'git reset --hard'. ...   exit=2
cmd: git clean -fd            -> BLOCKED: ... matches dangerous pattern 'git clean -fd'. ...   exit=2
cmd: git branch -D old        -> BLOCKED: ... matches dangerous pattern 'git branch -D'. ...   exit=2
cmd: git checkout .           -> BLOCKED: ... matches dangerous pattern 'git checkout \.'. ...   exit=2
cmd: git status               -> (no output) exit=0
cmd: git log --oneline        -> (no output) exit=0
cmd: git commit -m x          -> (no output) exit=0
cmd: echo "git push"          -> BLOCKED: 'echo "git push"' matches dangerous pattern 'git push'. ...   exit=2   (quoted text is blocked too)
python3 skills/git-guardrails-claude-code/scripts/block-dangerous-git.py
  -> python3: can't open file '.../scripts/block-dangerous-git.py': [Errno 2] No such file or directory   exit=2
```
(`scripts/` held only `block-dangerous-git.sh`. All nine lines carried timestamp 2026-11-07T06:29:05Z.)

**AFTER**: 2026-11-07T06:47:10Z, Linux, same nine commands piped into `python3 skills/git-guardrails-claude-code/scripts/block-dangerous-git.py`: the same exit codes (`git push origin main`, `git reset --hard HEAD~1`, `git clean -fd`, `git branch -D old`, `git checkout .`, `echo "git push"` -> exit 2 with `BLOCKED: '<cmd>' matches dangerous pattern '<pattern>'. The user has prevented you from doing this.`; `git status`, `git log --oneline`, `git commit -m x` -> exit 0, silent) and the same stderr text as the `.sh`. Empty stdin, `not json` and `{}` -> exit 0. The Windows job `Repo gate (Git Bash)` is in `.github/workflows/windows.yml`; its result exists only on the PR.

**DELTA**: A Windows user without bash or jq can install the git-guardrails hook as `py -3 block-dangerous-git.py` and get the same blocks, and the Windows CI now reports the repo gate `scripts/validate.sh` as its own job.

**WITNESS**: [who ran it and when — derived from `memory/event-trace/Txxx.jsonl`, never the
implementing agent alone]
