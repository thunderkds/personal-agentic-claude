# TASK_GUIDE — T245: UX review — UX criteria in the guide, a `ux-reviewer` in code-review, screenshots from the frontend agent
**Date**: 2026-11-03
**Complexity Level**: C2
**Risk Level**: Medium
**Priority**: P1
**Assigned agent**: common-infrastructure
**Agent guide**: `agents/common-infrastructure.md`

> Risk Medium: two hub files. `skills/code-review/SKILL.md` runs on every extended-track task, and
> `templates/TASK_GUIDE_template.md` feeds every guide. A hub touch raises Risk a level
> (`docs/claude-md/pipeline-stages.md` Stage 2 item 5). The edit is text only; no hook, no gate change.

---

## Mandatory Startup (Do Not Skip)

Before writing any code:
1. Read `PROJECT_SPEC.md`
2. Read the memory slice in your spawn prompt (`<!-- memory-slice -->`). Read `memory/MEMORY.md` in full only if your work reaches a file, hook, skill or decision the slice does not cover
3. Read this file completely
4. Read `agents/common-infrastructure.md`
5. Note the **Complexity Level** above and apply the matching process from the Complexity matrix in your role guide
6. Read `memory/codebase-map.md` (C2, multi-file)
7. Read `skills/write-better-skill/SKILL.md` — the craft reference for any `SKILL.md` or skill reference file here
8. Read `tasks/TASK_GUIDE_T192.md` `## Requirement` — T192 (Todo) owns the easy-ui `ui-test` skill and the three UI design rows; this task must not overlap it

---

## Requirement (Pillar 1 — Adapt the requirement)

User, 2026-11-03: *"the frontend agent do not have the UX skill, so it can not evaluate the change is
good or not following the requirement, let investigate and let me know"*. The Supervisor's
investigation found three gaps:
1. `agents/frontend.md` has no UX skill or checklist line, and no instruction to look at its own UI
   (its tools are `Read, Write, Edit, Bash, Glob, Grep`; Pillar 3 says "confirm the UI behaves in the
   browser" with no method).
2. `templates/TASK_GUIDE_template.md` `## UI / Design Acceptance Criteria` checks conformance only
   (visual regression, design tokens, responsiveness). No row names the user's goal, the flow steps,
   the states, or a pass condition traced to a `PRD.md` user story.
3. `skills/code-review/SKILL.md` has no UI/UX reviewer persona; `agents/qa.md` has nothing UI-specific.

The Supervisor proposed three fixes; the user replied *"yes, open the task [auto]"*.

**Restated intent**:
> A UI task's guide states what "good for the user" means, in rows an observer can check on a
> screenshot or a run. At Stage 4, a reviewer that is not the implementer looks at real screenshots
> and judges each row pass or fail. The frontend agent takes and checks the same screenshots before
> it reports ready, so most UX gaps are fixed before review.

**Out of scope** (what this task explicitly does NOT do):
- easy-ui sessions and the three existing UI design rows — T192 owns them. The `ux-reviewer` may name easy-ui as one screenshot method, nothing more.
- A new Hard-Stop Gate, or any edit to `AGENTS.md` (196 of 200 lines used). The UX rows bind through `code-review` findings, not through Gate 6.
- Any hook or merge-gate change.
- `agents/qa.md` — the independent check is the `ux-reviewer` persona (see Cut list).
- A UX design skill that designs screens. The scope is evaluation against stated criteria.

**Requirement Refs**: the kit has no single `PRD.md` (`PROJECT_SPEC.md` `## Readiness`: `README.md` stand-in). This task traces to the user's quoted request and the three gaps above, labelled G1–G3.

### Requirement Fidelity Gate (sign off BEFORE implementation)

- [x] Restated intent confirmed to match the user's request (auto (Supervisor), from the quoted messages and the approved three-fix proposal)
- [x] Domain terms align with `PROJECT_SPEC.md` glossary — **UX Acceptance Criteria** (new) is kept apart from the three **UI design Evidence rows** (Hard-Stop Gate 6)
- [x] Every Acceptance Criterion below traces to a line in the Requirement
- [x] Requirement Refs: no `PRD.md` IDs exist; G1–G3 are covered by AC 1–6

---

## Dependencies & Reachability

**Depends on**: `None` (T192 is related, not a precondition: this task works with headless Chrome alone)

**Entry point**: `ux-reviewer` — the persona row in `skills/code-review/SKILL.md` `#### Conditional reviewers`

---

## Acceptance Criteria

| # | Criterion (testable) | Traces to requirement |
|---|----------------------|-----------------------|
| 1 | `templates/TASK_GUIDE_template.md` has `### 4. UX Acceptance Criteria` inside `## UI / Design Acceptance Criteria`, a table with columns `User story`, `User goal`, `Flow / state`, `Pass condition (observable)`. The guidance says: each row cites a `PRD.md` US-ID (or the quoted request when no PRD), covers the empty / loading / error / success states that the screen has, and a pass condition is something a reviewer can see on a screenshot or a run — never "looks good" | G2 |
| 2 | `skills/code-review/SKILL.md` `#### Conditional reviewers` has one `ux-reviewer` row: activates when the diff touches UI files; the row points at `references/ux-reviewer.md` for its rules | G3 |
| 3 | New `skills/code-review/references/ux-reviewer.md` states: (a) take screenshots of the guide's `Entry point` at 375px and 1280px width (headless Chrome `--screenshot`, `Skill({ skill: "run" })`, or easy-ui when installed); (b) `Read` each image; (c) judge each UX row `pass` / `fail` with the screenshot path; (d) a `fail` is a P1 finding; (e) a row it cannot check (no running app, no browser) is a P2 finding `UX not checked: <reason>`, never a pass; (f) a UI diff whose guide has no UX rows is a P2 finding `UI change with no UX criteria` | G3, independence rule (`pipeline-stages.md` Evidence Gate) |
| 4 | `agents/frontend.md` `## Implementation checklist` has a `UX:` line: before Ready for Review, screenshot the changed screens, `Read` them, check each UX row, and list the screenshot paths in the report. Pillar 3 names the method (screenshot + `Read`) | G1 |
| 5 | `skills/code-review/SKILL.md` stays ≤ 8192 bytes (Codex skill-body cap; it is 8163 bytes before this task) | Non-Claude CLI projection, `AGENTS.md` `## Non-Claude CLIs` |
| 6 | Negative: a test checks that `ux-reviewer.md` maps "cannot check" to a finding and never to `pass`, and that the template's UX block is inside the UI section (deleted with it for pure-backend tasks) | G3 boundary |
| 7 | The full test suite still passes (`python3 -m pytest -q`) — no existing template, skill-size or projection test breaks | regression |

---

## Evaluation & Acceptance (How we know the agent worked correctly)

### Success Criteria (observable, pass/fail)

| # | Given (input/state) | Expect (output/behavior) | How it's checked |
|---|---------------------|--------------------------|------------------|
| 1 | The template after the change | `### 4. UX Acceptance Criteria` sits between `### 3. Layout / Responsiveness` and `## Approach`, with the four column headers | automated test |
| 2 | `skills/code-review/SKILL.md` | one `ux-reviewer` row in the conditional table; the file has ≤ 8192 bytes | automated test |
| 3 | `skills/code-review/references/ux-reviewer.md` | holds `375`, `1280`, `Read`, `P1`, `UX not checked`, `UI change with no UX criteria` | automated test |
| 4 | `agents/frontend.md` | a `- UX:` checklist line naming screenshot and `Read` | automated test |
| 5 | A real run: Supervisor screenshots `site/index.html` with headless Chrome at 375px and 1280px and `Read`s both | two PNG files exist and open; proves the documented command works on this machine | app run |
| 6 | Full suite | no new failure against `main` (5 known `MEMORY.md` budget failures noted on T217 are pre-existing; compare to a `main` run) | automated test |

### Verification Command (exact, runnable)

```bash
python3 -m pytest tests/test_t245_ux_review.py -q
python3 -m pytest -q
wc -c skills/code-review/SKILL.md   # must print ≤ 8192
# ci: skip for the screenshot line below — needs a local Chrome
google-chrome --headless --disable-gpu --window-size=375,800 --screenshot=/tmp/t245-375.png "file://$PWD/site/index.html"
```

### Evidence (filled by reviewer at Stage 4/5)

> **Moved.** Filled by the reviewer at Stage 4/5 in `tasks/TASK_REVIEW_T245.md`.

---

## Demonstration

> **Moved.** See `tasks/TASK_REVIEW_T245.md`.

---

## Approach

**Pattern reference**: `skills/resolve-question/references/advocate.md` — a skill that keeps a sub-role's full rules in `references/` and one pointer in `SKILL.md`, used here because `code-review/SKILL.md` has 29 bytes of headroom.

**Vital slice**: the template UX block, the `ux-reviewer` row + reference file, and the frontend `UX:` line. Together they give a criterion, an independent judge, and a self-check.
**Cut list**:
- `agents/qa.md` UX section — the `ux-reviewer` already is the non-implementer check; add later only if review misses UX gaps.
- A 4th row in Hard-Stop Gate 6 — needs an `AGENTS.md` line (4 left) and a hook change; findings bind already.
- Visual diff baselines — T192 / the existing Visual Regression row.
- A `PRD_template.md` UX section — the template's existing User Stories table is the source the UX rows cite.

Byte budget: if the one row does not fit in 29 bytes, shorten other lines in `code-review/SKILL.md` without changing any rule (same rule meaning, fewer words), and say which lines in the report.

---

## Edge Case Checklist

- [ ] `code-review/SKILL.md` over 8192 bytes after the row — AC 5 test catches it
- [ ] A UI task with no running app (static HTML): `file://` screenshot works; a server app with no start command → `UX not checked` P2, not a silent pass
- [ ] No Chrome/Chromium on the machine → `UX not checked: no browser` P2
- [ ] A pure-backend guide deletes the whole UI section, so the UX block goes with it and `ux-reviewer` never activates (no UI files in the diff)
- [ ] The UX block must not reuse the words "UI design Evidence rows" — one term, one meaning
- [ ] Plugin/`setup.sh` projection: the new `references/ux-reviewer.md` ships with the skill folder (check `MANIFEST` or the projection test if one lists files)

---

## Files to Change (Predicted)

| File | Change |
|------|--------|
| `templates/TASK_GUIDE_template.md` | add `### 4. UX Acceptance Criteria` block (AC 1) |
| `skills/code-review/SKILL.md` | one `ux-reviewer` row in `#### Conditional reviewers` (AC 2, 5) |
| `skills/code-review/references/ux-reviewer.md` | new — the persona's rules (AC 3) |
| `agents/frontend.md` | `UX:` checklist line; Pillar 3 names the method (AC 4) |
| `tests/test_t245_ux_review.py` | new — AC 1–6 |
| `MANIFEST` (only if it lists skill files one by one) | add the reference file |

## Files Must NOT Touch

| File | Reason |
|------|--------|
| `AGENTS.md` | 196/200 lines; no gate change in scope |
| `.claude/hooks/*` | no hook change in scope |
| `tasks/TASK_GUIDE_T192.md`, any `ui-test` skill | T192 owns easy-ui and the three UI design rows |
| `agents/qa.md` | cut list |

---

## Test Plan

Test-first (`tdd`): write `tests/test_t245_ux_review.py` with AC 1–6 as text assertions on the four
files (red), make the edits (green), then run the full suite and compare with a `main` run. Then the
real run: headless Chrome screenshots of `site/index.html` at 375px and 1280px, opened with `Read`.

---

## Completion Checklist

- [ ] Implementation done
- [ ] Self-review: `Skill({ skill: "code-review" })` run
- [ ] Security review: `Skill({ skill: "security-review" })` run (Risk Medium)
- [ ] Lint passes
- [ ] Tests written AND pass — output pasted into `tasks/TASK_REVIEW_T245.md`'s Evidence table (Hard-Stop Gate 5)
- [ ] `Skill({ skill: "verify" })` run — via the headless auto verify run
- [ ] `memory/MEMORY.md` updated (if new patterns or feedback learned)
- [ ] Supervisor notified: task ready for Stage 4 review
