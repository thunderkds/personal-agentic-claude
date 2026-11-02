# BRAINSTORMING_LOG_naming.md

**Date**: 2026-11-02
**Tier**: Standard
**Request (user, verbatim)**: "plan to update the name personal agentic claude to another naming, by the way should we merge the 0.5 and 1.5 stage, the .5 look does not professional as is, if we must use, it should be 1a, 1b or something like that, let brainstorming"

---

## The Problem Space

**Name.** The repo is `thunderkds/personal-agentic-claude`. The product is already called Easy Kit on the site and README, and the plugin is `easy-kit`. The repo name says "personal" and "claude", yet the kit also serves Codex and is meant for other people. So one thing has two names.

**Stages.** The pipeline has 8 steps: Phase 0, 0.5, 1, 1.5, 2, 3, 4, 5, yet the doctrine calls it the "5-stage pipeline". Half numbers read as afterthoughts.

Measured on `main` @ `c86dd1f3`, excluding `tasks/`, `memory/`, archives, old brainstorm logs and PRDs:

| Item | Lines | Files |
|---|---|---|
| `personal-agentic-claude` | 41 | 15 |
| `Stage 0.5` | 43 | 20 |
| `Stage 1.5` | 20 | 13 |
| `Phase 0` | 64 | 34 |
| `0.5a` / `0.5b` forms | 10 | 5 |

Code that names a stage: `scripts/token_audit.py:34-40` tags (`stage-0.5`, `stage-1.5`), and the message at `.claude/hooks/pre_agent_validate_guide.py:439`, pinned by `.claude/hooks/tests/test_pre_agent_validate_guide.py:327`. No hook parses a stage number to decide anything.

Name check, 2026-11-02: `github.com/thunderkds/easy-kit` answers 404, so the name is free there. Web searches found no project named exactly Easy Kit or EasyKit in this field. Near names exist: `agent-kit`, `claudekit`, `easydev`, and Easy App Kit on npm. Searches do not prove a name is free or unregistered.

---

## The Alternatives

### Path A — Stage 0–5, repo `easy-kit` (recommended)

Merge Phase 0 + 0.5 into **Stage 0: Define**. Merge 1 + 1.5 into **Stage 1: Set up**. Stages 2–5 keep their numbers. Old steps become named steps inside a stage, with no number.

Pros: every "Stage 2/3/4/5" in the docs, skills, memory and task history stays true. It matches "5-stage pipeline" plus a stage 0. Smallest rewrite that removes all half numbers.
Cons: Stage 0 and Stage 1 each do more, so their doc sections grow.

### Path B — Stage 1–6, repo `easy-kit`

Define, Set up, Plan, Build, Review, Ship as 1–6.

Pros: reads most cleanly: starts at 1.
Cons: every later number shifts, so old "Stage 3" means build and new "Stage 3" means plan. About 1,000 tracked files keep history in the old meaning. Highest confusion.

### Path C — Letters 0a, 0b, 1a, 1b, repo `easy-kit`

Phase 0 becomes 0a, 0.5 becomes 0b, 1 becomes 1a, 1.5 becomes 1b. The user's suggestion.

Pros: a one-to-one rename: no step merges, simplest edit.
Cons: still 8 steps, so the page stays as long and the "5-stage" mismatch stays.

### Name options, for any path

- `easy-kit`: one name across repo, plugin, site. Recommended.
- A distinctive new brand: easier to search for, but it renames the site, plugin and family too. Not proposed without a name from the user.

---

## 50% Rule Check

Rename only the labels and edit no gate logic. The stage work is text. For the name, change only live files: history stays as written, because GitHub redirects old URLs.

---

## Adversarial Review

- **Path A**: a guide says "Stage 0.5 grilling" in history. Fix: one mapping line in `docs/claude-md/pipeline-stages.md`; history is not rewritten.
- **Readiness** (`PROJECT_SPEC.md`) keys name stages by doc text (T223): update its wording and the template together.
- **Rename**: the install line `curl .../personal-agentic-claude/main/setup.sh` is public. Confirm that the old raw URL still redirects before and after. If it does not, every old install line and `update.sh` breaks. This must be tested on a real rename, and it is hard to undo cleanly.
- **Rename**: an existing install's Update reads its repo URL: an old copy points at the old name.
- **Vercel**: the site URL `personal-agentic-claude.vercel.app` is a separate project name, and the family sites link to it. Renaming needs a redirect.
- **Local**: remotes `origin` and `github` and worktrees use the old URL.
- **T236**: it publishes install commands, so the rename must come first. T235 runs before it either way.

---

## Surgical Scope

**Should touch**: `AGENTS.md`, `docs/claude-md/*`, `skills/*/SKILL.md`, `agents/*.md`, `templates/*`, `site/*`, `README.md`, `setup.sh`, `update.sh`, `scripts/token_audit.py`, the hook message, the tests pinning them.

**Must not touch**: `tasks/`, `memory/` history, archives, gate logic.

---

## Edge Case Checklist for TASK_GUIDE

- [ ] Old raw `setup.sh` URL answers after the rename
- [ ] `update.sh` in an old install still finds the repo
- [ ] `index.html` keeps at most 300 words after the stage labels change
- [ ] `tests/fixtures/site_story_baseline.json` baseline updated with a stated reason
- [ ] `T070_BASELINE_REF` repointed for the `AGENTS.md` edit
- [ ] Skill byte sizes stay under the Codex 8192-byte limit

---

## Design Review of the Merge (user: "if we merge, it good about the UI, but is it good about the design", 2026-11-02)

**Why the half numbers exist.** `5ca3c1a5` (2026-04-16) already had Phase 0, Stage 1 and Stage 1.5. `fb361179` (2026-05-11) added Stage 0.5 as 5 lines under the fixed "5-Stage" title. Nothing recorded a design reason for the numbers: `docs/adr` and `docs/ddr` never name them. The half number is how a step was inserted without renumbering.

**What does carry design weight: the stops.**

| Today | Purpose | Stop | Proof it is done |
|---|---|---|---|
| Phase 0 | Fix what is wanted | User confirms the PRD | `Requirements`, `Approved by` |
| 0.5a | Test the requirement | PRD gate: PASS | none of its own |
| 0.5b | Explore options | User picks a direction | `Direction` |
| Stage 1 | Prepare the repo | Checklist | `Codebase map`, `Tech stack` |
| 1.5 | Pick agents | User approves the team | none |

**Stage 0 merge is safe only with its 3 stops kept, in order.** Phase 0 converges and 0.5b diverges, so they are different work. T223's idea-radar case shows the cost of skipping them: a spawn 5 minutes after install, with architecture holes found after coding started. The hook checks Readiness lines, not stage numbers, so a label change cannot weaken it. A doc rewrite that flattens the steps could.

**Stage 1 merge improves the design.** The base team is unconditional, so the 1.5 stop asks the user to approve a fixed answer unless a new role is needed. `craft-agent` is already optional.

**Conditions on Path A:**
1. Stage 0 keeps three named steps in order, Requirements, Grilling, Direction, each with its stop.
2. "Stage done" stays per Readiness line. No Readiness line, hook or auto-mode rule changes.
3. The team stop fires only when `craft-agent` proposes a new role. User approved this behaviour change, 2026-11-02 ("go").

**Found, not part of this work:** `map-codebase` runs in Stage 1, after brainstorming, so on an existing repo the direction is chosen before the map exists.

---

## Next Actions

**Direction approved by the user, 2026-11-02: Path A, Stage 0–5, repo `easy-kit`.** Stage 2 writes the tasks: stage labels first, before T235 so `init` ships the new docs; repo rename after that, before T236. The rename on GitHub is the user's go-ahead.
