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
| `memory/MEMORY.md` **reading** (injected into non-Claude spawn prompts) | ✅ (plain markdown) | |
| `CLAUDE.md` auto-load | | ❌ filename is Claude-specific |
| `Skill({…})` / `Agent({subagent_type})` invocation | | ❌ Claude Code syntax |
| Built-in skills: `code-review`, `security-review`, `verify`, `run` | | ❌ no equivalent elsewhere |
| `settings.json` PreToolUse/PostToolUse hooks (guardrails, memory update) | | ❌ Claude-only |
| Memory **writes** (Supervisor curates hot/cold tier, runs compaction) | | ❌ Claude Supervisor only |

**Implication:** a non-Claude implementer can do **Pillar 2 (implementation)** inside a worktree
from a `TASK_GUIDE`. Pillars 1 (requirement fidelity) and 3 (evaluation/review) stay with the
Claude supervisor, which has the Skill/Agent tooling.

---

## Dispatch recipes

The supervisor still creates the worktree (Stage 3). The only change is *who* implements: instead
of `Agent({ subagent_type: … })`, the supervisor (or you) runs another CLI **inside the worktree
directory**. The verification command is then run by the Claude supervisor at Stage 4/5 as usual.

> Exact flags drift between CLI versions — confirm with `--help` for your installed version.

> **Memory injection for non-Claude implementers:** Before spawning a non-Claude agent, paste the
> contents of `memory/MEMORY.md` into its prompt manually — the same hot-tier context Claude
> sub-agents receive automatically. Cold files (`decisions.md`, `glossary.md`, `learnings.md`) are
> available for the agent to read if it needs depth.

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
- `.cursor/rules/agent-base.mdc` already exists in this repo (`alwaysApply: true`), so Cursor honors
  the same base rules as Claude sub-agents automatically — see "Doctrine file and adapter" below.

---

## Doctrine file and adapter (`AGENTS.md`, `.cursor/rules/agent-base.mdc`)

`AGENTS.md` is the kit's doctrine file (T173). Codex reads it directly; Claude Code reads it through
`CLAUDE.md`, which holds only the import `@AGENTS.md`. It ends with a short section naming what a
non-Claude CLI cannot enforce.

`.cursor/rules/agent-base.mdc` (read by Cursor) is a **required, thin adapter** — not an optional
convenience. It inlines the kit's non-negotiables (the four Karpathy principle names, the six
Hard-Stop Gate titles, the untrusted-content boundary rule, and "no TASK_GUIDE = no work") so a
Cursor-only user receives them through a guaranteed channel, and points at `docs/claude-md/` for
everything else.

It gains content but not authority: `AGENTS.md` + `agents/` remain canonical, and the adapter carries
that line. `docs/ddr/0006-provider-adapters-inline-non-negotiables.md` records the original decision
(its "`CLAUDE.md` stays primary" premise is superseded by T173); `tests/test_provider_adapters.py`
is the conformance test that keeps the adapter in sync with `AGENTS.md`.

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
