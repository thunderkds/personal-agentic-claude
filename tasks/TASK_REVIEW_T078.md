# TASK_REVIEW — T078: [Short Title]

> Sibling of `tasks/TASK_GUIDE_T078.md`. Everything here is **filled by the reviewer at Stage
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

**BEFORE** (two halves — this task changes non-executable Markdown AND adds executable test code):

*(a) Non-executable half — verbatim prior content of `.claude/skills/write-better-skill/SKILL.md` at commit `640283a`, before any T078 implementation commit.*

The file is 140 lines and contains these headings only — there is **no** `## Agent Skills Spec Conformance` section, and no line anywhere in the file states any spec constraint (no "64", no "1024", no "500 lines"):

```
$ grep -n '^#\{1,3\} ' .claude/skills/write-better-skill/SKILL.md
6:## Role: Skill Craft Reference
14:## Invocation
23:### Writing the description
33:## Leading Words
48:## Information Hierarchy
64:## Completion Criteria
79:## When to Split
88:## Pruning
100:## Fidelity Gate (Hallucination Check)
114:## Pipeline Integration (This Framework)
134:## Failure Modes
```

The `## Information Hierarchy` section ends its progressive-disclosure paragraph with a vague,
uncheckable claim (verbatim, line 60):

> **Progressive disclosure** is the move down the ladder — out of SKILL.md into a linked file — so the top stays legible. The pointer's *wording* decides how reliably the agent reaches the material.

The Registration checklist (verbatim, lines 126-130) says nothing about the spec's frontmatter rules
beyond folder-name matching:

> Registration checklist for any new skill:
> - [ ] Folder name matches `name:` frontmatter exactly
> - [ ] Added to the custom-skill table in `CLAUDE.md`
> - [ ] One-liner added to `memory/MEMORY.md` hot tier
> - [ ] `description` uses trigger phrasing (model-invoked) or human summary (user-invoked)

*(b) Executable half — the hook suite as it stands before the change, with no conformance test in it.*

```
$ date -u +%Y-%m-%dT%H:%M:%SZ
2026-08-18T11:03:13Z
$ python3 -m pytest .claude/hooks/tests/ -q
[...]
451 passed in 9.35s

$ ls .claude/hooks/tests/ | grep -c skill_spec_conformance
0
```

451 tests pass, and **zero** of them assert anything about `.claude/skills/`: the 30 skills' spec
compliance is entirely untested at this point.


**AFTER**: [same command, post-change] OR [verbatim excerpt of the new content]

**DELTA**: [one sentence — what a user can now do that they could not before]

**WITNESS**: [who ran it and when — derived from `memory/event-trace/Txxx.jsonl`, never the
implementing agent alone]
