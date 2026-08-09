# TASK_REVIEW — T064: Split reviewer-filled sections out of the implementer's guide

> Sibling of `tasks/TASK_GUIDE_T064.md`. This task dogfoods its own change: T064's Evidence and
> Demonstration live here, and the guide carries only `> **Moved.**` pointers.

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
| **UI: Visual regression (diff or verdict pasted)** | ☐ N/A | pure-backend task — hooks, templates and skill-instruction text only, no UI surface |
| **UI: Design-system compliance (tokens/colors/typography verified)** | ☐ N/A | pure-backend task — no UI surface |
| **UI: Responsiveness at target viewports** | ☐ N/A | pure-backend task — no UI surface |

---

## Demonstration

**BEFORE**: captured 2026-08-09T04:35:08Z, worktree `/home/hungnguyenhuu/workspace/pets/pac-t064`
at `2612a05 docs(T064): Stage 2 guide — split reviewer sections out of the guide`, before any
implementation commit. This task changes templates, hooks and skill-instruction text, so BEFORE is
the **verbatim prior content** of what is about to change, plus the byte measurements the change is
justified by.

Verbatim prior content — `templates/TASK_GUIDE_template.md` lines 100–113, `### Evidence`:

```markdown
### Evidence (filled by reviewer at Stage 4/5)

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
```

Verbatim prior content — `templates/TASK_GUIDE_template.md` lines 116–131, `## Demonstration`:

```markdown
## Demonstration

> Anchors what this task delivered to an observable before/after pair. BEFORE has no `N/A` path:
> if the task changes executable code, BEFORE is a pasted, timestamped terminal capture taken
> **before any implementation commit exists**; if it does not (docs, templates, skill-instruction
> text), BEFORE is the **verbatim prior content** of what changed — a quoted excerpt, not a command.

**BEFORE**: [pasted timestamped command output showing the thing absent/failing, captured before the
first implementation commit] OR [verbatim excerpt of the prior content, for non-executable changes]

**AFTER**: [same command, post-change] OR [verbatim excerpt of the new content]

**DELTA**: [one sentence — what a user can now do that they could not before]

**WITNESS**: [who ran it and when — derived from `memory/event-trace/Txxx.jsonl`, never the
implementing agent alone]
```

Byte measurements at `2612a05`, 2026-08-09T04:35:08Z (`python3` section-slice over the real files):

```
templates/TASK_GUIDE_template.md: TOTAL bytes: 9911
  ### Evidence: section bytes=1300
  ## Demonstration: section bytes=901

tasks/TASK_GUIDE_T060.md: total=27548 evidence=3871 demo=5501 moved=9372 remaining=18176 reduction=34.0%
tasks/TASK_GUIDE_T067.md: total=23952 evidence=2727 demo=4693 moved=7420 remaining=16532 reduction=31.0%
```

Prior state of the consumers, verbatim:

- `.claude/hooks/pre_agent_validate_guide.py:113` — `before_field_is_blank` sliced the section from
  the guide text only: `re.search(r"^## Demonstration\s*$(.*?)(?=^## |\Z)", guide, ...)`. No sibling
  file was ever consulted; a guide without the section was unconditionally "blank".
- `.claude/hooks/pre_bash_block_unsafe_merge.py:242` — the merge gate scanned the **whole guide**:
  `has_evidence_row = re.search(r"verify\s*\|[^|\n]+\|[^|\n]*pass", guide, re.IGNORECASE)`, with a
  `FileNotFoundError` branch appending the task to `unverified`.
- `.claude/skills/delivery-report/render.py:32,94` — `DEMO_SECTION_RE` and the `^###\s*Evidence`
  slice both read `guide_text` only; `parse_demonstration` raised `NoDemonstrationBlock` whenever the
  guide had no inline section, with no second source to try.
- `.claude/hooks/lib/guide_sections.py` — **did not exist**:

```
$ ls .claude/hooks/lib/
task_context.py
```

**AFTER**: [filled at Stage 4/5]

**DELTA**: [filled at Stage 4/5]

**WITNESS**: [derived from `memory/event-trace/T064.jsonl` at Stage 4/5 — never the implementing
agent alone]
