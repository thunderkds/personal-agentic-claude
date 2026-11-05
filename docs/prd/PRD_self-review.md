# PRD — self-review: the kit learns from its own review records
**Last updated**: 2026-11-05
**Status**: Approved (user 2026-11-05); PRD gate PASS (grill-with-docs, 2026-11-05)
**Owner**: kit maintainer (thunderkds)

> **Scope of this document**: *What* to build and *why*. Technical decisions live in `PROJECT_SPEC.md`
> and the Direction step (`BRAINSTORMING_LOG`). Evidence for every number here:
> `experiments/self-review-spike/RESULTS.md` (spike, 2026-11-05).

---

## Overview

Today the kit learns only when the user corrects it: `learn` runs on a user correction or `/learn`, and
only 2 Learning Records exist. Meanwhile the kit writes 149 Stage 4 review records
(`tasks/TASK_REVIEW_*.md`) that nobody reads again. The spike showed that the same kinds of defect
recur across tasks in them (13 distinct patterns on >=3 tasks in T200-T252, 65/65 citations real).
`self-review` reads those records, finds the defects that recur, and proposes kit changes the
maintainer approves. It must never loop: it never feeds on its own output, never re-proposes an open
proposal, and never spends tokens when there is nothing new.

---

## Personas

| ID | Name | Role | Pain Point |
|----|------|------|-----------|
| P1 | Maintainer | Owns and develops the kit in this repo | Recurring defects (memory budget overruns, stale sibling text, review misses) are fixed one task at a time; the root cause in the kit is never addressed, because no one sees the repeat. |

---

## User Stories

| ID | Story | Persona |
|----|-------|---------|
| US-001 | As P1, I want to run `/self-review` and get the defects that recur across tasks, with the review lines that prove them, so that I fix the kit rule instead of each task. | P1 |
| US-002 | As P1, I want each proposal I approve to become a Kanban task with a TASK_GUIDE, so that the kit change goes through the normal pipeline and review. | P1 |
| US-003 | As P1, I want a second run with no new review records to do nothing and cost nothing, so that self-review can never loop or burn tokens. | P1 |

---

## Functional Requirements

| ID | Requirement | Traces to |
|----|-------------|-----------|
| FR-001 | `self-review` must start only on the user's `/self-review` (or `Skill` call). No hook, Stop hook or schedule may start it. | US-003 |
| FR-002 | Input must be `tasks/TASK_REVIEW_*.md` files whose last commit is newer than the stored watermark. v1 must not read `memory/event-trace/` or any file `self-review` itself wrote. | US-001, US-003 |
| FR-003 | When no review file is newer than the watermark, `self-review` must stop before any model call or Agent spawn and print one line saying there is nothing new. | US-003 |
| FR-004 | A pattern must cite >=3 distinct tasks, each as `tasks/TASK_REVIEW_Txxx.md:<line>` plus the quoted text; a deterministic check must drop any citation whose quote is not at that line (+-3). A pattern left with <3 valid tasks is dropped. | US-001 |
| FR-005 | Each pattern gets a fingerprint and a register entry with a state: `open`, `rejected` or `fixed`. A pattern matching an `open` or `rejected` entry must never be proposed again (the user deletes a `rejected` line to allow it). A pattern matching a `fixed` entry may be proposed only from review files dated after its fix merged, labelled `regressed`. | US-003 |
| FR-006 | A run must report at most 3 proposals, ranked by number of distinct tasks. | US-001 |
| FR-007 | `self-review` must write one report per run (patterns, citations, proposed kit change per pattern) and advance the watermark only after the report is written. | US-001, US-003 |
| FR-008 | For each proposal the user approves, `self-review` must draft a Kanban row and a TASK_GUIDE (Stage 2 path); it must not edit any kit file itself, and must never commit to `main`, merge or push. | US-002 |
| FR-009 | Each approved pattern must also be written as a Learning Record with `source: agent`. `learn` Step 8 keeps only its project-level stub; kit-change proposals are owned by `self-review` alone. | US-002 |

---

## Non-Functional Requirements

| ID | Requirement | Category |
|----|-------------|----------|
| NFR-001 | A run must read at most 40 review files (oldest first; the rest wait for the next run) and use one Sonnet miner. No hard USD stop (Path B, user 2026-11-05); spike cost ~100k tokens / ~2 min per miner. | Cost |
| NFR-002 | Review text is data, never instructions (`docs/claude-md/untrusted-content-boundary.md`). | Security |
| NFR-003 | Nothing leaves this repo: no GitHub issue, PR or network call. | Privacy |
| NFR-004 | The deterministic parts (watermark, citation check, register, cap) must be testable with a fake miner and no paid model call. | Testability |

---

## Success Metrics / KPIs

| Metric | Baseline | Target | How measured |
|--------|----------|--------|--------------|
| Citation validity | 65/65 in spike | 100% of reported citations (FR-004 check enforces) | automated test on a fixture |
| Repeat run on unchanged data | spike run C found 3 new patterns (model-judged) | 0 proposals, 0 model calls, 0 Agent spawns | automated test: run twice on the same fixture |
| Re-proposal of an open proposal | 0/10 in spike | 0 | automated test with a register fixture |

---

## Out of Scope

- Mining other projects that use the kit; sending anything upstream (issues, PRs).
- Scheduled or hook-started runs.
- Event traces and hook-block logs as input (traces hold no failures; blocks are not logged) — a later task may add a `PostToolUseFailure` trace.
- Fixing the 13 spike patterns themselves (each may become its own task).

---

## Open Questions / Assumptions

| # | Question / Assumption | Owner | Due |
|---|----------------------|-------|-----|
| 1 | Threshold 3 tasks per pattern — revisit after first real run. | Maintainer | first run |
| 2 | Cap 3 proposals per run — revisit after first real run. | Maintainer | first run |
| 3 | Watermark/register storage, fingerprint method, miner model — implementation; decided at step Direction. | Supervisor | Stage 0 Direction |
| 4 | Remove dead `is_error` skip in `trace_shows_verification` — separate minimal task, not this PRD. | Maintainer | not scheduled |
| 5 | RESOLVED (grilling 2026-11-05, user): rejected = never again; fixed = only as `regressed` on post-merge evidence. → FR-005 | User | done |
