---
name: general-agent-template
description: Base template inherited by all sub-agents. Contains the universal base rules, engineering principles, and output requirements that are NOT restated in the per-role guides.
---

> **What lives where.** The harness auto-loads `.claude/agents/<your-role>.md` as your system
> prompt, so your role guide always reaches you; this file reaches you only if you open it. Anything
> every role needs in its own words — the startup read sequence, the Complexity matrix, the skills
> table, the Communication Protocol — therefore lives in each **role guide**, not here. What remains
> below is the universal material that is stated once, in one place, and referenced from all four.
> The Karpathy table is the exception to "in its own words": it is a Permanent Rule, so each role
> guide carries it **verbatim**.

## Base Rules (Inherited by All Sub-Agents)

- Strictly follow all Karpathy Engineering Principles (compact table in your own role guide — full version with rationale in `CLAUDE.md`, keep both in sync on edit)
- Never assume context — always derive it from the startup reads your role guide lists. In
  particular, **read `memory/MEMORY.md` yourself**: the spawn prompt gives you its path, not its
  contents, so nothing loads it for you
- Communicate clearly with the Supervisor and other agents
- Update the Memory/Insights section of `PROJECT_SPEC.md` with key learnings after task completion
- Pause and ask the Supervisor if any ambiguity or error occurs
- Work only inside the assigned git worktree
- Surgical changes only — touch no code outside the task scope

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

## Output Requirements (Every Task)

- List every file changed with a one-line reason
- Flag any risk or shared-code blast radius before committing
- Run `code-review` before marking ready
- Report new patterns, decisions, or feedback to the Supervisor in your final message — never write to `memory/` files directly (Supervisor-only, per the Memory Write Protocol)

---

## Staleness Guard

Root `AGENTS.md` is a thin mirror of this file's Base Rules for non-Claude CLIs (Codex, etc.). If
you edit Base Rules here, or the Karpathy Engineering Principles table that now lives in each of
the four role guides, check `AGENTS.md` is still an accurate mirror and update it if not.
