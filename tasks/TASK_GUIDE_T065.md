# TASK_GUIDE — T065: Make the memory channel honest and the size gate measure what it costs
**Date**: 2026-08-09
**Complexity Level**: C2
**Risk Level**: Medium
**Priority**: P2
**Assigned agent**: Common-Infrastructure-Agent
**Agent guide**: `.claude/agents/common-infrastructure.md`

> **Raised C1 → C2 at Stage 2.** Registered as C1 when it looked like one test assertion. It is not:
> the documented contract is restated in **eight shipping locations**, one of which actively
> instructs agents not to read memory, and `setup.sh` seeds the same claim into every downstream
> repo. Cross-cutting contract edits are C2.

---

## Mandatory Startup (Do Not Skip)

Before writing any code:
1. Read `PROJECT_SPEC.md`
2. Read `memory/MEMORY.md`
3. Read this file completely
4. Read `.claude/agents/common-infrastructure.md`
5. Note the **Complexity Level** above and apply the matching process from the Complexity matrix in `.claude/agents/general-agent-template.md`
6. **C2 task**: read `memory/codebase-map.md`
7. Read `docs/memory-usage-finding-2026-08-07.md` — T063's finding. Its §(b) and its open question 3 are the direct input to this task; do not re-derive them.

---

## Requirement (Pillar 1 — Adapt the requirement)

Two separate fictions are written into the harness and shipped downstream.

**Fiction 1 — the channel.** `craft-spawn-prompt` element 4 mandates *"Full contents of
`memory/MEMORY.md`, verbatim"*. T063 established that practice passes a **path**: zero of 49 `Agent`
records contained the file's H1, and 5 of 5 recent agents opened the file themselves. Both spawns in
this session (T064, T068) also passed a path, making three independent confirmations.
`docs/claude-md/pipeline-stages.md:155` is the sharp end — it says *"the agent must not re-read it;
it is already in context."* Under the real channel that sentence is **false**, and an agent obeying
it would skip memory entirely.

**Fiction 2 — the size gate.** The cap is `assert len(lines) <= 200` while the cost is characters.
Measured across the last 12 commits that touched the file:

| | oldest (`8a61b04`) | newest (`9d12d08`) | change |
|---|---|---|---|
| lines | 201 | 200 | **pinned** |
| chars | 42,577 | 49,156 | **+15.5%** |
| mean entry | 276 | 326 | +18% |

The gate passed on **every one of those commits.** The file's own stated format is `≤150 chars` per
entry; 130 of 146 entries (89%) violate it, mean 326, max 796. Twice in this session the Supervisor
consolidated older entries to satisfy the line cap while adding longer replacements — the line count
went *down* and the character count went *up*, and the gate was green each time.

**Restated intent** (Supervisor's interpretation, in the project's domain language):
> Make the documented memory channel say what actually happens (the agent is handed a path and reads
> the file), and replace the line-count cap with one that measures characters — the thing that maps
> to cost — so the gate can no longer pass a file that is growing.

**Out of scope**:
- **Compacting `memory/MEMORY.md`'s content.** That is `/compact-memory`'s job and it is a separate,
  human-approved pass. This task ships the *mechanism*; the content is instance-only and does not
  ship (`setup.sh` seeds a fresh stub).
- Changing *which* file is injected, adding a second tier, or touching the cold files.
- Deleting the hot tier. T063 could not establish that memory is drawn upon, but AC6 there forbids
  inferring non-use from absent evidence, and that reasoning stands.
- T066's startup-read dedup.

**Requirement Refs**: none — harness-internal, no `PRD.md` FR/NFR.

### Requirement Fidelity Gate (sign off BEFORE implementation)

- [x] Restated intent confirmed — channel direction chosen by the user 2026-08-09 over three stated alternatives
- [x] Domain terms align with `PROJECT_SPEC.md` glossary
- [x] Every Acceptance Criterion below traces to a line in the Requirement
- [x] Requirement Refs: N/A, stated rather than left blank

---

## Dependencies & Reachability

**Depends on**: `None` — T063 merged and its finding doc is on disk; the channel ruling is made.

**Entry point**: `test_memory_md_hot_tier_stays_within_line_limit` — the literal, grep-able test name
that enforces the current cap.

---

## Acceptance Criteria

| # | Criterion (testable) | Traces to requirement |
|---|----------------------|-----------------------|
| 1 | The hot-tier size test asserts on **characters**, not `len(lines)`. Budget is **52,000 chars** (current 49,156 + ~6% headroom) | Fiction 2 |
| 2 | The test's failure message reports current chars, the budget, and the overage — a bare `assert x <= y` gives the next Supervisor nothing to act on | Fiction 2 |
| 3 | The test additionally **reports** per-entry statistics (count, mean, max, how many exceed the documented per-entry limit) without failing on them. 89% currently violate; a hard per-entry gate would turn the suite red on arrival and is out of scope | Out of scope — no content compaction |
| 4 | The documented per-entry limit is corrected from the fictional `≤150 chars` to a figure the corpus can actually meet, **or** restated explicitly as an aspiration the current file does not meet. Silently keeping `≤150` while 89% violate it is not acceptable | Fiction 2 |
| 5 | `craft-spawn-prompt` element 4 says the spawn prompt passes the **path** `memory/MEMORY.md` and instructs the agent to read it — not "full contents, verbatim" | Fiction 1 |
| 6 | **The load-bearing correction**: `docs/claude-md/pipeline-stages.md:155`'s *"the agent must not re-read it; it is already in context"* is removed or inverted. An agent following the old sentence under the real channel never reads memory at all | Fiction 1 |
| 7 | Every one of the eight shipping locations listed in *Files to Change* is updated consistently — no location still claims verbatim injection or a 200-line cap | Fiction 1 + 2 |
| 8 | `setup.sh`'s seeded `MEMORY.md` stub carries the corrected rules, so a fresh downstream repo does not start from the fiction | Fiction 1 + 2 |
| 9 | **Negative, file-wide**: after the change, `grep -rn '200 lines\|≤200 lines'` over shipping files returns no hit that refers to the memory cap. Pre-existing unrelated hits (`CLAUDE.md`'s Simplicity First line "If 200 lines can be 50") must **not** be touched — enumerate them first and exclude them by content, not by count | Surgical Changes |
| 10 | **Negative, mutation-verified**: appending ~4,000 chars of long entries to `memory/MEMORY.md` **without** adding lines turns the new test RED. Under the old test that mutation was invisible — this is the precise defect and it must be pinned | Fiction 2 |
| 11 | **Negative, mutation-verified from the other direction**: adding many short lines that push line count past 200 but keep chars under budget must **pass**. The old failure mode must not simply be re-created under a new name | Fiction 2 |
| 12 | `memory/MEMORY.md` content is otherwise unmodified — its header rules may change, no index entry may be added, removed or reworded | Out of scope — no content compaction |

---

## Evaluation & Acceptance (How we know the agent worked correctly)

### Success Criteria (observable, pass/fail)

| # | Given (input/state) | Expect (output/behavior) | How it's checked |
|---|---------------------|--------------------------|------------------|
| 1 | The live `memory/MEMORY.md` as it ships today (49,156 chars) | test **passes** — the budget has headroom, this task does not turn the suite red | automated test |
| 2 | +4,000 chars added to existing entries, line count unchanged | test **fails**, message names chars/budget/overage (AC10) | automated test |
| 3 | 40 short lines added, chars still under budget | test **passes** (AC11) | automated test |
| 4 | `grep` for verbatim-injection claims across shipping files | zero hits (AC7) | automated test |
| 5 | A fresh `setup.sh` scaffold into a temp dir | seeded stub carries corrected rules (AC8) | automated test |

### Verification Command (exact, runnable)

```bash
pytest .claude/hooks/tests/ -q && bash scripts/smoke-install.sh
```

### Evidence

> **Moved.** Filled by the reviewer at Stage 4/5 in `tasks/TASK_REVIEW_T065.md`.

---

## Demonstration

> **Moved.** See `tasks/TASK_REVIEW_T065.md`.

---

## Approach

**Pattern reference**: `.claude/hooks/tests/test_token_audit_format.py` — the existing
`test_memory_md_hot_tier_stays_within_line_limit`. Keep its resolution style
(`Path(__file__).resolve().parents[3]`) and its position in the file; replace the assertion and add
the reporting. Rename it to match what it now measures.

**Note the odd home, and leave it there.** The memory cap test lives in a *token-audit format* test
file, which is unrelated. Moving it is tempting and out of scope — say so in your report rather than
doing it, and the Supervisor will register a follow-up if it is worth one.

**Why 52,000 and not "current size".** A cap set exactly at today's size fails on the next honest
edit and trains people to raise it. ~6% headroom lets the next few passes land while still catching
drift. **State in a comment that this number is a ratchet: it may be lowered by `/compact-memory`,
never raised to accommodate growth.** That sentence is the whole point of the task — without it the
new gate decays exactly as the old one did.

**Do the channel edit as a single consistent sweep.** Eight locations say the same thing; update them
in one pass and re-grep afterwards. This is the recorded "retiring a convention touches more places
than the AC table enumerates" — T058's AC named one reference and a second lived outside the
predicted diff. AC9's grep is the guard against exactly that, which is why it is a negative.

**Do not weaken AC9's grep to make it pass.** `CLAUDE.md`'s Simplicity First row contains the string
"200 lines" in a completely unrelated sense ("If 200 lines can be 50, rewrite"). Exclude it by
matching its content, not by allowing "one hit" — a count-based allowance silently permits the next
real regression. Same family as the recorded rule about not loosening a test to fit a fix.

---

## Edge Case Checklist

- [ ] The test must read the file as UTF-8 and count **characters, not bytes** — this file is full of `—`, `☐`, `≤`; a byte count would be ~15% higher and the budget would mean something different than stated
- [ ] Trailing-newline handling: pin whether the final newline counts, so the number is reproducible
- [ ] `setup.sh`'s stub is inside a quoted heredoc (`<<'EOF'`) — edits must not introduce shell expansion
- [ ] The advisory per-entry report must not fail the test even when 89% of entries violate the documented figure (AC3)
- [ ] AC9's grep must not match this guide, `tasks/TASK_REVIEW_T065.md`, `PROJECT_KANBAN.md` or `BRAINSTORMING_LOG.md` — they *describe* the old rule and legitimately quote it. Scope the grep to shipping files and say which
- [ ] `docs/memory-usage-finding-2026-08-07.md` is a historical record of what was true on that date — **do not rewrite it** to match the new state

---

## Files to Change (Predicted)

| File | Change |
|------|--------|
| `.claude/hooks/tests/test_token_audit_format.py` | cap test → chars, renamed, with reporting (AC1–AC3) |
| `.claude/skills/craft-spawn-prompt/SKILL.md` | element 4 → path, not verbatim (AC5) |
| `docs/claude-md/pipeline-stages.md` | line 155 (the harmful sentence, AC6) + line 223 |
| `docs/claude-md/memory-write-protocol.md` | lines 6 and 18 |
| `CLAUDE.md` | line 192 — Memory Write Protocol summary |
| `README.md` | lines 49 and 396 |
| `setup.sh` | the seeded `MEMORY.md` stub header (AC8) |
| `memory/MEMORY.md` | header rules lines 3 and 25 **only** — no index entry touched (AC12) |
| `.claude/hooks/tests/` (new or existing) | AC7–AC11 |

## Files Must NOT Touch

| File | Reason |
|------|--------|
| `memory/MEMORY.md` index entries | AC12 — content compaction is `/compact-memory`'s job |
| `memory/decisions.md`, `learnings.md`, `glossary.md` | Supervisor-only writes; cold tier out of scope |
| `docs/memory-usage-finding-2026-08-07.md` | historical record of a specific date |
| `CLAUDE.md`'s Karpathy Principles table | contains "200 lines" in an unrelated sense (AC9) |
| `PROJECT_KANBAN.md` | Supervisor closes the row; also test-covered |
| `tasks/TASK_GUIDE_T0*.md` | historical guides |

---

## Test Plan

Write AC10 first — append ~4,000 chars to existing entries without adding a line, and confirm the
**old** test passes while the **new** one fails. That contrast is the defect reproduction and the
whole justification for the task; capture it as the Demonstration BEFORE/AFTER.

Then AC11 in the opposite direction, so the fix is not just the old bug renamed.

For AC10/AC11, operate on a **copy** in `tmp_path`. Never write to the real `memory/MEMORY.md` —
T059 was exactly that defect and in a worktree it destroyed data. If a test must exercise the real
path, restore from a `cp` backup, not `git checkout` (the recorded gotcha: `git checkout` also
reverts your uncommitted fix).

Mutation-verify AC9's grep by **introducing** a fresh verbatim-injection claim into one shipping file
and confirming RED — a negative substring assertion passes trivially otherwise, and this family is at
seven recorded instances. Confirm each mutation actually executed before trusting a GREEN.

---

## Completion Checklist

- [ ] Implementation done
- [ ] Self-review: `Skill({ skill: "code-review" })` run
- [ ] Security review: `Skill({ skill: "security-review" })` run — required (Medium risk); check `git branch --show-current` first, the built-in diffs the checked-out branch
- [ ] Tests written AND pass — output pasted into `tasks/TASK_REVIEW_T065.md` (Hard-Stop Gate 5)
- [ ] `Skill({ skill: "verify" })` run
- [ ] UI Evidence rows marked ☐ N/A with justification — pure-backend task
- [ ] Learnings flagged to the Supervisor (do not write `memory/` yourself)
- [ ] Supervisor notified: task ready for Stage 4 review
