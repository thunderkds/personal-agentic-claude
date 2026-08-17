# TASK_GUIDE — T075: Decouple the hot-tier budget mutation from the live file's size, and ratchet 50,000 → 45,000
**Date**: 2026-08-17
**Complexity Level**: C1
**Risk Level**: Medium
**Priority**: P0
**Assigned agent**: QA-Automation-Agent
**Agent guide**: `.claude/agents/qa.md`

---

## Mandatory Startup (Do Not Skip)

Before writing any code:
1. Read `PROJECT_SPEC.md`
2. Read `memory/MEMORY.md`
3. Read this file completely
4. Read `.claude/agents/qa.md`
5. Note the **Complexity Level** above and apply the matching process from the Complexity matrix in your role guide
6. **C1, two test files: `memory/codebase-map.md` is not required.**

> **You do not have a `Skill` tool.** `code-review`, `security-review` and `verify` are run by the
> **Supervisor** at Stage 4/5. Implement, test, and report — do not attempt to invoke them.

> **P0 and blocking.** The suite is red right now. Every push in the repo is gated behind this fix,
> including T074 and T072. Do not expand scope.

---

## Requirement (Pillar 1 — Adapt the requirement)

`test_memory_channel_and_budget.py::test_ac10_growth_in_chars_without_growth_in_lines_turns_the_gate_red`
fails as of commit `6d1f325`.

It is **not** failing because memory content is wrong. The test pads existing `- [` index lines to
force a budget breach, then asserts the gate goes red. It can add at most
`134 entry lines × 72-char pad = 9,648` characters. It only ever passed because the live
`memory/MEMORY.md` happened to sit within that distance of the cap. The approved `/compact-memory`
pass on 2026-08-17 dropped the file 49,957 → 39,638, so the mutation now needs
`45,000/50,000 − 39,638 + 4,000 = 14,362` characters, cannot reach it, the gate correctly stays
green, and `pytest.raises(AssertionError)` sees nothing.

**Restated intent**:
> A test that verifies the budget gate must construct its own breach unconditionally, at **any** live
> file size. Today it silently depends on the live file being nearly full — so the tool built to empty
> that file is the tool that breaks the test. Additionally, per the `/compact-memory` contract, the
> freed headroom is banked by lowering the ratchet.

**Out of scope**:
- Any change to `memory/MEMORY.md` or the cold memory files — content is correct and human-approved
- Any change to `measure_hot_tier` / `assert_hot_tier_within_budget` behaviour — the **gate is correct**; only its test is wrong
- The other blockers (T074, T072) and the two unregistered T073 findings
- Raising the budget under any circumstance — it is a one-way ratchet

**Requirement Refs**: none — test-infrastructure work with no `PRD.md` backing. Anchor is the
`/compact-memory` run of 2026-08-17 and its recorded failure.

### Requirement Fidelity Gate (sign off BEFORE implementation)

- [x] Restated intent confirmed — reproduced by the Supervisor, arithmetic verified numerically
- [x] Domain terms align (`hot tier`, `ratchet`, `mutation control`)
- [x] Every Acceptance Criterion traces to the Requirement
- [x] Requirement Refs: N/A, deviation recorded above

---

## Dependencies & Reachability

**Depends on**: `None` — but **T074 and T072 both depend on this**; nothing can be pushed while it is red.

**Entry point**: `test_ac10_growth_in_chars_without_growth_in_lines_turns_the_gate_red`

---

## Acceptance Criteria

| # | Criterion (testable) | Traces to requirement |
|---|----------------------|-----------------------|
| 1 | `test_ac10` passes against the live `memory/MEMORY.md` at its current 39,638 chars | the reported failure |
| 2 | `test_ac10`'s mutation **asserts it actually breached the budget** before asserting the gate is red — the missing assertion that made it vacuous | "asserts characters grew but never that the budget was breached" |
| 3 | `test_ac10` passes at **any** live file size — proven by running it against a synthetic tiny copy (e.g. a 500-char stub) as well as the live file | "must construct its own breach unconditionally" |
| 4 | The mutation still adds **no lines** — `lines_after == lines_before` must hold, since line-invisibility is the whole point of AC10 | preserve the original intent |
| 5 | `HOT_TIER_CHAR_BUDGET` is `45_000` in `.claude/hooks/tests/test_token_audit_format.py` | banked headroom, Supervisor ruling 2026-08-17 |
| 6 | The in-code comment declaring the budget a downward-only ratchet is **preserved verbatim** — it is the load-bearing part, per the recorded lesson that "the fix is not the number, it is the sentence declaring it a ratchet" | do not delete the rule while touching the number |
| 7 | `test_ac11` (many short lines past 200 stay green) still passes — it needs ~40 chars of headroom below the budget | no regression |
| 8 | `test_live_memory_md_is_within_budget_today` passes at the new 45,000 budget (live 39,638) | no regression |
| 9 | Full suite green: **451 passed** | Hard-Stop Gate 5 |
| 10 | No file under `memory/` is modified by this task or by the suite when it runs | T059 precedent — a test that wrote to a tracked report destroyed data in a worktree |

---

## Evaluation & Acceptance

### Success Criteria (observable, pass/fail)

| # | Given (input/state) | Expect (output/behavior) | How it's checked |
|---|---------------------|--------------------------|------------------|
| 1 | Live `MEMORY.md` at 39,638 chars | `test_ac10` passes | automated test |
| 2 | A synthetic 500-char `MEMORY.md` copy with 3 entry lines | `test_ac10`'s logic still forces a breach and still sees the gate go red | automated test |
| 3 | A synthetic copy already **over** budget before mutation | test still behaves correctly (no false green) | automated test |
| 4 | After the fix | `lines_after == lines_before` still asserted and true | automated test |
| 5 | `HOT_TIER_CHAR_BUDGET` | equals `45_000`; ratchet comment byte-identical | automated test / grep |
| **SC6 (mutation control)** | Restore the old size-coupled padding loop (`while added < target and i < len(lines)`) | `test_ac10` goes **RED** again at the current file size | run, observe RED, revert |
| **SC7 (mutation control)** | Delete the new "did the mutation actually breach the budget?" assertion, then shrink the synthetic input so no breach occurs | the test goes **RED** — proving the new assertion is not vacuous | run, observe RED, revert |

> **Both mutation controls are mandatory, and SC7 is the important one.** This task exists because a
> control asserted the mutation *changed something* rather than that it *achieved its purpose*. Do not
> repeat that shape. Run each, confirm RED, revert, confirm GREEN, and paste the real output — a claim
> that you ran them is not evidence.

### Verification Command (exact, runnable)

```bash
cd /home/hungnguyenhuu/workspace/pets/personal-agentic-claude && \
  CLAUDE_ACTIVE_TASK=T075 python3 -m pytest .claude/hooks/tests/ -q
```

> Expect `451 passed`. Run the **whole** suite — `HOT_TIER_CHAR_BUDGET` is imported across two test
> modules, so changing it reaches further than the file you edit.

### Evidence (filled by reviewer at Stage 4/5)

> **Moved.** Filled by the reviewer at Stage 4/5 in `tasks/TASK_REVIEW_T075.md`.

---

## Demonstration

> **Moved.** See `tasks/TASK_REVIEW_T075.md`.

---

## Approach

**Pattern reference**: `.claude/hooks/tests/test_memory_channel_and_budget.py::test_ac11_many_short_lines_past_200_stay_green_while_under_budget`
— the sibling control directly below the broken test. It constructs its mutation from a fixed,
self-sufficient quantity rather than from the live file's distance to a limit. Imitate that
independence.

**Vital slice**: AC1–AC4 — make the mutation construct its own breach unconditionally and assert it
achieved it. That is the defect and the whole value; AC5/AC6 (the ratchet) is a one-line bank of
already-freed headroom riding along on the same surface.

**Cut list** (deliberately NOT built):
- Parametrizing the whole budget suite over multiple synthetic file sizes — AC3's single tiny-stub case proves size-independence; a matrix is speculation
- A shared fixture factory for synthetic MEMORY.md files — one helper used twice does not earn an abstraction
- Auditing the other 449 tests for the same size-coupling shape — real and worth doing, but a separate sweep, not this P0

**Reasoning**: the minimal correct fix is to make the padding loop **cycle** over the available entry
lines until `added >= target`, instead of stopping when it runs out of lines — then assert
`chars_after > HOT_TIER_CHAR_BUDGET` before expecting the gate to fire. That keeps the
no-new-lines property (AC4) intact, because appending to an existing line never adds one, while
removing every dependence on how full the live file happens to be.

---

## Edge Case Checklist

- [ ] The mutation must never add a line — appending to existing lines only, even when cycling
- [ ] A file with **zero** `- [` entry lines → the loop must not spin forever; fail loudly with a clear control message
- [ ] A file already over budget before mutation → must not produce a false green
- [ ] Do not weaken the assertion to make it pass — the gate is correct, only the test is wrong
- [ ] Preserve the ratchet comment verbatim while changing the number (AC6)
- [ ] `HOT_TIER_CHAR_BUDGET` is imported by two modules — grep both before assuming the blast radius
- [ ] Nothing under `memory/` may be written by the suite (T059)
- [ ] Do not "fix" a red test by editing what it asserts about the gate's message format (AC2 of the original task) — those assertions are still correct

---

## Files to Change (Predicted)

| File | Change |
|------|--------|
| `.claude/hooks/tests/test_memory_channel_and_budget.py` | Fix `test_ac10`'s padding loop; add the breach assertion; add the tiny-stub size-independence case |
| `.claude/hooks/tests/test_token_audit_format.py` | `HOT_TIER_CHAR_BUDGET` `50_000` → `45_000`, ratchet comment untouched |

## Files Must NOT Touch

| File | Reason |
|------|--------|
| `memory/MEMORY.md`, `memory/*.md` | Content is correct and human-approved; the suite must never write here (T059) |
| `assert_hot_tier_within_budget`, `measure_hot_tier` | The gate is correct — only its test is broken |
| `.claude/hooks/*.py` (non-test) | No hook behaviour changes in this task |
| `tasks/TASK_GUIDE_T074.md`, `PROJECT_KANBAN.md` | Supervisor-owned |

---

## Test Plan

1. **Reproduce first.** Run the suite, confirm `test_ac10` fails with `DID NOT RAISE`. Paste it.
2. **Fix the loop** so padding cycles until `target` is reached regardless of entry-line count.
3. **Add the missing assertion**: after mutating, assert `chars_after > HOT_TIER_CHAR_BUDGET` with a
   message naming both numbers — the mutation must be proven to have achieved its purpose, not merely
   to have changed the file.
4. **Add AC3's size-independence case**: a synthetic ~500-char stub with 3 entry lines; the same
   mutation logic must still breach and still turn the gate red.
5. **Lower the ratchet** to `45_000`, leaving the ratchet comment byte-identical.
6. **Run mutation controls SC6 and SC7**, observe RED each time, revert, confirm green.
7. **Full suite**: expect `451 passed`.

---

## Completion Checklist

- [ ] Reproduction pasted before any fix
- [ ] Implementation done
- [ ] Tests pass — full-suite output pasted into `tasks/TASK_REVIEW_T075.md`'s Evidence table (Hard-Stop Gate 5)
- [ ] Both mutation controls (SC6, SC7) run, observed RED, reverted, suite green — output pasted
- [ ] UI Evidence rows marked ☐ N/A (pure test-infrastructure task; UI/Design AC section deliberately deleted)
- [ ] Supervisor notified: task ready for Stage 4 review

---

## Stage 2 Amendment — Supervisor ruling, 2026-08-17

> The implementing agent halted on a genuine contradiction and was right to. Both defects below are
> **the Supervisor's**, introduced at Stage 2 of this task and at Stage 4 of T071. Recorded, not hidden.

### Defect 1 — AC5 contradicts this guide's own Files-Must-NOT-Touch list

AC5 lowers `HOT_TIER_CHAR_BUDGET` to `45_000`. Two existing tests then fail because they assert the
budget is stated in prose: `test_ac12` (against `memory/MEMORY.md`'s header) and `test_ac8` (against
`setup.sh`'s seeded stub). But `memory/MEMORY.md` was placed on Files-Must-NOT-Touch.

**Ruling: the prose edits are IN SCOPE. AC5 stands.** The Must-Not-Touch entry was written to protect
memory *content* — the Index and its entries, and the T059 data-destruction precedent. It was never
meant to freeze the header's statement of the budget. Leaving that header reading "Max 50,000
characters" while the gate enforces 45,000 would ship **prose that contradicts ground truth, in the
very file whose budget it describes** — which is precisely the defect T073 just fixed in
`post_bash_memory_update.py`, three commits ago. Recreating it here would be indefensible.

**Amended scope**, replacing the `memory/MEMORY.md` row in Files Must NOT Touch:

| File | Scope |
|------|-------|
| `memory/MEMORY.md` — **header rule block only** (the `> **Rules**:` line stating the budget) | **In scope.** Change `50,000` → `45,000`. The ratchet sentence itself stays byte-identical |
| `memory/MEMORY.md` — `## Index` and every entry | **Still off-limits.** Human-approved content; do not touch |
| `memory/decisions.md`, `glossary.md`, `learnings.md` | **Still off-limits** |
| `setup.sh` — the seeded stub's budget line (`setup.sh:348`) | **In scope.** Same one-number change, so a fresh install seeds the correct budget |

**AC15 (new)**: `memory/MEMORY.md`'s header and `setup.sh`'s seeded stub both state `45,000
characters`, and the ratchet sentence — *"a ratchet: `/compact-memory` may lower it, never raise it"*
— is preserved byte-identical in both. The number moves; the rule declaring it a ratchet must not.

### Defect 2 — a byte-identity pin the agent did not report, and could not have satisfied

`test_vital_slice.py::test_ac8_the_two_simplicity_first_compression_lines_survive` ends with:

```python
assert (ROOT / rel).read_bytes() == read_at(rel, PRE_TASK_REF), f"{rel} was modified"
```

where `rel` is `.claude/hooks/tests/test_memory_channel_and_budget.py` — **the file containing the
failing test T075 exists to fix.** No correct implementation can satisfy both this pin and AC1.

**Occurrence 8 of scope-guard-committed-as-invariant.** Written by the Supervisor during T071 and
signed off by the Supervisor at T071's Stage 4 — the same origin as occurrence 7, which blocked T073
eight days later on the sibling glob one function above. The lesson had already been written to
`memory/learnings.md` before either fired.

**Ruling, following the T073 precedent exactly: delete the byte-identity half, keep the content
half.** The `needles` check above it — that both Simplicity First compression lines still occur ≥2
times — is content-based and therefore durable; it is the real enforcement and it stays. Repointing
`PRE_TASK_REF` is **rejected**: it only moves the wall to T075's commit and guarantees a 9th
occurrence for the next task that touches this file.

**AC16 (new)**: `test_vital_slice.py::test_ac8` retains its `needles` content assertion unchanged, and
its final byte-identity `assert` on `test_memory_channel_and_budget.py` is deleted. No other
assertion in `test_vital_slice.py` is modified.

**SC8 (new mutation control, mandatory)**: delete one of the two Simplicity First compression lines
from a role guide and confirm `test_ac8` still goes **RED** on the surviving content assertion. This
proves the content half is doing real work after the pin is removed — without it, deleting the pin
could silently gut the test.

### Revised expected suite total

`452 passed` — 451 baseline, +1 for AC3's new size-independence test. AC16 removes an assertion, not
a test, so the count does not drop.
