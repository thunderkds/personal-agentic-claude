# TASK_GUIDE — T035: README.md — update install/update instructions
**Date**: 2026-07-17
**Complexity Level**: C0
**Risk Level**: Low
**Priority**: P1
**Assigned agent**: backend-developer
**Agent guide**: `.claude/agents/backend.md`

---

## Mandatory Startup (Do Not Skip)

Before writing any code:
1. Read `PROJECT_SPEC.md`
2. Read `memory/MEMORY.md`
3. Read this file completely
4. Read `.claude/agents/backend.md`
5. C0 — lightweight process per the Complexity matrix in `.claude/agents/general-agent-template.md`

---

## Requirement (Pillar 1 — Adapt the requirement)

`README.md` documents the old `~/.supervisor` central-clone + symlink install/update model, now superseded by ADR-0001. This task updates the documentation to match the shipped T032/T033 behavior — no code changes.

**Restated intent**:
> Update `README.md`'s install/update sections to describe the new direct-to-repo model: `setup.sh` fetches fresh and copies real files into the working repo (no `~/.supervisor` dependency), `update.sh` is a separate script that hash-compares and prompts on conflicts, and both require the target directory to already be a git repo.

**Out of scope**:
- Does not change any behavior — documentation only.
- Does not document the deferred migration path (doesn't exist yet) — if `README.md` currently has nothing about migrating existing installs, don't invent guidance for it.

**Requirement Refs**: ADR-0001 (Follow-up — "README.md needs its install/update instructions updated")

### Requirement Fidelity Gate (sign off BEFORE implementation)

- [ ] Restated intent confirmed to match ADR-0001's Follow-up item
- [ ] Domain terms align with `PROJECT_SPEC.md` glossary (do not reintroduce "Central clone" as current-state language — it's marked superseded)
- [ ] Every Acceptance Criterion below traces to ADR-0001
- [ ] Requirement Ref (ADR-0001) is fully covered by the Acceptance Criteria below

> An agent must NOT start implementing until this gate is checked. If anything here is unclear, STOP and ask the Supervisor.

---

## Dependencies & Reachability

**Depends on**: `T033 — update.sh must be finalized so its actual CLI/behavior is documented accurately, not speculatively`

**Entry point**: `Standalone — N/A: documentation file, read by users, not executed or imported by any code path.`

---

## Acceptance Criteria

| # | Criterion (testable) | Traces to requirement |
|---|----------------------|-----------------------|
| 1 | `README.md`'s install section describes `setup.sh` as fetching fresh and copying real files, with no mention of `~/.supervisor`/`SUPERVISOR_PATH` as a persistent requirement | ADR-0001 |
| 2 | `README.md` documents `update.sh` as a separate command, explains the conflict-prompt behavior on customized files in plain language | ADR-0001 |
| 3 | `README.md` documents the new git-repo prerequisite ("target directory must already be a git repository") | ADR-0001 |
| 4 | No stale reference to the symlink model remains anywhere in `README.md` (grep for "symlink", "~/.supervisor", "central clone" and confirm each remaining hit is either removed or intentionally historical) | ADR-0001 |

---

## Evaluation & Acceptance (How we know the agent worked correctly)

### Success Criteria (observable, pass/fail)

| # | Given (input/state) | Expect (output/behavior) | How it's checked |
|---|---------------------|--------------------------|------------------|
| 1 | `grep -i "symlink\|supervisor_path\|central clone" README.md` after the edit | No unintended hits (or only intentional historical/changelog mentions) | manual grep check |
| 2 | A new user follows the README's install steps verbatim against the real `setup.sh`/`update.sh` from T032/T033 | Steps match actual script behavior exactly | manual walkthrough |

### Verification Command (exact, runnable)

```bash
grep -in "symlink\|supervisor_path\|~/.supervisor\|central clone" README.md
```

### Evidence (filled by reviewer at Stage 4/5)

| Check | Result | Notes / output snippet |
|-------|--------|------------------------|
| **New test(s) cover Acceptance Criteria (file paths pasted)** | N/A | Documentation-only task, C0 — no automated test surface; verification is the grep command + manual walkthrough above |
| Verification command run | ☐ pass / ☐ fail | |
| Negative cases hold | N/A | |
| `verify` skill — works in running app | ☐ pass / ☐ fail | Manual: follow README steps against real setup.sh/update.sh |
| Review scope bounded to the change's blast radius (affected set, not whole repo) | ☐ pass / ☐ fail | |
| Full smoke suite still green (no regression) | ☐ pass / ☐ fail | |
| **UI: Visual regression** | N/A | Pure documentation task — no UI component |
| **UI: Design-system compliance** | N/A | Pure documentation task — no UI component |
| **UI: Responsiveness** | N/A | Pure documentation task — no UI component |

---

## Approach

Read the current `README.md` install/update sections in full first, then rewrite in place to match T032/T033's actual shipped CLI surface (flags, prompts, error messages) rather than this task guide's prose — the guide describes *intent*, the finished T032/T033 code is the source of truth for exact wording.

---

## Edge Case Checklist

- [ ] If `README.md` documents `SUPERVISOR_PATH` as an env var override anywhere, remove or repurpose that documentation to match whatever (if anything) T032/T033 still uses it for
- [ ] If `README.md` has a "how packs work" section referencing the central clone, leave pack documentation as-is (packs are out of scope for ADR-0001) but don't let it contradict the now-updated base-install section

---

## Files to Change (Predicted)

| File | Change |
|------|--------|
| `README.md` | Update install/update sections to match the new direct-to-repo model |

## Files Must NOT Touch

| File | Reason |
|------|--------|
| `setup.sh`, `update.sh`, `lib/harness-fetch.sh` | Implementation is fixed by T031/T032/T033 — this task only documents it |
| Packs documentation | Out of scope per ADR-0001 — packs keep current model |

---

## Test Plan

Grep-based check for stale terminology (see Verification Command) plus one manual walkthrough of the documented steps against the real finished scripts.

---

## Completion Checklist

- [ ] Implementation done
- [ ] Self-review: `Skill({ skill: "code-review" })` run
- [ ] Security review: N/A — Low risk, documentation only
- [ ] Lint passes: N/A
- [ ] Tests written AND pass — N/A (documentation-only, see Evidence table)
- [ ] `Skill({ skill: "verify" })` run — manual walkthrough confirmed
- [ ] `memory/MEMORY.md` updated (if new patterns or feedback learned)
- [ ] Supervisor notified: task ready for Stage 4 review
