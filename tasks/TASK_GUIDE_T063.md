# TASK_GUIDE — T063: establish whether injected memory is actually used
**Date**: 2026-08-07
**Complexity Level**: C1
**Risk Level**: Low
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
5. Note the **Complexity Level** above and apply the matching process from the Complexity matrix in `.claude/agents/general-agent-template.md`

Also read `.claude/hooks/post_tool_trace.py`, `.claude/hooks/lib/task_context.py`, and
`.claude/skills/craft-spawn-prompt/SKILL.md` (element 4) before starting.

**STOP-check before anything else**: run `ls tasks/TASK_GUIDE_T063.md`. If it is not there, you are in a
worktree forked from the wrong commit — stop and report to the Supervisor rather than proceeding.

---

## Requirement (Pillar 1 — Adapt the requirement)

`memory/MEMORY.md` is 200 lines and roughly 10,700 tokens. `CLAUDE.md` states it is *"injected in full
into every sub-agent spawn prompt"*, and `craft-spawn-prompt` element 4 requires the *"full contents of
`memory/MEMORY.md`, verbatim"*. Nothing has ever established that a sub-agent draws on it.

This gates T065. If injected memory is not used, the correct change is **deletion or a smaller hot
tier**, not compression — and compressing it would be wasted work.

A first look on 2026-08-07 produced a number that **cannot be trusted**, and understanding why is the
task's starting point. Counting `Read` records in `memory/event-trace/` showed only **5 of 49** tasks
with any read of `MEMORY.md`. But the actor behind those records is unknown:

```
T067 trace records:          bash 12, edit 13, read 1, write 2, Agent 1   (29 total)
T067 agent self-reported:    bash 14, edit 15, read 4                     (33 tool uses)
```

Close but not equal. So `event-trace` may be recording the sub-agent's calls, the Supervisor's own, or
some mix — and the 5-of-49 figure may simply be showing that the *Supervisor* rarely re-reads
`MEMORY.md`, which says nothing about agents.

**Building an answer on that instrument without first establishing what it measures is precisely the
failure that retired two DDRs** (DDR-0001 and DDR-0002 both died because the instrument did not capture
what it was assumed to). Resolving the attribution question is therefore AC1, not a footnote.

There is a second confound to remove. The Supervisor's spawn prompts this session **restated memory
content inline** — for example T059's and T067's prompts both told the agent that `git checkout` is
guardrail-blocked, which is itself a recorded memory learning. An agent that then avoids `git checkout`
proves nothing about `MEMORY.md`; it may have followed the prompt. Any behavioural measure must
separate the two channels.

**Restated intent**:
> Establish, from evidence rather than assumption, (a) what `event-trace` actually attributes and to
> whom, (b) whether `MEMORY.md` reaches a sub-agent verbatim or as a path it may never open, and
> (c) whether there is any observable sign that a sub-agent draws on it — then state plainly what
> that implies for T065, including "the available instruments cannot answer this" if that is the
> honest result.

**Out of scope**:
- Changing `MEMORY.md`, the Memory Write Protocol, the 200-line cap, or any hot-tier content. This task measures; T065 changes.
- Changing `post_tool_trace.py` or any hook. If the instrument is inadequate, that is a **finding**, and the fix is a follow-up task.
- Changing `craft-spawn-prompt`. A deviation between what it mandates and what the Supervisor actually does is a finding, not a fix here.
- Running expensive A/B spawns purely to generate data. If a behavioural experiment is warranted, propose it with a cost estimate and stop for approval.
- Concluding "memory is useless" from an absence of evidence. Absence of a citation is not evidence of non-use — see AC6.

**Requirement Refs**: none — internal, from the 2026-08-07 ideation session in `BRAINSTORMING_LOG.md`.

### Requirement Fidelity Gate (sign off BEFORE implementation)

- [ ] Restated intent confirmed (by Supervisor / user — not the implementing agent)
- [ ] Every Acceptance Criterion below traces to a line in the Requirement

---

## Dependencies & Reachability

**Depends on**: `None` — T061's telemetry is useful context but not required; this task's questions are about attribution and content reach, not cost.

**Entry point**: `scripts/memory_usage_report.py`

---

## Acceptance Criteria

| # | Criterion (testable) | Traces to requirement |
|---|----------------------|-----------------------|
| 1 | The report states, **with cited evidence**, whether `memory/event-trace/*.jsonl` records a sub-agent's own tool calls, the Supervisor's, or both — and how that was determined | "what event-trace actually attributes and to whom" |
| 2 | Where AC1 cannot be settled from existing records alone, the report says so explicitly and names the smallest experiment that would settle it, rather than guessing | the DDR-0001/0002 failure mode |
| 3 | The report states whether `MEMORY.md` reaches a sub-agent **verbatim in the prompt** or **as a path**, citing `craft-spawn-prompt` element 4 against at least three real spawn prompts recovered from `event-trace` `Agent` records | "verbatim or as a path" |
| 4 | Any divergence between what `craft-spawn-prompt` mandates and what the Supervisor actually did is reported as a finding, with the affected task IDs | "a deviation is a finding" |
| 5 | The report gives an operational definition of "used", and states its own limits — in particular that memory preventing a mistake silently is not observable as a citation | "any observable sign" |
| 6 | Negative: the report does not conclude that memory is unused from an absence of citations. If the evidence is absent rather than negative, it must say "not established" | "absence of a citation is not evidence of non-use" |
| 7 | The report ends with a stated implication for T065 — compress, delete, shrink the hot tier, or "cannot yet decide" — with the reasoning | "what that implies for T065" |
| 8 | `scripts/memory_usage_report.py` regenerates every number in the report from the repo, taking no arguments, writing to stdout only | reproducibility |
| 9 | Negative: the script writes to no file under `memory/` or `reports/`, and does not modify any tracked file | the T059 incident — a script that writes to tracked data is a data-loss defect |
| 10 | The script degrades cleanly on a missing or empty `memory/event-trace/` (a fresh worktree has none) — reporting zero counts, never crashing | the recorded worktree/gitignore gotcha |
| 11 | Full hook suite still green, all 258 pre-existing tests unmodified | no regression |

---

## Evaluation & Acceptance (How we know the agent worked correctly)

### Success Criteria (observable, pass/fail)

| # | Given (input/state) | Expect (output/behavior) | How it's checked |
|---|---------------------|--------------------------|------------------|
| 1 | The repo as-is | script exits 0, emits counts for every `T*.jsonl` | automated test |
| 2 | A temp dir with no `memory/event-trace/` | script exits 0, reports zero, no traceback | automated test |
| 3 | An `event-trace` dir with one malformed JSONL line | line skipped, script still exits 0 | automated test |
| 4 | After a full script run | `git status --short` reports no modification to any tracked file | automated check, output pasted |
| 5 | The written report | every numeric claim in it appears in the script's output | manual cross-check by the Supervisor |
| 6 | Full hook suite | 258 + new tests pass | automated test |

> SC4 is load-bearing. T059 was a defect of exactly this shape — a script that wrote to a tracked file
> and destroyed it in a worktree. A measurement task must not repeat it.

### Verification Command (exact, runnable)

```bash
python3 scripts/memory_usage_report.py && python3 -m pytest .claude/hooks/tests -q && git status --short
```

### Evidence (filled by reviewer at Stage 4/5)

| Check | Result | Notes / output snippet |
|-------|--------|------------------------|
| **New test(s) cover Acceptance Criteria (file paths pasted)** | ☐ pass / ☐ fail | |
| Verification command run | ☐ pass / ☐ fail | |
| Negative cases hold | ☐ pass / ☐ fail | [AC9/AC10 — mutation-verified] |
| verify | ☐ pass / ☐ fail / ☐ N/A | |
| Review scope bounded to the change's blast radius (affected set, not whole repo) | ☐ pass / ☐ fail | |
| Full smoke suite still green (no regression) | ☐ pass / ☐ fail | |
| **UI: Visual regression (diff or verdict pasted)** | ☐ N/A | analysis task, no UI component |
| **UI: Design-system compliance (tokens/colors/typography verified)** | ☐ N/A | analysis task, no UI component |
| **UI: Responsiveness at target viewports** | ☐ N/A | analysis task, no UI component |

---

## Demonstration

**BEFORE**: captured by the Supervisor on 2026-08-07 before any implementation commit — the question is
currently unanswerable, and the naive answer is untrustworthy:

```
$ # naive count of MEMORY.md reads per task in event-trace
5 of 49 tasks show any Read of MEMORY.md

$ # but the actor is unknown:
T067 trace records:        bash 12, edit 13, read 1, write 2, Agent 1  (29)
T067 agent self-reported:  bash 14, edit 15, read 4                    (33)
```

No artifact in the repo states what `event-trace` attributes, whether `MEMORY.md` reaches an agent
verbatim, or what "used" would mean.

**AFTER**: [the report, plus the script output that regenerates its numbers]

**DELTA**: [one sentence]

**WITNESS**: [derived from `memory/event-trace/T063.jsonl`, never the implementing agent alone]

---

## Approach

**Pattern reference**: `.claude/hooks/token_audit.py` — a read-only analysis script over
`memory/event-trace/` that emits a report and writes nothing it was not asked to. Imitate its structure
and its argument handling. **Do not imitate its test**: `test_token_audit_generator.py` was the T059
defect, writing to a real tracked file.

Work in this order, because each step decides whether the next is meaningful:

1. **Settle attribution (AC1/AC2).** Determine what `event-trace` records. Evidence already available:
   `Agent` records now carry `spawn.tool_stats` (T061), giving the sub-agent's own tool mix, which can
   be compared against the non-`Agent` records filed under the same task in the same window. If they
   reconcile, the trace holds agent calls; if they are disjoint, it holds Supervisor calls. If neither
   is clean, say so and name the experiment — do not guess.
2. **Settle reach (AC3/AC4).** `Agent` records store the spawn prompt in `summary` (truncated at
   `MAX_SUMMARY_LEN`, so this may only show the opening — note that limit rather than working around
   it). Determine whether prompts paste `MEMORY.md` or point at its path.
3. **Only then, attempt a usage signal (AC5/AC6/AC7).** If steps 1–2 show the instrument cannot see
   agent behaviour, the honest deliverable is "not established, and here is what would settle it".
   That is a **successful** outcome for this task, not a failure.

**The most likely honest result is "not established".** Say that plainly if it is what the evidence
supports. A measurement task that manufactures a confident answer is worse than one that reports the
instrument's limits — that is the whole lesson of DDR-0002.

### Known confound the report must address

Spawn prompts this session restated memory content inline. T059's and T067's both told the agent that
`git checkout` is guardrail-blocked, which is itself a recorded memory learning. An agent avoiding
`git checkout` therefore demonstrates nothing about `MEMORY.md`. Any behavioural claim must separate
the prompt channel from the memory channel, or be labelled as unable to.

---

## Edge Case Checklist

- [ ] `memory/event-trace/` is gitignored, so a fresh worktree has none — the script must report zero, not crash (AC10)
- [ ] `_untagged.jsonl` holds records with no task attribution; count it separately, never fold it into a task
- [ ] `summary` is truncated at `MAX_SUMMARY_LEN` (300) — a prompt-content check may be looking at the opening only
- [ ] Records predating T061 carry no `spawn` key; treat absence as "not captured", never as zero
- [ ] The Supervisor's own calls and an agent's may both land under one task ID — that is the AC1 question, not an assumption
- [ ] Task IDs with very few records may reflect an unarmed `active_task` pointer rather than little work
- [ ] Do not count a `Read` of `MEMORY.md` by the Supervisor writing a memory pass as evidence of agent use

---

## Files to Change (Predicted)

| File | Change |
|------|--------|
| `scripts/memory_usage_report.py` | new — read-only analysis over `memory/event-trace/`, stdout only |
| `.claude/hooks/tests/test_memory_usage_report.py` | new — AC8–AC11 |
| `reports/memory-usage_2026-08-07.md` | new — the written finding. **Confirm with the Supervisor before creating**: `reports/` is gitignored except `token-audit_*.md`, so a new file there will not survive the worktree unless the exception is extended |

## Files Must NOT Touch

| File | Reason |
|------|--------|
| `memory/**` | this task measures memory; it must not modify it |
| `.claude/hooks/post_tool_trace.py` | instrument inadequacy is a finding, not a fix here |
| `.claude/skills/craft-spawn-prompt/SKILL.md` | a mandate/practice divergence is a finding, not a fix here |
| `.claude/hooks/token_audit.py`, `reports/token-audit_*.md` | the retired DDR-0002 instrument |

---

## Test Plan

New test file alongside the script. AC8 (runs, exits 0), AC9 (**writes nothing** — snapshot `git
status --short` before and after and assert identical), AC10 (missing and empty trace dir), and the
malformed-line case.

AC9 is the load-bearing test and must be mutation-verified by making the script write a file and
confirming RED — it passes trivially against a script that never writes, which is the vacuous-assertion
shape this repo has now recorded six times, most recently a line-cap assertion that was non-vacuous
against one mutation and vacuous against another. Attack it from more than one direction: a write under
`memory/`, and a write under `reports/`.

Restore from a `cp` backup taken first — never `git checkout`.

The implementing agent must not be the sole oracle; the Supervisor signs off on AC9 and independently
cross-checks the report's numbers against the script output (SC5).

---

## Completion Checklist

- [ ] Implementation done
- [ ] Self-review: `Skill({ skill: "code-review" })` run
- [ ] Security review: not required (Low risk) — state that explicitly rather than leaving it blank
- [ ] Tests written AND pass — output pasted into Evidence table (Hard-Stop Gate 5)
- [ ] `Skill({ skill: "verify" })` run
- [ ] `memory/MEMORY.md` updated (flag to Supervisor; sub-agents do not write memory)
- [ ] Supervisor notified: task ready for Stage 4 review
