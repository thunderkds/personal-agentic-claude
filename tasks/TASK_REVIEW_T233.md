# TASK_REVIEW — T233: Plugin package and MIT LICENSE at the repo root

> Sibling of `tasks/TASK_GUIDE_T233.md`. Everything here is **filled by the reviewer at Stage
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
| **New test(s) cover Acceptance Criteria (file paths pasted)** | ☑ pass | `tests/test_plugin_package.py` (7 tests; red first: `7 failed in 0.14s` before the files existed; `7 passed in 0.79s` after) |
| Verification command run | ☑ pass | `claude plugin validate . --profile directory` -> `✔ Validation passed with warnings` (warnings: ICON_MISSING, README install line, symlinked .claude dirs; no LICENSE_MISSING); `python3 -m pytest tests -q` -> `1563 passed in 132.81s`; `python3 -m pytest .claude/hooks/tests -q` -> `1389 passed, 25 subtests passed in 38.01s`; `sh scripts/smoke-install.sh` -> `smoke-install.sh: PASS` |
| Negative cases hold | ☐ pass / ☐ fail | |
| verify | ☑ fail | auto-run by hook, session b6e3daf4-505b-4691-9594-0e596d9b4215, commit 4c701cfc15297e18364b25431a1603d72cb97dae, log .claude/verify-runs/T233-4c701cfc1529.log — fail |
| Review scope bounded to the change's blast radius (affected set, not whole repo) | ☑ pass | code-review inline on `main...HEAD`: P0 0, P1 0, P2 0, P3 0. Supervisor reran `claude plugin validate . --profile directory`: `Validation passed with warnings`. lane: `C1, 5 files, 234 lines, FITS`; `LICENSE` unpredicted by the checker though the guide names it. Risk Low, so no security-review. Startup-reads line complete. |
| Full smoke suite still green (no regression) | ☑ pass | Supervisor rerun: `pytest tests` 1563 passed; `.claude/hooks/tests` 1389 passed, 25 subtests passed; `smoke-install.sh: PASS`. |
| **Companion score (easy-verifier)** | ☐ N/A | Optional tool, not run for this task. |
| **UI: Visual regression (diff or verdict pasted)** | ☐ N/A | No UI in this task. |
| **UI: Design-system compliance (tokens/colors/typography verified)** | ☐ N/A | No UI in this task. |
| **UI: Responsiveness at target viewports** | ☐ N/A | No UI in this task. |

---

## Demonstration

> Anchors what this task delivered to an observable before/after pair. BEFORE has no `N/A` path:
> if the task changes executable code, BEFORE is a pasted, timestamped terminal capture taken
> **before any implementation commit exists**; if it does not (docs, templates, skill-instruction
> text), BEFORE is the **verbatim prior content** of what changed — a quoted excerpt, not a command.

**BEFORE** (captured 2026-11-02T07:37:17Z, `/home/hungnguyenhuu/workspace/pets/wt-t233`, unchanged code, no implementation commit):

```
$ claude plugin validate .
Validating components in: /home/hungnguyenhuu/workspace/pets/wt-t233

Validating skill: .../wt-t233/.claude/skills
⚠ Found 1 warning:
  ❯ directory: This directory is a symlink and nothing in it was read — component directories are read without following symlinks. ...

Validating agent: .../wt-t233/.claude/agents
⚠ Found 1 warning:
  ❯ directory: This directory is a symlink and nothing in it was read — ...

Plugin directory checks for /home/hungnguyenhuu/workspace/pets/wt-t233. ...

✘ Found 1 problem the plugin directory refuses a submission for:
  ❯ LICENSE: License missing (LICENSE_MISSING). This plugin has no LICENSE file and plugin.json has no `license`. The directory requires one of them.

$ ls LICENSE .claude-plugin hooks
ls: cannot access 'LICENSE': No such file or directory
ls: cannot access '.claude-plugin': No such file or directory
ls: cannot access 'hooks': No such file or directory
```

**AFTER** (2026-11-02, same worktree, files added):

```
$ ls LICENSE .claude-plugin hooks
LICENSE
.claude-plugin:
marketplace.json  plugin.json
hooks:
hooks.json

$ claude plugin validate . --profile directory
... ⚠ ICON_MISSING, README install-line advice (T236) ...
✔ Validation passed with warnings        (no LICENSE_MISSING)

$ (temp git project with PROJECT_KANBAN.md, T900 In Progress) claude -p "Run this exact bash command: <git push origin main>" --plugin-dir <worktree> --model haiku --max-budget-usd 0.5   [2026-11-02T07:38:16Z]
The push was blocked, and I haven't pushed anything.
A pre-push hook rejected the push because task T900 is still In Progress. ...
```

**DELTA**: A user can load the repo as the `easy-kit` plugin or add it as a marketplace, and its guard hooks fire from the plugin.

**WITNESS**: [reviewer fills from `memory/event-trace/T233.jsonl`]
