# TASK_GUIDE — T169: Writing Principles (ASD-STE100) become a named rule set next to Karpathy, for text a human reads only
**Date**: 2026-10-20
**Complexity Level**: C2
**Risk Level**: Medium
**Priority**: P1
**Assigned agent**: common-infrastructure
**Agent guide**: `agents/common-infrastructure.md`

> Medium (raised 2026-10-20 from C1/Low): the scope now restructures `CLAUDE.md`, and Hard-Stop Gate 2 sets a C2/Medium floor for restructuring. Still docs and tests only; no hook, script or installer behavior changes.

---

## Mandatory Startup (Do Not Skip)

Before writing any code:
1. Read `PROJECT_SPEC.md`
2. Read the memory slice in your spawn prompt (`<!-- memory-slice -->`). Read `memory/MEMORY.md` in full only if your work reaches a file, hook, skill or decision the slice does not cover
3. Read this file completely, then `BRAINSTORMING_LOG_plain-output.md`
4. Read `agents/common-infrastructure.md`
5. Note the **Complexity Level** above and apply the matching process from the Complexity matrix in `agents/common-infrastructure.md`

---

## Requirement (Pillar 1 — Adapt the requirement)

Source: the user, 2026-10-20: "just met the problem that, the agent output is technically". The user cited a Medium post on Karpathy's suggestion to write AI output in the ASD-STE100 style. Then: "let refer to the rules (ASD-STE100) as 4 principal of karpathy the we followed, The output should comes after using, not the way I can decide for now". The user approved Option A of `BRAINSTORMING_LOG_plain-output.md` with "go with A".

**Restated intent** (Supervisor's interpretation, in the project's domain language):
> `CLAUDE.md` gets a "Writing Principles (ASD-STE100)" section with a 4-row table: One Term, One Meaning · Short Sentences · One Action, Active Voice · No Noun Stacks. It sits next to the Karpathy Engineering Principles and has the same weight. The rules apply **only to text a human reads**: the Supervisor's chat replies to the user, and HTML reports. Agent-to-agent text needs precision, not easy reading, so it is exempt: spawn prompts, TASK_GUIDEs, sub-agent reports, Kanban rows and commits. A technical term is never replaced by a paraphrase. Keep the key term exactly. Gloss it once, only if the reader may not know it. The rules never rewrite the verbatim list (code, exact error text, file paths, commands, security warnings).

**Grilling decisions (2026-10-20, `grill-with-docs`)**:
- D1 — Keep the key term; gloss it once, never replace it. User: "must keep the key, not the whole". Source of the risk: STE allows technical names and verbs; the first draft did not say so, and forced paraphrase changed meaning ("git worktree" → "a separate copy of the repo").
- D2 — Human-facing output only. User: "should be used with the human eye, not from agent to agent, subagent. Cause the agent need the right, not the easy reading". Effect: no copy in the role guides, so spawns cost nothing extra.
- D3 — A glossary term in `PROJECT_SPEC.md` counts as one noun for the No Noun Stacks rule.
- D4 — When splitting a sentence, keep the link word (because, so, unless, only if).
- D5 — Measure token cost with `scripts/token_meter.py` before and after, never by eye (`docs/claude-md/token-economy.md`).

**Out of scope** (what this task explicitly does NOT do):
- A checker script (`ste_check.py`, Option B). It is on the cut list until the trial ends
- "Show, don't tell" (diagrams or HTML instead of text)
- The STE approved-word dictionary
- Rewriting existing Kanban rows, TASK_GUIDEs, commits or memory files

**Requirement Refs**: `BRAINSTORMING_LOG_plain-output.md` § Proposed principle set, § Option A, § Edge Case Checklist

### Requirement Fidelity Gate (sign off BEFORE implementation)

- [x] Restated intent confirmed to match the user's request (Supervisor, 2026-10-20; user approved Option A: "go with A")
- [x] Domain terms align with `PROJECT_SPEC.md` glossary
- [x] Every Acceptance Criterion below traces to a line in the Requirement
- [x] All Requirement Refs exist and are covered by the Acceptance Criteria

---

## Dependencies & Reachability

**Depends on**: none

**Entry point**: `CLAUDE.md` is auto-injected into the Supervisor's session. The role guides are auto-loaded as sub-agent system prompts. `AGENTS.md` and `.cursor/rules/agent-base.mdc` are the adapters for other CLIs.

---

## Acceptance Criteria

| # | Criterion (testable) | Traces to requirement |
|---|---|---|
| 1 | `CLAUDE.md` has a `## Writing Principles (ASD-STE100)` section. Its table has exactly 4 principle rows with the names One Term, One Meaning · Short Sentences · One Action, Active Voice · No Noun Stacks. Each row has a Problem Addressed column and an Operational Command column. The commands state the limits 20 words (steps), 25 words (descriptions) and 3 nouns in a row | Restated intent |
| 2 | The section states the scope in words: human-facing output only (Supervisor chat replies, HTML reports), and names the exempt agent-to-agent text (spawn prompts, TASK_GUIDEs, sub-agent reports, Kanban rows, commits) | D2 |
| 3 | The section states that the verbatim list is quoted unchanged | Restated intent |
| 4 | Rule 1 states: keep the key term exactly, gloss it once only if the reader may not know it, never replace it with a paraphrase | D1 |
| 5 | Rule 4 states that a `PROJECT_SPEC.md` glossary term counts as one noun; rule 2 states that a split keeps its link word (because, so, unless, only if) | D3, D4 |
| 6 | No role guide (`agents/*.md`) and no spawn template carries the table | D2 |
| 7 | `AGENTS.md` and `.cursor/rules/agent-base.mdc` list the 4 principle names, because another CLI can act as Supervisor | Restated intent |
| 8 | The new prose follows its own rules: no sentence over 25 words, outside the tables | Dogfooding |
| 9 | `TASK_REVIEW_T169.md` records `python3 scripts/token_meter.py --current --json` output for one session before and one after the change | D5 |
| 10 | The Response Standard "Write for a reader…" bullet points to the new section, and stays byte-identical between `CLAUDE.md` and `agents/general-agent-template.md` | Restated intent; existing `tests/test_response_standard.py` |

---

## Evaluation & Acceptance (How we know the agent worked correctly)

### Success Criteria (observable, pass/fail)

| # | Given (input/state) | Expect (output/behavior) | How it's checked |
|---|---|---|---|
| 1 | `CLAUDE.md` | section and 4 names present, limits stated | new `tests/test_writing_principles.py` |
| 2 | `CLAUDE.md` section | scope, exempt list, verbatim exemption, keep-the-term, glossary-term and link-word lines present | same |
| 3 | `agents/*.md` | no `Writing Principles` table | same |
| 4 | 2 adapters | 4 names present after whitespace normalization | same, or extend `tests/test_provider_adapters.py` the way the Karpathy names are checked |
| 5 | Response Standard | still byte-identical in both files | existing `tests/test_response_standard.py` |
| 6 | Karpathy table parser | still finds exactly 4 Karpathy names | existing `tests/test_provider_adapters.py` |

### Verification Command (exact, runnable)

```bash
python3 -m pytest -q tests/test_writing_principles.py tests/test_provider_adapters.py tests/test_response_standard.py
```

### Evidence (filled by reviewer at Stage 4/5)

> **Moved.** Filled by the reviewer at Stage 4/5 in `tasks/TASK_REVIEW_T169.md`.

---

## Demonstration

> **Moved.** See `tasks/TASK_REVIEW_T169.md`. BEFORE command: `grep -n "Writing Principles" CLAUDE.md agents/*.md AGENTS.md .cursor/rules/agent-base.mdc` (expect no match). AFTER: the same command shows every file.

---

## Approach

**Pattern reference**: the `## Karpathy Engineering Principles` table in `CLAUDE.md`, its `(Compact)` copy in each role guide, and the `(names — see CLAUDE.md …)` list in `AGENTS.md`.

**Vital slice**: the `CLAUDE.md` table with its two exemptions, plus the mirrors and the test.
**Cut list**:
- Checker script, "show, don't tell", word dictionary (see Out of scope)

Draft table (from the brainstorming log, so you may reword it to fit the rules):

| Principle | Problem Addressed | Operational Command |
|---|---|---|
| One Term, One Meaning | One thing gets three names; a forced paraphrase changes the meaning | Give each thing one name and keep it. Keep the key technical term exactly; never replace it with a paraphrase. Gloss it once, in brackets, only if the reader may not know it. |
| Short Sentences | Long sentences hide the point | Steps: 20 words or fewer. Descriptions: 25 words or fewer. Split a long sentence, but keep its link word (because, so, unless, only if). Never drop a number or a "not". |
| One Action, Active Voice | Several actions in one sentence; it is not clear who does what | Write one action per sentence. Write steps as commands. Name who acts: "The hook blocks the push", not "the push is gated". |
| No Noun Stacks | "pre-push assignee filter predicate" | Put no more than 3 nouns in a row. A `PROJECT_SPEC.md` glossary term counts as one noun. Break longer chains with verbs, or with "of / for / that". |

Scope line to place under the table: "These rules apply only to text a human reads: the Supervisor's chat replies and HTML reports. Agent-to-agent text needs precision, not easy reading: spawn prompts, TASK_GUIDEs, sub-agent reports, Kanban rows and commits are exempt."

Place the new section directly after the Karpathy section and before `## Code Naming Conventions`. Leave a blank line between the Karpathy table and the following text unchanged: the Karpathy parser in `tests/test_provider_adapters.py` reads up to the first blank line after the heading.

---

## Edge Case Checklist

- [ ] A quoted error, path or command over 20 words is exempt (the verbatim list wins)
- [ ] Records: a rewrite into STE keeps every fact, number and negation
- [ ] The mirrors stay in sync with `CLAUDE.md` (the test reads the names from both files, never hardcoded)
- [ ] `_claude_md_principle_names()` still returns exactly the 4 Karpathy names. A new table must not fall inside its regex window
- [ ] `tests/test_response_standard.py` still passes: change the bullet in both files at the same time
- [ ] Any CLAUDE.md size, line-cap or docs-match test (`tests/test_docs_match_installer.py`, `tests/test_update_claude_md.sh`) still passes

---

## Files to Change (Predicted)

| File | Change |
|---|---|
| `CLAUDE.md` | new section; Response Standard bullet points to it |
| `agents/general-agent-template.md` | same bullet change only (byte-identical rule); no table |
| `AGENTS.md`, `.cursor/rules/agent-base.mdc` | names list |
| `tests/test_writing_principles.py` | new |


## Scope Extension — CLAUDE.md ≤ 200 lines (added 2026-10-20)

Source: the user, 2026-10-20: "let check the CLAUDE.md and start reduce the file to no more 200 lines", then "do in this tasks also" (fold it into T169, not a new task). The user approved the Supervisor's cut list:

| Section | Now | Target | Rule kept |
|---|---|---|---|
| `## General Agent Template` | 21 lines | ~7 | Pointer to `agents/general-agent-template.md`; keep the untrusted-content line (pinned by `tests/test_provider_adapters.py`) and the Complexity/Risk line (check `.claude/hooks/tests/test_complexity_matrix_pointers.py`) |
| `## Mandatory Session Startup` | 14 lines | ~5 | Must invoke `Skill({ skill: "wake" })` before the first substantive reply; not optional; even if the user jumps straight to a task |
| Opening "Your job is to act…" list | 6 bullets | 1 line | — (restates the pipeline section) |
| `## Final Instruction` | 3 lines | 0 | The Phase 0 section already carries the "Start new project supervision" trigger |

No other section is cut. The Karpathy and Writing Principles tables, Hard-Stop Gates, Response Standard, pipeline stages and Memory Write Protocol stay as they are.

| # | Criterion (testable) | Traces to |
|---|---|---|
| 11 | `CLAUDE.md` is ≤ 200 lines | user request |
| 12 | `LINE_CAPS["CLAUDE.md"]` in `.claude/hooks/tests/test_vital_slice.py` is lowered to the new line count (≤ 200), so the file cannot grow back | user request; cap is a ratchet |
| 13 | Each "Rule kept" item above is still stated in `CLAUDE.md`; a test asserts the `wake` mandate and the agent-template pointer | cut list |
| 14 | `CLAUDE_LEGACY.md` follows its sync policy (memory: mirror session-startup gates + Hard-Stop Gates) — keep it consistent with any startup-section wording change, or record why no change is needed | memory decision "CLAUDE_LEGACY.md sync policy" |
| 15 | Full suite green; any pin that moves (dedup baselines, byte-identical checks) is repointed with a comment naming T169 and this extension, assertion bodies untouched | regression |

BEFORE for this extension: the current text of the four sections, quoted into `tasks/TASK_REVIEW_T169.md` before the first commit that cuts them.

## Files Must NOT Touch

| File | Reason |
|---|---|
| `PROJECT_KANBAN.md`, `memory/` | Supervisor-only |
| `BRAINSTORMING_LOG_plain-output.md` | locked planning input |
| `docs/claude-md/token-economy.md` | verbatim list is unchanged by design |
| `docs/adr/`, `docs/ddr/` | parked until the docs MCP lands (user decision) |

---

## Test Plan

TDD (`Skill({ skill: "tdd" })`): write `tests/test_writing_principles.py` first and confirm that it fails (red). Then edit the docs. Then run the Verification Command and the full suite `python3 -m pytest -q tests .claude/hooks/tests` and read its real exit code. Also run the shell suites that read `CLAUDE.md` (`bash tests/test_update_claude_md.sh`).

---

## Completion Checklist

- [ ] Implementation done
- [ ] Self-review: `Skill({ skill: "code-review" })` run
- [ ] Security review: N/A (Low risk)
- [ ] Tests written AND pass — output pasted into `tasks/TASK_REVIEW_T169.md`'s Evidence table (Hard-Stop Gate 5)
- [ ] `Skill({ skill: "verify" })` run (user-only)
- [ ] Supervisor notified: task ready for Stage 4 review
