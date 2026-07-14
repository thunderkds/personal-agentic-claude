---
name: craft-spawn-prompt
description: Use at Stage 3 (and inside the bugfix skill's Step 4) whenever the Supervisor is about to spawn a sub-agent for a TASK_GUIDE. Assembles a complete spawn prompt — auto-detecting standard vs. bugfix-flavored guides — pre-flight-checks it against the hook's structural task-ID pattern, and recommends a spawn model. Outputs a fenced prompt block for the Supervisor to paste into Agent(); never calls Agent itself.
---

## Role: Spawn Prompt Assembler

The single source of truth for turning a `tasks/TASK_GUIDE_Txxx.md` into a ready-to-paste `Agent()` prompt, so Stage 3 and the `bugfix` skill can't drift into two different checklists again. Consumes a guide path, produces text — it never calls the `Agent` tool itself, since skills run inline in the Supervisor's own context.

### Karpathy Operational Commands (Specific Overrides)
- **Ask vs. Guess**: if the guide is missing a required field (`**Assigned agent**`/`**Agent guide**`), stop and report the gap — do not guess an agent guide.
- **Surgical Changes**: flag pre-flight problems in the assembled prompt; never silently rewrite the prompt to dodge the hook.
- **Goal-Driven Execution**: success is a fenced prompt block containing all required elements, plus a pass/flag verdict from the pre-flight check.

### Workflow

#### 1. Read inputs
Read the TASK_GUIDE at the given path, the `.claude/agents/*.md` file named in its `**Agent guide**` field, and `memory/MEMORY.md`. If any is missing, stop and report to the Supervisor.

#### 2. Detect guide flavor
Search the guide for a `### Mental Model` (or `## Mental Model`) heading.
- **Present → bugfix-flavored.** Use the bugfix Step 4 shape.
- **Absent → standard Stage-3-style.** Use the standard shape.

#### 3. Assemble the prompt
Both shapes reuse the same 5-element checklist proven in `bugfix` Step 4; only element 2 and the presence of element 3 change:

| # | Element | Standard guide | Bugfix-flavored guide |
|---|---|---|---|
| 1 | Guide pointer | `tasks/TASK_GUIDE_Txxx.md` path | same |
| 2 | Orienting content | Guide's Restated Intent / Requirement section, verbatim | Confirmed Mental Model section, verbatim |
| 3 | First-action skill invocation | Only if the task explicitly requires one (e.g. `migration-safety` for schema work) — otherwise omit | `Skill({ skill: "diagnose" })` as the first action — always present |
| 4 | Memory injection | Full contents of `memory/MEMORY.md`, verbatim | same |
| 5 | Agent-guide pointer | `.claude/agents/<role>.md` from the guide's `**Agent guide**` field | same |

Any caller-supplied inputs (e.g. bugfix's fixed "invoke diagnose first" instruction) are accepted as parameters to this step, not re-derived.

#### 4. Pre-flight structural-reference check
Read `extract_structural_task_ids()` directly from `.claude/hooks/pre_agent_validate_guide.py` — do not re-derive or approximate the pattern, it must stay byte-for-byte in sync with what the hook enforces. Run it against the assembled prompt text:
- For every extracted task ID, confirm `tasks/TASK_GUIDE_T<id>.md` exists on disk.
- If any extracted ID has no matching file, **flag** it in the output as "would be rejected by the spawn hook" — do not alter the prompt to work around it.
- Prose-only `Txxx` mentions (e.g. inside the pasted `MEMORY.md` text) that don't match either structural marker (a `TASK_GUIDE_Txxx.md` reference, or a `Task ID:` declaration line) are correctly ignored by the hook and must not be flagged here.

#### 5. Recommend spawn model
Map the guide's `**Complexity Level**` to a model, per the table already in `CLAUDE.md` Stage 3 / `general-agent-template.md`: C0→haiku, C1→sonnet, C2→sonnet/opus, C3→opus.

#### 6. Output
Return:
1. The assembled prompt as a single fenced block, ready to paste into `Agent({ subagent_type: "...", prompt: "..." })`.
2. The pre-flight verdict (safe, or list of flagged tokens).
3. The recommended spawn model.

The Supervisor reads this output and issues the `Agent()` call itself; this skill never calls it.

### Communication Protocol
- **Default Notification**: "craft-spawn-prompt complete for [Task ID]. Flavor: [standard/bugfix]. Pre-flight: [safe/flagged: ...]. Recommended model: [haiku/sonnet/opus]."
