# TASK_GUIDE — T114: One command — it detects the project, shows a menu, and asks before acting
**Date**: 2026-09-12
**Complexity Level**: C2 (Hard-Stop Gate 2 floor: installer restructure)
**Risk Level**: Medium
**Priority**: P0
**Type**: HITL — the user reviews the real menu transcript before Done
**Assigned agent**: Common-Infrastructure-Agent
**Agent guide**: `agents/common-infrastructure.md`
**Branch**: worktree off `feat/easy-kit-one-command`; merges back into it

---

## Mandatory Startup (Do Not Skip)

Before writing any code:
1. Read `PROJECT_SPEC.md`
2. Read `memory/MEMORY.md`
3. Read this file completely
4. Read `agents/common-infrastructure.md`
5. Note the **Complexity Level** above and apply the matching process from the Complexity matrix in your role guide
6. Read `memory/codebase-map.md` (C2, multi-file)
7. Read `docs/adr/0002-one-confirmed-menu-driven-installer.md` in full — this task implements its "One command, menus only" section (action menu part)

---

## Requirement (Pillar 1 — Adapt the requirement)

User, 2026-09-12: "it should be one single command, the options should be the choose from user from the
list, not like the way user must remember the param and they push in the initialize" and "one command, but
need the confirm or accept user choose another if needed".

Today (probe, `main` `8115bc9`):
- Update is a second script that is **not installed into projects** and cannot bootstrap from `curl | sh`
  (`update.sh:59-62` exits): `sh ./update.sh` → `cannot open ./update.sh: No such file`.
- Re-running `setup.sh` on an installed, edited project **overwrites the edit silently** (exit 0).
- Prompts read stdin (`prompt_mode` gates on `[ -t 0 ]`, `prompt_conflict` reads fd 0). Under `curl | sh`,
  stdin *is* the script, so no prompt ever reaches the user.

**Restated intent**:
> A user runs the one published command in any project. Easy Kit works out whether it is already installed,
> offers a numbered action list with a safe default, shows exactly what it will do, and acts only after
> the user accepts — or picks another action. With no terminal it takes the safe path and says so.

**Out of scope** (T115 owns these):
- The CLI menu and project-type menu, and removing `--harness`/`--copy`/`--pack=` flags. In this task the
  install action keeps today's `prompt_mode` + flag behaviour, except its prompt input moves to `/dev/tty`.
- README / site / RUNBOOK wording.
- Packs (T116/T117).

**Requirement Refs**: none in `PRD.md`; authority ADR-0002 Decision, menu 1 + plan screen + no-TTY rules.

### Requirement Fidelity Gate (sign off BEFORE implementation)

- [x] Restated intent confirmed (Supervisor; user's own words quoted above)
- [x] Domain terms align with glossary — user-facing text says "Easy Kit" and "CLI", never "harness"
- [x] Every Acceptance Criterion traces to the Requirement
- [x] No `PRD.md` refs claimed

---

## Dependencies & Reachability

**Depends on**: T110, T111, T112, T113 — the update and install paths must already be edit-safe before a
menu offers "Update" and "Reinstall" to users

**Entry point**: `setup.sh` `main` → action menu

---

## Acceptance Criteria

| # | Criterion (testable) | Traces to requirement |
|---|----------------------|-----------------------|
| 1 | No lock present → menu `1) Install  2) Cancel`, default `1` (Enter accepts) | "detects … offers a numbered action list with a safe default" |
| 2 | Lock present → menu `1) Update (keeps your edits)  2) Reinstall (backs up your edits)  3) Cancel`, default `1` | same |
| 3 | Before acting, a plan screen lists: the action, files/dirs that will be backed up (T112 helper), and ends `Proceed? [Y/n]`; `n` returns to the action menu | "shows exactly what it will do … acts only after the user accepts — or picks another action" |
| 4 | Cancel (menu or `n` then Cancel) → exit 0, **zero** filesystem changes (`git status --porcelain` empty) | "acts only after the user accepts" |
| 5 | Invalid menu input (`9`, `abc`) → message + re-prompt, no action | numbered list must be forgiving |
| 6 | Update action runs today's update behaviour (T110/T111/T113 included); Reinstall backs up every file whose hash differs from the lock via the T112 helper, then installs fresh and rewrites the lock | "Update (keeps your edits)", "Reinstall (backs up your edits)" |
| 7 | All prompts — action menu, plan confirm, existing project-type prompt, per-file conflict prompt — read `/dev/tty`, never stdin. Proven by running the command as `cat setup.sh \| sh` inside a pty and answering every prompt | "`curl \| sh` … no prompt reaches the user" |
| 8 | No usable `/dev/tty` (run under `setsid … </dev/null`) → no menu; prints the chosen safe default: Install when no lock, Update when lock (edits kept, unresolved conflicts exit 2). **Reinstall never runs without a TTY.** | ADR-0002 no-TTY rule |
| 9 | `update.sh` is a thin alias (≤ 15 lines of code): run from a checkout, it runs the Update action of the adjacent `setup.sh` with the same menus/plan; run with no adjacent `setup.sh`, it prints the one install command and exits 1 | "`update.sh` remains only as a thin alias" |
| 10 | Every existing installer suite passes. Suites that pipe answers into stdin are converted to drive a pty; no assertion is weakened | regression, no weakened tests |
| 11 | Mutation control M1: make the plan confirm default to acting without reading input → AC4 test fails | observed failing |
| 12 | Mutation control M2: make prompts read stdin again → AC7 test fails | observed failing |

---

## Evaluation & Acceptance (How we know the agent worked correctly)

### Success Criteria (observable, pass/fail)

| # | Given (input/state) | Expect (output/behavior) | How it's checked |
|---|---------------------|--------------------------|------------------|
| 1 | empty git repo, pty answers `⏎ ⏎` (default Install, accept) | install completes; lock written | automated (pty) |
| 2 | installed repo, pty `3` | exit 0; `git status --porcelain` empty | automated (pty) |
| 3 | installed repo with edited skill, pty `2 ⏎` then `Y` | edited file present as `.bak`; kit version installed; plan screen named the file before confirm | automated (pty) |
| 4 | installed repo, pty `1 ⏎ n 3` | back to menu then cancelled; no changes | automated (pty) |
| 5 | `cat setup.sh \| sh` inside a pty, answers via the terminal | menus appear and answers take effect | automated (pty) |
| 6 | installed repo with edited skill, `setsid sh setup.sh </dev/null` | prints "no terminal — updating, keeping your edits"; edit kept; exit 2 | automated |
| 7 | empty repo, `setsid sh setup.sh </dev/null` | prints the install defaults; installs; exit 0 | automated |
| 8 | `sh update.sh` from a checkout in an installed repo, pty `⏎ Y` | same result as SC1's Update path | automated (pty) |
| 9 | `update.sh` copied alone to a temp dir and run | exit 1; prints the install command | automated |

### Verification Command (exact, runnable)

```bash
bash tests/test_one_command_menu.sh
bash tests/test_setup.sh
bash tests/test_update.sh
bash tests/test_install_update_smoke.sh
bash tests/test_update_claude_md.sh
bash tests/test_settings_merge.sh
bash tests/test_install_backups.sh
bash tests/test_update_removals.sh
bash tests/test_t098_harness_presence.sh
bash tests/test_harness_projection.sh
shellcheck -x setup.sh update.sh
```

### Evidence (filled by reviewer at Stage 4/5)

> Filled by the reviewer at Stage 4/5 in `tasks/TASK_REVIEW_T114.md`. **HITL**: paste the full terminal
> transcript of SC1, SC3 and SC6 for the user's wording review.

---

## Demonstration

> See `tasks/TASK_REVIEW_T114.md`.

---

## Approach

**Pattern reference**: `prompt_conflict` in `update.sh:196` — a `while` loop that re-prompts on invalid
input and treats EOF as "no answer, take the safe path". That is the contract every menu in this task
follows. For pty-driven tests, `memory/learnings.md` (T108): `script -qec` reaches `[ -t 0 ]`/`/dev/tty`
prompts a pipe cannot.

**Vital slice**: detection → action menu → plan screen → dispatch to the existing install/update code, with
one `/dev/tty` reader used by every prompt.
**Cut list**:
- Colour/box-drawing menus, arrow-key selection — numbered lines are enough and work everywhere.
- A "Repair" action — Update already reinstalls missing files as "new file installed".
- Remembering the last choice.

**Supervisor decisions**:
- **Code layout**: move update's functions out of `update.sh` into a new sibling library
  `lib/harness-update.sh`, sourced by `setup.sh` next to `lib/harness-fetch.sh`. (The brainstorming log said
  "into `lib/harness-fetch.sh`"; a sibling keeps the fetch library focused — recorded deviation, same
  outcome.) `setup.sh`'s existing piped-install bootstrap then covers update too.
- **TTY reader**: one function that opens `/dev/tty` inside a subshell probe (`: </dev/tty` can fail even
  when the file exists, e.g. under `setsid`); if it cannot, every prompt returns "no answer" and the no-TTY
  defaults apply.
- **Alias mechanism**: `update.sh` selects the Update action for `setup.sh` through an internal,
  undocumented environment variable (e.g. `EASYKIT_ACTION=update`). It is a seam, not a user option: never
  documented, and an unknown value is an error.

---

## Edge Case Checklist

- [ ] Lock present but canon half-deleted → Update default still correct (missing files reinstalled); the plan screen shows the count of files to restore
- [ ] Lock present but not a git repo any more → rejected before the menu (prerequisite order unchanged)
- [ ] Ctrl-C at any prompt → temp clone cleaned (existing traps), no partial write (prompts happen **before** any write)
- [ ] The fetch happens before the plan screen (the plan needs upstream content to know what will be backed up) — it writes only to the temp dir
- [ ] Windows Git Bash / macOS `/dev/tty` behaviour — note as untested if not verifiable here; do not claim it
- [ ] `setsid` is util-linux; tests needing it must skip with a named message where absent, never pass silently
- [ ] Old `~/.supervisor` symlink-model install still refused with the migration message before any menu

---

## Files to Change (Predicted)

| File | Change |
|------|--------|
| `setup.sh` | Detection, action menu, plan screen, `/dev/tty` reader, dispatch; `prompt_mode` reads via the reader |
| `lib/harness-update.sh` | New — update functions moved from `update.sh`; conflict prompt uses the reader |
| `update.sh` | Reduced to the alias |
| `tests/test_one_command_menu.sh` | New — SC1–SC9 + M1/M2 |
| `tests/test_update.sh`, `tests/test_install_update_smoke.sh`, others that pipe answers | Drive a pty instead of stdin; no assertion weakened |
| `.github/workflows/ci.yml` | Add the new suite step (T109's drift test will demand it) |
| `ci.yml` shellcheck list + `tests/test_shellcheck_clean.sh` | Add `lib/harness-update.sh` to both, together (T105 mirror) |

## Files Must NOT Touch

| File | Reason |
|------|--------|
| `--harness` / `--copy` / `--pack=` parsing, `prompt_packs`, `install_pack` | T115/T116 |
| `README.md`, `site/index.html`, `RUNBOOK.md` | T115 |
| `lib/merge-settings.py`, backup helper internals | Owned by T111/T112 — call them, don't change them |

---

## Test Plan

Capture BEFORE on the integration branch tip (after T110–T113 merge, before this task's first commit):
`sh ./update.sh` failing, and the silent overwrite on re-running setup. Then `tests/test_one_command_menu.sh`
with SC1–SC9 + M1/M2. Convert stdin-piping suites to pty without changing what they assert.

---

## Completion Checklist

- [ ] Implementation done
- [ ] Self-review: `Skill({ skill: "code-review" })` run (Supervisor)
- [ ] Security review: `Skill({ skill: "security-review" })` run (Medium risk)
- [ ] `shellcheck -x setup.sh update.sh lib/harness-update.sh` clean
- [ ] Tests written AND pass — output pasted into `tasks/TASK_REVIEW_T114.md` (Hard-Stop Gate 5)
- [ ] HITL: user reviewed the menu transcripts and approved the wording
- [ ] `/verify` — user-invoked
- [ ] Learnings flagged to the Supervisor
- [ ] Supervisor notified: task ready for Stage 4 review
