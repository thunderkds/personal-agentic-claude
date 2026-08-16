# TASK_GUIDE — T073: the memory-update hook tells every session not to commit tracked files
**Date**: 2026-08-16
**Complexity Level**: C1
**Risk Level**: Medium
**Priority**: P1
**Assigned agent**: Common-Infrastructure-Agent
**Agent guide**: `.claude/agents/common-infrastructure.md`

---

## Mandatory Startup (Do Not Skip)

Before writing any code:
1. Read `PROJECT_SPEC.md`
2. Read `memory/MEMORY.md`
3. Read this file completely
4. Read `.claude/agents/common-infrastructure.md`
5. Note the **Complexity Level** above and apply the matching process from the Complexity matrix in your role guide
6. C1, two files: `memory/codebase-map.md` is optional here

---

## Requirement (Pillar 1 — Adapt the requirement)

`.claude/hooks/post_bash_memory_update.py:33` ends the prompt it injects after every `git push` /
`git merge` with:

> `NOTE: memory/ writes are local-only (memory/* is gitignored except MEMORY.md). Do NOT commit or push the results of this pass — writing the files to disk is sufficient.`

**The premise is false.** Verified 2026-08-16:

- `git ls-files memory/` returns `MEMORY.md`, `codebase-map.md`, `decisions.md`, `glossary.md`,
  `learnings.md`, `feedback_no-claude-credit.md` and both Learning Records.
- `git check-ignore -v` matches **only** `memory/event-trace/` (`.gitignore:53`). It does not match
  `memory/decisions.md`, `memory/learnings.md` or `memory/glossary.md`.
- `.gitignore:5` states outright: *"task guides, memory contents, and planning docs are tracked"*.

So the hook fires after the exact operation that should carry the memory pass, and instructs the
Supervisor to leave tracked files dirty.

**Restated intent**:
> The post-`git` memory-update prompt must tell the truth about which memory files are tracked, so a
> Supervisor following it commits the cold-tier pass instead of leaving it uncommitted. Only
> `memory/event-trace/` is local-only.

**Why this is P1 and not cosmetic.** This is the mechanism behind an already-recorded loss. T046
shipped 2026-07-24 with a merged commit, passing tests and a closed Kanban row — and
`grep T046 memory/` was still empty two weeks later, because its whole memory pass sat in a forgotten
stash. The recorded learning is *"a memory pass is uncommitted work like any other, and stashes hide
it"*; this hook is the instruction that produces it. **Nothing downstream fails when memory is
missing**, so the defect is silent by construction and cannot be caught by the suite going red.

**Out of scope**:
- The hook's logic, trigger, routing table and the five numbered steps — only the trailing NOTE is wrong.
- Any broader audit of other hooks' prose. One location was swept for and one was found.
- `.gitignore` itself. It is correct; the prose describing it is not.
- Historical records that quote the old NOTE (`tasks/*`, `memory/decisions.md`, `PROJECT_KANBAN.md`,
  this guide) — they legitimately quote it and stay byte-identical.

**Requirement Refs**: no `PRD.md` in this repo. Source of record is `PROJECT_KANBAN.md`'s T073 row
plus the pre-flight sweep recorded below.

### Requirement Fidelity Gate (sign off BEFORE implementation)

- [x] Restated intent confirmed — user said "fix T073" after being shown the evidence
- [x] Domain terms align with `PROJECT_SPEC.md` (hot tier / cold tier / Memory Write Protocol)
- [x] Every Acceptance Criterion traces to the Requirement
- [x] N/A — no `PRD.md`

---

## Dependencies & Reachability

**Depends on**: `None`

**Entry point**: `post_bash_memory_update.py` — the `PostToolUse`/`Bash` hook registered in
`.claude/settings.json`; its prompt text reaches the Supervisor after every `git push`/`git merge`.

---

## Acceptance Criteria

| # | Criterion (testable) | Traces to requirement |
|---|----------------------|-----------------------|
| 1 | The NOTE in `post_bash_memory_update.py` no longer claims `memory/*` is gitignored except `MEMORY.md`, and no longer says not to commit | The premise is false |
| 2 | The replacement NOTE states positively that the cold-tier files **are** git-tracked and the pass **must** be committed | Restated intent |
| 3 | The replacement NOTE names `memory/event-trace/` as the **only** local-only path | Ground truth (`.gitignore:53`) |
| 4 | **Negative, file-wide**: the strings `gitignored except MEMORY.md`, `writes are local-only` and `Do NOT commit` do not appear anywhere in `.claude/hooks/*.py` | The retired-token pattern (T058/T065/T070/T071) |
| 5 | A new test asserts AC1–AC4 against the hook's **actual prompt constant**, imported from the module — not a copy of the string re-declared in the test | 7 recorded vacuous-assertion incidents; the newest is a helper that re-implements instead of calling |
| 6 | The new test asserts **ground truth, not just prose**: it runs `git check-ignore` on `memory/decisions.md` (expect: not ignored) and on a `memory/event-trace/` path (expect: ignored), so the NOTE and reality are checked against each other rather than the NOTE against itself | The defect was prose contradicting `.gitignore`; only a cross-check catches a recurrence |
| 7 | The hook's logic is byte-identical apart from the NOTE constant: trigger condition, the 5 numbered steps, the routing line and `main()` unchanged | Out of scope |
| 8 | Existing suite still green, unmodified — in particular `test_memory_channel_and_budget.py`, which lists this file in `SHIPPING_FILES` for its negative content sweeps | No test-loosening |
| 9 | **Added 2026-08-16.** In `.claude/hooks/tests/test_vital_slice.py::test_ac12_no_enforcement_machinery_was_added`, the **byte-identity half is deleted** — the `changed` list, its loop body and its `assert not changed`. The **content half is kept byte-identical**: `mentions`, the `"Vital slice" in p.read_text(...)` check, and `assert not mentions` with its message unchanged. Nothing else in that file is touched | Supervisor ruling 2026-08-16; the recorded "exclude by content, never by ref" rule |
| 10 | **Added 2026-08-16, mutation-verified.** After the edit, `test_ac12` must still go **RED** when a non-test hook is made to reference the advisory field — append `# Vital slice` to any `.claude/hooks/*.py` and confirm failure. This is the assertion that actually enforces DDR-0005 §5; if it stops discriminating, the deletion removed the guard instead of the scope guard | Guards against the narrowing silently disarming the real check |

---

## Evaluation & Acceptance

### Success Criteria (observable, pass/fail)

| # | Given | Expect | How it's checked |
|---|---|---|---|
| 1 | The hook's prompt constant after the change | Contains a positive "commit the cold files" instruction and names `memory/event-trace/` as the only exception | automated test |
| 2 | `grep -rn 'gitignored except MEMORY.md\|Do NOT commit' .claude/hooks/*.py` | zero hits | automated test (negative) |
| 3 | `git check-ignore memory/decisions.md` | non-zero exit (**not** ignored) | automated test, ground truth |
| 4 | `git check-ignore memory/event-trace/x.jsonl` | zero exit (**is** ignored) | automated test, ground truth |
| 5 | **Mutation**: restore the old NOTE text | AC4's negative goes **RED** | mutation control, must be observed |
| 6 | **Mutation**: add `memory/decisions.md` to `.gitignore` | AC6's ground-truth check goes **RED** | mutation control — proves the cross-check is live, not decorative |

### Verification Command (exact, runnable)

```bash
cd /home/hungnguyenhuu/workspace/pets/personal-agentic-claude && \
  python -m pytest .claude/hooks/tests/ -q > /tmp/t073.log 2>&1; echo "pytest exit=$?"; tail -3 /tmp/t073.log
```

> Do not pipe pytest into `tail` behind `&&` — `tail` always exits 0 and `&&` gates on the last
> command of the pipeline.

### Evidence (filled by reviewer at Stage 4/5)

> Filled in `tasks/TASK_REVIEW_T073.md`. All three UI rows are ☐ N/A — no UI component.

---

## Demonstration

> See `tasks/TASK_REVIEW_T073.md`.

---

## Approach

**Pattern reference**: `.claude/hooks/tests/test_memory_channel_and_budget.py` — it already sweeps
`SHIPPING_FILES` (which includes this hook) for retired claims, and its `UNRELATED_200_LINES` block
shows the house style for excluding a legitimate hit **by content, never by count**. Imitate that
structure for AC4's negative.

**Vital slice**: the NOTE constant in `post_bash_memory_update.py`, plus one test that cross-checks it
against `git check-ignore`. That is the whole defect and the whole guard.

**Cut list**:
- A sweep of every other hook's prose for unrelated inaccuracies — speculative; the sweep for *this*
  claim found exactly one location.
- Making the hook compute the ignore status at runtime instead of stating it. Rejected: it would put
  a `git check-ignore` subprocess in a hook that currently only prints, adding a failure mode to fix
  a sentence. The test does the checking; the hook keeps printing.
- Rewording the five numbered steps for consistency while in the file — adjacent-code improvement,
  which Surgical Changes forbids.
- Backfilling the historical records that quote the old NOTE. They are dated evidence.

**Reasoning.** The fix is one string; the *value* is in AC6. A test that only asserts the new prose
exists would pass just as happily if `.gitignore` changed underneath it tomorrow — which is precisely
how this defect survived. Asserting the prose and the ground truth **against each other** is what
makes the guard durable, and it is cheap here because `git check-ignore` is a two-line subprocess.

---

> ### Stage 3 amendment, 2026-08-16 — why AC9/AC10 exist
>
> The agent halted before committing: this task's one-line hook edit turns
> `test_vital_slice.py::test_ac12_no_enforcement_machinery_was_added` red. That test pins **every**
> non-test `.claude/hooks/*.py` byte-identical to `b69410c`. Verified independently by the Supervisor.
>
> **It is occurrence 7 of "a scope guard committed as an invariant", it was written during T071, and
> the Supervisor signed it off at T071's Stage 4** — while explicitly ruling that AC11's line caps
> were an acceptable budget, and missing the byte-identity glob one function below. The learning was
> written to `memory/learnings.md` the same day and then violated by its own author on the next task.
>
> **The fix was already inside the test.** It carries two assertions: `changed` (byte-identity of
> every hook — the scope guard) and `mentions` (no hook contains the string `Vital slice` — the real
> guard). Only `mentions` enforces DDR-0005 §5's refusal of a gate, and being content-based it stays
> true indefinitely and still catches a genuine regression. `changed` answered "did T071 add
> machinery?", a question that only meant something during T071's review.
>
> Ruling: **delete `changed`, keep `mentions`** — the recorded "exclude by content, never by ref"
> rule. Repointing `PRE_TASK_REF` (T070's precedent) was rejected here: it preserves both assertions
> but simply moves the wall to T073's commit, so the next hook edit hits it again. AC10 exists
> because deleting half of a two-assertion test is the easiest way to remove the wrong half.

## Edge Case Checklist

- [ ] `git check-ignore` exit codes are inverted from intuition: **0 means ignored**, 1 means not. Assert on the code deliberately, and add a comment — a reversed assertion here passes for the wrong reason.
- [ ] `memory/event-trace/` may be empty or absent in a fresh clone; `check-ignore` works on a path that does not exist, so do not create a file to test it.
- [ ] The hook text is also quoted in `PROJECT_KANBAN.md` and this guide — AC4 is scoped to `.claude/hooks/*.py`, not repo-wide, so those legitimate quotes do not trip it.
- [ ] Do not import the module by path with `importlib.spec_from_file_location` and then assume identity with an imported copy — recorded gotcha; import it once and read the constant off that object.
- [ ] `.claude/settings.json` registers the hook; do not touch registration.

---

## Files to Change (Predicted)

| File | Change |
|------|--------|
| `.claude/hooks/post_bash_memory_update.py` | the trailing NOTE only |
| `.claude/hooks/tests/test_memory_hook_note_truthfulness.py` | **new** — AC1–AC8 |

## Files Must NOT Touch

| File | Reason |
|------|--------|
| `.gitignore` | It is correct. The prose was wrong |
| `.claude/settings.json` | Hook registration is out of scope |
| `.claude/hooks/tests/test_memory_channel_and_budget.py` | AC8 — it must stay green unmodified |
| `.claude/hooks/tests/test_vital_slice.py` — everything except the `changed` half of `test_ac12` | AC9 permits deleting exactly that one assertion and its loop body. The other 36 tests, `PRE_TASK_REF`, and the `mentions` content check stay byte-identical |
| `post_bash_memory_update.py`'s logic, steps and routing | AC7 — NOTE constant only |
| `tasks/*`, `memory/decisions.md`, `PROJECT_KANBAN.md` | Dated records that legitimately quote the old text |

---

## Test Plan

One new test module. Import the hook module and read its prompt constant — do **not** re-declare the
string. Cover AC1–AC4 as prose assertions and AC6 as a `git check-ignore` cross-check, then run both
mutation controls and observe RED before reverting. Commit before mutating.

Full suite must be green: `python -m pytest .claude/hooks/tests/ -q` (442 at HEAD).

---

## Completion Checklist

- [ ] Implementation done
- [ ] Tests written AND pass — output pasted into `tasks/TASK_REVIEW_T073.md`'s Evidence table (Hard-Stop Gate 5)
- [ ] Both mutation controls observed RED, then reverted
- [ ] Supervisor notified: ready for Stage 4 review

> Stage 4/5 gates are the Supervisor's to run — a sub-agent has no `Skill` tool. Do not record a
> result for `code-review`, `security-review` or `verify`.
