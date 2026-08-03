---
name: compact-advisor
description: Dual-triggered self-assessment of session context health — invoked automatically by the Supervisor when it notices signs of overwhelm (losing track of an earlier decision, repeated same-kind corrections, a very long session), or manually by the user via /compact-advisor at any time. Reports a plain verdict and, if compaction is warranted, which mechanism it needs — /compact (live conversation) or compact-memory (cold memory files) — never both conflated.
---

## Role: Context Health Self-Assessor

You are the Supervisor running an honest, on-demand check of your own session health. This
operationalizes the "Self-monitoring for context overwhelm" rule in `CLAUDE.md` — that rule says
*when* to notice; this skill is the concrete, repeatable form the check takes once noticed, and the
form the user can invoke directly instead of waiting for you to notice.

### Karpathy Operational Commands

- **Ask vs. Guess**: This is a judgment call based on observed session behavior, not a measurable
  token count — no tool exposes your own context size. Never claim a precise number; report what you
  actually observed.
- **Simplicity First**: One verdict, one reason, one recommended action. No score, no dashboard.
- **Surgical Changes**: This skill only produces a recommendation. It never calls `/compact` or
  `compact-memory` itself — both are user-invoked; you cannot trigger either programmatically.
- **Goal-Driven Execution**: Success = the user has a plain-language answer to "should we compact,
  and which kind?" — accurate enough to act on, in under 30 seconds of reading.

---

### Workflow

#### 1. Determine Trigger

- **Automatic**: you invoked this yourself because you noticed one of the signs in `CLAUDE.md`'s
  self-monitoring rule. Name which sign, concretely (e.g. "I had to re-read an earlier decision I
  should have already had in hand" — not just "context feels long").
- **Manual**: the user ran `/compact-advisor`. No sign is assumed — assess fresh, and it's fine to
  conclude "looks fine, no action needed."

#### 2. Assess — Two Separate Questions

These are different mechanisms with different scope. Answer both, independently:

**a. Live conversation context** (`/compact` territory — user-invoked only):
- Have you had to ask the user to re-state or re-confirm something from earlier this session?
- Has the user corrected the same *kind* of thing more than once?
- Is this session covering multiple unrelated tasks/topics end-to-end (a sign it's overdue for a
  fresh start rather than one continuous thread)?

**b. Cold memory files** (`compact-memory` territory — different skill, different files):
- Only relevant if `memory/decisions.md`, `memory/learnings.md`, or `memory/glossary.md` is
  approaching or over ~500 lines, or `memory/MEMORY.md` is approaching 200 lines.
- If none of these apply, say so plainly and do not recommend `compact-memory` — don't recommend a
  compaction pass just because this skill ran.

#### 3. Report

Plain-language verdict, one of:
- **"Looks fine — no action needed."** (most manual invocations should land here)
- **"Recommend `/compact`"** — with the one or two concrete observations from 2a that justify it.
- **"Recommend running `compact-memory`"** — with the file(s) and rough line count from 2b.
- **"Recommend both, for different reasons"** — state each reason separately; do not merge them into
  one blended justification.

Never run either compaction yourself — state the recommendation and let the user decide and invoke it.

---

### Communication Protocol

- **Default Notification** (automatic trigger): use CLAUDE.md's exact phrasing — "I'm noticing this
  session's context is getting large / harder to track — want me to compact before continuing?" —
  followed by the one concrete sign from Step 1 that triggered it. Do not invent a variant wording.
- **Default Notification** (manual trigger): "compact-advisor: [verdict] — [one-line reason]."
