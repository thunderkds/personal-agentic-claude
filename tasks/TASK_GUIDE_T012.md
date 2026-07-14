# TASK_GUIDE — T012: Registration — CLAUDE.md + MEMORY.md + README
**Date**: 2026-06-19
**Complexity Level**: C0
**Risk Level**: Low
**Priority**: P1
**Assigned agent**: common-infrastructure
**Agent guide**: `.claude/agents/common-infrastructure.md`

---

## Mandatory Startup (Do Not Skip)

Before writing any code:
1. Read `PROJECT_SPEC.md`
2. Read `memory/MEMORY.md`
3. Read this file completely
4. Read `.claude/agents/common-infrastructure.md`
5. Read `CLAUDE.md` fully — specifically the custom skill table and the **5-Stage Agentic Pipeline → Stage 0.5** section where startup instructions live
6. Read `README.md` to find the custom skills table location and format
7. Apply C0 process from the Complexity matrix in `.claude/agents/general-agent-template.md`

**Depends on**: T011 (`.claude/skills/wake/SKILL.md` must exist before it can be registered)

---

## Requirement (Pillar 1 — Adapt the requirement)

Register the `wake` skill across all three discovery surfaces and embed it as a **mandatory** first step in the Supervisor's session startup protocol:

1. **`CLAUDE.md` — custom skill table**: add `wake` row (same format as existing rows).
2. **`CLAUDE.md` — Supervisor startup protocol**: add `wake` as a mandatory hard gate at the start of every new session. The Supervisor must invoke `/wake` before responding to the user's first substantive request. This is not a recommendation — it is a required first step, on the same level as reading `PROJECT_SPEC.md`.
3. **`memory/MEMORY.md`**: add one-liner under `### Decisions` recording the `wake` skill decision.
4. **`README.md`**: add `wake` to the custom skills table.

**Restated intent**: After T012 merges, `wake` is not just discoverable — it is embedded into the Supervisor's mandatory operating procedure. Every new session starts with `/wake`; the Supervisor is instructed to never skip it, in the same way it is instructed to never skip the Requirement Fidelity Gate.

**Out of scope**:
- Writing the SKILL.md (T011)
- `setup.sh` changes (no new folder infrastructure needed)
- Adding a `UserPromptSubmit` hook (deferred)

**Requirement Refs**:
- Brainstorming decision 2026-06-19: `/wake` is mandatory first step, hard gate, not optional
- User decision 2026-06-19: "should run it first, and run the tasks after — seem like the must run steps"

### Requirement Fidelity Gate (sign off BEFORE implementation)

- [x] Restated intent confirmed to match the user's request
- [x] Domain terms align with existing CLAUDE.md skill table format
- [x] Every Acceptance Criterion below traces to a line in the Requirement
- [x] T011 is complete — `.claude/skills/wake/SKILL.md` exists

> An agent must NOT start implementing until this gate is checked. If anything here is unclear,
> STOP and ask the Supervisor (Karpathy: Think Before Coding).

---

## Acceptance Criteria

| # | Criterion (testable) | Traces to requirement |
|---|----------------------|-----------------------|
| 1 | `CLAUDE.md` custom skill table contains a `wake` row with definition path `.claude/skills/wake/SKILL.md` and trigger description naming both the Supervisor mandatory startup trigger and user `/wake` | Skill table registration |
| 2 | `CLAUDE.md` contains a mandatory startup instruction for `wake` — phrased as a hard requirement (e.g. "must", "before responding", "mandatory"), not a suggestion — in a location the Supervisor reads at the start of every session | Mandatory startup gate requirement |
| 3 | `memory/MEMORY.md` contains a `wake` one-liner under `### Decisions` | MEMORY.md registration |
| 4 | `README.md` custom skills table contains a `wake` row | README registration |
| 5 | The CLAUDE.md startup instruction specifies the order: `/wake` fires **before** the Supervisor responds to the user's first substantive request, not after | Ordering requirement |

---

## Evaluation & Acceptance

### Success Criteria

| # | Given | Expect | How it's checked |
|---|-------|--------|-----------------|
| 1 | `grep -n "wake" CLAUDE.md` | Skill table row + mandatory startup instruction | grep + manual read of surrounding context |
| 2 | `grep -n "wake" memory/MEMORY.md` | One-liner under Decisions | grep |
| 3 | `grep -n "wake" README.md` | Row present in skills table | grep |
| 4 | Read the CLAUDE.md startup instruction | Uses "must" / "mandatory" / "required" language, not "should" / "recommended" | manual |

### Verification Command

```bash
grep -n "wake" CLAUDE.md && \
grep -n "wake" memory/MEMORY.md && \
grep -n "wake" README.md
```

### Evidence (filled by reviewer at Stage 4/5)

| Check | Result | Notes / output snippet |
|-------|--------|------------------------|
| Verification command run | ☐ pass / ☐ fail | [paste actual output] |
| Startup instruction uses mandatory language (not "should") | ☐ pass / ☐ fail | [paste the instruction line] |
| `wake` appears before other startup steps in CLAUDE.md | ☐ pass / ☐ fail | |
| Review scope bounded to CLAUDE.md, MEMORY.md, README.md only | ☐ pass / ☐ fail | |
| Full smoke suite still green | ☐ pass / ☐ fail | |

---

## Approach

### CLAUDE.md — custom skill table

Add one row matching the exact pipe/column format of adjacent rows:

```markdown
| `wake` | `.claude/skills/wake/SKILL.md` | Mandatory first action in every new session — invoke before responding to the user's first request. Reads git log, PROJECT_KANBAN.md, memory/MEMORY.md, and active LRs; emits a ≤50-line live briefing. Also user-invokable as `/wake` at any time for a live project snapshot. |
```

### CLAUDE.md — mandatory startup protocol

Locate the section the Supervisor reads at session start (the Permanent Rules or the opening role description). Add a clearly-demarcated startup block — **above** the 5-Stage Pipeline description so it is encountered first:

```markdown
## Mandatory Session Startup (Every New Conversation)

Before responding to the user's first substantive request, the Supervisor **must** invoke:

```
Skill({ skill: "wake" })
```

This is not optional. `wake` reads the live project state (git history, in-flight tasks, memory, active LRs) and emits a ≤50-line briefing. Only after `wake` completes may the Supervisor proceed.

**Do not skip `wake` even if the user jumps straight to a task.** Invoke it silently first, then respond.
```

### memory/MEMORY.md — Decisions section

Append one line under `### Decisions`:

```markdown
- [wake skill: mandatory cold-start briefing](decisions.md) — reads git/KANBAN/MEMORY/LRs live; ≤50-line output; hard gate before first Supervisor response each session
```

### README.md

Add `wake` to the custom skills table in the same format as other rows.

---

## Edge Case Checklist

- [ ] CLAUDE.md table row uses exact pipe format — misalignment breaks markdown rendering
- [ ] Mandatory startup block placement: must be **before** the 5-Stage Pipeline, not buried inside it — Supervisor reads top-to-bottom
- [ ] `memory/MEMORY.md` line count after addition must stay ≤200 — count before appending
- [ ] README.md skill table column order must match existing rows exactly
- [ ] The mandatory instruction must use hard language ("must", "required") not soft ("should", "recommended") — this is the user's explicit requirement

---

## Files to Change (Predicted)

| File | Change |
|------|--------|
| `CLAUDE.md` | Add `wake` skill table row; add mandatory session startup block |
| `memory/MEMORY.md` | Add `wake` one-liner under `### Decisions` |
| `README.md` | Add `wake` to custom skills table |

## Files Must NOT Touch

| File | Reason |
|------|--------|
| `.claude/skills/wake/SKILL.md` | Written by T011, not T012 |
| `setup.sh` | No new folder infrastructure needed |
| Any `.claude/agents/` files | No new agents |
| `memory/decisions.md` | Supervisor will update cold tier in the post-push memory pass |

---

## Test Plan

- `grep -n "wake" CLAUDE.md` — skill table row + startup block both present
- Read the startup block — confirms mandatory language and correct ordering
- `grep -n "wake" memory/MEMORY.md` — one-liner present
- `grep -n "wake" README.md` — row present
- Line count of `memory/MEMORY.md` ≤ 200

---

## Completion Checklist

- [ ] `CLAUDE.md` updated: `wake` skill table row added
- [ ] `CLAUDE.md` updated: mandatory session startup block added with hard-gate language, placed before 5-Stage Pipeline
- [ ] `memory/MEMORY.md` updated: `wake` one-liner under `### Decisions`
- [ ] `README.md` updated: `wake` row in custom skills table
- [ ] MEMORY.md line count confirmed ≤ 200
- [ ] Self-review: `Skill({ skill: "code-review" })` run
- [ ] Supervisor notified: T012 ready for Stage 4 review
