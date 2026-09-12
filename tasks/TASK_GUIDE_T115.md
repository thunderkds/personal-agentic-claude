# TASK_GUIDE — T115: Choose CLIs and project type from a list — every install flag is gone, and the docs show one line
**Date**: 2026-09-12
**Complexity Level**: C2 (Hard-Stop Gate 2 floor: installer restructure)
**Risk Level**: Medium
**Priority**: P1
**Type**: HITL — the user reviews the menu transcript and the new install section before Done
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
7. Read `docs/adr/0002-one-confirmed-menu-driven-installer.md` (menus 2 and 3; user-facing terms)

---

## Requirement (Pillar 1 — Adapt the requirement)

User, 2026-09-12: "the options should be the choose from user from the list, not like the way user must
remember the param and they push in the initialize."

Today users must know `--harness <name>` (repeatable), `--harness=<name>`, the no-op `--copy`, `--pack=<name>`
(which rejects `--pack mobile`), and the `sh -c "$(curl …)" -- --harness codex` form just to pass any of them
(`README.md:41-48`, `site/index.html:247-256`). The README is also 83 lines against its own 75-line cap —
`tests/test_readme_slim.py` is red on `main` today.

**Restated intent**:
> The one command takes no options. On install or reinstall the user picks which CLIs to set up and whether
> the project is new or existing from numbered lists; everything the docs tell a user to type is a single
> line.

**Out of scope**:
- Pack flags' *pack* behaviour — `--pack=` parsing is removed here as a flag; `prompt_packs`, `install_pack`
  and the pack catalog are T116.
- `packs/*/PACK.md` and `docs/claude-md/folder-structure.md` pack wording — T117.
- Renaming `harness-lock.json`, `lib/harness-fetch.sh` or any internal identifier (ADR-0002: not renamed).

**Requirement Refs**: none in `PRD.md`; authority ADR-0002 (menus 2–3, "Removed", user-facing terms).

### Requirement Fidelity Gate (sign off BEFORE implementation)

- [x] Restated intent confirmed (Supervisor; user's words quoted)
- [x] Domain terms align with glossary — "CLI", "Easy Kit" to users; "harness" internal only
- [x] Every Acceptance Criterion traces to the Requirement
- [x] No `PRD.md` refs claimed

---

## Dependencies & Reachability

**Depends on**: T114 — the action menu, plan screen and `/dev/tty` reader exist

**Entry point**: `setup.sh` `main` → install/reinstall path → CLI menu

---

## Acceptance Criteria

| # | Criterion (testable) | Traces to requirement |
|---|----------------------|-----------------------|
| 1 | Install/reinstall shows `Which CLIs should Easy Kit set up?` with `1) Claude Code  2) Codex`; a CLI found on `PATH` (`command -v claude` / `codex`) is pre-selected; if neither is found, Claude Code is pre-selected; Enter accepts | "picks which CLIs … from numbered lists" |
| 2 | Input `1 2`, `1,2` and `2` select exactly those CLIs; empty selection after the user clears it → "pick at least one" + re-prompt; invalid number → re-prompt | forgiving list input (T108's comma lesson) |
| 3 | Project-type menu `1) New project  2) Existing / legacy project` replaces today's greenfield/brownfield wording; default `1` | "whether the project is new or existing" |
| 4 | The plan screen (T114) shows the chosen CLIs and project type before `Proceed?` | confirm before acting |
| 5 | Update does **not** show menus 2–3; it re-derives CLIs from what is present (DDR-0007 presence rule, unchanged) | ADR-0002 menu scope |
| 6 | Any command-line argument → exit 1 before any write, message: Easy Kit takes no options, run it and choose from the menus; names the old flag it saw | "not … params the user must remember" |
| 7 | No-TTY run uses the defaults from AC1/AC3 and prints them | ADR-0002 no-TTY rule |
| 8 | `--harness`, `--harness=`, `--copy`, `--pack=` parsing is deleted, and no user-facing string in `setup.sh`, `update.sh`, `lib/*.sh` output contains the word `harness` (grep of `log_*`/`printf` string literals) | ADR-0002 "Removed" + terminology |
| 9 | `README.md`, `site/index.html`, `RUNBOOK.md`, `AGENTS.md` show exactly one install/update command (`curl -fsSL …/setup.sh \| sh`), no flag forms, and describe the menus in user terms | "the docs show one line" |
| 10 | `tests/test_readme_slim.py` passes **without** raising its 75-line cap | the pre-existing red |
| 11 | `tests/test_pack_docs_flags.py` (asserts `--pack=` docs match the flag parser) is retired with a one-line reason recorded in the review file, or rewritten to assert no flag is documented — agent's choice, justified | the flag it guards no longer exists |
| 12 | Every installer suite passes; tests that passed `--harness codex` now select Codex through the pty menu; no assertion weakened | regression |
| 13 | Mutation control M1: re-add `--harness` acceptance → AC6 test fails | observed failing |

---

## Evaluation & Acceptance (How we know the agent worked correctly)

### Success Criteria (observable, pass/fail)

| # | Given (input/state) | Expect (output/behavior) | How it's checked |
|---|---------------------|--------------------------|------------------|
| 1 | empty repo, PATH has fake `codex` only, pty `⏎ ⏎ ⏎ Y` | Codex projected; no `.claude/skills` link | automated (pty) |
| 2 | empty repo, pty CLI answer `1,2` | both CLIs set up | automated (pty) |
| 3 | empty repo, pty project type `2` | `CLAUDE.md` first line = `CLAUDE_LEGACY.md` first line | automated (pty) |
| 4 | `sh setup.sh --harness codex` | exit 1; message names `--harness`; `git status --porcelain` empty | automated |
| 5 | installed Codex-only repo, Update via pty | no CLI menu shown; Codex re-projected | automated (pty) |
| 6 | `setsid sh setup.sh </dev/null` in empty repo | prints "Claude Code" and "New project" defaults | automated |
| 7 | `python3 -m pytest tests/test_readme_slim.py tests/test_site_content.py -q` | pass | automated |
| 8 | grep user-facing strings for `harness` | no match | automated test |

### Verification Command (exact, runnable)

```bash
bash tests/test_cli_and_project_menus.sh
bash tests/test_one_command_menu.sh
bash tests/test_harness_projection.sh
bash tests/test_t098_harness_presence.sh
bash tests/test_setup.sh
bash tests/test_update.sh
bash tests/test_install_update_smoke.sh
python3 -m pytest .claude/hooks/tests/ tests/ -q
shellcheck -x setup.sh update.sh lib/harness-update.sh
```

### Evidence (filled by reviewer at Stage 4/5)

> Filled by the reviewer at Stage 4/5 in `tasks/TASK_REVIEW_T115.md`. **HITL**: paste SC1 transcript and the
> new README install section for the user's review.

---

## Demonstration

> See `tasks/TASK_REVIEW_T115.md`.

---

## Approach

**Pattern reference**: T114's action menu + `/dev/tty` reader (same file, merged before this task) for the
menus; `resolve_pack_choices` (`setup.sh:187`) for comma-tolerant number parsing — reuse its normalisation
idea for the CLI multi-pick before T116 deletes it.

**Vital slice**: the CLI multi-pick menu, the no-arguments rule, and the one-line docs.
**Cut list**:
- Detecting CLI versions or auth status — presence on `PATH` only.
- A third CLI — `VALID_HARNESSES` stays `claude codex` (N=2 by decision, DDR-0006 follow-up).
- Reworking the site's page structure — edit the install/update sections in place.

---

## Edge Case Checklist

- [ ] `claude` on PATH but the user deselects it → Claude not installed; Codex-only presence rule then holds on update
- [ ] Deselecting a CLI on **Reinstall** that was previously present → its projection/link is left alone or removed? Decide, state it on the plan screen, and test it — never silently orphan
- [ ] `command -v` returning an alias/function in the user's shell — the script runs in `sh`, so only real executables count; fine, but test with a fake executable on a temp `PATH`
- [ ] Site HTML still passes `tests/test_site_content.py` roster assertions
- [ ] `SUPERVISOR_REPO` remains an undocumented dev/test seam — not mentioned in README/site
- [ ] `memory/learnings.md`: ugrep wraps `grep` in this environment — use `command grep` in any grep-based test

---

## Files to Change (Predicted)

| File | Change |
|------|--------|
| `setup.sh` | CLI + project-type menus; remove flag parsing; no-arguments rule |
| `tests/test_cli_and_project_menus.sh` | New — SC1–SC8 + M1 |
| `tests/test_harness_projection.sh`, `tests/test_t098_harness_presence.sh`, `tests/test_setup.sh` | Select CLIs via pty instead of `--harness` |
| `tests/test_pack_docs_flags.py` | Retire or rewrite (AC11) |
| `README.md`, `site/index.html`, `RUNBOOK.md`, `AGENTS.md` | One-line install/update; menu description; README ≤ 75 lines |
| `.github/workflows/ci.yml` | Add new suite step |

## Files Must NOT Touch

| File | Reason |
|------|--------|
| `prompt_packs`, `resolve_pack_choices`, `install_pack`, `install_abs` | T116 |
| `packs/**`, `templates/PACK_template.md`, `docs/claude-md/folder-structure.md` | T117 |
| `tests/test_readme_slim.py` cap value | Must pass by shrinking the README, not by raising the cap |
| `lib/harness-update.sh` update internals | T114-owned |

---

## Test Plan

BEFORE: `sh setup.sh --harness codex` accepted and the README test red, captured before the first commit.
Then `tests/test_cli_and_project_menus.sh`; convert flag-driven suites to pty menus with identical assertions;
full pytest and shell suites green.

---

## Completion Checklist

- [ ] Implementation done
- [ ] Self-review: `Skill({ skill: "code-review" })` run (Supervisor)
- [ ] Security review: `Skill({ skill: "security-review" })` run (Medium risk)
- [ ] `shellcheck` clean
- [ ] Tests written AND pass — output pasted into `tasks/TASK_REVIEW_T115.md` (Hard-Stop Gate 5)
- [ ] HITL: user approved menu transcript + README install section
- [ ] `/verify` — user-invoked
- [ ] Learnings flagged to the Supervisor
- [ ] Supervisor notified: task ready for Stage 4 review
