---
name: general-agent-template
description: Base template inherited by all sub-agents. Contains mandatory rules, context loading order, and communication protocol.
---

## Mandatory Startup Sequence (Every Agent, Every Task)

Before writing a single line of code, execute in this order:

1. Read `PROJECT_SPEC.md` — project identity, architecture, constraints, known risks
2. Read `memory/MEMORY.md` — load session-persistent decisions and feedback
3. Read your assigned `tasks/TASK_GUIDE_Txxx.md` — task scope, acceptance criteria, files to touch / not touch
4. Read the relevant guide in `.claude/agents/` for your role — role-specific constraints and patterns

If any of these files is missing, **stop and notify the Supervisor before proceeding**.

---

## Base Rules (Inherited by All Sub-Agents)

- Strictly follow all Karpathy Engineering Principles
- Never assume context — always derive it from the files above
- Communicate clearly with the Supervisor and other agents
- Update the Memory/Insights section of `PROJECT_SPEC.md` with key learnings after task completion
- Pause and ask the Supervisor if any ambiguity or error occurs
- Work only inside the assigned git worktree
- Surgical changes only — touch no code outside the task scope

---

## Complexity Levels — How Much Process to Apply

Your `TASK_GUIDE` assigns a **Complexity Level**. Scale your effort to it — this is the primary control for how much process you run. **Risk Level is a separate axis**: it gates `security-review` regardless of complexity (a C0 change to auth code is still High risk).

| Level | Scope signal | Process | Skills | Model |
|---|---|---|---|---|
| **C0** Trivial | 1 file, ~≤10 LOC, no design decision (typo, copy, config flag) | Work inline — no worktree, no brainstorm | `code-review` optional | haiku |
| **C1** Simple | 1–2 files, known pattern, no new abstraction | Single agent | `code-review` always; `verify` if user-facing | sonnet |
| **C2** Moderate | 3+ files, *or* a design choice, *or* a new component | Plan before coding | `brainstorming` when >1 viable approach; `code-review` + `verify` | sonnet / opus |
| **C3** Complex | Cross-cutting, architectural, unknowns, or touches shared/core | Decompose into subtasks; multi-agent | `brainstorming` **mandatory**; `code-review` + adversarial `verify` | opus |

If the task proves harder than its assigned level, **escalate and pause** — notify the Supervisor with the new level rather than powering through. Anything larger than C3 is an **Epic** and must be split by the Supervisor at Stage 2 before pickup.

**Risk axis — hub files.** A change touching a **hub file** (one many others import/call) has a large code-dependency blast radius and should be rated higher Risk, even when the edit is small. This is what `docs/legacy/risk-hotspots.md` captures in legacy mode; in greenfield it's a judgment call. Scope your review and testing to that blast radius — the affected callers/dependents/tests — not the whole repo.

---

## Available Skills (Callable by Any Agent)

Trigger thresholds for these skills are set by the Complexity matrix above.

| Skill | Invoke | When |
|---|---|---|
| `brainstorming` | `Skill({ skill: "brainstorming" })` | C2 when >1 viable approach; C3 mandatory |
| `code-review` | `Skill({ skill: "code-review" })` | Before reporting task ready for review (C1+) |
| `security-review` | `Skill({ skill: "security-review" })` | Task Risk Level is Medium or High (independent of complexity) |
| `verify` | `Skill({ skill: "verify" })` | C1+ if user-facing; adversarial at C3 |
| `run` | `Skill({ skill: "run" })` | Launch the app to observe behavior during development |

---

## Communication Protocol

- Use concise, structured messages
- Always include Task ID (e.g. T001) when reporting status
- Notify Supervisor immediately when a task is ready for review
- Report format:

```
Agent: [agent name]
Task: T[NNN] — [short title]
Status: [in-progress | ready-for-review | blocked]
Changed files: [list]
Blockers / notes: [any]
```

---

## Output Requirements (Every Task)

- List every file changed with a one-line reason
- Flag any risk or shared-code blast radius before committing
- Run `code-review` skill before marking ready
- Update `memory/MEMORY.md` if new patterns or feedback were learned
