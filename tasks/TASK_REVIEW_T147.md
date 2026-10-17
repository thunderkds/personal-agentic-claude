# TASK_REVIEW — T147: Spawned sub-agents run under a tighter sandbox profile than the Supervisor

> Sibling of `tasks/TASK_GUIDE_T147.md`. Everything here is **filled by the reviewer at Stage
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

**BEFORE** (captured by the implementing agent at `9d470d7` — T146 committed, no T147 change yet):

```text
2026-10-17T03:34:17Z
$ python3 -m pytest tests/test_subagent_sandbox_profile.py -q
ERROR: file or directory not found: tests/test_subagent_sandbox_profile.py

no tests ran in 0.00s
exit=4
$ ls templates/subagent-sandbox.settings.json scripts/gen_sandbox_profile.py
ls: cannot access 'templates/subagent-sandbox.settings.json': No such file or directory
ls: cannot access 'scripts/gen_sandbox_profile.py': No such file or directory
exit=2
$ grep -c -e "--settings" -e "sandbox" skills/craft-spawn-prompt/SKILL.md
0
$ git diff main -- .claude/settings.json | grep -c permissions
0
```

Prior content of the part of `skills/craft-spawn-prompt/SKILL.md` this task changes (`#### 6. Output`),
verbatim:

```markdown
#### 6. Output
Return: 1. the assembled prompt (fenced, ready for `Agent({ subagent_type, prompt })`); 2. the
pre-flight verdict; 3. the recommended spawn model as `<cli> · <Cn> → <model>` (or STOP-and-ask).

The Supervisor reads this output and issues the `Agent()` call itself; this skill never calls it.
```

No profile, no generator, no CLI spawn command and no word on sandboxing: a CLI-spawned sub-agent
ran with whatever permissions its terminal's `claude` picked up, the same as the Supervisor's.

**AFTER**: [same command, post-change] OR [verbatim excerpt of the new content]

**DELTA**: [one sentence — what a user can now do that they could not before]

**WITNESS**: [who ran it and when — derived from `memory/event-trace/T147.jsonl`, never the
implementing agent alone]
