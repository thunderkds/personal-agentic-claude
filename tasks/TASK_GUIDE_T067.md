# TASK_GUIDE — T067: diagnose gains a root-cause rule, backward tracing, and behaviour-triggered red flags
**Date**: 2026-08-07
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
5. Note the **Complexity Level** above and apply the matching process from the Complexity matrix in `.claude/agents/general-agent-template.md`
6. Read `memory/codebase-map.md` (C2)

Also read `.claude/skills/diagnose/SKILL.md` and `.claude/hooks/tests/test_diagnose_evidence_loop.py` in
full before editing either. T058 and T060 both shipped changes to this pair; this task extends them and
must not weaken either.

**STOP-check before anything else**: run `ls tasks/TASK_GUIDE_T067.md`. If it is not there, you are in a
worktree forked from the wrong commit — stop and report to the Supervisor rather than proceeding.

---

## Requirement (Pillar 1 — Adapt the requirement)

The user pointed at prior art — `github.com/obra/superpowers/tree/main/skills/systematic-debugging`
(SKILL.md plus `root-cause-tracing.md`) — and asked what our `diagnose` skill can take from it.

A comparison found our skill already stronger on instrumentation, hypothesis generation, feedback-loop
construction and escalation. Four genuine gaps remain, plus two small practical items.

The sharpest of them, verified against the live file at `d374cb1`: **the string "root cause" appears
exactly once in all 124 lines of `diagnose/SKILL.md`, in the Communication Protocol notification
template on line 124.** The skill asks the agent to *report* a root cause but nowhere requires the fix
to be *at* one. Phase 5 says write a regression test then fix; nothing constrains where the fix lands.
Phase 6 asks "what would have prevented this bug?", which is post-hoc prevention, not a constraint.

**Restated intent**:
> `diagnose` should forbid symptom fixes outright, give the agent a backward call-chain tracing
> technique for "an invalid value arrived from somewhere" bugs, name the behaviours that mean the
> agent has already abandoned the method, and let it generate hypotheses by comparing against working
> reference code — without weakening anything T058 and T060 established, and without bloating a skill
> that is already 124 lines.

**Out of scope**:
- **Defense-in-depth is REJECTED, not deferred.** The prior art's post-root-cause step adds validation at multiple layers so the bug becomes "impossible" (its own example adds four redundant guards for one bug). That contradicts Simplicity First and Surgical Changes, and Phase 5 already requires reverting changes made for REJECTED hypotheses precisely to stop guards accumulating. It must not appear in any form.
- Restructuring our six phases into the prior art's four. Ours is the more developed shape.
- Replacing the T052 Stuck-Loop trigger (2 consecutive REJECTED hypotheses) with the prior art's 3-failed-fix-attempts trigger. Ours fires earlier; keep it.
- Reducing the 3–5 ranked-hypotheses requirement to the prior art's single hypothesis.
- Any change to Phase 1's ten-rung ladder or Phase 2.
- Vendoring any file from the prior art. Consulted, not copied.

**Requirement Refs**: none — internal, from the 2026-08-07 prior-art comparison.

### Requirement Fidelity Gate (sign off BEFORE implementation)

- [ ] Restated intent confirmed (by Supervisor / user — not the implementing agent)
- [ ] Every Acceptance Criterion below traces to a line in the Requirement

---

## Dependencies & Reachability

**Depends on**: `None`

**Entry point**: `### Phase 5 — Fix + regression test`

---

## Acceptance Criteria

| # | Criterion (testable) | Traces to requirement |
|---|----------------------|-----------------------|
| 1 | The Karpathy Operational Commands block gains a rule requiring the fix to address the root cause, stating explicitly that a fix applied where the error surfaced rather than where it originated is a failure, not a partial success | "forbid symptom fixes outright" |
| 2 | Phase 5 restates the rule at the point of action: before writing the fix, the agent must state where the root cause is and confirm the fix lands there | same |
| 3 | Phase 4 gains a **backward tracing** technique naming the ordered steps: observe the symptom, identify the code that directly produced it, identify its caller, continue up the chain recording the value passed at each level, and locate where the invalid value originated | "backward call-chain tracing technique" |
| 4 | Backward tracing is scoped to the case it fits — a value that is wrong on arrival — and does not replace or reorder the existing Placement options | scope lock |
| 5 | A **red-flag** block names at least four behaviours that mean the method has been abandoned: proposing a fix before tracing, changing more than one variable at a time, asserting a cause without evidence from the loop, and reaching for a quick fix under time pressure | "name the behaviours" |
| 6 | The red-flag block states that any of them returns the agent to Phase 1, and that it fires **before** the Stuck-Loop Checkpoint rather than replacing it — the Checkpoint counts disproven hypotheses, red flags catch the behaviour first | "already abandoned the method" |
| 7 | Phase 3 gains a working-reference comparison: locate similar code that works, enumerate the differences against the broken path, and derive hypotheses from those differences | "comparing against working reference code" |
| 8 | Phase 4's payload guidance notes that a probe may capture a stack trace to identify its caller, and that in tests the probe must write somewhere test output actually surfaces, since a project logger may be suppressed | small practical items |
| 9 | The Stuck-Loop Checkpoint's "widen scope" option names the architectural tell: each fix revealing new shared state or coupling in a different place indicates a design problem rather than a next bug | "architectural tell" |
| 10 | Negative: no occurrence of `defense-in-depth`, `defence-in-depth`, or `defense in depth` anywhere in the file | rejected direction must not re-enter |
| 11 | Negative: `### Phase 1` and `### Phase 2` bodies are byte-identical to their pre-task content | scope lock |
| 12 | Negative: the full ordered list of `###` headings is unchanged in text, count, and order | scope lock |
| 13 | Negative: the probe budget ceiling is still 1–10, and the Stuck-Loop counter still fires on 2 consecutive REJECTED hypotheses — neither replaced by the prior art's numbers | scope lock |
| 14 | Negative: Phase 3 still requires **3–5** ranked falsifiable hypotheses | scope lock |
| 15 | The file is **no longer than 165 lines** after the change (124 before; ≤41 net added) | "without bloating a skill already 124 lines" |
| 16 | All 31 pre-existing tests in `test_diagnose_evidence_loop.py` pass unmodified, and the full suite is green | no regression |

---

## Evaluation & Acceptance (How we know the agent worked correctly)

### Success Criteria (observable, pass/fail)

| # | Given (input/state) | Expect (output/behavior) | How it's checked |
|---|---------------------|--------------------------|------------------|
| 1 | The edited `diagnose/SKILL.md` | root-cause rule present in both the Karpathy block and Phase 5 | automated test |
| 2 | The edited file | backward tracing names all five ordered steps of AC3 | automated test |
| 3 | The edited file | red-flag block names ≥4 behaviours and routes them to Phase 1 | automated test |
| 4 | The edited file | Phase 3 contains the working-reference comparison | automated test |
| 5 | The edited file | Phase 1/2 bodies hash-identical to the pre-task capture; heading list unchanged | automated test |
| 6 | A draft containing `defense-in-depth` | file-wide substring assertion fails | automated test, mutation-verified RED |
| 7 | A draft at 166+ lines | line-count assertion fails | automated test, mutation-verified RED |
| 8 | Full hook suite | no regression | automated test |

### Verification Command (exact, runnable)

```bash
python3 -m pytest .claude/hooks/tests/test_diagnose_evidence_loop.py -q && python3 -m pytest .claude/hooks/tests -q
```

### Evidence (filled by reviewer at Stage 4/5)

| Check | Result | Notes / output snippet |
|-------|--------|------------------------|
| **New test(s) cover Acceptance Criteria (file paths pasted)** | ☑ pass | 12 new tests in `.claude/hooks/tests/test_diagnose_evidence_loop.py` (`test_t067_*`), covering AC1–AC10 and AC13–AC15. These are **assertions against instruction text**, not end-to-end runtime checks — the artifact under test is a skill document. `python3 -m pytest .claude/hooks/tests/test_diagnose_evidence_loop.py -q` → `44 passed in 0.11s` (32 pre-existing + 12 new). Note: AC16 says "31 pre-existing tests"; the file actually held **32** before this task. |
| Verification command run | ☑ pass | `python3 -m pytest .claude/hooks/tests/test_diagnose_evidence_loop.py -q` → `44 passed`; `python3 -m pytest .claude/hooks/tests -q` → `258 passed in 12.39s` (baseline in this worktree was 246). |
| Negative cases hold | ☑ pass | 18 mutation controls, **18/18 RED then restored GREEN**, restored by `cp` from a pre-edit backup (never `git checkout`). Includes the two trivially-passing ones: **AC10** — inserting `defense-in-depth guards at every layer` → `1 failed`, restored → `1 passed`; **AC15** — appending 20 padding lines (175 > 165) → `1 failed`, restored → `1 passed`. Also mutated: step *order* of the backward trace, red-flag routing, the secrets/PII sentence, the 10-probe ceiling → 25, the 2-consecutive-REJECTED trigger → "3 failed fix attempts", and 3–5 hypotheses → one. Script: `scratchpad/mutate.py`; it asserts each mutation target exists before mutating, so a control cannot itself go vacuous. |
| verify | ☑ pass | Full hook suite green (258), `diagnose/SKILL.md` = **155 lines** (≤165), `grep -c -iE 'defen[cs]e[ -]in[ -]depth'` = **0**, `grep -c -i 'root cause'` = **3** (was 1). |
| Review scope bounded to the change's blast radius (affected set, not whole repo) | ☑ pass | `git diff --stat`: exactly 2 files — `.claude/skills/diagnose/SKILL.md` (+35/-4) and its test file (+256/-...). No file from the "Must NOT Touch" table modified. |
| Full smoke suite still green (no regression) | ☑ pass | `258 passed`, 0 failed. No pre-existing test was edited to make it pass; the single pre-existing failure encountered (the Phase 3 hash pin) was a fixture **re-pin** mandated by AC7 — see Deviations below. |
| **UI: Visual regression (diff or verdict pasted)** | ☐ N/A | skill-instruction change, no UI component |
| **UI: Design-system compliance (tokens/colors/typography verified)** | ☐ N/A | skill-instruction change, no UI component |
| **UI: Responsiveness at target viewports** | ☐ N/A | skill-instruction change, no UI component |

### Deviations (implementer — for Supervisor sign-off)

1. **One pre-existing test fixture was changed: the Phase 3 hash pin.**
   `test_sc8_phase_1_2_3_bodies_are_byte_identical` pinned Phase 1, Phase 2 **and Phase 3** to their
   pre-T058 sha256. T067's AC7 requires Phase 3 to change (the working-reference comparison is a
   hypothesis *source*, so it belongs there) and T067's AC11 deliberately narrows the byte-identical
   guarantee to Phase 1/2 only — so this test cannot pass unmodified while AC7 is satisfied. AC16
   ("all pre-existing tests pass unmodified") and AC7 are in direct conflict on this one fixture.
   Resolution taken: the Phase 3 pin was **re-captured, not deleted**
   (`d8facfe3…` → `0a33b7ed…`, min-len 150 → 600), so Phase 3 stays locked against future drift, and
   the 3–5 requirement inside it is separately pinned by
   `test_t067_t058_and_t060_numbers_are_unchanged` (mutation-verified RED). Phase 1 and Phase 2 pins
   are untouched and still passing. **This is the one judgement call in the task and wants explicit
   Supervisor sign-off**; deleting the pin instead would have lost coverage.
2. **AC16's test count is off by one** — it says 31 pre-existing tests in the file; there are 32.
3. **Not verified, flagged rather than asserted**: nothing here proves the *behavioural* claim that
   an agent reading the new text will actually trace backward or stop at a red flag. Every assertion
   is structural, against the document. `verify` was run as the checks listed in the Evidence table,
   not as the built-in skill (the worktree has no separate runtime to exercise).

---

## Demonstration

> Skill-instruction text, not executable code, so BEFORE is the verbatim prior content.

**BEFORE**: `.claude/skills/diagnose/SKILL.md` at `d374cb1` is 124 lines, and the string `root cause`
occurs exactly once in the whole file — line 124, inside the notification template:

```
- **Default Notification**: "Diagnosis complete for [Task ID]. Root cause: [hypothesis]. Feedback loop: [type]. Regression test: [added / no-seam noted]. Prevention: [finding]."
```

Verified with `grep -n -i 'root cause' .claude/skills/diagnose/SKILL.md` → one hit, line 124.
The Karpathy Operational Commands block (lines 10–13) contains no root-cause rule, and Phase 5
(lines 104–110) constrains *when* the fix is written but never *where* it lands.

**AFTER**: 155 lines (+31, cap 165). `grep -n -i 'root cause'` now returns **three** hits — the
unchanged notification template at line 155, plus the standing rule at line 14 and its restatement at
the point of action at line 131. Verbatim excerpts:

Karpathy Operational Commands, line 14:

```
- **Fix the root cause, never the symptom**: the fix must land where the cause *originated*, not where the error *surfaced*. A fix applied at the surfacing site is a **failure, not a partial success**, even when the symptom disappears. A cause counts as the root cause only when the Checkpoint marked its hypothesis **CONFIRMED** — never when it is merely asserted.
```

Phase 5, at the point of action (lines 131–134):

```
**Before writing the fix**, state in one line where the root cause is — the CONFIRMED hypothesis and
the specific location it originates — and confirm the fix lands *there*, not at the site where the
error surfaced. A fix at the surfacing site is a failure, not a partial success. This constrains
*where* the fix goes; it does not require a test seam, so the no-seam finding below stays reachable.
```

Phase 4, backward tracing (lines 96–101):

```
**Backward tracing** — use this to pick probe *sites* when the bug has the shape *a value is already
invalid when it arrives*. It does not apply to a perf regression or a flaky test, and it replaces
none of step 5's Placement options, which still decide what each probe records. In order:
observe the symptom; identify the code that directly produced it; identify that code's caller;
continue up the call chain recording the value passed at each level; and locate where the invalid
value originated — that origin, not the site that surfaced it, is where the fix belongs.
```

Phase 4, red flags, immediately before the Stuck-Loop Checkpoint (lines 107–112):

```
**Red flags — the method has already been abandoned.** Any one of these returns you to **Phase 1**:
proposing a fix before tracing to an origin; changing more than one variable at a time; asserting a
cause without evidence from the loop; reaching for a quick fix under time pressure. These fire
*before* the Stuck-Loop Checkpoint below and do not replace it — the Checkpoint counts disproven
hypotheses and offers a choice of three options, while red flags catch the behaviour earlier and
offer no choice at all.
```

**DELTA**: `diagnose` now forbids symptom fixes as a standing rule *and* at the moment the fix is
written, supplies a scoped five-step backward trace for value-wrong-on-arrival bugs, names four
behaviours that route the agent back to Phase 1 before the Stuck-Loop Checkpoint would fire, and
derives hypotheses from a working reference — in +31 lines, with the 1–10 budget, the 2-consecutive-
REJECTED trigger and the 3–5 hypothesis requirement all unchanged and defense-in-depth absent.

**WITNESS**: [derived from `memory/event-trace/T067.jsonl`, never the implementing agent alone]

---

## Approach

**Pattern reference**: `.claude/hooks/tests/test_diagnose_evidence_loop.py` — section extraction by
heading, hash-pinned negative criteria, file-wide substring assertions for forbidden tokens. T058 and
T060 both established this exact shape against this exact file. Imitate it; do not invent a new style.

Six additions, each placed where the agent is already looking when it needs them rather than collected
into a new section:

| # | Addition | Placement | Why there |
|---|---|---|---|
| 1 | root-cause rule | Karpathy Operational Commands | it is a standing constraint, not a phase step |
| 2 | root-cause restated at point of action | Phase 5, before the fix | a rule stated only at the top is read once and forgotten by Phase 5 |
| 3 | backward tracing | Phase 4, alongside Placement | it is a placement strategy for a specific bug shape |
| 4 | red flags | immediately before the Stuck-Loop Checkpoint | its earlier-firing sibling; adjacency makes the relationship legible |
| 5 | working-reference comparison | Phase 3 | it is a hypothesis *source* |
| 6 | stack capture + test-visible output | Phase 4 payload | practical notes belong with the payload spec |

**Budget is a hard constraint, not advice.** The file is 124 lines and this repo runs a slim-skills
discipline; AC15 caps the result at 165. If the six additions do not fit, tighten the prose — do not
raise the cap. A skill nobody finishes reading enforces nothing.

### Prior art: what was taken, what was already better, what was rejected

Source: `github.com/obra/superpowers/tree/main/skills/systematic-debugging`, consulted 2026-08-07 —
`SKILL.md` and `root-cause-tracing.md`. **Consulted, not vendored.**

**Taken**: the root-cause-before-fix rule and its framing that a symptom fix is a failure rather than a
partial success; the five-step backward tracing method; the red-flag behaviour list routing back to
investigation; pattern analysis against a working reference; capturing a stack trace in a probe; the
note that test output must go where it actually surfaces because loggers may be suppressed; and the
architectural tell that each fix revealing new coupling elsewhere indicates a design problem.

**Already stronger here, deliberately not replaced**: their Phase 1 is one line ("reproduce reliably")
against our ten-rung ladder with an explicit stop-and-ask; they form *one* hypothesis where we require
3–5 ranked and falsifiable; their instrumentation is ad-hoc `console.error` against our NDJSON with a
mandatory `hypothesisId`, a 1–10 probe budget, CONFIRMED/REJECTED/INCONCLUSIVE verdicts citing log
lines, `#region` markers with deterministic cleanup, retain-until-post-fix-verification, and T060's
cross-tier correlation; their escalation is 3 failed fix attempts against our 2 consecutive disproofs
with three named options.

**Rejected outright**: defense-in-depth. See Out of scope. AC10 pins it as a negative so it cannot
re-enter through the implementation — the same device T058 used for its own rejected transport layer.

---

## Edge Case Checklist

- [ ] The root-cause rule must not contradict Phase 5's existing no-seam clause: when no correct seam exists that is a finding, and the rule must not make that path unreachable
- [ ] Backward tracing must not be stated as mandatory for every bug — it fits a value-wrong-on-arrival shape, not a perf regression or a flaky test
- [ ] The red-flag block must not duplicate the Stuck-Loop Checkpoint's three named options; it routes to Phase 1, the Checkpoint offers a choice
- [ ] Working-reference comparison must degrade gracefully when no working reference exists — say so rather than stalling
- [ ] "Root cause" must not become a word the agent asserts without evidence; tie it to the CONFIRMED verdict the Checkpoint already defines
- [ ] Stack capture interacts with the existing secrets/PII prohibition — a stack may embed paths; do not weaken that rule
- [ ] The line-count cap counts the whole file including frontmatter

---

## Files to Change (Predicted)

| File | Change |
|------|--------|
| `.claude/skills/diagnose/SKILL.md` | six additions per the placement table; ≤165 lines total |
| `.claude/hooks/tests/test_diagnose_evidence_loop.py` | new assertions for AC1–AC15; extend the hash-pin fixtures to a fresh pre-task capture |

## Files Must NOT Touch

| File | Reason |
|------|--------|
| `.claude/skills/bugfix/SKILL.md` | the T052 stuck-loop contract and its Attempts Log are unchanged here |
| `.claude/hooks/post_tool_trace.py` | T061's telemetry is unrelated |
| `memory/event-trace/**`, `reports/token-audit_*.md` | untouched by this task |
| `templates/TASK_GUIDE_template.md` | T064's scope, not this one's |

---

## Test Plan

Extend `test_diagnose_evidence_loop.py` in its existing style — no new test file.

Positive assertions for each of the six additions. Negative assertions for AC10 (forbidden token,
file-wide), AC11/AC12 (hash pins re-captured against the pre-task state), AC13/AC14 (the numbers T058
and T060 established), and AC15 (line count).

Every new assertion must be mutation-verified: break what it guards, observe RED, restore, observe
GREEN, paste both. **This applies with particular force to AC10 and AC15**, which pass trivially — a
file that never mentioned `defense-in-depth` satisfies AC10 unconditionally, and a file under the cap
satisfies AC15 unconditionally. Mutate by *introducing* the forbidden token and by *padding past* the
cap, and confirm RED in both cases. Two recorded precedents make this non-optional: T060's own Stage 4
fix passed the whole suite while asserting nothing, and this repo has now logged five vacuous-assertion
incidents.

Restore from a `cp` backup taken first — never `git checkout`, which is guardrail-blocked here and
would also revert the fix.

The implementing agent must not be the sole oracle; the Supervisor writes or signs off on the AC10,
AC15 and AC11/AC12 assertions.

---

## Completion Checklist

- [ ] Implementation done
- [ ] Self-review: `Skill({ skill: "code-review" })` run
- [ ] Security review: `Skill({ skill: "security-review" })` run (Medium risk) — run manually and label it if the checked-out branch is not the task branch
- [ ] Tests written AND pass — output pasted into Evidence table (Hard-Stop Gate 5)
- [ ] `Skill({ skill: "verify" })` run
- [ ] `memory/MEMORY.md` updated (flag to Supervisor; sub-agents do not write memory)
- [ ] Supervisor notified: task ready for Stage 4 review
