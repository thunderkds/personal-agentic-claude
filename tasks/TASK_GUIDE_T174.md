# TASK_GUIDE — T174: Update can overwrite or keep all edited files in one choice, and logs every decision
**Date**: 2026-10-26
**Complexity Level**: C2
**Risk Level**: High
**Priority**: P1
**Assigned agent**: common-infrastructure
**Agent guide**: `agents/common-infrastructure.md`

> Risk High: "Overwrite all" replaces the user's edited files in their own project in one step. The
> backup-first rule (T137) is the only thing that keeps those edits recoverable.

---

## Mandatory Startup (Do Not Skip)

Before writing any code:
1. Read `PROJECT_SPEC.md`
2. Read the memory slice in your spawn prompt (`<!-- memory-slice -->`). Read `memory/MEMORY.md` in full only if your work reaches a file, hook, skill or decision the slice does not cover
3. Read this file completely
4. Read `agents/common-infrastructure.md`
5. Note the **Complexity Level** above and apply the matching process (brainstorm / decompose / verify depth) from the Complexity matrix in your role guide (`agents/common-infrastructure.md`)
6. **C2/C3 or multi-file tasks only**: read `memory/codebase-map.md` for directory layout, entry points, and blast-radius hotspots — skip if the task is C0/C1 and touches a single known file
7. Read `docs/adr/0002-one-confirmed-menu-driven-installer.md` — this task must stay inside it (no flags)

---

## Requirement (Pillar 1 — Adapt the requirement)

User, 2026-10-26: "checking if we support 'Update for the auto-approve with the decision logs'" → Supervisor: not supported today (per-file `[o]verwrite / [s]kip / [v]iew` prompt only; outcomes printed to the screen, never saved) → user: "yes, plan it as a new task".

Supervisor-confirmed facts (2026-10-26, `main` @ `b122017`):
- `lib/harness-update.sh:157` `prompt_conflict` offers only `[o]verwrite / [s]kip / [v]iew diff again`, asked once per edited file.
- `lib/harness-update.sh:636` `plan_update` prints the plan; `setup.sh:644` `confirm_plan` asks `Proceed? [Y/n]`.
- No terminal → edited files are kept; the run exits `2` (`lib/harness-update.sh:732`, `:776`, `:780`).
- The `_decisions` file in `lib/harness-update.sh` is a temp list of `path<TAB>hash` used once to rewrite `.claude/harness-lock.json` (`:471`); it is not a human-readable log.
- ADR-0002 (Accepted, user 2026-09-12): "one single command; every option chosen from a list, never a parameter" — `setup.sh` has **no flags**.

User decisions (AskUserQuestion, 2026-10-26):
- D1 — Auto-approve is chosen **on the plan screen**: when the plan lists edited files, `Proceed? [Y/n]` is replaced by a numbered list. ("On the plan screen (Recommended)"). Shown preview, verbatim:
  ```
  How should Update treat your edited files?
    1) Ask me about each one
    2) Overwrite all of them (each backed up first)
    3) Keep all of them
    4) Cancel
  Choice [1]: 2
  ```
- D2 — The decision log is written on **every** Update run, to `.claude/update-log.md`, newest run on top. ("Every Update run (Recommended)"). Shown preview, verbatim:
  ```
  ## 2026-10-26 14:05 — Update 75040d9 → b122017
  Decided by: auto-approve (overwrite all)
  - CLAUDE.md — overwrote (your edits; backup CLAUDE.md.bak-75040d9)
  - agents/qa.md — overwrote (your edits; backup agents/qa.md.bak-75040d9)
  - 41 kit files you never edited — refreshed
  - 2 files added

  ## 2026-10-12 09:30 — Update 9f1c2aa → 75040d9
  Decided by: no terminal (kept edits)
  - CLAUDE.md — kept your version
  ```

**Restated intent** (Supervisor's interpretation, in the project's domain language):
> A user running **Update** can settle all their edited kit files with one choice from the plan
> screen — overwrite all (each backed up first) or keep all — instead of answering per file, and every
> Update run leaves a dated, human-readable record in `.claude/update-log.md` of what happened to each
> file and how it was decided.

**Out of scope** (what this task explicitly does NOT do):
- Any flag, env var or argument that selects auto-approve (ADR-0002). No-terminal runs keep today's behaviour: edits kept, exit `2` — they only gain a log entry.
- **Reinstall** and **Install** flows (they have their own backup plan; no per-file prompt).
- Changing the per-file prompt's answers (choice 1 is today's behaviour, unchanged).
- Board / Linear Decision Log (`board_sync.py decide`) — that is the Supervisor's decision log, a different thing.
- Rotating or truncating the log.

**Requirement Refs**:
- User request 2026-10-26 (above); ADR-0002 (no flags).

### Requirement Fidelity Gate (sign off BEFORE implementation)

- [x] Restated intent confirmed to match the user's request (Supervisor, 2026-10-26; D1/D2 answered by the user with previews)
- [x] Domain terms align with `PROJECT_SPEC.md` glossary (new term: **update log** = `.claude/update-log.md`; "decision log" in the user's words. Do not call it "Decision Log" — that name is the board's, T158)
- [x] Every Acceptance Criterion below traces to a line in the Requirement
- [x] All Requirement Refs exist and are covered by the Acceptance Criteria

---

## Dependencies & Reachability

**Depends on**: None — T137 (backup-first) and T114 (menu/plan screen) are in `main`.

**Entry point**: `How should Update treat your edited files?`

---

## Acceptance Criteria

| # | Criterion (testable) | Traces to requirement |
|---|----------------------|-----------------------|
| 1 | Update with a terminal and ≥1 edited file: after the plan, the prompt is exactly the D1 list (`How should Update treat your edited files?`, `1) Ask me about each one`, `2) Overwrite all of them (each backed up first)`, `3) Keep all of them`, `4) Cancel`, `Choice [1]: `). Enter = 1. Invalid input re-asks. | D1 |
| 2 | Choice 1 behaves exactly as today: the per-file `[o]verwrite / [s]kip / [v]iew diff again` prompt for each edited file. | D1 (no regression) |
| 3 | Choice 2: every edited file is backed up first (T137 `harness_backup_path`, `<file>.bak-<commit>` naming) and then replaced with upstream, with no per-file prompt. A file whose backup fails is **kept** (never overwritten without a backup), counted unresolved, and logged as kept with the reason. `CLAUDE.md` is included, delivered from its recorded source (T110/T173). | D1, Risk High |
| 4 | Choice 3: every edited file is kept, no prompt, no backup; the run reports success (not exit `2`), because the user decided. | D1 |
| 5 | Choice 4: nothing changes, no files written, no log entry; same exit as today's `n` at `Proceed?`. | D1 |
| 6 | Update with no edited files: the plan still ends in `Proceed? [Y/n]` (no list — nothing to decide). | D1 scope |
| 7 | Every Update run that changes or decides anything (choices 1–3, `Proceed? y`, and no-terminal runs) prepends one entry to `.claude/update-log.md`, creating the file if absent. Entry header: `## <YYYY-MM-DD HH:MM> — Update <old kit_commit short> → <new kit_commit short>`; then `Decided by: ` one of `asked per file`, `auto-approve (overwrite all)`, `auto-approve (keep all)`, `no edited files`, `no terminal (kept edits)`; then one line per edited file with its outcome (`overwrote (your edits; backup <path>)`, `kept your version`, `kept (backup failed: <reason>)`), one line per removal from the plan, and summary counts for refreshed and added files. Older entries stay below, byte-for-byte. | D2 |
| 8 | Negative: a log write failure (e.g. `.claude/update-log.md` is a directory or not writable) prints a warning and does not change the update's outcome or exit code. The log never contains file contents or diffs — paths, outcomes and counts only. | D2, safety |
| 9 | Negative: no new flag, env var or argument is read by `setup.sh` / `update.sh` (ADR-0002); `EASYKIT_ACTION` stays the only internal seam. | ADR-0002 |
| 10 | Docs: `site/index.html` `#update-flow` and `README.md`'s Update text describe the new list and the update log; the Hard-Stop Gate 6 UI rows are filled. | user-facing surface |

---

## Evaluation & Acceptance (How we know the agent worked correctly)

### Success Criteria (observable, pass/fail)

| # | Given (input/state) | Expect (output/behavior) | How it's checked |
|---|---------------------|--------------------------|------------------|
| 1 | Fixture install, 2 edited kit files, Update in a pty, answers `\n\n2\n` | both files = upstream; both `.bak-<commit>` backups exist with the user's content; log entry "auto-approve (overwrite all)" lists both with backup paths | automated (pty) |
| 2 | Same, answer `3` | both files byte-identical to the user's version; no backups; exit 0; log "auto-approve (keep all)" | automated (pty) |
| 3 | Same, answer `1` then `o`, `s` | today's per-file flow; log "asked per file" with one overwrote + one kept | automated (pty) |
| 4 | Same, answer `4` | no file changed (tree hash identical), no `.claude/update-log.md` | automated (pty) |
| 5 | Same, answer `x` then `2` | re-asks once, then behaves as SC 1 | automated (pty) |
| 6 | No edited files | `Proceed? [Y/n]` shown, list not shown; log "no edited files" with counts | automated (pty) |
| 7 | No terminal, 2 edited files | today's behaviour (kept, exit `2`); log "no terminal (kept edits)" | automated |
| 8 | Choice 2 with one backup forced to fail | that file kept + logged `kept (backup failed: …)`; other file overwritten | automated |
| 9 | `.claude/update-log.md` is a directory | warning printed; update outcome and exit code same as SC 1 | automated |
| 10 | Two Update runs in a row | two entries, newest first; first entry unchanged byte-for-byte | automated |

### Verification Command (exact, runnable)

```bash
bash tests/test_update_auto_approve.sh && bash tests/test_update.sh && bash tests/test_update_claude_md.sh && bash tests/test_install_backups.sh && bash tests/test_one_command_menu.sh && bash tests/test_install_update_smoke.sh && python3 -m pytest -q tests .claude/hooks/tests && sh scripts/validate.sh && sh scripts/smoke-install.sh && shellcheck -x setup.sh update.sh lib/harness-update.sh tests/test_update_auto_approve.sh
```

### Evidence (filled by reviewer at Stage 4/5)

> **Moved.** Filled by the reviewer at Stage 4/5 in `tasks/TASK_REVIEW_T174.md`.

---

## Demonstration

> **Moved.** See `tasks/TASK_REVIEW_T174.md`.

---

## UI / Design Acceptance Criteria

> UI scope is copy only: `site/index.html` `#update-flow` text (AC 10). No CSS, class or layout change.

### 1. Visual Regression

| Screen / Component | Verification method | Expected result |
|-------------------|---------------------|-----------------|
| `#update-flow` section | headless Chrome screenshot (section isolated) | new list + update-log text render in existing styles, no overlap |

### 2. Design-System Compliance

| Criterion | Verification method | Expected result |
|-----------|---------------------|-----------------|
| Colors / typography / spacing | diff review: no new CSS, classes or tokens | existing `<code>`, `<ul class="lead">`, `<pre>` styles only |

### 3. Layout / Responsiveness

| Viewport | Verification method | Expected result |
|----------|---------------------|-----------------|
| Mobile (390px) | headless Chrome screenshot | text wraps; any `<pre>` scrolls inside its box, page does not |
| Desktop (1280px) | headless Chrome screenshot | matches neighbouring sections |

---

## Approach

**Pattern reference**: `setup.sh` `confirm_plan` / `choose_action` (numbered-list prompts read from `/dev/tty` via `tty_read`, T114); `lib/harness-update.sh` `process_one_file` + `prompt_conflict` (per-file flow and `CONFLICT_DECISION`); `harness_backup_path` (T137 backup-first); `tests/test_update_claude_md.sh` `run_update` + `tests/lib/pty.sh` `run_in_pty` (driving prompts in a real terminal).

**Vital slice**: the plan-screen list (AC 1, 6), choice 2 with backup-first (AC 3) and the log entry (AC 7). Overwrite-all is the risky path; the log is how the user sees what it did.
**Cut list**:
- Log rotation / size cap.
- A "view the log" menu entry.
- Logging Install / Reinstall runs.
- Per-file choice inside choice 2 or 3 (mixing is what choice 1 is for).

Suggested shape (agent may improve, keep it small): `plan_update` already builds `.plan-ask` (the edited-files list). When it is non-empty and `TTY_OK=1`, `confirm_plan` for `update` asks the D1 list and sets a mode (`ask` / `overwrite_all` / `keep_all`); `prompt_conflict` returns `o` / `s` directly in the two auto modes. `process_one_file` already knows each file's outcome — append `outcome<TAB>path<TAB>detail` lines to a temp outcome file next to `_decisions`, and render the log entry from it once at the end of `run_update`, prepending to `.claude/update-log.md` via a temp file + `mv` (keep the file's mode; see the learning "An atomic write silently changes the file's mode").

---

## Edge Case Checklist

- [ ] `CLAUDE.md` with source `conflict` (heading unknown) is in the edited list — choice 2 must deliver it from `CLAUDE.md` (as `process_claude_md` does today on overwrite), choice 3 keeps it.
- [ ] A file listed as edited at plan time but unchanged by run time — no backup, logged as refreshed, never "overwrote".
- [ ] Backup name collision (`.bak-<commit>` exists) — T137 rule: an existing backup is never overwritten; follow `harness_backup_path`'s own fallback, and log the path it actually used.
- [ ] `kit_commit` missing from an old lock (pre-T137) — header shows `unknown → <new>`, never a blank.
- [ ] Log file exists but was edited by the user — prepend only; their text below stays byte-for-byte.
- [ ] Log file is a symlink — do not follow it outside the project; write a warning and skip the log (no write through a symlink).
- [ ] Removals (`plan_removals`): files deleted upstream are logged as `removed` / `kept (you edited it)` per the existing removal rules.
- [ ] Codex-only install (no Claude Code) — the same list and log apply; projection output lines are not logged per file.
- [ ] `Ctrl-D` / EOF at the list — same as today's EOF at `Proceed?`: cancel, nothing written.
- [ ] Time stamp uses local time with no locale-dependent month names (`date '+%Y-%m-%d %H:%M'`).

---

## Files to Change (Predicted)

| File | Change |
|------|--------|
| `setup.sh` | D1 list in the Update confirm step |
| `lib/harness-update.sh` | auto modes in `prompt_conflict` path; outcome recording; log rendering + prepend |
| `tests/test_update_auto_approve.sh` (new) | SC 1–10 |
| `.github/workflows/ci.yml` | run the new suite (`tests/test_ci_wires_shell_suites.py` requires it) |
| `site/index.html`, `README.md` | AC 10 copy |
| `tests/test_site_content.py` | only if a word-cap or section test needs the new text |

## Files Must NOT Touch

| File | Reason |
|------|--------|
| `MANIFEST` | `.claude/update-log.md` is project-owned, never a kit file |
| `docs/adr/*`, `docs/ddr/*` | historical records |
| `AGENTS.md`, `CLAUDE.md`, `CLAUDE_LEGACY.md` | not part of this change |

---

## Test Plan

New `tests/test_update_auto_approve.sh` in the style of `tests/test_update_claude_md.sh`: install a fixture from a local `file://` kit, edit two kit files, publish a newer fixture commit, run Update in a pty with canned answers, assert files, backups, exit codes and the log text. Written RED first against `main`. Include one mutation check (e.g. drop the backup call in overwrite-all → SC 1 must fail).

---

## Completion Checklist

- [ ] Implementation done
- [ ] Self-review: `Skill({ skill: "code-review" })` run
- [ ] Security review: `Skill({ skill: "security-review" })` run (High risk)
- [ ] Tests written AND pass — output pasted into `tasks/TASK_REVIEW_T174.md`'s Evidence table (Hard-Stop Gate 5)
- [ ] UI rows filled (Hard-Stop Gate 6)
- [ ] `Skill({ skill: "verify" })` run (user-only)
- [ ] Supervisor notified: task ready for Stage 4 review

---

## Questions Log
