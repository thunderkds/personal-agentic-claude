# Token & focus finding — 2026-09-25

> Measured by the Supervisor on 2026-09-25 from Claude Code session transcripts, before re-planning
> T124. The numbers below are the **baseline** that T124's meter must reproduce and that T125–T127
> are judged against. Prototype scripts were throwaway (scratchpad); T124 rebuilds them with tests.

## Source

Claude Code writes one JSONL transcript per session under
`$CLAUDE_CONFIG_DIR/projects/<project-slug>/` (here `~/.claude-personal/projects/`), and sub-agent
transcripts under `<session>/subagents/`. Every assistant API call carries a `usage` object:
`input_tokens`, `cache_creation.ephemeral_1h_input_tokens` / `ephemeral_5m_input_tokens`,
`cache_read_input_tokens`, `output_tokens`. This is the **structural, automatic** cost source that
DDR-0002 said any future token work would need — no human pastes `/cost`.

**Pricing model (billed-equivalent, claude-opus-5 API rates, $5 in / $25 out per MTok):** input 1×,
1-hour cache write 2×, 5-minute cache write 1.25×, cache read 0.1×. A token added to context costs one
cache write plus a 0.1× read on every later call in that session ("carry cost"). Multipliers from the
Anthropic prompt-caching docs; confirm rates before quoting dollars. On a subscription plan the
dollars are a proxy for usage-limit consumption; the percentages are what matter.

**Estimates:** 3.5 characters per token; carry cost assumes no compaction (so savings are upper bounds).
API calls are de-duplicated by `message.id` (streamed chunks share one).

## Scope

73 transcripts (19 sub-agent), 3,422 API calls, **$389** billed-equivalent, all projects under the
config dir as of 2026-09-25.

## Findings

### 1. Where spend goes

| Component | Share |
|---|---|
| Cache reads (context re-read every call) | 53% |
| Cache writes | 32% |
| Output | 15% |
| Uncached input | ~0% |

Median context per API call: **105k tokens** (p90 224k). Fixed prefix at a session's first call:
main median **43k**, sub-agent median **17k**; carried through each session it costs ≈ **23%** of spend.

### 2. Supervisor vs spawned agents

Supervisor (non-spawned) sessions: **$359 of $389 (92%)**, median 48 calls per session. What they carry,
beyond the fixed prefix (carry-weighted share of all spend):

| Content | Share |
|---|---|
| Bash tool results | 12.2% |
| Tool-call inputs written by the assistant (Edit/Write payloads etc.) | 7.7% |
| Read tool results | 6.7% |
| User prompts + skill bodies | 5.1% |
| Skill listing attachments | 3.0% |
| Assistant text | 2.6% |
| Hook output (`hook_success`, incl. a user-level status-line hook on every prompt) | 1.7% |

### 3. Spawned agents (the agent-to-agent handoff)

14 transcripts whose first message names a `TASK_GUIDE_Txxx` (13 in-process, 1 terminal). Medians:

| Metric | Baseline |
|---|---|
| Spawn prompt | 4,171 chars |
| Fixed prefix | 15.6k tokens |
| **Read before the first Edit/Write** | **16.8k tokens over 8 calls** |
| Context at first edit | 48k tokens |
| Calls per spawn | 29 |
| Pre-edit reading, carried to session end | **17% of spawn spend** (range 10–35%) |

Most-read file before the first edit: `memory/MEMORY.md` (6 of 14; 41k chars ≈ 12k tokens, a
whole-project index). DDR-0004 measured that trimming the **spawn prompt** saves little (it is already
in the Supervisor's cache); this is different — files the agent **reads itself** are new tokens,
written at 2× and re-read each call.

### 4. Bash output compression (the original T124 plan)

Replaying the planned rule (stdout > 200 lines → first 40 + error lines + last 60) over every Bash
result: **45 of 2,573** outputs qualify; saving **$4.06 = 1.04%** of spend. Sensitivity: >150 lines
1.4%, >100 2.5%, >50 4.7%. **Recall risk:** in 5 of 45 (11%) the agent quoted an elided line within
its next 3 outputs. Below DDR-0001's own 5% rollback trigger at every threshold → parked.

## Consequence

The overwhelm is in the **Supervisor's long sessions** and in **what a spawned agent reads before it
starts**, not in oversized tool output. See DDR-0009 and T124–T127.
