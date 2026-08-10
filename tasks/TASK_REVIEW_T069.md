# TASK_REVIEW — T069: Move the Karpathy table into the guaranteed channel

> Sibling of `tasks/TASK_GUIDE_T069.md`. Everything here is **filled by the reviewer at Stage
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
| **UI: Visual regression (diff or verdict pasted)** | ☐ pass / ☐ fail / ☐ N/A | [pure-docs/config task — no UI component; UI AC section deleted from the guide] |
| **UI: Design-system compliance (tokens/colors/typography verified)** | ☐ pass / ☐ fail / ☐ N/A | [pure-docs/config task — no UI component] |
| **UI: Responsiveness at target viewports** | ☐ pass / ☐ fail / ☐ N/A | [pure-docs/config task — no UI component] |

---

## Demonstration

> Anchors what this task delivered to an observable before/after pair. BEFORE has no `N/A` path:
> if the task changes executable code, BEFORE is a pasted, timestamped terminal capture taken
> **before any implementation commit exists**; if it does not (docs, templates, skill-instruction
> text), BEFORE is the **verbatim prior content** of what changed — a quoted excerpt, not a command.

**BEFORE**: Captured 2026-08-10 in worktree `/home/hungnguyenhuu/workspace/pets/wt-t069` at commit
`ad13dc6` — **before any implementation commit existed** (`git log --oneline -1` →
`ad13dc6 docs(T069): Stage 2 guide — move the Karpathy table to the guaranteed channel`).

The Karpathy table's *sole* location, verbatim, `.claude/agents/general-agent-template.md:26-33`:

```
## Karpathy Engineering Principles (Compact)

| Principle | Operational Command |
|---|---|
| Think Before Coding | Ask vs. Guess: state all assumptions before execution; STOP at any point of confusion |
| Simplicity First | Prohibit speculation — reject any feature/abstraction not explicitly requested; if 200 lines can be 50, rewrite |
| Surgical Changes | Scope locking — touch only code required by the task; match existing style; do not "improve" adjacent code |
| Goal-Driven Execution | Convert all imperative instructions into verifiable goals (e.g. "fix the bug" -> "write a failing test, then make it pass") |
```

Grep showing it lives nowhere else in `.claude/agents/`, and is absent from all four role guides —
i.e. it reaches a sub-agent only if that agent chooses to open the template:

```
$ grep -rn "## Karpathy Engineering Principles (Compact)" .claude/agents/
.claude/agents/general-agent-template.md:26:## Karpathy Engineering Principles (Compact)

$ for f in common-infrastructure backend frontend qa; do \
    printf '%s: ' ".claude/agents/$f.md"; \
    grep -cF -e "Ask vs. Guess" -e "Scope locking" ".claude/agents/$f.md"; done
.claude/agents/common-infrastructure.md: 0
.claude/agents/backend.md: 0
.claude/agents/frontend.md: 0
.claude/agents/qa.md: 0
```

The template's own prose asserted the location that this task invalidates —
`general-agent-template.md:14`: ``- Strictly follow all Karpathy Engineering Principles (below — full version with rationale in `CLAUDE.md`, keep both in sync on edit)`` — and
`## Staleness Guard` (line 67-69): "If you edit Base Rules or the Karpathy Engineering Principles
**above**, check `AGENTS.md` …".

**AFTER**: [same greps, post-change]

**DELTA**: [one sentence — what a sub-agent now receives that it previously only might have]

**WITNESS**: [who ran it and when — derived from `memory/event-trace/T069.jsonl`, never the
implementing agent alone]
