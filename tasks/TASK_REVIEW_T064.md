# TASK_REVIEW — T064: Split reviewer-filled sections out of the implementer's guide

> Sibling of `tasks/TASK_GUIDE_T064.md`. This task dogfoods its own change: T064's Evidence and
> Demonstration live here, and the guide carries only `> **Moved.**` pointers.

---

## Evidence

| Check | Result | Notes / output snippet |
|-------|--------|------------------------|
| **New test(s) cover Acceptance Criteria (file paths pasted)** | ☑ pass | `.claude/hooks/tests/test_guide_sections.py` — 49 tests covering AC1–AC15 and the guide's Edge Case Checklist. The AC7 block was written first, before any resolver code existed (confirmed RED: `FileNotFoundError: .../lib/guide_sections.py`). |
| Verification command run | ☑ pass | **Refreshed at Stage 5 — the earlier `2 failed, 314 passed` was captured before the escalations were resolved and the Stage 4 P2 was fixed; leaving it would have recorded a state that no longer exists.** `python3 -m pytest .claude/hooks/tests/ -q` → `317 passed in 8.14s`. The 2 escalated tests were repointed by the Supervisor (row string byte-identical, new location asserted, guide template additionally asserted NOT to carry it); +1 test pins the Stage 4 P2 fix. `scripts/smoke-install.sh: PASS`. |
| Negative cases hold | ☑ pass | 4 mutation controls, each confirmed to have actually executed before its verdict was trusted. **AC7**: resolver made to return a filled-looking row on a missing file → **8 tests RED**, restored → GREEN. **AC10**: register-hook regex widened to `TASK_(?:GUIDE\|REVIEW)_` → RED (`[hook:post_write] Registered T999`), restored → GREEN. **AC11**: three independent token forms appended (`challenge-response`, bare `**Q:**`/`**A:**`, `challenge/response`) → RED on each, restored → GREEN. **AC14**: one byte appended to `tasks/TASK_GUIDE_T060.md` → RED, restored → GREEN. |
| verify | ☑ pass | Supervisor-run at Stage 5 against the real files, no patching and no fixtures — all four resolution paths exercised: T064's own split pair resolves its Demonstration from the review file (True), T063's legacy inline guide still resolves (True), pre-T053 T001 correctly returns None, and nonexistent T999 returns None. Suite `317 passed`, `smoke-install.sh` PASS. Feature confirmed working — **pass**. |
| Review scope bounded to the change's blast radius (affected set, not whole repo) | ☑ pass | Reviewed: the 3 consumers the resolver touches (`pre_bash_block_unsafe_merge.py`, `pre_agent_validate_guide.py`, `delivery-report/render.py`), the new `lib/guide_sections.py`, both templates, and the 3 SKILL.md edits. Skipped as unaffected: all other hooks, `task_context.py` (imitated, not edited), `scripts/`. Confirmed by diff: 11 files, no unpredicted file touched, and `tasks/` shows only the added review file (AC14). |
| Full smoke suite still green (no regression) | ☑ pass | `bash scripts/smoke-install.sh` → `PASS`; `bash scripts/validate.sh` → `PASS` (it still resolves `templates/TASK_GUIDE_template.md`). `MANIFEST` deliberately unchanged: line 11 is the bare `templates` directory entry copied with `cp -r`, so `TASK_REVIEW_template.md` deploys downstream automatically (T054 precedent). |
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

**AFTER**: as of `925212c`, 2026-08-09T04:48:46Z. Both blocks now live in
`templates/TASK_REVIEW_template.md` with their field names and rows byte-identical to the excerpts
above (pinned by `test_ac1_moved_*_are_byte_identical_to_the_baseline` against `2612a05`), and each
vacated position in `templates/TASK_GUIDE_template.md` carries a one-line pointer:

```markdown
### Evidence (filled by reviewer at Stage 4/5)

> **Moved.** Filled by the reviewer at Stage 4/5 in `tasks/TASK_REVIEW_T[NNN].md`.

---

## Demonstration

> **Moved.** See `tasks/TASK_REVIEW_T[NNN].md`.
```

New state of the consumers — all three go through one resolver:

```
$ ls .claude/hooks/lib/
guide_sections.py  task_context.py
```

- `pre_bash_block_unsafe_merge.py` gained `has_filled_verify_row(task_id, tasks_dir=None)`, which
  resolves the Evidence section guide-first then review-file and **fails closed** on every absence.
  `VERIFY_ROW_PATTERN` is the T026 regex byte-for-byte — only *where* the text is read from changed.
  Its import of the resolver is deliberately **not** wrapped in a fail-open `except`.
- `pre_agent_validate_guide.py` gained `before_value_is_blank(section_body)`;
  `before_field_is_blank(guide)` keeps its whole-guide signature and delegates.
  `check_demonstration_warnings` takes an optional `tasks_dir` and resolves through the helper.
- `render.py`: `parse_demonstration(guide_text, review_text)` /
  `parse_evidence_table(guide_text, review_text)` / `build_slots(..., tasks_dir=None)`.
  `NoDemonstrationBlock` is raised only when *neither* source carries the block.

Live end-to-end against the real files in this worktree (no patching, no fixtures):

```
T064 Demonstration BEFORE resolved from TASK_REVIEW_T064.md -> warnings: []
T063 legacy inline Demonstration                            -> warnings: []
T001 pre-T053 guide (no Demonstration anywhere)             -> warnings: 1
T060 (legacy inline, verify row filled) -> has_filled_verify_row: True
```

Measured AC15 reduction over five real guides at `2612a05` (bytes shed by moving both bodies out,
already net of the two pointer lines added back):

```
T060: 33.6%   T067: 30.5%   T063: 31.4%   T061: 32.3%   T058: 16.3%
control (one-line sections, huge Approach): -0.4%  — the metric discriminates
```

AC15 asks for a guide "of T060's shape" and is met at **33.6%**. Reported honestly: T058 is an
outlier at 16.3% because its `## Approach` is unusually large, so the *typical* saving is ~31–34%,
not a floor.

**DELTA**: an implementing agent's guide no longer carries the ~31–34% of bytes that only the
reviewer ever fills, and the three consumers that read those two sections find them in either
location — so no existing guide had to be migrated to get the saving on new ones.

**WITNESS**: Derived from `memory/event-trace/T064.jsonl`, not typed and not taken from the
implementing agent's own report. 87 records spanning 2026-08-09T04:29:37Z → 04:58:32Z: Bash 41,
Edit 34, Read 6, Write 5, Agent 1, of which 13 records carry a `pytest` invocation. The trace holds
both the sub-agent's calls and the Supervisor's own (T063 established the file is not actor-split),
so this is deliberately **not** attributed to one party — what it witnesses is that the verification
commands were really executed under this task ID, not merely claimed. The Supervisor independently
re-ran the AC7 mutation from a second direction (unreadable-file → filled row, 11 tests RED) and
found the Stage 4 P2 itself, so the implementer was not the sole oracle for its own work.

---

## Escalations (raised, not worked around)

**1. Two pre-existing tests pin the moved table to its old file. Left RED, not edited.**

Both assert the `verify` row's *location*, which is exactly what AC2 and AC12 move:

| Test | Asserts | Contradicts |
|---|---|---|
| `test_task_guide_template_verify_row.py::test_fixed_row_present_in_template_file` | `"\| verify \| ☐ pass / ☐ fail / ☐ N/A \|" in templates/TASK_GUIDE_template.md` | AC2 |
| `test_bugfix_evidence_parity.py::test_ac7_gate_finds_verify_row_in_real_skeleton_shaped_guide` | the same row is inline in `.claude/skills/bugfix/SKILL.md`'s Step 3 skeleton | AC12 |

Neither AC can be satisfied while both tests pass unchanged. Their *intent* — the shipped example
row must satisfy the merge gate once filled — is fully preserved; only the file it lives in changed.
Replacement coverage was added at the new location rather than editing either test green:
`test_ac1_review_templates_verify_row_still_satisfies_the_gate` and
`test_ac12_gate_finds_the_verify_row_in_a_real_split_bugfix_pair` (the latter builds the pair from
the real template text plus the bugfix skeleton's three extra rows and runs the real gate function).
Every other test in both files still passes, including `test_bugfix_evidence_parity`'s SC1–SC4,
which prove the gate is unregressed on legacy inline guides.

Supervisor decision needed. The minimal resolution is to repoint both assertions at
`templates/TASK_REVIEW_template.md` / the bugfix skeleton's new review block, keeping all assertion
text verbatim — but that is a test edit, and this agent was instructed to escalate rather than make
it.

**2. Pre-existing: the template's *unfilled* `verify` row already satisfies the merge gate.**

Not introduced by this task, and not fixed here (out of scope, and the wording is pinned by the test
in Escalation 1). Reproduced against the baseline commit:

```
$ git show 2612a05:templates/TASK_GUIDE_template.md | grep '^| verify'
| verify | ☐ pass / ☐ fail / ☐ N/A | [what was observed — must literally state "pass" or "fail"
here too, e.g. "skill run, feature confirmed working — pass": the merge gate scans this Notes
column for the word "pass", not just the Result column] |

matches gate regex `verify\s*\|[^|\n]+\|[^|\n]*pass`: True
```

T026's fix put the word "pass" into the Notes column *as guidance*, and the gate matches the Notes
column for that word — so a task that has copied the template and filled in nothing already clears
the row check. Only `trace_shows_verification` is holding the gate shut in that case. This becomes
more visible with T064, because every new task now starts from a `TASK_REVIEW_Txxx.md` carrying that
row. T064's own `verify` row was written without the placeholder so it does not falsely clear its
own gate. Suggested follow-up task: reword the placeholder to describe the rule without containing
a bare `pass` in the Notes cell (e.g. `[...must literally state the word p-a-s-s here too...]`), and
add a test that the *unfilled* row does NOT match the gate.
