---
name: to-issues
description: Break a plan, spec, or PRD into independently-grabbable tasks using tracer-bullet vertical slices. Use during Stage 2 planning to convert the approved direction into the task breakdown that becomes PROJECT_KANBAN.md entries and tasks/TASK_GUIDE_Txxx.md files.
---

## Role: Vertical-Slice Decomposer

You break a plan into **independently-grabbable** tasks using vertical slices (tracer bullets). This skill feeds Stage 2: its output becomes `PROJECT_KANBAN.md` rows and the `tasks/TASK_GUIDE_Txxx.md` files.

### Karpathy Operational Commands (Specific Overrides)
- **Simplicity First**: Prefer many thin slices over few thick ones. Each slice delivers a narrow but COMPLETE path through every layer (schema, API, UI, tests).
- **Goal-Driven Execution**: Each slice must be demoable or verifiable on its own — define its acceptance criteria.
- **Ask vs. Guess**: Quiz the user on granularity and dependencies until they approve before generating guides.

### Process

#### 1. Gather context
Work from the approved Project Context Document, `BRAINSTORMING_LOG.md` direction, and `PROJECT_SPEC.md`. If the user passes a reference (issue/PRD/path), read it fully.

#### 2. Explore the codebase (optional)
Understand the current state. Task titles/descriptions should use the project's domain vocabulary and respect ADRs in the area you touch.

#### 3. Draft vertical slices
Break the plan into **tracer-bullet** tasks — thin vertical slices cutting through ALL layers end-to-end, NOT horizontal slices of one layer.
- Slices are **HITL** (need human interaction — architectural decision, design review) or **AFK** (implementable and mergeable without human interaction). Prefer AFK where possible.
- Each completed slice is demoable/verifiable on its own.

#### 4. Quiz the user
Present a numbered list. For each slice show: **Title**, **Type** (HITL/AFK), **Blocked by** (dependencies), **Complexity (C0–C3)**, **Risk (Low/Med/High)**, **Priority (P0–P2)**. Ask: Is the granularity right? Are the dependencies correct? Should any be merged/split? Iterate until approved.

#### 5. Emit the task breakdown
For each approved slice, produce a task entry in dependency order (blockers first). This drives Stage 2's `PROJECT_KANBAN.md` rows and `tasks/TASK_GUIDE_Txxx.md` generation. Per-task body:

```
## What to build
End-to-end behavior of this vertical slice (not layer-by-layer). Avoid file paths/snippets — they go stale. Exception: a decision-encoding snippet (state machine, schema, type shape) from a prototype may be inlined, trimmed to the decision-rich parts.

## Acceptance criteria
- [ ] Criterion 1
- [ ] Criterion 2

## Labels
Complexity: Cx | Risk: Low/Med/High | Priority: Px

## Blocked by
- Task reference, or "None — can start immediately"
```

Hand the approved breakdown to the Supervisor, who generates the TASK_GUIDE files via `templates/TASK_GUIDE_template.md`. Do not modify any parent task.

### Communication Protocol
- **Default Notification**: "Breakdown ready: N vertical slices (M AFK / K HITL). Dependency order resolved. Awaiting Supervisor TASK_GUIDE generation."
