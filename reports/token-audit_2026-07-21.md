# Token Audit Log — Window opened 2026-07-21 — **CLOSED 2026-08-04**

> **Closure**: closed by the **14-calendar-day** condition (2026-07-21 → 2026-08-04, exactly 14
> days), not the 7-session cap — only 4 qualifying sessions (`cold-start`/`wake`) were logged in
> this window: 2026-07-21, 2026-07-23, 2026-07-24, 2026-08-04. This is a legitimate OR-condition
> close with real automatically-derived data (95 entries), not a repeat of the original instrument
> failure DDR-0001 Amendment 1 describes (zero manual `/cost` entries ever logged) — so this does
> not trigger Amendment 1's "if the reopened window also comes up short, write a superseding DDR"
> clause. T030 may proceed with Supervisor+user (HITL) analysis of this window's data, noting the
> lighter sample (4, not 7, sessions). Next window: `reports/token-audit_2026-08-04.md`.

> **What this is**: baseline measurement instrument per DDR-0001 (see Amendment 1,
> 2026-07-21). Entries below are **derived automatically** from
> `memory/event-trace/*.jsonl` by `scripts/token-audit.sh` (T040) — not typed by
> hand. Re-running the script regenerates the entries table from current trace
> data each time; running it twice with unchanged trace data produces byte-identical
> output (idempotent by construction — nothing is ever appended). This is a
> generated, window-scoped artifact — it lives in `reports/`, not `memory/`.

## Window-close condition

This window closes at **7 logged sessions or 14 calendar days, whichever comes
first** (from 2026-07-21). A session = one conversation that ran `wake`. When
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
2026-07-14 | stage-3 | T013 | miss | ? | derived from Skill trace record
2026-07-14 | spawn | T018 | miss | ? | derived from Agent trace record
2026-07-14 | spawn | T020 | miss | ? | derived from Agent trace record
2026-07-14 | spawn | T019 | miss | ? | derived from Agent trace record
2026-07-14 | stage-4 | overhead | miss | ? | derived from Skill trace record
2026-07-14 | stage-0.5 | T017 | miss | ? | derived from Skill trace record
2026-07-14 | spawn | T021 | miss | ? | derived from Agent trace record
2026-07-14 | spawn | T022 | miss | ? | derived from Agent trace record
2026-07-14 | spawn | T023 | miss | ? | derived from Agent trace record
2026-07-14 | stage-4 | overhead | hit | ? | derived from Skill trace record
2026-07-16 | cold-start | overhead | hit | ? | derived from Skill trace record
2026-07-16 | stage-0.5 | overhead | hit | ? | derived from Skill trace record
2026-07-16 | stage-2 | overhead | hit | ? | derived from Skill trace record
2026-07-16 | spawn | T025 | miss | ? | derived from Agent trace record
2026-07-16 | stage-3 | overhead | hit | ? | derived from Skill trace record
2026-07-16 | spawn | T025 | hit | ? | derived from Agent trace record
2026-07-16 | stage-4 | overhead | hit | ? | derived from Skill trace record
2026-07-16 | stage-4 | T025 | hit | ? | derived from Skill trace record
2026-07-16 | stage-0.5 | overhead | hit | ? | derived from Skill trace record
2026-07-16 | stage-2 | overhead | hit | ? | derived from Skill trace record
2026-07-16 | spawn | T027 | miss | ? | derived from Agent trace record
2026-07-16 | stage-3 | overhead | hit | ? | derived from Skill trace record
2026-07-16 | spawn | T027 | hit | ? | derived from Agent trace record
2026-07-16 | stage-4 | overhead | hit | ? | derived from Skill trace record
2026-07-16 | stage-4 | T027 | hit | ? | derived from Skill trace record
2026-07-17 | stage-0.5 | overhead | hit | ? | derived from Skill trace record
2026-07-17 | stage-2 | overhead | hit | ? | derived from Skill trace record
2026-07-17 | stage-2 | T027 | hit | ? | derived from Skill trace record
2026-07-17 | stage-3 | overhead | hit | ? | derived from Skill trace record
2026-07-17 | stage-4 | T028 | miss | ? | derived from Skill trace record
2026-07-17 | stage-5 | T028 | hit | ? | derived from Skill trace record
2026-07-17 | stage-0.5 | overhead | hit | ? | derived from Skill trace record
2026-07-17 | stage-2 | overhead | hit | ? | derived from Skill trace record
2026-07-17 | stage-0.5 | overhead | hit | ? | derived from Skill trace record
2026-07-17 | stage-2 | overhead | hit | ? | derived from Skill trace record
2026-07-17 | spawn | T031 | miss | ? | derived from Agent trace record
2026-07-17 | stage-3 | T031 | hit | ? | derived from Skill trace record
2026-07-17 | spawn | T031 | hit | ? | derived from Agent trace record
2026-07-17 | stage-4 | T031 | hit | ? | derived from Skill trace record
2026-07-17 | stage-5 | overhead | hit | ? | derived from Skill trace record
2026-07-17 | spawn | T032 | miss | ? | derived from Agent trace record
2026-07-17 | stage-3 | T032 | hit | ? | derived from Skill trace record
2026-07-17 | spawn | T032 | hit | ? | derived from Agent trace record
2026-07-17 | stage-4 | T032 | hit | ? | derived from Skill trace record
2026-07-17 | stage-5 | overhead | hit | ? | derived from Skill trace record
2026-07-17 | spawn | T033 | miss | ? | derived from Agent trace record
2026-07-17 | stage-3 | T033 | hit | ? | derived from Skill trace record
2026-07-17 | spawn | T033 | hit | ? | derived from Agent trace record
2026-07-17 | stage-4 | T033 | hit | ? | derived from Skill trace record
2026-07-17 | stage-5 | overhead | hit | ? | derived from Skill trace record
2026-07-17 | spawn | T034 | miss | ? | derived from Agent trace record
2026-07-17 | spawn | T035 | miss | ? | derived from Agent trace record
2026-07-17 | stage-3 | T035 | hit | ? | derived from Skill trace record
2026-07-17 | spawn | T035 | hit | ? | derived from Agent trace record
2026-07-17 | spawn | T034 | hit | ? | derived from Agent trace record
2026-07-17 | stage-4 | T035 | hit | ? | derived from Skill trace record
2026-07-19 | stage-4 | overhead | hit | ? | derived from Skill trace record
2026-07-19 | cold-start | overhead | hit | ? | derived from Skill trace record
2026-07-21 | cold-start | overhead | hit | ? | derived from Skill trace record
2026-07-21 | stage-3 | overhead | hit | ? | derived from Skill trace record
2026-07-21 | spawn | T042 | miss | ? | derived from Agent trace record
2026-07-21 | spawn | T042 | hit | ? | derived from Agent trace record
2026-07-23 | cold-start | overhead | hit | ? | derived from Skill trace record
2026-07-23 | stage-3 | overhead | hit | ? | derived from Skill trace record
2026-07-23 | spawn | T039 | miss | ? | derived from Agent trace record
2026-07-23 | stage-4 | T039 | hit | ? | derived from Skill trace record
2026-07-23 | stage-3 | overhead | hit | ? | derived from Skill trace record
2026-07-23 | spawn | T043 | miss | ? | derived from Agent trace record
2026-07-23 | stage-4 | overhead | hit | ? | derived from Skill trace record
2026-07-23 | stage-4 | T043 | hit | ? | derived from Skill trace record
2026-07-23 | stage-4 | overhead | hit | ? | derived from Skill trace record
2026-07-24 | cold-start | overhead | hit | ? | derived from Skill trace record
2026-07-24 | stage-3 | overhead | hit | ? | derived from Skill trace record
2026-07-24 | stage-4 | overhead | hit | ? | derived from Skill trace record
2026-07-24 | stage-4 | overhead | hit | ? | derived from Skill trace record
2026-07-24 | stage-4 | overhead | hit | ? | derived from Skill trace record
2026-07-30 | stage-3 | overhead | hit | ? | derived from Skill trace record
2026-07-30 | cold-start | overhead | hit | ? | derived from Skill trace record
2026-07-30 | stage-4 | overhead | hit | ? | derived from Skill trace record
2026-07-31 | stage-4 | overhead | hit | ? | derived from Skill trace record
2026-07-31 | stage-3 | overhead | hit | ? | derived from Skill trace record
2026-07-31 | spawn | T047 | miss | ? | derived from Agent trace record
2026-07-31 | spawn | T048 | miss | ? | derived from Agent trace record
2026-08-03 | spawn | T045 | miss | ? | derived from Agent trace record
2026-08-03 | spawn | T045 | hit | ? | derived from Agent trace record
2026-08-03 | stage-4 | overhead | hit | ? | derived from Skill trace record
2026-08-03 | stage-0.5 | overhead | hit | ? | derived from Skill trace record
2026-08-03 | stage-0.5 | overhead | hit | ? | derived from Skill trace record
2026-08-03 | stage-2 | overhead | hit | ? | derived from Skill trace record
2026-08-03 | stage-0.5 | overhead | hit | ? | derived from Skill trace record
2026-08-04 | cold-start | overhead | hit | ? | derived from Skill trace record
2026-08-04 | stage-3 | overhead | hit | ? | derived from Skill trace record
2026-08-04 | spawn | T049 | miss | ? | derived from Agent trace record
2026-08-04 | stage-4 | overhead | hit | ? | derived from Skill trace record
2026-08-04 | stage-4 | overhead | hit | ? | derived from Skill trace record
```
