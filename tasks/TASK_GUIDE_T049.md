# TASK_GUIDE — T049: Refactor CLAUDE.md to under 200 lines via extracted resource files
**Date**: 2026-08-04
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
5. Complexity Level is **C2** — apply the matching process (brainstorm/decompose lightly, verify depth, model) from the Complexity matrix in `.claude/agents/general-agent-template.md`
6. Read `memory/codebase-map.md` if present for structural orientation

---

## Requirement (Pillar 1 — Adapt the requirement)

User request (verbatim, 2026-08-04): "start the task to refactor the CLAUDE.md, it should contain below 200 lines of code. if the content is large, should create the suitable resource and CLAUDE will refer to that by the link."

**Restated intent**:
> `CLAUDE.md` (the deployed greenfield Supervisor instructions file) must be reduced to **under 200 lines** while losing zero operational content. Any section too large to keep inline moves to a new linked resource file that `CLAUDE.md` references by relative link. The extracted files must remain part of the **deployed package** (i.e. discoverable by `setup.sh`/`update.sh` via `MANIFEST`), not left behind as repo-only docs — a project that installs via `setup.sh` must end up with working links, not 404s.

**Out of scope**:
- `CLAUDE_LEGACY.md` is NOT touched by this task. It has its own sync policy (mirror *additions* from CLAUDE.md — see `memory/decisions.md`); restructuring it is a separate follow-up task, not silently bundled in here.
- No content is deleted or reworded for meaning — this is a structural split, not a content rewrite. Tables, gate text, and rule wording carry over verbatim into their new home files.
- No changes to skill/agent/hook behavior — this is a documentation/instruction-file reorganization only.

**Requirement Refs**: No `PRD.md` exists for this framework's own self-maintenance (this repo IS the framework, not a downstream project). Traceability is the user's direct request above, restated intent, and Acceptance Criteria below.

### Requirement Fidelity Gate (sign off BEFORE implementation)

- [x] Restated intent confirmed to match the user's request (Supervisor, this pass)
- [x] Domain terms align with `PROJECT_SPEC.md` / `memory/glossary.md` (no new terms introduced)
- [ ] Every Acceptance Criterion below traces to a line in the Requirement — **agent must verify before starting**
- [x] No `PRD.md` Requirement Refs apply (see above)

> Do not start implementing until this gate is checked. If anything is unclear, STOP and ask the Supervisor.

---

## Dependencies & Reachability

**Depends on**: None

**Entry point**: `Standalone — N/A: this is the deployed CLAUDE.md instructions file itself, read by the Supervisor at session start, not called from application code.`

---

## Acceptance Criteria

| # | Criterion (testable) | Traces to requirement |
|---|----------------------|-----------------------|
| 1 | `wc -l CLAUDE.md` reports **< 200** | "below 200 lines of code" |
| 2 | Every section removed from `CLAUDE.md` exists verbatim (content-preserving, reformatting allowed) in a new resource file, linked from `CLAUDE.md` by a relative Markdown link | "create the suitable resource and CLAUDE will refer to that by the link" |
| 3 | Every new resource file's path is covered by an entry in `MANIFEST`, so `setup.sh`/`update.sh` deploy it into downstream projects alongside `CLAUDE.md` | implicit: a deployed CLAUDE.md must not link to files that don't exist post-install |
| 4 | The 6 **Hard-Stop Gates**, the **Karpathy Engineering Principles** table, and the **Mandatory Session Startup** (`wake`) section remain **inline in `CLAUDE.md`** (not extracted) — these are read every session and must not cost an extra hop | preserves operational reliability of the most safety-critical, highest-frequency content |
| 5 | All `Skill({ skill: "..." })` / `Agent({ subagent_type: "..." })` invocation syntax blocks throughout the document are preserved exactly (no reformatting that breaks copy-pasteable JSON-ish call syntax) | no regression to spawn/skill invocation reliability |
| 6 | A fresh read of `CLAUDE.md` + its linked resource files, taken together, contains the **same operational instructions** as the pre-refactor 565-line file — nothing silently dropped | "refactor" not "trim" — Karpathy Surgical Changes |
| 7 | `grep -rn "CLAUDE_LEGACY.md"` shows it is untouched (0 diff) unless explicitly asked | out-of-scope guard |

---

## Evaluation & Acceptance

### Success Criteria (observable, pass/fail)

| # | Given (input/state) | Expect (output/behavior) | How it's checked |
|---|---------------------|--------------------------|------------------|
| 1 | Refactored `CLAUDE.md` | `wc -l CLAUDE.md` < 200 | automated: `wc -l CLAUDE.md` |
| 2 | Any link in `CLAUDE.md` of the form `[...](path)` pointing at a new resource file | target file exists at that relative path | automated: script resolves every Markdown link target and asserts existence |
| 3 | New resource file paths | all present in `MANIFEST` | automated: for each new file's containing directory/path, confirm a covering line exists in `MANIFEST` |
| 4 | Content diff: concatenation of (new `CLAUDE.md` + all newly-linked resource files) vs. old 565-line `CLAUDE.md` | same section content present somewhere in the new set (headings/tables/prose intact, only location changed) | manual diff review by Supervisor at Stage 4, section-by-section |
| 5 | `CLAUDE_LEGACY.md` | byte-identical to pre-task version (`git diff` empty for that file) | automated: `git diff --stat CLAUDE_LEGACY.md` empty |

### Verification Command (exact, runnable)

```bash
wc -l CLAUDE.md
grep -oE '\[[^]]+\]\(([^)]+\.md[^)]*)\)' CLAUDE.md | sed -E 's/.*\(([^)]+)\).*/\1/' | while read -r f; do
  [ -f "$f" ] && echo "OK: $f" || echo "MISSING: $f"
done
git diff --stat CLAUDE_LEGACY.md
```

### Evidence (filled by reviewer at Stage 4/5)

| Check | Result | Notes / output snippet |
|-------|--------|------------------------|
| **New test(s) cover Acceptance Criteria (file paths pasted)** | ☑ pass | Verification script (below) independently re-run by Supervisor from the worktree `.claude/worktrees/agent-ae634b5ff56d79e03`: `wc -l CLAUDE.md` → `198`; link-resolution loop → all 5 `docs/claude-md/*.md` targets `OK`; `git diff --stat CLAUDE_LEGACY.md` → empty |
| Verification command run | ☑ pass | `wc -l CLAUDE.md` = 198; all 5 linked files resolve (folder-structure.md 47L, code-naming-conventions.md 30L, phase0-project-initiation.md 71L, pipeline-stages.md 234L, memory-write-protocol.md 18L = 400 lines total content preserved); `git diff --stat CLAUDE_LEGACY.md` empty |
| Negative cases hold | ☑ pass | Agent self-attested a deliberately-mistyped link path correctly reported `MISSING`; Supervisor did not re-run the negative case directly but confirms the positive-case script logic (bare `[ -f "$f" ]` test) would fail symmetrically |
| verify | ☑ pass | Supervisor read the refactored `CLAUDE.md` end-to-end plus all 5 extracted files — section-by-section diff against the pre-task 565-line version confirms no content silently dropped (only reformatted/relocated); Hard-Stop Gates, Karpathy Principles table, and Mandatory Session Startup confirmed inline per AC4; all `Skill({...})`/`Agent({...})` blocks intact — pass |
| Review scope bounded to the change's blast radius (affected set, not whole repo) | ☑ pass | Reviewed only: `CLAUDE.md`, `MANIFEST`, `docs/claude-md/*.md` (5 files) — the exact predicted Files-to-Change set, nothing else |
| Full smoke suite still green (no regression) | ☑ pass | Agent ran `python3 -m pytest .claude/hooks/tests/ -q` → `139 passed` (docs-only change, hooks untouched) |
| UI: Visual regression | ☑ N/A | docs-only task |
| UI: Design-system compliance | ☑ N/A | docs-only task |
| UI: Responsiveness | ☑ N/A | docs-only task |

---

## Approach

**Pattern reference**: `memory/decisions.md` → "T039 merged: CLAUDE.md Skills-vs-Agents dedup" entry — precedent for trimming CLAUDE.md by moving content out of the file the harness auto-injects, while keeping only what sub-agents actually need reachable in-context.

**Recommended split** (Supervisor's proposed allocation — agent may adjust with rationale, but must satisfy Acceptance Criteria 4 verbatim):

Create a new `docs/claude-md/` directory (add `docs/claude-md` as a new line in `MANIFEST` so it deploys):

| New file | Moves from CLAUDE.md | Approx. lines saved |
|---|---|---|
| `docs/claude-md/folder-structure.md` | `## Folder Structure Requirements (Mandatory)` full detail | ~40 |
| `docs/claude-md/code-naming-conventions.md` | `## Code Naming Conventions` full table | ~28 |
| `docs/claude-md/phase0-project-initiation.md` | `## Phase 0` Steps 1 / 1.5 / 2 full detail | ~65 |
| `docs/claude-md/pipeline-stages.md` | `## 5-Stage Agentic Pipeline` full Stage 0.5–5 detail | ~225 |
| `docs/claude-md/memory-write-protocol.md` | `## Memory Write Protocol` full detail | ~18 |

**Stays inline in CLAUDE.md** (per Acceptance Criterion 4): Communication Style, Skills vs Agents mechanism table + stage index, General Agent Template pointer table, Multi-CLI Configuration, Karpathy Engineering Principles table, Mandatory Session Startup (`wake`), Permanent Rules, **Hard-Stop Gates**, Final Instruction.

Each extraction point in `CLAUDE.md` should leave a short pointer, not silence — e.g.:
```
### Stage X: <Name>
See `docs/claude-md/pipeline-stages.md#stage-x-<slug>` for full stage detail.
Trigger: `Skill({ skill: "..." })` at <moment>.
```
so a reader skimming `CLAUDE.md` alone still knows the pipeline shape and where to look, not just a bare "see docs" with no orientation.

---

## Edge Case Checklist

- [ ] A Markdown link target must resolve relative to the **repo root**, matching how the rest of `CLAUDE.md`'s existing links (e.g. `templates/PRD_template.md`) are already written — don't introduce a different link-resolution convention
- [ ] `MANIFEST`'s comment header says "One resource path per line" — confirm a directory-level entry (`docs/claude-md`) is consistent with how `.claude/skills` (a directory) is already listed, not a new pattern
- [ ] Any `Skill({...})` / `Agent({...})` code block that got moved must still be inside a fenced code block in its new home file — a plain-text move can silently lose the fence
- [ ] Table rows split across a page boundary in the move must not lose their header row in the new file
- [ ] Final line count check must run on the actual committed file, not a working draft — re-run `wc -l` after the last edit

---

## Files to Change (Predicted)

| File | Change |
|------|--------|
| `CLAUDE.md` | Trim to <200 lines; replace extracted sections with short pointers + links |
| `docs/claude-md/folder-structure.md` | New — full Folder Structure Requirements content |
| `docs/claude-md/code-naming-conventions.md` | New — full Code Naming Conventions table |
| `docs/claude-md/phase0-project-initiation.md` | New — full Phase 0 Steps 1/1.5/2 |
| `docs/claude-md/pipeline-stages.md` | New — full 5-Stage Agentic Pipeline detail |
| `docs/claude-md/memory-write-protocol.md` | New — full Memory Write Protocol |
| `MANIFEST` | Add `docs/claude-md` line so it's deployed by setup.sh/update.sh |

## Files Must NOT Touch

| File | Reason |
|------|--------|
| `CLAUDE_LEGACY.md` | Explicitly out of scope this task (see Requirement) |
| `.claude/hooks/*.py` | No hook logic changes needed for a docs restructure |
| `.claude/skills/**`, `.claude/agents/**` | No skill/agent behavior changes needed |

---

## Test Plan

1. Run the Verification Command block above and paste real output into Evidence.
2. Manually diff pre- and post-refactor content section-by-section (Supervisor, Stage 4) to confirm nothing was silently dropped, not just reformatted.
3. Confirm `CLAUDE_LEGACY.md` has zero diff.
4. Confirm `.claude/hooks/tests/` suite is unaffected (docs-only change; expect same pass count as pre-task baseline).

---

## Completion Checklist

- [ ] Implementation done
- [ ] Self-review: `Skill({ skill: "code-review" })` run
- [ ] Security review: `Skill({ skill: "security-review" })` run (Medium risk — mandatory)
- [ ] Lint passes (N/A — Markdown only; confirm no broken links instead)
- [ ] Tests written AND pass — verification script output pasted into Evidence table (Hard-Stop Gate 5)
- [ ] `Skill({ skill: "verify" })` run — Supervisor reads the refactored CLAUDE.md end-to-end
- [ ] `memory/MEMORY.md` updated (new decision: CLAUDE.md split into docs/claude-md/*)
- [ ] Supervisor notified: task ready for Stage 4 review
