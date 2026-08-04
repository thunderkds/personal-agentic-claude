# Token Audit Log — Window opened 2026-08-04

> **What this is**: baseline measurement instrument per DDR-0001 (see Amendment 1,
> 2026-08-04). Entries below are **derived automatically** from
> `memory/event-trace/*.jsonl` by `scripts/token-audit.sh` (T040) — not typed by
> hand. Re-running the script regenerates the entries table from current trace
> data each time; running it twice with unchanged trace data produces byte-identical
> output (idempotent by construction — nothing is ever appended). This is a
> generated, window-scoped artifact — it lives in `reports/`, not `memory/`.

## Window-close condition

This window closes at **7 logged sessions or 14 calendar days, whichever comes
first** (from 2026-08-04). A session = one conversation that ran `wake`. When
the window closes, start a new file
(`reports/token-audit_<next-window-date>.md`) rather than appending further.

## Entry format

```
<date> | <event> | <task-tag> | <cache> | <model-tier> | <notes>
```

| Field | Vocabulary |
|---|---|
| `date` | `YYYY-MM-DD` (UTC) |
| `event` | `cold-start` \| `stage-N` (N = 0.5–5) \| `spawn` |
| `task-tag` | `Txxx` (structurally attributed, see `lib/task_context.py`) or `overhead` (unattributed) |
| `cache` | `hit` \| `miss` — heuristic only: first occurrence of a task-tag in this file is scored `miss`, repeats are `hit`. Not a real cache-hit measurement — do not over-trust it. |
| `model-tier` | `haiku` \| `sonnet` \| `opus` \| `?` — `?` when the trace record does not carry a model field. Never guessed. |
| `notes` | free text — which trace record this line was derived from |

**Known ceiling (accepted, DDR-0001 Amendment 1)**: hooks cannot observe real
token counts and no hook can capture `/cost`. Only the event stream (cold-start /
stage transitions / spawns) is automated here. Append the session's `/cost`
output manually as a separate line at session end — that is the ground-truth
number the tagged entries are checked against. No token count is ever
estimated or synthesized by this generator.

## Entries (derived — do not hand-edit; re-run `scripts/token-audit.sh` instead)

```
2026-08-04 | cold-start | overhead | hit | ? | derived from Skill trace record
2026-08-04 | stage-3 | overhead | hit | ? | derived from Skill trace record
2026-08-04 | spawn | T049 | miss | ? | derived from Agent trace record
2026-08-04 | stage-4 | overhead | hit | ? | derived from Skill trace record
2026-08-04 | stage-4 | overhead | hit | ? | derived from Skill trace record
2026-08-04 | stage-3 | overhead | hit | ? | derived from Skill trace record
2026-08-04 | spawn | T050 | miss | ? | derived from Agent trace record
```
