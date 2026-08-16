# TASK_REVIEW — T071: Vital Slice — extend Simplicity First in the guaranteed channel

> Sibling of `tasks/TASK_GUIDE_T071.md`. Everything here is **filled by the reviewer at Stage
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

**BEFORE** (captured 2026-08-16, on `feat/vital-slice-t071-impl` at `b69410c`, before any
implementation commit exists — this task changes documentation and template text, so BEFORE is the
verbatim prior content of every section T071 will change):

1. `.claude/agents/backend.md:48-53` — the section exists, and says nothing about ranking a
   requested surface by value:

   ```
   ## Simplicity First (your defining constraint)

   As the core engineer you set the architectural tone, so over-engineering here costs the whole
   project. Default to the simplest design that satisfies the TASK_GUIDE. **Reject any abstraction not
   required by the requirement or an approved decision (ADR).** Heavier patterns are decision-gated —
   see the appendix; never reach for them speculatively. If 200 lines can be 50, write 50.
   ```

2. `.claude/agents/frontend.md:49-54` — same shape, same silence:

   ```
   ## Simplicity First (your defining constraint)

   Default to the simplest UI that satisfies the TASK_GUIDE. **Reject any abstraction not required by
   the requirement or an approved decision (ADR)** — no premature component libraries, no speculative
   state machines, no design-system scaffolding the task didn't ask for. Reuse before you build. If a
   heavier pattern seems warranted (see appendix), propose it; don't introduce it unilaterally.
   ```

3. `.claude/agents/common-infrastructure.md` — **the section does not exist at all.** Verbatim
   prior state, mechanically established rather than asserted:

   ```
   $ grep -c '^## Simplicity First (your defining constraint)$' .claude/agents/common-infrastructure.md
   0
   $ grep -n '^## ' .claude/agents/common-infrastructure.md
   8:## Role
   12:## Mandatory Startup Sequence
   29:## Karpathy Engineering Principles (Compact)
   38:## Responsibilities
   48:## Constraints (inherits General Agent Template)
   55:## Environment Health Checklist
   68:## Complexity & escalation
   85:## Available skills — scale to the task's Complexity Level
   96:## Communication Protocol
   113:## Output Format
   ```

   The only Simplicity First text this role guide carries is the pinned Karpathy table row at
   line 34, which T071 must not touch.

4. `.claude/agents/qa.md` — **the section does not exist at all**, same as (3):

   ```
   $ grep -c '^## Simplicity First (your defining constraint)$' .claude/agents/qa.md
   0
   $ grep -n '^## ' .claude/agents/qa.md
   13:## Mandatory Startup Sequence
   29:## Karpathy Engineering Principles (Compact)
   38:## The independence rule (why this role exists)
   47:## Your part in the three pillars
   56:## Scope boundaries (who owns what)
   66:## Evaluation checklist (apply what the task needs)
   79:## Complexity & escalation
   95:## Available skills — scale to the task's Complexity Level
   107:## Communication Protocol
   ```

5. `CLAUDE.md:111` — the Simplicity First row, with no heuristic mention anywhere in the file
   (`grep -c '80/20' CLAUDE.md` → `0`):

   ```
   | Simplicity First       | Overcomplication and bloated abstractions  | Prohibit speculation. Reject any feature or abstraction not explicitly requested. If 200 lines can be 50, rewrite. |
   ```

6. `CLAUDE_LEGACY.md:186` — the mirror row:

   ```
   | Simplicity First    | Reject unrequested abstractions. |
   ```

7. `templates/TASK_GUIDE_template.md:143-150` — `## Approach` carries `Pattern reference` and no
   `Vital slice` / `Cut list` field:

   ```
   ## Approach

   **Pattern reference**: [path/to/existing/file.ext — what to imitate about it] or `None — no comparable prior art in this repo` (with a one-line reason)
   > Example: `Pattern reference: .claude/hooks/pre_agent_validate_guide.py — structural ID extraction, fail-open error handling`
   > Point at code that already works and should be imitated. Without one, the agent falls back to
   > generic best practice instead of this repo's conventions (Karpathy: Surgical Changes).

   [Recommended approach from brainstorming skill output, or Supervisor's decision for Low-risk tasks. Include the reasoning.]
   ```

8. Baselines at the same commit — `wc -l`: backend 137, frontend 134, common-infrastructure 129,
   qa 121, `CLAUDE.md` 198, `templates/TASK_GUIDE_template.md` 193 (matches the guide's AC11
   note). Suite at this commit: `405 passed`, `scripts/test-agent-template.sh` exit 0.

**AFTER**: [same command, post-change] OR [verbatim excerpt of the new content]

**DELTA**: [one sentence — what a user can now do that they could not before]

**WITNESS**: [who ran it and when — derived from `memory/event-trace/Txxx.jsonl`, never the
implementing agent alone]
