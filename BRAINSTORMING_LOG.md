# BRAINSTORMING_LOG.md
**Generated**: 2026-07-07
**Task / Context**: Meta-process gap — cross-task dependency tracking & "unreachable feature" detection in the Supervisor pipeline
**Skill**: `Skill({ skill: "brainstorming" })`

---

## The Problem Space

The Stage 2/3 pipeline splits work into independently-spawned tasks (`TASK_GUIDE_Txxx.md`), each executed by an isolated sub-agent in its own worktree. Two related failure modes have been observed in practice:

1. **Silent precondition failure**: Task B assumes an artifact from Task A (a backend endpoint, a schema field, a shared component) exists. If Task A hasn't landed yet, or landed differently than assumed, Task B's sub-agent either guesses, stubs it, or silently produces code that references something that doesn't exist — and nothing in the pipeline flags this before/during execution.
2. **Unreachable / illogical feature**: A task implements backend logic or a component with no caller — e.g. a feature with no button, route, or menu entry that would let a user (or another part of the system) actually invoke it. The task can pass its own Acceptance Criteria (the logic works in isolation) while being functionally dead code from the product's perspective. Nothing today checks "is this feature wired to something that reaches it."

Today, the only dependency-adjacent mechanisms that exist are:
- `PROJECT_KANBAN.md`'s `## Blocked` table (`Task | Reason | Waiting on`) — free-text, manually maintained, not read by any hook or gate.
- "Code-dependency blast radius" (hub files) — used only for Risk scoring and review scope, not for precondition or reachability checks.

Neither is enforced. A task can move Todo → In Progress → Ready for Review → Done without anything checking that its declared (or undeclared) dependencies actually resolved, or that its output is reachable.

**Non-negotiable constraints**:
- Must not require a full dependency-graph/static-analysis tool (Stage 1 already treats code-graph tooling as optional/absent-by-default) — the common case is no such tooling installed.
- Must not turn Stage 2 planning into a heavyweight DAG-authoring exercise — task breakdown is already tracer-bullet vertical slices via `to-issues`; dependency tracking should ride on top of that, not replace it.
- Must fail safely: a false-positive "possible gap" warning should never hard-block a task the way Hard-Stop Gates do — those are reserved for evidence/test gates. Dependency/reachability checks are advisory unless the user explicitly wants them to hard-block.

---

## Questions for the User

Resolved via `AskUserQuestion` before this log was finalized:

1. **Detection mode** — declarative-only vs. detected-only vs. both? → **Answered: Declarative + detected (both).**

Still open (deferred to Stage 2 planning / TASK_GUIDE authoring, not architectural):
2. Should the reachability check ("does this feature have a UI trigger") apply only to frontend/UI tasks, or also to backend endpoints that should be called by *something* (another service, a cron, a queue consumer)? Recommend: generalize to "declared entry point" rather than "UI button" specifically — same mechanism covers both.

---

## Alternative Paths

| Option | Name | Summary | Invasiveness | Code Volume | Regression Risk | Recommended? |
|--------|------|---------|-------------|------------|----------------|--------------|
| A | Declarative-Only (KANBAN field) | Add a structured `Depends on:` / `Reachable via:` field to TASK_GUIDE + KANBAN; Supervisor fills it at Stage 2; purely documentary | Low | ~30 lines (template edits) | Low | |
| B | Detected-Only (grep-based hook) | A hook/skill scans task guides and diffs for dependency signatures (referenced-but-missing files/endpoints, components with no importer) and warns | Medium | ~150 lines (new skill/hook) | Medium (heuristic false positives) | |
| C | Declarative + Verified (Hybrid) | Supervisor declares dependencies/entry-points at Stage 2 (source of truth in TASK_GUIDE); a Stage 3/4 hook or skill step verifies the declared precondition actually resolved before letting the dependent task proceed or a review pass complete | Medium | ~180 lines (template + hook/skill) | Low–Medium | ✅ Yes |

### Option A — Declarative-Only
**Approach**: Add a `## Dependencies` section to `TASK_GUIDE_template.md` (`Depends on: Txxx — [artifact]`, `Entry point: [route/button/caller] or Standalone — N/A`) and a parallel column in `PROJECT_KANBAN_template.md`. Supervisor fills it in at Stage 2 planning as part of task breakdown; sub-agents read it as context.
**Pros**: Trivial to implement; zero false positives (nothing is auto-detected); works everywhere regardless of stack/tooling.
**Cons**: Relies entirely on the Supervisor remembering to fill it in accurately and completely — this is the exact failure mode the user is reporting today, just with a new field to forget. Provides no mechanism to actually *catch* the problem when it happens, only a place to have documented intent to avoid it.
**Why it might fail**: Under time pressure, the Supervisor (or a rushed planning pass) will skip or under-fill the field, exactly as `PROJECT_KANBAN.md`'s existing `## Blocked` table is under-used today. Documentation-only fixes for enforcement gaps regress to their pre-fix state within a few sessions.

### Option B — Detected-Only
**Approach**: A new skill (`dependency-check` or folded into `code-review`) statically scans a task's diff for signatures of the two failure modes: (1) calls to endpoints/imports of files that don't exist in the current tree or another task's declared output, (2) newly-added functions/components/routes with zero inbound references anywhere in the repo (a basic "is this dead code" grep, not full call-graph analysis).
**Pros**: No reliance on the Supervisor's memory; catches the problem even if nobody thought to declare it.
**Cons**: Heuristic grep-based detection has real false-positive/false-negative rates — a component wired via dynamic import, a config-driven route table, or a plugin registry would all look "unreferenced" to a naive grep and generate noise. Noisy warnings erode trust in the check (same "cry wolf" risk the Hard-Stop Gates docs explicitly warn against). No tooling exists yet in this repo for cross-file reference resolution beyond `Grep`/`Glob`.
**Why it might fail**: First real use surfaces several false positives on legitimate dynamic-dispatch patterns; the Supervisor starts ignoring the warnings, and the check becomes theater — worse than not having it, because it creates false confidence.

### Option C — Declarative + Verified (Hybrid)
**Approach**: Two-part mechanism, mirroring the pattern already proven by the recent guardrail-hooks work (declared claim + independently-verified evidence, not self-report):
1. **Declare** (Stage 2, `to-issues`/planning): `TASK_GUIDE_template.md` gains a `## Dependencies & Reachability` section with two structured fields:
   - `Depends on: [Txxx — artifact name]` or `None`
   - `Entry point: [route/button/caller/consumer]` or `Standalone — N/A` (with a one-line reason if N/A)
2. **Verify** (Stage 3/4): a lightweight check — either a hook (`pre_agent_validate_guide.py` extended, since it already gates Agent spawns on TASK_GUIDE existence) or a step inside `code-review` — that:
   - Before spawning a dependent task: confirms the declared upstream Task is `Done` on `PROJECT_KANBAN.md`, or explicitly flags "spawning Txxx before its declared dependency Txxx is Done — confirm this is intentional (e.g. parallel stub work)."
   - At Stage 4 review: if `Entry point` is not `N/A`, greps for the declared entry point string (route path, button label, function call site) in the diff/repo; if not found, adds a review finding "declared entry point not found — feature may be unreachable" rather than silently passing.
**Pros**: Keeps the low-cost, always-correct part (explicit declaration) as source of truth, and adds just enough automated cross-check to catch the "forgot to wire it up" and "spawned out of order" cases without needing a real dependency graph. Fails toward a warning/finding, not a hard block — matches the existing Hard-Stop Gate philosophy of reserving hard blocks for evidence gates.
**Cons**: More surface area than Option A; the verification step is still string/heuristic-based (not perfect), though narrower in scope than B because it only checks *declared* entry points rather than guessing at all code.
**Why it might fail**: If the Supervisor declares a vague/wrong entry-point string (e.g. "the settings page" instead of an actual route path), the grep check will false-negative (nothing found even though it's wired correctly) — mitigated by requiring the declared string to be a literal snippet expected to appear in code (route path, function name, component name), not free prose.

---

## 50% Rule Check

For Option C: the "verify" half could be cut to just the ordering check (is the declared upstream task Done before spawn) and drop the entry-point grep — that's roughly 50% less code (no grep/finding logic in `code-review`, just an extension to the existing `pre_agent_validate_guide.py` hook). This trades away the "unreachable feature" half of the original problem, keeping only the "precondition ordering" half. Not recommended as the default, since the user's report explicitly named *both* failure modes (dependency ordering *and* missing UI trigger) — but flagged here as a valid fallback if Stage 4 review time budget is a concern on a given project.

---

## Recommended Path

**Option C — Declarative + Verified (Hybrid)**

This is the same shape as the guardrail-hooks change just shipped (`feat/deterministic-guardrails-hooks`): don't trust a self-report alone, but don't require full static analysis either — declare the claim where a human/Supervisor already has the context (Stage 2), then cheaply verify the claim's minimal, checkable form (ordering + literal string presence) where the harness already has a gate (`pre_agent_validate_guide.py`, `code-review`). It directly answers the user's two complaints: "feature B needs feature A as a precondition" (ordering check) and "no warning for a feature with no button to trigger it" (entry-point check) — without inventing new heavyweight tooling.

---

## Surgical Scope

Files that **should** be touched (next actions, not yet implemented):
- `templates/TASK_GUIDE_template.md` — add `## Dependencies & Reachability` section
- `templates/PROJECT_KANBAN_template.md` — add a `Depends on` column/notation to task lines (optional, for at-a-glance view)
- `.claude/hooks/pre_agent_validate_guide.py` — extend to parse `Depends on:` and check the referenced task's KANBAN status before allowing spawn
- `.claude/skills/code-review/SKILL.md` — add an "Entry-point reachability" check step for tasks with `Entry point:` declared
- `CLAUDE.md` — document the new TASK_GUIDE section and the Stage 2/4 responsibilities around it

Files that **must not** be touched:
- Existing Hard-Stop Gates 1–6 in `CLAUDE.md` — this is a new advisory check, not a hard block; do not fold it into the hard-stop numbering without explicit user decision
- `.claude/hooks/pre_bash_block_unsafe_merge.py` — the push/merge gate is about verify evidence, not dependency ordering; keep concerns separated

---

## Edge Case Checklist for TASK_GUIDE

- [ ] Declared `Depends on: Txxx` where Txxx doesn't exist in `PROJECT_KANBAN.md` (typo) — hook should flag as "unknown dependency," not silently pass
- [ ] Two tasks declare a circular dependency (A depends on B, B depends on A) — hook should detect and block with a clear message, this is a planning error not an execution one
- [ ] Task legitimately needs to start before its dependency finishes (e.g. parallel stub-and-integrate work) — the ordering check must be a confirmable warning, not a hard block, or this pattern becomes impossible
- [ ] `Entry point:` declared as vague prose ("the dashboard") instead of a literal grep-able string — Stage 2 must reject vague entry-point declarations and require a literal identifier
- [ ] Backend-only task with a legitimate external caller (webhook, cron, message consumer) outside this repo — `Entry point: N/A` with reason must be accepted, not flagged as unreachable

---

## Next Actions

1. Update `templates/TASK_GUIDE_template.md` and `templates/PROJECT_KANBAN_template.md` with the new Dependencies & Reachability fields.
2. Extend `.claude/hooks/pre_agent_validate_guide.py` to check declared `Depends on:` task status at spawn time (warn, don't hard-block).
3. Add an entry-point reachability check step to `.claude/skills/code-review/SKILL.md`.
4. Document the new section and its Stage 2/4 responsibilities in `CLAUDE.md`.
5. Run `Skill({ skill: "grill-with-docs" })` next to stress-test this direction's terminology and lock it before implementation (per the user's request to also run `/grill-with-docs`).

---

## User Selection

> **Approved direction**: Option C — Declarative + Verified (Hybrid)
> Approved by user on 2026-07-07 (via `AskUserQuestion`: "Declarative + detected (Recommended)").
