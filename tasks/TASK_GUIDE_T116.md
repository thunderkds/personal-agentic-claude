# TASK_GUIDE — T116: Every pack ships as a dormant catalog; the broken install-time pack installer is removed
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
1. Read `PROJECT_SPEC.md` (glossary: "Pack catalog", "Activated pack")
2. Read `memory/MEMORY.md`
3. Read this file completely
4. Read `agents/common-infrastructure.md`
5. Note the **Complexity Level** above and apply the matching process from the Complexity matrix in your role guide
6. Read `memory/codebase-map.md` (C2, multi-file)
7. Read `docs/adr/0002-one-confirmed-menu-driven-installer.md` ("Packs: a dormant catalog")

---

## Requirement (Pillar 1 — Adapt the requirement)

Probe, 2026-09-12, `main` `8115bc9`: `--pack=mobile`, and the interactive menu answered `1, 5`, both printed

```
[warn]  Pack 'mobile' not found in central clone (…/home/.supervisor/packs/mobile) — skipping.
[warn]  Pack 'api' not found in central clone (…/home/.supervisor/packs/api) — skipping.
[info]  Packs requested: mobile api
```

and installed nothing. `install_pack` (`setup.sh:327`) reads `$SUPERVISOR_PATH/packs`, the central clone
ADR-0001 removed; ADR-0001 deferred packs and no follow-up ever ran. User decision, 2026-09-12: packs are
**not chosen at install** — "the packs should be identified from the biz domain … Agent will analyze and
suggest the good packs" — and the catalog ships with the project.

**Restated intent**:
> Every Easy Kit project receives all packs as an inactive catalog that no CLI loads, update keeps that
> catalog current, and the installer no longer asks about, or pretends to install, packs.

**Out of scope**:
- Recommending or activating packs — T117 (`select-packs`).
- Changing any pack's content.
- `packs/*/PACK.md` "Installed via `setup.sh --pack`" wording — T117.

**Requirement Refs**: none in `PRD.md`; authority ADR-0002.

### Requirement Fidelity Gate (sign off BEFORE implementation)

- [x] Restated intent confirmed (Supervisor; user's words quoted)
- [x] Domain terms align with glossary ("Pack catalog", "Activated pack")
- [x] Every Acceptance Criterion traces to the Requirement
- [x] No `PRD.md` refs claimed

---

## Dependencies & Reachability

**Depends on**: T115 — both tasks rewrite `setup.sh`'s argument and prompt handling; serialised to avoid a known conflict (`memory/learnings.md`: don't spawn in parallel onto a known-open race)

**Entry point**: `MANIFEST` line `packs`

---

## Acceptance Criteria

| # | Criterion (testable) | Traces to requirement |
|---|----------------------|-----------------------|
| 1 | Fresh install → `packs/<name>/` present for all 5 packs, byte-identical to the kit's; lock records their hashes | "receives all packs as an inactive catalog" |
| 2 | No CLI loads the catalog: `.claude/skills/` and `.claude/agents/` (Claude) and `.codex/skills/` (Codex) contain **no** pack skill or agent name after install and after update | "no CLI loads" |
| 3 | Upstream changes a pack file → update refreshes it through the hash-lock rule (unedited → silent, edited → conflict) | "update keeps that catalog current" |
| 4 | The installer never asks about packs, and no output line claims packs were requested or installed; one info line says the catalog is available and that the Supervisor recommends packs for the project | "no longer asks about, or pretends to install, packs" |
| 5 | Deleted: `prompt_packs`, `resolve_pack_choices`, `install_pack`, `install_abs`, `SUPERVISOR_PATH`, `USE_COPY`, `PACKS` | ADR-0002 "Removed" |
| 6 | `tests/test_pack_choice_parsing.sh` (T108) retired, and its CI step and drift-test entry removed together; the review file records why (the parser no longer exists) | retire tests with their feature |
| 7 | `MANIFEST` `packs` line carries **no** `<harness>=<dest>` pair | catalog is never projected |
| 8 | Mutation control M1: add `codex=.codex/packs` to the line → AC2 test fails; M2: delete the `packs` line → AC1 test fails | observed failing |

---

## Evaluation & Acceptance (How we know the agent worked correctly)

### Success Criteria (observable, pass/fail)

| # | Given (input/state) | Expect (output/behavior) | How it's checked |
|---|---------------------|--------------------------|------------------|
| 1 | empty repo, install (Claude + Codex via pty) | `packs/{ai-agent,api,data,devops,mobile}/PACK.md` exist; `diff -r` vs kit `packs` clean | automated |
| 2 | same repo | none of `mobile-developer`, `ui-accessibility`, `pipeline-safety`, … (read names from `packs/*/agents`, `packs/*/skills` at test time) under `.claude/skills`, `.claude/agents`, `.codex/skills` | automated |
| 3 | upstream edits `packs/api/PACK.md`; update | project file updated | automated |
| 4 | install output | contains no `Pack '` / `Packs requested`; contains the catalog line | automated |
| 5 | `grep -nE 'install_pack|SUPERVISOR_PATH|USE_COPY|prompt_packs' setup.sh update.sh lib/*.sh` | no matches | automated test (use `command grep`) |

### Verification Command (exact, runnable)

```bash
bash tests/test_pack_catalog.sh
bash tests/test_setup.sh
bash tests/test_update.sh
bash tests/test_install_update_smoke.sh
bash tests/test_harness_projection.sh
bash tests/test_cli_and_project_menus.sh
python3 -m pytest .claude/hooks/tests/ tests/ -q
shellcheck -x setup.sh update.sh lib/harness-update.sh
```

### Evidence (filled by reviewer at Stage 4/5)

> Filled by the reviewer at Stage 4/5 in `tasks/TASK_REVIEW_T116.md`.

---

## Demonstration

> See `tasks/TASK_REVIEW_T116.md`.

---

## Approach

**Pattern reference**: `MANIFEST` itself — `templates` and `docs/claude-md` are shipped as plain directories
with no destination pair and are never discovered by any CLI. The catalog is exactly that shape.

**Vital slice**: one MANIFEST line plus the deletions.
**Cut list**:
- A catalog index file — each `PACK.md` already carries "When to use"; T117 reads them directly.
- Shipping only chosen packs — user chose the full catalog (~200 KB).

---

## Edge Case Checklist

- [ ] A project that previously ran `--pack=` got nothing (probe), so there is no pack migration — confirm no `.claude/agents/*` symlink into `~/.supervisor` is created or expected anywhere
- [ ] `detect_symlinks` must not trip over `packs/` in a project that has an unrelated `packs` symlink — it will refuse; that is the existing, correct behaviour for MANIFEST paths — state it in the review
- [ ] A user's own pre-existing `packs/` directory → T112 backup rule applies at install
- [ ] Removing a pack upstream later → T113 orphan rule removes the unedited catalog copy (no extra code)
- [ ] `tests/test_site_content.py` / site rosters mention packs — keep passing

---

## Files to Change (Predicted)

| File | Change |
|------|--------|
| `MANIFEST` | Add `packs` (no destination pair) |
| `setup.sh` | Delete pack menu/installer code and variables; add the catalog info line |
| `tests/test_pack_catalog.sh` | New — SC1–SC5 + M1/M2 |
| `tests/test_pack_choice_parsing.sh` | Delete |
| `.github/workflows/ci.yml`, `tests/test_ci_wires_shell_suites.py` | Remove the retired suite; add the new one |

## Files Must NOT Touch

| File | Reason |
|------|--------|
| `packs/**` content | Pack content unchanged |
| `packs/*/PACK.md`, `templates/PACK_template.md`, `docs/claude-md/folder-structure.md`, `CLAUDE.md`, `CLAUDE_LEGACY.md` | Pack doctrine wording — T117 |
| `skills/**`, `agents/**` | No activation here |

---

## Test Plan

BEFORE: the probe transcript above (already captured, pasted in the review file). Then
`tests/test_pack_catalog.sh` with SC1–SC5 + mutation controls; retired suite removed from CI and drift test
in the same commit; all suites green.

---

## Completion Checklist

- [ ] Implementation done
- [ ] Self-review: `Skill({ skill: "code-review" })` run (Supervisor)
- [ ] Security review: `Skill({ skill: "security-review" })` run (Medium risk)
- [ ] `shellcheck` clean
- [ ] Tests written AND pass — output pasted into `tasks/TASK_REVIEW_T116.md` (Hard-Stop Gate 5)
- [ ] `/verify` — user-invoked
- [ ] Learnings flagged to the Supervisor
- [ ] Supervisor notified: task ready for Stage 4 review
