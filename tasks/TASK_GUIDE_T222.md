# TASK_GUIDE — T222: The auto-mode Stop hook counts an Advocate only by its name pattern and the template's first prompt line
**Date**: 2026-10-31
**Complexity Level**: C1
**Risk Level**: High (safety hook: `.claude/hooks/stop_auto_mode_check.py` decides whether an `[auto]` run may stop)
**Priority**: P1
**Assigned agent**: common-infrastructure
**Agent guide**: `agents/common-infrastructure.md`

---

## Mandatory Startup (Do Not Skip)

1. Read `PROJECT_SPEC.md` (glossary rows Debate, Advocate, Auto mode, Final report)
2. Read the memory slice in your spawn prompt (`<!-- memory-slice -->`). Read `memory/MEMORY.md` in full only if your work reaches what the slice does not cover
3. Read this file completely
4. Read `agents/common-infrastructure.md`
5. Read `.claude/hooks/stop_auto_mode_check.py` in full, `.claude/hooks/post_tool_trace.py` `summarize()` (the trace summary is `json.dumps(tool_input)[:MAX_SUMMARY_LEN]`), and `.claude/hooks/tests/test_stop_auto_mode_check.py`
6. Read `skills/resolve-question/references/advocate.md` and `docs/claude-md/tracks.md` `### Debate size by Risk`

---

## Requirement (Pillar 1 — Adapt the requirement)

Found by the T221 auto verify run (2026-10-31): both live Advocates, on their own, cited `.claude/hooks/stop_auto_mode_check.py:248-249`:

```python
have = sum(1 for r in records if r.get("tool_name") == "Agent"
           and field(r.get("summary"), "description").startswith("Advocate"))
```

Any `Agent` call whose description starts with `Advocate` (for example `Advocates summary`, or an agent that never got the Advocate template) counts toward checks (3) and (5), so the hook can let an `[auto]` run stop that it should block.

User choice, 2026-10-31 (forced choice, option "Name + prompt line"): count a call as an Advocate only if its `description` matches `^Advocate \d+:` **AND** its `prompt` starts with the template's first line `Using the repo, answer alone:`.

**Restated intent**:
> The Stop hook counts an `Agent` trace record as an Advocate call only when both its description has the `Advocate <n>:` form and its prompt begins with the Advocate template's fixed first line. Every other check of the hook, and its block/allow behavior for correctly formed Debates, stays as it is.

**Out of scope**:
- The shared untagged 6h trace window (T186)
- Requiring distinct Advocate numbers
- Any change to the Debate rules in `skills/resolve-question/SKILL.md` (byte budget 8133 / 8192)
- Other checks of `stop_auto_mode_check.py`

**Requirement Refs**: T221 verify finding + user forced choice above

### Requirement Fidelity Gate

- [x] Restated intent confirmed — the user picked "Name + prompt line" 2026-10-31
- [x] Domain terms align — Advocate, Debate, Auto mode (`PROJECT_SPEC.md` glossary)
- [x] Every Acceptance Criterion traces to a line in the Requirement
- [x] All Requirement Refs exist and are covered

---

## Dependencies & Reachability

**Depends on**: T221 (template first line `Using the repo, answer alone:` in `skills/resolve-question/references/advocate.md`, on main)
**Entry point**: `.claude/hooks/stop_auto_mode_check.py` — the Advocate count used by checks (3) and (5)

---

## Acceptance Criteria

| # | Criterion (testable) | Traces to requirement |
|---|----------------------|-----------------------|
| 1 | One helper (e.g. `is_advocate_call(record)`) is the only place the hook decides "this record is an Advocate call": `tool_name == "Agent"`, `description` matches `^Advocate \d+:`, and `prompt` starts with `Using the repo, answer alone:`. Checks (3) and (5) both use it | forced choice |
| 2 | The prefix string is one module constant (e.g. `ADVOCATE_PROMPT_PREFIX`), and a test asserts it equals the first line of the fenced block in `skills/resolve-question/references/advocate.md` up to and including the colon, so rewording the template fails a test instead of silently breaking the hook | tie hook to template |
| 3 | Not counted (each a test): description `Advocates summary` with the right prompt; `Advocate 1 keep x` (no colon); `advocate 1: x` (lower case); right description with a prompt not starting with the prefix; right description with the prefix later in the prompt, not at the start | forced choice |
| 4 | Counted (each a test): `Advocate 1: convert recurring.csv?` with the template prompt; the summary truncated at `MAX_SUMMARY_LEN` (invalid JSON) where the prompt prefix is still complete — read through `field()`'s fallback | keep working Debates passing |
| 5 | A truncated summary whose prompt is cut before the prefix is complete is **not** counted (fail closed), and the block reason stays the existing one (`… Advocate \`Agent\` calls … has N`) | safety |
| 6 | Existing fixtures in `.claude/hooks/tests/test_stop_auto_mode_check.py` that use `"prompt": "Using the repo…"` move to the real prefix; every existing test still passes with no assertion weakened | no regression |
| 7 | Docs say the new rule in one place each: `docs/claude-md/tracks.md` `### Debate size by Risk` (the sentence "Each Advocate `Agent` call's `description` starts with `Advocate` …" becomes: description `Advocate <n>:` and prompt starting with the template's first line), the hook's module docstring check (3) line, and one line in `skills/resolve-question/references/advocate.md` saying the Stop hook keys on the first line. `skills/resolve-question/SKILL.md` unchanged | One Term, One Meaning |
| 8 | Mutation control: restoring `.startswith("Advocate")` makes at least one AC 3 test fail | Gate 5 |

---

## Evaluation & Acceptance

### Success Criteria

| # | Given | Expect | How it's checked |
|---|-------|--------|------------------|
| 1 | Medium report with 2 well-formed Advocate records | stop allowed (as today) | existing + AC 4 tests |
| 2 | Medium report with 1 well-formed + 1 `Advocates summary` record | blocked, "has 1" | AC 3 test |
| 3 | High report, 3 records but one lacks the prompt prefix | blocked | AC 3/5 test |
| 4 | Template first line reworded | AC 2 test fails | AC 2 test |

### Verification Command

```bash
python3 -m pytest -q .claude/hooks/tests/test_stop_auto_mode_check.py tests/test_auto_mode.py tests/test_resolve_question.py
```

---

### Evidence (filled by reviewer at Stage 4/5)

> **Moved.** Filled by the reviewer at Stage 4/5 in `tasks/TASK_REVIEW_T222.md`. No UI component: the three UI rows are N/A.

## Demonstration

> **Moved.** See `tasks/TASK_REVIEW_T222.md`.

---

## Approach

**Pattern reference**: the existing `field()` helper and the `\bAdvocate \d+:` regex already used for report lines (`stop_auto_mode_check.py:168`, `:253`).

**Vital slice**: the helper + constant (AC 1–2) and the negative tests (AC 3).
**Cut list**: distinct-number counting; any change to the trace writer (`post_tool_trace.py`); the untagged-window fix (T186).

---

## Edge Case Checklist

- [ ] Summary truncation: `summarize()` keeps `json.dumps(tool_input)[:MAX_SUMMARY_LEN]`; `description` comes before `prompt` in the harness input, so a very long description can push the prompt prefix past the cut → not counted (fail closed, AC 5). `Advocate <n>: <short question>` keeps it short.
- [ ] JSON escapes in the prompt (`\n` after the prefix) must not break the prefix match through `field()`'s fallback.
- [ ] Leading whitespace in the prompt: not counted (the template has none); state this in the test name.

---

## Files to Change (Predicted)

| File | Change |
|------|--------|
| `.claude/hooks/stop_auto_mode_check.py` | helper + constant; checks (3)/(5) use it; docstring line |
| `.claude/hooks/tests/test_stop_auto_mode_check.py` | fixtures to real prefix; new tests AC 2–5, 8 |
| `docs/claude-md/tracks.md` | one sentence in `### Debate size by Risk` |
| `skills/resolve-question/references/advocate.md` | one line: the Stop hook keys on the first line |
| `tests/test_auto_mode.py` | only if a pinned sentence of `tracks.md` moves (add a T222 comment) |

## Files Must NOT Touch

| File | Reason |
|------|--------|
| `skills/resolve-question/SKILL.md` | byte budget; out of scope |
| `.claude/hooks/post_tool_trace.py`, `.claude/settings.json` | out of scope |
| `PROJECT_KANBAN.md`, `memory/` | Supervisor-only |

---

## Test Plan

Red first: add the AC 2–5 tests, run them against the unchanged hook, paste the failures into the review file's BEFORE. Then change the hook and docs, run the Verification Command, then `python3 -m pytest .claude/hooks/tests/ tests/ -q`; paste outputs.

---

## Questions Log

---

## Completion Checklist

- [ ] Implementation done
- [ ] Tests written AND pass — output pasted into `tasks/TASK_REVIEW_T222.md`'s Evidence table (Hard-Stop Gate 5)
- [ ] Supervisor notified: task ready for Stage 4 review (code-review + security-review, Risk High)
