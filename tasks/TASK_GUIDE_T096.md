# TASK_GUIDE — T096 (B1): Relocate canonical `skills/` and `agents/` to plain root, without touching the 1,764-reference audit trail
**Date**: 2026-08-27
**Complexity Level**: C2
**Risk Level**: Medium
**Priority**: P1
**Assigned agent**: Common-Infrastructure-Agent
**Agent guide**: `.claude/agents/common-infrastructure.md`

---

## Mandatory Startup (Do Not Skip)

Before writing any code:
1. Read `PROJECT_SPEC.md`
2. Read `memory/MEMORY.md`
3. Read this file completely
4. Read `.claude/agents/common-infrastructure.md`
5. C2 task, multi-file: read `memory/codebase-map.md`
6. Read `docs/ddr/0007-canonical-skills-and-agents-at-plain-root.md` **in full**. It is the decision
   this task implements, and it contains the prohibition that defines the task's boundary.
7. Read `docs/adr/0001-direct-repo-install-no-central-clone.md` — it governs why downstream installs
   copy, and why this repo's symlink is a deliberate *exception* rather than a contradiction.

---

## Requirement (Pillar 1 — Adapt the requirement)

User request, 2026-08-27:

> "go with option B" … "generate plan for now, I will implement later"

Selected in `docs/brainstorming/BRAINSTORMING_LOG_harness-kit-portability.md`, decided in `DDR-0007`. This is **B1**,
the relocation half. B2 (`T097`) adds the per-harness projection and must not be started until B1 is
green.

**Restated intent**:
> Move the kit's portable assets out of the Claude-branded directory and into plain root, so that no
> harness is structurally privileged, while leaving the project's historical record exactly as it is
> and keeping this repo able to run its own skills at every point.

### What moves

| From | To |
|---|---|
| `.claude/skills/` | `skills/` |
| `.claude/agents/` | `agents/` |

`.claude/skills` and `.claude/agents` are then re-created as **committed symlinks** pointing at
`../skills` and `../agents` (relative, never absolute — see Out of scope).

### What does not move

- `.claude/hooks/` — Claude-only by nature. `wshobson/agents` records that lifecycle hooks port only
  to OpenCode and Antigravity. Relocating them buys portability nothing and costs 55 rewrites.
- `.claude/settings.json` — already deployed as a per-project copy outside `MANIFEST`.
- `templates/`, `docs/claude-md/` — already outside `.claude/`.

### The prohibition (read this before your first edit)

Counted 2026-08-27, `.claude/skills` + `.claude/agents` references across the repo:

| Class | Refs | Files | Treatment |
|---|---|---|---|
| **Live surface** | **225** | **49** | rewrite |
| **Historical audit trail** | **1,764** | — | **must not be touched** |

> **Correction (Stage 4, T096).** The 1,764 figure was measured against a different tree state
> and is stale. The real BEFORE count on this branch is **909**. AC4's *intent* — the historical
> trail is unchanged by the move — is unaffected and was verified against 909. See defect **D2** in
> `tasks/TASK_REVIEW_T096.md` for the per-directory breakdown.

The historical class is `memory/` (1013), `tasks/` (707), `PROJECT_KANBAN.md` (22), `reports/` (18),
`docs/ddr/` + `docs/adr/` (4), and every `BRAINSTORMING_LOG_*.md` (3). Those references record what
was true *at the time they were written*. Rewriting them falsifies the record this project runs on.

**A repo-wide `sed`/`xargs`/`find -exec` rewrite is forbidden.** Not discouraged — forbidden. No test
in this repo would catch the corruption: the suite asserts live behaviour, not whether
`memory/decisions.md` still says what happened. The damage would surface months later, unrecoverable
without archaeology. Rewrite only the 49 files enumerated below, and prove the historical count is
unchanged afterwards (AC4).

`memory/codebase-map.md` (39 refs) is the one exception inside the historical class: it is generated.
**Regenerate it with `/map-codebase` after the move — do not hand-edit it.**

### The exhaustive live file list (49)

`AGENTS.md` · `CLAUDE.md` · `CLAUDE_LEGACY.md` · `MANIFEST` · `setup.sh` · `.cursor/rules/agent-base.mdc`

`.claude/agents/`: `backend.md`, `common-infrastructure.md`, `frontend.md`, `general-agent-template.md`, `qa.md`

`.claude/hooks/`: `lib/guide_sections.py`, `tests/test_agent_guide_dedup.py`, `tests/test_bugfix_evidence_parity.py`, `tests/test_complexity_matrix_pointers.py`, `tests/test_diagnose_evidence_loop.py`, `tests/test_memory_channel_and_budget.py`, `tests/test_post_write_register_task_metadata.py`, `tests/test_post_write_register_task.py`, `tests/test_skill_reference_pointers.py`, `tests/test_skill_spec_conformance.py`, `tests/test_task_context.py`, `tests/test_vital_slice.py`

`.claude/skills/`: `craft-agent/SKILL.md`, `craft-spawn-prompt/SKILL.md`, `delivery-report/render.py`, `delivery-report/SKILL.md`, `git-guardrails-claude-code/SKILL.md`, `learn/SKILL.md`, `slim-skills/SKILL.md`, `teach/SKILL.md`, `write-better-skill/references/descriptions.md`, `write-better-skill/SKILL.md`

`docs/claude-md/`: `folder-structure.md`, `pipeline-stages.md`, `untrusted-content-boundary.md`

`scripts/`: `measure_agent_guide_tokens.py`, `smoke-install.sh`, `test-agent-template.sh`, `test-claude-md-refs.sh`, `validate.sh`

`templates/`: `SKILL_template.md`, `TASK_GUIDE_template.md`

`tests/`: `test_harness_fetch.sh`, `test_install_update_smoke.sh`, `test_provider_adapters.py`, `test_setup.sh`, `test_site_content.py`, `test_update.sh`

Re-derive this list at implementation time rather than trusting it blindly — the repo may have moved.
The derivation command is in Success Criteria #1. If your count differs from 49, **stop and report**;
a changed count means the scope changed.

**Out of scope**:
- Absolute symlink targets. `.claude/skills -> ../skills`, relative. An absolute target breaks Stage
  3: every sub-agent works in a worktree (`CLAUDE.md:85`), and a baked absolute link either is absent
  there or points back at the main checkout, letting agents read skills from outside their isolation
  boundary. `DDR-0007` rejects this explicitly.
- Any per-harness projection, `--harness` flag, `.codex/` directory, or `AGENTS.md` content
  correction — all of that is `T097` (B2). B1 changes only where files live.
- Relocating `.claude/hooks/` or `.claude/settings.json`.
- Renaming, splitting, merging, or editing the *content* of any skill or agent guide. This task moves
  files and rewrites path strings. If a skill's prose is wrong, that is a different task.
- `packs/` and `install_pack()` — `ADR-0001` left them out of scope and `DDR-0007` defers them again.

**Requirement Refs**: `DDR-0007` (Decision section) · `docs/brainstorming/BRAINSTORMING_LOG_harness-kit-portability.md`
(Option B, Surgical Scope)

### Requirement Fidelity Gate (sign off BEFORE implementation)

- [x] Restated intent confirmed to match the user's selection (Supervisor, 2026-08-27)
- [x] Domain terms align with `PROJECT_SPEC.md` — "canon", "projection", "live surface", "audit trail"
- [x] Every Acceptance Criterion below traces to a line in the Requirement or to `DDR-0007`
- [x] Requirement Refs resolve: `DDR-0007` exists on disk

---

## Dependencies & Reachability

**Depends on**: `None` (`DDR-0007` is a decision, already Accepted)

**Blocks**: `T097` (B2) — projection needs canon in its final location first.

**Entry point**: `python3 -m pytest .claude/hooks/tests/ -q && python3 -m pytest tests/ -q && bash scripts/validate.sh`

---

## Acceptance Criteria

| # | Criterion (testable) | Traces to |
|---|----------------------|-----------|
| 1 | `skills/` and `agents/` exist at plain root, containing all 30 skills and 5 agent guides; `git log --follow` on a moved file still shows its pre-move history (i.e. moved with `git mv`, not delete+add) | Decision |
| 2 | `.claude/skills` and `.claude/agents` are **symlinks** to `../skills` and `../agents`, committed, and **relative** — `readlink` returns a path with no leading `/` | Decision + Out of scope |
| 3 | This repo can still run its own skills: `Skill({ skill: "wake" })` resolves and executes after the move | "keeping this repo able to run its own skills" |
| 4 | The historical reference count is **unchanged at 909** (the guide's original 1,764 is stale — see the Correction above), verified by re-running the count command after the move. Any other number is a failure, including a lower one | The prohibition |
| 5 | The live reference count is **0** — no file in the 49-file list still refers to `.claude/skills` or `.claude/agents` except as an intentional mention of the symlink itself | Live surface |
| 6 | `python3 -m pytest .claude/hooks/tests/ -q` ≥ 697 passed, `python3 -m pytest tests/ -q` 40 passed, `bash scripts/validate.sh` exits 0 | no regression |
| 7 | The symlink survives a **fresh clone**: `git clone` the repo to a temp dir, and `.claude/skills/wake/SKILL.md` is readable there | Adversarial review |
| 8 | The symlink survives `git worktree add`: create a throwaway worktree and confirm `.claude/skills/wake/SKILL.md` resolves **inside that worktree**, not into the main checkout | Adversarial review (Stage 3 depends on this) |
| 9 | `MANIFEST` lists `skills` and `agents` at their new paths, and `bash scripts/smoke-install.sh` still passes | Live surface |
| 10 | `memory/codebase-map.md` is regenerated via `/map-codebase`, not hand-edited — its diff shows a full regeneration, not a targeted path substitution | The prohibition's exception |
| 11 | Negative / anti-vacuity: with `.claude/skills` deleted (symlink removed), at least one test in the suite goes red — proving the symlink is load-bearing and not decorative | anti-vacuity |
| 12 | At least one new automated test asserts AC2 (the symlink exists and is relative) so a future change cannot silently replace it with a copy | Hard-Stop Gate 5 |
| 13 | `update.sh` re-establishes the canon symlinks on every run. Given an install where `.claude/skills` is missing, a stale real directory, or a non-relative link, `update.sh` leaves it as the correct relative symlink onto the plain-root canon | Stage 5 verify (regression) |
| 14 | Neither installer ever reports success over a stale canon. Given `.claude/{skills,agents}` as a **real directory** from a pre-T096 install, `setup.sh` and `update.sh` either migrate it or exit **non-zero** — a `RC=0` "Setup complete" / "Update complete" over content Claude Code cannot see is a failure | Stage 5 verify (regression) |
| 15 | A test drives the real upgrade path, not the function: install at the pre-T096 shape, run `update.sh`, and assert the content readable at `.claude/skills/wake/SKILL.md` matches the canon at `skills/wake/SKILL.md` | Hard-Stop Gate 5 + anti-vacuity |

---

## Evaluation & Acceptance

### Success Criteria (observable, pass/fail)

| # | Given (input/state) | Expect (output/behavior) | How it's checked |
|---|---------------------|--------------------------|------------------|
| 1 | Live-surface derivation re-run before starting | 49 files, 225 refs — matching this guide. A different count halts the task | manual probe, output pasted |
| 2 | Historical count re-run after the move | 909 — identical to before (the 1,764 in this row was stale; see the Correction above) | manual probe, both numbers pasted |
| 6 | Pre-T096-shape install (`.claude/skills` a real dir holding stale content), then `update.sh` | `.claude/skills/wake/SKILL.md` reads the fresh canon, OR the run exits non-zero. Never RC=0 over stale content | automated test + manual probe, output pasted |
| 7 | Correct-shape install with `.claude/skills` deleted, then `update.sh` | the relative symlink is restored | automated test |
| 3 | `readlink .claude/skills` | `../skills` (relative) | automated test |
| 4 | Fresh `git clone` into a temp dir | `.claude/skills/wake/SKILL.md` readable | manual probe, output pasted |
| 5 | Throwaway `git worktree add` | `.claude/skills/wake/SKILL.md` resolves within the worktree | manual probe, output pasted |
| 6 | Full suite + `validate.sh` + `smoke-install.sh` | all green | automated test |
| 7 | `.claude/skills` symlink removed | at least one test fails | automated test (anti-vacuity probe) |

**Count commands** (use these exact forms so numbers are comparable across runs):

```bash
# live surface
grep -rIl '\.claude/\(skills\|agents\)' --exclude-dir=.git --exclude-dir=__pycache__ \
  .claude/hooks .claude/skills .claude/agents docs/claude-md tests scripts lib templates \
  CLAUDE.md CLAUDE_LEGACY.md AGENTS.md MANIFEST setup.sh update.sh .cursor 2>/dev/null | sort -u | wc -l

# historical audit trail (must not change)
grep -rIo '\.claude/\(skills\|agents\)' tasks memory reports docs/ddr docs/adr \
  PROJECT_KANBAN.md BRAINSTORMING_LOG*.md 2>/dev/null | wc -l
```

### Verification Command (exact, runnable)

```bash
python3 -m pytest .claude/hooks/tests/ -q && \
python3 -m pytest tests/ -q && \
bash scripts/validate.sh && \
readlink .claude/skills && readlink .claude/agents
```

Expected: `≥697 passed`, `40 passed`, exit 0, then `../skills` and `../agents`.

### Evidence

Full pasted output for every row is in `tasks/TASK_REVIEW_T096.md`.

| Row | Result | Evidence |
|---|---|---|
| AC1 — canon at plain root, history follows | PASS | 30 skills / 5 agents at `skills/`, `agents/`; move commit `2cbfa99` records **39 renames**, 0 delete+add; `git log --follow -- agents/qa.md` reaches `b4582e5 Create qa.md` |
| AC2 — committed **relative** symlinks | PASS | `git ls-files -s` shows mode `120000` for both; `readlink` -> `../skills`, `../agents` |
| AC3 — repo still runs its own skills | PASS | `/map-codebase` was invoked and executed through `.claude/skills` during this task (AC10); the skill roster reloads from the symlink |
| AC4 — historical trail unchanged | PASS | `git diff --name-only 695f5d8 HEAD -- tasks/ memory/ reports/ docs/ddr docs/adr PROJECT_KANBAN.md 'BRAINSTORMING_LOG*.md'` returns **only** `tasks/TASK_REVIEW_T096.md`, this task's own new file. Raw count 909 -> 953 is fully accounted for: +23 in that new file, +19 in gitignored `memory/event-trace/`. Per-directory tracked counts identical. **The guide's 1,764 is stale — see defect D2.** |
| AC5 — live reference count 0 | PASS | 225 -> 0 functional refs. 29 textual occurrences remain, itemized and justified in the review; 4 of them are `setup.sh`'s `install_pack()` targets, which the guide places out of scope |
| AC6 — no regression | PASS | `.claude/hooks/tests/` **707 passed** (697 baseline + 10 new); `tests/` **40 passed**; `scripts/validate.sh` exit 0 |
| AC7 — survives fresh clone | PASS | clone of the branch: `.claude/skills -> ../skills`, `wake/SKILL.md` readable, `realpath` resolves inside the clone |
| AC8 — survives `git worktree add` | PASS | throwaway worktree: `realpath` -> `<worktree>/skills/wake/SKILL.md`, **not** the main checkout. Probe worktree + branch removed |
| AC9 — MANIFEST + smoke-install | PASS | MANIFEST lists `agents`, `skills`; `scripts/smoke-install.sh` -> `PASS`, asserting both plain-root canon and both resolved symlinks after a real install |
| AC10 — codebase-map regenerated | PASS | `/map-codebase` run; diff is **230 insertions / 89 deletions** across the file — a full regeneration, not a targeted substitution |
| AC11 — anti-vacuity | PASS | `rm .claude/skills` -> **48 failed**, 659 passed, and `validate.sh` FAIL. Restored -> 707 passed |
| AC12 — new test pins the symlink | PASS | `.claude/hooks/tests/test_canon_symlinks.py`, **10 new tests**, asserting existence, symlink-not-copy, relative target, and resolution — with `DDR-0006`-shape mutation controls proving each check goes red when violated |
| AC13 — `update.sh` re-establishes the canon links every run | PASS | `harness_install_canon_symlinks` in `lib/harness-fetch.sh`, called by `update.sh` after the copy. Probes 2 and 3: pre-relocation real dir -> `../skills` + canon content; deleted link -> `../skills`, `../agents` restored, RC=0. Automated: `test_update.sh` tests 7–8 |
| AC14 — no installer reports success over a stale canon | PASS | Stale real dir is **migrated** (moved to `<link>.bak`, then linked) by both installers — `cmp` proves `.claude/skills/wake/SKILL.md` == `skills/wake/SKILL.md` after. When it cannot migrate (a `.bak` already exists) the run exits **RC=1** and never prints "Update complete" (`test_update.sh` test 9). `setup.sh` test 4 covers the same for install. A regular **file** at the link still exits RC=1 — unchanged by design (Probe 4) |
| AC15 — a test drives the real upgrade path | PASS | `tests/test_update.sh` test 7: install at the pre-relocation shape, run the REAL `update.sh`, then `cmp .claude/skills/brainstorming/SKILL.md skills/brainstorming/SKILL.md`. Asserts on installer-observable state, never a function return. Suite 20 -> **30 passed**; `test_setup.sh` 15 -> **18 passed**. Mutation control: removing the one call turns **6** of them red |

**Hard-Stop Gate 5** — new test code written as part of this task: `test_canon_symlinks.py`
(10 tests) plus symlink assertions added to `scripts/validate.sh` and `scripts/smoke-install.sh`;
suite output pasted above and in the review. Stage 5 follow-up added the upgrade-path tests:
`tests/test_update.sh` tests 7–9 (20 -> 30 passed) and `tests/test_setup.sh` test 4 (15 -> 18
passed), each driving the real installer end to end.

**UI / Design Evidence rows**: ☐ N/A — pure-infrastructure task, no UI component.

**Scope additions found during implementation** (both recorded in the review's DELTA):
15 further live references in 8 files that build the path via `os.path.join(ROOT, ".claude", ...)`
and so never matched the guide's derivation command; and `install_canon_symlinks()` in `setup.sh`,
without which a downstream install would have no `.claude/skills` at all.

---

## Demonstration

> BEFORE / AFTER / DELTA / WITNESS: see `tasks/TASK_REVIEW_T096.md`.

---

## Approach

**Vital slice**: the move plus the symlinks. Everything else in this guide exists to stop that move
from damaging something.

**Cut list**:
- No `.codex/` or any other vendor directory — that is `T097`.
- No content edits to any skill or agent guide.
- No `packs/` migration.
- No Windows copy-fallback implementation. Document the limitation in `README.md`; implementing a
  fallback nobody has asked for is speculation.

**Recommended sequence** — order matters, and this order keeps the repo runnable at every commit:

1. Re-derive the live list and both counts. Paste them. If they disagree with this guide, **stop**.
2. `git mv .claude/skills skills` and `git mv .claude/agents agents`. Use `git mv` so history follows
   (AC1); a delete-and-add loses `git log --follow` on 35 files.
3. Create the two relative symlinks and `git add` them. Commit here — the repo is runnable again at
   this point, and a reviewer can see the move separately from the 225 text edits.
4. Rewrite the 49 live files, **file by file from the enumerated list**, never by pattern across the
   repo. Commit in coherent groups (hooks, tests, scripts, docs) rather than one 49-file commit — a
   reviewer cannot check 225 substitutions in a single diff.
5. Re-run the historical count. It must read 909 (not the stale 1,764 — see the Correction above). If it moved, `git reset` and find out why before
   doing anything else.
6. Regenerate `memory/codebase-map.md` via `/map-codebase`.
7. Full verification command.

**Pattern reference**: `tests/test_provider_adapters.py` — the conformance-test shape from `DDR-0006`
(assert on the real file, ship a mutation control proving it goes RED). AC11 and AC12 want that same
shape applied to the symlink.

**On committing the symlink.** Git stores symlinks natively, so this works on clone — but a reader
seeing only `skills/` in a diff may mistake `.claude/skills` for a stale duplicate and delete it.
AC11 and AC12 exist precisely to make that deletion loud instead of silent. Do not skip them on the
grounds that "the symlink obviously works".
