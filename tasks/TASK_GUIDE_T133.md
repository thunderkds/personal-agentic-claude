# TASK_GUIDE — T133: Replies to the user read plainly — technical detail on request
**Date**: 2026-09-26
**Complexity Level**: C1
**Risk Level**: Low
**Priority**: P1
**Assigned agent**: common-infrastructure
**Agent guide**: `agents/common-infrastructure.md`

---

## Mandatory Startup (Do Not Skip)

Before writing any code:
1. Read `PROJECT_SPEC.md`
2. Read the memory slice in your spawn prompt (`<!-- memory-slice -->`). Read `memory/MEMORY.md` in full only if your work reaches a file, hook, skill or decision the slice does not cover
3. Read this file completely
4. Read `agents/common-infrastructure.md`
5. Note the **Complexity Level** above and apply the matching process from the Complexity matrix in your role guide
6. C1, but multi-file: skim `memory/codebase-map.md` only if you need to locate a test beyond the ones named below

---

## Requirement (Pillar 1 — Adapt the requirement)

User, 2026-09-26: *"Checking to make the response from agent look more human reading, not the
technical response in some case."*

Clarified by the user the same day (forced choice):
- **Scope: replies to the user only** — the Supervisor's chat messages and the prose of sub-agent
  reports the user reads. `PROJECT_KANBAN.md` rows, TASK_GUIDE/TASK_REVIEW Evidence, `memory/` and
  commit messages stay fully technical: they are the audit trail.
- **Default: plain first, detail on request** — say what happened and why it matters in everyday
  words; keep code, errors, paths and commands verbatim; a task ID or internal term appears only
  with a few words saying what it is; deeper technical detail only when the user asks.

User note, 2026-09-26 (after the guide was first drafted): *"the human readable should focus on the
question to ask the users in the most case, for the plain, should be highlight to make the content
focusing on"*. Read as two refinements:
- **Primary target = questions to the user.** The plain-language rule matters most when the agent
  asks the user to decide something (a chat question or an `AskUserQuestion` prompt and its
  options): the question must be answerable by someone without the project history.
- **Highlight the focus.** In a plain reply, the one thing the user must read or act on is
  highlighted (bold), so the eye lands on it first.

**Restated intent**:
> T100/T103 fixed the *shape* of a reply (answer first, no needless tables, no re-lists). Nothing
> governs its *vocabulary*, so a well-shaped reply can still read as an engineering log — bare task
> IDs, project shorthand ("diff-driven pass", "dormant catalog", "container replay") and hook names
> the user must already know. Success = a reader who has not followed the project's history can
> understand — and **answer** — a question the Supervisor puts to them without asking what its
> terms mean, and can spot the one thing they need to act on at a glance.

**Observed defect (measured, not assumed)**: the Supervisor's own `/wake` reply on 2026-09-26 obeyed
all seven current rules and still used undefined shorthand throughout; the user's request followed it.

**Out of scope**:
- The audit trail (Kanban rows, Evidence, `memory/`, commits, DDRs) — unchanged.
- Generated HTML reports and the `wake` briefing format (user chose "replies to you only" over
  "everything user-facing").
- Any hook, linter or response-text checker (same cut as T100: guidance, not machinery).
- Rewording the seven existing rules.

**Requirement Refs**: none in `PRD.md` — framework-behaviour task, same as T100/T103.

### Requirement Fidelity Gate (sign off BEFORE implementation)

- [x] Restated intent confirmed to match the user's request (user, forced choice, 2026-09-26)
- [x] Domain terms align with `PROJECT_SPEC.md` glossary
- [x] Every Acceptance Criterion below traces to a line in the Requirement
- [x] No PRD refs — none apply

---

## Dependencies & Reachability

**Depends on**: None — T100, T103 and T127 are Done and merged into this branch.

**Entry point**: `### Response Standard` (in `CLAUDE.md`) and `## Response Standard` (in `agents/general-agent-template.md`)

---

## Acceptance Criteria

| # | Criterion (testable) | Traces to requirement |
|---|----------------------|-----------------------|
| 1 | The Response Standard gains **at most two** new bullet lines stating the plain-language default: plain words first; a task ID, internal term or hook name gets a short gloss; technical depth only on request. The rule names **questions to the user** (chat questions and `AskUserQuestion` prompts/options) as where it applies most, and says to **bold the one thing the user must read or act on**. Existing seven lines byte-unchanged. | "plain first, detail on request"; user note: questions first, highlight the focus |
| 2 | The new line(s) appear **byte-identical** in both `CLAUDE.md` and `agents/general-agent-template.md` (T103's two-channel rule: `CLAUDE.md` reaches the Supervisor, the template reaches sub-agents). | "replies to the user" — Supervisor *and* sub-agent reports |
| 3 | The new rule keeps the audit-trail carve-out: the existing "Replies only — Evidence, KANBAN rows, `memory/` and commit messages stay fully detailed" sentence (template) and the matching `CLAUDE.md` sentence are unchanged and still govern it. No new rule text tells an agent to simplify a Kanban row, Evidence cell, memory entry or commit. | Scope: audit trail stays technical |
| 4 | The new rule does not conflict with the verbatim rule: nothing in it permits paraphrasing code, errors, paths, commands or security warnings. | "keep code, errors, paths and commands verbatim" |
| 5 | `tests/test_response_standard.py` count pins move 7 → the new total, and a new test asserts the plain-language rule is present in both files by a probe string read from the template (anti-vacuity, as the existing tests do). | Hard-Stop Gate 5 |
| 6 | Net instruction growth ≤ 4 lines across `CLAUDE.md` + template; `CLAUDE.md` does not exceed 202 lines. | T100 AC6 — instruction bloat measurably hurts |
| 7 | Full suite green: `python3 -m pytest tests/ .claude/hooks/tests/ -q`. Any `test_agent_guide_dedup.py` baseline repoint touches **only** the roles actually breached, with a comment naming T133 (T082 P1a: never blanket-repoint). | No regression |

---

## Evaluation & Acceptance

### Success Criteria (observable, pass/fail)

| # | Given | Expect | How it's checked |
|---|-------|--------|------------------|
| 1 | Branch tree | 7 old rules unchanged, ≤2 new, identical in both files | automated test (AC1/2/5) |
| 2 | **M1** — delete the new line from `CLAUDE.md` only | the byte-identity test goes RED | mutation control (Supervisor re-runs) |
| 3 | **M2** — delete the new line from both files | the new presence test goes RED (not just the count) | mutation control |
| 4 | **M3** — reword the new line so it says "simplify Kanban rows too" | reviewer catches AC3 breach at Stage 4 (text, not test — recorded as a review check, not faked as automated) | Stage 4 code-review |
| 5 | Supervisor live session, `main` vs branch, same prompt that forces a **decision question** (e.g. "plan a fix for T121 and ask me what you need") | branch: the question and its options are answerable without project history, and the decision itself is bolded; `main`: bare IDs/shorthand in the question | **user-run `/verify`** (Stage 5) — the Supervisor session is the only surface where this rule differs (T103 lesson) |
| 6 | Same A/B, a status question ("what's the project state?") | branch reply glosses or drops internal terms and bolds the single takeaway | user-run `/verify` |

### Verification Command

```bash
python3 -m pytest tests/test_response_standard.py -q && python3 -m pytest tests/ .claude/hooks/tests/ -q
```

### Evidence

> Filled by the reviewer at Stage 4/5 in `tasks/TASK_REVIEW_T133.md`.

---

## Demonstration

> See `tasks/TASK_REVIEW_T133.md`. Stage 5 must show a BEFORE/AFTER pair of real Supervisor replies
> to the same question, not a text read of the rule.

---

## Approach

**Pattern reference**: T127 (`tasks/TASK_GUIDE_T127.md`) — added the seventh rule to both files and
updated the same two test files; imitate exactly how it moved the count pins and repointed only the
breached role baseline.

**Vital slice**: one plain-language rule line, in both channels, pinned by a test.

**Cut list**:
- HTML reports / `wake` briefing wording (user scoped them out)
- A glossary the agent must look terms up in (more instruction text; the gloss goes inline instead)
- Per-audience modes or a "technical mode" toggle — "on request" is just the user asking
- Any automated readability/jargon checker

Guidance direction (the implementer drafts the exact wording; the Supervisor signs it off before
tests are written against it). Aim for one line, e.g.:

> - Write for a reader who hasn't followed the project, above all when asking them to decide: plain words, a task ID or internal term gets a few words saying what it is, the one thing to read or act on in bold, technical depth only when asked.

T100's Stage 5 found rules with a self-granting escape clause ("where helpful", "if needed") did not
bind — **avoid them**.

---

## Edge Case Checklist

- [ ] The rule must not push the Supervisor to drop task IDs entirely — the user still needs them to find rows; the rule is *gloss*, not *remove*.
- [ ] "Plain" must not become "longer": a gloss is a few words, not a paragraph (T100: guidance reshapes, it doesn't compress — don't make it worse).
- [ ] Highlight means **one** focus point per reply (or per question). Bolding every other phrase highlights nothing — the rule must say "the one thing", not "key points".
- [ ] Sub-agent `## Output Format` fenced blocks stay out of scope (template already says the standard governs only the prose around them).
- [ ] `_rule_lines()` stops at the next heading — a new line placed after the list, or as a sub-bullet, would be silently uncounted.

---

## Files to Change (Predicted)

| File | Change |
|------|--------|
| `CLAUDE.md` | add ≤2 bullet lines under `### Response Standard` |
| `agents/general-agent-template.md` | same line(s), byte-identical, under `## Response Standard` |
| `tests/test_response_standard.py` | count pins 7 → N; new presence test; docstring notes T133 |
| `.claude/hooks/tests/test_agent_guide_dedup.py` | only if a role's char baseline is breached — repoint that role alone, commented |

## Files Must NOT Touch

| File | Reason |
|------|--------|
| `agents/backend.md`, `frontend.md`, `qa.md`, `common-infrastructure.md` | the standard is shared; role guides point, never copy (existing test) |
| `docs/claude-md/token-economy.md` | verbatim list unchanged |
| `.claude/skills/wake/SKILL.md`, `html-report`, `delivery-report` | scoped out by the user |
| `PROJECT_KANBAN.md`, `memory/` | Supervisor-only writes |

---

## Test Plan

Write the new presence test and the count move first, watch them fail, then add the rule line(s).
Run M1 and M2 and paste the RED output into the review file. Stage 5 is the user-run `/verify` A/B
on the Supervisor's own replies (Success Criterion 5).

---

## Completion Checklist

- [ ] Implementation done
- [ ] Self-review: `Skill({ skill: "code-review" })` run
- [ ] Security review: N/A (Low risk)
- [ ] Tests written AND pass — output pasted into `tasks/TASK_REVIEW_T133.md` (Hard-Stop Gate 5)
- [ ] `/verify` run by the user — Supervisor A/B on a real status question
- [ ] Supervisor notified: task ready for Stage 4 review

---

## Round 2 — tighten the rule (user, 2026-09-26, after Stage 5)

Stage 5 passed, but the A/B showed two gaps, and the user asked for them to be closed before merge:
- **Too much bold.** The branch reply bolded list labels (`Done:`, `T117:`) as well as its main point, so nothing stood out.
- **Long sentences and meaning.** The user asked how a reworded long sentence keeps its meaning. The rule said nothing about it.

User's direction: one focus per reply; split long sentences, never cut them; don't pile up things to focus on.

**Round 2 ACs** (AC1–AC7 above still hold; AC1's "at most two lines" budget now uses both):

| # | Criterion | Traces to |
|---|-----------|-----------|
| R1 | The eighth rule line becomes exactly: `- Write for a reader who hasn't followed the project, above all when asking them to decide: plain words; a task ID or internal term gets a few words saying what it is; technical depth only when asked.` | user: plain words, questions first |
| R2 | A ninth line is added, exactly: `- One focus per reply: bold only the one thing to decide or do (else a one-line summary), never labels; show at most three items and offer the rest; split a long sentence rather than cut it, keeping every number and "not/only/unless".` | user: one focus, split not cut, too much highlighting |
| R3 | Both lines are byte-identical in `CLAUDE.md` and `agents/general-agent-template.md`; count pins 8 → 9; the presence test probes both lines. | T103 two channels |
| R4 | `CLAUDE.md` ≤ 202 lines (AC6). Baseline repoints only where a test actually breaks, each commented T133 round 2. | AC6/AC7 |
| R5 | Mutation controls re-run: delete the ninth line from `CLAUDE.md` only → RED; from both → RED. Output pasted into `TASK_REVIEW_T133.md` under a `Round 2` note. | Gate 5 |

**Round 2 Stage 5** (Supervisor, re-run on the user's authority): the same two prompts, old vs new. Count the bold items in each reply (target 1) and the listed items (target ≤3), and compare the replies fact by fact: any fact lost or changed = FAIL.
