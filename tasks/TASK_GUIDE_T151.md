# TASK_GUIDE — T151: The docs and site describe what T144, T145, T148 and T149 changed
**Date**: 2026-10-17
**Complexity Level**: C1
**Risk Level**: Low
**Priority**: P1
**Assigned agent**: common-infrastructure
**Agent guide**: `agents/common-infrastructure.md`

---

## Mandatory Startup (Do Not Skip)

Before writing any code:
1. Read `PROJECT_SPEC.md`
2. Read the memory slice in your spawn prompt (`<!-- memory-slice -->`). Read `memory/MEMORY.md` in full only if your work reaches a file, hook, skill or decision the slice does not cover
3. Read this file completely
4. Read `agents/common-infrastructure.md`
5. Note the **Complexity Level** above and apply the matching process from the Complexity matrix in your role guide
6. C1 — skip `memory/codebase-map.md`

---

## Requirement (Pillar 1 — Adapt the requirement)

The user asked on 2026-10-17, after T144/T145/T148/T149 merged into `feat/t144-t145-t148-t149`: *"did you update the docs following the update"* — then *"go ahead"* with a docs task. Those four tasks changed only their SKILL.md files, the `PROJECT_SPEC.md` glossary and `templates/RUNBOOK_template.md`; the user-facing docs still describe the old behavior.

**Verified state (2026-10-17, on `feat/t144-t145-t148-t149`)**:
- `docs/claude-md/pipeline-stages.md:159` — "Memory injection" describes the slice as `memory/MEMORY.md` index lines only; T145 added `decisions.md` entries matched on their `**Files**:` line, under `### From decisions.md`.
- `docs/claude-md/pipeline-stages.md:171-175` — Stage 4 code-review step does not mention T144's `scripts/lane_check.py <guide> <base>...HEAD` warn-only line.
- `docs/claude-md/pipeline-stages.md:231-235` — `ship` step does not mention T149's fifth GO condition (human approval of the exact version @ commit, recorded in the Release Log) or the smoke-test-before-deploy rule.
- `site/index.html:531` — the `post_tool_trace.py` hook row says only "appends every tool call"; T148 added the hash chain, the anchor under `~/.claude/harness-anchors/`, and `scripts/verify_trace.py`.
- `site/index.html:548` and `:655` — memory-slice rows: same gap as line 159.
- `site/index.html:371-373` and `:516-518` — say setup/update never touch "your own permissions"; since T148, `lib/merge-settings.py` appends the kit's `permissions.deny` entries (add-only; your entries kept; kit allow/ask never copied).

Source of truth for every fact: `memory/decisions.md` entry "T144/T145/T148/T149 merged …" (2026-10-17) and the SKILL.md / script docstrings on this branch.

**Restated intent**:
> Every place listed above says what the code on this branch now does, in the page's existing voice and structure, and a drift test fails if those mentions disappear.

**Out of scope**:
- Any behavior change to scripts, hooks or skills
- New site sections, nav entries, styling, or layout
- README.md, CLAUDE.md, CLAUDE_LEGACY.md (checked: nothing there describes the changed behavior)
- Documenting T147 (Blocked) or T150 (another session's task)

**Requirement Refs**: no `PRD.md` — traces to the user's request above and `memory/decisions.md` (2026-10-17 entry).

### Requirement Fidelity Gate (sign off BEFORE implementation)

- [x] Restated intent confirmed to match the user's request (Supervisor, 2026-10-17 — user said "go ahead" to this exact list)
- [x] Domain terms align with `PROJECT_SPEC.md` glossary (Lane, Anchor)
- [x] Every Acceptance Criterion below traces to a line in the Requirement
- [x] Requirement Refs — N/A, traced above

---

## Dependencies & Reachability

**Depends on**: T144, T145, T148, T149 (all merged on this branch)
**Entry point**: Standalone — N/A (docs)

---

## Acceptance Criteria

| # | Criterion (testable) | Traces to requirement |
|---|----------------------|-----------------------|
| 1 | `pipeline-stages.md` Memory injection says the slice also carries `decisions.md` entries whose `**Files**:` line names the task's files (T145) | :159 |
| 2 | `pipeline-stages.md` Stage 4 code-review names `scripts/lane_check.py` with a **three-dot** range and says it warns, never blocks (T144) | :171-175 |
| 3 | `pipeline-stages.md` `ship` step names the human approval of the exact version @ commit recorded in the Release Log, and the smoke test defined before the deploy; "never auto-deploys" stays (T149) | :231-235 |
| 4 | `site/index.html` hook row for `post_tool_trace.py` mentions the hash chain, the anchor outside the repo, and `scripts/verify_trace.py` (T148) | :531 |
| 5 | `site/index.html` memory-slice rows (:548, :655) mention `decisions.md` entries (T145) | :548, :655 |
| 6 | `site/index.html` :371-373 and :516-518 no longer claim permissions are never touched; they say the kit's deny rules are appended and the user's own entries kept (T148) | :371, :516 |
| 7 | New drift test(s) fail if any of AC1–AC6's mentions is removed; the whole existing `tests/test_site_content.py` stays green | Hard-Stop Gate 5 |

---

## Evaluation & Acceptance

### Success Criteria (observable, pass/fail)

| # | Given (input/state) | Expect (output/behavior) | How it's checked |
|---|---------------------|--------------------------|------------------|
| 1 | Edited docs | AC1–AC6 mentions present | new pytest |
| 2 | Existing site tests | still pass | `tests/test_site_content.py` |
| 3 | **Mutation control**: delete the `verify_trace.py` mention from the hook row | the new test goes RED | implementer runs, then restores |
| 4 | Every fact stated | matches the code/docstring on this branch (no invented flags, numbers or paths) | Supervisor review |

### Verification Command (exact, runnable)

```bash
python3 -m pytest tests/test_docs_t151.py tests/test_site_content.py -q && python3 -m pytest tests/ .claude/hooks/tests/ -q
```

### Evidence

> **Moved.** Filled by the reviewer at Stage 4/5 in `tasks/TASK_REVIEW_T151.md`.

---

## Demonstration

> **Moved.** See `tasks/TASK_REVIEW_T151.md`. BEFORE = the verbatim current text of each passage listed in the Requirement.

---

## UI / Design Acceptance Criteria

Text-only edits inside existing paragraphs, list items and table cells of `site/index.html`: no new elements, classes, styles or sections. The three UI Evidence rows are ☐ N/A with that justification, unless the edit adds markup beyond inline `<code>`/`<strong>` — then they apply.

---

## Approach

**Pattern reference**: `tests/test_site_content.py` (substring/drift tests over `site/index.html`).
**Vital slice**: the six passages above, one or two sentences each, matching each page's voice.
**Cut list**:
- Documenting `verify_trace.py`'s full verdict table on the site (the script's docstring owns it)
- A site section for the lane check (one sentence in the existing hook/skill text is enough)

---

## Edge Case Checklist

- [ ] HTML escaping: `<task>` and `<version> @ <commit>` written as `&lt;…&gt;` in `site/index.html`
- [ ] The memory cap test (`test_memory_cap_matches_enforced_budget`) still matches — don't change the 42,000 number
- [ ] No claim that the merge gate uses the trace chain (it doesn't yet)

---

## Files to Change (Predicted)

| File | Change |
|------|--------|
| `docs/claude-md/pipeline-stages.md` | three passages (AC1–AC3) |
| `site/index.html` | five passages (AC4–AC6) |
| `tests/test_docs_t151.py` | new drift tests |

## Files Must NOT Touch

| File | Reason |
|------|--------|
| `scripts/`, `.claude/hooks/`, `skills/`, `lib/` | docs only |
| `README.md`, `CLAUDE.md`, `CLAUDE_LEGACY.md` | out of scope |
| `memory/` | Supervisor-only |

---

## Test Plan

Substring drift tests per AC; existing site suite; full suite once.

---

## Completion Checklist

- [ ] Implementation done
- [ ] Self-review: `Skill({ skill: "code-review" })` run
- [ ] Security review: N/A (Low risk)
- [ ] Tests written AND pass — output pasted into `tasks/TASK_REVIEW_T151.md` (Hard-Stop Gate 5)
- [ ] `Skill({ skill: "verify" })` run
- [ ] Supervisor notified: task ready for Stage 4 review
