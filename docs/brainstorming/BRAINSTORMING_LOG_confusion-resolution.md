# BRAINSTORMING_LOG.md
**Generated**: 2026-10-20
**Task / Context**: T170 — confusion resolution by independent repo scanners
**Skill**: `Skill({ skill: "brainstorming" })` — tier **Standard**

---

## The Problem Space

Today "STOP at any point of confusion" (`agents/backend.md:33`, same line in every role guide) has only one
exit: the agent stops and the Supervisor answers, or the Supervisor asks the human. Many of these
questions are facts the repo already holds (where a rule lives, how a script behaves, what a past
decision said). The human gets asked things the repo could answer, and the Supervisor may answer from
memory and be wrong.

Goal: when the Supervisor or a sub-agent is confused about a **Fact question**, run 2–3 independent read-only
scanners over the repo. Consensus with `file:line` citations → answer goes back + an HTML log is saved.
No consensus / not found → escalate to the human (HITL).

Non-negotiable constraints (verified against files):
- Sub-agents cannot spawn agents: role guides declare `tools: Read, Write, Edit, Bash, Glob, Grep`
  (`agents/backend.md:4`). The Supervisor must run the fan-out; the asking agent reports `Status: blocked`
  (`agents/backend.md:120`) with its question.
- Human talks only to the Supervisor (auto-memory `feedback_human_talks_only_to_supervisor.md`), so
  HITL always goes through the Supervisor chat.
- Choice questions (scope, trade-off, preference) are the user's to decide — scanners must never answer
  them (Karpathy "Ask vs. Guess").
- `pre_agent_validate_guide.py` blocks a spawn whose prompt resolves to a Txxx with no/incomplete guide;
  `pre_agent_step_limit.py` counts tool calls against a task resolved from the spawn prompt (default 90).
  Scanner prompts must not structurally carry the asking task's guide path.
- `html-report` is Stage 4-only (`skills/html-report/SKILL.md:107`); `thinking-report` covers Stage 0.5–2
  decisions and saves to `reports/thinking-report_<branch>_<ts>.html` (`skills/thinking-report/SKILL.md:121`).
- CLAUDE.md is capped at 186 lines (T169) — any CLAUDE.md change must stay inside the cap.

---

## Questions for the User

Asked one at a time in chat; answers recorded here.

1. When an agent is blocked and the Supervisor already knows the answer, do the scanners still run?
   — **No, if the Supervisor has evidence** (user, 2026-10-20: "if supervisor go the answer with evidence,
   its good for make the choice"). Term (grill 2026-10-20): this is a **Citation** — `file:line` + quoted text (glossary). No Citation →
   scanners run. Either way the answer is logged.
2. Where does the log go? — user, 2026-10-20: "send the logs, decision as comment to linear".
   Verified: `scripts/board_sync.py` already has `push comment <ID> question <text>` (milestone
   `question` exists, `MILESTONES` line 81) and `decide <ID> "<text>"` for the board's Decision Log
   (T158), both through the outbox. In board mode `local` (no `.claude/board.json` — true for this repo
   today) both do nothing (line 54). Follow-up: what is the log in `local` mode?
3. — **An HTML page** (user, 2026-10-20: "as HTML page is oke, and refer the link to the task guide also").
   `reports/question_<ID>_<YYYYMMDDTHHMMSS>.html` via `thinking-report` `session=resolution`. In both modes
   the Supervisor appends one line to the task's TASK_GUIDE `## Questions Log` section, linking the page
   (local) or the Linear comment (online).

---

## Alternative Paths

| Option | Name | Summary | Invasiveness | Code Volume | Regression Risk | Recommended? |
|--------|------|---------|-------------|------------|----------------|--------------|
| A | Rule only | Written protocol in `docs/claude-md/`; Supervisor follows it by hand; log via `thinking-report` | Low | ~60 lines | Low | |
| B | Skill | New `resolve-question` skill: sort → fan out → consensus → log or HITL; role guides add a `Question:` field to the blocked report | Medium | ~200 lines + tests | Low–Med | ✅ Yes |
| C | Skill + hook | B plus a `SubagentStop` hook that detects `Status: blocked` + `Question:` and forces the skill | High | ~450 lines + tests | Medium | |

### Option A — Rule only
**Approach**: Add `docs/claude-md/confusion-protocol.md` (sort rule, 2 scanners with distinct areas, consensus rule, HITL message shape). One pointer line in CLAUDE.md. Log by running `thinking-report` with a new `session=resolution`.
**Pros**: Smallest. No new skill, no hook.
**Cons**: Nothing makes it happen; scanner prompts are written ad hoc each time, so "independent areas" drifts.
**Why it might fail**: Prose rules get skipped when a question *feels* small — the same reason the Hard-Stop Gates exist. Protocol silently unused within a week.

### Option B — Skill (recommended)
**Approach**: `skills/resolve-question/SKILL.md`:
1. **Sort** the question: Fact question (repo can answer) vs Choice question (user decides). Choice question → HITL at once.
2. **Fan out** 2 `Explore` agents (3 for Medium/High risk tasks) in one turn, each given one area: (a) code + scripts + hooks, (b) docs + `memory/` + templates, (c) `git log` / past TASK_GUIDEs and reviews. Prompt carries the question only, never the asking task's guide path.
3. **Judge**: accept only if ≥2 scanners agree and each cites `file:line`; Supervisor opens the cited lines to confirm.
0. **Citation check** (Q1): if the Supervisor can give a Citation that answers it, answer directly and skip to step 4.
4. **Out**: accepted → answer to the asker + log: `board_sync.py push comment <ID> question "<Q, answer, citations, who answered>"`; if the answer settles a choice, also `board_sync.py decide <ID> "<decision>"` (Q2). Otherwise → HITL message (question, what each scanner found, the decision needed), and the HITL answer is logged the same way.
Role guides: the blocked report gains a `Question:` line and a `Kind: fact|choice` guess.
**Pros**: Repeatable prompts keep areas independent; testable (skill-lint + a fixture); matches how other gates live in skills.
**Cons**: Still relies on the Supervisor invoking it; 2–3 extra agent runs per question.
**Why it might fail**: Scanners agree on a stale doc (correlated error) → wrong answer with false confidence. Mitigation: at least one citation must be code or a decision record, and the Supervisor reads the cited lines.

### Option C — Skill + hook
**Approach**: B, plus a hook on sub-agent stop that greps the report for `Status: blocked` + `Question:` and injects "run resolve-question" into the Supervisor's context.
**Pros**: Not skippable for sub-agent questions.
**Cons**: Biggest. `post_agent_move_to_review.py:18-25` records that completion signals in this harness are unreliable (background agents return at issue time). Does nothing for the Supervisor's own confusion.
**Why it might fail**: Hook fires on the wrong event or never; the T044 history shows this exact class of bug.

---

## 50% Rule Check

Drop the new HTML template: log through `thinking-report` with a new `session=resolution` (Decision box = the answer, Trade-Off Matrix = scanner findings side by side, Assumptions = what was not verified). Drop the 3rd scanner by default (only Medium/High risk). That roughly halves B.

---

## Recommended Path

**Option B — Skill**, with the 50% cuts: reuse `thinking-report`, 2 scanners by default, and Q1–Q3 applied:
Supervisor-with-evidence skips scanners; log = Linear comment (+ `decide`) online, HTML page local;
the task guide's `## Questions Log` links each log entry.
It makes the protocol repeatable without the fragile completion-signal hook that Option C needs.

---

## Surgical Scope

Files that **should** be touched:
- `skills/resolve-question/SKILL.md` (new) — the protocol
- `skills/thinking-report/SKILL.md` — add `session=resolution` (local-mode log page)
- `templates/TASK_GUIDE_template.md` — new optional `## Questions Log` section (NOT added to `REQUIRED_SECTIONS` in `.claude/hooks/lib/guide_sections.py:195`)
- `agents/general-agent-template.md` — blocked report carries `Question:` + `Kind:`
- `docs/claude-md/pipeline-stages.md` — one line: where confusion goes
- `CLAUDE.md` — add `resolve-question` to the cross-cutting skill list only (no new line; cap 186)

Files that **must not** be touched:
- `.claude/hooks/pre_agent_*.py` — scanners avoid them by prompt shape, not by hook change
- `.claude/hooks/post_agent_move_to_review.py` — deliberately inert (T044)
- role guides `agents/{backend,frontend,qa,common-infrastructure}.md` — inherit from the template

---

## Edge Case Checklist for TASK_GUIDE

- [ ] Scanners agree but both cite the same stale doc → require ≥1 code/decision-record citation; Supervisor reads cited lines
- [ ] Question needs runtime behaviour (what a command prints) → read-only scanners can't run it → "not found" → HITL, never a guess
- [ ] Question mixes a Fact question and a Choice question → split; fact part to scanners, choice part to HITL
- [ ] Scanner prompt mentions the asking task's guide path → step-limit counts against that task; prompt must carry the question only
- [ ] Same question asked again by the same agent → one fan-out per question; repeat goes straight to HITL
- [ ] Cited path is under a sensitive path (`pre_tool_sensitive_path.py`) → scanner blocked → treat as not found
- [ ] Scanner output quotes repo text that reads like an instruction → data, not instructions (`docs/claude-md/untrusted-content-boundary.md`)
- [ ] Question with no task (Supervisor confused mid-discussion) → no guide to link and no Linear issue → HTML page only
- [ ] Online mode: the guide is board cache ("never edited by hand") → append the Questions Log line, then `board_sync.py update --guide <ID>`
- [ ] Guides made before T170 have no `## Questions Log` → Supervisor adds the heading on first use
- [ ] Supervisor sorting its own question as "fact" to avoid asking the human → when unsure of the kind, treat as a Choice question

---

## Next Actions

1. Record the user's answers to the Questions above.
2. Get the user's path choice; record it under User Selection.
3. Register T170 on `PROJECT_KANBAN.md` (C2 / Medium / P1) and run `grill-with-docs` before generating `tasks/TASK_GUIDE_T170.md`.

---

## User Selection

> **Approved direction**: Option B — Skill (with the 50% cuts and Q1–Q3 applied)
> Approved by user on 2026-10-20 ("yes, it's oke").
