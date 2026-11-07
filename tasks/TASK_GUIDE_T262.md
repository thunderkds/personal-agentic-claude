# TASK_GUIDE — T262: Native Windows support, step 1 — decision record and LF line endings
**Date**: 2026-11-06
**Complexity Level**: C1
**Risk Level**: Low
**Priority**: P1
**Assigned agent**: common-infrastructure
**Agent guide**: `agents/common-infrastructure.md`

---

## Mandatory Startup (Do Not Skip)

Before writing any code:
1. Read `PROJECT_SPEC.md`
2. Read the memory slice in your spawn prompt (`<!-- memory-slice -->`). Read `memory/MEMORY.md` in full only if your work reaches a file, hook, skill or decision the slice does not cover
3. Read this file completely
4. Read `agents/common-infrastructure.md`
5. Note the **Complexity Level** above and apply the matching process from the Complexity matrix in `agents/common-infrastructure.md`
6. Read `docs/windows-support-plan.md` (the whole plan; this task is T-W1 of it)

---

## Requirement (Pillar 1 — Adapt the requirement)

User, 2026-11-06: "making plan to make this kit support window also [auto]", then "by pass the wsl, focus on the native window", then "as you recommend" (installer = PowerShell port).

**Restated intent** (Supervisor's interpretation, in the project's domain language):
> Record the native-Windows design as one ADR, and make a Windows checkout keep LF line endings so the shell scripts and hooks still run. No installer, hook or test code changes in this task.

**Out of scope** (what this task explicitly does NOT do):
- Any change to `setup.sh`, `update.sh`, `lib/*.sh`, `.claude/hooks/*.py` or `scripts/*.py` (those are T263..T268).
- The Windows CI job (T263).
- WSL2 documentation or detection (dropped by the user).

**Requirement Refs**: `docs/windows-support-plan.md` rows 1-10 and task T-W1. No `PRD.md` exists in this repo.

### Requirement Fidelity Gate (sign off BEFORE implementation)

- [x] Restated intent confirmed to match the user's request (Supervisor, 2026-11-06)
- [x] Domain terms align with `PROJECT_SPEC.md` glossary
- [x] Every Acceptance Criterion below traces to a line in the Requirement
- [x] All Requirement Refs exist

> An agent must NOT start implementing until this gate is checked. If anything here is unclear,
> STOP and ask the Supervisor (Karpathy: Think Before Coding).

---

## Dependencies & Reachability

**Depends on**: `None`

**Entry point**: `Standalone — N/A: a decision record and a git attribute file; nothing in the repo calls them by name. Git reads .gitattributes on checkout.`

---

## Acceptance Criteria

| # | Criterion (testable) | Traces to requirement |
|---|----------------------|-----------------------|
| 1 | `docs/adr/0003-native-windows-support.md` exists, copied from `templates/ADR_template.md`, and records: native Windows only (no WSL2), PowerShell as the shell target, `py -3` / `python` as the launcher, the installer language (PowerShell port, `setup.sh` untouched, parity test), and the symlink fallback | "Decision record (ADR)" |
| 2 | The ADR records the symlink fallback as decided: directory junction first, else a copy plus a drift check that `update` re-runs. It names the source: the user's default (the Supervisor offered it on 2026-11-06 and the user went on without changing it). No Debate: the task is Risk Low | plan "symlink fallback" |
| 3 | `.gitattributes` exists at the repo root and `git check-attr eol -- setup.sh .claude/hooks/post_tool_trace.py skills/git-guardrails-claude-code/scripts/block-dangerous-git.sh` prints `eol: lf` for all three | "keeps LF line endings (fixes row 10)" |
| 4 | Negative: binary files (`*.png`, `*.jpg`, `*.ico`, `*.woff2`) are marked `binary`, so git does not rewrite them | row 10 side effect |
| 5 | `git ls-files --eol` shows no tracked text file with `i/crlf` that was `i/lf` before this task (the attribute file does not change the index) | Surgical Changes |

---

## Evaluation & Acceptance (How we know the agent worked correctly)

### Success Criteria (observable, pass/fail)

| # | Given (input/state) | Expect (output/behavior) | How it's checked |
|---|---------------------|--------------------------|------------------|
| 1 | The finished branch | `git check-attr eol` prints `eol: lf` for the three paths in AC 3 | automated test |
| 2 | A `*.png` path | `git check-attr binary` prints `binary: set` | automated test |
| 3 | The ADR file | Contains the five decisions of AC 1, each under its own heading, and no `TODO` | automated test (grep) |
| 4 | `.gitattributes` with the `eol=lf` rule deleted | The test of row 1 goes red | mutation control |

### Verification Command (exact, runnable)

```bash
python3 -m pytest tests/test_windows_gitattributes.py -q
```

---

## Approach

**Pattern reference**: `docs/adr/0002-one-confirmed-menu-driven-installer.md` (ADR shape) and `tests/test_repo_name.py` (a small repo-fact test).

**Vital slice**: the ADR plus the three-line `.gitattributes`. Both are needed before any Windows code starts.
**Cut list**: `.editorconfig` (no request); converting existing files to LF (the index is already LF); a CRLF test on a real Windows runner (that is T263).

Order: write the failing test, write the ADR (symlink fallback as in AC 2), add `.gitattributes`, run the test.

`.gitattributes` content (starting point):

```
* text=auto eol=lf
*.sh text eol=lf
*.py text eol=lf
*.png binary
*.jpg binary
*.ico binary
*.woff2 binary
```

---

## Edge Case Checklist

- [ ] A `.gitattributes` already exists at the root: extend it, do not overwrite it
- [ ] `plugin/` holds symlinks: `.gitattributes` must not change how git stores them
- [ ] `.ps1` files do not exist yet; do not add rules for them (T268 adds them)
- [ ] Pin-test pre-flight: the `Pre-existing pin tests` row below is filled before work starts
- [ ] Stale references: grep `README.md`, `site/`, `docs/claude-md/folder-structure.md` for "Windows", "WSL" and a root-file list that the new `.gitattributes` or ADR should join

---

## Files to Change (Predicted)

| File | Change |
|------|--------|
| `docs/adr/0003-native-windows-support.md` | New ADR |
| `.gitattributes` | New (or extended) |
| `tests/test_windows_gitattributes.py` | New test, includes the mutation control of Success Criterion 4 |
| `MANIFEST` | Add the new files only if the manifest lists root dotfiles or `docs/adr/` (check first) |
| Pre-existing pin tests | Grep `tests/` and `.claude/hooks/tests/` for a file-list or root-listing pin (`test_manifest_exclusions.sh`, `test_readme_current.sh`, memory budget tests) and handle each: repoint, narrow or escalate |

## Files Must NOT Touch

| File | Reason |
|------|--------|
| `setup.sh`, `update.sh`, `lib/*.sh` | Installer work is T268 |
| `.claude/hooks/*`, `scripts/*.py` | Hook work is T264..T267 |
| `.claude/settings.json` | Hook launcher is T266 |

---

## Test Plan

`tests/test_windows_gitattributes.py` runs `git check-attr` through `subprocess` (no shell) on the paths in the Success Criteria, and greps the ADR for the five decision headings. A mutation control copies the repo's `.gitattributes` to a temp dir, deletes the `eol=lf` line, and asserts the check goes red.

---

## Completion Checklist

- [ ] Implementation done
- [ ] Self-review: `Skill({ skill: "code-review" })` run
- [ ] Lint passes
