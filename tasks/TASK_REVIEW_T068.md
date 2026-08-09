# TASK_REVIEW — T068: An unfilled `verify` Evidence row already satisfies the merge gate

> Sibling of `tasks/TASK_GUIDE_T068.md`. Everything here is **filled by the reviewer at Stage
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
| **New test(s) cover Acceptance Criteria (file paths pasted)** | ☑ pass | `.claude/hooks/tests/test_verify_row_fill_detection.py` — 9 tests, AC1–AC9 mapped 1:1 (AC1 reproduces the defect, AC2 the two-option unfilled shape, AC3+trap the four filled shapes incl. T050's `☑ pass / ☐ N/A`, AC4 the T026 Notes-column property, AC5 the Check-cell exactness, AC6 the whole-corpus old-vs-new diff, AC7 the mutation control, AC9 fail-closed on a missing section) |
| Verification command run | ☑ pass | `pytest .claude/hooks/tests/ -q` → `326 passed in 8.06s` (post-fix, full suite) |
| Negative cases hold | ☑ pass | AC1 run against the pre-fix pattern (stashed/reverted `pre_bash_block_unsafe_merge.py`) FAILED as expected — `assert True is False` on the template placeholder row — before the fix landed; restored and reran GREEN. See Demonstration below |
| verify | ☑ pass | Full targeted test file `test_verify_row_fill_detection.py` → `9 passed`; full hook suite `pytest .claude/hooks/tests/ -q` → `326 passed`; re-ran the real gate function `has_filled_verify_row` against real temp fixtures (`T900`=untouched placeholder → `False`, `T901`=T050's exact real shape → `True`) — matches AC1/AC3 exactly. Feature confirmed working — pass |
| Review scope bounded to the change's blast radius (affected set, not whole repo) | ☑ pass | Diff touches exactly `VERIFY_ROW_PATTERN` + `UNCHECKED_PASS_PATTERN` + `has_filled_verify_row`'s body/docstring in `.claude/hooks/pre_bash_block_unsafe_merge.py`, plus the new test file and this review file — nothing else in the hook (`main()`, `trace_shows_verification`, `BLOCKED_PATTERNS`, etc.) or in `templates/` was touched, per AC8/Files Must NOT Touch |
| Full smoke suite still green (no regression) | ☑ pass | `pytest .claude/hooks/tests/ -q` → `326 passed`, 0 failed, 0 errors — no other test file regressed |
| **UI: Visual regression (diff or verdict pasted)** | ☐ N/A | pure backend/tooling change, no UI surface |
| **UI: Design-system compliance (tokens/colors/typography verified)** | ☐ N/A | pure backend/tooling change, no UI surface |
| **UI: Responsiveness at target viewports** | ☐ N/A | pure backend/tooling change, no UI surface |

---

## Demonstration

**BEFORE** (2026-08-09T09:49:44Z, pre-fix, real `VERIFY_ROW_PATTERN` against the untouched template's placeholder row):

```
$ python3 -c "
import re
VERIFY_ROW_PATTERN = re.compile(r'verify\s*\|[^|\n]+\|[^|\n]*pass', re.IGNORECASE)
row = '| verify | ☐ pass / ☐ fail / ☐ N/A | [what was observed — must literally state \"pass\" or \"fail\" here too, e.g. \"skill run, feature confirmed working — pass\": the merge gate scans this Notes column for the word \"pass\", not just the Result column] |'
m = VERIFY_ROW_PATTERN.search(row)
print('BEFORE match on untouched template placeholder row:', bool(m))
"
BEFORE match on untouched template placeholder row: True
```

Confirmed again via the AC1 test run directly against the pre-fix code (stashed the fix, ran the
new test file, restored):

```
$ git stash push -- .claude/hooks/pre_bash_block_unsafe_merge.py
$ pytest .claude/hooks/tests/test_verify_row_fill_detection.py -v
...
test_verify_row_fill_detection.py::test_ac1_unfilled_template_placeholder_row_is_not_filled FAILED
E       assert True is False
...
1 failed, 8 passed in 0.04s
$ git stash pop
```

An unfilled `verify` row — the literal template placeholder, never edited by any reviewer — already
satisfied the gate's row check.

**AFTER** (2026-08-09T09:53:26Z, post-fix, same untouched placeholder row through the real module):

```
AFTER: template placeholder row classified as filled = False
```

And the trap case, T050's real legitimately-filled `☑ pass / ☐ N/A` row, still classifies correctly:

```
T900 (untouched placeholder) -> False
T901 (T050's exact shape: ☑ pass / ☐ N/A)   -> True
```

**DELTA**: A task in Ready for Review whose `verify` Evidence row is still the untouched template
placeholder is now correctly blocked by the merge gate; a genuinely filled row — including the
`☑ pass / ☐ N/A` shape T050 legitimately used — still passes.

**WITNESS**: Common-Infrastructure-Agent, run directly in `/home/hungnguyenhuu/workspace/pets/pac-t068`
(worktree, branch `t068-work`) at the timestamps above; `CLAUDE_ACTIVE_TASK=T068` was set for every
pytest invocation so `memory/event-trace/T068.jsonl` carries the attributed test-runner records.
