# TASK_REVIEW — T111: Kit hooks reach a project that already has `settings.json`, and stay current on update

> Sibling of `tasks/TASK_GUIDE_T111.md`. Filled by the reviewer at Stage 4/5.
>
> The Evidence table below was filled by the **implementing agent** (Common-Infrastructure-Agent,
> 2026-09-16) with its own pasted output. Stage 4/5 re-runs it independently; a row is not a
> reviewer's confirmation until the reviewer has re-run it.

---

## Evidence

| Check | Result | Notes / output snippet |
|-------|--------|------------------------|
| **New test(s) cover Acceptance Criteria (file paths pasted)** | ☑ pass | `tests/test_settings_merge.sh` (new, 39 assertions) — SC1–SC8 + M1 + the Edge Case Checklist. `bash tests/test_settings_merge.sh` → `--- 39 passed, 0 failed ---`. AC→test map in the section below. |
| Verification command run | ☑ pass | All six parts, 2026-09-16T07:16:59Z — see "Verification command output" below. `39 passed / 18 passed / 31 passed / 9 passed / shellcheck exit 0 / 795 passed`. |
| Negative cases hold | ☑ pass | Invalid JSON → `SC6: install exits 2 on invalid settings.json`, `SC6: invalid settings.json left byte-identical`, stderr carries `settings.json` + a `"hooks"` block. No `python3` (PATH rebuilt without any `python*`) → `SC7: install exits 2 when python3 is absent`, file byte-identical. User entries → `SC2: user hook entry survives install` / `… survives update`. Symlink → `edge: install exits 2 on a settings.json symlink`, `edge: the symlink target was never written through`. **M1 observed failing on the real source** — output pasted below, not asserted. |
| verify | ☐ pass / ☐ fail / ☐ N/A | Not run — `/verify` is user-invoked only (`memory/MEMORY.md`, project_verify_skill_is_user_only). |
| Review scope bounded to the change's blast radius (affected set, not whole repo) | ☑ pass | Changed set: `lib/merge-settings.py` (new), `setup.sh:install_settings` + `main`, `update.sh:main`, `tests/test_settings_merge.sh` (new), two fixture builders, `.github/workflows/ci.yml` (one step), 2 docs. `lib/harness-fetch.sh` untouched (T112/T113 own it) — `git diff feat/easy-kit-one-command --stat` confirms. `.claude/hooks/*.py`, the kit's own `.claude/settings.json` and `MANIFEST` untouched, per the guide's "Files Must NOT Touch". |
| Full smoke suite still green (no regression) | ☑ pass | `bash tests/test_install_update_smoke.sh` → `9 passed, 0 failed`. `python3 -m pytest .claude/hooks/tests/ -q` → `795 passed`. `python3 -m pytest tests/ -q` → `53 passed, 1 failed`; the one failure is `test_readme_slim.py::test_readme_is_at_most_75_lines` and is **pre-existing on the base branch** (`git show feat/easy-kit-one-command:README.md \| wc -l` → `83`; this branch does not modify `README.md`). |
| **Docs updated per guide's "Documentation to Update" (new text quoted)** | ☑ pass | D1, D2, D3 all applied — new text quoted verbatim in "Documentation updated" below. |
| **UI: Visual regression (diff or verdict pasted)** | ☑ N/A | shell installer + Python merge script; no UI. The two `site/index.html` edits are prose inside existing `<p class="lead">` / `<ul class="lead">` blocks — no new component, style or layout. |
| **UI: Design-system compliance (tokens/colors/typography verified)** | ☑ N/A | no UI; no new classes, colors or typography introduced (reused `lead`, `<code>`, `<em>`, `<strong>`). |
| **UI: Responsiveness at target viewports** | ☑ N/A | no UI; no layout change. |

### Acceptance Criteria → proving test

| AC | Proven by | Observed |
|----|-----------|----------|
| AC1 no settings.json → install writes the kit file | `AC1: fresh install writes .claude/settings.json as a real file`, `AC1: fresh install wires every kit hook` | pass |
| AC2 existing settings + user permissions → kit hooks added, permissions unchanged | `SC1: user permissions.allow preserved`, `SC1: kit_one.py wired`, `SC1: kit_two.py wired` | pass |
| AC3 user's own hook entry survives install and update | `SC2: user hook entry survives install`, `SC2: user hook entry survives update` | pass |
| AC4 upstream adds an entry → update adds it | `SC3: upstream-added entry present after update` | pass |
| AC5 upstream removes a kit entry + file → removed; user entry never removed | `SC4: upstream-removed kit entry is gone`, `SC4: user entry still present after a kit removal`, `SC8: no command points at a missing hook file after an upstream removal` | pass |
| AC6 idempotent — second install/update byte-identical | `SC5: second install leaves settings.json byte-identical`, `SC5: second update leaves settings.json byte-identical` (`cmp -s`) | pass |
| AC7 invalid JSON → untouched, loud stderr with the block, exit 2, rest of the run finishes | `SC6: install exits 2 …`, `SC6: invalid settings.json left byte-identical`, `SC6: stderr names the file`, `SC6: stderr prints a "hooks" block`, `SC6: stderr prints the kit entries to add`, `SC6: the run still completed its other work (lock written)` | pass |
| AC8 no `python3` on PATH → same as AC7 | `SC7: install exits 2 when python3 is absent`, `SC7: settings.json left byte-identical …`, `SC7: stderr names python3 as the cause` | pass |
| AC9 mutation control M1 | mutant applied to the real `lib/merge-settings.py`; failure output pasted below | **observed failing** |
| SC8 every merged command references an existing file | `SC8: every kit command references an existing hook file (fresh install)` + the post-removal variant | pass |
| Edge cases | `edge: quoted $CLAUDE_PROJECT_DIR command matched by path`, `edge: empty/null event lists do not crash the merge`, `edge: non-ASCII preserved unescaped`, `edge: non-ASCII written as UTF-8, not \u escapes`, `edge: install exits 2 on a settings.json symlink`, `edge: the symlink itself was not replaced`, `edge: the symlink target was never written through`, `edge: atomic write leaves no temp-file residue`, `edge: an edited kit matcher is restored to upstream's value` | pass |

### Verification command output (2026-09-16T07:16:59Z)

```
=== 1 bash tests/test_settings_merge.sh ===
PASS: M1: mutant (skip adding entries) fails the SC1 assertion, as required

--- 39 passed, 0 failed ---
=== 2 bash tests/test_setup.sh ===

----- summary: 18 passed, 0 failed -----
=== 3 bash tests/test_update.sh ===

----- summary: 31 passed, 0 failed -----
=== 4 bash tests/test_install_update_smoke.sh ===
PASS: AC4: update.sh wrote nothing into the non-git target before rejecting it

9 passed, 0 failed
=== 5 shellcheck -x setup.sh update.sh ===
(no output, exit 0)
=== 6 python3 -m pytest .claude/hooks/tests/ -q ===
...                                                                      [100%]
795 passed in 14.54s
```

Full first-suite output:

```
PASS: SC1: setup.sh exits 0 over an existing settings.json
PASS: SC1: user permissions.allow preserved
PASS: SC1: kit_one.py wired
PASS: SC1: kit_two.py wired
PASS: SC2: user hook entry survives install
PASS: edge: non-ASCII preserved unescaped
PASS: edge: non-ASCII written as UTF-8, not \u escapes
PASS: edge: empty/null event lists do not crash the merge
PASS: edge: quoted $CLAUDE_PROJECT_DIR command matched by path
PASS: SC8: every kit command references an existing hook file (fresh install)
PASS: SC5: second install leaves settings.json byte-identical
PASS: edge: atomic write leaves no temp-file residue
PASS: SC3: update.sh exits 0
PASS: SC3: upstream-added entry present after update
PASS: SC2: user hook entry survives update
PASS: SC3: user permissions still untouched after update
PASS: SC5: second update leaves settings.json byte-identical
PASS: SC4: upstream-removed kit entry is gone
PASS: SC4: user entry still present after a kit removal
PASS: SC4: surviving kit entries still wired
PASS: SC8: no command points at a missing hook file after an upstream removal
PASS: SC6: install exits 2 on invalid settings.json
PASS: SC6: invalid settings.json left byte-identical
PASS: SC6: stderr names the file
PASS: SC6: stderr prints a "hooks" block
PASS: SC6: stderr prints the kit entries to add
PASS: SC6: the run still completed its other work (lock written)
PASS: SC7: install exits 2 when python3 is absent
PASS: SC7: settings.json left byte-identical when python3 is absent
PASS: SC7: stderr names the file
PASS: SC7: stderr prints a "hooks" block
PASS: SC7: stderr names python3 as the cause
PASS: edge: install exits 2 on a settings.json symlink
PASS: edge: the symlink itself was not replaced
PASS: edge: the symlink target was never written through
PASS: AC1: fresh install writes .claude/settings.json as a real file
PASS: AC1: fresh install wires every kit hook
PASS: edge: an edited kit matcher is restored to upstream's value
PASS: M1: mutant (skip adding entries) fails the SC1 assertion, as required

--- 39 passed, 0 failed ---
```

`shellcheck` is not on this machine's `PATH`; per `memory/learnings.md` ("shellcheck IS available here —
fetch the static binary") the official v0.10.0 static build was fetched into the session scratchpad and used:

```
$ shellcheck --version
ShellCheck - shell script analysis tool
version: 0.10.0

$ shellcheck -x setup.sh update.sh
shellcheck -x setup.sh update.sh => rc=0

$ SHELLCHECK=<scratchpad>/shellcheck bash tests/test_shellcheck_clean.sh
test_shellcheck_clean: PASS — exit 0, no output
```

### M1 mutation control — observed failure, not asserted

The mutation was applied to the **real** `lib/merge-settings.py` (not a copy), neutralising the
"append the kit entries the project is missing" step by replacing `return merged_groups` with
`return [g for g in project_groups if not is_kit_group(g)]`, then the suite was re-run:

```
M1 mutation applied to lib/merge-settings.py
=== running suite against the MUTATED source ===
FAIL: SC1: kit_one.py wired
FAIL: SC1: kit_two.py wired
FAIL: edge: quoted $CLAUDE_PROJECT_DIR command matched by path
FAIL: SC3: upstream-added entry present after update
FAIL: SC4: surviving kit entries still wired
FAIL: edge: an edited kit matcher is restored to upstream's value
```

The source was then restored from the scratchpad copy (**not** via `git checkout`, per
`memory/learnings.md` "Reverting a mutation with `git checkout` also reverts your fix") and the suite
re-run green:

```
$ grep -n "return merged_groups" lib/merge-settings.py
110:    return merged_groups
$ bash tests/test_settings_merge.sh | tail -3
PASS: M1: mutant (skip adding entries) fails the SC1 assertion, as required

--- 39 passed, 0 failed ---
```

The suite also carries M1 as a permanent, self-applying case (it mutates the fixture's copy of the
script and asserts the SC1 check then fails), so the control cannot silently rot.

### Documentation updated

**D1 — `site/index.html` `#update-flow` bullet list.** New third bullet, added verbatim:

> **`.claude/settings.json`** — not a `MANIFEST` file, so it is *merged* rather than copied: the
> kit's hooks are reconciled into it on install *and* on update, while your own permissions and your
> own hook entries are kept exactly as they are. If it cannot be merged — invalid JSON, a symlink, or
> no `python3` — nothing is written, the block to add by hand is printed, and the run exits `2`.

**D2 — `site/index.html` `#hooks` section.** Read first, as the guide required: the section described
what each hook does and named its event/matcher/script, but said **nothing at all** about how the
wiring reaches a project — it neither claimed hooks are wired only when `settings.json` is absent nor
implied a manual merge. So the "add one sentence" branch applied. New paragraph after the intro:

> The wiring lives in `.claude/settings.json`. Both `setup.sh` and `update.sh` merge every entry below
> into that file — including into one your project already has — and never touch your own permissions
> or hook entries. No manual merge step.

**D3 — `RUNBOOK.md` Common Failure Modes table.** New row, inserted above the "Merge blocked" row:

> | `setup.sh`/`update.sh` exits 2 and prints a `"hooks"` block | `.claude/settings.json` is invalid
> JSON or a symlink, or `python3` is not on `PATH` (every kit hook runs as `python3 …`) | Fix the JSON
> / replace the symlink with a real file / install `python3`, then re-run. The file is left
> byte-identical, so the printed block can also be pasted in by hand |

---

## Demonstration

**BEFORE** (Supervisor, 2026-09-12, `main` `8115bc9`, before any implementation commit). Repo pre-seeded with
`.claude/settings.json` = `{"permissions":{}}`, then `setup.sh </dev/null`:

```
settings.json now: {"permissions":{}}
```

No hooks wired, no message. Update probe (see T110 BEFORE): `settings.json: NOT updated`.

**AFTER** (same probe, 2026-09-16T07:18:29Z, `feat/t111-settings-merge` `d3d05c4`). Scratch git repo
pre-seeded with `.claude/settings.json` = `{"permissions":{}}`, then `setup.sh </dev/null`:

```
settings.json before: {"permissions":{}}
[info]  Merged Easy Kit hooks into ./.claude/settings.json (your permissions and your own hook entries are kept).
[info]  Setup complete. Harness copied into <scratch>/probe
--- settings.json after install ---
permissions: {}
kit hooks wired: 8
   python3 "$CLAUDE_PROJECT_DIR"/.claude/hooks/post_write_register_task.py
   python3 "$CLAUDE_PROJECT_DIR"/.claude/hooks/post_agent_move_to_review.py
   python3 "$CLAUDE_PROJECT_DIR"/.claude/hooks/post_bash_memory_update.py
   python3 "$CLAUDE_PROJECT_DIR"/.claude/hooks/post_tool_trace.py
   python3 "$CLAUDE_PROJECT_DIR"/.claude/hooks/pre_agent_validate_guide.py
   python3 "$CLAUDE_PROJECT_DIR"/.claude/hooks/pre_bash_block_unsafe_merge.py
   python3 "$CLAUDE_PROJECT_DIR"/.claude/hooks/pre_agent_step_limit.py
   python3 "$CLAUDE_PROJECT_DIR"/.claude/hooks/stop_review_reminder.py
```

All 8 hooks the kit ships are wired; `permissions` came back byte-identical.

Update half of the same probe — a user permission and a user hook entry (`echo mine`) were then added
by hand and `update.sh </dev/null` run, 2026-09-16T07:18:42Z:

```
[info]  Merged Easy Kit hooks into ./.claude/settings.json (your permissions and your own hook entries are kept).
[info]  Update complete. Re-recorded ./.claude/harness-lock.json
permissions: {"allow": ["Bash(ls:*)"]}
user entry kept: True
kit hooks: 8
idempotent (2nd update byte-identical):
  (unchanged vs pre-update too)

no dangling command:
  missing files referenced: []
```

**DELTA**: A project that already has a `.claude/settings.json` now actually receives all 8 kit hooks
— on install *and* on every update — without losing a single permission or hook of its own, and if the
file cannot be merged the installer says so loudly with the exact block to paste instead of silently
doing nothing.

**WITNESS**: Common-Infrastructure-Agent (implementer), 2026-09-16T07:18:29Z–07:18:42Z, on
`feat/t111-settings-merge` `d3d05c4`, in a scratch git repo outside the worktree. **Not an independent
witness** — the implementer ran its own probe. Stage 4/5 must re-run it (the commands are reproduced
above verbatim) before this row counts as confirmed.

---

## Stage 4 Review (Supervisor, 2026-09-16)

**code-review**: P0 0 / P1 0 / P2 1 / P3 0. **security-review**: no findings at confidence >= 8.

Reachability (Phase 0.5): guide declares `install_settings` in `setup.sh` + a settings step in
`update.sh` `main`. Both present and called. Pass.

### P2-1 — `write_atomic` silently changed the file's permission bits (FIXED, `bff80cf`)

`tempfile.mkstemp` creates 0600 and `os.replace` carries that mode onto the destination, so a
project's 0644 `settings.json` came back 0600 — content preserved exactly, mode not, contradicting
the module's own "keeps everything the user added" contract. Verified by running it, not inferred:

```
mode BEFORE: 644
rc=0
mode AFTER:  600
```

git tracks only the exec bit, so this would never have appeared in a user's diff. Fixed by stating
the destination before the write and chmodding the temp file before `os.replace`; a new suite case
seeds the fixture at 644 and asserts the mode afterwards. **Observed failing** against a mutated
source with the `os.chmod` line removed:

```
FAIL: edge: atomic write changed the file mode 644 -> 600
--- 39 passed, 1 failed ---
```

Source restored from a scratchpad copy, not `git checkout` (which would have reverted the fix too),
then green: 40/40.

### Security review — no findings

The change writes the file that decides which commands run, so the question is whether untrusted
input can reach a `command` string. It cannot: `merge_event_groups` only ever appends objects taken
from the upstream file or preserves the project's own non-kit entries by reference — it never
constructs, concatenates or templates a command. Traversal through `HOOK_PATH_RE`
(`.claude/hooks/../../../etc/evil.py`) is fail-safe: matching only classifies an entry as kit-owned,
which means it is reconciled against upstream and therefore **dropped** when upstream ships no
matching key. Traversal makes a hostile entry more likely to be deleted, never executed — the
inverse of T110's finding, where a lock value became a source path that was copied. `write_atomic`
uses `mkstemp` in the destination directory then `os.replace`, which replaces a symlink rather than
writing through it. The shell side is fully quoted with no user-derived words.

Recorded as intended, not a defect: an edited kit entry is restored to upstream's version, so a user
who deliberately neutered a kit hook gets it back on update. That is the guide's ownership rule, now
documented in the site copy this task added.

### Carried to a later task (not a finding against T111)

`merge_settings` + `settings_merge_refused` are duplicated ~35 lines verbatim across `setup.sh` and
`update.sh`. The agent was following the guide's "Files Must NOT Touch" rule on
`lib/harness-fetch.sh` (T112/T113 edit there). Fold into a shared helper after those land.

### Post-fix verification (Supervisor, 2026-09-16)

```
tests/test_settings_merge.sh        40 passed, 0 failed
tests/test_setup.sh                 18 passed, 0 failed
tests/test_update.sh                31 passed, 0 failed
tests/test_install_update_smoke.sh   9 passed, 0 failed
python3 -m pytest .claude/hooks/tests/ -q      795 passed
```

`shellcheck -x setup.sh update.sh`: not re-run — `git diff --name-only 24bcdc6 -- setup.sh update.sh`
is empty, so the agent's clean result covers the current bytes of both scripts.
