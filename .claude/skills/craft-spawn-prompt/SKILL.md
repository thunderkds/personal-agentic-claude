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
Both shapes reuse the same checklist proven in `bugfix` Step 4; only element 2 and the presence of element 3 change:

| # | Element | Standard guide | Bugfix-flavored guide |
|---|---|---|---|
| 1 | Guide pointer | `tasks/TASK_GUIDE_Txxx.md` path | same |
| 2 | Orienting content | Guide's Restated Intent / Requirement section, verbatim | Confirmed Mental Model section, verbatim |
| 3 | First-action skill invocation | Only if the task explicitly requires one (e.g. `migration-safety` for schema work) — otherwise omit | `Skill({ skill: "diagnose" })` as the first action — always present |
| 4 | Memory injection | Full contents of `memory/MEMORY.md`, verbatim | same |
| 5 | Agent-guide pointer | `.claude/agents/<role>.md` from the guide's `**Agent guide**` field | same |
| 6 | Trace-attribution instruction | The active-task state-file line below, verbatim | same |
| 7 | Demonstration BEFORE-capture instruction | The BEFORE-capture line below, verbatim | same — for a bugfix guide, this is naturally satisfied by the Phase 1 repro loop the `diagnose` first action already builds; the instruction still restates the rule so the agent doesn't skip it under time pressure |

Any caller-supplied inputs (e.g. bugfix's fixed "invoke diagnose first" instruction) are accepted as parameters to this step, not re-derived.

**Element 6 — why a state file, not an env export (T047).** Hook trace attribution is structural only (`.claude/hooks/lib/task_context.py`), and a `Bash` `command` string is deliberately never scanned. Earlier guidance here told agents to run `CLAUDE_ACTIVE_TASK=Txxx <cmd>` or `export CLAUDE_ACTIVE_TASK=Txxx` inside a `Bash` tool call — **that does nothing.** A hook process is spawned by the harness as a *sibling* of the tool call, not a child of the command run inside it, so it inherits the harness's own environment, never the subshell a `Bash` tool call creates. Every record from that instruction landed in `_untagged.jsonl`, and `pre_bash_block_unsafe_merge.py:trace_shows_verification` correctly failed closed on it — blocking honest tasks. The env var still works when set in the process that *launches* the whole session (before `claude` starts), but not from inside a running one.

The fix is a channel `task_context.py` can actually observe: a plain state file, `<main-checkout>/.claude/hooks/.state/active_task`, written with a shell redirect from inside any `Bash` tool call. **The path must be a literal absolute path to the main checkout, not `$CLAUDE_PROJECT_DIR`.** That variable is real inside a hook's own spawned process (`settings.json`'s command strings rely on it, and `task_context.py` now resolves the state-file root from it there) — but it is a *different* process context from a `Bash` tool call's own shell, which does not inherit it (confirmed empirically: `echo $CLAUDE_PROJECT_DIR` from inside a `Bash` tool call prints empty). A sub-agent's cwd is its own worktree, so a bare relative path (`.claude/hooks/.state/active_task`) or an unset `$CLAUDE_PROJECT_DIR` reference both silently resolve to the wrong place — this was T047's own Stage 4 P1 finding, one layer below the defect the task was fixing. You (the Supervisor) run `craft-spawn-prompt` from the main checkout, so you already know the real absolute path at assembly time — embed it literally:

> **Trace attribution**: before running any test or verification command, write the active-task state file so the trace hook can attribute your `Bash` calls: `mkdir -p <absolute-path-to-main-checkout>/.claude/hooks/.state && printf '%s\n%s\n' "Txxx" "$(date -u +%Y-%m-%dT%H:%M:%SZ)" > <absolute-path-to-main-checkout>/.claude/hooks/.state/active_task` — substituting the real absolute path of the main checkout (not a variable, not a relative path) and `Txxx`. Do this once at the start of your session — it stays valid for `CLAUDE_ACTIVE_TASK_STATE_MAX_AGE_S` seconds (default 6h). Do **not** try `CLAUDE_ACTIVE_TASK=Txxx <cmd>` inside a `Bash` tool call, and do **not** write a cwd-relative path — neither reaches the hook, and both will leave your evidence unattributed.

Known limitation, not solved by this element: the state file is shared by every worktree using this checkout's hooks, so two tasks running verification at the same moment can race and mis-attribute each other's `Bash` calls. Safe for the common case (one task verifying at a time); flag genuinely concurrent Stage 3 verification to the Supervisor rather than trusting the file blindly.

**Element 7 — why this must be said before, not after (DDR-0003).** The guide's `## Demonstration` BEFORE field cannot be back-filled once an implementation commit exists — it is the one field in the whole checklist that isn't satisfiable by assertion after the fact. `pre_agent_validate_guide.py` only warns (non-blocking) when a referenced guide's BEFORE field is still blank at spawn time; it cannot verify a capture was taken at the *right* moment. The instruction is the substantive half of the mechanism, not the reminder — put it first in the spawn prompt, before any other implementation instruction:

> **Demonstration BEFORE capture**: before your first implementation commit, fill this guide's `## Demonstration` BEFORE field. If this task changes executable code, run the exact command(s) named in the guide's Demonstration section and paste the real, timestamped output — a BEFORE captured after the change is not a BEFORE, there is no `N/A` path. If it does not change executable code (docs/templates/skill-instruction text), BEFORE is the verbatim prior content of what you are about to change, quoted from the file as it exists right now.

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
