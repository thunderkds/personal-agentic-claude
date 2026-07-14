## Bug Fix Task Guide — T018
**Date**: 2026-07-14
**Complexity Level**: C1
**Risk Level**: Low
**Priority**: P1
**Assigned agent**: backend-developer
**Agent guide**: `.claude/agents/backend.md`

### Mental Model (confirmed by user)
- Observed: `.claude/hooks/post_write_register_task.py` extracts a title for new `TASK_GUIDE_Txxx.md` files via regex `^#\s+TASK_GUIDE[_\s]+T\d+[:\s—-]+(.+)$`. Real guide headings are formatted `# TASK_GUIDE — T005: CLI Wiring — Typer Entrypoint` (em-dash between `TASK_GUIDE` and the task ID). The `[_\s]+` class between `TASK_GUIDE` and `T\d+` does not include `—`, so the match fails and the hook falls back to `"untitled"`.
- Expected: the regex must extract the real title (e.g. `"CLI Wiring — Typer Entrypoint"`) from the actual heading format used across all existing guides.
- Likely divergence point: the character class `[_\s]+` immediately after `TASK_GUIDE` in the `extract()` call for `title` in `post_write_register_task.py`.
- Recent context: no prior decision/learning entries reference this hook; behavior has been wrong since the hook was introduced (all T005–T012 rows show `"untitled"`).

### Intake
- Trigger: Write tool creates/overwrites a file matching `tasks/TASK_GUIDE_(T\d+)\.md$` whose first line uses an em-dash between `TASK_GUIDE` and the task ID.
- Severity: P2 (data-quality bug in Kanban auto-registration, not a functional break).
- Affected area: `.claude/hooks/post_write_register_task.py` (title extraction regex only).

### Complexity & Risk
- Complexity: C1 (single file, but touches a PostToolUse hook used on every future Write — floor C1 per structural-work floor is not triggered, but the blast radius across future task registrations warrants care).
- Risk: Low

### Diagnosis Gates (Pillar 1 — must pass before any fix)
- [ ] Phase 1 feedback loop: write a scratch `tasks/TASK_GUIDE_T999_TEST.md` with a heading in the real em-dash format and run the hook against it (or invoke its `extract()` logic directly) to confirm current behavior returns `"untitled"`.
- [ ] Bug reproduces deterministically on the loop.
- [ ] Hypothesis: widening the class to `[_\s—-]+` (or equivalent) fixes extraction. No other hypotheses needed — this is a one-line regex fix with a clear, verified cause.
- [ ] Confirm fix extracts the correct title against all of T005–T012's real headings, not just one sample.

### Fix Gates (Pillar 2)
- [ ] Regression test written before the fix: a small script/test asserting `extract()`'s title regex against a fixed sample heading string (e.g. `"# TASK_GUIDE — T005: CLI Wiring — Typer Entrypoint"`) returns `"CLI Wiring — Typer Entrypoint"`, not `"untitled"`.
- [ ] Fix applied to the regex in `post_write_register_task.py`; regression test passes.
- [ ] Re-run the hook (or its extract function) against T005–T012's actual first lines and confirm each returns its real title, not `"untitled"`.
- [ ] Fix matches "correct behaviour": em-dash, hyphen, colon, and whitespace separators between `TASK_GUIDE` and the task ID, and between the ID and the title, all parse correctly.

### Cleanup Checklist (Pillar 3)
- [ ] All debug instrumentation removed (grep verified)
- [ ] Throwaway prototypes/scratch files (e.g. `TASK_GUIDE_T999_TEST.md`) deleted
- [ ] Correct hypothesis stated in commit message
- [ ] Post-mortem: what would have prevented this? (e.g. the hook was never tested against real guide headings at write time)

### Evidence
| Check | Command / observation | Result |
|---|---|---|
| Repro loop | `python3 -c "import re; print(re.search(r'^#\s+TASK_GUIDE[_\s]+T\d+[:\s—-]+(.+)$', '# TASK_GUIDE — T005: CLI Wiring — Typer Entrypoint', re.IGNORECASE))"` | `None` — confirmed old regex fails to match the real em-dash heading format, causing fallback to `"untitled"`. |
| Regression test | `python3 -m pytest .claude/hooks/tests/test_post_write_register_task.py -v` (5 cases: em-dash, underscore, hyphen separators, untitled fallback, and multi-line file content) | `5 passed in 0.01s` — all pass against fixed pattern with `re.IGNORECASE \| re.MULTILINE` |
| Smoke suite | No repo-wide automated test suite exists for this project (framework/docs repo, no `tests/` root dir). Verified fix against real data: ran `extract()` (as actually called by the hook — `re.search` against the full multi-line `guide` file content, not just the first line) against `tasks/TASK_GUIDE_T005.md`–`T012.md`. | Code-review (Stage 4) caught a regression here: the first fix only added `—`/`-` to the character class but omitted `re.MULTILINE`, so `re.search(pattern, guide, re.IGNORECASE)` against real (multi-line) file content still returned `None` → `"untitled"`, even though the isolated single-line test cases passed. Verified live against `tasks/TASK_GUIDE_T005.md` before the second fix: `title: 'untitled'`. Added `re.MULTILINE` to the `extract()` call; re-ran against all of T005–T012's real file content — all 8 now produce real titles (e.g. `T005 -> "CLI Wiring — Typer Entrypoint"`, `T009 -> "Core \`learn\` SKILL.md — detection, LR writing, supersession, skill promotion"`), none fell back to `"untitled"`. |
