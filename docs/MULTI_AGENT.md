# Using This System With Other Agents (Codex, Cursor, …)

> **Status:** Reference doc. Describes *how* this Claude-first supervisor OS can dispatch
> implementation work to other agentic CLIs. No mechanism changes — Claude Code remains the
> supervisor; other tools act as **implementers** on a single task.

---

## The one idea that makes this portable

This system does **not** depend on every agent being Claude. Its portability layer already
exists: the **`TASK_GUIDE` + Evidence Gate**.

- Every task is written in `tasks/TASK_GUIDE_Txxx.md` as a **verifiable goal** — acceptance
  criteria (`given → expect`) plus **one runnable verification command**.
- Correctness is judged by that command, run by the **Supervisor (Claude)** — *not* by the agent
  that wrote the code (the "implementing agent must not be the sole author of its own acceptance
  test" rule from the README).

Because the oracle is independent of the implementer, **any agent can implement a slice** and the
gate decides pass/fail the same way. The `TASK_GUIDE` is the contract; the host model is swappable.

```
Claude (Supervisor)                         Codex / Cursor (Implementer)
  ├─ Stage 2: writes TASK_GUIDE_Txxx.md  ──▶  reads it + PROJECT_SPEC.md
  │   (acceptance criteria + verify cmd)      implements in the worktree
  ├─ Stage 3: creates git worktree            runs the verify command
  └─ Stage 4/5: runs the Evidence Gate  ◀───  hands back the diff
      (decides pass/fail, tool-agnostic)
```

---

## What's portable vs. Claude-coupled

| Layer | Portable as-is | Claude-only |
|---|---|---|
| Pipeline, Karpathy principles, 3-pillar model, templates | ✅ | |
| `TASK_GUIDE` / `PROJECT_SPEC` / `PROJECT_KANBAN` (plain markdown) | ✅ | |
| Skill **content** (the migration checklist, ship workflow, etc.) | ✅ (it's just procedure) | |
| `git worktree` isolation | ✅ (plain git) | |
| `CLAUDE.md` auto-load | | ❌ filename is Claude-specific |
| `Skill({…})` / `Agent({subagent_type})` invocation | | ❌ Claude Code syntax |
| Built-in skills: `code-review`, `security-review`, `verify`, `run` | | ❌ no equivalent elsewhere |
| `settings.json` PreToolUse hooks (git-guardrails) | | ❌ Claude-only |

**Implication:** a non-Claude implementer can do **Pillar 2 (implementation)** inside a worktree
from a `TASK_GUIDE`. Pillars 1 (requirement fidelity) and 3 (evaluation/review) stay with the
Claude supervisor, which has the Skill/Agent tooling.

---

## Dispatch recipes

The supervisor still creates the worktree (Stage 3). The only change is *who* implements: instead
of `Agent({ subagent_type: … })`, the supervisor (or you) runs another CLI **inside the worktree
directory**. The verification command is then run by the Claude supervisor at Stage 4/5 as usual.

> Exact flags drift between CLI versions — confirm with `--help` for your installed version.

### Codex CLI

Codex auto-reads an **`AGENTS.md`** at the repo root (see "Optional: AGENTS.md" below), so the
prompt only needs the task pointer.

```bash
cd <worktree-path>
codex exec "Read tasks/TASK_GUIDE_T001.md and PROJECT_SPEC.md. Implement the slice test-first, \
touching only the predicted files. Then run the TASK_GUIDE's verification command and paste its \
output. Stop and report if any acceptance criterion is ambiguous."
```

- `codex exec` is the non-interactive/automation mode (good for a supervised one-shot per task).
- Keep one task per invocation — mirrors the one-vertical-slice rule.

### Cursor (cursor-agent)

Cursor reads **`.cursor/rules/*.mdc`** for repo conventions; its headless CLI runs a single prompt.

```bash
cd <worktree-path>
cursor-agent -p "Read tasks/TASK_GUIDE_T001.md and PROJECT_SPEC.md. Implement the slice test-first, \
touching only the predicted files. Run the verification command from the TASK_GUIDE and report its \
output. Pause and ask if intent is unclear."
```

- `-p` / `--print` is the non-interactive (headless) mode.
- If you want Cursor to honor the same base rules as Claude sub-agents, mirror
  `.claude/agents/general-agent-template.md` into a `.cursor/rules/agent-base.mdc` (see below).

---

## Optional: a shared `AGENTS.md`

`AGENTS.md` is an emerging cross-tool convention (read by Codex, and increasingly others). If you
want non-Claude implementers to inherit the base rules automatically, create a root `AGENTS.md`
that mirrors the essentials from `.claude/agents/general-agent-template.md`:

- Read `PROJECT_SPEC.md`, your `tasks/TASK_GUIDE_Txxx.md`, and the base rules before any work.
- Work only inside the assigned worktree; touch only the predicted files (Surgical Changes).
- Build test-first; a task is done only when its verification command passes.
- Stop and ask on any ambiguity — never guess.

This is **not required** for the dispatch recipes above (the prompt already points at the guides) —
it just removes repetition and gives Cursor/Codex a default to fall back on. Keep it a thin mirror,
not a second source of truth; `CLAUDE.md` + `.claude/agents/` remain canonical for the supervisor.

---

## What does NOT port (do these on the Claude side)

- **Review** (`code-review`, `security-review`) and **end-to-end `verify`** — keep on the Claude
  supervisor. This also *preserves the independence rule*: the non-Claude tool implements; Claude
  evaluates. Don't have the implementing CLI grade its own work.
- **`migration-safety` / `ship` gates** — run by the Claude supervisor (they're skills).
- **git-guardrails hook** — Claude-only; for other CLIs, rely on the worktree boundary + the
  "push only when asked" discipline, or each tool's own equivalent.

---

## TL;DR

Claude stays the conductor. Other agents are session musicians you hand a single sheet
(`TASK_GUIDE`) to. The Evidence Gate is the conductor's ear — it doesn't care who played the part,
only whether it was in tune.
