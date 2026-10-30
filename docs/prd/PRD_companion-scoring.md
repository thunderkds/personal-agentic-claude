# PRD — Companion Scoring (easy-verifier + easy-ui at the Evidence Gate)
**Last updated**: 2026-10-28
**Status**: In Review (Stage 0.5a done — grilling decisions D1–D5 below; brainstorming not yet run)
**Owner**: maiphuong0204@gmail.com

> **Scope of this document**: *What* to build and *why*. Architecture and task state go to `PROJECT_SPEC.md` at Stage 2.
> Source: Stage 0.5 `grill-with-docs mode=requirement`, 2026-10-28. Each FR cites the grilling decision (D1–D5) it came from.

---

## Overview

The kit's Stage 4/5 Evidence Gate is filled by the reviewer's own judgement. Its one hook-enforced
row is `verify`, and even that is trusted only against the event trace. Everything else — "code
review clean", "responsive at 375 px" — is a claim written by the same agent whose work is being
judged. Two companion MCP servers already exist on this machine and the kit uses neither:

- **easy-verifier-mcp** rates a repository or a change on 14 dimensions with deterministic rules
  over cited facts, and returns two headline numbers: `overall` and `change_risk`. No LLM runs
  inside it. It also has an **evaluate gate**: for a dimension its rules cannot decide (`solution-fit`
  has no static rule; any metric within ±10% of its threshold is borderline) it asks the calling
  agent for a rating, with evidence, and blends that answer in at half its confidence as weight.
  That asking round exists over MCP only.
- **easy-ui-mcp** drives Chromium through Playwright over MCP and returns a pass/fail session with
  screenshots and an HTML report.

This feature makes both available to the kit as **options**: a number the merge gate can refuse on,
and a browser run that can fill the three UI design rows. Neither server becomes a requirement —
a machine without them must still finish tasks.

---

## Personas

| ID | Name | Role | Pain Point |
|----|------|------|-----------|
| P1 | Reviewer (Supervisor at Stage 4) | Fills the Evidence table | Has no measured number; "looks fine" is the evidence |
| P2 | Developer merging | Runs the push that trips the merge gate | A weak change passes the gate because nothing measured it |
| P3 | Developer without the tools | Runs the kit on a machine with no Docker and no verifier installed | A hard tool dependency would stop every task |
| P4 | Reader of the site | Reads what the kit claims about these two servers | Copy that overclaims integration is a lie either way it drifts |

---

## User Stories

| ID | Story | Persona |
|----|-------|---------|
| US-001 | As a reviewer, I want a finished task's Evidence table to carry a score from a tool that does not guess, so the row is a measurement and not an opinion. | P1 |
| US-002 | As a developer, I want a change that scores under the floor to be refused by the merge gate I already have, not by a second gate I have to learn. | P2 |
| US-003 | As a reviewer, I want the dimensions the verifier's rules cannot decide answered from evidence I already hold, instead of left abstained. | P1 |
| US-004 | As a reviewer of a UI task, I want a real browser run to be one of the ways I can fill the three design rows. | P1 |
| US-005 | As a developer with neither tool installed, I want the task to finish, with the row naming what was missing and what was tried. | P3 |
| US-006 | As a reader of the site, I want it to say exactly what the kit does with these servers: it can call them, it never requires them. | P4 |

---

## Functional Requirements

| ID | Requirement | Traces to |
|----|-------------|-----------|
| FR-001 | `templates/TASK_REVIEW_template.md` gains one Evidence row, **Companion score (easy-verifier)**, with `☐ pass / ☐ fail / ☐ N/A` and Notes carrying `overall`, `change_risk`, the scope and ref scored, and the absolute path of the verifier report. (D1) | US-001 |
| FR-002 | The floor is `overall ≥ 80`. Below it the row reads `fail`. A failing `change_risk` rule (a bugfix with no matched regression test, a refactor that deleted a test) sets the row to `fail` whatever `overall` says, because `change_risk` is never averaged into `overall`. (D2) | US-001, US-002 |
| FR-003 | The floor is declared in the kit's doctrine and in the scoring skill. A `TASK_GUIDE` may never name its own floor. (D2) | US-002 |
| FR-004 | `.claude/hooks/pre_bash_block_unsafe_merge.py` gains one check beside its existing `verify` check: a Ready-for-Review task whose Companion score row — or any of its three UI design rows — explicitly reads `fail` blocks the push or merge. No second gate is added. (D1, D6; corrected 2026-10-28 — the hook reads no row but `verify` today) | US-002 |
| FR-005 | A `pass` Companion score row is trusted only when the verifier report file its Notes cite exists on disk. A row that cites no path, or a path that is absent, is **not a pass**: it is treated as unscored, and the reviewer must rewrite it as `N/A`. This is the same "measured, not claimed" rule the `verify` row already follows against the event trace. | US-002 |
| FR-006 | An absent row, a blank row, an unchecked-placeholder row, and an `N/A` row with a written reason all **never block**. Only an explicit `fail` blocks. (D5, D6) | US-005 |
| FR-007 | A new scoring skill runs the verifier, reads the two headline numbers, writes the row, and answers the verifier's `needs_input`: `change_kind` (confirm or override the detected kind) and `gate_evaluations` (rate a dimension the rules could not decide). (D3) | US-003 |
| FR-008 | A gate evaluation the kit submits must carry at least one resolving evidence reference drawn from evidence the kit already holds: the Stage 4 `code-review` findings, the task's Acceptance Criteria, or an easy-ui session report. A gate the kit cannot answer from held evidence is left abstained and reported as abstained. The kit never invents a rating. (D3) | US-003 |
| FR-009 | Degradation ladder, in order: registered MCP server (full function, including the asking round) → command line `python -m easy_verifier.adapters.cli score` (score only; the CLI never asks) → neither available, the row reads `N/A` naming the missing tool and the ladder step reached. The task is never stuck. (D5) | US-005 |
| FR-010 | A `ui-test` skill health-checks `http://localhost:8765/health`, drives a labelled easy-ui session, and pastes the verdict plus the report path into the three UI Evidence rows. (D4) | US-004 |
| FR-011 | `templates/TASK_GUIDE_template.md`'s three UI/Design sections name easy-ui as **one** verification method among the existing ones. The rows stay fillable by screenshot diff, LLM vision or Storybook snapshot. easy-ui not running means another method is used, never a stall. (D4) | US-004, US-005 |
| FR-012 | `site/index.html` `#mcps` copy and `tests/test_site_content.py` change together: the kit can call both servers and requires neither. `HONESTY_PHRASES` is re-based so it still catches the overclaim without banning the true sentence — it currently bans the substring `required`, which the honest wording needs. | US-006 |
| FR-013 | `PROJECT_SPEC.md` gains two glossary terms kept apart: **Companion score** (the kit's own Evidence row and its floor) and **evaluate gate** (easy-verifier's round where it asks the caller to rate what its rules cannot decide). Neither name is used for the other thing. | US-003 |
| FR-014 | **The whole feature is optional, and that is tested.** On a machine with neither server registered, running or installed, the pipeline, the merge hook and every template behave exactly as they did before this feature: no row is required, no stage stops, no command is attempted that needs either tool. A regression test asserts the no-tool path is unchanged. (D6) | US-005 |
| FR-015 | **Binding only when used.** A verifier run that happened is binding: the code must clear the floor. An easy-ui session that ran is binding: it must pass. Neither tool being used is not a finding, not a warning and not a row — it is the normal flow. (D6) | US-002, US-005 |

---

## Non-Functional Requirements

| ID | Requirement |
|----|-------------|
| NFR-001 | No outbound network request is made for scoring. Both servers are local; the verifier makes none by design. |
| NFR-002 | A scoring run writes no file into the evaluated repository when `EASY_VERIFIER_REPORTS_DIR` is set, and never into either companion repo. |
| NFR-003 | The verifier redacts a matched secret to a non-reversible fingerprint when it reads it. The kit never copies a raw matched value into an Evidence row, a report or a commit message. |
| NFR-004 | The shared verifier container listens on `127.0.0.1:8766` with no authentication, so while it runs any local process can read the mounted repositories through it read-only. The kit documents this where it tells an operator to start the container; it never starts one itself. |

---

## Out of Scope

- Installing, starting or orchestrating either server. The kit detects and uses; the operator runs.
- Any change to the kit's own `/verify` skill or its Evidence row.
- Any blocking gate beyond the one row check added to the existing merge hook.
- Per-dimension floors. Only `overall` and `change_risk` gate a merge.
- easy-ui beyond its v1 surface: web Chromium, local only. No mobile.
- Scoring the minimal track. The Companion score is an extended-track Evidence row.

---

## Open Questions

| ID | Question | Owner | Resolve by |
|----|----------|-------|-----------|
| OQ-001 | **Resolved 2026-10-28** — `changes --ref <base>...HEAD`. Not a preference: `change_risk.py:260` abstains unless the scope is `changes` or `worktree` (`SCOPE_ONLY`, `change_risk.py:91`), so the kit-aware `task` scope can never produce the sharp half of the floor in FR-002. | Supervisor | closed |
| OQ-002 | <!-- FLAGGED: unresolved --> Names for the two new skills, against the kit's existing roster. `ui-test` is the name the unlanded 2026-07-01 branch used. | Supervisor | Stage 2 |

---

## Grilling Decisions (D1–D5, 2026-10-28)

| ID | Decision |
|----|----------|
| D1 | A low score turns an Evidence row to `fail` and the merge gate refuses it. No separate score gate is built. |
| D2 | The floor is `overall ≥ 80`, and a failing `change_risk` rule fails the row on its own. Not per-Risk-level, not per-task. |
| D3 | The kit reads the score **and** answers the verifier's evaluate gate, with evidence it already holds. |
| D4 | easy-ui is **one named option** for the three UI design rows, not the required method and not kept out of the gate. |
| D5 | Absent tool: prefer MCP, fall back to the CLI, else skip with a note naming what was missing. The task is never stuck. |
| D6 | **Optional, and binding only when used.** User, 2026-10-28: *"if you use verifier mcp, and ui to check, the code must pass them. if not, just work on the normal flow, that all"*. A tool that ran is binding and its `fail` blocks the merge. A tool nobody ran changes nothing: no row, no stop, no dependency. This selected **Path A** (a standalone Stage 4 skill) on its own, because Path B folds an optional tool into a mandatory skill and Path C makes the scorer required on every machine. |
