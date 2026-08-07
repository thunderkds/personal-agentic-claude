# TASK_GUIDE — T059: a test writes to a tracked repo file and destroys it in a worktree
**Date**: 2026-08-07
**Complexity Level**: C1
**Risk Level**: Medium
**Priority**: P1
**Assigned agent**: common-infrastructure
**Agent guide**: `.claude/agents/common-infrastructure.md`

---

## Mandatory Startup (Do Not Skip)

Before writing any code:
1. Read `PROJECT_SPEC.md`
2. Read `memory/MEMORY.md`
3. Read this file completely
4. Read `.claude/agents/common-infrastructure.md`
5. Note the **Complexity Level** above and apply the matching process from the Complexity matrix in `.claude/agents/general-agent-template.md`

**STOP-check before anything else**: run `ls tasks/TASK_GUIDE_T059.md`. If it is not there, you are in a
worktree forked from the wrong commit — stop and report to the Supervisor rather than proceeding.

---

## Requirement (Pillar 1 — Adapt the requirement)

`.claude/hooks/tests/test_token_audit_generator.py:235` `test_real_report_generation_and_gitignore`
requests the `tmp_path` fixture, ignores it, and calls
`token_audit.generate_report(str(ROOT / "memory" / "event-trace"), str(ROOT / "reports" / "token-audit_2026-07-21.md"))`
— the real, git-tracked report file.

In the main checkout this looks harmless: `memory/event-trace/` is populated, so regeneration is
roughly idempotent and only ever appends. The only visible symptom is a permanently dirty working
tree. In a worktree the trace directory is gitignored and therefore empty, so the same call writes an
empty Entries block over all 106 derived entries.

Found during T058's Stage 4 review on 2026-08-06: the sub-agent's implementation commit had swept up
the clobbered file. Re-running the suite reproduced it deterministically, which proved the cause was
the suite and not the agent. It has since reproduced three more times in the 2026-08-07 session — the
file goes dirty on every full suite run.

**Restated intent**:
> The test suite must never write to a tracked repository file. AC4/AC8's intent — the real report
> exists, carries the DDR-0001 window header, and is not gitignored — must still be verified, but by
> reading the file, never by regenerating it.

**Out of scope**:
- Changing `token_audit.py` itself. The generator is correct; the test calls it wrongly.
- Changing what `reports/token-audit_2026-07-21.md` contains, or restoring its current dirty state — the Supervisor handles that separately.
- The `reports/` gitignore exception. `reports/token-audit_*.md` stays a deliberate tracked exception so it survives across worktrees.
- Auditing other test files for the same pattern. If you spot one, report it; do not fix it here.

**Requirement Refs**: none — internal defect found at T058 Stage 4.

### Requirement Fidelity Gate (sign off BEFORE implementation)

- [ ] Restated intent confirmed to match the defect (by Supervisor / user — not the implementing agent)
- [ ] Every Acceptance Criterion below traces to a line in the Requirement

---

## Dependencies & Reachability

**Depends on**: `None`

**Entry point**: `test_real_report_generation_and_gitignore`

---

## Acceptance Criteria

| # | Criterion (testable) | Traces to requirement |
|---|----------------------|-----------------------|
| 1 | `test_real_report_generation_and_gitignore` no longer calls `generate_report` with any path under `ROOT / "reports"` | "must never write to a tracked repository file" |
| 2 | The test still asserts the real `reports/token-audit_2026-07-21.md` contains `Window opened 2026-07-21` and a window-close condition, by **reading** it | AC4 intent preserved |
| 3 | The test still asserts the file is not gitignored via `git check-ignore` | AC8 intent preserved |
| 4 | After a full suite run from a clean checkout, `git status --short` reports **no** modification to `reports/token-audit_2026-07-21.md` | the defect itself |
| 5 | The same holds in a worktree: after a full suite run, the file is unmodified and still contains its 106 entries | the worktree-destructive case |
| 6 | If the test no longer needs `tmp_path`, the unused fixture parameter is removed | the fixture request is what disguised the defect |
| 7 | Negative: no other test in the file gains a write to any path under `ROOT / "reports"` | scope lock |
| 8 | Full hook suite still green | no regression |

---

## Evaluation & Acceptance (How we know the agent worked correctly)

### Success Criteria (observable, pass/fail)

| # | Given (input/state) | Expect (output/behavior) | How it's checked |
|---|---------------------|--------------------------|------------------|
| 1 | Clean checkout, full suite run | `git status --short` shows no `reports/` modification | automated check, output pasted |
| 2 | The tracked report temporarily emptied, then the suite run | the test **fails** — it is really reading the file, not vacuously passing | mutation control, must be observed RED |
| 3 | Worktree with empty gitignored trace dir, full suite run | report retains all 106 entries | manual verification, output pasted |
| 4 | Full hook suite | 207 passed | automated test |

> SC2 is load-bearing. A test that stops writing but also stops asserting would satisfy AC1 and AC4
> while proving nothing — that is the vacuous-assertion family this repo has hit four times
> (T036/T042/T039/T058). Emptying the file must turn this test RED.

### Verification Command (exact, runnable)

```bash
python3 -m pytest .claude/hooks/tests -q && git status --short reports/
```

### Evidence (filled by reviewer at Stage 4/5)

| Check | Result | Notes / output snippet |
|-------|--------|------------------------|
| **New test(s) cover Acceptance Criteria (file paths pasted)** | ☐ pass / ☐ fail | |
| Verification command run | ☐ pass / ☐ fail | |
| Negative cases hold | ☐ pass / ☐ fail | [SC2 mutation control — must show RED then restored] |
| verify | ☐ pass / ☐ fail / ☐ N/A | |
| Review scope bounded to the change's blast radius (affected set, not whole repo) | ☐ pass / ☐ fail | |
| Full smoke suite still green (no regression) | ☐ pass / ☐ fail | |
| **UI: Visual regression (diff or verdict pasted)** | ☐ N/A | test-file change, no UI component |
| **UI: Design-system compliance (tokens/colors/typography verified)** | ☐ N/A | test-file change, no UI component |
| **UI: Responsiveness at target viewports** | ☐ N/A | test-file change, no UI component |

---

## Demonstration

**BEFORE**: captured by the Supervisor on the main checkout at `2026-08-07T04:03:48Z`, before any
implementation commit exists, after a full suite run (`207 passed`):

```
$ git status --short reports/
 M reports/token-audit_2026-07-21.md

$ git diff --stat reports/token-audit_2026-07-21.md
 reports/token-audit_2026-07-21.md | 18 ++++++++++++++++++
 1 file changed, 18 insertions(+)
```

This is the benign main-checkout form of the defect — 18 appended lines, tracked file dirtied by a
test run. The destructive worktree form (all 106 entries replaced by an empty Entries block) was
observed on 2026-08-06 during T058 Stage 4 and is recorded in `memory/learnings.md`.

**AFTER**: [same command, post-change — expected to print nothing]

**DELTA**: [one sentence]

**WITNESS**: [derived from `memory/event-trace/T059.jsonl`, never the implementing agent alone]

---

## Approach

**Pattern reference**: `.claude/hooks/tests/test_token_audit_generator.py:225`
`test_old_window_file_intact_and_closed_inconclusive` — the correct shape already exists in this
same file, applied to the *other* tracked report. It reads the real file with `read_text` and
asserts against the content, and never calls `generate_report`. Imitate it exactly.

The generator is not at fault and must not be touched. `generate_report` is already exercised eight
times against `tmp_path` elsewhere in this file (lines 42, 91, 109, 134, 146, 156, 176, 198), so the
call at line 237 contributes **zero** generation coverage — it exists only to produce a file the test
then reads. Deleting the call loses nothing and stops the write.

Preferred fix: drop the `generate_report` call, read the existing tracked file, keep both assertions
and the `git check-ignore` check. The `tmp_path` parameter then becomes unused and should go — its
presence is what made the test look sandboxed on a skim, which is why this survived review.

If the AC4 wording is judged to require that generation-into-a-report-path is covered at all, add
that as a *separate* test writing into `tmp_path`. Do not reintroduce it here.

**Known gotcha for this task specifically**: running the suite is itself the reproduction. Expect
`reports/token-audit_2026-07-21.md` to go dirty on any run made before your fix lands. Do not commit
that file, and do not `git checkout` it — the git-guardrails hook blocks `git checkout -- <file>`
(recorded 2026-07-24, T046). If it is dirty at the end, leave it and say so; the Supervisor restores it.

---

## Edge Case Checklist

- [ ] The fix must not depend on `memory/event-trace/` being populated — that is precisely what differs between main and a worktree
- [ ] The test must fail loudly if the report file is missing entirely, not skip
- [ ] `git check-ignore` runs with `cwd=str(ROOT)`; keep that, since a worktree's cwd differs
- [ ] Do not assert on the entry count (106) — it grows legitimately as windows accumulate
- [ ] Removing `tmp_path` must not break any shared fixture ordering in the module

---

## Files to Change (Predicted)

| File | Change |
|------|--------|
| `.claude/hooks/tests/test_token_audit_generator.py` | `test_real_report_generation_and_gitignore` reads the tracked report instead of regenerating it; unused `tmp_path` removed |

## Files Must NOT Touch

| File | Reason |
|------|--------|
| `.claude/hooks/token_audit.py` | the generator is correct; the test calls it wrongly |
| `reports/token-audit_2026-07-21.md` | the tracked file this defect destroys — never commit a modification to it |
| `reports/token-audit_2026-07-17.md` | the closed prior window, asserted intact by the neighbouring test |
| `.gitignore` | the `reports/token-audit_*.md` tracked exception is deliberate |

---

## Test Plan

No new test file. Rework the one test in place, then prove the rework is not vacuous:

1. Run the full suite from a clean checkout; confirm `git status --short reports/` prints nothing.
2. Mutation control (SC2): temporarily truncate `reports/token-audit_2026-07-21.md` to an empty
   Entries block, run the test, observe **RED**, restore the file, observe **GREEN**. Paste both.
   Restore by `cp` from a backup you take first — do not use `git checkout`, which is guardrail-blocked
   and, per a recorded learning, would also revert your own uncommitted fix.
3. Worktree check (SC3): from a worktree whose `memory/event-trace/` is empty, run the suite and
   confirm the report still holds its full entry list.

---

## Completion Checklist

- [ ] Implementation done
- [ ] Self-review: `Skill({ skill: "code-review" })` run
- [ ] Security review: `Skill({ skill: "security-review" })` run (Medium risk) — run manually and label it if the checked-out branch is not the task branch
- [ ] Tests written AND pass — output pasted into Evidence table (Hard-Stop Gate 5)
- [ ] `Skill({ skill: "verify" })` run
- [ ] `memory/MEMORY.md` updated (flag to Supervisor; sub-agents do not write memory)
- [ ] Supervisor notified: task ready for Stage 4 review
