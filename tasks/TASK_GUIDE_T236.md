# TASK_GUIDE — T236: Real plugin install proven, then published on the README and site
**Date**: 2026-11-02
**Complexity Level**: C2
**Risk Level**: Medium
**Priority**: P1
**Assigned agent**: frontend-developer
**Agent guide**: `agents/frontend.md`
**Board**: `PROJECT_KANBAN.md`

---

## Mandatory Startup (Do Not Skip)

Before writing any code:
1. Read `PROJECT_SPEC.md` and `PROJECT_SPEC_SITE.md`
2. Use the memory slice in your spawn prompt (`<!-- memory-slice -->`). Read `memory/MEMORY.md` in full only if your work reaches a file, hook, skill or decision the slice does not cover
3. Read this file completely
4. Read `agents/frontend.md`
5. Note the **Complexity Level** above and apply the matching process from its Complexity matrix
6. Read `tests/test_site_story.py`: `index.html` is at its 300-word cap

---

## Requirement (Pillar 1 — Adapt the requirement)

User, 2026-11-02: chose the five-task split ("T236 Real install, then publish. Install in a clean repo, prove the gates block, then update site/README.").

**Restated intent**:
> A person with no access beyond the public repo installs the plugin from GitHub in a clean project, and the gates block. Only then do the README and site offer the plugin. Every sentence about it is true of what was run.

**Supervisor design decisions** (binding):
- **D1 — Prove first.** Run the install with anonymous access: `GIT_TERMINAL_PROMPT=0` and no credential helper, from `thunderkds/personal-agentic-claude`. Paste the real output. If it fails, stop and report; publish nothing.
- **D2 — Publish.** README install section: two paths, plugin and `setup.sh`. `docs.html#install`: the same. `index.html`: at most a short mention in `hero`, staying within 300 words; say what you cut.
- **D3 — Honest limits.** Docs state: Claude Code only; run `/easy-kit:init` once; each teammate installs the plugin; a plugin cannot set permissions.
- **D4 — Claims audit.** List every new sentence with what proves it in `tasks/TASK_REVIEW_T236.md` (T231 learning).

- **D5 — Carried from T233's verify.** Measure what a git-sourced install copies. A local install was 18 MB, with `tests/`, `tasks/`, `experiments/` and `memory/`. Report the size, and whether a smaller plugin source is worth a follow-up.

**Out of scope**: easy-memory in the marketplace (T217 stays deferred), Codex.

**Requirement Refs**: `docs/brainstorming/BRAINSTORMING_LOG_distribution.md` Option C.

### Requirement Fidelity Gate (sign off BEFORE implementation)

- [x] Restated intent confirmed to match the user's request (user approved this task's text, 2026-11-02)
- [x] Domain terms align with `PROJECT_SPEC.md` glossary
- [x] Every Acceptance Criterion below traces to a line in the Requirement or D1–D4
- [x] Requirement Refs filled

---

## Dependencies & Reachability

**Depends on**: T232, T233, T234, T235 (all merged and pushed: the install reads GitHub)
**Entry point**: `README.md`, `site/docs.html#install`

---

## Acceptance Criteria

| # | Criterion (testable) | Traces to |
|---|----------------------|-----------|
| 1 | Anonymous `claude plugin marketplace add` and `claude plugin install easy-kit@easy-kit` succeed; output pasted | D1 |
| 2 | In a clean repo after `/easy-kit:init`, a spawn with no guide and a `git push` with an open task are both blocked; output pasted | D1 |
| 3 | README and `docs.html#install` show both paths with their exact commands; a test pins the commands | D2 |
| 4 | D3 limits appear in `docs.html#install`; a test pins them | D3 |
| 5 | The D4 table exists, with no sentence unproven | D4 |
| 6 | Full suites pass: `python3 -m pytest tests -q`, `node --test tests/settings_tool/*.mjs`, `node --test tests/site_scrollspy/*.mjs` | regression |

---

## Evaluation & Acceptance (How we know the agent worked correctly)

### Success Criteria (observable, pass/fail)

| # | Given | Expect | How checked |
|---|-------|--------|-------------|
| 1 | a clean temp repo and anonymous git | the commands on the page work as written | headless run, budget at most $1, on model haiku |

### Verification Command (exact, runnable)

```bash
python3 -m pytest tests/test_site_content.py tests/test_site_story.py tests/test_plugin_package.py -q
```

### Evidence (filled by reviewer at Stage 4/5)

> Filled by the reviewer in `tasks/TASK_REVIEW_T236.md`.

---

## Demonstration

> **Moved.** See `tasks/TASK_REVIEW_T236.md`.

---

## UI / Design Acceptance Criteria

### 1. Visual Regression
| Screen / Component | Method | Expected |
|---|---|---|
| `docs.html#install`, `index.html` hero | screenshot at 1440 px, before and after | plugin path shown, layout unchanged |

### 2. Design-System Compliance
| Criterion | Method | Expected |
|---|---|---|
| Colors | existing hex test | tokens only |

### 3. Layout / Responsiveness
| Viewport | Method | Expected |
|---|---|---|
| 1440 / 768 / 375 | `scrollWidth == clientWidth` | no sideways scroll, long commands wrap |

---

## Approach

**Pattern reference**: the `.codebox` Copy block in `#install`.

**Vital slice**: AC 1 and AC 2.
**Cut list**: a third install path; a version badge.

---

## Edge Case Checklist

- [ ] A push to `main` deploys the site at once (`RUNBOOK.md`): merge only after AC 1 and AC 2 pass
- [ ] Copy button works on a second codebox

---

## Files to Change (Predicted)

| File | Change |
|------|--------|
| `README.md` | two install paths |
| `site/docs.html`, `site/index.html`, `site/theme.css` | plugin path |
| `tests/test_site_content.py`, `tests/test_site_story.py` | pin commands and limits |

## Files Must NOT Touch

| File | Reason |
|------|--------|
| `setup.sh` | in-repo mode stays as it is |
| `memory/*`, `PROJECT_KANBAN*.md` | Supervisor owns them |

---

## Test Plan

Do D1 first, and stop on failure. Red first for the pins. Edit the docs. Take screenshots with `file://` URLs. Run the full suites.

---

## Completion Checklist

- [ ] Implementation done
- [ ] Tests written AND pass — output pasted into `tasks/TASK_REVIEW_T236.md` (Hard-Stop Gate 5)
- [ ] All three UI Evidence rows filled (Hard-Stop Gate 6)
- [ ] Supervisor notified: task ready for Stage 4 review
