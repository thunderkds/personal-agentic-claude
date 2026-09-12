# TASK_GUIDE — T111: Kit hooks reach a project that already has `settings.json`, and stay current on update
**Date**: 2026-09-12
**Complexity Level**: C2 (Hard-Stop Gate 2 floor: installer restructure)
**Risk Level**: Medium
**Priority**: P1
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
7. Read `docs/adr/0002-one-confirmed-menu-driven-installer.md` and the 2026-08-17 T074 entries in `memory/learnings.md` (a `settings.json` hook entry pointing at a missing file bricks every Bash call)

---

## Requirement (Pillar 1 — Adapt the requirement)

Probe, 2026-09-12, `main` `8115bc9`:
- A project that already had `.claude/settings.json` (`{"permissions":{}}`) was installed into. After
  install the file was still exactly `{"permissions":{}}` — **zero kit hooks wired, and no message
  saying so**. `install_settings` (`setup.sh:399`) returns early on an existing file by design ("never
  overwrite project settings; merge hook changes manually") but never tells the user to merge.
- On update, an upstream `settings.json` change never arrives (`update.sh` has no settings step).

Every one of the 8 wired hooks runs as `python3 …` (measured), so `python3` is already a hard
prerequisite of a working install. ADR-0002 decides: merge with `python3`; leave user permissions alone;
fail the hook step loudly if `python3` is absent.

**Restated intent**:
> After install or update, `.claude/settings.json` contains every hook the kit ships, keeps everything the
> user added, never points at a hook file that does not exist, and any case the installer cannot merge is
> reported loudly with the exact block to add.

**Out of scope**:
- Changing any hook's behaviour or the set of hooks.
- Merging `settings.local.json`.
- Menus / single command (T114).
- Removing hook *files* deleted upstream (T113) — this task only keeps `settings.json` entries consistent with the hook files the kit ships.

**Requirement Refs**: none in `PRD.md`; authority ADR-0002 ("`settings.json` is merged with `python3`").

### Requirement Fidelity Gate (sign off BEFORE implementation)

- [x] Restated intent confirmed (Supervisor, probe + ADR-0002, user-approved)
- [x] Domain terms align with glossary
- [x] Every Acceptance Criterion traces to the Requirement
- [x] No `PRD.md` refs claimed

---

## Dependencies & Reachability

**Depends on**: T109 — installer suites wired into CI

**Entry point**: `install_settings` in `setup.sh`, and the settings step added to `update.sh`'s `main`

---

## Acceptance Criteria

| # | Criterion (testable) | Traces to requirement |
|---|----------------------|-----------------------|
| 1 | No `settings.json` in project → install writes the kit file (current behaviour kept) | regression |
| 2 | Existing `settings.json` with user `permissions` and no hooks → after install it contains every kit hook entry **and** the user's `permissions` unchanged | "contains every hook … keeps everything the user added" |
| 3 | User has their own hook entry (a command **not** under `.claude/hooks/`) → still present after install and after update | "keeps everything the user added" |
| 4 | Upstream adds a hook entry → update adds it to the project's `settings.json` | "stay current on update" |
| 5 | Upstream removes a kit hook entry (and its file) → update removes that entry from the project; a user entry is never removed | "never points at a hook file that does not exist" |
| 6 | Merge is idempotent: a second install/update produces a byte-identical `settings.json` | no churn in the user's git diff |
| 7 | `settings.json` is invalid JSON → file left byte-identical; stderr names the file and prints the kit hook block to add; the run finishes the rest of its work and exits 2 | "reported loudly with the exact block" |
| 8 | `python3` not on `PATH` (simulated via a restricted `PATH`) → same as AC7: file untouched, loud message, exit 2 | ADR-0002 "fail the hook step loudly" |
| 9 | Mutation control M1: make the merge skip adding entries → AC2 test fails | the guard must be observed failing |

---

## Evaluation & Acceptance (How we know the agent worked correctly)

### Success Criteria (observable, pass/fail)

| # | Given (input/state) | Expect (output/behavior) | How it's checked |
|---|---------------------|--------------------------|------------------|
| 1 | scratch repo with `{"permissions":{"allow":["Bash(ls:*)"]}}` | after install: `permissions.allow == ["Bash(ls:*)"]`; every kit `command` string present | automated (python json assert) |
| 2 | project settings with a user PreToolUse hook `echo mine` | present after install and after update | automated |
| 3 | upstream clone adds a hook entry + file; update | entry present in project | automated |
| 4 | upstream removes a kit entry + file; update | entry absent; user entry present | automated |
| 5 | run install/update twice | `cmp` identical | automated |
| 6 | settings file `{not json` | byte-identical after; stderr contains `settings.json` and a `"hooks"` block; exit 2 | automated |
| 7 | `PATH` without python3 | as SC6 | automated |
| 8 | every `command` in the merged file references an existing file | true for fresh install, post-update, post-removal | automated |

### Verification Command (exact, runnable)

```bash
bash tests/test_settings_merge.sh
bash tests/test_setup.sh
bash tests/test_update.sh
bash tests/test_install_update_smoke.sh
shellcheck -x setup.sh update.sh
python3 -m pytest .claude/hooks/tests/ -q
```

### Evidence (filled by reviewer at Stage 4/5)

> Filled by the reviewer at Stage 4/5 in `tasks/TASK_REVIEW_T111.md`.

---

## Demonstration

> See `tasks/TASK_REVIEW_T111.md`.

---

## Approach

**Pattern reference**: `.claude/hooks/lib/` Python modules — stdlib-only, defensive `json` handling. For
the shell side, `harness_install_canon_symlinks` in `lib/harness-fetch.sh`: idempotent, and it refuses
loudly instead of guessing.

**Vital slice**: one stdlib-only Python merge script, called by both install and update, with a stated
ownership rule for which entries are the kit's.
**Cut list**:
- Pretty-print preservation of the user's original formatting — `json.dump(indent=2)` is acceptable; write only when the merged content differs (AC6 keeps diffs quiet).
- Merging keys other than `hooks` — not requested.
- A `jq` path — `python3` is already required.

**Supervisor decision — ownership rule**: an entry is the kit's if its `command` references a path under
`.claude/hooks/`. Kit entries are reconciled against the upstream file's entries (add missing, remove ones
upstream no longer ships). Every other entry belongs to the user and is never modified or removed. The
merge script lives with the installer (e.g. `lib/merge-settings.py`) and runs from the temp clone, so it is
never installed into user projects.

---

## Edge Case Checklist

- [ ] User copied a kit entry but changed its matcher → still references `.claude/hooks/…` so it is kit-owned; decide and test: replaced by upstream's version (document it in the script header)
- [ ] `hooks` key present but an event's list is empty or `null`
- [ ] Unicode / non-ASCII in user permissions survives (`ensure_ascii=False`)
- [ ] `settings.json` is a symlink → refuse like invalid JSON; never write through it
- [ ] Merge writes atomically (temp file + rename) so an interrupted run never truncates the user's file
- [ ] A command string using `"$CLAUDE_PROJECT_DIR"` quoting — match the path, not the whole string

---

## Files to Change (Predicted)

| File | Change |
|------|--------|
| `lib/merge-settings.py` | New — stdlib-only merge with the ownership rule |
| `setup.sh` | `install_settings` calls the merge when the file exists |
| `update.sh` | New settings step after file processing |
| `tests/test_settings_merge.sh` | New — SC1–SC8 + M1 |

## Files Must NOT Touch

| File | Reason |
|------|--------|
| `.claude/hooks/*.py` | Hook behaviour is out of scope |
| `.claude/settings.json` (kit's own) | Source of truth for kit entries; not edited by this task |
| `MANIFEST` | `settings.json` stays a per-project merge, not a MANIFEST copy |
| `lib/harness-fetch.sh` copy functions | T112/T113 edit there; avoid merge conflicts |

---

## Test Plan

New `tests/test_settings_merge.sh` (offline `file://` upstream, python json assertions via `python3 -c`),
one case per Success Criteria row plus M1. Existing installer suites stay green.

---

## Completion Checklist

- [ ] Implementation done
- [ ] Self-review: `Skill({ skill: "code-review" })` run (Supervisor)
- [ ] Security review: `Skill({ skill: "security-review" })` run (Medium risk — writes a file that decides which commands run)
- [ ] `shellcheck -x setup.sh update.sh` clean
- [ ] Tests written AND pass — output pasted into `tasks/TASK_REVIEW_T111.md` (Hard-Stop Gate 5)
- [ ] `/verify` — user-invoked
- [ ] Learnings flagged to the Supervisor
- [ ] Supervisor notified: task ready for Stage 4 review
