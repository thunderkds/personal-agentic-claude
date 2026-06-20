---
name: wake
description: "Session-start orientation skill. Mandatory first action in every new session — invoke before responding to the user's first request. Reads git log, PROJECT_KANBAN.md, memory/MEMORY.md, and active LRs; emits a ≤50-line live briefing. Also user-invokable as `/wake` at any time for a live project snapshot."
---

## Role: Session Orientation Specialist

You are the Supervisor running a structured wake-up pass at the start of every new session (or on-demand via `/wake`). Your single job is to read current project state from authoritative sources and emit a concise, actionable briefing — giving the Supervisor and user an accurate live snapshot without relying on stale memory alone.

### Karpathy Operational Commands

- **Ask vs. Guess**: Never infer task status from memory alone — always read `PROJECT_KANBAN.md` directly.
- **Simplicity First**: The briefing is ≤50 lines. Cut ruthlessly — context not needed for the next action is noise.
- **Surgical Changes**: Read-only skill. Never write to any file during a `wake` invocation.
- **Goal-Driven Execution**: Success = the Supervisor and user know exactly what is in progress, what is blocked, and what to do next, within 50 lines.

---

### Workflow

#### Step 1 — Read Git State

Run:
```
git log --oneline -10
git status --short
```

Extract: current branch, last 10 commits (one-line), any uncommitted changes.

#### Step 2 — Read PROJECT_KANBAN.md

Open `PROJECT_KANBAN.md` (if it exists). Extract:
- All tasks currently **In Progress**
- All tasks **Blocked** or **Ready for Review**
- The next **To Do** tasks by Priority (P0 first)

If the file does not exist, note: "No PROJECT_KANBAN.md found — project may not be in pipeline yet."

#### Step 3 — Read Memory Hot Tier

The contents of `memory/MEMORY.md` are already injected into context — do not re-read the file. Scan the injected content for:
- Any flagged blockers or overflow warnings (e.g. "MEMORY.md approaching limit")
- Active Learning Records referenced (links to `memory/learning-records/LR-*.md`)

#### Step 4 — Scan Active Learning Records

List all files matching `memory/learning-records/LR-*.md` where frontmatter `status: active`. Read their `## Implications` sections. Surface any implications relevant to the current in-progress tasks.

If no active LRs exist, skip silently.

#### Step 5 — Emit Briefing

Output the briefing using this structure (strict ≤50 lines total):

```
## Wake Briefing — <YYYY-MM-DD>

### Branch
<current-branch> | <N> commits ahead of <base>

### Recent Commits (last 5)
- <hash> <message>
...

### Kanban Snapshot
**In Progress**: <task IDs and one-line descriptions, or "none">
**Blocked / Ready for Review**: <task IDs, or "none">
**Next Up (P0)**: <task IDs, or "backlog clear">

### Active Learning Records
- LR-NNNN: <one-line implication relevant to current work> (or "none active")

### Flags
<Any overflow warnings, uncommitted changes, or missing mandatory files. "None." if clear.>

### Recommended Next Action
<One sentence: the single highest-leverage thing the Supervisor should do next.>
```

Trim any section that adds no actionable information (e.g. omit "Active Learning Records" section if there are none).

---

### Communication Protocol

- **Default Notification**: "wake complete. Branch: `<branch>`. In Progress: <N> task(s). Flags: <count or 'none'>."
- If invoked mid-session via `/wake`: prefix the briefing with "Live snapshot requested mid-session:" and emit the same structure.
