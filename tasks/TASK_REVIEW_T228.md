# TASK_REVIEW — T228: dotfiles skill keeps agent config in one source

> Sibling of `tasks/TASK_GUIDE_T228.md`. Everything here is **filled by the reviewer at Stage
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
| **New test(s) cover Acceptance Criteria (file paths pasted)** | ☑ pass / ☐ fail | `tests/test_dotfiles.py` (written first, 36 red before the script): `python3 -m pytest tests/test_dotfiles.py -q` part of `188 passed in 1.84s` below. Temp HOME only |
| Verification command run | ☑ pass / ☐ fail | `python3 -m pytest tests/test_dotfiles.py tests/test_site_content.py tests/test_readme_slim.py -q` → `188 passed in 1.84s`. `plan --source /nonexistent` under a temp HOME → prints `source not found: /nonexistent` and the expected layout, exit=0 |
| Negative cases hold | ☑ pass / ☐ fail | Tests: invalid or wrong-type target settings refused and next folder goes on; invalid source refused with no write; real file, empty `CLAUDE.md`, dangling link, link elsewhere, `skills` link and symlinked `settings.json` are conflicts left unchanged; `.credentials.json` content never opened or printed; rename failure leaves the old file. Mutation: adding `allow` to `RULE_KEYS` → `1 failed, 43 passed` |
| verify | ☐ pass / ☐ fail / ☐ N/A | [what was observed — must literally state "pass" or "fail" here too, e.g. "skill run, feature confirmed working — pass": the merge gate scans this Notes column for the word "pass", not just the Result column] |
| Review scope bounded to the change's blast radius (affected set, not whole repo) | ☐ pass / ☐ fail | [what was reviewed vs. skipped, and why] |
| Full smoke suite still green (no regression) | ☐ pass / ☑ fail | `python3 -m pytest tests/ .claude/hooks/tests/ -q` → `1 failed, 2694 passed, 25 subtests passed in 140.25s`. The one failure, `test_find_kanban_section_on_real_current_board`, also fails at base `ff45291b`: `PROJECT_KANBAN.md` holds T228 under both Todo (line 11) and In Progress (line 89). Not caused by this code; the board is outside this task. `bash scripts/validate.sh` → `validate.sh: PASS` |
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

**BEFORE**: captured 2026-11-01T10:43:07Z at `ff45291b`, before any implementation commit:

```
$ python3 skills/dotfiles/scripts/dotfiles.py plan --source /nonexistent
python3: can't open file '/home/hungnguyenhuu/workspace/pets/wt-t228/skills/dotfiles/scripts/dotfiles.py': [Errno 2] No such file or directory
exit=2
```

**AFTER**: run under a temp HOME, 2026-11-01T10:50:16Z:

```
$ python3 skills/dotfiles/scripts/dotfiles.py plan --source /nonexistent
source not found: /nonexistent
expected source layout (each part is optional):
  settings.base.json   permissions.deny and permissions.ask are added to Claude folders
  AGENTS.md            linked as CLAUDE.md (Claude folders) and AGENTS.md (Codex folders)
  skills/<name>/       linked as skills/<name> in each folder
no target folder chosen, nothing changed. Found:
  <tmp>/home/.claude-a
  <tmp>/home/.codex
choose with --claude-dir <dir> or --codex-dir <dir>
exit=0
```

Full cycle on temp folders (source has 1 deny, 1 allow, `env`):

```
2026-11-01T10:52:51Z
$ plan
ignored in settings.base.json: permissions.allow, env
<tmp>/home/.claude-a (claude)
  + permissions.deny: Read(./.env)
  + link CLAUDE.md -> <tmp>/src/AGENTS.md
  + link skills/demo -> <tmp>/src/skills/demo
<tmp>/home/.codex (codex)
  + link AGENTS.md -> <tmp>/src/AGENTS.md
  + link skills/demo -> <tmp>/src/skills/demo
exit=0
$ status
ignored in settings.base.json: permissions.allow, env
<tmp>/home/.claude-a (claude)
  + permissions.deny: Read(./.env)
  + link CLAUDE.md -> <tmp>/src/AGENTS.md
  + link skills/demo -> <tmp>/src/skills/demo
  drift
<tmp>/home/.codex (codex)
  + link AGENTS.md -> <tmp>/src/AGENTS.md
  + link skills/demo -> <tmp>/src/skills/demo
  drift
exit=1
$ apply
ignored in settings.base.json: permissions.allow, env
<tmp>/home/.claude-a (claude)
  + permissions.deny: Read(./.env)
  + link CLAUDE.md -> <tmp>/src/AGENTS.md
  + link skills/demo -> <tmp>/src/skills/demo
  backup <tmp>/home/.claude-a/settings.json.bak-20261101T105251Z
  wrote <tmp>/home/.claude-a/settings.json
<tmp>/home/.codex (codex)
  + link AGENTS.md -> <tmp>/src/AGENTS.md
  + link skills/demo -> <tmp>/src/skills/demo
exit=0
$ apply
ignored in settings.base.json: permissions.allow, env
<tmp>/home/.claude-a (claude)
  no change
<tmp>/home/.codex (codex)
  no change
exit=0
$ status
ignored in settings.base.json: permissions.allow, env
<tmp>/home/.claude-a (claude)
  in sync
<tmp>/home/.codex (codex)
  in sync
exit=0
lrwxrwxrwx <tmp>/src/AGENTS.md
-rw------- settings.json
-rw------- settings.json.bak-20261101T105251Z
drwxrwxr-x skills
{
  "model": "opus",
  "permissions": {
    "deny": [
      "Read(./.env)"
    ]
  }
}
```

**DELTA**: A user can keep shared agent config in one folder of their own repo, see what would change in each chosen CLI folder, apply it on request, and check drift, with add-only changes.

**WITNESS**: [who ran it and when — derived from `memory/event-trace/Txxx.jsonl`, never the
implementing agent alone]
