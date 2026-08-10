# TASK_GUIDE — T069: Move the Karpathy table into the guaranteed channel
**Date**: 2026-08-10
**Complexity Level**: C2
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
5. Note the **Complexity Level** above (C2) and apply the matching process from the Complexity matrix in your role guide
6. C2 — read `memory/codebase-map.md` for directory layout and blast-radius hotspots
7. Read `.claude/hooks/tests/test_agent_guide_dedup.py` and `scripts/test-agent-template.sh` **before editing anything** — both encode the rules this task operates under, and one of them pins content in the file this task vacates

---

## Requirement (Pillar 1 — Adapt the requirement)

Registered from T066's Stage 4 review, and deliberately not treated as a T066 regression: the
compact Karpathy Engineering Principles table and the `Search Before You Build` ladder live **only**
in `.claude/agents/general-agent-template.md`, both before and after T066. The harness auto-loads
`.claude/agents/<role>.md` as an agent's system prompt, so a **role guide always arrives**, while
the template arrives only if the agent chooses to open it. The two things T041 inlined *specifically
because `CLAUDE.md` never reaches an agent* therefore sit one hop behind a read the agent may skip —
the identical failure class, one level down, and the third instance of "already covered must mean
reaches-the-context".

**Restated intent** (Supervisor's interpretation):
> Every sub-agent must receive the Karpathy Engineering Principles through a channel the harness
> guarantees, not through an optional read — without giving back the per-spawn saving T066 measured.

**Direction locked by the user 2026-08-10 — split by mandate.** Of the three options the Kanban row
listed, none is taken as written; the measurement below produced a fourth, and it is the one that
ships:

- The **Karpathy table is a Permanent Rule** — `CLAUDE.md` states the principles are "mandatory for
  the Supervisor and all sub-agents". A mandatory rule reachable only through an optional read is
  the defect. It moves **into all four role guides**.
- The **Search-Before-You-Build ladder is advisory** — a T041 checklist that shortens code. It
  **stays in the template**, referenced, and is pinned byte-identical by AC7.

**Evidence that settled the split** (measured by the Supervisor at Stage 2, 2026-08-10):

| Section | chars | ×4 roles |
|---|---|---|
| Karpathy compact table | 622 | 2,488 |
| Search-Before-You-Build ladder | 1,045 | 4,180 |

T066's measured per-spawn saving (role guide + template **pair**, which is what an agent actually
pays): c-infra −480, backend −2,142, frontend −2,123, qa −2,165 chars. Against that baseline:

| Option | c-infra | backend | frontend | qa |
|---|---|---|---|---|
| Inline **both** sections | **+1,187** | −475 | −456 | −498 |
| Inline the **table only** | +142 | −1,520 | −1,501 | −1,543 |

Inlining both erases ~78% of T066's saving and makes `common-infrastructure` — the most-used role —
net **worse than before T066**. Inlining the table alone keeps ~71%.

**And the shipped design is cheaper still.** Because the table is removed from the template once all
four role guides carry it, the pair cost is `+622` (role guide) `−622` (template) = **0 net chars
per spawn**. This task converts an optional read into a guaranteed one at zero measured cost. AC9
requires that number to be measured and pasted, not asserted — including a stated null result rather
than a reframed one.

**Option B is already shipped and is the thing that is not working.** All four role guides already
carry `4. Read .claude/agents/general-agent-template.md` in their startup sequence. Event trace
across 66 task buckets: **9 `Read` records on the template, in 4 buckets** (T001×3, T065, T066,
`_untagged`×4) — a floor, not a rate, since per T063 the active-task pointer arms after the startup
reads. Adding a second instruction to read it would repeat exactly what T065 disproved about
`craft-spawn-prompt` element 4: an instruction is not a channel.

**Out of scope**:
- The Search-Before-You-Build ladder's location. It stays in the template. AC7 pins it.
- `CLAUDE.md:86` and `docs/claude-md/pipeline-stages.md:118` both point at "the Complexity matrix in
  `.claude/agents/general-agent-template.md`", which T066 moved into the role guides. These are real
  stale pointers of the same class, found during this Stage 2 — **registered as T070, not fixed
  here**. Touching them is out of scope (Karpathy: Surgical Changes).
- Any change to `CLAUDE.md`. It never reaches a sub-agent; its full Karpathy section is
  cross-context redundancy that T066 pinned byte-identical, and that ruling stands.
- Content edits to the table itself. It moves verbatim; this task changes *where it lives*, not
  what it says.

**Requirement Refs**: none — this is an internal framework-integrity task with no `PRD.md` FR.
Traceability is to the T069 Kanban row and T066's Stage 4 finding.

### Requirement Fidelity Gate (sign off BEFORE implementation)

- [x] Restated intent confirmed to match the user's request — direction chosen by the user
      2026-08-10 from a Supervisor-measured three-way comparison
- [x] Domain terms align with the glossary — "guaranteed channel" is T066's term, already in
      `memory/decisions.md`
- [x] Every Acceptance Criterion below traces to a line in the Requirement
- [x] No `PRD.md` refs claimed, so none to cover

---

## Dependencies & Reachability

**Depends on**: `None` — T066 is merged to `main` (`d0b9f34`), and its test module is the substrate
this task builds on.

**Entry point**: `## Karpathy Engineering Principles (Compact)`
> The literal H2 whose location this task changes. Grep-able in every file it must appear in and in
> the one file it must disappear from.

---

## Acceptance Criteria

| # | Criterion (testable) | Traces to requirement |
|---|----------------------|-----------------------|
| 1 | `## Karpathy Engineering Principles (Compact)` and its four-row table appear in **all four** role guides, byte-identical to the template's current table | mandatory rule must reach the guaranteed channel |
| 2 | The table is **removed** from `.claude/agents/general-agent-template.md` — and only after AC1 holds, per the existing invariant at `test_agent_guide_dedup.py:119` | zero net cost; no duplication inside one context |
| 3 | `scripts/test-agent-template.sh` AC1 is **repointed** at the four role guides with its principle/command strings byte-identical, and additionally asserts the template no longer carries them | a test pins a section's *location* — the T064 family |
| 4 | `test_agent_guide_dedup.py` AC6 asserts the Karpathy table is reachable from each role guide **directly**, not via the template | the reachability claim must mean the guaranteed channel |
| 5 | `.claude/skills/craft-agent/SKILL.md` emits the table in newly generated role guides | a new role must not be born without a Permanent Rule (T066 edge case #6) |
| 6 | The template's header note and `## Staleness Guard` are updated — both currently name the Karpathy principles as living "above" | the file must not describe content it no longer has |
| 7 | `## Search Before You Build` is **byte-identical** in the template and appears in **no** role guide | pinned negative — the advisory half does not move |
| 8 | `AGENTS.md` remains an accurate mirror for non-Claude CLIs after the move | Staleness Guard's own instruction |
| 9 | Per-role before/after **character** counts for the role-guide + template pair are measured and pasted; a null result is stated as null | zero-net-cost claim must be measured, not asserted |
| 10 | Full suite green: `pytest .claude/hooks/tests`, `scripts/test-agent-template.sh`, `scripts/validate.sh`, `scripts/smoke-install.sh` | no regression |

---

## Evaluation & Acceptance

### Success Criteria (observable, pass/fail)

| # | Given (input/state) | Expect (output/behavior) | How it's checked |
|---|---------------------|--------------------------|------------------|
| 1 | Each of the four role guides | contains the four principle names and their operational commands inline | automated test |
| 2 | `general-agent-template.md` | contains neither the Karpathy H2 nor any of the four operational-command strings | automated test |
| 3 | `general-agent-template.md` | still contains `## Search Before You Build` with all 7 rungs, byte-identical to `main` | automated test + `git diff` |
| 4 | Mutation: delete the table from **one** role guide (e.g. `qa.md`) | AC1's test goes **RED** naming that role | mutation control |
| 5 | Mutation: restore the table to the template while leaving the role guides intact | AC2's test goes **RED** | mutation control |
| 6 | Mutation: delete the ladder from the template | AC7's test goes **RED** | mutation control |
| 7 | A role guide generated by `craft-agent` | carries the Karpathy table | automated test against the skill's emitted structure |

### Verification Command (exact, runnable)

```bash
cd /home/hungnguyenhuu/workspace/pets/personal-agentic-claude
python3 -m pytest .claude/hooks/tests -q
bash scripts/test-agent-template.sh
bash scripts/validate.sh
bash scripts/smoke-install.sh
```

### Evidence (filled by reviewer at Stage 4/5)

> **Moved.** Filled by the reviewer at Stage 4/5 in `tasks/TASK_REVIEW_T069.md`.

---

## Demonstration

> **Moved.** See `tasks/TASK_REVIEW_T069.md`.

---

## Approach

**Pattern reference**: `.claude/hooks/tests/test_agent_guide_dedup.py` — T066's own suite. It
already encodes this task's governing rule ("nothing may be removed from the template unless all
four role guides carry it", line 119) and the AC3 shape that checks the template does not restate a
shared section. Extend that module; do not start a new one.

Order of operations is load-bearing and is the AC2-trap lesson from T066 repeating in a new form:

1. **Add first, remove second.** Insert the table into all four role guides and confirm AC1 green
   *before* touching the template. The reverse order strips a Permanent Rule from every spawn for as
   long as the intermediate state exists.
2. **Repoint the pinning test, do not loosen it** (AC3). `scripts/test-agent-template.sh:45-60`
   asserts the four principle names and their operational commands against `$TEMPLATE`. Once the
   table moves, no correct implementation can satisfy both that assertion and AC2 — only a test edit
   can. This is the documented T064 case: keep the pinned strings **byte-identical**, repoint them
   at the new location, and add an assertion that the old location no longer carries them. Do not
   relax the `grep -qF` to something fuzzier.
3. **Measure in characters, through one reader** (AC9). T066's own AC7 test passed while the files
   were untouched because it compared `git show` bytes against `read_text` chars, and these guides
   are dense with `—`/`≤`. Normalise both sides through the same function.

---

## Edge Case Checklist

- [ ] Intermediate state: the table must never be absent from *both* locations at any commit
- [ ] `common-infrastructure.md` is the smallest guide and the most-used role — confirm the
      insertion landed there, not just in the three larger ones
- [ ] The template's header note ("Anything every role needs in its own words … lives in each role
      guide") already describes the end state — check whether it needs an edit at all before editing it
- [ ] `AGENTS.md` mirrors Base Rules *and* the Karpathy principles for non-Claude CLIs; it is a
      **different context** from a Claude sub-agent, so its copy is cross-context redundancy and must
      **not** be deleted as duplication
- [ ] The template's Base Rules line 14 says "Karpathy Engineering Principles (below …)" — "below"
      becomes false
- [ ] `scripts/measure_agent_guide_tokens.py` was written by T066 and may assume the template holds
      these sections — read it before trusting its output for AC9
- [ ] The four operational-command strings contain `->` and `"` — verify byte-identity by diff, not
      by eye

---

## Files to Change (Predicted)

| File | Change |
|------|--------|
| `.claude/agents/common-infrastructure.md` | add the Karpathy compact table |
| `.claude/agents/backend.md` | add the Karpathy compact table |
| `.claude/agents/frontend.md` | add the Karpathy compact table |
| `.claude/agents/qa.md` | add the Karpathy compact table |
| `.claude/agents/general-agent-template.md` | remove the table; fix the header note, Base Rules line 14, and the Staleness Guard |
| `scripts/test-agent-template.sh` | repoint AC1 at the role guides; assert the template no longer carries it |
| `.claude/hooks/tests/test_agent_guide_dedup.py` | AC6 checks per-role reachability directly; new tests for AC1/AC2/AC7 |
| `.claude/skills/craft-agent/SKILL.md` | generated role guides carry the table |
| `AGENTS.md` | only if the Staleness Guard check finds it inaccurate |

## Files Must NOT Touch

| File | Reason |
|------|--------|
| `CLAUDE.md` | pinned byte-identical by T066 AC5; never reaches a sub-agent |
| `docs/claude-md/pipeline-stages.md` | its stale Complexity pointer is T070's scope, not this task's |
| `memory/MEMORY.md` and all `memory/*.md` | Supervisor-only, per the Memory Write Protocol |
| `PROJECT_KANBAN.md` | Supervisor-only |

---

## Test Plan

Extend `.claude/hooks/tests/test_agent_guide_dedup.py`:

- AC1 — parametrised over all four roles: each role guide contains the H2 and all four principle
  names with their operational commands, compared against the table text extracted once from a
  single constant so the four assertions cannot drift from each other.
- AC2 — the template contains neither the H2 nor any operational-command string.
- AC7 — the ladder is present in the template and absent from every role guide; compare against
  `main` through one reader (chars, `read_text` both sides) so the T066 byte/char trap cannot recur.
- AC9 — a measurement helper that reports the per-role pair size before and after; **reporting
  only, never a hard assertion on a specific number** (the "scope guard committed as an invariant"
  lesson — a pinned count fails on the next legitimate edit).

Every mutation control in Success Criteria 4–6 must be **confirmed applied** (re-read the diff)
before its RED verdict is trusted, and reverted with `cp`, not `git checkout` — the recorded trap
that silently reverts the fix along with the mutation.

---

## Completion Checklist

- [ ] Implementation done
- [ ] Lint passes
- [ ] Tests written AND pass — output pasted into `tasks/TASK_REVIEW_T069.md`'s Evidence table
- [ ] Mutation controls 4–6 observed RED, then reverted
- [ ] AC9 measurement pasted, null result stated as null
- [ ] Supervisor notified: task ready for Stage 4 review

> `code-review`, `security-review` and `verify` are **not** runnable by you — `Skill()` is not in a
> sub-agent's toolset. Do not claim them. The Supervisor runs all three at Stage 4.
> If existing tests fail for reasons unrelated to this task, **STOP and report** — do not edit them green.
