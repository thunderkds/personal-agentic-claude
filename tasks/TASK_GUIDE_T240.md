# TASK_GUIDE — T240: Rename the repo from personal-agentic-claude to easy-kit
**Date**: 2026-11-02
**Complexity Level**: C2
**Risk Level**: Medium
**Priority**: P1
**Assigned agent**: common-infrastructure
**Agent guide**: `agents/common-infrastructure.md`
**Board**: `PROJECT_KANBAN.md`

---

## Mandatory Startup (Do Not Skip)

Before writing any code:
1. Read `PROJECT_SPEC.md`
2. Use the memory slice in your spawn prompt (`<!-- memory-slice -->`). Read `memory/MEMORY.md` in full only if your work reaches a file, hook, skill or decision the slice does not cover
3. Read this file completely
4. Read `agents/common-infrastructure.md`
5. Note the **Complexity Level** above and apply the matching process from its Complexity matrix
6. Read `docs/brainstorming/BRAINSTORMING_LOG_naming.md` and `RUNBOOK.md` (deploy section)

---

## Requirement (Pillar 1 — Adapt the requirement)

User, 2026-11-02: "plan to update the name personal agentic claude to another naming", then accepted `easy-kit`.

**Restated intent**:
> The repo is `thunderkds/easy-kit`, so one thing has one name. Every existing install keeps working, and the old install line keeps working or fails with a clear message.

**Supervisor design decisions** (binding):
- **D1 — Prove the redirect first.** Create a throwaway repo, rename it, then test the old `raw.githubusercontent.com` URL, `git clone`, and `update.sh`'s fetch by the old URL. Report the result before any edit. If the old raw URL does not redirect, stop and report `Status: blocked` with a `Question:` line.
- **D2 — The GitHub rename is the user's.** No agent runs it. This task prepares the code; the Supervisor gives the user the exact step.
- **D3 — Live files only.** 41 lines in 15 files. History stays as written.
- **D4 — Vercel.** The URL `personal-agentic-claude.vercel.app` is a separate project name. List what must change, including family site links. Do not change the Vercel project.

**Out of scope**: renaming the plugin (already `easy-kit`), the product name, T236's install docs.

**Requirement Refs**: `docs/brainstorming/BRAINSTORMING_LOG_naming.md`.

### Requirement Fidelity Gate (sign off BEFORE implementation)

- [x] Restated intent confirmed to match the user's request (user, 2026-11-02)
- [x] Domain terms align with `PROJECT_SPEC.md` glossary
- [x] Every Acceptance Criterion below traces to a line in the Requirement or D1–D4
- [x] Requirement Refs filled

---

## Dependencies & Reachability

**Depends on**: T239, T235
**Entry point**: `setup.sh`, `update.sh`

---

## Acceptance Criteria

| # | Criterion (testable) | Traces to |
|---|----------------------|-----------|
| 1 | The D1 results are pasted in `tasks/TASK_REVIEW_T240.md` | D1 |
| 2 | A test finds no `personal-agentic-claude` outside history paths and a stated allow list | D3 |
| 3 | An old install's `update.sh`, simulated, reaches the renamed repo | Restated intent |
| 4 | The D4 list is in the review file | D4 |
| 5 | Full suites pass: `python3 -m pytest tests -q`, `python3 -m pytest .claude/hooks/tests -q`, `sh scripts/smoke-install.sh` | regression |

---

## Evaluation & Acceptance (How we know the agent worked correctly)

### Success Criteria (observable, pass/fail)

| # | Given | Expect | How checked |
|---|-------|--------|-------------|
| 1 | a throwaway renamed repo | old URLs behave as D1 reports | real `curl` and `git` run |

### Verification Command (exact, runnable)

```bash
python3 -m pytest tests/test_repo_name.py -q && sh scripts/smoke-install.sh
```

### Evidence (filled by reviewer at Stage 4/5)

> Filled by the reviewer in `tasks/TASK_REVIEW_T240.md`.

---

## Demonstration

> **Moved.** See `tasks/TASK_REVIEW_T240.md`.

---

## Approach

**Pattern reference**: `tests/test_plugin_names.py` sweep test.

**Vital slice**: D1 and AC 3.
**Cut list**: rewriting history; a new domain.

---

## Edge Case Checklist

- [ ] GitHub frees the old name if someone else creates it: the redirect ends
- [ ] `SUPERVISOR_REPO` and `GITHUB_USERNAME` forks
- [ ] Remotes `origin` and `github`, worktrees
- [ ] A new repo at the old name would break the redirect: tell the user

---

## Files to Change (Predicted)

| File | Change |
|------|--------|
| `setup.sh`, `update.sh`, `README.md`, `RUNBOOK.md`, `site/*`, `scripts/memory_usage_report.py` | repo name |
| `tests/test_repo_name.py` and pins | new; pins follow |

## Files Must NOT Touch

| File | Reason |
|------|--------|
| `memory/*`, `PROJECT_KANBAN*.md` | Supervisor owns them |
| Vercel project, GitHub repo settings | the user's |

---

## Test Plan

D1 first, and stop on failure. Red first: `tests/test_repo_name.py`. Edit live files. Simulate an old install. Run the suites.

---

## Completion Checklist

- [ ] Implementation done
- [ ] Tests written AND pass — output pasted into `tasks/TASK_REVIEW_T240.md` (Hard-Stop Gate 5)
- [ ] UI Evidence rows marked N/A with a reason, or filled if `site/*` layout changes
- [ ] Supervisor notified: task ready for Stage 4 review (`code-review`, `security-review`)
