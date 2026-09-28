# TASK_GUIDE — T136: The spawn model is picked per CLI from the task's Complexity, never hard-coded to Claude names
**Date**: 2026-09-28
**Complexity Level**: C2 — 3+ files (skill, pipeline doc, two templates, PROJECT_SPEC) and one design choice (where the table lives)
**Risk Level**: Low — doctrine/template text plus drift tests; no hook, installer or deploy change
**Priority**: P1
**Assigned agent**: Common-Infrastructure-Agent
**Agent guide**: `agents/common-infrastructure.md`

---

## Mandatory Startup (Do Not Skip)

Before writing any code:
1. Read `PROJECT_SPEC.md`
2. Read the memory slice in your spawn prompt (`<!-- memory-slice -->`). Read `memory/MEMORY.md` in full only if your work reaches a file, hook, skill or decision the slice does not cover
3. Read this file completely
4. Read `agents/common-infrastructure.md`
5. Note the **Complexity Level** above and apply the matching process from the Complexity matrix in your role guide
6. Read `memory/codebase-map.md`, then `skills/craft-spawn-prompt/SKILL.md` (step 5 + Communication Protocol), `docs/claude-md/pipeline-stages.md` (Stage 1 item 2, Stage 1.5, Stage 3 ~line 153), `templates/PROJECT_SPEC_template.md` (`## Sub-Agent Team`), `templates/TASK_GUIDE_template.md` (Mandatory Startup item 5), `AGENTS.md`, and `tests/test_spawn_startup_reads.py` (pattern for doctrine-text tests)

---

## Requirement (Pillar 1 — Adapt the requirement)

User, 2026-09-28: *"when the claude generate the Taskguide, it will contains the model reference, but with the claude, example, the supervisor analyzied and pick the sonet for the tasks, but when swap to codex to implement, ti does not have the sonet, so what wrong here"* — then, on the proposed design: *"it should the complexity level and when we change to another CLI, it can depends on that to pick the suitable model following the rules"* — and *"yes, let go"* to the four details below.

**Diagnosis (Supervisor, 2026-09-28, read from the files):**
- The task guide already records only `**Complexity Level**` (C0–C3), which is CLI-neutral. Good — keep it.
- The model is chosen at spawn time by `skills/craft-spawn-prompt/SKILL.md:69` with a fixed Claude-only map `C0→haiku, C1→sonnet, C2→sonnet/opus, C3→opus`, repeated at `docs/claude-md/pipeline-stages.md:153`. No CLI other than Claude can satisfy it.
- Stage 1 item 2 (`pipeline-stages.md:49-51`) asks for each CLI's run command only, never its models.
- Stale pointers: `templates/TASK_GUIDE_template.md:18` says to take the *model* from the role guide's Complexity matrix — that matrix (e.g. `agents/backend.md:89-92`) has no model column; `craft-spawn-prompt/SKILL.md:69` cites a table "in `CLAUDE.md` Stage 3 / `general-agent-template.md`" that no longer exists there.

**Restated intent:**
> The task guide keeps only the Complexity level. A per-project **CLI model table** — one row per
> CLI, one column per level C0–C3 — is filled at Stage 1. At spawn time `craft-spawn-prompt` looks
> the task's level up in the row for the CLI that will run it, and reports `<cli> · <Cn> → <model>`.
> If the CLI has no row, or the cell is empty, it stops and asks the user — it never falls back to a
> Claude model name and never invents one.

**The four agreed details (user, 2026-09-28 — "yes"):**
1. The table lives in `PROJECT_SPEC.md` as a new `## CLI Model Table` section right after `## Sub-Agent Team`; the same section (with the Claude row pre-filled as the example, other rows as placeholders) goes into `templates/PROJECT_SPEC_template.md`. Columns: `CLI | Run command | C0 | C1 | C2 | C3`.
2. No row / empty cell → STOP and ask. No default, no guess.
3. `craft-spawn-prompt` step 5 takes the CLI as an input, looks up the cell, and its output + Default Notification name both CLI and level (`codex · C1 → <model>`), no longer `[haiku/sonnet/opus]`.
4. The three stale/hard-coded places above are corrected to point at the table.

**Round 2 (2026-09-28, from the user's `/verify`):** FAIL — every named-CLI case worked
(`claude · C2 → sonnet`, `claude · C0 → haiku`, codex/gemini → STOP), but a call that names **no**
CLI silently assumed `claude` and returned `claude · C2 → sonnet` with no warning — the original
defect one step earlier. Fix: AC10 + M4 only. Keep the round-1 work as is; the three Stage 4 P2/P3
notes (dead code in the AC8 test, step 6 reflow, AC5 duplicate `or`) may be cleaned up in the same
commit since they sit in the same two files — nothing else.

**Out of scope:**
- `model:` in `agents/*.md` frontmatter — it is Claude Code's own default for that agent and the spawn step overrides it; left as is.
- `scripts/token_audit.py` and its tests (`haiku|sonnet|opus` tier regexes) — a reporting tool; register a follow-up if it matters, don't change it here.
- Inventing any Codex/Gemini model name. The Codex row in this repo's `PROJECT_SPEC.md` is left as a placeholder the user fills; the agent must not write model names it has not been given.
- The installer / `update.sh` / MANIFEST / `.codex/skills/` projection.

**Requirement Refs**: no `PRD.md` — N/A.

### Requirement Fidelity Gate (sign off BEFORE implementation)

- [x] Restated intent confirmed (user, 2026-09-28: "it should the complexity level … depends on that to pick the suitable model", "yes, let go")
- [x] Domain terms align: *Complexity Level (C0–C3)*, *spawn model*, *CLI model table*, *Stage 1 Multi-CLI Authentication*
- [x] Every Acceptance Criterion below traces to a line in the Requirement
- [x] Requirement Refs: N/A — recorded, not skipped

---

## Dependencies & Reachability

**Depends on**: None

**Entry point**: `#### 5. Recommend spawn model` in `skills/craft-spawn-prompt/SKILL.md`

---

## Acceptance Criteria

| # | Criterion (testable) | Traces to |
|---|----------------------|-----------|
| 1 | `templates/PROJECT_SPEC_template.md` has a `## CLI Model Table` section directly after `## Sub-Agent Team`, header row `CLI \| Run command \| C0 \| C1 \| C2 \| C3`, a filled `claude` example row, and a placeholder row for another CLI | detail 1 |
| 2 | This repo's `PROJECT_SPEC.md` has the same section: `claude` row filled (`haiku / sonnet / sonnet or opus / opus`), `codex` row present with **empty** model cells marked to be filled by the user | detail 1; out-of-scope "no invented names" |
| 3 | `craft-spawn-prompt` step 5 reads the level from the guide and the CLI from its input, looks up `PROJECT_SPEC.md`'s `## CLI Model Table`, and contains no hard-coded `C0→haiku`-style map | detail 3 |
| 4 | Step 5 states: no row for the CLI, or an empty cell → STOP and ask the user; never fall back to another CLI's model | detail 2 |
| 5 | The skill's Output and Default Notification report `<cli> · <Cn> → <model>`; the string `[haiku/sonnet/opus]` is gone | detail 3 |
| 6 | `docs/claude-md/pipeline-stages.md` Stage 1 item 2 asks, per CLI, for its model at each level C0–C3 and records them in the table; Stage 3 (~line 153) points at the table instead of a hard-coded map | details 1, 4 |
| 7 | `templates/TASK_GUIDE_template.md` Mandatory Startup item 5 no longer tells the agent to take a *model* from the role-guide matrix | detail 4 |
| 8 | Outside `tasks/`, `memory/`, `reports/`, the `PROJECT_KANBAN*.md` boards (records that quote results), `docs/adr/`, `docs/ddr/`, `CLAUDE_LEGACY.md`, `scripts/token_audit.py`, `.claude/hooks/tests/test_token_audit_*`, and `agents/*.md` frontmatter, `git grep -nE 'C[0-3] ?→ ?(haiku\|sonnet\|opus)'` returns nothing | detail 4 |
| 9 | New `tests/test_cli_model_table.py` asserts AC1–AC8 as text checks (style of `tests/test_spawn_startup_reads.py`) | drift guard |
| 10 | **Round 2.** Step 5 states: **no CLI named** by the caller → STOP and ask which CLI will run the task; never assume `claude` (or any CLI). The Default Notification's STOP form covers it (e.g. `STOP: no CLI named — ask which CLI runs <Task ID>`). A new test in `tests/test_cli_model_table.py` asserts it | `/verify` 2026-09-28 step 5: with no CLI named the skill silently returned `claude · C2 → sonnet` |

**Mutation controls** (paste results in the review's "Negative cases hold" row):
**M1** — re-add `C0→haiku, C1→sonnet` to step 5 → AC3/AC8 test RED.
**M2** — delete the STOP-and-ask sentence from step 5 → AC4 test RED.
**M3** — delete the `## CLI Model Table` heading from the template → AC1 test RED.
**M4** (round 2) — delete the no-CLI-named STOP sentence from step 5 → AC10 test RED.

### Verification Command (exact, runnable)

```bash
python3 -m pytest tests/test_cli_model_table.py -q
python3 -m pytest .claude/hooks/tests tests -q | tail -1
sh scripts/validate.sh
```

### Evidence / Demonstration

> **Moved.** Filled in `tasks/TASK_REVIEW_T136.md`. BEFORE: the verbatim `#### 5. Recommend spawn model` block and `pipeline-stages.md` Stage 1 item 2 as they are now. AFTER: the same two places, plus one worked lookup — `claude · C1 → sonnet` and `codex · C1 → STOP (no model recorded)` read off this repo's table.

---

## UI / Design Acceptance Criteria

N/A — no UI component. All three UI Evidence rows ☐ N/A (doctrine/template text only).

---

## Approach

**Pattern reference**: `tests/test_spawn_startup_reads.py` (text assertions over `SKILL.md`, splitting on `#### N.` headings); `## Sub-Agent Team` table in `templates/PROJECT_SPEC_template.md` (table style).

**Vital slice**: AC1, AC3, AC4 — the table exists and the spawn step reads it and refuses to guess.
**Cut list**: per-CLI spawn *command* templates (the Sub-Agent Team table already carries spawn commands); auto-detecting installed CLIs; changing `agents/*.md` `model:`; `token_audit.py` tiers.

Keep edits surgical: replace step 5's text, don't restructure the skill. `craft-spawn-prompt/SKILL.md` is ~11.4 KB, already over Codex's 8 KB skill cap (`AGENTS.md`), so it is not projected to Codex either way — do not try to shrink it in this task.

---

## Edge Case Checklist

- [ ] A C2 cell holding two models (`sonnet or opus`) — step 5 says the Supervisor picks per the task's risk and reports which one; it does not fail
- [ ] A CLI whose single model has no size tiers — the user may put the same model in all four cells; nothing requires them to differ
- [ ] `PROJECT_SPEC.md` has no `## CLI Model Table` at all (older installs) — treated as "no row": STOP and ask, and suggest adding the section from the template
- [ ] The grep in AC8 must not flag the test file itself (build the regex from parts or exclude `tests/test_cli_model_table.py`)

---

## Files to Change (Predicted)

| File | Change |
|------|--------|
| `templates/PROJECT_SPEC_template.md` | New `## CLI Model Table` section |
| `PROJECT_SPEC.md` | Same section; claude row filled, codex row empty cells |
| `skills/craft-spawn-prompt/SKILL.md` | Step 5 lookup + STOP rule; Output item 3; Default Notification |
| `docs/claude-md/pipeline-stages.md` | Stage 1 item 2 asks for models per level; Stage 3 line points at the table |
| `templates/TASK_GUIDE_template.md` | Mandatory Startup item 5: drop "/ model" |
| `tests/test_cli_model_table.py` | New — AC9 |

## Files Must NOT Touch

| File | Reason |
|------|--------|
| `agents/*.md` | `model:` frontmatter out of scope |
| `scripts/token_audit.py`, `.claude/hooks/tests/test_token_audit_*` | Out of scope — follow-up |
| `setup.sh`, `update.sh`, `MANIFEST`, `.claude/hooks/**` | No installer/hook change |
| `memory/MEMORY.md` | Supervisor-only writes |
| `tasks/TASK_GUIDE_*.md` other than this one | Historical records |

---

## Test Plan

Write `tests/test_cli_model_table.py` first and observe it RED on `main`; make the doc edits; GREEN; run M1–M3; run the full suite and `validate.sh`.

---

## Completion Checklist

- [ ] Implementation done; AC9 tests observed RED first
- [ ] M1–M3 pasted in the Evidence table
- [ ] Self-review: `Skill({ skill: "code-review" })` run
- [ ] Full suite + `validate.sh` pass — output pasted into `tasks/TASK_REVIEW_T136.md`
- [ ] UI Evidence rows ☐ N/A with justification
- [ ] `/verify` — user-run
- [ ] Supervisor notified: task ready for Stage 4 review
