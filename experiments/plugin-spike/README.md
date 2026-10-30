# T216 — plugin spike (throwaway)

Question: can Easy Kit ship as a Claude Code plugin, and does the same folder work in Codex?
Decision context: `docs/brainstorming/BRAINSTORMING_LOG_distribution.md` (Option C, step 1).

## What is here

- `.claude-plugin/marketplace.json` — a one-plugin marketplace (`ekspike-market`)
- `ekspike/` — the plugin: skill `hello` (runs a script by plugin path), agent `probe`, one `PreToolUse` hook (`hooks/gate.py`) that blocks `echo SPIKE_BLOCK_ME` only in a folder with `PROJECT_KANBAN.md`
- Test: `tests/test_plugin_spike.py`

## Results (2026-10-30, Claude Code 2.1.314, codex-cli 0.163.0)

| # | Question | Claude Code | Codex |
|---|---|---|---|
| 1 | Manifest valid / installs from the marketplace | ✅ `Validation passed with warnings` (no author); `Successfully installed plugin: ekspike@ekspike-market (scope: user)` | ✅ `Added plugin ekspike from marketplace ekspike-market` — same folder, no second manifest |
| 2 | Skill loads, under which name | ✅ `ekspike:hello` | ✅ listed as `ekspike:hello` |
| 3 | Skill script path resolves | ✅ both `${CLAUDE_PLUGIN_ROOT}` and `${CLAUDE_SKILL_DIR}` expanded; `HELLO_OK via plugin-root`, `HELLO_OK via skill-dir` | not run |
| 4 | Agent spawn by prefixed name | ✅ `subagent_type: ekspike:probe` → `PROBE_OK` | not run |
| 5 | Agent spawn by bare name | ❌ `Agent type 'probe' not found. Available agents: claude, ekspike:probe, …` | not run |
| 6 | Blocking hook in a kit project | ✅ `ekspike gate: 'SPIKE_BLOCK_ME' is blocked in a kit project` | ❌ command ran, not blocked (hooks untrusted; see below) |
| 7 | Same hook outside a kit project | ✅ ran, no message | — |
| 8 | What a hook sees for an agent spawn | `subagent_type: "ekspike:probe"` (prefixed) | — |

Live cost: 5 headless Claude runs on haiku, $0.018 total; 1 Codex run, 3,127 tokens.

## What it means for the kit

- **Claude Code: a plugin works.** Skills, agents, blocking hooks and script paths all work from a plugin.
- **Every bare name must change.** Spawns need `easy-kit:backend-developer`, so the `subagent_type` table in `AGENTS.md`, the role guides and `craft-spawn-prompt` must name the prefixed form in plugin mode. The agent hooks are not affected: `pre_agent_validate_guide.py` and `pre_agent_step_limit.py` find the task from the Task ID in the spawn prompt (`lib/task_context.py`), not from the agent name. `post_tool_trace.py` only records `agent_type`.
- **Gate hooks must no-op outside a kit project.** The `PROJECT_KANBAN.md` check works, as rows 6 and 7 show.
- **Codex: the folder installs and skills load, but the gate did not fire.** `codex features list` shows `hooks stable true` and `plugin_hooks removed false`. Codex documents that plugin hooks need trust through `/hooks`. The run that bypasses trust (`--dangerously-bypass-hook-trust`) was refused by this session's safety check, so the cause is unconfirmed. Until it is, Codex users keep `setup.sh` for the gates.

## Rerun

```bash
python3 -m pytest -q tests/test_plugin_spike.py
claude plugin validate experiments/plugin-spike
cd <folder with PROJECT_KANBAN.md> && claude -p "Run this exact bash command: echo SPIKE_BLOCK_ME" \
  --plugin-dir <repo>/experiments/plugin-spike/ekspike --model haiku --max-budget-usd 0.5 --allowedTools "Bash(echo:*)"
```
