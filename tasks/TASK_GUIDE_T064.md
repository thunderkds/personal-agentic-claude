# TASK_GUIDE — T064: Split reviewer-filled sections out of the implementer's guide
**Date**: 2026-08-09
**Complexity Level**: C2
**Risk Level**: Medium
**Priority**: P2
**Assigned agent**: Common-Infrastructure-Agent
**Agent guide**: `.claude/agents/common-infrastructure.md`

---

## Mandatory Startup (Do Not Skip)

Before writing any code:
1. Read `PROJECT_SPEC.md`
2. Read `memory/MEMORY.md`
3. Read this file completely
4. Read `.claude/agents/common-infrastructure.md`
5. Note the **Complexity Level** above and apply the matching process (brainstorm / decompose / verify depth / model) from the Complexity matrix in `.claude/agents/general-agent-template.md`
6. **C2 task**: read `memory/codebase-map.md` for directory layout, entry points, and blast-radius hotspots

---

## Requirement (Pillar 1 — Adapt the requirement)

Registered on `PROJECT_KANBAN.md` as "TASK_GUIDE format refactor — prose to challenge-response cards",
motivated by `templates/TASK_GUIDE_template.md` shipping to every downstream repo and T060's guide
running 6,836 tokens — larger than `CLAUDE.md` itself.

**Scope was changed by the user on 2026-08-09, before this guide was written.** The registered
direction (prose → challenge-response cards) is **rejected, not deferred** — see *Out of scope*. The
evidence that moved it:

- T063 established the guide is not injected verbatim; the agent opens it with `Read`. Its bytes are
  therefore **cache_read**, re-paid on every agent turn rather than once.
- Real T061 telemetry (the gate this task was waiting on) now shows `cache_creation` flat at
  **265–423 tokens** across a bare-`echo` probe (15,727 total), T067 (83,802) and T063 (111,056),
  regardless of guide size. A 6,800-token guide never appears in `cache_creation`.
- Measuring the two most recent guides by section shows the largest single block is not reasoning
  prose but **reviewer-filled scaffolding the implementer never uses**:

  | Section | T060 | T067 | Filled by |
  |---|---|---|---|
  | `## Demonstration` | 5,443 ch | 4,633 ch | reviewer, Stage 4/5 |
  | `### Evidence` (inside `## Evaluation & Acceptance`) | ~3,000 ch | ~3,200 ch | reviewer, Stage 4/5 |
  | `## Approach` | 5,693 ch | 3,026 ch | **implementer — keep** |
  | `## Requirement` | 2,135 ch | 2,543 ch | **implementer — keep** |

**Restated intent** (Supervisor's interpretation, in the project's domain language):
> Move the two reviewer-filled sections out of the file the implementing agent reads, into a sibling
> `tasks/TASK_REVIEW_Txxx.md`, so roughly a third of guide bytes stop being re-read on every agent
> turn — while every byte of reasoning prose (`Requirement`, `Approach`, `Acceptance Criteria`,
> `Edge Case Checklist`) stays exactly where it is.

**Out of scope** (what this task explicitly does NOT do):
- **Converting any prose to challenge-response cards. Rejected outright, not deferred.** T058 and
  T060 both landed correctly *because* their guides carried recorded risks, rejected directions and
  prior art in prose; a card format that compresses the *why* would delete the thing that made them
  work. AC11 pins this as a file-wide negative.
- Migrating any of the 20 existing `tasks/TASK_GUIDE_T*.md` files. This ships as a **fallback, not a
  migration** — see *Approach*.
- Trimming `templates/TASK_GUIDE_template.md` boilerplate, deduplicating startup reads, or shrinking
  `memory/MEMORY.md`. Those are T066 and T065.
- Any claim that this recovers the ~15.7k per-spawn floor. DDR-0004 already ruled that it does not.

**Requirement Refs**: none — this is harness-internal tooling with no `PRD.md` FR/NFR.

### Requirement Fidelity Gate (sign off BEFORE implementation)

- [x] Restated intent confirmed to match the user's request — scope explicitly chosen by the user 2026-08-09 over three stated alternatives
- [x] Domain terms align with `PROJECT_SPEC.md` glossary
- [x] Every Acceptance Criterion below traces to a line in the Requirement
- [x] Requirement Refs: N/A, stated rather than left blank

> An agent must NOT start implementing until this gate is checked. If anything here is unclear,
> STOP and ask the Supervisor (Karpathy: Think Before Coding).

---

## Dependencies & Reachability

**Depends on**: `None` — T061 telemetry (the registered gate) has landed and is quoted above.

**Entry point**: `TASK_REVIEW_` — the literal, grep-able filename prefix every new consumer resolves.

---

## Acceptance Criteria

| # | Criterion (testable) | Traces to requirement |
|---|----------------------|-----------------------|
| 1 | `templates/TASK_REVIEW_template.md` exists and contains `## Evidence` and `## Demonstration` with field names and ordering byte-identical to the versions removed from `TASK_GUIDE_template.md` | Restated intent |
| 2 | `templates/TASK_GUIDE_template.md` no longer contains `## Demonstration` or the `### Evidence` table, and carries a one-line pointer to the sibling review file in each vacated position | Restated intent |
| 3 | `templates/TASK_GUIDE_template.md` sections `## Requirement`, `## Acceptance Criteria`, `## Approach`, `## Edge Case Checklist` are **byte-identical** to their content at `HEAD` | Out of scope — prose preserved |
| 4 | `pre_agent_validate_guide.py` finds the Demonstration BEFORE field in `TASK_REVIEW_Txxx.md` when the guide has no `## Demonstration` section | Fallback, not migration |
| 5 | `pre_agent_validate_guide.py` still finds it **inline** in a legacy guide that has `## Demonstration` and no sibling review file | Fallback, not migration |
| 6 | `pre_bash_block_unsafe_merge.py` finds the filled `verify` Evidence row in `TASK_REVIEW_Txxx.md` when the guide lacks an Evidence table | Fallback, not migration |
| 7 | **P0 negative**: when a task has *neither* an inline Evidence table *nor* a sibling review file, the merge gate **still blocks**. It must fail closed. A refactor that makes the gate return "verified" on a missing file silently retires the gate | Fallback, not migration |
| 8 | `delivery-report/render.py` renders BEFORE/AFTER/DELTA and the `filled / total` Evidence count from a split pair, and still renders a legacy inline guide unchanged | Fallback, not migration |
| 9 | `render.py` still raises `NoDemonstrationBlock` for a pre-T053 guide that has neither an inline block nor a review file — the pre-T053 edge case is preserved, not swallowed by the new fallback | Fallback, not migration |
| 10 | **Negative**: writing `tasks/TASK_REVIEW_T999.md` does **not** cause `post_write_register_task.py` to add a `PROJECT_KANBAN.md` row (its regex anchors `TASK_GUIDE_(T\d+)\.md$`) | Surgical Changes |
| 11 | **Negative, file-wide**: the strings `challenge-response`, `challenge/response` and `Q:`/`A:` card scaffolding appear nowhere in `templates/TASK_GUIDE_template.md` | Out of scope — rejected direction |
| 12 | `.claude/skills/bugfix/SKILL.md`'s Step 3 skeleton splits the same two sections the same way, keeping the two flavors' field names identical (the property `delivery-report` depends on to need no flavor branch) | Restated intent |
| 13 | `craft-spawn-prompt` element 7 instructs the agent to write BEFORE into `tasks/TASK_REVIEW_Txxx.md`, and the spawn prompt embeds that path as a **literal absolute path**, not `$CLAUDE_PROJECT_DIR/...` | recorded gotcha |
| 14 | All 20 existing `tasks/TASK_GUIDE_T*.md` files are byte-identical to `HEAD` | Out of scope — no migration |
| 15 | Measured: a guide of T060's shape, split, is ≥25% smaller in bytes than the same guide inline | Restated intent |

---

## Evaluation & Acceptance (How we know the agent worked correctly)

> Fill **Success Criteria** and **Verification Command** at Stage 2 (before spawning the agent).
> The reviewer fills **Evidence** in `tasks/TASK_REVIEW_T064.md` at Stage 4/5.
> Rule: the implementing agent must NOT be the sole author of its own acceptance test — the
> Supervisor writes or signs off on the oracle first, so code and test can't be wrong together.

### Success Criteria (observable, pass/fail)

| # | Given (input/state) | Expect (output/behavior) | How it's checked |
|---|---------------------|--------------------------|------------------|
| 1 | Split pair: guide with no Demonstration + `TASK_REVIEW_T900.md` with a filled BEFORE | `pre_agent_validate_guide` emits **no** blank-BEFORE warning | automated test |
| 2 | Split pair where the review file's BEFORE is still the placeholder | warning **is** emitted — the fallback resolves the file, it does not assume it is filled | automated test |
| 3 | Legacy guide with inline `## Demonstration`, no review file | resolved inline, behaviour identical to `HEAD` | automated test |
| 4 | **Neither** inline Evidence nor review file, task in Ready for Review | merge gate **blocks** (AC7) | automated test |
| 5 | Review file present with a `verify \| pass \| ... pass` row, guide has no Evidence table | merge gate passes the row check (trace check unchanged) | automated test |
| 6 | Pre-T053 guide, no Demonstration anywhere | `render.py` raises `NoDemonstrationBlock` (AC9) | automated test |
| 7 | `Write` of `tasks/TASK_REVIEW_T999.md` | Kanban unchanged, zero new rows (AC10) | automated test |

### Verification Command (exact, runnable)

```bash
CLAUDE_ACTIVE_TASK=T064 pytest .claude/hooks/tests/ -q
```

### Evidence

> **Moved.** Filled by the reviewer at Stage 4/5 in `tasks/TASK_REVIEW_T064.md`.
> This task dogfoods its own change — T064's own review artifact uses the split layout.

---

## Demonstration

> **Moved.** See `tasks/TASK_REVIEW_T064.md`.

---

## Approach

**Pattern reference**: `.claude/hooks/lib/task_context.py` — `resolve_task_id()`'s ordered-precedence
resolution with fail-open error handling. The section resolver added here has the same shape: try
each source in a fixed order, return the first hit, never raise.
> Do **not** imitate `pre_agent_validate_guide.py`'s two-line path juggling (`TASK_GUIDE_{ref}` then
> `TASK_GUIDE_T{tid}`); it is duplicated at three call sites already and should not be quadrupled.

**Fallback, not migration.** Every consumer gains one resolution step: read the section from the
guide; if the guide does not contain it, read the sibling `tasks/TASK_REVIEW_Txxx.md`. All 20
existing guides keep both sections inline and every parser keeps finding them there, so no existing
guide is touched and no historical task changes behaviour. Only guides generated from the new
template are split. This is deliberate: this hook family has **five recorded parsing defects**
(T018/T022/T024/T042/T045) and a big-bang migration would put all 20 guides on the new path at once.

**Put the resolver in one place.** Add a single helper — suggested
`.claude/hooks/lib/guide_sections.py`, exporting something like
`read_guide_section(task_id, heading) -> str | None` — and have all three consumers call it. Three
independent copies of the same fallback is how this family produced five defects.

**The order matters and inline must win.** Guide first, review file second. A legacy guide with an
inline section must never be overridden by a stray review file.

**AC7 is the load-bearing one.** The merge gate currently reads the guide and blocks when it cannot
find a filled `verify` row. Adding a second source creates a way to get that wrong in the dangerous
direction: if "review file missing" is ever treated as anything other than "no evidence", the gate
stops gating and does so silently, on every task. Write that test before the implementation.

**Do not weaken the merge gate's regex.** `verify\s*\|[^|\n]+\|[^|\n]*pass` is pinned by tests and
encodes the T026 two-bug fix (the word `pass` must be in the *Notes* column, not just Result).
Change *where the text is read from*, never *what is matched*. Same family as the recorded learning
"when a test pins prose, fix the prose around it, not the test".

**MANIFEST is deliberately unchanged.** Line 11 is the bare directory entry `templates`, copied with
`cp -r`, so `TASK_REVIEW_template.md` deploys downstream automatically. Adding an explicit path
would break the file's convention — this is the same call made and recorded on T054.

---

## Edge Case Checklist

- [ ] Review file exists but is empty or truncated → treated as "section absent", never as an exception
- [ ] Review file is unreadable (permissions) → fail open for the advisory hook, fail **closed** for the merge gate
- [ ] Both inline section and review file present → inline wins, deterministically
- [ ] `task_id` reaches a filesystem path in the new helper → same sanitisation posture as `task_context.py`; do not introduce a traversal via `TASK_REVIEW_{unsanitized}.md` (T056 precedent: `session_id` reached a filename and was sanitised)
- [ ] Guide has `## Demonstration` as a heading but an empty body → distinguish "absent" from "present but blank"; AC/SC2 depends on this distinction
- [ ] A `##`-level heading quoted inside a review file's pasted output truncating the section regex → the recorded `###`-in-a-Kanban-row family; use `(?=^## |\Z)` with `re.MULTILINE`, as the existing regexes already do
- [ ] `render.py`'s Evidence `filled / total` count spanning a file boundary → count from wherever the table resolved, never sum both

---

## Files to Change (Predicted)

| File | Change |
|------|--------|
| `.claude/hooks/lib/guide_sections.py` | **new** — single ordered-precedence section resolver, never raises |
| `templates/TASK_REVIEW_template.md` | **new** — `## Evidence` + `## Demonstration`, fields byte-identical to what was removed |
| `templates/TASK_GUIDE_template.md` | remove both sections, leave a one-line pointer in each vacated position |
| `.claude/hooks/pre_agent_validate_guide.py` | BEFORE lookup goes through the resolver |
| `.claude/hooks/pre_bash_block_unsafe_merge.py` | Evidence-row lookup goes through the resolver; **fails closed** on absence |
| `.claude/skills/delivery-report/render.py` | Demonstration + Evidence-count lookup goes through the resolver; `NoDemonstrationBlock` preserved |
| `.claude/skills/delivery-report/SKILL.md` | document the split-pair input |
| `.claude/skills/bugfix/SKILL.md` | Step 3 skeleton split the same way |
| `.claude/skills/craft-spawn-prompt/SKILL.md` | element 7 targets the review file, literal absolute path |
| `.claude/hooks/tests/test_guide_sections.py` | **new** — AC4–AC10 |

## Files Must NOT Touch

| File | Reason |
|------|--------|
| `tasks/TASK_GUIDE_T0*.md` (all 20 existing) | AC14 — this is a fallback, not a migration |
| `MANIFEST` | directory entry already deploys the new template (T054 precedent) |
| `memory/MEMORY.md`, `memory/*.md` | Supervisor-only writes; flag learnings instead |
| `PROJECT_KANBAN.md` | Supervisor closes the row; also test-covered, an edit is a code change |
| `.claude/hooks/lib/task_context.py` | attribution is out of scope; imitate its shape, don't edit it |

---

## Test Plan

Write the AC7 fail-closed test **first**, before any resolver code — it is the one criterion whose
failure mode is silent and repo-wide.

Then per consumer, both directions: split pair resolves, legacy inline still resolves. Fixtures go in
`tmp_path` — never regenerate or write to any tracked file under `tasks/` or `reports/` (T059 was
exactly this defect, and in a worktree it destroyed data).

**Mutation-verify every negative criterion.** AC7, AC10, AC11 and AC14 all pass trivially against a
do-nothing implementation. For each, introduce the forbidden condition, observe RED, restore:
- AC7 — make the resolver return a filled-looking row on a missing file; the gate test must go RED
- AC11 — insert `challenge-response` into the template; must go RED
- AC14 — touch one byte of an existing guide; must go RED

Attack AC11 and AC15 from **more than one direction** — the recorded T067 finding is that an
assertion can be non-vacuous against one mutation and vacuous against another (there `rstrip("\n")`
made blank-line padding invisible while non-blank padding was caught). This is the 7th entry in the
vacuous-assertion family; treat a GREEN control as unproven until you have confirmed the mutation
actually executed (a Supervisor control on T063 sat after `sys.exit(main())` and never ran).

---

## Completion Checklist

- [ ] Implementation done
- [ ] Self-review: `Skill({ skill: "code-review" })` run
- [ ] Security review: `Skill({ skill: "security-review" })` run — **required, Medium risk**; check `git branch --show-current` first, the built-in diffs the checked-out branch
- [ ] Tests written AND pass — output pasted into `tasks/TASK_REVIEW_T064.md` (Hard-Stop Gate 5)
- [ ] `Skill({ skill: "verify" })` run
- [ ] UI Evidence rows marked ☐ N/A with justification — pure-backend task
- [ ] Learnings flagged to the Supervisor (do not write `memory/` yourself)
- [ ] Supervisor notified: task ready for Stage 4 review
