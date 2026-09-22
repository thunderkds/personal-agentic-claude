# TASK_REVIEW — T114: One command — it detects the project, shows a menu, and asks before acting

> Sibling of `tasks/TASK_GUIDE_T114.md`. Filled by the reviewer at Stage 4/5.

---

## Evidence

| Check | Result | Notes / output snippet |
|-------|--------|------------------------|
| **New test(s) cover Acceptance Criteria (file paths pasted)** | ☑ pass | `tests/test_one_command_menu.sh` (+ `tests/lib/pty.sh`) — `22 passed, 0 failed` at `5dcf42b` (SC1–SC9, Reinstall removal P1 cases, no-TTY wording); 16/17 RED on pre-change code; output pasted below |
| Verification command run | ☑ pass | Supervisor independent re-run 2026-09-22 at `9b3854c`: all 14 suites exit 0 + `shellcheck -x setup.sh update.sh lib/harness-update.sh` clean; implementer re-run at `5dcf42b` pasted below |
| Negative cases hold | ☑ pass | cancel = zero changes, invalid input, no-TTY never reinstalls, M1/M2 RED (below); /verify probes: `9`/`abc` re-prompt, `n` back, Ctrl-C at confirm → porcelain empty |
| verify | ☑ pass | /verify 2026-09-22, real `setup.sh` in a pty against a `file://` upstream: install, cancel, Reinstall `.bak`, dropped-file removal (unedited removed, edited kept + in lock), no-TTY exit 2 with edit kept, `cat setup.sh \| sh`, `update.sh` alone → rc 1. Two wording findings fixed in `5dcf42b` and re-checked live |
| Review scope bounded to the change's blast radius (affected set, not whole repo) | ☑ pass | Supervisor Stage 4 2026-09-22: `main...feat/t114-one-command-menu` (setup.sh, lib/harness-update.sh, update.sh + callers). code-review: P1 1 (Reinstall skipped T113 removals) → fixed `9b3854c`; P3 2. security-review: no finding ≥8/10 |
| Full smoke suite still green (no regression) | ☑ pass | `test_install_update_smoke.sh` 9/0; pytest 6 failures identical on `3612edc` (memory budget ×5, README length), none installer |
| **Docs updated per guide's "Documentation to Update" (new text quoted)** | ☑ pass | D1 site #update-flow, D2–D3 RUNBOOK.md, D4 PROJECT_SPEC.md — quoted under "Docs updated (D1–D4)" |
| HITL: user reviewed menu transcripts (SC1, SC3, SC6) | ☑ pass | User approved the wording 2026-09-22 ("approve"), after the two /verify wording fixes |
| **UI: Visual regression (diff or verdict pasted)** | ☑ N/A | terminal text menu, no visual design surface; wording is reviewed through the HITL row above |
| **UI: Design-system compliance (tokens/colors/typography verified)** | ☑ N/A | no design system applies to plain terminal output |
| **UI: Responsiveness at target viewports** | ☑ N/A | terminal output; no viewports |

---

## Demonstration

**BEFORE** (Supervisor, 2026-09-12, `main` `8115bc9` — to be re-captured by the implementer on the
integration branch tip after T110–T113 merge, before this task's first commit):

```
===== update.sh as a user would run it (from their project) =====
ls: cannot access 'update.sh': No such file or directory
sh: 0: cannot open ./update.sh: No such file

===== re-running setup.sh on an existing, customized project =====
exit=0
local edit SILENTLY OVERWRITTEN
```

**BEFORE (implementer re-capture, 2026-09-22, branch tip `3612edc` = `main` after T110–T113 + T114 guide docs, before any T114 code commit):**

```
BEFORE captured 2026-09-22T06:27:32Z on 3612edc (feat/t114-one-command-menu tip = main + T114 guide docs)
$ SUPERVISOR_REPO=file://$KIT sh $KIT/setup.sh </dev/null   # first install
exit=0
===== update.sh as a user would run it (from their project) =====
$ ls update.sh; sh ./update.sh
ls: cannot access 'update.sh': No such file or directory
sh: 0: cannot open ./update.sh: No such file
exit=2
===== re-running setup.sh on an installed, edited project =====
$ echo "# local edit" >> skills/tdd/SKILL.md; SUPERVISOR_REPO=file://$KIT sh $KIT/setup.sh </dev/null
[info]  Setup complete. Harness copied into /tmp/claude-1000/-home-hungnguyenhuu-workspace-pets-wt-t114/b9cd955c-e534-4d9e-896d-f060fee5cbda/scratchpad/before.AxWu
[info]  CLAUDE source: CLAUDE.md | lock: .claude/harness-lock.json
[info]  Harnesses:claude
exit=0
local edit gone from skills/tdd/SKILL.md
SKILL.md
$ git status --porcelain
?? skills.bak/

===== second re-run, edit again, full output (same project, 2026-09-22) =====
$ echo '# edit2' >> skills/tdd/SKILL.md; SUPERVISOR_REPO=file://$KIT sh $KIT/setup.sh </dev/null
[info]  Non-interactive mode detected. Defaulting to greenfield (CLAUDE.md). Re-run interactively to choose brownfield.
[info]  Non-interactive mode: no packs installed. Re-run with --pack=<name> to add packs.
[info]  Fetching (shallow clone): file:///home/hungnguyenhuu/workspace/pets/wt-t114
[warn]  Backed up your existing './skills' to './skills.bak.1' before installing the kit's copy — compare and merge by hand, then delete the backup.
[info]  Setup complete. ...
exit=0
?? skills.bak.1/
```

> Correction to the guide's BEFORE wording, measured: since T112 the edit is no longer *lost* — but it
> is still overwritten in place **without asking**, with no plan and no choice of action, and the
> backup is the whole `skills/` directory (every skill), not the one edited file. `update.sh` is still
> not runnable from a project (exit 2, "cannot open").

**AFTER** (implementer, 2026-09-22, commit `f2f6a03`; full transcripts from
`EASYKIT_TRANSCRIPTS=<dir> bash tests/test_one_command_menu.sh`, ANSI colour codes and temp paths
normalised). The blank lines at the top of SC1/SC3 are the pty echoing the queued answers — a test
artifact, not installer output.

HITL — SC1 (empty repo, answers `⏎ ⏎ ⏎ ⏎`: Install, project type, packs, Proceed):

```
[info]  Using repo: file://<tmp>/kit
[info]  Fetching (shallow clone): file://<tmp>/kit

Easy Kit is not installed in <tmp>/sc1 yet.
  1) Install
  2) Cancel
Choose [1]: [info]  Is this a greenfield (new) or brownfield (existing/legacy) project?
        1) greenfield — use CLAUDE.md
        2) brownfield — use CLAUDE_LEGACY.md
        Choice [1/2]: [info]  Optional packs extend the core with domain-specific agents and skills.
        Available packs:
          1) mobile   — Flutter, React Native, Swift, Kotlin
          2) data     — Pipelines, notebooks, ETL, dbt
          3) devops   — Terraform, K8s, CI/CD, Docker
          4) ai-agent — LLM apps, RAG, MCP servers, multi-agent
          5) api      — REST/gRPC, OpenAPI, auth flows, SDK design
        Enter numbers separated by spaces, or press Enter to skip: 
Plan: Install Easy Kit into <tmp>/sc1
  - CLI: Claude Code
  - Project type: new project (CLAUDE.md)
  - Copies in: agents, skills, .claude/hooks, templates, docs/claude-md, AGENTS.md, .cursor/rules, CLAUDE.md
  - Existing paths that differ from the kit are moved aside first:
      (none)
  - Hooks: .claude/settings.json is created, or Easy Kit entries are merged into yours.
Proceed? [Y/n] [info]  Installed .claude/settings.json (copy). Restart Claude Code to activate hooks.
[info]  Wrote ./.claude/harness-lock.json (74 file hashes).
[info]  Setup complete. Harness copied into <tmp>/sc1
[info]  CLAUDE source: CLAUDE.md | lock: .claude/harness-lock.json
[info]  Harnesses:claude
```

HITL — SC3 (installed repo, `skills/tdd/SKILL.md` edited, answers `2 ⏎ ⏎ ⏎`: Reinstall, type, packs, Proceed):

```
2



[info]  Using repo: file://<tmp>/kit
[info]  Fetching (shallow clone): file://<tmp>/kit

Easy Kit is already installed in <tmp>/sc3.
  1) Update (keeps your edits)
  2) Reinstall (backs up your edits)
  3) Cancel
Choose [1]: [info]  Is this a greenfield (new) or brownfield (existing/legacy) project?
        1) greenfield — use CLAUDE.md
        2) brownfield — use CLAUDE_LEGACY.md
        Choice [1/2]: [info]  Optional packs extend the core with domain-specific agents and skills.
        Available packs:
          1) mobile   — Flutter, React Native, Swift, Kotlin
          2) data     — Pipelines, notebooks, ETL, dbt
          3) devops   — Terraform, K8s, CI/CD, Docker
          4) ai-agent — LLM apps, RAG, MCP servers, multi-agent
          5) api      — REST/gRPC, OpenAPI, auth flows, SDK design
        Enter numbers separated by spaces, or press Enter to skip: 
Plan: Reinstall Easy Kit in <tmp>/sc3 (backs up your edits)
  - Every kit file is replaced with a fresh copy, and the lock is rewritten.
  - Project type: new project (CLAUDE.md)
  - Your edited files are moved to <file>.bak first:
      skills/tdd/SKILL.md
  - Your own files that the kit does not ship are left alone.
  - Hooks: Easy Kit entries are merged into .claude/settings.json (your own entries are kept).
Proceed? [Y/n] [warn]  Backed up your existing './skills/tdd/SKILL.md' to './skills/tdd/SKILL.md.bak' before installing the kit's copy — compare and merge by hand, then delete the backup.
[info]  Merged Easy Kit hooks into ./.claude/settings.json (your permissions and your own hook entries are kept).
[info]  Harness 'claude': re-pointed .claude/{skills,agents} at the plain-root canon.
[info]  Reinstall complete. Re-recorded ./.claude/harness-lock.json
[info]  Setup complete. Harness copied into <tmp>/sc3
[info]  CLAUDE source: CLAUDE.md | lock: .claude/harness-lock.json
[info]  Harnesses:claude
```

HITL — SC6 (installed repo, same edit, `setsid -w sh setup.sh </dev/null`, exit 2):

```
[info]  Using repo: file://<tmp>/kit
[info]  Fetching (shallow clone): file://<tmp>/kit
[info]  No terminal — updating, keeping your edits (any file you edited is left as it is; re-run in a terminal to resolve).

Plan: Update Easy Kit in <tmp>/sc6 (keeps your edits)
  - Kit files you never edited are refreshed from upstream.
  - Files to add or restore: 0
  - You edited these; with no terminal they are kept as they are:
      skills/tdd/SKILL.md
  - Upstream no longer ships these and you never edited them; they will be removed:
      (none)
  - Upstream no longer ships these, but you edited them; they will be kept:
      (none)
  - Backed up: nothing. Update keeps your edits in place instead.
  - Hooks: Easy Kit entries are merged into .claude/settings.json (your own entries are kept).
[info]  No terminal — proceeding with the plan above.
[warn]  conflict: 'skills/tdd/SKILL.md' has local changes since install
[info]  diff (current vs upstream) for skills/tdd/SKILL.md:
--- ./skills/tdd/SKILL.md	2026-09-22 13:43:11.512714179 +0700
+++ <fetch-tmp>/skills/tdd/SKILL.md	2026-09-22 13:43:11.790941217 +0700
@@ -49,5 +49,3 @@
 
 ### Communication Protocol
 - **Default Notification**: "TDD complete for [Task ID]. N behaviors covered via vertical slices; all green. Refactors applied: [summary]."
-
-MY LOCAL EDIT
  Resolve: [o]verwrite / [s]kip / [v]iew diff again: 
[warn]  no input for 'skills/tdd/SKILL.md' — left your local version untouched; re-run interactively to resolve.
[info]  Merged Easy Kit hooks into ./.claude/settings.json (your permissions and your own hook entries are kept).
[info]  Harness 'claude': re-pointed .claude/{skills,agents} at the plain-root canon.
[info]  Update complete. Re-recorded ./.claude/harness-lock.json
[error] 1 conflict(s) could not be resolved (no interactive input). Re-run setup.sh in a terminal and choose Update to resolve them.
```

**DELTA**: re-running the one command in an installed project now asks — Update / Reinstall /
Cancel, with a plan naming every backup and removal before `Proceed? [Y/n]` — instead of
overwriting in place and moving the whole `skills/` directory aside; `sh update.sh` from a checkout
runs that same Update, and alone it prints the install command (exit 1) instead of "cannot open".

**WITNESS**: implementer (Common-Infrastructure-Agent, Claude Opus 5), 2026-09-22T06:45Z, in the
worktree `wt-t114`. Not yet re-run by the Supervisor or the user.

---

## Implementer evidence (2026-09-22 — for the Stage 4 reviewer to re-run, not a ticked row)

### Verification command, full output

```
Verification run 2026-09-22T06:45:23Z at f2f6a03 (shellcheck version: 0.11.0)
$ bash tests/test_one_command_menu.sh -> exit 0 | ----- summary: 17 passed, 0 failed -----
$ bash tests/test_setup.sh -> exit 0 | ----- summary: 18 passed, 0 failed -----
$ bash tests/test_update.sh -> exit 0 | ----- summary: 31 passed, 0 failed -----
$ bash tests/test_install_update_smoke.sh -> exit 0 | 9 passed, 0 failed
$ bash tests/test_update_claude_md.sh -> exit 0 | ----- summary: 35 passed, 0 failed -----
$ bash tests/test_settings_merge.sh -> exit 0 | --- 40 passed, 0 failed ---
$ bash tests/test_install_backups.sh -> exit 0 | 13 passed, 0 failed
$ bash tests/test_update_removals.sh -> exit 0 | 30 passed, 0 failed
$ bash tests/test_t098_harness_presence.sh -> exit 0 | 20 passed, 0 failed
$ bash tests/test_harness_projection.sh -> exit 0 | test_harness_projection.sh: 41 passed, 0 failed
$ bash tests/test_harness_fetch.sh -> exit 0 | ----- summary: 9 passed, 0 failed -----
$ bash tests/test_pack_choice_parsing.sh -> exit 0 | ----- summary: 15 passed, 0 failed -----
$ bash tests/test_readme_current.sh -> exit 0 | 
$ bash tests/test_shellcheck_clean.sh -> exit 0 | test_shellcheck_clean: PASS — exit 0, no output
$ shellcheck -x setup.sh update.sh lib/harness-update.sh
exit 0
$ sh scripts/smoke-install.sh
exit 0
$ python3 tests/test_ci_wires_shell_suites.py
----- summary: 4 passed, 0 failed -----
```

Every pre-existing suite's pass count equals its count on the pre-change tip `3612edc` (measured in a
detached worktree at that commit before any edit): setup 18, update 31, smoke 9, CLAUDE.md 35,
settings 40, backups 13, removals 30, t098 20, projection 41, fetch 9, pack parsing 15. No assertion
was removed; converted suites now type their answers into a pty instead of stdin.

`python3 -m pytest .claude/hooks/tests/ tests/ -q`: 843 passed, 6 failed — the same 6 fail on
`3612edc` (memory budget ×5, `test_readme_is_at_most_75_lines`); none touch installer code.

### New suite RED on the pre-change code

`tests/test_one_command_menu.sh` + `tests/lib/pty.sh` copied into a worktree at `3612edc`:
**1 passed, 16 failed**. The one pass is the MANIFEST-exclusion Reinstall case (a plain re-install
already honoured `!` paths); M3 below is what proves that case discriminates.

> Honest order note: the implementation was written before this suite, not strictly test-first; the
> RED above was measured afterwards against the untouched pre-change commit.

### Mutation controls (each applied, run, then reverted; revert byte-verified with `cmp`)

M1 — `confirm_plan` returns 0 before reading input → **SC4 (the AC4 test) fails**:

```
== M1 (confirm_plan returns 0 before reading) 2026-09-22T06:41:19Z
FAIL: SC1: default install via the menu (rc=0)
PASS: SC2: 3) Cancel exits 0 with git status empty
FAIL: SC4: plan rejection then cancel (rc=0)
PASS: AC5: '9' and 'abc' each re-prompt; nothing changes
PASS: AC5: invalid input on the install menu re-prompts; 2) Cancel writes nothing
FAIL: SC3: reinstall backup (rc=0 plan-line=27 ask-line=0)
PASS: SC3: exactly one backup made; lock rewritten with the kit's hash
PASS: Reinstall leaves the project's own .claude/hooks/tests untouched; no tests.bak
FAIL: AC3: Update plan contents (rc=2 rm=18 edit=16 ask=0)
PASS: SC5: piped install read its answers from the terminal (brownfield took effect)
PASS: SC6: no terminal -> Update, edit kept, exit 2, no menu, nothing reinstalled
PASS: SC7: no terminal -> installs with the printed defaults, exit 0
PASS: SC8: update.sh shows the same menu and runs Update (Enter, Enter)
PASS: AC9: update.sh with no install exits 1 and writes nothing
PASS: SC9: update.sh with no adjacent setup.sh prints the install command, exit 1
PASS: AC9: update.sh is 8 lines of code (<= 15)
PASS: seam: an unknown EASYKIT_ACTION is rejected before anything runs
----- summary: 13 passed, 4 failed -----
```

M2 — `tty_read` reads stdin instead of `/dev/tty` → **SC5 (the AC7 test) fails**:

```
== M2 (tty_read reads stdin instead of /dev/tty) 2026-09-22T06:42:02Z
PASS: SC1: Enter, Enter installs; menu showed Install/Cancel; plan confirmed
PASS: SC2: 3) Cancel exits 0 with git status empty
PASS: SC4: 'n' at the plan went back to the menu; Cancel left no change
PASS: AC5: '9' and 'abc' each re-prompt; nothing changes
PASS: AC5: invalid input on the install menu re-prompts; 2) Cancel writes nothing
PASS: SC3: edit saved as skills/tdd/SKILL.md.bak, kit version installed, plan named it before Proceed
PASS: SC3: exactly one backup made; lock rewritten with the kit's hash
PASS: Reinstall leaves the project's own .claude/hooks/tests untouched; no tests.bak
PASS: AC3: Update plan names the removal (skills/optimize) and the edited file before Proceed
FAIL: SC5: piped install answers (rc=0)
PASS: SC6: no terminal -> Update, edit kept, exit 2, no menu, nothing reinstalled
PASS: SC7: no terminal -> installs with the printed defaults, exit 0
PASS: SC8: update.sh shows the same menu and runs Update (Enter, Enter)
PASS: AC9: update.sh with no install exits 1 and writes nothing
PASS: SC9: update.sh with no adjacent setup.sh prints the install command, exit 1
PASS: AC9: update.sh is 8 lines of code (<= 15)
PASS: seam: an unknown EASYKIT_ACTION is rejected before anything runs
----- summary: 16 passed, 1 failed -----

```

M3 (extra) — the fresh file list ignores MANIFEST `!` exclusions → the exclusion Reinstall test fails:

```
== M3 (fresh list ignores MANIFEST ! exclusions) 2026-09-22T06:42:30Z
PASS: SC1: Enter, Enter installs; menu showed Install/Cancel; plan confirmed
PASS: SC2: 3) Cancel exits 0 with git status empty
FAIL: SC4: plan rejection then cancel (rc=0)
PASS: AC5: '9' and 'abc' each re-prompt; nothing changes
PASS: AC5: invalid input on the install menu re-prompts; 2) Cancel writes nothing
PASS: SC3: edit saved as skills/tdd/SKILL.md.bak, kit version installed, plan named it before Proceed
PASS: SC3: exactly one backup made; lock rewritten with the kit's hash
FAIL: Reinstall touched an excluded path (rc=0)
PASS: AC3: Update plan names the removal (skills/optimize) and the edited file before Proceed
PASS: SC5: piped install read its answers from the terminal (brownfield took effect)
PASS: SC6: no terminal -> Update, edit kept, exit 2, no menu, nothing reinstalled
PASS: SC7: no terminal -> installs with the printed defaults, exit 0
PASS: SC8: update.sh shows the same menu and runs Update (Enter, Enter)
PASS: AC9: update.sh with no install exits 1 and writes nothing
PASS: SC9: update.sh with no adjacent setup.sh prints the install command, exit 1
PASS: AC9: update.sh is 8 lines of code (<= 15)
PASS: seam: an unknown EASYKIT_ACTION is rejected before anything runs
----- summary: 15 passed, 2 failed -----

```

### Docs updated (D1–D4), new text

- **D1** `site/index.html` — install section lead: "To pull in newer Easy Kit changes later, run the
  same command again from your repo root and choose **Update** (see below)." `#update-flow` opening:
  "There is one command. Run the same install line again from inside your already-installed project
  … Easy Kit sees it is installed and asks what to do:" + the menu, then "Before it changes anything
  it shows a plan — the files it will ask you about, the files it will remove because the kit no
  longer ships them, and anything it will back up — and ends with `Proceed? [Y/n]`. Answer `n` to go
  back to the menu. **Cancel changes nothing.** With no terminal … it prints the safe default —
  Update, keeping every edit — and takes it; Reinstall never runs without a terminal. (An existing
  `update.sh` in a checkout still works: it runs the same Update action.)"
- **D2** `RUNBOOK.md` Deploy step 4: "The installer shows a menu (`1) Install  2) Cancel`), then a plan
  ending `Proceed? [Y/n]`: in a terminal, press Enter at every prompt to accept the defaults (Install,
  new project, no packs, Proceed). To run the check with no terminal instead — it then prints and takes
  the same defaults — prefix the line with `setsid -w` and append `</dev/null`."
- **D3** `RUNBOOK.md` v2.0.0 rollback: "running an update (the one install command, action **Update**)
  does **not** automatically turn those symlinks back …"; "then run the install command from the
  restored `main` inside the repo. If it shows the action menu, choose **Reinstall**; v1's `setup.sh`
  has no menu and reinstalls directly."; "Recovery there is the one install command against the
  restored `main`, run inside the repo in a terminal, choosing **Update** — per-file, with the conflict
  prompt." Failure Modes row: "An update exits 2 with 'conflict(s) could not be resolved' | Ran with no
  terminal over locally-customized files (no terminal = Update, every edit kept) | Re-run the install
  command in a real terminal, choose **Update**, and resolve per file".
- **D4** `PROJECT_SPEC.md` Architecture Summary: "`setup.sh` is the one Easy Kit command (ADR-0002):
  … detects whether Easy Kit is already installed (`.claude/harness-lock.json`), and offers a numbered
  action menu … then a plan screen of what it will copy, back up and remove, and acts only after
  `Proceed? [Y/n]`. Every prompt reads `/dev/tty`; with no terminal it prints and takes the safe
  default (Install, or Update keeping every edit — never Reinstall). … `update.sh` is a thin alias for
  the Update action."

### Not verified here (stated, not claimed)

- macOS / Windows Git Bash `/dev/tty` behaviour: untested (Linux, util-linux 2.39 `script`/`setsid` only).
- CI itself: not run; `ci.yml` step added and the drift guard passes locally.

---

## Stage 4 fix — BEFORE (P1: Reinstall skips the T113 removal contract)

Repro on tip `1b11e7c`, before any code change: install, upstream stops shipping `skills/optimize` (never edited in the project), then Reinstall (menu choice 2). The plan does not mention it, the files survive, and the lock entry is gone — so no later Update can remove it.

```text
$ date -u; git rev-parse --short HEAD
2026-09-22T08:02:27Z
1b11e7c
installed; lock has optimize: 1
upstream dropped skills/optimize (unedited in project)
reinstall rc=0
23:Plan: Reinstall Easy Kit in /tmp/tmp.DmX2ixr2y2/proj (backs up your edits)
24-  - Every kit file is replaced with a fresh copy, and the lock is rewritten.
25-  - Project type: new project (CLAUDE.md)
26-  - Your edited files are moved to <file>.bak first:
27-      (none: no kit file has been edited)
28-  - Your own files that the kit does not ship are left alone.
29-  - Hooks: Easy Kit entries are merged into .claude/settings.json (your own entries are kept).
30-Proceed? [Y/n] [info]  Merged Easy Kit hooks into ./.claude/settings.json (your permissions and your own hook entries are kept).
31-[info]  Harness 'claude': re-pointed .claude/{skills,agents} at the plain-root canon.
after reinstall: skills/optimize on disk: SKILL.md 
after reinstall: lock entries for skills/optimize: 0
```

## Stage 4 fix — AFTER

**Change.** `run_reinstall` now calls `carry_over_unprocessed` (processed list = the reinstall list: the fresh list + CLAUDE.md) before it rewrites the lock, and exits 2 when `DELETION_ABORTED` is set, the same way `run_update` does. `plan_update`'s classification loop and its removal lines were moved into `plan_removals` / `plan_print_removals`, which `plan_reinstall` now calls too (`setup.sh` passes it `$manifest`).

**Test-harness note.** `tests/test_one_command_menu.sh:205` (the AC3 block, which was already there) ran `git revert -q`, which is not a valid flag, so the fixture restore always failed silently and `skills/optimize` stayed missing for every later block. I changed it to `git revert --no-edit HEAD >/dev/null`. The same bug is at line 306 (SC8, the last fixture change in the file); it does no harm there, so I left it alone.

Same repro as BEFORE, on the fix:

```text
2026-09-22T08:08:56Z
installed; lock has optimize: 1
upstream dropped skills/optimize (unedited in project)
reinstall rc=0
23:Plan: Reinstall Easy Kit in /tmp/tmp.tyGhi9sfim/proj (backs up your edits)
24-  - Every kit file is replaced with a fresh copy, and the lock is rewritten.
25-  - Project type: new project (CLAUDE.md)
26-  - Your edited files are moved to <file>.bak first:
27-      (none: no kit file has been edited)
28-  - Upstream no longer ships these and you never edited them; they will be removed:
29-      skills/optimize
30-  - Upstream no longer ships these, but you edited them; they will be kept:
31-      (none)
32-  - Your own files that the kit does not ship are left alone.
33-  - Hooks: Easy Kit entries are merged into .claude/settings.json (your own entries are kept).
34-Proceed? [Y/n] [info]  removed 'skills/optimize' — upstream no longer ships it and you never edited it.
35-[info]  Merged Easy Kit hooks into ./.claude/settings.json (your permissions and your own hook entries are kept).
36-[info]  Harness 'claude': re-pointed .claude/{skills,agents} at the plain-root canon.
37-[info]  Reinstall complete. Re-recorded ./.claude/harness-lock.json
after reinstall: skills/optimize on disk: 
after reinstall: lock entries for skills/optimize: 0
```

RED (the new tests with the pre-fix `lib/harness-update.sh` + `setup.sh` from HEAD):

```text
2026-09-22T08:06:40Z
$ bash tests/test_one_command_menu.sh   # lib/harness-update.sh + setup.sh at HEAD 1b11e7c, new tests applied
PASS: SC1: Enter, Enter installs; menu showed Install/Cancel; plan confirmed
PASS: SC2: 3) Cancel exits 0 with git status empty
PASS: SC4: 'n' at the plan went back to the menu; Cancel left no change
PASS: AC5: '9' and 'abc' each re-prompt; nothing changes
PASS: AC5: invalid input on the install menu re-prompts; 2) Cancel writes nothing
PASS: SC3: edit saved as skills/tdd/SKILL.md.bak, kit version installed, plan named it before Proceed
PASS: SC3: exactly one backup made; lock rewritten with the kit's hash
PASS: Reinstall leaves the project's own .claude/hooks/tests untouched; no tests.bak
PASS: AC3: Update plan names the removal (skills/optimize) and the edited file before Proceed
FAIL: Reinstall: unedited dropped file (rc=0 rm=0 ask=30)
FAIL: Reinstall: edited dropped file (rc=0 keep=0 ask=30)
FAIL: Reinstall: incomplete upstream (rc=0)
PASS: SC5: piped install read its answers from the terminal (brownfield took effect)
PASS: SC6: no terminal -> Update, edit kept, exit 2, no menu, nothing reinstalled
PASS: SC7: no terminal -> installs with the printed defaults, exit 0
PASS: SC8: update.sh shows the same menu and runs Update (Enter, Enter)
PASS: AC9: update.sh with no install exits 1 and writes nothing
PASS: SC9: update.sh with no adjacent setup.sh prints the install command, exit 1
PASS: AC9: update.sh is 8 lines of code (<= 15)
PASS: seam: an unknown EASYKIT_ACTION is rejected before anything runs
----- summary: 17 passed, 3 failed -----
```

Mutation control (only the `carry_over_unprocessed` call removed from `run_reinstall`; the plan still names the files, but the run leaves them in place):

```text
2026-09-22T08:07:02Z
$ bash tests/test_one_command_menu.sh   # MUTANT: carry_over_unprocessed call deleted from run_reinstall
 lib/harness-update.sh | 90 ++++++++++++++++++++++++++++++++++-----------------
 1 file changed, 60 insertions(+), 30 deletions(-)
FAIL: Reinstall: unedited dropped file (rc=0 rm=29 ask=34)
FAIL: Reinstall: edited dropped file (rc=0 keep=31 ask=34)
FAIL: Reinstall: incomplete upstream (rc=0)
----- summary: 17 passed, 3 failed -----
```

Full Verification Command list, on the fix:

```text
2026-09-22T08:07:33Z
$ bash tests/test_one_command_menu.sh -> exit 0 | ----- summary: 20 passed, 0 failed -----
$ bash tests/test_setup.sh -> exit 0 | ----- summary: 18 passed, 0 failed -----
$ bash tests/test_update.sh -> exit 0 | ----- summary: 31 passed, 0 failed -----
$ bash tests/test_install_update_smoke.sh -> exit 0 | 9 passed, 0 failed
$ bash tests/test_update_claude_md.sh -> exit 0 | ----- summary: 35 passed, 0 failed -----
$ bash tests/test_settings_merge.sh -> exit 0 | --- 40 passed, 0 failed ---
$ bash tests/test_install_backups.sh -> exit 0 | 13 passed, 0 failed
$ bash tests/test_update_removals.sh -> exit 0 | 30 passed, 0 failed
$ bash tests/test_t098_harness_presence.sh -> exit 0 | 20 passed, 0 failed
$ bash tests/test_harness_projection.sh -> exit 0 | test_harness_projection.sh: 41 passed, 0 failed
$ bash tests/test_harness_fetch.sh -> exit 0 | ----- summary: 9 passed, 0 failed -----
$ bash tests/test_pack_choice_parsing.sh -> exit 0 | ----- summary: 15 passed, 0 failed -----
$ bash tests/test_readme_current.sh -> exit 0 | 
$ bash tests/test_shellcheck_clean.sh -> exit 0 | 
$ shellcheck -x setup.sh update.sh -> exit 0
```

---

## /verify wording fixes — BEFORE

Live run of `bash tests/test_one_command_menu.sh` at `9b3854c`, with the two new assertions added and no
code changed (2026-09-22T08:38:53Z). Both lines are quoted from the real run output:

```text
FAIL: Reinstall plan: says 'no kit file has been edited' beside an edited file
26:  - Your edited files are moved to <file>.bak first:
27:      (none: no kit file has been edited)
28:  - Upstream no longer ships these and you never edited them; they will be removed:
30:  - Upstream no longer ships these, but you edited them; they will be kept:
FAIL: SC6: no-terminal output prints the Resolve prompt
27:  Resolve: [o]verwrite / [s]kip / [v]iew diff again: 
28:[warn]  no input for 'skills/tdd/SKILL.md' — left your local version untouched; re-run interactively to resolve.
----- summary: 20 passed, 2 failed -----
```

## /verify wording fixes — AFTER

Changes: `plan_reinstall` empty-backup text is now "(none: no file the kit ships now has been edited)";
`prompt_conflict` returns "eof" without printing the Resolve prompt when `TTY_OK` is not 1 (the caller's
"[warn]  no input for …" line and the diff are unchanged). New assertions in `tests/test_one_command_menu.sh`
(RED above, GREEN below). Note: the first GREEN attempt failed only on my own assertion, which looked for
`+MY LOCAL EDIT`; the diff is current→upstream, so the edit reads `-MY LOCAL EDIT` — assertion corrected.

```text
PASS: Reinstall plan: empty-backup wording does not deny the edited file it lists
PASS: SC6: no conflict prompt printed without a terminal; warning and diff kept
```

Full Verification Command list, on the fix:

```text
2026-09-22T08:41:02Z
$ bash tests/test_one_command_menu.sh -> exit 0 | ----- summary: 22 passed, 0 failed -----
$ bash tests/test_setup.sh -> exit 0 | ----- summary: 18 passed, 0 failed -----
$ bash tests/test_update.sh -> exit 0 | ----- summary: 31 passed, 0 failed -----
$ bash tests/test_install_update_smoke.sh -> exit 0 | 9 passed, 0 failed
$ bash tests/test_update_claude_md.sh -> exit 0 | ----- summary: 35 passed, 0 failed -----
$ bash tests/test_settings_merge.sh -> exit 0 | --- 40 passed, 0 failed ---
$ bash tests/test_install_backups.sh -> exit 0 | 13 passed, 0 failed
$ bash tests/test_update_removals.sh -> exit 0 | 30 passed, 0 failed
$ bash tests/test_t098_harness_presence.sh -> exit 0 | 20 passed, 0 failed
$ bash tests/test_harness_projection.sh -> exit 0 | test_harness_projection.sh: 41 passed, 0 failed
$ bash tests/test_harness_fetch.sh -> exit 0 | ----- summary: 9 passed, 0 failed -----
$ bash tests/test_pack_choice_parsing.sh -> exit 0 | ----- summary: 15 passed, 0 failed -----
$ bash tests/test_readme_current.sh -> exit 0 |
$ bash tests/test_shellcheck_clean.sh -> exit 0 |
$ shellcheck -x setup.sh update.sh -> exit 0
```

HITL — SC6 after the fix (installed repo, one edit, `setsid -w sh setup.sh </dev/null`, exit 2):

```text
[info]  Using repo: file:///tmp/one-command-test.6pZgMT/kit
[info]  Fetching (shallow clone): file:///tmp/one-command-test.6pZgMT/kit
[info]  No terminal — updating, keeping your edits (any file you edited is left as it is; re-run in a terminal to resolve).

Plan: Update Easy Kit in /tmp/one-command-test.6pZgMT/sc6 (keeps your edits)
  - Kit files you never edited are refreshed from upstream.
  - Files to add or restore: 0
  - You edited these; with no terminal they are kept as they are:
      skills/tdd/SKILL.md
  - Upstream no longer ships these and you never edited them; they will be removed:
      (none)
  - Upstream no longer ships these, but you edited them; they will be kept:
      (none)
  - Backed up: nothing. Update keeps your edits in place instead.
  - Hooks: Easy Kit entries are merged into .claude/settings.json (your own entries are kept).
[info]  No terminal — proceeding with the plan above.
[warn]  conflict: 'skills/tdd/SKILL.md' has local changes since install
[info]  diff (current vs upstream) for skills/tdd/SKILL.md:
--- ./skills/tdd/SKILL.md	2026-09-22 15:41:23.940727171 +0700
+++ /tmp/harness-fetch.gNLFq4/skills/tdd/SKILL.md	2026-09-22 15:41:24.220953831 +0700
@@ -49,5 +49,3 @@
 
 ### Communication Protocol
 - **Default Notification**: "TDD complete for [Task ID]. N behaviors covered via vertical slices; all green. Refactors applied: [summary]."
-
-MY LOCAL EDIT
[warn]  no input for 'skills/tdd/SKILL.md' — left your local version untouched; re-run interactively to resolve.
[info]  Merged Easy Kit hooks into ./.claude/settings.json (your permissions and your own hook entries are kept).
[info]  Harness 'claude': re-pointed .claude/{skills,agents} at the plain-root canon.
[info]  Update complete. Re-recorded ./.claude/harness-lock.json
[error] 1 conflict(s) could not be resolved (no interactive input). Re-run setup.sh in a terminal and choose Update to resolve them.
```
