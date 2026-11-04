# TASK_GUIDE — T245: `ux-evaluate` skill — the frontend agent checks its UI against the requirement's UX criteria
**Date**: 2026-11-03
**Complexity Level**: C2
**Risk Level**: Medium
**Priority**: P1
**Assigned agent**: common-infrastructure
**Agent guide**: `agents/common-infrastructure.md`

> Risk Medium: two hub files. `templates/TASK_GUIDE_template.md` feeds every guide, and
> `skills/code-review/SKILL.md` runs on every extended-track task. A hub touch raises Risk a level
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
7. Read `skills/write-better-skill/SKILL.md` — the craft reference for any new `SKILL.md`. Draft the new skill through `Skill({ skill: "teach" })`'s workflow so its craft checks run inside creation
8. Read `tasks/TASK_GUIDE_T192.md` `## Requirement` — T192 (Todo) owns the easy-ui `ui-test` skill and the three UI design Evidence rows; this task must not overlap it

---

## Requirement (Pillar 1 — Adapt the requirement)

User, 2026-11-03: *"the frontend agent do not have the UX skill, so it can not evaluate the change is
good or not following the requirement, let investigate and let me know"*. The Supervisor's
investigation found three gaps:
1. G1 — `agents/frontend.md` has no UX skill in its `## Available skills` table and no way to look at
   its own UI (tools `Read, Write, Edit, Bash, Glob, Grep`; Pillar 3 says "confirm the UI behaves in
   the browser" with no method).
2. G2 — `templates/TASK_GUIDE_template.md` `## UI / Design Acceptance Criteria` checks conformance only
   (visual regression, design tokens, responsiveness). No row names the user's goal, the flow, the
   states, or a pass condition traced to the requirement.
3. G3 — no review step judges UX: `skills/code-review/SKILL.md` has no UI/UX persona.

The user approved opening a task (*"yes, open the task [auto]"*), then corrected the design
(2026-11-03): *"not the reviewer, it should be the UX skill and it belong to agent, not in the
code-review only"*.

**Restated intent**:
> A UX skill, `ux-evaluate`, that the frontend agent owns and runs while it builds. It looks at real
> screenshots of the changed screens and judges each UX criterion in the guide pass or fail, so the
> agent itself can tell whether its change meets the requirement. Code review runs the same skill
> again on UI diffs, from a context that did not write the code. The guide template gains the UX
> criteria the skill judges against.

**Out of scope** (what this task explicitly does NOT do):
- A `ux-reviewer` persona inside `code-review` with its own rules — the user rejected it. `code-review` only calls the skill.
- easy-ui sessions and the three existing UI design Evidence rows — T192 owns them. `ux-evaluate` may name easy-ui as one screenshot method, nothing more.
- A new Hard-Stop Gate, or new lines in `AGENTS.md` (196 of 200 lines used). The UX rows bind through the skill's verdict and `code-review` findings.
- Any hook or merge-gate change.
- `agents/qa.md` (see Cut list).
- Designing screens. The skill evaluates against stated criteria; it does not invent a design.

**Requirement Refs**: the kit has no single `PRD.md` (`PROJECT_SPEC.md` `## Readiness`: `README.md` stand-in). This task traces to the quoted requests and gaps G1–G3.

### Requirement Fidelity Gate (sign off BEFORE implementation)

- [x] Restated intent confirmed to match the user's request (auto (Supervisor), from the quoted messages including the 2026-11-03 correction)
- [x] Domain terms align with `PROJECT_SPEC.md` glossary — **UX Acceptance Criteria** (new) is kept apart from the three **UI design Evidence rows** (Hard-Stop Gate 6)
- [x] Every Acceptance Criterion below traces to a line in the Requirement
- [x] Requirement Refs: no `PRD.md` IDs exist; G1–G3 and the correction are covered by AC 1–8

---

## Dependencies & Reachability

**Depends on**: `None`

Related, not a precondition: the easy-ui task (Todo) adds one more screenshot method; the skill works with headless Chrome alone.

**Entry point**: `skills/ux-evaluate/SKILL.md` — named in `agents/frontend.md` `## Available skills` (the agent reads and follows it) and run by `code-review` as `Skill({ skill: "ux-evaluate" })`

---

## Acceptance Criteria

| # | Criterion (testable) | Traces to requirement |
|---|----------------------|-----------------------|
| 1 | New `skills/ux-evaluate/SKILL.md` with valid frontmatter (`scripts/validate.sh` accepts it), ≤ 8192 bytes (Codex cap). Its description says when to use it: a UI change, before Ready for Review, or from `code-review` on a UI diff | G1, correction |
| 2 | The skill's workflow: (a) read the guide's `### 4. UX Acceptance Criteria` rows and the requirement they cite; (b) take screenshots of the guide's `Entry point` at 375px and 1280px width (headless Chrome `--screenshot`, `Skill({ skill: "run" })`, or easy-ui when installed); (c) `Read` each image; (d) judge each row `pass` / `fail`, with the screenshot path and one line of reason; (e) output one verdict table | G1 |
| 3 | Negative paths in the skill: a row it cannot check (no running app, no browser) is `not checked: <reason>`, never `pass`; a UI change whose guide has no UX rows returns `no UX criteria` and tells the caller to ask the Supervisor for them; a vague pass condition ("looks good") is reported as `not checkable` | G1 boundary |
| 4 | `agents/frontend.md`: `## Available skills` has a `ux-evaluate` row; `## Implementation checklist` has a `UX:` line (before Ready for Review, `Read` `skills/ux-evaluate/SKILL.md` and follow its steps — a sub-agent has no `Skill` tool, `memory/learnings.md:895`; fix every `fail`; put the verdict table in the report); Pillar 3 names the method. The skill's own text works both ways: called with `Skill(...)` by the Supervisor, or read and followed by an agent | G1, "belong to agent" |
| 5 | `templates/TASK_GUIDE_template.md` has `### 4. UX Acceptance Criteria` inside `## UI / Design Acceptance Criteria`: columns `User story`, `User goal`, `Flow / state`, `Pass condition (observable)`; guidance says each row cites a `PRD.md` US-ID (or the quoted request), covers the empty / loading / error / success states the screen has, and states what is seen on a screenshot or a run | G2 |
| 6 | `skills/code-review/SKILL.md`: one conditional row — on a diff that touches UI files, run `Skill({ skill: "ux-evaluate" })`; a `fail` is a P1 finding, a `not checked` / `no UX criteria` is P2. No UX rules are copied into `code-review`. The file stays ≤ 8192 bytes (8163 before this task) | G3, "not in the code-review only" |
| 7 | Every place that lists all skills names `ux-evaluate` where tests require it (for example `site/index.html` skill flow, `tests/test_site_content.py` `SKILL_FLOW_GROUPING` stage 3); the full suite stays green | regression |
| 8 | Real run: the implementer runs `ux-evaluate` on `site/index.html` with 2 UX rows written for the test, and pastes the verdict table and the two screenshot paths | G1 proof |

**Amendment A1 (2026-11-03, user: "when I apply to build FE without design, it got the poor UX"; commit `75fecb67`)**: AC 3's `no UX criteria` no longer stops the skill. It judges nine fixed baseline UX checks (B-a to B-i) with or without rows and reports `no UX criteria — baseline checks only`. Evidence: round 4 in `tasks/TASK_REVIEW_T245.md` (blind-judged no-design builds: 35/35 with the skill, 29/29 without).

**Amendment A2 (2026-11-04, Stage 4 review R2, user: "yes [auto]")**: on a diff, the skill writes a baseline `fail` on a part the diff did not change as `fail (older)`; `code-review` rates it P3, not P1. AC 6's P1/P2 mapping stays for row fails and new baseline fails.

---

## Evaluation & Acceptance (How we know the agent worked correctly)

### Success Criteria (observable, pass/fail)

| # | Given (input/state) | Expect (output/behavior) | How it's checked |
|---|---------------------|--------------------------|------------------|
| 1 | `skills/ux-evaluate/SKILL.md` | valid frontmatter, ≤ 8192 bytes, holds `375`, `1280`, `Read`, `not checked`, `no UX criteria` | automated test |
| 2 | `agents/frontend.md` | a `ux-evaluate` row in `## Available skills` and a `- UX:` checklist line | automated test |
| 3 | The template | `### 4. UX Acceptance Criteria` between `### 3. Layout / Responsiveness` and `## Approach`, with the 4 headers | automated test |
| 4 | `skills/code-review/SKILL.md` | one row naming `ux-evaluate`; no `ux-reviewer`; ≤ 8192 bytes | automated test |
| 5 | Negative: the skill text | `not checked` never maps to `pass` | automated test |
| 6 | Real run on `site/index.html` | 2 PNGs at 375px and 1280px exist, open with `Read`, verdict table pasted | app run |
| 7 | Full suite | no new failure against a `main` run | automated test |

### Verification Command (exact, runnable)

```bash
python3 -m pytest tests/test_t245_ux_evaluate.py -q
sh scripts/validate.sh | grep "skills/ux-evaluate/SKILL.md"
python3 -m pytest -q
wc -c skills/ux-evaluate/SKILL.md skills/code-review/SKILL.md   # each ≤ 8192
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

**Pattern reference**: `skills/score/SKILL.md` — a skill that an optional tool improves, with a clear fallback when the tool is absent, and its own size + frontmatter tests (`tests/test_companion_scoring_skills.py`).

**Vital slice**: the `ux-evaluate` skill, its row in `agents/frontend.md`, the template UX block, and one `code-review` row that calls it. The agent gets the criterion, the skill and the habit; review reuses the same skill.
**Cut list**:
- `agents/qa.md` UX section — `code-review` already reruns the skill outside the implementer's context.
- A 4th row in Hard-Stop Gate 6 — needs `AGENTS.md` lines and a hook change; the skill's verdict and P1 findings bind already.
- Visual diff baselines — T192 / the existing Visual Regression row.
- A `PRD_template.md` UX section — the UX rows cite the existing User Stories table.
- An `AGENTS.md` stage-index entry — `score` is not listed there either; add only if a test requires it.

Byte budget for `code-review/SKILL.md` (29 bytes headroom): if the one row does not fit, shorten other lines without changing any rule, and list the lines in the report.

---

## Edge Case Checklist

- [ ] Either `SKILL.md` over 8192 bytes — AC 1 / AC 6 tests catch it
- [ ] Static HTML: `file://` screenshot works; a server app with no start command → `not checked`, not a silent pass
- [ ] No Chrome/Chromium → `not checked: no browser`
- [ ] A pure-backend guide deletes the whole UI section, so the UX block goes with it; `code-review` does not run the skill (no UI files in the diff)
- [ ] The skill and template never call the UX rows "UI design Evidence rows" — one term, one meaning
- [ ] Plugin and `setup.sh` installs ship the new skill folder (check any manifest or projection test that lists skills)

---

## Files to Change (Predicted)

| File | Change |
|------|--------|
| `skills/ux-evaluate/SKILL.md` | new — the UX skill (AC 1–3) |
| `agents/frontend.md` | skills-table row, `UX:` checklist line, Pillar 3 method (AC 4) |
| `templates/TASK_GUIDE_template.md` | `### 4. UX Acceptance Criteria` block (AC 5) |
| `skills/code-review/SKILL.md` | one conditional row that calls the skill (AC 6) |
| `site/index.html`, `tests/test_site_content.py` | only where tests require every skill listed (AC 7) |
| `tests/test_t245_ux_evaluate.py` | new — AC 1–6 |

## Files Must NOT Touch

| File | Reason |
|------|--------|
| `AGENTS.md` | 196/200 lines; no gate change in scope |
| `.claude/hooks/*` | no hook change in scope |
| `tasks/TASK_GUIDE_T192.md`, any `ui-test` skill | T192 owns easy-ui and the three UI design Evidence rows |
| `agents/qa.md` | cut list |

---

## Test Plan

Test-first (`tdd`): write `tests/test_t245_ux_evaluate.py` with AC 1–6 as assertions on the files
(red), make the edits (green), then run the full suite and compare with a `main` run. Then the real
run (AC 8): `ux-evaluate` on `site/index.html` with 2 test UX rows, screenshots at 375px and 1280px.

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
