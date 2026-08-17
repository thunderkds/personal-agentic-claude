# TASK_REVIEW — T075: Decouple the hot-tier budget mutation from the live file's size, and ratchet 50,000 → 45,000

> Sibling of `tasks/TASK_GUIDE_T075.md`. Everything here is **filled by the reviewer at Stage
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

**BEFORE**: captured 2026-08-17T08:45:27Z, before any implementation commit, by qa-expert
(QA-Automation-Agent), in worktree `/home/hungnguyenhuu/workspace/pets/wt-t075`:

```
$ cd /home/hungnguyenhuu/workspace/pets/wt-t075 && date -u +%Y-%m-%dT%H:%M:%SZ && \
  python3 -m pytest .claude/hooks/tests/test_memory_channel_and_budget.py::test_ac10_growth_in_chars_without_growth_in_lines_turns_the_gate_red -v
2026-08-17T08:45:27Z
...
        # The NEW gate is red, and says something actionable (AC2).
>       with pytest.raises(AssertionError) as exc:
E       Failed: DID NOT RAISE <class 'AssertionError'>

.claude/hooks/tests/test_memory_channel_and_budget.py:266: Failed
=========================== short test summary info ============================
FAILED .claude/hooks/tests/test_memory_channel_and_budget.py::test_ac10_growth_in_chars_without_growth_in_lines_turns_the_gate_red
============================== 1 failed in 0.04s ===============================
```

**AFTER**: BLOCKED — see report to Supervisor. Implementation of AC1–AC4 (test_ac10's own-breach
padding loop, the breach assertion, and the AC3 tiny-stub size-independence test) is complete and
was verified green in isolation. AC5 (lowering `HOT_TIER_CHAR_BUDGET` to `45_000`) surfaces a
contradiction with the Files-Must-Not-Touch list — see notes below — so the task is halted before a
full-suite AFTER capture, pending Supervisor ruling.

**DELTA**: not yet delivered — blocked pending Supervisor decision on the AC5/Must-Not-Touch
contradiction described in the qa-expert report.

**WITNESS**: qa-expert (QA-Automation-Agent), 2026-08-17, this worktree.
