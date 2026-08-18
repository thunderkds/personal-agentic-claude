# Instruction Patterns

Reached from `SKILL.md`'s *Information Hierarchy*. Six reusable structures for the body of a skill,
plus three rules for calibrating how tightly each part instructs. Not every skill needs all six —
take the ones that fit the job.

---

## The six patterns

### Gotchas

**Use when** the environment defies a reasonable assumption — a fact the agent will get wrong
unless told. Not general advice ("handle errors appropriately"); concrete corrections.

**Keep gotchas in `SKILL.md`, not behind a pointer.** A pointer only fires when the agent
recognizes its trigger condition, and the defining property of a non-obvious issue is that the agent
does not recognize it coming. A gotcha the agent reads after hitting the situation is a gotcha that
did not work.

**A correction the user has to make is the signal to add one.** Every time someone steers the agent
off a wrong path, that path is a gotcha the skill was missing.

This repo already stores the material: `memory/learnings.md`, and its index in `memory/MEMORY.md`.
When writing a skill that touches a subsystem that file covers, **mine it** — the entries there were
paid for in real incidents:

```markdown
## Gotchas
- `$CLAUDE_PROJECT_DIR` is set for hooks but **empty** inside an agent's Bash tool call. Never tell
  an agent to write to `$CLAUDE_PROJECT_DIR/...`; give a literal absolute path.
- An env var set inside a Bash call is invisible to hooks — they are spawned as siblings of the
  call, not children. `CLAUDE_ACTIVE_TASK=Txxx <cmd>` silently attributes nothing.
- `isolation: "worktree"` forks from `main`, not the current branch, so a guide committed on a
  feature branch is invisible to its own agent. Create the worktree off HEAD yourself and spawn
  without `isolation`.
```

### Output templates

**Use when** the output must take a specific shape. A concrete structure beats prose describing it —
the agent pattern-matches against the shape. Short templates inline; long or
conditionally-needed ones go in `assets/` behind a pointer.

```markdown
Report as:

Agent: <role>
Task: T<NNN> — <short title>
Status: <in-progress | ready-for-review | blocked>
Changed files: <list>
```

### Checklists

**Use when** a workflow has steps with dependencies or gates, and skipping one is plausible.
An explicit list lets the agent track where it is.

```markdown
Progress:
- [ ] Worktree created off HEAD
- [ ] Active-task state file written
- [ ] Tests written and RED
- [ ] Implementation committed
- [ ] Mutation controls observed and reverted
```

### Validation loops

**Use when** the work has a checker. Do the work, run the checker, fix, repeat until it passes —
and say explicitly that the agent may not proceed while it fails.

```markdown
1. Make the edit.
2. Run `python3 -m pytest .claude/hooks/tests/ -q`.
3. If it fails: read the failure, fix it, run again.
4. Proceed only once it passes.
```

A reference file can be the validator: instruct the agent to check its work against it before
finalizing.

### Plan-validate-execute

**Use when** the operation is batched or destructive and a mistake is expensive. The agent writes an
intermediate plan in a structured format, a validator checks the plan against a source of truth, and
only then does it execute.

```markdown
1. List the tasks the merge will close → `plan.txt`.
2. Validate each against `PROJECT_KANBAN.md` (a task still In Progress is rejected by the merge gate).
3. If validation fails, fix the board, re-validate.
4. Merge.
```

The load-bearing step is 3's checker. Its error message must name what was wrong *and* what was
available, so the agent can self-correct without asking.

### Bundled scripts

**Use when** execution traces show the agent rebuilding the same logic every run — parsing a format,
validating output, computing a summary. Write it once, test it, drop it in `scripts/`, and have
`SKILL.md` call it by path (`git-guardrails-claude-code/scripts/` is the existing example).

---

## Calibrating control

- **Match specificity to fragility.** Where several approaches are valid, describe the goal and
  leave the route open — explaining *why* beats a rigid directive, because an agent that understands
  the purpose decides better in context. Where operations are fragile or order matters, be exact:
  give the literal command and say it must not be modified. Most skills mix both; calibrate each
  section on its own.
- **Provide a default, not a menu.** Pick one tool or route, state it, and give the alternative in
  one clause behind its condition ("for a pre-existing worktree, spawn without `isolation`"). A list
  of equal options makes the agent deliberate instead of act.
- **Teach a procedure, not an answer.** A skill should generalize over a class of problems, not
  encode one instance. "Update row T079 to Done" is an answer; "locate the task's row by ID, set
  Status, move it under `### Done`, keep the Evidence link" is a procedure. Specific details still
  belong in a skill — output templates, hard constraints, exact commands — as long as the *approach*
  generalizes.
