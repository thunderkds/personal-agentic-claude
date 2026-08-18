# TASK_REVIEW — T079: [Short Title]

> Sibling of `tasks/TASK_GUIDE_T079.md`. Everything here is **filled by the reviewer at Stage
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

**BEFORE** (captured 2026-08-18T14:43:40Z, before any implementation commit on `fix/t079-impl`):

*Markdown half* — verbatim prior content of `.claude/skills/write-better-skill/SKILL.md`, the only
description-craft material the skill carried (lines 23–29). There was no `references/` directory, no
`## Sourcing` section, and no context pointer anywhere in the file:

```markdown
### Writing the description

A model-invoked description does two jobs: state what the skill is, and list the **branches** that trigger it. Every word is context load — prune harder than the body.

- **Front-load the leading word** — the description is where it does its invocation work.
- **One trigger per branch.** Synonyms that rename a single branch are duplication — collapse them.
- **Cut identity already in the body.** Keep triggers plus any "when another skill needs…" reach clause.
```

`.claude/skills/teach/SKILL.md` step 4 "Draft the SKILL.md" likewise reached no reference file — its
description bullet was self-contained:

```markdown
- **description**: trigger phrasing (model-invoked) or human summary (user-invoked); front-load the leading word; one trigger per branch; no identity prose that belongs in the body.
```

*Test half* — the hook suite before this task's change (no `test_skill_reference_pointers.py` exists):

```
$ date -u && python3 -m pytest .claude/hooks/tests/ -q
Tue Aug 18 02:43:40 PM UTC 2026
641 passed in 9.70s

$ ls .claude/hooks/tests/test_skill_reference_pointers.py
ls: cannot access '.claude/hooks/tests/test_skill_reference_pointers.py': No such file or directory
```


**AFTER**: [same command, post-change] OR [verbatim excerpt of the new content]

**DELTA**: [one sentence — what a user can now do that they could not before]

**WITNESS**: [who ran it and when — derived from `memory/event-trace/Txxx.jsonl`, never the
implementing agent alone]
