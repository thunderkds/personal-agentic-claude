# TASK_GUIDE — T028: Token Audit Log — scaffold + entry convention + format test
**Date**: 2026-07-17
**Complexity Level**: C1
**Risk Level**: Low
**Priority**: P0
**Assigned agent**: backend-developer
**Agent guide**: `.claude/agents/backend.md`

---

## Mandatory Startup (Do Not Skip)

Before writing any code:
1. Read `PROJECT_SPEC.md` (especially the four glossary terms: Token Audit Log, Measurement Window, Cold-start cost, $ per completed task)
2. Read `memory/MEMORY.md`
3. Read this file completely
4. Read `.claude/agents/backend.md`
5. Read `docs/ddr/0001-measure-first-token-refactor.md` — the decision this task implements
6. C1 single-purpose task — `memory/codebase-map.md` not required

---

## Requirement (Pillar 1 — Adapt the requirement)

User wants to reduce token/billing spend but confirmed spend concentration is unknown. Per DDR-0001, the first step is a baseline measurement instrument: a Token Audit Log capturing per-session, per-stage, per-spawn cost signals over a bounded Measurement Window, before any refactor is chosen.

**Restated intent** (Supervisor's interpretation):
> Create the measurement instrument itself: a self-documenting audit-log scaffold in `reports/`, a hot-tier reminder so every future Supervisor session actually logs entries, and an automated format test so the convention is machine-checkable.

**Out of scope**:
- Any actual refactor (CLAUDE.md trim, spawn dedup, report trimming) — deferred to T030's data-driven decision
- Hooks or automation for entry-writing — the convention is deliberately manual (DDR-0001 accepted trade-off)
- The `slim-skills` run — that is T029

**Requirement Refs**:
- No `PRD.md` FR applies — internal framework task, same precedent as T023/T025/T027. Traces to DDR-0001 Follow-up item 1.

### Requirement Fidelity Gate (sign off BEFORE implementation)

- [x] Restated intent confirmed to match the user's request (locked in BRAINSTORMING_LOG.md User Selection, 2026-07-17)
- [x] Domain terms align with `PROJECT_SPEC.md` glossary (grill-with-docs run this session; 4 terms locked)
- [ ] Every Acceptance Criterion below traces to a line in the Requirement
- [x] Requirement Refs: N/A precedent confirmed (internal task, DDR-0001 is the source)

> An agent must NOT start implementing until this gate is checked. If anything here is unclear,
> STOP and ask the Supervisor (Karpathy: Think Before Coding).

---

## Dependencies & Reachability

**Depends on**: None
**Entry point**: `token-audit` — grep-able in the `memory/MEMORY.md` hot-tier reminder line and the `reports/token-audit_2026-07-17.md` filename; the log is consumed by Supervisor sessions (read at wake), not by code.

---

## Acceptance Criteria

| # | Criterion (testable) | Traces to requirement |
|---|----------------------|-----------------------|
| 1 | `reports/token-audit_2026-07-17.md` exists with a header documenting: entry format, tag vocabulary (Task ID / `overhead`), cache-hit/miss marking, model-tier marking, `/cost` end-of-session rule, and the window-close condition (7 sessions or 14 days) | "self-documenting audit-log scaffold" |
| 2 | Header includes ≥3 sample entries (cold-start, spawn, stage-transition) that parse against the documented format | "self-documenting" — a future session can copy the format without guessing |
| 3 | `memory/MEMORY.md` gains exactly one hot-tier line reminding the Supervisor to log audit entries each session; hot tier stays ≤200 lines | "every future Supervisor session actually logs entries" |
| 4 | An automated test validates the scaffold: file exists, header contains the required convention elements, and every sample entry line matches the documented entry regex | "machine-checkable convention" (Hard-Stop Gate 5) |
| 5 | Negative: a malformed entry line (missing Task-ID tag) fails the entry regex in the test | format is actually constraining, not decorative |

---

## Evaluation & Acceptance

### Success Criteria (observable, pass/fail)

| # | Given (input/state) | Expect (output/behavior) | How it's checked |
|---|---------------------|--------------------------|------------------|
| 1 | Fresh checkout of this branch | `pytest .claude/hooks/tests/test_token_audit_format.py -q` passes | automated test |
| 2 | A sample line missing the Task-ID/overhead tag | entry regex rejects it (test asserts non-match) | automated test |
| 3 | `wc -l memory/MEMORY.md` | ≤200 | automated test or shell check |

### Verification Command (exact, runnable)

```bash
pytest .claude/hooks/tests/test_token_audit_format.py -q && wc -l memory/MEMORY.md
```

### Evidence (filled by reviewer at Stage 4/5)

| Check | Result | Notes / output snippet |
|-------|--------|------------------------|
| **New test(s) cover Acceptance Criteria (file paths pasted)** | ☑ pass | `.claude/hooks/tests/test_token_audit_format.py` — 5 tests: scaffold exists, header documents convention elements, sample entries match entry regex, malformed entry rejected, MEMORY.md ≤200 lines |
| Verification command run | ☑ pass | `pytest .claude/hooks/tests/test_token_audit_format.py -q && wc -l memory/MEMORY.md` → `.....  [100%] 5 passed in 0.02s` / `110 memory/MEMORY.md` (run on `main` post-merge, 2026-07-19) |
| Negative cases hold | ☑ pass | Malformed entry (missing Task-ID/overhead tag) confirmed rejected by the entry regex test |
| verify | ☑ pass | Scaffold + tests verified twice: once on the rebased worktree branch pre-merge, once on `main` post-merge (after fixing the `reports/` gitignore gap — see Edge Case Checklist above) |
| Review scope bounded to the change's blast radius (affected set, not whole repo) | ☑ pass | Diff isolated to `.claude/hooks/tests/test_token_audit_format.py`, `memory/MEMORY.md` (+2 lines), plus the follow-on `.gitignore` fix + `reports/token-audit_2026-07-17.md`; no unrelated files touched (T031–T035 work explicitly left untouched per user decision) |
| Full smoke suite still green (no regression) | ☑ pass | Existing hook suite unaffected; only the new test file added |
| **UI: Visual regression** | ☐ N/A | pure-backend/docs task |
| **UI: Design-system compliance** | ☐ N/A | pure-backend/docs task |
| **UI: Responsiveness** | ☐ N/A | pure-backend/docs task |

---

## Approach

Per DDR-0001 and the grilling resolutions:
- **Home is `reports/`, not `memory/`** — the log is a generated, window-scoped artifact; putting it in `memory/` would violate the Memory Write Protocol's defined file set (explicit grilling decision).
- Entry format: one line per event — `<date> | <event: cold-start|stage-N|spawn|cost> | <task-tag: Txxx|overhead> | <cache: hit|miss> | <model-tier> | <approx size / notes>`. Exact field order may be adjusted for readability, but every field above must be present and the header must document whatever final shape is chosen.
- The MEMORY.md line is the *only* always-on cost this task adds (~1 line ≈ 20 tokens/turn) — deliberately NOT a CLAUDE.md edit (DDR-0001 defers all CLAUDE.md changes).
- Test lives with the existing Python test suite in `.claude/hooks/tests/` (pytest already in use there).

---

## Edge Case Checklist

- [ ] Audit log must not grow unbounded — header states the window-close condition and that a new window = a new file
- [ ] Cache-hit vs. miss is a heuristic (first occurrence in session = miss) — header must say so, so readers don't over-trust it
- [x] `reports/` is gitignored (local-only per prior decision) — confirm the audit file is still readable by future local sessions; if gitignore blocks needed persistence, flag to Supervisor instead of silently changing .gitignore — **triggered**: gitignore blocked cross-worktree persistence; flagged to user via AskUserQuestion before any `.gitignore` edit; user selected the gitignore-exception fix (`reports/*` + `!reports/token-audit_*.md`)
- [ ] MEMORY.md hot-tier line count must stay ≤200 after the addition
- [ ] Sample entries in the header must be clearly marked as samples so they're never counted as real data

---

## Files to Change (Predicted)

| File | Change |
|------|--------|
| `reports/token-audit_2026-07-17.md` | new — scaffold with convention header + sample entries |
| `memory/MEMORY.md` | +1 hot-tier reminder line |
| `.claude/hooks/tests/test_token_audit_format.py` | new — format/convention test |

## Files Must NOT Touch

| File | Reason |
|------|--------|
| `CLAUDE.md` | DDR-0001 explicitly defers all CLAUDE.md edits until baseline data exists |
| `memory/decisions.md`, `memory/glossary.md`, `memory/learnings.md` | Supervisor-only writes (Memory Write Protocol) |
| `.claude/skills/*/SKILL.md` | T029's scope, not this task's |
| `.gitignore` | flag to Supervisor if reports/ persistence is a problem — do not edit unilaterally |

---

## Test Plan

Pytest: (1) scaffold file exists; (2) header contains required convention elements (window rule, tag vocabulary, cache marking, `/cost` rule); (3) each sample entry matches the entry regex; (4) a deliberately malformed line does NOT match; (5) `memory/MEMORY.md` ≤200 lines.

---

## Completion Checklist

- [ ] Implementation done
- [ ] Self-review: `Skill({ skill: "code-review" })` run
- [ ] Lint passes
- [ ] Tests written AND pass — output pasted into Evidence table (Hard-Stop Gate 5)
- [ ] `Skill({ skill: "verify" })` run
- [ ] Supervisor notified: task ready for Stage 4 review
