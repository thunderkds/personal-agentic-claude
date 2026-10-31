# TASK_GUIDE — T223: Project readiness — `PROJECT_SPEC.md` `## Readiness` section, a high-visibility spawn warning while it is incomplete, and no stage skipped as an auto decision
**Date**: 2026-10-31
**Complexity Level**: C2
**Risk Level**: High (hub file: `.claude/hooks/pre_agent_validate_guide.py` runs before every `Agent` spawn in every installed project; doctrine change to stage order)
**Priority**: P1
**Assigned agent**: common-infrastructure
**Agent guide**: `agents/common-infrastructure.md`

---

## Mandatory Startup (Do Not Skip)

1. Read `PROJECT_SPEC.md`
2. Read the memory slice in your spawn prompt (`<!-- memory-slice -->`). Read `memory/MEMORY.md` in full only if your work reaches what the slice does not cover
3. Read this file completely
4. Read `agents/common-infrastructure.md`
5. Read `.claude/hooks/pre_agent_validate_guide.py` in full and `.claude/hooks/tests/test_pre_agent_validate_guide.py`
6. Read `docs/claude-md/phase0-project-initiation.md`, `docs/claude-md/pipeline-stages.md` (Stage 0.5, Stage 1, Stage 2), `docs/claude-md/tracks.md` (`## Announcement`, `## Auto mode` table rows 1–4, `### Stops that stay`, the final report fields), and `templates/PROJECT_SPEC_template.md`

---

## Requirement (Pillar 1 — Adapt the requirement)

User, 2026-10-31: "when I boost you to the new project, just have somes docs, do not enough the architecture, flow, diagram, techstacks, but you still push to work on coding, how can it occurred, let investigate" → "you can see from the idea-radar repos" → "yes, let go".

Investigation (idea-radar session `38a748fd`, 2026-10-31): the user's first message was "I created the linear already, spec, and everything about requirement, let work on that to check evaluate and start the jobs parallel, [auto]". Within 5 minutes the Supervisor wrote `PROJECT_SPEC.md` (Architecture Summary: 3 sentences pointing at `docs/SPEC.md`), the board and the T001 guide, and spawned T001. Phase 0, Stage 0.5 and `map-codebase` did not run; auto decision 4 logged "Stage 0.5 grilling/brainstorming answered from the locked spec, not re-run as sessions — FACT: `docs/ISSUES.md`:3" (that line is about acceptance criteria, not architecture). A later gap analysis (`docs/analysis/2026-10-31-gaps.md`, after T001 was coded) found architecture holes, worst A1 "Nothing selects lowkey candidates".

Kit causes: (1) Phase 0 runs "new project only" (`tracks.md` auto table row 1) and nothing defines "new project" or "stage done" (`tracks.md:48` "from the first stage not yet done"); scaffold code + a spec file read as "not new". (2) Auto mode let a stage be skipped as a logged decision. (3) Nothing asks for a tech stack, main flow or diagram beyond the template's "2–3 sentences". (4) No hook looks at stage order.

User choices, 2026-10-31 (forced choice):
- Hook action: **"high warning with remind for the risk"** — a high-visibility warning, NOT a block.
- Proof: **"Readiness section"** — `PROJECT_SPEC.md` gets a `## Readiness` section with fixed lines; the hook checks each named file exists.
- Existing projects: **"Check them too"** — no grandfathering; an installed project without the section gets the warning on its next spawn.

**Restated intent**:
> A project records in one place, `PROJECT_SPEC.md` `## Readiness`, the files that prove it is ready to code: requirements, the brainstorming direction, the codebase map, the tech stack, a main-flow file with a Mermaid diagram, and the user's approval. While that section is missing or incomplete, every `Agent` spawn that names a task still goes ahead, but the spawn hook prints a loud warning that names each missing line and the risk (coding on an unchecked design). The doctrine defines "stage done" by these lines, so scaffold code or a spec file never makes a project "not new", and auto mode may not skip Stage 0.5 or Stage 1 as a decision: it runs them with its existing auto rules and repeats any readiness warning in its final report.

**Out of scope**:
- Blocking a spawn on readiness (user chose warn)
- Any change to `AGENTS.md` (0 lines of headroom, cap 196 — `memory/learnings.md`)
- `stop_auto_mode_check.py` (the Stop hook) — no new check there
- Filling this kit repo's own or idea-radar's `## Readiness` section (Supervisor does it after merge)
- Judging diagram quality; the hook checks presence only

**Requirement Refs**: user messages + forced choices above; investigation of idea-radar session `38a748fd`

### Requirement Fidelity Gate

- [x] Restated intent confirmed — the user picked the three options 2026-10-31
- [x] Domain terms align — Auto mode, Final report, Track (`PROJECT_SPEC.md` glossary); new term **Readiness section** (add a glossary row)
- [x] Every Acceptance Criterion traces to a line in the Requirement
- [x] All Requirement Refs exist and are covered

---

## Dependencies & Reachability

**Depends on**: none
**Entry point**: `.claude/hooks/pre_agent_validate_guide.py` `main()` — the advisory warnings path

---

## Acceptance Criteria

| # | Criterion (testable) | Traces to requirement |
|---|----------------------|-----------------------|
| 1 | `templates/PROJECT_SPEC_template.md` gains a `## Readiness` section with exactly these lines (placeholders in `[...]`): `- **Requirements**: [path, e.g. PRD.md or a stand-in like docs/SPEC.md]`, `- **Direction**: [path to the approved brainstorming log]`, `- **Codebase map**: [memory/codebase-map.md, or "none — blank scaffold"]`, `- **Tech stack**: [languages, frameworks, storage, hosting]`, `- **Main flow**: [path to a file that holds a Mermaid diagram of the main data/user flow]`, `- **Approved by**: [user YYYY-MM-DD]`, plus an optional `- **Waived**: [user YYYY-MM-DD — reason]` line explained in one sentence | Readiness section |
| 2 | One helper (e.g. `readiness_gaps(root)`) returns the list of gaps: no `PROJECT_SPEC.md`; no `## Readiness` section; a line missing, empty or still a `[...]` placeholder; a path line whose file does not exist (relative to the project root); a `Main flow` file with no ```` ```mermaid ```` block; `Approved by` not matching `user \d{4}-\d{2}-\d{2}`. `Codebase map: none — blank scaffold` is valid. A valid `Waived` line returns no gaps | Readiness section |
| 3 | On an `Agent` spawn that names a task (the existing structural task-ID path), when gaps exist the hook allows the spawn and emits a warning in `additionalContext` AND on stderr that starts with `⚠ HIGH RISK — project readiness incomplete:`, names every gap, and says the risk in one sentence (agents will code on a design nobody checked; architecture gaps found later cost rework) and what to do (fill `PROJECT_SPEC.md` `## Readiness`: run Phase 0 / Stage 0.5 / Stage 1, or ask the user for a `Waived` line). It never sets `"decision": "block"` | "high warning with remind for the risk" |
| 4 | The readiness warning is shown together with the existing advisory warnings (dependency, Demonstration, memory slice, startup reads) and does not replace them; the existing missing-guide and incomplete-guide blocks keep priority and are unchanged. A crash in the readiness check fails open (no warning, spawn allowed) | no regression; safety |
| 5 | A spawn with no structural task ID gets no readiness warning (unchanged path) | scope |
| 6 | Doctrine: `docs/claude-md/phase0-project-initiation.md` and `docs/claude-md/pipeline-stages.md` say a stage counts as done only when its `## Readiness` line is filled (Phase 0 → `Requirements` + `Approved by`; Stage 0.5 → `Direction`; Stage 1 → `Codebase map`, `Tech stack`; Stage 2 → `Main flow` before the first spawn). Scaffold code or an existing spec file does not make Phase 0 done: a stand-in spec is named on the `Requirements` line and still goes through Stage 0.5a grilling. `tracks.md:48` ("from the first stage not yet done") points at this rule. Auto table row 1's "new project only" becomes "while `Requirements` or `Approved by` is not filled" | stage-done definition |
| 7 | Auto mode (`docs/claude-md/tracks.md`): a new sentence says Stage 0.5 and Stage 1 are never skipped as an auto decision; they run with the auto rules of the table (rows 1–10). `Approved by` is never filled by the Supervisor in auto mode (it stays empty, so the warning fires). When the readiness warning fired in the run, the final report's `Not done:` line names it: `readiness incomplete: <gaps> (yours)`. Existing pinned sentences in `tests/test_auto_mode.py` move only with a T223 comment | auto decision loophole |
| 8 | `PROJECT_SPEC.md` glossary gains one row **Readiness section** | One Term, One Meaning |
| 9 | Tests in `.claude/hooks/tests/test_pre_agent_validate_guide.py` (or a new `test_readiness_warning.py`): no spec → warning; spec without section → warning; each gap kind → named; complete section with real files and a Mermaid block → no readiness warning; `Waived` → no warning; `Codebase map: none — blank scaffold` → valid; output never contains `"decision": "block"` for readiness; a forced exception in the helper → no warning, exit 0. Mutation control: making the helper return `[]` always fails at least one test | Gate 5 |
| 10 | Negative: `AGENTS.md`, `stop_auto_mode_check.py`, `.claude/settings.json` unchanged; whole suite passes (`python3 -m pytest -q .claude/hooks/tests/ tests/`) — note that this kit repo's own `PROJECT_SPEC.md` has no `## Readiness` yet, so its own spawns will warn; tests must use temp project roots, not the repo's real spec | out of scope |

---

## Evaluation & Acceptance

### Success Criteria

| # | Given | Expect | How it's checked |
|---|-------|--------|------------------|
| 1 | idea-radar shape: scaffold code, `docs/SPEC.md`, `PROJECT_SPEC.md` with no `## Readiness`, spawn naming `T001` | spawn allowed; `⚠ HIGH RISK — project readiness incomplete:` names the missing section | hook test with a temp root |
| 2 | Complete section, all files present, `Main flow` has a Mermaid block | no readiness warning | hook test |
| 3 | `Main flow` file without Mermaid | warning names the Main flow gap | hook test |
| 4 | `Waived: user 2026-10-31 — prototype` | no readiness warning | hook test |
| 5 | Doctrine text | stage-done rule + auto no-skip sentence present | `tests/test_auto_mode.py` / a doctrine test |

### Verification Command

```bash
python3 -m pytest -q .claude/hooks/tests/test_pre_agent_validate_guide.py tests/test_auto_mode.py
```

---

### Evidence (filled by reviewer at Stage 4/5)

> **Moved.** Filled by the reviewer at Stage 4/5 in `tasks/TASK_REVIEW_T223.md`. No UI component: the three UI rows are N/A.

## Demonstration

> **Moved.** See `tasks/TASK_REVIEW_T223.md`. BEFORE: run the hook on a temp project root shaped like idea-radar (no `## Readiness`) with a spawn prompt naming a task, and paste its output (expected: no readiness warning today).

---

## Approach

**Pattern reference**: the existing advisory checks in `pre_agent_validate_guide.py` (`check_memory_slice_warning`, `check_startup_reads_warning`) — same fail-open try/except, same `additionalContext` + stderr output; `ROOT` already resolves the project root from the hook path, so the check works in installed projects.

**Vital slice**: the template section (AC 1), the helper + warning (AC 2–4), the auto no-skip sentence (AC 7).
**Cut list**: blocking; Stop-hook check; diagram quality; filling real projects' sections; an `/init-readiness` skill.

---

## Edge Case Checklist

- [ ] `PROJECT_SPEC.md` path lines may be wrapped in backticks — strip them before the existence check.
- [ ] A path that points outside the project root (`../`, absolute) — treat as a gap (do not read outside the root).
- [ ] A Mermaid block in a file under `docs/` that is large — read only enough to find ```` ```mermaid ````.
- [ ] Warning must be one block, not repeated once per task ID in a multi-task prompt.
- [ ] `PROJECT_SPEC.md` placeholders `[...]` count as empty.

---

## Files to Change (Predicted)

| File | Change |
|------|--------|
| `.claude/hooks/pre_agent_validate_guide.py` | helper + warning; docstring paragraph |
| `.claude/hooks/tests/test_pre_agent_validate_guide.py` (or new test file) | AC 9 tests |
| `templates/PROJECT_SPEC_template.md` | `## Readiness` section |
| `docs/claude-md/phase0-project-initiation.md`, `docs/claude-md/pipeline-stages.md` | stage-done rule |
| `docs/claude-md/tracks.md` | line 48 pointer, auto row 1 wording, no-skip sentence, `Not done:` readiness item |
| `PROJECT_SPEC.md` | glossary row only |
| `tests/test_auto_mode.py` | only if a pinned sentence moves (T223 comment) |

## Files Must NOT Touch

| File | Reason |
|------|--------|
| `AGENTS.md` | 0 lines headroom; out of scope |
| `.claude/hooks/stop_auto_mode_check.py`, `.claude/settings.json` | out of scope |
| `PROJECT_KANBAN.md`, `memory/` | Supervisor-only |

---

## Test Plan

Red first: add the AC 9 tests, run them against the unchanged hook, paste the failures into the review file's BEFORE section. Then change the hook, template and docs, run the Verification Command, then `python3 -m pytest -q .claude/hooks/tests/ tests/`; paste outputs.

---

## Questions Log

---

## Completion Checklist

- [ ] Implementation done
- [ ] Tests written AND pass — output pasted into `tasks/TASK_REVIEW_T223.md`'s Evidence table (Hard-Stop Gate 5)
- [ ] Supervisor notified: task ready for Stage 4 review (code-review + security-review, Risk High)
