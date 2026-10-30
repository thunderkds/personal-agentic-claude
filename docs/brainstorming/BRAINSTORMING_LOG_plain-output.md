# BRAINSTORMING_LOG.md
**Generated**: 2026-10-20
**Task / Context**: Agent output reads too technical — adopt ASD-STE100 writing rules (source: a Medium post on Karpathy's suggestion)
**Skill**: `Skill({ skill: "brainstorming" })` — tier: Standard

---

## The Problem Space

The user finds agent output too technical. The worst case is chat replies, from the Supervisor and from sub-agent reports. Records (Kanban rows, TASK_GUIDE, commits) and HTML reports are sometimes too technical as well.

The user's direction (2026-10-20): adopt the ASD-STE100 rules as a named principle set, the same way the Karpathy Engineering Principles are adopted. The right output style must come from using the rules over time. The user does not want to choose a format now.

The current rules cover only part of this. `CLAUDE.md` § Response Standard has one bullet, "Write for a reader who hasn't followed the project… plain words", but it sets no checkable limit. The typical defect is a noun stack plus internal jargon, for example: "pre-push hook now filters In Progress rows by assignee before gating; mutant on the filter predicate killed".

Non-negotiables:
- Records stay fully detailed (the audit trail, `CLAUDE.md` § Supervisor Communication Style). In records, STE changes how a sentence is written. It never removes a fact.
- The verbatim list in `docs/claude-md/token-economy.md` is unchanged. Code, exact error text, paths, commands and security warnings are quoted as they are, never rewritten into STE.

Source caveat: the post is one author's experience over about a week, with no measurements. ASD-STE100 itself is a real aerospace standard: about 50 writing rules and a dictionary of approved words.

---

## Proposed principle set (shared by all options)

**Writing Principles (ASD-STE100)**: mandatory for every output a human reads.

| Principle | Problem Addressed | Operational Command |
|---|---|---|
| One Term, One Meaning | One thing gets three names; internal terms are not explained | Give each thing one name and keep it. The first time a task ID or internal term appears, add a few plain words that say what it is. |
| Short Sentences | Long sentences hide the point | Steps: 20 words or fewer. Descriptions: 25 words or fewer. Split a long sentence. Never drop a number or a "not / only / unless" to make it shorter. |
| One Action, Active Voice | Several actions in one sentence; it is not clear who does what | Write one action per sentence. Write steps as commands. Name who acts: "The hook blocks the push", not "the push is gated". |
| No Noun Stacks | "pre-push assignee filter predicate" | Put no more than 3 nouns in a row. Break longer chains with verbs, or with "of / for / that". |

---

## Questions for the User

1. Approve Option A (below) as the direction, so that Stage 2 can create the task?

---

## Alternative Paths

| Option | Name | Summary | Invasiveness | Code Volume | Regression Risk | Recommended? |
|--------|------|---------|-------------|------------|----------------|--------------|
| A | Principle table | Add the 4-row table to `CLAUDE.md` and mirror it in the same places as the Karpathy table | Low | ~40 lines of docs | Low | ✅ Yes |
| B | Table + checker | A, plus `scripts/ste_check.py` to check sentence length and noun stacks in sub-agent reports and Kanban rows at Stage 4 | Medium | ~40 docs + ~150 code + tests | Medium | |
| C | Extend Response Standard | Add 4 bullets to the Response Standard; no new table and no mirrors | Low | ~6 lines | Low | |

### Option A — Principle table
**Approach**: Add a "Writing Principles (ASD-STE100)" section after the Karpathy table. Mirror it in the same places as the Karpathy table: `agents/general-agent-template.md`, the four role guides, `AGENTS.md` and `.cursor/rules/agent-base.mdc`. Change the Response Standard "plain words" bullet so that it points to the new section.
**Pros**: The rules get the same weight as Karpathy, which is what the user asked for. Sub-agents receive them through their own guides. No code is needed.
**Cons**: Prose rules depend on the model following them. This is the same weakness LR-0002 records.
**Why it might fail**: The rules can slowly stop being followed in long sessions. Mitigation: check after a trial period ("the output should come after using").

### Option B — Table + checker
**Approach**: A, plus a script that flags sentences over 20 or 25 words and runs of 4 or more capitalized or technical tokens.
**Pros**: The check is measurable, and it addresses LR-0002.
**Cons**: A script cannot check chat replies before the user sees them, and chat replies are the main target. Noun-stack detection without an NLP library is a rough heuristic, so false positives are likely.
**Why it might fail**: It enforces the secondary target (records) and misses the primary target (chat).

### Option C — Extend Response Standard
**Approach**: Add the 4 rules as bullets under the existing Response Standard.
**Pros**: The smallest change.
**Cons**: The rules get lost in a list that already has 9 bullets. They do not reach the role guides, `AGENTS.md` or the Cursor rule. They do not have the "named principle set" status that the user asked for.
**Why it might fail**: Sub-agents never see the rules.

---

## 50% Rule Check

Option A with half the text: keep the 4-row table and skip the full mirrors. Each mirror holds a one-line pointer instead, like the role guides' compact Karpathy table. This is the recommended form.

---

## Recommended Path

**Option A — Principle table**, with compact pointers in the mirrors.

It matches the user's direction: a named set, used like Karpathy, judged after use. Option B is on the cut list and becomes a follow-up only if the trial shows that the rules drift.

**Cut list (not built now)**:
- `ste_check.py` checker (Option B)
- Karpathy's second point, "show, don't tell" (diagrams and interactive HTML instead of text). The `html-report`, `thinking-report` and `delivery-report` skills already cover part of it. Revisit after the trial.
- The ~900-word STE approved-word dictionary. It is too strict for software terms.

---

## Surgical Scope

Files that **should** be touched:
- `CLAUDE.md` — new section; change the Response Standard bullet
- `agents/general-agent-template.md`, `agents/{common-infrastructure,backend,frontend,qa}.md` — compact pointer
- `AGENTS.md`, `.cursor/rules/agent-base.mdc` — mirror of the non-negotiables

Files that **must not** be touched:
- `docs/claude-md/token-economy.md` verbatim list — unchanged by design
- Existing Kanban rows, TASK_GUIDEs and commits — no retroactive rewrite

---

## Edge Case Checklist for TASK_GUIDE

- [ ] A quoted error, path or command over 20 words is exempt (verbatim list wins)
- [ ] Records: a rewrite into STE must keep every fact, number and negation
- [ ] The mirrors stay in sync with `CLAUDE.md` (same drift risk as the Karpathy table)
- [ ] Any `CLAUDE.md` size or line cap test still passes after the new section

---

## Next Actions

1. On approval: Stage 2 creates the Kanban row and `tasks/TASK_GUIDE_Txxx.md` (C1, Low risk, docs only).
2. Trial for an agreed period. The user marks replies that are still too technical. Then decide on the cut-list items.

---

## User Selection

> **Approved direction**: Option A — Principle table
> Approved by user on 2026-10-20 ("go with A"). Task: T169.
