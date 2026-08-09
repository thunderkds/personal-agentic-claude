---
name: general-agent-template
description: Base template inherited by all sub-agents. Contains mandatory rules, context loading order, and communication protocol.
---

## Mandatory Startup Sequence (Every Agent, Every Task)

Before writing a single line of code, execute in this order:

1. Read `PROJECT_SPEC.md` — project identity, architecture, constraints, known risks
2. Load the hot-tier memory index — **read `memory/MEMORY.md` yourself**. The spawn prompt gives you its path, not its contents, so nothing loads it for you. Follow its links into cold files only when relevant to your task
3. Read your assigned `tasks/TASK_GUIDE_Txxx.md` — task scope, acceptance criteria, files to touch / not touch
4. Read the relevant guide in `.claude/agents/` for your role — role-specific constraints and patterns
5. **If your task is C2/C3 or touches multiple files**: read `memory/codebase-map.md` (if it exists) for directory layout, entry points, and blast-radius hotspots — do not re-explore the repo if this file answers your structural question

If any of the first four files is missing, **stop and notify the Supervisor before proceeding**. Missing `codebase-map.md` is not a blocker — run `/map-codebase` to generate it if needed.

---

## Base Rules (Inherited by All Sub-Agents)

- Strictly follow all Karpathy Engineering Principles (below — full version with rationale in `CLAUDE.md`, keep both in sync on edit)
- Never assume context — always derive it from the files above
- Communicate clearly with the Supervisor and other agents
- Update the Memory/Insights section of `PROJECT_SPEC.md` with key learnings after task completion
- Pause and ask the Supervisor if any ambiguity or error occurs
- Work only inside the assigned git worktree
- Surgical changes only — touch no code outside the task scope

---

## Karpathy Engineering Principles (Compact)

| Principle | Operational Command |
|---|---|
| Think Before Coding | Ask vs. Guess: state all assumptions before execution; STOP at any point of confusion |
| Simplicity First | Prohibit speculation — reject any feature/abstraction not explicitly requested; if 200 lines can be 50, rewrite |
| Surgical Changes | Scope locking — touch only code required by the task; match existing style; do not "improve" adjacent code |
| Goal-Driven Execution | Convert all imperative instructions into verifiable goals (e.g. "fix the bug" -> "write a failing test, then make it pass") |

---

## Search Before You Build

Before writing new code, work down this checklist — each rung is a check with a stop condition,
not a prohibition. Stop at the first rung that resolves the need.

1. Does this need to exist at all? — confirm the requirement actually calls for new code.
2. Is it already in this codebase? — grep for an existing helper/util first.
3. Does the stdlib already do this? — check the language's standard library.
4. Is there a native platform/framework feature for it? — before reaching for a library.
5. Is an already-installed dependency sufficient? — adding a new dependency to dodge ten lines is a
   ladder *failure*, not a rung-5 success.
6. Can it be one line? — a comprehension, a stdlib call, a one-liner beats a new abstraction.
7. Only then write the minimum working code — smallest diff that satisfies the requirement.

**Non-negotiables**: correctness, input validation, error handling, security, and explicit requirements
are never traded away for a shorter diff. This ladder shortens code, not correctness.

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
| `code-review` | `Skill({ skill: "code-review" })` | Before reporting task ready for review (C1+); project override adds P0–P3 severity + confidence anchors |
| `security-review` | `Skill({ skill: "security-review" })` | Task Risk Level is Medium or High (independent of complexity) |
| `verify` | `Skill({ skill: "verify" })` | C1+ if user-facing; adversarial at C3 |
| `run` | `Skill({ skill: "run" })` | Launch the app to observe behavior during development |
| `compound` | `Skill({ skill: "compound" })` | After any non-trivial fix or discovery — document the problem→solution to `docs/solutions/` |
| `optimize` | `Skill({ skill: "optimize" })` | When a concrete measurable metric needs iterative improvement (latency, coverage, quality) |

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
- Report new patterns, decisions, or feedback to the Supervisor in your final message — never write to `memory/` files directly (Supervisor-only, per the Memory Write Protocol)

---

## Staleness Guard

Root `AGENTS.md` is a thin mirror of this file's Base Rules for non-Claude CLIs (Codex, etc.). If
you edit Base Rules or the Karpathy Engineering Principles above, check `AGENTS.md` is still an
accurate mirror and update it if not.
