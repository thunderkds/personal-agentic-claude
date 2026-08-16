# 0005. Vital Slice extends Simplicity First, in the guaranteed channel, bounded by AC-immunity

**Status**: Accepted
**Date**: 2026-08-16
**Deciders**: User (path selection + four grilling rulings), Supervisor
**Related**: T071 · `BRAINSTORMING_LOG.md` session 2026-08-16 · constrains against DDR-0004, LR-0001, LR-0002 · builds on T066/T069 (guaranteed channel), T046 (advisory-field precedent), T067 (hard line cap)

---

## Context

The user asked to apply the Pareto principle to this kit, with the target being **downstream consumer
repos, not this repo**: *"when delivering a feature, we just need 20% of the code to get 80% of
quality."* The user also observed that Karpathy may already cover it, and set one hard constraint:
**the feature must still work correctly.**

Three forces made a decision necessary now.

**1. The overlap with Simplicity First is partial, not total.** `CLAUDE.md:111` reads *"Prohibit
speculation. Reject any feature or abstraction not explicitly requested. If 200 lines can be 50,
rewrite."* That is a **prohibition on the unrequested** plus a **compression rule applied after the
surface is chosen**. It contains no instruction to rank a *requested* surface by value and decline to
build part of it. Pareto is the stronger claim and the gap is genuine — so "do nothing" was rejected
on the merits, not dismissed.

**2. The obvious placement is the wrong placement, and the reason is invisible in the result.** The
instinctive home is the Karpathy principles table in `CLAUDE.md`. But `CLAUDE.md` is **not in the
sub-agent read set** — a principle placed there never reaches the agent writing the code. T069 had
already moved the Karpathy table into the four role guides precisely because the role guide is the
**structurally guaranteed** channel (the harness auto-loads it as the system prompt). Those table
rows are now **byte-pinned verbatim** by `test_agent_guide_dedup.py:KARPATHY_TABLE` *and* by
`scripts/test-agent-template.sh` via `grep -qF`, and `test_memory_channel_and_budget.py` separately
requires the two "If 200 lines can be 50" occurrences to **survive untouched**. A Stage 2 pre-flight
sweep found **8 shipping locations** carrying a Simplicity First statement against the 3 the
brainstorm predicted — the third consecutive occurrence of *"extending a convention touches more
places than the AC table enumerates"* (T058, T065, T070).

**3. A principle authorizing scope cuts is the highest-risk text this kit could ship.** The two
active Learning Records are LR-0001 (a structural refactor mis-evaluated as small, pipeline bypassed)
and LR-0002 (pipeline compliance is bypassed when tasks *feel* small). DDR-0004 then **rejected** a
Hard-Stop Gate 1 exemption on exactly that ground. A rule stating *most of what you were asked to
build is not worth building* supplies a principle-sanctioned vocabulary for that same documented
drift. Without an explicit boundary, this change is net-negative.

**Gate assessment (2-of-3, DDR not ADR):** *hard to reverse* — **partly**: ~38 lines are trivial to
delete here, but the kit ships downstream with no backfill, so a reversal never propagates to repos
that already installed it. *Surprising without context* — **yes**: nothing in the resulting files
explains why the rule sits in role-guide prose rather than the principles table, or why "20%" appears
in exactly one file; a future reader would "tidy" both and destroy the design. *Genuine trade-off* —
**yes**: four paths were weighed and the laundering risk shaped the outcome. Criterion 1 is arguable
enough that this was **not** flagged ADR-eligible; ADR-0001 changed install architecture across every
entry point, this is text in seven files.

---

## Decision

We will extend **Simplicity First** with a **Vital Slice** rule rather than adding a fifth Karpathy
principle or an optional skill, and we will place it in the guaranteed channel:

1. **The rule lives in role-guide prose.** Each of the four role guides carries it inside
   `## Simplicity First (your defining constraint)`, **written per-role, not copy-pasted**.
   `backend.md` and `frontend.md` have this section today; `common-infrastructure.md` and `qa.md` do
   **not** and will have it created — QA owns the oracle that the cut still works, and
   common-infrastructure writes the shared services where speculative generality most accumulates.
   Excluding them would leave the rule unreachable for the two roles best placed to enforce it.

2. **Every pinned string stays byte-identical.** The edit is *additive prose placed around the pins*,
   never a rewrite of a pinned row. This applies the recorded rule *"when a test pins prose, fix the
   prose around it, not the test"* by **placement** rather than by negotiating with the assertion,
   so no test constant and no `grep -qF` string is touched.

3. **The number is confined to `CLAUDE.md`.** "80/20" appears exactly once, in the principles row,
   explicitly labelled *a heuristic, not a target*. It appears in **no** role guide and **not** in
   `templates/TASK_GUIDE_template.md` — the files an agent acts from say **"vital slice"** and never
   a percentage. `CLAUDE_LEGACY.md` receives the matching additive edit in the same commit.

4. **AC-immunity is the load-bearing sentence, and it is stated wherever the rule is stated**:
   a Vital Slice narrows **implementation surface** only — never an Acceptance Criterion, never a
   pipeline stage, never a Hard-Stop Gate. If a cut is negotiating with the AC table it has stopped
   being a Vital Slice and become descoping, which is the user's call and not the principle's.

5. **The Cut List is the artifact.** Two advisory fields — `Vital slice` and `Cut list` — go in
   `templates/TASK_GUIDE_template.md`'s `## Approach`, mirroring T046's `Pattern reference`:
   **advisory, no hook, no gate, no backfill.** An unrecorded cut is indistinguishable from an
   oversight after the fact.

6. **Hard line cap: +8 lines per role guide, +2 in `CLAUDE.md`, +4 in the TASK_GUIDE template**
   (~38 total across 7 files). If it does not fit, **tighten the prose rather than raise the cap** —
   T067's device. The cap is about attention, not price: T061 measured ~97% of spawn tokens as cache
   reads and DDR-0004 established spawn *count* as the dominant cost lever, so these lines cost
   approximately nothing in dollars. They cost legibility, and T066 had just measured real reductions
   in these exact files (backend −15.4%, frontend −15.6%, qa −17.0%, c-infra −4.7%).

---

## Alternatives Considered

| Alternative | Pros | Cons | Why not chosen |
|-------------|------|------|----------------|
| **Extend Simplicity First in role-guide prose + advisory TASK_GUIDE fields** | Reaches the implementing agent through the structurally guaranteed channel; ~2% of the invasiveness of a principle-set change; resolves the overlap the user identified instead of shipping two principles that argue; leaves every pinned string untouched | Advisory fields are ignorable, and T046's `Pattern reference` shipped with no measurement of whether it is ever filled in | **Selected** |
| Fifth Karpathy principle in the table | Maximum visibility; principles are the one block T049 kept inline in `CLAUDE.md` | `CLAUDE.md` never reaches a sub-agent, so the rule would not arrive where code is written; dilutes a deliberately-small set of 4; fires on C0 tasks as pure ceremony; two principles about doing less, one of which permits cutting requested work — an agent resolving that conflict picks the permissive one | Rejected: highest laundering risk of the four, in the one channel that cannot deliver it |
| Optional `pareto` skill (the `optimize` precedent) | Matches the user's initial instinct; a skill can carry the full ranking procedure; opt-in costs nothing when unused | Invocation-triggered, and LR-0002 records that optional steps are skipped exactly when tasks *feel* small — which is when the 80% accumulates; *"already covered" must mean reaches-the-context*, and `tdd` is the recorded example of a skill that "covers" what it never delivers | Rejected: would be skipped precisely in the cases it exists for |
| Do nothing — Simplicity First already covers it | Zero change; the user raised it themselves | Simplicity First prohibits the *unrequested* and compresses what is written; it never says *rank the requested and decline part of it*. The user's quote is about selection, not compression | Rejected on the merits — the gap is real, not rhetorical |

---

## Consequences

### Positive
- The rule arrives in the channel the implementing agent is structurally guaranteed to read, rather
  than the channel that is merely tidy.
- `common-infrastructure.md` and `qa.md` gain a `## Simplicity First (your defining constraint)`
  section they never had — a pre-existing asymmetry closed, not created.
- The Cut List makes a deliberate omission legible six months later, which is the difference between
  a decision and a lapse.
- No test constant, no `grep -qF` string and no pinned row is modified, so the change cannot regress
  the T066/T069 guarantees.

### Negative (accepted trade-offs)
- **Advisory means ignorable.** The most likely failure is two blank fields in every TASK_GUIDE. This
  is accepted because it is the *honest* failure mode: visible in every guide, cheap to detect, cheap
  to reverse. Deliberately **not** escalated to a hook or gate — enforcement would contradict the
  T046 precedent this design follows.
- **Simplicity First now carries two ideas** (reject the unrequested; rank the requested). Accepted
  over a fifth principle, but it makes that row the densest in the table.
- **Spending part of T066's measured reduction back.** Bounded by the +8 cap.
- **Vagueness is the price of dropping the number.** "Vital slice" is less crisp than "20%", and
  vagueness is what lets an agent rationalize. Accepted because a number with no instrument behind it
  becomes a target — the failure recorded three times already (DDR-0001, DDR-0002, T063).

### Follow-up
- [ ] **T071** implements this DDR.
- [ ] Stage 4 review must check the **inverted-ranking tell**: a Cut List consisting mainly of error
      handling, validation or boundary conditions has the ranking backwards — that is where
      correctness lives, and it is exactly the code that *looks* like the disposable 80%.
- [ ] Open, unowned: whether the advisory fields are ever actually filled in. T046 shipped the same
      shape with no measurement; this DDR knowingly repeats that. Revisit after ~5 tasks.
- [ ] Unrelated but imminent: `memory/MEMORY.md` sits at ~49.5k / 50,000 chars. The next memory pass
      trips the ratchet; the sanctioned response is `/compact-memory`, never raising the budget.
