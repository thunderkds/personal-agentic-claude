# TASK_GUIDE — T042: Fix post_write_register_task.py — Complexity/Risk/Priority silently default
**Date**: 2026-07-21
**Complexity Level**: C1
**Risk Level**: Medium
**Priority**: P0
**Assigned agent**: Common-Infrastructure-Agent
**Agent guide**: `.claude/agents/common-infrastructure.md`

---

## Mandatory Startup (Do Not Skip)

1. Read `PROJECT_SPEC.md`
2. Read `memory/MEMORY.md` (pasted into your spawn prompt — do not re-read if present)
3. Read this file completely
4. Read `.claude/agents/common-infrastructure.md`
5. Read `.claude/hooks/post_write_register_task.py` in full, and `templates/TASK_GUIDE_template.md` lines 1–8

---

## Requirement (Pillar 1 — Adapt the requirement)

Discovered 2026-07-21 while filing T039/T041: the PostToolUse hook that auto-registers new
TASK_GUIDE files into `PROJECT_KANBAN.md` extracts three fields with regexes that **cannot match
the format its own template produces**, and silently substitutes defaults instead of failing.

| Line | Regex | Template writes | Result |
|---|---|---|---|
| `:51` | `Complexity[:\s]+(C[0-3])` | `**Complexity Level**: C2` | no match → defaults `C1` |
| `:52` | `Risk[:\s]+(Low\|Med(?:ium)?\|High)` | `**Risk Level**: Medium` | no match → defaults `Low` |
| `:53` | `Priority[:\s]+(P[0-2])` | `**Priority**: P1` | no match → defaults `P1` |

`[:\s]+` cannot cross the intervening ` Level**: ` (or `**: `). Every guide ever auto-registered
received default metadata that reads as if it were extracted.

**Restated intent**:
> When a TASK_GUIDE is written, the Kanban row must show that guide's real Complexity, Risk, and
> Priority. When a field genuinely cannot be read, the row must say so visibly rather than invent a
> plausible value.

**Why P0**: Risk Level gates `security-review` (Medium/High) and Complexity carries the Hard-Stop
Gate 2 floor. A guide correctly floored at C2/Medium appears on the board as C1/Low, so the board —
the artifact the Supervisor reads to decide what review a task needs — understates the required
process. This is the fourth defect in this family (T018 title regex, T022 task-ID extraction, T024
agent-field regex).

**Out of scope**:
- Rewriting the hook's structure, the Kanban format, or the TASK_GUIDE template
- The other hooks in `.claude/hooks/`
- Retro-editing `### Done` rows (historical record; leave them)

**Requirement Refs**: no `PRD.md`. Traceability: defect found by Supervisor inspection 2026-07-21;
**LR-0002** (rules that appear enforced but silently are not are a recurring systemic failure).

### Requirement Fidelity Gate (sign off BEFORE implementation)

- [x] Defect reproduced by Supervisor: T039/T041 guides (both `C2`/`Medium`) registered as `C1`/`Low`
- [x] Root cause confirmed by reading `:51-53` against `templates/TASK_GUIDE_template.md:3-5`
- [x] Every Acceptance Criterion traces to the Requirement

---

## Dependencies & Reachability

**Depends on**: `None`

**Entry point**: `post_write_register_task.py`
> The hook file itself; invoked by the PostToolUse `Write` matcher in `.claude/settings.json`.

---

## Acceptance Criteria

| # | Criterion (testable) | Traces to |
|---|----------------------|-----------|
| 1 | A guide containing `**Complexity Level**: C2` registers as `C2` | `:51` defect |
| 2 | A guide containing `**Risk Level**: Medium` registers as Medium (in whichever spelling AC5 fixes as canonical) | `:52` defect |
| 3 | A guide containing `**Priority**: P0` registers as `P0` | `:53` defect |
| 4 | A guide with a genuinely absent field registers that field as `?` — never a plausible-looking default | "say so visibly" |
| 5 | Kanban risk spelling is consistent: the hook's `Med` normalisation and the hand-written `Medium` rows must agree on one form, applied in both the hook and the currently-open Todo rows | consistency |
| 6 | **Negative**: the existing duplicate guard still short-circuits when the task ID is already present | scope guard |
| 7 | **Negative**: title and agent extraction (`:49`, `:50`) still behave exactly as before | scope guard — T018/T024 fixed these; do not regress them |
| 8 | Currently-open `### Todo` rows show metadata matching their guides | "board must be true now, not only for future tasks" |

---

## Evaluation & Acceptance

### Success Criteria (observable, pass/fail)

| # | Given (input/state) | Expect (output/behavior) | How it's checked |
|---|---------------------|--------------------------|------------------|
| 1 | Synthetic guide, template format, C2/High/P0 | row reads `C2`, High, `P0` | automated test |
| 2 | Synthetic guide with the Complexity line deleted | row reads `?`, not `C1` | automated test (negative) |
| 3 | Synthetic guide whose ID already exists in the Kanban | hook exits 0, Kanban unchanged | automated test (negative) |
| 4 | Bare-format guide (`Complexity: C3`, no `Level`/asterisks) | still reads `C3` — the fix must widen the pattern, not swap one rigid format for another | automated test |

### Verification Command (exact, runnable)

```bash
python3 -m pytest .claude/hooks/tests/ -q
```

### Evidence (filled by reviewer at Stage 4/5)

| Check | Result | Notes / output snippet |
|-------|--------|------------------------|
| **New test(s) cover Acceptance Criteria (file paths pasted)** | ☑ pass | `.claude/hooks/tests/test_post_write_register_task_metadata.py` (311 lines, 7 tests, new in commit `e35f987`). Re-run independently by the reviewer: `31 passed in 0.24s` (7 new + 24 pre-existing) |
| Verification command run | ☑ pass | `python3 -m pytest .claude/hooks/tests/ -q` → `...............................  [100%]` / `31 passed in 0.24s` |
| Negative cases hold | ☑ pass | AC4 `?` fallback (`test_missing_field_registers_as_visible_unknown_not_a_default`, asserts `"C1" not in row`); AC6 duplicate guard (`test_duplicate_task_id_is_a_no_op`, byte-compares Kanban before/after + `count("**T900**") == 1`); AC7 title/agent regression (`test_title_and_agent_extraction_unaffected_by_the_fix`); bare-format AC4 anti-regression (`test_bare_format_still_matches_widened_pattern`, `Complexity: C3`); adversarial prose (`test_regex_widening_does_not_match_prose_mentions_elsewhere`) |
| verify | ☑ pass | End-to-end run of the committed hook against **real** guides + a real copy of the live Kanban (not synthetic fixtures): fed `TASK_GUIDE_T039.md` and `TASK_GUIDE_T041.md` through `post_write_register_task.py` at `e35f987`, both produced `C2 \| Risk: Medium \| P1`, matching their guide headers exactly — the same values the pre-fix hook silently rendered as `C1 \| Risk: Low \| P1`. Confirmed working — pass |
| Review scope bounded to the change's blast radius | ☑ pass | Reviewed: the 2 changed files. Consumers traced by grep — `.claude/settings.json` (PostToolUse `Write` matcher) is the only registrant, and no code parses the hook's Kanban output. Verified the `Med`→`Medium` label change breaks nothing downstream: the only other `"Med"` reference in `.claude/hooks`, `.claude/skills`, `scripts`, `templates` was the hook's own normalizer line, which this diff replaces. Repo not re-read beyond that set |
| Full smoke suite still green (no regression) | ☑ pass | `bash scripts/smoke-install.sh` → `smoke-install.sh: PASS` |
| **UI: Visual regression** | ☐ N/A | Hook script, no UI component |
| **UI: Design-system compliance** | ☐ N/A | Hook script, no UI component |
| **UI: Responsiveness** | ☐ N/A | Hook script, no UI component |

---

## Approach

Widen the three patterns to tolerate the optional label word and markdown emphasis between the field
name and its value — e.g. allow an optional ` Level`, optional `*`/`_`, and the colon anywhere in
between — rather than hard-coding the current template's exact punctuation. AC4 exists specifically
to stop the fix from being "match `**Complexity Level**:` instead", which would break the moment
someone writes the field slightly differently. Test both spellings.

Change the three defaults from plausible values (`C1`, `Low`, `P1`) to `?`. `extract()` already
supports a `?` default and the title/agent fields legitimately keep real defaults — a wrong
complexity is worse than a visibly missing one, because a missing one prompts a human to look.

The existing duplicate guard means the hook cannot repair rows it previously wrote, so the fix alone
does not correct the board. Reconcile the currently-open `### Todo` rows against their guides as
part of this task (AC8). Leave `### Done` rows alone — they are a historical record and several were
hand-corrected at close time.

Follow the existing test conventions in `.claude/hooks/tests/`; read that directory before adding
files. Drive the hook the way the harness does — feed the PostToolUse event JSON on stdin — rather
than importing and calling internals, so the test exercises the real path.

---

## Edge Case Checklist

- [ ] Do not regress `:49` title extraction or `:50` agent extraction — both are prior bug fixes
      (T018, T024) with their own tests. Run the existing suite before and after.
- [ ] `risk` normalisation (`Med` vs `Medium`) currently rewrites the extracted value; AC5 requires
      one canonical form — pick it, apply it in the hook, and match the open Todo rows to it.
- [ ] The hook must still `sys.exit(0)` on every failure path. A hook that raises fires on **every
      Write in the repo** — never let an exception escape.
- [ ] Guides in `### Blocked` or `### In Progress` are out of AC8's scope; only `### Todo`.
- [ ] Regex must stay anchored enough not to match the word "Complexity" inside prose elsewhere in a
      guide (this file's own Requirement table contains the literal strings `Complexity[:\s]+` and
      `**Complexity Level**: C2` — a naive widening will match them).
- [ ] The step-limit hook false-positives on tool inputs mentioning old task IDs
      (`memory/learnings.md`); this guide names several. Bracket-glob the ID if it fires.

---

## Files to Change (Predicted)

| File | Change |
|------|--------|
| `.claude/hooks/post_write_register_task.py` | Widen `:51-53` patterns; defaults → `?`; settle risk spelling |
| `.claude/hooks/tests/` | **New** test file covering AC1–AC7 |
| `PROJECT_KANBAN.md` | Reconcile open `### Todo` rows to match their guides (AC8) |

## Files Must NOT Touch

| File | Reason |
|------|--------|
| `templates/TASK_GUIDE_template.md` | The template is correct and human-facing; the hook is what must adapt |
| `.claude/hooks/post_tool_trace.py`, `pre_agent_validate_guide.py`, others | Separate hooks; T022/T024 territory |
| `.claude/settings.json` | Hook registration is already correct |
| `CLAUDE.md`, `.claude/agents/general-agent-template.md` | Owned by T039 / T041 this cycle |
| `PROJECT_KANBAN.md` `### Done` rows | Historical record |

---

## Test Plan

1. **Red**: add tests asserting C2/Medium/P0 extraction from a template-format guide — they fail
   against current `main`, reproducing the defect.
2. **Green**: widen the patterns; tests pass.
3. **Negative controls**, each with pasted output: missing field → `?`; duplicate ID → no-op;
   bare `Complexity: C3` format → `C3`.
4. **Regression**: full existing `.claude/hooks/tests/` suite green (guards AC7).
5. **AC8**: after the hook is fixed, diff each open Todo row against its guide; paste the before/after.
6. Paste real output into every Evidence row — never a claim of output.

---

## Completion Checklist

- [ ] Implementation done
- [ ] Self-review: `Skill({ skill: "code-review" })` run
- [ ] Security review: `Skill({ skill: "security-review" })` run — **mandatory, Risk=Medium**
- [ ] Tests written AND pass — output pasted into Evidence table (Hard-Stop Gate 5)
- [ ] `Skill({ skill: "verify" })` run
- [ ] Report to the Supervisor for `memory/`: this is the 4th regex-extraction defect in these hooks — flag whether a shared field-parsing helper would prevent a 5th (do not build it in this task; do not write memory yourself)
- [ ] Supervisor notified: task ready for Stage 4 review
