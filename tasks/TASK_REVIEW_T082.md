# TASK_REVIEW — T082: [Short Title]

> Sibling of `tasks/TASK_GUIDE_T082.md`. Everything here is **filled by the reviewer at Stage
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

**BEFORE**: T082 changes no executable code. Verbatim prior content of the four surfaces named in
the guide's Demonstration section, quoted as they existed on `fix/t082-impl` before any T082
implementation commit:

1. `.claude/agents/general-agent-template.md` — Base Rules (lines 14-24):
   ```
   ## Base Rules (Inherited by All Sub-Agents)

   - Strictly follow all Karpathy Engineering Principles (compact table in your own role guide - full version with rationale in `CLAUDE.md`, keep both in sync on edit)
   - Never assume context — always derive it from the startup reads your role guide lists. In
     particular, **read `memory/MEMORY.md` yourself**: the spawn prompt gives you its path, not its
     contents, so nothing loads it for you
   - Communicate clearly with the Supervisor and other agents
   - Update the Memory/Insights section of `PROJECT_SPEC.md` with key learnings after task completion
   - Pause and ask the Supervisor if any ambiguity or error occurs
   - Work only inside the assigned git worktree
   - Surgical changes only — touch no code outside the task scope
   ```

2. `.claude/skills/resolve-pr-feedback/SKILL.md` — triage step (lines 47-62), including the
   `Default to **Fix**` sentence at line 58:
   ```
   #### Phase 2 — Triage

   For each thread, classify into one of four buckets:

   | Bucket | Criteria | Action |
   |---|---|---|
   | **Fix** | Valid finding; code change is clear and safe | Implement fix |
   | **Discuss** | Finding is invalid, based on a misread, or factually wrong | Reply with explanation; do not change code |
   | **Human judgment** | Decision requires business context the reviewer can't have | Reply asking the Supervisor or user to decide; flag for human |
   | **Question** | Reviewer is asking, not requesting a change | Reply with answer; no code change |

   Default to **Fix** when the comment is a nitpick or style suggestion — most review feedback is correct and worth addressing.

   Record the triage decision for every thread before writing a single line of code.

   Completion criterion: every thread assigned a bucket; triage table complete.
   ```

3. `.claude/skills/brainstorming/SKILL.md` — `WebSearch` bullet (line 16):
   ```
   - **Alternative Path Generation**: Research and propose modern best practices (use `WebSearch` when comparing stack choices or architectural patterns) and compare them.
   ```

4. `README.md` — `## Custom Skills` block (lines 329-339), current opening:
   ```
   ## Custom Skills

   All skills live in `.claude/skills/<name>/SKILL.md` and are auto-discovered by Claude Code. Invoke any skill via `Skill({ skill: "<name>" })` or the `/name` slash command.

   This repo's skills implement the open [Agent Skills specification](https://agentskills.io). A conforming `SKILL.md` must satisfy:
   - `name`: lowercase alphanumeric + hyphens only, matching the parent directory
   - `description`: non-empty, ≤1024 characters
   - length: ≤500 lines, counted over the whole file including frontmatter
   - optional `scripts/`, `references/`, `assets/` directories, loaded on demand

   `write-better-skill` is the in-repo authority for the full rules and the reasoning behind them; do not re-derive them here. Checked automatically by `.claude/hooks/tests/test_skill_spec_conformance.py`, run via `python3 -m pytest .claude/hooks/tests/test_skill_spec_conformance.py`.
   ```
   (No `### External security reporting` block exists anywhere in `README.md` prior to this task.)

**AFTER**: [same command, post-change] OR [verbatim excerpt of the new content]

**DELTA**: [one sentence — what a user can now do that they could not before]

**WITNESS**: [who ran it and when — derived from `memory/event-trace/Txxx.jsonl`, never the
implementing agent alone]
