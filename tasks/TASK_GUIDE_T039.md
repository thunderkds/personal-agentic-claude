# TASK_GUIDE — T039: Dedup the `## Skills vs Agents` section in CLAUDE.md
**Date**: 2026-07-21
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
5. Note the **Complexity Level** above (C2) and apply the matching process from the Complexity matrix in `.claude/agents/general-agent-template.md`
6. C2 task: read `memory/codebase-map.md` for structural orientation

---

## Requirement (Pillar 1 — Adapt the requirement)

User request (verbatim): *"so for the general, my CLAUDE.md is huge, so I need to refactor this"*

Scope was then narrowed by the user via forced choice to **"Narrow dedup only"**: collapse the
`## Skills vs Agents` section to only what the Claude Code harness does **not** already inject,
and leave the rest of CLAUDE.md untouched.

**Restated intent**:
> CLAUDE.md is 580 lines / ~11k tokens and is re-read every turn. Its largest single section (72
> lines) re-lists ~30 skills and 4 agents together with descriptions that Claude Code already
> auto-injects into every session from `.claude/skills/` and `.claude/agents/`. Remove the
> duplicated text, keep the information the harness does not supply, and prove by automated test
> that no skill/agent reference was broken in the process.

**Out of scope** (this task explicitly does NOT do):
- Any other section of CLAUDE.md (Folder Structure, Stage bodies, Code Naming Conventions,
  Karpathy table, Memory Write Protocol) — those are the trim DDR-0001 deferred pending data
- `CLAUDE_LEGACY.md` — see *Files Must NOT Touch*; whether legacy mirrors this dedup is a
  separate decision for the Supervisor after this task lands
- Extracting anything into new `docs/` files
- Changing Hard-Stop Gates, Permanent Rules, or any pipeline semantics

**Requirement Refs**: this repo has no `PRD.md`. Traceability instead:
- **DDR-0001** — establishes that CLAUDE.md trims need justification. This task's justification is
  *verifiable duplication*, not a spend hypothesis, so it does not conflict with the deferral.
- **User directive 2026-07-21** — scope locked to "Narrow dedup only".

### Requirement Fidelity Gate (sign off BEFORE implementation)

- [x] Restated intent confirmed to match the user's request (Supervisor, via forced-choice answer)
- [x] Domain terms align with `PROJECT_SPEC.md` glossary — "Skill", "Agent", "subagent_type" already canonical
- [x] Every Acceptance Criterion below traces to a line in the Requirement
- [x] Requirement Refs resolve (DDR-0001 exists at `docs/ddr/0001-measure-first-token-refactor.md`)

---

## Dependencies & Reachability

**Depends on**: `None`

**Entry point**: `## Skills vs Agents`
> The literal H2 heading in CLAUDE.md that this task rewrites. Grep-able and unique in the file.

---

## Acceptance Criteria

| # | Criterion (testable) | Traces to requirement |
|---|----------------------|-----------------------|
| 1 | `## Skills vs Agents` section is ≤30 lines (from 72) | "collapse the section" |
| 2 | Every `Skill({ skill: "X" })` reference remaining anywhere in CLAUDE.md resolves to an existing `.claude/skills/X/SKILL.md`, or is a documented built-in | "no reference broken" |
| 3 | Every `subagent_type` value remaining in CLAUDE.md resolves to a `.claude/agents/*.md` whose `name:` field matches | "no reference broken" |
| 4 | The four preserved items (see Approach) are still present verbatim-or-tighter: Skills-vs-Agents mechanism table, `subagent_type` → file mapping, the "spawn prompt needs only the task pointer" note, the blast-radius naming disambiguation | "keep what the harness does not supply" |
| 5 | **Negative**: `## Hard-Stop Gates` and `## Permanent Rules` sections are byte-identical to HEAD | "leave the rest untouched" |
| 6 | **Negative**: total CLAUDE.md line count decreased by ≥40 and by ≤80 (a larger drop means the agent went beyond scope) | "narrow dedup only" |

---

## Evaluation & Acceptance (How we know the agent worked correctly)

### Success Criteria (observable, pass/fail)

| # | Given (input/state) | Expect (output/behavior) | How it's checked |
|---|---------------------|--------------------------|------------------|
| 1 | CLAUDE.md after edit | `scripts/test-claude-md-refs.sh` exits 0 | automated test |
| 2 | A deliberately broken ref (e.g. `Skill({ skill: "nonexistent-xyz" })` temporarily inserted) | test exits non-zero naming the bad ref | automated test (negative control) |
| 3 | `git diff HEAD -- CLAUDE.md` | hunks touch only the `## Skills vs Agents` region | manual review at Stage 4 |
| 4 | Hard-Stop Gates section | unchanged | automated test (checksum compare vs `git show HEAD:CLAUDE.md`) |

### Verification Command (exact, runnable)

```bash
bash scripts/test-claude-md-refs.sh && \
  echo "lines: $(wc -l < CLAUDE.md) (was 580)"
```

### Evidence (filled by reviewer at Stage 4/5)

| Check | Result | Notes / output snippet |
|-------|--------|------------------------|
| **New test(s) cover Acceptance Criteria (file paths pasted)** | ☑ pass | `scripts/test-claude-md-refs.sh` — covers AC1/AC2/AC3/AC5/AC6. Red phase (against pre-edit CLAUDE.md): `PASS: AC2... PASS: AC3... FAIL: AC1: ## Skills vs Agents section is 71 lines (expected <=30)... PASS: AC5 (x2)... FAIL: AC6: line count decreased by 0`. Green phase (post-dedup, this commit 243ff49): `PASS: AC2: all Skill({ skill: "X" }) references resolve` / `PASS: AC3: all subagent_type references resolve` / `PASS: AC1: ## Skills vs Agents section is 27 lines (<=30)` / `PASS: AC5: ## Hard-Stop Gates byte-identical to HEAD` / `PASS: AC5: ## Permanent Rules byte-identical to HEAD` / `PASS: AC6: line count decreased by 44 (was 580, now 536; expected 40-80)` / `test-claude-md-refs: all checks passed` |
| Verification command run | ☑ pass | `bash scripts/test-claude-md-refs.sh && echo "lines: $(wc -l < CLAUDE.md) (was 580)"` → all 6 PASS lines above, then `lines: 536 (was 580)` |
| Negative cases hold | ☑ pass | Negative control: temporarily inserted `Skill({ skill: "nonexistent-xyz" })` after line 32 → `FAIL: AC2: unresolved skill reference(s): nonexistent-xyz` (test correctly named the bad ref), then reverted before the real dedup. AC5 checksum (Hard-Stop Gates + Permanent Rules byte-identical) and AC6 line-delta bounds (44, within 40–80) both pass in the green run above. |
| verify | ☑ pass | Docs-only task, no running app surface to exercise. `verify` here = re-running `scripts/test-claude-md-refs.sh` against the committed CLAUDE.md at HEAD (243ff49) — reran post-commit: `test-claude-md-refs: all checks passed`, exit 0 — pass. |
| Review scope bounded to the change's blast radius (affected set, not whole repo) | ☑ pass | `git diff HEAD~1 -- CLAUDE.md \| grep '^@@'` → only 3 hunks: `@@ -1,5 +1,5 @@` (Version bump), `@@ -18,18 +18,14 @@` and `@@ -38,53 +34,13 @@` (both inside `## Skills vs Agents`). `git diff --stat` confirms only `CLAUDE.md` + new `scripts/test-claude-md-refs.sh` touched — no other CLAUDE.md section, no `CLAUDE_LEGACY.md`, no `.claude/skills/**`/`.claude/agents/**`. |
| Full smoke suite still green (no regression) | ☑ pass | `bash scripts/smoke-install.sh` → all `[ok]` lines incl. `CLAUDE.md`, `.claude/agents`, `.claude/skills`, `.claude/settings.json`, `memory/*`, `tasks`, `.claude/harness-lock.json`, ending `smoke-install.sh: PASS`, exit 0 |
| **UI: Visual regression** | ☐ N/A | Docs-only task, no UI component |
| **UI: Design-system compliance** | ☐ N/A | Docs-only task, no UI component |
| **UI: Responsiveness** | ☐ N/A | Docs-only task, no UI component |

---

## Approach

The Claude Code harness already injects, unprompted, into every session:
- the full skill roster (`name: description`) discovered from `.claude/skills/`
- the full agent-type roster (`name: description`) discovered from `.claude/agents/`

Many of those auto-injected descriptions **already carry the stage mapping** (e.g. `code-review:
"...for Stage 4"`, `tdd: "Use during Stage 3 implementation"`, `to-issues: "Use during Stage 2
planning"`). So the CLAUDE.md tables restate both the description *and*, in most rows, the stage.

**Delete**: the ~30-row custom-skill catalog and the per-row description prose in the project
sub-agent table.

**Keep** (the harness supplies none of this):
1. The 4-row Skills-vs-Agents mechanism table (defined in / invoked via / runs / use for) — this is
   conceptual guidance, not a roster.
2. The `subagent_type` → `.claude/agents/<file>.md` path mapping. The harness gives the agent *name*
   and description but never the definition file path.
3. The note that `subagent_type` is the agent's `name:` field, and that because Claude Code
   auto-loads the matching agent file, the spawn prompt needs only the task pointer — not the whole
   guide. This is load-bearing and appears nowhere else.
4. The `blast-radius` naming disambiguation (data-breach blast radius ≠ code-dependency blast
   radius). Genuinely useful and not derivable from the description.
5. The `general-agent-template` caveat (shared base rules, not directly spawnable).
6. The note that pack skills get symlinked into `.claude/skills/`.

**Replace the catalog with** a compact stage→skill index listing **names only**, no descriptions —
so the pipeline ordering survives while the prose does not. Add one line stating explicitly that
skill descriptions are auto-injected and must not be restated here, so the section does not silently
re-grow.

**Write the test first** (`tdd`): `scripts/test-claude-md-refs.sh`, following the existing
`scripts/smoke-install.sh` conventions (same shebang, same pass/fail output style, `sh -n`-clean —
note `memory/learnings.md`: there is no shellcheck in this environment, so substitute `sh -n` plus a
real bash run and say so explicitly rather than silently skipping).

---

## Edge Case Checklist

- [ ] A dropped row conveyed something the harness description does **not** — before deleting any
      row, diff its text against that skill's actual `description:` frontmatter in
      `.claude/skills/<name>/SKILL.md`. If the row adds information, keep that information.
- [ ] `verify` is referenced in CLAUDE.md as a built-in but may not appear in the auto-injected
      roster. Do not assume every built-in is auto-listed — keep the built-ins table.
- [ ] Skill names inside *other* sections (Stage bodies, Permanent Rules) must keep resolving; the
      test must scan the whole file, not just the edited section.
- [ ] The step-limit hook (`pre_agent_step_limit.py`) is known to false-positive on any tool input
      whose *text* mentions an old task ID — this guide names T031/T038 nowhere for that reason;
      if it fires, bracket-glob the ID (`memory/learnings.md`).
- [ ] Do not "improve" adjacent prose while in the file (Surgical Changes). Scope is one section.
- [ ] Line-delta must stay within the AC6 bounds — an over-large drop is a scope violation, not a win.

---

## Files to Change (Predicted)

| File | Change |
|------|--------|
| `CLAUDE.md` | Rewrite `## Skills vs Agents` (72 → ≤30 lines); bump the `**Version:**` line |
| `scripts/test-claude-md-refs.sh` | **New** — reference-resolution + scope-guard test |

## Files Must NOT Touch

| File | Reason |
|------|--------|
| `CLAUDE_LEGACY.md` | The sync policy (`memory/decisions.md`) covers *additions*, not removals. Whether legacy mirrors this dedup is a Supervisor decision after this task lands. Divergence here is deliberate and tracked, not accidental. |
| `.claude/skills/**` | Skill definitions are the source of truth being deduped *against* — editing them would invalidate the test |
| `.claude/agents/**` | Same reason |
| `MANIFEST` | CLAUDE.md is not shipped by MANIFEST; nothing to update |
| Any other CLAUDE.md section | Explicitly deferred by DDR-0001 |

---

## Test Plan

1. **Red**: write `scripts/test-claude-md-refs.sh` against the *current* CLAUDE.md. AC1 (≤30 lines)
   and AC6 (line delta) must fail; AC2/AC3 (refs resolve) should already pass — that is the point,
   it proves the test can distinguish "unchanged" from "broken".
2. **Negative control**: temporarily insert `Skill({ skill: "nonexistent-xyz" })`, confirm the test
   fails naming it, then remove. Paste that output into Evidence.
3. **Green**: perform the dedup; all ACs pass.
4. **Regression**: `bash scripts/smoke-install.sh` still green.
5. Paste real command output — not a claim of output — into every Evidence row
   (`memory/learnings.md`: "a checkmark is a claim, not a fact").

---

## Completion Checklist

- [x] Implementation done
- [ ] Self-review: `Skill({ skill: "code-review" })` run — pending, Stage 4 (Supervisor to run)
- [ ] Security review: `Skill({ skill: "security-review" })` run — pending, Stage 4 (Risk=Medium, mandatory)
- [x] `sh -n` + real bash run on the new script (no shellcheck in this env — substituted `sh -n` static check + real `bash scripts/test-claude-md-refs.sh` execution, both green)
- [x] Tests written AND pass — output pasted into Evidence table (Hard-Stop Gate 5)
- [x] `Skill({ skill: "verify" })` run — see Evidence table `verify` row
- [x] Flag any new patterns to the Supervisor for `memory/` (do not write memory yourself) — see final report
- [x] Supervisor notified: task ready for Stage 4 review
