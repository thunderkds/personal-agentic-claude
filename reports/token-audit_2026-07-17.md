# Token Audit Log — Window opened 2026-07-17 — **CLOSED INCONCLUSIVE 2026-07-21**

> **Status: closed inconclusive at 1 of 7 required sessions.** Logging stopped after
> 2026-07-17. T029/T034/T035/T036/T037/T038 all merged on 2026-07-19 across multiple
> sessions with zero entries, and `/cost` was never logged once — so no ground-truth
> number exists to check the tagged entries against.
>
> The manual per-session convention had no failure signal, so its collapse went
> unnoticed for 4 days. See DDR-0001 Amendment 1. The window reopens at
> `reports/token-audit_2026-07-21.md`, derived from `memory/event-trace/` by
> `scripts/token-audit.sh` (T040) instead of typed by hand.
>
> **Retained, not deleted** — the entries below are real, and the failure itself is the
> finding that justified T040. Do not append to this file.

> **What this is**: baseline measurement instrument per DDR-0001. One line per
> logged event, appended manually during Supervisor sessions. This is a
> generated, window-scoped artifact — it lives in `reports/` (gitignored,
> local-only), not `memory/`.

## Window-close condition

This window closes at **7 logged sessions or 14 calendar days, whichever
comes first** (from 2026-07-17). A session = one conversation that ran
`wake`. When the window closes, start a new file
(`reports/token-audit_<next-window-date>.md`) rather than appending further —
this file is not meant to grow unbounded.

## When to log an entry

One line each at: session cold-start (right after `wake`), every Stage
transition, and every `Agent()` spawn. Also append the session's `/cost`
output as a separate line at session end — that is the ground-truth number
the tagged entries are checked against.

## Entry format

```
<date> | <event> | <task-tag> | <cache> | <model-tier> | <notes>
```

| Field | Vocabulary |
|---|---|
| `date` | `YYYY-MM-DD` |
| `event` | `cold-start` \| `stage-N` (N = 0.5–5) \| `spawn` \| `cost` |
| `task-tag` | `Txxx` (the active Task ID) or `overhead` (no single task applies) |
| `cache` | `hit` \| `miss` — **heuristic, not exact**: first occurrence of a given context in a session is scored `miss`, repeats within the same session are scored `hit`. This is an approximation of prompt-cache behavior, not a real cache-hit measurement — do not over-trust it. |
| `model-tier` | `haiku` \| `sonnet` \| `opus` (per Complexity→model mapping in CLAUDE.md Stage 3) |
| `notes` | free text — approx size, what happened |

A line missing the `task-tag` field (no `Txxx` or `overhead` token) is
malformed and must not be treated as a valid entry.

## Sample entries (illustrative only — NOT real data)

```
2026-07-17 | cold-start | overhead | miss | sonnet | wake read 4 files, ~6k tokens
2026-07-17 | spawn | T028 | miss | sonnet | backend-developer spawn, TASK_GUIDE + MEMORY.md injected
2026-07-17 | stage-4 | T028 | hit | sonnet | code-review skill, CLAUDE.md cached from cold-start
```

## Real entries

2026-07-17 | cold-start | overhead | miss | opus | session start, brainstorming token-efficiency topic
2026-07-17 | spawn | T028 | miss | sonnet | backend-developer spawned in worktree pac-T028, TASK_GUIDE+MEMORY.md injected
2026-07-17 | stage-4 | T028 | hit | sonnet | code-review on T028 diff, found+fixed stray duplicate files on main
2026-07-17 | stage-4 | T029 | hit | sonnet | code-review on T029 diff (slim-skills output), zero findings
2026-07-17 | cost | overhead | miss | opus | verify skill run for T028 — see /cost at session end for ground truth
