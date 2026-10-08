# TASK_REVIEW — T137: A backup is named after the kit version it replaces, and Update's "overwrite" takes one too

> Sibling of `tasks/TASK_GUIDE_T137.md`. Everything here is **filled by the reviewer at Stage
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
| **New test(s) cover Acceptance Criteria (file paths pasted)** | ☑ pass | `tests/test_install_backups.sh` — new `T137 SC1` (AC1 install, AC2, AC7 plan line), `T137 SC3` (AC3), `T137 SC4` (AC5: `.bak-<B>`, `.1`, `.2`, first byte-identical), `T137 edge` (non-hex `kit_commit` → dated name, nothing outside); existing SC1–SC5/edges moved to `.bak-<date>` (first install, AC3). `tests/test_update.sh` — new `T137 SC2` + `AC4` + `AC1` (Update), `T137 SC5` (AC6), `T137 edge` (failed backup keeps the file), `test4 (T137 SC6)` + `test6 (T137 AC9)`. AC8 docs: `tests/test_site_content.py`, `tests/test_docs_match_installer.py` 40 passed. Output: `17 passed, 0 failed` / `----- summary: 38 passed, 0 failed -----` (before: 13 / 31) |
| Verification command run | ☐ fail (1 pre-existing, unrelated) | 2026-10-08T15:21:14Z, HEAD `fd05b16`, exit=1: `17 passed, 0 failed` · `----- summary: 38 passed, 0 failed -----` · `30 passed, 0 failed` · `9 passed, 0 failed` · `validate.sh: PASS` · shellcheck silent · pytest `1 failed, 991 passed` — the one failure is `.claude/hooks/tests/test_kanban_section_parsing.py::test_find_kanban_section_on_real_current_board`: `AssertionError: T138 owns a row under 'Todo' on PROJECT_KANBAN.md but find_kanban_section() resolved it to 'In Progress'`. Identical at the baseline (`792b486`, before any T137 code: `1 failed, 991 passed`). It reads the live board, which this task may not edit — Supervisor's call |
| Negative cases hold | ☑ pass | Mutations, each applied to the committed tree, run, then `git checkout -- <file>`: **M1** (Update `o`: `if ! harness_backup_path …` → `if false`) → `FAIL: T137 SC2: [o]verwrite backup (rc=0 lock-before=8b30194 A=8b30194)` · `FAIL: T137 AC4: no [warn] line names agents/backend.md.bak-8b30194` · `----- summary: 35 passed, 2 failed -----` (re-run after the edge test was added: also `FAIL: T137 edge: failed backup on [o]verwrite (rc=0)`, `35 passed, 3 failed`). **M2** (`extract_lock_pairs` reads the whole lock again) → `FAIL: T137 SC5: kit_commit leaked into the file entries (rc=0)`, `36 passed, 1 failed`; the rewritten lock showed `  "kit_commit": "358a561",` AND `    "kit_commit": "abc1234",` inside `"files"`. **M3** (`_bn_base="$1.bak"`) → test_install_backups `6 passed, 11 failed` incl. `FAIL: T137 SC1: versioned Reinstall backup`, `FAIL: T137 SC4: collision numbering (rc=0/0/0/0)`; test_update `FAIL: T137 SC2`, `35 passed, 2 failed`. Plus `s` / `eof` make no backup (AC9) |
| verify | ☐ pass / ☐ fail / ☐ N/A | user-run (`/verify`) — not run by the implementing agent |
| Review scope bounded to the change's blast radius (affected set, not whole repo) | ☑ pass | Affected set: `harness_backup_path` callers (install `harness_copy_manifest`, `_harness_install_excluding`, `install_claude`, Reinstall, Update `o`), the lock readers (`lookup_lock_hash`, new `lookup_lock_field`, `extract_lock_pairs` → `process_one_file`, `resolve_claude_md_source`, `carry_over_unprocessed`, `plan_*`) and both lock writers. Every installer shell suite run (list in next row). `harness_install_canon_symlinks`' `<link>.bak` deliberately untouched (out of scope) — `test_setup` test4 / `test_update` test7 still assert `.claude/skills.bak` |
| Full smoke suite still green (no regression) | ☑ pass | All installer suites green at HEAD: install_backups 17/0, update 38/0, update_removals 30/0, install_update_smoke 9/0, one_command_menu 22/0, pack_catalog 16/0, setup 18/0, update_claude_md 35/0, manifest_exclusions 8/0, harness_fetch 9/0, settings_merge 40/0, cli_and_project_menus 24/0, t098_harness_presence 20/0, harness_projection 41/0, readme_current ALL PASS, shellcheck_clean PASS. pytest 991 passed / 1 pre-existing failure (row above) |
| **UI: Visual regression (diff or verdict pasted)** | ☐ N/A | No UI component: the `site/index.html` change is prose inside `#install` and `#update-flow` only (no markup/CSS change); `#what-you-get` untouched for T138 |
| **UI: Design-system compliance (tokens/colors/typography verified)** | ☐ N/A | Prose only — existing `<code>`/`<p class="lead">`/`<li>` elements reused, no new styles |
| **UI: Responsiveness at target viewports** | ☐ N/A | Prose only — no layout change |

---

## Open questions

None blocking. Two notes for the Supervisor:
- `PROJECT_SPEC.md` (Critical Constraints, Known Risk Areas) still says `<name>.bak` / `<name>.bak[.N]`.
  It is not in this guide's Files to Change, so it was left alone; it is now stale.
- A failed backup during Update `o` exits 2 with the existing summary line "N conflict(s) could not be
  resolved (no interactive input)". The `[error] Could not back up …` line above it says the real
  cause, but the summary's "(no interactive input)" wording is inaccurate for that case. Left as is
  (adjacent code); a one-line wording fix if wanted.

---

## Demonstration

> Anchors what this task delivered to an observable before/after pair. BEFORE has no `N/A` path:
> if the task changes executable code, BEFORE is a pasted, timestamped terminal capture taken
> **before any implementation commit exists**; if it does not (docs, templates, skill-instruction
> text), BEFORE is the **verbatim prior content** of what changed — a quoted excerpt, not a command.

**BEFORE**: captured 2026-10-08T15:04:20Z at `792b486` (no implementation commit yet), by the
common-infrastructure sub-agent. The guide names no Demonstration command, so this script (offline
fixture kit with two commits A → B; one project Reinstalled, one Updated with `o`) is the command;
AFTER re-runs it unchanged. Run: `sh demo_t137.sh "$PWD"` from the worktree root.

<details><summary>demo_t137.sh</summary>

```sh
#!/bin/sh
# T137 demonstration: what backup does each action leave, and does the lock know the kit version?
# usage: sh demo_t137.sh <repo-root>
set -u
REPO_ROOT="$1"
. "$REPO_ROOT/tests/lib/pty.sh"
W=$(mktemp -d "${TMPDIR:-/tmp}/t137-demo.XXXXXX"); trap 'rm -rf "$W"' EXIT
K="$W/kit"; mkdir -p "$K/agents" "$K/.claude" "$K/lib"
printf 'backend v1\n' > "$K/agents/backend.md"
printf '{ "hooks": {} }\n' > "$K/.claude/settings.json"
cp "$REPO_ROOT/lib/merge-settings.py" "$K/lib/"
printf '# Claude Project Supervisor Guidelines\n' > "$K/CLAUDE.md"; printf 'LEGACY\n' > "$K/CLAUDE_LEGACY.md"
printf 'agents\n' > "$K/MANIFEST"
git -C "$K" init -q; git -C "$K" -c user.email=t@e -c user.name=t add -A; git -C "$K" -c user.email=t@e -c user.name=t commit -qm A
A=$(git -C "$K" rev-parse --short HEAD)
for p in reinstall update; do
  P="$W/$p"; mkdir -p "$P"; git -C "$P" init -q
  ( cd "$P" && SUPERVISOR_REPO="file://$K" setsid sh "$REPO_ROOT/setup.sh" </dev/null >/dev/null 2>&1 )
  printf 'MY EDIT\n' > "$P/agents/backend.md"
done
printf 'backend v2\n' > "$K/agents/backend.md"; git -C "$K" -c user.email=t@e -c user.name=t commit -qam B
echo "kit commit installed (A): $A"
echo "\$ grep kit_commit .claude/harness-lock.json   # after install at A"
grep kit_commit "$W/reinstall/.claude/harness-lock.json" || echo "(no kit_commit field)"
( cd "$W/reinstall" && SUPERVISOR_REPO="file://$K" run_in_pty '2\n\n\n\n\n' "sh '$REPO_ROOT/setup.sh'" ) > "$W/r.log" 2>&1
echo "\$ Reinstall (menu 2) -> plan line + backups left:"
grep -a 'agents/backend.md' "$W/r.log" | tr -d '\r' | grep -av 'diff\|^[-+@]' | head -3
( cd "$W/reinstall" && ls -1d agents/backend.md* )
( cd "$W/update" && SUPERVISOR_REPO="file://$K" run_in_pty '\n\no\n' "sh '$REPO_ROOT/setup.sh'" ) > "$W/u.log" 2>&1
echo "\$ Update (menu 1), answer 'o' on the edited file -> backups left:"
( cd "$W/update" && ls -1d agents/backend.md* )
echo "agents/backend.md now: $(cat "$W/update/agents/backend.md")"
grep -a 'Backed up' "$W/u.log" | tr -d '\r' || echo "(no backup line in Update output)"
```
</details>

```
captured 2026-10-08T15:04:20Z at 792b486
kit commit installed (A): 9821f53
$ grep kit_commit .claude/harness-lock.json   # after install at A
(no kit_commit field)
$ Reinstall (menu 2) -> plan line + backups left:
      agents/backend.md
Proceed? [Y/n] [warn]  Backed up your existing './agents/backend.md' to './agents/backend.md.bak' before installing the kit's copy — compare and merge by hand, then delete the backup.
agents/backend.md
agents/backend.md.bak
$ Update (menu 1), answer 'o' on the edited file -> backups left:
agents/backend.md
agents/backend.md now: backend v2
  - Backed up: nothing. Update keeps your edits in place instead.
```

Absent before T137: the lock records no kit version; Reinstall's backup is a bare `.bak`; Update's
`o` replaced the user's `MY EDIT` with `backend v2` and left **no backup at all**.

**AFTER**: same script, captured 2026-10-08T15:20:28Z at `7d7f540` (ANSI colour stripped):

```
captured 2026-10-08T15:20:28Z at 7d7f540
kit commit installed (A): d4ac183
$ grep kit_commit .claude/harness-lock.json   # after install at A
  "kit_commit": "d4ac183",
$ Reinstall (menu 2) -> plan line + backups left:
      agents/backend.md
Proceed? [Y/n] [warn]  Backed up your existing './agents/backend.md' to './agents/backend.md.bak-d4ac183' before installing the kit's copy — compare and merge by hand, then delete the backup.
agents/backend.md
agents/backend.md.bak-d4ac183
$ Update (menu 1), answer 'o' on the edited file -> backups left:
agents/backend.md
agents/backend.md.bak-d4ac183
agents/backend.md now: backend v2
  - Backed up: only a file you choose to [o]verwrite. [s]kip keeps your edit in place.
  Resolve: [o]verwrite / [s]kip / [v]iew diff again: [warn]  Backed up your existing './agents/backend.md' to './agents/backend.md.bak-d4ac183' before installing the kit's copy — compare and merge by hand, then delete the backup.
```

**DELTA**: A user who picks Update's "overwrite" on a file they edited now gets that edit back as
`<file>.bak-<old kit commit>` instead of losing it, and every backup's name says which kit version it
came from.

**WITNESS**: [who ran it and when — derived from `memory/event-trace/Txxx.jsonl`, never the
implementing agent alone]
