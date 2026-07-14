## Bug Fix Task Guide — T020
**Date**: 2026-07-14
**Complexity Level**: C1
**Risk Level**: Low
**Priority**: P2
**Assigned agent**: common-infrastructure
**Agent guide**: `.claude/agents/common-infrastructure.md`

### Mental Model (confirmed by user)
- Observed: `.gitignore` marks `tasks/*`, `memory/*`, `PROJECT_SPEC.md`, `PROJECT_KANBAN.md`, `BRAINSTORMING_LOG.md`, and `reports/` as "per-project files, never commit to this repo" (framework-distribution framing). But `git ls-files` shows `memory/MEMORY.md`, `tasks/TASK_GUIDE_T001_EXAMPLE.md`, `PROJECT_SPEC.md`, `PROJECT_KANBAN.md`, and `reports/*.html` are already tracked in this repo. The user has confirmed this repo is being used as a **live dogfood instance**, not just a template distribution — so this state (tracked project files) is the intended one, and `.gitignore` is the thing that's wrong.
- Expected: `.gitignore` should stop ignoring the categories of files this repo actually needs tracked as a live instance: `PROJECT_SPEC.md`, `PROJECT_KANBAN.md`, `BRAINSTORMING_LOG.md`, `memory/*` (except truly ephemeral state), and enough of `tasks/*` to keep real guides versioned. `reports/` (generated HTML) can reasonably stay ignored since it's regenerable output, unless the user wants historical reports kept — confirm scope with user during implementation if ambiguous.
- Likely divergence point: `.gitignore` Section 1 ("Project-specific files (never commit to this repo)") was written for the template-distribution use case and never updated when this repo started being used live.
- Recent context: T004 ("`.gitignore` + repo hygiene") was completed 2026-06-10 — this predates the live-instance usage pattern that produced the currently-tracked files, which is likely why the mismatch exists.

### Intake
- Trigger: none (config drift) — compare `.gitignore` Section 1 patterns against `git ls-files` output.
- Severity: P2.
- Affected area: `.gitignore` only. No source code changes. Must not remove already-tracked files from git (that would be Bug 3's "distribution" option, which was explicitly rejected).

### Complexity & Risk
- Complexity: C1
- Risk: Low

### Diagnosis Gates (Pillar 1 — must pass before any fix)
- [ ] Phase 1 feedback loop: run `git ls-files | grep -E '^(memory/|tasks/|reports/|PROJECT_SPEC.md|PROJECT_KANBAN.md|BRAINSTORMING_LOG.md)'` and `git status --ignored` to see the full current mismatch between tracked files and `.gitignore` patterns.
- [ ] Bug reproduces deterministically: confirm `git check-ignore -v PROJECT_SPEC.md PROJECT_KANBAN.md memory/MEMORY.md tasks/TASK_GUIDE_T001_EXAMPLE.md` shows these are ignored despite being tracked.
- [ ] No hypothesis ranking needed — root cause is confirmed (stale gitignore section), only the exact new pattern set needs deciding.

### Fix Gates (Pillar 2)
- [ ] Update `.gitignore` Section 1 so it no longer ignores files this live instance intends to keep tracked: remove or scope down the `tasks/*`, `memory/*`, `PROJECT_SPEC.md`, `PROJECT_KANBAN.md`, `BRAINSTORMING_LOG.md` entries. Keep ignoring genuinely ephemeral/generated content (e.g. `.claude/hooks/.state/`, `memory/event-trace/`, and — unless the user says otherwise — `reports/`).
- [ ] Regression check (no-seam documented): this is a config file, not a test seam — verify instead with `git status` (should show no newly-untracked-then-ignored conflicts) and `git check-ignore -v` on the previously-mismatched files (should now report "not ignored" for files meant to stay tracked).
- [ ] Fix matches "correct behaviour": `git status` cleanly reflects that `PROJECT_SPEC.md`, `PROJECT_KANBAN.md`, `memory/MEMORY.md`, and real `tasks/TASK_GUIDE_*.md` files are tracked-and-not-ignored; only genuinely ephemeral paths remain ignored.

### Cleanup Checklist (Pillar 3)
- [ ] No instrumentation to remove
- [ ] No prototypes to delete
- [ ] Commit message explains the live-instance vs. distribution framing decision
- [ ] Post-mortem: what would have prevented this? (gitignore should be revisited whenever a repo's usage mode changes from template to live instance — flag as a note in `memory/decisions.md`)

### Evidence
| Check | Command / observation | Result |
|---|---|---|
| Repro loop | `git ls-files \| grep -E '^(memory/\|tasks/\|reports/\|PROJECT_SPEC.md\|PROJECT_KANBAN.md\|BRAINSTORMING_LOG.md)'` → `memory/MEMORY.md`, `tasks/TASK_GUIDE_T001_EXAMPLE.md`; `git status --ignored` showed `PROJECT_SPEC.md`, `PROJECT_KANBAN.md`, `BRAINSTORMING_LOG.md`, all real `tasks/TASK_GUIDE_T0*.md`, `memory/decisions.md`, `memory/glossary.md`, `memory/learnings.md`, `memory/learning-records/` sitting as `!!` (untracked-and-ignored) — confirmed mismatch: live-instance files existed on disk but were shadowed by `.gitignore` | Confirmed |
| Bug reproduces deterministically | `git check-ignore -v PROJECT_SPEC.md PROJECT_KANBAN.md memory/MEMORY.md tasks/TASK_GUIDE_T001_EXAMPLE.md` → `.gitignore:14:PROJECT_SPEC.md  PROJECT_SPEC.md` and `.gitignore:15:PROJECT_KANBAN.md  PROJECT_KANBAN.md` (memory/MEMORY.md and tasks/TASK_GUIDE_T001_EXAMPLE.md did not report, since they're already tracked — `check-ignore` doesn't flag tracked files, but their patterns `memory/*` / `tasks/*` were still present in `.gitignore` Section 1 and would re-ignore them if ever untracked) | Confirmed |
| Regression test (no-seam, config-only) | After edit: `git check-ignore -v PROJECT_SPEC.md PROJECT_KANBAN.md memory/MEMORY.md tasks/TASK_GUIDE_T001_EXAMPLE.md BRAINSTORMING_LOG.md` → exit code 1, no output (none of these paths are ignored anymore) | Pass |
| Fix matches correct behaviour | `git status` now lists `PROJECT_SPEC.md`, `PROJECT_KANBAN.md`, `BRAINSTORMING_LOG.md`, `memory/decisions.md`, `memory/glossary.md`, `memory/learnings.md`, `memory/learning-records/`, and all `tasks/TASK_GUIDE_T0*.md` as **Untracked files** (visible, trackable) instead of silently ignored; `git status --ignored` shows only `.claude/hooks/.state/`, `.claude/hooks/__pycache__/`, `.claude/settings.local.json`, `memory/event-trace/`, and `reports/` remain ignored (genuinely ephemeral/generated, no tracked files under those paths were disturbed) | Pass |
| Smoke suite | N/A — config-only change, no test suite applicable; `git diff --stat` confirms only `.gitignore` was modified, no other file contents touched | Pass (N/A justified) |
