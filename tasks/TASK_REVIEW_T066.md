# TASK_REVIEW — T066: De-duplicate the startup read set, in the direction the channel allows

> Sibling of `tasks/TASK_GUIDE_T066.md`. Everything here is **filled by the reviewer at Stage
> 4/5** — it is deliberately NOT in the guide, because the implementing agent re-reads the guide on
> every turn and never fills these two sections.
>
> Consumers resolve each section **guide first, this file second** (`.claude/hooks/lib/guide_sections.py`):
> a legacy guide that still carries these sections inline keeps working unchanged, and a stray
> review file can never override an inline section.

---

## Evidence

| Check | Result | Notes / output snippet |
|-------|--------|------------------------|
| **New test(s) cover Acceptance Criteria (file paths pasted)** | ☐ pass / ☐ fail | [test file path(s) — required before Done] |
| Verification command run | ☐ pass / ☐ fail | [paste actual output] |
| Negative cases hold | ☐ pass / ☐ fail | |
| verify | ☐ pass / ☐ fail / ☐ N/A | [what was observed — must literally state "pass" or "fail" here too, e.g. "skill run, feature confirmed working — pass": the merge gate scans this Notes column for the word "pass", not just the Result column] |
| Review scope bounded to the change's blast radius (affected set, not whole repo) | ☐ pass / ☐ fail | [what was reviewed vs. skipped, and why] |
| Full smoke suite still green (no regression) | ☐ pass / ☐ fail | |
| **UI: Visual regression (diff or verdict pasted)** | ☐ pass / ☐ fail / ☐ N/A | [screenshot path or LLM verdict — required for UI tasks, Hard-Stop Gate 6] |
| **UI: Design-system compliance (tokens/colors/typography verified)** | ☐ pass / ☐ fail / ☐ N/A | [method used + output] |
| **UI: Responsiveness at target viewports** | ☐ pass / ☐ fail / ☐ N/A | [viewports tested, any overflow findings] |

---

## Demonstration

> Anchors what this task delivered to an observable before/after pair. BEFORE has no `N/A` path:
> if the task changes executable code, BEFORE is a pasted, timestamped terminal capture taken
> **before any implementation commit exists**; if it does not (docs, templates, skill-instruction
> text), BEFORE is the **verbatim prior content** of what changed — a quoted excerpt, not a command.

**BEFORE**: This task changes documentation text, so BEFORE is the **verbatim prior content** of the
sections being moved, plus the per-role token table as it stood at `HEAD` (`3bcc919`). Captured
2026-08-09, before the first implementation commit.

*(1) Per-role loaded size at `HEAD` — `python3 scripts/measure_agent_guide_tokens.py HEAD`:*

```
# per-role loaded size — HEAD
template `.claude/agents/general-agent-template.md`: 7,246 chars (~1,811 tok est.)

| role | role guide chars | template chars | total chars | total tok (est.) |
|---|---|---|---|---|
| c-infra | 2,921 | 7,246 | 10,167 | 2,541 |
| backend | 6,682 | 7,246 | 13,928 | 3,482 |
| frontend | 6,335 | 7,246 | 13,581 | 3,395 |
| qa | 5,502 | 7,246 | 12,748 | 3,187 |
```

The c-infra (2,541) and backend (3,482) totals reproduce the TASK_GUIDE's own per-spawn figures
exactly, which confirms `chars / 4` is the estimator the guide used.

*(2) `general-agent-template.md` — the four sections being removed, verbatim prior content:*

```markdown
## Mandatory Startup Sequence (Every Agent, Every Task)

Before writing a single line of code, execute in this order:

1. Read `PROJECT_SPEC.md` — project identity, architecture, constraints, known risks
2. Load the hot-tier memory index — **read `memory/MEMORY.md` yourself**. The spawn prompt gives you its path, not its contents, so nothing loads it for you. Follow its links into cold files only when relevant to your task
3. Read your assigned `tasks/TASK_GUIDE_Txxx.md` — task scope, acceptance criteria, files to touch / not touch
4. Read the relevant guide in `.claude/agents/` for your role — role-specific constraints and patterns
5. **If your task is C2/C3 or touches multiple files**: read `memory/codebase-map.md` (if it exists) for directory layout, entry points, and blast-radius hotspots — do not re-explore the repo if this file answers your structural question

If any of the first four files is missing, **stop and notify the Supervisor before proceeding**. Missing `codebase-map.md` is not a blocker — run `/map-codebase` to generate it if needed.
```

```markdown
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
```

```markdown
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
```

```markdown
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
```

*(3) `common-infrastructure.md` — the two sections it does NOT have (AC2). Verbatim, the file's
entire startup section is four lines and there is no Communication Protocol and no Complexity
guidance anywhere in it:*

```markdown
## Mandatory Startup Sequence

Follow the General Agent Template (`.claude/agents/general-agent-template.md`):
1. Read `PROJECT_SPEC.md`
2. Read `memory/MEMORY.md`
3. Read assigned `tasks/TASK_GUIDE_Txxx.md`
4. Read this file (`.claude/agents/common-infrastructure.md`)
```

```
$ grep -c "Communication Protocol" .claude/agents/common-infrastructure.md
0
$ grep -ci "complexity" .claude/agents/common-infrastructure.md
1        # a pointer only: "see .claude/agents/general-agent-template.md"
```

*(4) `backend.md` / `frontend.md` / `qa.md` — their Communication Protocol delegates the report
format to the template rather than carrying it:*

```markdown
## Communication Protocol

Use the plain-text report format from the General Agent Template (Agent / Task / Status / Changed
files / Blockers). ...
```

**AFTER**: [same command, post-change] OR [verbatim excerpt of the new content]

**DELTA**: [one sentence — what a user can now do that they could not before]

**WITNESS**: [who ran it and when — derived from `memory/event-trace/Txxx.jsonl`, never the
implementing agent alone]
