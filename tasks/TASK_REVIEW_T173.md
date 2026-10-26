# TASK_REVIEW — T173: AGENTS.md is the primary doctrine file; CLAUDE.md imports it

> Sibling of `tasks/TASK_GUIDE_T173.md`. Everything here is **filled by the reviewer at Stage
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

**BEFORE** (captured by common-infrastructure at the branch base, before any T173 commit; HEAD `4d32f76` = `c573bbf` + the plan commit, which touches only `tasks/TASK_GUIDE_T173.md`):

```
$ date -u; git rev-parse --short HEAD
2026-10-26T03:02:08Z
4d32f76
$ head -3 CLAUDE.md AGENTS.md
==> CLAUDE.md <==
# Claude Project Supervisor Guidelines
**Version:** 1.17 (Unified Agentic Operating System) <br>
**Role:** Project Supervisor AI

==> AGENTS.md <==
# AGENTS.md

This is a thin adapter for non-Claude agentic CLIs (Codex, etc.) — auto-read at the repo root.
$ wc -l CLAUDE.md AGENTS.md
  186 CLAUDE.md
   55 AGENTS.md
  241 total
$ cd $(mktemp -d) && git init -q && SUPERVISOR_REPO=file:///home/hungnguyenhuu/workspace/pets/wt-t173 sh /home/hungnguyenhuu/workspace/pets/wt-t173/setup.sh </dev/null   # no terminal -> new-project default
exit=0
[info]  Installed .claude/settings.json (copy). Restart Claude Code to activate hooks.
[info]  Wrote ./.claude/harness-lock.json (117 file hashes).
[info]  CLAUDE source: CLAUDE.md | lock: .claude/harness-lock.json
[info]  CLIs: Claude Code, Codex
$ head -1 CLAUDE.md; wc -lc CLAUDE.md AGENTS.md; grep claude_md_source .claude/harness-lock.json
# Claude Project Supervisor Guidelines
  186 16898 CLAUDE.md
   55  2994 AGENTS.md
  241 19892 total
  "claude_md_source": "CLAUDE.md",
```

The installed project gets the full doctrine in `CLAUDE.md` (186 lines) and the 55-line thin adapter in `AGENTS.md`.

**AFTER**: [same command, post-change] OR [verbatim excerpt of the new content]

**DELTA**: [one sentence — what a user can now do that they could not before]

**WITNESS**: [who ran it and when — derived from `memory/event-trace/Txxx.jsonl`, never the
implementing agent alone]
