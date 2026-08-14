# TASK_REVIEW — T070: [Short Title]

> Sibling of `tasks/TASK_GUIDE_T070.md`. Everything here is **filled by the reviewer at Stage
> 4/5** — it is deliberately NOT in the guide, because the implementing agent re-reads the guide on
> every turn and never fills these two sections.
>
> Consumers resolve each section **guide first, this file second** (`.claude/hooks/lib/guide_sections.py`):
> a legacy guide that still carries these sections inline keeps working unchanged, and a stray
> review file can never override an inline section.

---

## Evidence

| Check | Result | Notes / output snippet |
|-------|--------|------------------------|
| **New test(s) cover Acceptance Criteria (file paths pasted)** | ☐ pass / ☐ fail | [test file path(s) — required before Done] |
| Verification command run | ☐ pass / ☐ fail | [paste actual output] |
| Negative cases hold | ☐ pass / ☐ fail | |
| verify | ☐ pass / ☐ fail / ☐ N/A | [what was observed — must literally state "pass" or "fail" here too, e.g. "skill run, feature confirmed working — pass": the merge gate scans this Notes column for the word "pass", not just the Result column] |
| Review scope bounded to the change's blast radius (affected set, not whole repo) | ☐ pass / ☐ fail | [what was reviewed vs. skipped, and why] |
| Full smoke suite still green (no regression) | ☐ pass / ☐ fail | |
| **UI: Visual regression (diff or verdict pasted)** | ☐ pass / ☐ fail / ☐ N/A | [screenshot path or LLM verdict — required for UI tasks, Hard-Stop Gate 6] |
| **UI: Design-system compliance (tokens/colors/typography verified)** | ☐ pass / ☐ fail / ☐ N/A | [method used + output] |
| **UI: Responsiveness at target viewports** | ☐ pass / ☐ fail / ☐ N/A | [viewports tested, any overflow findings] |

---

## Demonstration

> Anchors what this task delivered to an observable before/after pair. BEFORE has no `N/A` path:
> if the task changes executable code, BEFORE is a pasted, timestamped terminal capture taken
> **before any implementation commit exists**; if it does not (docs, templates, skill-instruction
> text), BEFORE is the **verbatim prior content** of what changed — a quoted excerpt, not a command.

**BEFORE**: T070 changes no executable code — it edits prose in three markdown files — so BEFORE is
the verbatim prior content of each line about to change, quoted from the tree at `2baecb9` (captured
2026-08-14, before any implementation commit exists on `feat/t070-impl`).

`CLAUDE.md:86`
```
- Scale process to the task's **Complexity Level (C0–C3)** — see the Complexity matrix in `.claude/agents/general-agent-template.md`. **Risk Level** separately gates `security-review`.
```

`docs/claude-md/pipeline-stages.md:118`
```
5. Assign each task three independent labels: **Complexity (C0–C3)**, **Risk (Low/Med/High)**, and **Priority (P0–P2)**. Split any task larger than C3 (an **Epic**) into smaller tasks before generating guides. (Complexity drives agent process; Risk gates `security-review`; Priority sets ordering — see the matrix in `.claude/agents/general-agent-template.md`.) When setting **Risk**, factor in whether the task touches a **hub file** — one many others depend on, so its code-dependency blast radius is large. In legacy mode this is recorded in `docs/legacy/risk-hotspots.md`; in greenfield it's a judgment call (optionally informed by a structural code-graph approach — see Stage 1). A hub touch raises Risk a level even when the edit itself is small.
```

`templates/TASK_GUIDE_template.md:18`
```
5. Note the **Complexity Level** above and apply the matching process (brainstorm / decompose / verify depth / model) from the Complexity matrix in `.claude/agents/general-agent-template.md`
```

**AFTER**: [same three lines, post-change — filled by the reviewer at Stage 4/5]

**DELTA**: [one sentence — what a user can now do that they could not before]

**WITNESS**: [who ran it and when — derived from `memory/event-trace/T070.jsonl`, never the
implementing agent alone]
