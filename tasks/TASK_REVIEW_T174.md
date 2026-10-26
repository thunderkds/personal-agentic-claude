# TASK_REVIEW — T174: Update can overwrite or keep all edited files in one choice, and logs every decision

> Sibling of `tasks/TASK_GUIDE_T174.md`. Everything here is **filled by the reviewer at Stage
> 4/5** — it is deliberately NOT in the guide, because the implementing agent re-reads the guide on
> every turn and never fills these two sections.
>
> Consumers resolve each section **guide first, this file second** (`.claude/hooks/lib/guide_sections.py`):
> a legacy guide that still carries these sections inline keeps working unchanged, and a stray
> review file can never override an inline section.

---

## Evidence

| Check | Result | Notes / output snippet |
|-------|--------|------------------------|
| **New test(s) cover Acceptance Criteria (file paths pasted)** | ☑ pass / ☐ fail | `tests/test_update_auto_approve.sh` (new, wired in `.github/workflows/ci.yml`): SC1–SC10, AC9, OLD (pre-T137 lock), EOF at the list, M1 mutation. RED on base `af8f1d2` (commit `75dcfa7`): `35 passed, 49 failed`. GREEN at `192a5a0`: `PASS: M1: dropping the backup call is caught by SC1's backup assertion` / `84 passed, 0 failed` |
| Verification command run | ☑ pass / ☐ fail | Full guide command at `192a5a0`, exit 0 (2026-10-26T04:35Z). Tails: `84 passed, 0 failed` (auto-approve) · `----- summary: 38 passed, 0 failed -----` (update) · `----- summary: 52 passed, 0 failed -----` (update_claude_md) · `17 passed, 0 failed` (install_backups) · `----- summary: 22 passed, 0 failed -----` (one_command_menu) · `9 passed, 0 failed` (smoke) · `1447 passed, 25 subtests passed in 68.72s (0:01:08)` · `validate.sh: PASS` · `smoke-install.sh: PASS` · shellcheck: no output, exit 0 |
| Negative cases hold | ☑ pass / ☐ fail | SC4 choice 4 and EOF at the list: tree snapshot identical, no log, exit 0. SC8 forced backup failure (fake `mv`): `PASS: SC8: agents/qa.md kept (never overwritten without a backup)`, logged `kept (backup failed: …)`, exit 2. SC9 log path is a directory / a symlink: `[warn]`, nothing written through the link, outcome and exit as SC1. AC8: log holds no file contents (markers absent). AC9: `UPDATE_MODE=overwrite_all` in the env with no terminal overwrites nothing (exit 2); `EASYKIT_ACTION` is the only `EASYKIT_` variable in setup.sh/update.sh/lib |
| verify | ☐ pass / ☐ fail / ☐ N/A | [what was observed — must literally state "pass" or "fail" here too, e.g. "skill run, feature confirmed working — pass": the merge gate scans this Notes column for the word "pass", not just the Result column] |
| Review scope bounded to the change's blast radius (affected set, not whole repo) | ☑ pass / ☐ fail | Implementer self-review only (no Skill tool in this headless run; Stage 4 `code-review` / `security-review` still owed): `setup.sh` `confirm_plan` + new `choose_update_mode`; `lib/harness-update.sh` `prompt_conflict`, `process_one_file`, `carry_over_unprocessed`, `plan_update` copy, new `update_decided_by` / `render_update_log_entry` / `write_update_log`, `run_update`. Install / Reinstall paths not changed (`run_reinstall` never calls `process_one_file`); covered by the existing suites in the Verification Command |
| Full smoke suite still green (no regression) | ☑ pass / ☐ fail | `smoke-install.sh: PASS`, `test_install_update_smoke` `9 passed, 0 failed`; also run outside the command: test_update_removals 30/0, test_cli_and_project_menus 24/0, test_setup 21/0, test_settings_merge 46/0, test_t098_harness_presence 20/0, test_manifest_exclusions 8/0, test_harness_projection 41/0, `test_shellcheck_clean: PASS — exit 0, no output` |
| **UI: Visual regression (diff or verdict pasted)** | ☐ pass / ☐ fail / ☐ N/A | [screenshot path or LLM verdict — required for UI tasks, Hard-Stop Gate 6] |
| **UI: Design-system compliance (tokens/colors/typography verified)** | ☐ pass / ☐ fail / ☐ N/A | [method used + output] |
| **UI: Responsiveness at target viewports** | ☐ pass / ☐ fail / ☐ N/A | [viewports tested, any overflow findings] |

---

## Demonstration

> Anchors what this task delivered to an observable before/after pair. BEFORE has no `N/A` path:
> if the task changes executable code, BEFORE is a pasted, timestamped terminal capture taken
> **before any implementation commit exists**; if it does not (docs, templates, skill-instruction
> text), BEFORE is the **verbatim prior content** of what changed — a quoted excerpt, not a command.

**BEFORE**: captured by common-infrastructure on the base `af8f1d2` (no T174 commit yet). Scratch
project under `mktemp -d`, installed from a local `file://` kit fixture, `CLAUDE.md` and
`agents/qa.md` edited, fixture bumped, then Update run in a pty (`script -qec`) with answers
Enter (Update), Enter (Proceed), `s`, `s`. ANSI colours stripped. The plan ends in `Proceed? [Y/n]`,
each edited file gets its own `Resolve:` prompt, and no `.claude/update-log.md` is written:

```
== 2026-10-26T04:07:22Z kit=/home/hungnguyenhuu/workspace/pets/wt-t174 @ af8f1d2 fixture=12d0839


s
s
[info]  Using repo: file:///tmp/tmp.dDARtZfTLu/fixture
[info]  Fetching (shallow clone): file:///tmp/tmp.dDARtZfTLu/fixture

Easy Kit is already installed in /tmp/tmp.dDARtZfTLu/project.
  1) Update (keeps your edits)
  2) Reinstall (backs up your edits)
  3) Cancel
Choose [1]: 
Plan: Update Easy Kit in /tmp/tmp.dDARtZfTLu/project (keeps your edits)
  - Kit files you never edited are refreshed from upstream.
  - Files to add or restore: 0
  - You edited these; you will be asked about each one ([o]verwrite / [s]kip).
    [o]verwrite moves your version to <file>.bak-2b6279f first:
      agents/qa.md
      CLAUDE.md
  - Upstream no longer ships these and you never edited them; they will be removed:
      (none)
  - Upstream no longer ships these, but you edited them; they will be kept:
      (none)
  - Backed up: only a file you choose to [o]verwrite. [s]kip keeps your edit in place.
  - Hooks: Easy Kit entries are merged into .claude/settings.json (your own entries are kept).
Proceed? [Y/n] [warn]  conflict: 'agents/qa.md' has local changes since install
[info]  diff (current vs upstream) for agents/qa.md:
--- ./agents/qa.md	2026-10-26 11:07:22.790129537 +0700
+++ /tmp/harness-fetch.O5jhh8/agents/qa.md	2026-10-26 11:07:22.860529458 +0700
@@ -1,2 +1,2 @@
 agent v1
-my edit
+v2
  Resolve: [o]verwrite / [s]kip / [v]iew diff again: [info]  skipped: agents/qa.md (kept your local version)
[warn]  conflict: 'CLAUDE.md' has local changes since install
[info]  diff (current vs upstream) for CLAUDE.md:
--- ./CLAUDE.md	2026-10-26 11:07:22.790129537 +0700
+++ /tmp/harness-fetch.O5jhh8/CLAUDE.md	2026-10-26 11:07:22.860529458 +0700
@@ -1,3 +1,3 @@
 GREENFIELD RULES
 v1
-my edit
+v2
  Resolve: [o]verwrite / [s]kip / [v]iew diff again: [info]  skipped: CLAUDE.md (kept your local version)
[warn]  .claude/settings.json not found in fetched Easy Kit — hook wiring left unchanged.
[info]  Claude Code: re-pointed .claude/{skills,agents} at the plain-root canon.
[info]  Update complete. Re-recorded ./.claude/harness-lock.json
== exit: 0
== $ ls .claude/update-log.md
ls: cannot access '.claude/update-log.md': No such file or directory
== $ ls *.bak* agents/*.bak*
ls: cannot access '*.bak*': No such file or directory
ls: cannot access 'agents/*.bak*': No such file or directory
```

**AFTER**: same scratch script, kit at `192a5a0` (all T174 commits), answers Enter (Update), `2`
(overwrite all). Plan section and everything after it shown; the menu lines above are unchanged:

```
== 2026-10-26T04:35:24Z kit=/home/hungnguyenhuu/workspace/pets/wt-t174 @ 192a5a0 fixture=e137e54

2
[info]  Using repo: file:///tmp/tmp.6bIuPL7U3x/fixture
[info]  Fetching (shallow clone): file:///tmp/tmp.6bIuPL7U3x/fixture

Easy Kit is already installed in /tmp/tmp.6bIuPL7U3x/project.
  1) Update (keeps your edits)
  2) Reinstall (backs up your edits)
  3) Cancel
Choose [1]: 
Plan: Update Easy Kit in /tmp/tmp.6bIuPL7U3x/project (keeps your edits)
  - Kit files you never edited are refreshed from upstream.
  - Files to add or restore: 0
  - You edited these; next you choose: ask about each one, overwrite all, or keep all.
    Overwriting moves your version to <file>.bak-f2566e5 first:
      agents/qa.md
      CLAUDE.md
  - Upstream no longer ships these and you never edited them; they will be removed:
      (none)
  - Upstream no longer ships these, but you edited them; they will be kept:
      (none)
  - Backed up: only a file you choose to overwrite. Keeping it leaves your edit in place.
  - Hooks: Easy Kit entries are merged into .claude/settings.json (your own entries are kept).
How should Update treat your edited files?
  1) Ask me about each one
  2) Overwrite all of them (each backed up first)
  3) Keep all of them
  4) Cancel
Choice [1]: [warn]  conflict: 'agents/qa.md' has local changes since install
[warn]  Backed up your existing './agents/qa.md' to './agents/qa.md.bak-f2566e5' before installing the kit's copy — compare and merge by hand, then delete the backup.
[info]  overwrote: agents/qa.md
[warn]  conflict: 'CLAUDE.md' has local changes since install
[warn]  Backed up your existing './CLAUDE.md' to './CLAUDE.md.bak-f2566e5' before installing the kit's copy — compare and merge by hand, then delete the backup.
[info]  overwrote: CLAUDE.md
[info]  Recorded this run in ./.claude/update-log.md.
[warn]  .claude/settings.json not found in fetched Easy Kit — hook wiring left unchanged.
[info]  Claude Code: re-pointed .claude/{skills,agents} at the plain-root canon.
[info]  Update complete. Re-recorded ./.claude/harness-lock.json
== exit: 0
== $ ls .claude/update-log.md
.claude/update-log.md
== $ ls *.bak* agents/*.bak*
CLAUDE.md.bak-f2566e5
agents/qa.md.bak-f2566e5
== $ cat .claude/update-log.md
## 2026-10-26 11:35 — Update f2566e5 → e137e54
Decided by: auto-approve (overwrite all)
- agents/qa.md — overwrote (your edits; backup agents/qa.md.bak-f2566e5)
- CLAUDE.md — overwrote (your edits; backup CLAUDE.md.bak-f2566e5)
- 1 kit files you never edited — refreshed
- 0 files added
```

**DELTA**: a user running Update settles all their edited kit files with one choice on the plan screen (ask each, overwrite all with a backup each, keep all, cancel), and every Update run leaves a dated record of what happened to each file in `.claude/update-log.md`.

**WITNESS**: [who ran it and when — derived from `memory/event-trace/Txxx.jsonl`, never the
implementing agent alone]
