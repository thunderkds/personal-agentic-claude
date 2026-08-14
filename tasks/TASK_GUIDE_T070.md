# TASK_GUIDE — T070: Repoint the stale Complexity-matrix pointers at the guaranteed channel
**Date**: 2026-08-13
**Complexity Level**: C2
**Risk Level**: Medium
**Priority**: P2
**Assigned agent**: common-infrastructure
**Agent guide**: `.claude/agents/common-infrastructure.md`

---

## Mandatory Startup (Do Not Skip)

Before writing any code:
1. Read `PROJECT_SPEC.md`
2. Read `memory/MEMORY.md`
3. Read this file completely
4. Read `.claude/agents/common-infrastructure.md`
5. Note the **Complexity Level** above (C2) and apply the matching process from the Complexity matrix in your role guide
6. **C2/C3 or multi-file tasks only**: read `memory/codebase-map.md` for directory layout, entry points, and blast-radius hotspots

If docs/legacy/ exists (legacy mode): also read `docs/legacy/risk-hotspots.md` and `docs/legacy/architecture.md`.

---

## Requirement (Pillar 1 — Adapt the requirement)

From the `PROJECT_KANBAN.md` Todo row registered 2026-08-10 out of T069's Stage 2:

> two pointers now name a channel that no longer holds the content. `CLAUDE.md:86` ("see the
> Complexity matrix in `.claude/agents/general-agent-template.md`") and
> `docs/claude-md/pipeline-stages.md:118` (same claim, in the Stage 2 labelling instructions) both
> direct the reader to a file from which T066 removed the C0–C3 matrix — it now lives in each role
> guide. Same class as T069 one level up: a reference that survives the move of the thing it
> references. […] Stage 2 must confirm whether `test_agent_guide_dedup.py`'s AC5 byte-identity pin
> on `CLAUDE.md` has to be repointed to a new baseline ref as part of the fix

**Restated intent** (Supervisor's interpretation, in the project's domain language):
> Every surviving instruction that sends a reader to `.claude/agents/general-agent-template.md` for
> the C0–C3 Complexity matrix must instead send them to the role guide, which is the channel that
> actually carries it — without loosening the test that pins `CLAUDE.md` byte-identical, and without
> rewriting the ~35 historical TASK_GUIDEs that record the old wording.

**Stage 2 finding — the row named two locations; the sweep found three.**

`grep -rn "Complexity matrix|matrix in \`" --include='*.md' --include='*.py' --include='*.sh'`
over the whole repo on 2026-08-13 classifies every hit into exactly four buckets:

| Bucket | Locations | Disposition |
|---|---|---|
| **Stale, shipping — must fix** | `CLAUDE.md:86`, `docs/claude-md/pipeline-stages.md:118`, **`templates/TASK_GUIDE_template.md:18`** | rewritten by this task |
| Already correct | `README.md:72` ("Each role guide carries its own … Complexity matrix"), `.claude/agents/general-agent-template.md:8` (describes the move) | untouched |
| Historical record | ~35 `tasks/TASK_GUIDE_T0*.md` line 18, `tasks/TASK_REVIEW_T066.md`, `memory/decisions.md:858` | untouched, byte-identical |
| Live board prose | `PROJECT_KANBAN.md`, `BRAINSTORMING_LOG.md` | untouched by the agent |

**`templates/TASK_GUIDE_template.md:18` is the one the row missed and the most valuable of the
three.** `MANIFEST:11` ships the bare `templates` directory to every downstream repo, and line 18 is
step 5 of the Mandatory Startup block that *every* implementing agent reads at the top of *every*
future task. The other two are Supervisor-facing; this one is the only stale pointer sitting in the
guaranteed channel of the reader it misdirects. This is the recorded learning *"retiring a
convention touches more places than the AC table enumerates"* firing for the third time (T058,
T065, now T070) — and the second time in a row where the Supervisor's own Stage 2 row under-counted
before the sweep ran.

**Out of scope** (what this task explicitly does NOT do):
- Rewriting the ~35 existing `tasks/TASK_GUIDE_T0*.md` files. They are the historical record of what
  each agent was actually told; back-editing them falsifies the audit trail and would be a ~35-file
  diff on a C1-registered task. Precedent: T064 shipped **fallback, not migration**, leaving all 20
  then-existing guides inline and asserting them byte-identical.
- Any change to the Complexity matrix content itself, in any role guide.
- Any change to `general-agent-template.md`. Line 8 correctly *describes* where the matrix went; it
  is not a stale pointer.
- Re-litigating T066's move or T069's split-by-mandate ruling. This task fixes references only.
- `README.md`. Already accurate as of `304e6e6`.

**Requirement Refs**: none — this is harness-internal maintenance registered from a Stage 4 finding,
not a `PRD.md` feature. Stated rather than left blank.

### Requirement Fidelity Gate (sign off BEFORE implementation)

- [x] Restated intent confirmed to match the user's request (Supervisor, from the Kanban row + user's "run Stage 2 for T070")
- [x] Domain terms align with `PROJECT_SPEC.md` glossary — "guaranteed channel", "role guide", "Complexity matrix" all as established by T066/T069
- [x] Every Acceptance Criterion below traces to a line in the Requirement
- [x] Requirement Refs: none exist in `PRD.md`; recorded as N/A above rather than fabricated

> An agent must NOT start implementing until this gate is checked. If anything here is unclear,
> STOP and ask the Supervisor (Karpathy: Think Before Coding).

---

## Dependencies & Reachability

**Depends on**: `None` — T069 is merged (`c635e5c`), which is what made these pointers stale.

**Entry point**: `general-agent-template.md` — the literal substring whose remaining occurrences in
the three shipping files are exactly what this task retires. AC4's file-wide negative greps for it.

---

## Acceptance Criteria

| # | Criterion (testable) | Traces to requirement |
|---|----------------------|-----------------------|
| 1 | `CLAUDE.md:86` no longer names `general-agent-template.md` as the matrix's location; it points at the role guide | "CLAUDE.md:86 … directs the reader to a file from which T066 removed the matrix" |
| 2 | `docs/claude-md/pipeline-stages.md:118` likewise, with the surrounding hub-file / Risk / Priority prose byte-identical apart from the pointer clause | "same claim, in the Stage 2 labelling instructions" |
| 3 | `templates/TASK_GUIDE_template.md:18` likewise | Stage 2 finding — third location, ships to every downstream repo |
| 4 | **Negative**: across those three files, zero lines pair a Complexity-matrix claim with `general-agent-template.md`. Asserted per-file with an explicit existence check on each path first | "a reference that survives the move of the thing it references" |
| 5 | **Positive**: for each of the four role guides, the file the new pointers name actually contains `## Complexity & escalation`. The pointer target is verified to hold the content, not merely to differ from the old one | the defect class itself — a pointer is only fixed if its new target is real |
| 6 | `test_agent_guide_dedup.py`'s AC5 pin still asserts `CLAUDE.md` byte-identity, with the assertion **shape** unchanged (`read_bytes() == read_at(rel, <ref>)`), repointed to a new baseline ref capturing the pre-T070 state. The `MANIFEST` half stays on `BASELINE_REF = "8fc4dd2"` | "Stage 2 must confirm whether the AC5 byte-identity pin has to be repointed" |
| 7 | **Negative**: the ~35 `tasks/TASK_GUIDE_T0*.md`, `tasks/TASK_REVIEW_T066.md`, `README.md`, `memory/decisions.md` and `.claude/agents/general-agent-template.md` are byte-identical to their pre-task state | Out of scope — historical record, T064 fallback-not-migration precedent |
| 8 | Full suite green (`394 passed` baseline or higher) and `test_memory_channel_and_budget.py` still green, since its `SHIPPING_FILES` list includes `CLAUDE.md` | no collateral breakage on a hub file |

---

## Evaluation & Acceptance (How we know the agent worked correctly)

### Success Criteria (observable, pass/fail)

| # | Given (input/state) | Expect (output/behavior) | How it's checked |
|---|---------------------|--------------------------|------------------|
| 1 | the three shipping files after the fix | zero Complexity-matrix→template pointers | automated test (AC4) |
| 2 | a mutation re-inserting the old clause into any one of the three | AC4 goes RED, naming that file | mutation control, run three times — once per file |
| 3 | a mutation deleting `## Complexity & escalation` from one role guide | AC5 goes RED | mutation control |
| 4 | a mutation appending one byte to `CLAUDE.md` | AC6 goes RED | mutation control |
| 5 | a mutation pointing AC4 at a non-existent path | the test ERRORS on the existence check, never free-passes | mutation control (the recorded negative-grep trap) |
| 6 | `tasks/TASK_GUIDE_T044.md` (a historical guide) | still carries the old line 18, unmodified | automated test (AC7) |

### Verification Command (exact, runnable)

```bash
# MUST be run from the repository root — see the note below.
cd <repo-root> && python -m pytest .claude/hooks/tests/ -q > /tmp/t070.log 2>&1; echo "exit=$?"; tail -3 /tmp/t070.log
```

> Do **not** pipe pytest into `tail` behind `&&` — recorded gotcha: `tail` always exits 0 and `&&`
> gates on the last command of the pipeline, so a red suite commits clean. Redirect, then read `$?`.
>
> **Run it from the repo root, not from `.claude/hooks/`.** Verified at Stage 2 on 2026-08-13: root
> gives `394 passed, exit=0`; `cd .claude/hooks && pytest tests/` gives `1 failed, 393 passed` —
> `test_task_guide_template_verify_row.py:62` opens `templates/TASK_REVIEW_template.md` through a
> **cwd-relative** path while its neighbours resolve from `Path(__file__).parents[3]`. That failure is
> pre-existing and unrelated to T070; do not "fix" it here and do not read it as a T070 regression.
> Baseline to beat: **394 passed**.

### Evidence (filled by reviewer at Stage 4/5)

> **Moved.** Filled by the reviewer at Stage 4/5 in `tasks/TASK_REVIEW_T070.md`.

---

## Demonstration

> **Moved.** See `tasks/TASK_REVIEW_T070.md`.

---

## Approach

**Pattern reference**: `.claude/hooks/tests/test_agent_guide_dedup.py` — specifically the
`BASELINE_REF` / `T069_BASELINE_REF` pair already in that file (lines 41 and 45). T069 hit this exact
situation and solved it by introducing a *second* named ref constant rather than moving the first.
Imitate that: add `T070_BASELINE_REF` and split the parametrize so each file is pinned to the
baseline that is correct for it.

**The AC6 repoint is the load-bearing part and has a recorded wrong answer.**
`test_agent_guide_dedup.py:184-190` parametrizes over `["CLAUDE.md", "MANIFEST"]` and asserts each is
byte-identical to `read_at(rel, BASELINE_REF)` with `BASELINE_REF = "8fc4dd2"`. AC1 edits `CLAUDE.md`,
so that assertion goes RED by construction — no correct implementation satisfies both AC1 and the
test as written. This is the T064-recorded *"a test can pin a section's location"* family, and the
governing rule is explicit: **repoint with the assertion byte-identical in shape, never loosen it,
never delete it.** Deleting the parametrize entry would silently retire the protection T066 put
there — that `CLAUDE.md`'s overlap with the agent guides is cross-context redundancy and must not be
collapsed. That property is still true after T070 and must still be guarded.

Concretely: keep the test, split the ref.

```python
BASELINE_REF = "8fc4dd2"          # unchanged — MANIFEST
T070_BASELINE_REF = "<pre-T070 sha>"  # CLAUDE.md, repointed by T070
```

Capture `<pre-T070 sha>` from the commit immediately before the `CLAUDE.md` edit, the same way T069
captured `8d6d56b` with an explicit BEFORE-capture commit. Do not use a branch name or `HEAD~1`.

**Wording for the three replacements.** Use T069's own phrasing from
`tasks/TASK_GUIDE_T069.md:18` — *"the Complexity matrix in your role guide"* — for the template,
whose reader is the implementing agent and does have a role guide. `CLAUDE.md` and
`pipeline-stages.md` address the **Supervisor**, who has no role guide, so those two must name the
directory instead: *"the Complexity matrix in each role guide (`.claude/agents/<role>.md`)"*. Do not
apply one phrasing to all three — the correct pointer depends on who is reading, which is the whole
lesson of T066.

**Why Risk is Medium and Complexity C2, both raised from the row's C1/Low.**
`docs/claude-md/pipeline-stages.md:118` — the very line being edited — states the rule that settles
this: *"A hub touch raises Risk a level even when the edit itself is small."* `CLAUDE.md` is the
harness's hub document and `templates/TASK_GUIDE_template.md` ships into every downstream repo, so
Low→Medium follows from the project's own written rule applied to itself. C1→C2 follows from scope
growth found at Stage 2: three shipping files rather than two, plus a pinned-test repoint that has
a documented wrong answer. Medium Risk makes `security-review` mandatory at Stage 4 — expected to be
trivially PASS (prose only, no executable surface), but it must be **run and labelled**, not assumed.
Hard-Stop Gate 2's C2 floor does **not** apply here; none of its trigger words are present. If the
user considers C2/Medium inflated for a three-line prose fix, that is a reasonable objection and the
labels can be dropped back on their instruction — but not silently.

---

## Edge Case Checklist

- [ ] The `pipeline-stages.md:118` sentence is long and carries hub-file, legacy-mode and Risk rules that have nothing to do with the pointer. Replace the pointer clause only; leave the rest byte-identical.
- [ ] `templates/TASK_GUIDE_template.md` uses the `[agent-file].md` placeholder at line 17. Keep line 18's new wording consistent with that placeholder convention rather than hard-coding one role.
- [ ] AC4's negative must exclude by **content**, never by allowing "one hit" or by a file count — the recorded negative-grep trap. Assert each of the three paths **exists** first, so a typo errors loudly rather than free-passing.
- [ ] AC7 must not be written as "no other file changed" via a broad `git status` check — the agent legitimately adds a test file. Enumerate the protected paths.
- [ ] `test_memory_channel_and_budget.py:52` lists `CLAUDE.md` in `SHIPPING_FILES` for a memory-channel content negative. The strings are unrelated and it should stay green — verify it, do not assume it.
- [ ] `post_write_register_task.py` auto-registers a stub Kanban row on the Write of a TASK_GUIDE. T070's row already exists in Todo — re-read the Kanban section before committing and remove any duplicate stub.
- [ ] One suite test resolves a path from the **cwd**, not from `__file__`, so the same tree reads green from the repo root and red from `.claude/hooks/`. Write T070's new test resolving from `Path(__file__).resolve().parents[3]` like its neighbours, so it cannot inherit this.
- [ ] Do not let the AC6 repoint drift into pinning a count or hash captured "as of this task" beyond the one byte-identity ref — the recorded T065 scope-guard-as-invariant failure.

---

## Files to Change (Predicted)

| File | Change |
|------|--------|
| `CLAUDE.md` | line 86 — repoint the matrix reference at the role guides (AC1) |
| `docs/claude-md/pipeline-stages.md` | line 118 — repoint the matrix reference, rest of the sentence untouched (AC2) |
| `templates/TASK_GUIDE_template.md` | line 18 — repoint the matrix reference (AC3) |
| `.claude/hooks/tests/test_agent_guide_dedup.py` | add `T070_BASELINE_REF`, split the AC5 parametrize so `CLAUDE.md` pins to it and `MANIFEST` stays on `BASELINE_REF` (AC6) |
| `.claude/hooks/tests/test_complexity_matrix_pointers.py` | **new** — AC4, AC5, AC7 |

## Files Must NOT Touch

| File | Reason |
|------|--------|
| `tasks/TASK_GUIDE_T0*.md` (~35 files) | historical record of what each agent was told; T064 fallback-not-migration precedent. AC7 pins them |
| `tasks/TASK_REVIEW_T066.md`, `memory/decisions.md` | completed-work record |
| `README.md` | already correct as of `304e6e6` |
| `.claude/agents/general-agent-template.md` | line 8 describes the move; it is not a stale pointer |
| `.claude/agents/{common-infrastructure,backend,frontend,qa}.md` | this task changes references, never matrix content. AC5 reads them, does not write them |
| `MANIFEST` | already ships `templates` and `docs/claude-md` as directory entries; still pinned byte-identical by the untouched half of AC5/AC10 |

---

## Test Plan

1. Write AC4 and AC5 **first**, RED against the current tree — AC4 must fail naming all three files.
2. Apply the three prose edits. AC4/AC5 go GREEN; `test_agent_guide_dedup.py`'s AC5 pin goes RED.
3. Commit the BEFORE state, capture its sha, repoint `CLAUDE.md` to `T070_BASELINE_REF` (AC6).
4. Add AC7's protected-path byte-identity assertions.
5. Run the five mutation controls in Success Criteria. For each: confirm the mutation actually landed
   (`git diff --stat`) *before* reading the verdict — a mutation that does not execute proves nothing —
   and revert with `cp` from a backup, never `git checkout`, which would also revert the fix.
6. Full suite + `scripts/smoke-install.sh`, exit codes captured without a pipe.

---

## Completion Checklist

- [ ] Implementation done
- [ ] Self-review: `code-review` run (Supervisor — a sub-agent has no `Skill` tool)
- [ ] Security review: `security-review` run — **mandatory at Medium risk**; check `git branch --show-current` first, or the built-in diffs main-vs-main and returns a false PASS
- [ ] Lint passes
- [ ] Tests written AND pass — output pasted into `tasks/TASK_REVIEW_T070.md`'s Evidence table (Hard-Stop Gate 5)
- [ ] `verify` run — feature confirmed working
- [ ] UI/Design Evidence rows marked ☐ N/A with justification (no UI component; section deleted above per Gate 6)
- [ ] `memory/MEMORY.md` updated (if new patterns learned)
- [ ] Supervisor notified: task ready for Stage 4 review
