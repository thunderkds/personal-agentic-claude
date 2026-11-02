# TASK_GUIDE — T239: Pipeline becomes Stage 0–5 with no half numbers
**Date**: 2026-11-02
**Complexity Level**: C2
**Risk Level**: Medium
**Priority**: P1
**Assigned agent**: common-infrastructure
**Agent guide**: `agents/common-infrastructure.md`
**Board**: `PROJECT_KANBAN.md`

---

## Mandatory Startup (Do Not Skip)

Before writing any code:
1. Read `PROJECT_SPEC.md`
2. Use the memory slice in your spawn prompt (`<!-- memory-slice -->`). Read `memory/MEMORY.md` in full only if your work reaches a file, hook, skill or decision the slice does not cover
3. Read this file completely
4. Read `agents/common-infrastructure.md`
5. Note the **Complexity Level** above and apply the matching process from its Complexity matrix
6. Read `docs/brainstorming/BRAINSTORMING_LOG_naming.md` (`## Design Review of the Merge`), `docs/claude-md/pipeline-stages.md`, `docs/claude-md/phase0-project-initiation.md` and `docs/claude-md/tracks.md` `## Auto mode`

---

## Requirement (Pillar 1 — Adapt the requirement)

User, 2026-11-02, verbatim: "should we merge the 0.5 and 1.5 stage, the .5 look does not professional as is"; then chose "Stage 0–5"; then, on the design review: "go" (the team stop is conditional).

**Restated intent**:
> The pipeline reads Stage 0 to Stage 5, with no half numbers. Stage 0 Define holds Requirements, Grilling and Direction, in that order, each with its stop. Stage 1 Set up holds Environment and Agent team. Stages 2–5 keep their numbers and meaning. Every stop stays, except that the team stop now fires only when a new role is proposed.

**Supervisor design decisions** (binding):
- **D1 — Mapping.** Phase 0 → Stage 0 step Requirements. 0.5a → step Grilling. 0.5b → step Direction. Stage 1 → Stage 1 step Environment. 1.5 → Stage 1 step Agent team. Steps have names, not numbers. `docs/claude-md/pipeline-stages.md` holds one mapping note for readers of old tasks.
- **D2 — Stops stay.** Stage 0 keeps its 3 stops in order: the user confirms the requirements, the PRD gate passes, the user picks a direction. Do not flatten them into one step.
- **D3 — Readiness and gates untouched.** `READINESS_LINES` and every check in `pre_agent_validate_guide.py` stay. "Stage done" stays per Readiness line. Only the wording that names stages changes. The merge gate file is not touched.
- **D4 — Auto mode means the same.** Rows of the `## Auto mode` table keep their rules and log labels; only stage names change. Row 11 (team): the base team is logged; no stop existed there.
- **D5 — Conditional team stop.** The Agent team step asks the user only when `craft-agent` proposes a role beyond the base team. With the base team alone, the Supervisor states the team in one line and goes on.
- **D6 — Names.** `docs/claude-md/phase0-project-initiation.md` becomes `docs/claude-md/stage0-define.md`; its "Step 1.5" gets a name. `scripts/token_audit.py` tags become `stage-0` and `stage-1`, and old tags in existing logs stay readable. "5-Stage" titles become "Stage 0–5".
- **D7 — History stays.** `tasks/`, `memory/`, archives, `docs/brainstorming/`, `docs/prd/` and `docs/adr/` are not rewritten.

**Out of scope**: the repo rename (T240), moving `map-codebase`, other half numbers inside one skill's own workflow (for example `code-review` Phase 0.5), any gate logic, `setup.sh`.

**Requirement Refs**: `docs/brainstorming/BRAINSTORMING_LOG_naming.md`.

### Requirement Fidelity Gate (sign off BEFORE implementation)

- [x] Restated intent confirmed to match the user's request (user, 2026-11-02)
- [x] Domain terms align with `PROJECT_SPEC.md` glossary, or this task updates them
- [x] Every Acceptance Criterion below traces to a line in the Requirement or D1–D7
- [x] Requirement Refs filled

---

## Dependencies & Reachability

**Depends on**: T234
**Entry point**: `docs/claude-md/pipeline-stages.md`, `AGENTS.md`

---

## Acceptance Criteria

| # | Criterion (testable) | Traces to |
|---|----------------------|-----------|
| 1 | A test finds no `Stage 0.5`, `Stage 1.5`, `0.5a`, `0.5b` or `Phase 0` outside the D7 paths and the one mapping note, with an anti-vacuity check | D1, D7 |
| 2 | `pipeline-stages.md` has headings Stage 0 to Stage 5, and Stage 0's three steps appear in order with their stops; a test pins it | D1, D2 |
| 3 | `READINESS_LINES` is unchanged, and `git diff` of `pre_agent_validate_guide.py` touches only message text | D3 |
| 4 | Each auto-mode table row keeps its rule and log label; a test compares them with `main` | D4 |
| 5 | The Agent team step states the conditional stop, and `AGENTS.md`, `craft-agent` and `brainstorming` agree | D5 |
| 6 | No link to `phase0-project-initiation.md` is left; `MANIFEST` and installs carry the new file | D6 |
| 7 | `site/index.html` stays at or under 300 words; the `#stages` flow and `docs.html#skills` show Stage 0 to 5 with all 35 skills | regression |
| 8 | Skills stay under the 8192-byte Codex limit | regression |
| 9 | Full suites pass: `python3 -m pytest tests -q`, `python3 -m pytest .claude/hooks/tests -q`, `sh scripts/smoke-install.sh`, `node --test tests/settings_tool/*.mjs`, `node --test tests/site_scrollspy/*.mjs` | regression |

---

## Evaluation & Acceptance (How we know the agent worked correctly)

### Success Criteria (observable, pass/fail)

| # | Given | Expect | How checked |
|---|-------|--------|-------------|
| 1 | a project with an empty Readiness section | a spawn still gets the `⚠ HIGH RISK` warning naming stages by their new names | run the hook on a sample event |
| 2 | both site pages at 1440 and 375 px | stage flow correct, no sideways scroll | headless Chrome, `file://` URLs |

### Verification Command (exact, runnable)

```bash
python3 -m pytest tests/test_stage_names.py tests/test_site_content.py tests/test_site_story.py tests/test_tracks.py tests/test_auto_mode.py -q
```

### Evidence (filled by reviewer at Stage 4/5)

> Filled by the reviewer in `tasks/TASK_REVIEW_T239.md`.

---

## Demonstration

> **Moved.** See `tasks/TASK_REVIEW_T239.md`.

---

## UI / Design Acceptance Criteria

### 1. Visual Regression
| Screen / Component | Method | Expected |
|---|---|---|
| `#stages`, `docs.html#skills`, pipeline strip and diagram | screenshot at 1440 px, before and after | six stages, layout intact |

### 2. Design-System Compliance
| Criterion | Method | Expected |
|---|---|---|
| Colors | existing hex test | tokens only |

### 3. Layout / Responsiveness
| Viewport | Method | Expected |
|---|---|---|
| 1440 / 768 / 375 | `scrollWidth == clientWidth` | no sideways scroll |

---

## Approach

**Pattern reference**: T234's `tests/test_plugin_names.py` for a sweep test with an anti-vacuity check.

**Vital slice**: `pipeline-stages.md`, `AGENTS.md`, the sweep test.
**Cut list**: new step numbering; rewriting history; moving `map-codebase`.

---

## Edge Case Checklist

- [ ] Sentences that say "Stage 0.5 and Stage 1" read correctly after the rename
- [ ] `tests/fixtures/site_story_baseline.json`: changed text is listed with a stated reason, no sentence silently lost
- [ ] `T070_BASELINE_REF` and `tests/test_agents_md_primary.py` follow the T226/T228 pattern
- [ ] `docs/main-flow.md` and `PROJECT_SPEC.md` `## Readiness` note wording
- [ ] Codex rewrite in `lib/harness-fetch.sh` is not affected

---

## Files to Change (Predicted)

| File | Change |
|------|--------|
| `AGENTS.md`, `CLAUDE_LEGACY.md`, `README.md` | stage names |
| `docs/claude-md/pipeline-stages.md`, `tracks.md`, `phase0-project-initiation.md` (renamed) and other `docs/claude-md/*` | stage names, D2, D5 |
| `skills/*/SKILL.md`, `agents/*.md`, `templates/*` | stage names |
| `site/index.html`, `site/docs.html` | stage names and flow |
| `scripts/token_audit.py`, `.claude/hooks/pre_agent_validate_guide.py` | tags, message text |
| `tests/*` | new `tests/test_stage_names.py`; pins follow |

## Files Must NOT Touch

| File | Reason |
|------|--------|
| `.claude/hooks/pre_bash_block_unsafe_merge.py` | gate logic |
| `setup.sh`, `lib/harness-*.sh` | not needed |
| `memory/*`, `PROJECT_KANBAN*.md`, `tasks/` other than this task's files | Supervisor owns them; history stays |

---

## Test Plan

Red first: `tests/test_stage_names.py`. Rename by file group, and run the suites after each group. Then the two Success Criteria runs.

---

## Completion Checklist

- [ ] Implementation done
- [ ] Tests written AND pass — output pasted into `tasks/TASK_REVIEW_T239.md` (Hard-Stop Gate 5)
- [ ] All three UI Evidence rows filled (Hard-Stop Gate 6)
- [ ] Supervisor notified: task ready for Stage 4 review (`code-review`, `security-review`)
