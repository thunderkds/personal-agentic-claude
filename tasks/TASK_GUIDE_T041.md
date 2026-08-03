# TASK_GUIDE — T041: Make engineering principles reachable by sub-agents + add the Search-Before-You-Build ladder
**Date**: 2026-07-21
**Complexity Level**: C2
**Risk Level**: Medium
**Priority**: P1
**Assigned agent**: Common-Infrastructure-Agent
**Agent guide**: `.claude/agents/common-infrastructure.md`

---

## Mandatory Startup (Do Not Skip)

Before writing anything:
1. Read `PROJECT_SPEC.md`
2. Read `memory/MEMORY.md` (pasted into your spawn prompt — do not re-read if present)
3. Read this file completely
4. Read `.claude/agents/common-infrastructure.md`
5. Read `.claude/agents/general-agent-template.md` — **this is the file you are editing**; read it in full before proposing any change
6. C2 task: read `memory/codebase-map.md` for structural orientation

---

## Requirement (Pillar 1 — Adapt the requirement)

Two defects were found in the same file during a 2026-07-21 review session, and the user directed
they be fixed as one task.

**Defect A — principles are commanded but never delivered.**
`.claude/agents/general-agent-template.md:22` instructs every sub-agent: *"Strictly follow all
Karpathy Engineering Principles."* The actual content of those four principles exists only in
`CLAUDE.md`. The template's own Mandatory Startup Sequence (lines 10–14) lists `PROJECT_SPEC.md`,
`memory/MEMORY.md`, the TASK_GUIDE, the role guide, and optionally `memory/codebase-map.md` —
**`CLAUDE.md` is not among them**. Every sub-agent is therefore ordered to follow rules whose text
it never receives. This is the same failure class as T036/T038: a rule that appears enforced and
silently is not.

**Defect B — no search-before-you-build step exists anywhere.**
The framework tells agents to write minimal code (`tdd/SKILL.md`) but never tells them to check
whether the code needs writing at all. Nothing in the repo instructs an agent to look for an
existing helper, a stdlib function, a platform feature, or an already-installed dependency first.

**Restated intent**:
> A spawned sub-agent should receive, in its own context, both the principles it is told to obey and
> an ordered procedure for avoiding unnecessary code — without materially inflating what every spawn
> costs.

**Source for Defect B's fix**: the "laziness ladder" from `github.com/DietrichGebert/ponytail`,
adopted as a **process rule on its own merits**. Its published metrics (54% fewer LOC, 20% cost
reduction) are self-reported, n=12, from the authors' own benchmark with no independent
replication — they are **not** part of this task's justification and must not be cited as
expected outcomes. Per DDR-0001, this repo does not refactor on unreplicated external numbers.

**Out of scope**:
- Editing `CLAUDE.md` (T039 owns that file this cycle — avoid a merge conflict)
- Editing `.claude/agents/backend.md`, `frontend.md`, `qa.md`, `common-infrastructure.md`
- Editing `.claude/skills/tdd/SKILL.md`
- Adding any new dependency, script, or hook beyond the one test named below
- Importing ponytail's `ponytail:` source-comment convention (see Approach — explicitly rejected)

**Requirement Refs**: no `PRD.md` exists in this repo. Traceability:
- **User directive 2026-07-21** — "merge them into one task"
- **DDR-0001** — governs the justification standard applied above
- **LR-0002** — pipeline rules that aren't actually enforced are a recurring systemic failure

### Requirement Fidelity Gate (sign off BEFORE implementation)

- [x] Restated intent confirmed by Supervisor against the user's request
- [x] Defect A verified by direct file inspection (`general-agent-template.md:10-14` vs `:22`)
- [x] Defect B verified by grep across `.claude/agents/` and `.claude/skills/tdd/`
- [x] Every Acceptance Criterion below traces to Defect A or Defect B

---

## Dependencies & Reachability

**Depends on**: `None` — independent of T039 (different file, no shared content)

**Entry point**: `## Search Before You Build`
> The literal H2 heading this task adds to `.claude/agents/general-agent-template.md`.
> Grep-able and unique across the repo.

---

## Acceptance Criteria

| # | Criterion (testable) | Traces to |
|---|----------------------|-----------|
| 1 | `general-agent-template.md` contains all four Karpathy principle names **and** a one-line operational command for each, inline | Defect A |
| 2 | `general-agent-template.md` contains a `## Search Before You Build` section with exactly 7 rungs, numbered 1–7 in ponytail's order | Defect B |
| 3 | The section contains a non-negotiables block stating that correctness, input validation, error handling, security, and explicit requirements are never traded for a shorter diff | Defect B |
| 4 | Line 22's bare `Strictly follow all Karpathy Engineering Principles` reference now resolves to content present in the same file (no cross-file dependency for the principles) | Defect A |
| 5 | **Negative**: `CLAUDE.md` is NOT added to the Mandatory Startup Sequence read list | cost guard — see Approach |
| 6 | **Negative**: the string `ponytail` appears nowhere in `.claude/agents/**` | scope guard |
| 7 | **Negative**: file grows by ≤45 lines (87 → ≤132). A larger growth means prose bloat in a file loaded on every spawn | cost guard |
| 8 | All four role guides (`backend.md`, `frontend.md`, `qa.md`, `common-infrastructure.md`) are byte-identical to HEAD | scope guard |

---

## Evaluation & Acceptance

### Success Criteria (observable, pass/fail)

| # | Given (input/state) | Expect (output/behavior) | How it's checked |
|---|---------------------|--------------------------|------------------|
| 1 | `general-agent-template.md` after edit | `scripts/test-agent-template.sh` exits 0 | automated test |
| 2 | Rungs renumbered/reordered, or one deleted | test exits non-zero naming the failure | automated test (negative control) |
| 3 | `CLAUDE.md` added to the startup read list | test exits non-zero (AC5) | automated test (negative control) |
| 4 | Role guides | checksum-identical to `git show HEAD:` | automated test |

### Verification Command (exact, runnable)

```bash
bash scripts/test-agent-template.sh && \
  echo "template lines: $(wc -l < .claude/agents/general-agent-template.md) (was 87, budget 132)"
```

### Evidence (filled by reviewer at Stage 4/5)

| Check | Result | Notes / output snippet |
|-------|--------|------------------------|
| **New test(s) cover Acceptance Criteria (file paths pasted)** | pass | `scripts/test-agent-template.sh` — content assertions for AC1-AC3, negative controls for AC5/AC6/AC7/AC8. `sh scripts/test-agent-template.sh` → 29 `PASS:` lines, `test-agent-template: all checks passed`, exit 0 |
| Verification command run | pass | `bash scripts/test-agent-template.sh && echo "template lines: $(wc -l < .claude/agents/general-agent-template.md) (was 87, budget 132)"` → all checks passed, then `template lines: 117 (was 87, budget 132)` |
| Negative cases hold | pass | AC5 (`CLAUDE.md` added to startup list) → `FAIL: AC5: ...cost guard violated`; AC6 (`ponytail` inserted) → `FAIL: AC6: the string 'ponytail' appears somewhere...`; AC7 (budget, verified at 117/132 — real growth 30 lines, within the 45-line cap, no separate mutation needed since it's a live measurement not a boolean flip); AC8 (`backend.md` touched) → `FAIL: AC8: backend.md differs from HEAD (checksum mismatch)`. All 4 pasted below the table under "Negative controls (full output)". |
| verify | pass | Re-ran `sh scripts/test-agent-template.sh` standalone after all 4 negative controls were reverted — clean pass, exit 0, confirming the working tree is back to the intended state |
| Review scope bounded to the change's blast radius | pass | Hub file — inherited by all 4 role guides (`backend.md`, `frontend.md`, `qa.md`, `common-infrastructure.md`); reviewed the template's full diff plus checksum-verified (AC8) that none of the 4 role guides changed, rather than re-reading each role guide's full content |
| Full smoke suite still green (no regression) | pass | `bash scripts/smoke-install.sh` → `smoke-install.sh: PASS` |
| **UI: Visual regression** | ☐ N/A | Docs-only task, no UI component |
| **UI: Design-system compliance** | ☐ N/A | Docs-only task, no UI component |
| **UI: Responsiveness** | ☐ N/A | Docs-only task, no UI component |

**Manual code-review (no `Skill` tool available to a sub-agent)**: PASS, 0 findings. Additive-only
diff to `general-agent-template.md` (new `## Karpathy Engineering Principles (Compact)` table + new
`## Search Before You Build` section + a 1-line pointer edit to the existing bullet); frontmatter
`name:`/`description:` untouched; no other section renumbered or reworded (Surgical Changes,
confirmed by the AC8 checksum on the 4 role guides that inherit this file).

**Manual security-review (Risk=Medium, mandatory — hub file inherited by all sub-agents)**: PASS, 0
findings, as expected for a docs-only change. No code, no executable content, no secrets.

**`sh -n` + real run substitution for shellcheck** (`memory/learnings.md` — no shellcheck in this
environment): `sh -n scripts/test-agent-template.sh` → clean, no output; `sh scripts/test-agent-template.sh`
real run → see Verification Command output above.

**Negative controls (full output, each reverted immediately after)**:

a. Deleted rung 4 (`Is there a native platform/framework feature for it?`):
```
PASS: AC2: ## Search Before You Build section present
FAIL: AC2: expected exactly 7 numbered rungs, found 6
PASS: AC2: rung 1 present
PASS: AC2: rung 2 present
PASS: AC2: rung 3 present
FAIL: AC2: rung 4 missing
PASS: AC2: rung 5 present
PASS: AC2: rung 6 present
PASS: AC2: rung 7 present
test-agent-template: FAILED
```

b. Added `CLAUDE.md` to the Mandatory Startup Sequence read list:
```
FAIL: AC5: CLAUDE.md was added to the Mandatory Startup Sequence read list (cost guard violated)
test-agent-template: FAILED
```

c. Inserted the word `ponytail` into the `## Search Before You Build` heading:
```
FAIL: AC2: expected exactly 7 numbered rungs, found 0
FAIL: AC2: rung 1 missing
FAIL: AC2: rung 2 missing
FAIL: AC2: rung 3 missing
FAIL: AC2: rung 4 missing
FAIL: AC2: rung 5 missing
FAIL: AC2: rung 6 missing
FAIL: AC2: rung 7 missing
FAIL: AC6: the string 'ponytail' appears somewhere in .claude/agents/**
test-agent-template: FAILED
```
(AC2 also fails here as a side effect — the mutated heading no longer matches the exact awk anchor,
which is itself evidence the test isn't matching loosely.)

d. Appended a blank line to `backend.md`:
```
FAIL: AC8: backend.md differs from HEAD (checksum mismatch)
test-agent-template: FAILED
```

All 4 reverted via `cp` from a pre-mutation backup immediately after capturing output; final state
re-verified clean (see `verify` row above).

**Deviation from the guide**: none. Implemented per the Approach section as written — compact
Karpathy table (name + operational command only, no "Problem Addressed" column), all 7 ladder rungs
in ponytail's original order, non-negotiables block, `ponytail:` source-comment convention rejected
as directed. Net growth: 87 → 117 lines (+30), within the ≤45-line budget.

---

## Approach

### Defect A — inline, do not link

Two candidate fixes were considered. The Supervisor has already decided; do not re-litigate:

| Option | Cost | Verdict |
|---|---|---|
| Add `CLAUDE.md` to the startup read list | ~11k tokens **per spawn** (CLAUDE.md is 580 lines) | **Rejected** — would cost more than T039 saves, on every single spawn |
| Inline a compact version of the four principles | ~12 lines, loaded once per spawn as part of a file the agent already reads | **Selected** |

Compress the Karpathy table to principle name + operational command. Drop the "Problem Addressed"
column — an agent needs the instruction, not the rationale. Keep the Task Transformation Table out
of scope; it is guidance for the Supervisor writing task guides, not for the agent executing one.

Since the principles now exist in two places, add a one-line pointer noting `CLAUDE.md` holds the
canonical full version, so a future editor updates both. Record this deliberate duplication in your
final report so the Supervisor can note it in `memory/`.

### Defect B — the ladder, all 7 rungs

Add `## Search Before You Build` with all seven rungs in ponytail's original order:
does-this-need-to-exist → already-in-this-codebase → stdlib → native platform feature → installed
dependency → can-it-be-one-line → only then write minimum working code.

Adopt all 7 rather than only the middle five. Rung 1 is the ladder's entry condition and rung 7 its
exit condition; a ladder truncated at both ends leaves an agent that reaches the bottom with no
instruction for what to do next. The apparent overlap of rungs 1 and 7 with `tdd/SKILL.md` is not
real duplication — `tdd` is invocation-triggered and does not load for every agent or every task,
whereas this template loads on every spawn.

Frame each rung as a **check with a stop condition**, not a prohibition. Include the guard against
its most likely misuse: adding a new dependency to avoid writing ten lines is a ladder *failure*,
not a rung-5 success.

**Rejected from the source material**: the `ponytail:` source-comment convention. Vendor-branded
markers in this repo's source buy nothing, and the Code Naming Conventions table has no slot for
them. If a deliberate simplification needs flagging, a plain comment naming the trade-off suffices.

### Test first

Write `scripts/test-agent-template.sh` before editing the template, following the conventions in the
existing `scripts/smoke-install.sh` (same shebang, same pass/fail output style). Per
`memory/learnings.md` there is no shellcheck in this environment — substitute `sh -n` plus a real
bash run and state that substitution explicitly rather than silently skipping it.

---

## Edge Case Checklist

- [ ] Prose bloat: this file loads on **every** sub-agent spawn. Every line added is paid repeatedly.
      Prefer a terse checklist to explanatory prose; AC7 enforces the budget.
- [ ] The ladder must not read as permission to under-build — AC3's non-negotiables block is what
      prevents "shortest diff wins" from eating validation and error handling. Do not drop it.
- [ ] Do not renumber or reword the existing Complexity matrix, Communication Protocol, or Output
      Requirements sections while in the file (Surgical Changes).
- [ ] Frontmatter (`name:` / `description:`) must stay intact — `general-agent-template` is
      referenced by name in `CLAUDE.md` and the role guides; a broken `name:` breaks resolution.
- [ ] `general-agent-template` is **not** a directly spawnable sub-agent. Nothing in this change may
      imply it is.
- [ ] The step-limit hook is known to false-positive on tool inputs whose text mentions an old task
      ID (`memory/learnings.md`); if it fires, bracket-glob the ID.
- [ ] Verify AC8 with a real checksum against `git show HEAD:<path>`, not by visual inspection —
      `memory/learnings.md`: "a checkmark is a claim, not a fact".

---

## Files to Change (Predicted)

| File | Change |
|------|--------|
| `.claude/agents/general-agent-template.md` | Inline compact Karpathy principles (Defect A); add `## Search Before You Build`, 7 rungs + non-negotiables (Defect B) |
| `scripts/test-agent-template.sh` | **New** — content assertions + 4 negative controls |

## Files Must NOT Touch

| File | Reason |
|------|--------|
| `CLAUDE.md` | Owned by T039 this cycle — concurrent edits would conflict |
| `.claude/agents/backend.md`, `frontend.md`, `qa.md`, `common-infrastructure.md` | AC8 asserts these are byte-identical; they inherit the template, they do not restate it |
| `.claude/skills/tdd/SKILL.md` | Rungs 1/7 overlap is deliberate and justified above — do not "fix" it by editing tdd |
| `docs/ddr/0001-measure-first-token-refactor.md` | Supervisor-owned; amended separately under T040 |
| `MANIFEST` | `.claude/agents` already ships as a blanket line — no manifest change needed |

---

## Test Plan

1. **Red**: write `scripts/test-agent-template.sh` against the *current* template. AC1, AC2, AC3
   must fail (content absent); AC5, AC6, AC8 must already pass — proving the test distinguishes
   "not yet done" from "done wrong".
2. **Negative controls** — run each, paste the failure output into Evidence, then revert:
   a. delete one rung → AC2 fails naming it
   b. add `CLAUDE.md` to the startup read list → AC5 fails
   c. insert the word `ponytail` → AC6 fails
   d. touch `backend.md` → AC8 fails
3. **Green**: implement both fixes; all ACs pass.
4. **Regression**: `bash scripts/smoke-install.sh` still green.
5. Paste real command output into every Evidence row — never a claim of output.

---

## Completion Checklist

- [ ] Implementation done
- [ ] Self-review: `Skill({ skill: "code-review" })` run
- [ ] Security review: `Skill({ skill: "security-review" })` run — **mandatory, Risk=Medium** (hub file inherited by all sub-agents); expected zero findings on a docs-only change, run it regardless
- [ ] `sh -n` + real bash run on the new script (no shellcheck in this env — state the substitution)
- [ ] Tests written AND pass — output pasted into Evidence table (Hard-Stop Gate 5)
- [ ] `Skill({ skill: "verify" })` run
- [ ] Report the deliberate CLAUDE.md/template principle duplication to the Supervisor for `memory/` — do not write memory yourself
- [ ] Supervisor notified: task ready for Stage 4 review
