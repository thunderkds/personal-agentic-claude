# TASK_GUIDE — T149: `ship` won't recommend GO for production until a human has approved that exact version
**Date**: 2026-10-16
**Complexity Level**: C1
**Risk Level**: Low
**Priority**: P2
**Assigned agent**: common-infrastructure
**Agent guide**: `agents/common-infrastructure.md`

---

## Mandatory Startup (Do Not Skip)

Before writing any code:
1. Read `PROJECT_SPEC.md`
2. Read the memory slice in your spawn prompt (`<!-- memory-slice -->`). Read `memory/MEMORY.md` in full only if your work reaches a file, hook, skill or decision the slice does not cover
3. Read this file completely
4. Read `agents/common-infrastructure.md`
5. Note the **Complexity Level** above and apply the matching process from the Complexity matrix in your role guide
6. C1 — skip `memory/codebase-map.md`

---

## Requirement (Pillar 1 — Adapt the requirement)

From the user's improvement list, area 6: *"Optional production-gate workflow (human approval required before production deploy)… Smoke-test + rollback conventions that the Supervisor can drive safely."* Grilled 2026-10-16: **gate + conventions, no deploys** — `ship` still never deploys. Brainstorm answer: the **Supervisor asks via a question prompt and records the answer**, naming the exact version/commit.

**Verified state (2026-10-16)**: `skills/ship/SKILL.md` § 7 "Pre-Flight GO Gate" already lists four GO conditions (evidence, rollback plan, health check, deploy command) and § 4 already builds a rollback plan with trigger conditions. There is no approval condition.

**Restated intent**:
> `ship`'s GO gate gains a fifth condition: the human approved this exact version for production, asked through a question prompt and recorded in the RUNBOOK's Release Log — and the smoke-test step names its pass condition before the deploy, not after.

**Out of scope**:
- Platform integrations (Railway/Vercel/Fly) or running any deploy
- A user-only approval command (the user chose Supervisor-asks)
- Staging environments

**Requirement Refs**: no `PRD.md` — traces to `memory/decisions.md` "Improvement-list grilling (2026-10-16)" area (6) and the brainstorm answers.

### Requirement Fidelity Gate (sign off BEFORE implementation)

- [ ] Restated intent confirmed to match the user's request (by Supervisor / user — not the implementing agent)
- [x] Domain terms align with `PROJECT_SPEC.md` glossary
- [ ] Every Acceptance Criterion below traces to a line in the Requirement
- [x] Requirement Refs — N/A, traced above

---

## Dependencies & Reachability

**Depends on**: None
**Entry point**: `skills/ship/SKILL.md` § 7 "Pre-Flight GO Gate"

---

## Acceptance Criteria

| # | Criterion (testable) | Traces to requirement |
|---|----------------------|-----------------------|
| 1 | § 7 gains: `- [ ] Production approval recorded for <version> @ <commit>` — asked with `AskUserQuestion` naming version and commit, answer copied verbatim into the Release Log row | "human approval… exact version" |
| 2 | An approval whose version or commit differs from the release being planned does not satisfy the gate | approving v2.1 ≠ approving v2.2 |
| 3 | `templates/RUNBOOK_template.md`'s Release Log table gains an `Approved (by / when / answer)` column | recorded |
| 4 | § 3 "Deployment Plan" requires the smoke test and its pass condition to be written **before** the deploy step; § 7 states the approval is a record **written by the Supervisor**, not a user-signed artifact | conventions + honest about the record |
| 5 | "the operator executes" and the no-auto-deploy line remain verbatim | no deploys |

---

## Evaluation & Acceptance

### Success Criteria (observable, pass/fail)

| # | Given (input/state) | Expect (output/behavior) | How it's checked |
|---|---------------------|--------------------------|------------------|
| 1 | `skills/ship/SKILL.md` | § 7 contains the approval line naming version and commit | automated text test |
| 2 | Same file | still contains "this is a recommendation; the operator executes" | automated |
| 3 | RUNBOOK template | Release Log header has the Approved column | automated |
| 4 | Live dry run of `ship` on this repo's next release | the question prompt names version + commit; GO only after the answer | manual at `/verify` |
| 5 | **Mutation control**: delete the approval line | SC1 RED | Supervisor re-runs |

### Verification Command (exact, runnable)

```bash
python3 -m pytest tests/test_ship_approval_gate.py -q
```

### Evidence

> **Moved.** Filled by the reviewer at Stage 4/5 in `tasks/TASK_REVIEW_T149.md`.

---

## Demonstration

> **Moved.** See `tasks/TASK_REVIEW_T149.md`.

---

## Approach

**Pattern reference**: `tests/test_response_standard.py` — text-presence tests over a SKILL.md.

**Vital slice**: the § 7 line + Release Log column.
**Cut list**:
- Pack-level smoke-test templates per platform (devops pack) — follow-up if wanted
- Re-asking approval on every re-plan of the same version

---

## Edge Case Checklist

- [ ] A release with no version tag yet — the commit alone is named, and the answer says so
- [ ] User answers "Other" with free text — copied verbatim, treated as not approved unless it says approve
- [ ] `ship` skill body stays under its current size — no Codex regression (it is not one of the four over 8 KB; keep it that way)

---

## Files to Change (Predicted)

| File | Change |
|------|--------|
| `skills/ship/SKILL.md` | § 3 smoke-test-before-deploy line, § 7 approval line |
| `templates/RUNBOOK_template.md` | Release Log column |
| `tests/test_ship_approval_gate.py` | new |

## Files Must NOT Touch

| File | Reason |
|------|--------|
| `RUNBOOK.md` | this repo's live runbook — only the template changes |
| `packs/devops/**` | cut |

---

## Test Plan

Text-presence pytest; SC4 live at Stage 5.

---

## Completion Checklist

- [ ] Implementation done
- [ ] Self-review: `Skill({ skill: "code-review" })` run
- [ ] Security review: N/A (Low risk)
- [ ] Tests written AND pass — output pasted into `tasks/TASK_REVIEW_T149.md` (Hard-Stop Gate 5)
- [ ] `Skill({ skill: "verify" })` run
- [ ] Supervisor notified: task ready for Stage 4 review
